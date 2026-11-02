"""Version drift: what changed between two runs of the same repository. Spec: specs/report.SPEC.md, drift.

    python stages/06-report/drift.py <old run folder> <new run folder>

Threat class 8 (supply chain and drift): a repository can be fine when installed and change
later. Comparing two audits shows what a new version adds: files, hooks, tool grants, MCP
servers, descriptions, phrase hits, network hosts, and capability. The AI stages are not compared
(model reads drift on their own). Detects nothing new: every line points at findings both runs
already made. Writes nothing unless asked (`write_report`, `since`).

Each new or gone phrase hit says where it came from (review C22 b, 2026-10-19): the repository
(its file was added, removed, or edited) or Walkdown (the same file, and a search term or the
matching code changed; `02.4-phrases` records both in its `terms` block).
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_shared"))

import layout  # noqa: E402
import pipeline  # noqa: E402
import record  # noqa: E402
import secretmask  # noqa: E402
import stagelist  # noqa: E402
import termdiff  # noqa: E402
from audience import audience  # noqa: E402
from stagenote import flat  # noqa: E402

STAGES = stagelist.CODED  # the coded steps; from stages.json
INVENTORY, BUILDER = STAGES[0], "02.6-builder"
PHRASES = "02.4-phrases"  # the step whose matching code `terms.code` hashes
COST_CHECKS = ("cap.ship", "cap.context")  # `02.5-capability`'s until restructure step 4, then the builder step's
REPORT = "changes.md"
# A run made before the stages were renamed (restructure step 1, 2026-10-28) keeps its stage
# outputs under the old names, which `load` does not read: this file marks such a run.
PRE_RENAME_FILE = "01-inventory.json"


def predates_rename(run_dir) -> bool:
    """A run made before the stages were renamed: its inventory is saved under the old name and
    not the new one. Its other stage files carry old names too. (Such a run is recognized, never
    read: with `data/` since 2026-10-02 the old name is in `data/`; before, at the top of the folder.)"""
    run_dir = Path(run_dir)
    old = any((d / PRE_RENAME_FILE).is_file() for d in (layout.data_dir(run_dir), run_dir))
    return old and not (layout.data_dir(run_dir) / f"{INVENTORY}.json").is_file()


def not_comparable(old_dir, new_dir) -> str | None:
    """Why two runs cannot be compared, in Walkdown's words (no repository text), or None. A run
    made before the rename is not compared, as costs are not compared with a run made before
    they were counted: comparing it would read stage files that no longer match and report
    every file as added or removed. The same goes for any run made before this version
    (`record.made_before`: no record, or a record of an older format, whose data inside the run has
    another shape; restructure step 7b): the one rule is that a run is compared only when its record has
    the current format. A run from before the rename keeps its own words. A run that stopped as asked before
    its last coded step (`--until`; `record.stopped_early`) is not compared either, since the steps the
    comparison reads did not all run; a run stopped after the last coded step is compared as usual (O3)."""
    for which, d in (("earlier", old_dir), ("newer", new_dir)):
        if predates_rename(d):
            return (f"not comparable: the {which} run was made before the stages were renamed, "
                    "so its stage files do not match")
        if record.made_before(d):
            return (f"not comparable: the {which} run was made by an earlier version of Walkdown, "
                    "and its data is in another shape")
        if record.stopped_early(d):
            after = stagelist.PLAIN[record.stop_of(record.read(d))["after"]]
            return f'not comparable: the {which} run stopped after "{after}", as asked'
    return None


def walkdown_version() -> str:
    """The VERSION file's text: a reader sees a version number on the pages, never "this version"."""
    try:
        return (HERE.parents[1] / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def render_not_comparable(old_dir, new_dir, why) -> str:
    v = walkdown_version()
    if "stopped after" in why:  # a run that stopped as asked (O3): going on with it, or a full run, can be compared
        return (f"# Changes: {Path(old_dir).name} -> {Path(new_dir).name}\n\n"
                f"{why[0].upper() + why[1:]}. Nothing was compared. A run that goes on to its last coded "
                "step (walkdown.py continue) can be compared.\n")
    return (f"# Changes: {Path(old_dir).name} -> {Path(new_dir).name}\n\n"
            f"{why[0].upper() + why[1:]}. Nothing was compared. Audit the repository again with "
            f"{'Walkdown ' + v if v else 'the Walkdown you have now'} to start a series that can be "
            "compared.\n")


def load(run_dir) -> dict:
    data = layout.data_dir(run_dir)
    out, docs, side = {}, {}, []
    for stage in STAGES:
        f = data / f"{stage}.json"
        if f.is_file():
            try:
                doc = pipeline.read_report(f)
            except (OSError, ValueError):  # an output that is not a report (the check of the run named it) compares as none
                continue
            docs[stage] = doc
            out[stage] = doc["findings"]
            if stage == "02.4-phrases":
                out["terms"] = doc.get("terms")  # absent before 2026-10-19
    try:  # `02.5-capability` with every citation; a side file that is not a report counts as none, as for the pages
        side.append(pipeline.read_report(data / "capability.json"))
        out["02.5-capability"] = side[0]["findings"]
    except (OSError, ValueError):
        pass
    else:
        if BUILDER not in out:  # a run made before step 4 kept what ships and what it costs here
            out[BUILDER] = [x for x in out["02.5-capability"] if x.get("check") in COST_CHECKS]
    secretmask.mask_reports(docs, *side)  # a run saved before the runner masked these, or stopped before it did
    return out


def _f(r, stage, check):
    return [x for x in r.get(stage, []) if x.get("check") == check and "skipped" not in x]


def pin(r) -> dict:
    return (_f(r, "02.1-inventory", "inv.pin") or [{}])[0]


def _norm(q) -> str:
    return " ".join(str(q or "").split())


def same_text(o: dict, n: dict) -> bool:
    """Two records of one file whose bytes differ only in line endings (2026-10-20). Either run
    may predate the line-ending hashes (`02.1-inventory` `sha256_lf`, `sha256_crlf`); the other's cover it."""
    if o.get("sha256_lf") and n.get("sha256_lf"):
        return o["sha256_lf"] == n["sha256_lf"]
    if n.get("sha256_lf"):
        return o.get("sha256") in (n["sha256_lf"], n.get("sha256_crlf"))
    if o.get("sha256_lf"):
        return n.get("sha256") in (o["sha256_lf"], o.get("sha256_crlf"))
    return False


def _hide(rows: list, r_old: dict, r_new: dict, check: str) -> list:
    """Rows of a comparison, without the words in a file where this check's row is masked in either run. A scan can flag in one run
    what it missed in the other, so the unmasked side can hold the key. Which file it was stays."""
    files = {x.get("file") for r in (r_old, r_new) for x in _f(r, INVENTORY, check) if x.get("masked")}
    return [(row[0],) + (secretmask.SECRET_MASK,) * (len(row) - 1) if row[0] in files else row for row in rows]


def compare(old: dict, new: dict) -> dict:
    """Every difference, as plain data. Keys are stable for rendering and for the brief."""
    c = {}
    of = {x["file"]: x for x in _f(old, "02.1-inventory", "inv.file")}
    nf = {x["file"]: x for x in _f(new, "02.1-inventory", "inv.file")}
    c["files_added"] = sorted(set(nf) - set(of))
    c["files_removed"] = sorted(set(of) - set(nf))
    changed, maybe, eol = [], [], []
    for f in sorted(set(of) & set(nf)):
        a, b = of[f].get("sha256"), nf[f].get("sha256")
        if a and b:
            if a != b:
                (eol if same_text(of[f], nf[f]) else changed).append(f)
        elif of[f].get("bytes") != nf[f].get("bytes"):
            changed.append(f)
        else:
            maybe.append(f)  # an older run has no content hash and the size is the same
    c["files_changed"], c["files_unverified"] = changed, maybe
    c["files_eol"] = eol  # the same content with other line endings: not an edit (2026-10-20)

    def ent(r):
        return {(x["file"], x["entry_point"]) for x in _f(r, "02.1-inventory", "inv.file")
                if x.get("entry_point")}
    c["entry_added"] = sorted(ent(new) - ent(old))
    c["entry_removed"] = sorted(ent(old) - ent(new))

    def hooks(r):
        return {(x["file"], str(x.get("event")), str(x.get("matcher") or ""), str(x.get("command")))
                for x in _f(r, "02.1-inventory", "struct.hooks")}
    c["hooks_added"] = _hide(sorted(hooks(new) - hooks(old)), old, new, "struct.hooks")
    c["hooks_removed"] = _hide(sorted(hooks(old) - hooks(new)), old, new, "struct.hooks")

    def grants(r):
        return {x["file"]: ("inherits all tools" if x.get("tools") is None
                            else ", ".join(sorted(map(str, x["tools"]))) or "no tools")
                for x in _f(r, "02.1-inventory", "struct.agent-tools")}
    og, ng = grants(old), grants(new)
    c["grants_changed"] = _hide(sorted((f, og.get(f, "(no agent)"), ng.get(f, "(no agent)"))
                                       for f in set(og) | set(ng) if og.get(f) != ng.get(f)), old, new, "struct.agent-tools")

    def mcp(r):
        return {(x["file"], str(x.get("name"))): (str(x.get("command") or ""), str(x.get("url") or ""))
                for x in _f(r, "02.1-inventory", "struct.mcp")}
    om, nm = mcp(old), mcp(new)
    c["mcp_added"] = _hide(sorted(k + nm[k] for k in set(nm) - set(om)), old, new, "struct.mcp")
    c["mcp_removed"] = _hide(sorted(k + om[k] for k in set(om) - set(nm)), old, new, "struct.mcp")
    c["mcp_changed"] = _hide(sorted(k + om[k] + nm[k] for k in set(om) & set(nm) if om[k] != nm[k]), old, new, "struct.mcp")

    def descs(r):
        return {x["file"]: _norm(x.get("text")) for x in _f(r, "02.1-inventory", "struct.description")}
    od, nd = descs(old), descs(new)
    c["desc_changed"] = _hide(sorted(((f, od.get(f), nd.get(f)) for f in set(od) | set(nd) if od.get(f) != nd.get(f)),
                                     key=lambda r: r[0]), old, new, "struct.description")

    def hits(r):  # keyed by text, not line: lines shift between versions
        out = {}
        for x in r.get("02.4-phrases", []):
            if str(x.get("check", "")).startswith("phrase.") and "skipped" not in x:
                out.setdefault((x["file"], x["check"], _norm(x.get("quote"))), x)
        return out
    oh, nh = hits(old), hits(new)
    c["hits_added"] = [nh[k] for k in sorted(set(nh) - set(oh))]
    c["hits_removed"] = [oh[k] for k in sorted(set(oh) - set(nh))]

    t = termdiff.diff(old.get("terms"), new.get("terms"))
    c["terms"] = t
    edited = set(c["files_added"]) | set(c["files_removed"]) | set(c["files_changed"])

    def cause(h, rows):
        f = h.get("file")
        if f in edited:
            return "repo"
        if f in c["files_unverified"]:
            return "unverified"
        if not t["known"]:
            return "walkdown"
        if set(h.get("patterns") or []) & rows:
            return "terms"
        return "code" if t["code_changed"] else "other"
    c["hits_added_cause"] = [cause(h, set(t["rows_added"]) | set(t["rows_changed"]))
                             for h in c["hits_added"]]
    c["hits_removed_cause"] = [cause(h, set(t["rows_removed"]) | set(t["rows_changed"]))
                               for h in c["hits_removed"]]

    def hosts(r):
        return {x["host"] for x in _f(r, "02.4-phrases", "endpoint.host")}
    c["hosts_added"] = sorted(hosts(new) - hosts(old))
    c["hosts_removed"] = sorted(hosts(old) - hosts(new))

    def legs(r):
        return {x["leg"]: bool(x.get("present")) for x in _f(r, "02.5-capability", "cap.leg")}
    ol, nl = legs(old), legs(new)
    c["legs_changed"] = sorted((k, ol.get(k), nl.get(k)) for k in set(ol) | set(nl)
                               if ol.get(k) != nl.get(k))

    def cap_grants(r):
        return {x["grant"] for x in _f(r, "02.5-capability", "cap.grant")}
    c["capgrants_added"] = sorted(cap_grants(new) - cap_grants(old))
    c["capgrants_removed"] = sorted(cap_grants(old) - cap_grants(new))

    def pairs(r):
        return {(x.get("pair"), x["file"], _norm(x.get("quote"))) for x in _f(r, "02.5-capability", "cap.pair")}
    c["pairs_added"] = sorted(pairs(new) - pairs(old))
    c["cost"] = {"old": cost_of(old), "new": cost_of(new)}  # slice 6, 2026-10-27
    return c


NOT_USED = ("people", "build", "unused")  # render.SHIP_BANDS "Not used at run time"
COST_PARTS = (("session", "every session"), ("project", "every session in this folder"),
              ("largest", "largest at its fullest"))


def cost_of(r) -> dict | None:
    """Slice 1's numbers in one run (tokens, estimated): every session, every session in the
    folder, the entry with the most at its fullest (ties to the first by path), and what is not
    used at run time; None for a run made before they were counted."""
    ctx = _f(r, BUILDER, "cap.context")
    if not ctx:
        return None
    tier = {x.get("tier"): x for x in ctx if x.get("tier") in ("session", "project")}
    top = sorted((x for x in ctx if x.get("tier") == "skill-max"), key=lambda x: (-x["tokens"], x["file"] or ""))
    unused = [x for x in _f(r, BUILDER, "cap.ship") if x.get("group") in NOT_USED]
    return {"session": tier["session"]["tokens"] if "session" in tier else None,
            "project": tier["project"]["tokens"] if "project" in tier else None,
            "largest": top[0]["tokens"] if top else None, "largest_file": top[0]["file"] if top else None,
            "not_used_files": len(unused), "not_used_tokens": sum(x.get("tokens") or 0 for x in unused)}


def cost_changed(c) -> bool:
    o, n = (c.get("cost") or {}).get("old"), (c.get("cost") or {}).get("new")
    keys = ("session", "project", "largest", "not_used_files", "not_used_tokens")
    return bool(o and n) and any(o[k] != n[k] for k in keys)


def cost_line(c) -> str | None:
    """The cost since the earlier run, counts only (no file name: the brief shows it)."""
    o, n = (c.get("cost") or {}).get("old"), (c.get("cost") or {}).get("new")
    if n is None:
        return None
    if o is None:
        return "costs not comparable: the earlier run was made before they were counted"
    parts = []
    for key, word in COST_PARTS:
        a, b = o[key], n[key]
        if a != b:
            parts.append(f"{word} {a:,} -> {b:,} tokens ({b - a:+,})" if a is not None and b is not None
                         else f"{word} {'none' if a is None else f'{a:,} tokens'} -> {'none' if b is None else f'{b:,} tokens'}")
    if (o["not_used_files"], o["not_used_tokens"]) != (n["not_used_files"], n["not_used_tokens"]):
        parts.append(f"not used at run time {_plural(o['not_used_files'], 'file')} -> {_plural(n['not_used_files'], 'file')} "
                     f"({o['not_used_tokens']:,} -> {n['not_used_tokens']:,} tokens)")
    return "cost: " + "; ".join(parts) if parts else None


# what each count is called in the brief and the summary line, in reading order
COUNTS = (("files_added", "file added", "files added"), ("files_removed", "file removed", "files removed"),
          ("files_changed", "file changed", "files changed"),
          ("files_eol", "file differing only in line endings", "files differing only in line endings"),
          ("entry_added", "entry point added", "entry points added"),
          ("hooks_added", "hook added", "hooks added"), ("hooks_removed", "hook removed", "hooks removed"),
          ("grants_changed", "agent tool grant changed", "agent tool grants changed"),
          ("mcp_added", "MCP server added", "MCP servers added"),
          ("mcp_changed", "MCP server changed", "MCP servers changed"),
          ("desc_changed", "description changed", "descriptions changed"),
          ("hits_added", "new phrase hit", "new phrase hits"), ("hits_removed", "phrase hit gone", "phrase hits gone"),
          ("hosts_added", "new network host", "new network hosts"),
          ("capgrants_added", "install grant added", "install grants added"),
          ("pairs_added", "new pair", "new pairs"))


# where a new or gone phrase hit came from, in reading order (review C22 b)
CAUSES = (("repo", "from changes in the repository"),
          ("terms", "from Walkdown's search terms"),
          ("code", "from Walkdown's matching code"),
          ("other", "from another part of Walkdown (same file, search terms, and matching code)"),
          ("walkdown", "from Walkdown (the older run recorded no search-term version)"),
          ("unverified", "on files the older run recorded no content hash for"))
CAUSE_SHORT = {"terms": "Walkdown's search terms", "code": "Walkdown's matching code",
               "other": "another part of Walkdown", "walkdown": "Walkdown",
               "unverified": "file not verified"}
OTHER_DIFFS = ("legs_changed", "entry_removed", "mcp_removed", "hosts_removed", "capgrants_removed")


def same_repo(old, new) -> bool:
    """Both runs read the same version of the repository (the same `02.1-inventory` pin)."""
    a, b = pin(old), pin(new)
    return bool(a.get("hash")) and a.get("hash") == b.get("hash")


def differs(c) -> bool:
    """Any difference in what the two runs recorded."""
    return (any(c.get(k) for k, *_ in COUNTS if k != "files_eol")  # line endings alone are no difference
            or any(c.get(k) for k in OTHER_DIFFS) or cost_changed(c))


def on_disk(c) -> int:
    """Files added, removed, or edited between the runs (line endings alone not counted)."""
    return len(c["files_added"]) + len(c["files_removed"]) + len(c["files_changed"])


def same_words(c) -> str:
    """What the brief, changes.md, and the summary say when both runs read the same version."""
    n = on_disk(c)
    if not n:
        return "same version of the repository; every difference comes from Walkdown"
    return (f"same commit of the repository, but {_plural(n, 'file')} on disk "
            f"{'differs' if n == 1 else 'differ'} from that run's; differences in other files come from Walkdown")


def _plural(n, word, many=None) -> str:
    return f"{n} {word if n == 1 else (many or word + 's')}"


def terms_line(t) -> str | None:
    """What changed in Walkdown's search terms and matching code, counts only."""
    if not t.get("known") or t.get("same"):
        return None
    counts = [(len(t[k]), w) for k, w in (("rows_added", "added"), ("rows_changed", "changed"),
                                          ("rows_removed", "retired")) if t[k]]
    out = ([_plural(sum(n for n, _ in counts), "search term")
            + " (" + ", ".join(f"{n} {w}" for n, w in counts) + ")"] if counts else [])
    if t["vocab_changed"]:
        out.append("word lists changed")
    if t["code_changed"]:
        out.append("matching code changed")
    return "Walkdown changed since the older run: " + ", ".join(out)


def cause_lines(c) -> list[str]:
    """Where new and gone phrase hits came from, when any came from Walkdown."""
    lines = []
    for key, word in (("hits_added_cause", "new phrase hits"), ("hits_removed_cause", "phrase hits gone")):
        n = collections.Counter(c.get(key) or [])
        if n and set(n) != {"repo"}:
            lines.append(f"{word}: " + ", ".join(f"{n[k]} {w}" for k, w in CAUSES if n.get(k)))
    return lines


def model_read_hits(c) -> int:
    return sum(1 for h in c["hits_added"] if h.get("audience") in ("model", "subagent"))


def summary_lines(c) -> list[str]:
    """Counts and Walkdown's own words only: safe for the brief (no repository text)."""
    if c.get("not_comparable"):
        return [c["not_comparable"]]
    lines = []
    for leg, a, b in c["legs_changed"]:
        lines.append(f"trifecta leg {LEG_WORDS.get(leg, leg)}: {'yes' if a else 'no'} -> "
                     f"{'yes' if b else 'no'}")
    parts = [_plural(len(c[k]), one, many) for k, one, many in COUNTS if c.get(k)]
    if len(c.get("hits_added") or []) == 1:  # "1 new phrase hit, 1 of the new phrase hits" read badly
        i = parts.index(_plural(1, "new phrase hit"))
        parts[i] += " (in text a model reads)" if model_read_hits(c) else " (not in text a model reads)"
    elif c.get("hits_added"):
        parts.append(f"{model_read_hits(c)} of the new phrase hits in text a model reads")
    if parts:
        lines.append(", ".join(parts))
    cl = cost_line(c)  # slice 6
    if cl:
        lines.append(cl)
    tl = terms_line(c.get("terms") or {})
    if tl:
        lines.append(tl)
    lines += cause_lines(c)
    return lines or ["no differences in what Walkdown records"]


LEG_WORDS = {"private-data": "Can read your data", "untrusted-content": "Can take outside input",
             "external-comms": "Can send data out"}  # render.LEG_NAMES (owner, 2026-10-20, C31 part B)


def _code(s, n=160) -> str:
    s = _norm(s).replace("`", "'")
    return f"`{s[:n] + ('...' if len(s) > n else '')}`"


def _files(p) -> str:
    """A pin's file count with its noun ("? files" when the run recorded none)."""
    k = p.get("files")
    return _plural(k, "file") if isinstance(k, int) else "? files"


def render(old_dir, new_dir, old, new, c) -> str:
    po, pn = pin(old), pin(new)
    L = [f"# Changes: {Path(old_dir).name} -> {Path(new_dir).name}", "",
         f"Old: {po.get('hash_kind', '?')} {str(po.get('hash', '?'))[:12]}, {_files(po)}. "
         f"New: {pn.get('hash_kind', '?')} {str(pn.get('hash', '?'))[:12]}, {_files(pn)}.",
         "",
         "What a newer version adds, from the findings both runs already made. Model reads "
         "are not compared. A change is a location to read; none is a verdict.", ""]
    if same_repo(old, new):
        w = same_words(c)
        L += [w[0].upper() + w[1:] + ".", ""]
    L += ["Summary: " + "; ".join(summary_lines(c)) + ".", ""]

    def section(title, rows, fmt):
        nonlocal L
        if rows:  # a name from the repository is one line: with a newline in it the rest would start a line of its own
            L += [f"## {title} ({len(rows)})", ""] + [f"- {flat(fmt(r))}" for r in rows] + [""]
    o, n = (c.get("cost") or {}).get("old"), (c.get("cost") or {}).get("new")
    if o and n and cost_changed(c):  # slice 6, 2026-10-27
        L += ["## What it costs (estimated tokens)", "", "| | Earlier | Now | Change |", "|---|---|---|---|"]
        for key, word in COST_PARTS + (("not_used_tokens", "not used at run time"),):
            a, b = o[key], n[key]
            fmt = lambda v: "none" if v is None else f"{v:,}"  # noqa: E731
            L.append(f"| {word[0].upper() + word[1:]} | {fmt(a)} | {fmt(b)} | "
                     f"{'' if a is None or b is None else f'{b - a:+,}'} |")
        if o.get("largest_file") != n.get("largest_file"):
            L.append(f"\nThe largest entry was {o.get('largest_file')}; now {n.get('largest_file')}.")
        L.append("")
    section("Trifecta legs that changed", c["legs_changed"],
            lambda r: f"{LEG_WORDS.get(r[0], r[0])}: {'yes' if r[1] else 'no'} -> {'yes' if r[2] else 'no'}")
    section("Install grants added", c["capgrants_added"], str)
    section("Install grants removed", c["capgrants_removed"], str)
    section("Hooks added", c["hooks_added"], lambda r: f"{r[0]}: {r[1]} runs {_code(r[3])}")
    section("Hooks removed", c["hooks_removed"], lambda r: f"{r[0]}: {r[1]} runs {_code(r[3])}")
    section("Agent tool grants changed", c["grants_changed"],
            lambda r: f"{r[0]}: {r[1]} -> {r[2]}")
    section("MCP servers added", c["mcp_added"], lambda r: f"{r[0]}: {r[1]} {_code(r[2] or r[3])}")
    section("MCP servers changed", c["mcp_changed"],
            lambda r: f"{r[0]}: {r[1]} {_code(r[2] or r[3])} -> {_code(r[4] or r[5])}")
    section("MCP servers removed", c["mcp_removed"], lambda r: f"{r[0]}: {r[1]}")
    section("Descriptions changed (always in the model's context)", c["desc_changed"],
            lambda r: f"{r[0]}: {_code(r[1]) if r[1] else '(none)'} -> {_code(r[2]) if r[2] else '(none)'}")
    section("New network hosts", c["hosts_added"], str)
    section("Entry points added", c["entry_added"], lambda r: f"{r[0]} ({r[1]})")
    section("New pairs", c["pairs_added"], lambda r: f"{r[1]}: {r[0]} {_code(r[2])}")
    t = c.get("terms") or {}
    if t.get("known") and not t.get("same"):
        rows = [f"{w}: {', '.join(t[k])}" for k, w in (("rows_added", "added"), ("rows_changed", "changed"),
                                                       ("rows_removed", "retired")) if t[k]]
        rows += [w for k, w in (("vocab_changed", "word lists (vocab.yaml) changed"),
                                ("code_changed", f'matching code (the step "{stagelist.PLAIN[PHRASES]}") changed')) if t[k]]
        section("Walkdown's search terms and matching code", rows, str)
    elif not t.get("known") and (c["hits_added"] or c["hits_removed"]):
        L += ["The older run recorded no search-term version, so a phrase hit on an unchanged file "
              "cannot be traced to a term or to the matching code.", ""]
    causes = dict(zip(map(id, c["hits_added"]), c.get("hits_added_cause") or []))

    def hit_line(h):
        k = causes.get(id(h), "repo")
        return (f"{h['file']}:{h.get('line')}: {h['check']} {_code(h.get('quote'))}"
                + ("" if k == "repo" else f" ({CAUSE_SHORT[k]})"))
    model_hits = [h for h in c["hits_added"] if h.get("audience") in ("model", "subagent")]
    other_hits = [h for h in c["hits_added"] if h not in model_hits]
    section("New phrase hits in text a model reads", model_hits, hit_line)
    by_aud = collections.Counter(h.get("audience") for h in other_hits)
    if other_hits:
        L += [f"New phrase hits elsewhere: " + ", ".join(f"{n} {a}" for a, n in by_aud.most_common())
              + " (scripts, human-facing files, test data).", ""]
    section("Files added", c["files_added"], lambda f: f"{f} ({audience(f)})")
    section("Files removed", c["files_removed"], str)
    section("Files changed", c["files_changed"], lambda f: f"{f} ({audience(f)})")
    if c.get("files_eol"):
        L += [f"## Files that differ only in line endings ({len(c['files_eol'])})", "",
              "The same content with other line endings (as when a checkout converts them); not "
              "counted as changed, and nothing in them is new.", ""] + [f"- {flat(f)}" for f in c["files_eol"]] + [""]
    if c["files_unverified"]:
        k = len(c["files_unverified"])
        L += [f"{_plural(k, 'file')} {'has' if k == 1 else 'have'} the same size in both runs but the older "
              "run recorded no content hash, so a change of the same length cannot be ruled out.", ""]
    if c["hits_removed"]:
        L += [f"Phrase hits gone: {len(c['hits_removed'])}.", ""]
    return "\n".join(L).rstrip() + "\n"


def write_report(old_dir, new_dir) -> tuple[Path, dict]:
    out = layout.report_dir(new_dir) / REPORT
    why = not_comparable(old_dir, new_dir)
    if why:
        out.write_text(render_not_comparable(old_dir, new_dir, why), encoding="utf-8")
        return out, {"not_comparable": why}
    old, new = load(old_dir), load(new_dir)
    c = compare(old, new)
    out.write_text(render(old_dir, new_dir, old, new, c), encoding="utf-8")
    return out, c


def since(old_dir, new_dir) -> dict:
    """What the brief and the summary page say about an earlier run: `same` when the repository
    version is the same; `differs` when anything recorded differs, then `lines` (counts only) and
    `report` (changes.md, written). With the same version and no difference, nothing is written;
    with the same version and a difference, every difference comes from Walkdown (2026-10-19).
    A run made before the stages were renamed is not compared (restructure step 1, 2026-10-28):
    `lines` is the one "not comparable" line, `changes.md` says so, and `not_comparable` is True."""
    why = not_comparable(old_dir, new_dir)
    if why:
        out = layout.report_dir(new_dir) / REPORT
        out.write_text(render_not_comparable(old_dir, new_dir, why), encoding="utf-8")
        return {"same": False, "differs": True, "lines": [why], "report": out, "on_disk": 0,
                "header": None, "cost_line": None, "not_comparable": True}
    old, new = load(old_dir), load(new_dir)
    same = same_repo(old, new)
    c = compare(old, new)
    if same and not differs(c):
        return {"same": True, "differs": False, "lines": [], "report": None, "on_disk": 0,
                "header": None}
    out = layout.report_dir(new_dir) / REPORT
    out.write_text(render(old_dir, new_dir, old, new, c), encoding="utf-8")
    return {"same": same, "differs": True, "lines": summary_lines(c), "report": out,
            "on_disk": on_disk(c), "header": same_words(c) if same else None, "cost_line": cost_line(c)}


def changes(run_dir) -> dict | None:
    """The one comparison of a run with the previous run of the same repository (restructure step 7,
    notes F2): `record.previous_run` finds it, `since` compares and writes `changes.md`, and the pages and
    the brief all read this result (the summary page's and the details page's "what changed", the
    brief's lines). None on a first run, or when the comparison fails (a note on stderr says why: drift
    is extra and never fails a report). Counts and Walkdown's own words only.

    `since` (the previous run's folder name), `same` (the same version of the repository), `differs`,
    `lines`, `on_disk`, `cost_line`, and, for the brief, `header` and `report` (the path of changes.md)."""
    try:
        run_dir = Path(run_dir)
        prev = record.previous_run(run_dir)
        if prev is None:
            return None
        s = since(prev, run_dir)
        return {"since": prev.name, "same": s["same"], "differs": s["differs"], "lines": s["lines"],
                "on_disk": s.get("on_disk", 0), "cost_line": s.get("cost_line"),
                "header": s.get("header"), "report": s.get("report"),
                "not_comparable": bool(s.get("not_comparable"))}
    except Exception as exc:
        print(f"note: version drift not computed: {exc}", file=sys.stderr)
        return None


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 2 or not all((Path(a) / "LOG.md").is_file() for a in args):
        print("usage: drift.py <old run folder> <new run folder>  (folders with LOG.md)",
              file=sys.stderr)
        return 2
    out, c = write_report(*args)
    print("\n".join(summary_lines(c)))
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
