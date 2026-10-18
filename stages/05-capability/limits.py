"""Stated limits and what backs them. Spec: specs/limits.SPEC.md.

Review C32 (partner's v3, 2026-10-14; built 2026-10-17). A line that tells the AI to stay read-only
is wording; whether a tool setting enforces it is a separate fact. For each read-only line a model
reads, this pairs the wording (stage 4) with what could back it: a restricting setting on the same
line (stage 4 `limit.setting`), the tools list of the skill or agent that owns the file (stage 1),
and other routes in the same skill that can write. Derived only; it detects nothing new and never
says a limit is broken, only what Walkdown found.
"""
from __future__ import annotations

import re
from pathlib import PurePosixPath

from legs import entry

LIMIT_WORDS = re.compile(r"\bread[- ]only\b|\bno side effects\b", re.I)
WRITE_CAPABLE = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"}
INSTRUCTION = ("model", "subagent")


def _fnd(reports, stage, check):
    return [f for f in (reports.get(stage) or {}).get("findings", []) if f.get("check") == check]


def _base(t) -> str:
    return str(t).split("(", 1)[0].strip()


def _writes(tools) -> list[str]:
    """The write-capable tools in a tools list ("*" counts as all of them)."""
    names = {_base(t) for t in tools or []}
    if "*" in names:
        return sorted(WRITE_CAPABLE)
    return sorted(names & WRITE_CAPABLE)


def _candidates(reports) -> dict:
    """(file, line) -> the stage 4 finding that states a read-only limit, instruction text only."""
    out = {}
    for f in (reports.get("04") or {}).get("findings", []):
        if f.get("audience") not in INSTRUCTION:
            continue
        if f.get("check", "").startswith("phrase.") and "B.safety-adjective" in (f.get("patterns") or []):
            text = f.get("quote") or ""
        elif f.get("check") == "term.safety":
            text = f"{f.get('term') or ''} {f.get('quote') or ''}"
        else:
            continue
        if LIMIT_WORDS.search(text):
            out.setdefault((f.get("file"), f.get("line")), f)
    return out


def _owner(rel: str, kinds: dict, skill_dirs: list[str]) -> tuple[str | None, str | None]:
    """(owner file, the folder the owner covers): the file itself when it is a skill, agent, or
    command; else the SKILL.md of the nearest skill folder above it."""
    if kinds.get(rel) in ("skill", "agent", "command"):
        d = str(PurePosixPath(rel).parent)
        return rel, (d if kinds[rel] == "skill" else None)
    for d in skill_dirs:  # longest first
        if d == "." or rel.startswith(d + "/"):
            return (f"{d}/SKILL.md" if d != "." else "SKILL.md"), d
    return None, None


def stated_limits(reports: dict) -> list[dict]:
    inv = (reports.get("01") or {}).get("findings", [])
    kinds = {f["file"]: f.get("entry_point") for f in inv if f.get("check") == "inv.file"}
    skill_dirs = sorted((str(PurePosixPath(f).parent) for f, k in kinds.items() if k == "skill"),
                        key=len, reverse=True)
    tools = {f["file"]: f for f in _fnd(reports, "01", "struct.agent-tools")}
    settings = [s for s in _fnd(reports, "04", "limit.setting") if s.get("audience") != "test-data"]
    on_line = {}
    for s in settings:
        on_line.setdefault((s.get("file"), s.get("line")), []).append(s)

    out = []
    for (rel, line), f in sorted(_candidates(reports).items(), key=lambda kv: (kv[0][0] or "", kv[0][1] or 0)):
        owner, folder = _owner(rel, kinds, skill_dirs)
        row = tools.get(owner) if owner else None
        owner_tools = row.get("tools") if row else None
        ev = [entry("04", f, "read-only wording")]
        status, backed_by = "stated", None
        flags = [s for s in on_line.get((rel, line), []) if "write" in (s.get("rules_out") or [])]
        if flags:
            status, backed_by = "backed", "flag"
            ev += [entry("04", s, f"a {s['kind']} setting on the line rules out writing") for s in flags]
        elif owner_tools is not None and not _writes(owner_tools):
            status, backed_by = "backed", "tools-list"
            ev.append(entry("01", row, f"tools list of {owner}: {', '.join(map(str, owner_tools))}"))
        elif owner_tools is not None:
            status = "contradicted"
            ev.append(entry("01", row, f"tools list of {owner} can write: {', '.join(_writes(owner_tools))}"))

        routes = []
        if folder is not None:
            inside = lambda p: folder == "." or (p or "").startswith(folder + "/")  # noqa: E731
            for s in settings:
                if s.get("grants_write") and inside(s.get("file")) and (s.get("file"), s.get("line")) != (rel, line):
                    routes.append({"file": s["file"], "line": s.get("line"),
                                   "what": f"a {s['kind']} setting that allows writing"
                                           + (f" ({s['value']})" if s.get("value") else "")})
            for p, t in tools.items():
                if p == owner or not inside(p) or kinds.get(p) not in ("agent", "command"):
                    continue
                if t.get("tools") is None or _writes(t.get("tools")):
                    routes.append({"file": p, "line": t.get("line"),
                                   "what": "an agent with no tools list" if t.get("tools") is None
                                           else f"an agent that can write ({', '.join(_writes(t['tools']))})"})
        ev += [{"stage": "04" if r["what"].startswith("a ") and "setting" in r["what"] else "01",
                "check": "limit.setting" if "setting" in r["what"] else "struct.agent-tools",
                "file": r["file"], "line": r["line"], "why": f"another route in the skill: {r['what']}"}
               for r in routes]
        out.append({"check": "cap.limit", "file": rel, "line": line, "limit": "read-only",
                    "quote": f.get("quote"), "status": status, "backed_by": backed_by,
                    "flags": [s["kind"] for s in flags],
                    "owner": owner, "owner_tools": owner_tools, "other_routes": routes,
                    "other_route_at": [f"{r['file']}:{r['line']}" for r in routes], "evidence": ev})
    return out
