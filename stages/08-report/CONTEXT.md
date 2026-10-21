# Stage 8: Report

**Question:** none. Stage 8 assembles; it detects nothing and concludes nothing.
**Output:** a run folder (`docs/RUN-FOLDER.md`; layout in `layout.py`): `summary.html` (one
page, for deciding whether to use the repository), `details.html` (every section in full, for
improving it), `review.html` (the places one at a time, for the reader to mark), `full.md` (every
finding, cited, stage order, then recommendations), and `LOG.md` at the top, everything else
under `data/`. The index of the outputs and their specs: `specs/REPORTS.md`.

Built 2026-09-29, ahead of stages 6 and 7; stage 6 joined the pipeline the same day. Stage 7
has no folder of its own: its content is gathered here from what stages 1 to 6 say they
skipped (their stderr notes and skip findings), the test data set aside, and the standing
limits, and written as section 7 and `data/07-limits.md`.

Sources: `pre-planning/REPORTING.md` (Part A layout, summary rules,
recommendation rules), `pre-planning/RUN-LAYOUT.md` (run folder, LOG.md),
`pre-planning/METHOD.md`, `stages/CONTRACT.md`. Not a blind build: there are no
stage 8 fixtures and nothing to be blind to.

## What it does

```
python stages/08-report/run.py <input_dir> --repo <name> [--results <dir>] [--date YYYY-MM-DD]
```

1. Creates `<results>/<repo>/<date>_<hash7>/` (default `<results>` is
   `RepoResults/`; `-2`, `-3` suffix when the folder exists). Refuses a run
   folder inside `<input_dir>`.
2. Runs stages 1 to 6 once each as subprocesses, in order: stage 1 once, its
   report passed to 3 and 4 with `--inventory`; stages 2 to 6 with `--out`
   `data/` (so `normalized/`, `graph.json`, `hits.json`, `capability.json`, and
   the stage 6 packet land there); stages 5 and 6 with `--reports` `data/`. Each
   report is saved as `data/NN-name.json`, each stage's stderr as
   `data/NN-name.notes.txt`. A stage that fails stops the pipeline; LOG.md shows it
   unfinished and later stages are not run.
3. Runs the grader for stages 1 to 6 (`grader.py <stage> --json`, with the run's stage 6
   choices) and records each result as that stage's **validation stamp** (REPORTING
   principle 6).
4. Writes `LOG.md`, `data/07-limits.md`, `summary.html`, `details.html`, `review.html`,
   `full.md`, with the reader's marks (`marks.py`).

## Rules carried from REPORTING

- Stage order everywhere. Plain-language headings (REPORTING "Section names").
- No verdict, no score, no severity, no ranking. Trifecta 3 of 3 is stated with
  the fixed qualifier.
- Every count resolves to file:line in the full report.
- A stage whose validation stamp is not PASS says so on its status line in `full.md` and
  points to section 7; `details.html` puts a pill on Other details, and `summary.html` names the
  step under its headline. A zero from an unvalidated stage is never shown as clean.
- Benign share: a hit count carries one only when stage 6 labels ran (C15, 2026-10-03).
- The places to check (`details_html.first_items`: listed on `details.html`, one card each on
  `review.html`, sorted into concern kinds on `summary.html`) are chosen by fixed rules, never
  by judgment:
  1. stage 1: hook rows (event, command).
  2. stage 2: `hidden+phrase` pairs on lines addressed to the model (stage 4
     `audience` not `human`); human-facing ones (issue and PR template comments)
     are counted, not listed (2026-09-29).
  3. stage 3: `orphan+phrase` and `dynamic+phrase` pairs (load-only files).
  4. stage 4: hits on the **zero-base-rate patterns** PHRASES lists as the ones
     to run first on an unknown repo (`POINT_PATTERNS` in `render.py`); term conflicts and
     redefined safety words; likely committed secrets; flagged text past the reader window;
     a flagged sentence repeated across files; rubric actions whose confirmation is redefined,
     or prohibited with no confirmation step.
  5. stage 5: test data and images a model-read file points at; read-only lines a tools list
     contradicts; `hook+phrase` pairs (an instruction in a script a context-injecting hook runs).
  6. stage 6, when a model ran: sweep passages, relational reads, and "do" reads, as model
     reads (experimental) in their own pass.
  Nothing is capped or ranked; files over the reader window are under Worth a look in Files.
- Load bytes are shown per host config, from stage 5's `cap.load-bytes` (one per
  hook config since 2026-09-29): when a plugin ships one hook per host, only one
  runs, so a sum double counts.
- Recommendations: only from fixed templates (`render.recommendations`), each conditional, each naming a narrower alternative, listed in
  stage then document order. A finding with no template gets none. One per file
  and template: a block of matching lines is one change. A permission-flag hit
  that edits a settings allow-list (`permissions.allow`, `allowedTools`,
  `settings.json`) gets its own template, not the skip-permissions one (2026-09-29,
  Case 003).
- Pair places (stages 2 and 3) list only lines the model reads (stage 4 audience
  `model` or `subagent`); pairs in scripts (`tool`) and human-facing files are
  counted, not listed. Stage 4 places list model, subagent, and tool lines (a
  zero-base-rate pattern in code is a capability locator) and count human-facing
  ones and test data.

## Deviations from RUN-LAYOUT (v1)

- Per-stage `NN-name.md` files are not written; each stage's JSON report is
  kept as `data/NN-name.json`, and `full.md` carries every finding in readable
  form. `04-terms.md` and `06-soft.md` do not exist; the term table is in section 4 and
  stage 6's packet is `data/06-packet.md`.

## Must never

- Detect: stage 8 reads stage reports, stage notes, and grader results only.
- Conclude, score, rank, or advise on installing.
- Write inside `<input_dir>`.
- Import code from another stage, with one exception (2026-10-03): the path rule in
  `stages/04-phrases/audience.py` (`audience`, `is_test_data`) is shared by stages 5, 6,
  and 8, so who a file is for is decided in one place. It decides nothing else.

## Stage 6 in the report (2026-09-29)

Stage 6 runs in the pipeline after stage 5, with the backends the user passes
(`--label`, `--compare`, `--relational`). Section 6 names every backend and whether
it is remote, counts labels and agreement, and lists relational reads and confident
`do` reads as places to check, the model reads (p >= 0.9 since 2026-10-01; 0.7 to 0.9
near the line). Answers never change sections 1 to 5.

## The summary as HTML, and re-rendering (2026-09-30)

The owner found `summary.md` busy and hard to read. Stage 8 also writes
`summary.html` (`summary_html.py`): the same facts in plain language, what to
look at first as grouped cards (stage 4 headlines say what matched, never what the
author meant), one plain sentence per stage with the technical line behind a
disclosure, light and dark themes. `summary.md` stays for text tools. (Since 2026-10-20 that
long page is `details.html` and `summary.md` is cut; see "Two pages" below.)

`run.py --rerender <run_dir>` rebuilds the reports from a finished run's saved stage
outputs, runs no stage and calls no model (only the grader, for stamps), and appends
a line to LOG.md. Report design changes no longer need a full re-run.

## The review page (2026-10-12, review C21)

`review_html.py` writes `review.html`: every place the summary's "Things to check" lists
(now under Risky asks and the other sections of `details.html`),
then the stage 6 model reads, one card at a time. Each card shows the line with three lines
either side from the run's own `normalized/text/` copy (never the audited folder), the matched
words, and what was flagged in plain words (`plain.py`, one entry per `patterns.yaml` row,
moved from the D3 labeling page). The reader marks each place Concerned, Not concerned, or Not
sure; the page renders no verdict and its marks change no report. Marks live in the browser and
leave as `marks.json`, which the reader saves in the run folder; a re-render reads it back.
Owner decisions: the places are Things to check plus model reads; no carry-over to the next run
in v1; whether marks feed stage 6 calibration is still open. A file where stage 4 found a
possible secret shows no lines around its places. Spec: `specs/review_html.SPEC.md`.

## Two pages, and marks that carry over (2026-10-20)

The owner saw two readers served by one page: someone asking "is this safe?" and someone
improving the repository. `summary.html` (`summary_html.py`) is now one page: the security
concerns found, by fixed kinds in a fixed order with one example each, what the repository can do,
and questions before use; what was not checked is on `details.html`. It never says "do not use", safe, or unsafe, and
gives no score. The long page moved to `details.html` (`details_html.py`), with a Not concerned box
on every row that names a place or an address. `summary.md` and `summary-v1.html` were cut (v1
stays at the tag `report-v1`); a re-render removes them.

Marks are one model across the pages (`marks.py`): Concerned, Not concerned, Not sure, saved by
the reader as `marks.json`. Each names its row by a stable key (what was flagged, never the line
number alone), and a run with no `marks.json` takes the newest earlier run's marks by key. This
replaces the v1 rule of no carry-over. Specs: `specs/REPORTS.md` and the specs it lists.
