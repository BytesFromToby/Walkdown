"""Do the tools fit the job? Spec: specs/fit.SPEC.md.

Slice 5 of the plan for builders (owner, 2026-10-26). For each skill, agent, and command (stage
4's trig.entry), what its reach asks tools to do (stage 4's ask.tools and ask.named, over the
reach slice 1 counts) against what it grants; and for each hook, how often it runs and what its
output adds. Families and hook facts are in fit.yaml. Nothing is run or read here.
"""
from __future__ import annotations

from pathlib import Path

import yaml

import cost
from hosts import hook_host  # stage 4's: whose a hook file is (slice 3)

HERE = Path(__file__).resolve().parent
F = yaml.safe_load((HERE / "fit.yaml").read_text(encoding="utf-8"))
FAMILY_OF = {t: fam for fam, tools in F["families"].items() for t in tools}
OFTEN = {ev.lower(): k for k, evs in F["how_often"].items() for ev in evs}
TOOL_EVENTS = {ev.lower() for ev in F["tool_events"]}
CLAUDE_EVENTS = set(F["claude_events"])


def tool_name(item: str) -> str:
    return str(item).split("(", 1)[0].strip()


def family_of(item: str) -> str | None:
    """The family a granted tool works in; `mcp` for an MCP tool; None for reading tools and
    names no family lists (never reported)."""
    name = tool_name(item)
    if name.startswith("mcp__"):
        return "mcp"
    return FAMILY_OF.get(name)


def _server(item: str) -> str:
    parts = tool_name(item).split("__")
    return parts[1] if len(parts) > 1 else ""


def _f04(reports, check) -> list[dict]:
    return [f for f in (reports.get("04") or {}).get("findings", []) if f.get("check") == check]


def entries_fit(reports, graph) -> list[dict]:
    """fit.unused, fit.missing, fit.inherits (spec)."""
    entries = [e for e in _f04(reports, "trig.entry") if e.get("mode") not in ("unread", "skipped")]
    asks: dict[str, dict] = {}
    for a in _f04(reports, "ask.tools"):
        asks.setdefault(a["file"], {})[a["family"]] = a["lines"]
    named: dict[str, set] = {}
    for a in _f04(reports, "ask.named"):
        named.setdefault(a["file"], set()).add(a["tool"])
    out_edges = cost._out(graph) if graph is not None else {}
    # missing and inherits: only references the AI follows to one file (measured 2026-10-27: a
    # plugin agent's `CLAUDE.md`, meaning the project it works in, matched only the example
    # project's CLAUDE.md by name)
    followed = {u: [e for e in es if not (e.get("by_name") or e.get("ambiguous"))] for u, es in out_edges.items()}
    scripts = {r for r in cost._files(reports) if cost._is_script(r)}
    skills = {e["name"]: e["file"] for e in entries if e["kind"] == "skill" and e.get("name")}

    def reach(rel, kind, kinds, edges):
        if graph is None:
            return {rel}
        return cost.reach(rel, kind, edges, kinds, scripts)[0]

    def reach_of(e, kinds, edges):
        mine = reach(e["file"], e["kind"], kinds, edges)
        for s in e.get("preloads") or []:  # a subagent's `skills` load with it
            if s in skills:
                mine |= reach(skills[s], "skill", kinds, edges)
        return mine

    def asked_in(mine):
        asked: dict[str, tuple] = {}
        for r in sorted(mine):
            for fam, lines in sorted(asks.get(r, {}).items()):
                asked.setdefault(fam, (r, lines[0]))
        return asked

    rows = []
    for e in sorted(entries, key=lambda x: x["file"]):
        rel, kind = e["file"], e["kind"]
        # never used: over every kind of reference (generous); missing and inherits: over the
        # references the AI follows (measured 2026-10-27: an example project's CLAUDE.md, reached
        # only through a folder named in passing, made a plugin's agent "missing" a shell)
        mine, loads = reach_of(e, cost.LOOSE, out_edges), reach_of(e, cost.LOADS, followed)
        used_fams, asked = asked_in(mine), asked_in(loads)
        names = set().union(*(named.get(r, set()) for r in mine)) if mine else set()
        where = {fam: f"{f}:{ln}" for fam, (f, ln) in asked.items()}
        grants = e.get("grants")
        if kind == "agent" and grants is None:
            rows.append({"check": "fit.inherits", "file": rel, "line": None, "families": sorted(asked),
                         "asked_at": where, "reach": len(loads)})
        for item in grants or []:
            fam = family_of(item)
            if fam is None:
                continue
            used = (f"mcp__{_server(item)}" in names) if fam == "mcp" else (fam in used_fams or tool_name(item) in names)
            if not used:
                rows.append({"check": "fit.unused", "file": rel, "line": e.get("grants_line"), "kind_of": kind,
                             "tool": item, "family": fam, "pre_approved": kind != "agent", "reach": len(mine)})
        gone = {tool_name(i) for i in e.get("disallowed") or []}
        if kind == "agent" and grants is not None:
            have = {family_of(i) for i in grants if tool_name(i) not in gone}
            why = "none of its tools does this"
        else:
            have = {fam for fam, tools in F["families"].items() if any(t not in gone for t in tools)}
            why = "its disallowed tools remove every tool that does this"
        for fam, (f, ln) in sorted(asked.items()):
            if fam not in have:
                rows.append({"check": "fit.missing", "file": rel, "line": e.get("grants_line"), "kind_of": kind,
                             "family": fam, "asked_at": f"{f}:{ln}", "why": why})
    # one row in every run: the check ran (a report tells "none" from "made before slice 5")
    rows.append({"check": "fit.checked", "file": None, "line": None, "entries": len(entries),
                 "with_grants": sum(1 for e in entries if e.get("grants")),
                 "inheriting": sum(1 for e in entries if e["kind"] == "agent" and e.get("grants") is None)})
    return rows


def hooks_fit(reports, injections) -> list[dict]:
    """fit.hook, one per hook (spec)."""
    size = {(i.get("file"), i.get("event"), i.get("command")): i.get("bytes") for i in injections
            if i.get("mechanism") == "hook"}
    rows = []
    for h in (reports.get("01") or {}).get("findings", []):
        if h.get("check") != "struct.hooks" or "skipped" in h:
            continue
        ev = str(h.get("event") or "")
        host = hook_host(h.get("file") or "")
        often = OFTEN.get(ev.lower(), "other")  # other hosts spell events in camelCase
        matcher = h.get("matcher")
        if ev.lower() in TOOL_EVENTS and matcher not in (None, "", "*"):
            often = "matching-tool-calls"
        # Claude Code's facts for Claude Code's own events; for another host, or another spelling, not known
        known = host == "claude" and ev in CLAUDE_EVENTS
        b = size.get((h.get("file"), ev, h.get("command")))
        rows.append({"check": "fit.hook", "file": h.get("file"), "line": h.get("line"), "event": ev, "host": host,
                     "matcher": matcher, "how_often": often,
                     "adds_context": (ev in F["stdout_context"]) if known else None,
                     "bytes": b, "over_cap": b is not None and b > F["output_cap_chars"]})
    return rows
