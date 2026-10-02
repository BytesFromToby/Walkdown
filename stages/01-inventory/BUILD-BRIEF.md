# Build brief: stage 1 (inventory)

Hand this to a session that has **not** read `Fixtures/ANSWERS/`. It is the
whole starting context.

## Task

Build stage 1 of Walkdown in `stages/01-inventory/`, so that
`python grader/grader.py 01` reports PASS and every script has a spec and tests.

## Read, in order

1. `CLAUDE.md` (project map, build rules)
2. `stages/01-inventory/CONTEXT.md` (this stage's contract: checks, flags, definitions, done-when)
3. `stages/CONTRACT.md` (the JSON report format and check IDs)
4. `pre-planning/METHOD.md` Stage 1, `pre-planning/REPORTING.md` Section 1, `pre-planning/TOOLING.md` Stage 1
5. `Fixtures/01-inventory/` (the test inputs; fine to look at)

## Never open

- `Fixtures/ANSWERS/` (the answer sheet). Prove the stage only through the
  grader's default output, which names misses without revealing expected values.
  Do not run the grader with `--explain`.

## Build rules

- Python 3, pytest. Core dependencies pip-installable only (TOOLING "Usable by
  everyone"). `python-magic` needs libmagic, so fall back to `filetype`.
- Every script: `specs/<name>.SPEC.md` (inputs, outputs, must-never,
  Done-when) and `tests/test_<name>.py` written from the spec **before** the
  code. Tests use their own tiny inline inputs, not the fixtures.
- `run.py` is the single entry point; it prints one contract-1 report to stdout.
- Do not edit `Fixtures/`, `grader/`, or `stages/CONTRACT.md`. If the contract
  or a fixture looks wrong, stop and write the problem down for the user.
- No em-dashes in docs. No Claude attribution in commits.

## Done

- Spec tests pass: `python -m pytest stages/01-inventory -q`
- `python grader/grader.py 01` → PASS
- Run on `ReposToExamine/superpowers-main/superpowers-main/` completes; compare its
  composition with REPORTING section 1 and note any difference.
- Commit on a branch `stage-01-inventory`; report what was built and what the
  grader said.
