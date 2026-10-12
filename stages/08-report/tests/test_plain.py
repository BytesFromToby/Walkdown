"""Tests for plain.py, written from specs/review_html.SPEC.md (Done when 7)."""
from pathlib import Path

import yaml

import plain

PATTERNS = Path(__file__).resolve().parents[2] / "04-phrases" / "patterns.yaml"


def test_every_pattern_has_plain_words_and_nothing_else():
    rows = yaml.safe_load(PATTERNS.read_text(encoding="utf-8"))["patterns"]
    ids = {r["id"] for r in rows}
    assert ids - set(plain.PLAIN) == set(), "patterns with no plain words"
    assert set(plain.PLAIN) - ids == set(), "plain words for patterns that do not exist"


def test_each_says_the_worry_and_has_no_em_dash():
    for pid, words in plain.PLAIN.items():
        assert "The worry: " in words, pid
        assert "—" not in words, pid


def test_describe_keeps_order_drops_repeats_and_names_retired():
    out = plain.describe(["L.ignore", "K.dns", "L.ignore", "H.report-only"])
    assert [p for p, _ in out] == ["L.ignore", "K.dns", "H.report-only"]
    assert out[0][1] == plain.PLAIN["L.ignore"] and "no longer" in out[2][1]
