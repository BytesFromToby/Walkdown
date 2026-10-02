# posture.py: spec

Each agent or command definition's tool posture (`cap.posture`), from stage 1
`struct.agent-tools`, by the tool-to-word table in `rules.py`. The stated job
sits beside the posture; stage 5 does not judge whether they match.

## Inputs

- `reports`: `{"01", ...}` contract-1 reports (reads `01`).
- `words(tools)`: a tool list, or `None` for inherit-all.

## Outputs

- `words(tools)`: the sorted list of distinct posture words. `None` gives
  `["all"]`. Each name is trimmed and a trailing argument scope removed
  (`Bash(git:*)` is `Bash`), then looked up case sensitively in
  `POSTURE_WORDS`, else by prefix in `POSTURE_PREFIXES` (`mcp__x` is
  `network`), else `other`. An empty list gives `[]`.
- `least_privilege(posture)`: true only when `posture == ["read"]`.
- `postures(reports)`: one finding per `struct.agent-tools` (not skipped), in
  stage 1 order: `{"check": "cap.posture", "file", "line", "tools" (as stage 1
  gave them, null for inherit-all), "posture", "least_privilege",
  "description", "evidence"}`; evidence is the `struct.agent-tools` finding
  (`why` `tool grant as stated`).

## Must never

- Compare the grant with the description, or score the posture.

## Done when (each backed by a test in `tests/test_posture.py`)

1. `[Read, Grep, Glob]` gives `["read"]`, least privilege true.
2. `[Read, Write, Edit, Bash]` gives `["execute", "read", "write"]`, false.
3. `None` gives `["all"]`, false; `tools` stays null in the finding.
4. `WebFetch`, `mcp__github__x` give `network`; `Task` gives `delegate`;
   `Frobnicate` and lowercase `read` give `other`; `Bash(git:*)` gives
   `execute`.
5. `postures` carries `file`, `line`, `description` from stage 1.
