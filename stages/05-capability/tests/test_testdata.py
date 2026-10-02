"""Tests for testdata.py, written from specs/testdata.SPEC.md."""
import testdata


def reports(s1=(), s3=(), s4=()):
    return {"01": {"findings": list(s1)}, "02": {"findings": []},
            "03": {"findings": list(s3)}, "04": {"findings": list(s4)}}


S1 = [{"check": "inv.pin", "file": None, "line": None},
      {"check": "struct.hooks", "file": "tests/plugin/hooks/hooks.json", "line": None},
      {"check": "struct.hooks", "file": "hooks/hooks.json", "line": None}]
S4 = [{"check": "phrase.K.exfil", "file": "tests/a.md", "line": 2, "audience": "test-data"},
      {"check": "phrase.K.exfil", "file": "SKILL.md", "line": 3, "audience": "model"}]


def test_set_aside_drops_test_data_and_counts_it():
    out, aside = testdata.set_aside(reports(S1, s4=S4))
    assert [f["file"] for f in out["01"]["findings"]] == [None, "hooks/hooks.json"]
    assert [f["file"] for f in out["04"]["findings"]] == ["SKILL.md"]
    assert aside == [{"check": "cap.testdata", "file": None, "line": None, "stage1": 1,
                      "stage4": 1, "top_folders": ["tests"]}]
    _, none = testdata.set_aside(reports([S1[0], S1[2]], s4=[S4[1]]))
    assert none == []


def test_loaded_test_data_is_kept_and_paired():
    s3 = [{"check": "graph.depth", "file": "tests/a.md", "line": None, "via": "static",
           "from": "SKILL.md", "depth": 1},
          {"check": "graph.depth", "file": "tests/b.md", "line": None, "via": "static",
           "from": "README.md", "depth": 1},
          {"check": "graph.depth", "file": "tests/c.md", "line": None, "via": "mention",
           "from": "SKILL.md", "depth": 1},
          {"check": "graph.depth", "file": "tests/d.md", "line": None, "via": "static",
           "from": "tests/a.md", "depth": 2}]
    r = reports(S1, s3, S4)
    pairs = testdata.loaded_pairs(r)
    assert [(p["file"], p["from"], p["pair"]) for p in pairs] == [("tests/a.md", "SKILL.md", "testdata+loaded")]
    out, aside = testdata.set_aside(r, {"tests/a.md"})
    assert "tests/a.md" in [f["file"] for f in out["04"]["findings"]]
    assert aside[0]["stage4"] == 0
