# Build brief: stage 5 (capability)

Hand this to a session that has **not** read `Fixtures/ANSWERS/`. It is the
whole starting context.

## Task

Build stage 5 of Walkdown in `stages/05-capability/`, so that the grader reports
PASS for stage 5, and every script has a spec and tests. Stage 5 derives; it
detects nothing.

## Read, in order

1. `CLAUDE.md` (project map, build rules)
2. `stages/05-capability/CONTEXT.md` (this stage's contract: inputs, legs, grants, injection, posture, pairs, checks, done-when)
3. `stages/CONTRACT.md` (the JSON report format, every stage's check IDs; stage 5's section is new)
4. `pre-planning/METHOD.md` Stage 5; `pre-planning/THREATS.md` "Organizing frame: the lethal trifecta"; `pre-planning/REPORTING.md` Section 5 and 1.8; `pre-planning/RED-TEAM.md` "Defensive note: the trifecta is prescriptive"
5. `stages/03-graph/run.py` and `stages/04-phrases/run.py` with their SPECs (how the input stages are called and what `--out` writes); `stages/04-phrases/patterns.yaml` (the pattern ids stage 5 names)
6. `Fixtures/05-capability/` (the test inputs: five small repos; fine to look at)

## Never open

- `Fixtures/ANSWERS/` (the answer sheet). Exclude it from every search. Prove the
  stage only through the grader's default output, which names misses without
  revealing expected values. Do not run the grader with `--explain`. Do not run
  any stage on the project root (it would read the answer files).

## Environment

- Use the existing project virtualenv: `.venv/Scripts/python`. Standard library
  only; install nothing. If you think you need a package, stop and say why.
- Never point pytest or any stage at `ReposToExamine/` except the one read-only
  stage 5 run named in Done. Run tests as `.venv/Scripts/python -m pytest stages -q`.
- Prefer the Write and Edit tools over shell heredocs for files with
  backslashes.

## Build rules

- Every script: `specs/<name>.SPEC.md` (inputs, outputs, must-never,
  Done-when) and `tests/test_<name>.py` written from the spec **before** the
  code. Tests build small stage reports inline as dicts; they never run stages
  1 to 4.
- `run.py` is the single entry point; it prints one contract-1 report to stdout
  and supports `--reports <dir>` and `--out <dir>`.
- Keep the rule tables (which checks and pattern ids establish each leg and
  grant, the tool-to-posture map) in one place, as data, so a reader can check
  them against CONTEXT.md line by line.
- Do not edit `Fixtures/`, `grader/`, `stages/CONTRACT.md`, `pre-planning/`, or
  stages 1 to 4. If the contract, CONTEXT.md, a fixture, or an input stage's
  output looks wrong, stop and write the problem down for the user instead of
  working around it.
- No em-dashes in docs. No Claude attribution in commits.

## Done

- `.venv/Scripts/python -m pytest stages -q` passes (stages 1 to 5).
- `.venv/Scripts/python grader/grader.py 05` → PASS.
- Run on `ReposToExamine/superpowers-main/superpowers-main/` completes. Report
  the numbers CONTEXT.md "Done when" item 3 asks for.
- Commit on a branch `stage-05-capability` (made from `main`); do not merge or
  push. Report what was built, the full grader output, the superpowers numbers,
  any problems found, every judgment call CONTEXT.md did not settle, and confirm
  you never opened `Fixtures/ANSWERS/`.
