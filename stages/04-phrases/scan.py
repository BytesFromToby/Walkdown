"""Run the pattern table over one file. Spec: specs/scan.SPEC.md."""
from __future__ import annotations

import re

from foldtext import base64_texts, fold_line, split_lines
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


def _rest(first: str, second: str) -> tuple[str, int] | None:
    """What the second line adds to the paragraph (stripped, without its quote marker when both
    lines are quoted) and where that starts in the raw line; None when the second line starts a
    new block: a list item, or a quote boundary (one line quoted and the other not)."""
    if _ITEM.match(second):
        return None
    q1, q2 = _QUOTE.match(first), _QUOTE.match(second)
    if bool(q1) != bool(q2):
        return None
    body = second[q2.end():] if q2 else second
    lead = len(second) - len(body.lstrip())
    return body.strip(), lead


def joined(first: str, second: str) -> str | None:
    """The two lines as one paragraph line, or None when the second starts a new block."""
    r = _rest(first, second)
    return None if r is None else first.rstrip() + " " + r[0]


def _run(lines: list[str], s: int, e: int):
    """Lines s..e (1-based) as one paragraph line, and per line (line, offset in the joined text,
    offset in the raw line, length); None when a line in the run starts a new block."""
    text = lines[s - 1].rstrip()
    pieces = [(s, 0, 0, len(text))]
    for k in range(s + 1, e + 1):
        r = _rest(lines[k - 2], lines[k - 1])
        if r is None:
            return None
        body, lead = r
        text += " "
        pieces.append((k, len(text), lead, len(body)))
        text += body
    return text, pieces


def _line_spans(m: dict, text: str, pieces) -> list[list[int]]:
    """Where a match on the joined text sits in each raw line, as [line, start, end], so a review
    card can mark the words on both sides of the break (C37 follow-up, 2026-10-20). Empty when
    the matched text cannot be placed (folding changed it)."""
    t = m.get("text") or ""
    low = text.lower()
    a = m.get("start")
    if not (isinstance(a, int) and low[a:a + len(t)] == t.lower()):
        a = low.find(t.lower()) if t else -1
    if a < 0:
        return []
    b = a + len(t)
    out = []
    for line, joff, roff, length in pieces:
        lo, hi = max(a, joff), min(b, joff + length)
        if lo < hi:
            out.append([line, roff + lo - joff, roff + hi - joff])
    return out


# Most lines joined into one: a match spread over more is not caught (a v1 limit; 2026-10-20).
MAX_JOIN = 4


def wrapped_findings(rel: str, lines: list[str], rows, audience: str, fm: set[int],
                     line_checks: dict[int, set]) -> list[dict]:
    """A hit on a run of lines of one paragraph joined as one line (two lines up to MAX_JOIN),
    for a check that no line or shorter run inside it hits, so nothing is counted twice. Cited
    at the first line; `end_line` is the last, `quote` is every line of the run, `wrapped` is
    true, and each match carries `spans`, its place in each raw line."""
    if not rel.lower().endswith(MARKDOWN_EXTS):
        return []
    prose = prose_lines(lines, fm)
    covered = {(n, n): set(line_checks.get(n, ())) for n in prose}  # checks hit inside a run
    out = []
    for size in range(2, MAX_JOIN + 1):
        for s in sorted(prose):
            e = s + size - 1
            left, right = covered.get((s, e - 1)), covered.get((s + 1, e))
            if left is None or right is None:
                continue
            run = _run(lines, s, e)
            if run is None:
                continue
            text, pieces = run
            folded = fold_line(text)
            found = _hits(rel, folded, rows, audience, False)
            inner = left | right
            covered[(s, e)] = inner | set(found)
            for check in sorted(found, key=_ORDER.__getitem__):
                if check in inner:
                    continue
                f = _finding(rel, s, text, folded, rows, audience, False, check, found[check])
                for m in f["matches"]:
                    m["spans"] = _line_spans(m, text, pieces)
                f.update(quote="\n".join(lines[s - 1:e]), end_line=e, wrapped=True)
                out.append(f)
    return out


_SENTENCE_END = re.compile(r"[.!?](?=\s|$)")


def _narrows(row) -> bool:
    """A row that narrows itself (a negative lookahead or an unless), the only kind the next
    line can cancel; a row anchored at the end of the line would be cancelled by any text."""
    return "(?!" in row.regex or row.unless is not None


def undone_by_next_line(rel: str, lines: list[str], findings: list[dict], rows, fm: set[int]):
    """A line hit whose own narrowing cancels it once its sentence goes on to the next line of
    the paragraph ("Don't ask" / "hypothetical questions"): the row is tested on the line joined
    with the next line up to that line's first sentence end, and a row that no longer hits is
    taken off the finding; a finding left with no row is no hit. Markdown only, rows that narrow
    themselves only (C37 follow-up, 2026-10-20). Returns (findings kept, rows taken off)."""
    if not rel.lower().endswith(MARKDOWN_EXTS):
        return findings, []
    prose = prose_lines(lines, fm)
    by_id = {r.id: r for r in rows}
    kept, undone = [], []
    for f in findings:
        n = f["line"]
        pats = [by_id[p] for p in f["patterns"] if p in by_id]
        if f.get("wrapped") or n not in prose or n + 1 not in prose or not any(map(_narrows, pats)):
            kept.append(f)
            continue
        r = _rest(lines[n - 1], lines[n])
        if r is None:
            kept.append(f)
            continue
        m = _SENTENCE_END.search(r[0])
        head = r[0][:m.end()] if m else r[0]
        folded = fold_line(lines[n - 1].rstrip() + " " + head)
        gone = [row for row in pats if _narrows(row) and not row.hits(folded)]
        if not gone:
            kept.append(f)
            continue
        undone.append({"check": f["check"], "file": rel, "line": n, "next_line": n + 1,
                       "patterns": [row.id for row in gone]})
        left = [row for row in pats if row not in gone]
        if left:
            raw = lines[n - 1]
            kept.append(_finding(rel, n, raw, fold_line(raw), rows, f["audience"], False,
                                 f["check"], left))
    return kept, undone


def base64_findings(rel: str, lines: list[str], rows, audience: str, fm: set[int],
                    line_checks: dict[int, set]) -> list[dict]:
    """A check that readable text hidden in base64 on a line hits and the line itself does not
    (review C42, 2026-10-25): cited at the line, `decoded: "base64"`, `decoded_text`."""
    out = []
    for n, raw in enumerate(lines, start=1):
        if len(raw) < 24:
            continue
        for text in base64_texts(raw):
            folded = fold_line(" ".join(text.split()))
            found = _hits(rel, folded, rows, audience, n in fm)
            for check in sorted(found, key=_ORDER.__getitem__):
                if check in line_checks.setdefault(n, set()):
                    continue
                f = _finding(rel, n, raw, folded, rows, audience, n in fm, check, found[check])
                f.update(folded=False, decoded="base64", decoded_text=text[:MATCH_CAP])
                out.append(f)
                line_checks[n].add(check)
    return out


_FM_KEY = re.compile(r"^(\s*)[\w.-]+:(?:\s+(.*))?$")
_BLOCK = re.compile(r"^[|>][+-]?\d?\s*(#.*)?$")
FM_MAX_JOIN = 20


def frontmatter_values(lines: list[str], fm: set[int]) -> list[tuple[int, list[tuple[int, str]]]]:
    """Each frontmatter value written over more than one line: (key line, [(line, value text)]),
    the key line's own value first when it has one. A block scalar (`key: >-`, `key: |`) or a
    plain value continued on lines indented more than its key (review C42)."""
    out = []
    nums = sorted(n for n in fm if lines[n - 1].strip() not in ("---", "..."))
    i = 0
    while i < len(nums):
        n = nums[i]
        m = _FM_KEY.match(lines[n - 1])
        if not m:
            i += 1
            continue
        indent, value = len(m.group(1)), (m.group(2) or "").strip()
        parts = [] if not value or _BLOCK.match(value) else [(n, value)]
        j = i + 1
        while j < len(nums) and nums[j] == nums[j - 1] + 1:
            raw = lines[nums[j] - 1]
            if raw.strip() and len(raw) - len(raw.lstrip()) <= indent:
                break
            if raw.strip():
                parts.append((nums[j], raw.strip()))
            j += 1
        if len(parts) > 1:
            out.append((n, parts[:FM_MAX_JOIN]))
        i = max(j, i + 1)
    return out


def frontmatter_findings(rel: str, lines: list[str], rows, audience: str, fm: set[int],
                         line_checks: dict[int, set]) -> list[dict]:
    """A check that a frontmatter value joined over its lines hits and none of its lines hits
    alone (review C42): cited at the first value line, `end_line`, `wrapped`, `spans`."""
    out = []
    for _key, parts in frontmatter_values(lines, fm):
        text, pieces = "", []
        for ln, part in parts:
            if text:
                text += " "
            raw = lines[ln - 1]
            pieces.append((ln, len(text), raw.index(part), len(part)))
            text += part
        folded = fold_line(text)
        found = _hits(rel, folded, rows, audience, True)
        inner = set().union(*(line_checks.get(ln, set()) for ln, _ in parts))
        s, e = parts[0][0], parts[-1][0]
        for check in sorted(found, key=_ORDER.__getitem__):
            if check in inner:
                continue
            f = _finding(rel, s, text, folded, rows, audience, True, check, found[check])
            for m in f["matches"]:
                m["spans"] = _line_spans(m, text, pieces)
            f.update(quote="\n".join(lines[s - 1:e]), end_line=e, wrapped=True)
            out.append(f)
    return out


def scan_text(rel: str, text: str, rows, audience: str, undone: list | None = None) -> list[dict]:
    """`undone`, when given, collects the line hits a next line cancelled (C37 follow-up)."""
    lines = split_lines(text)
    fm = frontmatter_lines(lines)
    findings: list[dict] = []
    for n, raw in enumerate(lines, start=1):
        folded = fold_line(raw)
        in_fm = n in fm
        by_check = _hits(rel, folded, rows, audience, in_fm)
        for check in sorted(by_check, key=_ORDER.__getitem__):
            findings.append(_finding(rel, n, raw, folded, rows, audience, in_fm, check, by_check[check]))
    findings, gone = undone_by_next_line(rel, lines, findings, rows, fm)
    if undone is not None:
        undone.extend(gone)
    line_checks: dict[int, set] = {}
    for f in findings:
        line_checks.setdefault(f["line"], set()).add(f["check"])
    findings += wrapped_findings(rel, lines, rows, audience, fm, line_checks)
    findings += frontmatter_findings(rel, lines, rows, audience, fm, line_checks)
    findings += base64_findings(rel, lines, rows, audience, fm, line_checks)
    findings.sort(key=lambda f: (f["line"], bool(f.get("wrapped")), _ORDER[f["check"]]))
    return findings
