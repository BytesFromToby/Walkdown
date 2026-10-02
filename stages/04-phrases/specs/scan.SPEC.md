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
