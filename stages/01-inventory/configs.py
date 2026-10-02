"""Hook configs and platform manifests. Spec: specs/configs.SPEC.md."""
from __future__ import annotations

import json

import yaml

GRANT_KEYS = {"tools", "permissions", "allowedTools", "allowed_tools", "allowed-tools",
              "capabilities"}
KNOWN_MANIFESTS = {"plugin.json", "plugin.yaml", "plugin.yml", "marketplace.json",
                   "gemini-extension.json"}


def load(rel: str, text: str):
    low = rel.lower()
    try:
        if low.endswith(".json"):
            return json.loads(text)
        if low.endswith((".yaml", ".yml")):
            return yaml.safe_load(text)
    except (ValueError, yaml.YAMLError):
        return None
    return None


# ------------------------------------------------------------------ hooks

def is_hook_config(doc) -> bool:
    if not isinstance(doc, dict) or not isinstance(doc.get("hooks"), dict):
        return False
    return any(isinstance(v, list) for v in doc["hooks"].values())


def hook_findings(rel: str, doc) -> list[dict]:
    out = []
    if not is_hook_config(doc):
        return out
    for event, entries in doc["hooks"].items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            row = {"check": "struct.hooks", "file": rel, "line": None, "event": event,
                   "matcher": entry.get("matcher")}
            inner = entry.get("hooks")
            if isinstance(inner, list):
                hooks = [h for h in inner if isinstance(h, dict)]
                cmds = [str(h.get("command", "")) for h in hooks]
                row.update(command="\n".join(cmds), commands=cmds,
                           types=[h.get("type") for h in hooks], format="nested")
                asyncs = [h["async"] for h in hooks if "async" in h]
                if asyncs:
                    row["async"] = asyncs
            else:
                cmd = entry.get("command")
                row.update(command=None if cmd is None else str(cmd), format="flat")
                if "async" in entry:
                    row["async"] = [entry["async"]]
            out.append(row)
    return out


# ------------------------------------------------------------------ MCP servers

def mcp_findings(rel: str, doc) -> list[dict]:
    """One struct.mcp per server a config declares under `mcpServers` (a plugin
    manifest, .mcp.json, or a settings file). Env values are never recorded, only
    their names (2026-09-29, Case 004: backlog declares its server in plugin.json)."""
    if not isinstance(doc, dict) or not isinstance(doc.get("mcpServers"), dict):
        return []
    out = []
    for name, spec in doc["mcpServers"].items():
        spec = spec if isinstance(spec, dict) else {}
        url = spec.get("url")
        transport = spec.get("type") or ("http" if url else "stdio")
        cmd = spec.get("command")
        args = spec.get("args") if isinstance(spec.get("args"), list) else []
        env = spec.get("env") if isinstance(spec.get("env"), dict) else {}
        out.append({"check": "struct.mcp", "file": rel, "line": None, "name": str(name),
                    "transport": str(transport),
                    "command": None if cmd is None else " ".join([str(cmd), *map(str, args)]),
                    "url": None if url is None else str(url),
                    "env_keys": sorted(map(str, env))})
    return out


# ------------------------------------------------------------------ manifests

def _scalar(v) -> str:
    return json.dumps(v) if not isinstance(v, str) else v


def _tokens(v, out: set):
    if isinstance(v, list):
        for item in v:
            if isinstance(item, (list, dict)):
                _tokens(item, out)
            else:
                out.add(_scalar(item))
    elif isinstance(v, dict):
        for k, val in v.items():
            if val is True:
                out.add(str(k))
            elif isinstance(val, (list, dict)):
                _tokens(val, out)
            else:
                out.add(f"{k}={_scalar(val)}")
    elif v is not None:
        out.add(_scalar(v))


def _has_grant_key(v) -> bool:
    if isinstance(v, dict):
        return any(k in GRANT_KEYS or _has_grant_key(val) for k, val in v.items())
    if isinstance(v, list):
        return any(_has_grant_key(x) for x in v)
    return False


def _collect(v, out: set):
    if isinstance(v, dict):
        for k, val in v.items():
            if k in GRANT_KEYS:
                _tokens(val, out)
            else:
                _collect(val, out)
    elif isinstance(v, list):
        for x in v:
            _collect(x, out)


def manifest_grants(doc) -> list[str] | None:
    if not isinstance(doc, dict) or not isinstance(doc.get("name"), str):
        return None
    out: set = set()
    _collect(doc, out)
    return sorted(out)


def is_manifest(rel: str, doc) -> bool:
    if not isinstance(doc, dict) or not isinstance(doc.get("name"), str):
        return False
    base = rel.rsplit("/", 1)[-1].lower()
    return base in KNOWN_MANIFESTS or _has_grant_key(doc)


def manifest_findings(manifests) -> list[dict]:
    groups: dict[str, list] = {}
    for rel, name, grants in manifests:
        groups.setdefault(name, []).append((rel, grants))
    out = []
    for name in sorted(groups):
        members = sorted(groups[name])
        sets = {tuple(sorted(g)) for _, g in members}
        out.append({"check": "struct.manifests", "file": None, "line": None, "name": name,
                    "files": [r for r, _ in members],
                    "grants": {r: sorted(g) for r, g in members},
                    "divergent": len(sets) > 1})
    return out
