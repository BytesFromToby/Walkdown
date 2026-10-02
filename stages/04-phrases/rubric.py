"""Harness rubric: J actions and whether their step asks first. Spec: specs/rubric.SPEC.md."""
from __future__ import annotations

import re

LIST_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
HEADING = re.compile(r"^\s{0,3}#{1,6}(\s|$)")
FENCE = re.compile(r"^\s*(```|~~~)")


def _indent(s: str) -> int:
    return len(s) - len(s.lstrip(" \t"))


def _blank(s: str) -> bool:
    return not s.strip()


def _item_start(lines: list[str], i: int):
    j = i
    while j >= 0:
        s = lines[j]
        if _blank(s) or HEADING.match(s) or FENCE.match(s):
            return None
        m = LIST_ITEM.match(s)
        if m:
            ind = len(m.group(1))
            if all(_indent(lines[k]) > ind for k in range(j + 1, i + 1)):
                return j, ind
        j -= 1
    return None


def _fence_block(lines: list[str], i: int):
    """(open, close) 0-based indexes of the fenced block holding line i, or None."""
    opens = [k for k in range(len(lines)) if FENCE.match(lines[k])]
    for a, b in zip(opens[0::2], opens[1::2]):
        if a < i < b:
            return a, b
    return None


def _paragraph_edge(lines: list[str], k: int, step: int) -> int:
    """Walk from k (a fence line) past blank lines to the next paragraph in the
    direction `step`, and return the far edge of that paragraph (or k if none)."""
    j = k + step
    while 0 <= j < len(lines) and _blank(lines[j]):
        j += step
    if not (0 <= j < len(lines)) or HEADING.match(lines[j]) or FENCE.match(lines[j]):
        return k
    while 0 <= j + step < len(lines) and not (_blank(lines[j + step]) or HEADING.match(lines[j + step])
                                               or FENCE.match(lines[j + step])):
        j += step
    return j


def step_span(lines: list[str], n: int) -> tuple[int, int]:
    """The 1-based inclusive line span of the step holding line n."""
    i = n - 1
    block = _fence_block(lines, i)
    if block is not None:
        # A fenced block is one step together with its lead-in paragraph above and
        # the paragraph right after it: a confirmation prompt shown to the user
        # ("This will permanently delete: ... Type 'discard' to confirm") is
        # introduced and followed by the instruction that waits on it (2026-09-29).
        a, b = block
        return _paragraph_edge(lines, a, -1) + 1, _paragraph_edge(lines, b, +1) + 1
    s = lines[i]
    if _blank(s) or HEADING.match(s) or FENCE.match(s):
        return n, n
    item = _item_start(lines, i)
    if item is not None:
        start, ind = item
        k = start + 1
        while (k < len(lines) and not _blank(lines[k]) and _indent(lines[k]) > ind
               and not HEADING.match(lines[k]) and not FENCE.match(lines[k])):
            k += 1
        return start + 1, k

    def plain(x):
        return not (_blank(x) or HEADING.match(x) or FENCE.match(x) or LIST_ITEM.match(x))

    lo = hi = i
    while lo - 1 >= 0 and plain(lines[lo - 1]):
        lo -= 1
    while hi + 1 < len(lines) and plain(lines[hi + 1]):
        hi += 1
    return lo + 1, hi + 1


def _confirmations(line: str, vocab):
    """Yield (negated: bool) for every confirmation-shaped match on one folded line."""
    for rx in vocab.confirm:
        for m in rx.finditer(line):
            neg = bool(vocab.neg_before.search(line[:m.start()])
                       or vocab.neg_after.match(line[m.end():]))
            yield neg
    for _ in vocab.neg_forms.finditer(line):
        yield True


def _row_hits(row, text: str, vocab) -> re.Match | None:
    m = row.rx.search(text)
    if m is None:
        return None
    if vocab.tiers.get(row.id) == vocab.ignore_unless_tier:
        return m
    if row.unless_rx is not None and row.unless_rx.search(text):
        return None
    return m


REDEFINES_CONFIRM = re.compile(
    r"\b(confirm\w*|approv\w*|permission\w*|consent\w*|ask(ing)?)\b[\"'*_`]*\s+"
    r"(means|mean|is\s+defined\s+as|refers\s+to|is\s+when|counts\s+as)\b", re.I)


def rubric_file(rel, raw, folded, instr, audience, rows, vocab) -> list[dict]:
    j_rows = [r for r in rows if r.check == "phrase.J.prohibited"]
    out: list[dict] = []
    for n in sorted(instr):
        if n < 1 or n > len(folded):
            continue
        text = folded[n - 1]
        hits = []
        for r in j_rows:
            m = _row_hits(r, text, vocab)
            if m is not None:
                hits.append((r, m))
        if not hits:
            continue
        prohibited = [(r, m) for r, m in hits if vocab.tiers.get(r.id) == "prohibited"]
        tier = "prohibited" if prohibited else "confirm-first"
        r0, m0 = (prohibited or hits)[0]
        src = raw[n - 1] if raw[n - 1] == text else text
        action = src[m0.start():m0.end()]

        lo, hi = step_span(folded, n)
        order = [n] + [k for k in range(lo, hi + 1) if k != n]
        confirm_line = None
        negated_seen = False
        redefined = False
        for k in order:
            if REDEFINES_CONFIRM.search(folded[k - 1]):
                # "Confirmation means announcing your intent" is a definition, not a
                # step that waits on the user: redefining the safety word is THREATS
                # 14's attack, so it never satisfies the rubric (2026-09-29).
                redefined = True
                continue
            for neg in _confirmations(folded[k - 1], vocab):
                if neg:
                    negated_seen = True
                elif confirm_line is None:
                    confirm_line = k
            if confirm_line is not None:
                break
        confirmed = confirm_line is not None
        out.append({"check": "rubric.action", "file": rel, "line": n, "quote": raw[n - 1],
                    "audience": audience, "tier": tier, "action": action,
                    "patterns": [r.id for r, _ in hits], "confirmation": confirmed,
                    "negated_confirmation": (not confirmed) and negated_seen,
                    "confirm_redefined": redefined,
                    "confirm_line": confirm_line,
                    "confirm_quote": raw[confirm_line - 1] if confirmed else None})
    return out
