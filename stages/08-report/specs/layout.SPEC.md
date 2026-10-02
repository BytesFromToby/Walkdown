# layout.py (added 2026-10-02)

Where things live in a run folder, in one place, so the writer, `--rerender`, and
`walkdown.py`'s brief agree.

## Layout

```
RepoResults/<repo>/<date>_<hash7>/
  summary.html  summary.md  full.md    the reports: what people read
  LOG.md                               what ran, each stage's validation stamp
  data/                                everything else: stage outputs and working files
```

A run made before 2026-10-02 has no `data/`: its stage outputs sit at the top and its
reports in `report/`.

## Outputs

- `is_new(run_dir)`: true when `data/` exists.
- `data_dir(run_dir)`: `data/`, or the run folder for an old run.
- `report_dir(run_dir)`: the run folder, or `report/` for an old run.

## Must never

- Move or rewrite an existing run's files. An old run stays in its old layout, re-renders
  included.

## Done when (each backed by a test)

1. A new run has exactly LOG.md, the three reports, and data/ at the top (`tests/test_run.py`).
2. `--rerender` writes reports where the run's layout keeps them, old or new (`tests/test_run.py`).
3. `data_dir` and `report_dir` answer for both layouts (`tests/test_layout.py`).
