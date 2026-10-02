"""Paths by which text reaches context at load, and bytes at load. Spec: specs/injection.SPEC.md."""
from __future__ import annotations

import posixpath
import re

from legs import entry
from rules import INJECTION_EVENTS, LOAD_BYTES_EVENTS

_VAR_PREFIX = re.compile(r"^(\$\{[^}]*\}|\$[A-Za-z_][A-Za-z0-9_]*)/")


def _findings(reports: dict, key: str) -> list[dict]:
    return [f for f in (reports.get(key) or {}).get("findings", []) if "skipped" not in f]


def _commands(hook: dict) -> list[str]:
    cmds = hook.get("commands")
    if isinstance(cmds, list) and cmds:
        return [str(c) for c in cmds if c]
    return [str(hook["command"])] if hook.get("command") else []


def _clean_token(tok: str) -> str:
    tok = tok.strip().strip("\"'")
    tok = _VAR_PREFIX.sub("", tok)
    while tok.startswith("./"):
        tok = tok[2:]
    return tok


def hook_scripts(hook: dict, graph: dict | None) -> list[str]:
    """Input files the hook's command names (rules 1 and 2 of the spec)."""
    if not graph:
        return []
    nodes = {n["path"] for n in graph.get("nodes", [])}
    cfg = hook.get("file") or ""
    cmds = _commands(hook)
    found: list[str] = []
    for e in graph.get("edges", []):
        if (e.get("kind") == "static" and e.get("from") == cfg
                and e.get("text") and any(e["text"] in c for c in cmds)):
            if e["to"] not in found:
                found.append(e["to"])
    cfg_dir = posixpath.dirname(cfg)
    roots = _plugin_roots(cfg, nodes)
    for c in cmds:
        for tok in c.split():
            t = _clean_token(tok)
            if not t:
                continue
            cands = [t] + [posixpath.join(r, t) for r in roots]
            if cfg_dir:
                cands.append(posixpath.normpath(posixpath.join(cfg_dir, t)))
            for cand in cands:
                if cand in nodes and cand not in found:
                    found.append(cand)
    return found


def _plugin_roots(cfg: str, nodes: set) -> list[str]:
    """Folders above the hook config that hold a plugin manifest, nearest first:
    what ${CLAUDE_PLUGIN_ROOT} means when the plugin sits in a subfolder of the
    repo (2026-09-29, Case 003: a plugin in a subfolder)."""
    out, d = [], posixpath.dirname(cfg)
    while d:
        if f"{d}/.claude-plugin/plugin.json" in nodes:
            out.append(d)
        d = posixpath.dirname(d)
    return out


def _hook_bytes(hook: dict, graph: dict | None, sizes: dict) -> tuple[int | None, str, list]:
    scripts = hook_scripts(hook, graph)
    if not scripts:
        return None, "unknown", []
    targets: dict[str, dict] = {}
    for e in graph.get("edges", []):
        if (e.get("kind") == "static" and e.get("from") in scripts
                and e.get("to") not in scripts and e.get("to") not in targets):
            targets[e["to"]] = e
    if not targets:
        return None, "unknown", []
    total, ev = 0, []
    for to, e in sorted(targets.items()):
        n = sizes.get(to) or 0
        total += n
        ev.append({"stage": "03", "check": "graph.edge", "file": e["from"], "line": e.get("line"),
                   "why": f"hook script reads {to} ({n} bytes)"})
    return total, "estimate", ev


def injections(reports: dict, graph: dict | None) -> list[dict]:
    s1 = _findings(reports, "01")
    sizes = {f["file"]: f.get("bytes") for f in s1 if f.get("check") == "inv.file"}
    out = []
    descs = sorted((f for f in s1 if f.get("check") == "struct.description"),
                   key=lambda f: (f.get("file") or "", f.get("line") or 0))
    for d in descs:
        out.append({"check": "cap.injection", "file": d.get("file"), "line": d.get("line"),
                    "mechanism": "description",
                    "bytes": len(str(d.get("text") or "").encode("utf-8")), "basis": "exact",
                    "evidence": [entry("01", d, "description: always-on text")]})
    events = {e.lower() for e in INJECTION_EVENTS}
    hooks = [f for f in s1 if f.get("check") == "struct.hooks"
             and str(f.get("event") or "").lower() in events]
    hooks = sorted(enumerate(hooks), key=lambda p: (p[1].get("file") or "", p[0]))
    for _, h in hooks:
        b, basis, edge_ev = _hook_bytes(h, graph, sizes)
        out.append({"check": "cap.injection", "file": h.get("file"), "line": h.get("line"),
                    "mechanism": "hook", "event": h.get("event"), "command": h.get("command"),
                    "bytes": b, "basis": basis,
                    "evidence": [entry("01", h, f"hook event: {h.get('event')}")] + edge_ev})
    return out


def _total(parts: list[dict], file) -> dict:
    known = [p for p in parts if p.get("bytes") is not None]
    unknown = len(parts) - len(known)
    if parts and not known:
        total, basis = None, "unknown"
    else:
        total = sum(p["bytes"] for p in known)
        basis = "exact" if all(p.get("basis") == "exact" for p in parts) else "estimate"
    ev = []
    for p in parts:
        src = p["evidence"][0] if p.get("evidence") else {}
        ev.append({"stage": src.get("stage", "01"), "check": src.get("check"),
                   "file": p.get("file"), "line": p.get("line"),
                   "why": f"{p['mechanism']}: {p['bytes'] if p['bytes'] is not None else 'unknown'}"
                          f" bytes ({p['basis']})"})
    return {"check": "cap.load-bytes", "file": file, "line": None, "bytes": total,
            "basis": basis, "unknown_parts": unknown, "parts": len(parts), "evidence": ev}


def load_bytes(inj: list[dict]) -> list[dict]:
    """One total per hook config (host): each host runs its own config, never all
    of them, so summing across configs double counts (changed 2026-09-29)."""
    counted = {e.lower() for e in LOAD_BYTES_EVENTS}
    descs = [f for f in inj if f.get("mechanism") == "description"]
    by_config: dict[str, list[dict]] = {}
    for f in inj:
        if f.get("mechanism") == "hook" and str(f.get("event") or "").lower() in counted:
            by_config.setdefault(f.get("file") or "", []).append(f)
    if not by_config:
        return [_total(descs, None)]
    return [_total(descs + hooks, cfg) for cfg, hooks in sorted(by_config.items())]
