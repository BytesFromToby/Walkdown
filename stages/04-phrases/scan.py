"""Run the pattern table over one file. Spec: specs/scan.SPEC.md."""
from __future__ import annotations

from foldtext import fold_line, split_lines
from patterns import CHECKS

_ORDER = {c: i for i, c in enumerate(CHECKS)}


def frontmatter_lines(lines: list[str]) -> set[int]:
    if not lines or lines[0].strip() != "---":
        return set()
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return set(range(2, i + 1))
    return set()


MATCH_CAP = 160


def _match(row, folded: str) -> dict:
    """The text a pattern matched on the folded line, so a reader (stage 6) knows which words
    were flagged (2026-09-30, soft D4). Capped; `start` is the offset in the folded line."""
    m = row.rx.search(folded)
    text = m.group(0) if m else ""
    return {"pattern": row.id, "text": text[:MATCH_CAP], "start": m.start() if m else None}


def scan_text(rel: str, text: str, rows, audience: str) -> list[dict]:
    lines = split_lines(text)
    fm = frontmatter_lines(lines)
    findings: list[dict] = []
    for n, raw in enumerate(lines, start=1):
        folded = fold_line(raw)
        changed = folded != raw
        in_fm = n in fm
        by_check: dict[str, list] = {}
        for row in rows:
            if row.applies(rel, audience, in_fm) and row.hits(folded):
                by_check.setdefault(row.check, []).append(row)
        for check in sorted(by_check, key=_ORDER.__getitem__):
            hit = by_check[check]
            only_folded = changed and not any(
                r.hits(raw) for r in rows if r.check == check and r.applies(rel, audience, in_fm))
            findings.append({"check": check, "file": rel, "line": n, "quote": raw,
                             "patterns": [r.id for r in hit], "audience": audience,
                             "folded": only_folded, "matches": [_match(r, folded) for r in hit]})
    return findings
