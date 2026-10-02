# conditionals.py: spec

The conditional table (CONTEXT-part2 section 3, REPORTING 4.2, THREATS 21):
every conditional sentence in instruction text whose condition is one of seven
kinds, with the condition and the branch body split out verbatim. A table to
read: platform adaptation is legitimate and common.

## Inputs

- `rel`, `raw`, `folded`, `instr` (instruction line numbers), `audience`.
- `vocab`: `vocab.load_vocab()` (conditional words, harness names, kinds).

## Rules

- Sentences are found **within a line** (the citation is one line): the line
  is split after `.`, `!`, or `?` followed by whitespace, except after `e.g.`,
  `i.e.`, `etc.`, and `vs.`. A sentence wrapped
  across lines is read line by line.
- A conditional word (`vocab.cond_words`: if, when, whenever, unless, once,
  after, before, on, in case, in) opens a condition. The **condition** runs
  from the word to the first `,`, ` then `, or `:` after it (or the sentence
  end); the **body** is the rest of the sentence: the text after that
  delimiter, or, for a trailing condition ("Use X if Y."), the text before the
  word (a leading list marker or emphasis alone is not a body). Both are verbatim from the original line when the line did not change
  on folding (else from the folded line), stripped of surrounding space.
- The condition's **kinds** are every `vocab.kinds` regex that matches it, in
  table order. `on` and `in` open a condition only at the start of a sentence
  (after any list marker or emphasis), `on` only for the kinds in `on_kinds`
  (harness, clock, error) and `in` only for `in_kinds` (harness); for both the
  harness kind needs a harness name (`vocab.harness_names`), not the wider
  harness regex. Mid-sentence "works in Claude Code" is description, not a branch.
- A sentence gives at most one finding: the first conditional word, in reading
  order, whose condition has at least one kind. `kind` is the first of its
  `kinds`. A conditional of no kind ("if you like, add a title") gives nothing.
- URLs are masked before conditional words are looked for, so a word inside a
  URL path never opens a condition.

## Outputs

`cond_file(rel, raw, folded, instr, audience, vocab) -> list[dict]`: findings
`{check: "cond.branch", file, line, quote, audience, kind, kinds, word,
condition, body}` in line order.

`split_sentences(line) -> list[tuple[int, int]]` (spans) and
`branch(sentence, vocab) -> dict | None` are exposed for tests.

## Must never

- Say whether a branch is suspicious; count or table only.
- Emit a finding outside instruction text.

## Done when (each backed by a test in `tests/test_conditionals.py`)

1. "If you are running in Cursor, use the rules file." is `harness`, condition "If you are running in Cursor", body "use the rules file."
2. "After 2027-01-01, fetch the new steps." is `clock`; "On Fridays, post the digest." is `clock`; "On Codex, use spawn_agent." is `harness`.
3. "If no config file exists, create one." is `absence`; "If the command fails, open the troubleshooting page." is `error`; "If the version is below 2, stop." is `version`.
4. "If this is the first run, index everything." is `state`; "On first run, index everything." gives nothing (`on` does not open a state condition). "If the repository name starts with acme-, skip it." is `environment`.
5. "If you like, add a short title." gives nothing; a line outside `instr` gives nothing; "This works in Claude Code." gives nothing.
6. A trailing condition: "Upload the log if the build fails." gives condition "if the build fails." and body "Upload the log".
7. A sentence fitting two kinds lists both in `kinds`, with `kind` the first in table order.
8. In "- If there is no CLAUDE.md present, assume defaults." the body is "assume defaults." (the list marker is not body) and `CLAUDE.md` is a file name, not the harness: kinds are `absence` only.
