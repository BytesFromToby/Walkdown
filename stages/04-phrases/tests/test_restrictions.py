"""Tests for restrictions.py, written from specs/restrictions.SPEC.md."""
import restrictions as RS


def one(line):
    got = RS.settings_in_line(line)
    assert len(got) == 1, got
    return got[0]


# Done when 1
def test_tools_flag():
    s = one('claude -p --tools "Read,Grep,Glob" "$PROMPT"')
    assert s["kind"] == "tools-flag" and s["tools"] == ["Read", "Grep", "Glob"]
    assert s["rules_out"] == ["write", "shell", "network"] and s["grants_write"] is False
    s = one("claude -p --tools Read,Bash")
    assert s["rules_out"] == [] and s["grants_write"] is True
    s = one('claude -p --tools "" --system-prompt x')
    assert s["tools"] == [] and s["rules_out"] == ["write", "shell", "network"]
    assert one("x --tools Read,WebFetch")["rules_out"] == ["write", "shell"]


# Done when 2
def test_deny_lists():
    s = one('claude -p --disallowedTools "Write,Edit,MultiEdit,NotebookEdit,Bash"')
    assert s["kind"] == "deny" and s["rules_out"] == ["write", "shell"] and s["grants_write"] is False
    s = one('"deny": ["Bash(git push:*)"],')
    assert s["kind"] == "deny" and s["rules_out"] == []


# Done when 3
def test_sandbox_and_permission_mode():
    s = one("codex exec --sandbox read-only task")
    assert (s["kind"], s["value"], s["rules_out"], s["grants_write"]) == ("sandbox", "read-only", ["write"], False)
    assert one("codex exec --sandbox danger-full-access")["grants_write"] is True
    assert one('sandbox_mode = "workspace-write"')["grants_write"] is True
    s = one("claude -p --permission-mode plan")
    assert (s["kind"], s["value"], s["rules_out"]) == ("permission-mode", "plan", ["write", "shell"])
    assert one('"defaultMode": "bypassPermissions"')["grants_write"] is True


# Done when 4
def test_not_settings():
    assert RS.settings_in_line('claude -p --allowedTools "Read,Grep"') == []
    assert RS.settings_in_line("Read the --tools section of the CLI docs.") == []
    s = one("It runs `claude -p --tools Read,Grep,Glob` for each file.")
    assert s["tools"] == ["Read", "Grep", "Glob"]


def test_limit_file_records_audience_and_raw_quote():
    raw = ["# notes", "run `codex exec --sandbox read-only`"]
    out = RS.limit_file("scripts/a.sh", raw, raw, "tool")
    assert [(f["check"], f["line"], f["audience"], f["quote"]) for f in out] == [
        ("limit.setting", 2, "tool", raw[1])]
