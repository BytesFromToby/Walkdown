"""What ships, and what it costs in an AI's context. Spec: specs/cost.SPEC.md.

Slice 1 of the plan for builders (owner, 2026-10-26). Derived from stages 1, 3, and 4 and the
facts in loading.yaml; nothing is run or read here. Tokens are an estimate from size.
"""
from __future__ import annotations

import posixpath
import sys
from math import ceil
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "04-phrases"))

from audience import SCRIPT_EXTS, audience, is_test_data  # noqa: E402

LOADING = yaml.safe_load((HERE / "loading.yaml").read_text(encoding="utf-8"))
BYTES_PER_TOKEN = LOADING["bytes_per_token"]
LISTING_CAP = LOADING["description_listing_chars"]
IMPORT_HOPS = LOADING["import_hops"]

AI_ENTRIES = ("skill", "agent", "command")
CONFIG = ("manifest", "mcp-config", "hook-config")
GROUPS = ("entry", "project", "on-demand", "maybe", "run", "config", "people", "build", "unused")
LOADS = ("static",)              # what the AI reads when it follows a reference
LOOSE = ("static", "dynamic", "mention")  # plus wildcards, folder reads, folders named
TIERS = ("session", "project", "skill-runs", "skill-full", "skill-max")


def tokens(size: int) -> int:
    """The estimate: size divided by BYTES_PER_TOKEN, rounded up."""
    return ceil(size / BYTES_PER_TOKEN) if size else 0


def _files(reports) -> dict[str, dict]:
    return {f["file"]: f for f in reports.get("01", {}).get("findings", [])
            if f.get("check") == "inv.file" and f.get("file")}


def _is_text(f: dict) -> bool:
    return bool(f.get("encoding"))


def _is_script(rel: str) -> bool:
    base = rel.rsplit("/", 1)[-1].lower()
    return "." in base and base.rsplit(".", 1)[1] in SCRIPT_EXTS


def _is_rule(rel: str) -> bool:
    return ("/" + rel).find("/.claude/rules/") >= 0 and rel.lower().endswith(".md")


def _out(graph) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for e in (graph or {}).get("edges", []):
        out.setdefault(e["from"], []).append(e)
    for v in out.values():
        v.sort(key=lambda e: (e["to"], e.get("line") or 0))
    return out


def _unit(entry: str, kind: str):
    """What an entry reaches is bounded: a skill is its own folder (Agent Skills: a skill is a
    directory, and only it installs), followed as deep as references go; an agent, command, or
    project file one level. Returns (keep-an-edge filter, hops)."""
    if kind == "skill":
        root = posixpath.dirname(entry)
        inside = (lambda e: e["to"].startswith(root + "/")) if root else (lambda e: True)
        return inside, None
    return None, 1


def reach(entry: str, kind: str, out, kinds, stop) -> tuple[set, dict]:
    """A folder named in passing counts only inside a skill's own folder: someone working in the
    repository can browse all of it anyway (measured on Walkdown's CLAUDE.md, 2026-10-26)."""
    keep, hops = _unit(entry, kind)
    if kind == "project":  # a glob in CLAUDE.md describes the layout; the host never loads it
        kinds = tuple(k for k in kinds if k == "static")
    elif kind != "skill":
        kinds = tuple(k for k in kinds if k != "mention")
    return _closure({entry}, out, kinds, stop=stop, keep=keep, hops=hops)


def outside(entry: str, out, stop) -> list[str]:
    """Files a skill's folder names outside itself: never counted, and they do not install with it.
    Only a reference that names one file: a bare name that matches files in several folders, or a
    folder read, says nothing about which (measured on an audited repository, 2026-10-26)."""
    root = posixpath.dirname(entry)
    if not root:
        return []
    mine, _ = reach(entry, "skill", out, LOOSE, stop)
    return sorted({e["to"] for u in mine if u not in stop for e in out.get(u, [])
                   if e.get("kind") == "static" and not e.get("ambiguous")
                   and not e["to"].startswith(root + "/")})


def _closure(starts, out, kinds, stop=frozenset(), keep=None, hops=None):
    """Files reached from `starts` over edges of `kinds`; `stop` files are reached but never
    followed; `keep` filters edges; `hops` limits the depth. Returns (reached, first parent)."""
    seen, parent = set(starts), {}
    frontier, depth = sorted(starts), 0
    while frontier and (hops is None or depth < hops):
        nxt = []
        for u in frontier:
            if u in stop:
                continue
            for e in out.get(u, []):
                v = e["to"]
                if e.get("kind") in kinds and v not in seen and (keep is None or keep(e)):
                    seen.add(v)
                    parent[v] = u
                    nxt.append(v)
        frontier, depth = sorted(nxt), depth + 1
    return seen, parent


def ship(reports, graph) -> list[dict]:
    """One `cap.ship` per file: the group it ships in (spec)."""
    files = _files(reports)
    if graph is None:
        return []
    out = _out(graph)
    scripts = {r for r in files if _is_script(r)}
    kind = {r: f.get("entry_point") for r, f in files.items()}
    real = {r for r in files if not is_test_data(r)}
    entries = {r for r in real if kind[r] in AI_ENTRIES}
    project = {r for r in real if kind[r] == "project-instructions" or _is_rule(r)}
    imported, _ = _closure(project, out, LOADS, keep=lambda e: e.get("at_import"), hops=IMPORT_HOPS)
    project |= imported
    static, loose, parent, lparent = set(project), set(project), {}, {}
    for s in sorted(entries | project):
        k = "project" if s in project else kind[s]
        got, par = reach(s, k, out, LOADS, scripts)
        static |= got
        parent.update({v: p for v, p in par.items() if v not in parent})
        got, par = reach(s, k, out, LOOSE, scripts)
        loose |= got
        lparent.update({v: p for v, p in par.items() if v not in lparent})
    hooks = {r for r in real if kind[r] == "hook-config"}
    hook_run, _ = _closure(hooks, out, LOOSE)
    rows = []
    for rel in sorted(files):
        f, k = files[rel], kind[rel]
        if (k == "ci" or is_test_data(rel)) and rel not in loose:
            g = "build"
        elif rel in entries:
            g = "entry"
        elif rel in project:
            g = "project"
        elif k in CONFIG:
            g = "config"
        elif rel in scripts and (rel in static or rel in hook_run):
            g = "run"
        elif rel in static:
            g = "on-demand"
        elif rel in loose:
            g = "maybe"
        elif k == "readme" or audience(rel) == "human":
            g = "people"
        elif audience(rel) == "tool":
            g = "build"
        else:
            g = "unused"
        size = f.get("bytes") or 0
        row = {"check": "cap.ship", "file": rel, "line": None, "group": g, "bytes": size,
               "tokens": tokens(size) if _is_text(f) else None}
        if g in ("on-demand", "maybe"):
            row["reached_by"] = (parent if g == "on-demand" else lparent).get(rel)
        rows.append(row)
    return rows


def _sum(rels, files) -> tuple[int, int, list[str]]:
    """(tokens, bytes, files that are not text) over `rels`."""
    tok = size = 0
    other = []
    for r in sorted(rels):
        f = files.get(r, {})
        size += f.get("bytes") or 0
        if _is_text(f):
            tok += tokens(f.get("bytes") or 0)
        else:
            other.append(r)
    return tok, size, other


def context(reports, graph, injections, ship_rows) -> list[dict]:
    """`cap.context` per tier (spec): session, project, and per skill, agent, or command."""
    if graph is None:
        return []
    files = _files(reports)
    out = _out(graph)
    group = {r["file"]: r["group"] for r in ship_rows}
    scripts = {r for r in files if _is_script(r)}
    entries = sorted(r for r, g in group.items() if g == "entry")
    rows = []

    descs = [f for f in reports.get("01", {}).get("findings", [])
             if f.get("check") == "struct.description" and f.get("file") in entries]
    tok = sum(ceil(min(len(str(f.get("text") or "")), LISTING_CAP) / BYTES_PER_TOKEN) for f in descs)
    size = sum(len(str(f.get("text") or "")[:LISTING_CAP].encode("utf-8")) for f in descs)
    per_config: dict[str, int] = {}
    unknown = []
    for i in injections:
        if i.get("mechanism") != "hook":
            continue
        if i.get("bytes") is None:
            unknown.append({"what": "hook", "file": i.get("file"), "event": i.get("event")})
        else:
            per_config[i.get("file")] = per_config.get(i.get("file"), 0) + i["bytes"]
    config = max(per_config, key=lambda c: (per_config[c], c), default=None)  # hosts never summed
    if config:
        tok += tokens(per_config[config])
        size += per_config[config]
    for m in reports.get("01", {}).get("findings", []):
        if m.get("check") == "struct.mcp" and not is_test_data(m.get("file") or ""):
            unknown.append({"what": "mcp", "file": m.get("file"), "name": m.get("name")})
    rows.append({"check": "cap.context", "file": None, "line": None, "tier": "session",
                 "tokens": tok, "bytes": size,
                 "files": sorted({f["file"] for f in descs} | ({config} if config else set())),
                 "hook_config": config, "unknown": unknown})

    project = sorted(r for r, g in group.items() if g == "project")
    if project:
        t, b, other = _sum(project, files)
        rows.append({"check": "cap.context", "file": None, "line": None, "tier": "project",
                     "tokens": t, "bytes": b, "files": project, "not_text": other})

    for e in entries:
        k = files[e].get("entry_point")
        full, _ = reach(e, k, out, LOADS, scripts)
        most, _ = reach(e, k, out, LOOSE, scripts)
        for tier, rels in (("skill-runs", {e}), ("skill-full", full - scripts), ("skill-max", most - scripts)):
            t, b, other = _sum(rels, files)
            row = {"check": "cap.context", "file": e, "line": None, "tier": tier, "kind": k,
                   "tokens": t, "bytes": b, "files": sorted(rels), "not_text": other}
            if tier == "skill-max" and k == "skill":
                row["outside"] = outside(e, out, scripts)
            rows.append(row)
    return rows
