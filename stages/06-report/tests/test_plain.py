"""Tests for plain.py, written from specs/report.SPEC.md, review_html (Done when 7). The words are the `plain`
field of each row of Library/patterns.yaml (restructure step 3b)."""
import sys
from pathlib import Path

import yaml

import plain

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import library  # noqa: E402

PATTERNS = library.path("patterns.yaml")


def test_every_pattern_has_plain_words_and_nothing_else():
    rows = yaml.safe_load(PATTERNS.read_text(encoding="utf-8"))["patterns"]
    ids = {r["id"] for r in rows}
    assert [r["id"] for r in rows if not str(r.get("plain", "")).strip()] == [], "patterns with no plain words"
    assert ids - set(plain.PLAIN) == set(), "patterns with no plain words"
    assert set(plain.PLAIN) - ids == set(), "plain words for patterns that do not exist"
    assert all(plain.PLAIN[r["id"]] == r["plain"] for r in rows)


def test_each_says_the_worry_and_has_no_em_dash():
    for pid, words in plain.PLAIN.items():
        assert "The worry: " in words, pid
        assert "—" not in words, pid


def test_describe_keeps_order_drops_repeats_and_names_retired():
    out = plain.describe(["L.ignore", "K.dns", "L.ignore", "H.report-only"])
    assert [p for p, _ in out] == ["L.ignore", "K.dns", "H.report-only"]
    assert out[0][1] == plain.PLAIN["L.ignore"] and "no longer" in out[2][1]
