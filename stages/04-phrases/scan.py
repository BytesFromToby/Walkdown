"""Run the pattern table over one file. Spec: specs/scan.SPEC.md."""
from __future__ import annotations

import re

from foldtext import fold_line, split_lines
from negation import anchor, negation
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


def _finding(rel, n, raw, folded, rows, audience, in_fm, check, hit) -> dict:
    only_folded = folded != raw and not any(
        r.hits(raw) for r in rows if r.check == check and r.applies(rel, audience, in_fm))
    negs = [negation(folded, anchor(r, folded)) for r in hit]  # review C25: tag, never drop
    stated_neg = all(negs)
    return {"check": check, "file": rel, "line": n, "quote": raw,
            "patterns": [r.id for r in hit], "audience": audience,
            "folded": only_folded, "matches": [_match(r, folded) for r in hit],
            "negated": stated_neg,
            "negation": negs[0]["word"] if stated_neg else None,
            "carve_out": next((x["carve_out"] for x in negs if x and x["carve_out"]), None)
            if stated_neg else None}


def _hits(rel, folded, rows, audience, in_fm) -> dict[str, list]:
    by_check: dict[str, list] = {}
    for row in rows:
        if row.applies(rel, audience, in_fm) and row.hits(folded):
            by_check.setdefault(row.check, []).append(row)
    return by_check


# Hard-wrapped prose (review C37, 2026-10-18): Markdown joins the lines of a paragraph, and so
# does the model, but the line pass reads one line at a time.
MARKDOWN_EXTS = (".md", ".markdown", ".mdc", ".mdx")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_HEADING = re.compile(r"^ {0,3}#{1,6}(\s|$)")
_RULE = re.compile(r"^ {0,3}([-*_=])(\s*\1){2,}\s*$")  # thematic break or setext underline
_ITEM = re.compile(r"^\s*([-*+]|\d{1,9}[.)])(\s|$)")
_QUOTE = re.compile(r"^ {0,3}>\s?")


def prose_lines(lines: list[str], fm: set[int]) -> set[int]:
    """The 1-based numbers of Markdown lines that can be part of a paragraph: not blank, not
    in frontmatter or a fenced code block (fences included), not a heading, a table row, a
    rule, or a line that starts with an HTML tag or comment."""
    out: set[int] = set()
    fence = None
    for n, raw in enumerate(lines, start=1):
        m = _FENCE.match(raw)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        s = raw.strip()
        if (n in fm or not s or _HEADING.match(raw) or _RULE.match(raw)
                or s.startswith("|") or s.startswith("<")):
            continue
        out.add(n)
    return out


def joined(first: str, second: str) -> str | None:
    """The two lines as one paragraph line, or None when the second starts a new block: a list
    item, or a quote boundary (one line quoted and the other not)."""
    if _ITEM.match(second):
        return None
    q1, q2 = _QUOTE.match(first), _QUOTE.match(second)
    if bool(q1) != bool(q2):
        return None
    rest = second[q2.end():] if q2 else second
    return first.rstrip() + " " + rest.strip()


def wrapped_findings(rel: str, lines: list[str], rows, audience: str, fm: set[int],
                     line_checks: dict[int, set]) -> list[dict]:
    """A hit on a line joined with the next line of its paragraph, for a check that neither
    line hits alone, so nothing the line pass found is counted twice. Cited at the first line;
    `end_line` is the second, `quote` is both lines, and `wrapped` is true."""
    if not rel.lower().endswith(MARKDOWN_EXTS):
        return []
    prose = prose_lines(lines, fm)
    out = []
    for n in sorted(prose):
        if n + 1 not in prose:
            continue
        text = joined(lines[n - 1], lines[n])
        if text is None:
            continue
        folded = fold_line(text)
        found = _hits(rel, folded, rows, audience, False)
        for check in sorted(found, key=_ORDER.__getitem__):
            if check in line_checks.get(n, ()) or check in line_checks.get(n + 1, ()):
                continue
            f = _finding(rel, n, text, folded, rows, audience, False, check, found[check])
            f.update(quote=lines[n - 1] + "\n" + lines[n], end_line=n + 1, wrapped=True)
            out.append(f)
    return out


def scan_text(rel: str, text: str, rows, audience: str) -> list[dict]:
    lines = split_lines(text)
    fm = frontmatter_lines(lines)
    findings: list[dict] = []
    line_checks: dict[int, set] = {}
    for n, raw in enumerate(lines, start=1):
        folded = fold_line(raw)
        in_fm = n in fm
        by_check = _hits(rel, folded, rows, audience, in_fm)
        line_checks[n] = set(by_check)
        for check in sorted(by_check, key=_ORDER.__getitem__):
            findings.append(_finding(rel, n, raw, folded, rows, audience, in_fm, check, by_check[check]))
    findings += wrapped_findings(rel, lines, rows, audience, fm, line_checks)
    findings.sort(key=lambda f: (f["line"], bool(f.get("wrapped")), _ORDER[f["check"]]))
    return findings
