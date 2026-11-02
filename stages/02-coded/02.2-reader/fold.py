"""Folded copy and invisible-character detection. Spec: specs/reader.SPEC.md, fold."""
from __future__ import annotations

import sys
import unicodedata
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import library  # noqa: E402

INV = library.invisible()  # Library/invisible.yaml: the one list, read by `02.2-reader`, `02.3-graph`, `02.4-phrases` (and its terms.code hash), `02.5-capability` (pairs), and `06-report` (details and review pages)
STRIP = INV.strip
SEPARATORS = INV.space  # replaced by a space, never a new line

KIND_ORDER = list(INV.kind_order)


def cp(ch: str) -> str:
    return f"U+{ord(ch):04X}"


def _in_runs(line: str) -> set[int]:
    """Positions of the characters that stand in a run (`library.runs`: two or more variation
    selectors in a row or with only stripped characters between them), the stripped characters
    between them included (they are in `STRIP` and reported under their own kind). One selector
    alone is ordinary and is left out."""
    return {i for r in library.runs(line) for i in range(r.start, r.end)}


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
    in_run = _in_runs(line)
    for i, ch in enumerate(line):
        if ch in STRIP or ch in SEPARATORS or i in in_run:
            removed.append(cp(ch))
            continue
        n = unicodedata.normalize("NFKC", ch)
        if n != ch:
            removed.append(cp(ch))
            continue
        if ascii_homoglyph(ch) is not None:
            removed.append(cp(ch))
    stripped = "".join(" " if ch in SEPARATORS else ch
                       for i, ch in enumerate(line) if ch not in STRIP and i not in in_run)
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
    return INV.kind.get(ch)


def hidden_chars(line: str) -> list[tuple[str, str]]:
    """Every invisible character in the line with its kind. A character with action `run` counts
    only inside a run: one variation selector alone is ordinary."""
    in_run = _in_runs(line)
    return [(ch, k) for i, ch in enumerate(line) if (k := _kind(ch)) and (ch not in INV.run or i in in_run)]


def invisible_finding(file: str, line_no: int | None, raw: str) -> dict | None:
    hits = hidden_chars(raw)
    if not hits:
        return None
    kinds = {k for _, k in hits}
    out = {"check": "read.divergence", "file": file, "line": line_no,
           "reading": "A-only", "text": raw,
           "carrier": "+".join(k for k in KIND_ORDER if k in kinds),
           "method": "static-style", "chars": [cp(ch) for ch, _ in hits]}
    runs = library.tag_texts(raw)  # what tag characters spell: the report says what (review C42)
    runs += [r.text for r in library.runs(raw) if r.text]  # a run of variation selectors that spells text
    if runs:
        out["decoded"] = " ".join(runs)
    return out
