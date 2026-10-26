"""Folded copy and text decoding for stage 4. Spec: specs/foldtext.SPEC.md.

Reimplements stage 2's fold rules; never imports stage 2.
"""
from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from functools import lru_cache

_RANGES = [(0x200B, 0x200F), (0x2060, 0x2064), (0xFEFF, 0xFEFF), (0x202A, 0x202E),
           (0x2066, 0x2069), (0x00AD, 0x00AD), (0xE0000, 0xE007F),
           (0x0000, 0x0000)]  # NUL, 2026-10-09
_TABLE: dict[int, str | None] = {c: None for lo, hi in _RANGES for c in range(lo, hi + 1)}
_TABLE.update({0x2028: " ", 0x2029: " ", 0x0085: " "})
# A run of tag characters spells ASCII (each minus U+E0000): read it, never drop it (review C42).
_TAG_RUN = re.compile("[\U000E0020-\U000E007E]+")

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


def _tags(m: re.Match) -> str:
    return " " + "".join(chr(ord(c) - 0xE0000) for c in m.group(0)) + " "


def _drop_accents(s: str) -> str:
    """Remove a combining mark that sits on an ASCII letter (an accented o in ignore reads o; review C42)."""
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", s):
        if unicodedata.combining(ch) and out and out[-1].isascii() and out[-1].isalpha():
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def fold_line(line: str) -> str:
    s = _TAG_RUN.sub(_tags, line) if not line.isascii() else line
    s = s.translate(_TABLE)
    if s.isascii():
        return s
    s = unicodedata.normalize("NFKC", s)
    s = "".join(_ascii_homoglyph(ch) or ch for ch in s)
    return _drop_accents(s) if not s.isascii() else s


def decode(data: bytes) -> str | None:
    for mark, codec in BOMS:
        if data.startswith(mark):
            try:
                return data[len(mark):].decode(codec)
            except UnicodeDecodeError:
                return None
    # A few NUL bytes in otherwise valid UTF-8 are text: a source file with a literal \0
    # sentinel was skipped whole, and one NUL could hide any file (2026-10-09, caveman)
    if b"\x00" in data:
        if data.count(b"\x00") * 100 > len(data):
            return None
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return None
        return text
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


_B64 = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/=])")


def base64_texts(line: str) -> list[str]:
    """Readable text hidden in base64 on a line (review C42): each run of 24 or more base64
    characters that decodes to strict UTF-8 of printable characters and white space, at least
    12 long with three words. Base64 of an image or a key decodes to no text."""
    out = []
    for m in _B64.finditer(line):
        core = m.group(0).rstrip("=")
        try:
            text = base64.b64decode(core + "=" * (-len(core) % 4), validate=True).decode("utf-8")
        except (binascii.Error, ValueError):
            continue
        if (len(text) >= 12 and all(c.isprintable() or c in "\t\n\r" for c in text)
                and len(re.findall(r"[A-Za-z]{2,}", text)) >= 3):
            out.append(text)
    return out


def split_lines(text: str) -> list[str]:
    if not text:
        return []
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]
