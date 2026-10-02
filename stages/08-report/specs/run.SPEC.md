# run.py: spec

The stage 8 entry point: runs stages 1 to 5 once, stamps them with the grader,
and writes the run folder (RUN-LAYOUT) with LOG.md, 07-limits.md, and
report/summary.md + report/full.md.

## Inputs

```
python stages/08-report/run.py <input_dir> --repo <name> [--results <dir>] [--date YYYY-MM-DD] [--no-validate]
```

- `--results`: parent of `<repo>/`; default `RepoResults/`.
- `--no-validate`: skip the grader (stamps absent). For tests only; a real run
  always validates.

## Behavior

1. Works in `<results>/<repo>/.running-<date>`, runs `pipeline.run_stages`
   there, then renames the folder to `<date>_<hash7>` (hash from stage 1's
   `inv.pin`), or `<date>_failed` when stage 1 failed; `-2`, `-3` when taken.
2. Runs `validate.stamps` for stages 1 to 5 unless `--no-validate`.
3. Writes `LOG.md`, `07-limits.md`, `report/summary.md`, `report/full.md`.
4. Prints the run folder path on stdout.

Exit 0 when every stage ran; 1 when a stage failed (documents are still written,
showing the failure); 2 for a missing input folder or a results folder inside
the input.

## Must never

- Write inside `<input_dir>`.
- Detect, judge, or advise on installing.

## Done when (each backed by a test in `tests/test_run.py`)

1. On a tiny repo with `--no-validate`, exit 0; the run folder is named
   `<date>_<hash7>` and holds the five stage JSONs, LOG.md, 07-limits.md, and
   both reports; the input is byte-identical afterwards.
2. A second run on the same date gets a `-2` suffix.
3. A results folder inside the input exits 2 and writes nothing there.

## Added 2026-09-29

Runs stage 6 after stage 5. `--label`, `--compare`, `--relational` pass through to
stage 6 (default: stage 6's own default, packet only unless the environment names a
backend). The grader stamps stage 6 with `WALKDOWN_SOFT_LABEL` set to `--label`.

`--rerender <run_dir>` (2026-09-30): rebuild `report/summary.md`, `summary.html`,
`full.md` from the run's `NN-name.json` and notes; no stage runs; stage JSONs are
unchanged; LOG.md gets one appended line. Exit 2 for a folder with no LOG.md. Tests:
`test_rerender_rebuilds_report_only`, `test_rerender_needs_a_run_folder`.

## `--both` (added 2026-10-01)

Passed to stage 6 as `--both` (Jev reads each line twice and averages). The grader stamp
for the run is taken with `WALKDOWN_SOFT_BOTH=1` as well as the label backend, so it tests
the configuration the run used. The report names the backend with ", two reads averaged".

## `--sweep` (added 2026-10-01)

Passed to stage 6 as `--sweep <backend>`; the grader stamp runs with
`WALKDOWN_SOFT_SWEEP` set the same.
