# Build brief: stage 2 (reader)

Hand this to a session that has **not** read `Fixtures/ANSWERS/`. It is the
whole starting context.

## Task

Build stage 2 of Walkdown in `stages/02-reader/`, so that the grader reports
PASS for stage 2 (or INCOMPLETE only because Tesseract is absent), and every
script has a spec and tests.

## Read, in order

1. `CLAUDE.md` (project map, build rules)
2. `stages/02-reader/CONTEXT.md` (this stage's contract: readings per format, checks, dependencies, done-when)
3. `stages/CONTRACT.md` (the JSON report format and check IDs)
4. `pre-planning/METHOD.md` Stage 2 and "Note on the reader"; `pre-planning/THREATS.md` classes 4, 6, 11; `pre-planning/REPORTING.md` Section 2; `pre-planning/TOOLING.md` Stage 2
5. `stages/01-inventory/` (a finished stage: follow its structure and SPEC style; reuse nothing by import, stages stay independent)
6. `Fixtures/02-reader/` (the test inputs; fine to look at)

## Never open

- `Fixtures/ANSWERS/` (the answer sheet). Exclude it from every search. Prove the
  stage only through the grader's default output, which names misses without
  revealing expected values. Do not run the grader with `--explain`. Do not run
  any stage on the project root (it would read the answer files).

## Environment

- Create the project virtualenv if it does not exist: `python -m venv .venv`,
  then `.venv/Scripts/python -m pip install -r requirements.txt`. Install only
  what `requirements.txt` lists. Nothing global, no optional tools.
- Pin the installed versions of the packages this stage uses into
  `requirements.txt` (`name==version`).
- Run everything with `.venv/Scripts/python`, including the grader and stage 1's
  tests (confirm they still pass in the venv).

## Build rules

- Every script: `specs/<name>.SPEC.md` (inputs, outputs, must-never,
  Done-when) and `tests/test_<name>.py` written from the spec **before** the
  code. Tests use their own tiny inline inputs (build small HTML, SVG, PDF, DOCX
  in the test), not the fixtures.
- `run.py` is the single entry point; it prints one contract-1 report to stdout
  and supports `--out <dir>` for the normalized text.
- Optional tools are optional: detect them, and when absent emit skips and say so
  on stderr.
- Do not edit `Fixtures/`, `grader/`, or `stages/CONTRACT.md`. If the contract,
  CONTEXT.md, or a fixture looks wrong, stop and write the problem down for the
  user instead of working around it.
- No em-dashes in docs. No Claude attribution in commits.

## Done

- `.venv/Scripts/python -m pytest stages -q` passes (stage 1 and stage 2).
- `.venv/Scripts/python grader/grader.py 02` → PASS, or INCOMPLETE where every
  skip is a check that needs Tesseract.
- Run on `ReposToExamine/superpowers-main/superpowers-main/` completes. Compare
  its count of HTML comments in markdown files with Case 001 (71 across 94
  markdown files) and note any difference.
- Commit on a branch `stage-02-reader` (made from `main`); do not merge or push.
  Report what was built, the full grader output, the superpowers comparison, any
  problems found, and confirm you never opened `Fixtures/ANSWERS/`.
