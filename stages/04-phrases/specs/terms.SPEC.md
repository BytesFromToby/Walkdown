# terms.py: spec

The term table (CONTEXT-part2 section 4, METHOD Stage 4, THREATS 14, PHRASES
B): every definition of a word in instruction text, every term defined more
than one way, and every definition of a safety word. Whether a definition is
reasonable is stage 6; which of two conflicting definitions governs is never
decided (THREATS 14).

## Inputs

- `rel`, `raw`, `folded`, `instr` (instruction line numbers), `audience`.
- `vocab`: `vocab.load_vocab()`.

## Rules: finding a definition (`defs_file`)

Only lines in `instr`. Sources, in this order; a line gives at most one
definition per term:

- `explicit`: `X means`, `X is defined as`, `X refers to` (`vocab.explicit_kw`),
  and `by X we mean` (`vocab.explicit_by`), within one sentence of the line.
  X is a quoted, backticked, or emphasized token right before the keyword if
  there is one; otherwise the words between the last `,` `;` `:` `|` or
  sentence start and the keyword, with a leading list marker, a leading
  article, and "the word" / "the term" dropped. X of more than `max_term_words` words, or made only of
  `not_terms` words ("this means", "which means"), is not a definition; nor is
  "by no means" / "by any means". The definition is the text after the keyword
  to the sentence end.
- `mapping`: `when the user says X` / `if the user asks for X` (`vocab.mapping`).
  X is the quoted text right after the phrase if quoted, else the words up to
  the next `,`. The definition is the text after that `,` (or after the closing
  quote and any comma) to the sentence end. No text after X means no definition.
- `glossary`: under a markdown heading matching `vocab.glossary_heading` (until
  the next heading of the same or higher level), a line `**X**: def`,
  `**X:** def`, or a list item `- X: def` with X of at most `max_term_words`
  words. The definition is the text after the colon.
- `procedural`: a heading `How to X` or `Steps to X`
  (`vocab.procedural_heading`); the term is X and the definition is the first
  non-blank line after the heading (none: no definition). The finding's `line`
  is the heading line.

`term` is normalized (`normalize_term`): quotes, backticks, and markdown
emphasis (`*`, `_`, `~`) removed, lowercased, whitespace collapsed, trailing
punctuation removed. `definition` is verbatim from the original line when the
line did not change on folding (else the folded line), stripped of surrounding
space. An empty term, or a definition with no word character (`"complete"
means.`), is not a definition.

Finding: `{check: "term.def", file, line, quote, audience, term, definition, source}`.

## Rules: across the run

- `conflicts(defs) -> list[dict]`: one `{check: "term.conflict", file: null,
  line: null, term, definitions}` per term with two or more different
  definitions, compared after lowercasing, collapsing whitespace, and removing
  trailing punctuation. `definitions` lists every definition of the term as
  `{file, line, text}` in file then line order. Ordered by term.
- `safety(defs, vocab) -> list[dict]`: one `{check: "term.safety", file, line,
  quote, audience, term}` per `term.def` where any word of the term matches
  `vocab.safety` (confirm, verify, done, safe, read-only, reversible, approve,
  permission, sandbox, allowed, and their inflections).

## Must never

- Decide which of two definitions is real, or call a definition safe or unsafe.
- Read definitions outside instruction text.

## Done when (each backed by a test in `tests/test_terms.py`)

1. `In this skill, "ship" means push to main.` gives term `ship`, definition `push to main.`, source `explicit`; `Confirmation means announcing your intent.` gives term `confirmation`.
2. `This means the tests pass.` and `by no means` give nothing; `By deploy we mean a tagged release.` gives term `deploy`.
3. `When the user says "tidy up", delete the branch.` gives a `mapping` definition of `tidy up`.
4. A `## Glossary` section with `- **Done**: merged and pushed` gives a `glossary` definition of `done`; the same line under `## Usage` gives none.
5. `## How to fix` followed by `Run the repair script.` gives a `procedural` definition of `fix` at the heading line.
6. Two different definitions of `ship` in two files give one `term.conflict` listing both; two identical definitions (differing only in case and spacing) give none.
7. A definition of `confirmation` or `verified` gives a `term.safety` finding; one of `ship` does not.
8. A line outside `instr` gives no definition.
9. `- Delete means delete` gives term `delete` (the list marker is not part of it); `| a | Delete means delete. |` gives term `delete`; `"complete" means.` gives nothing.
