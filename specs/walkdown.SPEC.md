# walkdown.py (added 2026-10-02)

The front door: one command from a folder or a git URL to a finished run and a brief.

## Inputs

`python walkdown.py <target> [--name NAME] [--fresh | --keep] [--label B] [--compare B]
[--relational B] [--sweep B] [--pinpoint B] [--both] [--revalidate] [--context N] [--hosts a,b]`, `python walkdown.py --version`,
`python walkdown.py diff <old run> <new run>`

- `target`: a folder, or a git URL (`http(s)://`, `git@`, `ssh://`, or ending in `.git`,
  unless a folder by that name exists). A GitHub folder link,
  `https://github.com/<owner>/<repo>/tree/<ref>[/<path>]`, clones the repository at `<ref>` (the
  first part after `/tree/`, a branch or tag) and audits the folder `<path>` (2026-10-25,
  review C41: a link copied from GitHub was taken as a git URL and failed to clone). A file
  link (`/blob/`) or a file is an error that says to give the folder holding it.
- `--name`: the run folder name; default the URL's or folder's last part without `.git` (for a
  folder link, the folder's last part), reduced to letters, digits, `.`, `_`, `-`.
- Stage 6 flags pass through to `stages/08-report/run.py` unchanged.
- `--revalidate` passes through too: re-run the fixture validation even when a stamp for the
  same code is cached (2026-10-03).
- `--version` prints `walkdown <VERSION>` and exits (2026-10-04).

## Outputs

- Before anything else, the clone included, the interpreter: the one Walkdown was started with
  when it can import every core module (`CORE_MODULES`: requirements.txt less pytest), else
  the project virtualenv's when that can (2026-10-21: an empty `.venv` in the Walkdown folder
  was preferred over a working interpreter, and every stage failed). When it is the
  virtualenv's, Walkdown runs itself again under it with the same arguments and returns that
  exit code, so the brief, version drift, and `diff` run there too (2026-10-25, review C41:
  started with a system Python, drift said "No module named 'yaml'" and `diff` crashed). When
  neither can, it runs nothing: it names the interpreter and the modules it lacks, with the
  `pip install -r requirements.txt` line, exit 2. `--version` and `--help` need no packages.
- A URL is cloned shallow (`git clone --depth 1 -- <url>`) into `ReposToExamine/<name>`. An
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
- Runs `stages/08-report/run.py <target> --repo <name> ...` with the interpreter above, and
  prints `Using Python at <path>` on stderr first.
- `--context` passes through to stage 8 (the expected context; slice 1, 2026-10-26), and `--hosts`
  (the hosts the builder builds for; slice 3).
- Prints the **brief** to stdout, in `summary.html`'s terms (owner, 2026-10-21): files examined;
  then one line on triggering (slice 4, `summary_html.brief_trigger_line`): "Will it trigger: <n>
  skills, <c> commands, <a> agents; <h> places that break a host rule, <g> from guidance; <o> pairs
  of descriptions that overlap."; then two lines on cost, counts only (`summary_html.brief_cost_lines`, slice 1): "Every session:
  <X> tokens. Largest skill at its fullest: <Y> tokens (<Z> of <C>)." (with "Every session in
  this folder: <P> tokens." when there are project files) and "Not used at run time: <n> files
  (<t> tokens).", the expected context read from `LOG.md`; then one line on what it needs
  (slice 2): "Needs: <n> programs, <m> packages; <k> not declared. Ties to one machine: <p> places.";
  then one line on hosts (slice 3, `summary_html.brief_ready_line`): "Ready for: <h> of 7 hosts have
  their files here; copies that differ: <d>; one-host features: <f>." with "For the hosts named:
  <k> things missing." when `LOG.md` names target hosts;
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
  (`summary_html.failed_checks` over the LOG.md stamps; INCOMPLETE is not counted; owner,
  2026-10-25). Stage 6 model reads on their
  own lines marked experimental (2026-10-03); one line on the fixture checks, from LOG.md's
  stamps in summary.html's terms (owner, 2026-10-25): "Fixture checks: no step failed.", or "Not
  every step worked in this run: " and each step that did not run or failed its check
  (`summary_html.not_working`), or "Fixture checks: none, this run was made without
  validation."; a check skipped for a missing optional tool (INCOMPLETE) is never named; the
  paths of `summary.html`, `details.html` (2026-10-20), `review.html` (2026-10-12), and
  `full.md`; the summary's footer (`summary_html.FOOTER`).
- After the brief, version drift against the previous run of the same name (`stages/08-report/specs/drift.SPEC.md`): counts only, plus the path of `changes.md`; one line when the version is the same and nothing differs; with the same version and a difference, a header saying every difference comes from Walkdown (`drift.since`, 2026-10-19); never fails the audit (2026-10-04). `walkdown.py diff <old> <new>` compares any two runs.
- Exit code: the stage 8 runner's; 2 for a bad target, a failed clone, or no interpreter with
  the packages.

## Must never

- Put text from the audited repository in the brief: no quote, file name, path inside the
  repository, or defined word. Headlines are Walkdown's own; the two that embed a defined word
  are replaced by fixed wording. The brief is what a chat assistant holding tools may read.
- Run anything from the cloned repository.
- Delete or overwrite anything except its own clone of the same URL in `ReposToExamine/<name>`.

## Done when (each backed by a test in `tests/test_walkdown.py`)

1. URLs and folders are told apart, and names derived, as above.
2. Validation stamps are read from LOG.md's table.
3. The brief carries legs, grants, the summary's headline and concern rows with counts, the
   wording-only line, the fixture-check line, report paths, and the summary's footer.
4. No text planted in the audited repository's findings appears in the brief.
5. A run whose steps did not run says it did not complete, never "found none", with the first step's error type and missing module, and no text from the error's path or message.
6. The launching interpreter is used when it has the core modules, even with a `.venv` in the Walkdown folder; with no usable interpreter, what it lacks is named.
7. With no concerns, a failed fixture check makes the headline say it may have missed some; an INCOMPLETE stamp does not, and the fixture-check line never names it (`test_brief_headline_follows_a_failed_check`).
8. Started with a Python without the packages, Walkdown runs itself again under the virtualenv's before cloning anything, with the same arguments, and never a second time (`test_a_python_without_the_packages_hands_over_to_the_venv`).
9. Git runs without prompts, with long paths and a time limit; a missing or private repository, and no git, are said in plain words (`test_git_never_prompts_and_says_why_a_clone_failed`).
10. A GitHub folder link clones the repository at its branch and audits the folder; a file link and a file are errors that say to give a folder (`test_github_folder_links_and_files`).
11. The brief's cost lines give counts against the run's expected context and no file or skill name (`test_brief_cost_lines`).
12. The brief's needs line gives counts only: programs, packages, how many are not declared, and places that tie it to one machine; never a package name (`test_brief_cost_lines`).
13. The brief's hosts line gives counts only, with what the hosts named are missing (`test_brief_ready_line`).
14. The brief's trigger line gives counts only, first, and no name or description (`test_brief_trigger_line`).
15. The brief's tools line gives counts only (`test_brief_fit_line`).
16. The brief's current-and-clean line gives counts only (`test_brief_clean_line`).
