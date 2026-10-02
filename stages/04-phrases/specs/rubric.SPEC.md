# rubric.py: spec

The harness rubric (CONTEXT-part2 section 1, THREATS 22, PHRASES J): for every
`phrase.J.prohibited` action in instruction text, its harness tier and whether
a confirmation step sits in the same step. A table to read, never a verdict.

## Inputs

- `rel`, `raw` (original lines), `folded` (the same lines folded), `instr`
  (set of 1-based line numbers that are instruction text), `audience`.
- `rows`: the pattern table; only `phrase.J.prohibited` rows are used.
- `vocab`: `vocab.load_vocab()`.

## Rules

- A line is a rubric line when it is instruction text and a J row hits its
  folded copy. Rows of the `ignore_unless_tier` tier (confirm-first) are run
  **without** their `unless`: that `unless` is part 1's same-line stand-in for
  a confirmation step, and the rubric measures the step itself. Prohibited-tier
  rows keep their `unless`. So every part 1 J hit in instruction text is a
  rubric line, plus confirm-first lines part 1 cancelled.
- One finding per rubric line. `tier` is `prohibited` if any prohibited row
  hits, else `confirm-first`; `action` is the text the first hitting row of that
  tier matched, taken from the original line when the line did not change on
  folding (else from the folded line); `patterns` lists every hitting J row.
- **The step** (`step_span(lines, n)`): if line `n` is a markdown list item
  (`-`, `*`, `+`, or `1.` / `1)` marker) or an indented continuation of one,
  the step is that item: the marker line plus the following non-blank lines
  indented deeper than the marker. Otherwise the paragraph: the run of
  consecutive non-blank lines around `n`, stopped by a heading, a list item,
  or a code fence line.
- A confirmation is a match of any `confirm` regex on a folded line of the
  step. It is negated when the text just before it matches `neg_before`
  ("without asking", "no need to confirm", "do not ask") or the text just after
  it matches `neg_after` ("confirmation is not required"). A match of
  `neg_forms` ("without asking", "no need to confirm", "do not ask") is a
  negated confirmation too.
- `confirmation` true when the step holds a non-negated confirmation;
  `confirm_line` and `confirm_quote` (the original line) name the first one,
  searching the action line first, then the step in line order.
  `negated_confirmation` true when the step holds a confirmation and every one
  is negated. When `confirmation` is false, `confirm_line` and `confirm_quote`
  are null.

## Outputs

`rubric_file(rel, raw, folded, instr, audience, rows, vocab) -> list[dict]`:
findings `{check: "rubric.action", file, line, quote, audience, tier, action,
patterns, confirmation, negated_confirmation, confirm_line, confirm_quote}`
in line order.

## Must never

- Say whether an action is acceptable; `confirmation: false` is a fact, not a finding of fault.
- Emit a row for a line outside instruction text (a `POST` in a script is code).
- Change or drop a part 1 finding.

## Done when (each backed by a test in `tests/test_rubric.py`)

1. A confirm-first verb alone in its paragraph gives `confirmation: false`, `tier: confirm-first`.
2. A verb with "ask the user to confirm" on the same line gives a row (though part 1 cancels it) with `confirmation: true` and `confirm_line` that line.
3. A list item whose indented continuation line says "Wait for the user's approval" gives `confirmation: true` with `confirm_line` the continuation line; the next list item is a different step.
4. "Send it without asking" gives `confirmation: false`, `negated_confirmation: true`.
5. A prohibited row hit ("permanently delete") gives `tier: prohibited`.
6. A line outside `instr` gives no row.
7. `step_span` covers a list item with continuation, a paragraph, and stops at a heading.

## Added 2026-09-29

A line in the step matching `REDEFINES_CONFIRM` (a confirmation word followed by
`means`, `is defined as`, `refers to`, `is when`, `counts as`) is skipped as a
confirmation and sets `confirm_redefined: true` (THREATS 14). Test:
`test_redefining_confirmation_is_not_a_confirmation`.

A line inside a fenced block: the step is the block plus the paragraph just
before its opening fence and the paragraph just after its closing fence. Tests:
`test_fenced_block_is_one_step_with_its_lead_in_and_follow_up`,
`test_fenced_block_without_confirmation`.
