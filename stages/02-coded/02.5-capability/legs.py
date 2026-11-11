"""Trifecta legs and install grants. Spec: specs/capability.SPEC.md, legs. Rules: rules.py."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

import coverlines as cov  # noqa: E402
import stagelist  # noqa: E402
from rules import CONNECTOR_NAMES, GRANT_RULES, GRANTS, LEG_RULES, LEGS  # noqa: E402

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
    return (stagelist.position(e["stage"]), e["file"] or "", e["line"] if e["line"] is not None else -1,
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
    s1, s4 = _findings(reports, "02.1-inventory"), _findings(reports, "02.4-phrases")
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
            out.append(entry("02.4-phrases", f, f"{check}: {', '.join(pats)}"))
        elif check in by_pattern:
            hit = [p for p in pats if p in by_pattern[check]]
            if hit:
                out.append(entry("02.4-phrases", f, f"{check}: {', '.join(hit)}"))

    tools = rule.get("tools", [])
    hook_events = rule.get("hook_events")
    events = ({e.lower() for e in hook_events} if isinstance(hook_events, list) else None)
    entry_points = set(rule.get("entry_points", []))
    for f in s1:
        check = f.get("check")
        if check == "struct.agent-tools":
            if f.get("tools") is None:
                if rule.get("inherit_all"):
                    out.append(entry("02.1-inventory", f, "tool grant: inherits all"))
            else:
                held = {tool_name(t) for t in f["tools"]}
                named = [t for t in tools if t in held]
                if named:
                    out.append(entry("02.1-inventory", f, f"tool grant: {', '.join(named)}"))
                conn = sorted(t for t in held if rule.get("connector_names")
                              and t.startswith("mcp__") and _CONNECTOR.search(t))
                if conn:
                    out.append(entry("02.1-inventory", f, f"connector tool grant: {', '.join(conn)}"))
        elif check == "struct.hooks" and hook_events:
            ev = str(f.get("event") or "")
            if hook_events == "*" or (events is not None and ev.lower() in events):
                out.append(entry("02.1-inventory", f, f"hook event: {ev}"))
        elif check == "struct.mcp" and (rule.get("mcp_servers") or rule.get("connector_names")):
            if rule.get("mcp_servers"):
                out.append(entry("02.1-inventory", f, f"MCP server: {f.get('name')}"))
            blob = " ".join(str(f.get(k) or "") for k in ("name", "command", "url"))
            if rule.get("connector_names") and _CONNECTOR.search(blob):
                out.append(entry("02.1-inventory", f, f"connector MCP server: {f.get('name')}"))
        elif check == "inv.file" and f.get("entry_point") in entry_points:
            out.append(entry("02.1-inventory", f, f"entry point: {f['entry_point']}"))
        elif check == "struct.description" and rule.get("descriptions"):
            out.append(entry("02.1-inventory", f, "description: always-on text"))

    for leg in rule.get("legs", []):
        out.extend((leg_evidence or {}).get(leg, []))
    return _dedupe(out)


def legs(reports: dict) -> list[dict]:
    """One `cap.leg` finding for each of the three legs, present or not. Each leg counts as looked at where it is judged."""
    out = []
    for leg in LEGS:
        ev = evidence(LEG_RULES[leg], reports)
        out.append({"check": "cap.leg", "file": None, "line": None, "leg": leg,
                    "present": bool(ev), "evidence": ev})
        cov.look("cap.leg")
    return out


# Where a grant's evidence comes from (R31, owner 2026-11-07, after an outside tester's report: a quoted example line made
# `elevated` an install grant): the settings (`02.1-inventory`: tools lists, hooks, descriptions, MCP servers) or the wording
# (`02.4-phrases`). Counted here, before the evidence is capped, so a report can say which.
SOURCE_OF = {"02.1-inventory": "settings", "02.4-phrases": "wording"}


def sources(ev: list[dict]) -> dict:
    """{"settings": n, "wording": n}: the grant's evidence entries by where they come from."""
    out = {"settings": 0, "wording": 0}
    for e in ev:
        out[SOURCE_OF.get(e.get("stage"), "settings")] += 1
    return out


def grants(reports: dict, leg_findings: list[dict]) -> list[dict]:
    """One `cap.grant` finding for each grant that has evidence, with `sources` (R31). Each of the grants counts as looked
    at where it is judged, whether it has evidence or not."""
    by_leg = {f["leg"]: f["evidence"] for f in leg_findings}
    out = []
    for g in GRANTS:
        ev = evidence(GRANT_RULES[g], reports, by_leg)
        cov.look("cap.grant")
        if ev:
            out.append({"check": "cap.grant", "file": None, "line": None, "grant": g,
                        "evidence": ev, "sources": sources(ev)})
    return out
