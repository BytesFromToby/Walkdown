"""Tests for posture.py, written from specs/posture.SPEC.md."""
import posture


def test_read_only_is_least_privilege():
    w = posture.words(["Read", "Grep", "Glob"])
    assert w == ["read"]
    assert posture.least_privilege(w) is True


def test_builder():
    w = posture.words(["Read", "Write", "Edit", "Bash"])
    assert w == ["execute", "read", "write"]
    assert posture.least_privilege(w) is False


def test_inherit_all():
    assert posture.words(None) == ["all"]
    assert posture.least_privilege(["all"]) is False
    r = {"01": {"findings": [{"check": "struct.agent-tools", "file": "agents/h.md",
                              "line": None, "tools": None, "description": "helps"}]}}
    f = posture.postures(r)[0]
    assert f["tools"] is None and f["posture"] == ["all"] and f["least_privilege"] is False


def test_other_words():
    assert posture.words(["WebFetch"]) == ["network"]
    assert posture.words(["mcp__github__create_issue"]) == ["network"]
    assert posture.words(["Task"]) == ["delegate"]
    assert posture.words(["Frobnicate"]) == ["other"]
    assert posture.words(["read"]) == ["other"]
    assert posture.words(["Bash(git:*)"]) == ["execute"]
    assert posture.words([]) == []


def test_postures_fields():
    r = {"01": {"findings": [
        {"check": "inv.file", "file": "agents/r.md", "line": None},
        {"check": "struct.agent-tools", "file": "agents/r.md", "line": 4,
         "tools": ["Read", "Grep"], "description": "Reads a change."},
    ]}}
    out = posture.postures(r)
    assert len(out) == 1
    f = out[0]
    assert f["check"] == "cap.posture"
    assert (f["file"], f["line"], f["description"]) == ("agents/r.md", 4, "Reads a change.")
    assert f["tools"] == ["Read", "Grep"] and f["least_privilege"] is True
    assert f["evidence"][0]["check"] == "struct.agent-tools"
