# Stage 8: Report (v1)

**Question:** none. Stage 8 assembles; it detects nothing and concludes nothing.
**Output:** a run folder (`docs/RUN-FOLDER.md`; layout in `layout.py`): `summary.html`,
`summary.md` (one screen, stage order), `full.md` (every finding, cited, stage order, then
recommendations), and `LOG.md` at the top, everything else under `data/`.

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
4. Writes `LOG.md`, `data/07-limits.md`, `summary.html`, `summary.md`, `full.md`.

## Rules carried from REPORTING

- Stage order everywhere. Plain-language headings (REPORTING "Section names").
- No verdict, no score, no severity, no ranking. Trifecta 3 of 3 is stated with
  the fixed qualifier.
- Every count resolves to file:line in the full report.
- A stage whose validation stamp is not PASS says so on its status line and
  points to section 7. A zero from an unvalidated stage is never shown as clean.
- Benign share: no stage labels hits benign in v1 (that is stage 6), so every
  hit count says "benign share not measured".
- Points of attention (summary) are chosen by fixed rules, never by judgment:
  1. stage 1: hook rows (event, command); files over the reader window.
  2. stage 2: `hidden+phrase` pairs on lines addressed to the model (stage 4
     `audience` not `human`); human-facing ones (issue and PR template comments)
     are counted, not listed (2026-09-29).
  3. stage 3: `orphan+phrase` and `dynamic+phrase` pairs (load-only files).
  4. stage 4: hits on the **zero-base-rate patterns** PHRASES lists as the ones
     to run first on an unknown repo (`POINT_PATTERNS` in `render.py`).
  5. stage 5: `hook+phrase` pairs (an instruction in a script a context-injecting
     hook runs), then hook injection paths.
  At most 5 per stage in the summary, then "+N more in the full report".
- Load bytes are shown per host config, from stage 5's `cap.load-bytes` (one per
  hook config since 2026-09-29): when a plugin ships one hook per host, only one
  runs, so a sum double counts.
- Recommendations: only from fixed templates (`RECOMMENDATIONS` in
  `render.py`), each conditional, each naming a narrower alternative, listed in
  stage then document order. A finding with no template gets none. One per file
  and template: a block of matching lines is one change. A permission-flag hit
  that edits a settings allow-list (`permissions.allow`, `allowedTools`,
  `settings.json`) gets its own template, not the skip-permissions one (2026-09-29,
  Case 003).
- Pair points (stages 2 and 3) list only lines the model reads (stage 4 audience
  `model` or `subagent`); pairs in scripts (`tool`) and human-facing files are
  counted, not listed. Stage 4 points list model, subagent, and tool lines (a
  zero-base-rate pattern in code is a capability locator) and count human-facing
  ones.

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
`do` reads as points of attention (p >= 0.9 since 2026-10-01; 0.7 to 0.9 counted as
near the line). Answers never change sections 1 to 5.

## The summary as HTML, and re-rendering (2026-09-30)

The owner found `summary.md` busy and hard to read. Stage 8 also writes
`summary.html` (`summary_html.py`): the same facts in plain language, what to
look at first as grouped cards (stage 4 headlines say what matched, never what the
author meant), one plain sentence per stage with the technical line behind a
disclosure, light and dark themes. `summary.md` stays for text tools.

`run.py --rerender <run_dir>` rebuilds the reports from a finished run's saved stage
outputs, runs no stage and calls no model (only the grader, for stamps), and appends
a line to LOG.md. Report design changes no longer need a full re-run.
