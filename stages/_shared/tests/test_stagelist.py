"""Tests for stagelist.py, written from specs/shared.SPEC.md, stagelist."""
import json
import re
from pathlib import Path

import pytest

import stagelist as SL

STAGES_DIR = Path(__file__).resolve().parents[2]
NAMES = ["01-intake", "02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases", "02.5-capability",
         "02.6-builder", "03-sweep", "04-pinpoint"]


def test_the_list_is_read_from_stages_json_and_the_tables_follow_it():
    doc = json.loads((STAGES_DIR / "stages.json").read_text(encoding="utf-8"))
    assert SL.STAGES == [s["name"] for s in doc["stages"]] == NAMES
    assert SL.INTAKE == "01-intake" and SL.FOLDER_STAGES == NAMES[1:] and SL.REPORT == "06-report"
    assert SL.AI_STAGES == ("03-sweep", "04-pinpoint")
    assert SL.CODED == tuple(NAMES[1:7])  # the coded steps, intake and the AI stages apart
    assert SL.AI_OPTION == {"03-sweep": "sweep", "04-pinpoint": "pinpoint"}
    assert SL.AI_ENV == {"03-sweep": "WALKDOWN_SOFT_SWEEP", "04-pinpoint": "WALKDOWN_SOFT_PINPOINT"}


def test_folders_come_from_the_list_and_every_one_has_its_runner():
    assert SL.stage_folder("01-intake") == "01-intake"
    assert SL.stage_folder("02.4-phrases") == "02-coded/02.4-phrases"
    assert SL.stage_folder("03-sweep") == "03-sweep" and SL.stage_folder("06-report") == "06-report"
    with pytest.raises(KeyError):
        SL.stage_folder("04-phrases")
    for s in [*SL.load_stage_list()["stages"], SL.load_stage_list()["report"]]:
        assert (STAGES_DIR / s["folder"] / "run.py").is_file(), s["name"]


def test_each_stage_a_reader_meets_has_a_plain_name_and_the_sections_have_headings():
    doc = SL.load_stage_list()
    assert list(SL.PLAIN) == NAMES  # intake has one since O3: a stop after it is named by it
    assert SL.PLAIN["01-intake"] == "Getting the copy"
    assert SL.PLAIN["02.6-builder"] == "Builder checks" and SL.PLAIN["04-pinpoint"] == "The line behind each flag"
    # the sections of full.md, in order: the five coded stages with a section, Sweep's, then section 7
    assert list(SL.HEADINGS) == ["02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases",
                                 "02.5-capability", "03-sweep", "07-limits"]
    assert SL.HEADINGS["07-limits"] == doc["report"]["limits_heading"] == "Not examined"
    assert all(SL.HEADINGS[s] == SL.PLAIN[s] for s in SL.HEADINGS if s != SL.LIMITS)
    assert list(SL.PLAIN_WITH_LIMITS) == [*NAMES, "07-limits"]


def test_an_ai_stage_has_an_option_and_a_variable_and_a_coded_stage_has_neither():
    for s in SL.load_stage_list()["stages"]:
        assert ("option" in s) == ("env" in s) == (s["name"] in SL.AI_STAGES)


def test_a_stage_reads_only_what_runs_before_it():
    for s in SL.load_stage_list()["stages"]:
        assert all(SL.STAGES.index(r) < SL.STAGES.index(s["name"]) for r in s.get("reads", ())), s["name"]
    assert SL.reads("02.1-inventory") == ()
    assert SL.reads("04-pinpoint") == ("02.1-inventory", "02.4-phrases", "03-sweep")


def test_position_follows_the_list():
    """A sort by stage uses the stage's place in the list, never a number read out of its name."""
    assert [SL.position(n) for n in NAMES] == list(range(len(NAMES)))
    assert SL.position("02.4-phrases") < SL.position("02.5-capability") < SL.position("03-sweep")
    with pytest.raises(KeyError):
        SL.position("06-report")  # the report stage is not in the list of stages


def test_the_check_of_the_run_is_listed_beside_the_stages_and_not_in_them():
    doc = json.loads((STAGES_DIR / "stages.json").read_text(encoding="utf-8"))
    assert doc["qa"] == {"name": "05-qa", "folder": "05-qa", "plain": "Checking the run",
                         "findings": ["qa.gap", "qa.limit", "qa.checked"]}
    assert SL.QA == "05-qa" and SL.stage_folder(SL.QA) == "05-qa"
    assert SL.QA not in SL.STAGES and SL.QA not in SL.PLAIN  # not a step a run chooses or stops after
    assert (STAGES_DIR / SL.stage_folder(SL.QA) / "run.py").is_file()
    with pytest.raises(KeyError):
        SL.position(SL.QA)


def test_every_step_a_page_can_name_has_its_plain_words_the_check_of_the_run_included():
    assert SL.STEP_WORDS["05-qa"] == "Checking the run"
    assert SL.STEP_WORDS["02.4-phrases"] == SL.PLAIN["02.4-phrases"] == "What the text asks for"
    assert SL.STEP_WORDS["04-pinpoint"] == "The line behind each flag"
    assert SL.STEP_WORDS["07-limits"] == "Not examined"
    assert list(SL.STEP_WORDS) == [*NAMES, "07-limits", "05-qa"]


def test_a_stage_list_without_a_qa_entry_still_gives_the_other_folders(tmp_path):
    """A list written before the check of the run (a test's fake) has no `qa`; the other entries still read."""
    (tmp_path / "stages.json").write_text(json.dumps({"stages": [{"name": "01-intake", "folder": "01-intake"}],
                                                      "report": {"name": "06-report", "folder": "06-report"}}),
                                          encoding="utf-8")
    assert SL.stage_folder("01-intake", tmp_path) == "01-intake" and SL.stage_folder("06-report", tmp_path) == "06-report"
    with pytest.raises(KeyError):
        SL.stage_folder("05-qa", tmp_path)
    (tmp_path / "stages.json").write_text(json.dumps({"stages": [], "qa": {"name": "05-qa", "folder": "elsewhere"},
                                                      "report": {}}), encoding="utf-8")
    assert SL.stage_folder("05-qa", tmp_path) == "elsewhere"


# ---------------------------------------------------------------- the checks a step makes (M9 slice C)

CONTRACT = STAGES_DIR / "CONTRACT.md"
CHECK_ID = re.compile(r"^[a-z]+\.[A-Za-z][\w.-]*$")
AI_CHECK_STEP = {"soft.sweep": "03-sweep", "soft.pinpoint": "04-pinpoint"}  # one section of the contract holds both


def contract_vocabulary() -> dict[str, list[str]]:
    """{step: the check ids `stages/CONTRACT.md` lists for it, in its order}: the first cell of each table row in the
    section whose heading names the step. Intake's and the check of the run's sections are read too, and the test says
    what it does with them."""
    out: dict[str, list[str]] = {}
    section = None
    for line in CONTRACT.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            named = re.findall(r"`(\d\d[\d.]*-[a-z]+)`", line)
            section = named or None
            continue
        if line.startswith("## "):
            section = None
        if section is None or not line.startswith("|"):
            continue
        first = line.split("|")[1]
        for token in re.findall(r"`([^`]+)`", first):
            if CHECK_ID.match(token):
                for step in section:
                    if len(section) == 1 or AI_CHECK_STEP.get(token) == step:
                        out.setdefault(step, []).append(token)
    return out


def test_the_checks_in_stages_json_are_the_checks_the_contract_lists_for_each_step():
    """A step's `checks` in `stages.json` and its section of `stages/CONTRACT.md` hold the same ids in the same order, so
    a check added to one and not the other fails here. The contract also lists intake's (`intake.source`) and the check of
    the run's (`qa.gap`, `qa.limit`, `qa.checked`); neither makes coverage lines, and neither is in the list."""
    vocab = contract_vocabulary()
    listed = {s["name"]: s.get("checks") for s in SL.load_stage_list()["stages"]}
    covered = [s for s in NAMES if s != "01-intake"]
    for step in covered:
        assert listed[step], f"{step} has no checks in stages.json"
        assert listed[step] == vocab[step], step
        assert len(set(listed[step])) == len(listed[step]), f"{step} lists a check twice"
    assert listed["01-intake"] is None and vocab["01-intake"] == ["intake.source"]
    qa = SL.load_stage_list()["qa"]  # the check of the run lists the kinds of its findings and has no checks with coverage lines
    assert list(dict.fromkeys(vocab["05-qa"])) == ["qa.gap", "qa.limit", "qa.checked"] == qa["findings"] and "checks" not in qa
    assert set(vocab) == set(NAMES) | {"05-qa"}  # no section of the contract is missed by this test
    every = [c for step in covered for c in listed[step]]
    assert len(every) == len(set(every)), "a check id is listed under two steps"


def test_the_checks_of_a_step_are_read_from_the_list():
    assert SL.checks("02.1-inventory")[0] == "inv.pin" and SL.checks("03-sweep") == ("soft.sweep",)
    assert SL.checks("01-intake") == () and SL.checks("05-qa") == () and SL.checks("06-report") == ()
    assert list(SL.CHECKS) == NAMES[1:] and SL.CHECKS["04-pinpoint"] == ("soft.pinpoint",)
    with pytest.raises(KeyError):
        SL.checks("04-phrases")
