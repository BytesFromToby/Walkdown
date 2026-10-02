# entrypoints.py: spec

Names the entry-point kind of each file. Stage 1, field `inv.file.entry_point`.
Stage 3 starts its graph from this list.

## Inputs

`classify(rel, *, is_symlink, has_tools, is_hook_config, is_manifest)`:
the relative path plus facts other stage 1 scripts already parsed
(frontmatter declares tools; parsed hook config; parsed manifest).

## Outputs

One of `skill`, `agent`, `command`, `hook-config`, `mcp-config`, `ci`,
`manifest`, `readme`, `project-instructions`, or None. First rule that holds wins:

1. A symlink: None (stage 1 never follows it).
2. `skill`: basename `SKILL.md`, or ending `.SKILL.md` (any case).
3. `agent` / `command`: a markdown file whose frontmatter declares tools, or a
   markdown file with an `agents` or `commands` folder in its path. `command`
   when a `commands` folder is in the path, else `agent`.
4. `mcp-config`: basename `.mcp.json`.
5. `hook-config`: the file parsed as a hook config (`configs.py`).
6. `ci`: `.github/workflows/*.yml|yaml`, `.gitlab-ci.yml`, `.circleci/config.yml`,
   `azure-pipelines.yml`, `.travis.yml`, `Jenkinsfile`. (v1 marks every CI
   workflow; which ones invoke an agent is a stage 3 question.)
7. `manifest`: the file parsed as a manifest (`configs.py`).
8. `readme`: basename starting with `README` (any case).
9. `project-instructions`: `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`,
   `GEMINI.md`, `.cursorrules`, `.windsurfrules`, `.clinerules` (any case,
   any folder), `.github/copilot-instructions.md`, markdown under
   `.cursor/rules/`: files a harness loads by itself when someone works in the
   repository (added 2026-09-29, Case 004).

Subagent prompt templates (files a `SKILL.md` names as a template) need the
reference graph, so stage 3 adds them.

## Must never

- Open a file. It classifies from the path and from facts it is handed.

## Done when (each backed by a test in `tests/test_entrypoints.py`)

1. `skills/x/SKILL.md` and `pos.SKILL.md` are `skill`.
2. A markdown file with tools outside `agents/` is `agent`; `commands/x.md` is `command`; `agents/x.md` without tools is `agent`.
3. `.mcp.json`, a hook config, a workflow file, a manifest, and `README.md` each get their kind.
4. A workflow file that also parses as a manifest is `ci`.
5. A symlink named `SKILL.md` and an ordinary file are None.
6. `CLAUDE.md`, `sub/AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md` are `project-instructions`.
