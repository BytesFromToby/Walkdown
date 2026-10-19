# termset.py: spec (added 2026-10-19, review C22 b)

The version of stage 4's search terms and matching code. Every stage 4 report records it, so two
runs of the same repository can say whether a new or gone phrase hit comes from the repository
or from Walkdown (`stages/08-report/drift.py`). Runs used to record only the Walkdown commit,
which says that something in Walkdown changed, never what.

## Inputs

- `rows`: the loaded pattern table (`patterns.load_table`).
- The part 2 word lists (`vocab.yaml`, or a given path).
- Stage 4's own code: the `.py` files directly in `stages/04-phrases/` (tests sit in a subfolder).

## Outputs

`describe(rows, vocab_path=None, code_folder=None)` returns the report's `terms` block:

- `rows`: `{row id: short hash}` over the fields that decide a hit (`check`, `regex`, `unless`,
  `audiences`, `paths`, `where`). A row's `note` and `source` never change its hash.
- `vocab`: a short hash of the word lists as loaded (comments and layout do not count), or null
  when they cannot be read.
- `version`: a short hash of `rows` and `vocab` together: the search terms.
- `code`: a short hash of stage 4's code, line endings normalized, so the same commit checked out
  on Windows and on Linux gives the same value. Any change to that code changes it, including
  changes that do not move a phrase hit.
- `count`: the number of rows.

`diff(old, new)` compares two blocks: `rows_added`, `rows_changed`, `rows_removed` (ids, sorted),
`vocab_changed`, `code_changed`, `same` (none of those), and `known`, false when either block is
missing (a run from before 2026-10-19), with every other field empty or false.

Nothing is bumped by hand: editing a row's regex, adding or retiring a row, or changing the code
changes the version on the next run.

## Must never

- Count a row's `note` or `source`, or comments in the YAML, as a change.
- Read any file outside stage 4's folder.
- Guess a difference when a block is missing (`known` is false instead).

## Done when (each backed by a test in `tests/test_termset.py`)

1. A row's hash changes with its regex, unless, audiences, paths, or where, and not with its note
   or source; `version` follows any row change and the word lists.
2. `code_version` changes when a stage 4 file changes and is the same for LF and CRLF copies.
3. `diff` lists added, changed, and removed rows and the vocab and code flags; identical blocks
   are `same`; a missing block is `known` false.
4. The stage 4 report carries `terms` (`tests/test_run.py`).
