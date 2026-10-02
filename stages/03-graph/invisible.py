"""Strip invisible characters before matching references. Spec: specs/invisible.SPEC.md.

Reimplements the strip half of stage 2's fold; never imports stage 2.
"""
from __future__ import annotations

import unicodedata

_RANGES = [(0x200B, 0x200F), (0x2060, 0x2064), (0xFEFF, 0xFEFF), (0x202A, 0x202E),
           (0x2066, 0x2069), (0x00AD, 0x00AD), (0xE0000, 0xE007F)]
STRIP = {c: None for lo, hi in _RANGES for c in range(lo, hi + 1)}

BOMS = [(b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\xef\xbb\xbf", "utf-8"), (b"\xfe\xff", "utf-16-be"), (b"\xff\xfe", "utf-16-le")]


def strip_line(line: str) -> str:
    stripped = line.translate(STRIP)
    if stripped.isascii():
        return stripped
    return unicodedata.normalize("NFKC", stripped)


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
