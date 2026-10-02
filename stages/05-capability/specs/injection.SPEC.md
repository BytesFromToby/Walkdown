# injection.py: spec

The paths by which text reaches context at load (`cap.injection`) and the total
bytes delivered before the first user input (`cap.load-bytes`), REPORTING 5.1.
Stage 5 never runs a hook to measure it.

## Inputs

- `reports`: `{"01", "02", "03", "04"}` contract-1 reports (reads `01`).
- `graph`: stage 3's `graph.json` (`nodes`, `edges`), or `None`.

## Description paths

One `cap.injection` per `struct.description` (not skipped):
`mechanism` `description`, `file` and `line` the description's, `bytes` the
UTF-8 length of its `text`, `basis` `exact`, `evidence` the description.

## Hook paths

One `cap.injection` per `struct.hooks` finding whose `event` is in
`INJECTION_EVENTS` (compared case-insensitively): `mechanism` `hook`, `file` the
hook config, `line` the hook's, `event` and `command` as stage 1 gave them.

The hook's **scripts** are the input files its command names:

1. every `static` edge in `graph` out of the hook config whose `text` appears
   in one of the hook's commands (`commands`, else `command`);
2. every whitespace-separated token of a command, with quotes, a leading
   `${VAR}/` or `$VAR/`, and a leading `./` removed, that equals a node path
   relative to the input root or to the hook config's folder (so a wrapper's
   argument, `run-hook.cmd session-start`, names `hooks/session-start` too).

`bytes` is the sum of the stage 1 `inv.file` `bytes` of every distinct target of
a `static` edge out of any script, the scripts themselves excluded; `basis`
`estimate`. When `graph` is `None`, no script is found, or the scripts name no
file: `bytes` null, `basis` `unknown`.

`evidence`: the `struct.hooks` finding (`why` `hook event: <event>`), then one
entry per counted edge: `{"stage": "03", "check": "graph.edge", "file": <script>,
"line": <edge line>, "why": "hook script reads <target> (<n> bytes)"}`.

A `${CLAUDE_PLUGIN_ROOT}/...` command token also resolves against each folder
above the hook config that holds `.claude-plugin/plugin.json`, nearest first
(2026-09-29: a plugin in a repo subfolder, Case 003).

## Load bytes

`load_bytes(injections)`: one `cap.load-bytes` **per hook config** (`file` the
config, `line` null), over the description paths plus that config's hook paths
whose event is in `LOAD_BYTES_EVENTS`. Each host runs its own config, never all
of them, so a sum across configs double counts (changed 2026-09-29, superpowers:
8,077 summed, 4,969 per host). With no such hook, one finding with `file` null
over the descriptions alone. Per finding:

- `bytes`: the sum of the known parts' bytes (0 with no parts).
- `unknown_parts`: the count of parts with `bytes` null.
- `basis`: `exact` when every part is exact (including no parts); `unknown`
  when there are parts and every one is unknown (then `bytes` is null);
  otherwise `estimate` (any part estimated or unknown beside a known part).
- `parts`: the count of parts; `evidence`: one entry per part pointing at its
  source finding.

## Outputs

`injections(reports, graph)` returns description paths (file, line order) then
hook paths (file order, then stage 1 order). `load_bytes(injections)` returns
the list, sorted by config path.

## Must never

- Run a hook or script, or read any file content; sizes come from stage 1.
- Present an estimate or unknown as exact.

## Done when (each backed by a test in `tests/test_injection.py`)

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
