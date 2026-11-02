# 02.3-graph: what loads what

**Question:** what loads what?
**Kind of evidence:** a reference graph. Nodes are files; edges are one file naming another, and every edge
carries the file and line that makes it.
**Plain name:** What loads what (its heading in `full.md`).

## Inputs

- `<input_dir>`: the folder audited, read-only.
  `python stages/02-coded/02.3-graph/run.py <input_dir> [--inventory <file>] [--out <dir>]`
- `data/02.1-inventory.json` (`--inventory`; `reads` in `stages/stages.json` is `02.1-inventory`): the
  `inv.file` rows, whose `entry_point` is not null are the entry points. Without it, `earlier_steps.py` runs
  02.1 first; if that fails, this step fails, since a graph with no entry points is not a result.
- `Library/invisible.yaml`: the characters stripped before a reference is matched.

## Process

1. Every file is a node. Every file that decodes as text is scanned for references (links, code spans,
   prose paths, bare file names that resolve, config strings), with the original line numbers.
2. Each reference is resolved to the nodes it names; a glob, a folder named, or a code scan that lists a
   folder is a dynamic load (`graph.dynamic`).
3. Breadth-first from the entry points gives reachability and depth.
4. Checks: `graph.entry`, `graph.orphan`, `graph.dangling`, `graph.dynamic`, `graph.depth`,
   `graph.unlisted` (a component on disk that a manifest leaves out), `graph.unscanned`, and
   `graph.case` (a reference that matches only when letter case is ignored).

Never: judge why a file is unreferenced or rank orphans; report an unresolved bare file name in prose as
dangling; follow a URL, run anything from the input, or follow a symlink out of the tree; write inside
`<input_dir>`; import another step's code; present the graph as complete when a dynamic load exists.

## Outputs

- stdout: one contract-1 report; the runner saves it as `data/02.3-graph.json`, and stderr as
  `data/02.3-graph.notes.txt`.
- With `--out <dir>` (the runner gives `data/`): `data/graph.json`, every node (path, entry kind, depth)
  and every edge (`from`, `line`, `to`, `kind` static or dynamic, `form`, `text`). `02.5-capability` and
  `02.6-builder` read it.

## The human check

An orphan is usually dead weight and a dangling reference is usually rot: both are places to look, not
verdicts, and the graph says in its limits when it cannot be known at review time. The fixtures
`Fixtures/02.3-graph/` (`case-repo`, `plugin-repo`, `sample-repo`) and
`python tools/grader/grader.py 02.3-graph` give the validation stamp in `LOG.md`.

## Spec

`specs/graph.SPEC.md`: one section per script, `run` first and the others in alphabetical order
(`extract`, `invisible`, `reach`, `resolve`, `scans`, `tokens`, `unlisted`).
