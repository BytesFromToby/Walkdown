# upstream.py: spec

Gets the stage 1 to 5 reports stage 6 reads, either from a folder of saved
reports or by running the stage runners as subprocesses. Stage code is never
imported. (Named `upstream`, not `inputs`, so it never collides with stage 5's
module of that name in one test session.)

## Inputs

- `load_dir(reports_dir)`: a folder holding `NN-name.json` reports. Stage 6
  needs `01-inventory.json` (file encodings), `04-phrases.json` (phrase hits, term
  and rubric rows) and `05-capability.json` (legs, pairs): these are `REQUIRED`.
  `02-reader.json` and `03-graph.json` are loaded and checked when present,
  never required.
- `run_stages(input_dir, stages_root, python, work_dir)`: runs, with `python`:
  1. `01-inventory/run.py <input_dir>`, saved to `work_dir/01-inventory.json`;
  2. `02-reader/run.py <input_dir>`;
  3. `03-graph/run.py <input_dir> --inventory <saved 01> --out <work_dir>`;
  4. `04-phrases/run.py <input_dir> --inventory <saved 01>`;
  5. `05-capability/run.py <input_dir> --reports <work_dir>` after reports 1 to
     4 are saved there as `NN-name.json` (stage 5's documented `--reports` form,
     so stages 1 to 4 run once).
- `skips(reports)`.

## Outputs

- `load_dir` and `run_stages` return `{"01": {...}, ..., "05": {...}}` (only the
  stages found, for `load_dir`), each a contract-1 report.
- A report must parse as JSON, have `contract` 1, the right `stage`, and a
  `findings` list, else `ReportError` naming the stage. A missing required file
  is a `ReportError`.
- `run_stages` raises `StageFailure` (stage, exit code, stderr tail) when a runner
  exits non-zero or prints no valid report.
- `skips(reports)`: `[(key, finding)]` for every finding with `skipped`, in stage
  order.

## Must never

- Import another stage's code or run anything from the input.
- Write anywhere but `work_dir`.
- Treat an input stage's skip as a failure.

## Done when (each backed by a test in `tests/test_upstream.py`)

1. `load_dir` on a folder with the five reports returns them keyed `01` to `05`;
   with only `01`, `04`, `05` it returns those three.
2. A missing required report, a wrong `stage`, or `contract` other than 1 raises
   `ReportError`.
3. `run_stages` with fake runners returns five reports; stages 3 and 4 get
   `--inventory` pointing at the saved stage 1 report; stage 5 gets `--reports`
   pointing at a folder that holds the four earlier reports.
4. A fake runner that exits non-zero raises `StageFailure` naming its stage.
5. `skips` lists a skipped finding with its stage key.
