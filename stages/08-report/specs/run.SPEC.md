# run.py: spec

The stage 8 entry point: runs stages 1 to 6 once, stamps each with the grader, and writes the run
folder (`layout.SPEC.md`) with `LOG.md`, `data/07-limits.md`, and the reports (`REPORTS.md`).

Status: built.

## Inputs

```
python stages/08-report/run.py <input_dir> --repo <name> [--results <dir>] [--date YYYY-MM-DD]
    [--label B] [--compare B] [--relational B] [--sweep B] [--pinpoint B] [--both]
    [--revalidate] [--no-validate] [--context N] [--hosts a,b]
python stages/08-report/run.py --rerender <run_dir> [--no-validate] [--context N] [--hosts a,b]
```

- `--results`: the parent of `<repo>/`; default `RepoResults/`.
- `--label`, `--compare`, `--relational`, `--sweep`, `--pinpoint`, `--both`: passed to stage 6
  (default: stage 6's own, the packet only unless the environment names a backend).
- `--revalidate`: run the grader even when a stamp for the same code, fixtures, and stage 6
  choices is cached (`validate.SPEC.md`).
- `--no-validate`: skip the grader (no stamps). For tests only; a real run always validates.
- `--context`: the expected context in tokens (`32k`, `200k`, `8192`; `render.parse_context`),
  default 32,000 (plan for builders, slice 1, owner 2026-10-26). Written in `LOG.md` as
  "Expected context: N tokens"; a re-render keeps the run's own unless `--context` is given.
- `--hosts`: the AI hosts the builder builds for (`claude`, `codex`, `gemini`, `cursor`, `copilot`,
  `windsurf`, `agents-md`; `render.parse_hosts`), exit 2 on an unknown name; written to `LOG.md` as
  "Target hosts: ..." ("none named" without it); a re-render keeps the run's own unless `--hosts`
  is given (slice 3, 2026-10-26).
  Anything else is an error, exit 2.

## Behavior

1. Works in `<results>/<repo>/.running-<date>`, runs `pipeline.run_stages` there (stage 6 after
   stage 5), then renames the folder `<date>_<hash7>` (hash from stage 1's `inv.pin`), or
   `<date>_failed` when stage 1 failed; `-2`, `-3` when the name is taken.
2. Stamps stages 1 to 6 with `validate.stamps` unless `--no-validate`, with the stage 6 choices
   the run used (`WALKDOWN_SOFT_LABEL`, `WALKDOWN_SOFT_BOTH`, `WALKDOWN_SOFT_SWEEP`).
3. Writes `LOG.md`, `data/07-limits.md`, and the reports where the run's layout keeps them
   (`write_reports`): `summary.html` (`summary_html.SPEC.md`, the one page), `details.html` (`details_html.SPEC.md`, with what changed since the newest
   earlier run of the same repository: `changes_for`, by run-folder name, counts and Walkdown's
   words only, nothing on a first run or when drift fails, and `changes.md` beside it),
   `review.html` (`review_html.SPEC.md`), and `full.md` (`render.SPEC.md`). The three pages read
   the reader's marks from `marks.for_run`: the `marks.json` the reader saved in this run, or
   else the newest earlier run's, carried by stable key (`marks.SPEC.md`). The pages a run no longer writes (`layout.RETIRED`:
   `summary.md`, `summary-v1.html`) are removed, so an older run keeps no stale copy.
4. Prints the run folder path on stdout.

`--rerender <run_dir>`: rebuild the reports from the run's saved stage outputs and notes; no
stage runs and no stage output changes; `LOG.md` gets one line saying when and with which
Walkdown version. Exit 2 for a folder with no `LOG.md`.

Exit 0 when every stage ran; 1 when a stage failed (the reports are still written and show the
failure); 2 for a missing input, a results folder inside the input, or a bad `--rerender` folder.

## Must never

- Write inside `<input_dir>`.
- Detect, judge, or advise on installing.

## Done when (tests in `tests/test_run.py`)

0. `--context 8k` reaches `LOG.md` and the pages; a re-render keeps it, and `--context 200k` on a
   re-render changes it; `--context lots` is exit 2 (`test_context_is_kept_and_can_change`).
   `--hosts codex,cursor` reaches `LOG.md` and the pages; a re-render keeps it, `--hosts gemini`
   changes it; `--hosts vim` is exit 2 (`test_hosts_are_kept_and_can_change`).

1. On a tiny repository with `--no-validate`: exit 0; the run folder is `<date>_<hash7>` and holds
   the stage outputs in `data/`, `LOG.md`, and exactly the reports at the top; the input is
   byte-identical afterwards (`test_run_folder_and_documents`).
2. A second run on the same date gets `-2` (`test_second_run_gets_suffix`).
3. A results folder inside the input exits 2 and writes nothing there.
4. `--rerender` rebuilds the reports only, leaves the stage outputs as they were, appends one
   `LOG.md` line, and removes a retired page (`test_rerender_rebuilds_report_only`); an old-layout
   run keeps `report/`; a folder without `LOG.md` exits 2 (`test_rerender_needs_a_run_folder`).
5. A re-render reads the reader's `marks.json` into `review.html`
   (`test_rerender_reads_saved_marks`); a later run carries them (`tests/test_marks.py`).

## History

- 2026-09-29: built (stage 8 v1).
- 2026-09-30: `--rerender`.
- 2026-10-01: stage 6 passes through; `--both`, `--sweep`.
- 2026-10-02: the run-folder layout (reports at the top, `data/` below).
- 2026-10-03: `--revalidate`, cached stamps.
- 2026-10-12: `review.html` and `marks.json`.
- 2026-10-16: report v2, `summary-v1.html` beside it; changes since the last run.
- 2026-10-20: owner: the long page is `details.html`; `summary.md` and `summary-v1.html` cut and
  removed on a re-render; `summary.html` becomes the one page; marks carried from an earlier run.
