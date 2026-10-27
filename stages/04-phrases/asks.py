"""What the text asks a tool to do, and loops with no stated limit. Spec: specs/asks.SPEC.md.

Slice 5 of the plan for builders (owner, 2026-10-26). In text the AI reads: by family of work
(shell, write, web, search, agent), the lines that ask for it; tools named outright; and loops
with no limit stated on their line or the next. The cues are in asks.yaml.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

import needs
from audience import audience

HERE = Path(__file__).resolve().parent
A = yaml.safe_load((HERE / "asks.yaml").read_text(encoding="utf-8"))
RULES = {fam: [[re.compile(p, re.I) for p in rule] for rule in rules] for fam, rules in A["families"].items()}
_T = "|".join(A["named_tools"])
NAMED = re.compile(r"`(" + _T + r")`|\b(" + _T + r") tool\b|\b(" + _T + r")\(")
NOT_ASKING = re.compile(A["not_asking"], re.I)
NOUN_BEFORE = re.compile(A["noun_before"], re.I)
QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”')
LOOPS = [re.compile(p, re.I) for p in A["loops"]]
LIMITS = [re.compile(p, re.I) for p in A["limits"]]
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
END = re.compile(r"[.!?:;]\s*$")
ITEM = re.compile(r"^([-*+]\s|\d+[.)]\s|#|>|\|)")
READS = ("model", "subagent")  # text the AI reads (audience.py)


def _lines(text: str) -> list[str]:
    return [x[:-1] if x.endswith("\r") else x for x in (text or "").split("\n")]


def sentences(lines: list[str]) -> list[tuple[int, str]]:
    """(first line, text): a line joined with the next while it does not end a sentence, never
    across a blank line, a list item, a heading, or fenced code (left out)."""
    out, buf, fence = [], None, None

    def flush():
        nonlocal buf
        if buf:
            out.append(buf)
        buf = None

    for n, line in enumerate(lines, start=1):
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            flush()
            fence = m.group(1)
            continue
        s = line.strip()
        if not s:
            flush()
            continue
        if buf and ITEM.match(s):
            flush()
        buf = (buf[0], buf[1] + " " + s) if buf else (n, s)
        if END.search(s):
            flush()
    flush()
    return out


def _outside_fences(lines: list[str]):
    fence = None
    for n, line in enumerate(lines, start=1):
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        yield n, line


def _without_frontmatter(lines: list[str]) -> list[str]:
    """Frontmatter blanked, line numbers kept: a tools list names tools, it asks for nothing."""
    if not lines or lines[0].strip() != "---":
        return lines
    end = next((k for k in range(1, len(lines)) if lines[k].strip() in ("---", "...")), None)
    return lines if end is None else [""] * (end + 1) + lines[end + 1:]


def unquoted(s: str) -> str:
    """Quoted text blanked: a quoted example asks for nothing."""
    return QUOTED.sub(lambda m: " " * len(m.group(0)), s)


def asks_for(rule, s: str) -> bool:
    """The rule's verb (its first pattern) somewhere in `s`, used as a verb (not right after "/",
    "-", or a determiner) with no negation shortly before it in its clause, and every other
    pattern in `s`."""
    if not all(p.search(s) for p in rule[1:]):
        return False
    return any(not NOT_ASKING.search(s[:m.start()]) and not NOUN_BEFORE.search(s[:m.start()])
               for m in rule[0].finditer(s))


def file_findings(rel: str, text: str, aud: str, servers=()) -> list[dict]:
    lines = _without_frontmatter(_lines(text))
    text = "\n".join(lines)
    fams: dict[str, set] = {}
    for n, s in sentences(lines):
        s = unquoted(s)
        for fam, rules in RULES.items():
            if any(asks_for(rule, s) for rule in rules):
                fams.setdefault(fam, set()).add(n)
    if rel.lower().endswith((".md", ".mdx", ".markdown")):
        for n, word in needs._instruction_uses(text):  # commands in shell blocks and inline code
            if needs.program(word):
                fams.setdefault("shell", set()).add(n)
    out = [{"check": "ask.tools", "file": rel, "line": min(ls), "family": fam, "lines": sorted(ls),
            "audience": aud} for fam, ls in sorted(fams.items())]
    named: dict[str, set] = {}
    srv = {s: re.compile(r"\bmcp__" + re.escape(s) + r"\b|\b" + re.escape(s) + r"\b", re.I) for s in servers}
    for n, line in enumerate(lines, start=1):
        for m in NAMED.finditer(line):
            named.setdefault(next(g for g in m.groups() if g), set()).add(n)
        for s, rx in srv.items():
            if rx.search(line):
                named.setdefault(f"mcp__{s}", set()).add(n)
    out += [{"check": "ask.named", "file": rel, "line": min(ls), "tool": t, "lines": sorted(ls), "audience": aud}
            for t, ls in sorted(named.items())]
    for n, line in _outside_fences(lines):
        if not any(p.search(unquoted(re.sub(r"`[^`]*`", " ", line))) for p in LOOPS):
            continue
        nxt = lines[n] if n < len(lines) else ""
        if any(p.search(line) or p.search(nxt) for p in LIMITS):
            continue
        out.append({"check": "fit.loop", "file": rel, "line": n, "quote": line.strip(), "audience": aud})
    return out


def findings(texts: dict, scripts=(), hook_configs=(), servers=()) -> list[dict]:
    """Every file the AI reads (audience model or subagent), in path order."""
    out = []
    for rel in sorted(texts):
        aud = audience(rel, scripts, hook_configs)
        if aud in READS and texts[rel] is not None:
            out += file_findings(rel, texts[rel], aud, servers)
    return out


def servers_of(entries: list[dict]) -> set:
    """The MCP servers the entries grant tools from (`mcp__<server>__...`)."""
    out = set()
    for e in entries:
        for g in e.get("grants") or []:
            parts = g.split("(", 1)[0].split("__")
            if len(parts) >= 2 and parts[0] == "mcp" and parts[1]:
                out.add(parts[1])
    return out
