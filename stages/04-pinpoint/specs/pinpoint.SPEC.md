# pinpoint: spec

The line behind each sweep flag, an optional AI stage (restructure step 5, 2026-10-29; first built
2026-10-13, owner, in the old soft stage). For each sweep passage the report shows, a second model
names the line that does the flagged kind of action, quotes it, and says it in one plain sentence. A
sweep passage can be a dozen lines; a reader new to this cannot tell which part is the issue. It runs
only when a backend is chosen and only after Sweep. Prototype and the three hand runs it was shaped
on: `pre-planning/soft/pinpoint/`.

Scripts: `run.py` (the runner), `pinpoint.py` (targets, question, check, findings, and `Reader`, this step's side of a text
model). Shared: `stages/_shared/softdata.py`, `linetext.py`, `upstream.py`, `back_claude.py` (the Claude Code command; it moved
there in M1 slice A, since Sweep uses it too; its spec is `shared.SPEC.md`, `back_claude`), `textmodel.py`, `usage.py`,
`probability.py`. One spec for the stage.

Status: built. Backends: the Claude Code command (`claude-cli`, with a model if the person names one). Jev does not read for
this step: it answers from fixed options, and the pinpoint needs a line and a sentence.

## Inputs

```
python stages/04-pinpoint/run.py <input_dir> --reports <dir> [--out <dir>] [--pinpoint none|claude-cli[:model]] [--input-only]
```

- `--pinpoint` (or `WALKDOWN_SOFT_PINPOINT`; the flag wins): `none` (the default), or `claude-cli` with a model if the person names one
  (`claude-cli:<model>`; the text before the first colon is the backend, in any case, and the rest is the model as typed). A value
  that cannot be used (an unknown backend, `jev`, a model name outside the allowed characters, nothing after a colon) exits 2
  with one sentence that says why (`options.parse_choice`). The options of the other reads (`--sweep`, `--label`, `--compare`,
  `--relational`) are not options of this stage.
- `--input-only` (O3): write `04-pinpoint.input.jsonl` and stop. It needs `--out` and a backend, and Sweep's
  report as any chosen backend does; without `--out` or a backend it exits 2 with one error line. See Behavior, 3.
- `--reports <dir>`: `03-sweep.json`, `02.1-inventory.json`, and `02.4-phrases.json` (for the `secret.found` rows), each a contract-1
  report of its stage. Needed only when a backend is chosen; without `--reports` the stage exits 2 and says it reads
  Sweep's report; a missing or invalid report exits 2. The stage never runs Sweep.
- `--out <dir>`: where the files below are written; a folder inside the input is refused (exit 2).
- The input folder, for the lines of each passage (`linetext.Lines` with the encodings `02.1-inventory` recorded).
- `Library/softreads.yaml`: `pinpoint` (`system`, `question`), the sweep option's `what` for the kind
  the passage was flagged as, `answer_cap` (an answer is cut at 2,500 characters and marked
  `capped`), and `retry_wait`, the seconds a call that got no answer waits before its second try (2).
- `WALKDOWN_SOFT_CLAUDE_MODEL` picks the Claude model when the option names none (default `sonnet`); the option wins.
  `WALKDOWN_SOFT_CLAUDE_WORKERS` the calls at a time (default 4).

## Behavior

1. **No backend.** The stage asks nothing and writes no file; the report has no backend and no finding.
2. **Targets.** `pinpoint.targets(sweep findings)`. The lines of each are the file's through `secretmask.ToSend`
   (`stages/_shared/specs/shared.SPEC.md`, `secretmask`), as Sweep reads them: a line the secret scan flagged is a blank at its place,
   numbered as before, with the rest of a private key. The stage checks this itself, so a Sweep report saved before the rule changes
   nothing. A target in a file the scan did not read, or with nothing left, is not asked about and is a skip finding with its reason
   (`secretmask.NOT_READ`; `NOTHING_LEFT`, which only such a saved report can reach, since Sweep sends no such passage). A
   note says how many lines of the passages are blank, in words that are no limit: Sweep's note already says so on the pages.
3. **The input file.** With `--out`, `04-pinpoint.input.jsonl` is written, and closed, before the backend
   is called. One JSON line per target: `qid`, `sweep_qid`, `backend`, `system` (the system prompt) and
   `prompt` (what goes to the model on stdin). With `--input-only` that is all the stage does (O3: a run stopped
   with `--until` just before the pinpoint): the questions are built from Sweep's report as always, no backend
   is made, nothing is sent, nothing is printed on stdout, the exit is 0, and the file is byte for byte the one a
   full read writes first. A note on stderr says what was written and that nothing was sent.
4. **Ask.** `backend.pinpoint(questions)`. A call that gets no answer is tried once more (`textmodel`, `shared.SPEC.md`).
5. **Check and record.** `pinpoint.findings` checks each answer against the passage; with `--out`,
   `04-pinpoint.answers.jsonl` holds one row per raw answer (`pinpoint.record`): `role` `pinpoint`,
   `qid`, `backend`, `model`, the `request` and `response`, and the model's `answer` verbatim and
   `capped`, or `skipped`. The row holds nothing of the second try: the answer is the one that was used (or, when
   neither try could be read, the second). With `--out`, **the call log** `04-pinpoint.calls.jsonl` (M9): one line for
   each passage whose first try got no answer or that was not sent, written only when there is a line
   (`stages/_shared/specs/shared.SPEC.md`, section `calllog`: `qid`, `backend`, `first`, `retry`, `at`). When there is a
   line the report also has a `calls` block (`log`, `answered_on_retry`, `not_sent`).
6. **Notes** on stderr: the backend, whether it is remote, how many passages; the summary
   (`pinpoint.summary`: passages asked, answers whose quote is in the text, skips by reason); the calls
   (how many answered on the retry, how many got no answer after it, how many were not sent, and the call log); the
   tokens the calls used (`usage.note`) and the cost the CLI reported. A plain progress line, `pinpoint: 25 of 431 passages done`,
   with no `note:` in front, is written every 25 passages. The report has a `usage` block (`stages/CONTRACT.md`, "Tokens").

## pinpoint.py

- `targets(findings)`: the `soft.sweep` findings the report shows as their own card: not skipped, no `02.4-phrases` pattern inside
  (`covered` empty), and either `p_any >= MIN_P` (0.4, the report's near-the-line floor, `render.SWEEP_NEAR_P`) or, for a read
  that gives no probability (a model that takes text; `probability.of` is None), `flagged`. A passage the pages list is a passage
  it asks about, for either kind of read.
- `question(finding, lines, data)`: `{qid: "pin:" + sweep qid, sweep_qid, _prompt, _system}`. The
  prompt holds the kind in the sweep option's own words, the passage as numbered lines marked as
  data, and the JSON shape asked for.
- `parse(text)`: the JSON object in an answer, or None. `readable(text)`: whether `parse` finds one; an answer that
  is not is a call with no answer (M9), which the backend tries once more.
- `locate(n, quote, lines)`: the last line of `quote` when it starts on line `n`; prose is hard-wrapped,
  so a quote may run onto the next lines of the passage. Spaces are folded. None when the quote does
  not start on line `n`.
- `find(n, quote, lines)`: `(start, end)` of the quote: on line `n` when it starts there, else on the
  first passage line it does start on (owner, 2026-10-13: a model can be a line off; one
  run had one, "run" ending line 447 quoted as line 448). None when the quote is nowhere in the
  passage.
- `check(answer, lines)`: `verified`, `why`, `line`, `line_end`, `quote`, `plain`, `also`. Verified when
  the quote is found in the passage and `plain` is not empty, or when no line is named and `plain` says
  so. `line` is where the quote really starts; `why` says when that differs from the model's number.
  `also` keeps at most 2 entries that pass the same check.
- `findings(targets, questions, answers, lines_of)`: one `soft.pinpoint` finding per target (fields in
  `stages/CONTRACT.md`), or `skipped` (no answer, the backend's skip, or `unparseable pinpoint answer`).
- `summary(findings)` and `record(result)`: the stderr lines and the answers-file row above.

## The Claude Code backend and the Reader

The backend is `stages/_shared/back_claude.py` (`shared.SPEC.md`, `back_claude`): the command, its isolation flags, the model
(`claude-cli:<model>`, else `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`), the second try, the stop on a rejected login (the first call
runs alone), the workers, and the tokens. This step's side of it is `pinpoint.Reader(data, backend)`: `pinpoint(questions)` asks
each with the pinpoint system text (`softreads.yaml pinpoint.system`) and takes an answer only when it holds a JSON object
(`readable`); an answer is cut at `answer_cap` and marked `capped`; one that cannot be read is a call with no answer, which the
backend tries once more, and `findings` skips it as `unparseable pinpoint answer` if the second try is no better.

## Outputs

stdout: `{"stage": "04-pinpoint", "contract": 1, "backends": [...], "findings": [...], "coverage": [...]}`, `"calls": {...}` when a
call got no answer on its first try (above), and `"usage": {...}` when a backend was chosen; a `backends` row:
`role` `pinpoint`, `backend`, `remote`, `model`. The orchestrator saves it as `data/04-pinpoint.json`
and the notes as `data/04-pinpoint.notes.txt`. Exit 0 when a report was produced; 2 for a bad input
folder, flag, or environment value, a chosen backend without a valid `--reports`, or a refused `--out`.

## What the step looked at (added 2026-10-30, M9 slice C)

The report's `coverage` list (`stages/CONTRACT.md`, "Coverage lines") has one line: `soft.pinpoint`, unit `passages`. `of` is the
sweep passages the report shows (`pinpoint.targets`), counted from Sweep's report before anything is sent; `looked_at` is counted in
`pinpoint.findings`, where a passage that got an answer gets its finding (a quote the passage does not hold is still an answer, with
`verified` false); `explained` is the passages that got none or an answer that cannot be read, each with its skip finding. A read in
which no passage got an answer has `looked_at` 0 and every passage explained. A passage that gets neither a finding nor a skip leaves
the line short (`tests/test_coverage.py`, with a fake backend and no model). `found` is the answers whose quote the passage holds
(`verified` true), since the read answers every passage it is asked about; an answer whose quote the passage does not hold is a
passage looked at with no result.

## Who calls it

- The orchestrator starts it only when `--pinpoint` (or `WALKDOWN_SOFT_PINPOINT`) names a backend and
  Sweep ran in the same run. `--pinpoint` without `--sweep` runs nothing and prints `note: --pinpoint
  needs --sweep; no pinpoint questions asked`.
- The grader does not run it: the stage has no fixture set (decision 5-C). `grader.py` says `no fixture
  set` and `LOG.md` shows `no fixture set` in its validation column; that is not a pass, a failure, or
  a step that did not work.

## Must never

- Change, demote, or remove a `soft.sweep` finding, or any finding of the coded steps (`02.1-inventory` to `02.6-builder`). "No line does this" is
  recorded, never acted on.
- Keep a quote that is not in the passage, word for word, in the run's own text, or show it at a line
  other than the one it starts on.
- Send a line the secret scan flagged, or a file it did not read. A quote of such a line is not in the passage as this step reads it.
- Hand the model tools or the user's settings: `--tools ""`, `--safe-mode`, no setting sources, an
  empty working folder.
- Send anything before the input file is on disk (when `--out` is given), or put the passage on a
  command line.
- Log in for the person, or write inside `<input_dir>`.
- Make a third call for a passage, or put a passage, a prompt, or a model's answer in the call log.
- Import another stage's code.

## Done when (tests in `tests/`)

1. Targets are exactly the passages the report shows (`test_pinpoint.py::test_targets_are_the_passages_the_report_shows`).
2. A quote may run onto the next lines but must start on its line; invented quotes and lines outside the
   passage fail; a real quote under the wrong line number is moved to its line
   (`test_a_quote_may_run_onto_the_next_lines_but_must_start_on_its_line`).
3. `check` keeps only quotes found in the text, drops failing `also` entries, accepts "no line" with a
   plain sentence, and refuses an empty plain sentence (`test_check_keeps_only_quotes_found_in_the_text`).
4. Skipped and unparseable answers are recorded as skips (`test_findings_record_skips_and_unparseable_answers`).
5. The question carries the numbered lines, the kind in the sweep option's words, and the
   data-not-instructions rule (`test_question_carries_numbered_lines_the_kind_in_words_and_the_data_rule`).
6. The summary counts the passages and names the skips; the answers row keeps the answer, request, and
   response verbatim (`test_summary_counts_the_passages_and_names_the_skips`,
   `test_record_keeps_the_answer_the_request_and_the_response_verbatim`).
7. The command holds `-p`, `--tools ""`, `--strict-mcp-config`, `--no-session-persistence`,
   `--safe-mode`, `--setting-sources ""`, `--output-format json`, `--model`, `--system-prompt`; the prompt
   goes on stdin, not argv; the working directory is empty at call time
   (`stages/_shared/tests/test_back_claude.py::test_command_flags_and_stdin`); the model is the one named, then the
   environment's, then `sonnet` (`test_the_model_is_the_one_named_then_the_environment_then_sonnet`).
8. An answer over the cap is cut and marked `capped`, and one that holds no JSON object is no answer
   (`test_pinpoint.py::test_the_readers_answer_is_cut_at_the_cap_and_marked_and_must_hold_a_json_object`); a login rejected again
   stops further calls; a timeout or `is_error` skips only its question; a missing CLI skips all without a call; no questions
   make no call (`test_back_claude.py::test_a_rejected_login_that_is_rejected_again_stops_further_calls`,
   `test_a_timeout_and_an_error_skip_only_their_question`, `test_a_missing_cli_skips_without_a_call`,
   `test_no_questions_means_no_call_and_no_lookup`).
9. Live, opt-in (`WALKDOWN_LIVE_CLAUDE=1`, `stages/_shared/tests/test_claude_isolation_live.py`): in a folder with a canary
   CLAUDE.md and project hooks that write marker files, the call without the isolation flags lets the
   leak through (proof the probe sees one), and the command this module builds lets neither through.
10. With no backend the stage asks nothing, writes nothing, and needs no reports; the environment picks a
    backend and a flag overrides it; an unknown value and the other stages' options exit 2
    (`test_run.py::test_with_no_backend_the_report_has_no_findings_and_nothing_is_written`,
    `test_the_environment_picks_a_backend_and_a_flag_overrides_it`,
    `test_an_unknown_backend_exits_2_and_so_do_the_options_of_the_other_reads`).
11. A chosen backend needs Sweep's report, the inventory, and the phrase report, each valid (`test_a_chosen_backend_needs_the_reports_and_sweeps_report`).
12. A stub backend names a line for each shown sweep passage, with the same findings as before on the same
    answers, and changes no sweep finding (`test_a_stub_backend_names_a_line_for_each_shown_passage`,
    `test_it_changes_no_sweep_finding`); skipped and unparseable answers are skip findings
    (`test_skipped_and_unparseable_answers_are_skips`); no shown passage asks nothing
    (`test_no_shown_passage_means_nothing_is_asked`).
13. `--out` writes the input before the backend is asked and the answers after; `--out` inside the input
    exits 2 (`test_out_writes_the_input_before_the_backend_is_asked_and_the_answers_after`,
    `test_out_inside_the_input_is_refused`).
14. No finding has a field named risk, severity, score, or verdict
    (`test_a_stub_backend_names_a_line_for_each_shown_passage`).
15. `python tools/grader/grader.py 04-pinpoint` says `no fixture set`, not FAIL and not NOT BUILT
    (`grader/tests/test_grader.py::test_a_listed_stage_with_no_sheet_and_no_fixtures_grades_no_fixture_set`;
    `stages/_shared/tests/test_validate.py::test_the_real_grader_stamps_pinpoint_no_fixture_set_and_sweep_pass`).
16. `--input-only` never sends: a backend whose `pinpoint` raises is never made or asked, the file is byte for byte the
    one a full read writes first, stdout is empty, and it is refused without `--out` or a backend
    (`test_input_only_writes_the_input_file_and_never_makes_or_asks_the_backend`,
    `test_input_only_is_refused_without_out_or_a_backend`).
17. A call that gets no answer is tried once more after the wait, and the answer is used
    (`test_back_claude.py::test_a_call_that_fails_once_is_tried_again_after_the_wait_and_the_answer_is_used`,
    `test_an_answer_that_cannot_be_used_is_tried_again_and_a_usable_one_is_used`); one that fails twice is skipped with
    the second try's reason and never made a third time
    (`test_a_call_that_fails_twice_is_skipped_with_the_second_tries_reason_and_never_tried_a_third_time`); an answer that
    cannot be read twice is kept as it came, for `pinpoint.findings` to skip as `unparseable pinpoint answer`
    (`test_an_answer_that_cannot_be_used_twice_is_kept_as_it_came_for_the_step_to_skip`,
    `test_run.py::test_an_answer_that_cannot_be_read_twice_is_still_the_unparseable_skip_and_is_logged`); without an `accept`
    the text is the answer (`test_without_an_accept_the_text_is_the_answer`).
18. A login rejected once and accepted on the retry stops nothing
    (`test_a_login_rejected_once_and_accepted_on_the_retry_stops_nothing`); nothing to call is not tried again and
    nothing waits (`test_nothing_to_call_is_not_tried_again_and_nothing_waits`).
19. The call log has a line for each passage whose first try got no answer or that was not sent, holds no text of the
    passage or the prompt, and is written only when there is a line; the answers file keeps the answer as it came
    (`test_run.py::test_a_call_that_fails_once_is_answered_on_the_retry_and_logged`,
    `test_a_call_that_fails_twice_is_a_skip_with_the_second_reason`,
    `test_an_answer_that_cannot_be_read_twice_is_still_the_unparseable_skip_and_is_logged`,
    `test_when_every_call_answers_on_the_first_try_there_is_no_call_log_and_no_calls_block`,
    `test_the_chosen_backend_is_made_with_the_readability_check_and_the_log_is_where_the_layout_says`;
    `test_back_claude.py::test_the_call_log_row_holds_no_text_of_the_passage_or_the_prompt`).
20. The wait before the second try is the data's
    (`test_back_claude.py::test_the_wait_before_the_second_try_is_the_one_in_the_data_and_no_number_of_the_backend`).
21. A model option is a backend and a model: `claude-cli:<model>` names the model, the variable is the fallback, and a value that
    cannot be used (`jev`, `jev:x`, an empty model, a character outside the allowed set, a leading dash) exits 2 with one sentence
    (`test_run.py::test_the_environment_picks_a_backend_and_a_flag_overrides_it`,
    `test_the_option_names_the_model_and_the_variable_is_the_fallback`,
    `test_the_options_that_cannot_be_used_exit_2_with_one_sentence_and_nothing_on_stdout`); the real stage with a model named finds
    no CLI on the offline path and sends nothing
    (`test_the_real_stage_with_a_model_named_finds_no_cli_on_the_offline_path_and_sends_nothing`).
22. A sweep read that gives no probability is asked about when it flagged the passage and no pattern covers it, and the report lists
    the same passages (`test_pinpoint.py::test_a_read_with_no_probability_is_asked_about_when_it_flagged_the_passage_and_no_pattern_covers_it`,
    `test_run.py::test_the_passages_a_read_with_no_number_flagged_are_the_ones_asked_about`).
23. The tokens the calls used are in the report's `usage` block (with `reported`, how many calls reported any) and a note, `not reported` and absent where the backend gave none, `(from N of M calls)` where only some did,
    and a pinpoint with nothing to ask sent nothing
    (`test_run.py::test_the_tokens_the_calls_used_are_in_the_report_and_a_note`,
    `test_a_run_with_no_backend_has_no_usage_block_and_a_pinpoint_with_nothing_to_ask_sent_nothing`).
24. The Reader asks each question with the pinpoint system text, names it in the request by its label, and gives the answer fields
    `findings` reads (`test_pinpoint.py::test_the_reader_asks_each_question_with_the_pinpoint_system_text_and_names_it_in_the_request`,
    `test_the_reader_over_the_cli_gives_the_answer_fields_the_findings_read`).
25. A file name is in no prompt of a text model (M1 fix 2): the prompt is the kind and the numbered lines of the passage, and the
    system text; a canary in the name reaches nothing sent
    (`test_pinpoint.py::test_a_file_name_reaches_nothing_a_text_model_is_sent`).

26. No flagged line goes to the model: it is no part of the question and keeps its number, with a private key's body too
    (`test_run.py::test_a_flagged_line_is_no_part_of_the_question_and_keeps_its_number`,
    `test_a_private_key_body_is_no_part_of_the_question`), a quote of it is not found (`test_a_quote_of_a_line_left_out_is_not_found`), and
    the input file holds none (`test_input_only_writes_no_flagged_key`), nor any file of the real stage behind the test wall
    (`test_the_real_stage_behind_the_wall_keeps_no_flagged_key_in_any_file`).
27. A passage with nothing left and a file the scan did not read are not sent and are skips, and the coverage line adds up
    (`test_a_passage_with_nothing_left_is_not_sent_and_is_a_skip`, `test_a_file_the_scan_did_not_read_is_not_sent`,
    `test_a_file_the_scan_leaves_out_by_name_is_not_sent`). The note counts the blank lines and names no limit
    (`test_the_note_counts_the_blank_lines_and_names_no_limit`).

## Known limits

- No grader rows: the answer is a model's, so there is no fixed expected line to gate on yet. The quote
  check is the gate on each answer. Fixtures with a known right line, and one where the honest answer is
  "no line", are the next step.
- The second read varies run to run (the hand runs named the same main line each time; the "also" lines
  and the plain wording changed).

## History

- 2026-10-13: built (owner) in the old soft stage as `pinpoint.py` and the `pinpoint` method of
  `back_claude.py`.
- 2026-10-29: its own stage (restructure step 5). `back_claude.py` is cut down to the pinpoint call (the
  labeling and relational reads left with the parked code); the stage reads Sweep's saved report instead
  of running with it; new: the input file, written before anything is sent. Findings are the same on the
  same answers.
- 2026-10-29: restructure step 7: `NAMES` and `ENV` are built from `stages.json`; any off value (`off`, `0`,
  `false`, `no`) is `none`, for the flag and the variable (notes M14 a); the grader is at `tools/grader/grader.py`.
- 2026-10-29: restructure step 7b: the earlier reports are keyed by stage name (`READS`, from `stages.json`), not by a
  two-digit number; the findings are the same.
- 2026-10-30: O3: `--input-only`.
- 2026-10-30: M9 slice A (owner: "if something was called and got no answer, log it, try it one more time, then move
  on"): a call that gets no answer, including an answer that cannot be read, is tried a second time after `retry_wait`
  (`Library/softreads.yaml`, 2 seconds); a login rejected again stops the later calls, which are skipped as
  `not sent: claude-cli: authentication error` (was `claude-cli: authentication error` for every one); the call log
  `04-pinpoint.calls.jsonl` and the report's `calls` block are new (`stages/_shared/specs/shared.SPEC.md`, `calllog`).
  The findings of a read in which every call answers on the first try are the same.
- 2026-10-30: M9 slice A, fix round: no text of the program's output is kept. A skip reason is `claude-cli: error, exit
  code <N>` (was `claude-cli: error: <160 characters of the output>`), and the call log's `first` and `retry` hold
  `kind` and `status` (the exit code) where they held a message. The output can repeat the prompt (the passage) and the
  model's words. The wait before the second try is tested as the data's.
- 2026-10-30: M9 slice C: the report has a `coverage` list (above). The findings, the call log, and the `calls` block are unchanged.
- 2026-10-31: M9 slice C, fix round: the line's `found` is the answers verified and not the passages answered (`coverlines.FLAG`).
- 2026-10-30: M9 slice B: this step writes its notes through `stagenote`, so a note that names a file or a path from the repository is one line, and a name with a line break cannot pass for a note of its own.
- 2026-10-31: M1 slice A: `back_claude.py` moved to `stages/_shared/` (Sweep uses it too) and is a `textmodel.TextModel`; `pinpoint.Reader` is this step's side of it (the answer cap and the readability check moved from the backend into `Reader.accept`); the option is a backend and a model (`claude-cli:<model>`); `targets` handles a sweep finding with no `p_any`; the report has a `usage` block and the stage a progress line. The first call runs alone now (it did not: calls already running in parallel finished when a login was rejected). The findings of a read are the same.
- 2026-10-31: M1 slice A, fix round: a model name is held to an allowed set (`options.bad_model`), and the stage refuses a bad `WALKDOWN_SOFT_CLAUDE_MODEL` itself when it is the model that will run (a stage run on its own did not).
- 2026-10-31: M1 slice A, fix round: a test holds that no file name is in what a text model is sent here (the prompt never had one); Sweep's text prompt now matches.
- 2026-10-31: M1 slice A, fix round: the `usage` block has `reported` (how many calls reported any token count) and a count has a ceiling of 10^15 (`stages/_shared/specs/shared.SPEC.md`, `usage`); the tokens of an error reply from the CLI are counted; the note says `(from 5 of 9 calls)` for a partial total.
- 2026-10-31: M1 slice A, fix round: the model a service names reaches the result only if it passes the model-name rule (a `<script>` tag, a link, or a line break in it left the record before this).
- 2026-11-01: M1 slice A, before merge: the status line no longer names API backends that follow: those backends are on hold (the owner, 2026-11-01).
- 2026-11-01: a flagged line is left out (the owner: a blank at its place, over `SECRET_MASK`). The question held the passage's lines as the file has them, so a flagged key reached the model and the input and answers files. The stage reads `02.4-phrases.json` too (`reads` in `stages/stages.json`), and a passage that was never going to have text is no longer asked about.
- 2026-11-01: a name the scan leaves out is a file it did not read (`stages/_shared/specs/shared.SPEC.md`, `secretmask`), and the note says "1 line" for one line.
- 2026-11-01: the scan reads build files now, so a file named like one goes by its rows (`stages/_shared/specs/shared.SPEC.md`, `secretmask`).
