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


def _root(tmp_path):
    for d in ("stages/01-inventory", "grader", "Fixtures/01-inventory"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "stages/01-inventory/run.py").write_text("x = 1\n")
    (tmp_path / "Fixtures/01-inventory/a.md").write_text("fixture\n")
    return tmp_path


def test_fingerprint_changes_with_code_fixtures_and_soft_choices(tmp_path):
    import validate
    root = _root(tmp_path)
    a = validate.fingerprint(root)
    assert a == validate.fingerprint(root, {"PATH": "x"})  # unrelated env ignored
    assert a != validate.fingerprint(root, {"WALKDOWN_SOFT_LABEL": "jev"})
    (root / "Fixtures/01-inventory/a.md").write_text("changed\n")
    b = validate.fingerprint(root)
    assert b != a
    (root / "stages/01-inventory/run.py").write_text("x = 2\n")
    assert validate.fingerprint(root) != b


def test_fingerprint_changes_when_an_optional_tool_appears(tmp_path, monkeypatch):
    import validate
    root = _root(tmp_path)
    monkeypatch.setattr(validate, "optional_tools", lambda: "tesseract=0")
    a = validate.fingerprint(root)
    monkeypatch.setattr(validate, "optional_tools", lambda: "tesseract=1")
    assert validate.fingerprint(root) != a


def test_cached_stamp_is_reused_and_says_so(tmp_path):
    import json
    import sys
    import validate
    root = _root(tmp_path)
    fp = validate.fingerprint(root)
    (root / ".cache").mkdir()
    (root / ".cache/stamps.json").write_text(json.dumps({f"01-inventory|{fp}": {
        "result": "PASS", "gate": "3/3", "negative": "1/1", "recall": None, "skipped": [],
        "date": "2026-10-03"}}))
    # no grader.py exists here: a cache miss would give ERROR
    got = validate.stamps(root, sys.executable, ["01-inventory"])["01-inventory"]
    assert got.result == "PASS" and got.cached == "2026-10-03"
    assert "measured 2026-10-03, same code and fixtures" in got.text
    fresh = validate.stamps(root, sys.executable, ["01-inventory"], cache=False)["01-inventory"]
    assert fresh.result == "ERROR" and fresh.cached is None
