# capability: spec

One spec for the `02.5-capability` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. Merged from the per-script specs in restructure step 8a.

## The rules

`02.5-capability` does **no new detection**. It reads `02.1-inventory` to `02.4-phrases` reports and states what
the artifact can do: the lethal trifecta legs, the install grants, the paths by
which text reaches context at load, each agent's tool posture, and the
cross-stage pairs a human should read first. It never concludes: the legs are a map
of what the artifact could do, and the reports never compare one repository with others
(owner, 2026-10-21).

The tables below are the contract of `Library/capability.yaml`: each table there is one table here (`rules.py` reads that file; see the `rules` section). The scripts' own sections follow.

### Evidence

Every derived finding carries `evidence`: a list of
`{"stage": "NN", "check": ..., "file": ..., "line": ..., "why": ...}` pointing at
the input findings that establish it, `why` naming the rule below that used it
(for example `tool grant: WebFetch`). In the stdout report, cap evidence at 20
entries per finding and add `evidence_total`; `capability.json` has them all.

`02.4-phrases` findings carry `patterns` (stable pattern ids from
`Library/patterns.yaml`). The rules below name pattern ids where a
check alone is too broad.

### Trifecta legs

Plain terms in reports (locked 2026-09-30, THREATS "Organizing frame"; since 2026-10-20 they
start with "Can", owner, review C31 part B): `private-data` = **Can read your data**,
`untrusted-content` = **Can take outside input**, `external-comms` = **Can send data out**.
Check IDs and field values are unchanged. The sections below keep the 2026-09-30 names as written.
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
(`02.4-phrases` `audience` `human`: README, docs, changelog, templates). They describe what
the user does, not what the artifact states or grants (2026-09-29, Case 004: README
install lines were the persistence and network evidence).

What does **not** establish a leg, and why:

- A skill with no grant of its own. It runs with the host's tools, but the
  artifact states nothing about them; `02.5-capability` maps what the artifact states.
- A `Bash` grant for `external-comms`. Bash can reach the network, but so can
  every shell; counting it makes every executing skill 3 of 3 and the map stops
  telling anything. Bash is recorded under `private-data` and in posture
  (`execute`). The report says this limit once (in the limits, `data/limits.md`).
- `K.telemetry` and `K.md-carrier`: documentation of other tools' behavior and
  markdown carriers, not a channel the artifact uses.

### Install grants

One `cap.grant` finding per grant kind **present**, `file` and `line` null. An
absent grant emits nothing.

| `grant` | Present when |
|---|---|
| `exec-at-load` | any `struct.hooks` finding (a hook runs a command on a harness event, not on the user's request); `evidence` names each event |
| `context-injection` | any `struct.description` (always-on text) or any hook on `SessionStart` or `UserPromptSubmit` |
| `persistence` | `phrase.E.env` with `E.persist-target`, `E.persist-redirect`, `E.memory`, `E.self-install`, `E.git-keys`, or `E.editor-autorun`; `phrase.E.perms` with `E.outlives-session` or `E.install-global` |
| `network` | any evidence that makes `external-comms` present, plus `phrase.E.perms` with `E.install-global` |
| `elevated` | `phrase.E.perms` with `E.perm-flags`, `E.allowlist`, or `E.confirm-off`; an agent or command inheriting all tools |

### Injection paths and bytes at load

REPORTING 5.1: bytes delivered into context before the first user input, by path.

- One `cap.injection` per `struct.description`: `mechanism: description`,
  `file` the defining file, `bytes` the UTF-8 length of the description,
  `basis: exact`.
- One `cap.injection` per hook on `SessionStart` (and `UserPromptSubmit`, marked
  with its `event`): `mechanism: hook`, `file` the hook config, `event`,
  `command`. `bytes`: the sum of the sizes of the files the hook's command script
  references (`02.3-graph` static edges out of the script file), `basis: estimate`;
  when the script is not in the tree or names no file, `bytes: null`,
  `basis: unknown`. `02.5-capability` never runs the hook to measure it.
- One `cap.load-bytes` per hook config (`file` the config; `file` null when no
  hook config injects at `SessionStart`): `bytes` the total over the
  descriptions plus that config's `SessionStart` hooks (each host runs its own
  config, so configs are never summed; changed 2026-09-29), `basis` `exact` when every part is
  exact, `estimate` when any part is estimated, and `unknown_parts` the count of
  parts with unknown bytes.

### Agent posture

One `cap.posture` per `struct.agent-tools` finding (`file` the definition,
`line` its line). Fields: `tools` (as `02.1-inventory` reported, null for inherit-all),
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
job; that comparison is a reading of the description, so `02.5-capability` records the
posture and the description side by side (`description` field) and a person
reads the match. A read-only posture is the one positive `02.5-capability` states on its
own (Case 002).

### Cross-stage pairs

One `cap.pair` per `02.4-phrases` `phrase.*` finding (not the part 2 tables) that sits on one of these, `file` and `line`
the phrase hit's:

| `pair` | The phrase finding's file or line is |
|---|---|
| `orphan+phrase` | a `graph.orphan` file |
| `dynamic+phrase` | a file whose `graph.depth` is `via: dynamic` (reached only through a load: a folder a config names, a code scan, or an instruction-file glob; `02.3-graph` marks folder and glob mentions elsewhere `via: mention`, and those do not pair, 2026-09-29) |
| `hidden+phrase` | inside a `read.divergence` with `reading: A-only` (from its `line` through the lines its `text` spans), or on a `read.fold` line when the hit matches only the folded text (`02.4-phrases` `folded: true`, 2026-10-09); except a hit made only of carrier patterns (`K.md-carrier`), which is the same fact as the divergence (2026-09-29) |

| `hook+phrase` | in a script a `SessionStart` or `UserPromptSubmit` hook runs (the hook's command script, plus files that script names directly), and the hit is an instruction-in-a-script pattern (`C.script-instruction`, `C.emit-instruction`): text that can reach the model through the hook's output (added 2026-09-29, Case 003) |

`${CLAUDE_PLUGIN_ROOT}` in a hook command resolves against the nearest folder
above the hook config that holds `.claude-plugin/plugin.json` (a plugin in a
subfolder of its repo), then the input root.

Fields: `pair`, `phrase_check`, `patterns`, `quote` (from the `02.4-phrases` finding),
and `evidence` citing both halves. A hit can be in more than one pair; emit one
finding per pair kind. Entry points are never orphans or dynamic-only, so their
visible lines never pair.

### Checks

| Check | One finding per | Fields |
|---|---|---|
| `cap.leg` | trifecta leg, always three (`file`, `line` null) | `leg`: `private-data`, `untrusted-content`, `external-comms`; `present`: bool; `evidence` |
| `cap.grant` | install grant present (`file`, `line` null) | `grant`: `exec-at-load`, `context-injection`, `persistence`, `network`, `elevated`; `evidence` |
| `cap.injection` | path by which text reaches context at load | `mechanism`: `description` or `hook`; `event` (hooks); `bytes`: int or null; `basis`: `exact`, `estimate`, `unknown` |
| `cap.load-bytes` | hook config (`file` the config), or run (`file` null) when none injects at load | `bytes`; `basis`; `unknown_parts` |
| `cap.posture` | agent or command definition | `tools`; `posture`: list; `least_privilege`: bool; `description` |
| `cap.pair` | phrase hit on an orphan, a dynamic-only file, or hidden text | `pair`; `phrase_check`; `patterns`; `quote`; `evidence` |

### Added 2026-09-30: outside code and connectors (locked trifecta definitions)

Since 2026-10-20 the legs are named "Can read your data", "Can take outside input", and "Can send
data out" (review C31 part B); the definitions below are unchanged.

- **Takes outside input** also counts third-party code brought onto the machine:
  `02.4-phrases` `E.clone` (git clone, gh repo clone, submodule add, degit, "clone the repo"),
  `E.install`, `E.install-global`, `E.runtime-install`. Human-facing text (a README's
  install line) never counts.
- **Reads your data** also counts connected accounts: `02.4-phrases` `E.connector` (widened:
  connect / link / authorize / sign in with your Gmail, Drive, Outlook, Slack, Notion,
  GitHub, ...), an MCP server whose name, command, or URL names such a service, and an
  agent tool `mcp__<service>__...` for one (`connector_names` in `Library/capability.yaml`, read as
  `CONNECTOR_NAMES` by `rules.py`).
- Neither source counts toward **Sends data out**: bringing code in or reading an account
  sends nothing.

## run

The single entry point for `02.5-capability`. Gets the `02.1-inventory` to `02.4-phrases` reports, derives the
capability map (`legs`, `injection`, `posture`, `pairs`), and prints one
contract-1 report (`stages/CONTRACT.md`). It detects nothing.

### Inputs

```
python stages/02-coded/02.5-capability/run.py <input_dir> [--reports <dir>] [--out <dir>]
```

- `--reports <dir>`: saved stage reports for this input (`inputs.load_dir`).
  Without `graph.json` in it, hook bytes are `unknown` and stderr says why.
- Without it: `inputs.run_stages` with the same Python, in a temporary folder
  outside the input that is removed afterwards.

### Outputs

stdout: `{"stage": "02.5-capability", "contract": 1, "findings": [...]}`, in this
order: three `cap.leg`, the `cap.grant` findings, the `cap.injection` findings,
one `cap.load-bytes`, the `cap.posture` findings, and the `cap.pair` findings. What ships, what it
costs, and whether the tools fit (`cap.ship`, `cap.context`, `fit.*`) were here until restructure
step 4 and are `02.6-builder`'s now (`../02.6-builder/specs/builder.SPEC.md`); that step reads this
report's `cap.injection` and `testdata+loaded` findings. Every finding carries `evidence` and `evidence_total` (the full count); on
stdout `evidence` holds at most `EVIDENCE_CAP` (20) entries.

stderr: the standing limit notes (`rules.LIMITS`), one line per skip carried
forward from an input stage (stage, check, file, reason), and a one-line map
summary (legs present of three, stated flatly).

`--out <dir>`: also writes `<dir>/capability.json`, the same report with every
evidence list whole (written whole or not at all: to a temporary file, then renamed over it, so a disk that fills leaves no
half of it for the report stage to trip on). The folder is created if needed. An `--out` inside
`<input_dir>` is refused (exit 2).

Exit 0 when a report was produced. Exit 2 for a missing or non-folder input, an
unreadable or invalid `--reports` folder, or a refused `--out`. Exit 1 when an
input stage fails.

### Must never

- Print anything but the report to stdout.
- Write inside `<input_dir>`; write anywhere without `--out` except its own
  temporary folder.
- Import another stage's code, run anything from the input, or fetch a URL.
- Conclude, score, rank, or render a verdict; omit an absent leg.

### Done when (each backed by a test in `tests/test_run.py`)

1. With `--reports` holding small inline reports, stdout parses as a contract-1
   report with stage `02.5-capability`, exit 0, every finding has `check`,
   `file`, `line`, `evidence`, and there are exactly three `cap.leg`.
2. The findings follow the stated order, and a map with all three legs states
   them `present` true.
3. A finding with more than 20 evidence entries is capped on stdout with
   `evidence_total` the full count, and `--out` writes `capability.json` with
   the full list; `--out` inside the input is refused.
4. A skip in an input report is named on stderr and the run still exits 0.
5. A missing input folder exits 2 with nothing on stdout; a `--reports` folder
   missing a report exits 2; the input is byte-identical after a run.
6. No finding has a field named risk, severity, score, or verdict.

### What the step looked at (added 2026-10-30, M9 slice C)

The report's `coverage` list (`stages/CONTRACT.md`, "Coverage lines") has eight lines. This step reads no file; it derives the
map from the earlier steps' findings, so its items are the entries of its own tables and those findings. `of` is counted in
`run.py` (`count_inputs`) from the findings the check is given, before the check runs, and each check counts `looked_at` inside
its own function.

| Checks | Unit | `of` | `looked_at` |
|---|---|---|---|
| `cap.leg` | `legs` | the legs in `Library/capability.yaml` | each leg judged in `legs` |
| `cap.grant` | `grants` | the grants in the table | each grant judged in `grants` (one with no evidence too) |
| `cap.injection` | `entries` | the descriptions and the hooks on an injecting event | each path made in `injections` |
| `cap.load-bytes` | `entries` | one total for each hook config on a counted event, or one for the descriptions alone | each total made in `_total` (the totals sum the paths `cap.injection` made) |
| `cap.posture` | `entries` | the inventory's agent and command definitions | each posture made in `postures` |
| `cap.pair` | `findings` | the phrase hits (after test data is set aside), the files reached by a direct reference (test data a model is pointed at), and the references a model would follow (pictures) | each tried in `pairs`, `loaded_pairs`, and `image_pairs` |
| `cap.limit` | `findings` | the read-only lines a model reads | each paired in `stated_limits` |
| `cap.testdata` | `findings` | every finding of the inventory and the phrase step | each kept or set aside in `set_aside` |

Nothing here is explained by a skip: a skip an earlier step carried forward is that step's. A check that is not run, or run
on fewer items than it was given, leaves `looked_at` below `of` (`tests/test_coverage.py`, a test for each line).

### History

- 2026-10-30: M9 slice C: the report has a `coverage` list (above, "What the step looked at"). The findings are unchanged.
- 2026-10-29: restructure step 8b: the "carried forward" note and the no-`graph.json` note name the earlier step
  by its plain name (`carried forward from the step "What the text asks for": ...`), since a note that matches
  a limit word reaches `data/limits.md` and `details.html`. Their ids are not on a page. The two standing limits
  of `Library/capability.yaml` begin `standing limit:` (they began `stage 5 limit:`, and the second said
  "stage 3 static edges"); only the note text on stderr changes, so `02.5-capability.json` and `capability.json`
  are the same. The report's `STANDING_NOTE` accepts both wordings.
- 2026-10-31: M9 slice C, fix round: `cap.load-bytes` is a line of its own (its items are the totals; the paths are `cap.injection`'s). The findings are unchanged.

## images

Added 2026-10-07.

Finds images a model is pointed at. A model with vision reads text in an image, instructions
included, while a person skimming the repository sees a picture. An image reaches the model
only when a file the model reads points at it, so the reference is the signal; OCR (`02.2-reader`)
and a model read of the pixels are extra detail. This replaces "every image needs OCR"
as the question the report asks.

### Inputs

`02.1-inventory` (`inv.file`: `ext`, `type`), `02.2-reader` (`read.unread`, `read.divergence` with carrier
`image-text`), `02.3-graph` (`graph.json` edges; `graph.depth` when graph.json is absent). Audience
by path from `02.4-phrases`'s `audience.audience`.

### Outputs

`image_pairs(reports, graph)`: one `cap.pair` with `pair: image+loaded` per image file that a
file with audience `model` or `subagent` references with a static reference or a load
(`kind: static`, or `load: true`). Fields:

- `file`: the image; `from`: the first referencing file (sorted); `froms`: every one.
- `read`: what `02.2-reader` got of its text: `svg` (read from the source), `ocr-text` (OCR found
  text), `ocr-empty` (OCR ran, found none), `unread` (with `reason`, e.g. OCR not installed).
- `evidence`: one row per referencing file and line.

An image is `inv.file` with an image extension (`IMAGE_EXTS`, SVG included) or an `image/`
content type. `run.derive` computes the pairs before test data is set aside, so an image under
tests/ that a model-read file points at still counts.

### Must never

- Pair a reference from a human-facing file (README, docs), a script, or test data.
- Pair a reference in a config file (edge `form: config`, or a `.json`, `.yaml`, `.toml`
  source): a manifest's icon is for the host's UI, not the model (found on two
  repositories, 2026-10-07).
- Pair an image that is only mentioned through a folder or glob (`load: false`).
- Read or decode the image itself: what is in it comes from `02.2-reader`.

### Done when (each backed by a test in `tests/test_images.py` or the `02.5-capability` fixtures)

1. A skill's static reference to an image gives the pair, with every referencing file.
2. References from a README, from test data, from a config file, and folder mentions give
   no pair.
3. `read` reports `unread` with the reason, `ocr-text`, `ocr-empty`, or `svg`.
4. Without graph.json, `graph.depth` static records give the pair.
5. Fixture `image-loaded`: the skill's image pairs; the README's banner and the unreferenced
   image do not.

Added 2026-10-18 (review C36): `from_line`, the line in `from` that references the image, so a
review card can show where the model is pointed at it (grader row `cap-img-from-line`).

### History

- 2026-10-29: restructure step 7b: the reports are keyed by stage name, and an evidence entry's `stage` is the stage's
  name (`02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`), not a two-digit number.

## injection

The paths by which text reaches context at load (`cap.injection`) and the total
bytes delivered before the first user input (`cap.load-bytes`), REPORTING 5.1.
`02.5-capability` never runs a hook to measure it.

### Inputs

- `reports`: `{"02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases"}` contract-1 reports, keyed by stage name (reads `02.1-inventory`).
- `graph`: `02.3-graph`'s `graph.json` (`nodes`, `edges`), or `None`.

### Description paths

One `cap.injection` per `struct.description` (not skipped):
`mechanism` `description`, `file` and `line` the description's, `bytes` the
UTF-8 length of its `text`, `basis` `exact`, `evidence` the description.

### Hook paths

One `cap.injection` per `struct.hooks` finding whose `event` is in
`INJECTION_EVENTS` (compared case-insensitively): `mechanism` `hook`, `file` the
hook config, `line` the hook's, `event` and `command` as `02.1-inventory` gave them.

The hook's **scripts** are the input files its command names:

1. every `static` edge in `graph` out of the hook config whose `text` appears
   in one of the hook's commands (`commands`, else `command`);
2. every whitespace-separated token of a command, with quotes, a leading
   `${VAR}/` or `$VAR/`, and a leading `./` removed, that equals a node path
   relative to the input root or to the hook config's folder (so a wrapper's
   argument, `run-hook.cmd session-start`, names `hooks/session-start` too).

`bytes` is the sum of the `02.1-inventory` `inv.file` `bytes` of every distinct target of
a `static` edge out of any script, the scripts themselves excluded; `basis`
`estimate`. When `graph` is `None`, no script is found, or the scripts name no
file: `bytes` null, `basis` `unknown`.

`evidence`: the `struct.hooks` finding (`why` `hook event: <event>`), then one
entry per counted edge: `{"stage": "02.3-graph", "check": "graph.edge", "file": <script>,
"line": <edge line>, "why": "hook script reads <target> (<n> bytes)"}`.

A `${CLAUDE_PLUGIN_ROOT}/...` command token also resolves against each folder
above the hook config that holds `.claude-plugin/plugin.json`, nearest first
(2026-09-29: a plugin in a repo subfolder, Case 003).

### Load bytes

`load_bytes(injections)`: one `cap.load-bytes` **per hook config** (`file` the
config, `line` null), over the description paths plus that config's hook paths
whose event is in `LOAD_BYTES_EVENTS`. Each host runs its own config, never all
of them, so a sum across configs double counts (changed 2026-09-29, one repository:
8,077 summed, 4,969 per host). With no such hook, one finding with `file` null
over the descriptions alone. Per finding:

- `bytes`: the sum of the known parts' bytes (0 with no parts).
- `unknown_parts`: the count of parts with `bytes` null.
- `basis`: `exact` when every part is exact (including no parts); `unknown`
  when there are parts and every one is unknown (then `bytes` is null);
  otherwise `estimate` (any part estimated or unknown beside a known part).
- `parts`: the count of parts; `evidence`: one entry per part pointing at its
  source finding.

### Outputs

`injections(reports, graph)` returns description paths (file, line order) then
hook paths (file order, then `02.1-inventory` order). `load_bytes(injections)` returns
the list, sorted by config path.

### Must never

- Run a hook or script, or read any file content; sizes come from `02.1-inventory`.
- Present an estimate or unknown as exact.

### Done when (each backed by a test in `tests/test_injection.py`)

1. A description of `"héllo"` gives `bytes` 6, `basis` `exact`.
2. A `SessionStart` hook whose config edge reaches `scripts/inject.sh`, which
   has a static edge to `SKILL.md` (658 bytes), gives `bytes` 658, `basis`
   `estimate`, and evidence naming the edge.
3. A wrapper command `"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" session-start`
   counts the files `hooks/session-start` reads.
4. A hook whose script is not in the tree, or names no file, or with no graph,
   gives `bytes` null, `basis` `unknown`.
5. A `UserPromptSubmit` hook gives a `cap.injection` with its `event` but is not
   counted in `cap.load-bytes`; a `PreToolUse` hook gives none.
6. `load_bytes` is `exact` over exact parts, `estimate` with one estimate,
   counts `unknown_parts`, is `unknown` with `bytes` null when every part is
   unknown, and is 0 `exact` with no parts.
7. Two hook configs give two `cap.load-bytes`, each the descriptions plus that
   config's hook, never their sum.

### History

- 2026-10-29: restructure step 7b: the reports are keyed by stage name, and an evidence entry's `stage` is the stage's
  name (`02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`), not a two-digit number.

## inputs

Gets the `02.1-inventory` to `02.4-phrases` reports (and `02.3-graph`'s `graph.json`) for one input from a folder of
saved reports. Stage code is never imported. A stage run on its own (the grader) has no such
folder: `run.py` has `stages/_shared/earlier_steps.py` run the steps this one reads
(`stages.json`, `reads`) into a temporary folder and reads that (restructure step 7; before, this
module ran them itself, `run_stages`, and the stages kept four more copies).

### Inputs

- `load_dir(reports_dir)`: a folder holding `02.1-inventory.json`,
  `02.2-reader.json`, `02.3-graph.json`, `02.4-phrases.json`, and optionally
  `graph.json`.
- `READS`: the steps it reads, built from `stages.json` (`stagelist.reads`); the reports are keyed by these
  stage names; no table of its own.
- `skips(reports)`: the loaded reports.

### Outputs

- `load_dir` returns `(reports, graph)`: `reports` is
  `{"02.1-inventory": {...}, "02.2-reader": {...}, "02.3-graph": {...}, "02.4-phrases": {...}}`, each a contract-1
  report; `graph` is the parsed `graph.json`, or `None` when `load_dir` finds
  none.
- Each report must parse as JSON, have `contract` 1, the right `stage`
  (`02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`), and a `findings`
  list. Otherwise `ReportError` (message names the stage).
- A missing report file in `load_dir` is a `ReportError`.
- `skips(reports)` returns `[(stage, finding)]` for every finding carrying
  `skipped`, in stage order.

### Must never

- Import code from another stage, or run anything from the input.
- Write anywhere but `work_dir`.
- Treat a skip in an input stage as a failure.

### Done when (each backed by a test in `tests/test_inputs.py`)

1. `load_dir` on a folder of four valid reports plus `graph.json` returns them
   keyed by stage name and the graph; without `graph.json` the graph is `None`.
2. A missing report file, a report with the wrong `stage`, or `contract` other
   than 1 raises `ReportError`.
3. `READS` is built from `stages.json` (`test_the_steps_it_reads_come_from_the_stage_list`).
4. `skips` lists a skipped finding with its stage.

(Running the steps for a stage on its own, and a runner that fails, are covered in `stages/_shared/specs/shared.SPEC.md`, section `earlier_steps`.)

### History

- 2026-10-29: restructure step 7: `run_stages`, `_runner`, and `StageFailure` left for `stages/_shared/earlier_steps.py`;
  `NAMES` is built from `stages.json`.
- 2026-10-29: restructure step 7b: the reports are keyed by stage name (`READS`), not by a two-digit number.

## legs

The trifecta legs (`cap.leg`) and the install grants (`cap.grant`), derived from
`02.1-inventory` and `02.4-phrases` findings by the rules in `rules.py` (`LEG_RULES`,
`GRANT_RULES`). One engine applies both tables.

### Inputs

- `reports`: `{"02.1-inventory": report, "02.2-reader": report, "02.3-graph": report, "02.4-phrases": report}`
  (contract-1 reports, keyed by stage name; only `02.1-inventory` and `02.4-phrases` are read here).

### Evidence

`evidence(rule, reports)` returns the list of entries a rule establishes. Each
entry is `{"stage", "check", "file", "line", "why"}` pointing at one input
finding:

| Rule key | Input finding | `why` |
|---|---|---|
| `phrase_any` | `02.4-phrases` finding with that check | `<check>: <its patterns, comma-joined>` |
| `phrase_patterns` | `02.4-phrases` finding with that check and a listed pattern | `<check>: <the listed patterns it carries>` |
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
  patterns or tools, not one per pattern). Entries are ordered by stage (its place in the stage list), then
  file, then line, then check, and exact duplicates are dropped.

### Outputs

- `legs(reports)`: always three `cap.leg` findings in `LEGS` order:
  `{"check": "cap.leg", "file": null, "line": null, "leg", "present", "evidence"}`.
  `present` is true exactly when `evidence` is non-empty.
- `grants(reports, leg_findings)`: one `cap.grant` per grant kind with
  non-empty evidence, in `GRANTS` order:
  `{"check": "cap.grant", "file": null, "line": null, "grant", "evidence"}`.
  `network` takes the `external-comms` leg's evidence plus its own rule.

### Must never

- Emit a grant with no evidence, or omit a leg.
- Count `Bash` toward `external-comms`, or count `K.telemetry` or
  `K.md-carrier`.
- Name a field risk, severity, score, or verdict; add up legs into a number.

### Done when (each backed by a test in `tests/test_legs.py`)

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

### Added 2026-09-29

- A `02.4-phrases` finding with `audience` `human` is never evidence. Test:
  `test_human_audience_phrase_evidence_is_ignored`.
- A rule with `mcp_servers: true` takes each `struct.mcp` as evidence (`MCP server:
  <name>`). Test: `test_mcp_server_in_a_manifest_counts_toward_untrusted_and_external`.
- Rules may take `phrase_patterns` for `phrase.E.env` / `phrase.E.perms` (clone and
  installs for leg 2, `E.connector` for leg 1) and `connector_names: true`: a
  `struct.mcp` or an `mcp__` tool grant whose name matches `CONNECTOR_NAMES` is leg 1
  evidence. Tests: `test_clone_and_installs_take_outside_input`,
  `test_connectors_read_your_data` (2026-09-30).

### History

- 2026-10-29: restructure step 7b: the reports are keyed by stage name, and an evidence entry's `stage` is the stage's
  name (`02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`), not a two-digit number.

## limits

Stated limits and what backs them (review C32, partner's v3, 2026-10-14; built 2026-10-17). A line
that tells the AI to stay read-only is wording; whether a tool setting enforces it is a separate
fact. Derived from `02.1-inventory` and `02.4-phrases`; detects nothing new.

### Inputs

`stated_limits(reports)`: the inventory and phrase reports (keys `02.1-inventory`, `02.4-phrases`), after test data is set aside.

### Which lines

A `02.4-phrases` finding in instruction text (audience `model` or `subagent`) that states a read-only limit:
a phrase hit with `B.safety-adjective` whose line says "read-only", "read only", or "no side
effects", or a `term.safety` definition of such a word. One finding per file and line.

### Outputs

One `cap.limit` per line: `file`, `line`, `quote`, `limit` (`read-only`), and:

- `owner`: the file itself when it is a skill, agent, or command entry point; otherwise the
  `SKILL.md` of the nearest skill folder above it; None when neither.
- `owner_tools`: the owner's tools list from `02.1-inventory` (`struct.agent-tools`), None when it has none.
- `status` and `backed_by`, first match wins:
  1. `backed`, `flag`: a `02.4-phrases` `limit.setting` on the same line rules out writing.
  2. `backed`, `tools-list`: the owner's tools list has no writing tool and no Bash.
  3. `contradicted`: the owner's tools list has a writing tool, Bash, or `*`.
  4. `stated`: none of these. Stated in the text; Walkdown found no tool setting that enforces it.
- `flags`: the kinds of the same-line settings that rule out writing (empty unless `flag`).
- `other_routes`: `{file, line, what}` for other routes inside the owner's skill folder that can
  write: a `limit.setting` that grants writing, or an agent or command with no tools list or a
  write-capable one. `other_route_at`: the same as `file:line` strings. Empty for an agent or command
  that owns its own file, and when no skill folder holds the line.
- `evidence`: the wording, then whatever decided the status, then each other route.

### Must never

- Detect: every input is a `02.1-inventory` or `02.4-phrases` finding.
- Say a limit is broken or ignored. `stated` means Walkdown found nothing that enforces it, which is
  as far as a static read goes.
- Count test data (set aside before this runs).

### Done when (each backed by a test in `tests/test_limits.py`)

1. A skill whose `allowed-tools` has no writing tool backs its read-only line (`tools-list`); one
   with Bash or Edit contradicts it; one with no tools list leaves it `stated`.
2. A restricting `--tools` list on the same line backs it (`flag`), whatever the owner's list.
3. A reference file under a skill folder is owned by that skill's `SKILL.md`.
4. A setting that grants writing elsewhere in the same skill folder is listed in `other_routes`; one
   in another skill is not.
5. A line a person reads (audience `human`) or without a read-only word gives no `cap.limit`.
6. The grader's `cap-limit-*` rows in `Fixtures/ANSWERS/02.5-capability.json` pass.

### History

- 2026-10-29: restructure step 7b: the reports are keyed by stage name, and an evidence entry's `stage` is the stage's
  name (`02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`), not a two-digit number.

## pairs

Cross-stage pairs (`cap.pair`): a `02.4-phrases` phrase hit that sits on an orphan
file, on a file reached only dynamically, or on hidden text. The pair is a
pointer for a human, read first; it is not a conclusion.

### Inputs

- `reports`: `{"02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases"}` contract-1 reports, keyed by stage name.
  The runner masks the lines the secret scan flagged in the saved `02.2-reader` report right after this step
  (`pipeline.mask_saved_reader`), since this is the last step that needs its hidden words. `02.1-inventory` and `02.3-graph`
  stay as they are until `02.6-builder` has read them, so this step has a hook's command to find its script by and a description's
  words to count (`pipeline.mask_saved`). This step's own report holds copies of those words (`cap.injection`'s `command` and `event`,
  `cap.posture`'s `tools` and `description`, `cap.limit`'s `owner_tools`, and an evidence entry's `why`), which go with them
  (`secretmask.mask_copies`), in `capability.json` too.

### Rules

For every `02.4-phrases` finding (not skipped, `file` set, and `line` or `text_line` set). A hit in
the extracted text of a PDF, DOCX, or image (`line` null, `text_line`, 2026-10-18) is placed by
`text_line` and is covered only by `02.2-reader` findings placed by `text_line` in the same file;
line-placed and text-line-placed findings never cover each other:

| `pair` | Holds when | Second half of the evidence |
|---|---|---|
| `orphan+phrase` | the file has a `graph.orphan` finding | `02.3-graph` `graph.orphan` (`why` `orphan file`) |
| `dynamic+phrase` | the file's `graph.depth` has `via` `dynamic` | `02.3-graph` `graph.depth` (`why` `reached only by a dynamic load`) |
| `hidden+phrase` | a `read.divergence` in the same file with `reading` `A-only` covers the line (from its `line` through `line` + the number of line breaks in its `text`) and holds one of the hit's matched words in its `text` (both through `_plain`, which starts from `library.read_hidden`: a run of variation selectors that spells text (`library.runs` and `library.run_text`, P1 2026-10-29: selectors in a row or with only stripped characters between them, the text read from the selectors alone) is read as that text, then tag characters are read as the ASCII they spell (2026-10-25, review C42); every character `Library/invisible.yaml` strips and every other run dropped, then NFKC, then any other format (Cf) character dropped, lower case, white space collapsed; a hit with no `matches` keeps the line rule; 2026-10-21, an outside tester: a visible `<pre>` instruction paired with a hidden button label on the same source line), or a `read.fold` is on the same file and line and the hit is `folded: true` (it matches only the folded text; 2026-10-09) | each covering `02.2-reader` finding (`why` `hidden text: <carrier>` or `folded line`) |

The first evidence entry is the phrase hit itself (`stage` `02.4-phrases`, its check,
file, line, `why` `phrase hit`).

### Outputs

`pairs(reports)`: one finding per (phrase hit, pair kind) that holds:
`{"check": "cap.pair", "file", "line" (the hit's), "pair", "phrase_check",
"patterns", "quote", "evidence"}`, plus `text_line` for a hit in extracted text (`line` null),
ordered by file, line (null first), text line, phrase check, then `PAIRS` order.

### Must never

- Read a file, or re-run a pattern.
- Pair a hit with a `B-only` divergence, a different file, or a line outside
  the divergence's span.

### Done when (each backed by a test in `tests/test_pairs.py`)

1. A hit in a `graph.orphan` file gives `orphan+phrase` with both halves in
   evidence and the hit's `patterns` and `quote`.
2. A hit in a file whose depth is `via` `dynamic` gives `dynamic+phrase`; `via`
   `static` gives nothing.
3. A hit on line 7 inside an `A-only` divergence at line 7 gives
   `hidden+phrase`; a divergence at line 5 whose `text` spans three lines covers
   line 7; a `B-only` divergence or a hit on another line gives nothing; a
   `read.fold` on the hit's line gives `hidden+phrase` only when the hit is `folded: true`
   (an en dash folds too; a hit that matches the raw line is not hidden by the fold).
4. A hit that is both orphan and hidden gives two findings, one per kind.
6. A hit whose patterns are all in `CARRIER_PATTERNS` (`K.md-carrier`: the
   `02.4-phrases` pattern that detects the markdown carrier itself) makes no
   `hidden+phrase`: it is the same fact as the divergence (2026-09-29, Case 003).
5. No `02.4-phrases` findings give no pairs.
8. A hit at `text_line` 3 of a PDF inside an `A-only` divergence at `text_line` 3 gives
   `hidden+phrase` with `line` null and `text_line` 3; a divergence at `line` 3 of the same
   file does not cover it.
7. `hook+phrase`: a `C.script-instruction` or `C.emit-instruction` hit in the
   script a `SessionStart` hook runs, or in a file that script names, pairs; the
   same hit under a `PostToolUse` hook, or in a script no hook runs, or a hit on
   another pattern, does not. `pairs(reports, graph)` takes `02.3-graph`'s graph.
9. A hit whose matched word is on the divergence's line but not in its hidden text gives no `hidden+phrase`; a word split by a zero-width character in the hidden text still pairs.
10. A sentence in tag characters pairs with the hit read from it (review C42; `test_tag_characters_pair_with_the_words_they_spell`).
11. `_plain` drops every character the list strips (U+180E, U+034F, the blank letters and cells, and the rest) and every run, keeps one variation selector alone, and reads a run that spells text as that text; a sentence hidden in selectors pairs with the hit read from it, and a word split by U+180E still pairs (`test_plain_drops_what_the_invisible_list_strips_and_every_run`, `test_plain_reads_a_run_that_spells_text_as_that_text`, `test_a_run_of_variation_selectors_pairs_with_the_words_it_spells`); zero-width spaces between the selectors hide nothing (`test_plain_reads_a_run_interleaved_with_stripped_characters`), and neither does a Mongolian selector among them (`test_a_mongolian_selector_inside_a_run_does_not_hide_its_text_from_the_pairing`).

### History

- 2026-10-29 (P1): `_plain` reads the invisible-character list (`Library/invisible.yaml`, through
  `stages/_shared/library.py`) where it had dropped only the Cf category, so the characters the list
  adds that are not Cf (the blank letters and cells, the variation selectors) are dropped too, and a
  run that spells text is read as that text, as a tag run is.
- 2026-10-29 (P1, review before verification): a run is selectors in a row or separated only by
  characters the list strips, and it is found before the tag run is read, so a zero-width space (or a
  tag run) between selectors no longer hides the text they spell.
- 2026-10-29 (P1, after verification): the text of a run is decoded from its byte selectors alone, so a
  Mongolian selector among them no longer hides it.
- 2026-10-29: restructure step 7b: the reports are keyed by stage name, and an evidence entry's `stage` is the stage's
  name (`02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`), not a two-digit number.
- 2026-11-01: this step reads the words of `02.2-reader` before the mask of a flagged line, so its pairs do not move with it
  (`stages/_shared/tests/test_pipeline.py`, `test_the_saved_reader_is_masked_once_the_pairs_have_read_it`).
- 2026-11-01: its copies of `02.1-inventory`'s words are masked after `02.6-builder` has read them, and the bytes, the scripts a hook
  names, and the legs are worked out before that, so none of them moves
  (`stages/06-report/tests/test_secret_fields.py`, `test_the_steps_read_the_words_before_they_were_masked`).

## posture

Each agent or command definition's tool posture (`cap.posture`), from `02.1-inventory`
`struct.agent-tools`, by the tool-to-word table in `rules.py`. The stated job
sits beside the posture; `02.5-capability` does not judge whether they match.

### Inputs

- `reports`: `{"02.1-inventory", ...}` contract-1 reports, keyed by stage name (reads `02.1-inventory`).
- `words(tools)`: a tool list, or `None` for inherit-all.

### Outputs

- `words(tools)`: the sorted list of distinct posture words. `None` gives
  `["all"]`. Each name is trimmed and a trailing argument scope removed
  (`Bash(git:*)` is `Bash`), then looked up case sensitively in
  `POSTURE_WORDS`, else by prefix in `POSTURE_PREFIXES` (`mcp__x` is
  `network`), else `other`. An empty list gives `[]`.
- `least_privilege(posture)`: true only when `posture == ["read"]`.
- `postures(reports)`: one finding per `struct.agent-tools` (not skipped), in
  `02.1-inventory` order: `{"check": "cap.posture", "file", "line", "tools" (as `02.1-inventory`
  gave them, null for inherit-all), "posture", "least_privilege",
  "description", "evidence"}`; evidence is the `struct.agent-tools` finding
  (`why` `tool grant as stated`).

### Must never

- Compare the grant with the description, or score the posture.

### Done when (each backed by a test in `tests/test_posture.py`)

1. `[Read, Grep, Glob]` gives `["read"]`, least privilege true.
2. `[Read, Write, Edit, Bash]` gives `["execute", "read", "write"]`, false.
3. `None` gives `["all"]`, false; `tools` stays null in the finding.
4. `WebFetch`, `mcp__github__x` give `network`; `Task` gives `delegate`;
   `Frobnicate` and lowercase `read` give `other`; `Bash(git:*)` gives
   `execute`.
5. `postures` carries `file`, `line`, `description` from `02.1-inventory`.

### History

- 2026-10-29: restructure step 7b: the reports are keyed by stage name, and an evidence entry's `stage` is the stage's
  name (`02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases`), not a two-digit number.
- 2026-11-01: `_plain` reads hidden text through `library.read_hidden`, the tag rule's one place; what it compares did not change.

## rules

The `02.5-capability` rule tables, loaded. The tables are data in `Library/capability.yaml` (restructure
step 3b); `rules.py` reads that file and gives every other `02.5-capability` script the names below, so a
reader can check the Library file against "The rules" (above) line by line. `rules.py` holds no table and
no logic: each name is one assignment from the loaded file, as the type the constant always had.

### Inputs

`Library/capability.yaml`, found through `stages/_shared/library.py`. It is imported.

### Outputs

Constants:

- `LEGS`: the three leg names in report order: `private-data`,
  `untrusted-content`, `external-comms`.
- `GRANTS`: the five grant kinds in report order: `exec-at-load`,
  `context-injection`, `persistence`, `network`, `elevated`.
- `LEG_RULES` and `GRANT_RULES`: one rule per leg or grant. A rule is a dict
  whose keys are any of:
  - `phrase_any`: `02.4-phrases` checks that count with any pattern.
  - `phrase_patterns`: `{check: [pattern ids]}`; a `02.4-phrases` finding counts when
    its check is a key and one of its `patterns` is listed.
  - `tools`: tool names; an agent or command grant (`struct.agent-tools`)
    counts when its `tools` include one (compared after trimming, case
    sensitive).
  - `inherit_all`: true when a `struct.agent-tools` finding whose `tools` is
    null counts.
  - `hook_events`: `struct.hooks` events that count, or `"*"` for any hook.
  - `entry_points`: `02.1-inventory` `inv.file` `entry_point` kinds that count.
  - `descriptions`: true when any `struct.description` counts.
  - `legs`: legs whose evidence this grant takes over whole (`network` takes
    `external-comms`).
- `INJECTION_EVENTS`: hook events that give a `cap.injection`
  (`SessionStart`, `UserPromptSubmit`).
- `LOAD_BYTES_EVENTS`: hook events counted in `cap.load-bytes`
  (`SessionStart`).
- `POSTURE_WORDS`: tool name to posture word, exactly the posture table in "The rules".
- `POSTURE_PREFIXES`: name prefix to posture word (`mcp__` to `network`).
- `POSTURE_INHERIT_ALL` (`all`), `POSTURE_OTHER` (`other`),
  `LEAST_PRIVILEGE` (`["read"]`).
- `PAIRS`: the pair kinds in report order: `orphan+phrase`, `dynamic+phrase`,
  `hidden+phrase`, `hook+phrase` (a tuple).
- `HOOK_INSTRUCTION_PATTERNS` and `CARRIER_PATTERNS` (sets of `02.4-phrases` pattern ids): the patterns that
  are instruction text inside a script string (they make the `hook+phrase` pair), and the one that
  detects a markdown carrier itself (it makes no `hidden+phrase` pair on its own).
- `CONNECTOR_NAMES`: the regex of services whose servers or tools reach the user's own data (leg 1).
- `EVIDENCE_CAP`: 20, the stdout cap on evidence entries per finding.
- `LIMITS`: the standing limit notes printed on stderr every run (Bash is not
  counted toward `external-comms`; hook bytes are an estimate). Each begins `standing limit:`.

### Must never

- Hold a rule that "The rules" (above) does not state, or compute anything.
- Name a field risk, severity, score, or verdict.

### Done when (each backed by a test in `tests/test_rules.py`)

1. `LEGS`, `GRANTS`, and `PAIRS` list exactly the names in "The rules" in order.
2. Every pattern id named in `LEG_RULES` and `GRANT_RULES` exists in
   `Library/patterns.yaml` under the check it is filed under (the test
   reads the yaml as text; no code is imported).
3. `Bash` is not in `LEG_RULES["external-comms"]["tools"]`; `K.telemetry` and
   `K.md-carrier` are named by no rule.
4. `POSTURE_WORDS` maps every tool in the posture table of "The rules" to its word.
5. Every name is the value of `Library/capability.yaml` in the type the callers use (tuples for `LEGS`,
   `GRANTS`, `PAIRS`; sets for the two pattern sets), the file is dated and sourced, the two pattern
   sets name real pattern ids, and `rules.py` holds no table (`test_every_name_is_the_library_value_in_the_type_the_callers_use`,
   `test_rules_py_holds_no_table`).

### History

- 2026-10-29: restructure step 3b: the tables moved out of Python into `Library/capability.yaml`, with
  their dates and sources, and `rules.py` became a loader that exposes the same names (so no caller
  changed). Every name loads to the value, type, and order it had (checked as data against the old
  file). This spec's list of outputs gained `hook+phrase`, `HOOK_INSTRUCTION_PATTERNS`,
  `CARRIER_PATTERNS`, and `CONNECTOR_NAMES`, which the code already had.

## testdata

Added 2026-10-02.

Keeps test data out of the capability map. Fixtures and tests are never loaded as
instructions when an artifact is installed, so their hooks, grants, and phrase hits say
nothing about what installing it grants. (Walkdown's self-audit: its own attack samples lit
every leg and grant.)

### Inputs

`02.1-inventory` to `02.4-phrases` reports. Test data is decided by `02.4-phrases`'s `audience.is_test_data` (path rule).

### Outputs

- `loaded_pairs(reports)`: one `cap.pair` with `pair: testdata+loaded` per `graph.depth`
  finding whose file is test data, `via: static`, and whose `from` is not test data and has
  path audience `model` or `subagent`. `from` names the referencing file; `from_line` the line
  there that names it, from the graph's static edge (None without the graph; added 2026-10-18,
  review C36).
- `set_aside(reports, loaded)`: a copy of the reports without `02.1-inventory` findings on a test-data
  path and `02.4-phrases` findings with audience `test-data`, except files in `loaded`; and one
  `cap.testdata` finding counting what was removed (none when nothing was): `inventory_set_aside`
  (from the inventory report) and `phrases_set_aside` (from the phrase report).
- `run.derive` computes the pairs first, then sets test data aside, then derives legs,
  grants, injection, posture, and pairs from what remains.

### Must never

- Drop test data silently: the count is a finding, and the limits (`data/limits.md`) state the rule.
- Set aside a test-data file that a model-read file references directly.
- Change `02.1-inventory` to `02.4-phrases` findings: the set-aside is a copy used only for derivation.

### Done when (each backed by a test in `tests/test_testdata.py` or the `02.5-capability` fixtures)

1. Test data is removed from the inventory and phrase reports and counted in `inventory_set_aside` and
   `phrases_set_aside`.
2. Loaded test data is kept and paired; references from human-facing or test files are not.
   With the graph, the pair records `from_line` (`test_loaded_pair_records_the_line_that_points_at_it`).
3. Fixture `testdata-only`: no legs or install grants from samples under tests/.
4. Fixture `testdata-loaded`: the pair appears and the loaded file's text counts.

### History

- 2026-10-29: restructure step 7b: the reports are keyed by stage name, an evidence entry's `stage` is the stage's name,
  and the `cap.testdata` counts `stage1` and `stage4` are `inventory_set_aside` and `phrases_set_aside`.
- 2026-10-30: M9 slice B: this step writes its notes through `stagenote`, so a note that names a file or a path from the repository is one line, and a name with a line break cannot pass for a note of its own.

## Stage history

- 2026-10-29: restructure step 4: `cap.ship`, `cap.context` (what ships and what it costs in an AI's context, slice 1, 2026-10-26) and `fit.unused`, `fit.missing`, `fit.inherits`, `fit.hook`, `fit.checked` (do the tools fit the job, slice 5) were this stage's. They are `02.6-builder`'s now (`../02.6-builder/CONTEXT.md`), and this stage emits none of them. That step reads this one's `cap.injection` findings (the bytes a hook adds) and its `testdata+loaded` pairs (which test-data files stay in).
