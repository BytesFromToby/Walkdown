"""Tests for calllog.py, written from specs/shared.SPEC.md, calllog (M9, slice A). No call is made and nothing waits:
`sleep` is a recorder."""
import datetime as dt
import json

import calllog
import layout


def fail(kind="Boom", status=None, reason="x: Boom", **kw):
    return calllog.failure(kind, status, reason, **kw)


def script(*outcomes):
    """A `try_once` that gives the outcomes in turn: an answer (any value) or a failure dict."""
    left, calls = list(outcomes), []

    def once():
        calls.append(1)
        o = left.pop(0)
        return (None, o) if isinstance(o, dict) and "reason" in o else (o, None)
    once.calls = calls
    return once


def test_a_first_try_that_answers_is_used_with_no_wait_and_no_record():
    waits = []
    once = script({"kind": "none"})
    answer, failed, tries = calllog.attempt(once, 2.0, waits.append)
    assert answer == {"kind": "none"} and failed is None and tries is None
    assert len(once.calls) == 1 and waits == []


def test_a_first_try_that_fails_is_tried_once_more_after_the_wait_and_the_answer_is_used():
    waits = []
    once = script(fail("RateLimit", 429), {"kind": "none"})
    answer, failed, tries = calllog.attempt(once, 2.0, waits.append)
    assert answer == {"kind": "none"} and failed is None
    assert waits == [2.0] and len(once.calls) == 2
    assert tries["first"] == {"kind": "RateLimit", "status": 429} and tries["retry"] == {"result": "answered"}
    assert dt.datetime.fromisoformat(tries["at"]).tzinfo is not None


def test_two_failures_end_the_call_with_the_second_tries_reason_and_both_are_recorded():
    waits = []
    once = script(fail("RateLimit", 429, "x: RateLimit, status 429"), fail("Timeout", None, "x: Timeout"))
    answer, failed, tries = calllog.attempt(once, 2.0, waits.append)
    assert answer is None and failed["reason"] == "x: Timeout" and len(once.calls) == 2 and waits == [2.0]
    assert tries["first"] == {"kind": "RateLimit", "status": 429}
    assert tries["retry"] == {"result": "no answer", "kind": "Timeout", "status": None}


def test_a_call_is_never_tried_a_third_time():
    once = script(fail(), fail(), {"kind": "none"})
    answer, failed, _ = calllog.attempt(once, 0, lambda s: None)
    assert answer is None and failed is not None and len(once.calls) == 2


def test_calls_stopped_during_the_wait_mean_no_second_try_and_the_first_reason_stands():
    once = script(fail("RateLimit", 429, "x: RateLimit, status 429"), {"kind": "none"})
    answer, failed, tries = calllog.attempt(once, 2.0, lambda s: None, stopped=lambda: "x: authentication failed")
    assert answer is None and failed["reason"] == "x: RateLimit, status 429" and len(once.calls) == 1
    assert tries["first"]["kind"] == "RateLimit"
    assert tries["retry"] == {"result": "not tried", "why": "x: authentication failed"}


def test_a_rejected_key_is_tried_again_like_any_other_failure():
    once = script(fail("AuthError", 401, "x: authentication failed", auth=True),
                  fail("AuthError", 401, "x: authentication failed", auth=True))
    answer, failed, tries = calllog.attempt(once, 2.0, lambda s: None)
    assert answer is None and failed["auth"] is True and len(once.calls) == 2
    assert tries["retry"]["result"] == "no answer"


def test_a_failure_keeps_a_kind_and_a_status_and_no_message_of_its_own():
    """An error's text can repeat the passage or the model's words, so the failure has a place for neither."""
    f = calllog.failure("E", 503, "x: E, status 503")
    assert set(f) == {"kind", "status", "reason", "auth"} and f["status"] == 503
    assert not hasattr(calllog, "short") and not hasattr(calllog, "MESSAGE_CAP")
    assert calllog.status_text(503) == ", status 503" and calllog.status_text(1, "exit code") == ", exit code 1"
    assert calllog.status_text(None) == ""


def test_a_passage_never_sent_has_no_first_try_and_a_retry_that_was_not_tried():
    t = calllog.unsent("jev: no key")
    assert t["first"] is None and t["retry"] == {"result": "not tried", "why": "jev: no key"}


def test_the_log_has_a_line_for_each_result_with_tries_in_the_order_of_the_results():
    waits = []
    _, _, answered = calllog.attempt(script(fail(), {"kind": "none"}), 2.0, waits.append)
    results = [{"qid": "a", "backend": "jev", "kind": "none"},
               {"qid": "b", "backend": "jev", "kind": "none", "tries": answered},
               {"qid": "c", "backend": "jev", "skipped": "jev: no key", "tries": calllog.unsent("jev: no key")},
               {"qid": "d", "backend": "jev", "skipped": "x", "request": {"state": "never in the log"},
                "tries": {"first": {"kind": "E", "status": None}, "retry": {"result": "no answer", "kind": "E",
                                                                            "status": None}, "at": "t"}}]
    got = calllog.rows(results)
    assert [r["qid"] for r in got] == ["b", "c", "d"]
    assert set(got[0]) == {"qid", "backend", "first", "retry", "at"}
    assert got[0]["retry"] == {"result": "answered"} and got[1]["first"] is None
    assert "request" not in json.dumps(got) and calllog.rows(None) == [] and calllog.rows([]) == []


def test_the_file_is_written_only_when_there_is_a_line(tmp_path):
    path = tmp_path / "03-sweep.calls.jsonl"
    assert calllog.write(path, []) is False and not path.exists()
    rows = [{"qid": "a", "backend": "jev", "first": None, "retry": {"result": "not tried", "why": "w"}, "at": "t"}]
    assert calllog.write(path, rows) is True
    assert [json.loads(x) for x in path.read_text("utf-8").splitlines()] == rows


def test_the_report_block_counts_retries_and_unsent_passages_and_is_absent_without_a_line():
    assert calllog.summary([], "03-sweep.calls.jsonl") is None
    rows = [{"qid": "a", "first": {"kind": "E", "status": 503}, "retry": {"result": "answered"}},
            {"qid": "b", "first": {"kind": "E", "status": 503}, "retry": {"result": "no answer", "kind": "E",
                                                                         "status": 503}},
            {"qid": "c", "first": None, "retry": {"result": "not tried", "why": "w"}},
            {"qid": "d", "first": None, "retry": {"result": "not tried", "why": "w"}}]
    assert calllog.summary(rows, "03-sweep.calls.jsonl") == {
        "log": "03-sweep.calls.jsonl", "answered_on_retry": 1, "not_sent": 2}
    assert calllog.summary(rows, None)["log"] is None


def test_a_read_that_got_no_answer_is_one_that_asked_and_every_passage_was_skipped():
    skip = {"check": "soft.sweep", "qid": "q1", "skipped": "jev: no key"}
    ok = {"check": "soft.sweep", "qid": "q2", "kind": "none"}
    assert calllog.tally({"findings": [skip, dict(skip, qid="q3"), ok]}) == (3, 2)
    assert calllog.got_nothing({"findings": [skip, dict(skip, qid="q3")]}) is True
    assert calllog.got_nothing({"findings": [skip, ok]}) is False  # a partial read worked
    assert calllog.got_nothing({"findings": []}) is False  # no passage was asked: nothing to answer
    assert calllog.got_nothing({"findings": [{"check": "soft.sweep", "file": None, "line": None,
                                              "skipped": "no sweep backend"}]}) is False  # names no passage
    assert calllog.got_nothing(None) is False and calllog.tally(None) == (0, 0)


def test_the_notes_line_counts_the_calls_and_names_the_log():
    rows = [{"first": {"kind": "E", "status": 503}, "retry": {"result": "answered"}},
            {"first": {"kind": "E", "status": 503}, "retry": {"result": "no answer", "kind": "E", "status": 503}},
            {"first": None, "retry": {"result": "not tried", "why": "w"}}]
    assert calllog.notes(rows, "03-sweep.calls.jsonl") == [
        "calls: 1 answered on the retry, 1 got no answer after it, 1 not sent; call log: 03-sweep.calls.jsonl"]
    assert calllog.notes(rows, None) == ["calls: 1 answered on the retry, 1 got no answer after it, 1 not sent"]
    assert calllog.notes([], "x") == []


def test_the_call_log_file_is_named_for_its_step():
    assert layout.calls_file("03-sweep") == "03-sweep.calls.jsonl"
    assert layout.calls_file("04-pinpoint") == "04-pinpoint.calls.jsonl"
