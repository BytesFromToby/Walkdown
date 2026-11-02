"""Tests for coverlines.py, written from specs/shared.SPEC.md, coverlines."""
import pytest

import coverlines as cov
import pipeline

LINES = [(("a.one", "a.two"), "files"), (("a.three",), "entries")]


@pytest.fixture(autouse=True)
def nothing_is_left_counting():
    cov.end()
    yield
    cov.end()


def test_a_line_counts_what_a_check_is_to_look_at_what_it_handled_and_what_is_explained():
    cov.begin(LINES)
    cov.of("a.one", 5)
    cov.look("a.one", 3)
    cov.look("a.one")
    cov.explain("a.one")
    cov.of("a.three", 2)
    findings = [{"check": "a.one"}, {"check": "a.two"}, {"check": "a.two", "skipped": "no tool"}, {"check": "a.three"}]
    assert cov.lines(findings) == [
        {"checks": ["a.one", "a.two"], "unit": "files", "of": 5, "looked_at": 4, "explained": 1, "found": 2},
        {"checks": ["a.three"], "unit": "entries", "of": 2, "looked_at": 0, "explained": 0, "found": 1}]  # a skip is no result


def test_nothing_is_counted_while_no_step_has_begun_and_a_key_that_is_not_a_line_counts_nothing():
    cov.look("a.one")
    cov.of("a.one", 3)
    cov.explain("a.one")
    assert cov.lines([]) == []
    cov.begin(LINES)
    cov.look("b.other")  # a function shared with another step
    assert cov.lines([])[0]["looked_at"] == 0


def test_the_lines_end_the_counting_so_the_next_step_starts_from_nothing():
    cov.begin(LINES)
    cov.look("a.one")
    assert cov.lines([])[0]["looked_at"] == 1
    assert cov.lines([]) == []
    cov.begin(LINES)
    assert cov.lines([])[0]["looked_at"] == 0


def test_program_uses_are_a_unit():
    assert "uses" in cov.UNITS and cov.valid([{"checks": ["a.one"], "unit": "uses", "of": 3, "looked_at": 3, "explained": 0,
                                               "found": 0}])
    cov.begin([(("a.one",), "uses")])
    assert cov.lines([])[0]["unit"] == "uses"


def test_a_line_needs_checks_and_a_known_unit():
    with pytest.raises(ValueError):
        cov.begin([(("a.one",), "pages")])
    with pytest.raises(ValueError):
        cov.begin([((), "files")])


def line(**kw):
    return {"checks": ["a.one"], "unit": "files", "of": 3, "looked_at": 3, "explained": 0, "found": 0, **kw}


def test_a_saved_list_is_valid_only_when_it_is_a_list_of_lines_with_whole_counts():
    assert cov.valid([]) and cov.valid([line()]) and cov.valid([line(of=0, looked_at=0)])
    for bad in ("x", 3, None, {"files": 3}, [1], [{}], [line(checks=[])], [line(checks="a.one")], [line(checks=[1])],
                [line(unit=None)], [line(of=2.5)], [line(of=True)], [line(looked_at=-1)], [line(found="1")],
                [{k: v for k, v in line().items() if k != "explained"}]):
        assert not cov.valid(bad), bad


def test_pipeline_reads_a_report_with_a_bad_coverage_as_one_that_cannot_be_read(tmp_path):
    import json
    base = {"stage": "02.1-inventory", "contract": 1, "findings": []}
    path = tmp_path / "r.json"
    for body, ok in (({}, True), ({"coverage": [line()]}, True), ({"coverage": {"files": 3}}, True),  # the old reader's object
                     ({"coverage": "all"}, False), ({"coverage": None}, False), ({"coverage": [line(of=1.5)]}, False)):
        path.write_text(json.dumps({**base, **body}), encoding="utf-8")
        if ok:
            assert pipeline.read_report(path)["stage"] == "02.1-inventory"
        else:
            with pytest.raises(ValueError):
                pipeline.read_report(path)
    assert cov.saved_lines({"coverage": {"files": 3}}) == [] and cov.saved_lines({}) == [] and cov.saved_lines(None) == []
    assert cov.saved_lines({"coverage": [line()]}) == [line()]


def test_problems_says_what_is_wrong_with_the_coverage_of_a_step_that_went_well():
    checks = ["a.one", "a.two", "a.three"]
    whole = {"findings": [{"check": "a.one"}], "coverage": [line(checks=["a.one", "a.two"], found=1),
                                                            line(checks=["a.three"], of=2, looked_at=1, explained=1)]}
    assert cov.problems(checks, whole) == []
    short = {"findings": [], "coverage": [line(checks=["a.one", "a.two"], looked_at=2), line(checks=["a.three"])]}
    assert cov.problems(checks, short) == ["line for a.one: looked_at 2 + explained 0 is not of 3"]
    over = {"findings": [], "coverage": [line(checks=checks, looked_at=3, explained=1)]}
    assert cov.problems(checks, over) == ["line for a.one: looked_at 3 + explained 1 is not of 3"]
    assert cov.problems(checks, {"findings": [], "coverage": [line(checks=["a.one"])]}) == [
        "a.two has no line", "a.three has no line"]
    # an id that is not on the step's list, another step's id, and an id two lines name
    assert cov.problems(checks, {"findings": [], "coverage": [line(checks=checks + ["x.y"])]}) == [
        "line for a.one: x.y is not on the step's list or is named by two lines"]
    assert cov.problems(checks, {"findings": [], "coverage": [line(checks=checks), line(checks=["a.one"])]}) == [
        "line for a.one: a.one is not on the step's list or is named by two lines",
        "line for a.one: a.one is not on the step's list or is named by two lines"]
    assert cov.problems(checks, {"findings": [{"check": "a.one"}], "coverage": [line(checks=checks, found=0)]}) == [
        "line for a.one: found 0 is not the results among the findings of its checks"]
    assert cov.problems(checks, {"findings": []}) == ["coverage is not a list of lines"]
    assert cov.problems(checks, {"findings": [], "coverage": [line(checks=checks, unit="pages")]}) == [
        "coverage is not a list of lines"]  # a unit nobody knows is a line that cannot be read


def test_a_finding_whose_check_is_not_on_the_steps_list_is_a_problem_a_skip_too():
    checks = ["a.one"]
    report = {"findings": [{"check": "a.one"}, {"check": "a.zzz"}, {"check": "a.yyy", "skipped": "no tool"}],
              "coverage": [line(checks=checks, found=1)]}
    assert cov.problems(checks, report) == [
        "a.zzz is the check of a finding and is not on the step's list",
        "a.yyy is the check of a finding and is not on the step's list"]
    assert cov.audit(checks, report)["off_list"] == ["a.zzz", "a.yyy"]


def test_an_id_with_white_space_in_it_cannot_start_a_line_of_a_hold():
    assert not cov.valid([line(checks=["a.one\nHoldback: now"])])
    assert not cov.valid([line(checks=[" a.one"])]) and not cov.valid([line(checks=[""])])
    report = {"findings": [{"check": "a.one\nthen words"}], "coverage": [line(checks=["a.one"])]}
    assert cov.audit(["a.one"], report)["off_list"] == [cov.UNNAMED]  # shown by a placeholder


def test_found_is_the_results_of_a_check_and_for_a_model_read_the_flags():
    assert cov.found_in(["a.one"], [{"check": "a.one"}, {"check": "a.one", "skipped": "x"}, {"check": "b"}]) == 1
    sweep = [{"check": "soft.sweep", "flagged": True}, {"check": "soft.sweep", "flagged": False},
             {"check": "soft.sweep", "skipped": "no answer"}]
    assert cov.found_in(["soft.sweep"], sweep) == 1
    pin = [{"check": "soft.pinpoint", "verified": True}, {"check": "soft.pinpoint", "verified": False}]
    assert cov.found_in(["soft.pinpoint"], pin) == 1
    assert cov.is_result({"check": "a.one"}) and not cov.is_result({"check": "a.one", "skipped": "x"})


def test_the_audit_names_what_is_wrong_as_data_for_the_check_of_the_run():
    checks = ["a.one", "a.two"]
    report = {"findings": [{"check": "a.one"}, {"check": "a.new"}],
              "coverage": [line(checks=["a.one", "b.other"], of=3, looked_at=1, found=0)]}
    got = cov.audit(checks, report)
    assert got["missing"] == ["a.two"] and got["off_list"] == ["a.new"]
    assert got["lines"][0]["reasons"] == ["check", "short", "found"] and got["lines"][0]["ids"] == ["b.other"]


def test_a_step_with_no_checks_has_nothing_to_audit():
    assert cov.audit([], {"findings": [], "coverage": []}) == {"missing": [], "off_list": [], "lines": []}
    assert cov.problems([], {"findings": [], "coverage": []}) == []
