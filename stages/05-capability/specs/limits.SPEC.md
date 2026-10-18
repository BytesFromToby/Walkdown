# limits.py: spec

Stated limits and what backs them (review C32, partner's v3, 2026-10-14; built 2026-10-17). A line
that tells the AI to stay read-only is wording; whether a tool setting enforces it is a separate
fact. Derived from stages 1 and 4; detects nothing new.

## Inputs

`stated_limits(reports)`: the stage 1 and 4 reports (keys `01`, `04`), after test data is set aside.

## Which lines

A stage 4 finding in instruction text (audience `model` or `subagent`) that states a read-only limit:
a phrase hit with `B.safety-adjective` whose line says "read-only", "read only", or "no side
effects", or a `term.safety` definition of such a word. One finding per file and line.

## Outputs

One `cap.limit` per line: `file`, `line`, `quote`, `limit` (`read-only`), and:

- `owner`: the file itself when it is a skill, agent, or command entry point; otherwise the
  `SKILL.md` of the nearest skill folder above it; None when neither.
- `owner_tools`: the owner's tools list from stage 1 (`struct.agent-tools`), None when it has none.
- `status` and `backed_by`, first match wins:
  1. `backed`, `flag`: a stage 4 `limit.setting` on the same line rules out writing.
  2. `backed`, `tools-list`: the owner's tools list has no writing tool and no Bash.
  3. `contradicted`: the owner's tools list has a writing tool, Bash, or `*`.
  4. `stated`: none of these. Stated in the text; Walkdown found no tool setting that enforces it.
- `flags`: the kinds of the same-line settings that rule out writing (empty unless `flag`).
- `other_routes`: `{file, line, what}` for other routes inside the owner's skill folder that can
  write: a `limit.setting` that grants writing, or an agent or command with no tools list or a
  write-capable one. `other_route_at`: the same as `file:line` strings. Empty for an agent or command
  that owns its own file, and when no skill folder holds the line.
- `evidence`: the wording, then whatever decided the status, then each other route.

## Must never

- Detect: every input is a stage 1 or 4 finding.
- Say a limit is broken or ignored. `stated` means Walkdown found nothing that enforces it, which is
  as far as a static read goes.
- Count test data (set aside before this runs).

## Done when (each backed by a test in `tests/test_limits.py`)

1. A skill whose `allowed-tools` has no writing tool backs its read-only line (`tools-list`); one
   with Bash or Edit contradicts it; one with no tools list leaves it `stated`.
2. A restricting `--tools` list on the same line backs it (`flag`), whatever the owner's list.
3. A reference file under a skill folder is owned by that skill's `SKILL.md`.
4. A setting that grants writing elsewhere in the same skill folder is listed in `other_routes`; one
   in another skill is not.
5. A line a person reads (audience `human`) or without a read-only word gives no `cap.limit`.
6. The grader's `cap-limit-*` rows in `Fixtures/ANSWERS/05-capability.json` pass.
