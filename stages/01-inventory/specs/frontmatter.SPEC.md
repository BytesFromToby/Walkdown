# frontmatter.py: spec

Parses a leading frontmatter block and reports its `description` and granted
tools. Stage 1, checks `struct.description` and `struct.agent-tools`.

## Inputs

- The decoded text of one markdown file (`.md`, `.markdown`, `.mdx`, `.mdc`)
  and its relative path.

## Outputs

`parse(text) -> Frontmatter | None`. None when the first line is not exactly
`---` (trailing whitespace allowed). Otherwise:

- `start_line`: 1. `lines`: the raw lines between the opening `---` and the
  closing line (`---` or `...`). A block with no closing line is None.
- `yaml`: the `yaml.safe_load` mapping, or None; `yaml_error`: the error text if
  the load failed or did not give a mapping.
- `first_colon`: a mapping from a first-colon split: each line of the form
  `key: value` at column 0 gives `key` and the value stripped of whitespace and
  one pair of matching surrounding quotes. Indented and non-matching lines are
  ignored.
- `key_line(key)`: the 1-based file line where `key:` starts at column 0, or None.

`description_finding(rel, fm) -> finding | None`: when either loader has a
`description`:

- `check` `struct.description`, `file`, `line` = `key_line("description")`.
- `text`: the YAML value verbatim (non-strings converted with `str`); when YAML
  failed, the first-colon value, and `loader` is `first-colon` instead of `yaml`.
- `loaders_disagree`: True when both loaders gave a value and they differ, or
  only one did. `first_colon_text` carries the first-colon value when they
  disagree.

`tools_value(fm) -> (field, list) | None`: the granted tools from `tools`, else
`allowed-tools`, else `allowedTools`. A list gives its items as strings. A
string splits on commas when it has one, otherwise on whitespace outside
parentheses; items are stripped and empties dropped.

`agent_tools_finding(rel, fm, kind) -> finding`: `check` `struct.agent-tools`,
`file`, `line` = the tools key line (None when absent), `tools` (list, or None
when the definition declares none), `description` (YAML value or first-colon
value, None if absent), `field` (which key), `kind` (`agent`, `command`, or
`skill`).

## Must never

- Execute or construct objects from YAML (safe loader only).
- Rewrite, trim, or normalize a description beyond what the loader returns.

## Done when (each backed by a test in `tests/test_frontmatter.py`)

1. A file without a leading `---`, or with an unclosed block, gives None.
2. A quoted description comes back unquoted and otherwise verbatim, with the line of its key.
3. A description with an unquoted `: ` that breaks YAML is still reported, via the first-colon loader, with `loader` `first-colon`.
4. A folded (`>`) description gives the YAML text and `loaders_disagree` True.
5. `tools` as a YAML list and as a comma string both give the same list.
6. `allowed-tools` with a space-separated value splits outside parentheses (`Bash(git add:*) Read` gives two items).
7. `agent_tools_finding` pairs the tools with the description and the tools line.
