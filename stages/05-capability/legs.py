"""Trifecta legs and install grants. Spec: specs/legs.SPEC.md. Rules: rules.py."""
from __future__ import annotations

import re

from rules import CONNECTOR_NAMES, GRANT_RULES, GRANTS, LEG_RULES, LEGS

_CONNECTOR = re.compile(CONNECTOR_NAMES, re.I)


def entry(stage: str, finding: dict, why: str) -> dict:
    """One evidence entry pointing at an input finding."""
    return {"stage": stage, "check": finding.get("check"), "file": finding.get("file"),
            "line": finding.get("line"), "why": why}


def tool_name(name) -> str:
    """Trim, and drop a trailing argument scope: 'Bash(git:*)' -> 'Bash'."""
    n = str(name).strip()
    if n.endswith(")") and "(" in n:
        n = n[:n.index("(")].strip()
    return n


def _findings(reports: dict, key: str) -> list[dict]:
    return [f for f in (reports.get(key) or {}).get("findings", []) if "skipped" not in f]


def _sort_key(e: dict):
    return (e["stage"], e["file"] or "", e["line"] if e["line"] is not None else -1,
            e["check"] or "", e["why"])


def _dedupe(entries: list[dict]) -> list[dict]:
    seen, out = set(), []
    for e in sorted(entries, key=_sort_key):
        k = tuple(sorted((k, repr(v)) for k, v in e.items()))
        if k not in seen:
            seen.add(k)
            out.append(e)
    return out


def evidence(rule: dict, reports: dict, leg_evidence: dict | None = None) -> list[dict]:
    s1, s4 = _findings(reports, "01"), _findings(reports, "04")
    out: list[dict] = []

    any_checks = set(rule.get("phrase_any", []))
    by_pattern = rule.get("phrase_patterns", {})
    for f in s4:
        check = f.get("check")
        pats = list(f.get("patterns") or [])
        if f.get("audience") == "human":
            # README, docs, changelog: they describe what the user does, not what the
            # artifact states or grants (2026-09-29, Case 004: README install lines
            # were the persistence and network evidence)
            continue
        if check in any_checks:
            out.append(entry("04", f, f"{check}: {', '.join(pats)}"))
        elif check in by_pattern:
            hit = [p for p in pats if p in by_pattern[check]]
            if hit:
                out.append(entry("04", f, f"{check}: {', '.join(hit)}"))

    tools = rule.get("tools", [])
    hook_events = rule.get("hook_events")
    events = ({e.lower() for e in hook_events} if isinstance(hook_events, list) else None)
    entry_points = set(rule.get("entry_points", []))
    for f in s1:
        check = f.get("check")
        if check == "struct.agent-tools":
            if f.get("tools") is None:
                if rule.get("inherit_all"):
                    out.append(entry("01", f, "tool grant: inherits all"))
            else:
                held = {tool_name(t) for t in f["tools"]}
                named = [t for t in tools if t in held]
                if named:
                    out.append(entry("01", f, f"tool grant: {', '.join(named)}"))
                conn = sorted(t for t in held if rule.get("connector_names")
                              and t.startswith("mcp__") and _CONNECTOR.search(t))
                if conn:
                    out.append(entry("01", f, f"connector tool grant: {', '.join(conn)}"))
        elif check == "struct.hooks" and hook_events:
            ev = str(f.get("event") or "")
            if hook_events == "*" or (events is not None and ev.lower() in events):
                out.append(entry("01", f, f"hook event: {ev}"))
        elif check == "struct.mcp" and (rule.get("mcp_servers") or rule.get("connector_names")):
            if rule.get("mcp_servers"):
                out.append(entry("01", f, f"MCP server: {f.get('name')}"))
            blob = " ".join(str(f.get(k) or "") for k in ("name", "command", "url"))
            if rule.get("connector_names") and _CONNECTOR.search(blob):
                out.append(entry("01", f, f"connector MCP server: {f.get('name')}"))
        elif check == "inv.file" and f.get("entry_point") in entry_points:
            out.append(entry("01", f, f"entry point: {f['entry_point']}"))
        elif check == "struct.description" and rule.get("descriptions"):
            out.append(entry("01", f, "description: always-on text"))

    for leg in rule.get("legs", []):
        out.extend((leg_evidence or {}).get(leg, []))
    return _dedupe(out)


def legs(reports: dict) -> list[dict]:
    out = []
    for leg in LEGS:
        ev = evidence(LEG_RULES[leg], reports)
        out.append({"check": "cap.leg", "file": None, "line": None, "leg": leg,
                    "present": bool(ev), "evidence": ev})
    return out


def grants(reports: dict, leg_findings: list[dict]) -> list[dict]:
    by_leg = {f["leg"]: f["evidence"] for f in leg_findings}
    out = []
    for g in GRANTS:
        ev = evidence(GRANT_RULES[g], reports, by_leg)
        if ev:
            out.append({"check": "cap.grant", "file": None, "line": None, "grant": g,
                        "evidence": ev})
    return out
