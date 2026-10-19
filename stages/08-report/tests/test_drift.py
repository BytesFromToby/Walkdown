"""Tests for drift.py, written from specs/drift.SPEC.md."""
import json
import os
import time

import drift

SECRET = "ZZREPOTEXTZZ"


def run(tmp, name, s1=(), s4=(), s5=(), pin_hash="aaa", terms=None):
    d = tmp / name
    (d / "data").mkdir(parents=True)
    (d / "LOG.md").write_text("log", encoding="utf-8")
    docs = {"01-inventory": [{"check": "inv.pin", "file": None, "line": None, "hash": pin_hash,
                              "hash_kind": "git", "files": len(s1)}] + list(s1),
            "03-graph": [], "04-phrases": list(s4), "05-capability": list(s5)}
    for stage, f in docs.items():
        doc = {"stage": stage, "contract": 1, "findings": f}
        if stage == "04-phrases" and terms is not None:
            doc["terms"] = terms
        (d / "data" / f"{stage}.json").write_text(json.dumps(doc), encoding="utf-8")
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


# Review C22 b (2026-10-19): where a new or gone hit came from.

def terms(rows, code="c1", vocab="w1"):
    return {"version": "v-" + "-".join(f"{k}{v}" for k, v in sorted(rows.items())), "count": len(rows),
            "rows": rows, "vocab": vocab, "code": code}


SAME = [inv("SKILL.md", "a1"), inv("lib.md", "b1")]
EDITED = [inv("SKILL.md", "a2"), inv("lib.md", "b1")]


def hit(file, pats, quote):
    return {"check": "phrase.E.env", "file": file, "line": 3, "quote": quote, "audience": "model",
            "patterns": pats}


def test_each_hit_says_where_it_came_from(tmp_path):
    old_t = terms({"E.a": "1", "E.b": "2", "E.gone": "3"})
    new_t = terms({"E.a": "1", "E.b": "9", "E.new": "4"}, code="c2")
    old = [hit("lib.md", ["E.gone"], "retired row"), hit("lib.md", ["E.a"], "matcher now misses")]
    new = [hit("SKILL.md", ["E.a"], "edited file"), hit("lib.md", ["E.new"], "added row"),
           hit("lib.md", ["E.b"], "changed row"), hit("lib.md", ["E.a"], "matcher now finds")]
    c = drift.compare(drift.load(run(tmp_path, "a", SAME, old, terms=old_t)),
                      drift.load(run(tmp_path, "b", EDITED, new, pin_hash="bbb", terms=new_t)))
    added = {h["quote"]: k for h, k in zip(c["hits_added"], c["hits_added_cause"])}
    assert added == {"edited file": "repo", "added row": "terms", "changed row": "terms",
                     "matcher now finds": "code"}
    gone = {h["quote"]: k for h, k in zip(c["hits_removed"], c["hits_removed_cause"])}
    assert gone == {"retired row": "terms", "matcher now misses": "code"}
    lines = drift.summary_lines(c)
    assert ("Walkdown changed since the older run: 3 search terms (1 added, 1 changed, 1 retired), "
            "matching code changed") in lines
    assert ("new phrase hits: 1 from changes in the repository, 2 from Walkdown's search terms, "
            "1 from Walkdown's matching code") in lines
    assert "phrase hits gone: 1 from Walkdown's search terms, 1 from Walkdown's matching code" in lines


def test_without_a_term_version_walkdown_is_named_not_guessed(tmp_path):
    a = drift.load(run(tmp_path, "a", SAME, []))
    b = drift.load(run(tmp_path, "b", SAME, [hit("lib.md", ["E.a"], "new")], terms=terms({"E.a": "1"})))
    c = drift.compare(a, b)
    assert c["terms"]["known"] is False and c["hits_added_cause"] == ["walkdown"]
    assert drift.summary_lines(c)[-1] == ("new phrase hits: 1 from Walkdown (the older run recorded no "
                                          "search-term version)")
    old = [dict(inv("lib.md", None), bytes=10)]
    c = drift.compare(drift.load(run(tmp_path, "c", old, [])),
                      drift.load(run(tmp_path, "d", [inv("lib.md", "b1")], [hit("lib.md", ["E.a"], "x")])))
    assert c["hits_added_cause"] == ["unverified"]


def test_repository_changes_alone_add_no_cause_line(tmp_path):
    t = terms({"E.a": "1"})
    c = drift.compare(drift.load(run(tmp_path, "a", SAME, [], terms=t)),
                      drift.load(run(tmp_path, "b", EDITED, [hit("SKILL.md", ["E.a"], "x")], pin_hash="b", terms=t)))
    lines = drift.summary_lines(c)
    assert not any(x.startswith(("Walkdown changed", "new phrase hits:")) for x in lines)


def test_since_same_version(tmp_path):
    """The same repository version: nothing to say when nothing differs; when a hit differs,
    the report is written and says every difference comes from Walkdown."""
    t = terms({"E.a": "1"})
    a = run(tmp_path, "2026-01-01_aaa", SAME, [], terms=t)
    b = run(tmp_path, "2026-01-02_aaa", SAME, [], terms=t)
    s = drift.since(a, b)
    assert (s["same"], s["differs"], s["report"]) == (True, False, None)
    assert not (b / "changes.md").exists()
    c = run(tmp_path, "2026-01-03_aaa", SAME, [hit("lib.md", ["E.new"], "x")],
            terms=terms({"E.a": "1", "E.new": "2"}))
    s = drift.since(a, c)
    assert (s["same"], s["differs"]) == (True, True)
    md = s["report"].read_text(encoding="utf-8")
    assert "Same version of the repository in both runs: every difference below comes from Walkdown." in md
    assert "## Walkdown's search terms and matching code (1)" in md and "- added: E.new" in md
    assert "(Walkdown's search terms)" in md
    assert "new phrase hits: 1 from Walkdown's search terms" in s["lines"]
    s = drift.since(a, run(tmp_path, "2026-01-04_bbb", EDITED, [], pin_hash="bbb", terms=t))
    assert (s["same"], s["differs"]) == (False, True) and s["report"].is_file()
