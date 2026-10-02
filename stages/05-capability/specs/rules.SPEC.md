# rules.py: spec

The stage 5 rule tables, as data, in one place. Every other stage 5 script reads
its rules from here, so a reader can check this file against `CONTEXT.md` line
by line. `rules.py` holds no logic beyond constants.

## Inputs

None. It is imported.

## Outputs

Constants:

- `LEGS`: the three leg names in report order: `private-data`,
  `untrusted-content`, `external-comms`.
- `GRANTS`: the five grant kinds in report order: `exec-at-load`,
  `context-injection`, `persistence`, `network`, `elevated`.
- `LEG_RULES` and `GRANT_RULES`: one rule per leg or grant. A rule is a dict
  whose keys are any of:
  - `phrase_any`: stage 4 checks that count with any pattern.
  - `phrase_patterns`: `{check: [pattern ids]}`; a stage 4 finding counts when
    its check is a key and one of its `patterns` is listed.
  - `tools`: tool names; an agent or command grant (`struct.agent-tools`)
    counts when its `tools` include one (compared after trimming, case
    sensitive).
  - `inherit_all`: true when a `struct.agent-tools` finding whose `tools` is
    null counts.
  - `hook_events`: `struct.hooks` events that count, or `"*"` for any hook.
  - `entry_points`: stage 1 `inv.file` `entry_point` kinds that count.
  - `descriptions`: true when any `struct.description` counts.
  - `legs`: legs whose evidence this grant takes over whole (`network` takes
    `external-comms`).
- `INJECTION_EVENTS`: hook events that give a `cap.injection`
  (`SessionStart`, `UserPromptSubmit`).
- `LOAD_BYTES_EVENTS`: hook events counted in `cap.load-bytes`
  (`SessionStart`).
- `POSTURE_WORDS`: tool name to posture word, exactly the CONTEXT table.
- `POSTURE_PREFIXES`: name prefix to posture word (`mcp__` to `network`).
- `POSTURE_INHERIT_ALL` (`all`), `POSTURE_OTHER` (`other`),
  `LEAST_PRIVILEGE` (`["read"]`).
- `PAIRS`: the pair kinds in report order: `orphan+phrase`, `dynamic+phrase`,
  `hidden+phrase`.
- `EVIDENCE_CAP`: 20, the stdout cap on evidence entries per finding.
- `LIMITS`: the stage 5 limit notes printed on stderr every run (Bash is not
  counted toward `external-comms`).

## Must never

- Hold a rule that `CONTEXT.md` does not state, or compute anything.
- Name a field risk, severity, score, or verdict.

## Done when (each backed by a test in `tests/test_rules.py`)

1. `LEGS`, `GRANTS`, and `PAIRS` list exactly the CONTEXT names in order.
2. Every pattern id named in `LEG_RULES` and `GRANT_RULES` exists in
   `stages/04-phrases/patterns.yaml` under the check it is filed under (the test
   reads the yaml as text; no code is imported).
3. `Bash` is not in `LEG_RULES["external-comms"]["tools"]`; `K.telemetry` and
   `K.md-carrier` are named by no rule.
4. `POSTURE_WORDS` maps every tool in the CONTEXT posture table to its word.
