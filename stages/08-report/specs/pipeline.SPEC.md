# pipeline.py: spec

Runs stages 1 to 5 once each, in order, as subprocesses, and saves what they
produce into the run folder.

## Inputs

`run_stages(input_dir, run_dir, stages_dir, python) -> list[StageRun]`

- `input_dir`: the repo copy under audit (read-only).
- `run_dir`: the run folder (exists, empty or not).
- `stages_dir`: the `stages/` folder.
- `python`: the interpreter to run each stage with.

## Behavior

- Order and arguments:
  - `01-inventory`: `run.py <input>`
  - `02-reader`: `run.py <input> --out <run_dir>`
  - `03-graph`: `run.py <input> --inventory <run_dir>/01-inventory.json --out <run_dir>`
  - `04-phrases`: `run.py <input> --inventory <run_dir>/01-inventory.json --out <run_dir>`
  - `05-capability`: `run.py <input> --reports <run_dir> --out <run_dir>`
- For each stage: stdout saved as `<run_dir>/<stage>.json` (after it parses as
  JSON), stderr saved as `<run_dir>/<stage>.notes.txt`, start and finish times
  recorded (UTC, ISO seconds).
- A stage that exits non-zero, or prints unparseable JSON, is recorded with
  `ok: False` and its error; no later stage runs.

## Outputs

A `StageRun` per stage attempted: `stage`, `ok`, `started`, `finished` (None
when not ok), `report` (dict or None), `notes` (list of stderr lines, blank
lines dropped), `error` (str or None).

`note_lines(text)`: the stderr lines, stripped, blank dropped, with any leading
`note: ` removed.

## Must never

- Write inside `input_dir`.
- Run a stage after one has failed.
- Import code from another stage.

## Done when (each backed by a test in `tests/test_pipeline.py`)

1. On a tiny repo (a SKILL.md and a README), all five stages run, five JSON
   reports and five notes files exist in the run folder, every `StageRun.ok` is
   True, and the input folder is byte-identical afterwards.
2. A stages folder whose stage 3 runner exits 1 gives three `StageRun`s, the
   third not ok with its error, and no `04-phrases.json`.
3. `note_lines` strips `note: ` and drops blank lines.

`soft` values may be `True` (added 2026-10-01): passed as a bare flag (`--both`). False
and None are dropped.

`stages` (added 2026-10-01): an optional subset of STAGES to run in order; baserates.py runs
stages 1 and 4 only.
