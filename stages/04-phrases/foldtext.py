"""Folded copy and text decoding for stage 4. Spec: specs/foldtext.SPEC.md.

Reimplements stage 2's fold rules; never imports stage 2.
"""
from __future__ import annotations

import unicodedata
from functools import lru_cache

_RANGES = [(0x200B, 0x200F), (0x2060, 0x2064), (0xFEFF, 0xFEFF), (0x202A, 0x202E),
           (0x2066, 0x2069), (0x00AD, 0x00AD), (0xE0000, 0xE007F)]
_TABLE: dict[int, str | None] = {c: None for lo, hi in _RANGES for c in range(lo, hi + 1)}
_TABLE.update({0x2028: " ", 0x2029: " ", 0x0085: " "})

BOMS = [(b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\xef\xbb\xbf", "utf-8"), (b"\xfe\xff", "utf-16-be"), (b"\xff\xfe", "utf-16-le")]


@lru_cache(maxsize=None)
def _ascii_homoglyph(ch: str) -> str | None:
    if ord(ch) < 128:
        return None
    try:
        from confusable_homoglyphs import confusables
        hits = confusables.is_confusable(ch, greedy=True)
    except Exception:
        return None
    for hit in hits or []:
        if hit.get("character") != ch:
            continue
        for h in hit.get("homoglyphs", []):
            c = h.get("c", "")
            if c and all(32 <= ord(x) < 127 for x in c):
                return c
    return None


def fold_line(line: str) -> str:
    s = line.translate(_TABLE)
    if s.isascii():
        return s
    s = unicodedata.normalize("NFKC", s)
    return "".join(_ascii_homoglyph(ch) or ch for ch in s)


def decode(data: bytes) -> str | None:
    for mark, codec in BOMS:
        if data.startswith(mark):
            try:
                return data[len(mark):].decode(codec)
            except UnicodeDecodeError:
                return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best is not None and best.encoding:
            return str(best)
    except Exception:
        pass
    return None


def split_lines(text: str) -> list[str]:
    if not text:
        return []
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]
