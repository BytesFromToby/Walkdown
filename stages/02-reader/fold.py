"""Folded copy and invisible-character detection. Spec: specs/fold.SPEC.md."""
from __future__ import annotations

import unicodedata
from functools import lru_cache

ZERO_WIDTH = {chr(c) for c in list(range(0x200B, 0x2010)) + list(range(0x2060, 0x2065))} | {"﻿"}
BIDI = {chr(c) for c in list(range(0x202A, 0x202F)) + list(range(0x2066, 0x206A))}
SOFT_HYPHEN = {"­"}
TAGS = {chr(c) for c in range(0xE0000, 0xE0080)}
NUL = {"\x00"}  # a NUL byte in a text file (2026-10-09)
STRIP = ZERO_WIDTH | BIDI | SOFT_HYPHEN | TAGS | NUL
SEPARATORS = {" ", " ", "\u0085"}  # replaced by a space, never a new line

KIND_ORDER = ["zero-width", "bidi", "soft-hyphen", "tag-chars", "nul"]


def cp(ch: str) -> str:
    return f"U+{ord(ch):04X}"


@lru_cache(maxsize=None)
def ascii_homoglyph(ch: str) -> str | None:
    """The first all-ASCII homoglyph of a non-ASCII character, or None."""
    if ord(ch) < 128:
        return None
    try:
        from confusable_homoglyphs import confusables
        hits = confusables.is_confusable(ch, greedy=True)
    except Exception:
        return None
    if not hits:
        return None
    for hit in hits:
        if hit.get("character") != ch:
            continue
        for h in hit.get("homoglyphs", []):
            c = h.get("c", "")
            if c and all(32 <= ord(x) < 127 for x in c):
                return c
    return None


def fold_line(line: str) -> tuple[str, list[str]]:
    removed: list[str] = []
    for ch in line:
        if ch in STRIP or ch in SEPARATORS:
            removed.append(cp(ch))
            continue
        n = unicodedata.normalize("NFKC", ch)
        if n != ch:
            removed.append(cp(ch))
            continue
        if ascii_homoglyph(ch) is not None:
            removed.append(cp(ch))
    stripped = "".join(" " if ch in SEPARATORS else ch for ch in line if ch not in STRIP)
    normal = unicodedata.normalize("NFKC", stripped)
    folded = "".join(ascii_homoglyph(ch) or ch for ch in normal)
    if folded != line and not removed:
        removed = [cp(ch) for ch in line if ord(ch) > 127 and ch not in folded]
    return folded, removed


def fold_finding(file: str, line_no: int | None, raw: str) -> dict | None:
    folded, removed = fold_line(raw)
    if folded == raw:
        return None
    return {"check": "read.fold", "file": file, "line": line_no,
            "folded": folded, "removed": removed}


def _kind(ch: str) -> str | None:
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


def hidden_chars(line: str) -> list[tuple[str, str]]:
    return [(ch, k) for ch in line if (k := _kind(ch))]


def invisible_finding(file: str, line_no: int | None, raw: str) -> dict | None:
    hits = hidden_chars(raw)
    if not hits:
        return None
    kinds = {k for _, k in hits}
    return {"check": "read.divergence", "file": file, "line": line_no,
            "reading": "A-only", "text": raw,
            "carrier": "+".join(k for k in KIND_ORDER if k in kinds),
            "method": "static-style", "chars": [cp(ch) for ch, _ in hits]}
