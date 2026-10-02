"""Reachability and depth over the reference graph. Spec: specs/reach.SPEC.md."""
from __future__ import annotations

from dataclasses import dataclass

# Edge tiers, strongest first. A node's `via` is the first tier whose edges
# (together with every stronger tier's) reach it.
TIERS = ("static", "dynamic", "mention")


@dataclass
class Reach:
    depth: dict[str, int]
    parent: dict[str, str | None]
    via: dict[str, str]
    orphans: list[str]


def _bfs(out, entries, kinds):
    """Breadth-first over edges whose kind is in `kinds`; parents tie-break by path."""
    depth: dict[str, int] = {}
    parent: dict[str, str | None] = {}
    frontier = sorted(entries)
    for e in frontier:
        depth[e], parent[e] = 0, None
    d = 0
    while frontier:
        cands: dict[str, list[str]] = {}
        for u in frontier:
            for v, kind in out.get(u, []):
                if kind in kinds and v not in depth:
                    cands.setdefault(v, []).append(u)
        d += 1
        frontier = sorted(cands)
        for v in frontier:
            depth[v], parent[v] = d, min(cands[v])
    return depth, parent


def reach(nodes, entries, edges) -> Reach:
    node_set = set(nodes)
    out: dict[str, list[tuple[str, str]]] = {}
    for frm, to, kind in edges:
        if frm == to or frm not in node_set or to not in node_set:
            continue
        out.setdefault(frm, []).append((to, kind))
    starts = set(e for e in entries if e in node_set)

    # Depth is measured over the strongest tier that reaches a node, so a loose
    # folder mention cannot flatten the graph: static (direct references), then
    # dynamic (loads: config folders, code scans, instruction-file globs), then
    # mention (folders or globs named anywhere else).
    depth, parent, via = {}, {}, {}
    for i, name in enumerate(TIERS):
        d, p = _bfs(out, starts, set(TIERS[: i + 1]))
        for n in d:
            if n not in depth:
                depth[n], parent[n], via[n] = d[n], p[n], name
    orphans = sorted(n for n in node_set if n not in depth)
    return Reach(depth, parent, via, orphans)


def depth_findings(r: Reach) -> list[dict]:
    return [{"check": "graph.depth", "file": n, "line": None, "depth": r.depth[n],
             "from": r.parent[n], "via": r.via[n]} for n in sorted(r.depth)]


def orphan_findings(r: Reach) -> list[dict]:
    return [{"check": "graph.orphan", "file": n, "line": None} for n in r.orphans]
