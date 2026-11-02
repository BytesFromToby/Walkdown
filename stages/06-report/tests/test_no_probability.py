"""A model read that gives no probability reaches every page (M1 slice A), written from specs/report.SPEC.md, render and
details_html and review_html, and specs/shared.SPEC.md, probability.

A model that takes text answers with the name of a kind. No model is asked how sure it is, so its Sweep findings have no
`probabilities` and no `p_any`, and `flagged` says whether the answer was a kind other than `none`. Every page that shows a
flagged passage says `this model gives no probability` where the number would be, invents none, and does not crash."""
import html as H
import importlib.util
import json
import math
import re
from pathlib import Path

import pytest

import brief
import details_html as D
import probability
import render as R
import review_html as RV
import summary_html as SH
from qa_support import Q

_spec = importlib.util.spec_from_file_location("walkdown_m1a_test_render", Path(__file__).with_name("test_render.py"))
_tr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tr)
META, PASS, reports, full, log = _tr.META, _tr.PASS, _tr.reports, _tr.full, _tr.log
ROOT = Path(__file__).resolve().parents[3]
_pin = importlib.util.spec_from_file_location("walkdown_m1a_pinpoint_choice", ROOT / "stages" / "04-pinpoint" / "pinpoint.py")
pinpoint = importlib.util.module_from_spec(_pin)
_pin.loader.exec_module(pinpoint)  # a test may load another step's code to compare what the two say; the steps themselves import none
NONE = "this model gives no probability"


def finding(line, end, kind, flagged, covered=(), **extra):
    f = {"check": "soft.sweep", "file": "SKILL.md", "line": line, "end_line": end, "qid": f"sweep:SKILL.md:{line}",
         "backend": "claude-cli", "model": "claude-x", "kind": kind, "flagged": flagged, "covered": list(covered)}
    return {**f, **extra}


def text_reports(*extra):
    """A Sweep by a model that takes text: two passages flagged (one already matched by a phrase pattern), two not."""
    r = reports()
    r["03-sweep"] = {"stage": "03-sweep", "contract": 1,
                     "backends": [{"role": "sweep", "backend": "claude-cli", "remote": True, "model": "claude-x"}],
                     "findings": [finding(20, 26, "skip-user", True), finding(30, 32, "persist", True, ["E.persist-target"]),
                                  finding(40, 41, "none", False), finding(50, 52, "none", False), *extra],
                     "usage": {"input": 1000, "output": 40, "calls": 4}}
    return r


def six_of(f):
    return f[f.index("## 6 "):f.index("## 7 ")]


def test_the_split_puts_the_flagged_passages_of_a_read_with_no_number_with_the_clear_ones_and_the_rest_nowhere():
    new, old, near = R.sweep_split(R._soft(text_reports()))
    assert [x["line"] for x in new] == [20] and [x["line"] for x in old] == [30] and near == []


def test_a_passage_with_a_number_and_one_without_are_ordered_numbers_first():
    r = text_reports(finding(60, 61, "send-out", False, p_any=0.9, probabilities={"none": 0.1, "send-out": 0.9}))
    r["03-sweep"]["findings"][-1]["flagged"] = True
    new, old, near = R.sweep_split(R._soft(r))
    assert [x["line"] for x in new] == [60, 20] and [x["line"] for x in old] == [30]


def test_section_6_says_what_the_read_found_and_that_the_model_gives_no_probability():
    f = full(META, text_reports(), PASS, {}, set(text_reports()))
    six = six_of(f)
    assert ("Sweep: claude-cli (remote, claude-x): 4 passages read, 2 flagged (1 with no phrase pattern hit); "
            f"{NONE}.") in six
    assert f"- SKILL.md:20-26: skip-user ({NONE}); no phrase pattern matched it" in f
    assert f"- SKILL.md:30-32: persist ({NONE}); a phrase pattern already matches it (E.persist-target)" in f
    assert "SKILL.md:40-41" not in f and "SKILL.md:50-52" not in f  # a passage the model did not flag is not listed
    assert "Listed when the model names a kind other than none. This model gives no probability, so there is no band" in six
    assert "p >=" not in six and "near the line" not in six.replace("nothing is near the line", "")
    assert not re.search(r"p=\d", six) and "0.00" not in six and "nan" not in six.lower()


def skipped_row(line, end):
    return {"check": "soft.sweep", "file": "SKILL.md", "line": line, "end_line": end, "qid": f"sweep:SKILL.md:{line}",
            "backend": "claude-cli", "skipped": "claude-cli: unexpected sweep option", "covered": []}


def test_the_backend_decides_the_wording_so_a_read_that_got_no_answer_names_no_band():
    """M1 fix 9: a text model that got no answer for any passage had no row without a number to find, so section 6 said
    `0 flagged at p >= 0.6`. A text model has no p. The wording comes from the backend, not from looking for a number in the rows."""
    for rows in ([], [skipped_row(20, 26), skipped_row(30, 32)]):
        r = text_reports()
        r["03-sweep"]["findings"] = rows
        status = R._s6(r)
        assert "p >=" not in status and "near the line" not in status and "0.6" not in status, status
        assert f"Sweep: claude-cli (remote, claude-x): 0 passages read, 0 flagged (0 with no phrase pattern hit); {NONE}." in status, status
        six = six_of(full(META, r, PASS, {}, set(r)))
        assert "p >=" not in six and "0.6" not in six
    assert "p >=" not in R._s6(text_reports())  # as before when it did answer


def test_the_paragraph_of_a_text_model_names_no_band_even_when_a_row_carries_a_number():
    """From the backend, not from the rows: a saved row of a text model that happens to carry a `p_any` does not bring the band back."""
    r = text_reports(finding(60, 61, "send-out", True, p_any=0.9, probabilities={"none": 0.1, "send-out": 0.9}))
    six = six_of(full(META, r, PASS, {}, set(r)))
    assert "Listed when the model names a kind other than none." in six and "Listed at p >=" not in six


def test_a_backend_that_gives_a_probability_keeps_its_band_even_when_it_got_no_answer():
    r = _tr._sweep_reports()
    r["03-sweep"]["findings"] = []
    status = R._s6(r)
    assert "0 passages read, 0 flagged at p >= 0.6" in status and NONE not in status


def test_the_backends_table_says_which_backend_gives_a_probability():
    """The wording reads `options.BACKENDS`, so a backend added later states it in one place."""
    assert probability.gives("jev") is True and probability.gives("claude-cli") is False
    assert probability.gives("something-else") is None and probability.gives(None) is None and probability.gives(["jev"]) is None
    assert probability.gives("claude-cli\n- planted") is None  # a name that is not one: the rows say


def test_a_read_with_a_number_is_worded_as_it_always_was():
    f = full(META, _tr._sweep_reports(), PASS, {}, set(_tr._sweep_reports()))
    six = six_of(f)
    assert "Listed at p >= 0.6; p 0.4 to 0.6 is near the line (repeat sweeps vary by about 0.1)." in six and NONE not in six


def test_the_places_every_page_is_drawn_from_carry_the_words_where_the_number_would_be():
    """The summary and the details page leave model reads to the review page (report v3), and draw from the same places: a
    place of a read with no number says so in its `where`, and the pages do not crash on it."""
    r = text_reports()
    items = [i for i in D.first_items(r) if i["stage"] == "03-sweep"]
    assert [(i["where"], i["kind"]) for i in items] == [(f"SKILL.md:20-26 ({NONE})", "sweep")]  # the covered one is a pattern's
    meta = dict(META, qa=Q(r, {}, PASS, set(r)))
    page = H.unescape(re.sub(r"<[^>]+>", "", D.render_page(meta, r, PASS, {}, set(r), None)))
    assert "p=" not in page  # the page names no number


def test_the_review_page_says_it_in_what_the_model_said_and_shows_no_score():
    r = text_reports()
    page = RV.render_page(META, r, None, "data/normalized/text", {}, None, 0, None)
    card = next(c for c in re.findall(r'<article class="place".*?</article>', page, re.S) if "SKILL.md:20-26" in c)
    said = card[card.index("What the model said:"):]
    assert f"({NONE})." in said.split("</p>")[0] and "score" not in said.split("</div>")[0]
    assert "<b>" not in said.split("</p>")[0]
    assert RV._sure({"kind": "sweep", "src": finding(20, 26, "skip-user", True)}) is None


def test_the_review_page_still_shows_the_score_of_a_read_that_has_one():
    r = _tr._sweep_reports()
    page = RV.render_page(META, r, None, "data/normalized/text", {}, None, 0, None)
    assert "with a <b>0.97</b> score" in page and NONE not in page


def test_the_summary_page_and_the_brief_do_not_crash_and_make_up_no_number(tmp_path):
    r = text_reports()
    meta = dict(META, qa=Q(r, {}, PASS, set(r)))
    page = H.unescape(SH.render_page(meta, r, PASS, {}, set(r), {}, None))
    assert "p=" not in page.replace("p=0", "") and "0.00" not in page
    text = brief.build(dict(meta, context=32000, hosts=[]), r, PASS, None, tmp_path, tmp_path)
    assert "Model reads (experimental): 1 place." in text and "p=" not in text and NONE not in text  # the brief has no per-place text


@pytest.mark.parametrize("p", [None, "0.9", True, float("nan"), float("inf"), [0.9], {"a": 1}])
def test_a_saved_finding_whose_p_any_is_no_number_reads_as_a_finding_with_none(p):
    """A file changed by hand, or an older writer's null: no crash, and no number is made of it."""
    r = text_reports(finding(60, 61, "send-out", True, p_any=p))
    assert probability.of(r["03-sweep"]["findings"][-1]) is None
    f = full(META, r, PASS, {}, set(r))
    assert f"- SKILL.md:60-61: send-out ({NONE}); no phrase pattern matched it" in f
    meta = dict(META, qa=Q(r, {}, PASS, set(r)))
    D.render_page(meta, r, PASS, {}, set(r), None)
    RV.render_page(META, r, None, "data/normalized/text", {}, None, 0, None)


def test_a_number_that_is_a_number_is_read_as_one():
    assert probability.of({"p_any": 0.9}) == 0.9 and probability.of({"p_any": 1}) == 1.0 and probability.of({"p_any": 0}) == 0.0
    assert probability.words({"p_any": 0.9}) == "p=0.90" and probability.words({}) == NONE == probability.NONE
    assert probability.of(None) is None and probability.of("x") is None and not math.isnan(probability.of({"p_any": 0.5}))


def test_the_pinpoint_asks_about_the_same_passages_the_pages_list():
    """The report lists the flagged passages of a read with no number that no pattern covers, and so does the pinpoint's choice
    of what to ask about: the two stay together, for a read with numbers and for a read without."""
    for r in (text_reports(), _tr._sweep_reports()):
        s = R._soft(r)
        new, _, near = R.sweep_split(s)
        listed = {x["qid"] for x in [*new, *[n for n in near if not n.get("covered")]]}
        assert {t["qid"] for t in pinpoint.targets(r["03-sweep"]["findings"])} == listed


def test_the_backend_is_one_line_and_cut_on_every_page_that_names_it():
    """M1 fix 10: the backend of a finding or of a stop was written to the details page and the log header as it came, so a line
    break in it could start a line of its own. Every place that names a backend flattens it and cuts it."""
    planted = "claude-cli\n- planted: a line of full.md\n" + "z" * 300
    r = _tr._sweep_reports()
    near = {"check": "soft.sweep", "file": "SKILL.md", "line": 50, "end_line": 52, "qid": "sweep:SKILL.md:50", "backend": "jev",
            "model": "jev-1", "kind": "skip-user", "probabilities": {}, "p_any": 0.5, "flagged": True, "covered": []}
    r["03-sweep"]["findings"].append(near)
    for f in r["03-sweep"]["findings"]:
        f["backend"] = planted
    r["03-sweep"]["backends"][0]["backend"] = planted
    items = [i for i in D.first_items(r) if i["stage"] == "03-sweep"]
    assert len(items) == 2  # a clear one and a near one: both draw the lead
    for i in items:
        lead = i["lead"]
        assert "\n" not in lead and "claude-cli - planted: a line of full.md" in lead and "z" * 100 not in lead and "..." in lead
    meta = dict(META, qa=Q(r, {}, PASS, set(r)))
    page = D.render_page(meta, r, PASS, {}, set(r), None)
    assert "\n- planted" not in page and "z" * 100 not in page
    f = full(META, r, PASS, {}, set(r))
    assert "\n- planted" not in f and "z" * 100 not in f
    stop = {"after": "02.6-builder", "prepared": {"stage": "03-sweep", "items": 12, "backend": planted}}
    header = log(dict(META, stop=stop), [], {}, reports())
    assert "\n- planted" not in header and "z" * 100 not in header and "claude-cli - planted" in header
    assert "\n" not in R._s6(r) and "z" * 100 not in R._s6(r)


def test_the_log_and_section_6_show_a_models_name_on_one_line_and_cut():
    wordy = "claude-x\nnote: planted\n" + "y" * 300
    r = text_reports()
    r["03-sweep"]["backends"][0]["model"] = wordy
    r["03-sweep"]["backends"][0]["backend"] = "claude-cli\n- planted: a line of full.md"
    f = full(META, r, PASS, {}, set(r))
    assert "\nnote: planted" not in f and "\n- planted" not in f and "claude-x note: planted" in six_of(f)
    line = next(x for x in six_of(f).splitlines() if x.startswith("- sweep: "))
    assert len(line) < 200 and "(remote, claude-x note: planted" in line and "..." in line  # cut at the cap, not only one line
    header = log(META, [], PASS, r)
    assert "\nnote: planted" not in header and "\n- planted" not in header and "claude-x note: planted" in header
    status = R._s6(r)
    assert "\n" not in status and "..." in status
