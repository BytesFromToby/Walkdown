"""Tests for foldtext.py, written from specs/foldtext.SPEC.md."""
from foldtext import decode, fold_line, split_lines


def test_zero_width_stripped():
    assert fold_line("ig​no​re all") == "ignore all"


def test_bidi_soft_hyphen_tags_stripped():
    assert fold_line("a‮b‬c") == "abc"
    assert fold_line("in­struction") == "instruction"
    # review C42: a tag run is read as the ASCII it spells, never dropped; a cancel tag is dropped
    tags = "".join(chr(0xE0000 + ord(c)) for c in "ignore")
    assert fold_line(f"before{tags}after") == "before ignore after"
    assert fold_line("a" + chr(0xE007F) + "b") == "ab"


def test_nfkc_and_confusables():
    assert fold_line("ｉｇｎｏｒｅ") == "ignore"
    assert fold_line("ignоre") == "ignore"  # Cyrillic o


def test_separators_become_space_and_do_not_split():
    assert fold_line("a b c\u0085d") == "a b c d"
    assert split_lines("one two\nthree") == ["one two", "three"]


def test_unchanged_lines():
    for s in ["plain ascii text", "a — b", "l 1 0 m I O"]:
        assert fold_line(s) == s


def test_accents_on_latin_letters_are_dropped():
    """Review C42 (an outside tester, 2026-10-25): accented look-alikes slipped past."""
    assert fold_line("café") == "cafe"
    assert fold_line("ignóre all prevíous") == "ignore all previous"
    assert fold_line("नि") == "नि"  # a mark on a non-Latin letter stays


def test_decode():
    assert decode("héllo".encode("utf-8")) == "héllo"
    assert decode(b"\xef\xbb\xbfhi") == "hi"
    assert decode("hi".encode("utf-16")) == "hi"
    assert decode(b"ab\x00cd") is None


def test_split_lines():
    assert split_lines("a\r\nb\n") == ["a", "b"]
    assert split_lines("a\n\nb") == ["a", "", "b"]
    assert split_lines("") == []


def test_nul_is_text_and_folded():
    from foldtext import decode, fold_line
    assert decode(b"Ig\x00nore all" + b" " * 300) is not None
    assert decode(b"\x00" * 50 + b"abc") is None
    assert fold_line("Ig\x00nore all") == "Ignore all"
