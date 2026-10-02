"""Tests for validate.py, written from specs/validate.SPEC.md."""
import sys

from validate import parse, stamps


def test_pass_stage():
    doc = {"stages": [{"stage": "04-phrases", "result": "PASS", "gate": {"passed": 31, "total": 31},
                       "negative": {"passed": 46, "total": 46}, "recall": {"found": 39, "total": 39},
                       "not_ok": []}]}
    st = parse(doc)["04-phrases"]
    assert st.result == "PASS" and st.gate == "31/31" and st.negative == "46/46" and st.recall == "39/39"
    assert st.text == "PASS (gate 31/31, negative 46/46, recall 39/39)"


def test_incomplete_lists_skips():
    doc = {"stages": [{"stage": "02-reader", "result": "INCOMPLETE", "gate": {"passed": 14, "total": 15},
                       "negative": {"passed": 12, "total": 12}, "recall": {"found": 0, "total": 0},
                       "not_ok": [{"id": "rd-img-ocr", "status": "SKIPPED"},
                                  {"id": "x", "status": "MISS"}]}]}
    st = parse(doc)["02-reader"]
    assert st.skipped == ["rd-img-ocr"] and st.recall is None
    assert "skipped: rd-img-ocr" in st.text and st.text.startswith("INCOMPLETE")


def test_grader_without_json_is_error(tmp_path):
    (tmp_path / "grader").mkdir()
    (tmp_path / "grader" / "grader.py").write_text("print('not json')\n", encoding="utf-8")
    assert stamps(tmp_path, sys.executable, ["01-inventory"])["01-inventory"].result == "ERROR"


def test_long_skip_list_collapses():
    doc = {"stages": [{"stage": "06-soft", "result": "PASS", "gate": {"passed": 1, "total": 1},
                       "negative": {"passed": 1, "total": 1}, "recall": {"found": 0, "total": 5},
                       "not_ok": [{"id": f"r{i}", "status": "SKIPPED"} for i in range(5)]}]}
    assert parse(doc)["06-soft"].text.endswith("skipped: 5 rows)")
