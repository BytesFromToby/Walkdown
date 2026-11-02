"""Tests for qaview.py, written from specs/report.SPEC.md, qaview: the report stage's view of `data/05-qa.json`."""
import json

import pytest

import qaview
from qa_support import Q

GAP = {"check": "qa.gap", "kind": "step-missing", "step": "02.3-graph", "why": "failed"}
LIMIT = {"check": "qa.limit", "kind": "standing", "step": None, "id": "static"}


def test_the_file_is_read_into_gaps_and_limits_in_the_order_the_check_made_them(tmp_path):
    doc = {"stage": "05-qa", "contract": 1, "findings": [LIMIT, GAP, {"check": "soft.sweep"}, "not a finding"]}
    (tmp_path / "05-qa.json").write_text(json.dumps(doc), encoding="utf-8")
    qa = qaview.Qa.read(tmp_path)
    assert qa.items == [LIMIT, GAP] and qa.gaps == [GAP] and qa.limits == [LIMIT]  # another stage's finding is none of its
    assert qa.of("step-missing") == [GAP] and qa.steps_missing() == ["02.3-graph"]
    assert qa.reads_with_no_answer() == []


def test_a_file_that_is_missing_or_does_not_read_is_no_check(tmp_path):
    with pytest.raises(qaview.NoCheck, match="05-qa.json is missing or cannot be read"):
        qaview.Qa.read(tmp_path)
    for text in ("not json", "[]", '{"findings": "no"}', '{"stage": "05-qa"}'):
        (tmp_path / "05-qa.json").write_text(text, encoding="utf-8")
        with pytest.raises(qaview.NoCheck):
            qaview.Qa.read(tmp_path)


def test_a_file_that_reads_and_holds_none_of_the_standing_limits_is_empty_and_no_check(tmp_path):
    """The check always ends in the limits that stand for every run; a file without any is not its output."""
    for findings in ([], [GAP], [{"check": "soft.sweep"}]):
        (tmp_path / "05-qa.json").write_text(json.dumps({"stage": "05-qa", "findings": findings}), encoding="utf-8")
        with pytest.raises(qaview.NoCheck, match="05-qa.json is empty"):
            qaview.Qa.read(tmp_path)


def test_a_meta_without_the_check_gets_an_empty_one_and_a_meta_with_it_keeps_it():
    assert qaview.of({}).items == []
    qa = Q({})
    assert qaview.of({"qa": qa}) is qa
