# trigger.py: spec

Will it trigger? (plan for builders, slice 4, owner 2026-10-26; the slice spec is
`pre-planning/SPEC-SLICE4-2026-10-26.md`). Stage 4 calls it with the texts it reads and stage 1's
inventory (each file's `entry_point` and `bom`). It runs nothing. Test data
(`audience.is_test_data`) is left out.

## Data: `trigger.yaml`

Dated, with sources (Claude Code's skills, subagents, and tools pages; the Agent Skills spec; the
published skill-authoring guidance): the frontmatter keys Claude Code knows for skills (commands
take the same) and for subagents; the documented values of `model`, `color`, `permissionMode`,
`effort`, `isolation`, `memory`, `context`, `shell`, and the boolean fields; Claude Code's tool
names and the older names not in the current list; the name and description limits; the listing
cap per entry (1,536 characters) and the listing's share of the context (1%); the subagent
warning (15,000 tokens); the "when" and person patterns; the overlap measure and its stop words.

## Entries

An entry is a `SKILL.md` (or `*.skill.md`), a Markdown file in a `commands/` folder, or one in an
`agents/` folder (stage 1's `entry_point`). An agents-folder file with no frontmatter, or with
neither a name nor a description, is documentation and no entry.

**Frontmatter** is the first non-blank line `---` to the next `---` or `...`, read as YAML; its
keys are the top-level `key:` lines.

**`trig.entry`**, one per entry: `kind`, `name` (a skill's folder or a command's file name when
none is given), `description_chars`, `listing_chars` (description, or a skill's or command's
first body line when it has none, plus `when_to_use`), `description_from`, `menu` (false with
`user-invocable: false`), `grants` (a subagent's `tools` or a skill's or command's `allowed-tools`, as
written; null when absent), `grants_line`, `disallowed`, `preloads` (a subagent's `skills`; slice 5),
and `mode`:

- `auto`: Claude chooses it by its description; `paths`: the same, only on matching files;
- `typed`: `disable-model-invocation` is true;
- `unread`: a skill or command whose frontmatter is not read (YAML that does not parse, or `---`
  not on the first line): it loads with no fields set;
- `skipped`, with `why`: a subagent Claude Code does not load (frontmatter not read; no name; a
  name and no description; a name starting with `-`, holding `:`, or over 256 characters).

## Findings

Each with `file`, `line` (the key's line when there is one), and `kind_of` (the entry's kind):

- **`trig.frontmatter`** `kind`: `yaml-error` (with the parser's first line), `not-first-line`,
  `missing` (a `SKILL.md` with none), `bom` (a byte-order mark before `---`; the docs do not say
  whether it is read).
- **`trig.rule`** `rule`, `host` (`agent-skills`: the spec, other hosts, uploads; `claude-api`:
  claude.ai uploads and the Skills API; `claude`: Claude Code). Skills: `name-missing`,
  `name-long`, `name-chars`, `name-folder` (a `SKILL.md` only), `name-reserved`, `name-xml`,
  `description-missing`, `description-empty`, `description-long`, `description-xml`. Skills and
  commands: `listing-cut` (`chars`, `lost`). Subagents: `agent-name`, `name-duplicate` (`other`).
- **`trig.guidance`** `kind`, published guidance and never a host rule, on entries that load:
  `no-when` (no `when_to_use` and no "when" pattern), `first-person`, `second-person`.
- **`trig.key`**: a key outside the kind's list, with `near`: the known key equal to it once case,
  `-`, and `_` are set aside, or one close spelling (`difflib`, 0.8), or null.
- **`trig.value`** `field`, `value`: a documented field outside its values (a model may also be a
  full `claude-` id), or a boolean field that is not a boolean.
- **`trig.tool`** `field`, `tool` (as written), `kind`: `unknown` with `near`, or `older` with
  `now`. A tool is the name before `(`; `mcp__...` and the current names are never reported.
- **`trig.overlap`** `other`, `shared`, `count`, `share`: within one listing (skills and commands;
  subagents), entries in `auto` or `paths` mode whose content words (lower case, three letters or
  more, not a stop word, a plural's `s` dropped) share at least half of the shorter set and at
  least 4 words, after the words in more than half of the listing's descriptions are set aside
  (when it holds 4 or more). Walkdown's own measure (owner, 2026-10-26), said so wherever shown.
- **`trig.listing`**, one row in every run: `skills` (skills and commands in `auto` or `paths`),
  `commands`, `agents`, `listing_chars` (each entry's capped at 1,536), `agent_chars`, `typed`,
  `unread`, `not_loaded` (never `skipped`, the grader's skip marker).

Stage 4 adds these last, after `host.*`.

## Must never

- Call a guidance row a host rule, or the overlap measure a host's.
- Say an older tool name fails; the docs do not say.

## Done when

1. Fixture `trigger-repo` (grader 04, rows `trig-*`): every kind above on its file, and no finding
   on a skill that follows every rule, an MCP tool, a permission rule, or unrelated descriptions.
2. `tests/test_trigger.py`: modes, the agents that are documentation, near names, values and
   booleans, the overlap listings and common words, the listing row.

## History

- 2026-10-26: built (slice 4). Measured on the audited repositories and the owner's skills before
  keeping the overlap measure: compared across all entries it paired each of one plugin's agents with the
  skill of the same name and the agents with each other through their shared boilerplate (14
  pairs); within one listing and with common words set aside, none. Two "when" patterns added
  ("Run once at the start", "Spawned by the orchestrator for its phase"): that plugin's no-when rows went
  from 8 to 1.
