"""Stage 6 runner: prints one contract-1 report. Spec: specs/run.SPEC.md.

    python stages/06-soft/run.py <input_dir> [--reports <dir>] [--out <dir>]
        [--label none|jev|laya|claude-cli] [--compare none|jev|laya|claude-cli] [--relational none|claude-cli]
        [--both] [--sweep none|jev]

--both (or WALKDOWN_SOFT_BOTH=1): Jev reads each line twice, plain and with the matched
words marked, and the two label distributions are averaged (soft D4). Jev only.

Builds the review packet over stages 1 to 5 and records the answers of the
backends the user picked (none by default). Answers never change a stage 1 to 5
finding, and nothing here renders a verdict.
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

import ask  # noqa: E402
import chunks as chunkmod  # noqa: E402
import packet  # noqa: E402
import softdata  # noqa: E402
import upstream  # noqa: E402

STAGE = "06-soft"
LABEL_CHOICES = ("none", "jev", "laya", "claude-cli")
REL_CHOICES = ("none", "claude-cli")
SWEEP_CHOICES = ("none", "jev")
ENV = {"label": "WALKDOWN_SOFT_LABEL", "compare": "WALKDOWN_SOFT_COMPARE",
       "relational": "WALKDOWN_SOFT_RELATIONAL", "sweep": "WALKDOWN_SOFT_SWEEP"}
ALLOWED = {"label": LABEL_CHOICES, "compare": LABEL_CHOICES, "relational": REL_CHOICES,
           "sweep": SWEEP_CHOICES}


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
    ap.add_argument("--label")
    ap.add_argument("--compare")
    ap.add_argument("--relational")
    ap.add_argument("--both", action="store_true")
    ap.add_argument("--sweep")
    return ap.parse_args(argv)


def resolve_choices(args, environ) -> dict:
    out = {}
    for role, env in ENV.items():
        v = getattr(args, role)
        src = f"--{role}"
        if v is None:
            v, src = environ.get(env) or "none", env
        v = v.strip().lower()
        if v not in ALLOWED[role]:
            raise ValueError(f"{src}: {v!r} is not one of {', '.join(ALLOWED[role])}")
        out[role] = v
    return out


def want_both(args, environ) -> bool:
    return bool(args.both) or str(environ.get("WALKDOWN_SOFT_BOTH", "")).strip().lower()         in ("1", "true", "yes", "on")


def default_factories(environ, both=False) -> dict:
    def jev(data):
        import back_jev
        return back_jev.Jev(data, both=both)

    def laya(data):
        import back_laya
        return back_laya.Laya(data)

    def claude(data):
        import back_claude
        return back_claude.ClaudeCLI(data, model=environ.get("WALKDOWN_SOFT_CLAUDE_MODEL"))
    return {"jev": jev, "laya": laya, "claude-cli": claude}


REMOTE = {"jev": True, "laya": False, "claude-cli": True}


def main(argv=None, environ=None, factories=None) -> int:
    environ = os.environ if environ is None else environ
    real_stdout = sys.stdout.buffer
    try:
        args = parse(sys.argv[1:] if argv is None else argv)
    except SystemExit:
        return 2
    try:
        choices = resolve_choices(args, environ)
    except ValueError as exc:
        eprint(f"error: {exc}")
        return 2
    both = want_both(args, environ)
    if both and "jev" not in (choices["label"], choices["compare"]):
        eprint("error: --both reads with Jev; pick --label jev or --compare jev")
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
    try:
        data = softdata.load()
    except softdata.DataError as exc:
        eprint(f"error: {exc}")
        return 1

    if args.reports:
        try:
            reports = upstream.load_dir(args.reports)
        except upstream.ReportError as exc:
            eprint(f"error: --reports: {exc}")
            return 2
    else:
        with tempfile.TemporaryDirectory(prefix="walkdown-06-") as tmp:
            if _inside(Path(tmp).resolve(), root):
                eprint("error: temporary folder would be inside the input")
                return 2
            try:
                reports = upstream.run_stages(root, HERE.parent, sys.executable, tmp)
            except upstream.StageFailure as exc:
                eprint(f"error: {exc}")
                return 1

    for key, f in upstream.skips(reports):
        eprint(f"note: carried forward from stage {upstream.NAMES[key]}: {f.get('check')} "
               f"{f.get('file')} skipped ({f.get('skipped')})")

    questions = packet.build(reports, root, data, packet.load_pattern_notes())
    labels = [q for q in questions if q["kind"] == "label"]
    rels = [q for q in questions if q["kind"] == "relational"]

    fac = dict(default_factories(environ, both))
    fac.update(factories or {})
    made: dict[str, object] = {}

    def backend(name):
        if name not in made:
            made[name] = fac[name](data)
        return made[name]

    results = {"label": None, "compare": None, "relational": None}
    used = []
    for role in ("label", "compare", "relational"):
        name = choices[role]
        if name == "none":
            continue
        eprint(f"note: {role} backend {name} ({'remote' if REMOTE[name] else 'local'}); "
               f"{len(rels if role == 'relational' else labels)} questions")
        with contextlib.redirect_stdout(sys.stderr):
            b = backend(name)
            results[role] = b.read(rels) if role == "relational" else b.label(labels)
        answered = [r for r in results[role] if "skipped" not in r]
        model = answered[0].get("model") if answered else getattr(b, "model", None)
        row = {"role": role, "backend": name, "remote": REMOTE[name], "model": model}
        if name == "jev" and both:
            row["reads"] = "both"
        used.append(row)
    chunk_list, sweep_results = [], None
    if choices["sweep"] != "none":
        name = choices["sweep"]
        reader = packet.Lines(root, reports.get("01"))
        chunk_list = [dict(c, qid=f"sweep:{c['file']}:{c['line']}")
                      for c in chunkmod.build(reports.get("01"), reader.lines)]
        eprint(f"note: sweep backend {name} ({'remote' if REMOTE[name] else 'local'}); "
               f"{len(chunk_list)} chunks")
        with contextlib.redirect_stdout(sys.stderr):
            b = backend(name)
            sweep_results = b.sweep(chunk_list)
        answered = [x for x in sweep_results if "skipped" not in x]
        used.append({"role": "sweep", "backend": name, "remote": REMOTE[name],
                     "model": answered[0].get("model") if answered else getattr(b, "model", None)})
    if not used:
        eprint("note: no backend picked; the packet is written and no answers are recorded")

    fs = ask.findings(questions, results["label"], results["compare"], results["relational"])
    fs += ask.sweep_findings(chunk_list, sweep_results,
                             (reports.get("04") or {}).get("findings", []))
    for line in ask.summary(questions, fs):
        eprint("note:", line)
    for name, b in made.items():
        toks = getattr(b, "tokens", None)
        if name == "jev" and toks:
            eprint(f"note: jev input tokens {toks} (the SDK reports tokens, not cost)"
                   + ("; two reads per line (--both)" if both else ""))
        cost = getattr(b, "cost_usd", None)
        if name == "claude-cli" and cost:
            eprint(f"note: claude-cli reported cost ${cost:.4f}")

    report = {"stage": STAGE, "contract": 1, "backends": used, "findings": fs}
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        meta = {"input": str(root), "backends": used}
        (out_dir / "06-packet.md").write_text(packet.render_md(questions, meta, data),
                                              encoding="utf-8")
        (out_dir / "packet.json").write_text(json.dumps(
            {"input": str(root), "options": data["label"]["options"],
             "label_question": data["label"]["question"], "questions": questions},
            ensure_ascii=False, indent=1), encoding="utf-8")
        with (out_dir / "answers.jsonl").open("w", encoding="utf-8") as fh:
            for role in ("label", "compare", "relational"):
                for r in results[role] or []:
                    fh.write(json.dumps(ask.record(role, r), ensure_ascii=False) + "\n")
            for r in sweep_results or []:
                fh.write(json.dumps(ask.record("sweep", r), ensure_ascii=False) + "\n")
    real_stdout.write(json.dumps(report, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    real_stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
