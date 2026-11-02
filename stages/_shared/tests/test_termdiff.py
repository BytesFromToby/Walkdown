"""Tests for termdiff.py, written from specs/shared.SPEC.md, termdiff."""
import termdiff


def test_diff():
    old = {"version": "v1", "rows": {"A": "1", "B": "2", "C": "3"}, "vocab": "w", "code": "c1"}
    new = {"version": "v2", "rows": {"A": "1", "B": "9", "D": "4"}, "vocab": "w", "code": "c2"}
    d = termdiff.diff(old, new)
    assert (d["known"], d["same"]) == (True, False)
    assert (d["rows_added"], d["rows_changed"], d["rows_removed"]) == (["D"], ["B"], ["C"])
    assert (d["vocab_changed"], d["code_changed"]) == (False, True)
    assert termdiff.diff(old, dict(old))["same"] is True
    for a, b in ((None, new), (old, None), ({}, new)):
        d = termdiff.diff(a, b)
        assert d["known"] is False and d["rows_added"] == [] and d["code_changed"] is False
