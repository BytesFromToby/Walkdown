# chunks.py (added 2026-10-01, soft D2)

Cuts the prose a model reads into passages for the coverage sweep. Reads only; asks no
model.

## Inputs

- Stage 1's inventory report; a `lines_reader(rel)` giving decoded lines (packet.Lines).

## Outputs

- `sweep_files(inventory)`: readable `inv.file` entries, not symlinks, with a prose
  extension (md, mdc, markdown, txt) and stage 4's path audience `model` or `subagent`.
  Sorted.
- `chunk_text(rel, lines)`: `{file, line, end_line, text}` per passage, 1-based inclusive.
  A leading YAML frontmatter block is one passage; each markdown heading (`#` to
  `######`, up to 3 leading spaces) starts a passage, except inside a code fence. A
  passage over `CAP` (1,200) characters is cut at a blank line once it reaches CAP / 2,
  or at a line end once it reaches CAP; a single line is never cut. Passages with no
  text after stripping are dropped.
- `build(inventory, lines_reader)`: every passage of every sweep file, file then line order.
- `covered(chunk, s4_findings)`: the stage 4 phrase patterns that hit inside the passage's
  lines (any audience), sorted.

## Must never

- Ask a model, write files, or follow a symlink.
- Cut inside a line.

## Done when (each backed by a test in `tests/test_chunks.py`)

1. Only prose a model reads is swept.
2. Frontmatter and headings start passages; a heading in a fence does not.
3. Long sections split at blank lines, never mid-line, with no gaps.
4. Blank passages dropped.
5. `covered` lists stage 4 patterns inside the lines only.
