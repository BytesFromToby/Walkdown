# hosts.py: spec

Is it ready for any AI? (plan for builders, slice 3, owner 2026-10-26; the slice spec is
`pre-planning/SPEC-SLICE3-2026-10-26.md`). Stage 4 calls it with the texts it reads, stage 1's
inventory, and stage 1's hook findings (`struct.hooks`). It reads nothing else and runs nothing.
Test data (`audience.is_test_data`) is left out throughout.

## Data: `hosts.yaml`

One row per host (`claude`, `codex`, `gemini`, `cursor`, `copilot`, `windsurf`, `agents-md`),
each with its source and the date checked: the instruction files it reads (`**/` means at any
depth), a `fallback` read only when none of those exist (Claude Code reads `AGENTS.md` only when
there is no `CLAUDE.md`), the folders it reads skills from, its MCP config files, and its hook
files. Then `copies` (instruction files kept one per host), `skill_keys` (the frontmatter keys of
the Agent Skills format), `claude_words`, and `claude_tools`. A host that changes is a data edit.

## Findings

**`host.coverage`**, one per host in `hosts.yaml` order, in every run (a fact per host, never a
fault): `host`, `name`, `instructions` (the files here it reads), `skills` (how many `SKILL.md`
sit in its skill folders, at any depth, plus for Claude Code a plugin's `skills/<name>/SKILL.md`
beside `.claude-plugin/plugin.json`), `skill_files`, `mcp`, `hooks` (stage 1's hook files that
are this host's: a file matching another host's `hooks` is that host's, any other is Claude
Code's).

**`host.drift`**, one per pair of `copies` files in one folder (`.github/copilot-instructions.md`
counts as the root folder's), the first in `copies` order as `file`, the other as `other`:
`relation` is `linked` when one is a symlink to the other, imports it (`@other` anywhere in a line,
as Claude Code and Gemini CLI read it), or is a short file (at most 10 lines that are not
headings) naming the other; else `same` when the text is equal line by line (trailing spaces and
line endings aside); else `differ`, with `only_here` and `only_there` (non-empty lines, trimmed,
found only in that file). A pair where one points to a third copy is left out: the pair with that
copy says it.

**`host.feature`**, in `SKILL.md` and `AGENTS.md` files, with `file`, `line`, `host`, `kind`,
`what`:

- `frontmatter`: a `SKILL.md` frontmatter key outside `skill_keys` that Claude Code knows
  (`trigger.yaml`; claude.ai and the Skills API refuse the skill; other hosts ignore the key). A
  key no host knows is `trigger.py`'s `trig.key` (owner, 2026-10-26);
- `claude-words`: a word from `claude_words` (`$ARGUMENTS`, `${CLAUDE_PLUGIN_ROOT}`, ...);
- `claude-tool`: a tool name from `claude_tools` as a whole word, or `Bash(...)` permission syntax;
- `import`: an `@path` in `AGENTS.md` outside code (fenced blocks and inline code), which no host
  but Claude Code and Gemini CLI expands, and those only in their own files;
- `hooks`: one per hook file (`line` null), `what` the host's name: each runs on one host only.

A host named in prose ("Claude will...") is not a feature (owner, 2026-10-26: common and usually
harmless). Stage 4 adds these findings last, after `need.*` and `port.*`.

## Must never

- Call a host's coverage a fault, or say which host a repository should support.
- Read a file outside the texts and inventory it is given.

## Done when

1. Fixture `hosts-repo` (grader 04, rows `hosts-*`): coverage for Claude Code, Cursor, Copilot,
   and Codex; one `differ` pair with its line counts and one `same` pair; a frontmatter key,
   `$ARGUMENTS`, and `WebFetch` on their lines; no feature in a skill with only Agent Skills keys.
2. `tests/test_hosts.py`: the fallback, plugin skills, hook owners, `linked` three ways, the
   Copilot file at the root, imports outside code only, and test data left out.

## History

- 2026-10-26: built (slice 3). Pointers measured on audited repositories the same day: a one-line
  CLAUDE.md and a 7-line GEMINI.md, each saying to read AGENTS.md, first came out as a `differ`
  pair with each other; now both are `linked` to AGENTS.md and their own pair is left out.
- 2026-10-26 (slice 4): frontmatter features only for keys Claude Code knows; a key no host knows
  (a typo, `version`) moved to `trig.key`. Cursor's hooks are `.cursor/hooks.json` (checked against
  cursor.com/docs/agent/hooks while building; the slice spec's table had only `environment.json`).
