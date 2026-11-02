# qa: spec

One spec for the `05-qa` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. The finding fields are in `stages/CONTRACT.md` ("The check of the run").

## The check of the run

Added by M9 slice B (owner, 2026-10-30): "I am seeing it as a confirm everything that should have ran has results expected. If not let the user know. ask if we should move forward with the report with what ran or run report with what it has."

The step runs after the steps that ran, the validation, and the record, on every run, and before the report. It is not one of the steps a run chooses or stops after: `stages/stages.json` lists it under `qa`, beside the report, and `--until` does not name it. It is coded, reads the run folder only, and writes `data/05-qa.json`. The report stage draws section 7, `data/limits.md`, and the lists of steps that did not work from that file; the words on the pages are the report's.

### Gaps, limits, and what a check looked at

| | A **gap** (`qa.gap`) | A **limit** (`qa.limit`) | A **check that found nothing** (`qa.checked`) |
|---|---|---|---|
| What | something that should be there and is not | something the run did not examine, and says so | what a check that found nothing looked at, so a "found none" has a number behind it |
| Holds the run | yes | no | no |
| Kinds | `step-missing`: a step that should have run has no output (`why`: `failed`, `not-started`, `output-missing`, `output-unreadable`); `fixture-failed`: a step that ran and gave a wrong answer on its fixtures (`FAIL`); `fixture-unchecked`: a fixture check that gave no verdict (`ERROR`, `SETUP ERROR`, `NOT BUILT`, and `no fixture set` for every step but Pinpoint, which has no fixtures by design); `model-no-answer`: a chosen model read in which no passage got an answer, even after the retry; `coverage-missing`, `coverage-short`, `coverage-broken`: a step's coverage lines (M9 slice C, below) | `stopped`: a step a stop left out; `fixture-incomplete`: a check skipped for a missing optional tool; `model-partial`: some passages unanswered; `not-started`: a chosen read not started because the read before it got no answer (counted once: the read is the gap); `read-dropped`: a read an earlier command chose and `continue` did not (choosing a read at `continue` is the consent to send, so it did not run; the person went on without it, so it is a limit and no gap); `skip`, `note`, `unread`, `unscanned`, `testdata`, `standing` | `checked` (slice C, below) |

Which steps should have run: intake, every coded step, and an AI step that was chosen (the record's `chosen`) or started (it is in the record's `steps`), less the coded steps a stop left out. A chosen read that never started because a step before it failed is a gap, as the coded steps after a crash are. A chosen read the record says why it has no step is none: one a stop was before (`--until`; the one a stop wrote the input of, `prepared`, is one), and one that was not started because the read before it got no answer (`not_started`, a limit). The fixture rule is applied to every step that has a stamp, intake and this step included: a stamp for a step that has no output is not a second finding. Its words: a FAIL is a step that ran and gave a wrong answer; ERROR, SETUP ERROR, NOT BUILT, and `no fixture set` on a step that has fixtures are checks that could not be made (a fixtures folder that is gone or empty stamps every step `no fixture set`), and their zeros are as unvalidated; Pinpoint's `no fixture set` is no gap.

### What each check looked at (M9 slice C)

Each step from `02.1-inventory` to `04-pinpoint` has a `coverage` list (`stages/CONTRACT.md`, "Coverage lines"): per check, or per
pass over the same items, `of` (what it was to look at, counted from its inputs), `looked_at` (counted where it handled each one),
`explained` (items a skip or an unread or not-scanned entry explains), and `found`. `stages.json` lists the checks each step makes
(`checks`), and a test holds that list to the contract. The rules for a step's coverage are stated once, in `coverlines.audit`, and
the step reads its answer. It holds a run for these, each in a step that went well and left a readable output
(`coverage_items`): `coverage-missing`, once for the step, when a check in its list has no line, or when a finding's check (a
skip's too) is not on the list (a step with no `coverage` list has none for every check; the object `02.2-reader` wrote under that
name before slice C reads as no list); `coverage-short`, for a line whose `looked_at` plus `explained` is less than `of` (items the
check neither looked at nor explained, the sample sentence being `The check "phrase.remote-load" of the step "What the text asks
for" looked at 3 of 5 files; 2 are not explained.`); and `coverage-broken`, for a line that cannot be right: `looked_at` plus
`explained` is more than `of` (a count that is too high is as wrong as one that is too low), `found` is not the results among the
findings of its checks (a read's `found` is its flags: `why` is `found`, with `found_line` and `found_actual`), or it names a check
ID that is not on the step's list, is another step's, or is named by another line (`why` is `check`, with the `ids`). Not gaps: a step with no output or that failed (it has its own gap), a step a stop left out (no output to check), a model read
in which no passage got an answer (`looked_at` 0 with every passage explained by its skip, so its own gap is the one), and a check
skipped for a missing optional tool (its items count as explained by the skip finding that already exists; owner, 2026-10-25). A
`coverage` that is not a list of lines is an output that cannot be read (`pipeline.read_report`), which is the step's one gap
(`output-unreadable`) and no coverage gap on top. A coverage line whose unit is not a known one, or whose check ID is empty or has
white space in it, is such a list. A step whose output cannot be trusted, or that could not be measured, says nothing about what a
check looked at (below).

`qa.checked`, kind `checked`, says what a check that found nothing looked at (`checked_items`; the lines in `render.checked_line`
and `render.checked_steps`). It is no limit and no gap, so the count of limits is what it was before the slice. A step gets
these only when its fixture check measured its "none": the stamp is a pass, or INCOMPLETE, with some of its rows asked and not skipped (a gate,
a negative, or a recall: `Stamp.measured`, the one place the rule is kept; a count that is not `passed/total` is a step not measured). A step stamped `no fixture set` (Pinpoint), a read whose
rows were all skipped, a step that failed or could not be checked, and a run made without validation get none. A check with a skip
finding of its own is not named, a line left with no check is dropped, and so is a line that does not add up, a line whose items were
all explained by skips (nothing was looked at), and a line of the whole run (`run`). The terminal note counts them apart: `0 gaps,
13 limits, 18 checked`.

### Hold

With one gap or more the report is not written. The runner records `held` (`{"by": "05-qa", "gaps": N}`) and exits 1; `--brief` makes the step write `brief.md` in Walkdown's own words (the `hold` section). `walkdown.py continue <run folder>` on a held run runs no step and writes the report with what the run has (the `runner` section of `stages/_shared/specs/shared.SPEC.md`); the record's `held` becomes `released`. The pages name every gap, as a step that did not work and in section 7.

### The order of this step's own stamp

The stamp of this step's fixtures needs nothing from the run being made, so the runner takes it with the other steps' stamps, before the record, and the record holds it. This step then reads it from the record like any other, and the fixture rule applies to it: when its own fixtures fail, its "no gap" cannot be trusted, and the run is held (`05-qa` is the step of the gap).

### Must never

- Detect anything in the repository, judge it, score it, or rank it.
- Read the audited repository, or put text from it in a gap (a gap holds a step's plain name, a check ID, counts, a fixture result, the reasons Walkdown gave a skipped passage, and an error's type), so the brief of a held run can be handed to a chat assistant.
- Import another step's code, reach a model or a network, or write anything but `brief.md` of a held run with `--brief`.

### History

- 2026-10-30: M9 slice B: built (the brief: `pre-planning/parked/M9-QA.md`). It takes over the gathering `render.limits` did (O2: skips, standing limits, INCOMPLETE stamps, steps that did not work, test data set aside).
- 2026-10-30: M9 slice C: the coverage gaps and the `checked` limit (above). The fixtures in `Fixtures/05-qa/` gain a coverage list in every run folder and cases for each new kind (`tools/fixture-generators/make_qa_runs.py`).
- 2026-10-31: M9 slice C, last fix round: a stamp with a count that is not `passed/total` (`abc`, `3`, `3/x`) reads as not measured and the run goes on (it ended `stage 05-qa failed`). The lines the check reads count the items each check reads (`stages/CONTRACT.md`, "Coverage lines"), so what it holds a run for is the same and the counts are different. The page lines of `qa.checked` are `render.checked_line` (ids, one for each pass) and `render.checked_steps` (counts, one for each step).
- 2026-10-31: M9 slice C, fix round: `checked` is a check of its own, `qa.checked`, and `qa.limit` holds what it held before the slice. It is said only for a step whose fixture check measured its "none". `coverage-broken` also holds a `found` that is off and a check ID that is not the step's or is named twice; `coverage-missing` also holds a finding whose check is not on the step's list. The fixtures gain seven cases (`coverage-found-wrong`, `coverage-unknown-id`, `coverage-other-steps-id`, `coverage-twice`, `coverage-stray-finding`, `coverage-ai-flagged`, `checked-not-measured`).

## run

`python stages/05-qa/run.py <run folder> [--brief]`

### Inputs

A run folder (`facts.load`). `--brief`: when the run has a gap, write `brief.md` in the run folder.

### Outputs

One contract-1 report on stdout: `{"stage": "05-qa", "contract": 1, "findings": [...]}`, the findings `gather.gather` returns. One line on stderr: the number of gaps and limits. With `--brief` and at least one gap, `brief.md` in the run folder (`hold.write`). Exit 0 when it produced a report, including a report with gaps (the runner holds the run; this exit code does not); exit 2 with one `error:` line for a folder that is not a run or was made before this version (a record of another `format`).

### Must never

- Write anywhere but `brief.md`, and that only with `--brief` and a gap: run on a fixture folder (the grader), it writes nothing.

### Done when (each backed by a test in `tests/test_run.py`)

1. The report is one contract-1 document, and the folder is not written (`test_the_report_is_one_contract_1_document_on_stdout_and_the_folder_is_not_written`).
2. `--brief` writes the brief of a held run and nothing else, and no gap writes nothing (`test_with_brief_a_gap_writes_the_brief_of_a_held_run`, `test_no_gap_with_brief_writes_nothing`).
3. A folder that is not a run, or was made before this version, is refused with one line (`test_a_folder_that_is_not_a_run_or_was_made_before_this_version_is_refused_with_one_line`).
4. The step is coded: it imports the standard library, `stages/_shared`, and its own modules, and nothing that reaches a model or a network (`test_the_check_is_coded_it_imports_no_other_step_and_nothing_that_reaches_a_model_or_a_network`).
5. The step grades PASS on its fixtures (`test_the_check_grades_pass_on_its_fixtures`).

### History

- 2026-10-30: M9 slice B: built.

## facts

The run folder as facts: the record's steps, stamps, stop, and steps not started; each step's saved output when it reads (`reports`) and its name in `unreadable` when it does not; each step's own notes (`notes`: the lines the step wrote as `note: ...`, the prefix removed, and none from a step that failed; `pipeline.own_notes`); for a step that failed, the error's type read from the traceback in its messages (`errors`: `steperror.error_of`); and the number of lines in each model step's call log that reads as JSON (`logs`).

### Inputs

`load(run_dir)`: a run folder. A saved output reads when it is a JSON object with a list of `findings`, each a dict with a `check` (`pipeline.read_report`, the test the report stage and the comparison of runs apply too).

### Outputs

A `Facts`. `NotARun` (a message) for a folder with no `data/`, or a record that is missing, unreadable, or of a format other than `record.FORMAT`.

### Must never

- Read anything outside the run folder, or write anything.

### Done when (each backed by a test in `tests/test_facts.py`)

1. A run folder is read as the record, the outputs, the messages, and the call logs (`test_a_run_folder_is_read_as_the_record_the_outputs_the_messages_and_the_call_logs`).
2. An output that does not read is unreadable and no report, a saved `[]` or `{}` included (`test_an_output_that_does_not_read_is_unreadable_and_not_a_report`); a call log with a line that is not JSON is not counted (`test_a_call_log_with_a_line_that_is_not_json_is_not_counted`).
3. A folder that is not a run, or was made before this version, is refused (`test_a_folder_that_is_not_a_run_or_was_made_before_this_version_is_refused`).
4. A step that failed gives no notes, and its error type is read from its traceback; a step that finished gives only the lines it wrote as notes (`test_a_step_that_failed_gives_no_notes_and_its_error_is_read_from_its_traceback_alone`, `test_a_step_that_finished_keeps_only_the_lines_it_wrote_as_its_own_notes`).
5. A read an earlier command chose and `continue` left out is in the facts, in the list's order and only as a read, with its backend where the record kept one (`test_the_reads_an_earlier_command_chose_and_continue_left_out_are_in_the_facts`).

### History

- 2026-10-30: M9 slice B: built.
- 2026-10-30: M9 slice B: `chosen` (the record's key) is in the facts.
- 2026-10-30: M9 slice B, second fix round: `dropped` and `backends` (the record's keys) are in the facts.
- 2026-10-30: M9 slice B, second fix round: the hold's words: `no fixture set` and NOT BUILT say the step has no fixtures to be checked against, the closing line is not a command when its file is the one that is gone, and an output that exists but cannot be read is not "no output".

## gather

Every gap and limit of a run, from its facts, in the order section 7 lists them: the steps (in the order intake, the coded steps, the chosen model reads, then this step's own stamp: a stop, a gap, or a stamp that is not a pass), the model reads, the steps not started, the skips and messages the steps name and the files not read, the files not scanned and the test data set aside, then the limits that stand for every run (`static`, `model-reads`, `version-drift`, `english-only`, `phrases-zero`; the report words them).

### Inputs

`gather(facts)`; `report(facts)` wraps the findings as a contract-1 report.

### Outputs

A list of findings (`qa.gap`, `qa.limit`), each with `kind`, `step`, `step_check` (the check the finding is about, where there is one), `expected`, and `found`, and the fields of its kind (`stages/CONTRACT.md`). A step that is stopped, a skip, a note, an unread or unscanned file, test data, and the standing limits are findings too: the report words each from its fields.

- A skipped check or message is kept once however often it repeats. A model read whose passages are counted (`model-partial` or `model-no-answer`) gives neither its passage skips nor its `skipped: ...` message.
- The messages that name a limit are those `stages/_shared/limitnote.py` matches, which the report stage's list of what was not checked matches too.
- A gap carries a `cause` where Walkdown knows one: a model read's reasons, counted; the type of the error a step stopped with, and the module of a missing import. Never an error's message.

### Must never

- Hold text from the audited repository in a gap.
- Count a step a stop left out, a read a stop is before or that waits with its input file after one, a read held back because the read before it got no answer, Pinpoint's `no fixture set`, a check skipped for a missing optional tool, or a read with some passages unanswered as a gap, and never count a read twice.

### Done when (each backed by a test in `tests/test_gather.py`)

1. A step that failed, never started, or lost its output is a gap, and a model read nobody chose is not: `test_a_step_that_failed_is_a_gap_and_so_is_each_step_after_it_that_never_started`, `test_a_step_the_record_says_went_well_whose_output_is_gone_or_unreadable_is_a_gap`, `test_a_chosen_model_read_that_failed_is_a_gap_and_one_nobody_chose_is_not`.
2. A step a stop left out, and a read waiting after a stop, are limits and no gap: `test_the_steps_a_stop_left_out_are_limits_and_not_gaps`, `test_a_stop_after_the_last_coded_step_leaves_nothing_out_and_a_model_read_waiting_is_no_gap`.
3. A fixture check that did not pass is a gap whatever its word, this step's own and intake's included; a check skipped for a missing tool, a pass, Pinpoint's `no fixture set`, and a run made without validation are not: `test_a_fixture_check_that_did_not_pass_is_a_gap_whatever_its_word`, `test_intake_and_the_check_of_the_run_itself_are_held_to_the_same_rule`, `test_a_check_skipped_for_a_missing_tool_a_pass_and_no_fixture_set_are_no_gap`, `test_a_run_made_without_validation_has_no_fixture_gap`, `test_a_step_with_no_output_gets_no_fixture_finding`. A check that gave no verdict is a gap of its own kind (`test_a_fixture_check_that_gave_no_verdict_is_a_gap_of_its_own_kind`), and `no fixture set` is a gap for every step but Pinpoint (`test_no_fixture_set_is_no_gap_for_pinpoint_and_a_gap_for_every_other_step`).
7. A chosen read that never started is a gap, like the coded steps after a crash; a stop before a chosen read is a stop, and a read waiting with its input file or held back by the one before it is counted once: `test_a_chosen_read_that_never_started_is_a_gap_like_the_coded_steps_after_a_crash`, `test_a_stop_before_a_chosen_read_is_a_stop_and_no_gap_and_a_waiting_read_is_not_counted_twice`, `test_a_chosen_read_the_one_before_it_held_back_is_counted_once`.
4. A model read in which no passage got an answer is a gap; one with some passages unanswered is a limit; one that asked about nothing or answered everything is neither; a Pinpoint not started is one limit and no second gap; reasons are counted, most common first: `test_a_model_read_in_which_no_passage_got_an_answer_is_a_gap`, `test_a_model_read_with_some_passages_unanswered_is_a_limit_and_not_a_gap`, `test_a_model_read_that_asked_about_nothing_or_answered_everything_is_neither`, `test_a_pinpoint_the_record_says_was_not_started_is_one_limit_and_no_second_gap`, `test_the_reasons_are_counted_most_common_first`.
5. The limits the report stage used to gather: skips once, messages once, unread and unscanned files, test data, the counted skips left out, the standing limits last, and the order: `test_a_skipped_check_is_a_limit_once_however_many_times_it_repeats`, `test_a_message_that_names_a_limit_is_kept_once_and_one_that_does_not_is_not`, `test_unread_and_unscanned_files_and_set_aside_test_data_are_limits`, `test_the_counted_passage_skips_of_a_model_read_are_left_out_of_the_skips`, `test_the_standing_limits_are_in_every_run_and_last`, `test_the_items_come_in_the_order_section_seven_lists_them`.
6. Every finding names its step and check and says what was expected and what was found, and a gap holds no text a repository could write: `test_every_finding_names_the_step_and_the_check_and_says_what_was_expected_and_what_was_there`, `test_the_report_has_a_gap_for_each_hold_and_holds_no_text_a_repository_could_write`.
8. A check with no coverage line is one gap for the step naming every check left out, and a step with no `coverage` list is that gap for all its checks: `test_a_check_with_no_coverage_line_is_one_gap_for_the_step_naming_every_check_left_out`, `test_a_step_with_no_coverage_list_is_one_gap_naming_all_its_checks`.
9. A line whose items are neither looked at nor explained is a gap naming the check and the counts, items explained by a skip make it whole, and a line that counts more than there were is a broken count and a gap: `test_a_line_whose_items_are_neither_looked_at_nor_explained_is_a_gap_that_names_the_check_and_the_counts`, `test_items_explained_by_a_skip_make_the_line_whole_and_are_no_gap`, `test_a_line_that_counts_more_than_there_were_is_a_broken_count_and_a_gap`.
10. One gap per cause: a step with no output, a step a stop left out, a coverage that cannot be read, and a model read with no answers have no coverage gap on top of their own; a model read that dropped a passage has one: `test_a_step_with_no_output_has_no_coverage_gap_on_top_of_its_own`, `test_a_stops_steps_have_no_coverage_to_check_and_a_coverage_that_cannot_be_read_is_the_one_gap_of_an_unreadable_output`, `test_a_read_with_no_answers_has_looked_at_zero_and_its_passages_explained_so_its_own_gap_is_the_only_one`, `test_a_partial_read_that_adds_up_is_a_limit_and_a_read_that_dropped_a_passage_is_a_gap`. A coverage gap holds no text a repository could write: `test_a_coverage_gap_holds_no_text_a_repository_could_write_and_names_the_step_and_the_check`.
11. A check that found nothing says what it looked at, once for a line, and not for a line that found something, an unwhole line, a line whose items were all skipped, or a step that did not work: `test_a_check_that_found_nothing_says_what_it_looked_at_and_one_that_found_something_does_not`, `test_a_line_that_adds_up_to_nothing_looked_at_a_run_line_and_a_line_with_a_gap_are_not_said_as_found_none`, `test_a_check_with_nothing_to_look_at_says_so`, `test_a_step_that_did_not_work_says_nothing_of_what_it_looked_at`.

### History

- 2026-10-30: M9 slice C: `coverage_items` and `checked_items` (above, "What each check looked at"), called from `gather` after the steps and before the standing limits.
- 2026-10-30: M9 slice B: built. The gathering is `render.limits` of 06-report moved here, with the same order and the same once-each rule; the words are the report's.
- 2026-10-30: M9 slice B: `FAIL` is not the only fixture result that holds a run. The pages have always named a step whose check gave `ERROR` (the grader could not run) or any other word but a pass as one that did not work, so the rule is "any word but a pass": the pages and the hold agree.
- 2026-10-30: M9 slice B, second fix round: a read an earlier command chose and `continue` did not is a `read-dropped` limit, after the read that was not started and before the skips (`dropped_items`); the pages say it in one sentence. It carries `backends` and `stopped`, so the words give a way that works: `continue` refuses once the run has finished.
- 2026-10-30: M9 slice B, fix round: `no fixture set` is a gap for every step but Pinpoint (a missing or empty fixtures folder stamps every step so, and the check passed such a run); a check that gave no verdict is its own kind, `fixture-unchecked`, apart from `fixture-failed` (FAIL); a chosen read is a step that should have run, so a crash before it is a gap for it too (the record's `chosen`); the notes the check reads are a finished step's own `note:` lines (a failed step gives none), and the error's type is read by `steperror`.

## hold

The brief of a held run, `brief.md`: the gaps, counted and named by step and check, then the two ways on. Walkdown's own words and paths only.

### Inputs

`build(run_dir, gaps, stop=None)`: the run folder, the `qa.gap` findings in order, and the record's stop (`record.stop_of`) when the run also stopped as asked. `write(run_dir, gaps, stop=None)` saves it as `brief.md`.

### Outputs

```
Walkdown brief: <the run's repository name>
This run is held before the report: the check of the run found 2 gaps.

  1. The step "What loads what" has no output: it failed (exit 1: ValueError).
  2. The step "Needs a human read" (soft.sweep) got no answer for any passage: 12 of 12. Reasons: jev: no key (12). The call log is data/03-sweep.calls.jsonl.

No report was written. The saved outputs of the steps that ran are in <run folder>/data.
To write the report with what ran: python walkdown.py continue <run folder>
Or fix the cause and audit the repository again.
What Walkdown knows of the cause: "What loads what": ValueError; "Needs a human read": jev: no key (12).
```

The count in the first line says how the gaps follow when a step failed: `found 4 gaps (1 step failed, and the 3 after it did not start)`, from the gaps' `why` (otherwise `found 2 gaps`). A fixture check that gave no verdict reads `The step "<plain>" could not be checked against its fixtures: it gave <result>.` for ERROR and SETUP ERROR and `The step "<plain>" has no fixtures to be checked against.` for NOT BUILT and `no fixture set` (a FAIL keeps `did not pass its fixture check: it gave FAIL.`), and with any such gap the brief ends with `To see why: python tools/grader/grader.py all`, or, when `tools/grader/grader.py` is the file that is missing, `tools/grader/grader.py is missing: get a fresh copy of Walkdown.` A step whose output is there and cannot be read reads `The step "<plain>": its saved output cannot be read.` (and `... is not in the run folder.`), not `has no output: ...`, which says two things. A run that also stopped as asked says it in the stop's own line, `Stopped after "<plain>", as asked (--until); the steps after it did not run.` (`common_lines.STOPPED_LINE`, the words the brief of a stopped run uses), just before "No report was written." The cause line is there only when a gap carries a cause. A folder with a space is quoted in the command. The coverage gaps (M9 slice C) are worded in `common_lines.coverage_gap_text`, once for the brief and the pages: `The check "phrase.remote-load" of the step "What the text asks for" looked at 3 of 5 files; 2 are not explained.`; a line of several checks names the first (`The check "phrase.K.exfil" and 13 more that run in the same pass of the step ... looked at 83 of 85 files; 2 are not explained.`); `The step "What this touches" did not say what 7 of its 8 checks looked at, starting with "cap.grant".` (`... did not say what its check "cap.limit" looked at.` for one); a broken count says `counted 3 looked at and 2 explained of 3 files: the counts do not add up.` A gap of a kind this file does not know is worded `The step "<plain>" (<check>): expected <expected>; found <found>.`

### Must never

- Hold text from the audited repository (see "Must never" above): the brief is handed to a chat assistant like any other.

### Done when (each backed by a test in `tests/test_hold.py`)

1. The brief counts the gaps, names each by step and check, and gives the two ways on in these words (`test_a_brief_counts_the_gaps_names_each_by_step_and_check_and_gives_the_two_ways_on`); one gap is "1 gap", and a folder with a space is quoted (`test_one_gap_is_one_gap_and_a_folder_with_a_space_is_quoted_in_the_command`).
2. No text a repository could write gets in (`test_a_brief_holds_no_text_a_repository_could_write`).
3. A gap of an unknown kind is worded from what it expected and found (`test_a_gap_of_a_kind_this_file_does_not_know_says_what_it_expected_and_what_it_found`).
4. `write` saves `brief.md` in the run folder (`test_write_saves_brief_md_in_the_run_folder`).
5. The first line counts the step that failed and the steps that never started (`test_the_first_line_counts_the_step_that_failed_and_the_steps_that_never_started`).
6. A check that could not be made is worded so and the brief says where to look (`test_a_check_that_could_not_be_made_is_worded_so_and_the_brief_says_where_to_look`).
7. A run that also stopped says so in the stop's own line (`test_a_run_that_also_stopped_says_so_in_the_stops_own_line`).
8. A coverage gap is worded in Walkdown's own words, names the step and the check, and holds no text a repository could write: `test_a_coverage_gap_is_worded_in_walkdowns_own_words_and_names_the_step_and_the_check`, `test_a_line_that_covers_several_checks_names_the_first_and_says_how_many_more_run_in_the_same_pass`, `test_an_explained_part_is_said_and_the_rest_is_what_is_not_explained`, `test_a_step_with_no_line_for_its_checks_and_a_broken_count_are_worded`, `test_a_coverage_gap_holds_no_text_a_repository_could_write`.

### History

- 2026-10-30: M9 slice C: the coverage gaps' words (above).
- 2026-10-30: M9 slice B: built.
