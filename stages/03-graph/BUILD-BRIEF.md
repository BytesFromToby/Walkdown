# Build brief: stage 3 (graph)

Hand this to a session that has **not** read `Fixtures/ANSWERS/`. It is the
whole starting context.

## Task

Build stage 3 of Walkdown in `stages/03-graph/`, so that the grader reports
PASS for stage 3, and every script has a spec and tests.

## Read, in order

1. `CLAUDE.md` (project map, build rules)
2. `stages/03-graph/CONTEXT.md` (this stage's contract: nodes, edges, dynamic loads, checks, done-when)
3. `stages/CONTRACT.md` (the JSON report format and check IDs)
4. `pre-planning/METHOD.md` Stage 3; `pre-planning/THREATS.md` classes 10 and 12; `pre-planning/REPORTING.md` Section 3
5. `stages/01-inventory/` (a finished stage: follow its structure and SPEC style; stage 3 calls its `run.py` as a subprocess and never imports it)
6. `stages/02-reader/specs/fold.SPEC.md` (the invisible-character set stage 3 strips before matching; reimplement, do not import)
7. `Fixtures/03-graph/` (the test input; fine to look at)

## Never open

- `Fixtures/ANSWERS/` (the answer sheet). Exclude it from every search. Prove the
  stage only through the grader's default output, which names misses without
  revealing expected values. Do not run the grader with `--explain`. Do not run
  any stage on the project root (it would read the answer files).

## Environment

- Use the existing project virtualenv: `.venv/Scripts/python`. Install nothing
  new; stage 3 needs only the standard library plus packages already in
  `requirements.txt`. If you think you need another package, stop and say why.
- Never point pytest or any stage at `ReposToExamine/` except the one read-only
  stage 3 run named in Done. Run tests as `.venv/Scripts/python -m pytest stages -q`.

## Build rules

- Every script: `specs/<name>.SPEC.md` (inputs, outputs, must-never,
  Done-when) and `tests/test_<name>.py` written from the spec **before** the
  code. Tests build their own tiny trees in `tmp_path`, not the fixtures.
- `run.py` is the single entry point; it prints one contract-1 report to stdout
  and supports `--inventory <file>` and `--out <dir>`.
- Do not edit `Fixtures/`, `grader/`, `stages/CONTRACT.md`, or stages 1 and 2.
  If the contract, CONTEXT.md, or a fixture looks wrong (for example, the grader
  flags a finding that CONTEXT.md requires), stop and write the problem down for
  the user instead of working around it.
- No em-dashes in docs. No Claude attribution in commits.

## Done

- `.venv/Scripts/python -m pytest stages -q` passes (stages 1, 2, and 3).
- `.venv/Scripts/python grader/grader.py 03` → PASS.
- Run on `ReposToExamine/superpowers-main/superpowers-main/` completes. Report:
  number of entry points by kind, orphans, dangling references split by
  `context`, dynamic loads, and the depth histogram.
- Commit on a branch `stage-03-graph` (made from `main`); do not merge or push.
  Report what was built, the full grader output, the superpowers numbers, any
  problems found, and confirm you never opened `Fixtures/ANSWERS/`.
