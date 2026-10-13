# pinpoint.py (added 2026-10-13, owner)

For each sweep passage the report shows, a second model names the line that does the flagged
kind of action, quotes it, and says it in one plain sentence. A sweep passage can be a dozen
lines; a reader new to this cannot tell which part is the issue. Opt-in: `--pinpoint
claude-cli`, and only with `--sweep`. Prototype and the three hand runs it was shaped on:
`pre-planning/soft/pinpoint/`.

## Inputs

- Stage 6's own `soft.sweep` findings, the decoded lines of each passage (packet.Lines), and
  `softreads.yaml` `pinpoint` (`system`, `question`) plus the sweep option's `what` text for
  the kind the passage was read as.

## Outputs

- `targets(findings)`: the `soft.sweep` findings the report shows as their own card: not
  skipped, `p_any >= MIN_P` (0.4, the report's near-the-line floor, `render.SWEEP_NEAR_P`), and
  no stage 4 pattern inside (`covered` empty).
- `question(finding, lines, data)`: `{qid: "pin:" + sweep qid, sweep_qid, _prompt, _system}`.
  The prompt holds the kind in the sweep option's own words, the passage as numbered lines
  marked as data, and the JSON shape asked for.
- `parse(text)`: the JSON object in an answer, or None.
- `locate(n, quote, lines)`: the last line of `quote` when it starts on line `n`; prose is
  hard-wrapped, so a quote may run onto the next lines of the passage. Spaces are folded.
  None when the quote does not start on line `n`.
- `find(n, quote, lines)`: `(start, end)` of the quote: on line `n` when it starts there, else on
  the first passage line it does start on (owner, 2026-10-13: a model can be a line off; the
  superpowers run had one, "run" ending line 447 quoted as line 448). None when the quote is
  nowhere in the passage.
- `check(answer, lines)`: `verified`, `why`, `line`, `line_end`, `quote`, `plain`, `also`.
  Verified when the quote is found in the passage and `plain` is not empty, or when no line is
  named and `plain` says so. `line` is where the quote really starts; `why` says when that
  differs from the model's number. `also` keeps at most 2 entries that pass the same check.
- `findings(targets, questions, answers, lines_of)`: one `soft.pinpoint` finding per target
  (fields in `stages/CONTRACT.md`), or `skipped` (no answer, the backend's skip, or
  `unparseable pinpoint answer`).

## Must never

- Change, demote, or remove a `soft.sweep` finding, or any stage 1 to 5 finding. "No line does
  this" is recorded, never acted on.
- Keep a quote that is not in the passage, word for word, in the run's own text, or show it at
  a line other than the one it starts on.
- Hand the model tools or the user's settings: the backend is `back_claude.py`, with the same
  isolation as every read (`--tools ""`, `--safe-mode`, no setting sources).

## Done when (each backed by a test in `tests/test_pinpoint.py`, `tests/test_run.py`)

1. Targets are exactly the passages the report shows.
2. A quote may run onto the next lines but must start on its line; invented quotes and lines
   outside the passage fail. A real quote under the wrong line number is moved to its line.
3. `check` keeps only quotes found in the text, drops failing `also` entries, accepts "no line"
   with a plain sentence, and refuses an empty plain sentence.
4. Skipped and unparseable answers are recorded as skips.
5. The question carries the numbered lines, the kind in the sweep option's words, and the
   data-not-instructions rule.
6. `run.py --sweep jev --pinpoint claude-cli` writes one `soft.pinpoint` per shown passage and a
   `pinpoint` backend row; `--pinpoint` without `--sweep` asks nothing.

## Known limits

- No grader rows: the answer is a model's, so there is no fixed expected line to gate on yet.
  The quote check is the gate on each answer. Fixtures with a known right line, and one where
  the honest answer is "no line", are the next step.
- The second read varies run to run (the hand runs named the same main line each time; the
  "also" lines and the plain wording changed).
