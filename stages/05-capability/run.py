"""Stage 5 runner: prints one contract-1 report. Spec: specs/run.SPEC.md.

    python stages/05-capability/run.py <input_dir> [--reports <dir>] [--out <dir>]

Derives the capability map from stages 1 to 4; detects nothing.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import inputs  # noqa: E402
from injection import injections, load_bytes  # noqa: E402
from legs import grants, legs  # noqa: E402
from pairs import pairs  # noqa: E402
from posture import postures  # noqa: E402
from rules import EVIDENCE_CAP, LIMITS  # noqa: E402
from testdata import loaded_pairs, set_aside  # noqa: E402

STAGE = "05-capability"


def eprint(*a):
    print(*a, file=sys.stderr)


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def derive(reports: dict, graph: dict | None) -> list[dict]:
    loaded = loaded_pairs(reports)
    reports, aside = set_aside(reports, {p["file"] for p in loaded})
    lg = legs(reports)
    inj = injections(reports, graph)
    findings = lg + grants(reports, lg) + inj + load_bytes(inj) + postures(reports) \
        + pairs(reports, graph) + loaded + aside
    for f in findings:
        f["evidence_total"] = len(f.get("evidence", []))
    return findings


def capped(findings: list[dict]) -> list[dict]:
    out = copy.deepcopy(findings)
    for f in out:
        f["evidence"] = f.get("evidence", [])[:EVIDENCE_CAP]
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="run.py")
    ap.add_argument("input_dir")
    ap.add_argument("--reports")
    ap.add_argument("--out")
    try:
        args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit:
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

    if args.reports:
        try:
            reports, graph = inputs.load_dir(args.reports)
        except inputs.ReportError as exc:
            eprint(f"error: --reports: {exc}")
            return 2
        if graph is None:
            eprint("note: no graph.json in --reports; hook bytes are unknown (stage 3 edges "
                   "needed)")
    else:
        with tempfile.TemporaryDirectory(prefix="walkdown-05-") as tmp:
            if _inside(Path(tmp).resolve(), root):
                eprint("error: temporary folder would be inside the input")
                return 2
            try:
                reports, graph = inputs.run_stages(root, HERE.parent, sys.executable, tmp)
            except inputs.StageFailure as exc:
                eprint(f"error: {exc}")
                return 1

    for note in LIMITS:
        eprint("note:", note)
    for key, f in inputs.skips(reports):
        eprint(f"note: carried forward from stage {inputs.NAMES[key]}: {f.get('check')} "
               f"{f.get('file')} skipped ({f.get('skipped')})")

    findings = derive(reports, graph)
    n = sum(1 for f in findings if f["check"] == "cap.leg" and f["present"])
    eprint(f"note: {n} of 3 trifecta legs present; a map of capability, not a verdict")

    report = {"stage": STAGE, "contract": 1, "findings": capped(findings)}
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        full = {"stage": STAGE, "contract": 1, "findings": findings}
        (out_dir / "capability.json").write_text(json.dumps(full, ensure_ascii=False, indent=1),
                                                 encoding="utf-8")
    sys.stdout.buffer.write(json.dumps(report, ensure_ascii=False, indent=1).encode("utf-8")
                            + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
