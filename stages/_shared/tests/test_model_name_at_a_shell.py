"""A typed model name against a Windows `.cmd` shim (M1 fix 1), written from specs/shared.SPEC.md, options and back_claude.

On Windows `claude` is usually a `.cmd` shim, and a `.cmd` file runs through `cmd.exe`, which reads `& | < > ^ %` and a quote in
an argument as commands and variables. So a model name is held to an allowed set before anything runs. This test puts a real
`claude.cmd` on the path of a call and sends every name that the rule lets through: a hostile name that gets past the rule runs a
command (the marker file appears) or reaches the shim changed, and the test fails. Nothing here calls the real CLI."""
import argparse
import json
import subprocess
import sys

import pytest

import back_claude
import options
import softdata

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="a .cmd shim is a Windows thing")

DATA = softdata.load()
HOSTILE = ["https://evil.example/x", "a//b", "x&echo.INJECTED>MARK", "x|echo.INJECTED>MARK", "x&&echo.INJECTED>MARK", "x%USERNAME%", "%PATH%", "x^y", 'x"y',
           'x" & echo.INJECTED>MARK & "', "x<MARK", "x>MARK", "x(y)", "x)&echo.INJECTED>MARK", "x!y!", "x`y", "x$y", "x;y", "x,y",
           "x=y", "x y", "x\ty", "x'y", "x*", "x?", "x{y}", "x~", "x#", "café", "日本語", "x\U0001f600", "x＆y"]
GOOD = ["sonnet", "opus", "sonnet[1m]", "claude-sonnet-4-5", "vendor/model.v2@2026+x:tag_1", "a" * 200]

FAKE = '''import json, os, sys
d = os.environ["SHIM_DIR"]
n = len(os.listdir(d))
open(os.path.join(d, "argv-%d.json" % n), "w", encoding="utf-8").write(json.dumps(sys.argv[1:]))
sys.stdin.buffer.read()
print(json.dumps({"type": "result", "is_error": False, "result": "ok", "modelUsage": {"m": {}}}))
'''


@pytest.fixture
def shim(tmp_path, monkeypatch):
    """A `claude.cmd` that records the arguments it was handed, one file per call, and answers `ok`."""
    calls = tmp_path / "calls"
    calls.mkdir()
    (tmp_path / "fake_claude.py").write_text(FAKE, encoding="utf-8")
    cmd = tmp_path / "claude.cmd"
    cmd.write_bytes(f'@echo off\r\n"{sys.executable}" "{tmp_path / "fake_claude.py"}" %*\r\n'.encode("utf-8"))
    monkeypatch.setenv("SHIM_DIR", str(calls))
    marker = tmp_path / "MARK"
    return cmd, calls, marker


def send(cmd, model):
    """One call the way the stage makes it: the backend over the real `.cmd`."""
    b = back_claude.ClaudeCLI(DATA, model=model, which=lambda name: str(cmd), workers=1, timeout=60)
    assert b.prepare() is None
    return b.call("S", "P")


def hostile(name, marker):
    return name.replace("MARK", str(marker))


def test_a_name_with_a_shell_character_or_outside_ascii_never_reaches_the_shim_from_the_option(shim):
    cmd, calls, marker = shim
    for name in HOSTILE:
        typed = "claude-cli:" + hostile(name, marker)
        try:
            backend, model = options.parse_choice("03-sweep", typed, "--sweep")
        except ValueError:
            continue  # refused before anything runs: the intended end
        send(cmd, model)  # a name the rule lets through is sent for real, and the asserts below fail
        pytest.fail(f"the rule let {name!r} through")
    assert not marker.exists() and list(calls.iterdir()) == []


def test_a_name_with_a_shell_character_or_outside_ascii_never_reaches_the_shim_from_the_variable(shim, monkeypatch):
    cmd, calls, marker = shim
    ap = argparse.ArgumentParser()
    options.add_run_options(ap)
    for name in HOSTILE:
        monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", hostile(name, marker))
        if options.check(ap.parse_args(["x", "--sweep", "claude-cli"])) is None:
            send(cmd, None)  # the model a bare claude-cli runs comes from the variable
            pytest.fail(f"the rule let {name!r} through")
    assert not marker.exists() and list(calls.iterdir()) == []


def test_a_name_the_rule_allows_reaches_the_shim_exactly_as_typed(shim):
    cmd, calls, marker = shim
    for i, name in enumerate(GOOD):
        assert options.parse_choice("03-sweep", "claude-cli:" + name, "--sweep") == ("claude-cli", name)
        reply, failure = send(cmd, name)
        assert failure is None and reply["text"] == "ok", (name, failure)
        argv = json.loads((calls / f"argv-{i}.json").read_text(encoding="utf-8"))
        assert argv[argv.index("--model") + 1] == name, name


def test_the_shim_here_does_run_a_command_when_a_name_is_not_held(shim):
    """The check the other tests rely on: the same shim, a name that skips the rule, and the marker appears. Without this the
    tests above could pass because the shim cannot run anything."""
    cmd, calls, marker = shim
    send(cmd, f"x&echo.INJECTED>{marker}")
    assert marker.exists()
