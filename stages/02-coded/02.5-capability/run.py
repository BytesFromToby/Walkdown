"""`02.5-capability` runner: prints one contract-1 report. Spec: specs/capability.SPEC.md, run.

    python stages/02-coded/02.5-capability/run.py <input_dir> [--reports <dir>] [--out <dir>]

Derives the capability map from `02.1-inventory` to `02.4-phrases`; detects nothing.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "_shared"))  # the earlier steps, when this runs on its own

import earlier_steps  # noqa: E402
import inputs  # noqa: E402
import stagelist  # noqa: E402
from injection import injections, load_bytes  # noqa: E402
from legs import grants, legs  # noqa: E402
from limits import _candidates, stated_limits  # noqa: E402
from pairs import pairs  # noqa: E402
from posture import postures  # noqa: E402
from rules import EVIDENCE_CAP, GRANTS, INJECTION_EVENTS, LEGS, LIMITS, LOAD_BYTES_EVENTS  # noqa: E402
from images import _references, image_pairs  # noqa: E402
from testdata import loaded_pairs, set_aside  # noqa: E402
import coverlines as cov  # noqa: E402
import stagenote  # noqa: E402

STAGE = "02.5-capability"
# What the step looked at (`stages/_shared/coverlines.py`). It derives the map from the earlier steps' findings and reads no
# file, so its items are the legs and grants of its tables and the findings it reads. `of` is counted here from those
# findings (`count_inputs`), before a check runs; each check counts what it looked at inside its own function (`legs`,
# `grants`, `injections`, `load_bytes`, `postures`, `pairs`, `loaded_pairs`, `image_pairs`, `stated_limits`, `set_aside`).
# `cap.load-bytes` totals the paths `cap.injection` made, one total for each hook config (or one for the descriptions alone), so it
# counts those totals on a line of its own.
LINES = [(("cap.leg",), "legs"),
         (("cap.grant",), "grants"),
         (("cap.injection",), "entries"),
         (("cap.load-bytes",), "entries"),
         (("cap.posture",), "entries"),
         (("cap.pair",), "findings"),
         (("cap.limit",), "findings"),
         (("cap.testdata",), "findings")]


def eprint(*a):
    print(*a, file=sys.stderr)


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _results(reports: dict, stage: str, check=None, prefix=None) -> list[dict]:
    """The earlier step's findings that are results (a skip is none), of one check or of every check that starts with `prefix`."""
    return [f for f in (reports.get(stage) or {}).get("findings", []) if "skipped" not in f
            and (check is None or f.get("check") == check)
            and (prefix is None or str(f.get("check", "")).startswith(prefix))]


def count_inputs(reports: dict, graph: dict | None, aside: bool) -> None:
    """What the checks are to look at, counted from the earlier steps' findings before the check runs (`coverlines`). Called
    twice: with the findings as they are (`aside` false: the checks that read test data too) and with test data set aside
    (`aside` true: the checks that do not)."""
    if not aside:
        static = sum(1 for f in _results(reports, "02.3-graph", "graph.depth") if f.get("via") == "static")
        cov.of("cap.pair", static + len(_references(reports, graph)))  # test-data loads, and the references to pictures
        cov.of("cap.testdata", sum(len((reports.get(s) or {}).get("findings", [])) for s in ("02.1-inventory", "02.4-phrases")))
        return
    events = {e.lower() for e in INJECTION_EVENTS}
    cov.of("cap.leg", len(LEGS))
    cov.of("cap.grant", len(GRANTS))
    cov.of("cap.injection", len(_results(reports, "02.1-inventory", "struct.description"))
           + sum(1 for f in _results(reports, "02.1-inventory", "struct.hooks") if str(f.get("event") or "").lower() in events))
    totals = {f.get("file") for f in _results(reports, "02.1-inventory", "struct.hooks")
              if str(f.get("event") or "").lower() in {e.lower() for e in LOAD_BYTES_EVENTS}}
    cov.of("cap.load-bytes", len(totals) or 1)  # one total for each hook config, or one for the descriptions alone
    cov.of("cap.posture", len(_results(reports, "02.1-inventory", "struct.agent-tools")))
    cov.of("cap.pair", len(_results(reports, "02.4-phrases", prefix="phrase.")))
    cov.of("cap.limit", len(_candidates(reports)))


def derive(reports: dict, graph: dict | None) -> list[dict]:
    cov.begin(LINES)
    count_inputs(reports, graph, aside=False)
    loaded = loaded_pairs(reports, graph)
    shown = image_pairs(reports, graph)  # before the set-aside: an image in tests/ still counts
    reports, aside = set_aside(reports, {p["file"] for p in loaded})
    count_inputs(reports, graph, aside=True)
    lg = legs(reports)
    inj = injections(reports, graph)
    findings = lg + grants(reports, lg) + inj + load_bytes(inj) + postures(reports) \
        + pairs(reports, graph) + loaded + shown + stated_limits(reports) + aside
    # what ships, what it costs, and whether the tools fit are the builder step's (02.6-builder,
    # restructure step 4); it reads this report's `cap.injection` findings
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
            stagenote.note("no graph.json in --reports; hook bytes are unknown (the edges from the step "
                           f"\"{stagelist.PLAIN['02.3-graph']}\" are needed)")
    else:
        with tempfile.TemporaryDirectory(prefix="walkdown-05-") as tmp:
            if _inside(Path(tmp).resolve(), root):
                eprint("error: temporary folder would be inside the input")
                return 2
            try:
                earlier_steps.run_before(STAGE, root, tmp)
                reports, graph = inputs.load_dir(tmp)
            except (earlier_steps.StepFailed, inputs.ReportError) as exc:
                eprint(f"error: {exc}")
                return 1

    for note in LIMITS:
        stagenote.note(note)
    for name, f in inputs.skips(reports):
        stagenote.note(f"carried forward from the step \"{stagelist.PLAIN.get(name, name)}\": {f.get('check')} "
                       f"{f.get('file')} skipped ({f.get('skipped')})")

    findings = derive(reports, graph)
    n = sum(1 for f in findings if f["check"] == "cap.leg" and f["present"])
    stagenote.note(f"{n} of 3 trifecta legs present; a map of capability, not a verdict")

    report = {"stage": STAGE, "contract": 1, "findings": capped(findings), "coverage": cov.lines(findings)}
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        full = {"stage": STAGE, "contract": 1, "findings": findings}
        (out_dir / "capability.json.tmp").write_text(json.dumps(full, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(out_dir / "capability.json.tmp", out_dir / "capability.json")  # whole or absent: a full disk leaves no half
    sys.stdout.buffer.write(json.dumps(report, ensure_ascii=False, indent=1).encode("utf-8")
                            + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
