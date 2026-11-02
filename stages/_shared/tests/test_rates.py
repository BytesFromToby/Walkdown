"""Tests for rates.py, written from specs/shared.SPEC.md, rates."""
import rates


def test_levels_bin_the_repo_count():
    assert [rates.level(n) for n in (0, 1, 2, 5)] == ["rare", "uncommon", "common", "common"]


def test_rate_and_phrase():
    t = {"repos": [{"hash": "a", "lines": {"X": 3}}, {"hash": "b", "lines": {}}]}
    rt = rates.rate(t, "X")
    assert rt == {"pattern": "X", "repos": 2, "repos_hit": 1, "lines": 3, "level": "uncommon"}
    assert rates.phrase(rt) == "uncommon: in 1 of 2 other audited repos, 3 lines"
    assert rates.rate(t, "X", exclude_hash="a")["level"] == "rare"
    assert rates.rate(None, "X") is None and rates.phrase(None) == ""


def test_shipped_table_loads():
    t = rates.load()
    assert t and len(t["repos"]) >= 1 and all("hash" in r and "lines" in r for r in t["repos"])
