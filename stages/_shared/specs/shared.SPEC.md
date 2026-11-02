# shared: spec

One spec for the `_shared` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. Merged from the per-script specs in restructure step 8a.

## audience

The audience tag on every `02.4-phrases` finding: who a line is addressed to, decided
by the file's path (METHOD "Audience tag", THREATS 19, the phrases spec, "The stage", "Findings"). The
tag describes the file, never the reader's intent.

Moved from `02.4-phrases` to `stages/_shared/` in restructure step 4 (no behavior changed): `02.4-phrases`,
`02.5-capability`, the builder step, `03-sweep`'s chunker, and the report all ask this one rule, and no step
imports another step's module for it.

### Inputs

- `rel`: the file's path relative to the input, forward slashes.
- `scripts`: the set of paths `02.1-inventory` counts as scripts (`inv.pin`
  `script_languages`, which covers extensionless files with a `#!` line).
- `hook_configs`: the set of paths `02.1-inventory` marks as hook configs (`inv.file`
  `entry_point` `hook-config`, or any file carrying a `struct.hooks` finding).

### Outputs

`audience(rel, scripts=(), hook_configs=()) -> str`, the first rule that holds:

1. `human`: the base name starts with `README`, `INSTALL`, `CONTRIBUTING`,
   `CODE_OF_CONDUCT`, `CHANGELOG`, `CHANGES`, `HISTORY`, `RELEASE-NOTES`,
   `RELEASE_NOTES`, `RELEASES`, `LICENSE`, `LICENCE`, `NOTICE`, `AUTHORS`, or
   `SECURITY` (any case; the second group added 2026-09-29), or a license or notice file by
   another common name (`THIRD_PARTY_NOTICES`, `THIRD-PARTY-NOTICES`, `THIRDPARTYNOTICES`,
   `THIRD_PARTY_LICENSES`, `THIRD-PARTY-LICENSES`, `COPYING`, `COPYRIGHT`, `PATENTS`, `CREDITS`,
   `ATTRIBUTION`, `OFL.`; 2026-10-25, review C43: license text in `THIRD_PARTY_NOTICES.md` was
   the summary's example for two concern kinds), or any folder in the path is `docs` or
   `.github`.
2. `subagent`: any folder in the path is `agents` or `commands`, or the base
   name matches `*prompt*.md` (any case).
3. `tool`: `rel` is in `scripts` or `hook_configs`, or its extension is a script
   extension (`py`, `sh`, `bash`, `zsh`, `js`, `mjs`, `cjs`, `ts`, `ps1`,
   `psm1`, `cmd`, `bat`, `rb`, `pl`).
4. `model`: everything else.

Folders are matched at any depth (`plugin/docs/x.md` is `human`), since
bundles nest plugins.

### Test data (added 2026-10-02)

`is_test_data(rel)`: true when any folder in the path is one of `TEST_DIRS` (test, tests,
__tests__, testdata, test-data, test_data, fixture, fixtures, __fixtures__, __snapshots__,
spec; case-insensitive) or the file name matches `TEST_FILE_GLOBS` (test_*.py, *_test.py,
*_test.go, *.test.*, *.spec.js/ts/mjs/tsx/jsx, conftest.py; fixtures.*, *.fixtures.*,
*.fixture.* added 2026-10-09). `audience` returns `test-data`
for such a path before any other rule. Test-data lines are never instruction lines, frontmatter
included. `02.5-capability` sets test data aside and pairs any test-data file a model-read file
references (`02.5-capability` `stages/02-coded/02.5-capability/specs/capability.SPEC.md`, section `testdata`).

### The sets it is given (added 2026-10-29, restructure step 4)

`inventory_sets(findings) -> (files, scripts, hook_configs)`, from `02.1-inventory`'s findings: the
`inv.file` rows sorted by path; the paths in any `inv.pin` `script_languages`; and the hook configs
(an `inv.file` with `entry_point` `hook-config`, plus every file named by a `struct.hooks`
finding). Written once because `02.4-phrases` and the builder step ask the same rule the same question.

### Must never

- Read the file, or judge who the text is really for.

### Done when (each backed by a test in `tests/test_audience.py`)

1. `README.md`, `docs/setup.md`, `.github/ISSUE_TEMPLATE/bug.md`, `CONTRIBUTING.md`, `INSTALL.txt` are `human`.
2. `agents/reviewer.md`, `commands/go.md`, `skills/x/implementer-prompt.md` are `subagent`.
3. `hooks/session-start` given in `scripts`, `hooks/hooks.json` given in `hook_configs`, and `tools/a.py` are `tool`.
4. `skills/x/SKILL.md` and `notes.md` are `model`.
5. Rule order holds: `docs/agents/x.md` is `human`; `agents/run.py` is `subagent`.
6. `CHANGELOG.md`, `RELEASE-NOTES.md`, `HISTORY.md`, `LICENSE`, `SECURITY.md` are `human` (2026-09-29);
   so are `THIRD_PARTY_NOTICES.md`, `THIRD-PARTY-NOTICES.md`, `COPYING`, `CREDITS.md`, `OFL.txt`
   (2026-10-25), and `references/copy-rules.md` is not.
7. Package, lock, and build configuration files (`BUILD_FILES`, `BUILD_GLOBS`:
   `package.json`, lockfiles, `tsconfig*.json`, `Dockerfile`, ...) are `tool`;
   plugin manifests stay `model` (added 2026-09-29, Case 004). These lists say who reads a file, and do not decide what the secret scan
   reads, which has a list of its own (`secret_scan.LOCK_FILES`; 2026-11-01).
8. Getting-started guides (`DIRECTIONS`, `USAGE`, `QUICKSTART`, `GETTING_STARTED`,
   `TUTORIAL`, `GUIDE`, `HOWTO`, `FAQ`) are `human`; pattern lists (`.gitignore`,
   `.gitattributes`, other ignore files, `CODEOWNERS`, `.gitmodules`) are `tool`
   (added 2026-09-30).
9. `inventory_sets` gives the `inv.file` rows by path, the script paths, and the hook configs, and
   `audience` called with them tags a hook script `tool` that it tags `model` without them
   (`test_inventory_sets`).

## back_claude

M1 slice A (2026-10-31). Moved from `stages/04-pinpoint/` (its spec section was "The Claude Code backend"), since Sweep and Pinpoint
both use it now.

Claude through the Claude Code command, with no tools: a text model (`textmodel.TextModel`). `--sweep claude-cli`,
`--pinpoint claude-cli`, and `claude-cli:<model>` for either. It never logs in, and an error is a skip. Remote: the text of the
passage goes to Anthropic through the person's own login.

### Inputs

`ClaudeCLI(data, model=None, runner=subprocess.run, which=shutil.which, timeout=300, sleep=time.sleep, workers=None)`. `model`: the
model the person named (`--sweep claude-cli:Some-Model`, case kept), else `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`: the option
wins. `workers`: the calls at a time, else `WALKDOWN_SOFT_CLAUDE_WORKERS` when it is a whole number above 0, else 4. One call per
item (`textmodel`: `{"qid", "system", "prompt", "label"}`):

```
claude -p --tools "" --strict-mcp-config --no-session-persistence
       --safe-mode --setting-sources ""
       --output-format json --model <model> --system-prompt <the system text>
```

`--safe-mode` and an empty `--setting-sources` (2026-10-12, an outside audit) keep the user's and any project's settings out of
the call: hooks, CLAUDE.md, skills, plugins, MCP servers. Without them the user's own hooks ran during every read, with the
audited text in the prompt; a live probe showed a CLAUDE.md canary and three hook events getting through. The prompt goes on
stdin, never on the command line. The working directory is a new empty temporary folder, removed afterwards. `command(exe,
system)` builds the command.

### Outputs

`prepare()` looks for `claude` on the path: `claude-cli: not installed` when it is not there (no call is made and none is tried
again). `request(item)`: the command with `<label>` in place of the system text (`label` names where the text is in the data, such
as `softreads.yaml pinpoint.system`) and the prompt that goes on stdin; no key is involved. `call(system, prompt)`: the reply
(`text` is the CLI's `result`, verbatim; `model` the first `modelUsage` key the CLI reports, else its `model`, else none; `usage`
from the CLI's `usage` block: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`, `cache_read_input_tokens`, each only
when it is a count (`usage.count`), and also from an error reply that has the block, since those tokens were spent; `response` the parsed JSON), or a failure: `claude-cli: authentication error` (the output mentions
login, authentication, an API key, or 401; `auth`), `claude-cli: timeout`, `claude-cli: error, exit code <N>` (non-zero exit,
unparseable output, or `is_error`; never the output's own text), `claude-cli: error: <ExceptionClass>` (the program could not be
run). The output is read to tell a rejected login from another error and is then dropped: a failed call's result, stdout, and stderr
can repeat the prompt and the model's words. `cost_usd` adds up the cost the CLI reports.

### Must never

- Log in for the person, or give the model a tool, a setting source, or the working folder of the run.
- Put the passage, a prompt, or a model's answer on a command line, in a skip reason, or in the call log.
- Keep any text of the program's output but in the answers file's `response`.

### Done when (each backed by a test in `tests/test_back_claude.py`)

1. The command holds `-p`, `--tools ""`, `--strict-mcp-config`, `--no-session-persistence`, `--safe-mode`, `--setting-sources ""`,
   `--output-format json`, `--model`, `--system-prompt`; the prompt goes on stdin; the working folder is empty at call time; the
   request names the system text by its label (`test_command_flags_and_stdin`).
2. The model is the one named, then the environment's, then `sonnet`, and keeps its case; the workers come from the environment only
   when it is a whole number above 0 (`test_the_model_is_the_one_named_then_the_environment_then_sonnet`,
   `test_the_workers_come_from_the_environment_when_it_is_a_whole_number_above_0`).
3. Live, opt-in (`WALKDOWN_LIVE_CLAUDE=1`, `test_claude_isolation_live.py`): in a folder with a canary CLAUDE.md and project hooks that
   write marker files, the call without the isolation flags lets the leak through (proof the probe sees one), and the command this
   module builds lets neither through.
4. A missing CLI skips every item without a call and nothing waits; no items make no call and no lookup
   (`test_a_missing_cli_skips_without_a_call`, `test_nothing_to_call_is_not_tried_again_and_nothing_waits`,
   `test_no_questions_means_no_call_and_no_lookup`).
5. A timeout and an error skip only their item; a login rejected again stops the later calls; one rejected once and accepted on the
   retry stops nothing (`test_a_timeout_and_an_error_skip_only_their_question`,
   `test_a_rejected_login_that_is_rejected_again_stops_further_calls`,
   `test_a_login_rejected_once_and_accepted_on_the_retry_stops_nothing`).
6. No text of an error is kept; failures that differ only in what the program said have one reason; a rejected login is a kind and
   an exit code (`test_no_text_of_an_error_is_kept_neither_the_passage_nor_the_prompt_nor_the_models_words`,
   `test_failures_that_differ_only_in_what_the_program_said_have_one_reason`,
   `test_a_rejected_login_is_kept_as_a_kind_and_an_exit_code`,
   `test_the_call_log_row_holds_no_text_of_the_passage_or_the_prompt`).
7. The tokens the CLI reports are added up over every call, a count it does not report is absent, a count that is not a whole number is
   not reported, and a call with no answer is still a call (`test_the_tokens_the_cli_reports_are_added_up_over_every_call`,
   `test_a_count_the_cli_does_not_report_is_absent_and_never_0`, `test_counts_that_are_not_whole_numbers_are_not_reported`,
   `test_a_call_that_got_no_answer_still_counts_as_a_call_sent_and_the_tokens_of_an_unusable_answer_are_kept`).
8. The model that answered reaches the result only if it passes the model-name rule, cut to 80 characters, and a service that names
   none, or one that fails the rule (a `<script>` tag, a link, a line break), leaves the model asked for
   (`test_the_model_that_answered_reaches_the_result_cut_to_the_cap`,
   `test_a_model_name_a_service_reports_is_held_to_the_model_name_rule`,
   `test_a_service_that_names_no_model_leaves_the_one_that_was_asked_for`).

### History

- 2026-10-13: built (owner) in the old soft stage as the pinpoint call of `back_claude.py`.
- 2026-10-29: its own stage, `stages/04-pinpoint/back_claude.py` (restructure step 5), cut down to the pinpoint call.
- 2026-10-30: M9 slice A: a call that gets no answer is tried once more; no text of the program's output is kept (a skip reason is
  `claude-cli: error, exit code <N>`).
- 2026-10-31: M1 slice A: moved here and made a `textmodel.TextModel`. It no longer knows Pinpoint (`pinpoint` and `readable` are gone:
  `ask(items, accept)` takes the step's own check of an answer), takes the model the person named, reports its usage, and Sweep uses
  it too. The first call runs alone (it did not before: calls already running in parallel finished when a login was rejected).

## calllog

M9, slice A (2026-10-30).

A model call that gets no answer is tried once more and logged. The two AI steps (`03-sweep`, `04-pinpoint`)
make one call for each passage. **No answer** is any call that ends without an answer Walkdown can use: an error
from the service or the program (rate limit, network, server error, timeout, a rejected key), or an answer outside
the options or one that cannot be read. This module holds the part both steps share: the second try, the record
of what happened, the call log, and the `calls` block of the step's report. What counts as an error, the wait,
and the key are each backend's (`stages/03-sweep/back_jev.py`, `stages/_shared/back_claude.py`); the rest of what the
backends do alike (the first call alone, the stop on a rejected key, the workers, `not sent`) is `textmodel`'s.

### Inputs

- `attempt(try_once, wait, sleep, stopped=lambda: None) -> (answer, failure, tries)`: makes the call by calling
  `try_once()`, which returns `(answer, None)` or `(None, failure)` (`failure(kind, status, reason, auth=False,
  **extra)`: the kind of failure, a status (an HTTP status code for Jev, the program's exit code for the CLI) or None,
  the words the passage is skipped with, whether the service rejected the key, and anything that rides along such as the
  raw response). A failure has no place for the error's own message: it can repeat the passage, the prompt, or the
  model's words, and the Jev SDK's holds an endpoint and a request id. `status_text(status, word)` is `, status 503`
  (or `, exit code 1`) at the end of a reason. A call that gets no answer waits `wait` seconds
  (`sleep(wait)`; `retry_wait` in `Library/softreads.yaml`, 2 seconds, handed in by the backend) and is made once more.
  `stopped()` is asked after the wait: when it returns a reason (a rejected key stopped the later calls), the second
  try is not made. A call is made at most twice. (A backend whose client retries by itself turns that off so this
  holds: the Jev backend builds the SDK's client with `RetryPolicy(max_retries=0)`, `sweep.SPEC.md`.)
- `unsent(why) -> tries`: the record of a passage whose call was never made.
- `rows(results) -> [row]`: the call log from a step's results; `write(path, rows)`; `summary(rows, log) -> dict |
  None`; `notes(rows, log) -> [line]`.

### Outputs

- `attempt` returns the answer (the first try's, or the second's) with `failure` None; or `answer` None and the
  failure that ended the call (the second try's, or the first's when no second try was made); and `tries`, None when
  the first try answered, else `{"first": {"kind", "status"}, "retry": ..., "at"}` with `retry` one of
  `{"result": "answered"}`, `{"result": "no answer", "kind", "status"}`, or `{"result": "not tried", "why"}`. `at` is
  the time (UTC, to the second).
- `unsent(why)` is `{"first": None, "retry": {"result": "not tried", "why": why}, "at"}`: nothing to call (no key,
  the package or the program missing) or the calls had been stopped.
- A backend puts `tries` on the passage's result. **The call log**, `data/<step>.calls.jsonl` (`layout.calls_file`),
  apart from `LOG.md`: one line for each result that has `tries`, in the order of the passages: `qid`, `backend`,
  `first` (the kind of failure and its status, or null for a passage never sent), `retry`, and `at`. It holds no key, no
  passage text, and no error message: its `qid` names the file and line, and the passage is in the step's input file.
  Failures that differ only in what their text said (a request id) are alike in the log and in the skip reasons, which
  is how section 7 counts them as one reason. `write` saves it only when there is a line to write.
- **The `calls` block** of the step's report (a top-level key beside `backends` and `findings`, present only when the
  log has a line): `log` (the file's name, null when the step was run without `--out`), `answered_on_retry` (lines
  whose retry answered), `not_sent` (lines with no first try). How many passages got no answer, and why, is in the
  step's findings (a skip with its reason); `notes` gives the one stderr line: how many answered on the retry, how
  many got no answer after it, how many were not sent, and the call log.

### Must never

- Put a key, a passage, a prompt, a model's answer, or any text of an error in the log, in a skip reason, or in a report.
- Make a third call, or wait more than once for a passage.

### Done when (each backed by a test in `tests/test_calllog.py`)

1. A first try that answers is used, with no wait and no record
   (`test_a_first_try_that_answers_is_used_with_no_wait_and_no_record`).
2. A first try that fails is made again after the wait and the answer is used, with the record of both
   (`test_a_first_try_that_fails_is_tried_once_more_after_the_wait_and_the_answer_is_used`).
3. Two failures end the call with the second try's reason, and a call is never made a third time
   (`test_two_failures_end_the_call_with_the_second_tries_reason_and_both_are_recorded`,
   `test_a_call_is_never_tried_a_third_time`).
4. Calls stopped during the wait mean no second try (`test_calls_stopped_during_the_wait_mean_no_second_try_and_the_first_reason_stands`);
   a rejected key is tried again like any other failure (`test_a_rejected_key_is_tried_again_like_any_other_failure`).
5. A passage never sent has no first try (`test_a_passage_never_sent_has_no_first_try_and_a_retry_that_was_not_tried`).
6. The log has a line for each result with `tries`, in order, with nothing of the request, and is written only when
   there is a line (`test_the_log_has_a_line_for_each_result_with_tries_in_the_order_of_the_results`,
   `test_the_file_is_written_only_when_there_is_a_line`).
7. The report block counts the retries and the passages not sent, and is absent without a line
   (`test_the_report_block_counts_retries_and_unsent_passages_and_is_absent_without_a_line`); a failure keeps a kind
   and a status and has no message (`test_a_failure_keeps_a_kind_and_a_status_and_no_message_of_its_own`); the file is
   named for its step
   (`test_the_call_log_file_is_named_for_its_step`).

### History

- 2026-10-30: M9 slice A: built.
- 2026-10-30: M9 slice A, fix round: the Jev backend turns the SDK's own retries off, so "a call is made at most twice"
  is true (the SDK retried a failed call twice by itself, which made up to six sends of a passage). A failure keeps a
  kind and a status instead of a short message, and `short` and `MESSAGE_CAP` are gone: an error's text can repeat the
  passage, the prompt, or the model's words, and the SDK's holds a request id, so no text of an error is kept. The log's
  `first` and `retry` hold `status` where they held `message`.

## common_lines

M9 slice B, fix round.

Walkdown's own words that the check of the run and the report stage both say. The check words a gap in the brief of a held
run (`stages/05-qa/hold.py`), and the report stage words the same gap on the pages and in section 7 once `continue` has
released the run; a phrase that is the same in both is here once, so the two read alike. Nothing here reads or computes.

### Outputs

- `UNCHECKED`, `NO_FIXTURES`, `unchecked_phrase(result)`: the phrase for a fixture check that gave no verdict (ERROR, SETUP
  ERROR, NOT BUILT, and `no fixture set` on a step that has fixtures): `could not be checked against its fixtures: it gave
  SETUP ERROR` for ERROR and SETUP ERROR, `has no fixtures to be checked against` for NOT BUILT and `no fixture set`. The
  hold's brief and section 7 say `The step "<plain>" <phrase>.`; the pages and the brief name one such step `<plain> <phrase>`.
- `UNCHECKED_MANY`: `{n} steps could not be checked against their fixtures, so a "none" from them is not measured`: several such
  steps are said once, as a count.
- `STOPPED_LINE`: `Stopped after "{plain}", as asked (--until); the steps after it did not run.`, the line the brief of a stopped
  run and the brief of a held run say a stop in.
- `DROPPED_LINE`, `DROPPED_NOTE`, `DROPPED_LOG`, `WAITING_LINE`, `option_text(option, backend)` (second fix round): the words for
  a model read an earlier command chose that did not run at `continue` (section 7, section 6, and the brief; the terminal's note;
  the log's `Soft models:` line) and for a chosen read waiting behind a stop (`Chosen and waiting: ...`), and `--sweep jev`.
- `dropped_how(stage, backends, stopped)`: how to get a dropped read. While the run is stopped, `--sweep jev at continue chooses
  it`. Once it has finished `continue` refuses, so `to read it, audit the repository again with --sweep jev --pinpoint
  claude-cli`, with every read before this one, since a pinpoint needs the sweep.
- `record_option(stage, backend)` and `RECORD_OPTION_UNUSABLE` (M1 slice A, fix round 3): the model option a record kept for a read, as
  a command may carry it, or None. The record is a file a person can edit, and a command is built from its words, so the value is held
  to the rule for the option it stands for (`options.parse_choice`: a backend Walkdown has that reads for this step, a model of the allowed
  characters) and printed in the form the options keep (`options.normal`: `Claude-CLI:Some-Model` is `claude-cli:Some-Model`). A
  value that fails, is not text, or asks for nothing is None. `dropped_how` prints that read's option bare. The brief's go-on command
  leaves such a read's option out and says, in one sentence: `The model option the record kept for "Needs a human read" could not be
  used, so the command to go on leaves it out.` (two reads: `"A" and "B"`).

### Must never

- Import anything or hold a table of steps: the callers bring the step's plain name.

### Done when (each backed by a test in `tests/test_common_lines.py`)

1. The two phrases are these words (`test_the_phrases_the_check_and_the_report_both_say`,
   `test_a_check_with_no_fixtures_is_not_said_to_have_given_a_word`); the hold, section 7, and the lists
   use them and no words of their own
   (`stages/06-report/tests/test_render.py::test_a_fixture_check_that_could_not_be_made_has_its_one_set_of_words_in_section_7_and_the_hold`).

- `UNIT_ONE`, `UNIT_MANY`, `unit_words(n, unit)`, `check_words(checks)`, `COVERAGE_KINDS`, `coverage_gap_text(gap)`,
  `coverage_page_words(gap)` (M9 slice C): the words of the check of the run's coverage gaps, once for the hold's brief and the
  pages. `coverage_gap_text` is one sentence with its full stop: `The check "phrase.remote-load" of the step "What the text asks
  for" looked at 3 of 5 files; 2 are not explained.` (a line of several checks names the first and says `and 13 more that run in
  the same pass`; items explained by skips are said: `looked at 3 of 6 files, with 1 more explained; 2 are not explained.`; a
  broken count: `counted 3 looked at and 2 explained of 3 files: the counts do not add up.`; a `found` that is not what the
  findings hold: `reported 4 found where its findings hold 2: the counts do not add up.`; a line that names a check it does not
  make or names a check twice: `has a coverage line starting with "a.b" that names a check it does not make or names a check twice: "x.y".` (two lines can
  name the same ID, so each is told by its first check); a step
  with no line for some checks: `The step "What this touches" did not say what its check "cap.limit" looked at.`, `... did not say
  what 7 of its 8 checks looked at, starting with "cap.grant".`).
  `coverage_page_words` is the clause for the pages' list of what did not work (`What the text asks for did not look at 2 files
  and does not say why`).

### History

- 2026-10-30: M9 slice B, fix round: built. `qastep.py` is gone, and with it the reason the check's words stood in files
  the phrase step does not import.
- 2026-10-30: M9 slice C: the words of the coverage gaps (above).
- 2026-10-31: M9 slice C, fix round: a step with no line for a check is worded `did not say what its check "..." looked at` (it read
  `has no coverage line for`); the broken-count words for a `found` that is off and for a check ID that is not the step's or is
  named twice.
- 2026-10-31: M1 slice A, fix round 3: `record_option` and `RECORD_OPTION_UNUSABLE`. With `backends` changed in `data/run.json`, a re-render
  printed `--sweep claude-cli:x & echo.INJECTED>marker note: planted` in the command to go on, which SKILL.md tells a model to relay as
  printed. `dropped_how` flattened a value and printed it; it prints only a value that is an option. Tests:
  `stages/06-report/tests/test_brief.py::test_a_model_option_the_record_kept_is_checked_as_an_option_before_it_is_printed`,
  `test_the_brief_of_a_stopped_run_whose_record_was_changed_by_hand_prints_no_planted_word`, and through the report stage
  `test_saved_outputs.py::test_a_run_record_changed_by_hand_cannot_put_words_in_the_command_to_go_on`.

## coverlines

M9 slice C (2026-10-30). Named so that it shares no name with the `coverage` package.

Coverage lines: for every check a step makes, what it looked at and how many it found. A step names its lines once
(`begin(lines)`, `lines` being `[(checks, unit)]`), counts as it works, and writes the list at the end into its report's `coverage`
(`stages/CONTRACT.md`, "Coverage lines"). The counters are the process's: each step runs as its own process, and a function that
counts while no step has begun, or for a key that is not one of the lines begun, counts nothing.

### Outputs

- `begin(lines)`, `end()`, `key_of(checks)` (a line's key is its first check), `of(key, n)`, `look(key, n)`, `explain(key, n)`.
  `of` is how many items the check should look at, counted from the inputs before the check runs and outside the function that
  makes the check; `look` is counted inside that function, where it handles an item; `explain` is counted where a reason is written
  for an item not looked at (a skip finding, an unread or unscanned finding, a "not scanned" entry). `of` and `look` come from
  different places, so a check that skips an item without saying so leaves `look` plus `explain` short of `of`, and the whole check being
  left out leaves `look` at 0 against an `of` that was counted outside it.
- `lines(findings)`: the `coverage` list, one line per line begun, `found` counted from `findings` by `found_in` (below); it ends
  the counting. `UNITS`: `files`, `entries`, `uses`, `passages`, `findings`, `legs`, `grants`, `run`.
- `is_result(finding)`, `found_in(checks, findings)`, `FLAG`: what `found` counts. A finding with `skipped` is no result. A model
  read answers every passage it is asked about, so its `found` is its flags: `flagged` for `soft.sweep` and `verified` for
  `soft.pinpoint` (`FLAG`), and an answer that flags nothing is a read with no result.
- `valid_id(c)`, `valid_line(line)`, `valid(saved)`, `whole(n)`, `saved_lines(report)`: whether a saved list is a list of lines
  whose check IDs are words with no white space in them (a line break in an ID would start a line of a hold's brief with words
  the repository chose), whose unit is a known one, and whose counts are whole; and the lines of a report that
  `pipeline.read_report` accepted (none for a report made before the lines).
- `audit(checks, report)`: what is wrong with a report's coverage, as data, for the check of the run and for the tests, so the
  rules are stated once: `missing` (the IDs on the step's list that no line names), `off_list` (the checks of the report's findings,
  skips included, that are not on the list; an ID with white space is shown by `UNNAMED`), and `lines` (each defective line with its
  `reasons`: `check` for an ID that is not on the list, is another step's, or is named by two lines, with the `ids`; `short`;
  `over`; `found`).
- `problems(checks, report)`: the same, as sentences; each step's tests assert it is empty: the lines cover exactly the step's
  checks, each in one line; every unit is a known one; `looked_at` plus `explained` is `of`, neither more nor less; `found` is the
  results among the findings of the line's checks; and every finding's check, a skip's too, is on the list.

### Must never

- Hold a file name or a text from the repository in a line, or count in a step that did not begin.
- Import a stage's code.

### Done when (each backed by a test in `tests/test_coverlines.py`)

1. A line counts what a check is to look at, handled, and explained, and `found` from the findings, a skip excepted
   (`test_a_line_counts_what_a_check_is_to_look_at_what_it_handled_and_what_is_explained`).
2. Nothing is counted when no step has begun or for a key that is not a line, and `lines` ends the counting
   (`test_nothing_is_counted_while_no_step_has_begun_and_a_key_that_is_not_a_line_counts_nothing`,
   `test_the_lines_end_the_counting_so_the_next_step_starts_from_nothing`).
3. A saved list is valid only as a list of lines with a known unit, check IDs with no white space, and whole counts
   (`test_a_saved_list_is_valid_only_when_it_is_a_list_of_lines_with_whole_counts`,
   `test_an_id_with_white_space_in_it_cannot_start_a_line_of_a_hold`), and `pipeline.read_report` refuses one that
   is not, bar the old reader's object (`test_pipeline_reads_a_report_with_a_bad_coverage_as_one_that_cannot_be_read`).
4. `problems` says what is wrong with a step's coverage (`test_problems_says_what_is_wrong_with_the_coverage_of_a_step_that_went_well`,
   `test_a_finding_whose_check_is_not_on_the_steps_list_is_a_problem_a_skip_too`), `found` is a result count and a read's is its
   flags (`test_found_is_the_results_of_a_check_and_for_a_model_read_the_flags`), and `audit` gives the same as data
   (`test_the_audit_names_what_is_wrong_as_data_for_the_check_of_the_run`).

### History

- 2026-10-30: M9 slice C: built.
- 2026-10-31: M9 slice C, last fix round: a new unit, `uses` (said "program uses" in `common_lines.UNIT_ONE` and `UNIT_MANY`).
  `validate.Stamp.measured` reads a count that is not `passed/total` as not measured, with no traceback (`abc`, `3`, `3/x`).
- 2026-10-31: M9 slice C, fix round: `found` is the results among the findings (a read's flags); a unit and an ID that cannot be
  read make the list invalid; `audit` states the rules for the check of the run once; a finding's check that is not on the step's
  list is a problem.

## earlier_steps

Restructure step 7.

A stage run on its own gets the earlier steps it reads run for it, here, in one place. (A run through
`walkdown.py` hands each stage the saved outputs it needs, so none of this runs. The grader runs each
stage on its fixtures by itself, and so do tests.) It replaces the five copies the stages kept: the
`load_inventory` of `02.3-graph` and `02.4-phrases`, `02.5-capability/inputs.py`, `02.6-builder/earlier.py`,
and `03-sweep/runstages.py` (notes O4).

### Inputs

- `run_before(stage, input_dir, work_dir, python=None, stages_dir=None) -> {step name: report}`: runs the steps
  `stage` reads (`stages.json`, `reads`), in order, as subprocesses, into `work_dir` with
  `pipeline.run_stages(..., alone=True)`. Each report is saved as `<work_dir>/<name>.json`, its messages as
  `<name>.notes.txt`, and `graph.json` lands beside them. A stage that reads nothing runs nothing.
- `inventory(stage, input_dir, saved=None, python=None, stages_dir=None) -> dict`: the inventory report for a
  stage that reads only that: the file `saved` (`--inventory`) when given, else the inventory step run in a
  temporary folder that is removed afterwards.

### Behavior

- The arguments are the ones the copies always gave: the inventory and the reader get the input folder; the
  graph gets `--inventory <work>/02.1-inventory.json --out <work>`; the phrases step gets `--inventory` and
  neither `--out` nor `--normalized`; the capability step gets `--reports <work>`. The pipeline gives its own
  steps `--out` and `--normalized` as well (`pipeline._args(alone=False)`); a stage on its own never did, and the
  grader's results depend on it.
- The first step that fails (a non-zero exit, or output that is not JSON) stops the rest; `StepFailed` names
  the step and why. `inventory` raises `ValueError("cannot read --inventory ...")` for a saved file it cannot read.
- The caller checks the saved reports against the contract when it reads them (each stage's `load_dir`).

### Must never

- Import a stage's code, or write inside `input_dir`.
- Run an AI stage: only the steps `reads` lists.

### Done when (each backed by a test in `tests/test_earlier_steps.py`)

1. The steps run in order with those arguments, and the reports and `graph.json` are saved
   (`test_the_steps_run_in_order_with_the_arguments_a_stage_on_its_own_always_gave_them`); a stage reads what
   `stages.json` says and a stage that reads nothing runs nothing (`test_a_stage_reads_what_stages_json_says_and_nothing_else`).
2. Runners are found through `stages.json` (`test_runners_are_found_through_stages_json`).
3. A failing step, or one that prints no report, raises `StepFailed` naming it, and the later steps do not run
   (`test_a_failing_step_raises_step_failed_naming_it_and_the_rest_do_not_run`,
   `test_a_step_that_prints_no_valid_report_is_a_failure`).
4. `inventory` reads a saved report or runs the step (`test_inventory_reads_a_saved_report_or_runs_the_step`).
5. The real list gives each stage the steps it ran on its own before
   (`test_the_real_list_gives_each_stage_the_steps_it_ran_on_its_own_before`); the grader's results are the same
   row for row (checked by `tools/grader/grader.py all`).

### History

- 2026-10-29: restructure step 7: built, in place of the five copies. A step's failure message now reads
  `<name> failed (exit N: <the last 500 characters of its messages>)`; the copies kept 1500 or 2000 characters.

## jevkey

The loaded-model build (2026-11-01). `read_key` moved here from `stages/03-sweep/back_jev.py`, so the code that decides what
`--reads` runs (`options`) can ask whether Jev is available without importing a stage. `back_jev.read_key` is this function, under
its old name and with its old behaviour.

Jev's key, and whether Jev is available. The key is read in the process that asks, never printed, logged, or stored.

### Outputs

- `KEY_NAME`: `TYPESAFE_API_KEY`.
- `read_key(environ=None, registry=None) -> str | None`: the key from the environment, else from the user environment in the
  Windows registry (`HKCU\Environment`, read in the process; `registry` is a callable standing in for it in tests); `None` when
  neither has it, or the registry cannot be read. It returns the key to the one caller that sends with it (`back_jev`).
- `has_key(environ=None, registry=None) -> bool`: whether `read_key` finds a key. It returns `True` or `False` and nothing else.
- `sdk_found() -> bool`: whether the package `typesafe_sdk` is there to be imported, asked of the import system
  (`importlib.util.find_spec`) and never by importing it. A module already in `sys.modules` counts as found; a `None` entry there
  (an import that is blocked) counts as not found.
- `available(environ=None, registry=None, sdk=sdk_found) -> bool`: Jev is available when the package is found and there is a key.
  The package is asked first, so no key is read on a machine without it. It returns `True` or `False` and nothing else.

### Must never

- Send anything, import `typesafe_sdk`, or make a client: the check is a question about the machine.
- Print, log, return, or store the key, in whole or in part. `has_key` and `available` return a `bool`, a note about them names no
  key, and the key appears in no output and no file of a run.

### Done when (each backed by a test in `tests/test_jevkey.py`)

1. `read_key` is the one function: `back_jev.read_key` is `jevkey.read_key`, and its existing tests hold
   (`test_back_jev_reads_its_key_through_jevkey`; `test_read_key_prefers_the_environment_then_the_registry` in the sweep's tests). With
   no registry given it asks this module's registry reader and returns its value, the environment first
   (`test_read_key_asks_the_registry_by_default_and_returns_its_value`; the real registry is never touched). The reader asks the user's
   environment for the key by name, shown on a stand-in for `winreg`
   (`test_the_registry_reader_asks_the_users_environment_for_the_key_by_name`).
2. `has_key` and `available` return `True` or `False`, never a key (`test_has_key_and_available_return_a_bool_and_never_the_key`),
   and a planted key is in no output of the call (`test_the_key_is_in_no_output_of_the_check`).
3. Jev is available only with the package and a key: each of the four cases (`test_available_needs_the_package_and_a_key`). The package
   is asked first: with none, neither the environment nor the registry is looked at, shown by a registry stand-in that records and does
   not raise (`read_key` swallows what a registry raises, so one that raises proves nothing)
   (`test_the_package_is_asked_before_the_key_is_read`).
4. The package is looked for and never imported, even when the key is there
   (`test_the_package_is_looked_for_and_never_imported`); a module already imported counts, and a blocked import does not
   (`test_a_module_already_imported_counts_and_a_blocked_import_does_not`); a package that is nowhere is not found
   (`test_a_package_that_is_nowhere_is_not_found`).

### History

- 2026-11-01: the loaded-model build: built. `read_key` and the registry read moved from `back_jev.py`; `has_key`, `sdk_found`, and
  `available` are new.
- 2026-11-01: the loaded-model build, fix round: two rules had no test that failed when they broke, and have one now: `read_key` asks the
  registry when none is given, and `available` asks the package before the key.
- 2026-11-01: the loaded-model build, before merge: the reader of the registry is tested on a stand-in for `winreg` (it had no test of what it asks for).

## layout

Where things live in a run folder, in one place, so the runner, the report stage, and the front door's
brief agree. One layout (restructure step 7, notes O5): there is no second one to handle.

### Layout

```
RepoResults/<repo>/<date>_<hash7>/
  summary.html  details.html  review.html  full.md    the reports (report.SPEC.md, The reports)
  brief.md                      the brief the front door prints (report.SPEC.md, brief)
  changes.md                    what changed since the previous run, when there is one
  marks.json                    the reader's marks, once saved
  LOG.md                        what ran, each step's validation stamp (written once by the report stage)
  data/                         everything else: stage outputs and working files, run.json (the record),
                                limits.md (what the run did not examine)
```

`REPORTS` names the four reports; `BRIEF`, `CHANGES`, `LIMITS`, and `RECORD` the brief, the changes file, the limits file,
and the record;
`RETIRED` the pages runs wrote before 2026-10-20 (`summary.md`, `summary-v1.html`), which a re-render removes.

### Outputs

- `data_dir(run_dir)`: `data/`. `report_dir(run_dir)`: the run folder. `input_file(stage)`: `<stage>.input.jsonl`, what an
  AI step would send (O3: written by itself when a run stops just before the step). `calls_file(stage)`:
  `<stage>.calls.jsonl`, the call log of an AI step (M9: one line for each passage whose call got no answer on its first
  try or was not sent; written only when there is a line).
- Whether a run was made before this version is not the layout's to say either: it takes the record and its
  format (`record.made_before`; the `record` section). The report stage does not re-render such a run; it says so in
  one plain line (`stages/06-report/specs/report.SPEC.md`, section `run`).
- Which run came before this one is not the layout's to say: it takes the runs' times, which are in the record
  (`record.earlier_runs`, `record.previous_run`; the `record` section).

### Must never

- Read a run made before this version, or move or rewrite an existing run's files, apart from removing the
  retired pages.
- Know a second layout. (`drift.predates_rename` recognizes an old run in order to call it not comparable; it
  reads nothing from it.)

### Done when (each backed by a test in `tests/test_layout.py`)

1. There is one layout (`test_one_layout`); it holds no rule for a run made before this version
   (`test_the_layout_has_no_rule_for_a_run_made_before_this_version`).
2. The layout has no rule for the previous run (`test_which_run_came_before_is_the_records_to_say_and_not_the_layouts`).
3. A run has exactly its reports, `brief.md`, `LOG.md`, and `data/` at the top
   (`stages/_shared/tests/test_runner.py::test_run_folder_and_documents`).

### History

- 2026-10-02: built: reports at the top, `data/` below.
- 2026-10-16: `summary-v1.html` beside report v2.
- 2026-10-20: owner: `details.html`; `summary.md` and `summary-v1.html` retired.
- 2026-10-29: restructure step 7: moved from `stages/05-report/` to `stages/_shared/`; one layout (the old one, with
  the stage outputs at the top and the reports in `report/`, is gone; `is_new` with it); `made_before` and the
  names of the brief, the limits file, and the record added. (Round 2: the rule for the previous run, first put
  here by name, is `record.py`'s and goes by time.)
- 2026-10-29: restructure step 7b: `made_before` moved to `record.py`, which has the format of the record: a run is
  "made before this version" when its record is missing or of an older format, not only when the file is missing.
- 2026-10-30: O3: `input_file(stage)`.
- 2026-10-30: M9 slice A: `calls_file(stage)`.

## library

How a stage finds and reads a file in `Library/` (the folder at the repository root that holds the
tables, lists, and sources Walkdown looks things up in; `Library/README.md`). The one place that
knows where the Library is. It is code, so it lives here in `stages/_shared/` and not in the Library,
which holds no code.

### Inputs

A plain file name: `fit.yaml`, `baserates.json`. A name with a folder in it (`a/b.yaml`,
`../x`) is refused: the Library has no sub-folders.

### Outputs

- `ROOT`, `LIBRARY`: the repository root (two folders above `stages/_shared/`) and its `Library/`.
- `path(name) -> Path`: the file's path. `LibraryError` (a `ValueError`) for a name that is not a
  plain file name.
- `load_yaml(name)`, `load_json(name)`: the file read as UTF-8 and parsed (`yaml.safe_load`,
  `json.loads`). Not cached: a caller may change what it gets. A missing file raises
  `FileNotFoundError`, as a stage's own read of a missing table always did.
- `invisible() -> Invisible`: the invisible-character list (`Library/invisible.yaml`), parsed once
  per process (`lru_cache`):
  - `strip`: the characters taken out of text (action `strip`);
  - `space`: the characters each turned into one space (action `space`);
  - `run`: the characters taken out and reported only where `run_length` or more stand in a run, in a
    row or with only `strip` characters between them (action `run`: the variation selectors);
  - `kind`: character to the kind `02.2-reader` reports, for every character that has one (in `strip`
    or `run`; a `run` character is reported only inside a run);
  - `kind_order`: the order kinds are joined in a finding's carrier;
  - `run_length`: how many `run` characters make a run (2), written once, in the file;
  - `run_re`: a compiled pattern for one run, built from `run`, `strip`, and `run_length`: a `run`
    character, then `run_length` minus one more, each after any number of `strip` characters (None
    when no character has action `run`).
- `runs(text) -> list[Run]`: every run in `text`, in order, as `Run(start, end, text)`: a slice of
  the line from the run's first `run` character to its last (the `strip` characters between them
  inside it), and what its `run` characters spell, or None. `run_length` or more characters of `run`,
  whichever of them (a selector from one block next to one from another is one run), in a row or with
  only `strip` characters between them: a zero-width space between two selectors does not break the
  run, and a visible character, a space, or a line separator does. One alone is not a run, even with
  a `strip` character after it. ASCII text has none. This is the one run finder: no stage keeps its
  own. The text a run spells is read from its `run` characters alone.
- `run_text(run) -> str | None`: what a run of variation selectors spells. U+FE00 to U+FE0F are the
  bytes 0 to 15 and U+E0100 to U+E01EF the bytes 16 to 255; the text is decoded from those byte
  selectors alone and returned when the bytes are UTF-8 of printable characters (and `\t\n\r`) with a
  word of two letters or more. Any other character of the run (a Mongolian free variation selector,
  which carries no byte) is skipped, as the `strip` characters between selectors are, so one of them
  among the byte selectors hides nothing. A run of Mongolian selectors only has no bytes and spells
  nothing, and neither do bytes that are not such text: None. The byte rule lives in the code, as the
  tag-character rule does, because it says what a selector means; the file says which characters are
  listed.
- `replace_runs(text, spell=False) -> str`: `text` with the `run` characters of each run taken out.
  The `strip` characters between them stay where they are, for the caller's own strip and, in
  02.4-phrases and 02.5-capability, so a tag run among them is still read. With `spell`, a run that
  spells text puts it at the run's start with a space on each side and its white space collapsed to
  single spaces (the line stays one line), as a run of tag characters is read; a run that spells
  nothing leaves nothing.
- `read_hidden(text) -> str`: `text` with what it hides written out, a space on each side of each: first
  `replace_runs(text, spell=True)`, then each run of tag characters U+E0020 to U+E007E as the ASCII it
  spells (each minus U+E0000). The `strip` characters stay, for the caller's own strip. This is the one
  place the tag rule is written: no stage keeps its own.
- `tag_texts(text) -> list[str]`: what each run of tag characters spells, in order. It finds them where
  `read_hidden` does, after `replace_runs(text, spell=True)`, so a tag character between the selectors of
  a run joins the ones beside it ("open"; it read "o p e n" in `02.2-reader` until 2026-11-01).

`invisible.yaml` is a `run_length`, a `kind_order`, and a list of `ranges`, each with `name`, `from`
and `to` (code points written `U+XXXX`, at least four hex digits, both ends included), `action`
(`strip`, `space`, or `run`), an optional `kind` (one of the file's `kind_order`; none for `space`),
`added` (a date), `source`, and `note`. It is refused with `LibraryError` when a code point is badly
written, `from` is after `to`, the action or the kind is not one the file allows, a `space` entry has a
kind, one character is listed twice, or `run_length` is missing or below 2 when a range has action
`run`. (`detect`, the action of U+180E before 2026-10-29, is gone.)

How a stage uses it:

- 02.2-reader (`fold.py`): `STRIP` is `strip`, `SEPARATORS` is `space`, `KIND_ORDER` is
  `kind_order`; `_kind(ch)` is `kind.get(ch)`; the characters of a run (`runs`) are stripped and
  reported; `decoded` is what the tag runs spell (`tag_texts`), then what the runs spell.
- 02.3-graph (`invisible.py`): `STRIP` is `strip` as a `str.translate` table (to nothing), after
  `replace_runs`. It does not turn the separators into a space and never did.
- 02.4-phrases (`foldtext.py`): `_TABLE` is `strip` (to nothing) and `space` (to one space); a line goes
  through `read_hidden` first. `termset.py` hashes the list (each code point and its action, and
  `run_length`) into `terms.code`.
- 02.5-capability (`pairs._plain`): `read_hidden`, then drops `strip`.
- 06-report (`details_html._fold_kind`): a code point in `strip` or `run` is "invisible characters"
  before the category rules. A `space` character (U+2028, U+2029, U+0085) keeps the classification it
  had: U+2028 and U+2029 are not invisible characters there, and U+0085 is by its category (Cc).
  `render.tag_text` is `tag_texts`, each run joined by a space.

A stage puts `stages/_shared` on `sys.path` itself before `import library`, as the stages do for each
other's modules (they run as scripts, and the tests import them by folder).

### Must never

- Hold or load code from the Library, or build a path into it for a stage (a stage asks `path`).
- Change what a stage read before the files moved: the bytes of every table, and each stage's set of
  invisible characters, are as they were.
- Cache `load_yaml` or `load_json` (the callers get their own copy).

### Done when (each backed by a test in `tests/`)

1. `ROOT` and `LIBRARY` point at the repository root and its `Library/`; `path` refuses a name with a
   folder in it (`test_library.py`).
2. Each of the 11 moved files loads through `load_yaml` or `load_json` to what a direct read gives
   (`test_library.py`).
3. No `.yaml`, `.yml` or `.json` file is left under `stages/` but `stages.json`; the Library holds
   no code and no sub-folder (`test_library.py`).
4. `invisible()` reads ranges, actions, and kinds; each bad entry is refused with a clear message
   (`test_library.py`).
5. Each step's invisible-character set is what it was, plus the P1 ranges: every one of the 150
   characters held before is handled as before (U+180E aside: detected under `tag-chars` and never
   stripped, then stripped as `zero-width`), and the list has 181 characters to strip, three
   separators, and 260 that strip in a run (a character alone is kept and not reported by all three
   fold steps), with the kind of every code point (`test_invisible_sets.py`). Every assigned code
   point with the Unicode property Default_Ignorable_Code_Point (source `S19`, read through the `regex`
   package) is in the list, and a range cites `S19` exactly when its code points have the property
   (`test_invisible_sets.py`). No fold step, `pairs.py`, or `details_html.py` keeps a copy of the list or
   the run rule (`test_the_stages_keep_no_copy_of_the_list`).
6. `runs`, `run_text`, and `replace_runs` find a run of two or more `run` characters (the length is the
   file's) in a row or with only `strip` characters between them, read the bytes of the selectors alone as
   text only when they are UTF-8 of printable characters with a word of two letters or more, skip a
   Mongolian selector among them and treat a run of Mongolian selectors only as spelling nothing
   (`test_a_mongolian_selector_among_byte_selectors_hides_no_text`,
   `test_a_run_of_mongolian_selectors_only_spells_nothing`), keep a spelled line one line, leave the `strip` characters that
   stood between the selectors in place, and do not count one selector with a `strip` character after
   it, or two with a visible character or a line separator between them, as a run
   (`test_library.py`: `test_selectors_separated_only_by_stripped_characters_are_one_run`,
   `test_one_selector_is_not_a_run_whatever_follows_it`); the file is refused without a good
   `run_length` (`test_library.py`).
7. `Library/README.md` has one row for every data file and for `PHRASES.md` and `THREATS.md`;
   `Library/SOURCES.md` lists the 19 outside sources (18 links, and RFC 2606 named without one) and
   Walkdown's own documents (the two public ones; each other one says whether it is in the
   repository, as a stage's `CONTEXT.md` and spec files are, or not published, as `pre-planning/`
   files and the removed tool are); no table
   holds a link; every `source` and `sources` value in a table is a `SOURCES.md` ID or a heading of
   `PHRASES.md` or `THREATS.md`; each entry in the two documents names exactly the pattern rows that
   cite it (`test_library_docs.py`).
8. `read_hidden` and `tag_texts` read the same runs of tag characters, a tag character between selectors
   joins the ones beside it, a run that spells text parts two tag runs in both, and no script under `stages/`
   but `library.py` writes the decode (`test_tag_characters_are_read_once_here`,
   `test_a_tag_character_between_variation_selectors_joins_the_ones_beside_it`, `test_the_tag_decode_is_written_once`).

### History

- 2026-10-29, restructure step 3: written with `Library/`. The 11 data files moved from the stage
  folders with `git mv` (bytes unchanged); the three stages' copies of the invisible-character list
  became `Library/invisible.yaml`. `validate.py`'s fingerprint gained `Library`
  (the `validate` section).
- 2026-10-29, restructure step 3b: the tables that change when a new issue comes up moved in:
  `capability.yaml` (stage 5's rules, from `rules.py`), a `plain` field on every row of
  `patterns.yaml` (from `plain.py`), and the words under each kind of place (`render.py`, `glance.py`)
  into `tools.yaml`, `hosts.yaml`, `trigger.yaml`, `clean.yaml`, and `fit.yaml`. Every `source` is now
  an ID from `SOURCES.md` or a section of `PHRASES.md` or `THREATS.md`, two new public documents in the
  Library; no table holds a link. `library.py` did not change.
- 2026-10-29, restructure step 3b, round 2: `SOURCES.md` says where each Walkdown document lives (a
  stage's `CONTEXT.md` and spec files are in the repository and ship; `pre-planning/` files and the
  removed tool are not published), instead of calling them all internal and unpublished. Two reasons
  kept under `*_source` keys in `softreads.yaml` are prose, not references, and stay as written.
- 2026-10-29 (P1, the invisible-character fix): `Library/invisible.yaml` gained the characters an outside
  note (2026-10-28) and the measurement the same day found (181 to strip, from 150), the `run` action
  (260 variation selectors, stripped and reported only in a run of two or more) with `run_length`, and
  the kinds `filler` and `variation-selectors`; the `detect` action went with U+180E, which is stripped
  as `zero-width`. `library.py` gained `Run`, `run_text`, `runs`, and `replace_runs`, and the
  `Invisible` fields `run`, `run_length`, and `run_re`. `SOURCES.md` gained `S19`.
- 2026-10-29 (P1, review before verification): a run is `run_length` or more `run` characters in a row or
  with only `strip` characters between them (it had been in a row only, so a zero-width space between
  two selectors ended the run and hid the text they spell). `run_re` takes `strip` into account;
  `runs` reads what a run spells from its selectors alone; `replace_runs` takes out the selectors and
  leaves the characters between them for the caller's strip (and for a tag run among them to be read).
  `details_html._fold_kind` treats `strip` and `run` characters as invisible and leaves the `space`
  characters in their category.
- 2026-10-29 (P1, after verification): `run_text` decodes a run's text from its byte selectors alone and
  skips a Mongolian selector among them (it returned None for any run holding one, so a single U+180B
  inside a run hid an instruction from 02.2, 02.4, and 02.5). A run of Mongolian selectors only still
  spells nothing.
- 2026-11-01: `read_hidden` and `tag_texts`: the tag-run decode was written in four places (`fold.py`, `foldtext.py`, `pairs.py`, `render.py`), and two of them read a tag character between selectors differently.

## limitnote

M9 slice B.

Which of a step's messages (`data/<step>.notes.txt`) name something the run did not examine. The check of the run
(`05-qa`) keeps the messages that match as limits of the run (`qa.limit`, kind `note`); the report stage's list of what
was not checked (`render.glance`) picks from the same messages. They share this pattern, so a message is a limit to both
or to neither. It was `render.LIMIT_NOTE`.

### Outputs

`LIMIT_NOTE`: a case-insensitive pattern for `limit`, `absent`, `not installed`, `not scanned`, `not built`, `incomplete`,
`skipped`, `unknown`, `not examined`, `not run`, and `carried forward`.

### Must never

- Import a stage.

### Done when (each backed by a test in `tests/test_limitnote.py`)

1. A message that names something not examined matches, in any letter case
   (`test_a_message_that_names_something_not_examined_is_a_limit_note`).
2. A message that names none does not, among them a step's own count of calls
   (`test_a_message_that_names_none_is_not`).

### History

- 2026-10-30: M9 slice B: moved here from `stages/06-report/render.py`, with the pattern unchanged.

## linetext

The original lines of the files under review, as the AI stages show them. Moved here from the soft
stage's `packet.py` (`Lines`, restructure step 5): `03-sweep` cuts passages from these lines and
`04-pinpoint` numbers a passage's lines for the second model, and both must read a file the same way.
(`readtext.py` is the coded stages' reader and reads by other rules; this one is the AI stages', and
reads what `02.1-inventory` recorded.) A module here imports no stage.

### Inputs

`Lines(input_dir, inventory)`: the folder under review (read-only) and `02.1-inventory`'s report (or None).

### Outputs

`Lines.lines(rel)`: the lines of the file `rel` under the folder, or None. The bytes are decoded with the
encoding `02.1-inventory` recorded for the file (`inv.file` `encoding`; utf-8 when absent or not a known codec);
a BOM (UTF-8, UTF-16 LE/BE, UTF-32 LE/BE) picks the codec and is dropped; undecodable bytes are
replaced, never an error. Lines are split on `\n` only (not on U+2028, U+2029, form feed, or other
characters Python's `splitlines` treats as breaks), one trailing `\r` removed from each, and a final
empty piece after a trailing newline is not a line. Line `i` of the result is line `i + 1` of the file.
A path outside the folder (`..`), a missing or unreadable file, an empty name, or None gives None. A file
is read once and cached.

### Must never

- Read outside the input folder, write anything, or follow a path out of it.

### Done when (each backed by a test in `stages/_shared/tests/test_linetext.py`)

1. A file is decoded with the recorded encoding; a BOM picks the codec and is dropped
   (`test_a_file_is_decoded_with_the_encoding_stage_one_recorded`).
2. An unknown or missing encoding reads as utf-8, and bad bytes are replaced
   (`test_an_unknown_or_missing_encoding_reads_as_utf8_and_bad_bytes_are_replaced`).
3. Lines split on line feed only, with one carriage return removed
   (`test_lines_split_on_line_feed_only_with_one_carriage_return_removed`).
4. A path outside the input or unreadable reads nothing
   (`test_a_path_outside_the_input_or_unreadable_reads_nothing`).
5. A file is read once (`test_a_file_is_read_once`).

## options

Restructure step 7.

What a person asked for, read in one place. The model options share one rule for "asks for nothing",
so the chosen-stage rule and the refusal rule agree (notes M14 a).

### Outputs

- `OFF`: `""`, `none`, `0`, `false`, `no`, `off`. `is_off(value)`: the value (None counts as empty), stripped
  and in any case, is one of them.
- `ai_chosen(stage, soft, environ)`: whether the AI stage was chosen: its option (`soft["sweep"]`,
  `soft["pinpoint"]`), else its environment variable, with a value that is not off. An option that has a value
  wins, even when that value is off (`--sweep none` and `--sweep off` stand over `WALKDOWN_SOFT_SWEEP=jev`). An empty
  option (`--sweep ""`) is no option: the variable decides, as it did on main.
- `refusal(chosen, environ)`: the message for the first parked option the person gave (`--label`,
  `--compare`, `--relational`, `--both`) whose value is not off, then for each parked environment variable
  (`WALKDOWN_SOFT_LABEL`, `_COMPARE`, `_RELATIONAL`, `_BOTH`) that is not off: `<option or variable> is not
  available in this version: labeling is being rebuilt`. The flags are checked first. Said before anything runs.

- The declarations (restructure step 7, notes F3): `add_run_options(ap, developer=False)` adds the target, `--name`,
  `--fresh`, `--keep`, one option for each AI stage in `stages.json` (`--sweep`, `--pinpoint`, with the stage's `help`),
  the parked options (hidden, to be refused), `--revalidate`, and the report options; `developer` adds `--repo`,
  `--results`, `--date`, and `--no-validate`, which only the runner's own command line takes.
  `add_report_options(ap)` adds `--context` and `--hosts`; the report stage declares just those two, with this function.
  `check(a)` runs before anything does: the refusal, then `--hosts` and `--context` read (`parse_hosts`, which needs the
  Library's host table, read only then; `parse_context`: `32k`, `200k`, `8192`, `8k`, `1m`), replacing the typed
  strings with a list of host names and a token count. It returns the message to print (`error: ...`, exit 2) or None.
  `DEFAULT_CONTEXT` is 32,000. Importing the module needs no package, so `--help` and `--version` work without one.
- `ai_choice(stage, soft, environ)` (O3): the backend chosen for an AI stage as the stage reads it (stripped, in lower
  case), or `""` when nothing was chosen, by the rule above; `ai_chosen` is whether it is not empty. The record keeps
  the backend that wrote an input file, and the stop's brief names it.
- `--until` (O3, `add_until_option`; the run and `continue` both take it): stop after a step. `until_names()` maps every
  way to name a step to the step, built from `stages/stages.json` and nothing else: the step's name (`02.4-phrases`),
  its number (`02.4`), its word (`phrases`), and, for the steps that share a folder under `stages/` (`02-coded`), the
  folder's name, number, and word (`02-coded`, `02`, `coded`), which name the last of them (`02.6-builder`); in any case.
  `resolve_until(typed)` is the step or None. `check` reads it before anything runs, with one error line each, exit 2:
  a value that is not a step (`--until 'x' is not a step (names: ...)`, listing the names), and an AI step nobody chose
  (`--until 03-sweep: that step runs only when chosen (--sweep)`, the option or variable of `check`'s own rule). On
  success `a.until` holds the step's name. `--until 04-pinpoint` with `--pinpoint` and no `--sweep` passes: Pinpoint is
  chosen, and the run keeps today's note that it needs `--sweep`.
- `add_continue_options(ap, developer=False)`: the options of `walkdown.py continue <run folder>`: the run folder, the
  AI options, `--until`, the parked options (declared to be refused), `--revalidate`, `--context`, and `--hosts`;
  `developer` adds `--no-validate`. Intake's options are not declared, since intake does not run again. The parsed
  options carry `continuing` (set by this function).
- **At `continue` only the option chooses an AI step.** Choosing a model read there is the consent to send, so the
  environment variables (`WALKDOWN_SOFT_SWEEP`, `WALKDOWN_SOFT_PINPOINT`) are not read: `ai_environ(a)` is `{}` for the
  options of a `continue` and None (the process's own) for a run, and `check_until` and the runner pass it to
  `ai_chosen`. `env_not_read_notes(soft)` gives, for each variable set to a value that is not off while its option is
  not given, `<variable> is not read at continue; give --<option> <backend> to send`; the runner prints each as a
  `note:`. A first command keeps its rule (the option, else the variable).

- **A model option is a backend and a model** (M1 slice A). `BACKENDS` is a table: `jev` (reads for Sweep; takes no model name) and
  `claude-cli` (Sweep and Pinpoint; a model is optional). Each row also says whether the backend gives a probability (`probability`: `jev`
  True, `claude-cli` False), which the pages word a read by (`probability.gives`). `parse_choice(stage, value, src)` reads a value: the text before the first
  colon is the backend, in any case; the rest is the model exactly as typed; `("none", None)` for an off value. `ValueError` with one
  sentence that starts with `src` (the option or variable) for a value that cannot be used: an unknown backend
  (`--sweep: 'gpt' is not one of none, jev, claude-cli`), a backend that does not read for this step (`--pinpoint: 'jev' is refused:
  jev answers from fixed options, and the pinpoint needs a line and a sentence from the model`), a model after a backend that
  takes none (`jev:<anything>`), and a model `bad_model` refuses: nothing after the colon, or a name that is not made of
  ASCII letters, digits, and `. _ : / @ + - [ ]` only (a short list of characters that pass and no others: on Windows a `.cmd` shim hands
  the name to the shell, which reads `& | < > ^ % "` as commands and variables), starts with a dash (a command would read an option),
  holds `//` (`https://host/x` would show in the reports as a link), or is over 200 characters. The one sentence says which characters are allowed (`MODEL_RULE`). A refusal echoes the typed value as
  `shown(text)`: quoted, ASCII only (a character outside it as a backslash escape), cut at 80 characters, so it prints on any
  terminal and does not fill the screen. `normal(value)` is the value as the stages and the record
  keep it: stripped, the backend in lower case, the model as typed. `backend_names(stage)`. `ai_choice` returns `normal(value)`.
  `check_models(a)` runs inside `check`, before anything runs: it reads each model option as a stage will, a run's variable too (not
  at `continue`), skips an option the parsed options do not declare (the report stage), and refuses a `WALKDOWN_SOFT_CLAUDE_MODEL`
  that `bad_model` refuses when a `claude-cli` names no model. Walkdown picks no model for a run where the person named nothing, lists no
  models, and asks nothing; a `claude-cli` with no model named runs `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`.

- **`--reads [model]`** (the loaded-model build, 2026-11-01) chooses the model reads for a person who names no backend: Sweep on Jev
  when Jev is available (its passages then go to TypeSafe, in place of the Claude model), else on the Claude model named; Pinpoint on
  the Claude model named; tools off. Both `add_run_options` and `add_continue_options` declare it
  (`ReadsAction`: `a.reads` is `None` when the option is absent, `True` when it is bare, and the text when a model follows it). `check`
  resolves it once, before anything runs, into `a.sweep` and `a.pinpoint`, as if those had been typed (`resolve_reads`; the table
  itself is the pure function `reads_plan`, so a test needs neither a key nor a program). Nothing else knows of it: the record, the
  stamps, the grader's choice, `continue`, and the pages see only the resolved values, and `a.reads` stays as typed for the three
  messages that name the option the person gave (`check_until`, the refusal on a held run, and the one below). Nothing is probed
  unless `--reads` is given: a default run reads no key and searches no path.

  | Jev available | `claude` found | Sweep | Pinpoint |
  |---|---|---|---|
  | yes | yes | `jev` | `claude-cli[:model]` |
  | yes | no | `jev` | does not run, with one note |
  | no | yes | `claude-cli[:model]` | `claude-cli[:model]` |
  | no | no | refused | |

  Jev is available when `jevkey.available()` says so (the package is found and a key can be read; the check sends nothing and shows
  no key). `claude` is found when `shutil.which("claude")` finds it, the same question `back_claude` asks before it calls. `[:model]`
  is `:<model>` when the person gave one (`--reads claude-opus-5-5` is `claude-cli:claude-opus-5-5`, the model exactly as typed) and
  nothing when `--reads` is bare, which runs `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`, as a bare `claude-cli` does (`check_models`
  refuses a bad variable by its own sentence, since that is the model that will run). A read that `--reads` does not run is set to `none`,
  as `--pinpoint none` would be, so its environment variable cannot choose it: the option wins, as it does for `--sweep`.
  `WALKDOWN_SOFT_SWEEP` and `WALKDOWN_SOFT_PINPOINT` choose nothing while `--reads` is given. An off value (`none`, `off`, `0`, and
  the rest of `OFF`) asks for nothing: both reads are `none`, and nothing is probed.
- **At `continue`, only the reads that can still run are chosen.** The steps the run's record says ran (`steps_done`: none for a
  folder with no readable record, which the runner refuses in its own words) are left out. A Sweep that ran leaves Pinpoint alone,
  `claude-cli[:model]`, and it needs `claude`; Sweep and Pinpoint that both did not run follow the table. A read that ran is not
  named, so no note says it was ignored. `continue` reads no variable for it. A held run refuses `--reads` as it refuses `--sweep`
  and `--pinpoint`, by the name the person typed (the runner, `cannot_release`).
- **Refused before anything runs** (`error: <sentence>`, exit 2), each one sentence, in this order:
  - `--reads` with `--sweep` or `--pinpoint` (an option with a value; an empty one is no option): `--reads: it cannot be given with --sweep or --pinpoint, which name the reads themselves; give one or the other.`
  - an empty model (`--reads ""`): `--reads: the model is empty; name one, or leave the model out.`
  - a backend typed as the model (the text before the first colon, in any case, is a key of `BACKENDS`: `jev` or `claude-cli`, so `Jev`,
    `claude-cli`, and `claude-cli:opus` are refused): `--reads: 'jev' is a backend, and --reads takes a model name; to name a backend, use --sweep or --pinpoint.`
    The quoted value is the one typed, through `shown`. It is refused before the machine is asked anything. A model that only contains a
    backend's name (`jev-latest`, `my-claude-cli`) is a model name. Without this, `claude` would be handed every passage under a name
    nobody meant, and the record could read `claude-cli:claude-cli:opus`.
  - a model `bad_model` refuses: `--reads: <the value as shown> is refused: <bad_model's reason>` (the same rule, and the same `shown`, as a
    model after `claude-cli:`).
  - no read can run: `--reads: no model read can run here: Jev has no key or package, and no claude command was found.`
  - at `continue`, the Sweep ran, so Pinpoint is the one left, and `claude` is not found: `--reads: no model read can run here: only Pinpoint is left, and it needs the claude command, which was not found.`

  One note, on stderr, before the run starts (Jev available, `claude` not found, Pinpoint still to run), written by `stagenote.note` like every note (the test of `stagenote` fails on any other write to stderr in a module a step imports, and this one is): `note: --reads: Pinpoint needs the claude command, which was not found, so it does not run.`
- **`--reads` takes an optional value, so `walkdown.py --reads <repo>` would read the repository as the model.** The parser that
  `walkdown.py` and `runner.py` use (`options.Parser`) turns the one error that follows, the missing target (or run folder), into one
  sentence, exit 2, no usage text and no traceback: `error: --reads took '<value>' as its model and left no repository to audit; put
  the repository first, as in: walkdown.py <repo> --reads [model]` (for `continue`: `left no run folder to continue; put the run
  folder first, as in: walkdown.py continue <run folder> --reads [model]`; the value is shown as `shown` does). Any other parse error
  is argparse's own. `walkdown.py <repo> --reads` and `walkdown.py <repo> --reads <model>` are the forms; `walkdown.py --reads <model> <repo>` also
  parses.
- **`--until`** follows what `--reads` chose: an AI step it does not run is refused as one nobody chose, by the option the person
  typed: `--until 04-pinpoint: --reads does not run that step here`.

### Must never

- Keep a second off list. The stages that read a model option themselves (`03-sweep`, `04-pinpoint`) use
  `is_off` too: any off value is `none`.
- Keep a copy of the stage names for `--until`: they come from the stage list.

### Done when (each backed by a test in `tests/test_options.py`)

1. One off list (`test_one_off_list_for_every_model_option`).
2. The chosen-stage rule and the refusal rule read it for options and variables
   (`test_the_chosen_stage_rule_and_the_refusal_rule_read_the_same_list`); an option with a value wins and an
   empty one is no option (`test_an_option_with_a_value_wins_and_an_empty_one_is_no_option`); an off value starts no stage
   (`test_an_off_value_starts_no_stage`); the two AI stages take any off value as none
   (`test_every_off_value_is_none_for_the_variable_and_the_flag` in each stage's `tests/test_run.py`).
3. The options are declared once and checked before anything runs; the report stage takes its two from the same
   function (`test_context_and_hosts_are_read_here`, `test_the_options_are_declared_once_and_checked_before_anything_runs`).
4. `--until` names a step by name, number, or word in any case, and `coded` is the last coded step, all built from the
   stage list (`test_until_names_come_from_the_stage_list`, `test_until_names_a_step_by_name_number_or_word`); a value
   that is not a step, and an AI step nobody chose, are refused with one line each
   (`test_until_that_is_not_a_step_or_an_unchosen_ai_step_is_refused`); `ai_choice` names the backend
   (`test_ai_choice_names_the_backend_the_stage_will_read`); `continue` declares its options and not intake's
   (`test_continue_declares_its_options_and_not_intakes`).
5. At `continue` the variable chooses nothing and a note says so; a run keeps its rule
   (`test_at_continue_the_variable_chooses_nothing_and_a_note_says_so`; through the runner:
   `test_at_continue_only_the_option_chooses_an_ai_step_never_the_variable`).
6. The backend is the text before the first colon in any case and the model is the rest as typed, and the value is kept with the
   model's case (`test_the_backend_is_the_text_before_the_first_colon_in_any_case_and_the_model_is_the_rest_as_typed`,
   `test_the_value_is_kept_with_the_models_case_for_the_record_and_the_command_to_go_on`).
7. A value that cannot be used is refused with one sentence that says why, before anything runs: `jev:<anything>`, `--pinpoint jev`, an
   unknown backend, an empty model, a character outside the allowed set (white space, a shell character, a control or invisible
   character, anything outside ASCII), a leading dash, a name over 200 characters
   (`test_a_value_that_cannot_be_used_is_refused_with_one_sentence_that_says_why`,
   `test_a_model_name_is_made_of_the_allowed_characters_only`,
   `test_a_refusal_prints_on_any_terminal_and_does_not_fill_it`, and against a real `.cmd` shim,
   `test_model_name_at_a_shell.py`: a hostile name never reaches it, from the option or the variable, and an allowed one arrives
   as typed; `tests/test_walkdown.py::test_a_model_name_the_terminal_cannot_print_ends_the_run_with_a_sentence_and_no_traceback`,
   which clears the traceback a non-ASCII name caused when the brief was written to a console that cannot print it),
   `test_the_model_options_are_refused_before_anything_runs`); the variable is read by the same rules at a run and not at
   `continue` (`test_the_variable_is_read_by_the_same_rules_at_a_run_and_not_at_all_at_continue`); the model the CLI will run from
   its variable is read too (`test_the_model_a_claude_cli_will_run_from_the_environment_is_read_by_the_same_rule`,
   `test_the_model_variable_is_held_to_the_same_rule`); the report stage
   reads no model option (`test_the_report_stage_declares_no_model_option_and_reads_none`).
8. `--reads` is an optional value, absent by default, and declared for a run and for `continue`
   (`test_reads_is_an_optional_value_absent_by_default_and_declared_for_a_run_and_for_continue`).
9. Each row of the table, with and without a model, resolves to the `--sweep` and `--pinpoint` values it stands for, and the model is
   exactly as typed (`test_the_table_row_by_row`); Jev with no `claude` runs Sweep alone and says so in the one note
   (`test_jev_without_claude_runs_the_sweep_alone_and_says_so_in_one_note`); `claude` is found by the path, the way `back_claude` looks
   (`test_claude_is_found_by_the_path_the_way_back_claude_looks`: `claude_found` and `back_claude`'s own lookup, its default `which` and
   the name it asks for, are asked on the same machine and agree).
10. Each refusal is one sentence in the words above, before anything runs, and the same for the front door and the runner
    (`test_each_refusal_of_reads_is_one_sentence`, `test_the_model_of_reads_goes_through_bad_model`); a backend typed as the model is
    refused and a name that contains one is not
    (`test_a_backend_typed_as_the_model_is_refused_and_a_name_that_contains_one_is_not`).
11. The option wins: `WALKDOWN_SOFT_SWEEP` and `WALKDOWN_SOFT_PINPOINT` choose nothing while `--reads` is given, and an off value asks
    for nothing (`test_under_reads_the_option_wins_over_the_variables`, `test_reads_asks_for_nothing_when_off`); a bare `--reads` runs
    `WALKDOWN_SOFT_CLAUDE_MODEL` as a bare `claude-cli` does, and a bad variable is refused as for it
    (`test_a_bare_reads_reads_the_model_variable_as_a_bare_claude_cli_does`).
12. A default run probes nothing: no key read and no path searched. The named helpers are replaced, and the calls under them are
    watched where they start (the real `shutil.which("claude")`, the search for the SDK, any open of the registry), so a call that goes
    round the helpers is seen (`test_reads_probes_nothing_unless_it_is_given`).
13. At `continue` only the reads that can still run are chosen, on a run where Sweep ran and on one where it did not, and no variable is
    read (`test_reads_at_continue_chooses_only_the_reads_that_can_still_run`; the record is read by `steps_done`,
    `test_steps_done_reads_the_record_and_nothing_else`; and through the runner
    `test_continue_reads_on_a_run_where_the_sweep_ran_chooses_the_pinpoint_alone`,
    `test_continue_reads_on_a_run_where_the_sweep_did_not_run_chooses_both`).
14. `--reads` before the target is one sentence, exit 2, no traceback, from a real run of the front door
    (`test_reads_before_the_target_is_one_sentence_exit_2_and_no_traceback`; the parser,
    `test_the_parser_turns_a_missing_target_after_reads_into_one_sentence_and_leaves_other_errors_alone`); the same on the runner's own
    command line (`test_the_runners_own_command_line_gives_the_one_sentence_swallow_error`).
15. `--until` follows what `--reads` chose (`test_until_follows_what_reads_chose`).

### History

- 2026-10-29: restructure step 7: from `pipeline.py` (`OFF`, `REFUSED`, `refusal`, `ai_chosen`), with one off list for
  every model option; before, `WALKDOWN_SOFT_SWEEP=off` counted as chosen and failed in the stage while the parked
  variables treated `off` as off.
  The option declarations (F3), `parse_context`, `parse_hosts`, and `check` joined it from `walkdown.py` and
  `stages/05-report/run.py`, which each declared the options and copied them across one by one. A refused option given
  an off value (`--label none`) is no longer refused: it asks for nothing.
- 2026-10-30: O3: `--until`, `until_names`, `resolve_until`, `check_until` (read by `check`), `add_continue_options`,
  and `ai_choice` (`ai_chosen` reads it).
- 2026-10-30: O3, fix round: at `continue` the environment variables of the AI stages choose nothing (`ai_environ`,
  `env_not_read_notes`). They did, as for a run, which would have sent a model read on a bare `continue`.
- 2026-10-31: M1 slice A: `BACKENDS`, `parse_choice`, `normal`, `bad_model`, `backend_names`, `check_models`. `ai_choice` lowercased the
  whole value; it keeps the model's case. The stages' own `SWEEP_CHOICES` and `PIN_CHOICES` are gone.
- 2026-10-31: M1 slice A, fix round: a model name is made of a short list of characters and no others (`MODEL_CHARS`: ASCII letters, digits, and `. _ : / @ + - [ ]`; no leading dash; at most 200 characters). The list of characters it refused let `& | < > ^ %` through, and on Windows a `claude.cmd` shim runs through `cmd.exe`, so `--sweep "claude-cli:x&echo.hi>f"` ran `echo` and `%USERNAME%` reached the shim as the user's name; a name outside ASCII crashed the front door when the brief was written to a console that cannot print it, and a name of 3,000 characters made a 3,053-character brief line. A refusal echoes the value as `shown(text)` (ASCII, cut at 80). `model_env_refusal` holds `WALKDOWN_SOFT_CLAUDE_MODEL` to the rule in the front door and in each stage.
- 2026-10-31: M1 slice A, fix round: each row of `BACKENDS` says whether the backend gives a probability (`probability`: `jev` True,
  `claude-cli` False), which the report words a read by (`probability.gives`).
- 2026-11-01: M1 slice A, before merge: the `required` value of a backend's `model`, its rule, and its test are gone. No backend had it, and those backends are on hold (the owner, 2026-11-01).
- 2026-11-01: the loaded-model build: `--reads [model]` (`ReadsAction`, `reads_plan`, `resolve_reads`, `steps_done`, `Parser`), resolved in `check` into the `--sweep` and `--pinpoint` values; `check_until` names `--reads` for a step it does not run. Jev's key moved to `jevkey` so that `options` can ask whether Jev is available.
- 2026-11-01: the loaded-model build, the note: the one note is written by `stagenote.note` (it was a `print` to stderr, which the test of what a step may write to stderr refuses in a module a step imports).
- 2026-11-01: the loaded-model build, fix round: the words said Jev is added to the model and that the model is the one loaded; they now say what happens: Sweep runs on Jev when Jev is available, in place of the Claude model (its passages go to TypeSafe), else on the Claude model named; Pinpoint runs on the Claude model named; tools off; a bare `--reads` names `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet` (`READS_HELP`, the comments, and the docs). A backend typed as the model is refused (`A_BACKEND`). Tests now hold: the real calls under the helpers are watched where a default run must probe nothing; the lookup of `claude` agrees with `back_claude`'s; the runner's command line is `options.Parser`.
- 2026-11-01: the loaded-model build, before merge: `READS_HELP` names TypeSafe, and the test of the words now also covers the sentences in the contract, the sweep's context, HOW-IT-WORKS, the specs, and `requirements-soft.txt` (added in `f88feea`, which had no line of its own here). The watch of a default run counts `OpenKeyEx` as an open of the registry.

## packages

M9 slice B, second fix round.

The Python packages Walkdown imports, in one list for the two places that need them: the front door, which checks that the
interpreter it was started with can import every core one before it runs anything, and the account of a crashed step
(`steperror`), which names a missing import's module only when it is one of these. The list lived in both, apart.

### Outputs

- `CORE_MODULES`: the import names of `requirements.txt`'s packages, less pytest (no stage imports it): `yaml`,
  `charset_normalizer`, `pdfminer`, `pypdf`, `pypdfium2`, `bs4`, `lxml`, `PIL`, `regex`, `confusable_homoglyphs`,
  `detect_secrets`. `walkdown.py` imports it.
- `OPTIONAL_MODULES`: what a stage imports when it is there and does without when it is not: `filetype`, `magic`, `playwright`,
  `pytesseract`, `typesafe_sdk`. `OWN_MODULES` is the two together.

### Must never

- Import anything.

### Done when (each backed by a test in `tests/test_packages.py`)

1. `OWN_MODULES` is exactly the third-party modules the stages import, read from the code with `ast`, so a module a stage
   starts to import must be added and one it stops importing must go; pytest is not in it
   (`test_the_list_is_exactly_the_third_party_modules_the_stages_import`).
2. `CORE_MODULES` are the packages of `requirements.txt` less pytest (`test_the_core_modules_are_requirements_txts_packages_less_pytest`).
3. The front door and `steperror` read this one list (`test_the_front_door_and_the_account_of_a_crash_read_this_one_list`).

### History

- 2026-10-30: M9 slice B, second fix round: built. `walkdown.CORE_MODULES` and `steperror.OWN_MODULES` were two lists, and the
  second held pytest, which no stage imports, and lacked `magic` and `filetype`, which the inventory does.

## pipeline

Runs the stages once each, in order, as subprocesses, and saves what they
produce into the run folder: the coded stages always, the two AI stages (`03-sweep`, `04-pinpoint`)
only when a person chose them (restructure step 5; `stages_to_run`). Intake, the first stage in `stages.json` (restructure step 2), runs
apart and first: `run_intake`.

### Inputs

`run_stages(input_dir, run_dir, stages_dir, python) -> list[StageRun]`

- `input_dir`: the repo copy under audit (read-only).
- `run_dir`: the run folder (exists, empty or not).
- `stages_dir`: the `stages/` folder. Each stage's runner is `stages_dir / <folder> / run.py`,
  with the folder looked up in `stages_dir / stages.json` (`stage_folder(name, stages_dir)`;
  `load_stage_list`; `STAGES` is the list's names in run order; `stages/CONTRACT.md`, "The
  stage list").
- `python`: the interpreter to run each stage with.

`run_intake(target, run_dir, stages_dir, python, name=None, fresh=False, keep=False) -> StageRun`
(restructure step 2):

- `target`: the folder or URL as the person gave it. Intake is the one stage that takes a target
  and not a folder; it runs before the run folder exists (the folder's name can come from its
  report), so `run_dir` is wherever its two files are saved first. Its arguments are
  `intake_args`: `<target> [--name N] [--fresh] [--keep]`.
- Its report is saved as `<run_dir>/01-intake.json` and its stderr as
  `<run_dir>/01-intake.notes.txt`, as for any stage. The report's one `intake.source` finding names
  the folder every other stage reads (`stages/01-intake/specs/intake.SPEC.md`).
- `STAGES` includes `01-intake`; `INTAKE` is its name and `FOLDER_STAGES` the rest. `run_stages`
  runs `stages_to_run(soft)` by default and never intake.

`stages_to_run(soft=None, environ=None)` (step 5): `FOLDER_STAGES` less each AI stage (`AI_STAGES`) nobody
chose. An AI stage is chosen by its option (`soft["sweep"]`, `soft["pinpoint"]`; `none` or empty is not a
choice) or, with no option, by the environment variable the stage itself reads (`WALKDOWN_SOFT_SWEEP`,
`WALKDOWN_SOFT_PINPOINT`); the option wins (`ai_chosen`). `04-pinpoint` is dropped unless `03-sweep` runs
(it reads Sweep's report). `refusal(chosen)` is the message for the parked options (`--label`,
`--compare`, `--relational`, `--both`) and for their environment variables (`WALKDOWN_SOFT_LABEL`,
`_COMPARE`, `_RELATIONAL`, `_BOTH`, when set to anything but empty, `none`, `0`, `false`, `no`, or `off`):
`<option or variable> is not available in this version: labeling is being rebuilt`; the flags are checked
first; the front door and the report stage's runner both say it before anything runs.

`cut_at(steps, until)` (O3): `(to run, left out)`: the steps through `until` in the list's order, and those after it; with
no `until`, all of them are to run. `position` (from `stagelist`) orders them, so intake (`until` its name) leaves every
step out. `run_stages(..., stages=[])` runs nothing: a list that is given is the list, empty or not (it used to read an
empty list as "the default steps"). `run_input_only(stage, input_dir, run_dir, stages_dir, python, soft)` runs an AI stage
with `--input-only`: the stage writes `<run_dir>/<stage>.input.jsonl` and stops, its messages are saved as
`<stage>.notes.txt`, nothing on stdout is read, and no `<stage>.json` is saved, so the stage reads everywhere else as a
step that did not run. The StageRun is ok when the stage exited 0, with no report.

`run_qa(run_dir, stages_dir, python)` and `gaps_in(report)` (M9, slice B): `run_qa` starts the check of the run
(`stages/<qa folder>/run.py <run folder> --brief`, the folder from `stages.json`'s `qa` entry through `stagelist`) as a
subprocess, as any step: its stdout is saved as `<run folder>/data/05-qa.json`, its stderr as `05-qa.notes.txt`, and the
StageRun is not ok when the check crashed. `--brief` has the check write the brief of a held run. `gaps_in(report)` is the
number of `qa.gap` findings.

`run_stages(..., not_started=None)` and `sweep_got_nothing(run_dir)` (M9, slice A): `04-pinpoint` is not started when
the run folder's saved `03-sweep.json` is a report in which no passage got an answer (`calllog.got_nothing`: it asked
about passages and every one is a skip, even after the retry), whether Sweep ran in this call or an earlier one
(`continue`): there is nothing to pinpoint, and it would fail the same way. A caller that passes a list as
`not_started` gets `{"stage": "04-pinpoint", "why": "sweep-no-answer"}` added to it (`SWEEP_NO_ANSWER`); the runner
records it and says why on the terminal. A Sweep that asked about no passage, or whose report is missing or cannot be
read, does not stop Pinpoint.

### Behavior

- Order and arguments:
  - `02.1-inventory`: `run.py <input>`
  - `02.2-reader`: `run.py <input> --out <run_dir>`
  - `02.3-graph`: `run.py <input> --inventory <run_dir>/02.1-inventory.json --out <run_dir>`
  - `02.4-phrases`: `run.py <input> --inventory <run_dir>/02.1-inventory.json --out <run_dir> --normalized <run_dir>/normalized`
    (`02.2-reader`'s extracted text of PDFs, DOCX, and images, 2026-10-18)
  - `02.5-capability`: `run.py <input> --reports <run_dir> --out <run_dir>`
  - `02.6-builder`: `run.py <input> --reports <run_dir>` (it writes no file of its own; added in
    restructure step 4)
  - `03-sweep` (only when chosen): `run.py <input> --reports <run_dir> --out <run_dir> [--sweep <backend>]`
  - `04-pinpoint` (only when chosen, and after Sweep): `run.py <input> --reports <run_dir> --out <run_dir>
    [--pinpoint <backend>]`; the option is passed only when the person gave it, else the stage reads
    its environment variable
  - an AI stage run to write its input file only (`run_input_only`) gets `--input-only` after those arguments
- For each stage: stdout saved as `<run_dir>/<stage>.json` (after it parses as
  JSON), stderr saved as `<run_dir>/<stage>.notes.txt`, start and finish times
  recorded (UTC, ISO seconds).
- A stage that exits non-zero, or prints unparseable JSON, is recorded with
  `ok: False` and its error; no later stage runs.
- Once `02.5-capability` has been started, whether it went well or not, `mask_saved_reader(run_dir)` masks the lines the secret
  scan flagged in `<run_dir>/02.2-reader.json` (`secretmask.mask_reader`). `02.2-reader` runs before the scan, and
  `02.5-capability` needs the hidden words to say a phrase hit is inside them; no later step reads them. A run stopped before
  `02.5-capability` keeps the words in that file until it goes on (the report stage masks what it loads). With nothing flagged
  the file stays as the step printed it. An output that is not a report is left as it is, for the check of the run to name. A
  stage run `alone` masks nothing.
- Once `02.6-builder` has been started, whether it went well or not, or once any step has failed, `mask_saved(run_dir)` masks the
  lines the secret scan flagged in every saved output that keeps words from a line (`secretmask.mask_reports`): `02.1-inventory`,
  `02.2-reader`, `02.3-graph`, `02.4-phrases`, `02.5-capability` and its `capability.json`, and `02.6-builder`, and `mask_edges` for
  `graph.json`. `02.6-builder` is the last step that reads those words: it counts a description's length and sets a hook against
  the bytes `02.5-capability` kept under its command. It runs once more after `04-pinpoint`, whose answers quote lines. A run stopped
  before `02.6-builder` keeps the words in those files until it goes on (the report stage masks what it loads). A file the mask does
  not change stays byte for byte as the step printed it, and one it changes is replaced whole, so a full disk leaves no half. An
  output that is not a report, and a `graph.json` that cannot be read, are left as they are. With no saved `02.4-phrases` report there
  is nothing to go by, and nothing changes. A stage run `alone` masks nothing. `data/normalized/` is the file's own text and stays.

### Outputs

A `StageRun` per stage attempted: `stage`, `ok`, `started`, `finished` (None
when not ok), `report` (dict or None), `notes` (list of stderr lines, blank
lines dropped), `error` (str or None). A stage that crashed has `exit N` and the error's type as its `error`
(`exit 1: ValueError`; `steperror.exit_text`). The line that ends a traceback holds the error's message, which can repeat
text from the audited repository or a model's words, and `error` reaches the record, `LOG.md`, and the line the runner
prints, so the end of the stderr is left out of it (M9 slice B). The whole stderr stays in `<stage>.notes.txt`. A stage run
`alone` (`run_stages(..., alone=True)`: for a stage that runs on its own, the grader's and the tests') has no record to
keep it out of, and its `error` is `exit N: <the end of its stderr>` as before M9 slice B, which is what the person
running it needs (`earlier_steps.StepFailed` carries it: `02.1-inventory failed (exit 2: error: cannot read ...)`). A stage
that printed unparseable JSON has `invalid JSON: <the parser's words>`, which holds none of the document.

`note_lines(text)`: the stderr lines, stripped, blank dropped, with any leading
`note: ` removed.

`own_notes(text, finished)` (M9 slice B fix round): the lines of a step's messages that the check of the run and the pages
may use: the lines the step wrote as its own notes (`note: ...` from the first column, the prefix removed), and none at
all when the step did not finish. Anything else on a step's stderr is a library's words or an error's message, which can
repeat text from the audited repository or a model's words; it stays in the notes file. A line that is indented, or that holds
`note: ` after other words, is not a note (a name from the repository is flattened onto one line by `stagenote` before it is
written, so no name can start a line of its own).

`read_report(path)` (M9 slice B fix round): a step's saved output as a report; `ValueError` when it is not a document
with a list of `findings`, each a dict with a `check` (a saved `[]` or `{}`, a number or an empty object among the findings,
and text cut off by a full disk are not reports). The check of the run, the report stage (the steps' outputs and the
capability step's side file `capability.json`), and the comparison of two runs read a saved output by this one test, so an
output is a report to all of them or to none. M9 slice C: a `coverage` it carries must be a list of lines (`coverlines.valid`);
one that is not (a word, a line that is not an object, a count that is not a whole number) is a report that cannot be read, the
same as bad `findings`: the step has the one gap `output-unreadable` and no coverage gap besides, and every reader refuses the
file alike. The one exception is an object under that name: `02.2-reader` wrote its counts there before slice C, so a run made
before is read as a report with no lines. (The alternative, reading a bad `coverage` as a coverage gap and keeping the step's
findings, would need every reader of a saved output to guard `coverage` itself; one test at the one door does not.)

`read_report(path)` (M1 slice A): a `usage` it carries must be an object whose counts, where it has them, are whole numbers
(`usage.valid`); one that is not (a word, a count that is a bool, a float, below zero, above 10^15, a null) is a report that cannot be
read, the same as bad `findings` or `coverage`: the step has the one gap `output-unreadable`, and every reader refuses the file alike.

`_spawn(cmd, show_progress)` (M1 slice A): a model step runs with its stderr read as it comes (`subprocess.Popen`, a thread for
stderr, stdout read whole) and the lines `stagenote.is_progress` accepts (`sweep: 25 of 431 passages done`) are written to this
process's stderr through `stagenote.show_progress`, so a long read says it is working on the person's terminal; nothing else a step
writes is shown. All of its stderr is still `data/<step>.notes.txt`. The coded steps, and a model step run with `--input-only`, run as
before. The reader reads the step's stderr to the end whatever happens to this process's own stderr: a write of a progress line
that fails (`OSError`, `ValueError`) is dropped for that line and the reading goes on, since a reader that stopped would let the
step's stderr pipe fill and the call would wait for ever (M1 fix 3). On any exception raised in the wait, `KeyboardInterrupt`
included, the step is killed and waited for, as `subprocess.run` does, so a model read does not go on running, and spending,
unattended (its pipes are closed once the reader has ended). On Windows the blocking read of the step's output is not interrupted by a
Ctrl-C: the parent sees it when the read returns, which is when the step ends (normally because the console's Ctrl-C reached the step
too), as with `subprocess.run`; this does not shorten the wait for a step that ignores a Ctrl-C.

`first_finding(report)` (M9 slice B, second fix round): the first finding of a report (the inventory's pin), or `{}` when the
report has none or is not one. The runner names and files a run by it, so an inventory that prints `{"findings": []}` or
`{"findings": [1]}` is a run named `<date>_nohash` and not a traceback with a `.running-<date>` folder left behind.

### Must never

- Write inside `input_dir`.
- Run a stage after one has failed.
- Import code from another stage.

### Done when (each backed by a test in `tests/test_pipeline.py`)

0. `STAGES` is the names in `stages.json`, intake first; `FOLDER_STAGES` is the rest
   (`test_the_stage_list_and_folders_come_from_stages_json`). `run_intake` runs intake apart, saves
   its two files, and names the folder; a target it cannot use is recorded as a failure with the
   message (`test_intake_runs_first_and_apart`, `test_intake_failure_is_recorded_with_its_exit_code_and_its_message_stays_in_the_notes`,
   `test_intake_args_carry_the_target_and_the_options`).

1. On a tiny repo (a SKILL.md and a README), a default run starts the coded stages and no AI stage: a
   JSON report and a notes file for each exist in the run folder, no `03-` or `04-` file does, every
   `StageRun.ok` is True, and the input folder is byte-identical afterwards
   (`test_a_default_run_runs_the_coded_stages_and_no_ai_stage`). An AI stage runs only when chosen,
   Pinpoint only after Sweep, and the flag wins over the environment
   (`test_an_ai_stage_runs_only_when_chosen_and_pinpoint_only_after_sweep`); an AI stage gets its own
   option only when the person gave it (`test_an_ai_stage_gets_its_own_option_only_when_the_person_gave_it`);
   the parked options are refused (`test_the_parked_options_are_refused_with_a_plain_message`), and so are
   their environment variables (`test_the_parked_environment_variables_are_refused_like_their_flags`).
2. A stages folder whose `02.3-graph` runner exits 1 gives three `StageRun`s, the
   third not ok with its error, and no `02.4-phrases.json`.
3. `note_lines` strips `note: ` and drops blank lines. `own_notes` keeps only `note: ` lines, and none from a step that
   did not finish (`test_own_notes_are_the_note_lines_of_a_step_that_finished`, `test_a_note_is_read_from_the_first_column_of_a_step_that_finished`). `read_report` reads a document with a
   list of findings, each finding a dict with a `check`, and refuses a list, an empty object, a `findings` that is not a
   list, and a finding that is a number, an empty object, or has no text `check`
   (`test_a_saved_output_is_a_report_only_when_it_is_a_document_with_a_list_of_findings`).
4. `cut_at` splits the steps at the named one, intake leaves all of them out, and an empty `stages` runs none
   (`test_cut_at_splits_the_steps_after_the_named_one`, `test_an_empty_list_of_stages_runs_nothing`); an AI stage run
   for its input file only leaves the notes and no report (`test_an_ai_stage_run_for_its_input_file_leaves_notes_and_no_report`).
5. Pinpoint is not started after a Sweep in which no passage got an answer, in the same call or on a saved Sweep report,
   and the caller is told why; it is started when one passage got an answer, when none was asked, and when the Sweep
   report is missing or unreadable
   (`test_pinpoint_is_not_started_after_a_sweep_in_which_no_passage_got_an_answer`,
   `test_pinpoint_is_started_when_one_passage_got_an_answer_or_none_was_asked`,
   `test_pinpoint_is_not_started_on_a_saved_sweep_that_got_no_answer_either`,
   `test_a_missing_or_unreadable_sweep_report_is_not_a_sweep_that_got_no_answer`).
6. A crashed step's `error` is its exit code and its error's type; text after the type, and a name that is not one of
   Python's own, stay out of it, and the whole stderr is in the notes file
   (`test_a_crashed_step_keeps_its_exit_code_and_its_errors_type_and_the_whole_stderr_stays_in_the_notes`). A stage run
   `alone` gives the end of its stderr (`test_a_stage_run_alone_gives_the_end_of_its_stderr_and_a_stage_of_a_run_does_not`).
7. The check of the run is started on a run folder and saves its report and its messages beside the steps'; a gap has it
   write the brief of a held run and a run without one does not; `gaps_in` counts the gaps
   (`test_the_check_of_the_run_is_started_on_a_run_folder_and_saves_its_report_like_a_step`).
8. A model step whose caller cannot write to its own stderr is still read to the end, with all of its stderr kept
   (`test_a_step_is_read_to_the_end_when_this_process_cannot_write_to_its_own_stderr`); a call that ends on an exception in the wait
   (the test raises `KeyboardInterrupt` and `RuntimeError` there) kills the step and waits for it
   (`test_a_step_is_killed_and_waited_for_when_the_call_ends_on_an_exception`).

`soft` (step 5): `{"sweep": backend, "pinpoint": backend}`; None or empty values are dropped. The
bare-flag form (`--both`, 2026-10-01) is gone with the double read.

`stages` (added 2026-10-01): an optional subset of `FOLDER_STAGES` to run in order; tools/baserates.py
runs `02.1-inventory` and `02.4-phrases` only.

- 2026-10-29: restructure step 5: `AI_STAGES`, `ai_chosen`, `stages_to_run`, `refusal`; `_args` for `03-sweep` and `04-pinpoint`; the bare-flag form of `soft` is gone.
- 2026-10-29: restructure step 5, round 2: `refusal` also refuses the parked environment variables.
- 2026-10-29: restructure step 7: moved from `stages/05-report/` to `stages/_shared/`. The stage list and its tables
  (`STAGES`, `INTAKE`, `FOLDER_STAGES`, `AI_STAGES`, `AI_OPTION`, `AI_ENV`, `load_stage_list`, `stage_folder`) are
  `stagelist.py`'s and the off list, `refusal`, and `ai_chosen` are `options.py`'s (the `stagelist` section,
  the `options` section); this module imports them, so the names still work here. `run_stages(..., alone=True)`
  runs steps as a stage on its own gets them (the `earlier_steps` section).
- 2026-10-30: O3: `cut_at` and `run_input_only` (with `--input-only` in the AI stages' arguments); a `stages` list that is
  given and empty runs nothing (`stages or ...` became `stages if stages is not None else ...`; the one caller that could
  pass an empty list, `earlier_steps.run_before`, already returned before it).
- 2026-10-30: M9 slice A: `run_stages(..., not_started=)` and `sweep_got_nothing`: Pinpoint is not started after a
  Sweep in which no passage got an answer (today it started on a Sweep that answered nothing, and asked nothing).
- 2026-10-30: M9 slice B: a crashed step's `error` is `exit N: <type>` and no longer `exit N: <the last 500 characters of
  its stderr>` (the verifier found that text could carry the repository's or a model's words into `LOG.md` and `run.json`).
- 2026-10-30: M9 slice B: `run_qa` and `gaps_in`.
- 2026-10-30: M9 slice C: `read_report` refuses a report whose `coverage` is not a list of lines (above, in Outputs).
- 2026-10-31: M1 slice A: `read_report` refuses a `usage` that is not counts of whole numbers; a model step's progress lines are shown
  as they come (`_spawn`).
- 2026-10-31: M1 slice A, fix round: `_spawn` kept reading the step's stderr only while writing a progress line worked. When this
  process's stderr failed, the reader thread died, the step's stderr pipe filled, and the call never returned. It reads on now. It
  also killed nothing on an exception, so one that reached the wait left the model read running and spending; it kills the step and waits for it.
- 2026-10-31: M1 slice A, fix round 2: the docstring and this spec said a Ctrl-C ends the call. On Windows the blocking read of the
  step's output is not interrupted by it, so the parent sees a Ctrl-C when the read returns, at the end of the step, as `subprocess.run`
  does; they say so now. Nothing in the code changed.
- 2026-11-01: `mask_saved_reader`, after `02.5-capability` (`test_the_saved_reader_is_masked_once_the_pairs_have_read_it`,
  `test_the_saved_reader_keeps_its_words_until_the_pairs_have_read_them`,
  `test_a_step_that_failed_after_the_scan_still_leaves_the_saved_reader_masked`,
  `test_nothing_flagged_leaves_the_saved_reader_as_the_step_printed_it`, `test_a_step_run_alone_for_another_masks_nothing`,
  `test_a_saved_reader_that_is_no_report_is_left_for_the_check_of_the_run`).
- 2026-11-01: `mask_saved`, after `02.6-builder`, after a step that failed, and after `04-pinpoint`
  (`test_every_saved_output_is_masked_once_the_last_step_that_reads_the_words_has_read_them`,
  `test_a_saved_output_keeps_its_words_until_the_last_step_that_reads_them_has_read_them`,
  `test_a_step_that_failed_after_the_scan_leaves_every_saved_output_masked`,
  `test_a_step_that_failed_before_the_scan_has_nothing_to_mask_by`,
  `test_nothing_flagged_leaves_every_saved_output_as_the_step_printed_it`,
  `test_a_saved_output_that_is_not_a_report_is_left_for_the_check_of_the_run`, `test_a_saved_output_keeps_the_ending_it_had`,
  `test_an_edge_of_the_graph_file_is_masked_with_the_rest`, `test_a_step_run_alone_for_another_masks_nothing_at_the_last_step_that_reads_the_words`,
  `test_a_file_the_mask_does_not_change_is_not_written_again`, `test_pinpoints_report_is_masked_when_it_has_run`). The saved files follow the rule the owner chose for
  `02.2-reader`, each masked after the last step that reads its words; the owner confirmed this one (2026-11-01).

## playwright_check

Restructure step 7.

Whether Playwright and the Chromium it launches are here. The reader draws HTML as a browser does only
when they are (`02.2-reader/render_html.py`), and the validation step needs to know whether they are,
because installing them changes what a stage can measure (`validate.optional_tools`). Both ask here; the
validation step used to import the reader's `render_html` for this one check (notes M13).

### Outputs

- `available() -> (bool, why)`: cheap, no browser started. The package is importable and the Chromium
  build it launches is installed (`expected_build`: the `chromium_headless_shell-<revision>` the package's
  own `browsers.json` names). A build for another Playwright version is not enough. `why` says what is
  missing and how to install it (`INSTALL`).
- `PLAYWRIGHT_BROWSERS_PATH=0` means the bundled browsers: available when the package is.

### Must never

- Start a browser or open a page.
- Import a stage.

### Done when (each backed by a test in `tests/test_playwright_check.py`)

1. It names what is missing (`test_available_names_what_is_missing`).
2. It wants the build this Playwright launches (`test_available_wants_the_build_this_playwright_launches`).

### History

- 2026-10-20: built as `render_html.available` (HTML render); 2026-10-21 wants the exact build.
- 2026-10-29: restructure step 7: moved here from the reader; `render_html` imports it, and so does `validate.py`.

## probability

M1 slice A (2026-10-31).

How sure a model was, as a Sweep finding says it. A finding from Jev has `p_any`. A finding from a model that takes text has none: no
model is asked how sure it is (Claude rated itself 0.9 or more 27 times and was right 12), so `probabilities` and `p_any` are absent
and the finding says only whether the model flagged the passage. Every reader of a Sweep finding asks here, so one with no number
is handled the same way everywhere and no number is made up for it.

### Outputs

- `of(finding)`: `p_any` as a number, or None when the finding has none: absent, null, text, a bool, or a number that is not finite
  (a saved file changed by hand reads as a finding with no number and not as a crash).
- `words(finding)`: `p=0.62`, or `NONE`. `NONE` is `this model gives no probability`: the words that stand where the number would be
  on every page.
- `gives(backend)`: whether the backend gives a probability with its Sweep answer, the `probability` of its row in `options.BACKENDS`
  (`jev` True, `claude-cli` False); None for a name the table does not have. The pages word a read by it, never by looking for a number
  in the rows: a text model that got no answer for any passage has no rows to look at (M1 fix 9).

### Must never

- Return a number for a finding that has none.

### Done when (each backed by a test in `stages/06-report/tests/test_no_probability.py` unless named)

1. A number is read as one and nothing else is (`test_a_number_that_is_a_number_is_read_as_one`,
   `test_a_saved_finding_whose_p_any_is_no_number_reads_as_a_finding_with_none`).
2. A backend states whether it gives a probability, in the table (`test_options.py::test_every_backend_says_whether_it_gives_a_probability`,
   `test_no_probability.py::test_the_backends_table_says_which_backend_gives_a_probability`).
3. The report's pages and the pinpoint's choice of passages agree for a read with a number and a read without
   (`test_the_pinpoint_asks_about_the_same_passages_the_pages_list`; the pinpoint's own rule is
   `stages/04-pinpoint/tests/test_pinpoint.py::test_a_read_with_no_probability_is_asked_about_when_it_flagged_the_passage_and_no_pattern_covers_it`).

### History

- 2026-10-31: M1 slice A: built. `render.sweep_split`, `_s6`, `_f6`, `details_html`, `review_html`, and `pinpoint.targets` each read
  `p_any` themselves before, and two of them formatted it and would have crashed on a finding without one.
- 2026-10-31: M1 slice A, fix round: `gives(backend)` and the `probability` key of `options.BACKENDS`. Section 6 told a text model that got no
  answer for any passage `0 flagged at p >= 0.6`, because it looked for a row without a number and there was none.

## rates

Restructure step 7.

Reads the base rates: how often each `02.4-phrases` pattern hit in the repositories already audited. The
table is `Library/baserates.json`; `tools/baserates.py` writes it, and the report stage reads it through
this module. A rate is a published fact about a pattern, never a judgment of the artifact under review.

### Outputs

- `rate(table, pattern, exclude_hash)`: the rate over the repos other than the one being audited
  (matched by hash): `repos`, `repos_hit`, `lines`, `level`. None without a table.
- `level(repos_hit)`: `rare` 0, `uncommon` 1, `common` 2 or more. `LEVELS` says each in words (the
  `levels` key the tool writes).
- `phrase(rate)`: "rare: in 0 of 3 other audited repos" (", N lines" when N > 0); "" without a rate.
- `load(path)`: the table, or None when it is missing or unreadable. The default is
  `Library/baserates.json`.

### Must never

- Judge, weight, sum, or rank. A level is a bin of a count, shown with the count.
- Count a repo against itself (the report passes the run's hash).

### Done when (each backed by a test in `tests/test_rates.py`)

1. `level` bins 0 / 1 / 2+.
2. `rate` excludes the audited repo by hash; `phrase` words it.
3. The shipped table loads.

### History

- 2026-10-29: restructure step 7: the reading half of `baserates.py`, which became a tool.

## readtext

How a file's bytes become the lines a stage reads. Moved here from `02.4-phrases` (`decode` and
`split_lines` from `foldtext.py`, the file loop from the runner) in restructure step 4, because
two steps read the repository's text and must read the same files and the same lines:
`02.4-phrases` scans it and `02.6-builder` asks what it needs, triggers on, and costs. A module
here imports no stage and reads nothing but the folder and the rows it is given.

### Inputs

The bytes of a file, a text, or the input folder with one `02.1-inventory` `inv.file` row.

### Outputs

`decode(data) -> str | None`: the text of a file, or None when it is not text.
A BOM (UTF-8, UTF-16 LE/BE, UTF-32 LE/BE) picks the codec and is dropped;
bytes holding NUL without a BOM are binary; then UTF-8; then the encoding
`charset-normalizer` detects; else None. NUL (2026-10-09): bytes with NUL are binary when NUL is
more than 1% of the bytes or the rest is not strict UTF-8; a few NULs in valid UTF-8 are text
(a literal `\0` sentinel in source made a file binary, so one NUL could hide any file).

`split_lines(text) -> list[str]`: the lines of a text, split on `\n` only
(never on U+2028, U+2029, U+0085, form feed, or other characters Python's
`splitlines` treats as breaks), one trailing `\r` removed from each line. A
final empty piece after a trailing newline is not a line. Line `i` of the
result is line `i + 1` of the file.

`read_row(input_dir, row) -> Read(text, size, why, binary)`: the text of one file by the rules `02.4-phrases`
has always used, in this order; the first that holds is the answer, and `text` is None for all
but the last:

1. the row has `skipped` (`02.1-inventory` could not read it): `why` is `unreadable: <reason>`;
2. the row is a symlink (`type` `inode/symlink`, or a `target`): `symlink (never followed)`;
3. the row has no `encoding` (`02.1-inventory` found it not to be text): `not text (<type or binary>)`, and
   `binary` is true (the one case `02.4-phrases` may still read from `02.2-reader`'s extracted copy);
4. the base name is one of `PATTERN_LISTS` (`.gitignore`, `.gitattributes`, `.npmignore`,
   `.dockerignore`, `.prettierignore`, `.eslintignore`, `codeowners`, `.gitmodules`, `.mailmap`;
   lists of path patterns read by git and tools, nothing in them is followed or executed):
   `pattern list (not instruction text)`;
5. the file cannot be opened: `unreadable: <error>`;
6. `decode` returns None: `undecodable text`;
7. else the text, with `size` its length in bytes.

`text_candidate(row)`: whether `read_row` will try to read a row, from the row alone (it passes rules 1 to 4). `pattern_list(row)`: whether a row
is a pattern list that rule 4 turns down (it passes rules 1 to 3 and not 4). The secret scan is the one check that opens these
(`02.4-phrases`'s spec, secret_scan).

### Must never

- Follow a symlink, write anywhere, or read a file outside `input_dir`.
- Differ between the two steps that call it: the rules live here only.

### Done when (each backed by a test in `tests/test_readtext.py`)

1. `decode` reads UTF-8, UTF-8 with BOM (dropped), UTF-16 with BOM; returns None for bytes holding
   NUL (`test_decode`).
2. `split_lines("a\r\nb\n")` is `["a", "b"]`; `split_lines("a\n\nb")` is `["a", "", "b"]`;
   `split_lines("")` is `[]` (`test_split_lines`).
3. `split_lines` does not split on U+2028, U+2029, or U+0085 (`test_split_lines_only_on_line_feed`
   here, and `02.4-phrases`'s `test_separators_become_space_and_do_not_split`, which folds them).
4. `read_row` reads a text file with its size, and says why for each of the six ways a file is not
   read, in the order above (`test_read_row_reads_text`, `test_read_row_says_why_a_file_is_not_read`,
   `test_read_row_checks_in_stage_4s_order`).
5. A few NULs in otherwise valid UTF-8 are text; mostly NUL is not
   (`02.4-phrases`'s `test_nul_is_text_and_folded`, which also folds the text).
6. A row is a text candidate, a pattern list, or neither (`test_a_row_is_a_text_candidate_a_pattern_list_or_neither`).

### History

- 2026-10-29: moved from `02.4-phrases` (restructure step 4). The tests of `decode` and
  `split_lines` moved with them; behavior unchanged.
- 2026-11-01: `pattern_list`, so the secret scan can read what `read_row` turns down by name.

## record

Restructure step 7.

The record of how a run went, as data: `data/run.json`. The runner writes it after the steps and the
validation; the report stage reads it to write `LOG.md` and the reports. It holds what no stage output holds,
so the report stage never reads anything back out of `LOG.md`'s text (notes F1): the stamps came from there.

### The file

```json
{"format": 3, "finished": "2026-10-29T18:34:52+00:00", "context": 32000, "hosts": ["codex"],
 "steps": [{"stage": "01-intake", "ok": true, "started": "...", "finished": "...", "error": null}, ...],
 "stamps": {"02.1-inventory": {"result": "PASS", "gate": "26/26", "negative": "7/7", "recall": null,
                                "skipped": [], "cached": null}, ...},
 "version": "0.4.0 (1a2b3c4)",
 "until": "02.6-builder", "prepared": {"stage": "03-sweep", "items": 12, "backend": "jev"},
 "continued": [{"after": "02.3-graph", "at": "2026-10-30T09:12:00+00:00"}]}
```

(`until`, `prepared`, and `continued` appear only in a run that stopped or was gone on with; see below.)

- `steps`: each step the runner started, in run order, intake first: its times, whether it produced a report, and
  its error when it did not (`exit N: <the error's type>`, or `invalid JSON: ...`; never the message, `steperror`).
  A step that did not start is not here.
- `stamps`: the validation stamp of each stage the grader was asked about (empty for a run made without
  validation), as `validate.Stamp` holds it. `cached` is the date a reused stamp was measured.
- `context` (the expected context in tokens, 32,000 unless `--context` said otherwise), `hosts` (the target
  hosts, `[]` when none were named), `finished` (when the runner ended).
- O3 added four keys and kept `FORMAT` 2, since a record without `until` is a run that went through, so every run made
  before reads as it does now:
  - `version`: the Walkdown that made the run, as the pages name it (`toolversion.tool_version`: `0.4.0 (1a2b3c4)`, and
    `+modified` for uncommitted changes). It is for display; `continue` compares its version number alone
    (`toolversion.release`).
  - `code`: a hash of the code and tables the run used (`toolversion.code_hash`: walkdown.py, and the `.py`, `.yaml`,
    and `.json` files of stages/ and Library/ less the tests, the specs, and hidden files). Two sets of uncommitted
    edits have the same `version` and a different `code`; `continue` goes on only when the version number and the
    code are this Walkdown's, so a commit or an edit that touches no code (a document) does not refuse a run.
  - `until`: the step the run stopped after. Present only for a run that stopped as asked, that is, when `--until`
    named a step with a step of the list after it and every step through it (and the input file below) went well.
  - `prepared`: `{"stage": "03-sweep", "items": 12, "backend": "jev"}`, the AI step that wrote its input file and
    stopped (`--input-only`), with the number of items in the file and the backend that wrote it. That step is not in
    `steps` when it went well: it did not run.
  - `continued`: `{"after": the step, "at": the time}` for each time the run was gone on with, oldest first.
- M9 (slice A) added a fifth, `not_started`, and kept `FORMAT` 2 the same way (a record without it is a run in which every
  chosen step was started):
  - `not_started`: `[{"stage": "04-pinpoint", "why": "sweep-no-answer"}]`, a chosen AI step that was not started
    because the step before it got no answer for any passage (`pipeline.run_stages`). That step is not in `steps`
    and has no stamp.
- M9 (slice B) added four keys and moved `FORMAT` to 3 (owner, 2026-10-30): a run has a new output, `data/05-qa.json`,
  and section 7 and the lists of steps that did not work are drawn from it, so a run made before has no such file and is
  not re-rendered or compared (`made_before`):
  - `qa`: `{"started", "finished"}`, when the check of the run ran (the runner writes it after the check; the record is
    written first, so it cannot hold its own check). `LOG.md`'s row for the check takes its times from it.
  - `held`: `{"by": "05-qa", "gaps": N}`, when the check found a gap and the run was held: no report was written, and
    `brief.md` is the hold's brief. A held run is not a stopped one; it has `held` and, if `--until` also stopped it, `until`.
  - `released`: `{"by": "05-qa", "gaps": N, "at": the time}`, after `walkdown.py continue` wrote the report of a held
    run. `held` is gone then. A run checked again (a later `continue`) that holds again loses its `released`.
  - `chosen`: the model reads the last command chose, by step name (`["03-sweep", "04-pinpoint"]`; absent when none was).
    A first command's is the steps it ran or would have run (`stages_to_run`); a `continue` sets it to the reads that
    already ran and the ones it chooses now, since the first command's choice is not carried (choosing at `continue` is the
    consent to send). The check counts a chosen read that has no step as a gap, unless the record says why (a stop was
    before it, `until`/`prepared`; or `not_started`). A record without it is a run that chose nothing it did not start.
  - `dropped` and `backends` (second fix round): `dropped` lists the reads an earlier command chose that a `continue` did
    not choose and so did not run (`runner.reads_left_out`: not a read that ran, one chosen here, or one held back by
    `not_started`; a read dropped at an earlier `continue` stays dropped until it is chosen). Nothing is lost
    silently: `continue` prints a note per dropped read, and the pages say it. `backends` is `{step: the backend chosen}`
    for the reads in `chosen` and `dropped`, which the stop's brief and the note need to name the option that chooses a
    read again (`--sweep jev`); the first command writes it from the options it was given, and a `continue` keeps it.

### Outputs

- `write(run_dir, steps, stamps, context, hosts, finished, version=None, until=None, prepared=None, continued=(),
  code=None, not_started=(), chosen=(), dropped=(), backends=None)`: saves it in `data/`. `steps` are `pipeline.StageRun`s. A key whose value is empty is
  not written.
- `amend(run_dir, **keys)`: add keys to the record already written (a key given `None` is taken out); returns it.
  `hold(run_dir, gaps, by)`: `held` is set and `released` taken out. `release(run_dir, at)`: `held` becomes `released`
  with the time. `held_of(record)`: `{"by", "gaps"}`, or None for a run that is not held (never held, or released).
  Only the runner calls them, after the steps, the validation, and the record.
- `stop_of(record)`: `{"after": until, "prepared": prepared or None}`, or None for a run that went through (no
  `until`, or one that names no step of the list). `stopped_early(run_dir)`: the run stopped before its last coded step
  (`stagelist.CODED[-1]`), so the comparison cannot read it.
- `read(run_dir)`: the record, or None when there is none, it cannot be read, or its `format` is not the current
  one (`FORMAT`, 3). `read_any(run_dir)`: the record whatever its format (None when there is none or it cannot be
  read); only the times that order runs are taken from it.
- `made_before(run_dir)`: `read(run_dir)` is None.
- `stamps_of(record)`: `{stage: validate.Stamp}`.

### The one rule for a run that is not the one being made (restructure step 7b)

> A run can be re-rendered or compared only when its record has the current format.

`made_before(run_dir)` says it: a run with no record, an unreadable record, or a record of another format was
made before this version of Walkdown. The format is the shape of the data inside the run, not only of the record
file, and it changes when that shape does. Every reader of an earlier run asks this one question:

- **Re-render** (`stages/06-report/run.py`): refused with one plain line and exit 2 (`stages/06-report/specs/report.SPEC.md`, section `run`).
- **Comparison** (`changes.md`, the brief's change lines, the details page, `drift.py <old> <new>`): the run is
  "not comparable" and nothing is compared field by field (`stages/06-report/specs/report.SPEC.md`, section `drift`).
- **Marks carried from an earlier run** do not ask: they carry from a run of any format, because a mark's key is
  matched to the places of the run being made (`stages/06-report/specs/report.SPEC.md`, section `marks`). **Which run is earlier** (below) does not ask
  either: a run with an older-format record is still ordered by the times in it (`read_any`).

### The previous run (notes F2; round 2 of step 7)

One rule, in one place, for "an earlier run" of the same repository:

> The previous run is the newest other run folder of the same repository that finished before this run started.

- `times(run_dir)` is `(started, finished)` in seconds: from the record, the first step's start (intake) and
  `finished`; for a run without a record (made before this version), its `LOG.md`'s modification time for both;
  `(0, 0)` when nothing says. A record whose times cannot be read falls back to the log.
- **A run with a record** is ordered by the times in it. A run **without** one is ordered by the date its folder
  name starts with (`YYYY-MM-DD_...`) first, because its log's time is not the run's time: v0.3.1 appended to
  `LOG.md` when a run was rendered again (a run made on 10-10 and rendered again on 10-27 has the newest log), and
  copying a results folder without file times gives every log the same time. The log's time counts only against a
  run of the same date. A name without a date uses the date of the run's own time. In full, for two runs:
  1. both have a record: the first is earlier when it **finished** before the other **started**;
  2. otherwise, the run with the earlier folder date is earlier;
  3. on the same date, each run's one time is compared (a record's **start**, or the log's time): the earlier time
     is earlier;
  4. a tie goes to the folder name, with a `-2`, `-3`, ... suffix counted as a number (no suffix is 1), so `-2`
     comes before `-10`.
  A folder with no times at all is dated by its name and has time 0, so on its date it is the oldest.
- `earlier_runs(run_dir)`: the sibling folders (a name that starts with a dot is a run in progress and is never
  one; this run is not one) that are earlier than this run by that order, newest first. This run is never one of
  its own earlier runs, and a later run is not either.
- `previous_run(run_dir)`: the first of them that has a `LOG.md` (a finished run) and was not stopped before its coded
  steps were all done (`stopped_early`, O3: the next full run is compared with the last run that went through), or None.
- `drift.changes` (`changes.md`, the brief, the details page) and `marks.for_run` (marks carried from an earlier
  run) both read it. A run rendered again is compared with the run before it, never with itself or a later one.

The names start with the date and end with the commit's hash, so ordering by name put two runs of one day in the
order of their hashes: a run this afternoon (hash `aaaaaaa`) skipped this morning's (`bbbbbbb`) for yesterday's.
Main's comparison picked by the log's time and was right; its mark carry-over picked by name and had the flaw.
Step 7 had first used the name for both; round 2 fixes both, which also fixes the carry-over flaw main had.

### Must never

- Hold text from the audited repository: it has times, results, and Walkdown's own words (an error is a stage's
  exit code and its error's type; until M9 slice B it was the tail of the stage's messages).
- Be written by anything but the runner, or read back out of anything but the file.

### Done when (each backed by a test in `tests/test_record.py`)

1. A record written reads back with the same steps, stamps (the same text), context, hosts, and finish time.
2. A missing, unreadable, or other-format file reads as None; `read_any` still reads an older format
   (`test_a_missing_unreadable_or_other_format_record_reads_as_none`). A run is made before this version unless its
   record has the current format (`test_a_run_is_made_before_this_version_unless_its_record_has_the_current_format`).
   A run with an older-format record is still ordered by its record's times
   (`test_a_record_of_an_older_format_still_orders_its_run_by_the_times_in_it`).
3. The previous run (`tests/test_record.py`): two runs on one day with the later one's hash sorting lower
   (`test_two_runs_on_one_day_are_ordered_by_time_and_not_by_commit_hash`); `-2` and `-10` suffixes
   (`test_a_suffix_counts_as_a_number_and_a_tie_in_time_is_broken_by_it`); a run without a record beside a new one
   (`test_a_run_made_before_this_version_is_ordered_by_its_logs_time_beside_a_new_one`); a re-render picks neither
   itself nor a later run (`test_a_rerender_never_picks_itself_or_a_later_run`); a run in progress, a folder
   with no times, and another repository (`test_a_run_in_progress_a_folder_with_no_times_and_another_repository_are_handled`);
   a record without times (`test_a_record_without_times_falls_back_to_the_log`). Round 3: an older run without a
   record, rendered again after a newer one was made, does not come after it
   (`test_an_older_run_without_a_record_rendered_again_later_does_not_come_after_a_newer_one`), and runs with and
   without a record are ordered across dates (`test_runs_with_and_without_a_record_are_ordered_across_dates`).
   Through the comparison and the marks:
   `test_drift.py::test_the_previous_run_of_two_runs_on_one_day_is_the_earlier_one_whatever_their_hashes`,
   `test_drift.py::test_an_older_run_rendered_again_later_is_not_compared_with_a_newer_one`,
   `test_marks.py::test_carry_over_takes_the_run_that_finished_last_and_not_the_name_that_sorts_last`,
   `test_marks.py::test_an_older_run_rendered_again_later_does_not_take_a_newer_runs_marks`.

4. The new keys are written when there is a value and read back; `stop_of` and `stopped_early` say where a run stopped
   (`test_a_stop_is_written_and_read_back`, `test_stopped_early_is_a_stop_before_the_last_coded_step`); the previous run
   skips a run stopped early and takes one stopped after the last coded step
   (`test_the_previous_run_skips_a_run_that_stopped_before_its_coded_steps_were_done`).

5. `not_started` is written when a chosen step was not started and read back, and a record without it is a run in
   which every chosen step was started (`test_not_started_is_written_when_there_is_one_and_read_back`).

6. `hold`, `release`, `held_of`, and `amend` write and read the keys of a hold; a check made again loses its release
   (`test_a_hold_and_its_release_are_written_to_the_record_and_read_back`,
   `test_amend_adds_keys_and_takes_out_a_key_given_none`). `FORMAT` is 3 and a record of format 2 reads as None
   (`test_a_record_reads_back_what_was_written`, `test_a_missing_unreadable_or_other_format_record_reads_as_none`).

(The runner writing it for a real run: `test_runner.py::test_the_record_holds_the_steps_the_stamps_and_the_options`.)

### History

- 2026-10-29: restructure step 7: built. `data/run.json` is a new file in the run folder; the stamps used to be in
  `LOG.md`'s table only.
- 2026-10-29: restructure step 7, round 2: the rule for the previous run (`times`, `earlier_runs`, `previous_run`) is
  here and goes by time, not by folder name (see above). It had been put in `layout.py` by name, which was a
  regression for the comparison against main (two runs on one day, `-2` and `-10`). It also fixes the same flaw
  main already had in mark carry-over, on purpose.
- 2026-10-29: restructure step 7, round 3: a run without a record is ordered by the date in its folder name first,
  and by its log's time only against a run of the same date (probe: `2026-10-10_ddddddd`, rendered again on 10-27,
  had sorted after `2026-10-20_eeeeeee`; for such runs only the marks carry-over was affected, and a results folder
  copied without file times did the same). A run with a record keeps its record's times.
- 2026-10-29: restructure step 7b: `FORMAT` is 2. The data inside a run changed shape in 7b: evidence entries, the
  reports the stages read from each other, `cap.testdata`'s counts, and the keys of the places on `review.html`
  name a stage by its name where they named it by a number. A run made between step 7 and step 7b has a record of
  format 1 and the old shape, and re-rendering or comparing it would be quietly wrong (`hidden_how` and the
  test-data line read the new names), so `read` refuses it and the one rule above (`made_before`) applies;
  `read_any` keeps its times for ordering. `made_before` moved here from `layout.py`, which does not know formats.
- 2026-10-30: O3: `version`, `until`, `prepared`, and `continued` (`FORMAT` stays 2); `stop_of` and `stopped_early`;
  `previous_run` skips a run that stopped before its coded steps were done.
- 2026-10-30: O3, fix round: `code`, a hash of the code the run used, beside `version` (`FORMAT` stays 2).
- 2026-10-30: M9 slice A: `not_started` (`FORMAT` stays 2).
- 2026-10-30: M9 slice B, fix round: `chosen`, the model reads a command chose.
- 2026-10-30: M9 slice B: `FORMAT` is 3; `qa`, `held`, and `released`; `amend`, `hold`, `release`, and `held_of`. A run
  made with format 2 is made before this version (the check of the run did not exist, so it has no `data/05-qa.json`).

## runner

Restructure step 7.

The runner takes a target to a run folder: intake, then the steps in `stages/stages.json` order, then the
validation, then the check of the run (`05-qa`, M9 slice B), then the report stage unless the check holds the run. It is
what `stages/05-report/run.py` was before the router step, without the reports (notes O1). It writes no report and
reads none; `walkdown.py` is a router over it.

Status: built.

### Inputs

```
python stages/_shared/runner.py <target> [--name N] [--fresh | --keep] [--sweep B] [--pinpoint B] [--reads [M]] [--until STEP]
    [--revalidate] [--context N] [--hosts a,b] [--repo R] [--results DIR] [--date D] [--no-validate]
python stages/_shared/runner.py continue <run folder> [--sweep B] [--pinpoint B] [--reads [M]] [--until STEP]
    [--revalidate] [--context N] [--hosts a,b] [--no-validate]
```

The options are declared once, in `options.py` (`add_run_options`; the last four are the developer options the
front door does not take). `audit(a, python=None) -> (run folder or None, exit code)` takes them already parsed and
checked (`options.check`: the parked options refused, `--until`, `--hosts`, and `--context` read). `main(argv)` does both and
prints the run folder's path. `resume(run_dir, a, python=None)` is `continue` (below), and `main` routes to it when the
first argument is `continue`.

### Behavior

1. Intake runs first (`pipeline.run_intake`), before any run folder exists, with its two files held in a scratch
   folder. Its notes (or its error) are repeated on this process's stderr. When it fails (a login needed, a clone
   that fails, a folder that is not a clone of the URL, a file, a path that is not a folder) nothing else runs and
   no run folder is made: exit 2. Otherwise the folder to audit and the run's name come from its `intake.source`
   finding (`--repo` wins over the name).
2. A results folder inside the audited folder is refused (exit 2, nothing written there).
3. It works in `<results>/<repo>/.running-<date>`, saves intake's two files in `data/` byte for byte, runs
   `pipeline.run_stages` there (the coded steps, and an AI stage only when chosen; `--pinpoint` without `--sweep` prints
   `note: --pinpoint needs --sweep; no pinpoint questions asked`; a chosen Pinpoint after a Sweep in which no passage
   got an answer is not started, and prints `note: the step "The line behind each flag" did not run: no passage got an
   answer from the step "Needs a human read", so there is nothing to pinpoint`, M9), then renames the folder
   `<date>_<hash7>` (hash from the inventory's `inv.pin`), or `<date>_failed` when the inventory failed; `-2`, `-3`
   when the name is taken (`free_name`).
4. It validates intake and each step that was to run and was started (`validate.stamps`, unless `--no-validate`), with
   the sweep choice the run used in the grader's environment (`WALKDOWN_SOFT_SWEEP`, as `options.ai_choice` gives it: the option, else
   at a run the variable, with the model as typed, and `WALKDOWN_SOFT_CLAUDE_MODEL` when a `claude-cli` names none; an off value is no
   choice; M1 slice A: a Sweep chosen by the variable was graded with it and cached as if nothing had been chosen) so
   Sweep's stamp measures that backend, and the check of the run (`05-qa`) in the same pass. A stage with no fixture set
   (Pinpoint) is stamped `no fixture set`. A step that was not started (above) gets no stamp. The check's stamp is made
   from its own fixtures and needs nothing from this run, so it is taken here, before the record, and the record holds it;
   the check then reads it like any step's stamp, and a stamp of its own that is not a pass is a gap
   (`stages/05-qa/specs/qa.SPEC.md`).
5. It writes the record (`data/run.json`, the `record` section): every step with its times and error, the stamps, the
   expected context (`--context`, else 32,000) and the target hosts, `not_started` when a chosen step was not started, and
   `chosen`, the model reads this command chose.
6. It starts the check of the run on the run folder (`pipeline.run_qa`: `stages/<qa folder>/run.py <run folder> --brief`),
   which reads the record and the steps' saved outputs and writes `data/05-qa.json` (its stdout) and `data/05-qa.notes.txt`.
   The record gains `qa` (`{"started", "finished"}`). A check that crashed leaves no `05-qa.json`: the run did not finish
   (`stage 05-qa failed: <error>`, exit 1, no brief, no report).
7. With **no gap** it starts the report stage on the run folder (`stages/<report folder>/run.py <run folder>`, the folder
   from `stages.json`, with the same Python), its stdout captured and its stderr left to show. The report stage's exit
   code is the run's unless a step failed.
8. With **a gap or more** the run is **held** (M9 slice B): the check wrote `brief.md` (its own words, the gaps, and the two
   ways on), the record gains `held` (`{"by": "05-qa", "gaps": N}`), no report is written (no page, no `LOG.md`, no
   `data/limits.md`), and the exit code is 1. The brief is what `walkdown.py` prints.
9. A step that failed is named on stderr (`stage <name> failed: <exit code and the error's type>`; the end of its
   messages is in `data/<step>.notes.txt`) and the exit code is 1. A step that failed is a gap, so the run is held;
   `continue` writes the reports, which show it.

Exit 0 when every step ran and the reports were written; 1 when a step failed, the run is held, or the report stage failed;
2 for a target intake cannot use, a results folder inside the input, or an option refused.

**`--until <step>`** (O3): the run stops after a step, so a person can look before it goes on (`stages/*/CONTEXT.md`
each name a check between steps).

- The steps to run are `stages_to_run` cut at the named step (`pipeline.cut_at`): intake, then the steps through the
  named one; nothing after it runs. A stop is only a stop when a step of that list comes after the named one:
  `--until 04-pinpoint` (the last step of the run) is an ordinary run, and so is `--until 02.6-builder` when no
  model read was chosen.
- When the next step this run would run is a chosen AI step, that step runs with `--input-only` (`pipeline.run_input_only`):
  `data/<step>.input.jsonl` is written, exactly what the step would send, and nothing is sent; it leaves no
  `<step>.json`, and its messages are kept as `<step>.notes.txt`. A stop further back writes no input file. If that
  step fails, the failure is a step of the record and the run did not stop as asked (exit 1).
- Filed like any run, under the same name rule. A run stopped after intake has no pin: it is named `<date>_stopped`
  (never `_failed`; `-2`, `-3` when taken).
- The record gains `version`, `until` (a stop only), and `prepared` (the step, how many items its file holds, the
  backend that wrote it; `record` section). Validation stamps are made for the steps that ran, and the grader gets the
  sweep choice only when the sweep ran. The report stage runs as usual.

**`continue <run folder>`** (`resume`): goes on in the same run folder.

- The run folder is made absolute where it enters the runner (`resume`'s argument, and `--results` in `audit`): the report
  stage is started in Walkdown's own folder, so a relative path would name another folder there.
- It refuses, with one error line, exit 2, and nothing in the folder changed. The cheap checks come first, in this
  order, and the inventory is run again only after all of them: the folder is not a run folder, or was made before
  this version (`record.made_before`); a step in it failed; the run did not stop (no `until`); the record's `version` is
  not this Walkdown's (`this run was stopped by Walkdown <v>; this is <v>; audit the repository again`); the record's
  `code` is not the hash of this Walkdown's code (`the code of Walkdown changed since this run stopped; audit the
  repository again`; a record with no `code` counts as changed); a step the record says ran has no saved output in
  `data/` (`the run folder is missing the output of "<plain>"; audit the repository again`); `--until` names a step at
  or before the stop; there is nothing to run (`nothing to run after "<plain>"; choose --sweep to go on`, naming the
  option of the first AI step not yet run); the folder intake named is gone, or its intake report cannot be read. Last,
  when the inventory ran (the stop is at or after it), it is run again into a temporary folder and its report compared
  with the saved one: any difference refuses (`the folder changed since the run stopped; audit it again`), but a saved
  inventory that is not a report is the run folder's fault and not the folder's, and says so
  (`the run folder has no readable output of "What ships"; audit the repository again`). A run stopped
  after intake has no inventory to compare, and its brief says the folder is read as it is when the run goes on.
- It runs the steps after the stop: every coded one not yet done, and an AI step only when its option is given at this
  command (the first command's choice is not carried, and neither is an environment variable: choosing at `continue` is
  the consent to send, the `options` section). A set `WALKDOWN_SOFT_SWEEP` or `WALKDOWN_SOFT_PINPOINT` with no option
  gets a `note:` saying it is not read. An AI option for a step that
  already ran gets a note and is ignored; `--pinpoint` without a sweep that ran or is chosen gets today's note. The
  steps go into the run's `data/`. A run stopped after intake is renamed `<date>_<hash7>` with `free_name`, keeping its date
  (`<date>_failed` if the inventory failed).
- It validates the steps it ran and merges the stamps with the saved ones, rewrites the record (its steps with the new
  ones after them; `finished` anew; `until` and `prepared` set by this command's own stop, or gone; `continued` gaining
  `{after, at}`; `chosen` the reads that already ran and the ones chosen at this command; `dropped` the reads an earlier
  command chose that it leaves out, each with a note on the terminal once its steps have run, `note: "<plain>" was chosen by an
  earlier command and is not run here; <dropped_how>`, except for one whose option was given here and that could not run for
  want of the sweep, which has its own note), and starts the report stage. The exit codes are an audit's.
- Once it is past its refusals and before any step runs, it takes out what the report stage and the check wrote for the
  stop (`clear_report`): the pages, `changes.md`, `LOG.md`, `brief.md`, `data/limits.md`, and `data/05-qa.json`. `marks.json`
  is the reader's and stays. A refusal removes none of them. A run on which the check then crashes has no page of the stop,
  so a person never reads one as the finished run's.
- `--context` and `--hosts` given here replace the record's; otherwise the record's stay.
- After the steps, the check of the run reads the whole run again (the new outputs, the merged stamps, the rewritten
  record) and holds it again if it still has a gap.

**`continue` on a held run** (`release`, M9 slice B): the owner's second way on from a hold, "write the report with what it
has". It runs no step and no grader, and the run's outputs are left as they are.

- A held run is released whatever else it is, a stopped one and a run with a step that failed included (O3's refusal of a
  failed step is for a stopped run that is gone on with). It does not look at the audited folder: no step reads it.
- It refuses, with one error line, exit 2, and the folder as it was: a model option (`--reads` too, named as the person typed it),
  `--until`, or `--revalidate` (`this run
  is held, and continue writes the report with what ran and runs no step, so --sweep cannot be given; leave it out, or audit
  the repository again`: choosing a read at `continue` is the consent to send, so it is refused and not ignored, and the
  grader is not run, so there is nothing to measure again); a record whose
  `version` is not this Walkdown's (`this run was held by Walkdown <v>; this is <v>; audit the repository again`); a record
  whose `code` is not the hash of this Walkdown's code (`the code of Walkdown changed since this run was held; audit the
  repository again`). `--context` and `--hosts` given here are kept in the record.
- `LOG.md` is removed if there is one, and the report stage writes the report (it is started with `--released-at <time>`,
  and with the `--context` and `--hosts` given here: while it runs the record still says held): the pages name every gap as
  a step that did not work and in section 7, and `LOG.md` says the hold and its release. Only once it has exited 0 does the
  record's `held` become `released` (`{"by", "gaps", "at"}`, the same time) and the `--context` and `--hosts` are kept.
  `brief.md` is then the report's brief. A command killed anywhere before that leaves a run that is still held, so the
  command its brief prints works again. The exit code is an audit's: 1 when a step failed, else 0. A released
  run that also stopped (`until`) is still a stopped run: the next `continue` goes on with the steps it left out, and the
  check holds it again if the gap is still there. The report stage run by itself on a held run refuses it, with one line
  that gives the command (`error: this run is held by the check of the run, so no report is written; python walkdown.py
  continue <run folder>`).
- If the report stage fails (it exits other than 0), the run goes back to held (`held_again`): the pages and `LOG.md` it
  wrote are removed and the hold's brief is written back as it was (the record was not touched: `held` as before, no
  `released`, the `--context` and `--hosts` as they were), and one line says so on the terminal (`error: the report stage failed
  (exit N), so no report was written and the run is held again; python walkdown.py continue <run folder> tries again`). The
  exit code is the report stage's. The brief that says no report was written stays true, and `continue` can be run again
  once the cause is gone.

### Must never

- Write a report, LOG.md, or the limits: those are the report stage's. (`continue` removes LOG.md and writes no text
  into it.)
- Change the folder of a run it refuses, or send anything: `--input-only` makes no client and reads no key.
- Write inside the audited folder, or import a stage's code (steps run as subprocesses).
- Parse an option itself: the front door and `main` use the one parser in `options.py`.

### Done when (each backed by a test in `tests/test_runner.py`; the hold and release rules 16 to 22)

1. A run on a tiny skill leaves `data/` with the intake files, every step's output and notes, `run.json`, and
   `limits.md`, and at the top exactly `LOG.md`, `brief.md`, and the four reports; the input is byte-identical
   afterwards (`test_run_folder_and_documents`).
2. The record holds the steps, the stamps, and the options, and the log follows it
   (`test_the_record_holds_the_steps_the_stamps_and_the_options`); the grader runs with the sweep choice, and an
   off value chooses nothing (`test_a_chosen_sweep_is_the_choice_the_grader_runs_with`).
3. The parked options and variables are refused before anything runs
   (`test_the_parked_options_are_refused_before_anything_runs`,
   `test_the_parked_environment_variables_are_refused_before_anything_runs`); `--context` and `--hosts` reach the
   log, the pages, and the brief, and a bad value is exit 2 (`test_context_and_hosts_reach_the_log_the_pages_and_the_brief`).
4. A chosen AI stage that failed is a step that did not work, on the pages, the brief, and the limits
   (`test_a_chosen_ai_stage_that_failed_is_a_step_that_did_not_work`); `--pinpoint` alone runs neither
   (`test_pinpoint_without_sweep_runs_no_ai_stage_and_says_so`).
5. A second run on the same date gets `-2` (`test_second_run_gets_suffix`); a results folder inside the input
   exits 2 (`test_results_inside_input_refused`); the run is named for intake's name unless `--repo` is given
   (`test_the_run_is_named_for_intakes_name_unless_repo_is_given`); a target intake cannot use stops the run before
   any folder (`test_a_copy_intake_cannot_get_stops_the_run_before_any_folder`); intake has a row and no section
   (`test_intake_runs_first_and_has_a_row_but_no_section`).
6. The report stage starts last, on a folder that holds only `data/`, and a failing report stage is the run's exit
   code (`test_the_runner_writes_no_report_and_the_report_stage_runs_last`).
7. Sending data out reaches the summary (`test_sending_data_out_reaches_the_summary`, review C39).
8. `--until` (O3): a stop after a coded step runs the steps through it and no more, records `until`, `version`, and the
   stamps of the steps that ran (`test_until_stops_after_the_named_step_and_the_record_says_so`); a stop after intake is
   named `<date>_stopped` (`test_a_stop_after_intake_is_named_stopped_and_going_on_renames_it`); a name that is the
   run's last step is an ordinary run (`test_until_the_last_step_is_an_ordinary_run`); a stop just before a chosen AI step
   writes its input file, sends nothing, and records `prepared`
   (`test_a_stop_just_before_a_model_read_writes_its_input_file_and_sends_nothing`); a stop after any step builds
   every report (`test_a_stop_after_any_step_builds_every_report`).
9. A stopped and continued run equals a straight run's step outputs, byte for byte
   (`test_a_stopped_and_continued_run_equals_a_straight_run`), on a fixture repository
   (`test_a_stopped_and_continued_run_on_a_fixture_repository_equals_a_straight_run`), by two stops and by intake
   (`test_two_stops_and_going_on_twice_equal_a_straight_run`, `test_a_stop_after_intake_is_named_stopped_and_going_on_renames_it`).
10. Each refusal of `continue` is one error line, exit 2, and the folder as it was
    (`test_each_refusal_of_continue_is_one_line_and_changes_nothing`); an AI step runs only when chosen at the
    command, and an option for a step that ran is ignored with a note
    (`test_continue_runs_an_ai_step_only_when_chosen_here_and_ignores_one_that_ran`); an environment variable chooses
    nothing at `continue`, and a note says so
    (`test_at_continue_only_the_option_chooses_an_ai_step_never_the_variable`).
11. A relative run folder works from any working folder, for `--results` and for `continue`
    (`test_a_relative_run_folder_works_from_any_working_folder`, `tests/test_walkdown.py::test_a_stop_and_continue_through_the_router_print_the_two_briefs`).
12. A folder missing the output of a step the record says ran is refused, so the inventory comparison cannot be skipped
    (`test_a_run_folder_missing_a_steps_output_is_refused`); the cheap refusals come before the inventory is run again
    (`test_the_cheap_refusals_come_before_the_inventory_is_run_again`); the code is checked as well as the version
    (`test_the_code_of_walkdown_is_checked_as_well_as_its_version`); `marks.json` is kept byte for byte
    (`test_continue_keeps_marks_json_byte_for_byte`).
13. A test finds no real model to call, in the test process and in the Python processes it starts with the environment it inherits.
    One wall is up for the whole pytest session before any test module is imported (the root `conftest.py`, with
    `tests/offline/offline_env.py`), whenever pytest finds the repository's `pytest.ini`: no model key and no WALKDOWN_SOFT_*
    variable in the environment; no folder with a `claude` program on the PATH; the stub for `typesafe_sdk` (it makes no call; imported, it
    exits 97, and in a running test it raises `WallBreach`, a `BaseException`, so that test fails with the line and the session goes on)
    first on `sys.path` and on PYTHONPATH; no read of a model key from the Windows registry, here (`block_registry`) and in every
    Python process a test starts (`tests/offline/stub/sitecustomize.py`). A test that wants a fake puts its own on its own PATH or
    passes its own runner. The one exemption is `stages/_shared/tests/test_claude_isolation_live.py`, only when
    WALKDOWN_LIVE_CLAUDE=1, with the machine's PATH saved before the wall. The wall does not reach: a session started with
    `--noconftest`, with `--confcutdir` below the root, or with `-c` of an ini file below the root; a Python process started with `-I`
    or `-E` or with PYTHONPATH dropped (no stub, no registry block); an environment a test builds from nothing; a program started by its
    full path. The wall's own proof, from inside a test and from a subprocess, and that it is up from the root, from a stage folder, and
    on a single file, on a fake machine that has a `claude` and keys: `tests/test_the_wall.py` (written for Linux and macOS too, with an
    executable `claude` script for the fake; run on Linux, and not yet on macOS); the offline dict is `tests/test_offline.py`.
14. A chosen Pinpoint after a Sweep in which no passage got an answer is not started: the record says why, it has no
    stamp, and the terminal gets a note; `continue --pinpoint` on such a Sweep does the same, and a Pinpoint that was
    started leaves no `not_started`
    (`test_a_chosen_pinpoint_that_was_not_started_is_in_the_record_and_said_on_the_terminal`,
    `test_continue_does_not_start_a_pinpoint_after_a_sweep_that_got_no_answer`,
    `test_a_run_whose_pinpoint_was_started_has_no_not_started_in_its_record`).
15. The stop just before a Pinpoint (`--until sweep`, or a `continue` with `--until`) respects the same hold: after a
    Sweep in which no passage got an answer, `prepare_next` writes no input file for it and does not run the step, adds
    to `not_started`, and the note is the same; the run is then one that went through (no `until`, no `prepared`, no
    stop lines, no "To go on" line, and `continue` refuses it as a run that did not stop). After a Sweep that got answers
    the input file is written as before
    (`test_the_stop_before_the_pinpoint_writes_no_input_file_after_a_sweep_that_got_no_answer`,
    `test_a_continue_that_stops_before_the_pinpoint_writes_no_input_file_after_a_sweep_that_got_no_answer`,
    `test_the_stop_before_the_pinpoint_still_writes_its_input_file_after_a_sweep_that_got_answers`).
16. The check of the run is stamped with the steps and before the record, which holds its stamp, and records its times
    (`test_the_record_holds_the_steps_the_stamps_and_the_options`); it runs after the record on a straight run, a stopped
    run, and a continued run (`test_the_check_runs_on_a_straight_run_a_stopped_run_and_a_continued_run`); a run with no gap
    is not held (`test_a_run_without_a_gap_is_not_held_and_the_check_ran_on_it`).
17. A run with a gap is held: exit 1, `held` in the record, no page and no `LOG.md`, `brief.md` the hold's brief with its
    two ways on (`test_a_run_with_a_gap_is_held_no_report_is_written_and_the_brief_says_how_to_go_on`); a chosen read that
    failed is held and `continue` releases it all the same
    (`test_a_chosen_ai_stage_that_failed_is_a_step_that_did_not_work`); a read that got no answer exits 1, where it
    exited 0 before (`test_a_chosen_pinpoint_that_was_not_started_is_in_the_record_and_said_on_the_terminal`,
    `test_the_stop_before_the_pinpoint_writes_no_input_file_after_a_sweep_that_got_no_answer`).
18. `continue` on a held run runs no step and no grader, leaves the outputs as they were, and writes the report with what
    the run has (`test_continue_on_a_held_run_runs_no_step_and_no_grader_and_writes_the_report`); a held run that is also a
    stopped one is released and stays stopped
    (`test_a_stopped_run_with_a_gap_is_held_and_continue_releases_it_without_going_on`).
19. It refuses a model option, `--until`, or `--revalidate`, and a run held by other code, with one line each and the folder
    as it was (`test_continue_on_a_held_run_refuses_a_model_option_and_until_and_a_run_of_other_code`,
    `test_continue_on_a_held_run_refuses_revalidate`); it keeps the `--context` and `--hosts` it is given
    (`test_continue_keeps_the_context_and_hosts_it_is_given_when_it_releases_a_run`).
20. The report stage by itself will not draw a held run
    (`test_the_report_stage_will_not_draw_a_held_run_and_names_continue`).
21. A check that crashed is a run that did not finish (`test_a_check_that_crashed_leaves_a_run_that_did_not_finish`).
22. A crashed step keeps its exit code and its error's type in the record, `LOG.md`, and the terminal, and text from its
    stderr is in none of them (`test_a_step_that_crashed_is_held_with_its_error_type_only_and_continue_writes_the_pages`;
    for each way a step can end, `test_nothing_a_crashed_step_prints_reaches_a_file_a_person_reads_or_the_terminal`).
23. `continue` takes out the pages and the check's output of the stop before any step runs, and a refusal takes out none
    (`test_continue_takes_out_the_pages_of_the_stop_before_any_step_runs_and_a_refusal_takes_out_none`); a check that
    crashes during `continue` leaves no page (`test_a_check_that_crashes_during_continue_leaves_no_page_of_the_stop`); a
    run held again leaves the brief and no page
    (`test_a_held_run_that_continue_holds_again_has_no_page_from_the_first_release`).
24. A saved output that is valid JSON and no report (`[]`, `{}`) is a gap in the check and no crash in the release
    (`test_a_saved_output_that_is_json_and_no_report_is_held_and_released_without_a_crash`).
25. A report stage that fails during a release puts the run back to held, with the hold's brief, and `continue` can be run
    again (`test_a_report_stage_that_fails_during_a_release_puts_the_run_back_to_held`).
26. A read an earlier command chose and `continue` leaves out is named by `reads_left_out` (not one that ran, one chosen here,
    or one held back; one dropped before stays dropped) and said: in the stop's brief, in a note at `continue`, and in the
    record, the log, section 6, section 7, and the brief afterwards, with no gap
    (`test_reads_left_out_names_what_an_earlier_command_chose_and_this_continue_did_not`,
    `test_a_read_chosen_by_the_first_command_and_left_out_at_continue_is_said_and_never_dropped_silently`); with two reads
    chosen and one chosen again at `continue`, only the other is left out
    (`test_with_two_reads_chosen_and_one_chosen_again_at_continue_only_the_other_is_left_out`); a read left out at one
    `continue` is still left out and still said at the next
    (`test_a_read_left_out_at_one_continue_is_still_left_out_and_still_said_at_the_next`).
27. An inventory with no pin does not crash the runner or the report
    (`test_an_inventory_with_no_pin_does_not_crash_the_runner_and_its_run_is_filed_held_and_released`), and a stopped run
    whose saved inventory is no report is refused for that
    (`test_a_stopped_run_whose_saved_inventory_is_no_report_is_refused_for_that_and_not_for_a_changed_folder`).
28. A command killed while it releases a held run (before the report stage starts, after it has written the report, at the
    write of the record) leaves a run that is still held, and the same command then releases it, with one time in the record
    and in `LOG.md`
    (`test_a_command_killed_while_it_releases_a_held_run_leaves_a_run_the_same_command_releases`).
29. `continue` takes out the files `clear_report` names and no other: a person's own `.html`, `.md`, and files under `data/`
    beside the run stay (`test_continue_takes_out_only_the_files_the_report_stage_names_and_leaves_a_persons_own`).
30. The record after a `continue` lists the reads that already ran with the ones chosen at that command
    (`test_continue_records_the_reads_that_already_ran_among_the_ones_chosen`).
31. The grader's stamp is measured for the backend and the model the person typed (the option, else the variable at a run, not at
    `continue`; `WALKDOWN_SOFT_CLAUDE_MODEL` when a `claude-cli` names none), and a stamp is cached by that
    (`test_the_stamp_is_measured_for_the_backend_and_the_model_the_person_typed`,
    `test_a_sweep_chosen_by_the_variable_is_graded_for_that_backend_too`,
    `test_the_model_the_cli_will_run_from_the_environment_is_part_of_the_stamps_choice`).
32. `--reads` is resolved before the runner sees it, so the run it makes is the run the same `--sweep` and `--pinpoint` make: the record,
    the grader's choice, the stamps, and the pages hold the resolved values and nothing of `--reads`
    (`test_reads_leaves_the_record_the_typed_options_leave`), and the grader's stamp is measured for what it resolved to
    (`test_the_stamp_is_measured_for_what_reads_chose`); it goes with `--until` and `--revalidate`
    (`test_reads_goes_with_until_and_revalidate`).
33. `continue --reads` on a run where the Sweep ran chooses the Pinpoint alone, on one where it did not chooses both, reads no
    variable, and on a held run is refused by its own name
    (`test_continue_reads_on_a_run_where_the_sweep_ran_chooses_the_pinpoint_alone`,
    `test_continue_reads_on_a_run_where_the_sweep_did_not_run_chooses_both`,
    `test_continue_reads_reads_no_variable`, `test_continue_on_a_held_run_refuses_reads_by_its_own_name`).

### History

- 2026-09-29: built as the body of `stages/05-report/run.py` (stage 8 v1).
- 2026-10-29: restructure step 7: moved to `stages/_shared/runner.py` without the reports; the run-folder naming
  (`free_name`, `inside`), the grader's environment, and the run's record are here; the report stage is started as
  a subprocess instead of called.
- 2026-10-30: O3: `--until` and `continue` (`resume`). The stop, the input file of a stop, the `_stopped` name, and the
  record's new keys are above. `audit` and `resume` share `prepare_next` and `report_stage`.
- 2026-10-30: O3, fix round: the run folder (`resume`) and `--results` (`audit`) are made absolute, since the report
  stage starts in Walkdown's own folder (a relative path to `continue` ran the steps, rewrote the record, removed
  LOG.md, and then failed in the report stage); at `continue` only the option chooses an AI step; the refusals run in
  the order above, with the inventory last, and a folder missing a step's output is refused (a missing inventory file
  used to skip the comparison); the record's `code` is checked as well as its `version`.
- 2026-10-30: M9 slice A: a chosen Pinpoint is not started after a Sweep in which no passage got an answer; the record's
  `not_started`; no stamp for a step that was not started.
- 2026-10-30: M9 slice A, fix round: `prepare_next` respects the hold too. `--sweep jev --pinpoint claude-cli --until
  sweep` after a Sweep with no answers wrote an empty `04-pinpoint.input.jsonl` and offered `continue --pinpoint`, which
  would have run nothing; now there is no input file, the same note, `not_started` in the record, and no stop (`left`
  is taken less the held step by `without_held`).
- 2026-10-30: M9 slice B: the check of the run (`05-qa`) runs after the record and before the report on every run
  (`check_then_report`), and holds a run that has a gap (`held` in the record, `brief.md` the hold's, exit 1, no report);
  `continue` on a held run releases it (`release`, `cannot_release`) and runs no step. The check is stamped with the steps.
  `audit` and `resume` end in `check_then_report` where they ended in `report_stage`.
- 2026-10-30: M9 slice B, fix round: the record keeps `chosen` (`audit` and `resume`), so a chosen read that never started
  is told from one nobody chose.
- 2026-10-30: M9 slice B, second fix round: `release` records the release after the report is written (the report stage is
  started with `--released-at`), and no longer before; a command killed in the middle left a record that said released, a
  brief that said held, and a command that was refused. `held_again` no longer has a record to put back.
- 2026-10-30: M9 slice B, second fix round: the record keeps `dropped` and `backends`. `--until 02.3 --sweep jev` and then a
  plain `continue` ran no sweep (right, under the rule that choosing at `continue` is the consent to send) and said nothing:
  the log and section 6 read "none was chosen". The stop's brief carries the options in its command, `continue` prints a
  note, and the pages say it; `--sweep jev --pinpoint claude-cli --until 02.3` and then `continue --sweep jev` drops the
  pinpoint the same way.
- 2026-10-30: M9 slice B, second fix round: the runner names a run by `pipeline.first_finding` (an inventory with no pin
  crashed it); a stopped run whose saved inventory is not a report is refused for that and not as a changed folder.
- 2026-10-30: M9 slice B, fix round: `continue` removes the pages, the brief, `changes.md`, the limits file, and the check's
  output once it is past its refusals (`clear_report`); before, a check that crashed during `continue` left the stop's pages
  beside a record that said the run had gone on. A report stage that fails during a release puts the run back to held
  (`held_again`; before, the record said released and the folder held a brief that said no report was written, or half a
  report). `--revalidate` is refused on a held run, as `--until` and a model option are. `report_stage` is `run_report`
  (the report stage's own exit code) and the failed-step rule.
- 2026-10-31: M1 slice A: `soft_grade_env` passes the choice as `options.ai_choice` reads it (the model as typed), and reads the
  variable too at a run: a Sweep chosen by `WALKDOWN_SOFT_SWEEP` was graded with it but cached under a fingerprint that held no
  choice. `WALKDOWN_SOFT_CLAUDE_MODEL` is passed for a `claude-cli` that names no model.
- 2026-10-31: M1 slice A, fix round 2: the tests' wall is one for the whole session (the root `conftest.py`, `tests/offline/offline_env.py`: `raise_wall`, `block_registry`, and `stub/sitecustomize.py`). `offline_env.offline` changed the environment of a subprocess only, so a broken rule in a step that runs in the test process, a `runner` or `which` ignored, a `client_factory` ignored, or a default that chose a backend, could reach the real `claude` or Jev with this machine's key (`read_key` fell through to the registry). The tests that built their own environment with `offline` use the session's now.
- 2026-10-31: M1 slice A, fix round 2: the `typesafe_sdk` stub fails the test that imports it (`WallBreach`, a `BaseException`) when pytest is
  running one, and keeps exit 97 for every other process. Exiting the pytest process lost the line (pytest holds a test's stderr): the run
  ended with exit 97 and an empty output.
- 2026-10-31: M1 slice A, fix round 3: the wall's guarantee is worded as what it is, with the exceptions named (Done-when item 13 above): the root `conftest.py` is not loaded by `--noconftest`, `--confcutdir` below the root, or `-c` of an ini file below the root, and a Python process started with `-I` or `-E` or without PYTHONPATH gets no stub and no registry block. They said "wherever pytest is started" and "nothing a test runs can call a model". `tests/test_the_wall.py` runs on Linux and macOS (a fake `claude` that is an executable script there, and counts and the registry line that depend on whether `winreg` exists).
- 2026-11-01: M1 slice A, before merge: the docstrings of `conftest.py` and `tests/test_the_wall.py` still claimed more than the wall does, and now say what Done-when item 13 says. Item 13 says the wall's tests have run on Linux and not yet on macOS.
- 2026-11-01: the loaded-model build: `cannot_release` names `--reads` when that is what the person typed (the options it resolved to are not theirs). Nothing else in the runner knows of `--reads`.

## secretmask

A report never repeats a secret it found, and a model read never sends one. Moved here from `02.4-phrases`'s runner (`mask_secret_lines`,
`SECRET_MASK`) in restructure step 4: `02.4-phrases` finds the secrets, and both it and
`02.6-builder` quote lines (`port.path`, `fit.loop`, `clean.*`), so both must mask a line a
secret sits on. `02.4-phrases`'s spec for it is `stages/02-coded/02.4-phrases/specs/phrases.SPEC.md`, section `secret_scan`.

`02.1-inventory`, `02.2-reader`, and `02.3-graph` keep words from lines too, and they run before the scan. `02.5-capability` and
`02.6-builder` copy words from `02.1-inventory`. So a step's words are masked after the last step that reads them, twice over:
`pipeline.mask_saved_reader` masks the saved reader once `02.5-capability` has read it, `pipeline.mask_saved` masks every saved
output once `02.6-builder` has read them or a step has failed, and the report stage masks what it loads (`06-report`'s `run.load`,
and `drift.load` for each run it compares), which covers a run stopped before those steps and a run saved before this rule.

`03-sweep` and `04-pinpoint` send lines off the machine, and a send cannot be taken back, so they hold back more than a page masks
(`ToSend`, below).

### Inputs

A list of findings that holds the `secret.found` findings of `02.4-phrases` (it may hold others whose
lines are to be checked). `mask_reader` takes the two steps' reports, and `mask_reports` a report for each step. `ToSend` takes
the findings of `02.4-phrases`, and each call the file's name and the lines `linetext` read.

### Outputs

`mask_secret_lines(findings, was=None)`, in place, for every finding that is not a `secret.found` and quotes a line that has a
`secret.found` on it in the same file:

- each text field that is a string (`TEXT_FIELDS`: what a person wrote, as it stands in the file) and each matched word
  (`matches[].text`) is replaced by `SECRET_MASK`. `NOT_TEXT` names a field that is a word from a fixed list for its check
  (`limit.setting`'s `value`, which `02.5-capability` reads);
- in a list whose items a person wrote and whose plain words are what a page is for (`WORD_LISTS`: `tools`, `grants`,
  `disallowed`, `preloads`, `env_keys`, `types`), an item that is a plain word stays and any other is replaced. A plain word
  (`PLAIN`) is letters, `-`, and `_`, up to 24 characters: `Read` stays, and `Bash(curl ...)` goes;
- in a list with nothing to keep (`WHOLE_LISTS`: `commands`, `shared`), each item is replaced, so how many there are stays;
- a word a config names (`PLAIN_FIELDS`: `event`, `transport`) stays when it is plain and is replaced otherwise, so a page still says
  when a masked hook runs;
- each list of code points (`chars`, `removed`) keeps each one once, sorted. In the order they stand, tag characters spell the text;
  once each and sorted, they still name the kinds a page counts.

`masked` is set true, on a finding that quotes the line for where it is, and on one a parser made (it has `span`, or is in `PLACED`)
for what it held, so a row with no words is not marked. The location stays. A `secret.found` that is a skip (`skipped`), or whose
only "secret" is base64 that decodes to readable text (`likely_not_secret` is `BASE64_TEXT`, review C42), masks nothing: it holds no
key, and its text is the instruction a reader needs. `was`, when given, collects `{file: the words masked}` for `mask_copies`.

The lines a finding quotes (`_lines_of`) are:

- its `span` (`02.1-inventory`'s `spans`, and `02.6-builder`'s `trigger` and `fit`), a value a parser read, which can run over many
  lines or have no `line` at all;
- for a finding in `PLACED` with no `span` key (a run saved before it was written, or a file that does not compose), and an
  `inv.license` with no line, any line of its file: nothing else says where its words sit, so a flagged line anywhere masks it. A
  `span` of null is a place known to have no lines of its own: a skill with no frontmatter;
- for a `soft.pinpoint`, the lines the model quoted (`pin_line` through `pin_end`), and none when it named none;
- for a `wrapped` finding, every line through its `end_line`;
- for a finding of `02.2-reader` (a `read.*` check), every line through its `end_line` (`02.2-reader`'s `reach`), or, in a run saved
  before the reader wrote that, as many more lines as its `text` holds line breaks. Such a run's hidden text whose line breaks
  were stripped or collapsed can name fewer lines than it sits on;
- otherwise its `line`.

A finding that names more than one place goes by what it holds at each (`_mask_places`):

- `endpoint.host`: `urls` in each occurrence on a flagged line. The `host`, `lookalike_of`, and `punycode` go only when every
  occurrence is on a flagged line, since then only a flagged line says the host;
- `term.conflict`: `text` in each definition on a flagged line, and the `term` when every one is;
- `rep.sentence`: the `sentence` when any place in `where` is flagged, since it stands at each;
- `rubric.action`'s `confirm_quote` by its `confirm_line`, `term.def`'s `term` by its `heading_line`, and each `also[].quote` of a
  `soft.pinpoint` by its own lines;
- `struct.manifests`, one row for the manifests of a plugin with no line for a grant: `grants[file]` as a word list when that file has
  a flagged line, and `name` when any of its files does;
- `need.package`, which has its files and no line: `package` when one of them has a flagged line and it is not a plain word.

A hook's `event` also goes by its own key's line (`event_line`), since an entry's `span` starts below it.

`mask_copies(node, was)`, in place: words masked at their source, wherever a later step copied them. `02.5-capability` and
`02.6-builder` copy a hook's command, an agent's description, a tool's name (`cap.injection`, `cap.posture`, `cap.limit`, `fit.hook`,
`cap.context`'s `unknown`), and none of those has a line to go by, so a copy goes by its value within one file: a string equal to a
word masked for that file (or for the file a `cap.limit` calls its `owner`) is replaced. An evidence entry that points at
`02.1-inventory` says such a word inside its `why`, which is replaced as a whole word. A finding with no file goes by the file of
each entry inside it. It returns whether anything was masked.

`mask_edges(graph, secrets)`, in place: in `graph.json`, an edge's `text` when (`from`, `line`) is flagged.

`mask_reports(reports, *side)`, in place: `reports` is `{step's name: its report}`, any of them absent or None, and `side` is reports
kept apart that hold `02.5-capability`'s findings (`capability.json`). It masks `02.1-inventory`, keeping its words; `02.2-reader`,
`02.3-graph`, `02.4-phrases`, `02.6-builder`, and `04-pinpoint`; and then the copies in `02.5-capability`, `side`, and `02.6-builder`.
With no `02.4-phrases` report, or nothing flagged, it changes nothing. Masking twice changes nothing more.

`mask_reader(reader, phrases)`: `mask_secret_lines` over the reader's findings and the `secret.found` findings of the
phrase report, in place. It returns whether a finding of the reader is masked now, and False when either report is missing.

`ToSend(phrase_findings)`: what of a file a model read may send.

- `lines(rel, lines)`: the lines as a read uses them, each one left out a blank at its place (`LEFT_OUT`), so every other line keeps
  its number. The list it was given when nothing is left out. None when the scan did not read the file, or there are no lines.
- `left_out(rel, lines)`: the numbers of the lines left out. Each line with a `secret.found` that is no skip, whatever its
  `likely_not_secret` says: a page shows a line marked `BASE64_TEXT`, and that mark looks at the line as a whole, so a key beside
  readable base64 gets it too. For a kind that names a private key (`PRIVATE_KEY`: `Private Key`, `private-key`), the rest of the key
  as well, since the scan flags only its first line: through the next line holding `-----END`, or with none through the line
  before the next blank line (a PuTTY file has no such line); nothing more when `-----END` is on the flagged line. A row whose line
  is not in the file adds nothing.
- `read(rel)`: whether the scan read the file: false for a file with a skip row, and for every file when the skip row names none
  (no scanner), since no row can say what is in such a file. A file of a build name in `agents/` or `commands/` goes by its rows, as any
  file does. The scan writes no row for a lock file (`secret_scan.LOCK_FILES`), and no read takes one: a read takes prose by its extension
  (`chunks.PROSE_EXTS`), and no lock file's name has one.
- `NOT_READ`: the reason a read gives for such a file. `left_out_note(count)`: the note that says how many lines a read left out, in words
  `limitnote` keeps as a limit.

What leaving a line out costs: the model does not read what stands beside the key on that line, and `02.4-phrases` still does. A
`BEGIN` line far above a `-----END` line leaves all between them out, and the count in the note shows that.

What it does not reach: the mask follows the scan, so a key the scan did not flag is not masked. That is a key seen only in a picture
or a PDF page (OCR, `02.2-reader`'s `image-text`, and what `review_html` shows as a place's image text), one spelled only in hidden
characters, one in a lock file, which the scan leaves out by name (`02.4-phrases`'s `secret_left_out`; a file it could not read is a skip), and
one in a file's own name. So a path is never masked: `file`, `to`, `from`, `resolves`, `graph.case`'s `written`, and `port.*`'s
`written`, `file_named`, and `script` each name a file that exists. The scan flags only a private key's first line, so a finding that
quotes a later line of the key is not masked (`ToSend` leaves the whole key out of what a model reads). `normalized/` holds each file's
own text.

### Must never

- Change a finding's location, check, count, flag, or a word from a fixed list; drop a finding or an item's place in a list; mask a
  line no `secret.found` is on; touch a `secret.found`; keep a hash of what it masks.

### Done when (each backed by a test in `tests/test_secretmask.py`)

1. Text fields and matched words on a secret line are masked and `masked` is set; the location and
   the other fields stay; a line with no secret is untouched; the `secret.found` is untouched.
2. A skipped scan masks nothing, and neither does a `secret.found` marked `BASE64_TEXT`.
3. A wrapped finding is masked by a secret on any of its lines.
4. `02.4-phrases`'s runner masks its own findings through it (`02.4-phrases/tests/test_secret_scan.py`),
   and the builder step masks the quotes it makes (`02.6-builder/tests/test_run.py`).
5. Every quote `02.2-reader` keeps of a flagged line is masked, and where and how the text hides stay
   (`test_every_quote_the_reader_keeps_of_a_flagged_line_is_masked_and_where_and_how_stay`).
6. A list of code points no longer spells the key and still names the kinds
   (`test_a_list_of_code_points_does_not_spell_the_key_and_still_names_the_kinds`).
7. Hidden text is masked by a flagged line anywhere in its reach, and not by one past it
   (`test_hidden_text_is_masked_by_a_flagged_line_anywhere_in_its_reach`); a run saved before `end_line` goes by the line
   breaks in its text (`test_a_run_saved_before_end_line_goes_by_the_line_breaks_in_its_text`); a finding of another step keeps
   its rule (`test_only_the_reader_gets_a_reach_a_finding_of_another_step_keeps_its_rule`).
8. A flag and a count are left alone (`test_a_flag_and_a_count_are_not_text`), a reader with nothing flagged is left as it is
   (`test_a_reader_with_nothing_flagged_is_left_as_it_is`), and masking twice changes nothing more
   (`test_masking_twice_changes_nothing_more`).
9. On a whole run of a made-up skill the key is in no report and no step output, and every hidden place is still counted
   (`06-report/tests/test_run.py`, `test_a_key_the_scan_flagged_is_in_no_report_and_no_step_output`).
10. `ToSend`: a flagged line is a blank at its place and the rest is as it was
    (`test_a_flagged_line_is_a_blank_at_its_place_and_the_rest_is_as_it_was`, `test_a_file_with_nothing_flagged_is_as_it_was`), also with a
    `likely_not_secret` mark (`test_a_line_marked_as_holding_no_key_is_left_out_too`); a file the scan did not read is not sent
    (`test_a_file_the_scan_could_not_read_is_not_sent`, `test_no_scanner_means_no_file_is_sent`, `test_no_lines_stay_no_lines`,
    and a file of a build name goes by its rows, `test_a_file_named_like_a_build_file_goes_by_its_rows_as_any_file_does`, while no lock
    file's name is one a read takes, `03-sweep/tests/test_secret_lines.py::test_no_lock_file_is_a_file_a_model_read_takes`); a
    private key goes through its end line (`test_a_private_key_is_left_out_through_its_end_line`,
    `test_a_private_key_on_one_line_takes_nothing_after_it`,
    `test_a_private_key_with_no_end_line_is_left_out_through_the_next_blank_line`), and another kind takes only its line
    (`test_another_kind_of_key_takes_only_its_own_line`); a row outside the file changes nothing
    (`test_a_row_outside_the_file_changes_nothing`); `left_out` names the lines (`test_left_out_names_the_lines`); the note counts them and
    names a limit (`test_the_note_counts_the_lines_and_names_a_limit`).
11. Every field of a person's words is masked (`test_every_field_of_a_persons_words_on_a_flagged_line_is_masked`), a word list keeps its plain
    words and a whole list how many (`test_a_word_list_keeps_its_plain_words_and_a_whole_list_keeps_how_many`), and a finding that quotes the line
    is marked with no words to mask (`test_a_finding_that_quotes_the_line_is_marked_for_where_it_is_with_no_words_to_mask`). A value is masked by a
    flagged line anywhere in its `span` and not past it, and how many commands there were stays
    (`test_a_description_or_a_hook_is_masked_by_a_flagged_line_anywhere_in_its_span_and_not_past_it`). With no `span`, any flagged
    line in its file masks it (`test_a_finding_a_parser_made_with_no_span_is_masked_by_a_flagged_line_anywhere_in_its_file`); a `span`
    of null is no lines (`test_a_span_of_none_is_no_lines_a_skill_with_no_frontmatter_is_not_masked_by_its_body`); a row with no words
    is not marked (`test_a_parser_finding_with_no_words_is_not_marked`).
12. A plain event or word stays and anything else goes (`test_a_plain_event_or_word_stays_and_anything_else_goes`), an event goes by
    its own line (`test_an_event_name_is_masked_by_its_own_line_when_the_entry_has_no_flagged_line`), and a word from a fixed list
    stays (`test_a_word_from_a_fixed_list_under_a_text_name_is_left_alone`).
13. A finding of several places goes by each (`test_an_address_goes_where_it_stands_and_a_host_only_when_every_place_is_flagged`,
    `test_a_conflict_masks_each_definition_where_it_stands_and_the_term_when_all_are_flagged`,
    `test_a_sentence_goes_when_any_place_it_stands_is_flagged`, `test_words_a_finding_quotes_from_another_line_go_by_that_line`,
    `test_a_manifest_row_goes_file_by_file_and_a_package_only_when_it_is_not_a_plain_word`,
    `test_a_models_quote_goes_by_the_lines_it_quotes_and_a_flagged_line_elsewhere_in_the_passage_leaves_it`).
14. A copy goes by its value within its file (`test_a_copy_goes_by_its_value_within_its_file_and_evidence_says_it_in_its_why`,
    `test_the_why_of_evidence_is_only_changed_for_a_whole_word`, `test_only_evidence_that_points_at_the_inventory_has_its_why_changed`,
    `test_a_finding_of_no_file_takes_no_words`), `mask_reports` covers every step and changes nothing with nothing
    flagged (`test_mask_reports_masks_every_step_and_its_copies_and_leaves_a_run_with_nothing_flagged_alone`), and an edge goes by
    its line (`test_an_edge_goes_by_the_line_it_comes_from`).
15. On a whole run of a made-up skill with one key in every place a step keeps a person's words, no key, whole or cut short, is in any
    report or step output, and each step read the words before they were masked (`06-report/tests/test_secret_fields.py`).

### History

- 2026-11-01: `02.2-reader`'s findings are masked (`mask_reader`), with `text`, `decoded`, and `folded` as text fields and `chars`
  and `removed` reduced. A divergence kept its text and `decoded`, so `full.md` and `data/02.2-reader.json` repeated a key the
  scan flagged, in hidden characters on its line, in a hidden comment, or on a later line of hidden text. The owner chose to
  mask the saved file as well as the reports (2026-11-01).
- 2026-11-01: `ToSend`, `NOT_READ`, and `left_out_note`. A chosen model read sent every line the scan flagged. The owner chose a blank at
  its place over `SECRET_MASK`: those words would stand in front of a model asked whether the text gathers secrets, with no way to
  measure the effect while model testing is on hold, and the pinpoint's quote check would accept a quote of them.
- 2026-11-01: `ToSend.read` is false for a name the scan leaves out. With no row, it said such a file was read, so a key in
  `agents/requirements.txt` went to the service chosen.
- 2026-11-01: `ToSend.read` no longer asks a name, and this module no longer imports `audience`. The scan reads build files now, so
  `agents/requirements.txt` goes by its rows, with its flagged lines blank. A lock file has no row, and no read takes one.
- 2026-11-01: the rule holds for every step. On a made-up skill with one key per place, 53 of 63 keys reached a report or a step
  output, in many more places than the five fields the notes had measured (`struct.description`, `struct.agent-tools`,
  `struct.hooks`, `graph.dangling`, `endpoint.host`): `struct.mcp`, `struct.manifests`, `inv.license`, `graph.dynamic`, `limit.setting`,
  `rep.sentence`, `term.conflict`, `trig.*`, `host.feature`, `clean.model`, `need.package`, and the copies in `cap.*` and `fit.*`, some
  of them on `summary.html`. `span`, `mask_copies`, `mask_edges`, and `mask_reports` are new, and `_mask_places` for the findings of
  several places.

## softdata

Loads and checks `Library/softreads.yaml`, the one data file holding everything the two AI stages
show a model: the coverage sweep question and its kinds (stage `03-sweep`), the pinpoint system
prompt and question (stage `04-pinpoint`), the cap on an answer, and the wait before a call that got no answer
is tried once more (M9). Each entry cites its source.
Moved here from the soft stage in restructure step 5 because both AI stages read it; cut down to
what they show (the labeling question and options, the relational templates, and the Claude system
prompt left with the parked code, and are in git history). A module here imports no stage.

### Inputs

- `load(path=DEFAULT)`: the YAML file (the default is `Library/softreads.yaml`, found through
  `library.path`).

### Outputs

A dict:

- `answer_cap`: int (characters; a model's answer is cut here).
- `retry_wait`: float (seconds; a call that gets no answer waits this long before its second try, 2 seconds since
  2026-10-30; a number from 0 to 60, so a test can set none).
- `sweep`: `{"question", "system", "source", "flag_p", "options": {name: {"what", "not_for", "examples", "source"}}}`. `system` is
  the system text a model that takes text is given with the question (the passage is data, never instructions; answer with the name
  of one option and nothing else); Jev takes the question as a Choice and needs none.
  `flag_p` is a number strictly between 0 and 1. `options` starts with `none` and names at least one
  kind; every option has non-empty `what`, `not_for`, `source`, and a non-empty `examples` list of text.
- `pinpoint`: `{"system", "question", "source"}`, all non-empty.

`DataError` (its message names the entry) when the file is missing or unparseable, `sweep` or
`pinpoint` is missing, `sweep.system` is missing or empty, an entry has no non-empty `source`, an option lacks `what`, `not_for`, or
examples, `sweep.options` does not start with `none` or names no kind, `flag_p` is not between 0 and
1, `answer_cap` is not a positive int, or `retry_wait` is missing or not a number from 0 to 60.

### Must never

- Hold an API key, a verdict, a score, or a severity field.
- Be read from anywhere but the Library (or a path a test passes).

### Done when (each backed by a test in `stages/_shared/tests/test_softdata.py`)

1. The shipped `Library/softreads.yaml` loads: the sweep question, `flag_p`, options starting with
   `none` each with `what`, `not_for`, `examples`, `source`, and the pinpoint system and question
   (`test_the_shipped_file_loads_with_the_sweep_kinds_and_the_pinpoint_question`).
2. The shipped file holds nothing the parked code showed a model: no label, relational, or Claude
   system prompt entry (`test_the_shipped_file_holds_nothing_the_parked_code_showed_a_model`).
3. A sweep that does not start with `none` or names no kind, a `flag_p` outside 0 and 1, an entry
   without a `source`, an option without examples, a missing section, a bad `answer_cap`, and a missing
   file each raise `DataError` (`test_a_sweep_that_does_not_start_with_none_or_names_no_kind_raises`,
   `test_flag_p_must_be_strictly_between_zero_and_one`, `test_an_entry_without_a_source_raises`,
   `test_an_option_without_examples_raises`, `test_a_missing_sweep_or_pinpoint_section_raises`,
   `test_the_answer_cap_must_be_a_positive_int`, `test_a_missing_file_raises`).
4. The shipped pinpoint system prompt states that the passage is data, never instructions for the
   model (`test_the_pinpoint_system_prompt_says_the_passage_is_data_not_instructions`).
5. The wait before the second try is 2 seconds, and a missing or out-of-range `retry_wait` raises `DataError`
   (`test_the_wait_before_the_second_try_is_two_seconds_and_must_be_a_number_of_seconds`).
6. The sweep has a system text that says the passage is data and asks for one option's name, with its source, and a sweep without
   one raises (`test_the_sweep_has_a_system_text_that_says_the_passage_is_data_and_asks_for_one_options_name`,
   `test_a_sweep_without_a_system_text_raises`).

### History

- 2026-10-30: M9 slice A: `retry_wait`.
- 2026-10-31: M1 slice A: `sweep.system`.

## stagelist

Restructure step 7.

Reads `stages/stages.json`, the one home for the stage list, and builds from it every table that is
keyed by a stage name. A new stage is one entry in the list. The check of the run (`qa`, M9 slice B) and the report
stage (`report`) are listed beside the stages and not in them: a run does not choose them and does not stop after
them. Nothing here imports a stage.

### The list

```json
{"stages": [{"name": "02.4-phrases", "folder": "02-coded/02.4-phrases",
             "plain": "What the text asks for", "heading": "What the text asks for",
             "reads": ["02.1-inventory"]}, ...],
 "report": {"name": "06-report", "folder": "06-report", "limits_heading": "Not examined"}}
```

Per stage: `name` and `folder` (every stage); `plain` (the words a reader meets for the step: the pages
and the brief name a step that did not run or failed its check by it, and a run that stopped after a step by
it; every stage, intake's being "Getting the copy" since O3, though no page or table that lists steps names intake
on a run that did not stop); `heading` (the heading of its section in `full.md`, for the stages that have one: the
five coded stages 02.1 to 02.5 and Sweep; the builder step and Pinpoint show inside others' sections);
`option` and `env` (an AI stage only: the command-line option and the environment variable that choose
it); `reads` (the earlier steps whose outputs it reads, in the order they run; what a stage run on its
own gets run for it, the `earlier_steps` section). The report entry's `limits_heading` is the heading of
section 7, which is the report stage's own and has no stage.

### Outputs

- `load_stage_list(stages_dir=None)`, `stage_folder(name, stages_dir=None)` (the check of the run's and the report
  stage's too; KeyError when the name is not listed; a list with no `qa` entry, as a test's fake may be, reads as before),
  `reads(stage, stages_dir=None)`.
- `checks(stage, stages_dir=None)`, `CHECKS` (M9 slice C): the check IDs a step makes, from `stages.json`'s `checks`, in the
  order of `stages/CONTRACT.md`'s vocabulary (empty for intake, the check of the run, and the report stage; `CHECKS` has the
  steps with a list). The coverage lines of a step cover exactly these; a test holds the list to the contract
  (`test_the_checks_in_stages_json_are_the_checks_the_contract_lists_for_each_step`).
- `STAGES` (names in run order), `INTAKE` (the first), `FOLDER_STAGES` (the rest), `AI_STAGES`, `CODED`
  (the folder stages that are not AI stages), `QA` (`05-qa`), `REPORT`, `AI_OPTION`, `AI_ENV`.
- `PLAIN` (name to plain name), `PLAIN_WITH_LIMITS` (the same with `"07-limits"` last), `STEP_WORDS` (the same with the
  check of the run, "Checking the run", after it: every step a page or the brief can name), `HEADINGS` (the
  sections of `full.md` in order, `"07-limits"` last), `LIMITS` (`"07-limits"`).
- `position(name)`: the stage's place in the list, counted from 0 (KeyError when it is not listed). A sort
  by stage uses this, so an order follows the list.

### Must never

- Hold a table of its own: the list is the only source.
- Import a stage's code.

### Done when (each backed by a test in `tests/test_stagelist.py`)

1. The tables follow the list (`test_the_list_is_read_from_stages_json_and_the_tables_follow_it`);
   folders come from it and every folder has its runner (`test_folders_come_from_the_list_and_every_one_has_its_runner`).
2. Plain names and headings (`test_each_stage_a_reader_meets_has_a_plain_name_and_the_sections_have_headings`);
   an AI stage has an option and a variable and a coded stage neither (`test_an_ai_stage_has_an_option_and_a_variable_and_a_coded_stage_has_neither`).
3. A stage reads only what runs before it (`test_a_stage_reads_only_what_runs_before_it`); a stage's
   position follows the list (`test_position_follows_the_list`).
   The check of the run is listed beside the stages and not in them, and has its runner
   (`test_the_check_of_the_run_is_listed_beside_the_stages_and_not_in_them`); every step a page can name has its plain
   words (`test_every_step_a_page_can_name_has_its_plain_words_the_check_of_the_run_included`); a list with no `qa` entry
   still gives the other folders (`test_a_stage_list_without_a_qa_entry_still_gives_the_other_folders`).
4. The report's `STATUS` and `SECTIONS`, which stay code, have exactly the keys of the stages with a heading
   (`stages/06-report/tests/test_render.py::test_the_stage_tables_are_built_from_the_stage_list_and_status_and_sections_are_checked_against_it`).

### History

- 2026-10-28 (restructure step 1): the list in `stages.json`, read by `pipeline.py`.
- 2026-10-29: restructure step 7: read here, with the plain names, headings, AI options, and `reads` it gained; the
  tables `render.HEADINGS`, `ORDER`, `LOG_ROWS`, `NAMED`, `STEP_NAMES`, `AI_STAGES`, `details_html.PLAIN_STAGE`,
  `walkdown.STAGE_NAMES`, `pipeline.AI_OPTION`, `AI_ENV`, `drift.STAGES`, and the `NAMES` of the stages that read
  reports are built from it (notes M7).
- 2026-10-29: restructure step 7b: `legacy_key` is gone. The reports inside a stage are keyed by stage name, so no
  stage turns a name into a two-digit number; `position(name)` is added for sorts.
- 2026-10-30: O3: `01-intake` has a `plain` name ("Getting the copy"), so a run stopped after intake is named by it.
  `stagelist.py` itself is unchanged (its code is part of the phrase step's `terms.code`).
- 2026-10-30: M9 slice B fix round: the check of the run's entry is read here (`QA`, `STEP_WORDS`, and `stage_folder`),
  and `qastep.py`, which read it apart from this file so that `terms.code` (the version of the phrase step's code, which
  includes the modules the step imports) would not move, is gone. `terms.code` moves once, with this change: a run made
  after it says the phrase matching changed against one made before, though none of the matching did.
- 2026-10-30: M9 slice C: `checks(stage)` and `CHECKS`, from `stages.json`'s new `checks` per step. `terms.code` moves again,
  as the brief says it will, with the phrase step's own scripts.

## stagenote

M9 slice B, second fix round.

How a step writes a note on its stderr. A step's notes (`data/<step>.notes.txt`) are where the check of the run and the pages
read Walkdown's own words from a step: the line it wrote as `note: ...` is a limit of the run. A note often names a file or a
path from the audited repository, and a name can hold a newline. Written as it is, the rest of the name starts a line of its
own, and a name that carries `note: ` after a newline reads as a note the step wrote. Every note, and the reader's warning
that names a file, goes through here and is flattened to one line.

### Outputs

- `flat(text)`: the text on one line (every run of whitespace, a newline and the unicode line separators included, is one
  space).
- `note(text)`: `note: ` and the text, on stderr, on one line. `warning(text)`: the same with `warning: ` (the check does not
  read warnings).
- `flat(text, cap=None)` (M1 slice A): with `cap`, a longer line is cut to that many characters and ends in `...`. A value that comes
  from a service (the model that answered) reaches a page or a note only so, in one line, cut to `MODEL_CAP` (80).
- `progress(who, done, total)` (M1 slice A): one plain line, `sweep: 25 of 431 passages done`, with no `note: ` in front, so the check
  of the run does not read it as one of the step's notes. It takes a name and two counts, so nothing from outside can be in it.
  `is_progress(line)` says whether a line is one, and `show_progress(line)` is the runner's: it writes such a line to its own stderr
  and nothing else. A line is one only if the whole of it matches `PROGRESS`, `(sweep|pinpoint): [0-9]+ of [0-9]+ passages done`: the
  name of a model step and ASCII digits (the pattern was any lower-case word and `\d`, which matches the digits of other scripts).
  The runner writes the line as the step wrote it, so the pattern is the whole of what a step can put on the terminal.

### Must never

- Write anything but one line. Import a stage.

### Done when (each backed by a test in `tests/test_stagenote.py`)

1. Every kind of line break and run of whitespace becomes one space (`test_flat_puts_every_kind_of_line_break_and_run_of_whitespace_on_one_line`);
   a note and a warning are one line with their prefix (`test_a_note_and_a_warning_are_one_line_each_with_their_prefix`).
2. A name with a newline and `note: ` in it is part of one note and not a note of its own
   (`test_a_name_that_carries_a_newline_and_note_is_part_of_one_note_and_not_a_note_of_its_own`, and with a real repository,
   `tests/test_runner.py::test_a_file_name_in_the_repository_is_never_a_note_the_step_wrote`, skipped on a machine whose git
   cannot hold such a path).
3. A value from a service is one line and cut at its cap, and a progress line is plain, one line, and not a note
   (`test_a_value_from_a_service_is_one_line_and_cut_at_the_cap`, `test_a_progress_line_is_plain_one_line_and_not_a_note`,
   `test_a_line_that_is_not_progress_is_not_taken_for_one`, `test_a_progress_line_takes_a_name_and_two_counts_and_cannot_carry_text`,
   `test_only_a_model_steps_name_and_ascii_digits_make_a_progress_line`).
4. Nothing from outside can start a line of a finished step's stderr
   (`test_nothing_from_outside_can_start_a_line_of_a_finished_steps_stderr`: it reads every script of the steps and the `_shared`
   modules they import; a write to stderr goes through this module, or is an `error:` or `usage:` line just before a non-zero
   return, since `own_notes` reads only a step that exits 0; `traceback`, `warnings`, `logging`, and `sys.stderr.write` are
   refused. `test_a_write_round_the_helper_is_found` holds the shapes it must catch).

### History

- 2026-10-30: M9 slice B, second fix round: built. The inventory's notes name submodules and tracked files by their path, and
  a path with a newline and a `note: ` line reached `data/limits.md`, `full.md`, `details.html`, and `05-qa.json` as a limit the
  inventory had named. Every note site of the steps, and the reader's warning, use it. The phrase step imports it, so its
  `terms.code` moves.
- 2026-10-31: M1 slice A: `flat(text, cap)`, `MODEL_CAP`, `progress`, `is_progress`, `show_progress`. The phrase step imports this module,
  so its `terms.code` moves.
- 2026-10-31: M1 slice A, fix round: `PROGRESS` is `(sweep|pinpoint): [0-9]+ of [0-9]+ passages done`, matched whole. It checked the shape
  only (`[a-z-]+: \d+ ...`), so a line with any lower-case name, or with digits of another script, was shown on the terminal as a
  step's progress. The phrase step imports this module, so its `terms.code` moves again.
- 2026-10-30: M9 slice B, last fixes: the test now holds the rule itself. It had looked only for a literal `note:` or `warning:`
  at the start of a print, so most ways round the helper passed.

## steperror

M9 slice B.

What a step that crashed is allowed to say of its error. A step's stderr is its traceback, and the line that ends it
holds the error's message, which can repeat text from the audited repository or a model's words. The record, `LOG.md`,
and the error line the runner prints keep the exit code and the error's type; the whole stderr stays in
`data/<step>.notes.txt`. The type is given only when it is the name of one of Python's own exceptions (a name a library
or a message supplies could be any words), and the brief and the check of the run name a missing import's module only
when it is one of Walkdown's own packages.

### Outputs

- `error_of(stderr)`: `(the error's type, "No module named '...'" or None)`. The line read is the first line that is not
  indented after the header of the last traceback (`Traceback (most recent call last):`; a chain's last error is the
  one raised last). It must be one word, then nothing or a colon (`ValueError`, `ValueError: the message`), and the word
  must be a builtin exception (`is_builtin_error`); otherwise `(None, None)`, and so for a stderr with no traceback
  (`sys.exit("message")` prints the message alone). For a missing import (`No module named 'yaml.nodes'`) the module is
  given as its top-level name, and only when it is in `packages.OWN_MODULES`, the import names of Walkdown's packages (the
  `packages` section keeps that list true to the real imports). Nothing of the message is returned.
- `is_builtin_error(name)`: whether `name` is one of Python's own exceptions.
- `exit_text(code, stderr)`: `exit 1: ValueError`, or `exit 1` when the stderr names no error.

### Must never

- Return any of an error's message but the top-level module of a missing import of Walkdown's own.
- Return a name that is not one of Python's own exceptions.
- Import a stage.

### Done when (each backed by a test in `tests/test_steperror.py`)

1. The type of the line that ends the last traceback is returned, a missing import's module of Walkdown's own with it,
   and nothing of the message (`test_the_type_is_returned_and_nothing_of_the_message`,
   `test_a_missing_import_names_its_module_only_when_it_is_one_of_walkdowns_packages`).
2. A later line of a message that looks like an error is not read
   (`test_the_line_that_ends_the_last_traceback_is_the_one_read_and_not_a_later_line_of_the_message`), and a traceback
   header inside a message can give only a name Python gives
   (`test_a_traceback_header_inside_a_message_can_only_give_a_name_python_gives`).
3. A name that is not one of Python's own gives nothing, however long or short
   (`test_only_a_name_python_itself_gives_an_exception_is_a_type`); a stderr with no traceback names no error
   (`test_a_stderr_with_no_traceback_names_no_error`).
4. `exit_text` is the code and the type, or the code alone (`test_exit_text_is_the_code_and_the_type_or_the_code_alone`).
5. A crash that prints each of these shapes leaves none of its words in a file a person reads
   (`tests/test_runner.py::test_nothing_a_crashed_step_prints_reaches_a_file_a_person_reads_or_the_terminal`).

### History

- 2026-10-30: M9 slice B: built. The pattern was the brief's (`brief.stage_error`, which reads this now); a name over 60
  characters is no longer taken as a type.
- 2026-10-30: M9 slice B fix round: the line read is the one that ends the last traceback, no longer the last line of the
  stderr that looked like an error (a message with a line of its own, `CANARYWORDError: ...`, was read as the error), and
  the name must be one of Python's own exceptions, so `MAX_TYPE` is gone. A missing import's module is named only when it
  is one of Walkdown's packages, and as its top-level name; before, any module a message named was repeated.

## termdiff

Restructure step 7.

What changed between two runs' `terms` blocks. The block is `02.4-phrases`'s: the version of its search terms
and matching code, recorded in every report (`02.4-phrases/termset.py`, `describe`). The report stage's
drift compares two runs' blocks to say whether a new or gone phrase hit comes from the repository or from
Walkdown (review C22 b). The comparison moved here from `termset.py` so that the report stage imports no
stage (notes M13); it works on the blocks as plain data.

### Outputs

`diff(old, new)` compares two blocks: `rows_added`, `rows_changed`, `rows_removed` (ids, sorted),
`vocab_changed`, `code_changed`, `same` (none of those), and `known`, false when either block is missing
or has no `rows` (a run from before 2026-10-19), with every other field empty or false.

### Must never

- Guess a difference when a block is missing (`known` is false instead).
- Import a stage or read a file.

### Done when (each backed by a test in `tests/test_termdiff.py`)

1. `diff` lists added, changed, and removed rows and the vocab and code flags; identical blocks are
   `same`; a missing block is `known` false (`test_diff`).

### History

- 2026-10-19: built as `termset.diff` (review C22 b).
- 2026-10-29: restructure step 7: moved to `stages/_shared/` (notes M13); `termset.py` keeps the half that
  builds the block.

## textmodel

M1 slice A (2026-10-31).

The calls every model backend makes alike, and the contract of a model that takes text. The two model steps ask one question for
each passage. Whatever answers (Jev or the Claude Code command), the steps around the call are
written here once, so a backend is only the call.

### Outputs

`Backend` (the part every backend shares). A backend sets `name`, `remote`, and `model`, and supplies `prepare()` (the reason nothing
can be called, or None; the client is built here), `once(item)` (one call and what is made of its answer: `(fields, None)` or
`(None, calllog.failure(...))`, with the tokens the call reported riding on either as `usage`), and `request(item)` (exactly what is
sent for the item, with no key in it). `ask(items, who=None)` returns one result for each item, in order:

- Nothing to call (`prepare` gave a reason): every item is skipped with it, no call is made, and none is tried again
  (`calllog.unsent`).
- **The first call runs alone**, so a rejected key stops every later call; the rest run `workers` at a time.
- A call that gets no answer is tried once more after `retry_wait` (`calllog.attempt`; at most two calls for an item). A failure with
  `auth` stops the calls that have not started: each is skipped as `not sent: <reason>`.
- The result is the item's `qid`, the `backend`, the `request`, and either the answered fields or `skipped` with the reason (and the
  `response` when the failure kept one), and `tries` when the first try got no answer or the call was not made. A failure that carries
  `answer` (fields to keep when the second try is no better) gives a result with those fields and no `skipped`.
- Every call adds to `usage` (`usage.Tally`): an answer or not, and the tokens it reported, an error reply's too (a failure carries them
  as `usage`). A call that reported any count is one of `reported`.
- `who` (`sweep`, `pinpoint`): every 25 items finished, `stagenote.progress` writes a plain line on stderr. A step that gives no name,
  and a read of fewer than 25 items, say nothing.

`TextModel(Backend)`: a model that takes a system text and a prompt and gives back text. It supplies `call(system, prompt)`, which
returns `(reply, None)` with `reply` = `text` (a string), `model` (the model that answered, as the service named it), `usage`
(`usage.clean`: whole numbers only), and `response` (kept in the answers file), or `(None, failure)`. An item is `{"qid", "system",
"prompt"}` (and a `label` a backend may use in its request). `ask(items, accept=None, who=None)`: `accept(text)` turns the text into
the fields the step wants, `(fields, None)`, or says it cannot be used, `(None, calllog.failure(...))`, a call with no answer that
is tried once more like any other; with none, the text is `answer`. A failure from `accept` keeps the raw `response`. The model that
answered is a value from a service, and a service can put a tag, a link, or a line break there. `Backend.answered_by(name)` keeps it
only if it passes `options.bad_model` (the rule for a name the person types), cut to `stagenote.MODEL_CAP` (80) characters; any other
name, or none, leaves the model that was asked for: the one the person named, `sonnet` for a `claude-cli` that names none, `jev-latest`
for Jev, whose answer is held to the same rule.

`Jev` (`stages/03-sweep/back_jev.py`) is a `Backend` and not a `TextModel`: it answers with typed probabilities from fixed options.

### Must never

- Write the second try, the stop on a rejected key, the first call alone, the workers, or `not sent` again in a backend.
- Keep an error's own text, a key, or a passage in a skip reason, a failure, or a log.
- Make a third call for an item.

### Done when

1. The one extra try, the stop on a rejected key, the first call alone, the workers in parallel and in order, and `not sent` are the
   base's and no backend's (`tests/test_back_claude.py::test_the_contract_is_one_class_for_every_backend`,
   `test_the_first_call_runs_alone_and_the_rest_run_at_the_same_time`,
   `test_a_rejected_login_stops_the_calls_even_with_workers_because_the_first_call_runs_alone`, and the retry and stop tests of
   `back_claude`, above; `stages/03-sweep/tests/test_back_jev.py`, the same rules for Jev).
2. An answer the step cannot use is tried once more, then kept as it came or skipped
   (`test_an_answer_that_cannot_be_used_is_tried_again_and_a_usable_one_is_used`,
   `test_an_answer_that_cannot_be_used_twice_is_kept_as_it_came_for_the_step_to_skip`,
   `test_without_an_accept_the_text_is_the_answer`).
3. A long read says it is working every 25 passages, with no `note:` in front, and a short read says nothing
   (`test_a_long_read_says_it_is_working_every_25_passages`, `test_a_short_read_says_nothing_while_it_works`).

### History

- 2026-10-31: M1 slice A: built, from what `back_jev.py` and `back_claude.py` each wrote.
- 2026-11-01: M1 slice A, before merge: this section and the module's docstring no longer name API backends that follow: those backends are on hold (the owner, 2026-11-01).

## toolversion

O3.

The version of this Walkdown, as the pages and the run's record name it. Two readers need the same text: the report
stage puts it in `LOG.md` and `full.md` (`meta["tool"]`), and the runner writes it into the record (`version`), so that
`continue` can tell a run stopped by this Walkdown from one stopped by another.

### Outputs

`tool_version(root)`: `0.4.0 (a5bf24e)`, the `VERSION` file and the git commit, with `+modified` when tracked files have
uncommitted changes; the version alone without git (a downloaded zip), `unversioned` without a `VERSION` file.

`release(text)`: the version number alone (`0.4.0` from `0.4.0 (a5bf24e+modified)`); `continue` compares it.

`code_hash(root)`: 16 hex digits over the files a run runs and reads: `walkdown.py` and every `.py`, `.yaml`, and
`.json` file under `stages/` and `Library/` except those in a `tests`, `specs`, or `__pycache__` folder and any hidden
file or folder (a name starting with a dot, such as `.mypy_cache`), so a document or a file an editor or a file
browser leaves behind (`.DS_Store`, `Thumbs.db`, `run.py~`) does not count; the file's path and its content with
line endings made alike, in path order. The record keeps it (`code`), and `continue`
compares it, because two sets of uncommitted edits give the same `tool_version` (`+modified`). It does not look at
`validate.fingerprint`, which also covers the tests, the specs, the fixtures, the grader, and the optional tools.

### Must never

- Write anything, or fail: a missing git or file gives the shorter text.

### Done when (each backed by a test in `tests/test_toolversion.py`)

1. The text follows the `VERSION` file and git, with and without either
   (`test_the_version_is_the_version_file_and_the_commit`).
2. The hash follows the code and the tables and nothing else (stray editor and file-browser files and caches
   included), tells different edits apart, ignores line endings, and is the same for the same files in another
   folder (`test_the_code_hash_follows_what_a_run_runs_and_reads`).
3. `release` is the version number alone (`test_release_is_the_version_number_alone`).

### History

- 2026-10-04: built in `stages/05-report/run.py` (`+modified`, and the version alone without git).
- 2026-10-30: O3: moved to `stages/_shared/`; the runner and the report stage both read it there.
- 2026-10-30: O3, fix round: `code_hash`.
- 2026-10-30: O3 verification: `code_hash` counts only `.py`, `.yaml`, and `.json` files outside hidden folders (a
  `.DS_Store` had refused a `continue`); `release`, so `continue` compares the version number and the code, and a
  commit or a document edit between the stop and `continue` no longer refuses the run.

## upstream

Reading the reports of the stages that ran before an AI stage. Moved here from the soft stage's
`upstream.py` (restructure step 5) and cut down to what both AI stages share: read a saved
`NN-name.json` and check it against the report contract (`stages/CONTRACT.md`). Running the earlier
stages as subprocesses is not here; it is `earlier_steps.py`'s (restructure step 7, in place of Sweep's
`runstages.py`). Stage code is never imported. (Named `upstream`, not `inputs`, so it never collides with
`02.5-capability`'s module of that name in one test session.)

### Inputs

- `load_dir(reports_dir, names, required=None)`: a folder holding `<stage name>.json` reports; `names`
  is the stage names of the reports wanted; `required` the names that must be there (default: all
  of `names`).
- `check(name, doc)`: a parsed report.
- `skips(reports)`.

### Outputs

- `load_dir` returns `{stage name: report}` for the reports found, each a contract-1 report.
- A report must parse as JSON, be an object, have `contract` 1, the right `stage`, and a `findings`
  list, else `ReportError` naming the stage. A missing required file is a `ReportError`.
- `skips(reports)`: `[(stage name, finding)]` for every finding with `skipped`, in name order.

### Must never

- Import another stage's code, run anything, or write anything.
- Treat an earlier stage's skip as a failure.

### Done when (each backed by a test in `stages/_shared/tests/test_upstream.py`)

1. `load_dir` returns the reports keyed by the stage names given
   (`test_load_dir_returns_the_reports_keyed_by_the_names_given`); a missing report raises unless it is
   not required (`test_a_missing_report_raises_unless_it_is_not_required`).
2. A wrong `stage`, a `contract` other than 1, no `findings` list, or a file that is not JSON raises
   `ReportError` (`test_a_wrong_stage_a_wrong_contract_or_no_findings_list_raises`,
   `test_a_file_that_is_not_json_raises`).
3. `skips` lists a skipped finding with its stage name (`test_skips_lists_the_skipped_findings_with_their_stage`).

### History

- 2026-10-29: restructure step 7b: the reports are keyed by stage name. Until then a caller gave
  `{two-digit key: stage name}` and got the reports back under the key.

## usage

M1 slice A (2026-10-31).

Token totals of a model read. A model step's report has a `usage` block: `input`, `output`, `cache_write`, `cache_read`, and
`calls`, and `reported`, each a whole number no higher than 10^15 (`CEILING`: a service can put any number in its reply, and a count of
thousands of digits fills a page or raises when added to another). A count the backend did not report is absent from the block and is
never written as 0; the totals add up the calls that reported them, so they are a lower bound when some did not. `calls` is Walkdown's own
count of the calls it sent (a second try is a call), so it is always there, and is 0 for a read that sent nothing. `reported` is how many
of those calls reported any token count, an error reply's included (the tokens were spent); it is never above `calls`, and a total from
fewer calls than were sent says so in its words.

### Outputs

- `TOKENS`, `KEYS`; `whole(n)` is `coverlines.whole`: not a bool, not a float, not below 0 (left as it is: the numbers there are Walkdown's
  own). `CEILING` is 10^15 and `count(n)` is `whole(n)` and no higher than `CEILING`; the counts of a usage block are read with it.
- `clean(fields)`: the token counts of a dict that are counts, under `TOKENS`; a count that is missing, a float, a bool, below zero, or
  above `CEILING` is left out (not reported).
- `valid(block)`: an object whose counts, where it has them, are counts, and whose `reported`, where it has it, is no more than its
  `calls`. `pipeline.read_report` refuses a report whose `usage` is not, and `validate.Stamp.from_dict` reads a stamp whose `usage` is not as one that spent none.
- `plus(*blocks)`: the blocks added key by key over the blocks that have the key; None for none, and a block that cannot be read
  counts for nothing. A sum above `CEILING` is left out, and so is `reported` when a block does not say it.
- `Tally` (thread-safe): `add(spent=None)` counts one call sent and what it reported; `block()` is the step's block, and a total above
  `CEILING` (calls that each reported a very large count) is left out of it, as one such count is.
- `words(block)`: `596,200 in, 31,464 out`, with `1,200 cache write` and `300 cache read` where reported and not 0; a total that
  only some of the calls reported ends `(from 5 of 9 calls)` (`partial(block)` is `(reported, calls)` when `reported` is above 0 and
  below `calls`, else None, also for a block that does not say); `not reported` for a block with no token count, one that cannot be
  read, or whose `reported` is 0, `sent nothing` for a read with no call. `note(block)` is the step's note: `tokens the calls used, as
  the backend reported them: 7 in, 3 out (1 call)`, with the partial clause in the place of the number of calls.

### Must never

- Write a count that was not reported as 0, or a count that is not a whole number, or one above `CEILING`.

### Done when (each backed by a test in `tests/test_usage.py`)

1. Only whole numbers no higher than 10^15 are counts, and a block can be read only when its counts are (`test_only_whole_numbers_are_counts`,
   `test_a_block_of_whole_counts_can_be_read`, `test_a_block_that_is_not_counts_of_whole_numbers_cannot_be_read`,
   `test_a_count_above_the_ceiling_is_not_a_count`; a backend that reports one: `test_back_claude.py::test_a_count_above_the_ceiling_is_not_reported`).
2. Blocks add up, and the tally counts every call and adds only what was reported, from threads too
   (`test_blocks_are_added_key_by_key_over_the_blocks_that_have_the_key`,
   `test_the_tally_counts_every_call_and_adds_only_what_was_reported`, `test_the_tally_is_exact_when_calls_come_in_from_threads`).
3. The words say what was reported and `not reported` for the rest (`test_the_words_say_what_was_reported_and_say_not_reported_for_the_rest`,
   `test_the_note_names_the_tokens_and_the_calls`), and a total from only some of the calls says so
   (`test_a_total_from_only_some_of_the_calls_says_so`); `reported` must be a count no higher than `calls`
   (`test_a_reported_that_is_not_a_count_or_is_more_than_the_calls_cannot_be_read`) and adds up only over blocks that say it
   (`test_reported_adds_up_only_over_blocks_that_say_it`); an error reply's tokens are counted
   (`test_back_claude.py::test_the_tokens_of_an_error_reply_are_counted_because_they_were_spent`).
4. A saved `usage` that is not counts of whole numbers, or has a count above the ceiling, is an output that cannot be read, in every reader
   (`tests/test_pipeline.py::test_a_usage_that_is_not_counts_of_whole_numbers_makes_a_saved_output_a_report_that_cannot_be_read`,
   `stages/06-report/tests/test_saved_outputs.py`, every `usage` body: the check names the gap `output-unreadable`, the report is
   written from a held run, a re-render and the comparison of two runs do not crash).

### History

- 2026-10-31: M1 slice A: built.
- 2026-10-31: M1 slice A, fix round: a count has a ceiling, `CEILING` = 10^15. There was none: a service's count of 10^4000 gave an 18 KB
  brief, and a sum past 4,300 digits raised. `clean` leaves a count above it out, `valid` makes a saved one an output that cannot be read,
  and a total above it is left out of a block. `coverlines.whole` is as it was.
- 2026-10-31: M1 slice A, fix round: the block has `reported`, how many calls reported any token count. Nine calls of which five reported
  printed `Sweep 500 in, 15 out`, which reads as complete; it prints `(from 5 of 9 calls)` now (`partial`), and `reported` 0 is `not
  reported`. `valid` refuses a `reported` above `calls`. `back_claude.call` dropped the `usage` of an error reply, and those tokens were
  spent; a failure carries it now. The grader sums `reported` with the other counts.
- 2026-10-31: M1 slice A, fix round: the name of the model that answered is held to the model-name rule (`Backend.answered_by`). It was cut and put on one line, so a `<script>` tag or a link a service put in it reached `full.md` and `LOG.md`; a name that fails the rule now leaves the model that was asked for.
- 2026-10-31: M1 slice A, fix round 2: `Backend.answered_by` had a branch for "the person named none, so `not reported`". It never ran: every
  backend has a model (`ClaudeCLI.model` is the one named, else `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`), so a bare `claude-cli` records
  `sonnet`. The branch, `NOT_REPORTED`, and its test are gone.
- 2026-10-31: M1 slice A, fix round 2: a model name that holds `//` is refused (`bad_model`, `MODEL_RULE`). `https://evil.example/x` passed (letters, `:`, `/`, `.`) and would have shown in `full.md` and `LOG.md`, for a typed name, the variable, and a service's name alike.

## validate

Turns the grader's result for each stage into that stage's validation stamp
(REPORTING principle 6: no zero without validation).

### Inputs

- `stamps(root, python, stages) -> dict[str, Stamp]`: runs
  `python <root>/tools/grader/grader.py <stage> --json` once per stage and parses it.
- `parse(doc) -> dict[str, Stamp]`: the parsing half, for a grader `--json`
  document.

### Outputs

`Stamp`: `result` (`PASS`, `FAIL`, `INCOMPLETE`, `NOT BUILT`, `SETUP ERROR`, or
`ERROR` when the grader could not be run or parsed), `gate` and `negative` as
`"passed/total"` strings (or None), `recall` as `"found/total"` (or None),
`skipped`: ids of expectations the grader marked SKIPPED, `text`: one line for
a log or a report, for example `PASS (gate 31/31, negative 46/46, recall 39/39)`
or `INCOMPLETE (gate 14/15, negative 12/12; skipped: rd-img-ocr)`.

### Must never

- Read `Fixtures/ANSWERS/` itself. The grader is the only reader of answers.
- Turn anything but a grader PASS into a PASS.

### Done when (each backed by a test in `tests/test_validate.py`)

1. A grader document with a PASS stage gives `result` PASS and the gate,
   negative, and recall strings.
2. An INCOMPLETE stage lists its SKIPPED ids in `skipped` and in `text`.
3. A grader run that prints no JSON gives `result` ERROR.

### Added 2026-09-29

- `stamps(root, python, stages, env)` passes `env` to the grader runs; `05-report` sets
  `WALKDOWN_SOFT_SWEEP` to the run's sweep backend so Sweep's stamp is that
  backend's recall on the sweep fixture. A stage the grader reports as `no fixture set` (Pinpoint) is
  stamped with that word as its whole result (`Stamp.text` is `no fixture set`); it is not an error.
- More than three skipped ids collapse to `skipped: N rows`. Test:
  `test_long_skip_list_collapses`.

### The tokens a fixture check spent (M1 slice A)

- `Stamp.usage`: what the grader's run of the step used, the grader's `usage` for it (`tools/grader/grader.py` adds up the `usage`
  blocks of the cases it ran), or None when it sent nothing or no backend was chosen. It is in `to_dict` only when the check spent
  something, and a `usage` that cannot be read (`usage.valid`) is read as none, in `parse` and in `from_dict`. It is not in `text`.
- A stamp reused from the cache spent nothing in this run and has none: the cache keeps no `usage` (an entry that holds one is read
  without it). `--revalidate` measures again, and spends again.
- A stamp that measured nothing is not kept (`not Stamp.measured`, other than `no fixture set`): a model read in which every fixture row was
  skipped (no key, no login, no program) is a PASS with nothing behind it, and the person may fix that and run again; the cache must not
  hand the same stamp back. It is graded again at the next run. Test:
  `test_a_stamp_that_measured_nothing_is_not_kept_so_the_next_run_measures_again`.
- The fingerprint holds the choice the grader runs with as the person typed it (`WALKDOWN_SOFT_SWEEP=claude-cli:Some-Model`, and
  `WALKDOWN_SOFT_CLAUDE_MODEL` for a `claude-cli` that names no model), so a model's first run is measured and a later run reuses
  the stamp. Tests: `test_the_grader_documents_usage_is_the_stamps_and_it_changes_no_other_word_of_it`,
  `test_a_usage_the_grader_prints_that_is_not_counts_of_whole_numbers_is_no_usage`,
  `test_a_stamp_keeps_its_usage_in_the_record_only_when_it_spent_some`,
  `test_a_record_with_a_usage_that_cannot_be_read_is_a_stamp_that_spent_none_and_no_traceback`,
  `test_the_cache_never_keeps_the_tokens_of_the_run_that_measured_the_stamp`,
  `test_the_fingerprint_holds_the_model_as_the_person_typed_it`.

### Cached stamps (added 2026-10-03, review C16)

- `fingerprint(root, env)`: sha256 over every file under `stages/`, `tools/grader/`, `Fixtures/`, and
  `Library/` (the tables the stages read; added 2026-10-29, restructure step 3; path and bytes,
  `__pycache__` skipped), the Python major.minor, which optional
  tools are present (`optional_tools()`: Tesseract with pytesseract; added
  2026-10-08; pdf2image and Playwright dropped 2026-10-12, since no stage used them; Playwright
  back 2026-10-20 with `02.2-reader`'s own check, `render_html.available`), and the `WALKDOWN_SOFT_*` variables in `env`. Any change to
  code, fixtures, answers, a Library table, installed optional tools, or the AI choices gives a new
  fingerprint, so installing Tesseract never reuses a `02.2-reader` INCOMPLETE measured without it.
  Test for the Library: `test_fingerprint_covers_the_library`.
- `stamps(..., cache=True)` reuses `.cache/stamps.json` entries keyed `<stage>|<fingerprint>`
  and runs the grader only for misses, saving each new PASS, INCOMPLETE, or `no fixture set` with the date
  (`CACHEABLE`). A reused stamp has `cached` set to that date, and its text says "measured <date>, same code
  and fixtures". Any other result (FAIL, SETUP ERROR, NOT BUILT, ERROR) is never saved and an entry that holds
  one is not reused: it can come from the machine and not the code (a killed process, a full disk), so the next
  run grades the step again. Tests: `test_only_a_pass_an_incomplete_and_a_no_fixture_set_are_cached`,
  `test_a_failed_stamp_left_in_the_cache_by_an_older_version_is_not_reused`. `cache=False` (`--revalidate`)
  always runs the grader.
- A Sweep stamp with a remote model is measured once per fingerprint; the model can drift
  between runs, which the cache does not see.
- 2026-10-29: restructure step 5: a stage the grader reports as `no fixture set` is stamped with that word; the sweep backend is the only choice passed to the grader.
- 2026-10-29: restructure step 7: moved from `stages/05-report/` to `stages/_shared/` (the runner there stamps; the report stage only reads the stamps); the grader is at `tools/grader/grader.py` and the fingerprint keys on `stages/`, `tools/grader/`, `Fixtures/`, and `Library/` (`test_fingerprint_keys_on_the_stages_the_grader_the_fixtures_and_the_library`).
- 2026-10-29: restructure step 7: `Stamp.to_dict` and `Stamp.from_dict` (the record keeps the stamps as data).
- 2026-10-31: M1 slice A: `Stamp.usage` (above), and a stamp that measured nothing is not cached.
- 2026-10-30: M9 slice B fix round: the cache keeps only PASS, INCOMPLETE, and `no fixture set`. A FAIL was cached before, so
  a check that failed once for a reason outside the code (the grader's run was killed) held every later run of the same
  code until `--revalidate`.
- 2026-11-01: gitleaks left the fingerprint's optional tools, since no stage runs it (`02.4-phrases`, secret_scan), and `secretmask.PRIVATE_KEY` went to
  detect-secrets's one name for the kind.
