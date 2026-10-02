# legs.py: spec

The trifecta legs (`cap.leg`) and the install grants (`cap.grant`), derived from
stage 1 and stage 4 findings by the rules in `rules.py` (`LEG_RULES`,
`GRANT_RULES`). One engine applies both tables.

## Inputs

- `reports`: `{"01": report, "02": report, "03": report, "04": report}`
  (contract-1 reports; only `01` and `04` are read here).

## Evidence

`evidence(rule, reports)` returns the list of entries a rule establishes. Each
entry is `{"stage", "check", "file", "line", "why"}` pointing at one input
finding:

| Rule key | Input finding | `why` |
|---|---|---|
| `phrase_any` | stage 4 finding with that check | `<check>: <its patterns, comma-joined>` |
| `phrase_patterns` | stage 4 finding with that check and a listed pattern | `<check>: <the listed patterns it carries>` |
| `tools` | `struct.agent-tools` whose `tools` include a listed name | `tool grant: <the listed names it holds>` |
| `inherit_all` | `struct.agent-tools` with `tools` null | `tool grant: inherits all` |
| `hook_events` | `struct.hooks` whose `event` is listed (or any, for `"*"`) | `hook event: <event>` |
| `entry_points` | `inv.file` whose `entry_point` is listed | `entry point: <kind>` |
| `descriptions` | `struct.description` | `description: always-on text` |
| `legs` | the evidence of that leg, unchanged | (as the leg) |

- Tool names are compared after trimming whitespace, case sensitive, and with a
  trailing argument scope removed (`Bash(git:*)` compares as `Bash`), since a
  scoped grant is still a grant of that tool.
- Hook events are compared case-insensitively (Cursor's `sessionStart` is the
  same event as `SessionStart`).
- Findings carrying `skipped` never establish anything.
- One input finding gives at most one entry per rule (an entry naming several
  patterns or tools, not one per pattern). Entries are ordered by stage, then
  file, then line, then check, and exact duplicates are dropped.

## Outputs

- `legs(reports)`: always three `cap.leg` findings in `LEGS` order:
  `{"check": "cap.leg", "file": null, "line": null, "leg", "present", "evidence"}`.
  `present` is true exactly when `evidence` is non-empty.
- `grants(reports, leg_findings)`: one `cap.grant` per grant kind with
  non-empty evidence, in `GRANTS` order:
  `{"check": "cap.grant", "file": null, "line": null, "grant", "evidence"}`.
  `network` takes the `external-comms` leg's evidence plus its own rule.

## Must never

- Emit a grant with no evidence, or omit a leg.
- Count `Bash` toward `external-comms`, or count `K.telemetry` or
  `K.md-carrier`.
- Name a field risk, severity, score, or verdict; add up legs into a number.

## Done when (each backed by a test in `tests/test_legs.py`)

1. An empty set of reports gives three legs, all `present` false with empty
   evidence, and no grants.
2. `phrase.creds` gives `private-data`; `phrase.K.exfil` with `K.data-flow`
   gives `private-data` and `external-comms`; `K.http-verb` alone gives only
   `external-comms`; `K.telemetry` alone gives nothing.
3. A grant of `[Read, Bash]` gives `private-data` only; `[WebFetch]` gives
   `untrusted-content` and `external-comms`; `tools` null gives all three legs
   and the `elevated` grant; `Bash(git:*)` counts as `Bash`.
4. `phrase.remote-load` gives `untrusted-content` and `external-comms`; an
   `mcp-config` entry point gives the same two.
5. A `PreToolUse` hook gives `private-data`, `exec-at-load`; a `SessionStart`
   hook gives `exec-at-load` and `context-injection`, with `why` naming the
   event; `sessionStart` counts as `SessionStart`.
6. `E.persist-redirect` gives `persistence`; `E.install-global` gives
   `persistence` and `network`; `E.perm-flags` gives `elevated`; a description
   gives `context-injection`.
7. `network` evidence includes every `external-comms` entry.
8. Evidence entries carry `stage`, `check`, `file`, `line`, `why`; a finding
   with two listed patterns gives one entry naming both.

## Added 2026-09-29

- A stage 4 finding with `audience` `human` is never evidence. Test:
  `test_human_audience_phrase_evidence_is_ignored`.
- A rule with `mcp_servers: true` takes each `struct.mcp` as evidence (`MCP server:
  <name>`). Test: `test_mcp_server_in_a_manifest_counts_toward_untrusted_and_external`.
- Rules may take `phrase_patterns` for `phrase.E.env` / `phrase.E.perms` (clone and
  installs for leg 2, `E.connector` for leg 1) and `connector_names: true`: a
  `struct.mcp` or an `mcp__` tool grant whose name matches `CONNECTOR_NAMES` is leg 1
  evidence. Tests: `test_clone_and_installs_take_outside_input`,
  `test_connectors_read_your_data` (2026-09-30).
