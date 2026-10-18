# restrictions.py: spec

Settings that restrict what tools an agent can use (review C32, partner's v3, 2026-10-14; built
2026-10-17). A part 2 table: facts for stage 5 to pair with read-only wording. A restriction is
never a risk and never flagged on its own.

## Inputs

`settings_in_line(line)`: one folded line. `limit_file(rel, raw, folded, aud)`: a file's raw and
folded lines and its audience (any audience; consumers filter).

## Outputs

One `limit.setting` finding per setting a line names, with `file`, `line`, `quote` (the raw line),
`audience`, and:

| `kind` | Recognized as | Extra field | `rules_out` | `grants_write` |
|---|---|---|---|---|
| `tools-flag` | `--tools` with a quoted (possibly empty) or bare list of tool names | `tools` | `write` when the list has no writing tool (Write, Edit, MultiEdit, NotebookEdit) and no Bash; `shell` when it has no Bash; `network` when it has no WebFetch, WebSearch, or Bash; nothing when it has `*` | True when the list has a writing tool, Bash, or `*` |
| `deny` | `--disallowedTools` (or `--disallowed-tools`) with a list, or a JSON `"deny": [ ... ]` list on one line | `tools` | `write` when every writing tool and Bash are denied; `shell` when Bash is; `network` when WebFetch, WebSearch, and Bash are. A scoped deny such as `Bash(git push:*)` denies one use, not the tool | False |
| `sandbox` | `--sandbox <mode>` or `sandbox_mode = "<mode>"` (read-only, workspace-write, danger-full-access) | `value` | `write` for read-only | True for workspace-write and danger-full-access |
| `permission-mode` | `--permission-mode <mode>` or `defaultMode` (plan, default, acceptEdits, bypassPermissions, dontAsk) | `value` | `write` and `shell` for plan | True for acceptEdits and bypassPermissions |

A list is a tool list only when every item reads as a tool name (`Read`, `Bash(git diff:*)`,
`mcp__server__tool`, `*`); "the `--tools` section" is not a setting. A bare list stops at a quote,
a space, or a backtick, so a flag inside Markdown code reads the same as in a script.

## Must never

- Count `--allowedTools` as a restriction: it pre-approves the tools it names and leaves every
  other tool available.
- Judge a setting, or report one as a risk.

## Done when (each backed by a test in `tests/test_restrictions.py`)

1. `--tools "Read,Grep,Glob"` rules out write, shell, and network and grants no write; `--tools
   Read,Bash` rules out nothing and grants write; `--tools ""` rules out all three.
2. `--disallowedTools "Write,Edit,MultiEdit,NotebookEdit,Bash"` rules out write and shell; a JSON
   deny list with only `Bash(git push:*)` rules out nothing.
3. `--sandbox read-only` rules out write; `--sandbox danger-full-access` grants write;
   `--permission-mode plan` rules out write and shell.
4. `--allowedTools "Read,Grep"` and "the `--tools` section of the docs" are not settings; a list in
   backticks is read without the backtick.
5. The grader's `p2-lim-*` rows in `Fixtures/ANSWERS/04-phrases.json` pass.
