"""The check of the run, for the report's tests (M9 slice B): the pages are drawn from `data/05-qa.json`, so a test that
draws a page from hand-made reports makes the check's findings from the same facts, by the check's own code.

    qa = Q(reports, notes=None, stamps=None, runs_ok=None, stop=None, not_started=())

`reports` is the report stage's dict ({stage: report}, None for a chosen model read that failed); `runs_ok` the steps that
went well (default: those with a report); `stamps` {stage: Stamp}. Intake is added as a step that went well, since a hand-made
`reports` has no section for it. The step rows follow the way the runner writes them: a model read that is a key of
`reports` was started.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
QA = HERE.parents[1] / "05-qa"
for p in (QA, HERE.parents[1] / "_shared"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import coverlines  # noqa: E402
import facts as F  # noqa: E402
import gather  # noqa: E402
import qaview  # noqa: E402
import stagelist  # noqa: E402

AI = stagelist.AI_STAGES
CODED = stagelist.CODED
T = "2026-01-01T00:00:00+00:00"


def with_coverage(stage, doc):
    """`doc` with the coverage list of a step that went well (one line for all its checks, every item looked at or explained
    by a skip finding), unless it has one."""
    checks = stagelist.checks(stage)
    if "coverage" in doc or not checks:
        return doc
    findings = doc.get("findings") or []
    if stage in AI:
        asked = [f for f in findings if f.get("qid")]
        skipped = sum(1 for f in asked if "skipped" in f)
        line = {"checks": list(checks), "unit": "passages", "of": len(asked), "looked_at": len(asked) - skipped,
                "explained": skipped, "found": coverlines.found_in(checks, findings)}
    else:
        skipped = sum(1 for f in findings if "skipped" in f)
        line = {"checks": list(checks), "unit": "files", "of": 3, "looked_at": 3 - skipped, "explained": skipped,
                "found": coverlines.found_in(checks, findings)}
    return {**doc, "coverage": [line]}


def facts_of(reports, notes=None, stamps=None, runs_ok=None, stop=None, not_started=()):
    ok = {s for s, r in reports.items() if r is not None} if runs_ok is None else set(runs_ok)
    steps = [{"stage": "01-intake", "ok": True, "started": T, "finished": T, "error": None}]
    for stage in (*CODED, *AI):
        if stage in AI:
            if stage in reports:  # a model read that is a key of `reports` was started
                steps.append({"stage": stage, "ok": stage in ok, "started": T, "finished": T if stage in ok else None,
                              "error": None if stage in ok else "exit 1: boom"})
        elif stage in ok:
            steps.append({"stage": stage, "ok": True, "started": T, "finished": T, "error": None})
    # a step that went well has an output: its report when the test gave one, else an empty one, and the coverage a step that
    # went well writes (M9 slice C) when the test gave none, so a hand-made report is not a coverage gap
    saved = {s: with_coverage(s, reports.get(s) or {"stage": s, "contract": 1, "findings": []}) for s in ok}
    saved.setdefault("01-intake", {"stage": "01-intake", "contract": 1, "findings": []})
    return F.Facts(steps=steps, stamps=dict(stamps or {}), stop=stop or None, not_started=list(not_started or []),
                   reports=saved, notes=dict(notes or {}))


def Q(reports, notes=None, stamps=None, runs_ok=None, stop=None, not_started=()):
    """The check's view of hand-made facts, as the report stage reads it from `data/05-qa.json`."""
    found = gather.gather(facts_of(reports, notes, stamps, runs_ok, stop, not_started))
    return qaview.Qa(json.loads(json.dumps(found)))  # through JSON, as the file is


def check_run(run_dir):
    """Make `data/05-qa.json` for a run folder the way the runner does, after a test has changed the run's data."""
    run_dir = Path(run_dir)
    report = gather.report(F.load(run_dir))
    (run_dir / "data" / "05-qa.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return report
