"""Version drift: what changed between two runs of the same repository. Spec: specs/drift.SPEC.md.

    python stages/08-report/drift.py <old run folder> <new run folder>

Threat class 8 (supply chain and drift): a repository can be fine when installed and change
later. Comparing two audits shows what a new version adds: files, hooks, tool grants, MCP
servers, descriptions, phrase hits, network hosts, and capability. Stage 6 is not compared
(model reads drift on their own). Detects nothing new: every line points at findings both runs
already made. Writes nothing unless asked (`write_report`).
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "04-phrases"))

import layout  # noqa: E402
from audience import audience  # noqa: E402

STAGES = ("01-inventory", "03-graph", "04-phrases", "05-capability")
REPORT = "changes.md"


def load(run_dir) -> dict:
    data = layout.data_dir(run_dir)
    out = {}
    for stage in STAGES:
        f = data / f"{stage}.json"
        if f.is_file():
            out[stage] = json.loads(f.read_text(encoding="utf-8")).get("findings", [])
    cap = data / "capability.json"
    if cap.is_file():  # stage 5 with every citation
        out["05-capability"] = json.loads(cap.read_text(encoding="utf-8")).get("findings", [])
    return out


def _f(r, stage, check):
    return [x for x in r.get(stage, []) if x.get("check") == check and "skipped" not in x]


def pin(r) -> dict:
    return (_f(r, "01-inventory", "inv.pin") or [{}])[0]


def _norm(q) -> str:
    return " ".join(str(q or "").split())


def compare(old: dict, new: dict) -> dict:
    """Every difference, as plain data. Keys are stable for rendering and for the brief."""
    c = {}
    of = {x["file"]: x for x in _f(old, "01-inventory", "inv.file")}
    nf = {x["file"]: x for x in _f(new, "01-inventory", "inv.file")}
    c["files_added"] = sorted(set(nf) - set(of))
    c["files_removed"] = sorted(set(of) - set(nf))
    changed, maybe = [], []
    for f in sorted(set(of) & set(nf)):
        a, b = of[f].get("sha256"), nf[f].get("sha256")
        if a and b:
            if a != b:
                changed.append(f)
        elif of[f].get("bytes") != nf[f].get("bytes"):
            changed.append(f)
        else:
            maybe.append(f)  # an older run has no content hash and the size is the same
    c["files_changed"], c["files_unverified"] = changed, maybe

    def ent(r):
        return {(x["file"], x["entry_point"]) for x in _f(r, "01-inventory", "inv.file")
                if x.get("entry_point")}
    c["entry_added"] = sorted(ent(new) - ent(old))
    c["entry_removed"] = sorted(ent(old) - ent(new))

    def hooks(r):
        return {(x["file"], str(x.get("event")), str(x.get("matcher") or ""), str(x.get("command")))
                for x in _f(r, "01-inventory", "struct.hooks")}
    c["hooks_added"] = sorted(hooks(new) - hooks(old))
    c["hooks_removed"] = sorted(hooks(old) - hooks(new))

    def grants(r):
        return {x["file"]: ("inherits all tools" if x.get("tools") is None
                            else ", ".join(sorted(map(str, x["tools"]))) or "no tools")
                for x in _f(r, "01-inventory", "struct.agent-tools")}
    og, ng = grants(old), grants(new)
    c["grants_changed"] = sorted((f, og.get(f, "(no agent)"), ng.get(f, "(no agent)"))
                                 for f in set(og) | set(ng) if og.get(f) != ng.get(f))

    def mcp(r):
        return {(x["file"], str(x.get("name"))): (str(x.get("command") or ""), str(x.get("url") or ""))
                for x in _f(r, "01-inventory", "struct.mcp")}
    om, nm = mcp(old), mcp(new)
    c["mcp_added"] = sorted(k + nm[k] for k in set(nm) - set(om))
    c["mcp_removed"] = sorted(k + om[k] for k in set(om) - set(nm))
    c["mcp_changed"] = sorted(k + om[k] + nm[k] for k in set(om) & set(nm) if om[k] != nm[k])

    def descs(r):
        return {x["file"]: _norm(x.get("text")) for x in _f(r, "01-inventory", "struct.description")}
    od, nd = descs(old), descs(new)
    c["desc_changed"] = sorted((f, od.get(f), nd.get(f)) for f in set(od) | set(nd)
                               if od.get(f) != nd.get(f))

    def hits(r):  # keyed by text, not line: lines shift between versions
        out = {}
        for x in r.get("04-phrases", []):
            if str(x.get("check", "")).startswith("phrase.") and "skipped" not in x:
                out.setdefault((x["file"], x["check"], _norm(x.get("quote"))), x)
        return out
    oh, nh = hits(old), hits(new)
    c["hits_added"] = [nh[k] for k in sorted(set(nh) - set(oh))]
    c["hits_removed"] = [oh[k] for k in sorted(set(oh) - set(nh))]

    def hosts(r):
        return {x["host"] for x in _f(r, "04-phrases", "endpoint.host")}
    c["hosts_added"] = sorted(hosts(new) - hosts(old))
    c["hosts_removed"] = sorted(hosts(old) - hosts(new))

    def legs(r):
        return {x["leg"]: bool(x.get("present")) for x in _f(r, "05-capability", "cap.leg")}
    ol, nl = legs(old), legs(new)
    c["legs_changed"] = sorted((k, ol.get(k), nl.get(k)) for k in set(ol) | set(nl)
                               if ol.get(k) != nl.get(k))

    def cap_grants(r):
        return {x["grant"] for x in _f(r, "05-capability", "cap.grant")}
    c["capgrants_added"] = sorted(cap_grants(new) - cap_grants(old))
    c["capgrants_removed"] = sorted(cap_grants(old) - cap_grants(new))

    def pairs(r):
        return {(x.get("pair"), x["file"], _norm(x.get("quote"))) for x in _f(r, "05-capability", "cap.pair")}
    c["pairs_added"] = sorted(pairs(new) - pairs(old))
    return c


# what each count is called in the brief and the summary line, in reading order
COUNTS = (("files_added", "files added"), ("files_removed", "files removed"),
          ("files_changed", "files changed"), ("entry_added", "entry points added"),
          ("hooks_added", "hooks added"), ("hooks_removed", "hooks removed"),
          ("grants_changed", "agent tool grants changed"), ("mcp_added", "MCP servers added"),
          ("mcp_changed", "MCP servers changed"), ("desc_changed", "descriptions changed"),
          ("hits_added", "new phrase hits"), ("hits_removed", "phrase hits gone"),
          ("hosts_added", "new network hosts"), ("capgrants_added", "install grants added"),
          ("pairs_added", "new pairs"))


def model_read_hits(c) -> int:
    return sum(1 for h in c["hits_added"] if h.get("audience") in ("model", "subagent"))


def summary_lines(c) -> list[str]:
    """Counts and Walkdown's own words only: safe for the brief (no repository text)."""
    lines = []
    for leg, a, b in c["legs_changed"]:
        lines.append(f"trifecta leg {LEG_WORDS.get(leg, leg)}: {'yes' if a else 'no'} -> "
                     f"{'yes' if b else 'no'}")
    parts = [f"{len(c[k])} {w}" for k, w in COUNTS if c.get(k)]
    if c.get("hits_added"):
        parts.append(f"{model_read_hits(c)} of the new phrase hits in text a model reads")
    if parts:
        lines.append(", ".join(parts))
    return lines or ["no differences in what Walkdown records"]


LEG_WORDS = {"private-data": "Reads your data", "untrusted-content": "Takes outside input",
             "external-comms": "Sends data out"}


def _code(s, n=160) -> str:
    s = _norm(s).replace("`", "'")
    return f"`{s[:n] + ('...' if len(s) > n else '')}`"


def render(old_dir, new_dir, old, new, c) -> str:
    po, pn = pin(old), pin(new)
    L = [f"# Changes: {Path(old_dir).name} -> {Path(new_dir).name}", "",
         f"Old: {po.get('hash_kind', '?')} {str(po.get('hash', '?'))[:12]}, {po.get('files', '?')} files. "
         f"New: {pn.get('hash_kind', '?')} {str(pn.get('hash', '?'))[:12]}, {pn.get('files', '?')} files.",
         "",
         "What a newer version adds, from the findings both runs already made. Model reads (stage 6) "
         "are not compared. A change is a location to read; none is a verdict.", "",
         "Summary: " + "; ".join(summary_lines(c)) + ".", ""]

    def section(title, rows, fmt):
        nonlocal L
        if rows:
            L += [f"## {title} ({len(rows)})", ""] + [f"- {fmt(r)}" for r in rows] + [""]
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
    model_hits = [h for h in c["hits_added"] if h.get("audience") in ("model", "subagent")]
    other_hits = [h for h in c["hits_added"] if h not in model_hits]
    section("New phrase hits in text a model reads", model_hits,
            lambda h: f"{h['file']}:{h.get('line')}: {h['check']} {_code(h.get('quote'))}")
    by_aud = collections.Counter(h.get("audience") for h in other_hits)
    if other_hits:
        L += [f"New phrase hits elsewhere: " + ", ".join(f"{n} {a}" for a, n in by_aud.most_common())
              + " (scripts, human-facing files, test data).", ""]
    section("Files added", c["files_added"], lambda f: f"{f} ({audience(f)})")
    section("Files removed", c["files_removed"], str)
    section("Files changed", c["files_changed"], lambda f: f"{f} ({audience(f)})")
    if c["files_unverified"]:
        L += [f"{len(c['files_unverified'])} files have the same size in both runs but the older run "
              "recorded no content hash, so a change of the same length cannot be ruled out.", ""]
    if c["hits_removed"]:
        L += [f"Phrase hits gone: {len(c['hits_removed'])}.", ""]
    return "\n".join(L).rstrip() + "\n"


def previous_run(run_dir) -> Path | None:
    """The newest other run of the same repository (sibling folder with a LOG.md), by its
    finish order on disk; None when this is the first."""
    run_dir = Path(run_dir).resolve()
    sibs = [p for p in run_dir.parent.iterdir()
            if p.is_dir() and p != run_dir and (p / "LOG.md").is_file()]
    sibs.sort(key=lambda p: (p / "LOG.md").stat().st_mtime)
    return sibs[-1] if sibs else None


def write_report(old_dir, new_dir) -> tuple[Path, dict]:
    old, new = load(old_dir), load(new_dir)
    c = compare(old, new)
    out = layout.report_dir(new_dir) / REPORT
    out.write_text(render(old_dir, new_dir, old, new, c), encoding="utf-8")
    return out, c


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
