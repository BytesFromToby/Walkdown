"""Tests for pairs.py, written from specs/pairs.SPEC.md."""
import pairs


def reports(s2=(), s3=(), s4=()):
    return {"01": {"findings": []}, "02": {"findings": list(s2)},
            "03": {"findings": list(s3)}, "04": {"findings": list(s4)}}


def hit(file, line, check="phrase.L.override"):
    return {"check": check, "file": file, "line": line, "quote": "Ignore all.",
            "patterns": ["L.ignore"], "audience": "model"}


def div(file, line, text, reading="A-only"):
    return {"check": "read.divergence", "file": file, "line": line, "reading": reading,
            "text": text, "carrier": "comment", "method": "static-style"}


def kinds(r):
    return [p["pair"] for p in pairs.pairs(r)]


def test_orphan():
    r = reports(s3=[{"check": "graph.orphan", "file": "notes.md", "line": None}],
                s4=[hit("notes.md", 5)])
    out = pairs.pairs(r)
    assert len(out) == 1
    p = out[0]
    assert p["check"] == "cap.pair" and p["pair"] == "orphan+phrase"
    assert (p["file"], p["line"]) == ("notes.md", 5)
    assert p["phrase_check"] == "phrase.L.override"
    assert p["patterns"] == ["L.ignore"] and p["quote"] == "Ignore all."
    assert [e["stage"] for e in p["evidence"]] == ["04", "03"]
    assert p["evidence"][1]["check"] == "graph.orphan"


def test_dynamic():
    dyn = {"check": "graph.depth", "file": "p/s.md", "line": None, "depth": 1,
           "from": "SKILL.md", "via": "dynamic"}
    assert kinds(reports(s3=[dyn], s4=[hit("p/s.md", 5)])) == ["dynamic+phrase"]
    stat = dict(dyn, via="static")
    assert kinds(reports(s3=[stat], s4=[hit("p/s.md", 5)])) == []


def test_hidden():
    assert kinds(reports(s2=[div("r.md", 7, "Disregard")], s4=[hit("r.md", 7)])) == [
        "hidden+phrase"]
    assert kinds(reports(s2=[div("r.md", 5, "a\nb\nc")], s4=[hit("r.md", 7)])) == [
        "hidden+phrase"]
    assert kinds(reports(s2=[div("r.md", 5, "a\nb")], s4=[hit("r.md", 7)])) == []
    assert kinds(reports(s2=[div("r.md", 7, "x", reading="B-only")], s4=[hit("r.md", 7)])) == []
    assert kinds(reports(s2=[div("other.md", 7, "x")], s4=[hit("r.md", 7)])) == []
    fold = {"check": "read.fold", "file": "r.md", "line": 7, "folded": "x", "removed": ["U+200B"]}
    out = pairs.pairs(reports(s2=[fold], s4=[hit("r.md", 7)]))
    assert [p["pair"] for p in out] == ["hidden+phrase"]
    assert out[0]["evidence"][1]["check"] == "read.fold"


def test_two_kinds():
    r = reports(s2=[div("n.md", 5, "x")],
                s3=[{"check": "graph.orphan", "file": "n.md", "line": None}],
                s4=[hit("n.md", 5)])
    assert kinds(r) == ["orphan+phrase", "hidden+phrase"]


def test_no_hits():
    r = reports(s3=[{"check": "graph.orphan", "file": "n.md", "line": None}])
    assert pairs.pairs(r) == []


def test_carrier_only_hit_makes_no_hidden_pair():
    # a link definition is the hidden carrier; K.md-carrier on it is the same fact
    link = dict(hit("CHANGELOG.md", 9), check="phrase.K.exfil", patterns=["K.md-carrier"])
    both = dict(hit("CHANGELOG.md", 9), check="phrase.K.exfil",
                patterns=["K.md-carrier", "K.data-flow"])
    d = div("CHANGELOG.md", 9, "[1.0]: https://x.invalid/compare")
    assert kinds(reports(s2=[d], s4=[link])) == []
    assert kinds(reports(s2=[d], s4=[both])) == ["hidden+phrase"]


def hook(event="SessionStart", cmd='bash "${CLAUDE_PLUGIN_ROOT}/hooks/start.sh"'):
    return {"check": "struct.hooks", "file": "hooks/hooks.json", "line": None, "event": event,
            "matcher": None, "command": cmd}


GRAPH = {"nodes": [{"path": p} for p in ["hooks/hooks.json", "hooks/start.sh", "hooks/real.sh",
                                         "scripts/other.sh"]],
         "edges": [{"from": "hooks/hooks.json", "to": "hooks/start.sh", "kind": "static",
                    "text": "hooks/start.sh"},
                   {"from": "hooks/start.sh", "to": "hooks/real.sh", "kind": "static",
                    "text": "real.sh"}]}


def instr(file, line, pattern="C.script-instruction"):
    return {"check": "phrase.C.second-order", "file": file, "line": line,
            "quote": 'MSG="Run: npx x install"', "patterns": [pattern], "audience": "tool"}


def test_hook_phrase_pair():
    r = reports(s4=[instr("hooks/start.sh", 4), instr("hooks/real.sh", 2),
                    instr("scripts/other.sh", 3)])
    r["01"]["findings"] = [hook()]
    got = {(p["file"], p["line"]) for p in pairs.pairs(r, GRAPH) if p["pair"] == "hook+phrase"}
    # the hook's script, and the script it calls one hop on; never an unrelated script
    assert got == {("hooks/start.sh", 4), ("hooks/real.sh", 2)}


def test_hook_phrase_needs_injecting_event_and_instruction_pattern():
    r = reports(s4=[instr("hooks/start.sh", 4)])
    r["01"]["findings"] = [hook(event="PostToolUse")]
    assert "hook+phrase" not in kinds_g(r)
    r = reports(s4=[instr("hooks/start.sh", 4, pattern="K.http-verb")])
    r["01"]["findings"] = [hook()]
    assert "hook+phrase" not in kinds_g(r)
    assert kinds_g(reports(s4=[instr("hooks/start.sh", 4)])) == []  # no hook, no graph


def kinds_g(r):
    return [p["pair"] for p in pairs.pairs(r, GRAPH)]


def test_part2_tables_do_not_pair():
    row = {"check": "rubric.action", "file": "notes.md", "line": 5, "quote": "Post it.",
           "patterns": ["J.confirm-first"], "audience": "model"}
    r = reports(s3=[{"check": "graph.orphan", "file": "notes.md", "line": None}], s4=[row])
    assert pairs.pairs(r) == []
