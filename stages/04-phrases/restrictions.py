"""Settings that restrict what tools an agent can use. Spec: specs/restrictions.SPEC.md.

Review C32 (partner's v3, 2026-10-14; built 2026-10-17): read-only wording is easy to find; whether
a tool setting backs it is not. This table records every flag or setting that restricts tools, so
stage 5 can pair it with the wording. A fact, never a risk: no restriction is flagged on its own.
"""
from __future__ import annotations

import re

WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
SHELL_TOOLS = {"Bash"}
NETWORK_TOOLS = {"WebFetch", "WebSearch"}
ORDER = ("write", "shell", "network")

# --tools and --disallowedTools with a quoted (possibly empty) or bare list. --allowedTools is left
# out on purpose: it pre-approves the tools it names and leaves every other tool available.
LIST_FLAG = re.compile(r"""--(?P<flag>tools|disallowed-?tools)(?:\s+|=)"""
                       r"""(?:(?P<q>["'])(?P<quoted>[^"']*)(?P=q)|(?P<bare>[^\s"'`]+))""", re.I)
SANDBOX = re.compile(r"""(?:--sandbox(?:\s+|=)|\bsandbox_mode\s*=\s*)["']?"""
                     r"""(?P<v>read-only|workspace-write|danger-full-access)\b""", re.I)
MODE = re.compile(r"""(?:--permission-mode(?:\s+|=)|"?defaultMode"?\s*[:=]\s*)["']?"""
                  r"""(?P<v>plan|default|acceptEdits|bypassPermissions|dontAsk)\b""")
DENY = re.compile(r""""deny"\s*:\s*\[(?P<list>[^\]]*)\]""")
TOOL = re.compile(r"^(?:[A-Z][A-Za-z]*|mcp__[\w-]+)(?:\([^)]*\))?$|^\*$")


def _tokens(value: str) -> list[str] | None:
    """Tool names in a flag's value, or None when it does not read as a tool list."""
    toks = [t for t in re.split(r"[,\s]+", value.strip()) if t]
    return toks if all(TOOL.match(t) for t in toks) else None


def _base(t: str) -> str:
    return t.split("(", 1)[0]


def _allowlist(tools: list[str]) -> tuple[list[str], bool]:
    names = {_base(t) for t in tools}
    star = "*" in names
    out = {"write": not star and not names & (WRITE_TOOLS | SHELL_TOOLS),
           "shell": not star and "Bash" not in names,
           "network": not star and not names & (NETWORK_TOOLS | SHELL_TOOLS)}
    return [k for k in ORDER if out[k]], star or bool(names & (WRITE_TOOLS | SHELL_TOOLS))


def _denylist(tools: list[str]) -> list[str]:
    bare = {t for t in tools if "(" not in t}  # Bash(git push:*) denies one use, not the tool
    out = {"write": (WRITE_TOOLS | SHELL_TOOLS) <= bare, "shell": "Bash" in bare,
           "network": (NETWORK_TOOLS | SHELL_TOOLS) <= bare}
    return [k for k in ORDER if out[k]]


def settings_in_line(line: str) -> list[dict]:
    """Each restricting setting a line names: kind, tools or value, rules_out, grants_write."""
    out = []
    for m in LIST_FLAG.finditer(line):
        raw = m.group("quoted") if m.group("q") else m.group("bare")
        tools = _tokens(raw)
        if tools is None:
            continue
        if m.group("flag").lower() == "tools":
            rules_out, grants = _allowlist(tools)
            out.append({"kind": "tools-flag", "tools": tools, "rules_out": rules_out,
                        "grants_write": grants})
        else:
            out.append({"kind": "deny", "tools": tools, "rules_out": _denylist(tools),
                        "grants_write": False})
    for m in DENY.finditer(line):
        tools = re.findall(r"""["']([^"']+)["']""", m.group("list"))
        if tools and all(TOOL.match(t) for t in tools):
            out.append({"kind": "deny", "tools": tools, "rules_out": _denylist(tools),
                        "grants_write": False})
    for m in SANDBOX.finditer(line):
        v = m.group("v").lower()
        out.append({"kind": "sandbox", "value": v, "rules_out": ["write"] if v == "read-only" else [],
                    "grants_write": v in ("workspace-write", "danger-full-access")})
    for m in MODE.finditer(line):
        v = m.group("v")
        out.append({"kind": "permission-mode", "value": v,
                    "rules_out": ["write", "shell"] if v == "plan" else [],
                    "grants_write": v in ("acceptEdits", "bypassPermissions")})
    return out


def limit_file(rel: str, raw: list[str], folded: list[str], aud: str) -> list[dict]:
    """One `limit.setting` finding per setting, any audience; the quote is the raw line."""
    out = []
    for n, line in enumerate(folded, start=1):
        for s in settings_in_line(line):
            out.append({"check": "limit.setting", "file": rel, "line": n, **s, "audience": aud,
                        "quote": raw[n - 1]})
    return out
