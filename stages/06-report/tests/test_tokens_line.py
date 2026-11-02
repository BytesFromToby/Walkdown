"""The token line and the fixture line (M1 slice A), written from specs/report.SPEC.md, render and brief.

    Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint 1,490 in, 73 out; Sweep's fixture check 39,823 in.
    Sweep on jev: found 33 of 34 in its fixtures.

Both are Walkdown's own words and numbers. The token line is in section 6 of `full.md` and in the brief; a read that does not
report its tokens says `not reported`, and a fixture check reused from an earlier run spent none and says none."""
import importlib.util
import re
from pathlib import Path

import brief
import render as R
from qa_support import Q
from validate import Stamp

_spec = importlib.util.spec_from_file_location("walkdown_m1a_test_render_tokens", Path(__file__).with_name("test_render.py"))
_tr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_tr)
META, PASS, reports, full = _tr.META, _tr.PASS, _tr.reports, _tr.full
LINE = "Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint 1,490 in, 73 out; Sweep's fixture check 39,823 in."


def with_reads(sweep_usage=None, pin_usage=None, pin=True):
    r = _tr._sweep_reports()
    if sweep_usage is not None:
        r["03-sweep"]["usage"] = sweep_usage
    if pin:
        r["04-pinpoint"] = {"stage": "04-pinpoint", "contract": 1, "findings": [],
                            "backends": [{"role": "pinpoint", "backend": "claude-cli", "remote": True, "model": "claude-x"}],
                            **({} if pin_usage is None else {"usage": pin_usage})}
    return r


SWEEP = {"input": 596200, "output": 31464, "calls": 431}
PIN = {"input": 1490, "output": 73, "calls": 5}
FIXTURE = {"input": 39823, "calls": 36}


def stamps(sweep=None, **kw):
    return dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "31/34", usage=sweep, **kw), "04-pinpoint": Stamp("no fixture set")})


def test_the_line_names_each_read_that_ran_and_the_fixture_check_in_the_owners_words():
    assert R.tokens_line(with_reads(SWEEP, PIN), stamps(FIXTURE)) == LINE


def test_a_read_that_does_not_report_its_tokens_says_not_reported():
    r = with_reads(SWEEP, {"calls": 5})
    assert R.tokens_line(r, stamps()) == ("Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint not reported.")
    r = with_reads({"calls": 431}, PIN)
    assert R.tokens_line(r, stamps()) == "Model reads used: Sweep not reported; Pinpoint 1,490 in, 73 out."
    assert "Pinpoint not reported" in R.tokens_line(with_reads(SWEEP, None), stamps())  # a report with no usage block at all


def test_a_fixture_check_that_spent_no_tokens_this_run_is_not_in_the_line():
    """A saved stamp reused this run spends none and says none: its stamp carries no usage. One that sent no call says nothing
    either, and one whose calls reported no token count says `not reported`."""
    assert R.tokens_line(with_reads(SWEEP, PIN), stamps(None, cached="2026-10-30")) == (
        "Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint 1,490 in, 73 out.")
    assert "fixture" not in R.tokens_line(with_reads(SWEEP, PIN), stamps({"calls": 0}))
    assert R.tokens_line(with_reads(SWEEP, PIN), stamps({"calls": 36})).endswith("Sweep's fixture check not reported.")
    assert "fixture" not in R.tokens_line(with_reads(SWEEP, PIN), {k: v for k, v in stamps(FIXTURE).items() if k != "03-sweep"})


def test_a_total_that_only_some_of_the_calls_reported_says_so_in_every_place_it_is_printed(tmp_path):
    """M1 fix 5: nine calls with five reporting is `Sweep 500 in, 15 out (from 5 of 9 calls)`, in the line of the brief, in section 6,
    and for the fixture check; when every call reported the words are as they were, and when none did it is `not reported`."""
    part = {"input": 500, "output": 15, "calls": 9, "reported": 5}
    full_ = {"input": 596200, "output": 31464, "calls": 431, "reported": 431}
    r = with_reads(part, {"input": 1490, "output": 73, "calls": 5, "reported": 5})
    st = stamps({"input": 39823, "calls": 36, "reported": 20})
    line = R.tokens_line(r, st)
    assert line == ("Model reads used: Sweep 500 in, 15 out (from 5 of 9 calls); Pinpoint 1,490 in, 73 out; "
                    "Sweep's fixture check 39,823 in (from 20 of 36 calls).")
    assert R.tokens_line(with_reads(full_, PIN), stamps(FIXTURE)) == LINE  # every call reported, or a block that does not say: as before
    assert R.tokens_line(with_reads(dict(full_), PIN), stamps(dict(FIXTURE, reported=36))) == LINE
    assert R.tokens_line(with_reads({"calls": 9, "reported": 0}, None, pin=False), stamps()) == "Model reads used: Sweep not reported."
    f = full(META, r, st, {}, set(r))
    assert line in f[f.index("## 6 "):f.index("## 7 ")].splitlines()
    text = brief_text(tmp_path, r, st)
    assert f"\n\n{line}\n\n" in text


def test_a_read_that_sent_nothing_says_so():
    assert R.tokens_line(with_reads({"calls": 0}, {"calls": 0}), stamps()) == (
        "Model reads used: Sweep sent nothing; Pinpoint sent nothing.")


def test_cache_tokens_are_named_when_there_are_some():
    r = with_reads({"input": 10, "output": 2, "cache_write": 1200, "cache_read": 300, "calls": 1}, None, pin=False)
    assert R.tokens_line(r, stamps()) == "Model reads used: Sweep 10 in, 2 out, 1,200 cache write, 300 cache read."


def test_a_run_with_no_model_read_has_no_token_line_and_says_what_it_always_said():
    r = reports()
    assert R.tokens_line(r, PASS) is None and R.tokens_line({**r, "03-sweep": None}, PASS) is None  # a read that left no report
    assert "Model reads used" not in full(META, r, PASS, {}, set(r)) and _tr.NO_MODEL in full(META, r, PASS, {}, set(r))


def test_only_the_pinpoint_that_ran_is_named():
    r = with_reads(SWEEP, None, pin=False)
    assert R.tokens_line(r, stamps()) == "Model reads used: Sweep 596,200 in, 31,464 out."


def test_section_6_has_the_line_after_the_validation_and_before_the_findings():
    r = with_reads(SWEEP, PIN)
    f = full(META, r, stamps(FIXTURE), {}, set(r))
    six = f[f.index("## 6 "):f.index("## 7 ")]
    assert LINE in six.splitlines()
    assert six.index("Validation:") < six.index(LINE) < six.index("### Sweep:")


def test_the_brief_has_the_line_in_its_own_paragraph(tmp_path):
    r = with_reads(SWEEP, PIN)
    meta = dict(META, context=32000, hosts=[], qa=Q(r, {}, stamps(FIXTURE), set(r)))
    text = brief.build(meta, r, stamps(FIXTURE), None, tmp_path, tmp_path)
    assert f"\n\n{LINE}\n\n" in text
    assert text.index("Model reads (experimental)") < text.index(LINE)
    assert "SKILL.md" not in LINE and not re.search(r"[A-Za-z]/", LINE)  # numbers and Walkdown's words only


def test_the_brief_has_the_line_for_a_read_that_listed_no_place(tmp_path):
    r = with_reads(SWEEP, None, pin=False)
    r["03-sweep"]["findings"] = []
    meta = dict(META, context=32000, hosts=[], qa=Q(r, {}, stamps(), set(r)))
    text = brief.build(meta, r, stamps(), None, tmp_path, tmp_path)
    assert "Model reads (experimental)" not in text and "\n\nModel reads used: Sweep 596,200 in, 31,464 out.\n\n" in text


# ---------------------------------------------------------------- the fixture line (owner's answer 3)

def brief_text(tmp_path, r, st, **meta):
    m = dict(META, context=32000, hosts=[], qa=Q(r, {}, st, set(r)), **meta)
    return brief.build(m, r, st, None, tmp_path, tmp_path)


def test_the_brief_says_what_sweep_found_in_its_fixtures_under_the_fixture_checks(tmp_path):
    r = with_reads(SWEEP, None, pin=False)
    st = dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "31/34")})
    text = brief_text(tmp_path, r, st)
    assert "Fixture checks: no step failed.\nSweep on jev: found 31 of 34 in its fixtures.\n" in text
    named = brief_text(tmp_path, r, st, backends={"03-sweep": "claude-cli:Some-Model_2"})  # the person's option, case kept
    assert "\nSweep on claude-cli:Some-Model_2: found 31 of 34 in its fixtures.\n" in named


def test_a_low_count_shows_and_holds_nothing(tmp_path):
    r = with_reads(SWEEP, None, pin=False)
    st = dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "3/34")})
    text = brief_text(tmp_path, r, st)
    assert "\nSweep on jev: found 3 of 34 in its fixtures.\n" in text and "Fixture checks: no step failed." in text


def test_rows_that_got_no_answer_are_said(tmp_path):
    r = with_reads(SWEEP, None, pin=False)
    st = dict(PASS, **{"03-sweep": Stamp("INCOMPLETE", None, None, "30/34", skipped=["a", "b"])})
    assert "\nSweep on jev: found 30 of 34 in its fixtures (2 got no answer).\n" in brief_text(tmp_path, r, st)


def test_the_line_is_not_there_when_sweep_did_not_run_or_its_fixtures_were_not_measured(tmp_path):
    r = with_reads(SWEEP, None, pin=False)
    nothing = dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "0/34", skipped=[f"r{i}" for i in range(34)])})  # all skipped
    assert "in its fixtures" not in brief_text(tmp_path, r, nothing)
    for bad in (Stamp("FAIL", None, None, "3/34"), Stamp("ERROR"), Stamp("no fixture set"), Stamp("PASS", None, None, "abc")):
        assert "in its fixtures" not in brief_text(tmp_path, r, dict(PASS, **{"03-sweep": bad})), bad
    assert "in its fixtures" not in brief_text(tmp_path, r, PASS)  # no stamp for Sweep (a run made without validation)
    assert "in its fixtures" not in brief_text(tmp_path, reports(), PASS)  # a default run: the brief is as it was
    assert "in its fixtures" not in brief_text(tmp_path, {**r, "03-sweep": None}, dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "3/4")}))


def test_a_saved_stamp_reused_still_says_what_it_found(tmp_path):
    r = with_reads(SWEEP, None, pin=False)
    st = dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "31/34", cached="2026-10-30")})
    assert "\nSweep on jev: found 31 of 34 in its fixtures.\n" in brief_text(tmp_path, r, st)


def test_the_model_name_in_the_line_is_one_line(tmp_path):
    r = with_reads(SWEEP, None, pin=False)
    st = dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "31/34")})
    text = brief_text(tmp_path, r, st, backends={"03-sweep": "claude-cli:a\nnote: planted"})
    assert "\nnote: planted" not in text and "Sweep on claude-cli:a note: planted: found 31 of 34" in text


def test_the_model_name_in_the_line_is_cut_at_the_cap(tmp_path):
    """M1 fix round 2: the name is one line (above) and cut at `stagenote.MODEL_CAP` like every other place the pages name a model,
    so a record that holds a long name (the rule allows 200 characters, and a saved record can hold anything) cannot fill the line."""
    r = with_reads(SWEEP, None, pin=False)
    st = dict(PASS, **{"03-sweep": Stamp("PASS", None, None, "31/34")})
    for name in ("claude-cli:" + "m" * 189, "x" * 3000):
        line = next(x for x in brief_text(tmp_path, r, st, backends={"03-sweep": name}).splitlines() if x.startswith("Sweep on "))
        shown = line[len("Sweep on "):line.index(": found ")]
        assert len(shown) <= 80 and shown.endswith("..."), (len(shown), line[:120])
    waiting = brief.stop_lines({"after": "02.3-graph", "prepared": None}, tmp_path, waiting=["03-sweep"],
                               backends={"03-sweep": "claude-cli:" + "m" * 189})
    said = " ".join(x for x in waiting if not x.startswith("To go on"))  # the command to go on keeps the option as typed
    assert "m" * 100 not in said and "claude-cli:" + "m" * 60 in said and "..." in said, said[:200]
    assert "claude-cli:" + "m" * 189 in waiting[-1]
