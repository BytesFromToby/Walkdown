# grader.py: spec

Runs a stage against its fixtures and scores the result against the answer
sheet. The only component in Walkdown that reads `Fixtures/ANSWERS/`.

## Inputs

- A stage selector: `02.1`, `02.1-inventory`, or `all`.
- `Fixtures/<stage>/`: the fixture inputs.
- `Fixtures/ANSWERS/<stage>.json`: the answers (format in `Fixtures/ANSWERS/README.md`).
- `stages/<folder>/run.py`: the stage runner (contract in `stages/CONTRACT.md`); the stage's
  folder comes from `stages/stages.json`: its `stages`, and the check of the run under `qa` (M9 slice B), which is not a
  step a run chooses but has fixtures and is graded like one.
- `--root <dir>`: project root. Default: two folders above this script (`tools/grader/`).

## Commands

```
python tools/grader/grader.py <stage|all>            grade (default output)
python tools/grader/grader.py <stage|all> --explain  also print expected values and notes on misses
python tools/grader/grader.py <stage|all> --json     machine-readable result on stdout
python tools/grader/grader.py --check-answers        validate answers + fixture hashes; run no stage
python tools/grader/grader.py --rehash <stage>       rewrite fixture hashes after a deliberate change
```

## Behavior

1. Load the stage's answers. Stop with a setup error if the file is missing or
   malformed (unknown polarity, unknown match operator, missing check), or if its `"stage"` is not
   the stage its file name says.
2. For each case, verify fixture hashes: every file under `Fixtures/<stage>/<root>`
   must be listed with a matching sha256, and every listed file must exist. Any
   difference is a setup error naming each file (**stale answers**). This check
   runs before any stage code.
3. If the stage is not listed in `stages/stages.json`, or its `run.py` does not exist, the
   stage is **NOT BUILT**.
4. Run the runner once per case: `python run.py <case root>`, 300 s timeout (1,800 s for a stage a person chooses to read with a
   model, an entry of `stages/stages.json` with an `option`: it makes a call for each passage, each allowed 300 s), and
   parse stdout as a contract-1 report. A non-zero exit, timeout, or invalid JSON
   is a stage error and the stage **FAILS**.
5. Score each expectation against the case's findings:
   - A finding **matches** an expectation when `check` is equal, `file` is equal
     if the expectation has one, `line` is equal if it has one, and every
     `match` condition holds.
   - A skip finding (has `skipped`) for the same check and file marks the
     expectation **SKIPPED** instead of scoring it. A skip that names a `carrier` (`02.2-reader`'s
     PDF page OCR, 2026-10-18) marks only the rows whose `match` names that carrier with
     `eq`; the file's other rows for the check are still scored.
   - The negative line's false-positive count is the rows that hit, never the skipped ones.
   - `gate`: passes when at least one finding matches (exactly `count` when
     given). Otherwise a miss.
   - `negative`: passes when no finding matches. Otherwise a false positive.
   - `recall`: counted, reported as found / total.
6. Report findings no expectation touched as **unlisted**, counted per check.
   Informational only; they do not affect the result.
7. List every `deferred` entry as deferred. Never scored.

## Result per stage

| Result | When | Exit code |
|---|---|---|
| PASS | every gate passed and every negative passed, no skips on gate or negative rows | 0 |
| FAIL | any gate missed, any negative hit, or a stage error | 1 |
| INCOMPLETE | no failures, but a gate or negative row was skipped | 2 |
| NOT BUILT | no `run.py` for the stage | 3 |
| SETUP ERROR | answers missing or malformed, or stale fixture hashes | 4 |
| no fixture set | the stage is listed in `stages/stages.json` and has no answer sheet and no `Fixtures/<stage>/` folder (an AI stage without a fixture set; restructure step 5, decision 5-C) | 0 |

For `all`, the exit code is the highest of the stages graded. Recall never
affects the result.

A stage with **no fixture set** is not run and not stamped as a pass or a fail: the grader prints
`== <stage>: no fixture set`, `--json` gives `"result": "no fixture set"` with zero rows, and a
run's `LOG.md` shows `no fixture set` in its validation column. It is not an error and not a step
that did not work. A stage with fixtures but no answer sheet is still a SETUP ERROR, and a stage
named on the command line that is neither listed nor has a sheet is still an unknown stage.
`--check-answers` and `--rehash` look only at answer sheets.

## Must never

- Modify anything under `Fixtures/` except the `fixtures` hash maps, and only
  under `--rehash`.
- Print expected values (match conditions) or notes without `--explain`. The
  default output names the expectation id, check, file, line, and polarity only,
  so a blind build session can run the grader without reading the answers.
- Treat a skip, a stage error, or a missing stage as a pass.
- Let recall affect the result.
- Grade against stale fixtures (hash mismatch).

## Done when (each backed by a test in `tests/test_grader.py`)

1. A stage that emits exactly the expected findings grades PASS, exit 0.
2. A missed gate grades FAIL, exit 1, and names the expectation id.
3. A finding on a negative grades FAIL and counts as a false positive.
4. Missed recall rows are reported as a percentage and the stage still PASSES. When every recall row was
   skipped (no model answered), the line says `recall    not measured: all <n> rows were skipped` and prints
   no percentage (`test_a_recall_line_says_not_measured_when_every_row_was_skipped`); `--json` is unchanged.
5. A missing `run.py` grades NOT BUILT, exit 3.
6. A changed, added, or removed fixture file is a SETUP ERROR, exit 4, before any stage runs.
7. A skip on a gate row grades INCOMPLETE, exit 2.
8. Match operators `eq`, `contains` (case-insensitive), `same_items`, `includes`, `excludes`, and `count` behave as specified.
9. Default output contains no match values or notes; `--explain` shows them.
10. A runner that exits non-zero or prints invalid JSON grades FAIL.
11. `--rehash` rewrites hashes so a changed fixture grades again.
12. Deferred rows are listed and not scored.
13. `--check-answers` passes on the real `Fixtures/ANSWERS/` (every fixture hashed, every expectation well-formed).
14. A listed stage with no sheet and no fixtures grades "no fixture set", exit 0, and `all` names it beside
    the graded stages (`test_a_listed_stage_with_no_sheet_and_no_fixtures_grades_no_fixture_set`,
    `test_all_grades_the_stages_with_sheets_and_names_the_one_with_none`); fixtures without a sheet
    stay a SETUP ERROR (`test_fixtures_without_a_sheet_is_still_a_setup_error`); an unlisted stage with
    no sheet is still unknown (`test_a_stage_not_listed_with_no_sheet_is_still_an_unknown_stage`);
    `--check-answers` and `--rehash` ignore it (`test_check_answers_and_rehash_leave_the_stage_with_no_sheet_alone`).
15. A sheet whose `"stage"` names another stage is a SETUP ERROR, exit 4
    (`test_a_sheet_whose_stage_field_names_another_stage_is_a_setup_error`).
16. The check of the run, listed under `qa` in `stages/stages.json` and not in `stages`, is found and graded; listed
    nowhere it is NOT BUILT, and the `report` entry is not graded
    (`test_the_check_of_the_run_is_graded_through_the_qa_entry_of_the_stage_list`).

17. A stage's `usage` block (`stages/CONTRACT.md`, "Tokens") is added up over the cases and printed under `usage` in `--json`
    (not in the text output); a block that is not an object of whole counts adds nothing; a stage that sent nothing has none
    (`test_a_stages_usage_is_summed_and_printed_in_the_json_and_not_otherwise`, `test_the_usage_of_every_case_is_added_up`,
    `test_a_usage_that_is_not_counts_of_whole_numbers_adds_nothing_and_no_traceback`, which includes a count above 10^15).
18. A model read may take longer than a coded step, and a coded step may not
    (`test_a_model_read_may_take_longer_than_a_coded_step_and_a_coded_step_may_not`).

## History

- 2026-10-29: restructure step 7: moved from `grader/` to `tools/grader/` (Q13); the default root is two folders above
  the script; a recall line with every row skipped says so instead of printing 0% as measured (notes M14 c).
- 2026-10-29 (after the restructure, notes M7): a sheet's `"stage"` field is checked against its file name.
- 2026-10-30: M9 slice B: `graded_entries` reads the `qa` entry of the stage list beside `stages`, so `05-qa` is found
  (`runner_path`) and named (`listed_names`). Its fixtures are run folders: the grader runs
  `python stages/05-qa/run.py <case root>` on each as it runs any stage.
- 2026-10-31: M1 slice A: `--json` carries a stage's `usage` (what its fixture check spent, for the stamp: `stages/_shared/specs/shared.SPEC.md`, `validate`), and a stage that makes model calls has 1,800 s a case.
- 2026-10-31: M1 slice A, fix round: the grader sums `reported` with the other counts of a `usage` block, and a count above 10^15 is no count (its block adds nothing).
