"""Prohibitions: is a matched action stated in the negative? Spec: specs/negation.SPEC.md.

Review C25 (partner's audit, 2026-10-12 and 2026-10-14): "Never have the user paste an API key
into chat" hit J.enter-secret like an instruction to do it. A hit is never dropped for this; it
is tagged, so the report can say "stated as a prohibition" (soft D5 spirit: mark, never demote).
Text only; a fixed rule, no model.
"""
from __future__ import annotations

import re

# A word that forbids what follows it in the same clause. Descriptions ("its adapter does not
# enforce", "cannot stay off", "will not run") say what happens, not what the text asks, and are
# left out (first real run, Compound Engineering, 2026-10-16).
NEG = re.compile(
    r"\b(never|do\s+not|don['’]t|must\s+not|mustn['’]t|should\s+not|shouldn['’]t|may\s+not|"
    r"not\s+allowed\s+to|forbidden\s+to|prohibited\s+from|avoid|refuse\s+to)\b", re.I)
# Right after the negation, a word that turns it into an instruction ("don't forget to upload",
# "never skip the push", "never mind the warning, delete ...").
DOUBLE = re.compile(r"\s+(forget|hesitate|fail|skip|miss|neglect|stop|omit|mind|wait|delay|"
                    r"only|just)\b", re.I)
# Ends the clause the negation governs.
BREAK = re.compile(r"[.;:!?,]\s|[.;:!?]$|\s[-–—]\s|\b(but|instead|then|otherwise|so)\b", re.I)
# An exception after the action, to the end of its sentence.
CARVE = re.compile(r"\b(unless|except|other than|until)\b[^.;!?]*", re.I)
MAX_GAP = 60  # characters between the negation and the action
CARVE_CAP = 160


def first_lookahead(regex: str) -> str | None:
    """The body of a lookahead-led pattern's first `(?=.*X)`, for rows that match an empty
    string at the line start (K.data-flow); None for any other pattern."""
    i = regex.find("(?=.*")
    if i < 0 or regex[:i].strip("^") != "":
        return None
    depth, j = 1, i + 5
    while j < len(regex) and depth:
        c = regex[j]
        if c == "\\":
            j += 2
            continue
        depth += c == "("
        depth -= c == ")"
        j += 1
    return regex[i + 5:j - 1] if depth == 0 else None


def anchor(row, folded: str) -> int | None:
    """Where a row's action starts on the folded line: its match, or for a lookahead-only row
    the first match of its first lookahead."""
    m = row.rx.search(folded)
    if m is None:
        return None
    if m.group(0):
        return m.start()
    body = first_lookahead(row.rx.pattern)
    if body:
        a = re.search(body, folded, row.rx.flags)
        if a:
            return a.start()
    return m.start()


def negation(folded: str, start: int) -> dict | None:
    """{"word", "carve_out"} when a negation governs the action at `start`, else None. The
    negation is the last one before `start` in the same clause and at most MAX_GAP characters
    away; a double negative or idiom right after it ("don't forget to") is not a prohibition."""
    if start is None:
        return None
    before = folded[:start]
    last = None
    for m in NEG.finditer(before):
        last = m
    if last is None:
        return None
    gap = folded[last.end():start]
    if len(gap) > MAX_GAP or BREAK.search(gap) or DOUBLE.match(folded, last.end()):
        return None
    tail = folded[start:]
    c = CARVE.search(tail)
    end = re.search(r"[.;!?](\s|$)", tail)
    carve = None
    if c and (end is None or c.start() < end.start()):
        carve = c.group(0).strip()[:CARVE_CAP]
    return {"word": last.group(0), "carve_out": carve}
