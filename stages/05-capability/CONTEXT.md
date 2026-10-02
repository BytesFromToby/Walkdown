# Stage 5: Capability

**Question:** what does installing it grant?
**Kind of evidence:** derived, never detected. Every statement cites the stage 1
to 4 findings that establish it.
**Report heading:** What this touches.

Stage 5 does **no new detection**. It reads stage 1 to 4 reports and states what
the artifact can do: the lethal trifecta legs, the install grants, the paths by
which text reaches context at load, each agent's tool posture, and the
cross-stage pairs a human should read first. It never concludes. A clean,
well-built skill usually scores three of three; that is a map, not a verdict
(REPORTING, "Rules for the summary").

Sources for every rule below: `pre-planning/METHOD.md` (Stage 5),
`pre-planning/THREATS.md` ("Organizing frame: the lethal trifecta", classes 7,
12, 15, 16, 17), `pre-planning/REPORTING.md` (Section 5, 1.8, and the summary
format), `pre-planning/RED-TEAM.md` ("Defensive note: the trifecta is
prescriptive"), `stages/CONTRACT.md`. Nothing here comes from the answer sheet;
a builder of this stage never opens `Fixtures/ANSWERS/`.

---

## Inputs

- `<input_dir>`: a pinned repo copy or a fixture folder. Read-only.
- The reports of stages 1 to 4 for that input, reached through their runners,
  never by importing their code:
  - `--reports <dir>`: a folder holding `01-inventory.json`, `02-reader.json`,
    `03-graph.json`, `04-phrases.json` already produced for this input.
  - Without it, `run.py` runs each `stages/NN-name/run.py <input_dir>` as a
    subprocess with the same Python. Stage 3 is run with `--out <tempdir>` so
    stage 5 can read its `graph.json` edges. If any stage fails, stage 5 fails
    (exit non-zero); a capability map over a missing stage is not a result.
- A skip in an input stage (for example, stage 2 without Tesseract) is carried
  forward: stage 5 names it on stderr. It does not fail the run.

## Outputs

- `run.py <input_dir>` prints one contract-1 report to stdout.
- `run.py <input_dir> --out <dir>` also writes `<dir>/capability.json`: every
  finding with its **full** evidence list (the report may cap evidence per
  finding, see below). Never writes inside `<input_dir>`.

## Evidence

Every derived finding carries `evidence`: a list of
`{"stage": "NN", "check": ..., "file": ..., "line": ..., "why": ...}` pointing at
the input findings that establish it, `why` naming the rule below that used it
(for example `tool grant: WebFetch`). In the stdout report, cap evidence at 20
entries per finding and add `evidence_total`; `capability.json` has them all.

Stage 4 findings carry `patterns` (stable pattern ids from
`stages/04-phrases/patterns.yaml`). The rules below name pattern ids where a
check alone is too broad.

## Trifecta legs

Plain terms in reports (locked 2026-09-30, THREATS "Organizing frame"):
`private-data` = **Reads your data**, `untrusted-content` = **Takes outside input**,
`external-comms` = **Sends data out**. Check IDs and field values are unchanged.
Clone or install of third-party code (leg 2) and connected accounts (leg 1) are counted
since 2026-09-30 (see the section at the end).

One `cap.leg` finding per leg, **always three**, `file` and `line` null, with
`present` true or false. A leg with no evidence is `present: false` with an
empty `evidence` list; that is a stated result, never an omission.

Tool names in grants are compared case-sensitively after trimming. "Inherits
all" means a `struct.agent-tools` finding whose `tools` is null.

| Leg | `present` when any of these exists |
|---|---|
| `private-data` | `phrase.creds` (any pattern); `phrase.K.exfil` with `K.data-flow`; an agent or command grant including `Read`, `Grep`, `Glob`, `Bash`, or inheriting all; a hook (`struct.hooks`) on `PreToolUse`, `PostToolUse`, or `UserPromptSubmit` (it sees tool input or the user's prompt) |
| `untrusted-content` | `phrase.remote-load` (any pattern); a grant including `WebFetch` or `WebSearch`, or inheriting all; an `mcp-config` entry point (`inv.file`, tool output from a server); a `struct.mcp` server declared in any config (added 2026-09-29) |
| `external-comms` | `phrase.K.exfil` with any of `K.http-verb`, `K.relay-host`, `K.chat-webhook`, `K.dns`, `K.encode-send`, `K.data-flow`, `K.dest-ref`, `K.dest-stored`, `K.telemetry-send`; `phrase.remote-load` (a fetch is an outbound request); a grant including `WebFetch` or `WebSearch`, or inheriting all; an `mcp-config` entry point |

The external-comms leg also counts a `struct.mcp` server (2026-09-29).

**Phrase evidence from human-facing files never counts** for a leg or a grant
(stage 4 `audience` `human`: README, docs, changelog, templates). They describe what
the user does, not what the artifact states or grants (2026-09-29, Case 004: README
install lines were the persistence and network evidence).

What does **not** establish a leg, and why:

- A skill with no grant of its own. It runs with the host's tools, but the
  artifact states nothing about them; stage 5 maps what the artifact states.
- A `Bash` grant for `external-comms`. Bash can reach the network, but so can
  every shell; counting it makes every executing skill 3 of 3 and the map stops
  telling anything. Bash is recorded under `private-data` and in posture
  (`execute`). The report says this limit once (stage 7).
- `K.telemetry` and `K.md-carrier`: documentation of other tools' behavior and
  markdown carriers, not a channel the artifact uses.

## Install grants

One `cap.grant` finding per grant kind **present**, `file` and `line` null. An
absent grant emits nothing.

| `grant` | Present when |
|---|---|
| `exec-at-load` | any `struct.hooks` finding (a hook runs a command on a harness event, not on the user's request); `evidence` names each event |
| `context-injection` | any `struct.description` (always-on text) or any hook on `SessionStart` or `UserPromptSubmit` |
| `persistence` | `phrase.E.env` with `E.persist-target`, `E.persist-redirect`, `E.memory`, `E.self-install`, `E.git-keys`, or `E.editor-autorun`; `phrase.E.perms` with `E.outlives-session` or `E.install-global` |
| `network` | any evidence that makes `external-comms` present, plus `phrase.E.perms` with `E.install-global` |
| `elevated` | `phrase.E.perms` with `E.perm-flags`, `E.allowlist`, or `E.confirm-off`; an agent or command inheriting all tools |

## Injection paths and bytes at load

REPORTING 5.1: bytes delivered into context before the first user input, by path.

- One `cap.injection` per `struct.description`: `mechanism: description`,
  `file` the defining file, `bytes` the UTF-8 length of the description,
  `basis: exact`.
- One `cap.injection` per hook on `SessionStart` (and `UserPromptSubmit`, marked
  with its `event`): `mechanism: hook`, `file` the hook config, `event`,
  `command`. `bytes`: the sum of the sizes of the files the hook's command script
  references (stage 3 static edges out of the script file), `basis: estimate`;
  when the script is not in the tree or names no file, `bytes: null`,
  `basis: unknown`. Stage 5 never runs the hook to measure it.
- One `cap.load-bytes` per hook config (`file` the config; `file` null when no
  hook config injects at `SessionStart`): `bytes` the total over the
  descriptions plus that config's `SessionStart` hooks (each host runs its own
  config, so configs are never summed; changed 2026-09-29), `basis` `exact` when every part is
  exact, `estimate` when any part is estimated, and `unknown_parts` the count of
  parts with unknown bytes.

## Agent posture

One `cap.posture` per `struct.agent-tools` finding (`file` the definition,
`line` its line). Fields: `tools` (as stage 1 reported, null for inherit-all),
`posture`, `least_privilege`.

| Tool | Posture word |
|---|---|
| `Read`, `Grep`, `Glob`, `LS`, `NotebookRead`, `TodoRead`, `TodoWrite` | `read` |
| `Write`, `Edit`, `MultiEdit`, `NotebookEdit` | `write` |
| `Bash`, `PowerShell` | `execute` |
| `WebFetch`, `WebSearch`, any `mcp__*` tool | `network` |
| `Task`, `Agent` | `delegate` |
| tools null (inherits all) | `all` |
| any other name | `other` |

`posture` is the sorted set of words. `least_privilege` is true only when
`posture` is exactly `["read"]`. METHOD asks whether a grant matches the stated
job; that comparison is a reading of the description, so stage 5 records the
posture and the description side by side (`description` field) and stage 6
reads the match. A read-only posture is the one positive stage 5 states on its
own (Case 002).

## Cross-stage pairs

One `cap.pair` per stage 4 `phrase.*` finding (not the part 2 tables) that sits on one of these, `file` and `line`
the phrase hit's:

| `pair` | The phrase finding's file or line is |
|---|---|
| `orphan+phrase` | a `graph.orphan` file |
| `dynamic+phrase` | a file whose `graph.depth` is `via: dynamic` (reached only through a load: a folder a config names, a code scan, or an instruction-file glob; stage 3 marks folder and glob mentions elsewhere `via: mention`, and those do not pair, 2026-09-29) |
| `hidden+phrase` | inside a `read.divergence` with `reading: A-only` (from its `line` through the lines its `text` spans), or on a `read.fold` line; except a hit made only of carrier patterns (`K.md-carrier`), which is the same fact as the divergence (2026-09-29) |

| `hook+phrase` | in a script a `SessionStart` or `UserPromptSubmit` hook runs (the hook's command script, plus files that script names directly), and the hit is an instruction-in-a-script pattern (`C.script-instruction`, `C.emit-instruction`): text that can reach the model through the hook's output (added 2026-09-29, Case 003) |

`${CLAUDE_PLUGIN_ROOT}` in a hook command resolves against the nearest folder
above the hook config that holds `.claude-plugin/plugin.json` (a plugin in a
subfolder of its repo), then the input root.

Fields: `pair`, `phrase_check`, `patterns`, `quote` (from the stage 4 finding),
and `evidence` citing both halves. A hit can be in more than one pair; emit one
finding per pair kind. Entry points are never orphans or dynamic-only, so their
visible lines never pair.

## Test data (added 2026-10-02)

Before anything is derived, findings in test data (folders such as tests/ and fixtures/,
files such as test_*.py; stage 4 `audience.is_test_data`) are set aside and counted in one
`cap.testdata` finding. A test-data file that a model-read file references directly is not
set aside; it is reported as a `testdata+loaded` pair. `specs/testdata.SPEC.md`.

## Checks

| Check | One finding per | Fields |
|---|---|---|
| `cap.leg` | trifecta leg, always three (`file`, `line` null) | `leg`: `private-data`, `untrusted-content`, `external-comms`; `present`: bool; `evidence` |
| `cap.grant` | install grant present (`file`, `line` null) | `grant`: `exec-at-load`, `context-injection`, `persistence`, `network`, `elevated`; `evidence` |
| `cap.injection` | path by which text reaches context at load | `mechanism`: `description` or `hook`; `event` (hooks); `bytes`: int or null; `basis`: `exact`, `estimate`, `unknown` |
| `cap.load-bytes` | hook config (`file` the config), or run (`file` null) when none injects at load | `bytes`; `basis`; `unknown_parts` |
| `cap.posture` | agent or command definition | `tools`; `posture`: list; `least_privilege`: bool; `description` |
| `cap.pair` | phrase hit on an orphan, a dynamic-only file, or hidden text | `pair`; `phrase_check`; `patterns`; `quote`; `evidence` |

## Dependencies

Standard library only. No new packages without a note to the user.

## Must never

- Detect anything: no new pattern, no file reading beyond the stage reports,
  stage 3's `graph.json`, and file sizes for `bytes`.
- Conclude, score, rank, or render a verdict. No field named risk, severity,
  score, or verdict. Three of three is stated flatly.
- Omit an absent leg. Absence is `present: false`.
- Run anything from the input, or fetch a URL.
- Write inside `<input_dir>`.
- Import code from another stage. Stages 1 to 4 are reached through their
  runners.

## Done when

1. Every script in this folder has a `specs/<name>.SPEC.md` and pytest tests written
   from it, and they pass. Tests build small stage reports inline (JSON dicts);
   they do not run stages 1 to 4.
2. `.venv/Scripts/python grader/grader.py 05` reports PASS.
3. Run on `ReposToExamine/superpowers-main/superpowers-main/` it completes.
   Record: the three legs with the evidence count for each, grants, bytes at load
   (Case 001 by hand: `hooks/session-start` injects `using-superpowers/SKILL.md`
   at `SessionStart`), posture per agent, and pair counts by kind. Case 001's
   hand result was 3 of 3.

## Added 2026-09-30: outside code and connectors (locked trifecta definitions)

- **Takes outside input** also counts third-party code brought onto the machine:
  stage 4 `E.clone` (git clone, gh repo clone, submodule add, degit, "clone the repo"),
  `E.install`, `E.install-global`, `E.runtime-install`. Human-facing text (a README's
  install line) never counts.
- **Reads your data** also counts connected accounts: stage 4 `E.connector` (widened:
  connect / link / authorize / sign in with your Gmail, Drive, Outlook, Slack, Notion,
  GitHub, ...), an MCP server whose name, command, or URL names such a service, and an
  agent tool `mcp__<service>__...` for one (`CONNECTOR_NAMES` in `rules.py`).
- Neither source counts toward **Sends data out**: bringing code in or reading an account
  sends nothing.
