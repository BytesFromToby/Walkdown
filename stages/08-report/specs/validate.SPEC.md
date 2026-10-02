# validate.py: spec

Turns the grader's result for each stage into that stage's validation stamp
(REPORTING principle 6: no zero without validation).

## Inputs

- `stamps(root, python, stages) -> dict[str, Stamp]`: runs
  `python <root>/grader/grader.py <stage> --json` once per stage and parses it.
- `parse(doc) -> dict[str, Stamp]`: the parsing half, for a grader `--json`
  document.

## Outputs

`Stamp`: `result` (`PASS`, `FAIL`, `INCOMPLETE`, `NOT BUILT`, `SETUP ERROR`, or
`ERROR` when the grader could not be run or parsed), `gate` and `negative` as
`"passed/total"` strings (or None), `recall` as `"found/total"` (or None),
`skipped`: ids of expectations the grader marked SKIPPED, `text`: one line for
a log or a report, for example `PASS (gate 31/31, negative 46/46, recall 39/39)`
or `INCOMPLETE (gate 14/15, negative 12/12; skipped: rd-img-ocr)`.

## Must never

- Read `Fixtures/ANSWERS/` itself. The grader is the only reader of answers.
- Turn anything but a grader PASS into a PASS.

## Done when (each backed by a test in `tests/test_validate.py`)

1. A grader document with a PASS stage gives `result` PASS and the gate,
   negative, and recall strings.
2. An INCOMPLETE stage lists its SKIPPED ids in `skipped` and in `text`.
3. A grader run that prints no JSON gives `result` ERROR.

## Added 2026-09-29

- `stamps(root, python, stages, env)` passes `env` to the grader runs; stage 8 sets
  `WALKDOWN_SOFT_LABEL` to the run's labeling backend so stage 6's stamp is that
  backend's recall on the labeled set.
- More than three skipped ids collapse to `skipped: N rows`. Test:
  `test_long_skip_list_collapses`.
