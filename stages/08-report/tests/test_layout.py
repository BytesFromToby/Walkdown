"""Tests for layout.py, written from specs/layout.SPEC.md."""
import layout


def test_both_layouts(tmp_path):
    old, new = tmp_path / "old", tmp_path / "new"
    old.mkdir()
    (new / "data").mkdir(parents=True)
    assert not layout.is_new(old) and layout.is_new(new)
    assert layout.data_dir(old) == old and layout.report_dir(old) == old / "report"
    assert layout.data_dir(new) == new / "data" and layout.report_dir(new) == new
