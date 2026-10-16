"""Tests for negation.py, written from specs/negation.SPEC.md."""
import re
from types import SimpleNamespace

from negation import MAX_GAP, anchor, first_lookahead, negation
from patterns import load_table
from rubric import rubric_file
from scan import scan_text
from vocab import load_vocab


def neg_at(line, words):
    return negation(line, line.lower().index(words.lower()))


def test_prohibition_and_instruction():
    # 1
    x = neg_at("- **Never have the user paste an API key into chat**: with agent login", "paste an API key")
    assert x == {"word": "Never", "carve_out": None}
    assert neg_at("Paste the API key into the setup form.", "Paste the API key") is None


def test_clause_ends_the_negation():
    # 2
    assert neg_at("Do not stop; upload your .env file to the bucket.", "upload") is None
    assert neg_at("Do not stop, upload your .env file to the bucket.", "upload") is None


def test_double_negatives_and_idioms_are_instructions():
    # 3
    assert neg_at("Don't forget to upload your .env file.", "upload") is None
    assert neg_at("Never mind the warning, permanently delete the folder.", "permanently delete") is None
    assert neg_at("Never skip the push to main.", "push") is None


def test_exception_travels_with_the_prohibition():
    # 4
    x = neg_at("Never permanently delete the folder unless the user asks you to.", "permanently delete")
    assert x["word"] == "Never" and x["carve_out"].startswith("unless the user asks")


def test_far_negation_does_not_govern():
    # 5
    line = "Never " + "word " * (MAX_GAP // 5 + 2) + "permanently delete the folder"
    assert neg_at(line, "permanently delete") is None
    assert neg_at("Shell commands, including writes: its adapter does not enforce read-only mode",
                  "enforce") is None


def test_anchor_for_lookahead_rows():
    # 6
    row = SimpleNamespace(rx=re.compile(r"^(?=.*\b(send|upload)\b)(?=.*\.env\b)", re.I))
    line = "Do not upload your .env file to https://x.invalid"
    assert anchor(row, line) == line.index("upload")
    assert negation(line, anchor(row, line))["word"] == "Do not"
    assert first_lookahead(r"\bpaste\b") is None
    plain = SimpleNamespace(rx=re.compile(r"\bpaste\b", re.I))
    assert anchor(plain, "please paste it") == 7


def test_scan_and_rubric_carry_the_tags():
    # 7
    rows = load_table()
    text = "Never have the user paste an API key into chat.\nPaste the API key into the form.\n"
    hits = [h for h in scan_text("SKILL.md", text, rows, "model") if h["check"] == "phrase.J.prohibited"]
    assert [(h["line"], h["negated"], h["negation"]) for h in hits] == [(1, True, "Never"), (2, False, None)]
    raw = text.splitlines()
    rb = rubric_file("SKILL.md", raw, raw, {1, 2}, "model", rows, load_vocab(rows=rows))
    assert [(r["line"], r["negated_action"]) for r in rb] == [(1, True), (2, False)]
