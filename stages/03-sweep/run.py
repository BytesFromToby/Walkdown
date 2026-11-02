"""Sweep runner: prints one contract-1 report. Spec: specs/sweep.SPEC.md, Behavior.

    python stages/03-sweep/run.py <input_dir> [--reports <dir>] [--out <dir>] [--sweep none|jev|claude-cli[:model]]
        [--input-only]

The coverage sweep: every passage of the prose a model reads gets one question to a model, so
text no pattern matched still gets a read. A line the secret scan flagged is not sent (`secretmask.ToSend`). It runs only when a backend is chosen (`--sweep jev`,
`--sweep claude-cli:<model>`, or WALKDOWN_SOFT_SWEEP); with none, it asks nothing and reports no findings. With `--out` it
writes `03-sweep.input.jsonl` (exactly what the model is shown) BEFORE anything is sent, and
`03-sweep.answers.jsonl` (what came back, verbatim) after, and `03-sweep.calls.jsonl` (the call log:
a call that got no answer is tried once more, and each passage whose first try got none, or that was not
sent, has a line) when there is a line to write. With `--input-only` (and `--out`) it
writes the input file and stops: no request, no key read, nothing on stdout. An answer never changes a
`02.1-inventory` to `02.5-capability` finding, and nothing here renders a verdict.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_shared"))

import calllog  # noqa: E402
import chunks as chunkmod  # noqa: E402
import coverlines as cov  # noqa: E402
import earlier_steps  # noqa: E402
import findings  # noqa: E402
import layout  # noqa: E402
import linetext  # noqa: E402
import options  # noqa: E402
import secretmask  # noqa: E402
import softdata  # noqa: E402
import stagelist  # noqa: E402
import upstream  # noqa: E402
import stagenote  # noqa: E402
import usage  # noqa: E402

STAGE = "03-sweep"
INVENTORY, PHRASES = "02.1-inventory", "02.4-phrases"
# The earlier steps it reads (the inventory and the phrase findings): from stages.json. The reports
# are keyed by these names.
READS = stagelist.reads(STAGE)
ENV = stagelist.AI_ENV[STAGE]
REMOTE = {"jev": True, "claude-cli": True}
NO_BACKEND = "no sweep backend"
INPUT_FILE = f"{STAGE}.input.jsonl"
ANSWERS_FILE = f"{STAGE}.answers.jsonl"
CALLS_FILE = layout.calls_file(STAGE)  # the call log (M9): written only when a call got no answer on its first try
# What the step looked at (`stages/_shared/coverlines.py`): the passages built are the items. `of` is counted from the
# inventory and the phrase findings before anything is sent; a passage that got an answer is looked at and one that got none
# is explained by its skip, both counted in `findings.sweep_findings`.
SWEEP = "soft.sweep"
LINES = [((SWEEP,), "passages")]


def eprint(*a):
    print(*a, file=sys.stderr, flush=True)


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def parse(argv):
    ap = argparse.ArgumentParser(prog="run.py")
    ap.add_argument("input_dir")
    ap.add_argument("--reports")
    ap.add_argument("--out")
    ap.add_argument("--sweep")
    ap.add_argument("--input-only", action="store_true")
    return ap.parse_args(argv)


def resolve_choice(args, environ) -> tuple[str, str | None]:
    """(the backend, the model the person named or None): `("none", None)` when nothing is chosen. The option wins over the
    variable. A value that cannot be used raises ValueError with the sentence `options.parse_choice` gives."""
    v, src = args.sweep, "--sweep"
    if v is None:
        v, src = environ.get(ENV) or "none", ENV
    backend, model = options.parse_choice(STAGE, v, src)  # one off list and one set of refusals for every model option
    why = options.model_env_refusal(backend, model, environ.get(options.MODEL_ENV))  # the model a bare claude-cli will run
    if why:
        raise ValueError(why)
    return backend, model


def default_factories(environ, model=None) -> dict:
    """The backends this step can make, each from the softreads data. `model`: what the option named after the colon; the
    Claude Code command otherwise runs `WALKDOWN_SOFT_CLAUDE_MODEL`, then its own default."""
    def jev(data):
        import back_jev
        return back_jev.Jev(data)

    def claude(data):
        import back_claude
        import text_sweep
        return text_sweep.TextSweeper(data, back_claude.ClaudeCLI(data, model=model or environ.get(options.MODEL_ENV)))
    return {"jev": jev, "claude-cli": claude}


def _write_jsonl(path: Path, rows) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def main(argv=None, environ=None, factories=None) -> int:
    environ = os.environ if environ is None else environ
    real_stdout = sys.stdout.buffer
    try:
        args = parse(sys.argv[1:] if argv is None else argv)
    except SystemExit:
        return 2
    try:
        backend, model = resolve_choice(args, environ)
    except ValueError as exc:
        eprint(f"error: {exc}")
        return 2
    target = Path(args.input_dir)
    if not target.is_dir():
        eprint(f"error: not a folder: {target}")
        return 2
    root = target.resolve()
    out_dir = None
    if args.out:
        out_dir = Path(args.out).resolve()
        if _inside(out_dir, root):
            eprint(f"error: --out {out_dir} is inside the input; refusing to write there")
            return 2
    if args.input_only and (out_dir is None or backend == "none"):
        eprint("error: --input-only writes the input file and stops: it needs --out <dir> and a backend "
               f"({', '.join(options.backend_names(STAGE))})")
        return 2

    used, fs, calls, tokens = [], [], None, None
    cov.begin(LINES)
    if backend == "none":
        stagenote.note("no backend picked; the sweep asks nothing")
        # one skip, so the grader counts the fixture's recall rows as not measured (skipped), not
        # as misses; a run never gets here, since the orchestrator does not start an unchosen stage
        fs = [{"check": "soft.sweep", "file": None, "line": None, "skipped": NO_BACKEND}]
    else:
        try:
            data = softdata.load()
        except softdata.DataError as exc:
            eprint(f"error: {exc}")
            return 1
        if args.reports:
            try:
                reports = upstream.load_dir(args.reports, READS)
            except upstream.ReportError as exc:
                eprint(f"error: --reports: {exc}")
                return 2
        else:
            with tempfile.TemporaryDirectory(prefix="walkdown-03-") as tmp:
                if _inside(Path(tmp).resolve(), root):
                    eprint("error: temporary folder would be inside the input")
                    return 2
                try:
                    earlier_steps.run_before(STAGE, root, tmp)
                    reports = upstream.load_dir(tmp, READS)
                except (earlier_steps.StepFailed, upstream.ReportError) as exc:
                    eprint(f"error: {exc}")
                    return 1
        for name, f in upstream.skips(reports):
            stagenote.note(f"carried forward from the step \"{stagelist.PLAIN.get(name, name)}\": {f.get('check')} "
                           f"{f.get('file')} skipped ({f.get('skipped')})")

        reader = linetext.Lines(root, reports.get(INVENTORY))
        to_send = secretmask.ToSend((reports.get(PHRASES) or {}).get("findings", []))  # no line the secret scan flagged goes out
        chunk_list = [dict(c, qid=f"sweep:{c['file']}:{c['line']}")
                      for c in chunkmod.build(reports.get(INVENTORY), lambda rel: to_send.lines(rel, reader.lines(rel)))]
        cov.of(SWEEP, len(chunk_list))  # every passage built is to be answered or skipped
        swept = chunkmod.sweep_files(reports.get(INVENTORY))
        unread = [{"check": SWEEP, "file": rel, "line": None, "skipped": secretmask.NOT_READ}
                  for rel in swept if not to_send.read(rel)]
        left_out = sum(len(to_send.left_out(rel, reader.lines(rel) or [])) for rel in swept if to_send.read(rel))
        if left_out:
            stagenote.note(secretmask.left_out_note(left_out))
        if unread:
            stagenote.note(f"left out of the read, {len(unread)} file(s): {secretmask.NOT_READ}")
        fac = dict(default_factories(environ, model))
        fac.update(factories or {})
        b = fac[backend](data)
        stagenote.note(f"sweep backend {backend}{'' if model is None else ':' + model} "
                       f"({'remote' if REMOTE[backend] else 'local'}); {len(chunk_list)} chunks")
        if out_dir is not None:
            # what the model will be shown is on disk before anything is sent to it
            out_dir.mkdir(parents=True, exist_ok=True)
            _write_jsonl(out_dir / INPUT_FILE,
                         ({"qid": c["qid"], "backend": backend, **b.request(c)} for c in chunk_list))
        if args.input_only:  # the file is the whole job: nothing is sent, nothing is printed
            stagenote.note(f"--input-only: wrote {INPUT_FILE} ({len(chunk_list)} chunks); nothing was sent")
            return 0
        with contextlib.redirect_stdout(sys.stderr):
            results = b.sweep(chunk_list)
        answered = [x for x in results if "skipped" not in x]
        used.append({"role": "sweep", "backend": backend, "remote": REMOTE[backend],
                     "model": answered[0].get("model") if answered else getattr(b, "model", None)})
        fs = findings.sweep_findings(chunk_list, results,
                                     (reports.get(PHRASES) or {}).get("findings", []))
        log = CALLS_FILE if out_dir is not None else None
        log_rows = calllog.rows(results)
        calls = calllog.summary(log_rows, log)
        if out_dir is not None:
            _write_jsonl(out_dir / ANSWERS_FILE, (findings.record(r) for r in results))
            calllog.write(out_dir / CALLS_FILE, log_rows)
        for line in findings.summary(fs) + calllog.notes(log_rows, log):
            stagenote.note(line)
        fs += unread  # after the summary: the check of the run takes each from the report, and a `skipped:` note would say it twice
        tally = getattr(b, "usage", None)
        tokens = tally.block() if tally is not None else None
        if tokens is not None:
            stagenote.note(usage.note(tokens))

    report = {"stage": STAGE, "contract": 1, "backends": used, "findings": fs, "coverage": cov.lines(fs)}
    if calls:  # only a step with a call that got no answer on its first try has the block
        report["calls"] = calls
    if tokens is not None:  # what the calls used: counts the backend reported, and the calls sent (usage.py)
        report["usage"] = tokens
    real_stdout.write(json.dumps(report, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    real_stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
