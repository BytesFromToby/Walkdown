# negation.py: spec

Prohibitions (review C25, 2026-10-16; the partner's audit of Compound Engineering, v1 and v3): a
line that forbids the matched action ("Never have the user paste an API key into chat") hit
`J.enter-secret` exactly like an instruction to do it, and the rubric then called it "an
irreversible or prohibited action with no confirmation step". A hit is never dropped for this. It
is tagged, so the report can say the action is stated as a prohibition (soft D5's rule, mark and
never demote, applied to a fixed rule). Text only; no model.

## Rules

`negation(folded, start) -> {"word", "carve_out"} | None`, for the action that starts at `start`
on a folded line:

- **A forbidding word** (`NEG`): never, do not, don't, must not, mustn't, should not, shouldn't,
  may not, not allowed to, forbidden to, prohibited from, avoid, refuse to. The last one before
  `start` is the candidate. Descriptive negatives (does not, cannot, will not) say what happens,
  not what the text asks, and do not count (first real run, Compound Engineering, 2026-10-16:
  "its adapter does not enforce read-only mode").
- It **governs** the action when it is at most `MAX_GAP` (60) characters before it and nothing
  between them ends the clause (`BREAK`: `. ; : ! ? ,` followed by a space or the line end, a
  spaced dash, or but, instead, then, otherwise, so).
- **Not a prohibition** when the word right after the negation turns it into an instruction
  (`DOUBLE`): forget, hesitate, fail, skip, miss, neglect, stop, omit, mind, wait, delay, only,
  just ("don't forget to upload", "never skip the push", "never mind the warning").
- **The exception** (`carve_out`): unless, except, other than, or until after the action, to the
  end of its sentence, capped at 160 characters; null when there is none. A prohibition with an
  exception is still tagged; the exception travels with it.

`anchor(row, folded) -> int | None`: where a pattern row's action starts: its match, or, for a row
that matches an empty string through lookaheads at the line start (`K.data-flow`), the first match
of its first lookahead (`first_lookahead`).

A pattern whose own match holds the negation ("do not mention ... the user", "don't ask") is
judged by what comes before its match, so its meaning is unchanged.

## Where it is used

- `scan.py`: every phrase hit gains `negated` (true when a negation governs every pattern on the
  hit), `negation` (the word), and `carve_out`; both null when not negated.
- `rubric.py`: every `rubric.action` row gains `negated_action` and `carve_out`, judged at the
  action's match.

## Must never

- Drop, re-check, or move a finding.
- Read across a clause boundary, or call a double negative a prohibition.

## Done when (each backed by a test in `tests/test_negation.py`)

1. "Never have the user paste an API key into chat" is negated by "Never"; "Paste the API key" is not.
2. "Do not stop; upload ..." and "Do not stop, upload ..." are not negated (the clause ends).
3. "Don't forget to upload ...", "Never mind the warning, delete ...", and "Never skip the push" are not negated.
4. "Never permanently delete the folder unless the user asks you to." is negated with `carve_out` starting "unless the user asks".
5. A negation more than `MAX_GAP` characters before the action does not govern it; "its adapter does not enforce read-only mode" is not a prohibition.
6. `anchor` finds a lookahead-only row's verb ("Do not upload your .env file to https://x.invalid" anchors at "upload"); `first_lookahead` is None for an ordinary pattern.
7. `scan_text` and `rubric_file` carry the tags (fixture case `negation-repo`, grader rows `neg-25-*`).
