"""Folded copy for `02.4-phrases`. Spec: specs/phrases.SPEC.md, foldtext.

Reimplements `02.2-reader`'s fold rules; never imports `02.2-reader`. Decoding bytes and splitting lines are
`stages/_shared/readtext.py` (restructure step 4: the builder step reads text the same way).
"""
from __future__ import annotations

import base64
import binascii
import re
import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import library  # noqa: E402

# Library/invisible.yaml: the one list. `02.4-phrases` strips, turns the line separators into a space, and
# reads what a run of variation selectors or of tag characters spells (`library.read_hidden`), or drops it.
_INV = library.invisible()
_TABLE: dict[int, str | None] = {ord(ch): None for ch in _INV.strip}
_TABLE.update({ord(ch): " " for ch in _INV.space})

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


def _drop_accents(s: str) -> str:
    """Remove a combining mark that sits on an ASCII letter (an accented o in ignore reads o; review C42)."""
    out: list[str] = []
    for ch in unicodedata.normalize("NFD", s):
        if unicodedata.combining(ch) and out and out[-1].isascii() and out[-1].isalpha():
            continue
        out.append(ch)
    return unicodedata.normalize("NFC", "".join(out))


def fold_line(line: str) -> str:
    s = library.read_hidden(line).translate(_TABLE)
    if s.isascii():
        return s
    s = unicodedata.normalize("NFKC", s)
    s = "".join(_ascii_homoglyph(ch) or ch for ch in s)
    return _drop_accents(s) if not s.isascii() else s


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
