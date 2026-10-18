"""Manifest versus disk: components a manifest leaves out. Spec: specs/unlisted.SPEC.md."""
from __future__ import annotations

import posixpath

KINDS = ("skill", "agent", "command")


def manifest_root(manifest: str) -> str:
    """The folder above a manifest in a dot folder (.claude-plugin/), else the manifest's own."""
    d = posixpath.dirname(manifest)
    if posixpath.basename(d).startswith("."):
        d = posixpath.dirname(d)
    return d


def _under(path: str, root: str) -> bool:
    return root == "" or path.startswith(root + "/")


def components(nodes: list[str]) -> list[tuple[str, str, str]]:
    """(kind, file, folder or file that holds it) for every skill, agent, and command."""
    out = []
    for n in nodes:
        base, parent = posixpath.basename(n), posixpath.dirname(n)
        if base == "SKILL.md":
            out.append(("skill", n, parent))
        elif n.endswith(".md") and posixpath.basename(parent) == "agents":
            out.append(("agent", n, n))
        elif n.endswith(".md") and posixpath.basename(parent) == "commands":
            out.append(("command", n, n))
    return out


def unlisted(manifests: list[str], nodes: list[str], edges: list[dict]) -> list[dict]:
    roots = {m: manifest_root(m) for m in manifests}
    comps = components(nodes)

    def owners(path: str) -> set[str]:
        """Every manifest whose root is the deepest root holding `path`: a plugin with one
        manifest per host (.claude-plugin/, .cursor-plugin/) is compared once per host."""
        holding = [r for r in roots.values() if _under(path, r)]
        if not holding:
            return set()
        deepest = max(holding, key=len)
        return {m for m, r in roots.items() if r == deepest}

    reached: dict[str, set[str]] = {m: set() for m in manifests}
    for e in edges:
        if e.get("from") in reached:
            reached[e["from"]].add(e["to"])
    out = []
    for m in sorted(manifests):
        mine = [c for c in comps if m in owners(c[1])]
        for kind in KINDS:
            of_kind = [c for c in mine if c[0] == kind]

            def listed(c):
                file, holder = c[1], c[2]
                return any(t == file or (kind == "skill" and _under(t, holder))
                           for t in reached[m])

            hit = [c for c in of_kind if listed(c)]
            if not hit:
                continue  # the manifest does not enumerate this kind
            for c in sorted(of_kind, key=lambda c: c[1]):
                if c not in hit:
                    out.append({"check": "graph.unlisted", "file": c[1], "line": None,
                                "manifest": m, "kind": kind, "listed": len(hit),
                                "on_disk": len(of_kind)})
    return out
