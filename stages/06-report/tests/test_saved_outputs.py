"""A saved file of a run that is not what its step wrote must never crash a reader (M9 slice B, second fix round).

A step's output can be cut off by a full disk, or a step can end well having printed something that is not a report. The
check of the run names such an output a gap and holds the run, and `continue` must then always reach the report: a held run
that cannot be released is stuck for good. Each saved file of a clean run is replaced by each bad body in turn, and the
readers run on it: the check, the hold, the release, a re-render, and the comparison with an earlier run (`walkdown.py diff`).
A traceback in any of them fails the test."""
import json
import shutil
import time

import pytest

import drift
import record
from qa_support import check_run

BODIES = {
    "empty list": "[]",
    "empty object": "{}",
    "a number among the findings": json.dumps({"stage": "x", "contract": 1, "findings": [1]}),
    "a finding with no check": json.dumps({"stage": "x", "contract": 1, "findings": [{}]}),
    "a finding with a check and nothing else": json.dumps({"stage": "x", "contract": 1, "findings": [{"check": "x.y"}]}),
    "findings that are not a list": json.dumps({"stage": "x", "contract": 1, "findings": 3}),
    "text cut off": '{"stage": "x", "contract": 1, "findings": [{"check": "a", "fi',
    "a report with no findings": json.dumps({"stage": "x", "contract": 1, "findings": []}),  # a report, with nothing in it
    # M9 slice C: a bad `coverage` is an output that cannot be read (the step has the one gap, `output-unreadable`)
    "a coverage that is a word": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": "everything"}),
    "a coverage that is a number": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": 3}),
    "a coverage that is null": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": None}),
    "a coverage line that is a number": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": [1]}),
    "a coverage line with no checks": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": [
        {"checks": [], "unit": "files", "of": 1, "looked_at": 1, "explained": 0, "found": 0}]}),
    "a coverage line with a count that is not whole": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": [
        {"checks": ["a.b"], "unit": "files", "of": 2.5, "looked_at": 1, "explained": 0, "found": 0}]}),
    "a coverage line with a count that is a boolean": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": [
        {"checks": ["a.b"], "unit": "files", "of": True, "looked_at": 1, "explained": 0, "found": 0}]}),
    "a coverage line with a count below zero": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": [
        {"checks": ["a.b"], "unit": "files", "of": 1, "looked_at": -1, "explained": 0, "found": 0}]}),
    "a coverage line with a count that is text": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": [
        {"checks": ["a.b"], "unit": "files", "of": "3", "looked_at": 1, "explained": 0, "found": 0}]}),
    "a coverage line with no unit": json.dumps({"stage": "x", "contract": 1, "findings": [], "coverage": [
        {"checks": ["a.b"], "of": 1, "looked_at": 1, "explained": 0, "found": 0}]}),
    # M1 slice A: a bad `usage` is an output that cannot be read, the same one gap, and no traceback anywhere
    "a usage that is a word": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": "many"}),
    "a usage that is a number": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": 3}),
    "a usage that is a list": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": [1, 2]}),
    "a usage that is null": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": None}),
    "a usage count that is a boolean": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"input": True, "calls": 1}}),
    "a usage count that is a float": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"output": 2.5, "calls": 1}}),
    "a usage count below zero": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"cache_read": -1, "calls": 1}}),
    "a usage count that is text": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"input": "5", "calls": 1}}),
    "a usage count that is null": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"input": None, "calls": 1}}),
    "a usage whose calls is a boolean": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"input": 1, "calls": False}}),
    # M1 fix 6: a count above 10**15 is not a count (a service can put any number in its reply)
    "a usage count above the ceiling": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"input": 10 ** 15 + 1, "calls": 1}}),
    "a usage count of four thousand digits": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"output": 10 ** 4000, "calls": 1}}),
    "a usage whose reported is a boolean": json.dumps({"stage": "x", "contract": 1, "findings": [], "usage": {"calls": 1, "reported": True}}),
    "a usage whose reported is more than its calls": json.dumps({"stage": "x", "contract": 1, "findings": [],
                                                                 "usage": {"input": 5, "calls": 1, "reported": 2}}),
    "a usage of whole counts": json.dumps({"stage": "x", "contract": 1, "findings": [],
                                           "usage": {"input": 5, "output": 0, "cache_write": 2, "cache_read": 3, "calls": 1}}),
    # the object `02.2-reader` wrote under that name before slice C is a report with no coverage lines: it reads
    "the old reader's object under coverage": json.dumps({"stage": "x", "contract": 1, "findings": [],
                                                           "coverage": {"files": 3, "files_read": 3}}),
}
READS_AS_A_REPORT = ("a report with no findings", "a finding with a check and nothing else",
                     "the old reader's object under coverage", "a usage of whole counts")
FILES = ["01-intake.json", "02.1-inventory.json", "02.2-reader.json", "02.3-graph.json", "02.4-phrases.json",
         "02.5-capability.json", "02.6-builder.json", "capability.json"]


@pytest.fixture(scope="module")
def older_run(made_run, tmp_path_factory):
    """An earlier run of the same repository, to compare with (`diff`)."""
    base = tmp_path_factory.mktemp("older")
    dest = base / "results" / "tiny" / "2026-01-01_older"
    shutil.copytree(made_run, dest)
    rec = json.loads((dest / "data" / "run.json").read_text(encoding="utf-8"))
    rec["finished"] = "2026-01-01T00:00:00+00:00"
    for s in rec["steps"]:
        s["started"], s["finished"] = "2026-01-01T00:00:00+00:00", "2026-01-01T00:00:01+00:00"
    (dest / "data" / "run.json").write_text(json.dumps(rec), encoding="utf-8")
    return dest


def test_a_run_record_changed_by_hand_cannot_put_words_in_the_command_to_go_on(run_dir, run_main):
    """M1 fix round 3, through the report stage: `data/run.json` says the run stopped and kept a model option that no option could be;
    a re-render prints the command to go on with no option for it, one plain sentence, and none of the planted words."""
    rec_path = run_dir / "data" / "run.json"
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    for planted in ("claude-cli:x & echo.INJECTED>marker note: planted", "claude-cli:https://evil.example/x", "jev:fast", 7):
        rec.update({"until": "02.3-graph", "chosen": ["03-sweep"], "backends": {"03-sweep": planted}, "prepared": None})
        rec_path.write_text(json.dumps(rec), encoding="utf-8")
        assert run_main(["--rerender", str(run_dir)]) == 0
        text = (run_dir / "brief.md").read_text(encoding="utf-8")
        assert [x for x in text.splitlines() if x.startswith("To go on:")] == [f"To go on: python walkdown.py continue {run_dir}"], planted
        assert 'The model option the record kept for "Needs a human read" could not be used, so the command to go on leaves it out.' in text
        assert not [w for w in ("INJECTED", "planted", "evil.example", "jev:fast") if w in text], planted
    rec["backends"] = {"03-sweep": "claude-cli:Some-Model_2"}
    rec_path.write_text(json.dumps(rec), encoding="utf-8")
    assert run_main(["--rerender", str(run_dir)]) == 0
    assert f"To go on: python walkdown.py continue {run_dir} --sweep claude-cli:Some-Model_2" in (run_dir / "brief.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("body", list(BODIES))
@pytest.mark.parametrize("name", FILES)
def test_no_reader_crashes_on_a_saved_output_that_is_not_a_report(name, body, run_dir, run_main, older_run, capsys):
    (run_dir / "data" / name).write_text(BODIES[body], encoding="utf-8")
    report = check_run(run_dir)  # the check of the run reads it
    gaps = sum(1 for f in report["findings"] if f["check"] == "qa.gap")
    is_a_report = body in READS_AS_A_REPORT
    if name != "capability.json" and not is_a_report:  # only the pages read the side file
        assert gaps >= 1, "an output that is not a report is a gap"
    if gaps:
        record.hold(run_dir, gaps, "05-qa")
        for page in ("summary.html", "details.html", "review.html", "full.md", "LOG.md", "brief.md", "data/limits.md"):
            (run_dir / page).unlink(missing_ok=True)
        assert run_main([str(run_dir)]) == 2  # held: refused with one line and no traceback
        assert capsys.readouterr().err.startswith("error: this run is held")
        record.release(run_dir, time.strftime("%Y-%m-%dT%H:%M:%S+00:00"))  # what `continue` does before the report
    assert run_main([str(run_dir)]) == 0  # the report with what the run has
    for page in ("summary.html", "details.html", "review.html", "full.md", "LOG.md", "brief.md"):
        assert (run_dir / page).is_file(), page
    assert run_main(["--rerender", str(run_dir)]) == 0  # a re-render
    drift.write_report(older_run, run_dir)  # `walkdown.py diff`
    drift.since(older_run, run_dir)
    drift.changes(run_dir)
