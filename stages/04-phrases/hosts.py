"""Is it ready for any AI? Spec: specs/hosts.SPEC.md.

Slice 3 of the plan for builders (owner, 2026-10-26). From the texts stage 4 reads and stage 1's
inventory: which hosts' files the repository has (hosts.yaml), whether copies kept for two hosts
say the same thing, and which words in text meant for any AI belong to one host.
"""
from __future__ import annotations

import fnmatch
import posixpath
import re
from pathlib import Path

import yaml

from audience import is_test_data

HERE = Path(__file__).resolve().parent
HOSTS = yaml.safe_load((HERE / "hosts.yaml").read_text(encoding="utf-8"))
SKILL_KEYS = set(HOSTS["skill_keys"])
# Keys Claude Code knows (trigger.yaml); a key no host knows is slice 4's (owner, 2026-10-26)
CLAUDE_SKILL_KEYS = set(yaml.safe_load((HERE / "trigger.yaml").read_text(encoding="utf-8"))["keys"]["skill"])
CLAUDE_WORDS = HOSTS["claude_words"]
CLAUDE_TOOLS = re.compile(r"\b(?:" + "|".join(HOSTS["claude_tools"]) + r")\b|\bBash\([^)\n]*\)")
AT_IMPORT = re.compile(r"(?:^|(?<=\s))@([\w./-]+\.\w+)")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
COPILOT_FILE = ".github/copilot-instructions.md"
# A file this short that names the other copy points to it (measured 2026-10-26: a GEMINI.md of
# 7 lines saying to read AGENTS.md).
POINTER_LINES = 10


def _lines(text: str | None) -> list[str]:
    return [x[:-1] if x.endswith("\r") else x for x in (text or "").split("\n")]


def _match(path: str, pattern: str) -> bool:
    if pattern.startswith("**/"):
        return fnmatch.fnmatchcase(path, "*/" + pattern[3:])
    return fnmatch.fnmatchcase(path, pattern)


def _skills_in(files: set, folder: str) -> set:
    rx = re.compile(r"(?:^|/)" + re.escape(folder) + r"/.+/SKILL\.md$")
    return {f for f in files if rx.search(f)}


def _plugin_skills(files: set) -> set:
    """A plugin's skills/<name>/SKILL.md, beside its .claude-plugin/plugin.json."""
    out = set()
    for f in files:
        m = re.match(r"(?:(.*)/)?skills/[^/]+/SKILL\.md$", f)
        if m and posixpath.join(m.group(1) or "", ".claude-plugin/plugin.json") in files:
            out.add(f)
    return out


def hook_host(path: str) -> str:
    """Whose a hook file is: the first other host whose `hooks` match, else Claude Code."""
    for key, h in HOSTS["hosts"].items():
        if key != "claude" and any(_match(path, p) for p in h.get("hooks", [])):
            return key
    return "claude"


def coverage(files: set, hook_files: set) -> list[dict]:
    """One host.coverage per host: its instruction files, skills, MCP config, and hook files here."""
    out = []
    for key, h in HOSTS["hosts"].items():
        inst = sorted({f for f in files for p in h["instructions"] if _match(f, p)})
        if not inst and h.get("fallback"):
            inst = sorted(f for f in files if f in h["fallback"])
        skills = set()
        for folder in h.get("skills", []):
            skills |= _skills_in(files, folder)
        if h.get("plugin_skills"):
            skills |= _plugin_skills(files)
        out.append({"check": "host.coverage", "file": None, "line": None, "host": key, "name": h["name"],
                    "instructions": inst, "skills": len(skills), "skill_files": sorted(skills),
                    "mcp": sorted(f for f in files if f in h.get("mcp", [])),
                    "hooks": sorted(f for f in hook_files if hook_host(f) == key)})
    return out


def _copy_name(rel: str) -> str | None:
    if rel == COPILOT_FILE:
        return rel
    name = rel.rsplit("/", 1)[-1]
    return name if name in HOSTS["copies"] and name != COPILOT_FILE else None


def _points_to(text: str | None, name: str) -> bool:
    """An `@name` import (Claude Code and Gemini CLI expand one anywhere in a line), or a short file
    that names the other copy."""
    lines = [x.strip() for x in _lines(text) if x.strip()]
    imp = re.compile(r"(?:^|[\s(])@(\./)?" + re.escape(name) + r"(?![\w.-])")
    if any(imp.search(x) for x in lines):
        return True
    body = [x for x in lines if not x.startswith("#")]
    return 0 < len(body) <= POINTER_LINES and any(name in x for x in body)


def _links(a: str, b: str, texts: dict, rows: dict) -> bool:
    """`a` is a symlink to `b`, or points to it."""
    target = rows.get(a, {}).get("target")
    name = b.rsplit("/", 1)[-1]
    return bool(target and posixpath.basename(target) == name) or _points_to(texts.get(a), name)


def drift(texts: dict, rows: dict) -> list[dict]:
    """host.drift for each pair of instruction copies kept for different hosts in one folder."""
    by_dir: dict[str, list[str]] = {}
    for rel in set(texts) | {r for r, row in rows.items() if row.get("target") is not None}:
        if is_test_data(rel) or not _copy_name(rel):
            continue
        folder = "" if rel == COPILOT_FILE else (rel.rsplit("/", 1)[0] if "/" in rel else "")
        by_dir.setdefault(folder, []).append(rel)
    order = {n: i for i, n in enumerate(HOSTS["copies"])}
    out = []
    for _folder, rels in sorted(by_dir.items()):
        rels.sort(key=lambda r: order[_copy_name(r)])
        points = {a: {b for b in rels if b != a and _links(a, b, texts, rows)} for a in rels}
        for i, a in enumerate(rels):
            for b in rels[i + 1:]:
                la = [x.rstrip() for x in _lines(texts.get(a))]
                lb = [x.rstrip() for x in _lines(texts.get(b))]
                here = there = 0
                if b in points[a] or a in points[b]:
                    relation = "linked"
                elif points[a] or points[b]:
                    continue  # one points to a third copy; that pair says it
                elif la == lb:
                    relation = "same"
                else:
                    sa = {x.strip() for x in la if x.strip()}
                    sb = {x.strip() for x in lb if x.strip()}
                    relation, here, there = "differ", len(sa - sb), len(sb - sa)
                out.append({"check": "host.drift", "file": a, "line": None, "other": b,
                            "relation": relation, "only_here": here, "only_there": there})
    return out


def _frontmatter(lines: list[str]) -> list[tuple[int, str]]:
    """(line, key) for the top-level keys of a file's frontmatter."""
    if not lines or lines[0].strip() != "---":
        return []
    out = []
    for n in range(1, len(lines)):
        if lines[n].strip() in ("---", "..."):
            return out
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:", lines[n])
        if m:
            out.append((n + 1, m.group(1)))
    return []


def _feature(rel, n, kind, what, host="claude") -> dict:
    return {"check": "host.feature", "file": rel, "line": n, "host": host, "kind": kind, "what": what}


def features(texts: dict, hook_files: set) -> list[dict]:
    """host.feature: one host's words in text meant for any AI (SKILL.md, AGENTS.md), and hooks."""
    out = []
    for rel, text in sorted(texts.items()):
        name = rel.rsplit("/", 1)[-1]
        if text is None or is_test_data(rel) or name not in ("SKILL.md", "AGENTS.md"):
            continue
        lines = _lines(text)
        if name == "SKILL.md":
            out += [_feature(rel, n, "frontmatter", key) for n, key in _frontmatter(lines)
                    if key not in SKILL_KEYS and key in CLAUDE_SKILL_KEYS]
        fence = False
        for n, line in enumerate(lines, start=1):
            if FENCE.match(line):
                fence = not fence
            words = [w for w in CLAUDE_WORDS if w in line]
            if words:
                out.append(_feature(rel, n, "claude-words", ", ".join(words)))
            tools = list(dict.fromkeys(m.group(0) for m in CLAUDE_TOOLS.finditer(line)))
            if tools:
                out.append(_feature(rel, n, "claude-tool", ", ".join(tools)))
            if name == "AGENTS.md" and not fence:
                imports = AT_IMPORT.findall(re.sub(r"`[^`]*`", " ", line))
                if imports:
                    out.append(_feature(rel, n, "import", ", ".join(imports)))
    for f in sorted(hook_files):
        host = hook_host(f)
        out.append(_feature(f, None, "hooks", HOSTS["hosts"][host]["name"], host))
    return out


def findings(texts: dict, file_rows: list, hook_rows: list) -> list[dict]:
    files = {r["file"] for r in file_rows if r.get("file") and not is_test_data(r["file"])}
    rows = {r["file"]: r for r in file_rows if r.get("file")}
    hook_files = {h["file"] for h in hook_rows if h.get("file") and not is_test_data(h["file"])}
    return coverage(files, hook_files) + drift(texts, rows) + features(texts, hook_files)
