"""Tests for facts.py, written from specs/qa.SPEC.md, facts."""
import json

import pytest

import facts as F
from qa_helpers import STEPS, report, sweep_finding


def test_a_run_folder_is_read_as_the_record_the_outputs_the_messages_and_the_call_logs(run_folder):
    run = run_folder(ran=[*STEPS, "03-sweep"], outputs={"03-sweep": report("03-sweep", [sweep_finding(1, "jev: no key")])},
                     until="02.6-builder", not_started=[{"stage": "04-pinpoint", "why": "sweep-no-answer"}],
                     files={"02.2-reader.notes.txt": "note: tesseract not installed\n\nwarning: reader failed on a.md\n",
                            "03-sweep.calls.jsonl": '{"qid": "a"}\n{"qid": "b"}\n'})
    got = F.load(run)
    assert [s["stage"] for s in got.steps] == [*STEPS, "03-sweep"]
    assert set(got.reports) == {*STEPS, "03-sweep"} and got.unreadable == set()
    assert got.notes["02.2-reader"] == ["tesseract not installed"]  # the step's own notes only: not the other line
    assert got.logs == {"03-sweep": 2}  # a call log's lines, for a model step that has one
    assert got.stop == {"after": "02.6-builder", "prepared": None}
    assert got.not_started == [{"stage": "04-pinpoint", "why": "sweep-no-answer"}]
    assert got.stamps["02.1-inventory"].result == "PASS"


def test_an_output_that_does_not_read_is_unreadable_and_not_a_report(run_folder):
    run = run_folder(files={"02.3-graph.json": "not json", "02.4-phrases.json": "[1, 2]",
                            "02.5-capability.json": '{"findings": "no"}', "02.6-builder.json": "[]",
                            "02.2-reader.json": "{}"})
    got = F.load(run)
    assert got.unreadable == {"02.3-graph", "02.4-phrases", "02.5-capability", "02.6-builder", "02.2-reader"}
    assert "02.3-graph" not in got.reports and "02.1-inventory" in got.reports


def test_a_coverage_that_is_not_a_list_of_lines_makes_the_output_unreadable_and_the_old_readers_object_reads(run_folder):
    """M9 slice C: a bad `coverage` is a report that cannot be read, like bad findings (`pipeline.read_report`), so the step has
    the one gap. The object `02.2-reader` wrote under that name before the lines reads, and has no lines."""
    bad = {"checks": ["a.b"], "unit": "files", "of": 2.5, "looked_at": 1, "explained": 0, "found": 0}
    run = run_folder(files={
        "02.3-graph.json": json.dumps({**report("02.3-graph"), "coverage": "all of it"}),
        "02.4-phrases.json": json.dumps({**report("02.4-phrases"), "coverage": [bad]}),
        "02.5-capability.json": json.dumps({**report("02.5-capability"), "coverage": [7]}),
        "02.2-reader.json": json.dumps({**report("02.2-reader", coverage=None), "coverage": {"files": 3}})})
    got = F.load(run)
    assert got.unreadable == {"02.3-graph", "02.4-phrases", "02.5-capability"}
    assert "02.2-reader" in got.reports and got.reports["02.2-reader"]["coverage"] == {"files": 3}


def test_a_call_log_with_a_line_that_is_not_json_is_not_counted(run_folder):
    run = run_folder(ran=[*STEPS, "03-sweep"], files={"03-sweep.calls.jsonl": '{"qid": "a"}\nnot json\n'})
    assert F.load(run).logs == {}
    assert F.call_log_lines(run / "data" / "gone.jsonl") is None


def test_a_folder_that_is_not_a_run_or_was_made_before_this_version_is_refused(run_folder, tmp_path):
    with pytest.raises(F.NotARun, match="not a run folder"):
        F.load(tmp_path / "nowhere")
    run = run_folder()
    path = run / "data" / "run.json"
    rec = json.loads(path.read_text(encoding="utf-8"))
    for older in (1, 2):  # format 2 is a run made before the check of the run
        path.write_text(json.dumps({**rec, "format": older}), encoding="utf-8")
        with pytest.raises(F.NotARun, match="made before this version"):
            F.load(run)
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(F.NotARun):
        F.load(run)


def test_a_step_that_failed_gives_no_notes_and_its_error_is_read_from_its_traceback_alone(run_folder):
    """M9 slice B fix round: the messages of a step that failed are an error's words, which can repeat text from the
    audited repository. The check keeps none of them as notes; it reads the error's type from the traceback."""
    stderr = ("note: CANARYMSG not installed, limit reached\n"
              "Traceback (most recent call last):\n  File \"x.py\", line 3, in <module>\n"
              "ValueError: CANARYMSG skipped\nnote: CANARYMSG unknown limit\nCANARYWORDError: x\n")
    run = run_folder(failed=("02.3-graph",), files={"02.3-graph.notes.txt": stderr})
    got = F.load(run)
    assert got.notes["02.3-graph"] == []
    assert got.errors == {"02.3-graph": ("ValueError", None)}  # a step that finished has no entry


def test_a_step_that_finished_keeps_only_the_lines_it_wrote_as_its_own_notes(run_folder):
    run = run_folder(files={"02.4-phrases.notes.txt": "warning: a library says unknown limit\nnote: skipped: x\n"
                                                      "note: not scanned: a.md: binary\n  note: indented, so not a note\nplain unknown\n"})
    assert F.load(run).notes["02.4-phrases"] == ["skipped: x", "not scanned: a.md: binary"]


def test_the_reads_an_earlier_command_chose_and_continue_left_out_are_in_the_facts(run_folder):
    run = run_folder(dropped=["04-pinpoint", "03-sweep", "05-qa", "nonsense"],
                     backends={"03-sweep": "jev", "04-pinpoint": ["not", "text"]})
    got = F.load(run)
    assert got.dropped == ["03-sweep", "04-pinpoint"]  # in the list's order, and only reads
    assert got.backends == {"03-sweep": "jev"}  # a backend is text


def test_a_run_without_dropped_reads_has_none(facts):
    assert facts().dropped == [] and facts().backends == {}
