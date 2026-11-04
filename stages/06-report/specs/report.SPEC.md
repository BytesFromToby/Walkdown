# report: spec

One spec for the `06-report` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. Merged from the per-script specs in restructure step 8a.

## The reports

What a run gives its readers, who each output is for, what the reports may and may not say, and
how the specs stay true. Every output listed here has its own spec; this file is the index.

Status: decided by the owner 2026-10-20; the two pages rebuilt as report v3, "glance and know",
2026-10-27 (owner; the `glance` section). Built: `summary.html`, `details.html`, `review.html`,
`full.md`, `changes.md`, marks that carry over, and the docs (see "Build status").

### Two readers

1. **Deciding whether to use a repository** ("is this safe?"). Wants one page: what it can do,
   what Walkdown found that could be dangerous, and what to ask before using it.
2. **Improving or investigating a repository.** Wants every detail, and a way to work through
   it: mark what has been looked at, set aside what is fine, and see only what is new next time.

One page served both until 2026-10-20 and did neither well. Each reader now has their own.

### The outputs

A run folder (`docs/RUN-FOLDER.md`) holds the reports at the top and everything else in `data/`.

| File | Reader | What it is | Spec |
|---|---|---|---|
| `summary.html` | anyone, no computer skills needed (owner, 2026-10-27) | One page, eight questions at a glance, each with a short label and a one-line answer: will its skills switch on, how much of the AI's memory it uses (the one place for tokens), what comes in the package, will it work on someone else's computer, with other AI tools, does it ask only for the tools it needs, is it finished and up to date, anything to be careful about | the `summary_html` section, the `glance` section |
| `details.html` | improving | The same eight questions with everything behind them: tables, charts, and every place in folded lists; then what Walkdown didn't check | the `details_html` section, the `glance` section |
| `review.html` | improving | The places to check, one at a time, each marked Concerned, Not concerned, or Not sure | the `review_html` section |
| `full.md` | either | Every finding with file and line: the complete record, as text | the `render` section |
| `changes.md` | either | What changed since the previous run of the same repository | the `drift` section |
| `marks.json` | improving | The reader's marks, saved by the reader; carried to later runs | the `marks` section |
| `brief.md` | either (and a chat assistant) | The brief `walkdown.py` prints: counts, legs, grants, the fixture-check line, the paths of the reports; no text from the repository (restructure step 7: now saved in the run folder) | the `brief` section |
| `LOG.md`, `data/` | either | Run log; stage outputs, notes, the record (`data/run.json`), the limits (`data/limits.md`), the text Walkdown read | the `run` section; `stages/_shared/specs/shared.SPEC.md`, section `layout` |

Cut (owner, 2026-10-20): `summary.md` (the summary as text) and `summary-v1.html` (report v1,
kept while v2 settled). Report v1 stays retrievable at git tag `report-v1`.

The brief that `walkdown.py` prints (it is `brief.md`) names `summary.html` first, then `details.html`,
`review.html`, and `full.md`.

### What the reports may say

- **No verdict.** Never "do not use this", "safe", "unsafe", a score, a grade, or a rank of one
  place over another. (Owner, 2026-10-20; to revisit.)
- **"Security concerns" is allowed.** Question 8 counts the places in the fixed concern kinds
  and names the kinds (the `summary_html` section). The kinds and their order are fixed; nothing is
  picked by how bad it seems.
- **Plain words.** The summary is for a reader with no computer skills: fixed templates, file
  names only in small "where" notes, tokens in question 2 only, and no repository text but hidden
  text that reads like an instruction (80 characters; owner, 2026-10-27).
- **Nothing found never means safe.** `summary.html` says so once, in its footer, and names any
  step that did not run or did not pass its fixture check; what was not checked is in "What
  Walkdown didn't check" on `details.html` and in `full.md` section 7. A question whose check did
  not run says "Not measured", never "nothing".
- **Capability, never intent.** A box says what the repository could do. Whether it does is only
  seen by running it, and the cards say so.
- **Repository text is escaped and never run.** No page opens a link, loads a page, or shows a
  secret's value. No value from the repository starts a line of `full.md`: every line goes through
  `one_line` at the one point the report is put together.

### Marks

One marking model: **Concerned**, **Not concerned**, **Not sure**, made on `review.html` only
(owner, 2026-10-27); the other two pages say how many places are marked. "Ignore" is Not
concerned. One `marks.json` per run, written only by the reader. Marks carry over to later
runs of the same repository, matched by what was flagged rather than by line number, so moved
lines keep their marks and changed lines get a fresh look (the `marks` section).

### Keeping the specs true

This is how a change stays traceable from the owner's decision to the code and its tests.

- Every output and every script has a spec in `specs/`.
- A spec describes current behavior, top to bottom. A change to an output changes its spec in
  the same commit; the old wording goes, and one line is added to the spec's **History**.
- **History** is the last section of every spec: date, what changed, and why (an owner decision
  or a review item, such as `C36`).
- Each "Done when" item names the test that backs it.
- A part not yet built is marked **To build** where it is described, and loses the mark in the
  commit that builds it.
- The public docs (`docs/READING-THE-REPORT.md`, `docs/RUN-FOLDER.md`, `docs/HOW-IT-WORKS.md`)
  follow the specs in the same commit.

### Build status

| Part | State |
|---|---|
| This spec set | written 2026-10-20 |
| `summary.html`, one page | built 2026-10-20 |
| `details.html` (the long page, renamed) | built 2026-10-20 |
| Not concerned boxes on `details.html` | built 2026-10-20; removed 2026-10-27 (report v3) |
| Report v3: `summary.html` and `details.html` as eight questions (`glance.py`) | built 2026-10-27 |
| Marks carried over, stable keys | built 2026-10-20 (all three pages) |
| Cut `summary.md` and `summary-v1.html` | built 2026-10-20 (a re-render removes them) |
| Docs follow | built 2026-10-20 (README, docs/, CLAUDE.md, `05-report` CONTEXT, CHANGELOG, the skill) |

### History

- 2026-10-20: written (owner): two readers, two pages; no verdict, "security concerns" allowed;
  Not concerned replaces ignore; marks carry over; `summary.md` and `summary-v1.html` cut; specs
  describe current behavior and end with a history. Later the same day: no "Not checked" on
  `summary.html` (owner).
- 2026-10-26 (owner, plan for builders): `summary.html` became the builder's page.
- 2026-10-27 (owner, report v3, "glance and know"): both pages rebuilt as eight questions for a
  reader with no computer skills; marking on `review.html` only; the old pages replaced outright.
- 2026-10-30 (M9 slice B, last fixes): a hook's matcher, a plugin's name, a front matter field, or a file name with a line
  break in it started a line of its own in `full.md` and read as the report's: `one_line`. It was so before this slice.

## run

The report stage's entry point: from a run folder's `data/` and its record, write every report. Its one job.
It runs no stage, validates nothing, and calls no model. Running the steps is the runner's
(`stages/_shared/specs/shared.SPEC.md`, section `runner`); the front door only routes (`specs/walkdown.SPEC.md`).

Status: built.

### Inputs

```
python stages/06-report/run.py <run folder> [--context N] [--hosts a,b]
python stages/06-report/run.py --rerender <run folder> [--context N] [--hosts a,b]     (the same)
```

- `<run folder>`: `RepoResults/<repo>/<run>`, as the runner left it: the stage outputs and their notes in `data/`
  and the record `data/run.json` (`stages/_shared/specs/shared.SPEC.md`, section `record`). `--rerender` is a synonym, kept because
  re-rendering is how the stage runs for a run that already has its reports.
- `data/05-qa.json`, the check of the run's output (`stages/05-qa/`, M9 slice B): what is missing from the run (`qa.gap`)
  and what it did not examine (`qa.limit`). Section 7, `data/limits.md`, and the lists of steps that did not work are drawn
  from it (the `qaview` section); this stage gathers none of them.
- `--context`, `--hosts`: the expected context in tokens (`32k`, `200k`, `8192`) and the AI hosts built for. Declared
  once, in `options.py`, with the front door's; the run's own come from its record and these replace them for
  this render (they are not saved: the next render takes the record's again). A bad value is exit 2.

### Behavior

1. A folder that is not a run (no `LOG.md` and no `data/`) is exit 2: `error: not a run folder (no LOG.md): <path>`.
   A run made before this version (`record.made_before`: the layout before 2026-10-02, the stage names before
   restructure step 1, no `data/run.json`, or a record of an older format, as a run made between step 7 and step 7b
   has): one plain line, exit 2, nothing written: `error: this run was made before this version of Walkdown, so it
   is not re-rendered; audit the repository again.` (notes O5, M3; step 7b). A run the check of the run **held**
   (the record has `held`; M9 slice B) is not drawn either: `error: this run is held by the check of the run, so no
   report is written; python walkdown.py continue <run folder>`, exit 2, nothing written. `continue` releases it first: the
   runner starts this stage on the held run with its own option `--released-at <time>` (hidden from `--help`), which lets it
   draw a run whose record still says held, and the time is the one LOG.md gives for the release (the runner records the
   release once this stage has exited 0). A
   run with no readable `data/05-qa.json` is exit 2 with one line (`error: 05-qa.json is missing or cannot be read; the
   check of the run (data/05-qa.json) has not been made for this run: audit the repository again`).
2. It reads each stage's report and notes from `data/` (intake's report only for `LOG.md`'s table, since no report has
   a section for it). An AI stage that was chosen and left no report is a step that did not work: it has a notes file
   or a step in the record, and its key in the reports is `None`. A stage nobody chose has neither and is not a key.
   The AI step a stop made write its input file (the record's `prepared`, O3) is neither: it did not run, so it is
   no key, and its notes stay in the file. `meta["stop"]` is the record's stop (`record.stop_of`: where the run stopped
   and what was prepared; None for a run that went through), `meta["continued"]` the record's `continued`, and
   `meta["not_started"]` the record's `not_started` (M9: a chosen model read that was not started), `meta["chosen"]` its
   `chosen` (M9 slice B: the model reads this run chose); the pages,
   the brief, `LOG.md`, and the limits read them (the sections below). `meta["qa"]` is the check of the run's output
   (`qaview.Qa`) and `meta["qa_run"]` the record's `qa` (when the check ran). A step output that is not a report (not
   valid JSON, or not a document with a list of findings, as a saved `[]` or `{}`: `pipeline.read_report`, the test the
   check applies, which also asks each finding to be a dict with a `check`) is left out as if it were not there: the check
   has named it a gap. The capability step's side file `capability.json` is read the same way, and one that is not a report
   counts as none (the pages draw from the step's own capped output; the step is named as one that did not work if it has
   none). The notes the pages read are the
   step's own (`pipeline.own_notes`: the lines it wrote as `note: ...`, and none from a step that failed), the same lines
   the check reads. The version in `meta["tool"]` is
   `toolversion.tool_version`. A saved output can still keep words from a line the secret scan flagged (a run stopped before the
   runner masked it, or saved before the runner did): `load` masks all of them in memory (`secretmask.mask_reports`), `capability.json`
   with them, for every report at once, and writes no step output.
3. It writes, in this order:
   - `LOG.md`, when the folder has none (a first pass; `continue` removes it, so the report stage writes it again): the
     run's header and its stage table, from the record (`render.log`; intake's row first and the builder step's last of
     the coded rows, `render.LOG_ROWS`; a row for an AI stage only when it was started; a step's result is its count,
     "1 finding" or "3 findings", or `FAILED: <why>`; the report stage's row lists its outputs, `brief.md` and
     `data/limits.md` among them; there is no `07-limits` row; the check of the run has a row of its own before the
     report stage's, with its times from the record's `qa`, its count of findings, and its stamp), then, for a run that was stopped or gone on with, one
     line for each time it went on, one for the stop it is at, and one for the input file the stop wrote
     (`render.stop_log_lines`; O3), and, first, one for a hold the check of the run made and `continue` released (the
     record's `released`; M9 slice B). A folder that has one keeps it.
   - `data/limits.md`: what the run did not examine (`render.limits_doc(meta)`), the same text as section 7 of `full.md`,
     drawn from the check of the run's findings (was `data/07-limits.md`; section 7 has no stage, notes O2).
   - `changes.md` and the comparison with the previous run: once (`drift.changes`), feeding the summary page, the
     details page, and the brief.
   - `summary.html` (the `summary_html` section), `details.html` (the `details_html` section), `review.html`
     (the `review_html` section), `full.md` (the `render` section), with the reader's marks from `marks.for_run`: the
     `marks.json` saved in the run, or else the newest earlier run's, carried by stable key (the `marks` section). The
     pages a run no longer writes (`layout.RETIRED`: `summary.md`, `summary-v1.html`) are removed.
   - `brief.md` (the `brief` section), built from the same data, the record's stamps, and the same comparison.
4. A folder that already had a `LOG.md` gets one line appended saying when and with which Walkdown version the
   reports were written again. A first pass appends nothing.
5. It prints the run folder's path on stdout.

Exit 0; 2 for a folder that is not a run, a run made before this version, or a bad option.

### Must never

- Detect, judge, or advise on installing; run a stage or the grader (the stamps are the record's, as measured
  when the audit ran).
- Write inside the audited folder; read `LOG.md`'s text back.
- Import another stage's code (it uses `stages/_shared/` and its own modules).

### Done when (tests in `tests/test_run.py`)

1. A run folder with its reports removed gets them all again from `data/` and the record, with `LOG.md` written once,
   `data/limits.md`, and `brief.md` (`test_the_report_stage_writes_every_report_from_the_data_and_the_record`).
2. `--rerender <folder>` is the same as giving the folder; each render appends one line to an existing log
   (`test_rerender_is_the_same_as_giving_the_run_folder`, `test_rerender_rebuilds_report_only`: the stage outputs are
   unchanged and a retired page is removed).
3. The stamps come from the record and the log is not read back (`test_the_stamps_come_from_the_record_and_not_from_the_log`).
4. A render reads the reader's `marks.json` (`test_rerender_reads_saved_marks`); a later run carries it
   (`tests/test_marks.py`).
5. `--context` and `--hosts` are kept from the record and can change on a render
   (`test_context_and_hosts_are_kept_and_can_change_on_a_rerender`).
6. A chosen AI stage that left no report is named, and one nobody chose is not
   (`test_a_rerender_names_a_chosen_ai_stage_that_left_no_report`); saved AI outputs are read back
   (`test_a_rerender_shows_the_ai_stages_a_run_chose`).
7. A folder that is not a run is exit 2 (`test_rerender_needs_a_run_folder`); a run made before this version, in
   any of its forms, gets the one plain line and nothing is written
   (`test_a_run_made_before_this_version_is_not_rerendered_and_the_message_is_one_plain_line`; a record of an
   older format: `test_a_run_whose_record_has_an_older_format_is_not_rerendered`).
8. A run whose inventory failed is still reported, from its record
   (`test_a_run_made_by_this_version_without_an_inventory_is_still_reported`).
9. A run that stopped as asked (O3) is reported from its record: the step that wrote only its input file is no key of
   the reports and no step failed, `LOG.md` carries the stop and the later continues, and the stop reaches
   the pages, the brief, and the limits
   (`test_a_stopped_run_is_reported_with_its_stop_and_the_prepared_step_is_not_a_failure`,
   `test_the_log_has_a_line_for_each_time_a_run_went_on`).
10. A Sweep in which no passage got an answer, and a Pinpoint the record says was not started, reach section 7, the
    limits file, both pages, and the brief in the same count, and the headline says the coded checks are complete
    (`test_a_sweep_that_got_no_answer_and_a_step_not_started_reach_every_page_and_the_brief`).
11. Section 7, `data/limits.md`, the summary's warning, and the brief are drawn from `data/05-qa.json`: change the file and
    they change (`test_section_7_the_limits_file_and_the_lists_of_steps_that_did_not_work_are_drawn_from_the_checks_output`);
    a gap of a kind the report does not know is in section 7 and among the steps that did not work
    (`test_a_gap_of_a_kind_the_report_does_not_know_is_in_section_7_and_among_the_steps_that_did_not_work`); a run with no
    readable output of the check is not drawn (`test_a_run_with_no_output_of_the_check_is_not_drawn`); `LOG.md` has a row
    for the check (`test_the_log_has_a_row_for_the_check_with_its_times_its_count_and_its_stamp`).
12. A held run is not drawn, and says the command that releases it
    (`stages/_shared/tests/test_runner.py::test_the_report_stage_will_not_draw_a_held_run_and_names_continue`).
13. `LOG.md` says a hold that `continue` released, in a line of its own before the stop's lines, and says nothing for a run
    that was never held (`test_the_log_says_a_hold_that_continue_released_and_a_run_never_held_says_nothing`).
14. A key the scan flagged, in hidden characters on its line, in a hidden comment, or on a later line of hidden text, is in no
    report and no step output, and every hidden place is still counted and named by file and line
    (`test_a_key_the_scan_flagged_is_in_no_report_and_no_step_output`); a run saved before the mask is masked when drawn and its
    data is left alone (`test_a_run_saved_before_the_mask_is_masked_when_drawn_and_its_data_is_left_alone`).
15. On a whole run of a made-up skill with one key in every place a step keeps a person's words, no key, whole or cut short, is in any
    report or step output (`test_secret_fields.py`, `test_a_key_the_scan_flagged_is_in_no_report_and_no_step_output`); every place is
    still counted and a masked hook is named by its line (`test_each_place_is_still_counted_and_named_by_where_it_is`); a plain event
    and a plain tool stay (`test_a_plain_event_and_a_plain_tool_stay_since_they_are_what_a_page_is_for`); a line with no key keeps its
    words (`test_a_line_that_holds_no_key_keeps_its_words`); each step read the words before they were masked
    (`test_the_steps_read_the_words_before_they_were_masked`); `capability.json` is masked with the reports
    (`test_the_side_file_of_the_capability_step_is_masked_with_the_reports`); and a run saved before this rule is masked when drawn and
    its data is left alone (`test_a_run_saved_before_the_mask_is_masked_when_drawn_and_its_data_is_left_alone`).

### History

- 2026-09-29: built (stage 8 v1). 2026-09-30: `--rerender`. 2026-10-01: stage 6 passes through. 2026-10-02: the run-folder
  layout (reports at the top, `data/` below). 2026-10-03: `--revalidate`, cached stamps. 2026-10-12: `review.html` and
  `marks.json`. 2026-10-16: report v2; changes since the last run. 2026-10-20: owner: the long page is
  `details.html`; marks carried from an earlier run. 2026-10-28: restructure step 2: intake runs first, `--repo`
  defaults to intake's name.
- 2026-10-29: restructure step 5: the AI stages run only when chosen; the parked options are refused; `no fixture set`
  for Pinpoint; a chosen AI stage that failed is a step that did not work.
- 2026-10-29: restructure step 7: the report stage does one job. Running intake and the steps, the run-folder naming,
  the options, and the grader's stamps went to the runner (`stages/_shared/runner.py`); the stage reads the run's
  record (`data/run.json`, a new file) and writes every report, `LOG.md` once, `data/limits.md` (was `data/07-limits.md`),
  and `brief.md` (the front door used to build the brief and print it without saving it). `--rerender` is a synonym;
  it no longer re-runs the grader (the stamps are the record's) and takes no `--no-validate`. One layout: a run made
  before this version is refused in one plain line (was: the old layout re-rendered in place, and `drift.predates_rename`
  gave a longer message). The comparison with the previous run is made once.
- 2026-10-29: restructure step 7b: the refusal asks `record.made_before`, so a run with a record of an older format
  (made between step 7 and step 7b, with the old shape of data inside) is refused too; the line no longer says
  "it has no data/run.json", so one line fits both cases.
- 2026-10-30: O3: `meta["stop"]` and `meta["continued"]` from the record; the step that wrote only its input file is no
  key of the reports; `LOG.md` gains the lines for a stop and each continue; `tool_version` moved to
  `stages/_shared/toolversion.py`, which this stage and the runner both read.
- 2026-10-30: M9 slice A: `meta["not_started"]` from the record.
- 2026-10-30: M9 slice B: the folder is `stages/06-report/` and the step is `06-report` in `stages/stages.json` (it was
  `05-report`); the new step `05-qa` runs before it. The entries above keep the name the folder had.
- 2026-10-30: M9 slice B: the stage reads `data/05-qa.json` (`qaview`) and draws section 7, `data/limits.md`, and the lists
  of steps that did not work from it instead of gathering them; it refuses a held run and a run with no output of the
  check; `LOG.md` has a row for the check; an output of a step that cannot be read is left out, and nothing crashes. The words on the
  pages are the same for the same run.
- 2026-10-30: M9 slice B, second fix round: steps whose fixture check could not be made (ERROR, SETUP ERROR, NOT BUILT, `no
  fixture set` on a step that has fixtures) ran and wrote their output, so they are not "steps that did not work"
  (`not_working`, `failed_checks`) and are said once, apart (`unchecked_sentence`: the one step with what its check gave, or
  `8 steps could not be checked against their fixtures, so a "none" from them is not measured`): in the warning, details.html's
  first line, the headline, the first card's caveat, and the brief's last line only when the headline does not carry it (a run
  that did not complete or that stopped). Before, a release with eight such steps said
  `not every step worked, so it may have missed some` and the same clause eight times.
- 2026-10-30: M9 slice B, second fix round: a model read an earlier command chose and `continue` left out is said (the log's
  `Soft models:` line, section 6, section 7 as a `read-dropped` limit, and the brief; before, the log and section 6 said no
  read was chosen), and the stop's brief puts the options of the reads that wait in its `To go on:` command.
- 2026-10-30: M9 slice B, second fix round: a half-written `capability.json` (a full disk) held the run and then crashed
  every `continue` and re-render and `diff`; `run.py` and `drift.load` read it through `pipeline.read_report` and count a
  failure as no file. A saved inventory with no `inv.pin` (`render.pin_of`) draws the pages instead of crashing them. Every
  saved file of a run with every bad body goes through the check, the hold, the release, a re-render, and `diff`
  (`tests/test_saved_outputs.py`).
- 2026-10-30: M9 slice B, second fix round: a file name or a reason from the repository is printed on one line wherever
  `full.md` and `data/limits.md` print it (`loc`, and the `skip`, `unread`, `unscanned`, and `note` lines of section 7): a
  name with a newline and `- ` or `## ` after it forged a bullet or a heading (`flat`, `stagenote`). `changes.md` (`drift`)
  prints each bullet on one line the same way (`test_a_file_name_with_a_newline_is_one_line_in_changes_md`); the HTML pages
  escape a name and a newline is a space there.
- 2026-10-30: M9 slice B fix round: `LOG.md`'s row for a step that went well and has no readable output says
  `no readable output` where it counted findings (it crashed the report stage on the first pass after a release). An output
  that was valid JSON and no report (`[]`, `{}`) is left out like one that cannot
  be read; before, it crashed the report stage when `continue` released the run (and `drift.load`, which compares a run with the
  previous one, is tolerant the same way). The notes the pages read are a step's own `note: ...` lines, and none from a step
  that failed: a crashed step's stderr was read as notes before, so a line of an error's message with a limit word in it
  reached "What Walkdown didn't check" on `details.html`.
- 2026-11-01: `load` masks the saved reader in memory (`secretmask.mask_reader`), so every report reads the one masked copy and a
  re-render writes no step output (`test_a_run_saved_before_the_mask_is_masked_when_drawn_and_its_data_is_left_alone`,
  `test_a_key_the_scan_flagged_is_in_no_report_and_no_step_output`). A run the runner has masked is the same; a run stopped before
  `02.5-capability` or saved before this rule still holds the words in its file. `full.md` printed a divergence's `text` and `decoded`
  on a line the scan flagged, and `read.fold`'s `removed` spelled tag characters in order.
- 2026-11-01: `load` masks every step's saved words in memory (`secretmask.mask_reports`), and takes `capability.json` to mask with them,
  so `report` reads that file before it calls `load`. A hook's command, a description, a link's address, and more reached `full.md`,
  `details.html`, and `summary.html` from a flagged line.

## brief

Restructure step 7.

The brief: a plain summary of a finished run, saved as `brief.md` in the run folder. The front door prints that
file and builds nothing. Before step 7 `walkdown.py` built the brief itself: it re-read `data/*.json`, imported the
report stage's modules, read the stamps back out of `LOG.md`'s table, and printed the text without saving it
(notes F1).

### Inputs

`build(meta, reports, stamps, changes, run_dir, data) -> str`; `write(run_dir, meta, reports, stamps, changes, data)`
saves it as `brief.md` and returns the path.

- `meta`: `repo`, `context` (tokens; 32,000 when empty), `hosts` (the target hosts), `stop` (the record's
  `stop_of`, O3: set for a run that stopped as asked).
- `reports`: `{stage: report}` as the report stage loaded them, with `None` for an AI stage that was chosen, started,
  and left no report (a step that did not work).
- `stamps`: `{stage: validate.Stamp}` from the record (`record.stamps_of`): never parsed back out of `LOG.md`.
  `results_of(stamps)` is `{stage: result word}` for the stages the brief names.
- `changes`: the one comparison with the previous run (`drift.changes`) or None.
- `data`: the run's `data/` folder: a step with no output is explained from its notes file (`stage_error`).

### Outputs

The text the front door has always printed, in `summary.html`'s terms (owner, 2026-10-21): how many files and the
pin (`Files: <n>. Pinned: ...`; `Files examined:` until 2026-11-04); what Walkdown examined, as counts
(`coverage.brief_line`, since 2026-11-04); one line each on triggering, cost (two), needs, hosts, tools, and current and clean, counts only; "What it can
do:" with the three trifecta legs as checkboxes, what they mean together, and the install grants; the summary's
headline, then one line per concern kind with its place count and the wording-only line; the model reads, marked
experimental; **the token line** (M1 slice A) in a paragraph of its own after them, whenever a model read ran:
`Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint 1,490 in, 73 out; Sweep's fixture check 39,823 in.`
(`render.tokens_line`; each read's tokens as the backend reported them, `not reported` for a read that did not report them,
`sent nothing` for one that sent nothing, the cache counts named when there are some, and `(from 5 of 9 calls)` after a total that only
some of the calls reported (`usage.words`: `reported` above 0 and below `calls`; the clause is on the fixture check's clause too); the
fixture check only when it spent tokens in this run: a stamp reused from an earlier run spent none and says none); one line on the fixture checks (`Fixture checks: no step
failed.`, `Not every step worked in this run: ...`, or `Fixture checks: none, this run was made without validation.`), and
under it, when Sweep ran and its fixtures were measured (`Stamp.measured`), **the fixture line** (`fixture_line`, M1 slice A, owner's
answer 3): `Sweep on jev: found 33 of 34 in its fixtures.` (the backend as the record kept the person's option, on one line and cut at `stagenote.MODEL_CAP`, as is the one the waiting line of a
stopped run names; with rows that got no
answer, `found 30 of 34 in its fixtures (2 got no answer)`). A low count shows and holds nothing; the pages' Sweep stamp says the
same. The paths of `summary.html`, `details.html`
(**"Everything behind each answer: <path>"**: the line said "Every section in full" until step 7, which described
the page before report v3; notes F6), `review.html`, and `full.md`; and the summary's footer. Then the changes
lines (`changes_lines`): nothing on a first run; one line when the version is the same and nothing differs; a
header and the counts and `Details: <changes.md>` otherwise. The header is `Changes since <run>: <same words>:`
for the same version of the repository, `Changes since <run> (version drift):` for another, and
`Changes since <run>:` when the earlier run cannot be compared (`not_comparable`), since then the repository
may be the same (2026-10-29, restructure notes M6). The text ends with a newline after the footer and a
newline after the changes lines, so a first run ends with one blank line, as the printed brief always did.

When a step produced no output the headline says the run did not complete and never that it found none, and the
next line says why the first such step stopped: the error's type, plus the module of a missing import, never the
rest of its message (`stage_error`). An AI stage nobody chose is never named; one that was chosen and left no
report counts as a step that did not run.

**A model read whose calls got no answer** (M9, slice A; the page words are the `summary_html` section's). A model
read never adds a security concern, so the headline is built from the coded steps alone (`not_run(qa)`): a
chosen model read that left no output (the error line above still names it) or ran and got no answer for any passage
(`summary_html.model_down(qa)`) adds "The coded checks are complete; the model read did not work." to the headline, which then
has no "cannot say" line for it. With a coded check INCOMPLETE or failed the added sentence is worded as the
`summary_html` section says. "Not every step worked in this run:" names such a read as "<plain> did not run" or "<plain> got no answer for
any passage". After the model reads, the brief has one line for each read with passages that got no answer, counts only
(`<plain>: N of M passages got no answer, after one retry.`, `render.model_read_lines(qa)`; no reason, since a reason can
carry an error's text), and one for a chosen step the record says was not started (`render.not_started_lines(qa)`). The
steps that did not run, the model reads that did not work, and the fixture checks that did not pass are the check of the
run's gaps (`qa`, from `meta["qa"]`); `stage_error` names the first step with no output (`qa.steps_missing()`).

**A run that stopped as asked** (`--until`; O3). A coded step the stop left out (`render.stopped_left`) did not fail:
the lists of steps that did not run or did not work (`not_run`, "Not every step worked") leave it out, and the headline
says why in `summary_html.headline`'s own words (the `summary_html` section). After the headline block (the headline, the concern
rows, the wording-only line) the brief has, in Walkdown's words and its own paths only (`stop_lines`):
`Stopped after "<plain>", as asked (--until); the steps after it did not run.`; after a stop at intake,
`The folder is read as it is when the run goes on.`; the input file line when a step wrote one
(`Wrote <path>: what "<plain>" would send, <N> passages. Nothing was sent.`, the path the file's full path); and
`To go on: python walkdown.py continue <run folder>`, with the option and backend of each chosen read the stop is before
(` --sweep jev --pinpoint claude-cli`; the backends are the record's `backends`, and the prepared step's own backend
fills one the record lacks), so the choice is one copy away and still the person's to run. Each backend is held to the rule for the
option (`common_lines.record_option`) before it is printed: a record changed by hand cannot put words in a command that a model
relays as printed. A read whose value fails has no option in the command, and one sentence says so (`The model option the record kept
for "Needs a human read" could not be used, so the command to go on leaves it out.`). A line above the command names
those reads (`Chosen and waiting: "Needs a human read" (jev); "The line behind each flag" (claude-cli).`). When the stop is before `02.5-capability`, "What it can
do:" has no boxes to show and says `What it can do: not measured, the run stopped after "<plain>", as asked.`; when it is
before `02.1-inventory`, the first line says `Files: none yet. Pinned: nothing yet.` and, with no fixture check
to report, `Fixture checks: none yet, the run stopped before the steps they check.` (the run was validated, for intake).
A stop after the last coded step changes none of this except the stop lines.

### Must never

- Put text from the audited repository in the brief: no quote, file name, path inside the repository, or defined
  word. Headlines are Walkdown's own; the two that embed a defined word are replaced by fixed wording
  (`own_words`). The brief is what a chat assistant holding tools may read.
- Read `LOG.md`, or import more of the report than its own modules.

### Done when (each backed by a test in `tests/test_brief.py`)

1. The stamps are the results in the record (`test_the_stamps_the_brief_reads_are_the_results_in_the_record`).
2. The brief carries the legs, grants, headline and concern rows with counts, the wording-only line, the
   fixture-check line, the report paths, and the footer, with none of the repository's text
   (`test_brief_has_the_facts_and_none_of_the_repository_text`); the details line describes the v3 page
   (`test_the_brief_describes_the_v3_details_page`); the file equals the text built
   (`test_the_brief_is_saved_in_the_run_folder_and_equals_the_text_built`).
3. A run whose steps did not run says it did not complete, with the first step's error type and missing module
   and nothing from the error's path or message (`test_a_crashed_run_says_it_did_not_complete`); the builder step
   counts (`test_the_brief_names_a_builder_step_that_did_not_run_or_failed`); with no concerns a failed fixture
   check says it may have missed some, and INCOMPLETE and no stamp do not (`test_brief_headline_follows_a_failed_check`).
4. The AI stages: a run with none is not missing one, a chosen one that failed is named, and a stage with no fixture
   set is not a failed check (`test_a_run_with_no_ai_stage_is_not_missing_one_and_a_run_with_them_shows_the_model_reads`,
   `test_a_chosen_ai_stage_that_failed_is_counted_in_the_brief_and_one_nobody_chose_is_not`).
8. A model read that got no answer for any passage is a step that did not work and the headline says the coded checks are
   complete; a partial read is only counted; the count holds no reason and no file name; a step that was not started has
   its line (`test_the_brief_counts_passages_with_no_answer_and_a_read_that_got_none_is_a_step_that_did_not_work`,
   `test_the_brief_says_a_chosen_step_was_not_started_and_why`).
5. The cost, needs, hosts, trigger, tools, and clean lines give counts only (`test_brief_cost_lines`,
   `test_brief_ready_line`, `test_brief_trigger_line`, `test_brief_fit_line`, `test_brief_clean_line`).
6. The changes lines come from the one comparison (`test_changes_since_the_previous_run_come_from_the_one_comparison`).
7. A run that stopped as asked says so and how to go on, names no failed step, holds no repository text, and keeps its
   usual lines when it stopped after the last coded step
   (`test_a_stop_is_said_in_the_headline_and_the_stop_lines_and_names_no_failed_step`,
   `test_a_stop_before_a_model_read_names_the_input_file_and_the_option_to_go_on_with`,
   `test_a_stop_after_intake_has_nothing_examined_yet`).
9. The token line is in the brief in a paragraph of its own, for a read that listed no place too
   (`test_tokens_line.py::test_the_brief_has_the_line_in_its_own_paragraph`,
   `test_the_brief_has_the_line_for_a_read_that_listed_no_place`); the fixture line is under the fixture checks when Sweep ran and its
   fixtures were measured, says rows that got no answer, shows a low count and holds nothing, and is not there for a read that was not
   measured, a failed check, no stamp, or a default run
   (`test_the_brief_says_what_sweep_found_in_its_fixtures_under_the_fixture_checks`, `test_a_low_count_shows_and_holds_nothing`,
   `test_rows_that_got_no_answer_are_said`,
   `test_the_line_is_not_there_when_sweep_did_not_run_or_its_fixtures_were_not_measured`,
   `test_a_saved_stamp_reused_still_says_what_it_found`, `test_the_model_name_in_the_line_is_one_line`).

### History

- 2026-10-02: the brief, in `walkdown.py`. 2026-10-21 to 2026-10-27: summary.html's terms; the cost, needs, hosts,
  trigger, tools, and clean lines.
- 2026-10-29: restructure step 7: moved to the report stage and saved as `brief.md`; stamps from the record; the
  details line says "Everything behind each answer"; the changes lines are made from `drift.changes`, once.
- 2026-10-30: O3: the lines for a run that stopped as asked (above), and the headline and the step lists that leave a
  step the stop left out out of the failures.
- 2026-10-30: M9 slice A: a model read that did not work no longer makes the headline say "cannot say" (restructure
  M14 b); the count line and the not-started line.

## coverage

Status: built 2026-11-04 (owner: "We will never get every file type. ... a white list (ones we examine), a yellow list
(the archive), and if not on those they are tagged as red").

What Walkdown examined, file by file, in three tiers, by file type (the extension, lowercased). It is bookkeeping from
what the steps recorded, not a judgment of the files, and it holds no run: a red file is a standing limit, not a gap.

### Inputs

`02.1-inventory`'s `inv.file` rows and its `archive` census flags; `02.2-reader`'s `read.unread` rows (the reader
writes one for every file it does not read); the builder's `cap.ship` groups (which files the AI loads).

### Outputs

- `rows(r)`: per file but symlinks (never followed; "Files worth a look" lists them), its `tier`:
  - `examined` (white): it decodes as text, or the reader ran and did not list it as unread (it drew the text out of a
    PDF, a Word document, or an image by OCR);
  - `archive` (yellow): otherwise, the census flagged it `archive` (looked inside for programs, compiled Python, and
    Office macros; the text inside was not read);
  - `not` (red): anything else, with `why` (the reader's reason, "could not be read", or "not text, and the reader step
    did not run").
  Each row also says whether the AI loads it (`cap.ship` group `entry`, `project`, `on-demand`, or `maybe`) and whether
  it is in a test or fixture folder.
- `by_tier(r)`: per tier, its types, most files first, each with its files, count, and how many the AI loads and how
  many are in test folders.
- `section_html(r, files=False)`: "What Walkdown examined", three rows: white "Examined", yellow "Archives, looked
  inside for programs only", red "No tests are run on these file types" with "Walkdown does not analyze files with these
  extensions. Use with caution." (the owner's wording) and how many of them the AI loads. A tier with no files is left out. `summary.html` shows it between
  the header and "At a glance"; `details.html` (`files=True`) between the header and the bar of questions, naming
  the yellow and red files, the ones the AI loads first, up to 50 a tier, with a count of those in test folders.
- `full_lines(r)`: `full.md` section 1, after "Script languages": the three tiers with their types, then every yellow
  and red file with whether the AI loads it, whether it is in a test folder, and why.
- `brief_line(r)`: the brief's second line, counts only: `Examined: 4; archives looked inside for programs only: 1;
  no tests are run on 5 (4 file types; the AI loads 1 of them).` The first line now says `Files: <n>`, not
  `Files examined: <n>`.

### Must never

- Put a file the checks did not read in the white tier: without the reader, a PDF or a document is not white.
- Name a file or a type in the brief (it holds no text from the repository).
- Say the repository is safe or unsafe: red is what Walkdown cannot see.

### Done when (tests in `tests/test_coverage.py`, and one each in `test_summary_html.py` and `test_details_html.py`)

1. Text and what the reader read are white, archives yellow, the rest red, symlinks left out
   (`test_each_file_is_examined_an_archive_or_not_and_symlinks_are_left_out`).
2. Without the reader a PDF is red and a document yellow (`test_without_the_reader_a_pdf_or_document_was_not_examined`).
3. Types group by extension with what the AI loads and test folders counted
   (`test_types_group_by_extension_with_what_the_ai_loads_and_test_folders_counted`).
4. The pages show the tiers, and details names the files (`test_the_pages_show_three_tiers_and_details_names_the_files`,
   `test_what_walkdown_examined_comes_before_the_glance`, `test_what_walkdown_examined_comes_first_and_names_the_red_files`).
5. `full.md` names every file and the brief gives counts only
   (`test_full_md_names_every_file_and_the_brief_gives_counts_only`).
6. "Unknown file type" is gone from "Files worth a look", and the archive row says what was checked
   (`test_the_unknown_file_type_row_is_gone_and_the_archive_row_says_what_was_checked`).

## details_html

Status: rebuilt 2026-10-27 as report v3 (owner; the `glance` section holds the eight questions).
Before: the long page of report v2 (2026-10-16), renamed from `summary.html` on 2026-10-20, with a
Not concerned box on every row.

The page for someone who wants everything behind the summary: the same eight questions, each
opening with the same chip and answer, then every table, chart, and place, long lists folded. It
also holds the place list every other output reads (`first_items`) and the helpers for marks and
licenses.

### Inputs

`render_page(meta, reports, stamps, notes, runs_ok, changes=None, marks=None) -> str`. `changes`:
`run.changes_for`; `marks`: the run's marks (`marks.for_run`), read only to say how many places
are marked.

### Output: `details.html`

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
   summary's "More", then the detail (the `glance` section).
4. **What changed since run X**, only when an earlier run of the same repository is a different
   version, or the same version and something differs (`run.changes_for`, `drift.since`; review
   C22 b): the drift lines and a link to `changes.md`.
5. **What Walkdown didn't check** (`glance.not_checked(r, notes, qa, stop)`; the steps that did not work and every limit
   are the check of the run's): a step that did not work, the model reads
   when they did not run (the line "The optional model reads (a second opinion from an AI) were not
   run." only when neither AI stage, `03-sweep` or `04-pinpoint`, has a report in the run), or that
   every step ran and passed; then every limit of the run, folded (`render.limits`, which names INCOMPLETE stamps
   and skipped checks). A run that stopped as asked (O3) says 'Every step that ran passed its own checks.', then lines of their own, apart
   from the checks skipped for a missing tool: `render.stopped_steps_line` ('The run stopped after "<plain>", as
   asked. Not run: <plain names>.'), and for a held-back read `render.stop_input_line` ('The run stopped after
   "<plain>", as asked; what "<AI plain>" would send is in data/<file>; nothing was sent.'). The held-back read is
   not listed as "Model reads (optional): not run" and the sentence that the optional model reads were not run is
   left out. A model read in which no passage got an answer is a step that did not work in the first line ('<plain> got no
   answer for any passage', M9). Beside that line, each read's passages that got no answer have a line of their own
   (`<plain>: N of M passages got no answer, after one retry. Reasons: ... The call log is data/<step>.calls.jsonl.`,
   `render.model_read_lines(..., full=True)`), and so does a chosen step the record says was not started
   (`meta["not_started"]`). They are not in the list of what was skipped, which reads "most often because an optional
   tool is not installed", and the fold of every limit leaves them out, since the page says each once. When the only
   step that did not work is a model read, the first line does not add that a step that did not work can miss places
   (`summary_html.only_model_reads`).
6. **Footer**: a link to `review.html` to mark each place, `full.md`, and `render.NOT_WHAT`.

No Not concerned boxes and no marks bar (owner, 2026-10-27): marking is on `review.html` only.

### Helpers other outputs read

- `first_items`, `unique`, `grouped`: the places, read by `review.html`, `summary.html`, `glance`,
  and the brief in `walkdown.py`. A place carries `stage`: the name of the stage whose section lists
  it (`02.1-inventory` to `02.5-capability`, or `03-sweep` for a model's reading), from `stages.json`;
  `is_model_read(item)` asks whether that stage is an AI stage (`stagelist.AI_STAGES`), never a number.
  `02.4-phrases` phrase places are `render.point_hits` (C39). `_item` gives a place `context`, what Walkdown says of the line itself,
  in this order: what a quote's hidden tag characters spell ("The hidden tag characters spell: ...", `render.tag_text`) and what its
  runs of variation selectors spell ("The hidden variation selectors spell: ...", `render.selector_text`, from `library.runs`; P1
  2026-10-29; one sentence pair, `spelled_note(text)`), what a base64 stretch decodes to (C42), and, for a hit in an MCP server's
  description (`tool_text`), `TOOL_TEXT_NOTE`, which says the line is code the AI reads as a description. Each is its own line on
  `review.html` and stands before the place's note on `details.html`, for every kind of place; a phrase place's note (its base
  rate) stays off `details.html`, as before. `unique` keeps each sentence once. Until 2026-11-03 these sentences were the start of
  the note, so the base-rate `lead` ran into them ("How often this pattern turns up elsewhere: Decoded from base64: ..."). `_spelled_places` adds a place of its own, kind `hidden+spelled`,
  titled "Hidden characters that spell out text", under `02.2-reader` after the `hidden+phrase` places, for
  a `read.divergence` with `decoded` in a file the AI reads (`render.audience`: model or subagent): never
  when another place on that line says what it spells already, or when the secret scan flagged the line
  (`secret_lines`: a report never repeats a secret). A line
  that forbids the matched action keeps its place with ", stated as a prohibition"; a forbidden
  rubric action is never one "with no confirmation step" (C25). A read-only line whose owner's tools
  list can write is its own place (C32). A command in `.cursor/environment.json` notes that it runs
  on Cursor's cloud machine (`HOOK_NOTES`, C31).
- `action_group`: runs, out, lasting, or words (C29), for the concern rows.
- `mark_rows`: every row a mark can name (each review card, each outside link, each Worth a look
  file, each place under a trifecta box, each hidden place), read by `review.html`, so a marks file
  saved before report v3 keeps its marks.
- `license_line`, `file_concerns`, `fold_meaning`, `fold_kinds` (typography never counted),
  `_divergences`, `_leg_ev`, `_ev_words`, `_allows`, `link_rows`, `CARRIER_PLAIN`, `carrier_plain`,
  `GROUP_PLAIN`, `READ_BY`, `TRIFECTA_LEDE`, `PLAIN_STAGE`: read by `glance`.
- `_fold_kind(code)`: the kind of a code point a `read.fold` removed. A code point in the
  invisible-character list (`Library/invisible.yaml`) that the list strips (action `strip`) or that
  stands in a run (action `run`) is "invisible characters" before any category rule, so a Hangul
  filler (a letter by category) is not called a look-alike letter and a variation selector is not
  "other symbols". A character the list turns into a space (action `space`: U+2028, U+2029, U+0085)
  keeps its category: U+2028 and U+2029 stay typography ("other symbols"), and U+0085 is a control
  character, so "invisible characters" as before. The category rules decide the rest (a format,
  control, private-use, or unassigned character is still "invisible characters"; a letter is
  "look-alike letters"; spaces, dashes, quotes, and symbols are typography).
- `CARRIER_PLAIN`: the plain words for how `02.2-reader` saw text differ (`carrier`). It names the
  kinds of invisible character: `zero-width` "invisible characters", `bidi` "text-direction
  controls", `soft-hyphen` "soft hyphens", `filler` "blank letters and cells", `tag-chars` "hidden
  tag characters", `variation-selectors` "runs of variation selectors", `nul` "NUL characters".
  `carrier_plain(carrier)` gives the words for one carrier; a carrier joined with `+`
  ("zero-width+bidi") reads as its parts' words: "A and B" for two parts, "A, B, and C" for three or
  more (commas, with "and" before the last), and a carrier with no entry reads as it is written.

### Must never

- Show a score, severity, rank, or verdict.
- Emit unescaped repository text (addresses included).
- Show a secret's value, or open, fetch, or check a link.
- Write `marks.json`.

### Done when (tests in `tests/test_details_html.py`)

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
   (`test_cursor_setup_commands_say_where_they_run`), C32
   (`test_contradicted_read_only_lines_get_their_own_place`), C29 (`test_action_groups`), C42
   (`test_items_say_what_hidden_text_spells`).
5. The license line and the summary's short license (`test_license_line_in_header`,
   `test_license_line_unrecognized_field_none_and_old_run`).
6. Changes only when they apply (`test_changes_only_when_relevant`); What Walkdown didn't check last
   (`test_not_checked_last_with_every_limit`); the model-reads line is there for a default run and
   gone for a run with a `03-sweep` report
   (`test_not_checked_says_the_model_reads_did_not_run_only_when_no_ai_stage_has_a_report`).
7. Each question's detail (`test_question_sections_carry_everything_behind_them`); files worth a
   look and the trifecta credit (`test_files_worth_a_look_and_the_trifecta_credit`).
8. A code point the invisible-character list strips or that stands in a run is "invisible characters" (a
   Hangul filler, a variation selector); a line separator (U+2028, U+2029) keeps its category; the
   category rules still decide the rest
   (`test_the_invisible_list_decides_what_is_an_invisible_character`). Each kind of invisible
   character has plain words, a joined carrier reads as its parts ("A and B", "A, B, and C"), and the
   hidden-text lines use them (`test_carriers_have_plain_words_and_a_joined_carrier_reads_as_its_parts`,
   `test_the_hidden_text_lines_use_the_plain_words_for_a_joined_carrier`).
9. A place's note says what its quote's tag characters spell and what its runs of variation selectors
   spell, tag note first (`test_items_say_what_hidden_text_spells`,
   `test_items_say_what_a_variation_selector_run_spells`).
10. The count of passages that got no answer is one line of its own with its reasons, a read that got none is named as a
    step that did not work, a partial read is not, a step that was not started has its line, and none of it is said
    twice (`test_not_checked_gives_the_count_of_passages_with_no_answer_in_one_line_and_names_a_read_that_got_none`,
    `test_not_checked_says_each_fact_about_a_model_read_once`).

### History

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
- 2026-10-29: restructure step 6 (keep-or-cut, Q8): the places for a label read, a relational read, and
  the questioning line (C28) are cut from `first_items`; no stage has written those findings since
  step 5.
- 2026-10-29: restructure step 6, round 2: "The optional model reads ... were not run." is printed only
  when neither AI stage has a report in the run. It had been tied to the label list, which is always
  empty, so it also appeared on a run where Sweep ran.
- 2026-10-29: restructure step 7: `PLAIN_STAGE` is built from `stages/stages.json` (`stagelist.PLAIN_WITH_LIMITS`); same names, same order.
- 2026-10-29: restructure step 7b: a place's `stage` is the stage's name, where it was the number of its section, 1 to 6;
  "is a model read" asks whether the stage is an AI stage (`is_model_read`). The pages read the same.
- 2026-10-29 (P1): `_fold_kind` reads the invisible-character list before the category rules, and
  `CARRIER_PLAIN` has words for the kinds the list gained (`filler`, `variation-selectors`) and the two
  it lacked (`tag-chars`, `nul`); `carrier_plain` reads a carrier joined with `+` as its parts' words
  (a line with two kinds used to show the raw joined name; "A and B" for two parts, "A, B, and C" for
  more, after verification). A place's note says what a selector run in its quote spells (`_item`).
  The characters the list
  turns into a space (U+2028, U+2029, U+0085) keep their category, so a line's fold kinds are counted
  as before for them.
- 2026-10-30: M9 slice A: "What Walkdown didn't check" gives the count of a model read's passages that got no answer
  in one line, names a read that got none as a step that did not work, and has the line for a step that was not
  started (`render.glance`, `render.limits`, `meta["not_started"]`).
- 2026-11-01: a `secret.found` skip for one file is no place: `first_items` lists no "Looks like a committed secret" for a skip of either
  kind (it listed one with no kinds and no scanner's name). `test_one_file_the_secret_scan_could_not_scan_does_not_unsay_the_rest`.
- 2026-11-01: a hook whose command is masked is named by the first line of its entry (`render.hook_where`), in `first_items` and in
  what installing it allows, since the words no longer tell it from the next hook in its file
  (`test_secret_fields.py`, `test_each_place_is_still_counted_and_named_by_where_it_is`). A hook that is not masked is named as before.

## drift

Added 2026-10-04.

Version drift (threat class 8): what changed between two runs of the same repository.

### Inputs

Two run folders (each with LOG.md), current or old layout (`layout.py`). Reads `02.1-inventory`, `02.3-graph`,
`02.4-phrases`, `02.5-capability`, and the builder step `02.6-builder` (`02.5-capability` from `capability.json` when present, for every
citation; the cost rows `cap.ship` and `cap.context` from the builder step, or, in a run made before
restructure step 4, from `capability.json`, where `02.5-capability` wrote them). The AI steps (`03-sweep`,
`04-pinpoint`) are never compared: model reads drift between runs on their own.

### Outputs

- `compare(old, new)`: files added, removed, changed (by `02.1-inventory`'s per-file `sha256`; by size
  when an older run has no hash, and a same-size file without a hash is listed as unverified,
  never as unchanged); entry points added and removed; hooks added and removed (file, event,
  matcher, command); agent tool grants changed ("inherits all tools" when a definition lists
  none; "(no agent)" when it does not exist in one run); MCP servers added, removed, changed;
  descriptions changed; phrase hits new and gone, keyed by file, check, and the line's text so
  a hit that only moved is neither; network hosts added and removed; trifecta legs that
  switched; install grants added and removed; pairs added.
- `summary_lines(c)`: counts and Walkdown's own words only, no repository text (safe for the
  brief). A count of one reads in the singular ("1 file added", "1 new phrase hit"); `COUNTS` holds
  both forms of each (restructure step 8b). New phrase hits say how many are in text a model reads:
  "2 new phrase hits, 1 of the new phrase hits in text a model reads"; one new hit says it beside its
  count, "1 new phrase hit (in text a model reads)" or "(not in text a model reads)".
- `render(...)` / `write_report(old, new)`: `changes.md` beside the new run's reports, most
  consequential first (legs, grants, hooks, tool grants, MCP servers, descriptions, hosts,
  entry points, pairs, phrase hits in text a model reads, then counts elsewhere, then files).
- `changes(run)` (restructure step 7, notes F2): the one comparison of a run with the previous run of the same
  repository, which `changes.md`, the brief, and the summary and details pages all read. The previous run is
  `record.previous_run`: the newest other run folder of the same repository that finished before this run
  started, by the times in its record; a run without a record (v0.3.1 and before) by the date in its folder name,
  then its LOG.md's modification time against a run of the same date, with the folder name (`-2` before `-10`)
  as the tie-break (`stages/_shared/specs/shared.SPEC.md`, section `record`). Before step 7 the brief picked by LOG.md
  time and the pages by name, so re-rendering an older run could compare it with a newer one; the rule is
  by time now and never picks the run itself or a later one. It returns `since` (the earlier run's folder
  name), `same`, `differs`, `lines`, `on_disk`, `cost_line`, `header` (for the brief), and `report` (the path
  of `changes.md`, written once), or None on a first run or when the comparison fails (a note on stderr
  says why: drift is extra and never fails a report). `STAGES` is the coded steps from `stages.json`.
- `main([old, new])`: writes the report and prints the summary; 2 for bad arguments.

The report stage runs `changes` after every audit; the brief prints one line when the version is the same, and
the summary and the report path otherwise. `walkdown.py diff <old> <new>` runs this file on demand (a route to
the report stage's comparison).

### Secrets (added 2026-11-01)

`load` masks each run it reads (`secretmask.mask_reports`), so a run stopped before the runner masked it, or saved before the runner
did, shows no flagged line in `changes.md`. A masked value has no words to compare: two runs that both mask a description or a hook read as
the same, and an edit behind the mask shows as the file changed. One run's scan can flag what the other's missed (a file it could not
read then), so the side that is not masked can hold the key: `_hide` shows the file and the mask for each row of `hooks_added`,
`hooks_removed`, `grants_changed`, `mcp_added`, `mcp_removed`, `mcp_changed`, and `desc_changed` in a file where that check's row is
masked in either run.

Done when: `test_two_runs_are_each_masked_and_a_description_with_the_same_flagged_line_is_no_change`,
`test_a_word_is_not_shown_for_a_file_masked_in_one_run_only`.

### Must never

- Put repository text in `summary_lines`.
- Compare model reads, judge a change, or rank changes by importance beyond a fixed reading order.
- Write anywhere but `changes.md` in the newer run.

### Done when (each backed by a test in `tests/test_drift.py`)

1. Each kind of change is found; a moved line is not a new hit.
2. A same-size file without a hash in the older run is unverified, not unchanged.
3. The summary carries no repository text; identical runs say so.
4. The report is written beside the newer run's reports, and the previous run is found by time, once
   (`test_report_and_the_one_comparison_with_the_previous_run`; two runs on one day whatever their hashes:
   `test_the_previous_run_of_two_runs_on_one_day_is_the_earlier_one_whatever_their_hashes`; a comparison that fails
   is a note, not an error: `test_a_comparison_that_fails_is_a_note_and_not_an_error`; the rule itself:
   `stages/_shared/tests/test_record.py`).

### Where a hit came from (added 2026-10-19, review C22 b)

`load` also reads the `terms` block of the `02.4-phrases` report (`stages/02-coded/02.4-phrases/termset.py`).
`compare` adds `terms` (`termdiff.diff` of the two blocks, `stages/_shared/termdiff.py` since restructure step 7) and, aligned with `hits_added` and
`hits_removed`, `hits_added_cause` and `hits_removed_cause`, one per hit:

- `repo`: the hit's file was added, removed, or edited.
- `unverified`: the older run has no content hash for the file.
- `walkdown`: the file is the same and the older run has no `terms` block, so a term cannot be
  told from the matching code.
- `terms`: the file is the same and one of the hit's patterns was added or changed (a new hit),
  or retired or changed (a gone hit).
- `code`: the file and the hit's terms are the same and `02.4-phrases`'s code changed.
- `other`: the file, the terms, and the code are all the same (another stage's output moved it).

`summary_lines` adds "Walkdown changed since the older run: ..." (search terms added, changed,
retired; word lists; matching code) and, when any hit came from Walkdown, one line each for new
and gone hits by cause. Counts only. `changes.md` lists the changed terms by id and marks each
new hit in text a model reads with its cause when that is not the repository.

`same_repo(old, new)`: both runs have the same `02.1-inventory` pin. `differs(c)`: anything recorded
differs. `since(old, new)`: what `walkdown.py` and the summary page say about the previous run:
with the same version and no difference, nothing is written; otherwise `changes.md` is written,
and with the same version it opens by saying every difference comes from Walkdown.

Done when (tests in `tests/test_drift.py`):

5. Each cause is assigned: an edited file, an added, changed, or retired row, a matching-code
   change, a missing term version, a file without a hash; the summary counts them.
6. Repository changes alone add no cause or Walkdown line.
7. `since` with the same version writes nothing when nothing differs, and writes a report that
   names Walkdown when something does.

### Line endings and files on disk (added 2026-10-20)

A file present in both runs whose `sha256` differs but whose text is the same apart from line
endings (`same_text`: both runs' `sha256_lf` equal; or, when one run predates those hashes, its
`sha256` equal to the other run's `sha256_lf` or `sha256_crlf`) goes in `files_eol`, never in
`files_changed`. It is not an edit: a hit in it is traced as in an unchanged file, it alone makes
no difference (`differs`), and `changes.md` lists it under its own heading. Found 2026-10-20 on
one repository at one commit: 7 files counted as changed whose line endings alone had gone from CRLF to
LF.

`on_disk(c)`: files added, removed, or edited. With the same version and none on disk, the brief,
`changes.md`, and the summary say every difference comes from Walkdown (`same_words`); with some
on disk (a local folder with uncommitted edits), they say the same commit, with N files that
differ on disk, and that differences in other files come from Walkdown. `since` returns
`on_disk` and that `header`.

Done when (tests in `tests/test_drift.py`): a CRLF-to-LF file is line endings only and its hit is
not put down to the repository; a run without the new hashes is matched in either direction; the
same version with only line-ending changes writes nothing, and with a file edited on disk says so.

### Cost since the earlier run (added 2026-10-27, slice 6)

`compare` adds `cost`: slice 1's numbers in each run (`cost_of`: every session, every session in
the folder, the entry with the most at its fullest and which, and the files and tokens not used at
run time), or null for a run made before they were counted. `cost_changed` is a difference
(`differs`). `cost_line`: "cost: every session 1,200 -> 1,320 tokens (+120); ..." with only the
numbers that changed and never a file name (the brief shows it), or "costs not comparable: the
earlier run was made before they were counted"; `summary_lines` carries it, `since` returns it as
`cost_line`, and `changes.md` gains a table "What it costs (estimated tokens)" with the largest
entry's file when it changed.

Done when: `test_cost_since_the_earlier_run`.

### Runs made before the stage rename (added 2026-10-28, restructure step 1)

Stage names changed in step 1 (`01-inventory` became `02.1-inventory`, and so on), and a run's
stage files (`data/<stage>.json`) carry them. A run made before then keeps the old names, which
`load` does not read; compared as it is, every file would be called added or removed.
`predates_rename(run)`: the run has `01-inventory.json` (in `data/`, or at the top of the folder for a run made
before 2026-10-02: such a run is recognized here and never read) and no `data/02.1-inventory.json`
(a failed run with no stage output is not this case). `not_comparable(old, new)`: when either
run predates the rename, "not comparable: the earlier run was made before the stages were
renamed, so its stage files do not match" (or "the newer run"), else None. Then nothing is
compared:

- `since` returns `{"same": False, "differs": True, "lines": [that line], "report": changes.md,
  "not_comparable": True, ...}`, so the brief, the details page, and `changes.md` say it, and
  `changes.md` holds that sentence, "Nothing was compared", and a request to audit the repository
  again with Walkdown and the number in the `VERSION` file (`walkdown_version`), which the pages
  show, to start a series that can be compared.
- `write_report` and `walkdown.py diff` do the same; `summary_lines` returns the line.
- Runs filed under fresh names for a comparison (`cmp-*`) never meet this case.

### Runs made before this version (added 2026-10-29, restructure step 7b)

One rule with the re-render (`stages/_shared/specs/shared.SPEC.md`, section `record`): a run is compared only when its record has the current format.
`not_comparable(old, new)` also answers, after the rename check, for a run with `record.made_before`: no record,
or a record of an older format, whose data inside the run has another shape (a run made between step 7 and step 7b
names the stage of an evidence entry by number). The line is "not comparable: the earlier run was made by an earlier
version of Walkdown, and its data is in another shape" (or "the newer run"): the files have the same names, so the
rename case's "stage files do not match" is not said here, and "this version" is not a thing a reader can see (restructure
step 8b). A run from before the rename keeps its own sentence, whatever its record says. Nothing
is compared field by field: `since`, `write_report`, `walkdown.py diff`, and so `changes.md`, the brief's change
lines, and the details page all say it. Marks carried from the run do not depend on this
(the `marks` section).

### Runs that stopped as asked (added 2026-10-30, O3)

A run stopped with `--until` before its last coded step (`record.stopped_early`: its record has `until`, and the step is
before `02.6-builder`) is not compared, since the steps the comparison reads did not all run. `not_comparable(old, new)`
answers, after the two checks above, with 'not comparable: the newer run stopped after "<plain>", as asked' (or "the
earlier run"), and `changes.md` says so and that a run that goes on to its last coded step can be compared. A run
stopped after `02.6-builder` is compared as usual, and so is one that went through. `record.previous_run` skips a run
stopped early, so the next full run is compared with the last run that went through its coded steps.

Done when: `test_a_run_that_stopped_before_its_coded_steps_is_not_compared_and_one_stopped_after_them_is`,
`test_the_next_full_run_is_compared_with_the_last_run_that_went_through`.

Done when (7b): `test_a_run_whose_record_has_an_older_format_is_not_compared`,
`test_a_run_with_no_record_and_the_newer_run_with_an_older_record_are_not_compared_either`,
`test_the_previous_run_with_an_older_record_is_not_compared_in_the_one_comparison`,
`test_the_diff_command_says_not_comparable_for_an_older_record`.

Done when: `test_a_run_from_before_the_rename_is_recognised`,
`test_a_run_from_before_the_rename_is_not_compared`,
`test_the_newer_run_from_before_the_rename_is_not_compared_either`,
`test_the_diff_command_says_not_comparable`,
`test_the_not_comparable_line_reaches_the_details_page`,
`test_two_runs_from_after_the_rename_still_compare`.
- 2026-10-29: restructure step 7b: a run whose record is missing or of an older format is not comparable (above).
- 2026-10-30: O3: a run that stopped before its last coded step is not comparable (above).
- 2026-11-01: each run is masked when loaded, and a row of a file masked in one run shows no words from the other (above, Secrets).

## glance

Status: built 2026-10-27 (report v3, "glance and know"; the design and the owner's decisions are
in `pre-planning/SPEC-REPORT-V3-2026-10-27.md`).

The eight questions both pages answer, as data, and the page shell both pages use. It reads the
same findings as every other output and detects nothing.

### The reader

Someone with no computer skills. Plain words, file names only in small grey "where" notes, and
tokens named in one place only (question 2). Every sentence is a fixed template filled from
findings, so it says the same thing on any repository.

### Inputs

`questions(meta, reports, stamps, runs_ok, marks=None) -> list[Q]`. `meta["context"]` is the
expected context (default `render.DEFAULT_CONTEXT`, 32,000); `meta["hosts"]` the tools named with
`--hosts`; `marks` the run's marks, own or carried (the `marks` section).

`Q`: `id`, `question`, `chip`, `tone` (`look`, `notes`, `fact`, `none`, `unmeasured`), `answer`
(escaped HTML), `bullets` (HTML), `more` (on both pages), `detail` (on `details.html` only).

### Chips

Never a verdict. **N to look at** (amber: a host rule, a security kind, or the words against the
grants found something), **N notes** (amber: published guidance and harmless facts), a **fact**
(blue: a measure), **Nothing to look at** (green: the checks ran and found nothing), **Not
measured** (grey: the run was made before the check, or a step did not run; never "nothing").

### The eight questions, in order

The checks the questions read (`trig.*`, `need.*`, `port.*`, `host.*`, `ask.*`, `fit.*`, `clean.*`,
`cap.ship`, `cap.context`) are looked up in the `02.6-builder` report since restructure step 4 (they
were `02.4-phrases`'s and `02.5-capability`'s); the questions, their wording, and their order did not change.


1. **Will its skills switch on when they should?** (`switch`; slice 4). Not measured without
   `trig.entry`. To look at: frontmatter not read, agents not loaded, name and description rules,
   unknown keys with a near match, values, tool names, overlaps, cut descriptions; notes: guidance,
   unknown keys with no near match, the listing over its room. Answers: "<N> of the <skills and
   helpers> won't switch on as written: ..."; "Yes. <N> of the ... switch on by themselves; <M>
   only when you ask for them by name."; "Yes. All <...> are set up to switch on by themselves.";
   "Yes. Its one skill is set up to switch on by itself." Detail: every entry in a table, every
   place by kind.
2. **How much of the AI's memory does it use?** (`memory`; slice 1; the one place for tokens). Not
   measured without the builder step's cost (`02.6-builder`, `cap.context`). Chip (fact): "under 1%", "up to N%", or "more than fits": the
   largest entry at its fullest (or what it always loads) against the expected context. Answer:
   "<Very little | A small part | About N%> on Claude. On <a local AI | your AI>, its biggest <kind>
   takes <about a fifth | ...> of the memory."; at Claude's context, "On Claude, ...". More: what a
   token is; the table (rows: Always there once installed; Its biggest <kind> (<name>), with
   everything it reads; Extra, only when someone works inside <folder>; Unused files, if the AI were
   told to open them all), columns "Local AI (32k tokens)" at the default, "Your AI (<N>k tokens)"
   otherwise, then "Claude (200k tokens)" unless the context is Claude's; the room for the skill
   list; "Since run <name>: <cost line>." when the earlier run is comparable (`since_line`).
   Detail: how big each skill and helper gets, as bars.
3. **What comes in the package?** (`package`; slice 1). Not measured without file groups. Chip
   (fact): "<N> extra files" or "Nothing extra". Answer: "<W> of its <F> files do the work. The other
   <N> come along without being used." More: one stacked bar of the four groups (do the work, notes
   for people, tests and build tools, nothing refers to them), the legend, and the saving (a fact,
   never an order). Detail: every file by group; **Files worth a look** (`details_html.file_concerns`:
   unknown or mismatched types, programs in compiled form, compiled Python, archives or documents holding a program or macros
   (these three added 2026-11-03), archives, symlinks, files the AI reads where blank lines or spaces push text out of view
   (added 2026-11-03), files longer than a reviewer's viewer shows).
4. **Will it work on someone else's computer?** (`elsewhere`; slice 2). Not measured unless the run
   found programs, packages, or places here, or holds slice 3's `host.coverage` (there is no marker
   finding; `render.needs_of`). Chip: one to look at per kind (programs never declared, or packages
   when every program is; each `port.*` kind; case-only references). Answer: "<Two> things could
   trip it up on another computer." or "Yes. Everything it uses is something it says to install,
   and nothing ties it to one computer." Bullets: one template per kind (`PORT_PLAIN`, from `Library/tools.yaml`), with "(N
   of them in <folder>/)" when one top folder holds half or more. Detail: the largest kind by file,
   the programs table, every place by kind.
5. **Will it work with AI tools other than Claude?** (`hosts`; slice 3). Not measured without host
   findings. Chip (fact): "Claude Code only" when no other tool has files; "<N> of 7 tools"; with
   `--hosts`, "<N> missing for your tools" or "Nothing missing for your tools". Answer: "<N> of the
   7 AI tools Walkdown knows find its files where they sit." Bullets: the to-do list first with
   `--hosts`; copies that differ; one line per kind of one-tool feature (`FEATURE_PLAIN`, from `Library/hosts.yaml`); a tile
   per tool. Never says which tool a repository should support.
6. **Does it ask only for the tools it needs?** (`tools`; slice 5). Not measured without
   `fit.checked`. To look at: unused grants, tasks with no tool, read-only claims contradicted,
   loops with no stated limit, hooks on every prompt or tool call. Answer with none: "Yes. Every
   tool it is allowed to use is one it actually uses, and nothing it asks for is missing." Bullets:
   one per kind (`FIT_PLAIN`, templates from `Library/fit.yaml`). Detail: every place by kind, the helpers and their tools.
7. **Is it finished and up to date?** (`clean`; slice 6). Not measured without `clean.checked`.
   Notes: unfinished text, dated claims, older tool names; pinned model IDs are a fact inside.
   Answers: "Nearly. <counts>." or "Yes. No unfinished notes, no dates that will go stale, and no
   older tool names." The summary shows no line of the repository's; details quotes each place.
8. **Anything to be careful about?** (`careful`). Rows from `summary_html.rows` (the fixed concern
   kinds and order). Chip: "<N> to look at"; "Nothing found" (never "safe"); "Not checked" when a
   step did not run and nothing was found. Answers: one kind, "<N> place(s) has/have <plain row
   name>." ("Both are the same text." when the hidden places share their text); several, "Walkdown
   found <N> places worth a look, of <K> kinds: <short names>."; none, "Walkdown found none of the
   security concerns it looks for." with " Not every step worked, so it may have missed some." when
   a step failed its fixture check or did not run; a step that did not run and nothing found, "This
   run did not complete: ..., so Walkdown cannot say whether it has any of these." (a coded step: a
   model read that did not work adds " The coded checks are complete; the model read did not work."
   instead, M9; chip "Nothing found"). A run that stopped as
   asked before its last coded step (`meta["stop"]`, O3) says 'This run stopped after the step "<plain>", as
   asked, so Walkdown cannot say whether it has any of these.' when nothing was found, chip "Not checked", and adds
   ' The run stopped after the step "<plain>", as asked, so it may have missed some.' to an answer that found
   places; a step the stop left out is not named as one that did not run. Bullets: per row,
   its name, count, and first place; for hidden text, what it says, up to 80 characters with comment
   marks taken out (the one repository text on the summary); the wording-only count; "<M> of <N>
   places marked so far. Go through each place and mark it." (`marked_line`: the rule-found review
   cards, any mark, own or carried). More: What it can do (the three boxes ticked or crossed; left
   out when `02.5-capability` did not run), what all three together risk, and what installing it allows.
   Detail: the credit (the lethal trifecta, Simon Willison's name) and why it can do these; **Every
   place, by kind** (a fold per row, each place linked to its review card, quoted, with Walkdown's
   note for any kind but a phrase match, and a model read that questions it); hidden text (by how
   it hides, by file, every place; lines read differently once invisible characters or look-alike
   letters are swapped, typography left out; text in another alphabet or language; "Nothing hidden
   from people." only when there is none of these); wording that shapes how the AI decides, by
   group; worth reading first; web addresses by site (gathered, never opened); passwords and keys
   (never the value; test data set aside; "Not checked" without a scanner).

**Counting.** A place counts once, as `review.html` counts it: findings on one line are one place
(`summary_html.rows` ids, `total`, `wording_count`). A place may fall in two rows; the answer's
total counts it once.

### The page shell

`CSS` (theme tokens for light and dark, the validated palette, phone width with no page-wide
scroll), `SCRIPT` (tooltips on `data-tip`, by mouse and keyboard), `page`, `card` (the head always
shown; "More ›" only when there is more), `section`, `meta_line` ("Checked <day> · version <hash7>
(or folder) · <N> files · <license>"), `short_license` (the license's name only, never a file's
text; `details.html` adds the full line), `what_it_is` (nothing when `02.1-inventory` did not run),
`since_line`, `changes_section`, `not_checked` (steps that did not work, model reads not run,
every limit folded).

### Must never

- Say "safe", "unsafe", or "do not use", or give a score, grade, or rank.
- Name tokens on the summary outside question 2.
- Quote the repository on the summary, but for hidden text that reads like an instruction (80
  characters); never a license file's text there.
- Say "nothing" for a check that did not run.
- Show a secret's value, or open, fetch, or check a link.
- Emit unescaped repository text.

### Done when

Tests in `tests/test_summary_html.py` (the cards), `tests/test_details_html.py` (the sections),
`tests/test_review_html.py`, `tests/test_run.py`, and `tests/test_marks.py`:

1. Eight questions in order, title, footer, theme tokens (`test_eight_questions_in_order_title_and_footer`,
   `test_order_title_toc_and_theme_tokens`).
2. Each question's chip, answer, and bullets on fixture findings (`test_switch_question_comes_first`,
   `test_memory_question_one_table_and_the_since_line`, `test_package_question`,
   `test_elsewhere_question`, `test_hosts_question`, `test_tools_question`, `test_clean_question`,
   `test_careful_card_answer_bullets_and_what_it_can_do`, `test_one_kind_answer_names_it`), and
   everything behind them on details (`test_question_sections_carry_everything_behind_them`).
3. Not measured, never "nothing", for a check the run did not make (`test_unmeasured_questions_say_so`,
   `test_elsewhere_question`); a step that did not run or failed never reads as clean
   (`test_a_failed_check_never_reads_as_clean`, `test_a_run_missing_a_step_never_reads_as_clean`).
4. Tokens in question 2 only (`test_tokens_are_named_in_one_place`); the summary quotes only hidden
   text (`test_summary_quotes_only_hidden_text`); the license by name only
   (`test_license_line_in_header`, `test_license_line_unrecognized_field_none_and_old_run`).
5. A place counts once (`test_a_place_counts_once_as_review_html_counts_it`,
   `test_one_card_for_one_place_named_by_several_findings`); marks counted
   (`test_marks_are_counted_and_skip_the_example`, `test_a_carried_mark_keeps_from_and_the_pages_show_it`).
6. Every place by kind, linked and quoted; hidden text, folded lines, other languages, secrets,
   links, the trifecta credit, files worth a look (the details tests of those names).
7. Checked by eye on an audited plugin's run (2026-10-27) in a browser, at desktop and phone width,
   in the light theme (the dark theme's tokens are tested, not seen).

### History

- 2026-10-27: built (owner: "Let build the back end for the new reports"), from the two pages the
  owner approved on an audited plugin's run. Owner decisions: the old pages replaced outright; marking on
  `review.html` only; "Yes." answers kept; the summary quotes only hidden instructions. The recount
  on every audited run the same day: a place counts once, as on `review.html`; question 4 says Not
  measured on a run made before slice 2; "under 1%" as a chip; one entry in the singular; the
  license by name only on the summary; Files worth a look, the trifecta credit, the folded-line
  count, and other alphabets kept from the page before.
- 2026-10-29: restructure step 3b: the sentences for questions 4, 5, and 6 are Library data, not
  written in `glance.py`: `PORT_PLAIN` (`tools.yaml`, `port_kinds`), `FEATURE_PLAIN` (`hosts.yaml`,
  `feature_kinds`), and `FIT_PLAIN` (`fit.yaml`, `fit_kinds`). `FIT_PLAIN` was six functions and is
  six templates now, filled by `_fill` like `PORT_PLAIN` (`_fill` gained `{has}`, `{it_gets}`, and
  `{itself}`); every sentence is the same for any count (`tests/test_library_kinds.py`).
- 2026-10-30: O3: question 8 and "What Walkdown didn't check" say a run stopped as asked, apart from a step that
  failed (`meta["stop"]`). A card of questions 1 to 7 that no step measured says `Not measured: the run stopped after
  the step "<plain>", as asked.` in place of "this run was made before this check, or a step did not run" when the
  stop left a coded step out (`questions`).
- 2026-11-01: "Passwords and keys" tells a skip for one file from no scanner. `Not checked: no secret scanner was available for this
  run.` is for the skip with `file` null. A skip with a file leaves what the scan found in place and adds `The secret scan could not
  scan N file(s), so it may hold one:` (`they` for more than one) with the places. A skip for one file had hidden every line found
  and said no scanner was available. `test_one_file_the_secret_scan_could_not_scan_does_not_unsay_the_rest`,
  `test_a_zero_with_a_file_the_secret_scan_could_not_scan_says_so`.
- 2026-11-01: "Passwords and keys" names the lock files the scan left out (`secret_left_out` on `02.4-phrases`'s report): `The secret scan left
  out N lock file(s), since the hashes in a lock file look like keys, so it may hold one:` (`they` for more than one) with the places. The
  owner read the words and kept them. Nothing with no such file, with no scanner, or for a run saved before the key.
  `test_a_lock_file_the_scan_left_out_is_named_beside_what_it_found`, `test_no_lock_file_left_out_says_nothing_and_neither_does_a_run_with_no_scanner`.

## marks

Status: built 2026-10-20 (owner decision the same day). Since report v3 (owner, 2026-10-27),
marks are made on `review.html` only.

The reader's marks: one model, one file, carried to later runs of the same repository.

### The model

Three marks: **Concerned** (look into it, or change it), **Not concerned** (read it; fine for what
the repository is for), **Not sure**. "Ignore" is Not concerned (owner, 2026-10-20). A mark
belongs to the reader: Walkdown never sets one, and a mark changes no finding, no count in
`full.md`, and nothing in `data/`.

Marks are made on `review.html` (any of the three). `summary.html` and `details.html` say how
many places are marked ("<M> of <N> places marked so far") and make no marks. A marks file saved
from the `details.html` boxes before report v3 still loads: `review.html` keeps its link, file,
evidence, and hidden marks as they are.

### The file: `marks.json`

Saved by the reader in the run folder, next to the pages (a download from either page). Walkdown
never writes it.

`{walkdown_marks: 2, repo, run, pinned, saved, marks: [{key, id, kind, where, headline, mark,
note, from}]}`

- `key`: the row's stable key (below). `id`: the place id on `review.html` (a hash of section,
  headline, location, and quote), for places only.
- `kind`: `place`, `link`, `file`, `evidence`, `hidden`. `where`: the location as shown.
  `headline`.
- `mark`: `concerned`, `not-concerned`, `not-sure`; `note`: the reader's words, optional.
- `from`: the run the mark was made in. It is kept when the mark carries over and when the
  reader only adds a note; changing the mark makes it this run's.

A `walkdown_review: 1` file (made before this spec) still loads: its marks match by `id`.

### The code: `marks.py`

- `place_key(item)`, `link_key(url, file=None, line=None)`, `file_key(reason, path)`, `evidence_key(box, file, text, line=None)`,
  `hidden_key(file, carrier, text)`: the keys below, each a hash of its row kind and parts with
  white space collapsed. `details_html._hidden_key` gives the line in place of the text for a masked hidden place: a hash of the
  words would be one of the secret, and two masked places in a file have the same text. For the same reason a key never hashes the
  mask (`secretmask.SECRET_MASK`): a place whose quote is the mask is keyed by where it is (`file:line`), as a masked hook is, an
  address that is the mask by its file and line, and a trifecta place whose cited line is masked by its line number. A row with its
  words keeps the key it had.
- `load(path)`: `(data, None)`; `(None, reason)` for a file that is not JSON or has no list of
  marks; `(None, None)` when there is none.
- `for_run(run_dir)`: `{data, error, carried}`: the run's own file, or the carried one with the
  name of the run it came from.
- `match(data, rows)`: rows are (row id, every key the row answers to); a mark matches by key,
  else by id; returns ({row id: the mark's record}, how many match no row). The rows of a run
  are `details_html.mark_rows`; both pages match against them, and each page's download holds
  every mark that matched, so saving from either page keeps the other's marks.

On `review.html` a card answers to the key of every finding on it, so a carried mark finds its
card when the findings on a line change but one of them is still there.

### Stable keys

A key names what was flagged, never the line number alone, so a mark follows its line when lines
move and drops away when the line itself changes:

| Row | Key |
|---|---|
| A place | the name of its stage, headline, file, and the flagged text with white space collapsed (the quote; for a place with no quote, the location) |
| A repeated sentence | the name of its stage, headline, and the sentence |
| An outside link | the whole address |
| A Worth a look file | the reason (`ext-magic-mismatch`, `archive`, `symlink`, `reader-window`, and since 2026-11-03 `executable`, `bytecode`, `archive-executable`, `padding`; `unknown-type` until 2026-11-04, when the red tier of `coverage` took its files) and the file path |
| A trifecta place | the box, the file, and the text of the cited line (from `02.4-phrases`'s quote at that line, else the line number) |
| A hidden place | the file, how it hides (`carrier`), and the hidden text (else the line number) |

### Marks saved before step 7b

Until restructure step 7b (2026-10-29) a place's key hashed the number of its report section, 1 to 6,
where it now hashes the name of its stage. A `marks.json` the reader saved before then holds the old keys.
Walkdown does not rewrite it. Instead each place also answers to its old key: `BEFORE_7B_NUMBER` is a fixed
table from each stage name to the number its places carried, kept as history and never changed;
`old_place_key(item)` builds the key the old way (None for a stage that is not in the table); the review
cards list the old key beside the current one (`keys`, `data-keys`), so `match` and the page's own
loader accept a mark under either. The rows of the other kinds (links, files, evidence, hidden places)
never hashed a stage number, and carry over as they did. `walkdown_marks` stays 2: the file's shape is
unchanged, and a file saved by the new page holds the new keys.

### Place ids

A place's `id` (on `review.html`, and in a saved `marks.json`) is a hash of the number its section carried before
step 7b, its headline, location, and quote (`marks.old_stage_part`), and it is deliberately unchanged by the rename
of the stages. The id is not a name for a stage: it is a handle that a reader's saved file holds, that the page's own
script matches by when a key is missing, and that the first marks file Walkdown loaded (`walkdown_review: 1`) held
alone. Hashing the stage's name instead would change every id on the page (and every link to a card), and a saved
file would lose its ids. So the ids keep the history table's number and the keys (which are names) are converted.
A stage added after step 7b is not in the table and hashes its own name.

### Carry-over

When `run.py` writes a run's pages (a new run or `--rerender`):

1. The run's own `marks.json`, when there is one, is the run's marks.
2. Otherwise, the newest earlier run of the same repository (a sibling run folder that finished before this one
   started: `record.earlier_runs`, the one rule the comparison with the previous run uses too; by time, not by
   folder name, since step 7 round 2, which also fixes the flaw main had: two runs on one day were ordered by
   commit hash) with a `marks.json` gives **carried** marks:
   each matched to this run's rows by key. Marks whose key matches no row are dropped and
   counted ("<n> earlier marks match nothing in this run").
3. A carried mark shows as the reader's mark with "Your mark from run <name>.", and can be
   changed. Saving from the page writes it into this run's `marks.json` (`from` as above).
   `review.html` says how many marks were carried from which run, and how many match nothing.

All three marks carry over. A Concerned mark stays until the reader changes it.

Marks carry from an earlier run **whatever its format**, including a run that is not re-rendered or compared
because its record is of an older format (`record.made_before`, step 7b): the keys handle the older shape
(`BEFORE_7B_NUMBER`, above), and that run is still ordered by the times in its record
(`test_marks_carry_from_a_run_with_an_older_record_though_it_is_not_compared`).

### Must never

- Write `marks.json`, or change a finding or count because of a mark.
- Match a mark by line number alone.
- Carry marks between different repositories (different run folder parents).

### Done when (tests in `tests/test_marks.py`)

1. A place's key is the same when its line number changes and different when its text changes
   (`test_place_key_follows_the_line_not_its_number`).
2. Each row kind gets its key as in the table (`test_each_row_kind_gets_its_key`).
3. A new run with no `marks.json` takes the newest earlier run's marks, matched by key; unmatched
   marks are counted; a run with its own `marks.json` ignores earlier ones; other repositories
   and later runs are never read (`test_carry_over_from_the_newest_earlier_run`,
   `test_carry_over_takes_the_run_that_finished_last_and_not_the_name_that_sorts_last`).
4. A carried mark keeps `from`; `review.html` and `summary.html` show it
   (`test_a_carried_mark_keeps_from_and_the_pages_show_it`). The page script, driven in a browser
   (2026-10-20): carried marks labeled with their run, a changed mark becomes this run's, a note
   keeps the run, the download is `walkdown_marks: 2`.
5. A `walkdown_review: 1` file loads by id (`test_a_walkdown_review_1_file_loads_by_id`).
6. A marks file saved before step 7b carries over: its places are found by the old keys, with ids that match
   nothing, the file is not changed, and `data-keys` holds the old key
   (`test_a_marks_file_saved_before_the_change_carries_over_by_its_old_keys`,
   `test_a_run_made_before_the_change_hands_its_marks_to_the_next_run`); the table is the numbering step 7
   used (`test_the_history_table_is_the_numbering_step_7_used_and_covers_every_stage_a_place_carries`);
   a place's key hashes the stage name and the old key is pinned
   (`test_place_key_hashes_the_stage_name_and_the_old_key_is_the_one_step_7_built`); a place keeps its id
   (`test_a_place_keeps_the_id_a_saved_file_holds`).
7. End to end, two runs with the line moved: the mark carries; nothing in `data/`, `full.md`, or
   `changes.md` differs with and without marks; Walkdown writes no `marks.json`
   (`test_marks_carry_to_a_later_run_and_change_nothing_else`).
8. Two masked places with one headline in a file each keep their own mark through `match`, and a place with its words keeps its key
   (`test_two_masked_places_in_a_file_each_keep_their_own_mark`); a masked address or trifecta line is keyed by where it stands
   (`test_a_masked_address_or_trifecta_line_is_keyed_by_where_it_stands`).

### History

- 2026-10-12: `marks.json` from `review.html` (C21): one run, no carry-over.
- 2026-10-20: owner: one model across pages, Not concerned replaces ignore, marks carry over.
  Built the same day: `review.html` and `summary.html` (`walkdown_marks: 2`), then the Not
  concerned boxes on `details.html` with the `link`, `file`, `evidence`, and `hidden` kinds.
- 2026-10-27 (owner, report v3): marking on `review.html` only; the Not concerned boxes on
  `details.html` are gone, and both other pages count the marked places.
- 2026-10-29: restructure step 7b: a place's key hashes the name of its stage, not its section number; a
  marks file saved before carries over through `BEFORE_7B_NUMBER` and `old_place_key` (nothing is
  written to the reader's file; `walkdown_marks` stays 2).
- 2026-11-01: a masked hidden place's key comes from its line (`test_the_mark_key_of_a_masked_hidden_place_does_not_come_from_its_text`).
  A mark saved on such a place before this has no row to carry over to.
- 2026-11-01: a masked hook's key comes from its place (`file:line`): two masked hooks in a file have the same text, and a hash of the
  words would be one of the secret (`test_a_masked_hook_has_a_key_of_its_own`). A mark saved on such a hook before this has no row to
  carry over to.
- 2026-11-03: a key never hashes the mask. Every masked quote has the same words, so two masked places with one headline in a file had
  one key: a saved file held both marks under it, and `match` and the page's loader gave both to the first place, so one was lost. A
  masked place is keyed by `file:line`, a masked address by its file and line, and a masked trifecta line by its number. A mark saved
  on such a place before this has no row to carry over to; it was not certain to reach its own place before either.

## qaview

M9 slice B. The report stage's view of the check of the run's output, `data/05-qa.json` (`stages/05-qa/specs/qa.SPEC.md`).
Section 7, `data/limits.md`, and the lists of steps that did not work are drawn from it: the check decides what is a gap and
what is a limit and in what order, and the report words them. This module only reads the file and answers what the pages ask
of it.

### Outputs

- `Qa.read(data_dir)`: the findings (`qa.gap`, `qa.limit`) of `data/05-qa.json`, in the order the check made them;
  `NoCheck` when the file is missing or does not read, or reads and holds none of the limits that stand for every run (the
  check always ends in them, so a file without any is empty and not its output: `05-qa.json is empty`). `Qa(findings)`
  builds one from findings (the tests do).
- `qa.items`, `qa.gaps`, `qa.limits`; `qa.of(*kinds)`: the findings of those kinds; `qa.steps_missing()`: the steps with no
  output; `qa.reads_with_no_answer()`: the model reads that got no answer for any passage.
- `of(meta)`: `meta["qa"]`, or an empty one for a `meta` that has none (a page drawn by a test).

### Must never

- Gather, judge, or reorder: the check's order is section 7's order.

### Done when (each backed by a test in `tests/test_qaview.py`)

1. The file is read into gaps and limits in the check's order (`test_the_file_is_read_into_gaps_and_limits_in_the_order_the_check_made_them`).
2. A file that is missing or does not read is no check (`test_a_file_that_is_missing_or_does_not_read_is_no_check`), and
   neither is one that holds no standing limit (`test_a_file_that_reads_and_holds_none_of_the_standing_limits_is_empty_and_no_check`;
   the report stage says so in one line and exits 2: `test_a_run_whose_output_of_the_check_is_empty_is_not_drawn`).
3. `of(meta)` keeps a check and gives an empty one to a `meta` without it
   (`test_a_meta_without_the_check_gets_an_empty_one_and_a_meta_with_it_keeps_it`).

### History

- 2026-10-30: M9 slice B: built.
- 2026-10-30: M9 slice B, fix round: a readable file with none of the standing limits is no check.

## render

`full.md`, the run log, the not-checked lists, the recommendations, and the fixed tables and
words the pages share. Pure functions over the stage reports: nothing is detected or judged, and
every rule that picks what to show is a fixed table at the top of the file.

Status: built.

### Inputs

- `meta`: `repo`, `run`, `date`, `source`, `hash`, `hash_kind`, and optionally `tool`,
  `channel`, `finished`, `feedback`.
- `reports`: `{stage: contract-1 report}` for the stages that ran.
- `stamps`: `{stage: validate.Stamp}`; `notes`: `{stage: [stderr lines]}`; `runs_ok`: the stages
  that completed.
- `capability_full`: `02.5-capability`'s `capability.json` (every citation), optional.
- The builder checks (`need.*`, `port.*`, `host.*`, `trig.*`, `ask.*`, `fit.*`, `clean.*`, `cap.ship`,
  `cap.context`) are read from the `02.6-builder` report (`render.BUILDER`) since restructure step 4; a
  report without one says Not measured for them, as a run made before the checks did. The step has a row
  in `LOG.md` and is named wherever a step that did not run or did not pass its fixture check is
  named (`render.NAMED`: the limits, "What Walkdown didn't check", the warning, the headline, the
  brief), but has no section of its own. `phrases_findings(r)`
  is every finding `02.4-phrases` held before the move (its own, then the builder's that were its), for the
  lookups by line that read all of them (the audience of a line, the text of a line).

### Outputs

- **`full(...)` -> `full.md`**: sections 1 to 7 in stage order, each with its status line
  (`STATUS`), its validation stamp, and every finding: location (`loc`: `file:line`, or
  `file (extracted text, page N, line M)` for PDF, DOCX, and image text), fields, and the
  verbatim quote in a code span (`code`). Then Recommendations, then "What this is not"
  (`NOT_WHAT`). Notable lists: divergences with their carrier and, for a drawn page, how
  (`carrier rendered (collapsed)`); every line changed by folding, typography included; the
  rubric table, prohibitions marked; settings that restrict tools and stated limits with what
  backs them; each leg's and grant's evidence.
- **`recommendations(reports)`**: template matches only, in stage then document order; each
  conditional ("If ...") and naming a narrower alternative; one per file and template; settings
  allow-list edits have their own template. Recommendations carry no model text (owner,
  2026-10-20, C28).
- **`limits(qa)`, `limits_doc(meta)` -> `data/limits.md`** (was `data/07-limits.md`; section 7 has no stage): the limits,
  one line for each finding of the check of the run, in its order (it gathers them since M9 slice B; `limit_line` words
  each kind, and a kind it does not know is worded `The step "<plain>" (<check>): expected <expected>; found <found>.`):
  stages that failed or are not validated, skip findings, stage notes naming a limit, unread and unscanned files, then
  `STANDING_LIMITS` (a table by the id the check gives each: `static`, `model-reads`, `version-drift`, `english-only`,
  `phrases-zero`). Every line, nothing folded. The checks that found nothing (`qa.checked`) are no limits and are not in this
  file, which is what it was before slice C; `full.md` says them under their own heading at the end of section 7 (below). A step is named by its plain name in quotes
  (`step(stage)`: `step "What the text asks for"`), never by its id: `The step "<name>" did not run to
  completion; ...`, `The step "<name>" validation <result>: ...`, and a note is prefixed `(step "<name>")`.
  The test-data line counts the findings kept out of the capability map for the steps "What ships" and
  "What the text asks for". The standing limits say what the optional model reads are: Sweep flags
  passages for a person to read, Pinpoint names the line behind each flag, and neither changes a finding
  in sections 1 to 5. A coded step the run's stop left out (the check's `stopped` finding, O3) is not
  a step that did not run to completion: its line is `<name>: not run, the run stopped after "<name>" (--until).`
  **A model read with passages that got no answer** (M9, `model_read_lines(qa, full=True)`; after the lines on steps
  and before the skip lines): one line for each read, `<plain>: N of M passages got no answer, after one retry. Reasons:
  <reason> (<count>); .... The call log is data/<step>.calls.jsonl.` The retry is said only of passages that were sent
  (`no_answer_phrase`: `12 of 12 passages got no answer; none was sent` when nothing was; `5 of 12 passages got no
  answer, after one retry; 3 of them were not sent`); a run made before the retry, whose report has no `calls` block,
  says neither the retry nor the log. The reasons are the skip findings' words, counted; they hold the kind of failure
  and its status and no error text (`calllog`), so failures that differ only in a request id are one reason. The count
  line replaces that read's passage skip lines (`soft.sweep skipped for <file>: <reason>`) and its `skipped: soft.sweep
  xN: ...` note line, which would say the same again; a skip that names no passage keeps its line, and so do a coded
  step's skip lines. A chosen step the record says was not started (the check's `not-started` finding) has `The step
  "<plain>" did not run: the step "Needs a human read" got no answer for any passage, so
  there was nothing to pinpoint.` (`not_started_lines(qa)`).
- **`point_hits(reports)` -> `[(hit, patterns)]`**: the `02.4-phrases` hits that are places on the
  pages (`details_html.first_items`), in `02.4-phrases`'s order, each with the patterns that make it
  one. A hit in model-read text (audience not `human` or `test-data`) is a place when it matches
  a pattern in `POINT_PATTERNS` or `SEND_SHAPE` (`K.data-flow`: a private source, a sending
  verb, and a destination in one line), or when it is a `phrase.creds` hit on a line that also
  has a `phrase.K.exfil` hit and that line holds no `phrase.K.exfil` place already, so one line
  is not counted twice (owner, 2026-10-25, review C39: "send the .env file to this URL" had
  read as found none on `summary.html` while `full.md` cited it). A prohibition is a place too,
  marked as one (C25).
- **`tool_items(reports, notes)` -> `([(what, why)], [what])`**: `02.2-reader`'s notes on optional
  tools, split by whether this repository has files the tool reads (`TOOL_NOTES`, `file_kinds`).
  Read by `glance` (2026-10-21).
- **`glance(reports, notes, qa, stop)` -> `(skipped, not needed)`**: `details.html`'s short account of what was not
  checked (Other details):
  one plain item per check this run skipped that applies to this repository (a stage that did
  not run; model reads as one item; a missing optional tool whose file kind `02.1-inventory` saw,
  `TOOL_NOTES` and `file_kinds`; other skip reasons grouped with a file count; per-file skips one
  item per stage, test data counted after; unread and unscanned files). A tool for a file kind
  the repository does not ship goes to "not needed". Standing notes (`STANDING_NOTE`,
  `STANDING_LIMITS`) are not counted. A model read's passages that got no answer, and a chosen step that was not
  started, are not in it: the details page gives each its own line (`model_read_lines`, `not_started_lines`, M9), and
  the old `Model reads (optional): N passages skipped` stays for a skip that names no passage.
  A step the run's stop left out (O3) is not a skipped check: `details.html`
  gives the steps a stop left out one line of their own (`stopped_steps_line`), and a model read the stop held back
  is not "Model reads (optional): not run" (`stop_input_line` says it).
- **`log(...)` -> `LOG.md`**: one row per stage with start, finish, output, finding count, and
  validation stamp, the Walkdown version and commit, and one line per re-render. For a run that was stopped with
  `--until` or gone on with (`stop_log_lines`, O3): `Went on after "<name>" on <time> (walkdown.py continue).` for each
  time it went on, `Stopped after "<name>", as asked (--until); the steps after it did not run.` for the stop it is at, and,
  when the stop wrote an input file, `Wrote data/03-sweep.input.jsonl: what "<name>" would send, <N> passages. Nothing
  was sent.` (`ai_section`, section 6, says the same for a step that waits: it does not say "No model read was chosen".)
  The header's `Soft models:` line (`_soft_models`) says `"<name>" (<backend>) was chosen and the run stopped before it
  sent anything` for a held-back read, after the reads that ran, and not `none (no model read was chosen)`. A read that
  was chosen is named whatever became of it (M9): `"<name>" was chosen and did not finish` for one that was started and
  left no report, `"<name>" was chosen and did not run` for one the record says was not started (`not_started`), and
  (M9 slice B, from the record's `chosen`, `chosen_without_a_step`) `"<name>" was chosen and did not start` for one a step
  before it kept from starting (a crash) and `"<name>" was chosen and the run stopped before it` for one a stop was before and
  that is not the one that wrote its input file, and `"<name>" was chosen by an earlier command and did not run at continue` for
  a read the record says an earlier command chose and that did not run at `continue` (`dropped`). Section 6 of `full.md` says the same of
  such a read in a line of its own (`ai_section`) and does not say no read was chosen; for a dropped read the line is the one
  of section 7 and the brief: `The step "<plain>" was chosen by an earlier command and did not run at continue; <how>.`
  (`dropped_line`; `common_lines.dropped_how` gives the way that works: `continue` while the run is stopped, a new audit once it
  has finished).
  `none (no model read was chosen)` is for a run that chose none.
- **The sections of `full.md` for a stop** (O3): a section whose step the stop left out has the status `Not run: the
  run stopped after "<plain>", as asked. See 7.` (`status(..., stop)`; `Not run. See 7.` for a step that failed or
  that nobody chose to run), and the five "Not measured" lines of the builder sections (what it needs, will it trigger,
  ready for any AI, current and clean, do the tools fit) read `Not measured: the run stopped after the step "<plain>",
  as asked.` (`stop_not_measured`, the same words as the cards of the pages). A run that did not stop keeps the old
  words.
- **Stop words** (O3): `stopped_left(stop)` (the coded steps after the step a run stopped at; none for a run that went
  through or one stopped after the last coded step), `stop_plain(stop)`, `STOPPED_LINE`, `WROTE_LINE`, `WENT_ON_LINE`,
  `STOP_NOT_MEASURED`, `STOP_INPUT_LINE`, `wrote_line(stop, path)`, `stop_not_measured(stop)`, `stop_input_line(stop)`,
  and `stopped_steps_line(stop)`: one place for the words the pages, the brief, and `LOG.md` use for a stop.
- **`code(s)`**: an inline code span that survives backticks inside `s`.

### Shared tables and words

- `LEG_NAMES` ("Can read your data", "Can take outside input", "Can send data out"), `LEG_DEFS`,
  `TRIFECTA_ALL`, `TRIFECTA_SOME` (worded 2026-10-21 so neither sentence takes back the
  other, and with no comparison to other repositories); `NOT_WHAT`; `CAPABILITY_ONLY` and `CAPABILITY_ONLY_SHORT`
  ("capability only").
- `POINT_PATTERNS`, `SEND_SHAPE`, `SUBGROUPS`, `HEADINGS`, `ORDER`.
- Signal levels (soft D1): each `02.4-phrases` point names its patterns with their base rate over the
  other audited repositories (`rates_note`, from `Library/baserates.json`), or just the pattern when
  there is no table.
- Sweep band (soft D2): `SWEEP_DRIFT` 0.1 around the 0.5 cutoff; a passage at p_any >= 0.6 is
  listed, 0.4 to 0.6 is near the line; a passage whose top answer is `none` is named by its
  likeliest kind (`sweep_kind`).
- A read with no probability (M1 slice A; a model that takes text, `probability.of` is None): there is no band to put a passage
  in. Whether the read has one is decided from its backend (`probability.gives`, the `probability` of the backend's row in
  `options.BACKENDS`), and never by looking for a number in the rows: a text model that got no answer for any passage has no rows to
  look at, and the status line must not name a band (`0 flagged at p >= 0.6`) for a model that has no `p` (M1 fix 9). The status
  line is then `Sweep: claude-cli (remote, <model>): 0 passages read, 0 flagged (0 with no phrase pattern hit); this model gives no
  probability.`, and a backend that gives a probability keeps its band, with or without rows. `sweep_split` lists the passages it flagged with the clear ones, after any that have a number and in the order they came, and
  puts the ones it did not flag nowhere. Section 6 words it: the status line reads `Sweep: claude-cli (remote, <model>): 4 passages
  read, 2 flagged (1 with no phrase pattern hit); this model gives no probability.`, the opening paragraph says `Listed when the
  model names a kind other than none. This model gives no probability, so there is no band and nothing is near the line.`, and each
  row is `- <file>:<lines>: <kind> (this model gives no probability); <what covers it>`. `details_html.first_items` and
  `review_html` carry the same words in the place's `where` and in "What the model said"; the summary and the details page leave model
  reads to the review page (report v3). No number is made up, and a saved `p_any` that is no number (null, text, a bool, not finite)
  is read as none. A read with numbers is worded as it always was.
- The model a service names, and the backend, reach section 6, `LOG.md`, and the details page through `flat` and `stagenote.MODEL_CAP`: one
  line, cut to 80 characters. The backend is flattened and cut wherever a page writes it: the status line and the rows of section 6,
  the log header (a stop's `prepared.backend` too), and the lead of a place on the details page (M1 fix 10). A saved report from before
  the steps held a service's model name to the model-name rule can carry any text in the model, so the pages flatten it as well.
- Benign share (C15): section 4 says `BENIGN_SHARE` ("benign share not measured."). No stage writes
  a label now, so the report reads none; the section's opening line says the same, and nothing on a
  page names the labels (restructure step 8b).
- Step names on a page: `step(stage)` gives `step "<plain name>"` from `stages/stages.json`; the "Not
  measured" lines of the builder's questions, the sweep lines of section 6 ("no phrase pattern matched
  it"), and the other lines that named a stage by its number use it. An evidence citation in `full.md`
  keeps the stage's id (restructure step 7b). Counts that read "N <noun>" go through `n()`, so one is
  "1 file" and many are "files" (R2).
- Stated limits: `limit_words`, `limit_routes` (C32).
- Test data: hits, hooks, and pairs in test data are counted, never listed as points.

### Must never

- Emit a score, severity, rank, or verdict word (benign as a verdict, concerning, safe,
  malicious, risk score).
- Sum SessionStart hook bytes across host configs.
- Show a stage that did not pass validation without saying so.

### Done when (tests in `tests/test_render.py`)

1. `full` holds every `02.4-phrases` finding's location and quote, and marks prohibitions in section 4
   and the rubric table.
2. An INCOMPLETE stamp is said on its stage and puts the stage in `limits`.
3. Hook configs' load bytes are listed per host, never summed.
4. `recommendations`: a SessionStart hook and a fetch-and-follow hit each give one line starting
   with the location and containing "If"; allow-list edits in one file give one; a
   `hook+phrase` pair gets its template.
5. `code` survives a backtick.
6. No document contains "verdict: ", "score", "severity", "benign:", or "malicious".
7. Hidden-text and orphan pairs on human-facing lines are counted, model-facing ones listed; a
   pair whose only `02.2-reader` evidence is a folded line reads "disguised with look-alike or
   invisible characters" (`hidden_how`).
8. Section 6 (the AI reads; step 5): a run that started neither AI stage says in one line `No model read was chosen; optional: `--sweep jev`, then `--pinpoint claude-cli`.` and nothing else (no validation line); a run that did names each backend, what Sweep found, each started stage's validation word (`no fixture set` for Pinpoint is neither a pass nor a failure), and a chosen stage that did not finish. The packet's question listing is gone. Before step 5 the section also named label counts,
   agreement, relational answers and skips, and every question with its answer or skip. The report
   reads no label (step 6): section 4 always says the benign share is not measured
   (`test_benign_share_is_not_measured`).
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
13. A stop (O3): a step it left out is a limit with its reason and not a failure, the log and section 6 say what was
    written and not sent, and a run that went through changes nowhere
    (`test_a_step_the_stop_left_out_is_a_limit_with_its_reason_and_not_a_failure`,
    `test_the_log_says_the_stop_the_input_file_and_each_continue`,
    `test_section_6_says_a_model_read_waits_and_nothing_was_sent`); the "Not measured" lines of the builder sections
    and each section's status say the run stopped after the step, as asked, and keep their words for a run that did
    not stop (`test_full_md_says_a_stop_left_a_section_out_and_a_run_that_did_not_stop_keeps_its_words`); the log
    header says a held-back model read was chosen
    (`test_the_log_header_says_a_model_read_was_chosen_and_the_stop_held_it_back`).
14. A model read's passages that got no answer (M9): section 7 and `limits.md` have a line for each read with the count,
    the reasons counted, and the call log; every passage answered means no line; the count line replaces that read's
    passage skip lines and its `skipped:` note, while a coded step's skip lines stay; the skipped list of the details
    page does not hold the count, and keeps the old words for a skip that names no passage; a chosen step that was not
    started has its line
    (`test_section_7_counts_the_passages_that_got_no_answer_counts_the_reasons_and_names_the_call_log`,
    `test_section_7_says_nothing_when_every_passage_got_an_answer_and_each_read_has_its_own_line`,
    `test_section_7_says_a_model_reads_skips_once_in_its_count_and_a_coded_steps_skips_stay`,
    `test_the_skipped_list_of_the_details_does_not_hold_the_count_and_a_run_with_no_count_keeps_its_words`,
    `test_a_step_that_was_not_started_is_in_section_7_and_not_in_the_details_list_of_skipped_checks`).
15. The log header names a chosen model read whatever became of it, and says no model read was chosen only for a run that
    chose none (`test_the_log_header_names_a_chosen_model_read_whatever_became_of_it`,
    `test_the_log_header_names_a_chosen_read_that_never_started_and_one_a_stop_was_before`); section 6 says a chosen read
    that never started and never that no read was chosen
    (`test_section_6_says_a_chosen_read_that_never_started_and_never_that_no_read_was_chosen`).
16. A fixture check that could not be made reads `The step "<plain>" could not be checked against its fixtures: it gave
    <result>.` (ERROR, SETUP ERROR) or `The step "<plain>" has no fixtures to be checked against.` (NOT BUILT, `no fixture
    set`) in section 7, as in the hold's brief, and a FAIL keeps its words
    (`test_a_fixture_check_that_could_not_be_made_has_its_one_set_of_words_in_section_7_and_the_hold`).
17. A file name or a reason from the repository is one line in section 7 and wherever `full.md` prints a location
    (`test_a_name_from_the_repository_is_one_line_in_section_7_and_the_body_of_full_md`).
18. A read an earlier command chose and `continue` left out has one sentence in section 7, section 6, the log, and the brief
    (`test_a_read_chosen_earlier_and_left_out_at_continue_has_one_sentence_in_section_7_section_6_the_log_and_the_brief`); the
    stop's brief names the reads that wait and carries their options
    (`test_a_stop_before_a_model_read_names_the_input_file_and_the_option_to_go_on_with`,
    `test_the_waiting_reads_are_the_chosen_ones_a_stop_is_before_including_the_one_that_wrote_its_input`).


### Added 2026-10-25 (review C42, an outside tester)

- `tag_text(s)`: what the Unicode tag characters in a line spell (`library.tag_texts`: U+E0020-U+E007E,
  each minus U+E0000), each run joined by a space, or None. `selector_text(s)`: the same for the runs of
  variation selectors (`library.runs`: two or more selectors, in a row or with only stripped characters
  between them; the text each spells, white space collapsed), or None (P1, 2026-10-29).
  `lookalike_note(h)`: for an `endpoint.host`
  with `lookalike_of`, " (look-alike letters, <punycode>; imitates <host>)", else "".
- `full.md`: a phrase hit with `decoded_text` says "(decoded from base64: ...)"; a divergence
  with `decoded` adds "the hidden characters spell ..." (it said "the tag characters spell ..."
  until 2026-10-29, when a run of variation selectors began to add its text to `decoded` too), and
  a masked one says the mask once, in place of its text, and nothing after it; an
  endpoint written with look-alike letters carries `lookalike_note`.

Done when: `test_decoded_and_lookalike_text_is_shown`, `test_full_says_what_hidden_characters_spell_whichever_kind_hid_them`.

### Added 2026-10-27 (plan for builders, slice 6): is it current and clean

- `clean_of(r)`: `02.6-builder`'s `clean.*` (`02.4-phrases`'s until restructure step 4) as `kinds` in `CLEAN_KINDS` order (from `Library/clean.yaml`, `clean_kinds`), the distinct model IDs, and
  `measured` when the run has `clean.checked`. `clean_parts(kind, f, quote=False)`: (where, what);
  with `quote` the line's text (details and full.md only). `clean_count`: a row's count, the models
  row with how many distinct.
- `full.md` section 4 ends with "Current and clean" (`clean_lines`), after "Ready for any AI".

Done when: `test_clean_helpers`.

### Added 2026-10-26 (plan for builders, slice 5): do the tools fit the job

- `fit_of(r)`: `02.6-builder`'s `fit.unused`, `fit.missing`, `fit.inherits`, `fit.hook`, and
  `fit.loop` (`02.5-capability`'s and `02.4-phrases`'s until restructure step 4), and `02.5-capability`'s contradicted `cap.limit` rows as `kinds` in `FIT_KINDS` order (from `Library/fit.yaml`, `fit_kinds`, with `FAMILY_TEXT` and `OFTEN_TEXT` from the same file) (hooks:
  those that run on every prompt or tool call); `measured` when the run has `fit.checked`.
  `fit_parts(kind, f)`: (where, what) in words (`FAMILY_TEXT`); `hook_text(h)`: how often a hook
  runs, its output's tokens when it becomes context, the cap, or that it is not known for that host.
  `brief_fit_counts`.
- `full.md` section 5 ends with "Do the tools fit the job" (`fit_lines`): entries checked, every
  place, and the other hooks.

Done when: `test_fit_helpers`.

### Added 2026-10-26 (plan for builders, slice 4): will it trigger

- `BYTES_PER_TOKEN` from `Library/loading.yaml`; `TRIGGER_TABLE` is `Library/trigger.yaml`, read through `library` (not by importing the builder step's `trigger.py`).
- `trigger_of(r)`: `02.6-builder`'s `trig.*`, `measured` when the run has a `trig.listing`, and `kinds`:
  `TRIG_KINDS` in order (from `Library/trigger.yaml`, `trigger_kinds`: not read, agents not loaded, rules, keys, values, tools, overlaps, cut in
  the listing, guidance), each with its name, why, and places. `trig_parts(kind, f)`: (where, what)
  in words; `trig_place` joins them. `entries_line(tr)`: skills and commands by mode, then agents.
  `listing_lines(tr, ctx)`: the descriptions' tokens against about 1% of the expected context and
  of 200,000, saying when they do not fit at the expected one; agents against Claude Code's warning.
  `brief_trigger_counts(tr)`: places that break a host rule, guidance rows, overlapping pairs.
- `full.md` section 4 gains "Will it trigger" (`trigger_lines`) before "Ready for any AI".

Done when: `test_trigger_helpers`.

### Added 2026-10-26 (plan for builders, slice 3): is it ready for any AI

- `HOST_KEYS` (from `Library/hosts.yaml`, read through `library`); `log` writes "Target hosts: ..." ("none named"
  without any). Reading the option (`parse_hosts`) is `stages/_shared/options.py`'s since restructure step 7, and a
  run's hosts come from its record (`data/run.json`), not from this line: nothing reads `LOG.md` back.
- `ready_of(r)`: `02.6-builder`'s `host.coverage`, `host.drift` (and those that differ), `host.feature`
  by kind (`FEATURE_KINDS`, from `Library/hosts.yaml`: name and why), every `SKILL.md` outside test data, and the `loose`
  ones no host reads where they sit. `host_line(c)`: a host's files here, or "none of its files (it
  reads ...)" from `Library/hosts.yaml`. `drift_line(d, cov)`: a differing pair and who reads each.
- `todo(r, targets)`: per host named, in order: no instruction file it reads; none of the skills
  where it reads them (only when some host reads skills in place); the places written for Claude
  Code only, counted by kind; other hosts' hook files; "nothing missing." when none; then each
  differing pair where the named hosts read different sides.
- `full.md` section 4 ends with "Ready for any AI" (`ready_lines`): the to-do list for the hosts
  named, every host, the skills to install, every copy, every feature.

Done when: `test_ready_helpers`.

### Added 2026-10-26 (plan for builders, slice 2)

- `PORT_KINDS`: the kinds of place that tie a repository to one machine, in order, each with its
  name and why it breaks elsewhere (`02.6-builder`'s `port.*`, `02.3-graph`'s `graph.case`); read from
  `Library/tools.yaml` (`port_kinds`). `needs_of(r)`:
  the programs, packages, what is not declared, and the places by kind; `graph.case` only from
  files that run or the AI reads (not test data, not files for people); `measured` when the run
  found any of these or holds slice 3's `host.coverage` (there is no marker finding, so a run made
  before slice 2 is not measured).
- `full.md` section 1 ends with "What it needs" (each program and package, declared where or
  not, and where used) and "What ties it to one machine" (every place by kind; `needs_lines`).

Done when: `test_needs_lines`.

### Added 2026-10-26 (plan for builders, slice 1): what it costs and what ships

- `DEFAULT_CONTEXT` (32,000, from `options.py`) and `CLAUDE_CONTEXT` (200,000); `log` writes "Expected context: N
  tokens". Reading the option (`parse_context`: `32k`, `200k`, `8192`, `8k`, `1m`) is `options.py`'s since
  restructure step 7, and a run's context comes from its record, not from `LOG.md`.
- `cost(r)`: `02.6-builder`'s `session` and `project` tiers (`cap.context`; `cap.ship` for the bands) and the entry with the most at its fullest
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

19. A read with no probability (M1 slice A): the split lists the passages it flagged with the clear ones and the rest nowhere, in order
    after any with a number; section 6 says it in its status line, its paragraph, and each row; no number, `p=`, `0.00`, or `nan` is on
    the page; a read with numbers is worded as it was
    (`test_no_probability.py::test_the_split_puts_the_flagged_passages_of_a_read_with_no_number_with_the_clear_ones_and_the_rest_nowhere`,
    `test_a_passage_with_a_number_and_one_without_are_ordered_numbers_first`,
    `test_section_6_says_what_the_read_found_and_that_the_model_gives_no_probability`,
    `test_a_read_with_a_number_is_worded_as_it_always_was`; from the backend, with no row and with only skipped rows,
    `test_the_backend_decides_the_wording_so_a_read_that_got_no_answer_names_no_band`,
    `test_a_backend_that_gives_a_probability_keeps_its_band_even_when_it_got_no_answer`,
    `test_the_backends_table_says_which_backend_gives_a_probability`); the places the pages draw from carry the words in their `where`
    (`test_the_places_every_page_is_drawn_from_carry_the_words_where_the_number_would_be`), the review page says it in "What the model
    said" and shows no score (`test_the_review_page_says_it_in_what_the_model_said_and_shows_no_score`,
    `test_the_review_page_still_shows_the_score_of_a_read_that_has_one`), the summary page and the brief do not crash
    (`test_the_summary_page_and_the_brief_do_not_crash_and_make_up_no_number`), a saved `p_any` that is no number reads as none
    (`test_a_saved_finding_whose_p_any_is_no_number_reads_as_a_finding_with_none`), and the pinpoint asks about the same passages
    (`test_the_pinpoint_asks_about_the_same_passages_the_pages_list`).
20. The token line names each read that ran, `not reported` where the backend gave none, `sent nothing`, the cache counts, and the
    fixture check only when it spent tokens in this run, and a default run has none
    (`test_tokens_line.py::test_the_line_names_each_read_that_ran_and_the_fixture_check_in_the_owners_words`,
    `test_a_read_that_does_not_report_its_tokens_says_not_reported`,
    `test_a_fixture_check_that_spent_no_tokens_this_run_is_not_in_the_line`, `test_a_read_that_sent_nothing_says_so`,
    `test_a_total_that_only_some_of_the_calls_reported_says_so_in_every_place_it_is_printed`,
    `test_cache_tokens_are_named_when_there_are_some`,
    `test_a_run_with_no_model_read_has_no_token_line_and_says_what_it_always_said`, `test_only_the_pinpoint_that_ran_is_named`);
    section 6 has it after the validation and before the findings (`test_section_6_has_the_line_after_the_validation_and_before_the_findings`).
21. The model and the backend a service or a file names are one line and cut on every page that shows them
    (`test_no_probability.py::test_the_log_and_section_6_show_a_models_name_on_one_line_and_cut`,
    `test_the_backend_is_one_line_and_cut_on_every_page_that_names_it`: the details page, the log header with a stop, section 6).

### History

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
- 2026-10-29 (P1): a divergence's `decoded` text can come from a run of variation selectors as well as
  from tag characters, so `full.md` says "the hidden characters spell" (it said "the tag characters
  spell"). `selector_text(s)` is new: what the runs of variation selectors in a line spell (from
  `library.runs`), for a place's note beside `tag_text`'s, so the review and details pages say what a
  selector run spells as `full.md` does.
- 2026-10-29: restructure step 5: the soft stage splits into `03-sweep` and `04-pinpoint`, both optional. Section 6 says in one line when no model read was chosen; the packet and its question listing are gone; the LOG.md and limits lines follow the stages that were started; a stage with no fixture set is stamped `no fixture set` and is neither a pass nor a failure.
- 2026-10-29: restructure step 5, round 2: LOG.md's header says `Soft models: none (no model read was chosen)` for a run that chose none; a chosen AI stage that failed (a key of the reports with no report) is named as a step that did not work.
- 2026-10-29: restructure step 6 (keep-or-cut, Q8): the "Conditionals" listing and the conditionals
  count in the part 2 summary line leave `full.md` (the table was cut from stage 4). The report's
  readers of a stage 6 label are cut, since no stage has written one since step 5: the benign share
  is always "not measured"; the questioning line, the notes beside legs marked "not an instruction",
  the "do" reads (`DO_*`, `DRIFT`, `NOT_DO_P`, `do_reads`, `p_do`), and the label, comparison,
  agreement, read, and question pieces of `_soft` are gone. Section 4 keeps its "stage 6 labels did
  not run" words until step 8.
- 2026-10-29: restructure step 3b: the words under each kind of place are read from the Library, not
  written in `render.py`: `PORT_KINDS` (`tools.yaml`, `port_kinds`), `FEATURE_KINDS` (`hosts.yaml`,
  `feature_kinds`), `TRIG_KINDS` (`trigger.yaml`, `trigger_kinds`), `FIT_KINDS`, `FAMILY_TEXT`, and
  `OFTEN_TEXT` (`fit.yaml`, `fit_kinds`, `family_text`, `often_text`), and `CLEAN_KINDS` (`clean.yaml`,
  `clean_kinds`). Each name has the same value, type, and order as before; the pages are the same
  bytes (`tests/test_library_kinds.py`).
- 2026-11-01: `secrets_line` says `Secret scan: skipped (no scanner installed).` only for the skip with `file` null. A skip for one file
  leaves the count and the scanner's name in place and adds `The secret scan could not scan N file(s).`; section 7 names each file, as
  it did. Section 4's list of lines leaves such a skip out (`test_the_secret_line_tells_one_file_it_could_not_scan_from_no_scanner`).
- 2026-11-01: `secrets_line` adds `The secret scan left out N lock file(s).` from `secret_left_out`, after what it could not scan, and nothing
  with no scanner (`test_the_secret_line_says_how_many_lock_files_the_scan_left_out`). A whole run: `06-report/tests/test_secret_fields.py`.

### History (restructure step 7)

- 2026-10-29: the tables keyed by stage name (`HEADINGS`, `ORDER`, `LOG_ROWS`, `NAMED`, `STEP_NAMES`, `AI_STAGES`, `AI_SECTION`)
  are built from `stages/stages.json` (`stagelist`, notes M7); `STATUS` and `SECTIONS` stay code, and a test checks
  their keys against the list (`test_the_stage_tables_are_built_from_the_stage_list_and_status_and_sections_are_checked_against_it`).
  The limits file is `data/limits.md`; `log` has no `07-limits` row, its `05-report` row lists `brief.md` and
  `data/limits.md` among its outputs, and its deps line says `see data/limits.md`. `parse_context`, `parse_hosts`,
  `context_of`, and `hosts_of` left (the first two for `options.py`; nothing reads LOG.md back). The base rates are
  read through `stages/_shared/rates.py`.
- 2026-10-29: restructure step 7b: the citations under the trifecta legs and install grants in `full.md` print the
  stage of each piece of evidence as the evidence holds it, by name (`- stage 02.1-inventory struct.agent-tools ...`);
  they printed its number (`- stage 01 ...`). It is the one line of `full.md` that changes with the data, on purpose
  (restructure notes M1, N3: a stage has one name everywhere it appears). The pages' words do not change.

### History (restructure step 8b)

- 2026-10-29: restructure step 8b: the words on the pages. A stage named by an old number or an id on a reader page
  is named by its plain name in quotes (`step()`); the lines are the standing limits (stage 2, stage 4, and the one
  about stage 6 answers, now what Sweep and Pinpoint do), the "Not measured" lines of `full.md` (stage 4, stages 4
  and 5, stage 3 and 5), the sweep line and list in section 6, the limits lines (`Stage <id> did not run to
  completion`, `Stage <id> validation`, `(<id>) <note>`, the test-data line), section 6's validation line and its
  "was chosen but did not finish" line, section 5's "derived from stages 1 to 4", the brief's "Model reads
  (experimental, stage 6)", and `changes.md`'s "Model reads (stage 6)" and "matching code (stage 4)". The benign
  share is "not measured" with no mention of labels, in section 4's status line and its opening line. The "not
  comparable" line for a run of an older record format says the run was made by an earlier version of Walkdown and
  its data is in another shape. The line that notes extracted text (02.4) and the "carried forward" notes (02.5,
  Sweep) name the step; `glance` still skips the older wording. Counts go through `n()`: `COUNTS` in `drift.py`
  holds both forms, and the lines, passages, files, and findings counts of `render.py`, `glance.py`, and `review_html.py`
  that read "1 files" now read "1 file". The failed model read's wording is untouched (parked, `MODEL-NOTES.md` M9).
  Round 2: the two standing limits of `02.5-capability` (`Library/capability.yaml`) begin `standing limit:` and no
  longer say "stage 5" or "stage 3"; `STANDING_NOTE` accepts that and the older `stage 5 limit`.

### History (O3)

- 2026-10-30: O3: a run stopped with `--until`. `limits`, `glance`, `ai_section`, `full`, and `log` take the stop from
  `meta["stop"]` and `meta["continued"]` (new keys, from the record); the stop words are in one place (above). A step
  the stop left out is a limit with its reason, and the line no longer says it did not run to completion.
- 2026-10-30: O3, fix round: the sections of `full.md` and their "Not measured" lines say the run stopped, as the
  cards do (`status`, `needs_lines`, `ready_lines`, `trigger_lines`, `fit_lines`, `clean_lines` take `stop`); the
  `Soft models:` line of `LOG.md` names a held-back read; `render.glance` no longer lists a step the stop left out as a
  skipped check (`stopped_steps_line` and `stop_input_line` say them); `summary.html` and `details.html` each get
  the line for a held-back read (`summary_html.stop_note`).
- 2026-10-30: O3 verification: "What Walkdown didn't check" says a held-back read once (`stop_input_line`); the
  sentence " The run stopped before the model read." after "Every step that ran passed its own checks." is gone.

### History (M9)

- 2026-10-30: M9 slice B: `limits(qa)` and `limits_doc(meta)` word the check of the run's findings and gather nothing:
  the gathering (skips, standing limits, INCOMPLETE stamps, steps that did not work, test data set aside) moved to
  `stages/05-qa/gather.py` with the same order and the same once-each rule, and the words are as they were. `ai_passages`
  is gone (the check counts); `model_read_lines`, `model_read_nothing`, `not_started_lines`, and `glance` take the check's
  view. `STANDING_LIMITS` is a table by id, `LIMIT_NOTE` is `stages/_shared/limitnote.py`'s, `STEP_NAMES` names the check,
  and `log` has a row for the check.
- 2026-10-30: M9 slice A: `limits`, `limits_doc`, and `glance` give a model read's count of passages that got no answer
  (`model_read_lines`, `no_answer_phrase`, `ai_passages`, `model_read_nothing`) and a chosen step that was not started
  (`not_started_lines`, from `meta["not_started"]`). Everything else in section 7 is as it was.
- 2026-10-30: M9 slice A, fix round: section 7 says a model read's skips once, in its count line, with the reasons by
  kind (the passage skip lines and the step's `skipped:` note of that step are left out; a coded step's stay). The
  details page gives the count its own line beside "Not every step worked" with the reasons and the call log, no longer
  under "Skipped in this run, most often because an optional tool is not installed", and its fold of every limit leaves
  it out. The summary has no count line for a read that got no answer for any passage (its headline and warning say
  it), and its warning does not say places are missed when the only step that did not work is a model read.
  "The coded checks are complete" is worded truly when a coded check was skipped for a missing tool (INCOMPLETE).
- 2026-10-30: M9 slice A, fix round: the log header names a chosen model read that crashed or was not started
  (`_soft_models`); it said `none (no model read was chosen)` for a Sweep that was chosen and crashed.
- 2026-10-30: M9 slice B, fix round: the log header and section 6 name a chosen read with no step (`chosen_without_a_step`,
  from the record's `chosen`): a crash before the reads left `Soft models: none (no model read was chosen)` and a section 6
  that said no read was chosen. Section 7 words a fixture check that gave no verdict (`fixture-unchecked`) in the hold's
  words (`common_lines.UNCHECKED`); `STOPPED_LINE` is `common_lines.STOPPED_LINE`.
- 2026-10-30: M9 slice C: `limit_line` words the three coverage gaps (`coverage-missing`, `coverage-short`, `coverage-broken`)
  in the hold's sentence (`common_lines.coverage_gap_text`), so none falls to the fallback for a kind it does not know, and a new
  check of the run's own, `qa.checked`, in `checked_line`: `What the text asks for: phrase.K.exfil, phrase.creds and 19 more checked
  83 files, with 2 more skipped (listed above), found none.` (a check with nothing to look at: `... had nothing to look at.`).
  `summary_html.not_working_pairs` words a coverage gap as a clause
  (`common_lines.coverage_page_words`), and `failed_checks` names a step with one beside a step that failed its fixture check,
  once, so the headline does not say "found none" without saying a step did not work.

### Checks that found nothing (M9 slice C, fix round)

`checked_lines(qa)` gives the lines of `qa.checked` in the check's order, none when no step has one. `full.md` puts them
under `### Checks that found nothing` at the end of section 7, after the standing limits, as bullets with the check ids, one for
each pass (`checked_line`: `What the text asks for: phrase.K.exfil, phrase.creds and 19 more checked 83 files, with 2 more skipped
(listed above), found none.`; "listed above" is the limits above it; `Builder checks: port.exec checked 319 program uses, found
none.`). `details.html` has a fold of its own, `Checks that found nothing (N)`, after the fold of the limits, with counts and no ids,
one line for each step (`checked_steps`, owner, 2026-10-31):

    What the model actually reads: checked 66 files with 2 checks and 41 files with 1 check, found none. 1 check had nothing to look at.
    Builder checks: checked 4 files with 1 check, 58 files with 4, 319 program uses with 1, 1 file with 1, 16 entries with 8, 47 files with 2 and 51 files with 3, found none. 1 check had nothing to look at.

Within a step the lines with the same count and unit merge and their checks add up, in the order of first appearance. One count reads
`checked N units with K check(s)`; two counts both carry the word and are joined by "and"; three or more carry it on the first only,
with commas and "and" before the last. ` K check(s) had nothing to look at.` follows as a sentence of its own (a step with only those
reads `Builder checks: 1 check had nothing to look at.`), and ` Some were skipped (listed above).` follows, with no number, when any
line of the step has `explained` above 0, since the lines of one step can skip the same files. The fold's N is checks across every
line, the ones with nothing to look at included. Neither `data/limits.md` nor the fold of the limits holds them, and a run with none
has no heading and no fold. A unit `uses` is said "program uses" (`1 program use`) on both forms.

### History (the mask of a flagged line)

- 2026-11-01: `hook_where`: a hook's config file, and for a hook whose command is masked, the line to open. Section 1 of `full.md` and
  `details_html` use it.

## review_html

Covers `review_html.py` and `plain.py`.

The page that walks the places to check one at a time, for the reader to mark each Concerned, Not
concerned, or Not sure. Walkdown renders no verdict: the reader makes the call, and the marks are
the reader's own (the "The reports" section, the `marks` section).

Status: built (C21 2026-10-12; C33, C36, C31 part B, C32, C28 since; marks through `marks.py`,
carried from an earlier run, and shared with `details.html`, 2026-10-20).

### Inputs

- `render_page(meta, reports, text_dir=None, text_href=None, marks=None, marks_error=None,
  carried=None, cap_full=None)`: `text_dir` is the run's `data/normalized/text/` (`02.2-reader`'s text,
  the line numbers `02.4-phrases` cites); `text_href` the same folder relative to the page; `marks`,
  `marks_error`, `carried`: from `marks.for_run` (the run's own marks, or an earlier run's and that
  run's name); `cap_full`: `capability.json`, so marks are matched against the same rows as on
  `details.html` (`details_html.mark_rows`).
- `load_marks`: `marks.load`.

### Places

`places(r)`: the places `details_html.first_items` lists, grouped so that one place is one card:

- Every finding on one line is one place, whichever stage found it (`findings_at`). The card
  leads with the first finding, says "and N more findings on this line", tags every stage that
  found something, and lists each finding under its own headline in "What was flagged".
- A sentence repeated across files (`rep.sentence`) is one place listing every location; the
  findings at those locations join it.
- A passage (more than one line) and a place with no line stay alone.
- A model read of a place's line joins its card; a place made only of model reads is a model
  read, walked in its own pass.
- Place ids: a hash of section, headline, location, and quote; a merged place's id comes from its
  members'. A re-render of the same run gives the same ids. Since step 7b the section part is still the
  number the section carried before (`marks.old_stage_part`, from the history table), on purpose: an id is not a
  name for a stage but a handle in the reader's marks.json, which the page's script matches by when a key is
  missing, and which a `walkdown_review: 1` file holds alone. Hashing the stage's name would change every id and
  every link to a card and leave a saved file's ids pointing at nothing (the `marks` section, "Place ids"). Each
  card also carries its lead's
  stable key and every member's (`data-key`, `data-keys`; `marks.place_key`), which marks match, and the
  key each of them had before step 7b (`marks.old_place_key`), so a marks file saved then still matches,
  on the page's script as well. `data-stage` is the name of the card's stage.

### Each card

- Section tags in plain words; "Place k of N" (rule findings) or "Model read k of N"; the
  headline; the location linked to this run's copy of the text (never the original file; no
  "(p=...)" on a model read).
- **To decide:** one line on what the reader is deciding (`DECIDE`), on cards made only of model
  reads and on test-data and image cards.
- **What the model said:** for each model read: who read it, what it read, and the score in one
  sentence; how far to trust it (`MODEL_NOTE`). A verified
  `soft.pinpoint` adds "Where in the passage:", "In plain words:", and up to two "Also close"
  lines, and the text opens on those lines; an unverified pinpoint shows only that its quote was
  not found.
- **What was flagged:** why a place of this kind is listed (`WHY`), each pattern in plain words
  (`plain.describe`) with its id, the item's note (base rate, model reading), every definition of
  a conflicting term.
- **Is it enforced?** on a read-only line (`render.limit_words`, `limit_routes`).
- On a test-data or image card: **Where the AI is pointed at it** (the line that names the file,
  two lines either side) and **The start of the file** (`START_LINES` lines and how many more) or
  **Text read from the image**.
- The text: the flagged line with `CONTEXT` lines either side, numbered, the flagged lines shaded
  and the matched words in `<mark>`, on every line of a wrapped match (`02.4-phrases` `spans`). A
  passage longer than `MAX_SPAN` lines shows its first lines and counts the rest. Without the
  file's text, the quote; without either, nothing. Invisible characters show as `U+XXXX`
  (`_invisible`): every character `Library/invisible.yaml` strips; a character it gives the `run`
  action (a variation selector) only where it stands in a run, which `render_line` finds with
  `library.runs` on the whole line before any cut (the rule every step uses, so one selector after an
  emoji shows as it is, and two or more, or selectors with stripped characters between them, show as
  badges); and every format, control, line-separator, paragraph-separator, and tag character the
  category rules name. A tab shows as it is.
- One closing line on what only running it shows (`RUNTIME`; a prohibition has its own;
  fixed-fact kinds have none).
- Three marks (pressing the chosen one again clears it) and an optional note.

### The page

- Header: links at the top right to `summary.html` and `details.html`; repository, source, pin,
  run; "Walkdown flagged N places" and "a model read M more (experimental)", saying the model
  reads are a separate, optional pass; the three marks with one line each; an index of every
  place with its mark, model reads under their own heading; whether saved marks were loaded and
  how many match nothing in this run, or how many were carried from which run and how many
  earlier marks match nothing in this run.
- **Passes** (C36): Rule findings; Model reads, optional (only when there are any); Not sure,
  again (the places marked Not sure when it is opened, held while they are marked again). Back,
  Next, Next unmarked, and the progress line work within the pass; marking a card or following
  the index to another pass switches to it. The page opens on the first unmarked rule finding,
  or on the card the address names.
- One place at a time, or Show all; keys 1 to 3, arrows, N. Without the script, every card is
  listed and marking is off; print lists every card.
- "When you are done": counts per mark, what is left, the next pass; Download `marks.json`, Copy,
  Load a marks file (matched by key, else by id).
- Marks are kept in the browser as they are made. The page starts from the run's marks, its own
  or carried; a carried mark says "Your mark from run <name>." under the buttons until the
  reader changes it; the download is `walkdown_marks: 2` with stable keys (the `marks` section), and
  it keeps the marks made on `details.html` before report v3 (links, files, trifecta and hidden
  places) as they are.
- Theme tokens for light and dark, phone width.

### plain.py

`PLAIN`: pattern id to plain words, one entry per row of `Library/patterns.yaml`, read from the row's
`plain` field (the words are Library data since restructure step 3b; `plain.py` holds no table),
each saying what the words are and "The worry: ...", never whether the line is a problem.
`describe(patterns)`: (id, words) per id, once each; an id with no entry (a retired pattern in an
old run) says the pattern no longer exists.

### Must never

- Show a score, severity, or verdict, or a mark the reader did not make.
- Emit unescaped artifact text. All artifact text is escaped in Python; the script builds no
  markup from it; JSON embedded in the page cannot close its script tag.
- Show lines around a place in a file where `02.4-phrases` found what looks like a secret; the flagged
  line shows `02.4-phrases`'s mask.
- Read the audited repository; text comes from the run folder.
- Let marks change any finding or any other report; write `marks.json`.

### Done when (tests in `tests/test_review_html.py`, `tests/test_plain.py`)

1. One card per place, rule findings first, model reads after (`test_one_card_per_summary_item_model_reads_last`,
   `test_findings_on_one_line_are_one_card_with_every_finding`,
   `test_a_model_read_of_the_same_line_joins_the_card`,
   `test_a_repeated_sentence_is_one_card_listing_every_place`,
   `test_a_lone_finding_keeps_its_id_and_a_passage_stays_alone`).
2. The text with `CONTEXT` lines, the line marked, matched words in `<mark>`, wrapped matches on
   every line (`test_wrapped_match_is_marked_on_each_line`); without text, the quote.
3. A long passage keeps its location and counts the lines not shown; invisible characters as
   badges, every character the invisible-character list strips or runs among them
   (`test_every_character_the_list_strips_is_shown_as_a_badge_and_a_run_character_where_it_stands_in_a_run`: a
   character the list strips always, a selector only in a run, an emoji and its one selector as they
   are); a card's note says what a
   selector run in its line spells (`test_a_card_says_what_a_selector_run_in_its_line_spells`).
4. Escaping in cards and in the embedded marks; no lines around a secret.
5. Every pattern row has a `plain` field, and `PLAIN` holds exactly those, each with "The worry:" and
   no em-dash; `plain.py` holds no table (`tests/test_plain.py`, `tests/test_library_kinds.py`).
6. Saved marks for places on the page are embedded, others counted; an unreadable file is
   reported and the page still renders; same ids on a re-render.
7. To decide, the pointed-at line and start of file, image text
   (`test_test_data_card_shows_where_and_what`, `test_image_card_shows_its_text`).
8. The runtime line per kind (`test_runtime_line_per_kind_of_card`).
9. Passes, numbering within the pass, the index heading
   (`test_model_reads_are_a_separate_pass_and_not_sure_can_be_walked_again`); the script driven
   in a browser on a real run with no page errors (2026-10-20).
10. No verdict words; each page links the others at the top right.
11. Carried marks shown with their run; stable keys written (`tests/test_marks.py`).

### History

- 2026-10-12: built (C21); places, marks, `marks.json` per run.
- 2026-10-13: model reads in plain words; optional pinpoint.
- 2026-10-16: one card per place (C33).
- 2026-10-18: cards a reader can decide (C36, first half); wrapped lines marked (C37).
- 2026-10-20: runtime line (C31 part B), contradicted read-only places (C32), questioning reads
  (C28), passes and Not sure again (C36); wrapped matches on every line.
- 2026-10-20: owner: marks carry over and are shared with `details.html`. Built the same day
  (`marks.py`, `walkdown_marks: 2`).
- 2026-10-27 (owner, report v3): the only page that makes marks; `summary.html` and `details.html`
  count them and link here.
- 2026-10-29 (P1, after verification): `_invisible` reads `Library/invisible.yaml` (every character it
  strips shows as `U+XXXX`, and a character it gives the `run` action shows only where it stands in a
  run, as in every step) and keeps the category rules, so nothing shown before stops being shown; the
  combining grapheme joiner, the blank letters and cells, and the variation selectors in a run printed
  raw before. One variation selector after an emoji reads as it is. A card's note says what a selector
  run in its quote spells.
- 2026-10-29: restructure step 6 (keep-or-cut, Q8): the cards of a stage 6 label or relational read
  (kinds `label` and `read`), the questioning line, and the question-to-pattern lookup are cut: no
  stage has written those findings since step 5. A rule in the page's style sheet for the questioning
  line stays, unused, so the page is the same bytes.
- 2026-10-29: restructure step 3b: `PLAIN` is read from the `plain` field of each row of
  `Library/patterns.yaml`; `plain.py` holds no table. The words are byte for byte what they were.
- 2026-10-29: restructure step 7b: a card's `data-stage` is the stage's name, not a section number; its label
  comes from the stage's plain name by that name; a model read is a place under an AI stage. The card's
  `data-keys` also holds the old keys of its places (the marks section). The words on the page are the same.

## summary_html

Status: rebuilt 2026-10-27 as report v3, "glance and know" (owner; the `glance` section holds the
eight questions). Before: the builder's page of 2026-10-26 (slice 1), and the page for someone
deciding whether to use a repository of 2026-10-20.

The one page: eight questions, each with a short label and a one-line answer, that someone with no
computer skills can read at a glance. Everything behind each answer is one tap away ("More ›"),
and the rest is on `details.html`, `review.html`, and `full.md`. It also holds the concern rows,
the security headline, and the brief's lines that `walkdown.py` prints, so the page and the
brief count the same way.

### Inputs

`render_page(meta, reports, stamps, notes, runs_ok, marks=None, changes=None) -> str`. `changes`
is `run.changes_for` (its cost line goes under question 2); `marks` the run's marks, own or
carried (the `marks` section). The places come from `details_html.first_items`, the same set
`review.html` walks.

### Output: `summary.html`

1. **Header.** The name; "Checked <day> · version <hash7> · <N> files · License: <name>"
   (`glance.meta_line`); what it is in one sentence (`glance.what_it_is`: "A plugin for Claude
   Code: 9 skills (step-by-step instructions the AI follows for a task) and 7 helpers ..."); and
   "Walkdown reads the files without running anything. It points things out; you decide what
   matters. Tap a line for more."
2. **At a glance**: the eight questions as cards (`glance.card`), in order: switch, memory,
   package, elsewhere, hosts, tools, clean, careful. Each card shows the question, its chip, and
   its answer; "More ›" opens the bullets and, for question 2, the memory table.
3. **A step that did not work**, only then (`not_working(qa)`, `warning`; the steps are the check of the run's gaps, in
   its order, `render.NAMED`:
   the six that have a section, and the builder step `02.6-builder`, "Builder checks", between
   `02.5-capability` and `03-sweep`, since restructure step 4 round 2): "Not every step worked in
   this run.", each such step by its plain name with "did not run" (no output), "did not pass its
   fixture check (FAIL)"; that a step that did not work can
   miss places, so this page may show fewer than there are (left out when the only step that did not work is a model
   read, which adds no place this page counts: `only_model_reads`, `warning(..., model_only=)`); and a link to "What
   Walkdown didn't check" on `details.html`. A step with nothing in this repository to test, and a fixture check
   that did not run because an optional tool is not installed (INCOMPLETE, any stage), never reach
   this page (owner, 2026-10-25); `details.html` and `full.md` list both. A run made without
   validation has no stamps and gets no line for them. A model read in which no passage got an answer, even after the
   retry (`render.model_read_nothing`), is such a step too: "<plain> got no answer for any passage" (M9). A read with
   some passages answered is not.
   **The model read's count** (`model_note`, M9), only when a model read has some passages that got no answer (a read
   that got none for any passage is in the headline and the warning already, and has no count line here) or a chosen
   step was not started: one line under the cards and above the warning, `<plain>: N of M passages got no answer, after
   one retry.` (`render.model_read_lines`; the retry is said only of passages that were sent: `5 of 12 passages got no
   answer, after one retry`, `12 of 12 passages got no answer; none was sent`, `5 of 12 passages got no answer, after
   one retry; 3 of them were not sent`; a run made before the retry says neither), and for a chosen step that was not
   started (the record's `not_started`) `The step "The line behind each flag" did not run: the step "Needs a human read"
   got no answer for any passage, so there was nothing to pinpoint.`
4. **Footer**: links to `details.html`, `review.html` ("go through each place and mark it"), and
   `full.md`; then the page's one qualifier (`FOOTER`): "Walkdown reads a repository's files
   without running anything. It points out what it finds and leaves the judgment to you. Finding
   nothing does not mean a repository is safe."

Marking is on `review.html` only (owner, 2026-10-27); question 8 says how many places are marked.

### The concern rows (`CONCERNS`, `rows`)

One row per concern kind that has a place, in this fixed order; each place falls in the first row
that fits:

1. **Hidden text that reads like an instruction** (kind `hidden+phrase`).
2. **Hidden characters that spell out text** (kind `hidden+spelled`; `details_html._spelled_places`). A row of
   its own: nothing checked that the text reads like an instruction, and it is more than wording. It names
   the first place and quotes nothing.
3. **Runs code**: hooks, commands run at load, commands the person is asked to run
   (`details_html.action_group` = `runs`).
4. **Looks like a committed secret** (kind `secret`; test data and likely-not-secrets already left
   out).
5. **Reads secrets, calls out, or shares** (`action_group` = `out`).
6. **Lasting changes or permissions** (`action_group` = `lasting`; includes read-only lines a tools
   list contradicts).

The rest is wording only (`action_group` = `words`). A row holds each place once: findings that
`review.html` shows as one card (one line named by several) count once, and a row's `ids` are its
places' review cards. `total(rows)` counts every place once across the rows (a place may be in two);
`wording_count` counts the wording-only places once, leaving out any a row holds. A row's
`not_concerned` counts the places the reader marked Not concerned, and its `example` is the first
place (stage, file, line) not so marked. Model reads are never concerns.

### The security headline (`headline`), for the brief

- With concerns: "Walkdown found security concerns in this repository: <N> places, of <K> kinds."
  (`total`), with "(<M> of them marked Not concerned.)" when the reader marked some.
- With none: "Walkdown found none of the security concerns it looks for."
- When a step produced no output (`not_run(qa)`), never "found none": 'This run did not complete: the
  step "<name>" did not run' (or '<n> steps did not run, starting with "<name>"'), then "so Walkdown
  cannot say whether this repository has the security concerns it looks for." or, with concerns
  from the steps that ran, "In the steps that ran, Walkdown found security concerns: ..."
  (2026-10-21, an outside tester: an empty .venv crashed `02.1-inventory` and the page read as clean).
- With none and a step that failed its fixture check (`failed_checks(qa)`), never plain "found none":
  "..., but not every step worked, so it may have missed some." (owner, 2026-10-25, review C40).
- A model read that did not work (`model_down`: a chosen read that left no output, or one that ran and got no answer for
  any passage even after the retry; M9, restructure M14 b) does not make the headline say Walkdown cannot say: a model
  read adds no security concern. `headline(..., model=, incomplete=)` adds to the usual line "The coded checks are
  complete; the model read did not work." With a coded step that failed its fixture check it adds only "The model read
  did not work.", since the coded checks are not complete. With a coded step INCOMPLETE (a check skipped for a missing
  tool, `incomplete_checks`) the checks are not "complete" either, so it adds 'The coded checks ran, and "What Walkdown
  didn't check" names any skipped for a missing tool; the model read did not work.' (`model_down_sentence`).
  `not_run(qa)` names the coded steps alone (`ai=True` adds a chosen read that left no output), and `headline` is given
  those as `missing`.
  A coded step that did not run keeps its "did not complete" line.
- A run that stopped as asked before its last coded step (`headline(..., stop=meta["stop"])`, O3; a coded step the
  stop left out is not "missing"): 'This run stopped after the step "<plain>", as asked, so Walkdown cannot say whether
  this repository has the security concerns it looks for.', or, with concerns from the steps that ran, 'This run stopped
  after the step "<plain>", as asked. In the steps that ran, Walkdown found security concerns: ...'. A step that did
  fail still gets the "did not complete" form, which comes first. `not_run`, `not_working`, and `failed_steps` take the
  same `stop` and leave out of their lists a step it left out, so "Not every step worked" lists failures only.

Question 8 on the page says the same things in its own templates (the `glance` section).

### The brief's lines

`brief_trigger_line`, `brief_cost_lines`, `brief_needs_line`, `brief_ready_line`, `brief_fit_line`,
`brief_clean_line`: counts only, no repository text but package names; `None` when the run did not
make the check. `TOGETHER` (what the three boxes mean together) and `WORDING` are the brief's too.

### The line for a model read a stop held back (O3)

`stop_note(stop)`: under the cards and above the warning, one line when the run stopped just before a model read:
`The run stopped after "<plain>", as asked; what "<AI plain>" would send is in data/<file>; nothing was sent.`
(`render.stop_input_line`: Walkdown's words and its own path). `details.html` has the same line in "What Walkdown didn't
check". Any other run has none.

### Must never

- Say "do not use", call the repository safe or unsafe, or give a score, grade, or rank.
- Choose concerns by anything but the fixed kinds and order above.
- Show a secret's value, or open, fetch, or check a link.
- Emit unescaped repository text.

### Done when (tests in `tests/test_summary_html.py`)

1. The page: eight questions in order, title, footer links and qualifier
   (`test_eight_questions_in_order_title_and_footer`).
2. Rows in the fixed order, each place once (`test_rows_in_fixed_order_each_place_once`,
   `test_a_place_counts_once_as_review_html_counts_it`); marks counted and skipped for the example
   (`test_marks_are_counted_and_skip_the_example`); model reads never concerns
   (`test_model_reads_are_never_concerns`).
3. The headline and question 8 never read as clean when a step did not run or failed
   (`test_a_failed_check_never_reads_as_clean`, `test_a_run_missing_a_step_never_reads_as_clean`).
4. A step that did not work is named at the bottom; an INCOMPLETE stamp is not
   (`test_a_step_that_did_not_work_is_named_at_the_bottom`). The builder step counts like the
   others: not run, or failed its fixture check, it is named in the headline's "steps did not run"
   and in the warning, and a PASS says nothing (`test_a_builder_step_that_did_not_run_is_named`,
   `test_a_builder_step_that_failed_its_fixture_check_is_named`).
5. The brief's lines (in the question tests: `test_switch_question_comes_first`,
   `test_memory_question_one_table_and_the_since_line`, `test_elsewhere_question`,
   `test_hosts_question`, `test_tools_question`, `test_clean_question`).
6. No verdict words; repository text escaped (`test_no_verdict_words_and_escaping`). Checked by eye
   on an audited plugin's run (2026-10-27).
7. A model read in which no passage got an answer is a step that did not work, and a partial read, or one that asked
   about no passage, is not
   (`test_a_model_read_in_which_no_passage_got_an_answer_is_a_step_that_did_not_work`,
   `test_a_partial_read_is_a_read_that_worked_and_a_read_that_asked_nothing_is_too`); the headline and question 8 say the
   coded checks are complete and the model read did not work (the headline has no "cannot say" line for a model read)
   (`test_the_headline_says_the_coded_checks_are_complete_and_the_model_read_did_not_work`,
   `test_the_careful_answer_says_the_same_and_does_not_read_as_not_checked`); a skipped check for a missing tool is
   worded truly (`test_the_coded_checks_are_complete_only_when_none_was_skipped_for_a_missing_tool`); one line gives the
   count of a partial read, and says what was sent (`test_one_line_under_the_cards_gives_the_count_of_passages_with_no_answer`, `test_the_count_says_what_was_sent`);
   a step that was not started has its line (`test_a_step_that_was_not_started_is_one_line_with_its_cause`); a read
   that got no answer for any passage has no count line (`test_a_read_that_got_no_answer_for_any_passage_is_not_counted_again_under_the_cards`);
   the warning does not say places are missed when only a model read did not work
   (`test_the_warning_does_not_say_places_are_missed_when_only_a_model_read_did_not_work`).

### History

- 2026-09-29: first summary (text, `summary.md`).
- 2026-10-07: HTML summary page (report v1).
- 2026-10-16: report v2, the long page in the owner's order (now the `details_html` section).
- 2026-10-20: owner: two readers, two pages. This spec becomes the one page; the long page moves
  to `details.html`. No verdict, "security concerns" allowed. Built the same day. Then the "Not
  checked" section and the headline's count of checks that did not run were removed, and a
  warning under the headline names a step that did not work (owner). Then fewer caveats (owner,
  on the first run with no concerns): "it looks for" in the headline, no "nothing found" line
  there, "Nothing to point out here." and no ledes on empty sections, no "no verdict and no score"
  sentence, and a plain footer as the page's one qualifier. 2026-10-21 (owner, after a fresh
  install showed the warning on every run without the optional tools): the warning moved to the
  bottom, and an INCOMPLETE stage 2 counts only when the missing tool reads files the repository
  has. Under the three boxes, what they mean
  together, and no lede above them (owner).
- 2026-10-26 (owner, plan for builders, slice 1): rebuilt as the builder's page: what it costs,
  what you ship, is it safe; Questions before use moved to `details.html`.
- 2026-10-25 (owner, after an outside tester's report, review C40): what reaches this page is a
  step that did not run or a step that ran and failed its fixture check; with no concerns, a
  failed check changes the headline. A step with nothing to test and a check skipped for a
  missing optional tool stay in `details.html` and `full.md` (this ends the 2026-10-21 stage 2
  line, "skipped part of this repository", and with it the "pDF" and "hTML" in that line).
- 2026-10-27 (owner, report v3): rebuilt as eight questions at a glance (`glance.py`): tokens in one
  place, plain words for a reader with no computer skills, charts, "What you ship" as one bar of how
  the files are used. The old blocks (trigger, cost, ship, elsewhere, ready, fit, clean, concerns,
  can) are gone; the concern rows, headline, warning, and brief lines stay here. Recount the same
  day: a place counts once in the rows and the headline, as on `review.html`.
- 2026-10-30: M9 slice C: `failed_checks` also names a step with a coverage gap (once), and `not_working_pairs` words the three
  coverage gaps as clauses (`common_lines.coverage_page_words`), so a coverage gap is among the steps that did not work and the
  headline does not say "found none" without saying so.
- 2026-10-31: M9 slice C, last fix round: the fold of `details.html` is one line for each step in the form the owner chose
  (`checked_steps`; it was one line for each pass, `checked_line_counts`, which is gone), and its number counts checks. A unit `uses`
  is said "program uses". Left as it is: an ID that is unknown or named twice reads "reported counts that do not add up" in the summary's
  warning, since only a tampered file reaches it.
- 2026-10-31: M9 slice C, fix round: what a check that found nothing looked at is `qa.checked` and no limit. `data/limits.md` and the
  fold of the limits are what they were; `full.md` has `### Checks that found nothing` at the end of section 7 and `details.html` the
  fold `Checks that found nothing (N)` after the limits fold, with counts and no check ids.
  Left as it is: several coverage gaps on one step repeat the step's name in the warning (`What this touches reported counts that do not
  add up; What this touches reported counts that do not add up`), the way several steps that did not work are listed.
- 2026-10-30: M9 slice B: `not_run`, `model_down`, `failed_checks`, `incomplete_checks`, `not_working`,
  `not_working_pairs`, `only_model_reads`, and `model_note` take the check of the run (`qa`) and read its gaps and limits;
  `failed_steps` and `results` are gone (`not_working` is the one list). A fixture check that did not pass is a gap
  whatever its word, so intake's and the check's own are named too. A gap of a kind the page does not know is worded
  `<plain>: <found>`.
- 2026-10-29: restructure step 5, round 2: `not_run`, `not_working`, and `failed_steps` take the reports, so a chosen AI step that failed (a key with no report) is named like the builder; a step nobody chose is never named. The plain name of Pinpoint is "The line behind each flag".
- 2026-10-29: restructure step 7b: places are ordered by their stage's place in the stage list
  (`stagelist.position`), then file and line, as they were by section number; the page is the same.
- 2026-10-30: M9 slice A: a model read in which no passage got an answer is a step that did not work; the headline and
  question 8 say the coded checks are complete and the model read did not work (a model read that failed used to make
  the headline say it could not say, restructure M14 b); `model_note` is one line with the count of passages that got no
  answer, after one retry. `not_run(runs_ok, None, stop)` names the coded steps alone.
- 2026-10-31: M1 slice A: `render.tokens_line` (the token line, in section 6 and the brief), `brief.fixture_line` (the fixture line), a read with no probability in `sweep_split`, `_s6`, `_f6`, `details_html.first_items`, and `review_html._model_said` (through `stages/_shared/probability.py`: two of them formatted `x['p_any']` and would have crashed), and the backend and model of a backend row are flattened and cut before a page shows them. `render.NO_MODEL_READ` is unchanged: a default run's pages are the same.
- 2026-10-31: M1 slice A, fix round: the token line says `(from 5 of 9 calls)` after a total that only some of the calls reported, for a read and for the fixture check (`usage.words`); nine calls of which five reported printed `Sweep 500 in, 15 out`, which reads as complete. A saved `usage` with a `reported` above its `calls`, or a count above 10^15, is an output that cannot be read.
- 2026-10-31: M1 slice A, fix round: section 6's status line says `this model gives no probability` without the band whenever the read's backend gives none (`probability.gives`), with rows or without. A text model that got no answer for any passage was told `0 flagged at p >= 0.6`.
- 2026-10-31: M1 slice A, fix round: the backend is flattened and cut where the details page writes it (`Read by <backend> as telling the reader to:`, a clear place and a near one) and in the log header's line for a stop (`prepared.backend`). They wrote it as it came.
- 2026-10-31: M1 slice A, fix round 2: the model name in the fixture line and in the waiting line of a stopped run is cut at `MODEL_CAP`; it was one line and uncut (the command to go on keeps the option as typed). Test: `test_tokens_line.py::test_the_model_name_in_the_line_is_cut_at_the_cap`.
- 2026-10-31: M1 slice A, fix round 3: the command to go on, and the line above it, print a backend the record kept only if it is a model option (`common_lines.record_option`); a value changed by hand in `data/run.json` is left out, with one sentence. It printed whatever the record held, flattened.
- 2026-11-03 (owner): `K.prompt-leak`, `L.never-refuse`, `L.no-disclaimer`, and `E.decode-exec` join `POINT_PATTERNS`: none hit in
  seven ordinary repositories (three skill collections, four MCP servers), as the rows already there. `E.tls-off` and
  `E.registry-config` hit in them (a `curl -k` to localhost, the public npm registry) and stay in `full.md`, as `E.mcp` does.
  `FAMILY` gives `K.prompt-leak` and `E.decode-exec` headlines of their own, and `PATTERN_GROUP` files `E.decode-exec` under
  runs code, though its check, `phrase.E.perms`, reads as a lasting change
  (`tests/test_details_html.py::test_the_four_rows_from_skillspector_are_places_and_decoding_code_runs_code`).
- 2026-11-03: `context` on a place (`_item`): what hidden characters spell, what base64 decodes to, and, new, that a line of
  code is an MCP description the AI reads (`TOOL_TEXT_NOTE`). It is its own line on a review card, so the base-rate lead no longer
  runs into it, and `details.html` shows it for phrase places too. `full.md`'s phrase hit says `(model, sent to the AI by an MCP
  server)` for a `tool_text` hit (it said `in an MCP description` until prompt and reply text were read, the same day) (`tests/test_details_html.py::test_what_is_said_of_the_line_is_its_own_line_and_a_lead_never_runs_into_it`,
  `tests/test_review_html.py::test_what_is_said_of_a_line_is_its_own_line_on_the_card_before_the_lead`).
- 2026-11-01: `hidden+spelled`: a hidden place whose characters spell text and that has no phrase hit is a place of its own (a row here, a card on `review.html`), and `details.html`'s list of every hidden place says what each one's characters spell (`spelled_note`). Until now only a line with a phrase hit said it on these two pages, and `full.md` alone said it for the rest. A default run with no such line has the same pages.
