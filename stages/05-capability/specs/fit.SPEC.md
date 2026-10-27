# fit.py: spec

Do the tools fit the job? (plan for builders, slice 5, owner 2026-10-26; the slice spec is
`pre-planning/SPEC-SLICE5-2026-10-26.md`). Derived from stage 4's `trig.entry`, `ask.tools`,
`ask.named`, stage 1's `struct.hooks`, stage 3's edges (the reach slice 1 counts), and this stage's
`cap.injection`. Nothing is run or read here. The yardstick is the entry's own words against its
own grants.

## Data: `fit.yaml`

Dated, with sources (Claude Code's subagents, skills, and hooks pages): the families of work and
the tools that do them (`shell`: Bash, PowerShell, Monitor; `write`: Write, Edit, NotebookEdit,
MultiEdit; `web`: WebFetch; `search`: WebSearch; `agent`: Agent, Task); how often each hook event
runs; which events' plain stdout becomes context; the 10,000-character output cap.

## Entries

Every `trig.entry` that loads (not `unread`, not `skipped`). Its **reach** is slice 1's
(`cost.reach` over every kind of reference: a skill its own folder, an agent or command one
level), plus, for a subagent, the reach of each skill its `skills` field preloads. What it
**asks for** is every family an `ask.tools` row in its reach names, with the first place; what it
**names** is every `ask.named` tool in its reach.

## Findings

- **`fit.unused`**: a granted tool in a family (`fit.yaml`) or from an MCP server, when nothing in
  the reach asks for its family and the reach never names it (an MCP tool: never names its
  server): `tool` (as written), `family`, `kind_of`, `pre_approved` (true for a skill or command:
  `allowed-tools` only pre-approves), `line` (the grant's key line). Reading tools and names no
  family lists are never reported (owner, 2026-10-26).
- **`fit.missing`**: a family the reach asks for that the entry cannot use: a subagent whose
  `tools` list (less its disallowed tools) has no tool of that family, or any entry whose
  disallowed tools remove every tool of it. `family`, `asked_at`, `why`. A skill's `allowed-tools`
  never makes a task missing (owner, 2026-10-26).
- **`fit.inherits`**: a subagent with no `tools` list (every tool, MCP tools included):
  `families` its reach asks for, `asked_at`.
- **`fit.hook`**, one per stage 1 hook: `event`, `matcher`, `how_often` (`every-prompt`,
  `every-tool-call`, `matching-tool-calls` for a tool event with a narrower matcher,
  `every-turn`, `once-a-session`, `other`), `adds_context` (the event's plain stdout becomes
  context), `bytes` (this stage's `cap.injection` estimate, or null), `over_cap`.

## Must never

- Say a grant is wrong, or that a tool is unused anywhere but in the entry's own reach.
- Call a skill's task missing because of `allowed-tools`.

## Done when

1. Fixture `fit-repo` (grader 05, rows `fit-*`): an unused grant, two missing families, an
   inheriting agent, a thin agent whose words live in the skill it reads (no finding), a skill's
   pre-approved and unused tool, and three hooks by how often they run.
2. `tests/test_fit.py`: families, MCP servers, preloaded skills, disallowed tools, hook matchers.

## History

- 2026-10-26: built (slice 5).
