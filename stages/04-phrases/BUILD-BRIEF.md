# Build brief: stage 4 (phrases)

Hand this to a session that has **not** read `Fixtures/ANSWERS/`. It is the
whole starting context.

## Task

Build stage 4 v1 of Walkdown in `stages/04-phrases/`: the pattern engine and the
14 phrase checks, so that the grader reports PASS for stage 4, and every script
has a spec and tests.

## Read, in order

1. `CLAUDE.md` (project map, build rules)
2. `stages/04-phrases/CONTEXT.md` (this stage's contract: scope, pattern table, checks, findings, done-when)
3. `stages/CONTRACT.md` (the JSON report format and check IDs)
4. `pre-planning/PHRASES.md` (all of it: the pattern sets and base rates)
5. `pre-planning/THREATS.md` classes 1, 2, 3, 5, 7, 13 to 17, 19 to 22, and "Extensions to classes 1-12"; `pre-planning/METHOD.md` Stage 4; `pre-planning/RED-TEAM.md` (skim: how patterns get beaten)
6. `stages/02-reader/specs/fold.SPEC.md` (the fold stage 4 reimplements; do not import it)
7. `stages/03-graph/` (the most recent finished stage: follow its structure and SPEC style)
8. `Fixtures/04-phrases/` (the test inputs; fine to look at)

## Never open

- `Fixtures/ANSWERS/` (the answer sheet). Exclude it from every search. Prove the
  stage only through the grader's default output, which names misses without
  revealing expected values. Do not run the grader with `--explain`. Do not run
  any stage on the project root (it would read the answer files).

## How to write the patterns

- Start from PHRASES and THREATS, row by row, into `patterns.yaml`, each row
  citing its source. Run the grader only after the table is written from the
  docs.
- A missed gate means the pattern does not cover the class as THREATS describes
  it. Widen it to the class and cite the bullet. Never write a pattern that only
  matches one fixture sentence's wording.
- A hit on a negative means the pattern is broader than the class. Narrow it, or
  add an `unless` with a stated reason.
- Recall rows are measured, not targets. Report the recall; do not chase it.
- List every pattern you added beyond PHRASES (with its THREATS source) in your
  final report, so they can be folded back into PHRASES.

## Environment

- Use the existing project virtualenv: `.venv/Scripts/python`. Install nothing
  new. If you think you need another package, stop and say why.
- Never point pytest or any stage at `ReposToExamine/` except the one read-only
  stage 4 run named in Done. Run tests as `.venv/Scripts/python -m pytest stages -q`.
- Prefer the Write and Edit tools over shell heredocs for files with
  backslashes (regexes); heredocs have collapsed `\\` before.

## Build rules

- Every script: `specs/<name>.SPEC.md` (inputs, outputs, must-never,
  Done-when) and `tests/test_<name>.py` written from the spec **before** the
  code. Tests use their own tiny inline inputs, not the fixtures.
- `run.py` is the single entry point; it prints one contract-1 report to stdout
  and supports `--out <dir>`.
- Do not edit `Fixtures/`, `grader/`, `stages/CONTRACT.md`, `pre-planning/`, or
  stages 1 to 3. If the contract, CONTEXT.md, or a fixture looks wrong, stop and
  write the problem down for the user instead of working around it.
- No em-dashes in docs. No Claude attribution in commits.

## Done

- `.venv/Scripts/python -m pytest stages -q` passes (stages 1 to 4).
- `.venv/Scripts/python grader/grader.py 04` → PASS.
- Run on `ReposToExamine/superpowers-main/superpowers-main/` completes. Report
  hits per check and per pattern, beside the PHRASES base rate where one exists.
- Commit on a branch `stage-04-phrases` (made from `main`); do not merge or push.
  Report what was built, the full grader output (including recall), the
  superpowers counts, the patterns added beyond PHRASES, any problems found, and
  confirm you never opened `Fixtures/ANSWERS/`.
