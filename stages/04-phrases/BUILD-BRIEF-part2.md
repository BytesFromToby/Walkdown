# Build brief: stage 4, part 2

Hand this to a session that has **not** read `Fixtures/ANSWERS/`. It is the
whole starting context.

## Task

Add part 2 to stage 4 in `stages/04-phrases/`: the harness rubric, the endpoint
census, the conditional table, and the term table, so that the grader reports
PASS for stage 4, and every new script has a spec and tests.

## Read, in order

1. `CLAUDE.md` (project map, build rules)
2. `stages/04-phrases/CONTEXT-part2.md` (this build's contract)
3. `stages/04-phrases/CONTEXT.md` (part 1: the pattern engine, audience tags, folding) and the existing code, SPECs, and tests in `stages/04-phrases/`
4. `stages/CONTRACT.md` (report format; the part 2 checks are listed there)
5. `pre-planning/METHOD.md` Stage 4; `pre-planning/REPORTING.md` Section 4; `pre-planning/THREATS.md` classes 1, 14, 21, 22; `pre-planning/PHRASES.md` sets B, I, J and "Stage 4 v1 measurement"
6. `tools/extract_urls.py` (the old endpoint extractor: read it for its lessons, do not port it)
7. `Fixtures/04-phrases/part2-repo/` (the new test input; fine to look at) and the rest of `Fixtures/04-phrases/`

## Never open

- `Fixtures/ANSWERS/` (the answer sheet). Exclude it from every search. Prove the
  work only through the grader's default output. Do not run the grader with
  `--explain`. Do not run any stage on the project root.

## Environment

- `.venv/Scripts/python` only; standard library plus what `requirements.txt`
  already pins. Install nothing. If you need a package, stop and say why.
- Never point pytest or any stage at `ReposToExamine/` except the two read-only
  stage 4 runs named in Done. Tests: `.venv/Scripts/python -m pytest stages grader -q`.
- Write files with the Write and Edit tools, not shell heredocs: heredocs have
  turned `\b` into backspace characters in this repo before. After editing
  `patterns.yaml` or any file with regexes, check it has no `\x08` bytes.

## Build rules

- New scripts get `specs/<name>.SPEC.md` and `tests/test_<name>.py` written from the
  spec **before** the code; tests use tiny inline inputs, not the fixtures.
- Keep word lists (confirmation wording, safety vocabulary, TLDs, registry
  hosts, conditional kinds) as data in one place, each citing its source doc.
- `run.py` stays the single entry point; part 2 findings follow part 1's in the
  report. `--out` also writes part 2 counts into `hits.json`.
- Update `CONTEXT.md`'s scope note (part 2 is built) and the stderr "not built"
  list (only position/repetition and gitleaks remain).
- Do not edit `Fixtures/`, `grader/`, `stages/CONTRACT.md`, `pre-planning/`, or
  other stages. If the contract, CONTEXT-part2.md, or a fixture looks wrong, stop
  and write the problem down instead of working around it.
- No em-dashes in docs. No Claude attribution in commits.

## Done

- `.venv/Scripts/python -m pytest stages grader -q` passes.
- `.venv/Scripts/python grader/grader.py 04` → PASS.
- Runs on `ReposToExamine/superpowers-main/superpowers-main/` and
  `ReposToExamine/claude-familiar/` complete; report the numbers CONTEXT-part2.md
  "Done when" item 3 asks for.
- Commit on a branch `stage-04-part2` (made from `main`); do not merge or push.
  Report what was built, the full grader output, the numbers, every judgment call
  CONTEXT-part2.md did not settle, any problems, and confirm you never opened
  `Fixtures/ANSWERS/`.
