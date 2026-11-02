# walkdown.py (added 2026-10-02)

The front door: one command from a folder or a git URL to a finished run and a brief. It only routes
(restructure step 7): it picks the Python, parses the options once (`stages/_shared/options.py`), has the runner
(`stages/_shared/runner.py`, `stages/_shared/specs/shared.SPEC.md`, section `runner`) run the steps, validate them, and start the report stage, and
prints the brief file the report stage wrote (`brief.md` in the run folder; `stages/06-report/specs/report.SPEC.md`, section `brief`).
It holds no report code: no brief, no stamps read from `LOG.md`, no comparison with an earlier run. Everything
below that says what the brief holds is the report stage's spec now, kept here because it is what the person
sees.

## Inputs

`python walkdown.py <target> [--name NAME] [--fresh | --keep] [--sweep B] [--pinpoint B] [--reads [MODEL]] [--until STEP] [--revalidate] [--context N] [--hosts a,b]`,
`python walkdown.py continue <run folder> [--sweep B] [--pinpoint B] [--reads [MODEL]] [--until STEP] [--revalidate] [--context N] [--hosts a,b]`,
`python walkdown.py --version`, `python walkdown.py diff <old run> <new run>`

- `target`: a folder, or a git URL (`http(s)://`, `git@`, `ssh://`, or ending in `.git`,
  unless a folder by that name exists). A GitHub folder link,
  `https://github.com/<owner>/<repo>/tree/<ref>[/<path>]`, clones the repository at `<ref>` (the
  first part after `/tree/`, a branch or tag) and audits the folder `<path>` (2026-10-25,
  review C41: a link copied from GitHub was taken as a git URL and failed to clone). A file
  link (`/blob/`) or a file is an error that says to give the folder holding it.
- `--name`: the run folder name; default the URL's or folder's last part without `.git` (for a
  folder link, the folder's last part), reduced to letters, digits, `.`, `_`, `-`. Intake decides
  it (`stages/01-intake/specs/intake.SPEC.md`).
- `--sweep` and `--pinpoint` (declared from `stages/stages.json`) take a backend and, after a colon, a model
  (`--sweep claude-cli:<model>`; `options.parse_choice`); a value that cannot be used is refused before anything runs (exit 2, one
  sentence that says why, written in ASCII and cut at 80 characters so any terminal prints it). They go to the runner unchanged; a run without them uses no
  model. An off value (empty, `none`, `0`, `false`, `no`, `off`, any case) chooses nothing, for the flag and for the
  environment variable alike (notes M14 a). `--label`, `--compare`, `--relational`, and `--both` are refused before anything runs, and so are
  their environment variables `WALKDOWN_SOFT_LABEL`, `_COMPARE`, `_RELATIONAL`, `_BOTH` (exit 2;
  `error: <option or variable> is not available in this version: labeling is being rebuilt`;
  restructure step 5). The brief counts a chosen AI stage that left no report (a step in the record or a notes
  file, no `data/<stage>.json`) as a step that did not run, and never names one nobody chose.
- `--reads [MODEL]` (the loaded-model build, 2026-11-01) chooses the model reads without naming a backend: Sweep on Jev when Jev
  is available (its key can be read and its package is found; the sweep's passages then go to TypeSafe, in place of the Claude model),
  else on the Claude Code command; Pinpoint on the Claude Code command when it is found; the Claude Code command runs with its tools off
  and `MODEL` as typed, or `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`, when `--reads` is bare. It is resolved once, here in the check before anything runs, into the `--sweep` and `--pinpoint` values, as if they had been
  typed (`stages/_shared/specs/shared.SPEC.md`, section `options`, holds the table, the six sentences it can be refused with, and the
  one note); the runner, the record, the stamps, and the pages see only those values. It cannot be given with `--sweep` or
  `--pinpoint`. It takes an optional value, so `walkdown.py --reads <repo>` reads the repository as the model: the front door
  says so in one sentence and exits 2 (no usage text, no traceback). `walkdown.py <repo> --reads` is the form. At `continue` it
  chooses only the reads that can still run. It is the consent to send, as `--sweep` is.
- `--revalidate` passes through too: re-run the fixture validation even when a stamp for the
  same code is cached (2026-10-03).
- `--until STEP` (O3; declared in `options.add_until_option`): stop after a step, given by its name in
  `stages/stages.json` (`02.4-phrases`), its number (`02.4`), or its word (`phrases`), in any case; `02-coded`, `02`, and
  `coded` mean the last coded step (`02.6-builder`). A value that is not a step, and an AI step nobody chose, are refused
  before anything runs (exit 2, one line: `--until 03-sweep: that step runs only when chosen (--sweep)`). The stop,
  what it writes, and the run folder it leaves are in `stages/_shared/specs/shared.SPEC.md`, section `runner`; the brief
  it prints is below.
- `continue <run folder>` (O3): goes on in a run that stopped, with `--until`, the AI options, `--revalidate`,
  `--context`, and `--hosts`; intake's options are not declared. It is a route to `runner.resume`, as `diff` is a route
  to the report stage's comparison, and prints the new brief. It refuses with one line, exit 2, and the folder as it was,
  when the run cannot be gone on with (the `runner` section lists each). An AI read runs only when its option is given
  at this command: choosing it there is the consent to send. The environment variables `WALKDOWN_SOFT_SWEEP` and
  `WALKDOWN_SOFT_PINPOINT` choose nothing at `continue` (a first command keeps its rule: the option, else the variable);
  when one is set and its option is not given, `continue` prints one `note:` saying it is not read and giving the
  option to send. A relative run folder is read from the folder the command was started in. On a **held** run (below) it
  runs no step: it writes the report with what the run has, prints its brief, and refuses a model option or `--until`.
- `--version` prints `walkdown <VERSION>` and exits (2026-10-04).

## Outputs

- Before anything else, the clone included, the interpreter: the one Walkdown was started with
  when it can import every core module (`CORE_MODULES` of `stages/_shared/packages.py`: requirements.txt less pytest), else
  the project virtualenv's when that can (2026-10-21: an empty `.venv` in the Walkdown folder
  was preferred over a working interpreter, and every stage failed). When it is the
  virtualenv's, Walkdown runs itself again under it with the same arguments and returns that
  exit code, so the brief, version drift, and `diff` run there too (2026-10-25, review C41:
  started with a system Python, drift said "No module named 'yaml'" and `diff` crashed). When
  neither can, it runs nothing: it names the interpreter and the modules it lacks, with the
  `pip install -r requirements.txt` line, exit 2. `--version` and `--help` need no packages.
- Getting the copy is intake's job, the first stage (`stages/01-intake/`, restructure step 2,
  2026-10-28); `walkdown.py` holds no fetch code. What follows is what intake does, kept here
  because it is what the person sees. A URL is cloned shallow (`git clone --depth 1 -- <url>`) into `ReposToExamine/<name>`. An
  existing clone of the same URL (its `origin`, compared without `.git` or a trailing slash,
  case-insensitive) is updated to the remote's latest commit (`fetch --depth 1`, `reset --hard
  FETCH_HEAD`, `clean -fdx`; 2026-10-03). `--keep` audits whatever is there without updating;
  `--fresh` deletes the clone and clones again. A folder there that is not a clone of this URL
  is an error (exit 2) unless `--keep`. A folder link clones into `ReposToExamine/<repo>` (or
  `--name`, which then names both the clone and the run) with `--branch <ref>` and updates
  with `fetch --depth 1 origin <ref>`; its folder missing at that ref is an error. Every git
  command runs with no prompts (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`, and ssh in
  batch mode unless `GIT_SSH_COMMAND` is set), long paths on (`-c core.longpaths=true`, for
  Windows), and a 10-minute limit (2026-10-25, review C41: a private or mistyped URL could wait
  for a login). A repository that is missing or needs a login fails at once and says so in
  plain words; so does a branch that is not there, and git not being installed.
- Parses the options once, checks them (the parked options and variables refused; `--hosts` and `--context`
  read; a bad one is `error: ...`, exit 2, before anything runs), prints `Using Python at <path>` on stderr, and
  calls `runner.audit` with the interpreter above. The target goes through as it was given: the runner runs
  intake, which clones or reads the folder, and names the run; a target intake refuses (a file, a path that is not
  a folder, a failed clone) ends the run with intake's message alone, exit 2. A run with no `brief.md` at the end
  says `error: the run did not finish; see the messages above` and never exits 0. The report stage's
  folder is read from `stages/stages.json` (the one home for the stage list; `stages/CONTRACT.md`).
- `--context` (the expected context; slice 1, 2026-10-26) and `--hosts` (the hosts the builder builds for; slice 3)
  are declared with `options.add_report_options`, the same function the report stage declares them with; the run's
  record keeps them.
- Prints the **brief file** to stdout, exactly as the report stage saved it. It is in `summary.html`'s terms (owner, 2026-10-21): files examined;
  then one line on triggering (slice 4, `summary_html.brief_trigger_line`): "Will it trigger: <n>
  skills, <c> commands, <a> agents; <h> places that break a host rule, <g> from guidance; <o> pairs
  of descriptions that overlap."; then two lines on cost, counts only (`summary_html.brief_cost_lines`, slice 1): "Every session:
  <X> tokens. Largest skill at its fullest: <Y> tokens (<Z> of <C>)." (with "Every session in
  this folder: <P> tokens." when there are project files) and "Not used at run time: <n> files
  (<t> tokens).", the expected context from the run's record; then one line on what it needs
  (slice 2): "Needs: <n> programs, <m> packages; <k> not declared. Ties to one machine: <p> places.";
  then one line on hosts (slice 3, `summary_html.brief_ready_line`): "Ready for: <h> of 7 hosts have
  their files here; copies that differ: <d>; one-host features: <f>." with "For the hosts named:
  <k> things missing." when the record names target hosts;
  then one line on tools (slice 5, `summary_html.brief_fit_line`): "Tools fit: <u> granted and never
  used, <m> tasks with no tool, <l> loops with no stated limit; <h> hooks run on every prompt or tool
  call."; then one line on current and clean (slice 6, `summary_html.brief_clean_line`): "Current and
  clean: <u> unfinished, <d> dated claims, <m> pinned model IDs (<k> distinct), <o> older tool names.";
  the changes lines gain the cost line (`drift.cost_line`) when there is an earlier run;
  and the pin; "What it can do:" with the three trifecta legs as checkboxes, what they mean
  together (`summary_html.TOGETHER`), and the install grants; the summary's headline sentence,
  then one line per concern kind with its place count, in the summary's order, and the
  wording-only line (`summary_html.headline`, `rows`, `WORDING`). When a step produced no output
  the headline says the run did not complete and never that it found none, and the next line
  says why the first such step stopped: the error's type, plus the module of a missing import,
  never the rest of its message (`stage_error`, from `data/<stage>.notes.txt`). With no concerns
  and a step that ran but failed its fixture check, the headline says it may have missed some
  (`summary_html.failed_checks` over the record's stamps; INCOMPLETE is not counted; owner,
  2026-10-25). Model reads (the optional `03-sweep` and `04-pinpoint` steps) on their
  own lines marked experimental (2026-10-03); one line on the fixture checks, from the record's
  stamps in summary.html's terms (owner, 2026-10-25): "Fixture checks: no step failed.", or "Not
  every step worked in this run: " and each step that did not run or failed its check
  (`summary_html.not_working`), or "Fixture checks: none, this run was made without
  validation."; a check skipped for a missing optional tool (INCOMPLETE) is never named; the
  paths of `summary.html`, `details.html` (2026-10-20; the line reads "Everything behind each answer",
  restructure step 7, notes F6), `review.html` (2026-10-12), and `full.md`; the summary's footer
  (`summary_html.FOOTER`).
- A run that stopped (`--until`) before its last coded step (O3): the headline says `This run stopped after the step
  "<plain>", as asked, so Walkdown cannot say whether this repository has the security concerns it looks for.` (or, with
  concerns from the steps that ran, `... as asked. In the steps that ran, Walkdown found security concerns: ...`), and a
  step the stop left out is not named as one that did not run or failed. After the headline block the brief says
  `Stopped after "<plain>", as asked (--until); the steps after it did not run.`, the input file line when a chosen AI
  step wrote one (`Wrote <path>: what "<plain>" would send, <N> passages. Nothing was sent.`), and `To go on: python
  walkdown.py continue <run folder>`, with the option and backend of each chosen read still waiting (` --sweep jev`), under a
  line that names them (`Chosen and waiting: ...`). A plain `continue` leaves those reads out and says so on stderr
  (`note: "Needs a human read" was chosen by an earlier command and is not run here; --sweep jev at continue chooses it`, or
  `to read it, audit the repository again with --sweep jev` once the run has finished and `continue` would refuse) and in the
  report. A stop after intake adds that the folder is read as it is when the run goes on. The report
  stage (`render.py`, `summary_html.py`, `brief.py`) owns these words (`stages/06-report/specs/report.SPEC.md`).
- After the brief, in the same file, version drift against the previous run of the same name (`stages/06-report/specs/report.SPEC.md`, section `drift`; `drift.changes`, made once by the report stage and shared with `changes.md` and the pages): counts only, plus the path of `changes.md`; one line when the version is the same and nothing differs; with the same version and a difference, a header saying every difference comes from Walkdown (`drift.since`, 2026-10-19); never fails the audit (2026-10-04). `walkdown.py diff <old> <new>` is a route to that comparison (`stages/06-report/drift.py`, run with the chosen interpreter): it compares any two runs.
- **A held run** (M9 slice B): the check of the run (`05-qa`) runs after the steps and the record; when it finds a gap
  (a step that did not run or failed, a step whose fixture check did not pass or could not be made, a chosen model read in
  which no passage got an answer) the report is not written, and what is printed is the brief the check wrote: `Walkdown
  brief: <name>`, `This run is held before the report: the check of the run found N gaps.` (after a crash, `found 4 gaps (1
  step failed, and the 3 after it did not start)`), each gap by step and check, `No report was written. The
  saved outputs of the steps that ran are in <data folder>.`, then the two ways on, `To write the report with what ran:
  python walkdown.py continue <run folder>` and `Or fix the cause and audit the repository again.` (with what Walkdown knows
  of the cause, such as a missing key, on a line after it, and `To see why: python tools/grader/grader.py all` last when a
  fixture check could not be made). It holds Walkdown's own words and paths only
  (`stages/05-qa/specs/qa.SPEC.md`, section `hold`). If a step failed, its name and its exit code and error's type are
  on stderr (`stage 02.3-graph failed: exit 1: ValueError`); the whole messages are in `data/<step>.notes.txt`.
- Exit code: the runner's (2 for a bad target or a failed clone, which intake reports; 1 when a step failed or the run is
  held); 2 for no interpreter with the packages or an option refused.

## Must never

- Put text from the audited repository in the brief: no quote, file name, path inside the
  repository, or defined word. Headlines are Walkdown's own; the two that embed a defined word
  are replaced by fixed wording. The brief is what a chat assistant holding tools may read.
- Run anything from the cloned repository.
- Delete or overwrite anything except its own clone of the same URL in `ReposToExamine/<name>`.

## Done when (each backed by a test in `tests/test_walkdown.py`)

1. URLs and folders are told apart, and names derived, as above (intake:
   `stages/01-intake/tests/`). The target and every option go to the runner as given, parsed once, and nothing
   is fetched here (`test_the_target_and_the_options_go_to_the_runner_as_given`,
   `test_walkdown_holds_no_fetch_code`); a file or a path that is not a folder ends the run with
   intake's message (`test_a_target_intake_refuses_ends_the_run`).
2. The front door prints the brief file the report stage wrote, as it is, and a run with none never exits 0
   (`test_the_router_prints_the_brief_file_the_report_stage_wrote`, `test_a_whole_run_through_the_router_prints_what_the_report_stage_saved`);
   `diff` is a route to the report stage's comparison (`test_diff_is_a_route_to_the_report_stages_comparison`); it holds
   only routing: no brief, no stamps, no drift, no import of a stage, one path added to `sys.path`
   (`test_walkdown_holds_only_routing`). The brief reads the validation stamps from the record
   (`data/run.json`), never from LOG.md's text (`stages/06-report/tests/test_brief.py`).
3. The brief carries legs, grants, the summary's headline and concern rows with counts, the
   wording-only line, the fixture-check line, report paths, and the summary's footer
   (`stages/06-report/tests/test_brief.py::test_brief_has_the_facts_and_none_of_the_repository_text`; the other
   items below are tested there too, since the brief moved to the report stage).
4. No text planted in the audited repository's findings appears in the brief.
5. A run whose steps did not run says it did not complete, never "found none", with the first step's error type and missing module, and no text from the error's path or message. The builder step (`02.6-builder`, "Builder checks") counts among the steps, so a run with none at all says 7 steps did not run; one where only it is missing or failed its fixture check names it (`test_the_brief_names_a_builder_step_that_did_not_run_or_failed`).
6. The launching interpreter is used when it has the core modules, even with a `.venv` in the Walkdown folder; with no usable interpreter, what it lacks is named.
7. With no concerns, a failed fixture check makes the headline say it may have missed some; an INCOMPLETE stamp does not, and the fixture-check line never names it (`test_brief_headline_follows_a_failed_check`).
8. Started with a Python without the packages, Walkdown runs itself again under the virtualenv's before cloning anything (intake clones, in the orchestrator, after the handover), with the same arguments, and never a second time (`test_a_python_without_the_packages_hands_over_to_the_venv`).
9. Git runs without prompts, with long paths and a time limit; a missing or private repository, and no git, are said in plain words (intake's `test_git_never_prompts_and_says_why_a_clone_failed`).
10. A GitHub folder link clones the repository at its branch and audits the folder; a file link and a file are errors that say to give a folder (intake's `test_a_github_folder_link_names_the_branch_and_the_folder`, `test_a_github_link_to_a_missing_folder_or_a_file_fails`).
11. The brief's cost lines give counts against the run's expected context and no file or skill name (`test_brief_cost_lines`).
12. The brief's needs line gives counts only: programs, packages, how many are not declared, and places that tie it to one machine; never a package name (`test_brief_cost_lines`).
13. The brief's hosts line gives counts only, with what the hosts named are missing (`test_brief_ready_line`).
14. The brief's trigger line gives counts only, first, and no name or description (`test_brief_trigger_line`).
15. The brief's tools line gives counts only (`test_brief_fit_line`).
16. The brief's current-and-clean line gives counts only (`test_brief_clean_line`).
17. `continue` is a route to the runner with its own options, checked before anything runs; it prints the brief the report
    stage wrote, and a refusal prints nothing but the runner's line, exit 2
    (`test_continue_is_a_route_to_the_runner_and_prints_the_brief`,
    `test_continue_checks_its_options_before_anything_runs`). `--until` reaches the runner as the step's name
    (`test_the_target_and_the_options_go_to_the_runner_as_given`). The router stays routing only
    (`test_walkdown_holds_only_routing`).
18. A run stopped with `--until` and gone on with, on the command line, prints a stop's brief and then the brief of the
    whole run (`test_a_stop_and_continue_through_the_router_print_the_two_briefs`).
19. A held run prints the hold's brief and exits 1 with no page in the folder, and `continue` prints the brief of the report
    it wrote and exits 0
    (`test_a_held_run_prints_the_hold_brief_and_exits_1_and_continue_prints_the_report_brief`).
20. A model name the terminal cannot print (outside ASCII), or one far too long, ends the run with the one refusal sentence and no
    traceback, on a console that holds only the Windows ANSI set
    (`test_a_model_name_the_terminal_cannot_print_ends_the_run_with_a_sentence_and_no_traceback`).
21. `--reads` reaches the runner as the two options it stands for, with the note and the refusals printed before anything runs
    (`test_reads_reaches_the_runner_as_the_two_options_it_stands_for`, `test_reads_refusals_and_the_note_through_the_front_door`,
    `test_continue_takes_reads_through_the_front_door`).
22. `--reads` before the target is one sentence, exit 2, no traceback
    (`test_reads_before_the_target_is_one_sentence_exit_2_and_no_traceback`); after the target, on a machine with nothing to read on, the
    forms in the docs end before any step runs with the one sentence, from a real run under the wall
    (`test_reads_after_the_target_with_nothing_to_run_on_is_one_sentence_exit_2_from_a_real_run`).
23. A whole run through the front door with `--reads`, on each row of the table, makes the pages of the run the same `--sweep` and
    `--pinpoint` make; no key appears in any output or file of it; and in the front door's process a run with no `--reads` neither reads a key nor searches the
    path, the real calls under the helpers watched (a step is a child process, outside the watch) (`test_a_whole_run_with_reads_on_each_row_of_the_table`,
    `test_the_key_is_in_no_output_or_file_of_a_run_with_reads`, which runs both rows that run Jev, the one that prints the note
    among them, and `test_a_default_run_probes_nothing`); with nothing to read on it is refused before the runner, the grader, or a fake is touched
    (`test_reads_with_nothing_to_run_on_is_refused_before_anything_runs`).
24. The skill asks for `--reads <its own model ID>` only when the user asks for model reads, says that Sweep runs on Jev in place of
    its model when Jev is available (its passages go to TypeSafe, a second remote service), and tells the user so in one sentence
    before the run, and runs it only on a yes
    (`test_the_skill_asks_for_reads_with_its_own_model_id_and_only_when_the_user_asks`); the help text, the docstring, the README, the CHANGELOG, the contract, the sweep's
    context, HOW-IT-WORKS, and the specs say the same: each names TypeSafe and gives the choice as a choice
    (`test_the_words_about_reads_say_that_jev_replaces_the_model_and_name_typesafe`).
- 2026-10-29: restructure step 5: `--label`, `--compare`, `--relational`, and `--both` are refused; the brief and the LOG.md stamps read the two AI stages (a stage with no fixture set reads `no fixture set`, not a failed check).
- 2026-10-29: restructure step 5, round 2: the parked environment variables are refused; the brief counts a chosen AI stage that failed.
- 2026-10-29: restructure step 7: the front door only routes. The brief, `stamps()`, `stage_error()`, `own_words()`, and `drift_lines()` moved to the report stage (`brief.py`; the brief is saved as `brief.md` and printed from there); the options are parsed once (`options.py`) and given to `runner.audit`; the stamps come from the run's record, not from `LOG.md`; the details line says "Everything behind each answer". An off value for a model option means off for the flag and the variable alike (notes M14 a).
- 2026-10-29 (after the restructure, notes M10): a target intake refuses ends with intake's message alone; the second line, `the run did not finish`, is left for a run that got a folder and wrote no brief.
- 2026-10-30: O3: `--until STEP` and `walkdown.py continue <run folder>`; the brief of a run that stopped.
- 2026-10-30: M9 slice B: a run with a gap is held and prints the brief of a held run, exit 1; `continue` on a held run
  writes the report with what it has.
- 2026-10-31: M1 slice A: `--sweep` and `--pinpoint` take a backend and, after a colon, a model (`--sweep claude-cli:<model>`), and the
  usage text in the file's docstring says so. The front door still only routes: `options.py` reads the value and refuses one that
  cannot be used before anything runs (exit 2, one sentence). The fix round (the same day) holds a model name to an allowed set of
  ASCII characters, so a name outside ASCII no longer reaches the brief the front door writes to the console (it ended in a
  traceback on a console that cannot print it), and a refusal is printed in ASCII and cut at 80 characters.
- 2026-11-01: the loaded-model build: `--reads [model]`, resolved in the check into `--sweep` and `--pinpoint`; `continue` takes it too; the usage text in the file's docstring says so. The front door still only routes (`options.Parser` is the parser, and `options.check` does the resolving).
- 2026-11-01: the loaded-model build, fix round: the usage text in the file's docstring says what `--reads` runs (Sweep on Jev when Jev is available, else on the Claude model named; Pinpoint on the Claude model named; tools off), and a backend typed as the model is the sixth refusal.
- 2026-11-01: the loaded-model build, before merge: the docstring names TypeSafe. The default run's watch is said to cover the front door's process (a step is a child process). The test of the words holds the claim in every place a reader meets it and pins no sentence; it had pinned the help and the docstring to not naming TypeSafe. The skill runs `--reads` only on a yes, after telling the user where the text goes (the owner, 2026-11-01).
