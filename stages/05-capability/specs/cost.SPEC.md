# cost.py: spec

What a repository ships, and what it costs in an AI's context (plan for builders, slice 1,
owner 2026-10-26; the slice spec is `pre-planning/SPEC-SLICE1-2026-10-26.md`). Derived from
stage 1 (`inv.file`, `struct.description`, `struct.mcp`), stage 3's `graph.json` edges, stage
5's hook injections, and the facts in `loading.yaml` (each with its source and the date it was
checked). Nothing is run or read.

## Tokens

An estimate: a file's size in bytes divided by `bytes_per_token` (4), rounded up, per file.
For English text that is about one token per four characters; text in other scripts uses more
bytes per character, so its estimate runs high. A description counts its characters, cut at
`description_listing_chars` (1,536) as Claude Code cuts the skill listing. A file that is not
text has no token count (`tokens: null`) and is named in `not_text`.

## How far a file reaches

Measured before it was settled (2026-10-26): followed across the whole repository, one skill
reached 240,000 tokens on Walkdown and 559,000 on another audited repository through README and docs links,
and every file counted as used. So each entry's reach is bounded:

- **A skill** is its own folder (the Agent Skills specification: a skill is a directory, and only
  it installs). It reaches every file inside that folder its references lead to, as deep as they
  go, wildcard loads and folder mentions included for `skill-max`. A skill whose `SKILL.md` is at
  the repository's root has the whole repository as its folder. What its folder names outside
  itself is listed (`outside` on its `skill-max` row) and never counted: only references that
  name one file (`static`, not `ambiguous`), since a bare name matching files in many folders,
  or a folder read, says nothing about which.
- **An agent or a command** reaches the files it names directly, one level, wildcard loads
  included for `skill-max`; folder mentions do not count.
- **A project file** (`CLAUDE.md` and the rest) reaches its `@` imports (up to four hops, as the
  host expands them) and the files it names directly, one level. Its wildcards and folder
  mentions do not count: they describe the layout, the host never loads them, and someone
  working in the repository can browse it all anyway.
- **A script** is `run` only when a loaded file names it or a hook runs it; one reached only by a
  wildcard or folder mention is `maybe`.

## `ship(reports, graph) -> [cap.ship]`

One per file: `file`, `group`, `bytes`, `tokens`, and `reached_by` (the file that first names
it) for `on-demand` and `maybe`. Entries are the skills, agents, and commands (stage 1
`entry_point`) outside test data; project files are project instructions (`CLAUDE.md`,
`AGENTS.md`, `GEMINI.md`, ...) and `.claude/rules/*.md` outside test data, plus what their
`@` imports reach (stage 3 `at_import` edges, up to `import_hops`, 4). Rules, in order:

1. `build`: CI, or test data (`audience.is_test_data`), unless an entry or project file reaches it.
2. `entry`: a skill, agent, or command.
3. `project`: a project file or an import of one.
4. `config`: a manifest, MCP config, or hook config.
5. `run`: a script (`audience.SCRIPT_EXTS`) that an entry or project file names, or a hook config reaches.
6. `on-demand`: reached from an entry or project file over static edges, within each one's
   reach (above; scripts are reached, never followed).
7. `maybe`: reached only once wildcard loads and folder reads count (and folder mentions, for a
   skill inside its own folder).
8. `people`: a README, or a file written for people (`audience` `human`).
9. `build`: any other file read by tools (`audience` `tool`: build and lock files, scripts nothing reaches).
10. `unused`: everything else: nothing points to it (text written for the AI, or an image or
    font no file names).

`.claude/rules` files with `paths` load on demand in Claude Code; slice 1 counts every rule file
as loaded at launch, an upper bound. With no `graph.json`, nothing is reported.

## `context(reports, graph, injections, ship) -> [cap.context]`

- `session` (always one): every entry's description (cut at 1,536 characters), plus the hook
  text of the one hook config with the most (`cap.injection` `mechanism: hook`; each host runs
  its own config, so configs are never summed). `unknown`: what only running shows, never
  guessed: hooks with no estimate (`what: hook`) and MCP servers (`what: mcp`, their tool
  definitions). `files`, `hook_config`.
- `project` (only when there are project files): every project file and import.
- Per entry (`file` the entry, `kind` its kind): `skill-runs` (the entry file), `skill-full`
  (plus everything it reaches over static edges, scripts left out), `skill-max` (plus wildcard
  loads, folder reads, and folder mentions). An agent's body loads in its own context.

Each: `tier`, `tokens`, `bytes`, `files`, and `not_text` where it applies.

## Must never

- Guess a size only running shows; call a file unused when something names it; count a script
  in a context tier.

## Done when

1. Fixture `cost-repo` (grader 05, rows `cost-ship-*`, `cost-tier-*`): every file's group and
   every tier's tokens; scripts are in no context tier; a file nothing names is in none.
2. `tests/test_cost.py`: a skill in test data is `build`, and a test file a skill names is
   `on-demand`; a README a skill names is `on-demand`; an import of an import counts, a fifth
   hop does not; a description over 1,536 characters is cut; hook configs are never summed and
   a hook with no estimate and an MCP server are `unknown`; an image a skill names is `not_text`.
3. `tests/test_cost.py`: a skill in a subfolder reaches only inside it and lists what it names
   outside; an agent reaches one level; a glob in `CLAUDE.md` reaches nothing; a script reached
   only by a wildcard is `maybe`, not `run` (`test_reach_is_bounded`).
