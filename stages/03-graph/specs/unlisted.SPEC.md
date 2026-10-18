# unlisted.py: spec

Manifest versus disk, the other half (METHOD; 2026-10-18). Stage 3, check `graph.unlisted`.

A manifest that names the skills, agents, or commands a plugin ships is what a reviewer reads to
learn what it holds. A component on disk beside it that the manifest leaves out is easy to miss,
and a host that finds components by folder (Claude Code loads `skills/`, `agents/`, `commands/`
whatever the manifest lists) can still load it. Stage 3 reports where the two disagree; whether
the host loads the unlisted one is the host's rule, not a fact in the repository.

## Inputs

`unlisted(manifests, nodes, edges) -> list[dict]`:

- `manifests`: the files stage 1 marked `entry_point` `manifest`.
- `nodes`: every file path in the tree.
- `edges`: stage 3's edges (`from`, `to`, `kind`), static and dynamic.

## Rules

- A manifest's **root** is the folder above it when it sits in a dot folder
  (`.claude-plugin/plugin.json`, `.codex-plugin/...`), else its own folder.
- **Components** under the root, by kind: a `skill` is a folder holding a `SKILL.md` (the
  component's file is that `SKILL.md`); an `agent` is a `.md` file directly in an `agents/`
  folder; a `command` is a `.md` file directly in a `commands/` folder. Components under
  another manifest's root below this one belong to that one. Manifests that share a root (one
  per host: `.claude-plugin/`, `.cursor-plugin/`) are each compared with its components.
- A component is **listed** when an edge from the manifest reaches its file, or (for a skill)
  any file in its folder.
- A manifest **enumerates** a kind when it lists at least one component of that kind. Only
  kinds it enumerates are compared: a manifest that names no skills relies on the folder, and
  there is nothing to compare.

## Outputs

One `graph.unlisted` finding per component of an enumerated kind that its manifest does not
list: `check`, `file` (the component's file), `line` null, `manifest`, `kind`, `listed` (how
many of that kind the manifest lists), `on_disk` (how many of that kind are under its root).
Ordered by manifest, kind, file.

## Must never

- Compare a kind the manifest does not enumerate.
- Say whether the host loads an unlisted component.

## Done when (each backed by a test in `tests/test_unlisted.py`)

1. A `.claude-plugin/plugin.json` listing skills `a` and `b` of `a`, `b`, `c`, and agent `x`
   of `x`, `y`, gives `skills/c/SKILL.md` (`kind` skill, `listed` 2, `on_disk` 3) and
   `agents/y.md`; commands, which it does not list, give nothing.
2. A manifest that reaches every skill through a folder reference (`./skills/`) gives nothing.
3. A manifest with no component references gives nothing.
4. A skill under a nested plugin's own manifest is that manifest's, not the outer one's.
5. Two manifests at one root (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`) are each compared: one listing every skill gives nothing, the other listing one of two gives the other.
