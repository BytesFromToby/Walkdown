"""Runs of non-Latin script. Spec: specs/script_runs.SPEC.md."""
from __future__ import annotations

import unicodedata
from functools import lru_cache

import regex

# Unicode Script property values (long names), most common first.
SCRIPTS = """Common Inherited Latin Cyrillic Greek Han Hiragana Katakana Hangul Arabic Hebrew
Devanagari Bengali Thai Armenian Georgian Ethiopic Tamil Telugu Kannada Malayalam Gujarati
Gurmukhi Oriya Sinhala Khmer Lao Myanmar Tibetan Mongolian Syriac Thaana Nko Cherokee
Canadian_Aboriginal Ogham Runic Yi Bopomofo Coptic Glagolitic Tifinagh Vai Bamum Javanese
Balinese Sundanese Batak Buginese Tai_Le New_Tai_Lue Tai_Tham Tai_Viet Cham Lepcha Limbu
Ol_Chiki Saurashtra Kayah_Li Rejang Lisu Meetei_Mayek Samaritan Mandaic Tagalog Hanunoo Buhid
Tagbanwa Braille Gothic Old_Italic Deseret Shavian Osmanya Cypriot Linear_B Linear_A Ugaritic
Old_Persian Phoenician Kharoshthi Cuneiform Egyptian_Hieroglyphs Imperial_Aramaic Avestan
Inscriptional_Parthian Inscriptional_Pahlavi Old_Turkic Old_South_Arabian Old_North_Arabian
Kaithi Brahmi Chakma Sharada Takri Miao Sora_Sompeng Meroitic_Cursive Meroitic_Hieroglyphs
Carian Lycian Lydian Anatolian_Hieroglyphs Adlam Bassa_Vah Duployan Elbasan Grantha Khojki
Khudawadi Mahajani Manichaean Mende_Kikakui Modi Mro Nabataean Old_Hungarian Old_Permic
Pahawh_Hmong Palmyrene Pau_Cin_Hau Psalter_Pahlavi Siddham Tirhuta Warang_Citi Ahom Hatran
Multani SignWriting Bhaiksuki Marchen Newa Osage Tangut Masaram_Gondi Nushu Soyombo
Zanabazar_Square Dogra Gunjala_Gondi Hanifi_Rohingya Makasar Medefaidrin Old_Sogdian Sogdian
Elymaic Nandinagari Nyiakeng_Puachue_Hmong Wancho Chorasmian Dives_Akuru Khitan_Small_Script
Yezidi Cypro_Minoan Old_Uyghur Tangsa Toto Vithkuqi Kawi Nag_Mundari Syloti_Nagri Phags_Pa
Old_Sogdian Garay Gurung_Khema Kirat_Rai Ol_Onal Sunuwar Todhri Tulu_Tigalari""".split()

_PATTERNS = []
for _name in dict.fromkeys(SCRIPTS):
    try:
        _PATTERNS.append((_name, regex.compile(rf"\p{{Script={_name}}}")))
    except regex.error:
        pass

IGNORED = {"Latin", "Common", "Inherited", "Unknown"}


@lru_cache(maxsize=None)
def script_of(ch: str) -> str:
    for name, pat in _PATTERNS:
        if pat.match(ch):
            return name
    return "Unknown"


def runs(line: str) -> list[dict]:
    out: list[dict] = []
    cur = None  # [script, start, end]
    for i, ch in enumerate(line):
        if not unicodedata.category(ch).startswith("L"):
            continue
        s = script_of(ch)
        if s in IGNORED:
            if cur:
                out.append(cur)
                cur = None
            continue
        if cur and cur[0] == s:
            cur[2] = i
        else:
            if cur:
                out.append(cur)
            cur = [s, i, i]
    if cur:
        out.append(cur)
    return [{"script": s, "text": line[a:b + 1], "col": a} for s, a, b in out]


def script_findings(file: str, line_no: int | None, line: str) -> list[dict]:
    return [{"check": "read.script", "file": file, "line": line_no, "script": r["script"],
             "text": r["text"], "col": r["col"]} for r in runs(line)]
