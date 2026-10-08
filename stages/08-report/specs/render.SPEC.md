# render.py: spec

Pure functions that turn stage reports into the run's documents. Nothing is
detected or judged; every rule that picks what to show is a fixed table at the
top of the file (`SUBGROUPS`, `POINT_PATTERNS`, `LEG_NAMES`, `STANDING_LIMITS`,
the recommendation templates).

## Inputs

- `meta`: `repo`, `run`, `date`, `source`, `hash`, `hash_kind`, optional
  `tool`, `channel`, `finished`, `feedback`.
- `reports`: `{stage: contract-1 report}` for the stages that ran.
- `stamps`: `{stage: validate.Stamp}`.
- `notes`: `{stage: [stderr lines]}`.
- `runs_ok`: the set of stages that completed.
- `capability_full`: stage 5's `capability.json` (full evidence), optional.

## Outputs

- `summary(...)`: the summary page (REPORTING Part A). One status line per
  stage 1 to 7 in stage order, plain-language headings, points of attention
  under the stage that found them (at most `MAX_POINTS`, then "+N more"),
  the recommendation count, and the "What this is not" paragraph.
  - Stage 4's line carries hit counts by sub-group and "benign share not
    measured".
  - Stage 5's line states each leg yes / no; when all three are yes it adds the
    fixed qualifier `TRIFECTA_ALL`. The trifecta is described in plain words; the term "lethal
    trifecta" appears in the docs with its credit, not in the report (2026-10-07). Bytes at load are listed per path, never
    summed across hook configs.
  - A stage whose stamp is not PASS adds "Validation <result>: see 7.".
  - A stage that did not run shows "Not run. See 7.".
  - Stage 6 shows "Not built."
- `full(...)`: sections 1 to 7, each with status line, validation stamp, and
  every finding (file:line, fields, verbatim quote in a code span), then
  Recommendations, then "What this is not".
- `recommendations(reports)`: template matches only, in stage then document
  order; each conditional ("If ...") and naming a narrower alternative; one per
  file and template; settings allow-list edits get their own template.
- `limits(...)` / `limits_doc(...)`: stage 7: failed or unvalidated stages,
  skip findings, stage notes naming a limit, unread and unscanned files, then
  `STANDING_LIMITS`.
- `glance(...)` -> `(skipped, not needed)` (added 2026-10-07; the owner read "58 things not
  examined" as a hole): the summary's count. One plain item per check this run skipped that
  applies to this repository: a stage that did not run, model reads (one item, not one per
  file), a missing optional tool whose file kind stage 1 saw (`TOOL_NOTES`, `file_kinds`;
  language detection applies to every run), other skip reasons grouped with a file count,
  unread and unscanned files. A tool for a file kind the repository does not ship goes to
  "not needed". Standing notes (`STANDING_NOTE`) and `STANDING_LIMITS` are not counted.
  `limits` is unchanged and still lists every line.
- Section 7 of `summary(...)` is `glance_line`: the skipped items by name, "Not needed here",
  any stage whose validation is not PASS, and the length of the full list.
- `log(...)`: LOG.md per RUN-LAYOUT: one row per stage with start, finish,
  output, finding count, and validation stamp; 06 as not built.
- `code(s)`: an inline code span that survives backticks inside `s`.

## Signal levels (added 2026-10-01, soft D1)

- Each stage 4 summary point names its patterns with their base rate over the other
  audited repos (`rates_note`, from `baserates.json`): "L.ignore, rare: in 0 of 3 other
  audited repos". No table: the pattern is just named.
- Stage 6 "do" reads use a band around the 0.8 cutoff, `DRIFT` = 0.1 (measured: 95% of
  repeat Jev reads of one line within 0.09): p >= 0.9 is listed as a real-instruction
  read (up to the point cap); 0.7 <= p < 0.9 is one counted "near the line" line with the
  drift stated, and each such read is tagged ", near the line" in the full report; below
  0.7 is counted, in the full report.

## Evidence read as not an instruction (added 2026-10-01, soft D5)

A stage 6 label other than `do` at p(label) >= `NOT_DO_P` (0.8) on a line that stage 5
cites as stage 4 evidence marks that entry in the full report ("stage 6: read as
description, not an instruction; jev p=0.85") and counts it beside the leg. The leg's
yes/no never changes. When a present leg's whole evidence list (not truncated:
`evidence_total` equals the listed count) is marked, the summary says so under the
trifecta line. Stage 1 evidence (grants, hooks) is never marked.

## Sweep (added 2026-10-01, soft D2)

Sweep band (2026-10-01): measured drift of p_any between repeat sweeps is up to 0.10, so
`SWEEP_DRIFT` = 0.1 around the stage 6 cutoff 0.5. The report lists a passage at p_any >=
0.6; 0.4 to 0.6 is near the line, flagged or not, counted in the summary and tagged
", near the line" in the full report. A passage whose top answer is `none` is named by its
likeliest listed kind (`sweep_kind`). Listed sweep passages with no stage 4 hit lead the
stage 6 points, strongest first:
"<file>:<line>-<end>: no stage 4 pattern here; jev reads this passage as telling the reader
to <plain kind> (p=..)". Flagged passages stage 4 already covers are one counted line. The
status line adds "Sweep: ..: N passages read, F flagged, U with no stage 4 hit". The full
report lists every flagged passage with its kind, p, and coverage.

## Test data (added 2026-10-02)

Hits, hooks, and pairs in test data are counted in the summary ("N more ... in test data"),
never listed as points. Section 5's status adds "Test data set aside: N findings ...", the
`testdata+loaded` pairs lead the stage 5 points and have their own list in the full report,
and section 7 states that test data is recognized by name.

## Must never

- Emit a score, severity, rank, or verdict word (benign, concerning, safe,
  malicious, risk score).
- Sum SessionStart hook bytes across host configs.
- Show a non-PASS stage without saying so.

## Done when (each backed by a test in `tests/test_render.py`)

1. A small report set gives a summary with seven numbered stage lines in order,
   each heading from `HEADINGS`.
2. All three legs present adds the trifecta qualifier; two of three does not.
3. An INCOMPLETE stamp puts "Validation INCOMPLETE: see 7." on that stage's line
   and the stage into `limits`.
4. A hit on a `POINT_PATTERNS` pattern appears as a point under stage 4; a hit
   on another pattern does not.
5. Two hook configs' `cap.load-bytes` (one per host, from stage 5) are listed
   separately and not summed.
6. `recommendations` gives one line for a SessionStart hook and one for a
   fetch-and-follow hit, each starting with the location and containing "If".
7. `full` contains every stage 4 finding's location and quote.
8. `code` wraps text containing a backtick so the span is not broken.
9. No document contains the words "verdict: ", "score", "severity", "benign:",
   or "malicious".
10. Hidden-text pairs on human-audience lines (stage 4 `audience`) are counted
   under stage 2, not listed; model-audience ones are listed.
11. `dynamic+phrase` pairs are listed under stage 3 beside `orphan+phrase`.
12. Allow-list edits (`permissions.allow`) in one file give one recommendation
   with the settings template; a skip-permissions flag gives the other template.
13. Orphan pairs on human-audience lines are counted under stage 3, not listed.
14. A `hook+phrase` pair is a stage 5 point and gets the "If this message is meant
   for the user" recommendation.
15. Stage 6: status line names each backend (local or remote, model), label counts,
   agreement, relational answers and skips; points list relational reads and `do`
   reads at p >= `DO_POINT_P` (0.8, provisional), counting weaker ones; the full
   report lists every question with each answer or skip.

## Benign share (added 2026-10-03, review C15)

`benign_share(r)`: when stage 6 labeled lines, section 4's status line ends with "of N lines a
model reads, <backend> labels X as an instruction to do the matched action and Y as something
else (... by label)", pointing to the measured accuracy; otherwise "benign share not measured
(stage 6 labels did not run)". Section 4's line count is split by audience (read by a model,
in scripts, human-facing, test data; review A5).
5. `glance` counts a missing tool only when the repository has that file kind, never counts a
   standing note, and folds model-read skips into one item (`tests/test_summary_html.py`).
