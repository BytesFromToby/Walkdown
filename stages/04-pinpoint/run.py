"""Pinpoint runner: prints one contract-1 report. Spec: specs/pinpoint.SPEC.md, Behavior.

    python stages/04-pinpoint/run.py <input_dir> --reports <dir> [--out <dir>]
        [--pinpoint none|claude-cli[:model]] [--input-only]

For each sweep passage the report shows, a second model names the line that does the flagged
kind of action. A line the secret scan flagged is not sent (`secretmask.ToSend`). It runs only when a backend is chosen (`--pinpoint claude-cli`, or
WALKDOWN_SOFT_PINPOINT) and only after Sweep ran: it reads `03-sweep.json` (and the inventory)
from `--reports`. With no backend it asks nothing and reports no findings. With `--out` it
writes `04-pinpoint.input.jsonl` (exactly what the model is shown) BEFORE anything is sent, and
`04-pinpoint.answers.jsonl` (what came back, verbatim) after, and `04-pinpoint.calls.jsonl` (the call log:
a call that got no answer is tried once more, and each passage whose first try got none, or that was not
sent, has a line) when there is a line to write. With `--input-only` (and `--out`) it writes
the input file and stops: no backend is made, nothing is sent, nothing is printed. A pinpoint marks,
never demotes: the sweep finding stays.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_shared"))

import calllog  # noqa: E402
import coverlines as cov  # noqa: E402
import layout  # noqa: E402
import linetext  # noqa: E402
import options  # noqa: E402
import pinpoint  # noqa: E402
import secretmask  # noqa: E402
import softdata  # noqa: E402
import stagelist  # noqa: E402
import upstream  # noqa: E402
import stagenote  # noqa: E402
import usage  # noqa: E402

STAGE = "04-pinpoint"
ENV = stagelist.AI_ENV[STAGE]
REMOTE = {"claude-cli": True}
INVENTORY, PHRASES, SWEEP = "02.1-inventory", "02.4-phrases", "03-sweep"
NOTHING_LEFT = "nothing of this passage is left to send to a model"  # a Sweep report saved before no flagged line went out can name one
# The reports it reads (the inventory, the phrase step's for the secret scan, and Sweep's): from stages.json. The reports are keyed by
# these names.
READS = stagelist.reads(STAGE)
INPUT_FILE = f"{STAGE}.input.jsonl"
ANSWERS_FILE = f"{STAGE}.answers.jsonl"
CALLS_FILE = layout.calls_file(STAGE)  # the call log (M9): written only when a call got no answer on its first try
# What the step looked at (`stages/_shared/coverlines.py`): the sweep passages the report shows are the items. `of` is counted
# from Sweep's report before anything is sent; a passage that got an answer is looked at and one that got none is explained by
# its skip, both counted in `pinpoint.findings`.
PINPOINT = "soft.pinpoint"
LINES = [((PINPOINT,), "passages")]


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
    ap.add_argument("--pinpoint")
    ap.add_argument("--input-only", action="store_true")
    return ap.parse_args(argv)


def resolve_choice(args, environ) -> tuple[str, str | None]:
    """(the backend, the model the person named or None): `("none", None)` when nothing is chosen. The option wins over the
    variable. A value that cannot be used raises ValueError with the sentence `options.parse_choice` gives."""
    v, src = args.pinpoint, "--pinpoint"
    if v is None:
        v, src = environ.get(ENV) or "none", ENV
    backend, model = options.parse_choice(STAGE, v, src)  # one off list and one set of refusals for every model option
    why = options.model_env_refusal(backend, model, environ.get(options.MODEL_ENV))  # the model a bare claude-cli will run
    if why:
        raise ValueError(why)
    return backend, model


def default_factories(environ, model=None) -> dict:
    """The backends this step can make. `model`: what the option named after the colon; the Claude Code command otherwise
    runs `WALKDOWN_SOFT_CLAUDE_MODEL`, then its own default."""
    def claude(data):
        import back_claude
        return pinpoint.Reader(data, back_claude.ClaudeCLI(data, model=model or environ.get(options.MODEL_ENV)))
    return {"claude-cli": claude}


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
        stagenote.note("no backend picked; the pinpoint asks nothing")
    else:
        if not args.reports:
            eprint("error: --pinpoint reads Sweep's report: give --reports <dir> holding "
                   f"{INVENTORY}.json, {PHRASES}.json, and {SWEEP}.json")
            return 2
        try:
            data = softdata.load()
        except softdata.DataError as exc:
            eprint(f"error: {exc}")
            return 1
        try:
            reports = upstream.load_dir(args.reports, READS)
        except upstream.ReportError as exc:
            eprint(f"error: --reports: {exc}")
            return 2
        reader = linetext.Lines(root, reports[INVENTORY])
        to_send = secretmask.ToSend(reports[PHRASES]["findings"])  # no line the secret scan flagged goes out
        tg = pinpoint.targets(reports[SWEEP]["findings"])
        cov.of(PINPOINT, len(tg))  # every passage the report shows is to be answered or skipped

        def lines_of(f):
            ls = to_send.lines(f["file"], reader.lines(f["file"])) or [""] * f["end_line"]
            return {n: ls[n - 1] for n in range(f["line"], f["end_line"] + 1)}

        def not_sent(f):
            if not to_send.read(f["file"]):
                return secretmask.NOT_READ
            return None if "".join(lines_of(f).values()).strip() else NOTHING_LEFT

        qs = [pinpoint.question(f, lines_of(f), data) for f in tg]
        held = {q["qid"]: why for f, q in zip(tg, qs) if (why := not_sent(f))}
        asked = [q for q in qs if q["qid"] not in held]
        left_out = sum(1 for f in tg if to_send.read(f["file"])
                       for n in to_send.left_out(f["file"], reader.lines(f["file"]) or []) if f["line"] <= n <= f["end_line"])
        if left_out:
            words = "1 line the secret scan flagged is" if left_out == 1 else f"{left_out} lines the secret scan flagged are"
            stagenote.note(f"{words} blank in the passages it asks about")
        rows = ({"qid": q["qid"], "sweep_qid": q["sweep_qid"], "backend": backend,
                 "system": q["_system"], "prompt": q["_prompt"]} for q in asked)
        if args.input_only:  # the questions need no backend: none is made, and nothing is sent or printed
            out_dir.mkdir(parents=True, exist_ok=True)
            _write_jsonl(out_dir / INPUT_FILE, rows)
            stagenote.note(f"--input-only: wrote {INPUT_FILE} ({len(asked)} sweep passages); nothing was sent")
            return 0
        fac = dict(default_factories(environ, model))
        fac.update(factories or {})
        b = fac[backend](data)
        stagenote.note(f"pinpoint backend {backend}{'' if model is None else ':' + model} "
                       f"({'remote' if REMOTE[backend] else 'local'}); {len(asked)} sweep passages")
        if out_dir is not None:
            # what the model will be shown is on disk before anything is sent to it
            out_dir.mkdir(parents=True, exist_ok=True)
            _write_jsonl(out_dir / INPUT_FILE, rows)
        with contextlib.redirect_stdout(sys.stderr):
            answers = b.pinpoint(asked)
        got = [x for x in answers if "skipped" not in x]
        answers += [{"qid": qid, "backend": backend, "skipped": why} for qid, why in held.items()]
        used.append({"role": "pinpoint", "backend": backend, "remote": REMOTE[backend],
                     "model": got[0].get("model") if got else getattr(b, "model", None)})
        fs = pinpoint.findings(tg, qs, answers, lines_of)
        log = CALLS_FILE if out_dir is not None else None
        log_rows = calllog.rows(answers)
        calls = calllog.summary(log_rows, log)
        if out_dir is not None:
            _write_jsonl(out_dir / ANSWERS_FILE, (pinpoint.record(r) for r in answers))
            calllog.write(out_dir / CALLS_FILE, log_rows)
        for line in pinpoint.summary(fs) + calllog.notes(log_rows, log):
            stagenote.note(line)
        tally = getattr(b, "usage", None)
        tokens = tally.block() if tally is not None else None
        if tokens is not None:
            stagenote.note(usage.note(tokens))
        cost = getattr(b, "cost_usd", None)
        if cost:
            stagenote.note(f"{backend} reported cost ${cost:.4f}")

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
