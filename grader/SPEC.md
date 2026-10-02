# grader.py: spec

Runs a stage against its fixtures and scores the result against the answer
sheet. The only component in Walkdown that reads `Fixtures/ANSWERS/`.

## Inputs

- A stage selector: `01`, `01-inventory`, or `all`.
- `Fixtures/<stage>/`: the fixture inputs.
- `Fixtures/ANSWERS/<stage>.json`: the answers (format in `Fixtures/ANSWERS/README.md`).
- `stages/<stage>/run.py`: the stage runner (contract in `stages/CONTRACT.md`).
- `--root <dir>`: project root. Default: the folder above `grader/`.

## Commands

```
python grader/grader.py <stage|all>            grade (default output)
python grader/grader.py <stage|all> --explain  also print expected values and notes on misses
python grader/grader.py <stage|all> --json     machine-readable result on stdout
python grader/grader.py --check-answers        validate answers + fixture hashes; run no stage
python grader/grader.py --rehash <stage>       rewrite fixture hashes after a deliberate change
```

## Behavior

1. Load the stage's answers. Stop with a setup error if the file is missing or
   malformed (unknown polarity, unknown match operator, missing check).
2. For each case, verify fixture hashes: every file under `Fixtures/<stage>/<root>`
   must be listed with a matching sha256, and every listed file must exist. Any
   difference is a setup error naming each file (**stale answers**). This check
   runs before any stage code.
3. If `stages/<stage>/run.py` does not exist, the stage is **NOT BUILT**.
4. Run the runner once per case: `python run.py <case root>`, 300 s timeout, and
   parse stdout as a contract-1 report. A non-zero exit, timeout, or invalid JSON
   is a stage error and the stage **FAILS**.
5. Score each expectation against the case's findings:
   - A finding **matches** an expectation when `check` is equal, `file` is equal
     if the expectation has one, `line` is equal if it has one, and every
     `match` condition holds.
   - A skip finding (has `skipped`) for the same check and file marks the
     expectation **SKIPPED** instead of scoring it.
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

For `all`, the exit code is the highest of the stages graded. Recall never
affects the result.

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
4. Missed recall rows are reported as a percentage and the stage still PASSES.
5. A missing `run.py` grades NOT BUILT, exit 3.
6. A changed, added, or removed fixture file is a SETUP ERROR, exit 4, before any stage runs.
7. A skip on a gate row grades INCOMPLETE, exit 2.
8. Match operators `eq`, `contains` (case-insensitive), `same_items`, `includes`, `excludes`, and `count` behave as specified.
9. Default output contains no match values or notes; `--explain` shows them.
10. A runner that exits non-zero or prints invalid JSON grades FAIL.
11. `--rehash` rewrites hashes so a changed fixture grades again.
12. Deferred rows are listed and not scored.
13. `--check-answers` passes on the real `Fixtures/ANSWERS/` (every fixture hashed, every expectation well-formed).
