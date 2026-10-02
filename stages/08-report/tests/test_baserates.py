"""Tests for baserates.py, written from specs/baserates.SPEC.md."""
import baserates


def _f(pat, line, audience="model", check="phrase.L.override", **kw):
    return {"check": check, "file": "a.md", "line": line, "patterns": [pat], "audience": audience, **kw}


def test_count_lines_outside_human_files_once_per_line():
    rep = {"findings": [_f("L.ignore", 1), _f("L.ignore", 1, check="phrase.H.anti-review"),
                        _f("L.ignore", 2, audience="tool"), _f("L.ignore", 3, audience="human"),
                        _f("K.dns", 4, skipped="x"),
                        {"check": "term.def", "file": "a.md", "line": 5, "audience": "model"}]}
    assert baserates.count(rep) == {"L.ignore": 2}


def test_levels_bin_the_repo_count():
    assert [baserates.level(n) for n in (0, 1, 2, 5)] == ["rare", "uncommon", "common", "common"]


def test_rate_and_phrase():
    t = {"repos": [{"hash": "a", "lines": {"X": 3}}, {"hash": "b", "lines": {}}]}
    rt = baserates.rate(t, "X")
    assert rt == {"pattern": "X", "repos": 2, "repos_hit": 1, "lines": 3, "level": "uncommon"}
    assert baserates.phrase(rt) == "uncommon: in 1 of 2 other audited repos, 3 lines"
    assert baserates.rate(t, "X", exclude_hash="a")["level"] == "rare"
    assert baserates.rate(None, "X") is None and baserates.phrase(None) == ""


def test_shipped_table_loads():
    t = baserates.load()
    assert t and len(t["repos"]) >= 1 and all("hash" in r and "lines" in r for r in t["repos"])
