"""Tests for layout.py, written from specs/shared.SPEC.md, layout."""
import layout


def test_one_layout(tmp_path):
    """Restructure step 7 (notes O5): the stage outputs are in data/ and the reports are at the top; there
    is no other place, whether or not data/ exists yet."""
    d = tmp_path / "run"
    d.mkdir()
    assert layout.data_dir(d) == d / "data" and layout.report_dir(d) == d
    (d / "data").mkdir()
    assert layout.data_dir(d) == d / "data" and layout.report_dir(d) == d
    assert not hasattr(layout, "is_new")
    assert layout.REPORTS == ("summary.html", "details.html", "review.html", "full.md")
    assert layout.BRIEF == "brief.md" and layout.LIMITS == "limits.md" and layout.RECORD == "run.json"


def test_the_layout_has_no_rule_for_a_run_made_before_this_version():
    """Restructure step 7b: whether a run was made before this version is the record's to say, by its format
    (`record.made_before`), so there is one rule and the layout holds none."""
    assert not hasattr(layout, "made_before")


def test_which_run_came_before_is_the_records_to_say_and_not_the_layouts():
    """Restructure step 7, round 2: ordering runs needs their times, which are in the record
    (`record.earlier_runs`, `record.previous_run`); the layout only says where things are."""
    assert not hasattr(layout, "earlier_runs") and not hasattr(layout, "previous_run")
