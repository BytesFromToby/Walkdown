# reach.py: spec

Reachability and depth over the reference graph: `graph.orphan` and
`graph.depth`.

## Inputs

`reach(nodes, entries, edges) -> Reach`: every node path; the entry-point
paths; edges as `(from, to, kind)` with `kind` `static`, `dynamic` (a load), or `mention`
(a folder or glob mention; run.SPEC decides which).

## Outputs

`Reach`: `depth` ({node: int}, reachable nodes only), `parent` ({node: str or
None}), `via` ({node: `static`, `dynamic`, or `mention`}), `orphans` (sorted list).

- Breadth-first from every entry point at once; entry points are depth 0,
  parent None, via `static`.
- **Depth is measured over static edges first** (changed 2026-09-29). A node
  reachable through static edges alone gets its depth over static edges only,
  `via` `static`, even when a dynamic edge reaches it in fewer hops. On
  superpowers, directory mentions ("see `skills/`") otherwise put most files one
  hop from an entry point and the depth measure stopped telling anything.
- Tiers, strongest first: static, dynamic, mention (2026-09-29). A node takes
  the first tier that reaches it together with every stronger tier, and its
  depth over those edges: reachable over static plus dynamic edges is `via`
  `dynamic`; reachable only once mention edges are added is `via` `mention`.
  Either way it is reachable, never an orphan.
- `parent` is a node one hop closer on the shortest path the depth came from.
  Ties break by sorted path, so the output is stable.
- Orphans: nodes reachable from no entry point over any edges.
- Self-edges and edges to unknown nodes are ignored.

`depth_findings(reach)` and `orphan_findings(reach)` give the contract
findings (`graph.depth` with `depth`, `from`, `via`, `line` null;
`graph.orphan` with `line` null), in path order.

## Must never

- Rank or judge orphans.
- Drop dynamic or mention edges from reachability.

## Done when (each backed by a test in `tests/test_reach.py`)

1. A chain `E -> a -> b` gives depths 0, 1, 2 with parents None, E, a.
2. A file reached only by a dynamic edge is reachable, `via` `dynamic`.
3. A file reached by a dynamic edge at depth 1 and a static path at depth 2 is depth 2, `via` `static`, with the static parent.
6. A file reached only through a dynamic hop followed by a static hop is depth 2, `via` `dynamic`.
4. Two entry points: each node takes the nearer one.
5. A file nothing reaches is an orphan and has no depth finding; an entry point is never an orphan.
7. Tiers: a file reached only by a mention is `via` `mention`; one reached by a load is `via` `dynamic`; a file a mention reaches in one hop but a static-then-load path reaches in two is `via` `dynamic` at depth 2.
