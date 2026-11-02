"""Plain helpers for the tests of the check of the run: steps, reports, and stamps as the record and the steps write them."""
import coverlines
import stagelist
from validate import Stamp

CODED = ["02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases", "02.5-capability", "02.6-builder"]
STEPS = ["01-intake", *CODED]
T = "2026-01-01T00:00:00+00:00"
AUTO = object()  # "give the step the coverage a step that went well has"


def step(stage, ok=True, error=None):
    return {"stage": stage, "ok": ok, "started": T, "finished": T if ok else None, "error": error}


def line(checks, unit="files", of=3, looked_at=3, explained=0, found=0):
    return {"checks": list(checks), "unit": unit, "of": of, "looked_at": looked_at, "explained": explained, "found": found}


def good_coverage(stage, findings=()):
    """The coverage list of a step that went well (M9 slice C): one line for all of its checks, every item looked at or
    explained by a skip finding. A model step counts the passages in its findings; a coded step looked at three files."""
    checks = stagelist.checks(stage)
    if not checks:
        return None
    if stage in stagelist.AI_STAGES:
        asked = [f for f in findings if f.get("qid")]
        skipped = sum(1 for f in asked if "skipped" in f)
        return [line(checks, "passages", len(asked), len(asked) - skipped, skipped, coverlines.found_in(checks, findings))]
    skipped = sum(1 for f in findings if "skipped" in f)
    return [line(checks, "files", 3, 3 - skipped, skipped, coverlines.found_in(checks, findings))]


def report(stage, findings=(), coverage=AUTO, **extra):
    doc = {"stage": stage, "contract": 1, **extra, "findings": list(findings)}
    lines = good_coverage(stage, findings) if coverage is AUTO else coverage
    if lines is not None:
        doc["coverage"] = lines
    return doc


def passed(stages):
    return {s: Stamp("PASS", "1/1", "1/1") for s in stages}


def sweep_finding(n, skipped=None):
    f = {"check": "soft.sweep", "file": "fixture.md", "line": n, "end_line": n, "qid": f"sweep:fixture.md:{n}",
         "backend": "jev"}
    return {**f, "skipped": skipped} if skipped else {**f, "kind": "none"}
