# inputs.py: spec

Gets the stage 1 to 4 reports (and stage 3's `graph.json`) for one input,
either from a folder of saved reports or by running the stage runners as
subprocesses. Stage code is never imported.

## Inputs

- `load_dir(reports_dir)`: a folder holding `01-inventory.json`,
  `02-reader.json`, `03-graph.json`, `04-phrases.json`, and optionally
  `graph.json`.
- `run_stages(input_dir, stages_root, python, work_dir)`: runs, with `python`:
  1. `stages_root/01-inventory/run.py <input_dir>`, its stdout saved to
     `work_dir/01-inventory.json`;
  2. `stages_root/02-reader/run.py <input_dir>`;
  3. `stages_root/03-graph/run.py <input_dir> --inventory <saved 01> --out <work_dir>`
     (which writes `work_dir/graph.json`);
  4. `stages_root/04-phrases/run.py <input_dir> --inventory <saved 01>`.
  Passing the saved stage 1 report is the documented way to give stages 3 and 4
  the same stage 1 result (their run specs, Done-when "`--inventory` gives the
  same findings"); stage 1 then runs once.
- `skips(reports)`: the loaded reports.

## Outputs

- `load_dir` and `run_stages` return `(reports, graph)`: `reports` is
  `{"01": {...}, "02": {...}, "03": {...}, "04": {...}}`, each a contract-1
  report; `graph` is the parsed `graph.json`, or `None` when `load_dir` finds
  none.
- Each report must parse as JSON, have `contract` 1, the right `stage`
  (`01-inventory`, `02-reader`, `03-graph`, `04-phrases`), and a `findings`
  list. Otherwise `ReportError` (message names the stage).
- `run_stages` raises `StageFailure` (message names the stage, the exit code,
  and the tail of its stderr) when a runner exits non-zero or prints no valid
  report. A missing report file in `load_dir` is a `ReportError`.
- `skips(reports)` returns `[(stage, finding)]` for every finding carrying
  `skipped`, in stage order.

## Must never

- Import code from another stage, or run anything from the input.
- Write anywhere but `work_dir`.
- Treat a skip in an input stage as a failure.

## Done when (each backed by a test in `tests/test_inputs.py`)

1. `load_dir` on a folder of four valid reports plus `graph.json` returns them
   keyed `01` to `04` and the graph; without `graph.json` the graph is `None`.
2. A missing report file, a report with the wrong `stage`, or `contract` other
   than 1 raises `ReportError`.
3. `run_stages` with fake runners (small scripts written by the test that print
   canned reports) returns the four reports and the graph, and stages 3 and 4
   receive `--inventory` pointing at the saved stage 1 report.
4. A fake runner that exits non-zero raises `StageFailure` naming its stage.
5. `skips` lists a skipped finding with its stage.
