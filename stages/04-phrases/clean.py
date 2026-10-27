"""Is it current and clean? Spec: specs/clean.SPEC.md.

Slice 6 of the plan for builders (owner, 2026-10-27): unfinished text, dated claims, pinned model
IDs, and older tool names, as facts with locations (clean.yaml). Nothing here judges whether a
date is past, a model retired, or a TODO matters.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from asks import FENCE, unquoted
from audience import audience
from trigger import T as TRIGGER

HERE = Path(__file__).resolve().parent
C = yaml.safe_load((HERE / "clean.yaml").read_text(encoding="utf-8"))
UNFINISHED = {kind: [re.compile(p) for p in spec.get("exact", [])]
              + [re.compile(p, re.I) for p in spec.get("any_case", [])]
              for kind, spec in C["unfinished"].items()}
TEMPLATE = [re.compile(p, re.I) for p in C["template_paths"]]
DATED = [re.compile(p.replace("{months}", C["months"]), re.I) for p in C["dated"]]
MODELS = [re.compile(p, re.I) for p in C["models"]]
OLDER = TRIGGER["older_tools"]
_O = "|".join(OLDER)
OLDER_RX = re.compile(r"`(" + _O + r")`|\b(" + _O + r") tool\b|\b(" + _O + r")\(")
SPAN = re.compile(r"`[^`\n]*`")
FILE_EXT = re.compile(r"\.(md|mdx|json|jsonl|ya?ml|py|ts|js|txt|html|csv)$", re.I)
MARKDOWN = (".md", ".mdx", ".markdown", ".mdc")
READS = ("model", "subagent")  # text the AI reads (audience.py)


def _lines(text: str) -> list[str]:
    return [x[:-1] if x.endswith("\r") else x for x in (text or "").split("\n")]


def regions(rel: str, lines: list[str]) -> list[tuple[int, str, str]]:
    """(line, text, region): `frontmatter`, `code` (fenced, or a file that is not Markdown), or
    `text`."""
    if not rel.lower().endswith(MARKDOWN):
        return [(n, x, "code") for n, x in enumerate(lines, start=1)]
    out, fence, front = [], None, bool(lines) and lines[0].strip() == "---"
    for n, line in enumerate(lines, start=1):
        if front:
            out.append((n, line, "frontmatter"))
            if n > 1 and line.strip() in ("---", "..."):
                front = False
            continue
        m = FENCE.match(line)
        if fence:
            out.append((n, line, "code"))
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            continue
        if m:
            fence = m.group(1)
            out.append((n, line, "code"))
            continue
        out.append((n, line, "text"))
    return out


def _in_span(line: str, pos: int) -> bool:
    return any(m.start() <= pos < m.end() for m in SPAN.finditer(line))


def file_findings(rel: str, text: str, aud: str) -> list[dict]:
    md = rel.lower().endswith(MARKDOWN)
    template = any(p.search(rel) for p in TEMPLATE)
    out, seen = [], set()
    for n, line, reg in regions(rel, _lines(text)):
        prose = unquoted(SPAN.sub(" ", line)) if md else line  # a quoted or code "TODO" is a mention
        if not (md and reg == "code"):  # a fenced example's TODO is the example's
            for kind, pats in UNFINISHED.items():
                if kind == "placeholder" and template:
                    continue  # a template's placeholders are what it ships (owner, 2026-10-27)
                if kind != "todo" and reg == "code":
                    continue  # in code, `{{x}}` is an f-string's brace (measured 2026-10-27); markers only
                if any(p.search(prose) for p in pats):
                    out.append({"check": "clean.unfinished", "file": rel, "line": n, "kind": kind,
                                "quote": line.strip(), "audience": aud})
        if aud in READS and md and reg == "text" and any(p.search(unquoted(prose)) for p in DATED):
            out.append({"check": "clean.dated", "file": rel, "line": n, "quote": line.strip(), "audience": aud})
        for p in MODELS:
            for m in p.finditer(line):
                mid = m.group(0).rstrip(".-:")
                if mid.lower().endswith("-latest") or FILE_EXT.search(mid) or (n, mid.lower()) in seen:
                    continue  # an alias that follows, or a file name (claude-fable-5.md)
                seen.add((n, mid.lower()))
                where = "code" if reg == "text" and _in_span(line, m.start()) else reg
                out.append({"check": "clean.model", "file": rel, "line": n, "model": mid, "where": where,
                            "audience": aud})
        if aud in READS and md and reg == "text":
            for tool in dict.fromkeys(next(g for g in m.groups() if g) for m in OLDER_RX.finditer(line)):
                out.append({"check": "clean.older", "file": rel, "line": n, "tool": tool, "now": OLDER[tool],
                            "audience": aud})
    return out


def findings(texts: dict, scripts=(), hook_configs=()) -> list[dict]:
    """Every file but those written for people and test data, in path order; then one
    `clean.checked` row in every run (a report tells "none" from "made before slice 6")."""
    out, n = [], 0
    for rel in sorted(texts):
        aud = audience(rel, scripts, hook_configs)
        if aud not in ("human", "test-data") and texts[rel] is not None:
            out += file_findings(rel, texts[rel], aud)
            n += 1
    return out + [{"check": "clean.checked", "file": None, "line": None, "files": n}]
