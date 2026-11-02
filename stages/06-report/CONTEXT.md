# 06-report: the reports

**Question:** none. The report stage assembles; it detects nothing and concludes nothing. From a run folder's
`data/` and its record it writes every report. Running the steps, validating them, and naming the run folder
are the runner's (`stages/_shared/runner.py`); `walkdown.py` only routes.

## Inputs

- A run folder, `RepoResults/<repo>/<date>_<hash7>/`:
  `python stages/06-report/run.py <run folder> [--context N] [--hosts a,b]` (`--rerender <run folder>` is the
  same). A run with no record, or a record of an older format, is not re-rendered: one plain line, exit 2.
- In its `data/`: `<step>.json` and `<step>.notes.txt` for each step in `stages/stages.json` that ran
  (`01-intake` to `04-pinpoint`; an AI stage only when a person chose it); `run.json`, the record the runner
  wrote (each step's times and result, the validation stamps, the expected context, the target hosts);
  `05-qa.json` (the check of the run: the gaps and limits that section 7 and the lists of steps that did not work are
  drawn from; a run with none is not drawn); `capability.json` (the full evidence); `normalized/text/<path>.txt` (the text the run read, which the
  review page shows, never the audited folder).
- `marks.json` in the run folder (the reader's marks), else the newest earlier run's of the same repository;
  the previous run of that repository, for `changes.md`.
- From `Library/`: `patterns.yaml` (the plain words), `hosts.yaml`, `trigger.yaml`, `tools.yaml`, `fit.yaml`,
  `clean.yaml`, `loading.yaml`, and `baserates.json` (through `stages/_shared/rates.py`). The `VERSION` file.

## Process

Read each step's report and notes and the record; write `LOG.md` (once; a folder that has one gets one line
appended), `data/limits.md`, `changes.md`, `summary.html`, `details.html`, `review.html` (with the reader's
marks), `full.md`, and `brief.md`. Rules: stage order everywhere; plain-language headings; every sentence
a fixed template; every count resolves to a file and line in `full.md`; a step whose validation stamp is
not PASS says so, and a zero from an unvalidated step is never shown as clean; recommendations only from
fixed templates, each naming a narrower alternative.

A run the check of the run held (`held` in the record) is not drawn until `walkdown.py continue` releases it.

Never: detect; conclude, score, rank, or advise on installing (no verdict, no "safe" or "unsafe"); gather what a run
did not examine (the check of the run does); write
inside the audited folder; import another stage's code (it reads the other steps' outputs as data); run a
step, the grader, or a model; read `LOG.md` back.

## Outputs

In the run folder:

- `summary.html` (one page, eight questions at a glance, for deciding whether to use the repository),
  `details.html` (the same questions with everything behind them, for improving it), `review.html` (the
  places one at a time, where the reader marks Concerned, Not concerned, or Not sure), `full.md` (every
  finding, cited, in stage order), `brief.md` (the brief `walkdown.py` prints), `LOG.md`, and `changes.md`
  (what changed since the previous run, when there is one).
- `data/limits.md`: what the run did not examine. It removes the pages a run no longer writes
  (`summary.md`, `summary-v1.html`). stdout: the run folder's path.

## The human check

A person reads `summary.html` first, then `details.html`, and follows any count to its file and line in
`full.md`; `LOG.md` shows each step's validation stamp, and a step that did not run or failed its fixture
check is named on the pages and in the brief. The stage has no fixtures of its own (there is nothing to
be blind to): `stages/06-report/tests/` checks the pages. Re-rendering rebuilds the reports from the saved
outputs, so a design change needs no new audit.

## Spec

`specs/report.SPEC.md`: "The reports" first (the report set and who each file is for), then one section per
script (`run`, `brief`, `details_html`, `drift`, `glance`, `marks`, `qaview`, `render`, `review_html` with `plain.py`,
`summary_html`).
