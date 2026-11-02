# 02.1-inventory: what ships

**Question:** what ships?
**Kind of evidence:** counting and parsing. No file is read for meaning.
**Plain name:** What ships (its heading in `full.md`).

## Inputs

- `<input_dir>`: the folder audited, read-only.
  `python stages/02-coded/02.1-inventory/run.py <input_dir>`
- Nothing from `data/` (`reads` in `stages/stages.json` is empty) and no table from `Library/`.
- Optional: `python-magic` (needs libmagic), else the pure-python `filetype` package, said on stderr.

## Process

It walks the folder, pins it, and records one row per file and one per structural fact, in this order:

1. `inv.pin` (`walk.py`): the git HEAD when the folder is the top level of its own work tree, else a sha256
   over the sorted files; file and byte totals.
2. `inv.file` (`census.py`, `entrypoints.py`): extension, bytes, lines, exec bit, encoding, BOM, detected
   type, entry-point kind.
3. `struct.census` (`census.py`): the flags `reader-window`, `long-line`, `ext-magic-mismatch`, `bom`,
   `archive`, `symlink`.
4. `struct.description` and `struct.agent-tools` (`frontmatter.py`): descriptions verbatim, granted tools.
5. `struct.hooks`, `struct.manifests`, `struct.mcp` (`configs.py`): hook rows, platform manifests, MCP servers.
6. `inv.license` (`licenses.py`): license files and declared license fields, matched to fixed wording.

Items 4 and 5 keep a person's words, and this step runs before the secret scan, so they also say the lines those words come from
(`span`, `event_line`; `spans.py`). The runner masks the saved report once `02.6-builder` has read it
(`stages/_shared/specs/shared.SPEC.md`, secretmask).

Never: open a file for meaning; run anything from the input; follow a symlink out of the tree; write inside
`<input_dir>`; call a flag "suspicious" (a flag is a location and a measurement); fail the run because an
optional tool is missing (a check that cannot run is a skip).

## Outputs

- stdout: one contract-1 report; the runner saves it as `data/02.1-inventory.json`, and stderr as
  `data/02.1-inventory.notes.txt`. It writes no other file.
- Its `inv.pin` names the run (the hash in `<date>_<hash7>`) and is the first thing the brief states.

## The human check

A flag is a place and a count, not a verdict: a file over 2,000 lines or 50 KB is something the AI's reader
window may cut, not a fault. The fixtures in `Fixtures/02.1-inventory/` (descriptions, manifests, agent grants,
hooks, MCP servers, the reader limit, licenses) and `python tools/grader/grader.py 02.1-inventory` show that
each check finds what it should and nothing it should not; the result is this step's validation stamp in
`LOG.md`.

## Spec

`specs/inventory.SPEC.md`: one section per script (`run`, `walk`, `census`, `entrypoints`, `frontmatter`,
`configs`, `licenses`).
