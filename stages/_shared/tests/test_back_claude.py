"""Tests for back_claude.py and the calls it shares with every backend (textmodel.py), written from specs/shared.SPEC.md,
back_claude and textmodel. The CLI is never called."""
import json
import os
import subprocess
import threading
from types import SimpleNamespace

import back_claude
import calllog
import softdata
import textmodel

DATA = softdata.load()
SYSTEM = "THE SYSTEM TEXT"


def item(i, text="Proceed without asking."):
    return {"qid": f"q:{i}", "system": SYSTEM, "prompt": f"PASSAGE {i}: {text}", "label": "softreads.yaml a.system"}


class StubRunner:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def __call__(self, cmd, input=None, cwd=None, capture_output=None, timeout=None, **kw):
        self.calls.append({"cmd": cmd, "input": input, "cwd": cwd,
                           "cwd_files": os.listdir(cwd)})
        out = self.outputs.pop(0)
        if isinstance(out, BaseException):
            raise out
        rc, body = out
        return SimpleNamespace(returncode=rc, stdout=body.encode("utf-8"), stderr=b"")


def ok(text, model="claude-sonnet-x", **more):
    return (0, json.dumps({"type": "result", "is_error": False, "result": text,
                           "modelUsage": {model: {"inputTokens": 5}}, **more}))


def make(runner, which="C:/bin/claude.exe", waits=None, workers=1, model="sonnet"):
    """A ClaudeCLI over a stub runner. Nothing waits: the wait before a second try is handed to `waits`. One call at a
    time, so the script of the stub is in order."""
    sleep = (lambda s: None) if waits is None else waits.append
    return back_claude.ClaudeCLI(DATA, model=model, runner=runner, which=lambda n: which, sleep=sleep, workers=workers)


def bad(text="overloaded"):
    return (0, json.dumps({"type": "result", "is_error": True, "result": text}))


JSON = '{"line": 3, "quote": "Proceed", "plain": "It acts alone.", "also": []}'


def is_json(text):
    """An accept that wants a JSON object in the answer, as the pinpoint's does."""
    if "{" in text:
        return {"answer": text}, None
    return None, calllog.failure("unreadable answer", None, "claude-cli: unreadable answer", answer={"answer": text})


def test_command_flags_and_stdin():
    r = StubRunner([ok("fine")])
    res = make(r).ask([item(3)])
    call = r.calls[0]
    cmd = call["cmd"]
    for flag in ("-p", "--strict-mcp-config", "--no-session-persistence", "--safe-mode"):
        assert flag in cmd
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--setting-sources") + 1] == ""
    assert cmd[cmd.index("--output-format") + 1] == "json"
    assert cmd[cmd.index("--model") + 1] == "sonnet"
    assert cmd[cmd.index("--system-prompt") + 1] == SYSTEM
    assert "Proceed without asking." not in " ".join(cmd)  # the prompt goes on stdin and never on the command line
    prompt = call["input"].decode("utf-8") if isinstance(call["input"], bytes) else call["input"]
    assert prompt == item(3)["prompt"]
    assert call["cwd_files"] == []
    assert not os.path.exists(call["cwd"])
    assert res[0]["answer"] == "fine" and res[0]["qid"] == "q:3"
    assert res[0]["model"] == "claude-sonnet-x" and res[0]["backend"] == "claude-cli"
    # the record of what was sent names the command with a placeholder for the system text, which the data holds
    shown = res[0]["request"]["command"]
    assert shown[shown.index("--system-prompt") + 1] == "<softreads.yaml a.system>"
    assert res[0]["request"]["stdin"] == prompt


def test_the_model_is_the_one_named_then_the_environment_then_sonnet(monkeypatch):
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", "haiku")
    assert back_claude.ClaudeCLI(DATA).model == "haiku"
    assert back_claude.ClaudeCLI(DATA, model="Some-Model_2").model == "Some-Model_2"  # the option wins, its case kept
    monkeypatch.delenv("WALKDOWN_SOFT_CLAUDE_MODEL")
    assert back_claude.ClaudeCLI(DATA).model == "sonnet"
    r = StubRunner([ok("fine")])
    make(r, model="Some-Model_2").ask([item(3)])
    assert r.calls[0]["cmd"][r.calls[0]["cmd"].index("--model") + 1] == "Some-Model_2"


def test_the_workers_come_from_the_environment_when_it_is_a_whole_number_above_0(monkeypatch):
    for text, workers in (("2", 2), ("12", 12), ("0", 4), ("-1", 4), ("many", 4), ("", 4), ("2.5", 4)):
        monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_WORKERS", text)
        assert back_claude.ClaudeCLI(DATA).workers == workers, text
    monkeypatch.delenv("WALKDOWN_SOFT_CLAUDE_WORKERS")
    assert back_claude.ClaudeCLI(DATA).workers == 4 and back_claude.ClaudeCLI(DATA, workers=1).workers == 1


def test_a_rejected_login_that_is_rejected_again_stops_further_calls():
    """M9 slice A: the first call is tried once more; rejected again, it stops every later call, which are
    skipped as not sent."""
    body = json.dumps({"type": "result", "is_error": True,
                       "result": "Invalid API key · Please run /login"})
    r = StubRunner([(1, body), (1, body)])
    res = make(r).ask([item(3), item(7)])
    assert len(r.calls) == 2  # the first try and its one retry; nothing after
    assert [x["skipped"] for x in res] == ["claude-cli: authentication error",
                                          "not sent: claude-cli: authentication error"]
    assert res[0]["tries"]["first"]["kind"] == "authentication" and res[0]["tries"]["retry"]["result"] == "no answer"
    assert res[1]["tries"]["first"] is None
    assert res[1]["tries"]["retry"] == {"result": "not tried", "why": "claude-cli: authentication error"}


def test_a_rejected_login_stops_the_calls_even_with_workers_because_the_first_call_runs_alone():
    body = json.dumps({"type": "result", "is_error": True, "result": "Invalid API key · Please run /login"})
    r = StubRunner([(1, body), (1, body)])
    res = make(r, workers=4).ask([item(i) for i in range(1, 7)])
    assert len(r.calls) == 2  # not six: nothing else started while the first was being rejected
    assert [x["skipped"] for x in res[1:]] == ["not sent: claude-cli: authentication error"] * 5


def test_the_first_call_runs_alone_and_the_rest_run_at_the_same_time():
    log, lock = [], threading.Lock()
    pair = threading.Barrier(2, timeout=10)  # two calls wait for each other: they must be in flight together

    def runner(cmd, input=None, cwd=None, capture_output=None, timeout=None, **kw):
        n = input.decode("utf-8").split(":")[0].split()[-1]
        with lock:
            log.append(("start", n))
        if n != "1":
            pair.wait()
        with lock:
            log.append(("end", n))
        body = json.dumps({"type": "result", "is_error": False, "result": "fine"})
        return SimpleNamespace(returncode=0, stdout=body.encode("utf-8"), stderr=b"")
    res = make(runner, workers=2).ask([item(i) for i in (1, 2, 3)])
    assert log[:2] == [("start", "1"), ("end", "1")]  # the first alone: it ended before any other started
    assert all("skipped" not in x for x in res) and [x["qid"] for x in res] == ["q:1", "q:2", "q:3"]  # in order


def test_a_login_rejected_once_and_accepted_on_the_retry_stops_nothing():
    body = (1, json.dumps({"type": "result", "is_error": True, "result": "Invalid API key"}))
    r = StubRunner([body, ok("a"), ok("b")])
    res = make(r).ask([item(3), item(7)])
    assert [x.get("answer") for x in res] == ["a", "b"] and len(r.calls) == 3
    assert res[0]["tries"]["retry"] == {"result": "answered"} and "tries" not in res[1]


def test_a_timeout_and_an_error_skip_only_their_question():
    gone = subprocess.TimeoutExpired("claude", 1)
    r = StubRunner([gone, gone, bad(), bad(), ok("fine")])  # each failing question is tried twice
    res = make(r).ask([item(3), item(7), item(11)])
    assert res[0]["skipped"] == "claude-cli: timeout"
    assert res[1]["skipped"].startswith("claude-cli: error")
    assert res[2]["answer"] == "fine" and len(r.calls) == 5


def test_a_call_that_fails_once_is_tried_again_after_the_wait_and_the_answer_is_used():
    waits = []
    r = StubRunner([ok(JSON), bad("overloaded"), ok(JSON), subprocess.TimeoutExpired("claude", 1), ok(JSON)])
    res = make(r, waits=waits).ask([item(3), item(7), item(11)])
    assert all("skipped" not in x for x in res) and len(r.calls) == 5
    assert waits == [DATA["retry_wait"], DATA["retry_wait"]] == [2.0, 2.0]  # only the two failed calls waited
    assert "tries" not in res[0]
    assert res[1]["tries"]["first"] == {"kind": "error", "status": 0}  # the program's exit code; the text is not kept
    assert res[1]["tries"]["retry"] == {"result": "answered"}
    assert res[2]["tries"]["first"]["kind"] == "timeout"
    assert res[1]["answer"] == JSON and res[1]["request"]["stdin"] == item(7)["prompt"]


def test_a_call_that_fails_twice_is_skipped_with_the_second_tries_reason_and_never_tried_a_third_time():
    r = StubRunner([bad("overloaded"), subprocess.TimeoutExpired("claude", 1), ok(JSON)])
    res = make(r).ask([item(3), item(7)])
    assert res[0]["skipped"] == "claude-cli: timeout" and len(r.calls) == 3
    assert res[0]["tries"]["first"] == {"kind": "error", "status": 0}
    assert res[0]["tries"]["retry"]["kind"] == "timeout" and res[0]["tries"]["retry"]["result"] == "no answer"
    assert res[1]["answer"] == JSON


def test_an_answer_that_cannot_be_used_is_tried_again_and_a_usable_one_is_used():
    r = StubRunner([ok("I could not tell."), ok(JSON)])
    res = make(r).ask([item(3)], is_json)
    assert res[0]["answer"] == JSON and "skipped" not in res[0] and len(r.calls) == 2
    assert res[0]["tries"]["first"]["kind"] == "unreadable answer" and res[0]["tries"]["retry"] == {"result": "answered"}


def test_an_answer_that_cannot_be_used_twice_is_kept_as_it_came_for_the_step_to_skip():
    r = StubRunner([ok("no json one"), ok("no json two")])
    [res] = make(r).ask([item(3)], is_json)
    assert len(r.calls) == 2 and "skipped" not in res and res["answer"] == "no json two"
    assert res["model"] == "claude-sonnet-x" and res["response"]["result"] == "no json two"  # the model and the raw response ride along
    assert res["tries"]["retry"]["result"] == "no answer" and res["tries"]["retry"]["kind"] == "unreadable answer"
    assert "no json" not in json.dumps(res["tries"])  # the log holds none of the answer's text


def test_without_an_accept_the_text_is_the_answer():
    r = StubRunner([ok("fine")])
    assert make(r).ask([item(3)])[0]["answer"] == "fine" and len(r.calls) == 1


def test_nothing_to_call_is_not_tried_again_and_nothing_waits():
    waits = []
    r = StubRunner([])
    [res] = make(r, which=None, waits=waits).ask([item(3)])
    assert res["skipped"] == "claude-cli: not installed" and r.calls == [] and waits == []
    assert res["tries"]["first"] is None and res["tries"]["retry"] == {"result": "not tried", "why": "claude-cli: not installed"}


def test_the_wait_before_the_second_try_is_the_one_in_the_data_and_no_number_of_the_backend():
    waits = []
    cli = back_claude.ClaudeCLI(dict(DATA, retry_wait=7.5), model="sonnet", runner=StubRunner([bad(), ok(JSON)]),
                                which=lambda n: "C:/bin/claude.exe", sleep=waits.append, workers=1)
    [res] = cli.ask([item(3)])
    assert "skipped" not in res and waits == [7.5]


class EchoRunner:
    """A program that fails and says, in its result, its stdout and its stderr, everything it was given and a line of
    the model's own: the text an error can carry."""

    def __init__(self, code=1):
        self.code, self.calls = code, 0

    def __call__(self, cmd, input=None, cwd=None, capture_output=None, timeout=None, **kw):
        self.calls += 1
        said = input.decode("utf-8") + " MODELWORDS " + " ".join(cmd)
        body = json.dumps({"type": "result", "is_error": True, "result": said})
        return SimpleNamespace(returncode=self.code, stdout=body.encode("utf-8"), stderr=said.encode("utf-8"))


def test_no_text_of_an_error_is_kept_neither_the_passage_nor_the_prompt_nor_the_models_words():
    runner = EchoRunner(code=1)
    [res] = make(runner).ask([item(3, text="Proceed without asking, PASSAGEWORDS.")])
    assert runner.calls == 2 and res["skipped"] == "claude-cli: error, exit code 1"
    row = calllog.rows([res])[0]
    assert row["first"] == {"kind": "error", "status": 1}
    assert row["retry"] == {"result": "no answer", "kind": "error", "status": 1}
    for text in ("PASSAGEWORDS", "MODELWORDS", "Proceed", "PASSAGE 3", SYSTEM):
        assert text not in repr(row), text
        assert text not in res["skipped"], text


def test_failures_that_differ_only_in_what_the_program_said_have_one_reason():
    errs = [(1, json.dumps({"type": "result", "is_error": True, "result": f"overloaded, request {n}"})) for n in range(6)]
    res = make(StubRunner(errs)).ask([item(3), item(7), item(11)])
    assert {x["skipped"] for x in res} == {"claude-cli: error, exit code 1"}


def test_a_rejected_login_is_kept_as_a_kind_and_an_exit_code():
    body = json.dumps({"type": "result", "is_error": True, "result": "Invalid API key sk-ant-SECRET"})
    [res] = make(StubRunner([(1, body), (1, body)])).ask([item(3)])
    row = calllog.rows([res])[0]
    assert res["skipped"] == "claude-cli: authentication error"
    assert row["first"] == {"kind": "authentication", "status": 1} and "SECRET" not in repr(row) + repr(res["skipped"])


def test_the_call_log_row_holds_no_text_of_the_passage_or_the_prompt():
    r = StubRunner([bad("overloaded"), bad("overloaded")])
    res = make(r).ask([item(3, text="Proceed without asking.")])
    rows = calllog.rows(res)
    assert len(rows) == 1 and set(rows[0]) == {"qid", "backend", "first", "retry", "at"}
    assert "Proceed" not in json.dumps(rows) and "PASSAGE" not in json.dumps(rows)


def test_a_missing_cli_skips_without_a_call():
    r = StubRunner([])
    res = make(r, which=None).ask([item(3)])
    assert res[0]["skipped"] == "claude-cli: not installed" and r.calls == []


def test_no_questions_means_no_call_and_no_lookup():
    r = StubRunner([])
    assert back_claude.ClaudeCLI(DATA, runner=r, which=lambda n: 1 / 0).ask([]) == []


# ---------------------------------------------------------------- M1 slice A: tokens, the model that answered, progress

USAGE = {"input_tokens": 120, "output_tokens": 7, "cache_creation_input_tokens": 1000, "cache_read_input_tokens": 50}


def test_the_tokens_the_cli_reports_are_added_up_over_every_call():
    r = StubRunner([ok("a", usage=USAGE), ok("b", usage={"input_tokens": 80, "output_tokens": 3})])
    cli = make(r)
    cli.ask([item(3), item(7)])
    assert cli.usage.block() == {"input": 200, "output": 10, "cache_write": 1000, "cache_read": 50, "calls": 2, "reported": 2}


def test_a_count_the_cli_does_not_report_is_absent_and_never_0():
    r = StubRunner([ok("a", usage={"input_tokens": 80}), ok("b")])  # the second call reports no usage at all
    cli = make(r)
    cli.ask([item(3), item(7)])
    assert cli.usage.block() == {"input": 80, "calls": 2, "reported": 1}


def test_counts_that_are_not_whole_numbers_are_not_reported():
    bad_counts = {"input_tokens": 1.5, "output_tokens": True, "cache_creation_input_tokens": -4, "cache_read_input_tokens": "9"}
    cli = make(StubRunner([ok("a", usage=bad_counts), ok("b", usage="a lot")]))
    cli.ask([item(3), item(7)])
    assert cli.usage.block() == {"calls": 2, "reported": 0}


def test_a_count_above_the_ceiling_is_not_reported():
    """M1 fix 6: a service can put any number in its reply; a count above 10**15 is not a count."""
    huge = {"input_tokens": 10 ** 15 + 1, "output_tokens": 10 ** 4000, "cache_read_input_tokens": 10 ** 15}
    cli = make(StubRunner([ok("a", usage=huge), ok("b", usage="a lot")]))
    cli.ask([item(3), item(7)])
    assert cli.usage.block() == {"cache_read": 10 ** 15, "calls": 2, "reported": 1}


def test_a_call_that_got_no_answer_still_counts_as_a_call_sent_and_the_tokens_of_an_unusable_answer_are_kept():
    r = StubRunner([ok("no json", usage=USAGE), ok(JSON, usage=USAGE), bad(), bad()])
    cli = make(r)
    cli.ask([item(3), item(7)], is_json)
    assert cli.usage.block() == {"input": 240, "output": 14, "cache_write": 2000, "cache_read": 100, "calls": 4, "reported": 2}


def test_the_tokens_of_an_error_reply_are_counted_because_they_were_spent():
    """M1 fix 5: a reply with `is_error` (or a non-zero exit code) that holds a usage block spent those tokens."""
    err_reply = (0, json.dumps({"type": "result", "is_error": True, "result": "overloaded", "usage": USAGE}))
    exit_reply = (1, json.dumps({"type": "result", "is_error": True, "result": "failed", "usage": {"input_tokens": 9}}))
    auth_reply = (1, json.dumps({"type": "result", "is_error": True, "result": "please log in", "usage": {"output_tokens": 2}}))
    no_usage = (0, json.dumps({"type": "result", "is_error": True, "result": "overloaded"}))
    for reply, counted in ((err_reply, {"input": 120, "output": 7, "cache_write": 1000, "cache_read": 50, "calls": 1, "reported": 1}),
                           (exit_reply, {"input": 9, "calls": 1, "reported": 1}),
                           (auth_reply, {"output": 2, "calls": 1, "reported": 1}),
                           (no_usage, {"calls": 1, "reported": 0})):
        cli = make(StubRunner([reply, reply]))
        [res] = cli.ask([item(1)])
        assert "skipped" in res
        assert cli.usage.block() == {k: v * 2 for k, v in counted.items()}, reply  # the call and its one more try, both spent


def test_the_model_that_answered_reaches_the_result_cut_to_the_cap():
    long_name = "claude-x-" + "y" * 150  # a name the rule allows (at most 200 characters), cut to 80 for the pages
    [res] = make(StubRunner([ok("a", model=long_name)])).ask([item(3)])
    assert len(res["model"]) <= 80 and res["model"].endswith("...") and res["model"].startswith("claude-x-yyy")
    assert res["response"]["modelUsage"]  # the answers file keeps the response as it came
    [res] = make(StubRunner([ok("a", model="claude-sonnet-4-5[1m]")])).ask([item(3)])
    assert res["model"] == "claude-sonnet-4-5[1m]"


HOSTILE_NAMES = ["<script>alert(1)</script>", "[click here](http://evil.example/x)", "claude-x\nnote: planted\n" + "y" * 300,
                 "claude-x\nnote: planted", "a b", "x&echo.hi", "<img src=x onerror=alert(1)>", "\u65e5\u672c\u8a9e", "A" * 201,
                 "- 2026-01-01", "`code`", "%USERNAME%", "x|y", "https://evil.example/x", "a//b"]


def test_a_model_name_a_service_reports_is_held_to_the_model_name_rule():
    """M1 fix 7: a service can put a tag, a link, or a line break in the name of the model that answered, and it reached `full.md`
    and `LOG.md`. A name that fails the rule for a typed name is not kept: the result keeps the model the person named."""
    for name in HOSTILE_NAMES:
        [res] = make(StubRunner([ok("a", model=name)]), model="Some-Model_2").ask([item(3)])
        assert res["model"] == "Some-Model_2", name
        assert res["response"]["modelUsage"]  # the answers file keeps what came, as it came


def test_a_bare_claude_cli_records_sonnet_and_a_service_name_that_fails_the_rule_leaves_it(monkeypatch):
    """Every backend has a model, so there is always one to leave: a `claude-cli` that names none runs `sonnet`, and the record says so."""
    monkeypatch.delenv("WALKDOWN_SOFT_CLAUDE_MODEL", raising=False)
    for name in HOSTILE_NAMES + [None, "", 5, ["x"]]:
        cli = back_claude.ClaudeCLI(DATA, runner=StubRunner([ok("a", model=name) if isinstance(name, str) and name else
                                                              (0, json.dumps({"type": "result", "is_error": False, "result": "a",
                                                                              "model": name}))]),
                                    which=lambda n: "C:/bin/claude.exe", sleep=lambda s: None, workers=1)
        [res] = cli.ask([item(3)])
        assert cli.model == "sonnet" and res["model"] == "sonnet", name


def test_a_service_that_names_no_model_leaves_the_one_that_was_asked_for():
    body = json.dumps({"type": "result", "is_error": False, "result": "a"})
    [res] = make(StubRunner([(0, body)]), model="Some-Model_2").ask([item(3)])
    assert res["model"] == "Some-Model_2"


def test_a_long_read_says_it_is_working_every_25_passages(capsys):
    cli = make(StubRunner([ok("a")] * 60))
    cli.ask([item(i) for i in range(60)], who="sweep")
    err = capsys.readouterr().err.splitlines()
    assert err == ["sweep: 25 of 60 passages done", "sweep: 50 of 60 passages done"]  # no `note:` in front
    cli = make(StubRunner([ok("a")] * 30))
    cli.ask([item(i) for i in range(30)])  # a step that gives no name says nothing
    assert capsys.readouterr().err == ""


def test_a_short_read_says_nothing_while_it_works(capsys):
    make(StubRunner([ok("a")] * 24)).ask([item(i) for i in range(24)], who="pinpoint")
    assert capsys.readouterr().err == ""


def test_the_contract_is_one_class_for_every_backend():
    """A text model supplies `call` and the base does the rest: the second try, the stop on a rejected key, the first call
    alone, the workers, and `not sent` are not written again in a backend."""
    assert issubclass(back_claude.ClaudeCLI, textmodel.TextModel) and issubclass(textmodel.TextModel, textmodel.Backend)
    assert {"ask", "_one", "_try"} <= set(vars(textmodel.Backend)) and "ask" in vars(textmodel.TextModel)
    for name in ("ask", "_one", "_try", "once"):
        assert name not in vars(back_claude.ClaudeCLI)
