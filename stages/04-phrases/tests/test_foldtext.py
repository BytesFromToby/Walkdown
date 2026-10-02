"""Tests for foldtext.py, written from specs/foldtext.SPEC.md."""
from foldtext import decode, fold_line, split_lines


def test_zero_width_stripped():
    assert fold_line("ig​no​re all") == "ignore all"


def test_bidi_soft_hyphen_tags_stripped():
    assert fold_line("a‮b‬c") == "abc"
    assert fold_line("in­struction") == "instruction"
    tags = "".join(chr(0xE0000 + ord(c)) for c in "hi")
    assert fold_line(f"before{tags}after") == "beforeafter"


def test_nfkc_and_confusables():
    assert fold_line("ｉｇｎｏｒｅ") == "ignore"
    assert fold_line("ignоre") == "ignore"  # Cyrillic o


def test_separators_become_space_and_do_not_split():
    assert fold_line("a b c\u0085d") == "a b c d"
    assert split_lines("one two\nthree") == ["one two", "three"]


def test_unchanged_lines():
    for s in ["plain ascii text", "a — b", "café", "l 1 0 m I O"]:
        assert fold_line(s) == s


def test_decode():
    assert decode("héllo".encode("utf-8")) == "héllo"
    assert decode(b"\xef\xbb\xbfhi") == "hi"
    assert decode("hi".encode("utf-16")) == "hi"
    assert decode(b"ab\x00cd") is None


def test_split_lines():
    assert split_lines("a\r\nb\n") == ["a", "b"]
    assert split_lines("a\n\nb") == ["a", "", "b"]
    assert split_lines("") == []
