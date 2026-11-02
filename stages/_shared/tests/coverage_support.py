"""The coverage list of a step that went well, for tests that stand a step in with a report of their own (M9 slice C).

The check of the run holds a run in which a step's report has no line for one of its checks, so a fake step's report carries
the lines a real step writes: one line for all of the step's checks, every item looked at or explained by a skip finding."""
import stagelist


def good_lines(stage: str, findings=()) -> list | None:
    """The `coverage` list for `stage`, or None for a step that has no checks (intake)."""
    checks = stagelist.checks(stage)
    if not checks:
        return None
    findings = list(findings)
    if stage in stagelist.AI_STAGES:
        asked = [f for f in findings if f.get("qid")]
        skipped = sum(1 for f in asked if "skipped" in f)
        return [{"checks": list(checks), "unit": "passages", "of": len(asked), "looked_at": len(asked) - skipped,
                 "explained": skipped, "found": len(asked) - skipped}]
    skipped = sum(1 for f in findings if "skipped" in f)
    return [{"checks": list(checks), "unit": "files", "of": 3, "looked_at": 3 - skipped, "explained": skipped,
             "found": sum(1 for f in findings if "skipped" not in f)}]


def with_lines(report: dict) -> dict:
    """`report` with the coverage a step that went well writes, unless it has some or the step has no checks."""
    if "coverage" in report:
        return report
    lines = good_lines(report["stage"], report.get("findings") or [])
    return report if lines is None else {**report, "coverage": lines}
