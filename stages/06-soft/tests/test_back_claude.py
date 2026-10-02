"""Tests for back_claude.py, written from specs/back_claude.SPEC.md. The CLI is never called."""
import json
import os
import subprocess
from types import SimpleNamespace

import back_claude
import softdata

DATA = softdata.load()


def q(i, text="Proceed without asking."):
    return {"qid": f"rel:term.safety:a.md:{i}", "kind": "relational", "file": "a.md", "line": i,
            "template": "term.safety", "question": DATA["relational"]["term.safety"]["question"],
            "state": {"quote": text}, "sources": []}


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


def ok(text, model="claude-sonnet-x"):
    return (0, json.dumps({"type": "result", "is_error": False, "result": text,
                           "modelUsage": {model: {"inputTokens": 5}}}))


def make(runner, which="C:/bin/claude.exe"):
    return back_claude.ClaudeCLI(DATA, model="sonnet", runner=runner, which=lambda n: which)


def test_command_flags_and_stdin():
    r = StubRunner([ok("It would act without asking.")])
    res = make(r).read([q(1)])
    call = r.calls[0]
    cmd = call["cmd"]
    for flag in ("-p", "--strict-mcp-config", "--no-session-persistence"):
        assert flag in cmd
    assert cmd[cmd.index("--tools") + 1] == ""
    assert cmd[cmd.index("--output-format") + 1] == "json"
    assert cmd[cmd.index("--model") + 1] == "sonnet"
    assert cmd[cmd.index("--system-prompt") + 1] == DATA["claude_system_prompt"]["text"]
    joined = " ".join(cmd)
    assert "Proceed without asking." not in joined
    assert DATA["relational"]["term.safety"]["question"] not in joined
    prompt = call["input"].decode("utf-8") if isinstance(call["input"], bytes) else call["input"]
    assert "Proceed without asking." in prompt and "STATE" in prompt
    assert call["cwd_files"] == []
    assert not os.path.exists(call["cwd"])
    assert res[0]["answer"] == "It would act without asking."
    assert res[0]["model"] == "claude-sonnet-x" and res[0]["backend"] == "claude-cli"
    assert res[0]["capped"] is False


def test_answer_over_cap_is_cut():
    long = "x" * (DATA["answer_cap"] + 50)
    res = make(StubRunner([ok(long)])).read([q(1)])
    assert len(res[0]["answer"]) == DATA["answer_cap"] and res[0]["capped"] is True


def test_auth_error_stops_calls():
    body = json.dumps({"type": "result", "is_error": True,
                       "result": "Invalid API key · Please run /login"})
    r = StubRunner([(1, body)])
    res = make(r).read([q(1), q(2)])
    assert len(r.calls) == 1
    assert all(x["skipped"] == "claude-cli: authentication error" for x in res)


def test_timeout_and_is_error_skip_only_their_question():
    err = (0, json.dumps({"type": "result", "is_error": True, "result": "overloaded"}))
    r = StubRunner([subprocess.TimeoutExpired("claude", 1), err, ok("fine")])
    res = make(r).read([q(1), q(2), q(3)])
    assert res[0]["skipped"] == "claude-cli: timeout"
    assert res[1]["skipped"].startswith("claude-cli: error")
    assert res[2]["answer"] == "fine"


def test_missing_cli_skips_without_call():
    r = StubRunner([])
    res = make(r, which=None).read([q(1)])
    assert res[0]["skipped"] == "claude-cli: not installed" and r.calls == []


def lq(i):
    return {"qid": f"label:a.md:{i}", "kind": "label", "file": "a.md", "line": i,
            "question": DATA["label"]["question"], "state": {"text": "Start over."}, "sources": []}


def test_label_parses_json_and_records_self_reported_confidence(monkeypatch):
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_WORKERS", "1")
    runner = StubRunner([ok('```json\n{"label": "other-sense", "confidence": 0.9}\n```'),
                         ok("I think it is do."), ok('{"label": "banana", "confidence": 1}')])
    out = make(runner).label([lq(1), lq(2), lq(3)])
    assert out[0]["label"] == "other-sense" and out[0]["confidence"] == 0.9
    assert out[0]["probabilities"] == {"other-sense": 0.9} and out[0]["confidence_kind"] == "self-reported"
    assert out[1]["skipped"] == "claude-cli: unparseable label answer"
    assert out[2]["skipped"] == "claude-cli: unparseable label answer"
    sent = runner.calls[0]["input"].decode("utf-8")
    for name in DATA["label"]["options"]:
        assert f"- {name}:" in sent
    assert '"text": "Start over."' in sent and "--tools" in runner.calls[0]["cmd"]
