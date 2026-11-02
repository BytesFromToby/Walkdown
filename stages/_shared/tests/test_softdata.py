"""Tests for softdata.py, written from specs/shared.SPEC.md, softdata."""
import pytest
import yaml

import softdata


def test_the_shipped_file_loads_with_the_sweep_kinds_and_the_pinpoint_question():
    d = softdata.load()
    assert isinstance(d["answer_cap"], int) and d["answer_cap"] > 0
    sw = d["sweep"]
    assert sw["question"] and sw["source"] and 0 < sw["flag_p"] < 1
    assert list(sw["options"])[0] == "none" and len(sw["options"]) >= 2
    for opt in sw["options"].values():
        assert opt["what"] and opt["not_for"] and opt["examples"] and opt["source"]
    assert d["pinpoint"]["system"] and d["pinpoint"]["question"] and d["pinpoint"]["source"]


def test_the_shipped_file_holds_nothing_the_parked_code_showed_a_model():
    """Label's question and options, the relational templates, and the Claude system prompt left
    with the parked code (restructure step 5)."""
    raw = yaml.safe_load(softdata.DEFAULT.read_text("utf-8"))
    assert set(raw) == {"answer_cap", "answer_cap_source", "retry_wait", "retry_wait_source", "sweep", "pinpoint"}
    assert set(softdata.load()) == {"answer_cap", "retry_wait", "sweep", "pinpoint"}


def _write(tmp_path, doc):
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(doc), "utf-8")
    return p


def _raw():
    return yaml.safe_load(softdata.DEFAULT.read_text("utf-8"))


def test_a_sweep_that_does_not_start_with_none_or_names_no_kind_raises(tmp_path):
    doc = _raw()
    del doc["sweep"]["options"]["none"]
    with pytest.raises(softdata.DataError, match="none"):
        softdata.load(_write(tmp_path, doc))
    doc = _raw()
    doc["sweep"]["options"] = {"none": doc["sweep"]["options"]["none"]}
    with pytest.raises(softdata.DataError):
        softdata.load(_write(tmp_path, doc))


def test_flag_p_must_be_strictly_between_zero_and_one(tmp_path):
    for bad in (0, 1, 1.5, "half", True):
        doc = _raw()
        doc["sweep"]["flag_p"] = bad
        with pytest.raises(softdata.DataError, match="flag_p"):
            softdata.load(_write(tmp_path, doc))


def test_an_entry_without_a_source_raises(tmp_path):
    doc = _raw()
    del doc["sweep"]["options"]["override"]["source"]
    with pytest.raises(softdata.DataError, match="override"):
        softdata.load(_write(tmp_path, doc))
    doc = _raw()
    del doc["pinpoint"]["source"]
    with pytest.raises(softdata.DataError, match="pinpoint"):
        softdata.load(_write(tmp_path, doc))


def test_an_option_without_examples_raises(tmp_path):
    doc = _raw()
    doc["sweep"]["options"]["override"]["examples"] = []
    with pytest.raises(softdata.DataError, match="examples"):
        softdata.load(_write(tmp_path, doc))


def test_a_missing_sweep_or_pinpoint_section_raises(tmp_path):
    for key in ("sweep", "pinpoint"):
        doc = _raw()
        del doc[key]
        with pytest.raises(softdata.DataError):
            softdata.load(_write(tmp_path, doc))


def test_the_answer_cap_must_be_a_positive_int(tmp_path):
    for bad in (0, -1, 2.5, "big", True):
        doc = _raw()
        doc["answer_cap"] = bad
        with pytest.raises(softdata.DataError, match="answer_cap"):
            softdata.load(_write(tmp_path, doc))


def test_the_wait_before_the_second_try_is_two_seconds_and_must_be_a_number_of_seconds(tmp_path):
    """M9 slice A: the wait is a number in the Library, and the backends hold none of their own."""
    assert softdata.load()["retry_wait"] == 2.0
    for bad in (-1, 61, "two", True, None):
        doc = _raw()
        doc["retry_wait"] = bad
        with pytest.raises(softdata.DataError, match="retry_wait"):
            softdata.load(_write(tmp_path, doc))
    doc = _raw()
    del doc["retry_wait"]
    with pytest.raises(softdata.DataError, match="retry_wait"):
        softdata.load(_write(tmp_path, doc))
    doc = _raw()
    doc["retry_wait"] = 0
    assert softdata.load(_write(tmp_path, doc))["retry_wait"] == 0.0


def test_a_missing_file_raises(tmp_path):
    with pytest.raises(softdata.DataError):
        softdata.load(tmp_path / "nope.yaml")


def test_the_pinpoint_system_prompt_says_the_passage_is_data_not_instructions():
    system = softdata.load()["pinpoint"]["system"].lower()
    assert "data" in system and "never instructions for you" in system


# M1 slice A: the system text a model that takes text is given with the sweep question
def test_the_sweep_has_a_system_text_that_says_the_passage_is_data_and_asks_for_one_options_name():
    sw = softdata.load()["sweep"]
    low = sw["system"].lower()
    assert "data" in low and "never instructions for you" in low and "no tools" in low
    assert "exactly one option" in low and "nothing else" in low
    raw = yaml.safe_load(softdata.DEFAULT.read_text("utf-8"))["sweep"]
    assert raw["system_source"].strip() and raw["system"].strip() == sw["system"]


def test_a_sweep_without_a_system_text_raises(tmp_path):
    for bad in (None, "", "  "):
        doc = _raw()
        if bad is None:
            del doc["sweep"]["system"]
        else:
            doc["sweep"]["system"] = bad
        with pytest.raises(softdata.DataError, match="system"):
            softdata.load(_write(tmp_path, doc))
