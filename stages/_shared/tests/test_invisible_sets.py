"""The invisible-character list moved from three stages into Library/invisible.yaml (restructure
step 3, C4). Each stage's set had to be exactly what it was; the "was" below is written out here as
the three stages once held it (measured 2026-10-28: the three sets are equal). P1 (2026-10-29) then
added to the list: every character held before is handled as before, U+180E aside (it was detected
under the tag-chars kind and never stripped; it is stripped as zero-width now), and the new ones are
written out here too, independent of the file, so a range dropped from the file fails a test.
The list is also held to the Unicode property Default_Ignorable_Code_Point (source S19)."""
import importlib.util
import re
from pathlib import Path

import pytest
import regex
import yaml

import library

STAGES = Path(__file__).resolve().parents[2]


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, STAGES / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


fold = _load("walkdown_s02_fold_inv", "02-coded/02.2-reader/fold.py")
graph_inv = _load("walkdown_s03_invisible_inv", "02-coded/02.3-graph/invisible.py")
foldtext = _load("walkdown_s04_foldtext_inv", "02-coded/02.4-phrases/foldtext.py")


def _span(*pairs):
    return {chr(c) for lo, hi in pairs for c in range(lo, hi + 1)}


# ---- what `02.3-graph` and `02.4-phrases` held: eight ranges
RANGES = [(0x200B, 0x200F), (0x2060, 0x2064), (0xFEFF, 0xFEFF), (0x202A, 0x202E),
          (0x2066, 0x2069), (0x00AD, 0x00AD), (0xE0000, 0xE007F), (0x0000, 0x0000)]
WAS_STRIP = {c for lo, hi in RANGES for c in range(lo, hi + 1)}
WAS_SEPARATORS = {0x2028, 0x2029, 0x0085}

# ---- what `02.2-reader` held: five named sets, and the rule that gave a character its kind
ZERO_WIDTH = {chr(c) for c in list(range(0x200B, 0x2010)) + list(range(0x2060, 0x2065))} | {"﻿"}
BIDI = {chr(c) for c in list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A))}
SOFT_HYPHEN = {"\xad"}
TAGS = {chr(c) for c in range(0xE0000, 0xE0080)}
NUL = {"\x00"}
S2_STRIP = ZERO_WIDTH | BIDI | SOFT_HYPHEN | TAGS | NUL
S2_SEPARATORS = {" ", " ", "\u0085"}


def was_kind(ch):
    if ch in ZERO_WIDTH:
        return "zero-width"
    if ch in BIDI:
        return "bidi"
    if ch in SOFT_HYPHEN:
        return "soft-hyphen"
    if ch in NUL:
        return "nul"
    o = ord(ch)
    if 0xE0000 <= o <= 0xE007F or o == 0x180E:
        return "tag-chars"
    return None


# ---- what the list gained (P1, 2026-10-28 and 2026-10-29)
ADDED_ZERO_WIDTH = _span((0x180E, 0x180E), (0x034F, 0x034F), (0x206A, 0x206F), (0xFFF9, 0xFFFB),
                         (0x1D173, 0x1D17A), (0x1BCA0, 0x1BCA3))
ADDED_BIDI = {"\u061c"}
ADDED_FILLER = _span((0x115F, 0x1160), (0x3164, 0x3164), (0xFFA0, 0xFFA0), (0x17B4, 0x17B5), (0x2800, 0x2800))
RUN = _span((0xFE00, 0xFE0F), (0xE0100, 0xE01EF), (0x180B, 0x180D), (0x180F, 0x180F))
NOW_STRIP = {chr(c) for c in WAS_STRIP} | ADDED_ZERO_WIDTH | ADDED_BIDI | ADDED_FILLER


def now_kind(ch):
    if ch in ADDED_ZERO_WIDTH:
        return "zero-width"
    if ch in ADDED_BIDI:
        return "bidi"
    if ch in ADDED_FILLER:
        return "filler"
    if ch in RUN:
        return "variation-selectors"
    return was_kind(ch)


def test_the_counts_are_what_they_were_and_what_they_are_now():
    assert len(WAS_STRIP) == 150 and len(WAS_SEPARATORS) == 3
    assert len(NOW_STRIP) == 181 and len(RUN) == 260
    inv = library.invisible()
    assert len(inv.strip) == 181 and len(inv.space) == 3 and len(inv.run) == 260
    assert len(inv.kind) == 441  # 181 to strip and 260 in runs; the separators have no kind
    assert inv.run_length == 2


def test_the_three_old_copies_were_equal():
    """The premise of the move; if this fails the list cannot be one list."""
    assert S2_STRIP == {chr(c) for c in WAS_STRIP}
    assert S2_SEPARATORS == {chr(c) for c in WAS_SEPARATORS}


def test_every_character_held_before_is_handled_as_before_but_u180e():
    inv = library.invisible()
    for c in sorted(WAS_STRIP):
        ch = chr(c)
        assert ch in inv.strip and ch in fold.STRIP and c in graph_inv.STRIP and foldtext._TABLE[c] is None
        assert inv.kind[ch] == was_kind(ch), f"U+{c:04X}"
    assert {ch for ch in inv.space} == S2_SEPARATORS and all(ch not in inv.kind for ch in S2_SEPARATORS)
    # the one change: detected under tag-chars and never stripped, then stripped as zero-width
    assert "\u180e" not in S2_STRIP and was_kind("\u180e") == "tag-chars"
    assert "\u180e" in inv.strip and inv.kind["\u180e"] == "zero-width"


def test_stage_2_strips_and_spaces_the_list():
    assert set(fold.STRIP) == NOW_STRIP
    assert set(fold.SEPARATORS) == S2_SEPARATORS
    assert fold.KIND_ORDER == ["zero-width", "bidi", "soft-hyphen", "filler", "tag-chars",
                               "variation-selectors", "nul"]


def test_stage_2_names_the_kind_of_every_code_point():
    # every code point, so a character gaining or losing a kind cannot slip through
    got = {o: fold._kind(chr(o)) for o in range(0x110000) if fold._kind(chr(o))}
    want = {o: now_kind(chr(o)) for o in range(0x110000) if now_kind(chr(o))}
    assert got == want
    assert 0x180E in got and chr(0x180E) in fold.STRIP  # stripped now, kind zero-width
    assert got[0x180E] == "zero-width"


def test_stage_3_strips_the_list_and_leaves_the_separators():
    assert graph_inv.STRIP == {ord(ch): None for ch in NOW_STRIP}
    assert graph_inv.strip_line("a b\u0085c") == "a b\u0085c"
    assert graph_inv.strip_line("re\u200bfer\xadence") == "reference"


def test_stage_4_strips_and_spaces_the_list():
    want = {ord(ch): None for ch in NOW_STRIP}
    want.update({0x2028: " ", 0x2029: " ", 0x0085: " "})
    assert foldtext._TABLE == want
    assert foldtext.fold_line("a b c\u0085d") == "a b c d"


def test_the_three_stages_agree_with_each_other_and_with_the_file():
    inv = library.invisible()
    assert set(fold.STRIP) == {chr(c) for c in graph_inv.STRIP} == {chr(c) for c, v in foldtext._TABLE.items() if v is None}
    assert set(fold.STRIP) == set(inv.strip)
    assert set(fold.SEPARATORS) == set(inv.space)
    assert set(inv.run) == RUN and not (set(inv.run) & set(inv.strip)) and not (set(inv.run) & set(inv.space))


def test_stage_2_folds_and_reports_as_before_with_u180e_now_stripped():
    assert fold.fold_line("a​b c") == ("ab c", ["U+200B", "U+2028"])
    assert fold.fold_line("a\u180eb") == ("ab", ["U+180E"])
    assert fold.hidden_chars("a\u180eb\x00") == [("\u180e", "zero-width"), ("\x00", "nul")]
    f = fold.invisible_finding("f.md", 3, "x‮y​z")
    assert f["carrier"] == "zero-width+bidi" and f["chars"] == ["U+202E", "U+200B"]


@pytest.mark.parametrize("code", sorted(ord(ch) for ch in NOW_STRIP))
def test_every_stripped_character_is_gone_from_all_three_stages(code):
    ch = chr(code)
    assert fold.fold_line("a" + ch + "b")[0] == "ab"
    assert graph_inv.strip_line("a" + ch + "b") == "ab"
    got = foldtext.fold_line("a" + ch + "b")
    if 0xE0020 <= code <= 0xE007E:  # `02.4-phrases` reads a tag character as the ASCII it spells (C42)
        assert ch not in got and got.startswith("a") and got.endswith("b") and got != "ab"
    else:
        assert got == "ab"


@pytest.mark.parametrize("code", sorted(ord(ch) for ch in RUN))
def test_a_run_character_is_stripped_in_a_run_and_kept_alone_by_all_three_stages(code):
    ch = chr(code)
    for text in ("a" + ch + "b", "✔" + ch + " ok"):  # alone: kept, nothing reported
        assert fold.fold_line(text) == (text, [])
        assert graph_inv.strip_line(text) == text
        assert foldtext.fold_line(text) == text
        assert fold.hidden_chars(text) == []
    two = "a" + ch + ch + "b"
    assert fold.fold_line(two) == ("ab", [f"U+{code:04X}"] * 2)
    assert graph_inv.strip_line(two) == "ab"
    spelled = library.run_text(ch + ch)  # two bytes can spell a two-letter word ("AA"): read, else dropped
    assert foldtext.fold_line(two) == ("a " + spelled + " b" if spelled else "ab")
    assert fold.hidden_chars(two) == [(ch, "variation-selectors")] * 2


def test_the_stages_keep_no_copy_of_the_list():
    """Done when 4: the list and the run rule are in the Library and `stages/_shared/library.py` only."""
    needles = ["180E", "034F", "206A", "FFF9", "1D173", "1BCA0", "061C", "115F", "3164", "FFA0", "17B4",
               "2800", "FE00", "FE0F", "E0100", "E01EF", "180B"]
    files = ["02-coded/02.2-reader/fold.py", "02-coded/02.3-graph/invisible.py",
             "02-coded/02.4-phrases/foldtext.py", "02-coded/02.5-capability/pairs.py",
             "06-report/details_html.py"]
    for rel in files:
        text = (STAGES / rel).read_text(encoding="utf-8")
        assert not [n for n in needles if re.search(rf"(?i)(?<![0-9A-F]){n}(?![0-9A-F])", text)], rel
        assert "VS_RUN" not in text and "vs_text" not in text, rel


# ---- the Unicode property (source S19)

DI = regex.compile(r"(?=\p{DI})\P{Cn}")  # default-ignorable and assigned, by the one Unicode data of `regex`


def _all_chars():
    return "".join(chr(c) for c in range(0x110000) if not 0xD800 <= c <= 0xDFFF)


def test_every_assigned_default_ignorable_code_point_is_in_the_list():
    inv = library.invisible()
    listed = inv.strip | inv.space | inv.run
    di = DI.findall(_all_chars())
    assert len(di) > 300  # the property matched a few hundred code points
    assert [f"U+{ord(ch):04X}" for ch in di if ch not in listed] == []


def test_a_range_cites_s19_exactly_when_all_its_code_points_have_the_property():
    doc = yaml.safe_load(library.path("invisible.yaml").read_text(encoding="utf-8"))
    prop = regex.compile(r"\p{DI}")
    seen_with, seen_without = 0, 0
    for r in doc["ranges"]:
        lo, hi = int(r["from"][2:], 16), int(r["to"][2:], 16)
        has = [bool(prop.fullmatch(chr(c))) for c in range(lo, hi + 1)]
        assert all(has) or not any(has), f"{r['name']}: only part of the range has the property"
        cites = "S19" in [x.strip() for x in str(r["source"]).split(";")]
        assert cites == all(has), r["name"]
        seen_with += cites
        seen_without += not cites
    # the ranges that do not: interlinear annotation, the blank braille cell, NUL, and the two separator entries
    assert seen_without == 5 and seen_with == len(doc["ranges"]) - 5
