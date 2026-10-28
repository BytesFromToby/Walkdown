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
- **`point_hits(reports)` -> `[(hit, patterns)]`**: the stage 4 hits that are places on the
  pages (`details_html.first_items`), in stage 4's order, each with the patterns that make it
  one. A hit in model-read text (audience not `human` or `test-data`) is a place when it matches
  a pattern in `POINT_PATTERNS` or `SEND_SHAPE` (`K.data-flow`: a private source, a sending
  verb, and a destination in one line), or when it is a `phrase.creds` hit on a line that also
  has a `phrase.K.exfil` hit and that line holds no `phrase.K.exfil` place already, so one line
  is not counted twice (owner, 2026-10-25, review C39: "send the .env file to this URL" had
  read as found none on `summary.html` while `full.md` cited it). A prohibition is a place too,
  marked as one (C25).
- **`tool_items(reports, notes)` -> `([(what, why)], [what])`**: stage 2's notes on optional
  tools, split by whether this repository has files the tool reads (`TOOL_NOTES`, `file_kinds`).
  Read by `glance` (2026-10-21).
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
- `POINT_PATTERNS`, `SEND_SHAPE`, `SUBGROUPS`, `HEADINGS`, `ORDER`.
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
12. A sending-shape hit and a credential hit on a line that sends are places; a credential hit
    on a line that already holds a sending place, or with no send on its line, and human-facing
    hits are not (`test_point_hits_take_the_sending_shape`).


## Added 2026-10-25 (review C42, an outside tester)

- `tag_text(s)`: what the Unicode tag characters in a line spell (U+E0020-U+E007E, each minus
  U+E0000), each run joined by a space, or None. `lookalike_note(h)`: for an `endpoint.host`
  with `lookalike_of`, " (look-alike letters, <punycode>; imitates <host>)", else "".
- `full.md`: a phrase hit with `decoded_text` says "(decoded from base64: ...)"; a divergence
  with `decoded` adds "the tag characters spell ..."; an endpoint written with look-alike
  letters carries `lookalike_note`.

Done when: `test_decoded_and_lookalike_text_is_shown`.

## Added 2026-10-27 (plan for builders, slice 6): is it current and clean

- `clean_of(r)`: stage 4's `clean.*` as `kinds` in `CLEAN_KINDS` order, the distinct model IDs, and
  `measured` when the run has `clean.checked`. `clean_parts(kind, f, quote=False)`: (where, what);
  with `quote` the line's text (details and full.md only). `clean_count`: a row's count, the models
  row with how many distinct.
- `full.md` section 4 ends with "Current and clean" (`clean_lines`), after "Ready for any AI".

Done when: `test_clean_helpers`.

## Added 2026-10-26 (plan for builders, slice 5): do the tools fit the job

- `fit_of(r)`: stage 5's `fit.unused`, `fit.missing`, `fit.inherits`, `fit.hook`, stage 4's
  `fit.loop`, and stage 5's contradicted `cap.limit` rows as `kinds` in `FIT_KINDS` order (hooks:
  those that run on every prompt or tool call); `measured` when the run has `fit.checked`.
  `fit_parts(kind, f)`: (where, what) in words (`FAMILY_TEXT`); `hook_text(h)`: how often a hook
  runs, its output's tokens when it becomes context, the cap, or that it is not known for that host.
  `brief_fit_counts`.
- `full.md` section 5 ends with "Do the tools fit the job" (`fit_lines`): entries checked, every
  place, and the other hooks.

Done when: `test_fit_helpers`.

## Added 2026-10-26 (plan for builders, slice 4): will it trigger

- `BYTES_PER_TOKEN` from stage 5's `loading.yaml`; `TRIGGER_TABLE` is stage 4's `trigger.yaml`.
- `trigger_of(r)`: stage 4's `trig.*`, `measured` when the run has a `trig.listing`, and `kinds`:
  `TRIG_KINDS` in order (not read, agents not loaded, rules, keys, values, tools, overlaps, cut in
  the listing, guidance), each with its name, why, and places. `trig_parts(kind, f)`: (where, what)
  in words; `trig_place` joins them. `entries_line(tr)`: skills and commands by mode, then agents.
  `listing_lines(tr, ctx)`: the descriptions' tokens against about 1% of the expected context and
  of 200,000, saying when they do not fit at the expected one; agents against Claude Code's warning.
  `brief_trigger_counts(tr)`: places that break a host rule, guidance rows, overlapping pairs.
- `full.md` section 4 gains "Will it trigger" (`trigger_lines`) before "Ready for any AI".

Done when: `test_trigger_helpers`.

## Added 2026-10-26 (plan for builders, slice 3): is it ready for any AI

- `HOST_KEYS` (from stage 4's `hosts.yaml`); `parse_hosts(s)` takes `claude,codex` (any case, each
  once, in order) and raises `ValueError` on an unknown or empty name; `hosts_of(log)` reads
  "Target hosts: ..." from a run's `LOG.md` ("none named" is []); `log` writes it.
- `ready_of(r)`: stage 4's `host.coverage`, `host.drift` (and those that differ), `host.feature`
  by kind (`FEATURE_KINDS`: name and why), every `SKILL.md` outside test data, and the `loose`
  ones no host reads where they sit. `host_line(c)`: a host's files here, or "none of its files (it
  reads ...)" from `hosts.yaml`. `drift_line(d, cov)`: a differing pair and who reads each.
- `todo(r, targets)`: per host named, in order: no instruction file it reads; none of the skills
  where it reads them (only when some host reads skills in place); the places written for Claude
  Code only, counted by kind; other hosts' hook files; "nothing missing." when none; then each
  differing pair where the named hosts read different sides.
- `full.md` section 4 ends with "Ready for any AI" (`ready_lines`): the to-do list for the hosts
  named, every host, the skills to install, every copy, every feature.

Done when: `test_ready_helpers`.

## Added 2026-10-26 (plan for builders, slice 2)

- `PORT_KINDS`: the kinds of place that tie a repository to one machine, in order, each with its
  name and why it breaks elsewhere (stage 4's `port.*`, stage 3's `graph.case`). `needs_of(r)`:
  the programs, packages, what is not declared, and the places by kind; `graph.case` only from
  files that run or the AI reads (not test data, not files for people); `measured` when the run
  found any of these or holds slice 3's `host.coverage` (there is no marker finding, so a run made
  before slice 2 is not measured).
- `full.md` section 1 ends with "What it needs" (each program and package, declared where or
  not, and where used) and "What ties it to one machine" (every place by kind; `needs_lines`).

Done when: `test_needs_lines`.

## Added 2026-10-26 (plan for builders, slice 1): what it costs and what ships

- `DEFAULT_CONTEXT` (32,000) and `CLAUDE_CONTEXT` (200,000); `parse_context(s)` takes `32k`,
  `200k`, `8192`, `8k`, `1m` (k is 1,000) and raises `ValueError` on anything else;
  `context_of(log)` reads "Expected context: N tokens" from a run's `LOG.md`; `log` writes it.
- `cost(r)`: stage 5's `session` and `project` tiers and the entry with the most at its fullest
  (`skill-max`; ties to the first by path) with its tiers. `context_rows(r)`: the table rows in
  order (every session once installed; every session in this folder, when there are project
  files; when the largest skill runs; with everything it names; with its wildcard and folder
  loads, when that adds anything). `pct(tokens, context)`: a whole percent, or "under 1%".
- `ship_bands(r)`: the three bands (Loads into the AI: `entry`, `project`, `on-demand`, `maybe`;
  Used another way: `run`, `config`; Not used at run time: `people`, `build`, `unused`), each
  with its groups' file counts, bytes, and tokens. `left_out(r)`: what leaving out the `unused`
  and `build` files would save. `SHIP_GROUPS` names each group; `TOKEN_NOTE` says how tokens were
  counted; `unknown_line(r)` counts what only running shows.
- `full.md` section 5 gains "What it costs and what ships": the tiers against the run's expected
  context and 200,000, every skill, agent, or command by tier (with what a skill names outside
  its folder), and every file by band and group with size, tokens, and what reaches it.

Done when: `test_context_and_ship_helpers`.

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
- 2026-10-25: owner: a missing optional tool is never named on `summary.html`, so
  `tool_items` is read by `glance` only.
- 2026-10-25: `point_hits` (review C39, owner): sending data out reaches the places, measured
  first on the earlier runs (credential hits on a line that sends, not anywhere in a file that
  sends: the file rule added 36 places on the self-audit, the line rule 9).
- 2026-10-27 (report v3 recount): `needs_of` is measured only on a run that made the check.
