"""Tests for softdata.py, written from specs/softdata.SPEC.md."""
import pytest
import yaml

import softdata


def test_shipped_file_loads_with_exact_options_and_templates():
    d = softdata.load()
    assert list(d["label"]["options"]) == list(softdata.LABELS)
    assert softdata.LABELS == ("do", "not-to", "description", "example-or-quote", "other-sense")
    for opt in d["label"]["options"].values():
        assert opt["what"] and opt["not_for"] and opt["examples"] and opt["source"]
    assert set(d["relational"]) == set(softdata.RELATIONAL)
    for t in d["relational"].values():
        assert t["question"] and t["source"]
    assert d["claude_system_prompt"]["text"] and d["claude_system_prompt"]["source"]
    assert isinstance(d["answer_cap"], int) and d["answer_cap"] > 0
    assert d["label"]["question"] and d["label"]["source"]


def _write(tmp_path, doc):
    p = tmp_path / "s.yaml"
    p.write_text(yaml.safe_dump(doc), "utf-8")
    return p


def _raw():
    return yaml.safe_load(softdata.DEFAULT.read_text("utf-8"))


def test_missing_option_raises(tmp_path):
    doc = _raw()
    del doc["label"]["options"]["not-to"]
    with pytest.raises(softdata.DataError):
        softdata.load(_write(tmp_path, doc))


def test_missing_template_raises(tmp_path):
    doc = _raw()
    del doc["relational"]["legs"]
    with pytest.raises(softdata.DataError):
        softdata.load(_write(tmp_path, doc))


def test_entry_without_source_raises(tmp_path):
    doc = _raw()
    del doc["relational"]["term.safety"]["source"]
    with pytest.raises(softdata.DataError):
        softdata.load(_write(tmp_path, doc))


def test_option_without_examples_raises(tmp_path):
    doc = _raw()
    doc["label"]["options"]["do"]["examples"] = []
    with pytest.raises(softdata.DataError):
        softdata.load(_write(tmp_path, doc))


def test_missing_file_raises(tmp_path):
    with pytest.raises(softdata.DataError):
        softdata.load(tmp_path / "nope.yaml")


def test_system_prompt_says_quoted_text_is_data():
    text = softdata.load()["claude_system_prompt"]["text"].lower()
    assert "data" in text
    assert "no instructions for you" in text
