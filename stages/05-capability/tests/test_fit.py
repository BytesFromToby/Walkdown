"""Tests for fit.py, written from specs/fit.SPEC.md."""
import fit


def entry(file, kind, grants=None, disallowed=(), preloads=None, name=None, mode="auto"):
    return {"check": "trig.entry", "file": file, "kind": kind, "mode": mode, "grants": grants,
            "grants_line": 4, "disallowed": list(disallowed), "preloads": preloads, "name": name}


def ask(file, family, line=7):
    return {"check": "ask.tools", "file": file, "family": family, "lines": [line]}


def reports(*rows, s1=()):
    return {"01": {"findings": list(s1)}, "04": {"findings": list(rows)}}


def by(fs, check, **kw):
    return [f for f in fs if f["check"] == check and all(f.get(k) == v for k, v in kw.items())]


def test_unused_missing_and_inherits_without_a_graph():
    r = reports(
        entry("agents/a.md", "agent", ["Read", "Bash", "Write", "WebFetch", "mcp__gh__create_issue", "mcp__db__q"]),
        ask("agents/a.md", "shell"), ask("agents/a.md", "agent"),
        {"check": "ask.named", "file": "agents/a.md", "tool": "Write", "lines": [9]},
        {"check": "ask.named", "file": "agents/a.md", "tool": "mcp__gh", "lines": [9]},
        entry("agents/b.md", "agent", None), ask("agents/b.md", "write"),
        entry("agents/c.md", "agent", None, mode="skipped"), ask("agents/c.md", "web"),
    )
    fs = fit.entries_fit(r, None)
    assert {f["tool"] for f in by(fs, "fit.unused", file="agents/a.md")} == {"WebFetch", "mcp__db__q"}
    assert [(f["family"], f["asked_at"]) for f in by(fs, "fit.missing")] == [("agent", "agents/a.md:7")]
    assert by(fs, "fit.inherits", file="agents/b.md")[0]["families"] == ["write"]
    assert not [f for f in fs if f["file"] == "agents/c.md"]


def test_skills_preloads_and_disallowed():
    r = reports(
        entry("skills/s/SKILL.md", "skill", ["Bash", "WebSearch"], disallowed=["Write", "Edit", "NotebookEdit",
                                                                            "MultiEdit"], name="s"),
        ask("skills/s/SKILL.md", "shell"), ask("skills/s/SKILL.md", "write"),
        entry("agents/p.md", "agent", ["Read", "Bash"], preloads=["s"]),
    )
    fs = fit.entries_fit(r, None)
    [u] = by(fs, "fit.unused", file="skills/s/SKILL.md")
    assert (u["tool"], u["pre_approved"]) == ("WebSearch", True)
    [m] = by(fs, "fit.missing", file="skills/s/SKILL.md")
    assert m["family"] == "write" and "disallowed" in m["why"]
    # the preloaded skill's words count for the agent: its Bash is used, and write is missing
    assert not by(fs, "fit.unused", file="agents/p.md")
    assert [f["family"] for f in by(fs, "fit.missing", file="agents/p.md")] == ["write"]


def test_reach_through_the_graph():
    graph = {"edges": [{"from": "agents/t.md", "to": "skills/x/SKILL.md", "kind": "static"}]}
    r = reports(entry("agents/t.md", "agent", ["Read", "Bash"]), ask("skills/x/SKILL.md", "shell"),
                s1=[{"check": "inv.file", "file": f} for f in ("agents/t.md", "skills/x/SKILL.md")])
    assert not by(fit.entries_fit(r, graph), "fit.unused")


def test_hooks():
    s1 = [{"check": "struct.hooks", "file": "h.json", "line": None, "event": e, "matcher": m, "command": c}
          for e, m, c in (("UserPromptSubmit", None, "a"), ("PreToolUse", "*", "b"), ("PostToolUse", "Edit|Write", "c"),
                          ("SessionStart", None, "d"), ("Notification", None, "e"))]
    inj = [{"mechanism": "hook", "file": "h.json", "event": "UserPromptSubmit", "command": "a", "bytes": 12000}]
    fs = fit.hooks_fit({"01": {"findings": s1}}, inj)
    got = [(f["event"], f["how_often"], f["adds_context"], f["bytes"], f["over_cap"]) for f in fs]
    assert got == [("UserPromptSubmit", "every-prompt", True, 12000, True),
                   ("PreToolUse", "every-tool-call", False, None, False),
                   ("PostToolUse", "matching-tool-calls", False, None, False),
                   ("SessionStart", "once-a-session", True, None, False),
                   ("Notification", "other", False, None, False)]
    other = [{"check": "struct.hooks", "file": f, "line": None, "event": e, "matcher": None, "command": "x"}
             for f, e in ((".cursor/hooks.json", "sessionStart"), ("hooks/hooks.json", "sessionStart"),
                          (".github/hooks/a.json", "userPromptSubmitted"))]
    got = [(f["host"], f["how_often"], f["adds_context"]) for f in fit.hooks_fit({"01": {"findings": other}}, [])]
    assert got == [("cursor", "once-a-session", None), ("claude", "once-a-session", None), ("copilot", "other", None)]
