"""Tests for upstream.py, written from specs/shared.SPEC.md, upstream."""
import json

import pytest

import upstream

NAMES = ("02.1-inventory", "03-sweep", "02.4-phrases")


def rep(name, findings=()):
    return {"stage": name, "contract": 1, "findings": list(findings)}


def write_reports(d, names=NAMES):
    d.mkdir(parents=True, exist_ok=True)
    for n in names:
        (d / f"{n}.json").write_text(json.dumps(rep(n)), "utf-8")
    return d


def test_load_dir_returns_the_reports_keyed_by_the_names_given(tmp_path):
    r = upstream.load_dir(write_reports(tmp_path / "r"), NAMES)
    assert sorted(r) == sorted(NAMES) and r["03-sweep"]["stage"] == "03-sweep"


def test_a_missing_report_raises_unless_it_is_not_required(tmp_path):
    d = write_reports(tmp_path / "r", ("02.1-inventory", "02.4-phrases"))
    with pytest.raises(upstream.ReportError, match="03-sweep"):
        upstream.load_dir(d, NAMES)
    r = upstream.load_dir(d, NAMES, required=("02.1-inventory", "02.4-phrases"))
    assert sorted(r) == ["02.1-inventory", "02.4-phrases"]


def test_a_wrong_stage_a_wrong_contract_or_no_findings_list_raises(tmp_path):
    d = write_reports(tmp_path / "r")
    (d / "02.4-phrases.json").write_text(json.dumps(
        {"stage": "02.3-graph", "contract": 1, "findings": []}), "utf-8")
    with pytest.raises(upstream.ReportError, match="02.4-phrases"):
        upstream.load_dir(d, NAMES)
    d2 = write_reports(tmp_path / "r2")
    (d2 / "03-sweep.json").write_text(json.dumps(
        {"stage": "03-sweep", "contract": 2, "findings": []}), "utf-8")
    with pytest.raises(upstream.ReportError, match="contract"):
        upstream.load_dir(d2, NAMES)
    d3 = write_reports(tmp_path / "r3")
    (d3 / "03-sweep.json").write_text(json.dumps({"stage": "03-sweep", "contract": 1}), "utf-8")
    with pytest.raises(upstream.ReportError, match="findings"):
        upstream.load_dir(d3, NAMES)


def test_a_file_that_is_not_json_raises(tmp_path):
    d = write_reports(tmp_path / "r")
    (d / "03-sweep.json").write_text("{not json", "utf-8")
    with pytest.raises(upstream.ReportError, match="cannot read"):
        upstream.load_dir(d, NAMES)


def test_skips_lists_the_skipped_findings_with_their_stage():
    reports = {"02.1-inventory": {"findings": [{"check": "read.divergence", "skipped": "no tesseract"}]},
               "02.4-phrases": {"findings": [{"check": "phrase.x"}]}}
    assert upstream.skips(reports) == [("02.1-inventory", {"check": "read.divergence",
                                                           "skipped": "no tesseract"})]
