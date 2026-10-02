"""Agent and command tool posture. Spec: specs/posture.SPEC.md. Table: rules.py."""
from __future__ import annotations

from legs import entry, tool_name
from rules import LEAST_PRIVILEGE, POSTURE_INHERIT_ALL, POSTURE_OTHER, POSTURE_PREFIXES, POSTURE_WORDS


def word(name) -> str:
    n = tool_name(name)
    if n in POSTURE_WORDS:
        return POSTURE_WORDS[n]
    for prefix, w in POSTURE_PREFIXES.items():
        if n.startswith(prefix):
            return w
    return POSTURE_OTHER


def words(tools) -> list[str]:
    if tools is None:
        return [POSTURE_INHERIT_ALL]
    return sorted({word(t) for t in tools})


def least_privilege(posture: list[str]) -> bool:
    return list(posture) == LEAST_PRIVILEGE


def postures(reports: dict) -> list[dict]:
    out = []
    for f in (reports.get("01") or {}).get("findings", []):
        if f.get("check") != "struct.agent-tools" or "skipped" in f:
            continue
        p = words(f.get("tools"))
        out.append({"check": "cap.posture", "file": f.get("file"), "line": f.get("line"),
                    "tools": f.get("tools"), "posture": p,
                    "least_privilege": least_privilege(p),
                    "description": f.get("description"),
                    "evidence": [entry("01", f, "tool grant as stated")]})
    return out
