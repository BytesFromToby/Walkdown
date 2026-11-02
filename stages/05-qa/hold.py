"""The brief of a held run. Spec: specs/qa.SPEC.md, hold.

When the check finds a gap the report is not written, and this brief is the one thing the person is shown: the gaps,
counted and named by step and check, and the two ways on. It is written in Walkdown's own words and paths only. A
gap holds the step's plain name, a check ID, a count, a fixture result, and the kind of error a step stopped with; none
of those is text from the audited repository, so the brief can be handed to a chat assistant like any other. A run that
also stopped as asked (`--until`) says so in the stop's own line.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
import layout  # noqa: E402
import stagelist  # noqa: E402
import common_lines  # noqa: E402

GAP = "qa.gap"
CONTINUE = "To write the report with what ran: python walkdown.py continue {folder}"
AUDIT_AGAIN = "Or fix the cause and audit the repository again."
SEE_WHY = "To see why: python tools/grader/grader.py all"  # for a fixture check that gave no verdict
NO_GRADER = "tools/grader/grader.py is missing: get a fresh copy of Walkdown."  # when that is the file that is gone
GRADER = Path(__file__).resolve().parents[2] / "tools" / "grader" / "grader.py"

HOW = {"failed": "it failed", "not-started": "it did not start", "output-missing": "its saved output is not in the run folder",
       "output-unreadable": "its saved output cannot be read"}
HAS_OUTPUT = ("output-missing", "output-unreadable")  # the step ran and went well; what it saved is what is wrong


def gap_line(g: dict) -> str:
    """One gap as a line, by its kind. A kind this file does not know (a later check's) says what it expected and found."""
    name = f'The step "{stagelist.STEP_WORDS.get(g["step"], g["step"])}"'
    kind = g.get("kind")
    if kind == "step-missing":
        how = HOW.get(g.get("why"), "it left no output")
        error = f" ({g['error']})" if g.get("why") == "failed" and g.get("error") else ""
        if g.get("why") in HAS_OUTPUT:  # it did write one: "has no output: its saved output cannot be read" says two things
            return f"{name}: {how}."
        return f"{name} has no output: {how}{error}."
    if kind == "fixture-failed":
        return f"{name} did not pass its fixture check: it gave {g.get('result')}."
    if kind == "fixture-unchecked":
        return f"{name} {common_lines.unchecked_phrase(g.get('result'))}."
    if kind == "model-no-answer":
        check = f" ({g['step_check']})" if g.get("step_check") else ""
        reasons = "; ".join(f"{r} ({c})" for r, c in g.get("reasons") or [])
        log = f" The call log is data/{layout.calls_file(g['step'])}." if g.get("logged") is not None else ""
        return (f"{name}{check} got no answer for any passage: {g.get('none')} of {g.get('asked')}."
                + (f" Reasons: {reasons}." if reasons else "") + log)
    if kind in common_lines.COVERAGE_KINDS:
        return common_lines.coverage_gap_text(g)
    check = f" ({g['step_check']})" if g.get("step_check") else ""
    return f"{name}{check}: expected {g.get('expected')}; found {g.get('found')}."


def causes(gaps: list) -> list[str]:
    """What Walkdown knows of why, for the gaps that carry a cause (a model read's reasons, a step's error type)."""
    return [f'"{stagelist.STEP_WORDS.get(g["step"], g["step"])}": {g["cause"]}' for g in gaps if g.get("cause")]


def found(gaps: list) -> str:
    """`4 gaps`, and with a step that failed, how the rest follow from it: `4 gaps (1 step failed, and the 3 after it did
    not start)`. The counts are of the gaps: a step that failed, and the steps that never started."""
    n = len(gaps)
    said = f"{n} {'gap' if n == 1 else 'gaps'}"
    failed = sum(1 for g in gaps if g.get("kind") == "step-missing" and g.get("why") == "failed")
    behind = sum(1 for g in gaps if g.get("kind") == "step-missing" and g.get("why") == "not-started")
    if not failed:
        return said
    after = "it" if failed == 1 else "them"
    return (f"{said} ({failed} {'step' if failed == 1 else 'steps'} failed"
            + (f", and the {behind} after {after} did not start" if behind else "") + ")")


def build(run_dir, gaps: list, stop: dict | None = None) -> str:
    """The brief of a run held for these gaps (the `qa.gap` findings, in order). `stop`: where the run stopped as asked
    (`record.stop_of`), or None; a stopped run says so in the stop's own line."""
    run_dir = Path(run_dir)
    folder = f'"{run_dir}"' if " " in str(run_dir) else str(run_dir)
    L = [f"Walkdown brief: {run_dir.resolve().parent.name}",
         f"This run is held before the report: the check of the run found {found(gaps)}.", ""]
    L += [f"  {i}. {gap_line(g)}" for i, g in enumerate(gaps, 1)]
    L += [""]
    if stop:
        L.append(common_lines.STOPPED_LINE.format(plain=stagelist.STEP_WORDS[stop["after"]]))
    L += ["No report was written. The saved outputs of the steps that ran are in " + str(layout.data_dir(run_dir)) + ".",
          CONTINUE.format(folder=folder), AUDIT_AGAIN]
    known = causes(gaps)
    if known:
        L.append("What Walkdown knows of the cause: " + "; ".join(known) + ".")
    if any(g.get("kind") == "fixture-unchecked" for g in gaps):
        L.append(SEE_WHY if GRADER.is_file() else NO_GRADER)
    return "\n".join(L) + "\n"


def write(run_dir, gaps: list, stop: dict | None = None) -> Path:
    """Save the brief of a held run as `brief.md` in the run folder; return its path."""
    path = layout.report_dir(run_dir) / layout.BRIEF
    path.write_text(build(run_dir, gaps, stop), encoding="utf-8")
    return path
