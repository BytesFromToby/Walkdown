"""Tests for drift.py, written from specs/drift.SPEC.md."""
import json
import os
import time

import drift

SECRET = "ZZREPOTEXTZZ"


def run(tmp, name, s1=(), s4=(), s5=(), pin_hash="aaa"):
    d = tmp / name
    (d / "data").mkdir(parents=True)
    (d / "LOG.md").write_text("log", encoding="utf-8")
    docs = {"01-inventory": [{"check": "inv.pin", "file": None, "line": None, "hash": pin_hash,
                              "hash_kind": "git", "files": len(s1)}] + list(s1),
            "03-graph": [], "04-phrases": list(s4), "05-capability": list(s5)}
    for stage, f in docs.items():
        (d / "data" / f"{stage}.json").write_text(json.dumps({"stage": stage, "contract": 1,
                                                              "findings": f}), encoding="utf-8")
    return d


def inv(f, sha, bytes_=10, entry=None):
    return {"check": "inv.file", "file": f, "line": None, "sha256": sha, "bytes": bytes_,
            "entry_point": entry}


OLD1 = [inv("SKILL.md", "a1", entry="skill"), inv("lib.py", "b1"), inv("gone.md", "c1"),
        {"check": "struct.agent-tools", "file": "agents/x.md", "line": None, "tools": ["Read"]}]
NEW1 = [inv("SKILL.md", "a2", entry="skill"), inv("lib.py", "b1"), inv("new.md", "d1"),
        {"check": "struct.agent-tools", "file": "agents/x.md", "line": None, "tools": None},
        {"check": "struct.hooks", "file": "hooks/hooks.json", "line": None, "event": "SessionStart",
         "matcher": None, "command": f"run {SECRET}"},
        {"check": "struct.mcp", "file": ".mcp.json", "line": None, "name": "srv", "command": "x",
         "url": None},
        {"check": "struct.description", "file": "SKILL.md", "line": None, "text": f"now {SECRET}"}]
HIT = {"check": "phrase.K.exfil", "file": "SKILL.md", "line": 4, "quote": f"send it {SECRET}",
       "audience": "model", "patterns": ["K.dns"]}
MOVED_OLD = {"check": "phrase.L.override", "file": "SKILL.md", "line": 9, "quote": "ignore that",
             "audience": "model"}
MOVED_NEW = dict(MOVED_OLD, line=30)
LEG = lambda leg, p: {"check": "cap.leg", "file": None, "line": None, "leg": leg, "present": p,
                      "evidence": []}


def test_compare_finds_each_kind_of_change(tmp_path):
    a = drift.load(run(tmp_path, "a", OLD1, [MOVED_OLD], [LEG("external-comms", False)]))
    b = drift.load(run(tmp_path, "b", NEW1, [MOVED_NEW, HIT], [LEG("external-comms", True),
                   {"check": "cap.grant", "file": None, "line": None, "grant": "exec-at-load",
                    "evidence": []}], pin_hash="bbb"))
    c = drift.compare(a, b)
    assert c["files_added"] == ["new.md"] and c["files_removed"] == ["gone.md"]
    assert c["files_changed"] == ["SKILL.md"]  # lib.py has the same hash
    assert c["grants_changed"] == [("agents/x.md", "Read", "inherits all tools")]
    assert len(c["hooks_added"]) == 1 and len(c["mcp_added"]) == 1 and len(c["desc_changed"]) == 1
    assert c["hits_added"] == [HIT] and c["hits_removed"] == []  # a moved line is not new
    assert c["legs_changed"] == [("external-comms", False, True)]
    assert c["capgrants_added"] == ["exec-at-load"]


def test_older_run_without_hashes_is_flagged_not_guessed(tmp_path):
    old = [dict(inv("a.md", None), bytes=5), dict(inv("b.md", None), bytes=5)]
    new = [inv("a.md", "x", bytes_=5), inv("b.md", "y", bytes_=6)]
    c = drift.compare(drift.load(run(tmp_path, "a", old)), drift.load(run(tmp_path, "b", new)))
    assert c["files_changed"] == ["b.md"] and c["files_unverified"] == ["a.md"]


def test_summary_lines_carry_no_repository_text(tmp_path):
    a = drift.load(run(tmp_path, "a", OLD1))
    b = drift.load(run(tmp_path, "b", NEW1, [HIT], pin_hash="bbb"))
    text = "\n".join(drift.summary_lines(drift.compare(a, b)))
    assert SECRET not in text and "hooks added" in text and "1 of the new phrase hits" in text
    assert drift.summary_lines(drift.compare(a, a)) == ["no differences in what Walkdown records"]


def test_report_and_previous_run(tmp_path):
    a = run(tmp_path, "2026-01-01_aaa", OLD1)
    time.sleep(0.01)
    b = run(tmp_path, "2026-01-02_bbb", NEW1, [HIT], pin_hash="bbb")
    os.utime(a / "LOG.md", (1, 1))
    assert drift.previous_run(b) == a and drift.previous_run(a) == b
    out, c = drift.write_report(a, b)
    md = out.read_text(encoding="utf-8")
    assert out == b / "changes.md" and "## Hooks added (1)" in md and "Trifecta" not in md
    assert drift.main([str(a)]) == 2
