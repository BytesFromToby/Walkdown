"""Tests for reach.py, written from specs/reach.SPEC.md."""
from reach import depth_findings, orphan_findings, reach


def test_chain():
    rc = reach(["E", "a", "b"], ["E"], [("E", "a", "static"), ("a", "b", "static")])
    assert rc.depth == {"E": 0, "a": 1, "b": 2}
    assert rc.parent == {"E": None, "a": "E", "b": "a"}
    assert rc.via["b"] == "static"


def test_dynamic_only():
    rc = reach(["E", "g"], ["E"], [("E", "g", "dynamic")])
    assert rc.depth["g"] == 1 and rc.via["g"] == "dynamic" and rc.orphans == []


def test_static_depth_wins_over_shorter_dynamic():
    # A directory mention reaching t in one hop does not flatten its static depth.
    edges = [("E", "t", "dynamic"), ("E", "m", "static"), ("m", "t", "static")]
    rc = reach(["E", "m", "t"], ["E"], edges)
    assert rc.depth["t"] == 2 and rc.via["t"] == "static" and rc.parent["t"] == "m"
    edges = [("E", "a", "dynamic"), ("E", "b", "static"), ("a", "t", "static"),
             ("b", "t", "static")]
    rc = reach(["E", "a", "b", "t"], ["E"], edges)
    assert rc.depth["t"] == 2 and rc.via["t"] == "static" and rc.parent["t"] == "b"


def test_dynamic_only_depth_counts_all_edges():
    # g is reached only through a dynamic hop, then a static one: depth 2, via dynamic.
    edges = [("E", "d", "dynamic"), ("d", "g", "static")]
    rc = reach(["E", "d", "g"], ["E"], edges)
    assert rc.depth == {"E": 0, "d": 1, "g": 2}
    assert rc.via["d"] == "dynamic" and rc.via["g"] == "dynamic" and rc.parent["g"] == "d"


def test_two_entries():
    edges = [("E1", "a", "static"), ("a", "b", "static"), ("b", "c", "static"),
             ("E2", "c", "static")]
    rc = reach(["E1", "E2", "a", "b", "c"], ["E1", "E2"], edges)
    assert rc.depth["c"] == 1 and rc.parent["c"] == "E2"


def test_orphans_and_findings():
    rc = reach(["E", "a", "o"], ["E"], [("E", "a", "static"), ("o", "E", "static"),
                                         ("E", "E", "static"), ("E", "zzz", "static")])
    assert rc.orphans == ["o"]
    of = orphan_findings(rc)
    assert of == [{"check": "graph.orphan", "file": "o", "line": None}]
    df = depth_findings(rc)
    assert [d["file"] for d in df] == ["E", "a"]
    assert df[0] == {"check": "graph.depth", "file": "E", "line": None, "depth": 0,
                     "from": None, "via": "static"}


def test_mention_tier():
    # a mention reaches m; a load reaches d; static wins over both
    edges = [("E", "m", "mention"), ("E", "d", "dynamic"), ("E", "s", "static"),
             ("E", "x", "mention"), ("E", "y", "static"), ("y", "x", "dynamic")]
    rc = reach(["E", "m", "d", "s", "x", "y"], ["E"], edges)
    assert rc.via == {"E": "static", "m": "mention", "d": "dynamic", "s": "static",
                      "x": "dynamic", "y": "static"}
    assert rc.depth["x"] == 2 and rc.parent["x"] == "y" and rc.orphans == []
