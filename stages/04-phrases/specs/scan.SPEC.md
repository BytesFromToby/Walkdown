# scan.py: spec

Runs the pattern table over one file's lines and builds the stage 4 findings
(CONTEXT "Findings").

## Inputs

- `rel`: the file's path relative to the input, forward slashes.
- `text`: the decoded file text.
- `rows`: the loaded pattern table (`patterns.load_table`).
- `audience`: the file's audience tag (`audience.audience`).

## Outputs

`scan_text(rel, text, rows, audience) -> list[dict]`:

- Lines come from `foldtext.split_lines` (split on `\n` only), numbered from 1,
  so every line number is the original's.
- Each line is folded (`foldtext.fold_line`) and every row that `applies` is
  tested on the **folded** line with `row.hits`.
- One finding per line per check that has at least one hit:
  `check`, `file` (`rel`), `line`, `quote` (the original line, verbatim, line
  ending removed), `patterns` (the ids that hit, in table order), `audience`,
  and `folded`: true when the folded line differs from the raw line and no
  pattern of this check hits the raw line (the hit exists only after folding,
  THREATS class 4), and `matches`: one `{pattern, text, start}` per id in
  `patterns`, the matched text on the folded line (at most 160 characters) and
  its offset in the folded line (2026-09-30).
- Findings are ordered by line, then by check in CONTRACT order.

`frontmatter_lines(lines) -> set[int]`: the 1-based numbers of the lines inside
a leading YAML frontmatter block: line 1 is `---`, and the block ends at the
next line that is `---` or `...`. The delimiter lines are not in the set. No
closing delimiter means no frontmatter.

## Must never

- Grep only the raw text; the folded copy is the input and the raw line is the quote.
- Drop, merge, rank, or score a hit.
- Change a line number.

## Done when (each backed by a test in `tests/test_scan.py`)

1. A line that hits two patterns of one check gives one finding listing both ids, in table order; a line that hits two checks gives two findings.
2. `quote` is the raw line verbatim, and `line` is its original number.
3. A keyword split by a zero-width character, or written in fullwidth letters, hits with `folded` true; a plain hit has `folded` false.
4. A line separator (U+2028) inside a line does not shift later line numbers.
5. A `where: frontmatter` row hits inside frontmatter only; `frontmatter_lines` finds the block and ignores an unclosed one.
6. `audience` is carried onto each finding, and an `audiences` restriction is honored.

## Added 2026-10-16 (review C25)

Each finding carries `negated`, `negation`, and `carve_out` from `negation.py`: `negated` is true
when a negation governs every pattern's action on the line (`negation.anchor` for where each
action starts). The finding is otherwise unchanged. Test: `tests/test_negation.py` (7).

## Added 2026-10-18 (review C37): instructions hard-wrapped across lines

Markdown joins the lines of a paragraph, and so does a model reading it, but the line pass reads
one line at a time: "add a machine-level backstop to" / "`~/.codex/config.toml` so ..." hits no
row, because the verb ends one line and the target starts the next.

`wrapped_findings` runs after the line pass, in Markdown files only (`.md`, `.markdown`, `.mdc`,
`.mdx`). For each line and the line after it, both in one paragraph, it folds the two joined by a
space and tests every row that applies. A check gives a wrapped finding only when neither line
hits it alone, so nothing the line pass found is counted twice. The finding is the usual one,
cited at the first line, plus `end_line` (the second line) and `wrapped: true`; `quote` is both
raw lines with a newline between them, and `matches` offsets are into the joined text.

A pair is never joined when either line is blank, in frontmatter, inside a fenced code block or
is a fence, a heading, a table row, a rule or setext underline, or starts with an HTML tag or
comment; or when the second line starts a list item, or one line is quoted (`>`) and the other
is not. Quoted lines join without the second line's `>`. A list item's continuation line joins.

Findings stay ordered by line; on one line, line-pass findings come before wrapped ones.

`run.mask_secret_lines` masks a wrapped finding when either of its lines holds a secret.

Not done: a match across three or more lines (only neighbours are joined), and the reverse
case, a line-pass hit that the next line undoes (`don't ask` / `hypothetical questions`).

Done when (tests in `tests/test_scan.py`, `tests/test_secret_scan.py`):

7. A row that hits only the joined pair gives one finding at the first line with `end_line`,
   `wrapped`, both lines as the quote, and the matched text from the joined line.
8. A check either line hits alone gives no wrapped finding for that pair.
9. Blank lines, list starts, fences, headings, table rows, rules, tag lines, quote boundaries,
   and frontmatter are never joined; only Markdown files are joined.
10. Quoted lines join without the marker; a list item's continuation joins.
11. A wrapped finding sorts after the line findings of its first line.
12. A secret on the second line masks the wrapped finding.

Fixture: `Fixtures/04-phrases/wrapped-lines.md` (grader rows `ph-wrap-*`: three wrapped
positives, the one-line twin, and negatives for a sentence boundary, a list, and a code fence).
