# compare_runs.py: spec

Says whether two run folders of the same input hold the same reports. The restructure rule is that
a move gives the same reports: baseline runs were made before it, the same inputs are run again
after each step, and this tool compares the two. A pure move must show no difference; a step that
cuts something must show only the differences it announced before it started. Python standard
library only. Brief: `pre-planning/restructure/STEP-00-compare.md`.

## Inputs

```
python tools/compare_runs.py <old run folder> <new run folder>
       [--map map.json] [--expect expect.json] [--brief-old FILE --brief-new FILE] [--show-text]
```

- Two run folders (`RepoResults/<repo>/<date>_<hash7>`). A run folder has `LOG.md` and `data/`
  (the layout since 2026-10-02); anything else is a usage error.
- `--map`: what a step renamed. Two shapes, anything else is a usage error:

  ```
  {"names": {"04-phrases": "02.4-phrases"},
   "paths": {"stages/04-phrases": "stages/02-coded/02.4-phrases"},
   "files": {"data/06-packet.md": "data/03-packet.md"}}
  ```

  or the flat `{"04-phrases": "02.4-phrases"}`, which means `names` only. Every section is optional,
  every entry is old to new, and two old entries may not go to one new one. The map is applied to
  the OLD run, so that old maps onto new:
  - `names`: the old run's stage file names, the `stage` key inside them, the top-level `stage` key
    of `data/capability.json` (nothing else in a JSON file is mapped), the stage notes files
    (`data/<stage>.notes.txt`), and LOG.md stage rows; and inside every compared text (pages,
    LOG.md, `07-limits.md`, the old soft step's packet, notes files, the brief) as a whole token:
    `04-phrases` matches in `(04-phrases)` and `stages/04-phrases/x`, not in `104-phrases` or
    `04-phrases2`.
  - `paths`: literal replacements inside the same compared texts, tried before names and longest
    first, so `stages/04-phrases` becomes `stages/02-coded/02.4-phrases` and not a path with only
    the stage name changed.
  - `files`: an old run file (a path from the run folder) paired with the new run's file of its
    new path, compared as one file, by the rules of the old path. A stage report moved to another
    stage report path (`data/NN-name.json`) is paired too, so its report keys are compared.
  - One pass over each text: a replacement is never replaced again, so a map that sends A to B and
    B to C does not send A to C, and a path whose new form holds an old name keeps it.
- `--expect`: what a step announced before it started. Every key is optional.

  ```
  {"checks_removed": [...], "checks_added": [...], "checks_changed": [...],
   "files_differ": [...], "validation_changed": [...], "report_keys_differ": [...],
   "note": "..."}
  ```

  Each difference is listed under its own kind, and a listing under another kind does not count:
  - `checks_removed`, `checks_added`, `checks_changed`: check ids, exact.
  - `files_differ`: files as the report names them (`summary.html`, `LOG.md`, `data/graph.json`,
    `data/04-phrases.notes.txt`, `data/normalized/text/x.md`, `marks.json`, `brief`,
    `data/02.1-inventory.json` for a stage file with no counterpart). `LOG.md` covers the lines
    outside the stage rows, never a stage row or its validation result. A top-level file is named
    exactly. A `*` is allowed only after a literal folder and stands for part of one path segment
    (`data/*.notes.txt`, `data/normalized/text/*`; it stops at a `/`). A `**` is allowed only as
    the whole last segment after a literal folder (`data/normalized/**`), and covers everything
    below it. No pattern covers a stage report file (`data/<stage>.json`, any stage in either run
    or in the map) or a file that has a rule of its own (`data/graph.json`, `hits.json`,
    `capability.json`, `packet.json`, `answers.jsonl`, `06-packet.md`, `07-limits.md`, `limits.md`): those are
    announced by name, so a stage split names its one-sided stage files.
  - `validation_changed`: exact stage names of LOG.md rows, after `--map` (`04-phrases`). A
    validation result that changed, and a stage row that is missing from one LOG.md (its stamp is
    gone), are both announced here. No `*`.
  - `report_keys_differ`: `<stage>:<key>` for a key of a stage report other than `findings`
    (`02-reader:coverage`, `04-phrases:terms`, `04-phrases:stage`), and `<stage>:terms.code`. A `*`
    is allowed only as the whole stage part (`*:terms.code`); the key is exact.
  - Any other `*` or `**` is a usage error. A `*.*` or a `*-*` would cover differences of other kinds.
- `--brief-old`, `--brief-new`: the briefs `walkdown.py` printed (at v0.3.1 it does not save them).
  Both or neither. Line endings are read as `\n`, and a UTF-16 file (a shell redirect) is read.
- `--show-text`: also print the differing text, for repositories that are the owner's own.

## What is compared

Every file in both run folders is accounted for. A file in one run only is a difference. A file
the tool has no rule for is compared byte for byte.

1. **Findings.** Every finding in every stage report `data/NN-name.json`, pooled across the stage
   files and grouped by `check`. Within a check, a multiset of each finding as canonical JSON
   (sorted keys; `0`, `0.0`, `false`, and `"0"` are different), so order never matters. A check is
   *removed* (none left in the new run), *added* (none in the old), or *changed* (both have some and
   the multisets differ). What is left on each side is paired by `file` and `line`, best match
   first, so a changed finding shows the names of the fields that differ; the rest are removed or
   added. The report says, for information, which stage file holds each check in the old run (after
   `--map`) and in the new; a finding that moved to another stage file is the same finding. A stage
   file with no counterpart after the map, or one that cannot be read as a stage report, is a
   difference; one with no counterpart says that its report keys were not compared, so a change
   in them cannot hide behind a missing pair.
2. **The other keys of each stage report** (`stage`, `contract`, `coverage` in each step from 02 to 04-pinpoint since
   M9 slice C, `reading` in 02, `terms` in 04,
   `backends` in 06, any other), each as canonical JSON, for a stage file in both runs. `stage` is
   compared after `--map`. `terms.code` is a hash of the `02.4-phrases` code files and changes when the
   code moves, so it is an item of its own (`<stage>:terms.code`) that `--expect` can announce; the
   rest of `terms` (`version`, `count`, `rows`, `vocab`) is compared as the key `terms`. A value is
   never printed, only that the key differs and how many values.
3. **Every other file, by its path from the run folder:**
   - `data/graph.json`, `hits.json`, `capability.json`, `packet.json`: as canonical JSON. In
     `capability.json` the top-level `stage` is compared after the map's names; nothing else in
     any of them is mapped.
   - `data/answers.jsonl`: each line as canonical JSON.
   - `data/06-packet.md`: text, with names and dates taken out (it says `Written: <run date>`).
   - `data/07-limits.md` and `data/limits.md` (its name since M9 slice B): text, with names taken out.
   - `data/<stage>.notes.txt`: text, with names taken out (a stage's own messages).
   - every file under `data/normalized/`: `.json` as canonical JSON, `.jsonl` by line, any other as
     text exactly as it is.
   - anything else (`marks.json`, a stray file): byte for byte.
   A file the map's `files` moved keeps the rules of its old path (the packet stays the packet).
   The stage reports and LOG.md are compared by 1, 2, and 4; the pages by 5.
4. **LOG.md.** Each stage row, keyed by stage name after `--map`: it must exist in both runs and
   its validation result must match. The finding count and output columns of a row are not
   compared (the findings are, by check). Every other line is compared in order.
5. **Pages:** `summary.html`, `details.html`, `review.html`, `full.md`, and `changes.md`. A page in
   only one run is a difference.
6. **The brief,** when both are given.

JSON that cannot be parsed is compared as text. Text is read with every byte kept: bytes that are
not UTF-8 stay in the comparison as lone surrogates, so files that differ only in such bytes still
differ (the output shows them as `?`).

## What is taken out first

Only these, measured from two identical runs (Appendix A of the brief), and then the map. Nothing
else is ignored. Each run's own names are used: its folder name, and the folder it is filed under.

| What | Where | Becomes |
|---|---|---|
| Run folder name `<YYYY-MM-DD>_<hash7>`, optional `-N` | text files and the brief | `<RUN>` |
| The folder the run is filed under | the same | `<REPO>` |
| Absolute path to the run folder (given or a path ending in `<REPO>/<RUN>`) | the same | `<RUNDIR>` |
| Times `YYYY-MM-DDTHH:MM:SS+00:00` | LOG.md | `<TIME>` |
| The note `; measured YYYY-MM-DD, same code and fixtures` after a stamp | the same | removed |
| ISO dates, dates like `28 October 2026`, `Walkdown <version> (<commit>)` with optional `+modified` | LOG.md, the pages, `06-packet.md`, the brief | `<DATE>`, `<VERSION>` |
| The brief's `Changes since <run>` lines (the line, the lines indented under it, the blank line before it) and the blank lines at the end | the brief | removed |
| The map's `names` and `paths`, in the old run's text only | the text files named above and the brief (not JSON, not `normalized/`) | the new names and paths |

The text files `07-limits.md` and `data/*.notes.txt` get the first three rows, the cache note,
and the map. JSON files, findings, stage report keys, and everything under `normalized/` get none
of it: they are compared as they are (`normalized/` holds the audited repository's text, which a
step does not rename). Dates and versions are taken out of a page wherever they appear, including
inside text the page quotes from the repository; the finding it quotes is compared as it is, so a
change in the repository's text still shows there. Line numbers in the output count the lines after
this step. Compare like with like: the brief's `Changes since` lines are set aside, so a first
run's brief and a second run's brief compare, but the runs in a pair should be a first with a first.
Two files with the same bytes are not the same file once the map changes the old one's text.

## Outputs

Markdown on stdout. The first line is `SAME` (no difference at all) or
`DIFFERENT: <n> unexpected, <m> expected`. Then one section for each area: Findings (a table of
every check with old and new counts, the stage file that holds it in each run, and its status; then
the differences, which include the stage report keys), Files (every file except the stage reports,
LOG.md, and the pages), LOG.md, Pages, Brief (when given), and Announced (when `--expect` is given:
its note, and anything announced that was not seen; that is information, not a difference). A
difference counts once: a check, a stage report key, a file, a stage's LOG.md row (missing on one
side) or validation result, or a group of lines outside the stage rows. A difference is *expected*
when `--expect` lists it under its kind, otherwise *UNEXPECTED*.

Without `--show-text` the output holds no text from the audited repository:

- a finding difference is shown by check, `file`, `line`, and the names of the fields that differ;
- a page, brief, LOG.md, or text-file difference by line numbers and counts of lines;
- a JSON file's or a stage report key's difference by the count of values that differ, never by key
  or value (a key can be repository text); a file compared byte for byte by its two sizes;
- file names, check ids, stage names, stage report key names, and LOG.md validation results
  (Walkdown's own words).

At most 20 detail lines are printed for a check; the counts stay whole.

Exit code: 0 when no difference is unexpected, 1 when one is, 2 on a usage error (a folder that is
not a run folder, a file named on the command line that is missing or not usable, a map that is
not one of the two shapes, a file in a run that cannot be read, only one brief, a `*` in
`--expect` where it is not allowed). Usage errors print `error: ...` on stderr and nothing on
stdout.

## Filing the runs

Every file in a run folder counts, so a run folder is left as the run made it.

- Comparison runs are filed as `cmp-<name>` (`python walkdown.py <input> --name cmp-<name>`), never
  under the input folder's own name. The tool replaces the name a run is filed under, and the input's
  folder carries the same name in its path, so that replacement would hide a change to the input
  path and give false differences.
- Nothing else is saved into a `base-*` baseline folder (`marks.json`, `Thumbs.db`, a note): it would
  be a file in one run only.

## Must never

- Write anything inside either run folder, or anywhere else.
- Read `Fixtures/ANSWERS/`, or open files under `ReposToExamine/`. It reads only the two run
  folders and the files named on the command line; paths to the audited input are text it never
  opens.
- Print text from an audited repository without `--show-text`.
- Treat a file that exists in one run and not the other as equal.
- Ignore anything the table above does not list.
- Let an announcement cover a difference of another kind (`LOG.md` never covers a validation
  result or a stage row; a stage file never covers its report keys), or let a `*` cover more than
  it names.

## Done when (each backed by a test)

1. Two runs of the same code on the same input compare as `SAME` and exit 0, whatever the table
   above lists differs between them: names, folder paths, times, cache notes, dates (the old soft step's
   packet's `Written:` line too), versions, briefs of a first and a second run
   (`tests/test_compare_runs.py`: `test_identical_runs_are_same`,
   `test_each_listed_thing_is_normalized`, `test_everything_listed_at_once_is_same`,
   `test_run_folder_path_in_a_page_is_normalized_in_any_slash_style`,
   `test_brief_first_run_and_second_run_each_compare_like_with_like`,
   `test_dates_are_taken_out_of_the_packet_but_not_the_limits`, `test_finding_order_never_matters`,
   `test_json_side_files_compare_as_parsed_json`, `test_json_key_order_and_whitespace_are_not_differences`,
   `test_a_stage_row_counts_only_by_its_validation_result`, `test_a_run_compared_with_itself_is_same`).
   The verifier repeats this on the baseline pairs.
2. Each of these is reported and exits 1: a finding removed, added, or a whole check removed or
   added (`test_finding_removed`, `test_whole_check_removed`,
   `test_finding_added_and_whole_check_added`, `test_repeated_findings_are_counted`); one field of a
   finding changed (`test_one_field_of_a_finding_changed`,
   `test_a_field_added_to_a_finding_is_a_change`); a value that changes type only, in a finding, a
   JSON file, a JSON line, or a normalized copy (`test_a_json_change_of_type_only_is_a_difference`,
   `test_a_finding_field_that_changes_type_only_is_a_difference`); a side file changed
   (`test_side_file_changed`, `test_jsonl_and_text_side_files`, `test_normalized_file_changed`); a
   page line changed (`test_page_line_changed`, `test_page_line_added_in_the_middle`); a stage's
   validation result changed (`test_validation_result_changed`, `test_validation_result_changed_alone`);
   a stage row missing from one LOG.md (`test_a_missing_log_row_counts_under_validation_changed`);
   a LOG.md line outside the stage rows (`test_log_lines_outside_the_stage_rows`); a brief line
   changed (`test_brief_line_changed`); any key of a stage report other than `findings`
   (`test_each_stage_report_key_outside_findings_is_compared`, `test_terms_code_is_an_item_of_its_own`);
   a file in one run only, whatever it is called or where it is
   (`test_file_in_one_run_only`, `test_a_stray_file_in_one_run_only_is_a_difference`,
   `test_changes_page_in_one_run_only`, `test_stage_file_in_one_run_only`,
   `test_a_stage_file_that_is_not_a_report_is_a_difference`); a file with no rule changed, even
   by a byte of whitespace (`test_a_file_with_no_rule_is_compared_byte_for_byte`); a notes file
   changed (`test_notes_files_are_text_with_names_normalized`); text that differs only in bytes that
   are not UTF-8 (`test_bytes_that_are_not_utf8_still_differ`). Nothing outside the table is
   ignored (`test_a_changed_pin_is_a_difference`,
   `test_dates_are_not_taken_out_of_json_findings_or_normalized_copies`,
   `test_a_version_in_a_finding_is_not_taken_out`).
3. Under `--map`, a check whose findings moved to a renamed stage file compares as the same, and
   so do its notes file and its `stage` key; without the map the stage file has no counterpart
   (`test_map_renamed_stage_file_compares_as_same`, `test_map_names_are_whole_names_and_do_not_chain`
   (a map with a value that is also a key), `test_map_also_renames_the_stage_key_and_the_notes_file`,
   `test_map_does_not_hide_a_finding_that_changed`,
   `test_a_check_moved_between_stage_files_is_the_same_finding`).
4. Map format 2: a run renamed as step 1 renames it (names, paths, and the packet's file) compares as
   `SAME` under the map and as different without it; the map reaches the text of every surface, so a
   new run that kept an old name in one place is found in that place and no other; names are whole
   tokens; paths go first and longest first; replacement never chains; a file the map moved keeps
   its rules; `capability.json`'s `stage` follows the names and nothing else in a JSON file does;
   a stage report the map pairs by file has its report keys compared, and one it does not pair says
   so; the flat map still means names only; a map of any other shape exits 2; and a map cannot
   hide an old name the new run still has (`test_step_1_map_makes_the_renamed_run_the_same`,
   `test_the_map_reaches_the_text_of_every_surface`, `test_map_names_are_whole_tokens_inside_text`,
   `test_map_paths_go_first_and_longest_first`, `test_map_replacement_in_text_never_chains`,
   `test_a_map_cannot_hide_a_name_the_new_run_failed_to_change`,
   `test_map_files_pair_a_moved_file_and_keep_its_own_rules`, `test_a_version_1_map_means_names_only`,
   `test_a_map_that_is_not_one_of_the_two_shapes_exits_2`,
   `test_capability_json_stage_is_compared_after_the_map_and_nothing_else_in_json_is`,
   `test_capability_json_with_the_same_bytes_still_differs_if_the_new_run_kept_the_old_stage`,
   `test_a_stage_report_file_the_map_pairs_by_file_has_its_report_keys_compared`,
   `test_a_renamed_stage_report_file_cannot_be_hidden_by_a_pattern`).
5. A difference listed in `--expect` under its kind is reported as expected and exits 0; an
   unlisted one still fails; a listing under the wrong kind does not count; `LOG.md` never covers
   a validation result or a missing stage row, which have their own name; `terms.code` is announced
   alone; a `*` that could cover more than was named is refused; an announcement not seen is
   listed and does not fail (`test_expected_removed_added_changed_checks`,
   `test_expected_files_differ_with_names_and_patterns`, `test_an_unlisted_difference_still_fails`,
   `test_a_listing_under_the_wrong_kind_does_not_count`,
   `test_announced_but_not_seen_is_listed_and_not_a_failure`,
   `test_announcing_log_md_does_not_cover_a_validation_change`,
   `test_a_validation_change_is_announced_by_its_own_name`,
   `test_a_report_key_difference_can_be_announced_by_name`, `test_terms_code_is_an_item_of_its_own`,
   `test_a_star_that_could_cover_more_than_was_named_is_refused`,
   `test_a_star_after_a_folder_or_in_place_of_a_stage_is_allowed`,
   `test_near_bare_patterns_cannot_hide_a_deleted_page_or_a_failed_validation`,
   `test_a_star_stops_at_a_slash`, `test_data_star_does_not_cover_a_file_that_has_a_rule_of_its_own`,
   `test_no_pattern_covers_a_stage_report_file_or_capability_json`).
6. With a marker string in repository text, the output never holds it unless `--show-text` is given:
   in a changed, removed, or added finding, a page, a JSON or text side file, a notes file, a file
   compared byte for byte, a stage report key, a normalized copy, the limits file, the LOG.md, and
   the brief (`test_marker_in_a_changed_finding_is_never_printed`,
   `test_marker_in_removed_and_added_findings_is_never_printed`,
   `test_marker_in_pages_files_and_the_brief_is_never_printed`,
   `test_marker_in_log_lines_is_never_printed`, `test_report_key_values_are_never_printed`).
7. A usage error exits 2 with nothing on stdout, a file that cannot be read included
   (`test_usage_errors_exit_2`, `test_a_file_that_cannot_be_read_exits_2`,
   `test_a_map_sending_two_names_to_one_is_a_usage_error`,
   `test_a_star_that_could_cover_more_than_was_named_is_refused`).
8. It writes nothing, and opens only the two run folders and the files named on the command line
   (`test_writes_nothing_in_either_run_folder`, `test_reads_only_the_two_runs_and_the_files_named`).
9. The whole suite and the grader pass: `.venv/Scripts/python -m pytest -q` and
   `.venv/Scripts/python tools/grader/grader.py all` (run by the builder and the verifier; not a unit test).

## History

- 2026-10-28: built, restructure step 0.
- 2026-10-28: verifier round 1 (A to E): `06-packet.md` loses its dates (`Written:`); JSON compared
  as canonical JSON, so a change of type shows; every file in both run folders is listed, a file in
  one run only is a difference, a file with no rule is compared byte for byte, and notes files are
  compared as text (renamed by `--map`); every stage report key besides `findings` is compared,
  `stage` after the map and `terms.code` as an item of its own; validation results and report keys
  have their own names in `--expect`, and a bare `*` is refused; text is read keeping every byte.
  The earlier list of what is not compared (`marks.json`, notes files, stage report keys) was wrong
  and is gone.
- 2026-10-28: round 3 (step 1 needs it): map format 2 (`names`, `paths`, `files`), with names and
  paths applied inside the old run's text and a moved file compared by its old path's rules; a
  missing LOG.md stage row is announced under `validation_changed`, not `LOG.md`; `*` in `--expect`
  is allowed only after a literal folder (`files_differ`) or as the whole stage part
  (`report_keys_differ`), and `validation_changed` and the check lists are exact; the filing rule
  (`cmp-<name>`, nothing added to `base-*`) is written down.
- 2026-10-28: round 4: `capability.json`'s top-level `stage` is compared after the map's names; in
  `files_differ`, `*` stops at a `/` and `**` is only the last segment after a literal folder, and no
  pattern covers a stage report file or a file that has a rule of its own (they are named exactly);
  a stage report the map pairs by `files` has its report keys compared, and an unpaired one says
  its report keys were not compared.
- 2026-10-31: M9 slice C, last fix round: `data/limits.md` has the rule `data/07-limits.md` has (text, with names taken out, and named exactly in `files_differ`), so a run filed under another name and made on another day no longer differs in its title. The old name still works.
