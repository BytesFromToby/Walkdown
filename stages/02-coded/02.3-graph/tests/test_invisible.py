"""Tests for invisible.py, written from specs/graph.SPEC.md, invisible."""
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


def test_the_new_invisible_characters_split_nothing():
    """P1 (2026-10-29): a reference split by a format character, a blank letter, or a run of variation
    selectors still reads whole; one selector alone stays (it is ordinary after an emoji or a CJK character)."""
    for ch in ("\u180e", "\u034f", "\u206a", "\ufff9", "\U0001d173", "\U0001bca0", "\u061c", "\u3164",
               "\u115f", "\uffa0", "\u17b4", "\u2800"):
        assert strip_line(f"refer{ch}ences/details.md") == "references/details.md", ascii(ch)
    assert strip_line("refer\ufe0f\ufe0fences/details.md") == "references/details.md"
    assert strip_line("refer\U000e0100\U000e0101ences/details.md") == "references/details.md"
    assert strip_line("refer\u180b\u180cences/details.md") == "references/details.md"
    assert strip_line("see ✔\ufe0f docs/a.md") == "see ✔\ufe0f docs/a.md"
    # zero-width spaces between the selectors do not break the run; one selector before one stays
    assert strip_line("refer\ufe0f\u200b\ufe0fences/details.md") == "references/details.md"
    assert strip_line("refer\ufe0f\u200bences/details.md") == "refer\ufe0fences/details.md"


def test_nul_is_text_and_stripped():
    from invisible import decode, strip_line
    assert decode(b"see a\x00b.md" + b" " * 300) is not None
    assert decode(b"\x00" * 50 + b"abc") is None
    assert strip_line("ref\x00s.md") == "refs.md"
