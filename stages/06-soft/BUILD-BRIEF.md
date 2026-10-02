# Build brief: stage 6 (soft reads)

Hand this to a session that has **not** read `Fixtures/ANSWERS/`. It is the
whole starting context.

## Task

Build stage 6 in `stages/06-soft/`: the review packet (labeling and relational
questions) and the pluggable backends (Jev, Laya, Claude CLI), so that the grader
reports PASS for stage 6 with no backend, and every script has a spec and tests.

## Read, in order

1. `CLAUDE.md` (project map, build rules)
2. `stages/06-soft/CONTEXT.md` (this stage's contract)
3. `stages/CONTRACT.md` (report format; stage 6's checks are listed there)
4. `pre-planning/METHOD.md` Stage 6; `pre-planning/RED-TEAM.md` §8; `pre-planning/REPORTING.md` Section 6
5. `stages/05-capability/` (how a stage reaches stages 1 to 4 through `--reports` or subprocesses) and `stages/04-phrases/patterns.yaml` (pattern ids and `source` text)
6. An earlier private evaluation of how Jev and Laya were called (not included in this repository)
7. The installed SDK types: `.venv/Lib/site-packages/typesafe_sdk/` and `.venv/Lib/site-packages/laya/`
8. `Fixtures/06-soft/labels-repo/` (the test input; fine to look at)

## Never open

- `Fixtures/ANSWERS/`. Exclude it from every search. Prove the stage only through
  the grader's default output. Do not run the grader with `--explain`. Do not run
  any stage on the project root.

## Environment

- `.venv/Scripts/python` only. `typesafe-sdk`, `torch` (CPU), and `laya` are
  installed (see `requirements-soft.txt`). Install nothing else; if you need a
  package, stop and say why.
- The Jev key is in `HKCU\Environment` as `TYPESAFE_API_KEY`. Read it in-process
  with `winreg` if it is not in `os.environ`. **Never print, log, echo, or write
  it**, and never put it on a command line.
- Laya's first load downloads its weights (about 1.7 GB) from Hugging Face; that
  download is approved. Load it once per run.
- The Claude CLI (`claude`) is installed; its login may have expired. If a call
  returns an authentication error, record skips and move on; do not try to log in.
- Tests stub every backend: no network, no model load, no CLI call in pytest.
- Write regex-bearing files with the Write and Edit tools, not shell heredocs.
- Never point pytest or any stage at `ReposToExamine/` except the runs in Done.

## Build rules

- Every script: `specs/<name>.SPEC.md` and `tests/test_<name>.py` written from the spec
  **before** the code.
- Option definitions (`what` / `not_for` / `examples`), relational question
  templates, and the Claude system prompt live as data in one file, each citing
  its source doc.
- `run.py` is the single entry point: `run.py <input_dir> [--reports <dir>]
  [--out <dir>] [--label none|jev|laya] [--compare none|jev|laya] [--relational
  none|claude-cli]`, flags overriding `WALKDOWN_SOFT_LABEL`,
  `WALKDOWN_SOFT_COMPARE`, `WALKDOWN_SOFT_RELATIONAL`.
- Do not edit `Fixtures/`, `grader/`, `stages/CONTRACT.md`, `pre-planning/`, or
  other stages. If the contract, CONTEXT.md, or a fixture looks wrong, stop and
  write it down.
- No em-dashes in docs. No Claude attribution in commits.

## Done

- `.venv/Scripts/python -m pytest stages grader -q` passes.
- `.venv/Scripts/python grader/grader.py 06` → PASS (no backend).
- `WALKDOWN_SOFT_LABEL=jev .venv/Scripts/python grader/grader.py 06` and the same
  with `laya`: PASS, with recall reported. One fixture run with `--label jev
  --compare laya`: agreement rate.
- Runs on `ReposToExamine/backlog/` and `ReposToExamine/claude-familiar/` with
  `--label jev --compare laya --relational claude-cli` complete (outputs to the
  session scratchpad, not the repo).
- Commit on a branch `stage-06-soft` (from `main`); do not merge or push. Report
  what was built, the full grader outputs (none, jev, laya), agreement, the two
  repo runs, the Jev cost if the SDK reports it, every judgment call, any
  problems, and confirm you never opened `Fixtures/ANSWERS/`.
