# configs.py: spec

Parses hook configs and platform manifests. Stage 1, checks `struct.hooks` and
`struct.manifests`. Parsing only; no command is run and no referenced script is
opened.

## Inputs

- The decoded text and relative path of a `.json`, `.yaml`, or `.yml` file.

## Outputs

`load(rel, text) -> object | None`: `json.loads` for `.json`, `yaml.safe_load`
for `.yaml` / `.yml`; None on any parse error or other extension.

### Hooks

`is_hook_config(doc)`: `doc` is a JSON object whose `hooks` value is an object
with at least one event name mapping to a list.

`hook_findings(rel, doc) -> list[finding]`: one `struct.hooks` finding per entry
in each event's list, in file order:

- `event`: the event name. `matcher`: the entry's `matcher` verbatim, or None
  when the entry has none.
- Claude Code shape (`{matcher, hooks: [{type, command}]}`): `command` is the
  inner commands joined with a newline; `commands` lists them; `types` lists
  each inner `type`; `async` lists each inner `async` value where present.
  `format` is `nested`.
- Flat shape (`{command, matcher?}`, used by some other hosts): `command` is
  the entry's command; `format` is `flat`.
- `file` = `rel`, `line` = null (JSON gives no positions).

### Manifests

`manifest_grants(doc) -> list[str] | None`: None unless `doc` is an object with
a string `name`. Otherwise the sorted set of grant tokens found under any key
named `tools`, `permissions`, `allowedTools`, `allowed_tools`, `allowed-tools`,
or `capabilities`, at any depth:

- a list item gives its string form;
- inside a grant, an object's key with value `true` gives the key, a list
  recurses into its items, an object recurses, any other value gives `key=value`
  (JSON spelling: `network=false`).

`is_manifest(rel, doc)`: `doc` has a string `name`, and it either declares at
least one grant key (even empty) or its basename is a known plugin manifest
(`plugin.json`, `plugin.yaml`, `plugin.yml`, `marketplace.json`,
`gemini-extension.json`).

`manifest_findings(manifests) -> list[finding]`: `manifests` is a list of
`(rel, name, grants)`. Groups by `name`; one `struct.manifests` finding per
group, sorted by name: `file` null, `line` null, `name`, `files` (sorted),
`grants` ({file: tokens}), `divergent` True when the token sets are not all
identical (a set of one is never divergent).

## Must never

- Run a hook command or open the script it names.
- Judge a grant. `divergent` is a comparison, not a verdict.

## Done when (each backed by a test in `tests/test_configs.py`)

1. A Claude Code hooks file with two events gives one finding per matcher entry with event, matcher, and command.
2. A flat entry without a matcher gives `matcher` None and `format` `flat`.
3. JSON with no `hooks`, an empty `hooks` object, or unparsable text is not a hook config.
4. Grants from `tools: [...]` and from `permissions: {allowedTools: [...], network: true}` flatten to tokens.
5. Two manifests with one name and different grants give one finding with `divergent` True; identical grants give False; different names give two findings.
6. A `plugin.json` with a name and no grant is a manifest; a `package.json` with a name and no grant is not.
7. A YAML manifest loads through the safe loader.

## Added 2026-09-29: MCP servers

`mcp_findings(rel, doc)`: one `struct.mcp` per entry under a top-level `mcpServers`
mapping in any parsed config: `name`, `transport` (`type`, else `http` when a `url`
is given, else `stdio`), `command` (command plus args), `url`, `env_keys` (sorted
names; values are never recorded). Test: `test_mcp_servers_from_any_config`.
