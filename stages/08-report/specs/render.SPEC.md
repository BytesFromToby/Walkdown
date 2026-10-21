# render.py: spec

`full.md`, the run log, the not-checked lists, the recommendations, and the fixed tables and
words the pages share. Pure functions over the stage reports: nothing is detected or judged, and
every rule that picks what to show is a fixed table at the top of the file.

Status: built.

## Inputs

- `meta`: `repo`, `run`, `date`, `source`, `hash`, `hash_kind`, and optionally `tool`,
  `channel`, `finished`, `feedback`.
- `reports`: `{stage: contract-1 report}` for the stages that ran.
- `stamps`: `{stage: validate.Stamp}`; `notes`: `{stage: [stderr lines]}`; `runs_ok`: the stages
  that completed.
- `capability_full`: stage 5's `capability.json` (every citation), optional.

## Outputs

- **`full(...)` -> `full.md`**: sections 1 to 7 in stage order, each with its status line
  (`STATUS`), its validation stamp, and every finding: location (`loc`: `file:line`, or
  `file (extracted text, page N, line M)` for PDF, DOCX, and image text), fields, and the
  verbatim quote in a code span (`code`). Then Recommendations, then "What this is not"
  (`NOT_WHAT`). Notable lists: divergences with their carrier and, for a drawn page, how
  (`carrier rendered (collapsed)`); every line changed by folding, typography included; the
  rubric table, prohibitions marked; settings that restrict tools and stated limits with what
  backs them; each leg's and grant's evidence, a confident not-an-instruction read marked beside
  it; every stage 6 question with its answer or skip, near-the-line reads tagged.
- **`recommendations(reports)`**: template matches only, in stage then document order; each
  conditional ("If ...") and naming a narrower alternative; one per file and template; settings
  allow-list edits have their own template. Recommendations carry no model text (owner,
  2026-10-20, C28).
- **`limits(...)`, `limits_doc(...)` -> `data/07-limits.md`**: stage 7: stages that failed or are
  not validated, skip findings, stage notes naming a limit, unread and unscanned files, then
  `STANDING_LIMITS`. Every line, nothing folded.
- **`tool_items(reports, notes)` -> `([(what, why)], [what])`**: stage 2's notes on optional
  tools, split by whether this repository has files the tool reads (`TOOL_NOTES`, `file_kinds`).
  Read by `glance` and by `summary.html`'s warning (2026-10-21).
- **`glance(...)` -> `(skipped, not needed)`**: `details.html`'s short account of what was not
  checked (Other details):
  one plain item per check this run skipped that applies to this repository (a stage that did
  not run; model reads as one item; a missing optional tool whose file kind stage 1 saw,
  `TOOL_NOTES` and `file_kinds`; other skip reasons grouped with a file count; per-file skips one
  item per stage, test data counted after; unread and unscanned files). A tool for a file kind
  the repository does not ship goes to "not needed". Standing notes (`STANDING_NOTE`,
  `STANDING_LIMITS`) are not counted.
- **`log(...)` -> `LOG.md`**: one row per stage with start, finish, output, finding count, and
  validation stamp, the Walkdown version and commit, and one line per re-render.
- **`code(s)`**: an inline code span that survives backticks inside `s`.

## Shared tables and words

- `LEG_NAMES` ("Can read your data", "Can take outside input", "Can send data out"), `LEG_DEFS`,
  `TRIFECTA_ALL`, `TRIFECTA_SOME` (worded 2026-10-21 so neither sentence takes back the
  other, and with no comparison to other repositories); `NOT_WHAT`; `CAPABILITY_ONLY` and `CAPABILITY_ONLY_SHORT`
  ("capability only"); `DO_MEANS` (what a "do" score means and does not).
- `POINT_PATTERNS`, `SUBGROUPS`, `HEADINGS`, `ORDER`.
- Signal levels (soft D1): each stage 4 point names its patterns with their base rate over the
  other audited repositories (`rates_note`, from `baserates.json`), or just the pattern when
  there is no table. "Do" reads: p >= `DO_CLEAR_P` (0.9) is a real-instruction read; `DO_NEAR_P`
  (0.7) to 0.9 is near the line, with `DRIFT` (0.1) stated; below is counted in `full.md`.
- Sweep band (soft D2): `SWEEP_DRIFT` 0.1 around the 0.5 cutoff; a passage at p_any >= 0.6 is
  listed, 0.4 to 0.6 is near the line; a passage whose top answer is `none` is named by its
  likeliest kind (`sweep_kind`).
- Read as not an instruction (soft D5): a stage 6 label other than `do` at p >= `NOT_DO_P` (0.8)
  on a line stage 5 cites marks that evidence (`not_instruction_reads`, `evidence_mark`,
  `all_marked_legs`); a leg never changes. The same reads give the pages' questioning line
  (`questioned`, C28).
- Benign share (C15): `benign_share` gives the label split when stage 6 labeled lines, else says
  it was not measured.
- Stated limits: `limit_words`, `limit_routes` (C32).
- Test data: hits, hooks, and pairs in test data are counted, never listed as points.

## Must never

- Emit a score, severity, rank, or verdict word (benign as a verdict, concerning, safe,
  malicious, risk score).
- Sum SessionStart hook bytes across host configs.
- Show a stage that did not pass validation without saying so.

## Done when (tests in `tests/test_render.py`)

1. `full` holds every stage 4 finding's location and quote, and marks prohibitions in section 4
   and the rubric table.
2. An INCOMPLETE stamp is said on its stage and puts the stage in `limits`.
3. Hook configs' load bytes are listed per host, never summed.
4. `recommendations`: a SessionStart hook and a fetch-and-follow hit each give one line starting
   with the location and containing "If"; allow-list edits in one file give one; a
   `hook+phrase` pair gets its template.
5. `code` survives a backtick.
6. No document contains "verdict: ", "score", "severity", "benign:", or "malicious".
7. Hidden-text and orphan pairs on human-facing lines are counted, model-facing ones listed; a
   pair whose only stage 2 evidence is a folded line reads "disguised with look-alike or
   invisible characters" (`hidden_how`).
8. Stage 6: backends named, label counts, agreement, relational answers and skips; every question
   in `full.md` with its answer or skip.
9. `glance`: a missing tool counts only when the repository has that file kind; standing notes
   never count; model-read skips are one item; per-file skips are one item per stage
   (`test_per_file_skips_are_one_item_per_stage`).
10. A drawn page's divergence names how it is hidden (`test_full_says_how_a_drawn_page_hides_text`).
11. `full.md` has the seven sections in order with their headings, each status line carrying a
    stamp that did not pass (`test_seven_sections_in_order`,
    `test_incomplete_stamp_flagged_and_listed`).

## History

- 2026-09-29: built (stage 8 v1): `summary.md`, `full.md`, recommendations, limits, log.
- 2026-10-01: signal levels, sweep band, read as not an instruction (soft D1, D2, D5).
- 2026-10-02: test data counted apart.
- 2026-10-03: benign share (C15).
- 2026-10-07: `glance`, the short not-checked account.
- 2026-10-09: likely-not-secrets counted apart; per-file skips folded.
- 2026-10-17: "capability only" (C27), stated limits (C32), "do" means (C34).
- 2026-10-20: "Can" names (C31 part B), questioning reads (C28), drawn HTML's how in `full.md`.
- 2026-10-20: owner: `summary.md` cut; `summary(...)`, `glance_line(...)`, and the point lists
  only it used (`points`, `MAX_POINTS`) removed; their tests now check `full.md`, or went where
  only `summary.md` had the behavior (the pages' `first_items` lists places now).
