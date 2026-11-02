"""Tests for earlier_steps.py, written from specs/shared.SPEC.md, earlier_steps. Fake runners print canned
reports and log the arguments they were given."""
import json
import sys

import pytest

import earlier_steps
import stagelist

READS_5 = ["02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases", "02.5-capability"]

FAKE = r'''
import json, sys
from pathlib import Path
name = {name!r}
args = sys.argv[1:]
with Path({log!r}).open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({{"stage": name, "args": args}}) + "\n")
if "--out" in args:
    out = Path(args[args.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(json.dumps({{"nodes": [], "edges": [], "fake": True}}))
if {fail!r} == name:
    sys.stderr.write("boom")
    sys.exit(3)
if {nojson!r} == name:
    print("not json")
else:
    print(json.dumps({{"stage": name, "contract": 1, "findings": []}}))
'''


def make_stages(root, log, fail=None, nojson=None, reads=None):
    """A stages/ folder with five runners under 02-coded/ and a stages.json naming them; the last
    stage (02.6-builder) reads the five before it, as the real list says."""
    listed = []
    for name in [*READS_5, "02.6-builder"]:
        folder = f"02-coded/{name}"
        d = root / folder
        d.mkdir(parents=True)
        (d / "run.py").write_text(FAKE.format(name=name, log=str(log), fail=fail, nojson=nojson), "utf-8")
        entry = {"name": name, "folder": folder}
        if name == "02.6-builder":
            entry["reads"] = READS_5 if reads is None else reads
        listed.append(entry)
    (root / "stages.json").write_text(json.dumps({"stages": listed, "report": {
        "name": "06-report", "folder": "06-report"}}), "utf-8")
    return root


def calls_of(log):
    return [json.loads(line) for line in log.read_text("utf-8").splitlines()]


def test_the_steps_run_in_order_with_the_arguments_a_stage_on_its_own_always_gave_them(tmp_path):
    log = tmp_path / "log.jsonl"
    stages = make_stages(tmp_path / "stages", log)
    inp, work = tmp_path / "in", tmp_path / "work"
    inp.mkdir()
    work.mkdir()
    got = earlier_steps.run_before("02.6-builder", inp, work, sys.executable, stages)
    assert list(got) == READS_5 and all(r["contract"] == 1 for r in got.values())
    calls = calls_of(log)
    assert [c["stage"] for c in calls] == READS_5
    inv, i, w = str(work / "02.1-inventory.json"), str(inp), str(work)
    assert [c["args"] for c in calls] == [
        [i],                                        # inventory
        [i],                                        # reader: no --out, so no text copy
        [i, "--inventory", inv, "--out", w],        # graph: its graph.json is read by later steps
        [i, "--inventory", inv],                    # phrases: no --out, no --normalized
        [i, "--reports", w]]                        # capability: reads the saved reports, writes no file
    assert json.loads((work / "graph.json").read_text("utf-8"))["fake"] is True
    for name in READS_5:
        assert json.loads((work / f"{name}.json").read_text("utf-8"))["stage"] == name


def test_a_stage_reads_what_stages_json_says_and_nothing_else(tmp_path):
    log = tmp_path / "log.jsonl"
    stages = make_stages(tmp_path / "stages", log, reads=["02.1-inventory", "02.4-phrases"])
    work = tmp_path / "work"
    work.mkdir()
    got = earlier_steps.run_before("02.6-builder", tmp_path, work, sys.executable, stages)
    assert list(got) == ["02.1-inventory", "02.4-phrases"]
    assert [c["stage"] for c in calls_of(log)] == ["02.1-inventory", "02.4-phrases"]
    assert earlier_steps.run_before("02.1-inventory", tmp_path, work, sys.executable, stages) == {}  # reads none


def test_runners_are_found_through_stages_json(tmp_path):
    stages = make_stages(tmp_path / "stages", tmp_path / "log")
    assert stagelist.stage_folder("02.3-graph", stages) == "02-coded/02.3-graph"
    with pytest.raises(KeyError, match="not in"):
        stagelist.stage_folder("99-none", stages)


def test_a_failing_step_raises_step_failed_naming_it_and_the_rest_do_not_run(tmp_path):
    log = tmp_path / "log.jsonl"
    stages = make_stages(tmp_path / "stages", log, fail="02.2-reader")
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(earlier_steps.StepFailed, match="02.2-reader failed") as exc:
        earlier_steps.run_before("02.6-builder", tmp_path, work, sys.executable, stages)
    assert "exit 3" in str(exc.value) and "boom" in str(exc.value)  # run alone, it gives the end of its stderr (no record)
    assert [c["stage"] for c in calls_of(log)] == ["02.1-inventory", "02.2-reader"]


def test_a_step_that_prints_no_valid_report_is_a_failure(tmp_path):
    stages = make_stages(tmp_path / "stages", tmp_path / "log", nojson="02.1-inventory")
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(earlier_steps.StepFailed, match="02.1-inventory failed"):
        earlier_steps.run_before("02.6-builder", tmp_path, work, sys.executable, stages)


def test_inventory_reads_a_saved_report_or_runs_the_step(tmp_path):
    log = tmp_path / "log.jsonl"
    stages = make_stages(tmp_path / "stages", log, reads=["02.1-inventory"])
    saved = tmp_path / "inv.json"
    saved.write_text(json.dumps({"stage": "02.1-inventory", "contract": 1, "findings": ["saved"]}), "utf-8")
    assert earlier_steps.inventory("02.6-builder", tmp_path, saved)["findings"] == ["saved"]
    assert not log.exists()  # a saved report runs nothing
    with pytest.raises(ValueError, match="cannot read --inventory"):
        earlier_steps.inventory("02.6-builder", tmp_path, tmp_path / "missing.json")
    # no saved report: the step runs, in a folder that is removed afterwards
    got = earlier_steps.inventory("02.6-builder", tmp_path, None, stages_dir=stages)
    assert got["stage"] == "02.1-inventory" and [c["stage"] for c in calls_of(log)] == ["02.1-inventory"]


def test_the_real_list_gives_each_stage_the_steps_it_ran_on_its_own_before():
    """The grader grades each stage on its own; the steps it reads must be exactly the ones the five
    copies ran, or its results would move (restructure step 7, notes O4)."""
    reads = stagelist.reads
    assert reads("02.3-graph") == reads("02.4-phrases") == ("02.1-inventory",)
    assert reads("02.5-capability") == tuple(READS_5[:4])
    assert reads("02.6-builder") == tuple(READS_5)
    assert reads("03-sweep") == ("02.1-inventory", "02.4-phrases")
    assert reads("02.1-inventory") == reads("02.2-reader") == ()
    names = stagelist.STAGES
    for s in stagelist.load_stage_list()["stages"]:  # a stage reads only what runs before it
        assert all(names.index(r) < names.index(s["name"]) for r in s.get("reads", ())), s["name"]
