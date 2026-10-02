"""Assemble the summary, full report, LOG, and limits. Spec: specs/render.SPEC.md.

Pure functions over stage reports. Nothing here detects or judges; every rule
that picks what to show is a fixed table below.
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baserates  # noqa: E402

HEADINGS = {
    "01-inventory": "What ships",
    "02-reader": "What the model actually reads",
    "03-graph": "What loads what",
    "04-phrases": "What the text asks for",
    "05-capability": "What this touches",
    "06-soft": "Needs a human read",
    "07-limits": "Not examined",
}
ORDER = list(HEADINGS)

SUBGROUPS = {  # CONTRACT stage 4 table
    "4a Reaching out": ["phrase.K.exfil", "phrase.creds", "phrase.remote-load"],
    "4b Taking the wheel": ["phrase.L.override", "phrase.A.consent", "phrase.B.defs",
                            "phrase.H.anti-review", "phrase.I.conditional"],
    "4c Changing the environment": ["phrase.E.perms", "phrase.C.second-order", "phrase.D.trust",
                                    "phrase.E.env", "phrase.J.prohibited"],
    "4d Talking to the human": ["phrase.G.human"],
}

# Summary points for stage 4: the zero-base-rate patterns PHRASES lists as the
# ones to run first on an unknown repo ("Stage 4 v1 measurement"), plus
# fetch-and-follow (THREATS 3, Case 001's point of attention).
POINT_PATTERNS = {
    "K.relay-host", "K.chat-webhook", "K.dns", "K.encode-send", "K.dest-ref", "K.dest-stored",
    # E.mcp left out 2026-10-01 (owner): common in the audited corpus (2 repos); full report only
    "E.redirect-var", "E.git-keys", "E.memory", "E.persist-redirect",
    "L.ignore", "L.system-frame", "L.context-end", "L.guardrail", "L.new-instructions",
    "A.prior-consent", "A.standing", "A.install-consent", "A.persona-grant",
    "J.enter-secret", "RL.pipe-shell", "G.pipe-shell", "RL.fetch-follow",
}
MAX_POINTS = 5
# Stage 6 "do" reads (soft D1, 2026-10-01). The cutoff is 0.8 (measured: 7/7 right on the
# real lines). Jev's p(do) for one line moves between runs: 95% of repeat reads within 0.09
# (soft/EVAL.md "near-the-line band"). So a read within DRIFT of the cutoff is "near the
# line", listed apart from the reads well clear of it.
DO_CUTOFF = 0.8
DRIFT = 0.1
DO_CLEAR_P = round(DO_CUTOFF + DRIFT, 2)   # listed as a real-instruction read
DO_NEAR_P = round(DO_CUTOFF - DRIFT, 2)    # listed as near the line
# Soft D5 (2026-10-01): a stage 6 label other than "do" at p >= 0.8 marks a stage 5 evidence
# line as "read as not an instruction" (measured: 7/7 and 9/9 right on the real lines; at
# 0.6 three real instructions were misread). A mark never changes stage 5: the leg stays.
NOT_DO_P = 0.8
# Measured base rates of stage 4 patterns over the audited corpus (soft D1; baserates.py).
BASE = baserates.load()
COL = 32  # summary label column: longest heading plus a space

# The trifecta legs in plain words, locked by the owner 2026-09-30 (THREATS "Organizing frame").
LEG_NAMES = {"private-data": "Reads your data", "untrusted-content": "Takes outside input",
             "external-comms": "Sends data out"}
LEG_DEFS = {
    "private-data": "Reads the user's data, wherever it lives: files, secrets, settings, connected accounts.",
    "untrusted-content": "Brings in text the user didn't write: the web, other people's issues or email, MCP tools, third-party code.",
    "external-comms": "Moves data off the machine or into shared places: web requests, webhooks, pushes, posts.",
}
TRIFECTA_ALL = ("All three legs of the lethal trifecta. That raises risk. "
                "It is not an issue on its own.")
NOT_WHAT = ('What this is not: static examination only. "Clean" means these stages found '
            "nothing, not that the artifact is safe. This report offers possible issues with "
            "evidence and reaches no verdict. What to do with it is yours to decide.")

# Stage notes that name something the run did not examine (for 07-limits).
LIMIT_NOTE = re.compile(r"limit|absent|not installed|not scanned|not built|incomplete|skipped|"
                        r"unknown|not examined|not run|carried forward", re.I)

STANDING_LIMITS = [
    "Static examination only. Nothing in the artifact was executed, fetched, or installed.",
    "Stage 6 answers are located observations from the backends section 6 names; they "
    "never change a stage 1 to 5 finding. Hit counts carry no benign share.",
    "Version drift (class 8) is snapshot-blind: one pinned copy was examined; what the "
    "artifact becomes after an update is not.",
    "English-language scope: the phrase layer is blind to non-English text (stage 2 lists "
    "non-Latin runs).",
    "Stage 4 matches patterns; a payload phrased outside every pattern reads as no hit. "
    "A zero here is not safety.",
]


# ---------------------------------------------------------------- helpers

def code(s) -> str:
    """Inline code span that survives backticks inside the text; newlines shown as \\n."""
    s = str(s).replace("\r", "").replace("\n", "\\n")
    run = max((len(m) for m in re.findall(r"`+", s)), default=0)
    fence = "`" * (run + 1)
    pad = " " if s.startswith("`") or s.endswith("`") or run else ""
    return f"{fence}{pad}{s}{pad}{fence}"


def loc(f) -> str:
    if f.get("file") is None:
        return "(repo)"
    return f"{f['file']}:{f['line']}" if f.get("line") is not None else f["file"]


def fnd(reports, stage, check=None):
    rep = reports.get(stage) or {}
    return [f for f in rep.get("findings", []) if check is None or f["check"] == check]


def n(x, word, plural=None) -> str:
    return f"{x} {word if x == 1 else (plural or word + 's')}"


def pairs(reports, kind):
    return [f for f in fnd(reports, "05-capability", "cap.pair") if f.get("pair") == kind]


def _points(items, fmt):
    lines = [f"  - {fmt(x)}" for x in items[:MAX_POINTS]]
    if len(items) > MAX_POINTS:
        lines.append(f"  - +{len(items) - MAX_POINTS} more in the full report")
    return lines


def stamp_suffix(stamps, stage) -> str:
    st = stamps.get(stage)
    if st is None or st.result == "PASS":
        return ""
    return f" Validation {st.result}: see 7."


# ---------------------------------------------------------------- status lines

def status(reports, stamps, stage) -> str:
    if stage not in reports or reports[stage] is None:
        return "Not run. See 7."
    return STATUS[stage](reports) + stamp_suffix(stamps, stage)


def _s1(r):
    pin = fnd(r, "01-inventory", "inv.pin")[0]
    hooks = fnd(r, "01-inventory", "struct.hooks")
    configs = len({h["file"] for h in hooks})
    agents = fnd(r, "01-inventory", "struct.agent-tools")
    mans = sum(len(m.get("files", [])) for m in fnd(r, "01-inventory", "struct.manifests"))
    langs = pin.get("script_languages") or {}
    return (f"{n(pin['files'], 'file')}, {n(len(pin.get('extensions') or {}), 'format')}, "
            f"{n(len(langs), 'script language')}. {n(len(hooks), 'hook')} "
            f"({n(configs, 'host config')}). {n(len(agents), 'agent or command definition')}. "
            f"{n(mans, 'platform manifest')}.")


def _s2(r):
    total = fnd(r, "01-inventory", "inv.pin")[0]["files"]
    unread = len(fnd(r, "02-reader", "read.unread"))
    read = total - unread
    pct = f"{100 * read / total:.1f}%" if total else "n/a"
    div = fnd(r, "02-reader", "read.divergence")
    div = [d for d in div if "skipped" not in d]
    carriers = collections.Counter(d.get("carrier", "?") for d in div)
    cs = ", ".join(f"{v} {k}" for k, v in carriers.most_common())
    fold = len(fnd(r, "02-reader", "read.fold"))
    script = len(fnd(r, "02-reader", "read.script"))
    return (f"{read}/{total} files ({pct}). {n(len(div), 'divergence')}"
            f"{' (' + cs + ')' if cs else ''}. {n(fold, 'line')} changed by folding. "
            f"{n(script, 'non-Latin run')}.")


def _s3(r):
    entries = len(fnd(r, "03-graph", "graph.entry"))
    orph = len(fnd(r, "03-graph", "graph.orphan"))
    dang = fnd(r, "03-graph", "graph.dangling")
    ctx = collections.Counter(d.get("context", "?") for d in dang)
    cs = ", ".join(f"{v} {k}" for k, v in ctx.most_common())
    dyn = len(fnd(r, "03-graph", "graph.dynamic"))
    depth = fnd(r, "03-graph", "graph.depth")
    loaded = sum(1 for d in depth if d.get("via") == "dynamic")
    mentioned = sum(1 for d in depth if d.get("via") == "mention")
    tail = " Graph incomplete by construction." if dyn else ""
    return (f"{n(entries, 'entry point')}. {n(orph, 'orphan')}. "
            f"{n(len(dang), 'dangling reference')}{' (' + cs + ')' if cs else ''}. "
            f"{n(dyn, 'dynamic load')}: {n(loaded, 'file')} loaded only through one (named by "
            f"nothing), {n(mentioned, 'file')} reached only through a folder or glob mention."
            f"{tail}")


def phrase_hits(r):
    return [h for h in fnd(r, "04-phrases") if h["check"].startswith("phrase.")]


def _s4(r):
    hits = phrase_hits(r)
    by = collections.Counter(h["check"] for h in hits)
    parts = [f"{g.split()[0]} {sum(by[c] for c in cs)}" for g, cs in SUBGROUPS.items()]
    line = f"{' · '.join(parts)} hits ({len(hits)} lines); benign share not measured."
    return line + "\n" + " " * COL + part2_line(r)


def part2_line(r) -> str:
    hosts = fnd(r, "04-phrases", "endpoint.host")
    undoc = [h for h in hosts if not h.get("documented") and not h.get("local")]
    rub = fnd(r, "04-phrases", "rubric.action")
    unconf = [x for x in rub if not x.get("confirmation")]
    conds = collections.Counter(c.get("kind") for c in fnd(r, "04-phrases", "cond.branch"))
    cs = ", ".join(f"{v} {k}" for k, v in conds.most_common()) or "none"
    defs = fnd(r, "04-phrases", "term.def")
    return (f"Hosts: {len(hosts)}, {len(undoc)} not named in the docs. Confirm-first or "
            f"prohibited actions in instruction text: {len(rub)}, {len(unconf)} with no "
            f"confirmation step. Conditionals: {cs}. Definitions: {len(defs)}, "
            f"{n(len(fnd(r, '04-phrases', 'term.conflict')), 'conflict')}, "
            f"{n(len(fnd(r, '04-phrases', 'term.safety')), 'safety-word definition')}.")


def not_instruction_reads(r) -> dict:
    """{(file, line): soft.label} for confident stage 6 reads that a line is not an
    instruction: label other than do, p(label) >= NOT_DO_P."""
    out = {}
    for x in fnd(r, "06-soft", "soft.label"):
        if "skipped" in x or x.get("label") in (None, "do"):
            continue
        if (x.get("probabilities") or {}).get(x["label"], 0) >= NOT_DO_P:
            out[(x.get("file"), x.get("line"))] = x
    return out


def evidence_mark(e, reads) -> dict | None:
    """The stage 6 read marking one evidence entry, for stage 4 phrase evidence only."""
    if e.get("stage") != "04":
        return None
    return reads.get((e.get("file"), e.get("line")))


def all_marked_legs(r) -> list[str]:
    """Present legs whose whole evidence list (not truncated) is marked as not an
    instruction. The leg is still present; the report says so beside it."""
    reads = not_instruction_reads(r)
    out = []
    for f in fnd(r, "05-capability", "cap.leg"):
        ev = f.get("evidence") or []
        whole = f.get("evidence_total", len(ev)) == len(ev)
        if f.get("present") and ev and whole and all(evidence_mark(e, reads) for e in ev):
            out.append(f["leg"])
    return out


def _s5(r):
    legs = {f["leg"]: f["present"] for f in fnd(r, "05-capability", "cap.leg")}
    line = " · ".join(f"{LEG_NAMES[k]}: {'yes' if legs.get(k) else 'no'}" for k in LEG_NAMES)
    if legs and all(legs.values()):
        line += "\n" + " " * COL + TRIFECTA_ALL
    for k in all_marked_legs(r):
        line += ("\n" + " " * COL + f"{LEG_NAMES[k]}: every line cited for it was read in "
                 "stage 6 as not an instruction; the leg stays, see 5 in the full report.")
    grants = [f["grant"] for f in fnd(r, "05-capability", "cap.grant")]
    line += "\n" + " " * COL + ("Install grants: " + ", ".join(grants) + "." if grants
                               else "Install grants: none.")
    return line


STATUS = {"01-inventory": _s1, "02-reader": _s2, "03-graph": _s3, "04-phrases": _s4,
          "05-capability": _s5, "06-soft": lambda r: _s6(r)}


# ---------------------------------------------------------------- points of attention

def points(reports, stage) -> list[str]:
    r = reports
    if stage == "01-inventory":
        items = [f"{h['file']}: {h.get('event')} hook runs {code(h.get('command'))}"
                 for h in fnd(r, stage, "struct.hooks")]
        items += [f"{c['file']}: over the reader window ({c.get('detail')})"
                  for c in fnd(r, stage, "struct.census") if c.get("flag") == "reader-window"]
        return _points(items, str)
    if stage == "02-reader":
        model, counted = _split_audience(r, pairs(r, "hidden+phrase"))
        lines = _points(model, lambda p: f"{loc(p)}: hidden when rendered and matches "
                                         f"{p['phrase_check']}: {code(p['quote'].strip())}")
        return lines + _counted_line(counted, "More hidden-text hits")
    if stage == "03-graph":
        both = pairs(r, "orphan+phrase") + pairs(r, "dynamic+phrase")
        model, counted = _split_audience(r, both)
        why = {"orphan+phrase": "referenced by nothing",
               "dynamic+phrase": "loaded only through a dynamic load, named by nothing"}
        lines = _points(model, lambda p: f"{loc(p)}: {why[p['pair']]}, and matches "
                                         f"{p['phrase_check']}: {code(p['quote'].strip())}")
        return lines + _counted_line(counted, "More such pairs")
    if stage == "04-phrases":
        hits = [h for h in phrase_hits(r) if POINT_PATTERNS & set(h.get("patterns", []))]
        model = [h for h in hits if h.get("audience") != "human"]
        human = len(hits) - len(model)
        lines = _points(_part2_points(r) + model,
                        lambda h: h if isinstance(h, str) else
                        f"{loc(h)}: {code(h['quote'].strip())} "
                        f"({rates_note(r, sorted(POINT_PATTERNS & set(h['patterns'])))})")
        if human:
            lines.append(f"  - {n(human, 'more hit')} on these patterns in human-facing files, "
                         "in the full report")
        return lines
    if stage == "05-capability":
        items = [("hook", p) for p in pairs(r, "hook+phrase")]
        items += [("inj", i) for i in fnd(r, stage, "cap.injection") if i.get("mechanism") == "hook"]
        return _points(items, _point5)
    if stage == "06-soft":
        return _points6(r)
    return []


def _split_audience(r, items):
    """Pairs on lines the model reads (model or subagent audience) are listed; pairs in
    scripts (tool) and human-facing files are counted. Stage 4 tags audience by path."""
    aud = {(h["file"], h["line"]): h.get("audience") for h in fnd(r, "04-phrases")}
    listed = [p for p in items if aud.get((p["file"], p["line"])) not in ("human", "tool")]
    counted = collections.Counter(aud.get((p["file"], p["line"])) for p in items
                                  if p not in listed)
    return listed, counted


def _counted_line(counted, what) -> list[str]:
    parts = []
    if counted.get("tool"):
        parts.append(f"{counted['tool']} in scripts")
    if counted.get("human"):
        parts.append(f"{counted['human']} in human-facing files (changelog, license, docs, "
                     "templates)")
    return [f"  - {what}: " + " and ".join(parts) + ", in the full report"] if parts else []


def _part2_points(r) -> list[str]:
    """Rare, high-signal part 2 rows: a word defined two ways, a safety word defined,
    a prohibited-tier action with no confirmation step, a step whose confirmation is
    a redefinition (THREATS 14, 22)."""
    out = [f"{d['file']}:{d['line']}: \"{c['term']}\" is defined differently in "
           f"{n(len(c['definitions']), 'place')}" for c in fnd(r, "04-phrases", "term.conflict")
           for d in c["definitions"][:1]]
    out += [f"{loc(t)}: defines the safety word \"{t['term']}\": {code(t['quote'].strip())}"
            for t in fnd(r, "04-phrases", "term.safety")]
    for x in fnd(r, "04-phrases", "rubric.action"):
        if x.get("confirm_redefined"):
            out.append(f"{loc(x)}: {x['tier']} action whose step redefines confirmation: "
                       f"{code(x['quote'].strip())}")
        elif x.get("tier") == "prohibited" and not x.get("confirmation"):
            out.append(f"{loc(x)}: prohibited-tier action with no confirmation step: "
                       f"{code(x['quote'].strip())}")
    return out


def _soft(r):
    """Stage 6 pieces: questions, answered labels, comparison labels, reads, skips."""
    f = [x for x in fnd(r, "06-soft")]
    live = [x for x in f if "skipped" not in x]
    return {"questions": [x for x in f if x["check"] == "soft.question"],
            "labels": [x for x in live if x["check"] == "soft.label"],
            "compare": [x for x in live if x["check"] == "soft.compare"],
            "agree": [x for x in live if x["check"] == "soft.agree"],
            "reads": [x for x in live if x["check"] == "soft.read"],
            "sweep": [x for x in live if x["check"] == "soft.sweep"],
            "skips": [x for x in f if "skipped" in x],
            "backends": (r.get("06-soft") or {}).get("backends") or []}


# Soft D2 sweep: what each kind tells the reader to do, in plain words.
SWEEP_PLAIN = {
    "override": "set aside its other instructions",
    "send-out": "send data out",
    "secrets": "gather secrets or private files",
    "skip-user": "act without asking the user, or keep something from them",
    "remote-instructions": "fetch outside text and follow it",
    "persist": "make lasting changes outside the task",
}


def span(x) -> str:
    e = x.get("end_line")
    return f"{x['file']}:{x['line']}" + (f"-{e}" if e and e != x["line"] else "")


# Sweep band (2026-10-01): stage 6 flags at p_any > 0.5. Repeat sweeps of the same passage
# moved p_any by up to 0.10 (95% within 0.07 where p_any >= 0.3; soft/EVAL.md), and the three
# passages that crossed 0.5 between runs sat within 0.03 of it. So the report lists a passage
# at p_any >= 0.6 and calls 0.4 to 0.6 near the line, flagged or not.
SWEEP_CUTOFF = 0.5
SWEEP_DRIFT = 0.1
SWEEP_CLEAR_P = round(SWEEP_CUTOFF + SWEEP_DRIFT, 2)
SWEEP_NEAR_P = round(SWEEP_CUTOFF - SWEEP_DRIFT, 2)


def sweep_kind(x) -> str:
    """The kind to name: the chosen one, or for a passage whose top answer is `none`, the
    likeliest listed kind."""
    if x.get("kind") and x["kind"] != "none":
        return x["kind"]
    others = {k: v for k, v in (x.get("probabilities") or {}).items() if k != "none"}
    return max(others, key=others.get) if others else "none"


def sweep_split(s):
    """Sweep passages by the band, strongest first: (clear with no stage 4 hit inside, clear
    and already covered by stage 4, near the line)."""
    ranked = sorted(s["sweep"], key=lambda x: -x.get("p_any", 0))
    clear = [x for x in ranked if x.get("p_any", 0) >= SWEEP_CLEAR_P]
    near = [x for x in ranked if SWEEP_NEAR_P <= x.get("p_any", 0) < SWEEP_CLEAR_P]
    return ([x for x in clear if not x.get("covered")], [x for x in clear if x.get("covered")], near)


def _both(b) -> str:
    return ", two reads averaged" if b.get("reads") == "both" else ""


def _s6(r) -> str:
    s = _soft(r)
    qs = s["questions"]
    nl = sum(1 for q in qs if q.get("kind") == "label")
    line = f"{n(len(qs), 'question')} ({nl} labeling, {len(qs) - nl} relational)."
    if not s["backends"]:
        return line + " Packet only: no model read (06-packet.md in the run folder)."
    for b in s["backends"]:
        where = "remote" if b.get("remote") else "local"
        line += f" {b['role'].capitalize()}: {b['backend']} ({where}, {b.get('model')}{_both(b)})"
        if b["role"] == "label":
            c = collections.Counter(x["label"] for x in s["labels"])
            line += ": " + (", ".join(f"{v} {k}" for k, v in c.most_common()) or "no answers")
        elif b["role"] == "compare":
            agree = sum(1 for x in s["agree"] if x.get("agree"))
            line += f": agrees with the primary on {agree}/{len(s['agree'])}"
        elif b["role"] == "relational":
            skipped = [x for x in s["skips"] if x["check"] == "soft.read"]
            line += f": {len(s['reads'])} answered"
            if skipped:
                line += f", {len(skipped)} skipped ({skipped[0]['skipped']})"
        elif b["role"] == "sweep":
            new, old, near_sw = sweep_split(s)
            line += (f": {len(s['sweep'])} passages read, {len(new) + len(old)} flagged at "
                     f"p >= {SWEEP_CLEAR_P} ({len(new)} with no stage 4 hit), "
                     f"{len(near_sw)} near the line")
        line += "."
    return line + " Answers are observations, not verdicts."


def _points6(r) -> list[str]:
    s = _soft(r)
    # Sweep passages with no stage 4 hit come first: they are the only stage 6 points about
    # text no pattern located (soft D2). Strongest first.
    new, old, near_sw = sweep_split(s)
    items = [f"{span(x)}: no stage 4 pattern here; {x['backend']} reads this passage as telling "
             f"the reader to {SWEEP_PLAIN.get(sweep_kind(x), sweep_kind(x))} (p={x['p_any']:.2f})"
             for x in new]
    for x in s["reads"]:
        if not x.get("answer"):
            continue
        if x.get("file"):  # a read anchored to a line: show its substance
            flat = " ".join(x["answer"].replace("**", "").split())
            items.append(f"{loc(x)}: read by {x['backend']}: {code(flat[:240] + ('…' if len(flat) > 240 else ''))}")
        else:  # the repo-wide capability narrative: point to it, do not quote a lead-in
            items.append(f"(repo): capability narrative by {x['backend']} "
                         f"({len(x['answer'].split())} words), in the full report")
    clear, near = do_reads(s["labels"])
    items += [f"{loc(x)}: {x['backend']} reads this line as an instruction to do the matched "
              f"action (p={p_do(x):.2f})" for x in clear]
    lines = _points(items, str)
    if old:
        lines.append(f"  - {n(len(old), 'more passage')} flagged by the sweep where stage 4 already "
                     "has a hit, in the full report")
    if near_sw:
        lines.append(f"  - {n(len(near_sw), 'more passage')} near the sweep's line (p {SWEEP_NEAR_P} "
                     f"to {SWEEP_CLEAR_P}): repeat sweeps vary by about {SWEEP_DRIFT}, so these "
                     "could go either way; in the full report")
    if near:
        lines.append(f"  - {n(len(near), 'more \"do\" read')} near the line (p {DO_NEAR_P} to "
                     f"{DO_CLEAR_P}): repeat reads of one line vary by about {DRIFT}, so these "
                     "could go either way; in the full report")
    weak = sum(1 for x in s["labels"] if x.get("label") == "do") - len(clear) - len(near)
    if weak:
        lines.append(f"  - {n(weak, 'more \"do\" read')} below p={DO_NEAR_P}, in the full report")
    return lines


def p_do(x) -> float:
    return (x.get("probabilities") or {}).get("do", 0)


def do_reads(labels):
    """Stage 6 "do" reads split by the band: (clear: p >= DO_CLEAR_P, near the line:
    DO_NEAR_P <= p < DO_CLEAR_P). Only reads whose label is do."""
    dos = [x for x in labels if x.get("label") == "do"]
    return ([x for x in dos if p_do(x) >= DO_CLEAR_P],
            [x for x in dos if DO_NEAR_P <= p_do(x) < DO_CLEAR_P])


def run_hash(r):
    pin = [f for f in fnd(r, "01-inventory", "inv.pin")]
    return pin[0].get("hash") if pin else None


def rates_note(r, patterns) -> str:
    """Each pattern with its measured base rate over the other audited repos (soft D1):
    'L.ignore, rare: in 0 of 3 other audited repos'. A pattern without a table is just named."""
    out = []
    for p in patterns:
        ph = baserates.phrase(baserates.rate(BASE, p, run_hash(r)))
        out.append(f"{p}, {ph}" if ph else p)
    return "; ".join(out)


def _f6(r):
    s = _soft(r)
    by_q = collections.defaultdict(list)
    for x in s["labels"] + s["compare"] + s["reads"] + s["skips"]:
        by_q[x.get("qid") or (x.get("file"), x.get("line"))].append(x)
    L = ["Questions a pattern cannot settle, and the answers of the backends named here. "
         "Every answer is a located observation; none changes a finding in sections 1 to 5.", ""]
    L += [f"- {b['role']}: {b['backend']} ({'remote' if b.get('remote') else 'local'}, "
          f"{b.get('model')}{_both(b)})" for b in s["backends"]] or ["- no backend: packet only"]
    if s["sweep"]:
        new, old, near_sw = sweep_split(s)
        L += ["", "### Sweep: passages a model read as asking for one of the listed actions", "",
              f"{n(len(s['sweep']), 'passage')} read. A located observation from a model, made to "
              "reach text no pattern matched; it never replaces stage 4. Listed at "
              f"p >= {SWEEP_CLEAR_P}; p {SWEEP_NEAR_P} to {SWEEP_CLEAR_P} is near the line (repeat "
              f"sweeps vary by about {SWEEP_DRIFT}).", ""]
        L += [f"- {span(x)}: {sweep_kind(x)} (p={x['p_any']:.2f}"
              + (", near the line" if x in near_sw else "") + "); "
              + (f"stage 4 already hits it ({', '.join(x['covered'])})" if x.get("covered")
                 else "no stage 4 hit") for x in new + old + near_sw] or ["- none flagged"]
    L += ["", "### Questions", ""]
    for q in s["questions"]:
        L.append(f"- {loc(q)} [{q.get('kind')}] {q.get('question')}")
        for a in by_q.get(q.get("qid"), []) or by_q.get((q.get("file"), q.get("line")), []):
            if "skipped" in a:
                L.append(f"    - {a['check']}: skipped ({a['skipped']})")
            elif a["check"] == "soft.read":
                L.append(f"    - {a['backend']} ({a.get('model')}): {code(a.get('answer'))}")
            else:
                p = a.get("probabilities") or {}
                band = (", near the line" if a["check"] == "soft.label" and a.get("label") == "do"
                        and DO_NEAR_P <= p_do(a) < DO_CLEAR_P else "")
                L.append(f"    - {a['backend']} ({a.get('model')}): {a.get('label')} "
                         f"(p={p.get(a.get('label'), 0):.2f}{band})")
    return L + [""]


def _point5(item) -> str:
    kind, x = item
    if kind == "hook":
        return (f"{loc(x)}: an instruction in a script a context-injecting hook runs, so it can "
                f"reach the model before the first user input: {code(x['quote'].strip())}")
    return (f"{x['file']}: {x.get('event')} hook puts text in context before the first user "
            f"input ({_bytes(x)})")


def _bytes(i) -> str:
    if i.get("bytes") is None:
        return "bytes unknown"
    return f"{i['bytes']:,} bytes, {i.get('basis')}"


def load_bytes_line(reports) -> str:
    """Stage 5 gives one total per hook config (host); configs are never summed."""
    inj = fnd(reports, "05-capability", "cap.injection")
    desc = [i for i in inj if i.get("mechanism") == "description"]
    d = sum(i.get("bytes") or 0 for i in desc)
    per = fnd(reports, "05-capability", "cap.load-bytes")
    hosts = [f"{x['file']} {_bytes(x)}" for x in per if x.get("file")]
    line = f"Bytes at load: descriptions {d:,} ({len(desc)}, exact)"
    if hosts:
        line += "; with each host's SessionStart hook: " + "; ".join(hosts)
    return line + "."


# ---------------------------------------------------------------- recommendations

ALLOW_EDIT = re.compile(r"permissions\.allow|allowedTools|settings(\.local)?\.json", re.I)


def recommendations(reports) -> list[str]:
    """Fixed templates only; conditional; each names a narrower alternative; stage then document order.
    One recommendation per file and template: a block of matching lines is one change."""
    out, done = [], set()
    for h in sorted(fnd(reports, "01-inventory", "struct.hooks"), key=lambda x: x["file"]):
        if str(h.get("event", "")).lower() == "sessionstart":
            out.append(f"{h['file']}: If the SessionStart context does not need to be computed at "
                       "run time, ship it as a static file the hook reads, so the shell step can "
                       "be removed.")
    for f in fnd(reports, "04-phrases"):
        pats = set(f.get("patterns", []))
        if f["check"] == "phrase.remote-load" and "RL.fetch-follow" in pats:
            out.append(f"{loc(f)}: If the instructions this line fetches do not need to change "
                       "after release, inline them or pin a commit SHA instead of a branch, so "
                       "they are part of what a reviewer reads.")
        if ("E.perm-flags" in pats and f.get("audience") in ("model", "tool")
                and not f["file"].startswith("tests/")):
            if ALLOW_EDIT.search(f.get("quote", "")):
                key = (f["file"], "allow-edit")
                if key not in done:
                    done.add(key)
                    out.append(f"{loc(f)}: If these tools do not need to run without a prompt in "
                               "every project, leave the user's permission settings unchanged and "
                               "document the entries for the user to add, or ask before writing "
                               "them.")
            elif (f["file"], "skip") not in done:
                done.add((f["file"], "skip"))
                out.append(f"{loc(f)}: If this run does not need every permission, grant the "
                           "specific tools it uses (an allowlist) instead of skipping permission "
                           "checks.")
    for p in pairs(reports, "hook+phrase"):
        out.append(f"{loc(p)}: If this message is meant for the user, not the model, write it to "
                   "the terminal (stderr) or the README instead of the hook output that becomes "
                   "the model's context.")
    for p in fnd(reports, "05-capability", "cap.posture"):
        if "all" in (p.get("posture") or []):
            out.append(f"{loc(p)}: If this agent does not need every tool, list the ones it "
                       "uses in a `tools:` field; it inherits all of them now.")
    return out


# ---------------------------------------------------------------- limits (stage 7)

def limits(reports, notes, stamps, runs_ok) -> list[str]:
    out = []
    for stage in ORDER[:6]:
        st = stamps.get(stage)
        if stage not in runs_ok:
            out.append(f"Stage {stage} did not run to completion; its section is not a result.")
        elif st is not None and st.result != "PASS":
            out.append(f"Stage {stage} validation {st.text}: its zeros are not validated "
                       "for the skipped checks.")
    seen = set()
    for stage in ORDER[:6]:
        for f in fnd(reports, stage):
            if "skipped" in f:
                key = f"{f['check']} skipped for {f.get('file')}: {f['skipped']}"
                if key not in seen:
                    seen.add(key)
                    out.append(key)
        for line in notes.get(stage, []):
            if LIMIT_NOTE.search(line) and line not in seen:
                seen.add(line)
                out.append(f"({stage}) {line}")
    for u in fnd(reports, "02-reader", "read.unread"):
        key = f"Unread: {u['file']}: {u.get('reason')}"
        if key not in seen:
            seen.add(key)
            out.append(key)
    for u in fnd(reports, "03-graph", "graph.unscanned"):
        out.append(f"Not scanned for references: {u['file']}: {u.get('reason')}")
    return out + STANDING_LIMITS


# ---------------------------------------------------------------- documents

def summary(meta, reports, stamps, notes, runs_ok) -> str:
    L = [f"# {meta['repo']}", "",
         f"{meta['source']} | retrieved {meta['date']} | {meta['hash_kind']} {meta['hash'][:12]}",
         "Static examination only. Nothing executed.", ""]
    for i, stage in enumerate(ORDER, 1):
        head = f"{i} {HEADINGS[stage]}".ljust(COL - 1) + " "
        if stage == "07-limits":
            lim = limits(reports, notes, stamps, runs_ok)
            L.append(f"{head}{n(len(lim), 'item')}, including: " + _limit_gist(reports, stamps))
            continue
        L.append(f"{head}{status(reports, stamps, stage)}")
        if stage == "05-capability" and stage in reports:
            L.append(" " * COL + load_bytes_line(reports))
        pts = points(reports, stage) if stage in reports else []
        if not pts and stage in reports and stamps.get(stage) and stamps[stage].result == "PASS" \
                and stage != "05-capability":
            L[-1] += " Nothing on the attention list (validated)."
        L.extend(pts)
    L += ["", f"Recommendations: {len(recommendations(reports))}, in the full report. Unranked.",
          "", NOT_WHAT, ""]
    return "\n".join(L)


def _limit_gist(reports, stamps) -> str:
    bits = []
    unread = fnd(reports, "02-reader", "read.unread")
    if unread:
        bits.append(n(len(unread), "unread file"))
    bad = [s for s, st in stamps.items() if st.result != "PASS"]
    if bad:
        bits.append("validation not PASS for " + ", ".join(bad))
    if not (reports.get("06-soft") or {}).get("backends"):
        bits.append("stage 6 ran packet only (no model)")
    bits += ["stage 4 position/repetition and gitleaks not built",
             "version drift not examined"]
    return "; ".join(bits) + "."


def full(meta, reports, stamps, notes, runs_ok, capability_full=None) -> str:
    L = [f"# {meta['repo']}: full report", "",
         f"{meta['source']} | retrieved {meta['date']} | {meta['hash_kind']} {meta['hash']}",
         f"Run {meta['run']} | Walkdown {meta.get('tool', '?')}",
         "Static examination only. Nothing executed. Every finding below is a location to "
         "look at, not a verdict. Stage order; nothing is ranked.", ""]
    for i, stage in enumerate(ORDER, 1):
        L.append(f"## {i} {HEADINGS[stage]}")
        L.append("")
        if stage == "07-limits":
            L += [f"- {x}" for x in limits(reports, notes, stamps, runs_ok)] + [""]
            continue
        L.append(status(reports, stamps, stage).replace("\n" + " " * COL, " "))
        st = stamps.get(stage)
        L += ["", f"Validation: {st.text if st else 'not run'}", ""]
        if stage in reports:
            L += SECTIONS[stage](reports, capability_full)
    recs = recommendations(reports)
    L += ["## Recommendations", "",
          "Conditional on what the skill is for. Unranked, in stage order."
          + ("" if recs else " None: no finding matched a recommendation template."), ""]
    L += [f"- {x}" for x in recs] + ["", NOT_WHAT, ""]
    return "\n".join(L)


def _list(title, rows, fmt):
    if not rows:
        return [f"### {title} (0)", "", "None.", ""]
    return [f"### {title} ({len(rows)})", ""] + [f"- {fmt(x)}" for x in rows] + [""]


def _f1(r, _):
    pin = fnd(r, "01-inventory", "inv.pin")[0]
    ext = ", ".join(f"{k or '(none)'} {v}" for k, v in sorted((pin.get("extensions") or {}).items(),
                                                             key=lambda kv: (-kv[1], kv[0])))
    langs = "; ".join(f"{k}: {', '.join(v)}" for k, v in sorted((pin.get("script_languages") or {}).items()))
    L = [f"Pin: {pin.get('hash_kind')} {pin.get('hash')}, {pin.get('files')} files, "
         f"{pin.get('bytes'):,} bytes.", "", f"Formats: {ext}.", "", f"Script languages: {langs or 'none'}.", ""]
    ep = [f for f in fnd(r, "01-inventory", "inv.file") if f.get("entry_point")]
    L += _list("Entry points", ep, lambda f: f"{f['file']} ({f['entry_point']})")
    L += _list("Structural census", fnd(r, "01-inventory", "struct.census"),
               lambda f: f"{loc(f)}: {f.get('flag')}: {f.get('detail')}")
    L += _list("Descriptions (always-on text)", fnd(r, "01-inventory", "struct.description"),
               lambda f: f"{loc(f)}: {code(f.get('text'))}")
    L += _list("Agent and command tool grants", fnd(r, "01-inventory", "struct.agent-tools"),
               lambda f: f"{loc(f)}: tools {f.get('tools') if f.get('tools') is not None else '(none listed: inherits all)'}; "
                         f"job {code(f.get('description'))}")
    L += _list("Hooks", fnd(r, "01-inventory", "struct.hooks"),
               lambda f: f"{f['file']}: event {f.get('event')}, matcher {f.get('matcher')}, "
                         f"command {code(f.get('command'))}")
    L += _list("Platform manifests", fnd(r, "01-inventory", "struct.manifests"),
               lambda f: f"{f.get('name')}: {', '.join(f.get('files', []))}; "
                         f"declared permissions differ: {'yes' if f.get('divergent') else 'no'}")
    return L


def _f2(r, _):
    L = _list("Divergences (reading A versus reading B)",
              [d for d in fnd(r, "02-reader", "read.divergence") if "skipped" not in d],
              lambda d: f"{loc(d)}: {d.get('reading')}, carrier {d.get('carrier')}, "
                        f"method {d.get('method')}: {code(d.get('text'))}")
    L += _list("Lines changed by folding", fnd(r, "02-reader", "read.fold"),
               lambda d: f"{loc(d)}: removed or replaced {', '.join(d.get('removed', []))}")
    L += _list("Non-Latin script runs", fnd(r, "02-reader", "read.script"),
               lambda d: f"{loc(d)}: {d.get('script')} {code(d.get('text'))}")
    L += _list("Metadata carrying text", fnd(r, "02-reader", "read.metadata"),
               lambda d: f"{loc(d)}: {d.get('field')} = {code(d.get('text'))}")
    L += _list("Unread", fnd(r, "02-reader", "read.unread"),
               lambda d: f"{loc(d)}: {d.get('reason')}")
    return L


def _f3(r, _):
    depth = fnd(r, "03-graph", "graph.depth")
    hist = collections.Counter((d["via"], d["depth"]) for d in depth)
    hs = "; ".join(f"{via} depth {k}: {v}" for (via, k), v in sorted(hist.items()))
    L = [f"Depth histogram (static = reached by direct references; dynamic = only through a "
         f"load: a folder a config names, a code scan, an instruction-file glob; mention = only "
         f"through a folder or glob named elsewhere): {hs or 'none'}.", ""]
    L += _list("Entry points used", fnd(r, "03-graph", "graph.entry"),
               lambda f: f"{f['file']} ({f.get('kind')})")
    L += _list("Orphans (reachable from no entry point)", fnd(r, "03-graph", "graph.orphan"),
               lambda f: f["file"])
    L += _list("Files loaded only through a dynamic load (named by nothing)",
               [d for d in depth if d.get("via") == "dynamic"],
               lambda d: f"{d['file']} (depth {d['depth']}, from {d.get('from')})")
    L += _list("Files reached only through a folder or glob mention (not a load)",
               [d for d in depth if d.get("via") == "mention"],
               lambda d: f"{d['file']} (depth {d['depth']}, from {d.get('from')})")
    L += _list("Dynamic loads", fnd(r, "03-graph", "graph.dynamic"),
               lambda f: f"{loc(f)}: {f.get('source')} {code(f.get('pattern'))} "
                         f"({'load' if f.get('load') else 'mention'}) resolves to "
                         f"{n(len(f.get('resolves', [])), 'file')}")
    L += _list("Dangling references", fnd(r, "03-graph", "graph.dangling"),
               lambda f: f"{loc(f)}: {code(f.get('target'))} ({f.get('context')})")
    L += _list("Not scanned for references", fnd(r, "03-graph", "graph.unscanned"),
               lambda f: f"{f['file']}: {f.get('reason')}")
    L += _list("Reference depth, directly reached files",
               [d for d in depth if d.get("via") == "static"],
               lambda d: f"{d['file']}: depth {d['depth']}" + (f", from {d['from']}" if d.get("from") else ""))
    return L


def _f4(r, _):
    hits = phrase_hits(r)
    L = ["Every hit is a locator. Benign share not measured here; stage 6 labels, when run, read "
         "the lines a model sees (section 6). Audience is "
         "who the file addresses, by path.", ""]
    for group, checks in SUBGROUPS.items():
        L += [f"### {group}", ""]
        for c in checks:
            rows = [h for h in hits if h["check"] == c]
            pc = collections.Counter(p for h in rows for p in h.get("patterns", []))
            L.append(f"#### {c} ({n(len(rows), 'line')})")
            L.append("")
            if pc:
                L += ["Patterns: " + ", ".join(f"{k} {v}" for k, v in sorted(pc.items())), ""]
            L += [f"- {loc(h)} [{', '.join(h.get('patterns', []))}] ({h.get('audience')})"
                  f"{' (matched only after folding)' if h.get('folded') else ''}: "
                  f"{code(h['quote'].strip())}" for h in rows] or ["None."]
            L.append("")
    return L + _f4_part2(r)


def _f4_part2(r):
    L = ["### Tables", "", part2_line(r), ""]
    L += _list("Endpoints (hosts named anywhere; documented = named in the docs)",
               sorted(fnd(r, "04-phrases", "endpoint.host"),
                      key=lambda h: (h.get("documented"), not h.get("local"), h["host"])),
               lambda h: f"{h['host']}: {'documented' if h.get('documented') else 'not in the docs'}"
                         f"{', local' if h.get('local') else ''}, {h.get('kind')}; "
                         f"{', '.join(f'{v} {k}' for k, v in (h.get('where') or {}).items() if v)}; "
                         f"first at {loc((h.get('occurrences') or [{}])[0]) if h.get('occurrences') else '?'}")
    L += _list("Confirm-first and prohibited actions in instruction text",
               fnd(r, "04-phrases", "rubric.action"),
               lambda x: f"{loc(x)}: {x.get('tier')}, {code(x.get('action'))}, "
                         f"{'confirmation at line ' + str(x['confirm_line']) if x.get('confirmation') else 'no confirmation step'}"
                         f"{' (negated: without asking)' if x.get('negated_confirmation') else ''}"
                         f"{' (the step redefines confirmation)' if x.get('confirm_redefined') else ''}: "
                         f"{code(x['quote'].strip())}")
    L += _list("Conditionals", fnd(r, "04-phrases", "cond.branch"),
               lambda c: f"{loc(c)}: {c.get('kind')}: if {code(c.get('condition'))} then "
                         f"{code(c.get('body'))}")
    L += _list("Definitions", fnd(r, "04-phrases", "term.def"),
               lambda t: f"{loc(t)}: \"{t.get('term')}\" ({t.get('source')}): {code(t.get('definition'))}")
    L += _list("Terms defined more than one way", fnd(r, "04-phrases", "term.conflict"),
               lambda c: f"\"{c['term']}\": " + "; ".join(f"{d['file']}:{d['line']}"
                                                          for d in c.get("definitions", [])))
    L += _list("Safety words defined", fnd(r, "04-phrases", "term.safety"),
               lambda t: f"{loc(t)}: \"{t.get('term')}\"")
    return L


def _ev(f, full_by_key, reads=None):
    ev = full_by_key.get(_key(f), f).get("evidence", [])
    return [f"    - stage {e.get('stage')} {e.get('check')} {loc(e)}: {e.get('why')}{_mark(e, reads)}"
            for e in ev]


def _mark(e, reads) -> str:
    x = evidence_mark(e, reads or {})
    if not x:
        return ""
    return (f" (stage 6: read as {x['label']}, not an instruction; {x.get('backend')} "
            f"p={x['probabilities'][x['label']]:.2f})")


def _key(f):
    return (f["check"], f.get("file"), f.get("line"), f.get("leg"), f.get("grant"), f.get("pair"),
            f.get("mechanism"), f.get("event"))


def _f5(r, capability_full):
    full_by_key = {_key(f): f for f in (capability_full or {}).get("findings", [])}
    L = ["A map of capability, derived from stages 1 to 4, not a verdict. A clean, well-built "
         "repository usually has all three legs. A Bash grant is counted as private-data "
         "access and execute posture, never as external communication.", "", "### Trifecta legs", ""]
    reads = not_instruction_reads(r)
    for f in fnd(r, "05-capability", "cap.leg"):
        ev = full_by_key.get(_key(f), f).get("evidence", [])
        marked = sum(1 for e in ev if evidence_mark(e, reads))
        also = f", {marked} read in stage 6 as not an instruction" if marked else ""
        L.append(f"- {LEG_NAMES.get(f['leg'], f['leg'])}: {'yes' if f['present'] else 'no'} "
                 f"({n(len(ev), 'citation')}{also})")
        L += _ev(f, full_by_key, reads)
    L += ["", "### Install grants", ""]
    grants = fnd(r, "05-capability", "cap.grant")
    for f in grants:
        ev = full_by_key.get(_key(f), f).get("evidence", [])
        L.append(f"- {f['grant']} ({n(len(ev), 'citation')})")
        L += _ev(f, full_by_key)
    if not grants:
        L.append("None.")
    L += ["", "### Text in context at load", "", load_bytes_line(r), ""]
    L += [f"- {loc(i)}: {i.get('mechanism')}{' ' + str(i.get('event')) if i.get('event') else ''}, "
          f"{_bytes(i)}" for i in fnd(r, "05-capability", "cap.injection")]
    L.append("")
    L += _list("Agent and command posture", fnd(r, "05-capability", "cap.posture"),
               lambda p: f"{loc(p)}: {', '.join(p.get('posture', []))}"
                         f"{' (least privilege)' if p.get('least_privilege') else ''}; "
                         f"job {code(p.get('description'))}")
    for kind, title in (("orphan+phrase", "Orphan with a phrase hit"),
                        ("hidden+phrase", "Hidden text with a phrase hit"),
                        ("dynamic+phrase", "Load-only file with a phrase hit"),
                        ("hook+phrase", "Instruction in a script a context-injecting hook runs")):
        L += _list(f"Pairs: {title}", pairs(r, kind),
                   lambda p: f"{loc(p)}: {p['phrase_check']} [{', '.join(p.get('patterns', []))}]: "
                             f"{code(p['quote'].strip())}")
    return L


SECTIONS = {"01-inventory": _f1, "02-reader": _f2, "03-graph": _f3, "04-phrases": _f4,
            "05-capability": _f5, "06-soft": lambda r, c: _f6(r)}


def _soft_models(reports) -> str:
    """The stage 6 backends this run used, for the log header."""
    bs = (reports.get("06-soft") or {}).get("backends") or []
    if not bs:
        return "Soft models: none (stage 6 wrote the question packet only)"
    return "Soft models: " + "; ".join(
        f"{b['role']} {b['backend']} ({'remote' if b.get('remote') else 'local'}, {b.get('model')}"
        f"{_both(b)})" for b in bs)


def log(meta, runs, stamps, reports) -> str:
    L = [f"# {meta['repo']} run {meta['run']}", "",
         f"Source: {meta['source']} | channel: {meta.get('channel', 'directory')} | "
         f"pinned: {meta['hash_kind']} {meta['hash']}",
         f"Walkdown: {meta.get('tool', '?')} | optional deps: {meta.get('deps', 'see 07-limits.md')}",
         _soft_models(reports), "",
         "| Stage | Started | Finished | Output | Result | Validation |",
         "|---|---|---|---|---|---|"]
    by = {x.stage: x for x in runs}
    for stage in ORDER[:6]:
        x = by.get(stage)
        st = stamps.get(stage)
        if x is None:
            L.append(f"| {stage} | | | | not run | |")
            continue
        res = f"{len(x.report['findings'])} findings" if x.ok else f"FAILED: {x.error}"
        L.append(f"| {stage} | {x.started} | {x.finished or ''} | {stage + '.json' if x.ok else ''} | "
                 f"{res} | {st.text if st else ''} |")
    L += [f"| 07-limits | | {meta.get('finished', '')} | 07-limits.md | written | |",
          f"| 08-report | | {meta.get('finished', '')} | report/summary.md, report/full.md | written | |",
          "", "Awaiting human: whether to publish; whether coordinated disclosure is needed.", "",
          "Factory feedback:", ""]
    L += [f"- {x}" for x in meta.get("feedback", [])] or ["- (none recorded)"]
    return "\n".join(L) + "\n"


def limits_doc(meta, reports, notes, stamps, runs_ok) -> str:
    return "\n".join([f"# {meta['repo']} run {meta['run']}: not examined", ""]
                     + [f"- {x}" for x in limits(reports, notes, stamps, runs_ok)]) + "\n"
