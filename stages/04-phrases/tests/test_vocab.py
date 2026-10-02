"""Tests for vocab.py, written from specs/vocab.SPEC.md."""
import pytest

from patterns import load_table
from vocab import DEFAULT_VOCAB, VocabError, load_vocab

TABLE = """patterns:
  - id: J.a
    check: phrase.J.prohibited
    regex: 'send'
    source: 'PHRASES:J'
"""


def test_shipped_vocab_loads():
    v = load_vocab(rows=load_table())
    assert v.tiers and set(v.tiers.values()) <= {"prohibited", "confirm-first"}
    j_rows = [r.id for r in load_table() if r.check == "phrase.J.prohibited"]
    assert set(j_rows) == set(v.tiers)
    assert v.confirm and v.tlds and v.registry


def test_kind_order():
    v = load_vocab()
    assert [k for k, _ in v.kinds] == ["harness", "clock", "version", "state", "environment",
                                      "absence", "error"]


def _write(tmp_path, text):
    p = tmp_path / "v.yaml"
    p.write_text(text, encoding="utf-8")
    return p


def _shipped():
    return DEFAULT_VOCAB.read_text("utf-8")


def test_untiered_j_row(tmp_path):
    t = tmp_path / "t.yaml"
    t.write_text(TABLE, encoding="utf-8")
    with pytest.raises(VocabError):
        load_vocab(rows=load_table(t))


def test_bad_regex(tmp_path):
    text = _shipped().replace("explicit_keyword: '", "explicit_keyword: '(unclosed ", 1)
    with pytest.raises(VocabError):
        load_vocab(_write(tmp_path, text))


def test_missing_source(tmp_path):
    text = _shipped().replace(
        "  safety:\n    source: 'CONTEXT-part2 section 4 and METHOD",
        "  safety:\n    nosource: 'CONTEXT-part2 section 4 and METHOD", 1)
    assert text != _shipped()
    with pytest.raises(VocabError):
        load_vocab(_write(tmp_path, text))


def test_no_backspace_bytes():
    assert b"\x08" not in DEFAULT_VOCAB.read_bytes()
