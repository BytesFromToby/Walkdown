# details_html.py: spec

Status: rebuilt 2026-10-27 as report v3 (owner; `glance.SPEC.md` holds the eight questions).
Before: the long page of report v2 (2026-10-16), renamed from `summary.html` on 2026-10-20, with a
Not concerned box on every row.

The page for someone who wants everything behind the summary: the same eight questions, each
opening with the same chip and answer, then every table, chart, and place, long lists folded. It
also holds the place list every other output reads (`first_items`) and the helpers for marks and
licenses.

## Inputs

`render_page(meta, reports, stamps, notes, runs_ok, changes=None, marks=None) -> str`. `changes`:
`run.changes_for`; `marks`: the run's marks (`marks.for_run`), read only to say how many places
are marked.

## Output: `details.html`

1. **Header.** "<name> in detail"; the meta line (`glance.meta_line`) and a link back to the
   summary; the license line (`license_line`): the license of each license file at the top level
   (or in `.claude-plugin/`) with the file, or that the file is not one Walkdown recognizes and how
   it begins; with no such file, what the top-level license fields say; with neither, "No license
   found"; then "Also stated:" any other license, and how many other license files are not
   recognized. Test data left out; a run made before the license check (no `license_checked` on
   `inv.pin`) shows no line. It names the license a file matches, never what the license allows.
   Then what it is, and that long lists are folded.
2. **The jump bar** (`TOC`): Switching on, Memory, Package, Other computers, Other AI tools, Tools,
   Finished, Careful, Not checked.
3. **The eight questions** as sections (`glance.section`): question, chip, answer, bullets, the
   summary's "More", then the detail (`glance.SPEC.md`).
4. **What changed since run X**, only when an earlier run of the same repository is a different
   version, or the same version and something differs (`run.changes_for`, `drift.since`; review
   C22 b): the drift lines and a link to `changes.md`.
5. **What Walkdown didn't check** (`glance.not_checked`): a step that did not work, the model reads
   when they did not run, or that every step ran and passed; then every limit of the run, folded
   (`render.limits`, which names INCOMPLETE stamps and skipped checks).
6. **Footer**: a link to `review.html` to mark each place, `full.md`, and `render.NOT_WHAT`.

No Not concerned boxes and no marks bar (owner, 2026-10-27): marking is on `review.html` only.

## Helpers other outputs read

- `first_items`, `unique`, `grouped`: the places, read by `review.html`, `summary.html`, `glance`,
  and the brief in `walkdown.py`; stage 4 phrase places are `render.point_hits` (C39). `_item` notes
  what a quote's hidden tag characters spell and what a base64 stretch decodes to (C42). A line
  that forbids the matched action keeps its place with ", stated as a prohibition"; a forbidden
  rubric action is never one "with no confirmation step" (C25). A read-only line whose owner's tools
  list can write is its own place (C32); a confident model read that a flagged line is not an
  instruction adds `questioned` (C28). A command in `.cursor/environment.json` notes that it runs
  on Cursor's cloud machine (`HOOK_NOTES`, C31).
- `action_group`: runs, out, lasting, or words (C29), for the concern rows.
- `mark_rows`: every row a mark can name (each review card, each outside link, each Worth a look
  file, each place under a trifecta box, each hidden place), read by `review.html`, so a marks file
  saved before report v3 keeps its marks.
- `license_line`, `file_concerns`, `fold_meaning`, `fold_kinds` (typography never counted),
  `_divergences`, `_leg_ev`, `_ev_words`, `_allows`, `link_rows`, `CARRIER_PLAIN`, `GROUP_PLAIN`,
  `READ_BY`, `TRIFECTA_LEDE`, `PLAIN_STAGE`: read by `glance`.

## Must never

- Show a score, severity, rank, or verdict.
- Emit unescaped repository text (addresses included).
- Show a secret's value, or open, fetch, or check a link.
- Write `marks.json`.

## Done when (tests in `tests/test_details_html.py`)

1. Sections in order with the jump bar, title, back link, footer, theme tokens
   (`test_order_title_toc_and_theme_tokens`); no mark boxes, the marked count
   (`test_no_mark_boxes_marking_is_on_review_only`).
2. Repository text escaped; no verdict words (`test_text_is_escaped`, `test_no_verdict_words`).
3. Every place by kind, linked to its review card and quoted
   (`test_every_place_by_kind_linked_to_its_review_card_and_quoted`); hidden text, other languages,
   folded lines with typography left out (`test_hidden_text_counts_and_empty_state`,
   `test_hidden_text_counts_other_language_passages`, `test_fold_line_counts_only_what_can_change_meaning`);
   secrets (`test_secrets_never_values_test_data_set_aside_and_empty_states`); links
   (`test_web_addresses_table`); risky wording (`test_risky_wording_counts_and_groups`).
4. The review items kept: C25 (`test_prohibitions_are_said_and_never_called_unconfirmed`), C31
   (`test_cursor_setup_commands_say_where_they_run`), C28
   (`test_a_model_read_that_questions_a_finding_is_shown_with_it`), C32
   (`test_contradicted_read_only_lines_get_their_own_place`), C29 (`test_action_groups`), C42
   (`test_items_say_what_hidden_text_spells`).
5. The license line and the summary's short license (`test_license_line_in_header`,
   `test_license_line_unrecognized_field_none_and_old_run`).
6. Changes only when they apply (`test_changes_only_when_relevant`); What Walkdown didn't check last
   (`test_not_checked_last_with_every_limit`).
7. Each question's detail (`test_question_sections_carry_everything_behind_them`); files worth a
   look and the trifecta credit (`test_files_worth_a_look_and_the_trifecta_credit`).

## History

- 2026-10-07: HTML summary page (report v1, now at tag `report-v1`).
- 2026-10-12: review page link; trifecta legs checked first, colored by position (owner).
- 2026-10-16: report v2 in the owner's order (title, trifecta, files, outside links, hidden text,
  secrets, risky asks, changes, recommendations, other details); prohibitions (C25).
- 2026-10-17: license line (class demo feedback); "capability only" (C27).
- 2026-10-19: same-version changes when Walkdown changed (C22 b).
- 2026-10-20: "Can" names (C31 part B); contradicted read-only places (C32); questioning reads
  (C28); First pass and Questions before use (C29); line endings are not edits (drift).
- 2026-10-20: trifecta columns with linked place lists, General risks replaces "How it gets in";
  hidden text reworked, typography left out (owner). Renamed to `details.html`, Not concerned on
  every row, First pass and Questions before use moved to `summary.html` (owner; built the same
  day).
- 2026-10-21 to 2026-10-27: slices 1 to 6 added a section each (trigger, ship, elsewhere, ready, fit,
  clean); review C42 notes (2026-10-25).
- 2026-10-27 (owner, report v3): rebuilt as the eight questions with everything behind them
  (`glance.py`); no Not concerned boxes, marks bar, or page script for marks (marking on
  `review.html` only). Not carried to the new page: Recommendations, the trifecta's place lists,
  Files and map stats, and the model reads' agreement counts (all still in `full.md`), and Questions
  before use (dropped; the facts behind it are in questions 6 and 8).
