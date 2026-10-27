"""Will it trigger? Spec: specs/trigger.SPEC.md.

Slice 4 of the plan for builders (owner, 2026-10-26). For each skill, agent, and command: how it
triggers, frontmatter its host does not read, the name and description rules, published
guidance, keys and values no host takes, tool names no host knows, descriptions that overlap, and
the listing they make together. The rules and their sources are in trigger.yaml.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from audience import is_test_data

HERE = Path(__file__).resolve().parent
T = yaml.safe_load((HERE / "trigger.yaml").read_text(encoding="utf-8"))
KEYS = {"skill": T["keys"]["skill"], "command": T["keys"]["skill"], "agent": T["keys"]["agent"]}
TOOLS = set(T["tools"])
OLDER = T["older_tools"]
NAME_RX = re.compile(T["name"]["pattern"])
MODEL_ID = re.compile(T["model_id"])
XML = re.compile(r"<[A-Za-z/][^>]*>")
WHEN = [re.compile(p, re.I) for p in T["when_patterns"]]
FIRST = [re.compile(p) for p in T["person_patterns"]["first"]]
SECOND = [re.compile(p, re.I) for p in T["person_patterns"]["second"]]
STOP = set(T["stopwords"])
BOOLS = {"true", "false", "yes", "no", "on", "off", "1", "0"}
TOOL_FIELDS = {"skill": ("allowed-tools", "disallowed-tools"), "command": ("allowed-tools", "disallowed-tools"),
               "agent": ("tools", "disallowedTools")}
SPLIT = re.compile(r"[,\s]+(?![^()]*\))")
KEY_LINE = re.compile(r"^([A-Za-z_][\w.-]*)\s*:")
# Whose rule each is: the Agent Skills spec (other hosts, uploads), claude.ai uploads and the
# Skills API, or Claude Code.
RULE_HOST = {"name-missing": "agent-skills", "name-long": "agent-skills", "name-chars": "agent-skills",
             "name-folder": "agent-skills", "description-missing": "agent-skills",
             "description-empty": "agent-skills", "description-long": "agent-skills",
             "name-reserved": "claude-api", "name-xml": "claude-api", "description-xml": "claude-api",
             "listing-cut": "claude", "agent-name": "claude", "name-duplicate": "claude"}


@dataclass
class Front:
    first: int          # index of the opening ---
    end: int            # index of the closing ---
    data: dict | None   # None when the YAML does not parse
    error: str | None
    keys: list          # (line, key), top level


def _lines(text: str | None) -> list[str]:
    return [x[:-1] if x.endswith("\r") else x for x in (text or "").split("\n")]


def read_front(lines: list[str]) -> Front | None:
    """The frontmatter: the first non-blank line `---` and its closing `---` or `...`."""
    i = next((k for k, x in enumerate(lines) if x.strip()), None)
    if i is None or lines[i].strip() != "---":
        return None
    end = next((k for k in range(i + 1, len(lines)) if lines[k].strip() in ("---", "...")), None)
    if end is None:
        return None
    body = lines[i + 1:end]
    data, err = None, None
    try:
        loaded = yaml.safe_load("\n".join(body))
        if isinstance(loaded, dict):
            data = loaded
        elif loaded is None:
            data = {}
        else:
            err = f"frontmatter is a {type(loaded).__name__}, not a mapping"
    except yaml.YAMLError as e:
        err = str(e).split("\n")[0]
    keys = [(i + 2 + k, m.group(1)) for k, x in enumerate(body) if (m := KEY_LINE.match(x))]
    return Front(i, end, data, err, keys)


def entry_kind(row: dict) -> str | None:
    """skill, agent, or command, as Claude Code loads them; None for anything else."""
    folders = row["file"].split("/")[:-1]
    ep = row.get("entry_point")
    if ep == "skill":
        return "skill"
    if ep == "command" and "commands" in folders:
        return "command"
    if ep == "agent" and "agents" in folders:
        return "agent"
    return None


def near(word: str, known) -> str | None:
    """The known name a word is closest to: the same once case, `-`, and `_` are set aside, or
    one spelling slip away."""
    norm = re.sub(r"[-_\s]", "", word.lower())
    for k in known:
        if re.sub(r"[-_\s]", "", k.lower()) == norm:
            return k
    m = difflib.get_close_matches(word, list(known), n=1, cutoff=0.8)
    return m[0] if m else None


def _truthy(v) -> bool:
    return v is True or str(v).strip().lower() in ("true", "yes", "on", "1")


def _text(v) -> str | None:
    return None if v is None else (v if isinstance(v, str) else str(v))


def _items(v) -> list[str] | None:
    """A tools or skills field as a list of its items as written; None when absent."""
    if v is None:
        return None
    items = [_text(x) for x in v] if isinstance(v, list) else SPLIT.split(_text(v))
    return [x.strip() for x in items if x and x.strip()]


def words(s: str) -> set:
    """Content words: lower case, three letters or more, not a stop word, a plural's s dropped."""
    out = set()
    for w in re.findall(r"[a-z][a-z'-]*", (s or "").lower()):
        w = w.strip("'-")
        if len(w) < 3 or w in STOP:
            continue
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.add(w)
    return out


def _f(check, rel, line, **kw) -> dict:
    return {"check": check, "file": rel, "line": line, **kw}


def check_entry(rel: str, kind: str, text: str, bom: bool = False) -> tuple[dict | None, list]:
    """(the trig.entry row, or None for a file Claude Code never loads as one; its findings)."""
    lines = _lines(text)
    front = read_front(lines)
    out = []
    if kind == "agent" and front is None:
        return None, []  # documentation kept beside the agents
    entry = _f("trig.entry", rel, None, kind=kind, name=None, description_chars=0, listing_chars=0,
               mode="auto", menu=True, description_from=None)
    read = front is not None and front.first == 0 and front.data is not None
    if front is None:
        if kind == "skill":
            out.append(_f("trig.frontmatter", rel, None, kind="missing", kind_of=kind))
    elif front.first > 0:
        out.append(_f("trig.frontmatter", rel, front.first + 1, kind="not-first-line", kind_of=kind))
    elif front.data is None:
        out.append(_f("trig.frontmatter", rel, 1, kind="yaml-error", kind_of=kind, error=front.error))
    elif bom:
        out.append(_f("trig.frontmatter", rel, 1, kind="bom", kind_of=kind))
    folder = rel.split("/")[-2] if rel.endswith("SKILL.md") and "/" in rel else None
    if front is not None and not read:
        entry.update(mode="skipped" if kind == "agent" else "unread", why="its frontmatter is not read",
                     name=folder if kind == "skill" else None)
        return entry, out
    data = front.data if read else {}
    keyline = {k: n for n, k in (front.keys if read else [])}
    name, desc, wtu = _text(data.get("name")), _text(data.get("description")), _text(data.get("when_to_use"))
    body_start = front.end + 1 if read else 0
    if desc is None and kind != "agent":  # Claude Code uses the first non-empty line
        first = next((x.strip() for x in lines[body_start:] if x.strip()), None)
        entry["description_from"] = "first line" if first else None
        listing = first or ""
    else:
        entry["description_from"] = "frontmatter" if desc is not None else None
        listing = desc or ""
    if wtu:
        listing += " " + wtu
    entry.update(name=name or (folder if kind == "skill" else rel.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                               if kind == "command" else None),
                 description_chars=len(desc or ""), listing_chars=len(listing))
    gfield, dfield = TOOL_FIELDS[kind]  # what it grants, for slice 5 (stage 5 fit.py)
    entry.update(grants=_items(data.get(gfield)), grants_line=keyline.get(gfield),
                 disallowed=_items(data.get(dfield)) or [],
                 preloads=_items(data.get("skills")) if kind == "agent" else None)

    def rule(r, line=None, **kw):
        out.append(_f("trig.rule", rel, line, kind_of=kind, rule=r, host=RULE_HOST[r], **kw))

    if kind == "agent":
        why = None
        if not name and not desc:
            return None, out  # documentation kept beside the agents
        if not name:
            why = "it has no name: Claude Code treats it as documentation"
        elif not desc:
            why = "it has a name but no description"
        elif name.startswith("-") or ":" in name or len(name) > T["agent_name_max"]:
            why = "Claude Code skips this name"
            rule("agent-name", keyline.get("name"), value=name)
        if why:
            entry.update(mode="skipped", why=why)
    else:
        if _truthy(data.get("disable-model-invocation", False)):
            entry["mode"] = "typed"
        elif data.get("paths"):
            entry["mode"] = "paths"
        if "user-invocable" in data and not _truthy(data["user-invocable"]):
            entry["menu"] = False
    if kind == "skill":
        if name is None:
            rule("name-missing")
        else:
            ln = keyline.get("name")
            if len(name) > T["name"]["max"]:
                rule("name-long", ln, chars=len(name))
            if not NAME_RX.match(name):
                rule("name-chars", ln)
            if folder and name != folder:
                rule("name-folder", ln, folder=folder)
            if any(w in name.lower() for w in T["name"]["reserved"]):
                rule("name-reserved", ln)
            if XML.search(name):
                rule("name-xml", ln)
        if desc is None:
            rule("description-missing")
        elif not desc.strip():
            rule("description-empty", keyline.get("description"))
        else:
            if len(desc) > T["description_max"]:
                rule("description-long", keyline.get("description"), chars=len(desc))
            if XML.search(desc):
                rule("description-xml", keyline.get("description"))
    if kind != "agent" and len(listing) > T["listing_chars"]:
        rule("listing-cut", keyline.get("description"), chars=len(listing), lost=len(listing) - T["listing_chars"])
    if desc and desc.strip() and entry["mode"] != "skipped":
        if not wtu and not any(p.search(desc) for p in WHEN):
            out.append(_f("trig.guidance", rel, keyline.get("description"), kind_of=kind, kind="no-when"))
        if any(p.search(desc) for p in FIRST):
            out.append(_f("trig.guidance", rel, keyline.get("description"), kind_of=kind, kind="first-person"))
        elif any(p.search(desc) for p in SECOND):
            out.append(_f("trig.guidance", rel, keyline.get("description"), kind_of=kind, kind="second-person"))
    for n, key in front.keys if read else []:
        if key not in KEYS[kind]:
            out.append(_f("trig.key", rel, n, kind_of=kind, key=key, near=near(key, KEYS[kind])))
    vkind = "agent" if kind == "agent" else "skill"
    for field, allowed in T["values"][vkind].items():
        v = data.get(field)
        if v is None:
            continue
        v = _text(v)
        if field == "model" and MODEL_ID.match(v):
            continue
        if v not in allowed:
            out.append(_f("trig.value", rel, keyline.get(field), kind_of=kind, field=field, value=v))
    for field in T["booleans"][vkind]:
        v = data.get(field)
        if v is not None and not isinstance(v, bool) and str(v).strip().lower() not in BOOLS:
            out.append(_f("trig.value", rel, keyline.get(field), kind_of=kind, field=field, value=_text(v)))
    for field in TOOL_FIELDS[kind]:
        for item in _items(data.get(field)) or []:
            tool = item.split("(", 1)[0].strip()
            if not tool or tool.startswith("mcp__") or tool in TOOLS:
                continue
            if tool in OLDER:
                out.append(_f("trig.tool", rel, keyline.get(field), kind_of=kind, field=field, tool=item,
                              kind="older", now=OLDER[tool]))
            else:
                out.append(_f("trig.tool", rel, keyline.get(field), kind_of=kind, field=field, tool=item,
                              kind="unknown", near=near(tool, TOOLS)))
    entry["chooses_by"] = listing if entry["mode"] in ("auto", "paths") else None
    return entry, out


def overlaps(entries: list[dict]) -> list[dict]:
    """trig.overlap: pairs in one listing (skills and commands; subagents) that share at least
    overlap_share of the shorter one's content words and at least overlap_min of them, after the
    words common to most of the listing are set aside."""
    out = []
    for listing in (("skill", "command"), ("agent",)):
        have = [(e["file"], words(e["chooses_by"])) for e in entries
                if e.get("chooses_by") and e["kind"] in listing]
        common = set()
        if len(have) >= T["common_min"]:
            df = {}
            for _, ws in have:
                for w in ws:
                    df[w] = df.get(w, 0) + 1
            common = {w for w, k in df.items() if k > T["common_share"] * len(have)}
        have = [(f, ws - common) for f, ws in have]
        for i, (a, wa) in enumerate(have):
            for b, wb in have[i + 1:]:
                shared = wa & wb
                small = min(len(wa), len(wb))
                if small and len(shared) >= T["overlap_min"] and len(shared) >= T["overlap_share"] * small:
                    out.append(_f("trig.overlap", a, None, other=b, shared=sorted(shared), count=len(shared),
                                  share=round(len(shared) / small, 2)))
    return sorted(out, key=lambda f: (f["file"], f["other"]))


def findings(texts: dict, file_rows: list) -> list[dict]:
    entries, found = [], []
    for row in sorted(file_rows, key=lambda r: r["file"]):
        rel = row["file"]
        kind = entry_kind(row)
        if kind is None or is_test_data(rel) or texts.get(rel) is None:
            continue
        entry, out = check_entry(rel, kind, texts[rel], bool(row.get("bom")))
        if entry is not None:
            entries.append(entry)
        found += out
    names: dict[str, str] = {}
    for e in entries:  # subagent names are unique across the tree (sub-agents docs)
        if e["kind"] == "agent" and e["mode"] != "skipped" and e["name"]:
            if e["name"] in names:
                found.append(_f("trig.rule", e["file"], None, kind_of="agent", rule="name-duplicate",
                                host=RULE_HOST["name-duplicate"], other=names[e["name"]]))
            else:
                names[e["name"]] = e["file"]
    chosen = [e for e in entries if e.get("chooses_by")]
    listing = _f("trig.listing", None, None,
                 skills=sum(1 for e in chosen if e["kind"] != "agent"),
                 commands=sum(1 for e in chosen if e["kind"] == "command"),
                 agents=sum(1 for e in chosen if e["kind"] == "agent"),
                 listing_chars=sum(min(e["listing_chars"], T["listing_chars"]) for e in chosen if e["kind"] != "agent"),
                 agent_chars=sum(e["description_chars"] for e in chosen if e["kind"] == "agent"),
                 typed=sum(1 for e in entries if e["mode"] == "typed"),
                 unread=sum(1 for e in entries if e["mode"] == "unread"),
                 not_loaded=sum(1 for e in entries if e["mode"] == "skipped"))  # never `skipped`: a skip marker
    over = overlaps(entries)
    for e in entries:
        e.pop("chooses_by", None)
    return entries + found + over + [listing]  # the listing row in every run: the check ran
