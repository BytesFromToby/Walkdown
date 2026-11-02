# baserates.py (added 2026-10-01, soft D1; a tool since restructure step 7)

Measured base rates of `02.4-phrases` patterns over the audited corpus: how often each pattern
turns up in repos already audited. A published fact about a pattern, recomputed as the
corpus grows; never a judgment of the artifact under review (CHARTER). This is the writing half;
the report reads the table through `stages/_shared/rates.py` (`../../stages/_shared/specs/shared.SPEC.md`,
section "rates").

## Inputs

`python tools/baserates.py <label>=<input_dir> [...] [--out PATH]`; the default out is
`Library/baserates.json` (committed; the report stage reads it).

**Label each input neutrally** (`repo-1`, `repo-2`, ...), never with the repository's name: the
Library is public, and the table keeps each label (and the commit hash) it is given. The help says so,
and so does this spec (notes M15 b: the table's four labels are `repo-1` to `repo-4`; a real name would
bring the repository's name back into a public file).

## Outputs

- For each repo: the inventory and the phrase steps run in a temporary folder
  (`pipeline.run_stages` with `stages=["02.1-inventory", "02.4-phrases"]`); `{name (the label), hash
  (inv.pin), lines: {pattern id: lines hit}}`.
- `count(report04)`: phrase findings only, skipped ones excluded, audience not `human` or `test-data`
  (the lines the places to check draw from); a line hit by a pattern under two checks counts once.
- The table: `generated`, `what`, `levels` (`rates.LEVELS`), and `repos`.

## Must never

- Judge, weight, sum, or rank. A level is a bin of a count, shown with the count.
- Write inside a corpus repo.

## Done when (each backed by a test in `tests/test_baserates.py`; the reading half in `stages/_shared/tests/test_rates.py`)

1. `count` counts non-human, unskipped phrase lines once per line.
2. The help and the error ask for neutral labels (`test_the_help_and_the_error_ask_for_neutral_labels`).
3. The table it writes carries the levels the report reads and loads back through the reader
   (`test_the_table_it_writes_carries_the_levels_the_report_reads`).

## History

- 2026-10-01: built as `stages/05-report/baserates.py`.
- 2026-10-29: restructure step 7: moved to `tools/` (Q13); the reading half (`level`, `rate`, `phrase`, `load`) is
  `stages/_shared/rates.py`, since a stage does not import a tool; the spec and help ask for neutral labels (M15 b).
