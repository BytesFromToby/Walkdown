"""Tests for run.py (the check of the run), written from specs/qa.SPEC.md, run.

The check prints one contract-1 report for a run folder and writes nothing; with `--brief` and a gap it writes the brief of a
held run. The runner starts it after the steps, the validation, and the record (`stages/_shared/tests/test_runner.py`)."""
import ast
import json
import subprocess
import sys
from pathlib import Path

from qa_helpers import STEPS
from validate import Stamp

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
RUN = HERE / "run.py"


def start(*args):
    return subprocess.run([sys.executable, str(RUN), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def tree(folder):
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def test_the_report_is_one_contract_1_document_on_stdout_and_the_folder_is_not_written(run_folder):
    run = run_folder(stamps={**{s: Stamp("PASS") for s in STEPS}, "02.4-phrases": Stamp("FAIL")})
    before = tree(run)
    got = start(run)
    assert got.returncode == 0, got.stderr
    doc = json.loads(got.stdout)
    assert doc["stage"] == "05-qa" and doc["contract"] == 1
    assert [f["kind"] for f in doc["findings"] if f["check"] == "qa.gap"] == ["fixture-failed"]
    assert tree(run) == before  # it wrote nothing: no report and no brief
    assert "1 gap" in got.stderr


def test_the_note_counts_the_gaps_the_limits_and_the_checks_that_found_nothing_apart(run_folder):
    """The limits are what the run did not examine; what a check looked at is said apart (`qa.checked`), so the first count
    reads as it did before slice C."""
    got = start(run_folder())
    doc = json.loads(got.stdout)
    gaps = [f for f in doc["findings"] if f["check"] == "qa.gap"]
    limits = [f for f in doc["findings"] if f["check"] == "qa.limit"]
    checked = [f for f in doc["findings"] if f["check"] == "qa.checked"]
    assert not gaps and checked and all(f["kind"] != "checked" for f in limits)
    assert f"0 gaps, {len(limits)} limits, {len(checked)} checked" in got.stderr


def test_with_brief_a_gap_writes_the_brief_of_a_held_run(run_folder):
    held = run_folder(failed=("02.3-graph",), ran=STEPS[:4])
    got = start(held, "--brief")
    assert got.returncode == 0  # the check ran; whether the run is held is in its report
    brief = (held / "brief.md").read_text(encoding="utf-8")
    assert brief.startswith("Walkdown brief: tiny\nThis run is held before the report")
    assert sorted(p.name for p in held.iterdir()) == ["brief.md", "data"]  # the one file it wrote
    assert tree(held / "data").keys() == {f"{s}.json" for s in STEPS[:3]} | {"run.json"}  # and nothing in data/


def test_no_gap_with_brief_writes_nothing(run_folder):
    run = run_folder()
    before = tree(run)
    assert start(run, "--brief").returncode == 0 and tree(run) == before


def test_a_folder_that_is_not_a_run_or_was_made_before_this_version_is_refused_with_one_line(tmp_path, run_folder):
    got = start(tmp_path / "nowhere")
    assert got.returncode == 2 and got.stdout == ""
    assert got.stderr.strip() == f"error: not a run folder (no data/): {tmp_path / 'nowhere'}"
    run = run_folder()
    path = run / "data" / "run.json"
    path.write_text(json.dumps({**json.loads(path.read_text(encoding="utf-8")), "format": 2}), encoding="utf-8")
    got = start(run)
    assert got.returncode == 2 and "made before this version of Walkdown" in got.stderr


def imported_names(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_the_check_is_coded_it_imports_no_other_step_and_nothing_that_reaches_a_model_or_a_network():
    """The step is coded: the standard library, `stages/_shared`, and its own modules only. No other step's code, no model
    client, no network, no subprocess."""
    shared = {p.stem for p in (ROOT / "stages" / "_shared").glob("*.py")}
    own = {p.stem for p in HERE.glob("*.py")}
    forbidden = {"subprocess", "socket", "urllib", "http", "requests", "anthropic", "typesafe_sdk", "ssl"}
    for path in HERE.glob("*.py"):
        names = imported_names(path)
        assert not names & forbidden, (path.name, names & forbidden)
        outside = {n for n in names if n not in sys.stdlib_module_names and n not in shared and n not in own}
        assert not outside, (path.name, outside)


def test_the_check_grades_pass_on_its_fixtures():
    """The step is a detector of gaps in a run and is validated like one: 7 runs it must hold, 7 it must not."""
    got = subprocess.run([sys.executable, str(ROOT / "tools" / "grader" / "grader.py"), "05-qa", "--json"],
                         capture_output=True, text=True, encoding="utf-8")
    doc = json.loads(got.stdout)["stages"][0]
    assert doc["stage"] == "05-qa" and doc["result"] == "PASS", doc
    assert doc["gate"]["passed"] == doc["gate"]["total"] > 0 and doc["negative"]["passed"] == doc["negative"]["total"] > 0
