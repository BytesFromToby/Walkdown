# layout.py: spec

Where things live in a run folder, in one place, so the writer, `--rerender`, and `walkdown.py`'s
brief agree.

## Layout

```
RepoResults/<repo>/<date>_<hash7>/
  summary.html  details.html  review.html  full.md    the reports (REPORTS.md)
  changes.md                    what changed since the previous run, when there is one
  marks.json                    the reader's marks, once saved
  LOG.md                        what ran, each stage's validation stamp
  data/                         everything else: stage outputs and working files
```

`REPORTS` names the reports; `RETIRED` the pages runs wrote before 2026-10-20 (`summary.md`,
`summary-v1.html`), which a re-render removes. A run made before 2026-10-02 has no `data/`: its
stage outputs sit at the top and its reports in `report/`.

## Outputs

- `is_new(run_dir)`: true when `data/` exists.
- `data_dir(run_dir)`: `data/`, or the run folder for an old run.
- `report_dir(run_dir)`: the run folder, or `report/` for an old run.

## Must never

- Move or rewrite an existing run's files, apart from removing the retired pages. An old run
  stays in its old layout, re-renders included.

## Done when (each backed by a test)

1. A new run has exactly `LOG.md`, the reports, and `data/` at the top (`tests/test_run.py`).
2. `--rerender` writes reports where the run's layout keeps them, old or new, and removes a
   retired page (`tests/test_run.py`).
3. `data_dir` and `report_dir` answer for both layouts (`tests/test_layout.py`).

## History

- 2026-10-02: built: reports at the top, `data/` below.
- 2026-10-16: `summary-v1.html` beside report v2.
- 2026-10-20: owner: `details.html`; `summary.md` and `summary-v1.html` retired.
