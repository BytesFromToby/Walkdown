"""Tests for invisible.py, written from specs/invisible.SPEC.md."""
from invisible import decode, strip_line


def test_zero_width_split_path():
    assert strip_line("refer\u200bences/de\u200dtails.md") == "references/details.md"


def test_bidi_soft_hyphen_tags_removed_ascii_kept():
    line = "a\u202eb\u202c c\u00add " + "".join(chr(0xE0000 + ord(c)) for c in "hi") + "x.md"
    assert strip_line(line) == "ab cd x.md"
    plain = "See `SKILL.md` for l1 and 0m."
    assert strip_line(plain) == plain


def test_nfkc():
    assert strip_line("\uff44\uff4f\uff43\uff53\uff0f\uff41.md") == "docs/a.md"


def test_no_confusable_fold():
    assert strip_line("d\u043ecs/a.md") == "d\u043ecs/a.md"


def test_decode():
    assert decode("h\u00e9\n".encode("utf-8")) == "h\u00e9\n"
    assert decode(b"\xef\xbb\xbfhi\n") == "hi\n"
    assert decode("hi\n".encode("utf-16")) == "hi\n"
    assert decode(b"\x00\x01\x02binary") is None
