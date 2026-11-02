"""The earlier steps a stage reads, run for it when it runs on its own. Spec: specs/shared.SPEC.md, earlier_steps.

A run through `walkdown.py` always hands each stage the saved outputs it needs (`--reports`,
`--inventory`). A stage run by itself (the grader grades each stage on its fixtures this way, and so
do tests) has none, so it asks here for the steps it reads, as listed in `stages/stages.json`
(`reads`): they run in order as subprocesses, the way the pipeline runs them, and each report is
saved in the work folder under its name. One helper, in place of the five copies the stages kept
(restructure step 7, notes O4). No stage code is imported.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pipeline  # noqa: E402
import stagelist  # noqa: E402

STAGES_DIR = Path(__file__).resolve().parents[1]
INVENTORY = "02.1-inventory"


class StepFailed(Exception):
    """An earlier step that did not produce a report when it was run here."""


def run_before(stage: str, input_dir, work_dir, python=None, stages_dir=None) -> dict[str, dict]:
    """Run the steps `stage` reads, in order, into `work_dir`; {step name: its report}. Each report
    is saved there as `<name>.json` (and its messages as `<name>.notes.txt`), with `graph.json`
    beside them. The first step that fails stops the rest: StepFailed names it and why."""
    stages_dir = STAGES_DIR if stages_dir is None else Path(stages_dir)
    names = list(stagelist.reads(stage, stages_dir))
    if not names:  # a step that reads nothing has nothing to run first
        return {}
    runs = pipeline.run_stages(input_dir, work_dir, stages_dir, python or sys.executable,
                               stages=names, alone=True)
    for r in runs:
        if not r.ok:
            raise StepFailed(f"{r.stage} failed ({r.error})")
    return {r.stage: r.report for r in runs}


def inventory(stage: str, input_dir, saved=None, python=None, stages_dir=None) -> dict:
    """The inventory report for a stage that reads only that: the saved report when `saved` is
    given (ValueError when it cannot be read), else the inventory step run on `input_dir`
    (StepFailed when it fails)."""
    if saved:
        try:
            return json.loads(Path(saved).read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"cannot read --inventory {saved}: {exc}")
    with tempfile.TemporaryDirectory(prefix="walkdown-earlier-") as tmp:
        return run_before(stage, input_dir, tmp, python, stages_dir)[INVENTORY]
