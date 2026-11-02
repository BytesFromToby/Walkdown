"""Strip invisible characters before matching references. Spec: specs/graph.SPEC.md, invisible.

Reimplements the strip half of `02.2-reader`'s fold; never imports `02.2-reader`.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import library  # noqa: E402

# Library/invisible.yaml: the one list. `02.3-graph` strips (`strip`, and the runs `library.runs` finds);
# it leaves the line separators as they are.
STRIP = {ord(ch): None for ch in library.invisible().strip}

BOMS = [(b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\xef\xbb\xbf", "utf-8"), (b"\xfe\xff", "utf-16-be"), (b"\xff\xfe", "utf-16-le")]


def strip_line(line: str) -> str:
    stripped = library.replace_runs(line).translate(STRIP)  # a run of variation selectors goes too; one alone stays
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
    # A few NUL bytes in otherwise valid UTF-8 are text: a source file with a literal \0
    # sentinel was skipped whole, and one NUL could hide any file (2026-10-09)
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
