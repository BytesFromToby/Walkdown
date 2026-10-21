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
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "04-phrases"))
import baserates  # noqa: E402
from audience import audience, is_test_data  # noqa: E402

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
# Stage 6 "do" reads (soft D1, 2026-10-01). The cutoff is 0.8 (measured: 7/7 right on the
# real lines). Jev's p(do) for one line moves between runs: 95% of repeat reads within 0.09
# (soft/EVAL.md "near-the-line band"). So a read within DRIFT of the cutoff is "near the
# line", listed apart from the reads well clear of it.
DO_CUTOFF = 0.8
DRIFT = 0.1
DO_CLEAR_P = round(DO_CUTOFF + DRIFT, 2)   # listed as a real-instruction read
DO_NEAR_P = round(DO_CUTOFF - DRIFT, 2)    # listed as near the line
# What a "do" read means, beside its score (review C34, 2026-10-17): the label says a line tells
# the AI to do the flagged thing; it never says the thing is harmful.
DO_MEANS = ("The score is how sure the model is that the line tells the AI to do the flagged thing. "
            "It does not say whether doing it is harmful: that depends on what the skill is for.")
# An agent with no tools list (review C27, 2026-10-17): it can use every tool, and the report
# counts that toward the legs; that is what it could do, with no evidence that it does.
CAPABILITY_ONLY = "capability only: what it could use, with no evidence it does"
CAPABILITY_ONLY_SHORT = "capability only"
# Stated limits (review C32, 2026-10-17): what backs read-only wording, in plain words.
SETTING_WORDS = {"tools-flag": "a --tools list", "deny": "a deny list", "sandbox": "a read-only sandbox",
                 "permission-mode": "plan mode"}
WRITE_CAPABLE = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"}


def limit_words(x) -> str:
    """Whether a tool setting backs a read-only line (stage 5 cap.limit), in plain words. It says
    what Walkdown found, never that the limit is broken."""
    owner, tools = x.get("owner"), x.get("owner_tools") or []
    if x.get("status") == "backed" and x.get("backed_by") == "flag":
        kinds = ", ".join(dict.fromkeys(SETTING_WORDS.get(k, k) for k in x.get("flags") or [])) or "a setting"
        return (f"A setting on this line backs it: {kinds} that rules out writing. Whether the command "
                "runs that way, only running it shows.")
    if x.get("status") == "backed":
        return (f"A tool setting backs it: the tools list of {owner} ({', '.join(map(str, tools))}) has "
                "no writing tool and no shell.")
    if x.get("status") == "contradicted":
        w = [str(t) for t in tools if str(t).split("(")[0] in WRITE_CAPABLE or t == "*"]
        # a fact only: "read-only" can describe something else, such as a data source (2026-10-17,
        # Compound Engineering's "Email sources are read-only"), which no setting decides
        return f"No tool setting backs it: the tools list of {owner} includes {', '.join(w)}."
    return ("Stated in the text; Walkdown found no tool setting that enforces it"
            + (f" ({owner} has no tools list)." if owner else "."))


def limit_routes(x, cap: int = 3) -> str:
    """Other routes in the same skill that can write, or ""."""
    rs = x.get("other_routes") or []
    if not rs:
        return ""
    shown = "; ".join(f"{r['file']}" + (f":{r['line']}" if r.get("line") is not None else "")
                      + f" ({r['what']})" for r in rs[:cap])
    return (f"Elsewhere in the same skill, a route can write: {shown}"
            + (f"; +{len(rs) - cap} more" if len(rs) > cap else "") + ".")  # full.md: one per evidence line, so kept short (owner)
# Soft D5 (2026-10-01): a stage 6 label other than "do" at p >= 0.8 marks a stage 5 evidence
# line as "read as not an instruction" (measured: 7/7 and 9/9 right on the real lines; at
# 0.6 three real instructions were misread). A mark never changes stage 5: the leg stays.
NOT_DO_P = 0.8
# Measured base rates of stage 4 patterns over the audited corpus (soft D1; baserates.py).
BASE = baserates.load()
COL = 32  # summary label column: longest heading plus a space

# The trifecta legs in plain words, locked by the owner 2026-09-30 (THREATS "Organizing frame").
# "Can ...": a static read shows what a skill could do, never what it does (owner, 2026-10-20,
# review C31 part B; the 2026-09-30 names were "Reads your data", "Takes outside input",
# "Sends data out", which the v1 page at the tag report-v1 keeps).
LEG_NAMES = {"private-data": "Can read your data", "untrusted-content": "Can take outside input",
             "external-comms": "Can send data out"}
LEG_DEFS = {
    "private-data": "Reads the user's data, wherever it lives: files, secrets, settings, connected accounts.",
    "untrusted-content": "Brings in text the user didn't write: the web, other people's issues or email, MCP tools, third-party code.",
    "external-comms": "Moves data off the machine or into shared places: web requests, webhooks, pushes, posts.",
}
# Plain words, no named term on the page (owner 2026-10-07); the docs credit Simon Willison's
# "lethal trifecta".
# Reworded by the owner 2026-10-21: no "It is not an issue on its own", which pulled against
# the sentence before it.
TRIFECTA_ALL = ("All three at once: it can read your data, take outside input, and send data out. "
                "That is the combination text from outside can steer into sending your data away.")
TRIFECTA_SOME = ("{n} of 3. That risk needs all three at once: reading your data, taking outside "
                 "input, and sending data out.")
NOT_WHAT = ('What this is not: static examination only. "Clean" means these stages found '
            "nothing; it does not mean the artifact is safe. This report offers possible issues "
            "with evidence and reaches no verdict. What to do with it is yours to decide.")

# Stage notes that name something the run did not examine (for 07-limits).
LIMIT_NOTE = re.compile(r"limit|absent|not installed|not scanned|not built|incomplete|skipped|"
                        r"unknown|not examined|not run|carried forward", re.I)

STANDING_LIMITS = [
    "Static examination only. Nothing in the artifact was executed, fetched, or installed.",
    "Stage 6 answers are located observations from the backends section 6 names; they "
    "never change a stage 1 to 5 finding. Hit counts carry a benign share only when stage 6 "
    "labels ran.",
    "Version drift (class 8): each run examines one pinned copy. walkdown.py compares it with "
    "the previous run of the same repository when there is one (changes.md next to this report); "
    "what the artifact becomes after its next update is seen only by auditing it again.",
    "English-language scope: the phrase layer is blind to non-English text (stage 2 lists "
    "non-Latin runs, and prose passages in another language in Latin script; a short line can "
    "slip past that check).",
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
    if f.get("line") is not None:
        return f"{f['file']}:{f['line']}"
    if f.get("text_line") is not None:  # a PDF, DOCX, or image: the line in its extracted text
        page = f", page {f['page']}" if f.get("page") is not None else ""
        return f"{f['file']} (extracted text{page}, line {f['text_line']})"
    return f["file"]


def fnd(reports, stage, check=None):
    rep = reports.get(stage) or {}
    return [f for f in rep.get("findings", []) if check is None or f["check"] == check]


def n(x, word, plural=None) -> str:
    return f"{x} {word if x == 1 else (plural or word + 's')}"


def pairs(reports, kind):
    return [f for f in fnd(reports, "05-capability", "cap.pair") if f.get("pair") == kind]


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
    lang = len(fnd(r, "02-reader", "read.language"))
    return (f"{read}/{total} files ({pct}). {n(len(div), 'divergence')}"
            f"{' (' + cs + ')' if cs else ''}. {n(fold, 'line')} changed by folding. "
            f"{n(script, 'non-Latin run')}. {n(lang, 'passage')} in a language other than English.")


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
    unl = len(fnd(r, "03-graph", "graph.unlisted"))
    tail = (f" {n(unl, 'skill, agent, or command', 'skills, agents, or commands')} on disk that "
            f"their manifest leaves out." if unl else "") + tail
    return (f"{n(entries, 'entry point')}. {n(orph, 'orphan')}. "
            f"{n(len(dang), 'dangling reference')}{' (' + cs + ')' if cs else ''}. "
            f"{n(dyn, 'dynamic load')}: {n(loaded, 'file')} loaded only through one (named by "
            f"nothing), {n(mentioned, 'file')} reached only through a mention of a folder or wildcards."
            f"{tail}")


def phrase_hits(r):
    return [h for h in fnd(r, "04-phrases") if h["check"].startswith("phrase.")]


LABEL_WORDS = (("do", "an instruction to do the matched action"), ("not-to", "an instruction not to"),
               ("description", "a description"), ("example-or-quote", "a quote or example"),
               ("other-sense", "the words in another sense"))


def benign_share(r) -> str:
    """REPORTING rule 2 (2026-10-03 review C15): when stage 6 labeled the lines a model reads,
    say how many read as an instruction to do the matched action and how many as something
    else. Without labels, say the share is not measured."""
    labels = [x for x in fnd(r, "06-soft", "soft.label") if "skipped" not in x and x.get("label")]
    if not labels:
        return "benign share not measured (stage 6 labels did not run)."
    c = collections.Counter(x["label"] for x in labels)
    other = len(labels) - c["do"]
    rest = ", ".join(f"{c[k]} {w}" for k, w in LABEL_WORDS[1:] if c[k])
    return (f"of {len(labels)} lines a model reads, {labels[0].get('backend')} labels {c['do']} as "
            f"an instruction to do the matched action and {other} as something else"
            + (f" ({rest})" if rest else "") + "; model labels, measured accuracy in "
            "docs/MODEL-ACCURACY.md.")


AUDIENCE_GROUP = {"model": "read by a model", "subagent": "read by a model", "tool": "in scripts",
                  "human": "human-facing", "test-data": "test data"}
AUDIENCE_ORDER = ("read by a model", "in scripts", "human-facing", "test data")


def _s4(r):
    hits = phrase_hits(r)
    by = collections.Counter(h["check"] for h in hits)
    parts = [f"{g.split()[0]} {sum(by[c] for c in cs)}" for g, cs in SUBGROUPS.items()]
    # where the lines are, by audience (2026-10-03 review A5): the totals include human-facing
    # files and test data, which never reach a model on install
    aud = {}
    for h in hits:
        aud.setdefault((h.get("file"), h.get("line")), h.get("audience"))
    where = collections.Counter(AUDIENCE_GROUP.get(a, "read by a model") for a in aud.values())
    split = ", ".join(f"{where[k]} {k}" for k in AUDIENCE_ORDER if where[k])
    line = f"{' · '.join(parts)} hits on {len(aud)} lines ({split}); {benign_share(r)}"
    return line + "\n" + " " * COL + part2_line(r)


def part2_line(r) -> str:
    hosts = fnd(r, "04-phrases", "endpoint.host")
    undoc = [h for h in hosts if not h.get("documented") and not h.get("local")]
    rub = fnd(r, "04-phrases", "rubric.action")
    unconf = [x for x in rub if not x.get("confirmation") and not x.get("negated_action")]
    forbid = sum(1 for x in rub if x.get("negated_action"))
    conds = collections.Counter(c.get("kind") for c in fnd(r, "04-phrases", "cond.branch"))
    cs = ", ".join(f"{v} {k}" for k, v in conds.most_common()) or "none"
    defs = fnd(r, "04-phrases", "term.def")
    dens = fnd(r, "04-phrases", "pos.density")
    reps = fnd(r, "04-phrases", "rep.sentence")
    tail = (f" Long files with flagged lines: {len(dens)}, "
            f"{sum(1 for d in dens if d.get('beyond_window'))} with some past the reader window. "
            f"Sentences repeated across files: {len(reps)}, "
            f"{sum(1 for x in reps if x.get('patterns'))} flagged. " + secrets_line(r))
    return (f"Hosts: {len(hosts)}, {len(undoc)} not named in the docs. Confirm-first or "
            f"prohibited actions in instruction text: {len(rub)}, {len(unconf)} with no "
            f"confirmation step, {forbid} stated as prohibitions. Conditionals: {cs}. Definitions: {len(defs)}, "
            f"{n(len(fnd(r, '04-phrases', 'term.conflict')), 'conflict')}, "
            f"{n(len(fnd(r, '04-phrases', 'term.safety')), 'safety-word definition')}." + tail)


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


LABEL_SAID = dict(LABEL_WORDS)


def questioned(reads, src) -> str | None:
    """One line for a card and the summary when a reviewer model's reading questions a finding
    (owner, 2026-10-20, review C28): a confident stage 6 read that the finding's line is not an
    instruction (`not_instruction_reads`). The finding stays; this is shown beside it."""
    if not src or src.get("line") is None:
        return None
    x = reads.get((src.get("file"), src.get("line")))
    if not x:
        return None
    p = (x.get("probabilities") or {}).get(x["label"], 0)
    return (f"A reviewer model's reading questions this: {x.get('backend') or 'a model'} read the "
            f"line as {LABEL_SAID.get(x['label'], x['label'])} (p={p:.2f}).")


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
    for t in fnd(r, "05-capability", "cap.testdata"):
        line += ("\n" + " " * COL + f"Test data set aside: {t.get('stage1', 0) + t.get('stage4', 0)} "
                 "findings in test or fixture folders count toward none of the above.")
    return line


STATUS = {"01-inventory": _s1, "02-reader": _s2, "03-graph": _s3, "04-phrases": _s4,
          "05-capability": _s5, "06-soft": lambda r: _s6(r)}


# ---------------------------------------------------------------- notes on places


def prohibition_note(x, short=False) -> str:
    """Review C25: a hit or rubric row whose action the line forbids ("Never ..."). The finding
    stays; this says how it is stated, with any exception ("unless ...")."""
    if not (x.get("negated") or x.get("negated_action")):
        return ""
    carve = f"; exception: {x['carve_out']}" if x.get("carve_out") else ""
    if short:
        return f" ({carve[2:]})" if carve else ""
    word = f" ({x['negation']}{carve})" if x.get("negation") else (f" ({carve[2:]})" if carve else "")
    return f" (stated as a prohibition{word})"


def hidden_how(p) -> str:
    """How a hidden+phrase pair hides its line: rendering hides it, or the phrase matches only
    once look-alike or invisible characters are folded (2026-10-09)."""
    whys = [str(e.get("why", "")) for e in p.get("evidence", []) if e.get("stage") == "02"]
    if any(w.startswith("hidden text") for w in whys) or not whys:
        return "hidden when rendered"
    return "disguised with look-alike or invisible characters"


def _split_audience(r, items):
    """Pairs on lines the model reads (model or subagent audience) are listed; pairs in
    scripts (tool) and human-facing files are counted. Stage 4 tags audience by path."""
    aud = {(h["file"], h["line"]): h.get("audience") for h in fnd(r, "04-phrases")}
    listed = [p for p in items
              if aud.get((p["file"], p["line"])) not in ("human", "tool", "test-data")]
    counted = collections.Counter(aud.get((p["file"], p["line"])) for p in items
                                  if p not in listed)
    return listed, counted


def secrets_line(r) -> str:
    """Section 4's count of lines that look like committed secrets (2026-10-04)."""
    allf = [x for x in (r.get("04-phrases") or {}).get("findings", []) if x.get("check") == "secret.found"]
    if any("skipped" in x for x in allf):
        return "Secret scan: skipped (no scanner installed)."
    test = sum(1 for x in allf if x.get("audience") == "test-data")
    plain = sum(1 for x in allf if x.get("likely_not_secret") and x.get("audience") != "test-data")
    engine = allf[0].get("engine") if allf else None
    extra = [f"{test} in test data"] if test else []
    if plain:
        extra.insert(0, f"{plain} that look like hashes, variable names, plain words, or local "
                        "test passwords")
    return (f"Lines that look like committed secrets: {len(allf) - test - plain}"
            + (f" (plus {'; plus '.join(extra)})" if extra else "")
            + (f", by {engine}." if engine else "."))


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
    return line + " Answers are located observations; they reach no verdict."


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


IMAGE_READ = {  # what stage 2 got of a pointed-at image's text, in plain words
    "unread": "this run could not read its text (no OCR), so open it and look",
    "ocr-text": "OCR found text in it (section 2), so read what the model would",
    "ocr-empty": "OCR found no text, but small or low-contrast text a model can read may still be there",
    "svg": "its text was read from the SVG source (section 2)",
}


def image_note(x) -> str:
    return (f"Referenced from {', '.join(x.get('froms') or [x.get('from')])}, which the model reads. "
            f"A model with vision reads text in an image; {IMAGE_READ.get(x.get('read'), x.get('read'))}.")


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
        out.append(f"{loc(p)}: If this message is meant for the user, write it to "
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
    for t in fnd(reports, "05-capability", "cap.testdata"):
        out.append(f"Test data is recognized by folder and file name (tests, fixtures, test_*.py "
                   f"and the like): {t.get('stage1', 0)} stage 1 and {t.get('stage4', 0)} stage 4 "
                   "findings there were kept out of the capability map and the summary. Test data "
                   "that a model-read file references directly is listed in section 5.")
    return out + STANDING_LIMITS


# details.html's count of what was not examined (owner 2026-10-07: 58 lines read as a hole).
# Only checks this run skipped that apply to this repository, one item each. Standing limits of
# the method, one-line-per-file repeats, and tools for file types the repository does not ship
# are left to the full list (section 7, data/07-limits.md), which keeps every line.
IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "ico"}
HTML_EXTS = {"html", "htm", "xhtml"}
# (stage 2 note start, what it covers, file kinds it serves (None = all text), why it was not
# done). A check with no code is "not built yet", apart from one waiting on a missing tool
# (2026-10-12, an outside audit: these three once read "<tool> not installed", though no code
# used the tools).
TOOL_NOTES = [
    ("tesseract", "Text inside images (OCR)", ("image",), "Tesseract not installed"),
    ("tesseract", "PDF pages drawn and read (OCR)", ("pdf",), "Tesseract not installed"),
    ("not built: PDF render", "PDF pages drawn and read as images", ("pdf",), "not built yet"),
    ("html render:", "HTML as a browser draws it", ("html",), "Playwright not installed"),  # since 2026-10-20
    ("not built: HTML render", "HTML as a browser draws it", ("html",), "not built yet"),
    ("not built: language detection", "Language detection in Latin-script text", None, "not built yet"),
    # the same three as runs before 2026-10-12 noted them
    ("poppler", "PDF pages drawn and read as images", ("pdf",), "not built yet"),
    ("playwright", "HTML as a browser draws it", ("html",), "not built yet"),
    ("lingua", "Language detection in Latin-script text", None, "not built yet"),
]
BINARY_NOTE = "limit: files that do not decode as text"
PER_FILE_NOTE = re.compile(r"^not scanned: (.+?): (.+)$")  # one file's skip line
STANDING_NOTE = re.compile(r"^(v1 limit|stage 5 limit|graph incomplete by construction"
                           r"|not scanned: .*\(not instruction text\))")


def file_kinds(reports) -> set[str]:
    """The kinds of file stage 1 saw that need an optional tool: image, pdf, html, docx."""
    kinds = set()
    for f in fnd(reports, "01-inventory", "inv.file"):
        ext, typ = (f.get("ext") or "").lower(), f.get("type") or ""
        if ext in IMAGE_EXTS or typ.startswith("image/"):
            kinds.add("image")
        if ext == "pdf" or typ == "application/pdf":
            kinds.add("pdf")
        if ext in HTML_EXTS or typ == "text/html":
            kinds.add("html")
        if ext == "docx":
            kinds.add("docx")
    return kinds


def glance(reports, notes, stamps, runs_ok) -> tuple[list[str], list[str]]:
    """(skipped, not needed): plain items for details.html's count (Other details). `skipped` is what this run
    could not look at in this repository; `not needed` names tools the repository has no use for."""
    skipped, idle = [], []
    for stage in ORDER[:6]:
        if stage not in runs_ok:
            skipped.append(f"{HEADINGS[stage]}: did not run to completion")
    kinds = file_kinds(reports)
    if "06-soft" in reports:
        soft = [f for f in fnd(reports, "06-soft") if "skipped" in f
                and f["check"] in ("soft.label", "soft.read")]
        if not (reports.get("06-soft") or {}).get("backends"):
            skipped.append("Model reads (optional): not run")
        elif soft:
            skipped.append(f"Model reads (optional): {n(len(soft), 'question')} skipped")
    for line in notes.get("02-reader", []):
        for start, what, serves, why in TOOL_NOTES:
            if line.startswith(start):
                if serves is None or kinds & set(serves):
                    skipped.append(f"{what}: {why}")
                else:
                    idle.append(f"{what}: none in this repository")
    for stage in ORDER[:6]:
        per_file: collections.Counter = collections.Counter()
        in_tests = 0
        for line in notes.get(stage, []):
            if stage == "02-reader" and any(line.startswith(t[0]) for t in TOOL_NOTES):
                continue
            if stage == "06-soft" or not LIMIT_NOTE.search(line) or STANDING_NOTE.search(line):
                continue
            if line.startswith(BINARY_NOTE):
                if "scanned from stage 2's extracted text" in line:
                    continue  # read from stage 2's text (2026-10-18); files without one are per-file notes
                if kinds & {"image", "pdf", "docx"}:
                    skipped.append("Phrase patterns in PDF, DOCX, and image files")
                continue
            m = PER_FILE_NOTE.match(line)
            if m:  # one item per stage, not one per file (2026-10-09: 67 on caveman)
                if is_test_data(m.group(1)):
                    in_tests += 1
                else:
                    per_file[m.group(2)] += 1
                continue
            skipped.append(f"{HEADINGS[stage]}: {line}")
        if per_file:
            kinds_txt = ", ".join(f"{c} {why}" for why, c in per_file.most_common())
            skipped.append(f"{HEADINGS[stage]}: {n(sum(per_file.values()), 'file')} not scanned "
                           f"({kinds_txt})" + (f", plus {in_tests} in test data" if in_tests else ""))
        elif in_tests:
            idle.append(f"{HEADINGS[stage]}: {n(in_tests, 'file')} not scanned, all in test data")
    other = collections.Counter(
        f["skipped"] for stage in ORDER[:5] for f in fnd(reports, stage)
        if "skipped" in f and "tesseract" not in str(f["skipped"])
        and not str(f["skipped"]).startswith("html not drawn (playwright"))
    skipped += [f"{n(c, 'file')}: {why}" for why, c in other.items()]
    unread = fnd(reports, "02-reader", "read.unread")
    if unread:
        skipped.append(f"{n(len(unread), 'file')} could not be read")
    unscanned = fnd(reports, "03-graph", "graph.unscanned")
    if unscanned:
        skipped.append(f"{n(len(unscanned), 'file')} not scanned for references")
    return skipped, idle


# ---------------------------------------------------------------- documents

def full(meta, reports, stamps, notes, runs_ok, capability_full=None) -> str:
    L = [f"# {meta['repo']}: full report", "",
         f"{meta['source']} | retrieved {meta['date']} | {meta['hash_kind']} {meta['hash']}",
         f"Run {meta['run']} | Walkdown {meta.get('tool', '?')}",
         "Static examination only. Nothing executed. Every finding below is a location to "
         "look at; none is a verdict. Stage order; nothing is ranked.", ""]
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
               lambda f: f"{loc(f)}: tools {f.get('tools') if f.get('tools') is not None else '(none listed: inherits all; ' + CAPABILITY_ONLY_SHORT + ')'}; "
                         f"job {code(f.get('description'))}")
    L += _list("Hooks", fnd(r, "01-inventory", "struct.hooks"),
               lambda f: f"{f['file']}: event {f.get('event')}, matcher {f.get('matcher')}, "
                         f"command {code(f.get('command'))}")
    L += _list("Platform manifests", fnd(r, "01-inventory", "struct.manifests"),
               lambda f: f"{f.get('name')}: {', '.join(f.get('files', []))}; "
                         f"declared permissions differ: {'yes' if f.get('divergent') else 'no'}")
    if pin.get("license_checked"):
        L += _list("Licenses (license files and declared license fields)", fnd(r, "01-inventory", "inv.license"),
                   lambda f: f"{loc(f)}: {f.get('license') or 'not recognized'}; "
                             + (f"declared in {f.get('field')}" if f.get("source") == "field"
                                else f"license file, matched by {f['how']}" if f.get("how") else "license file")
                             + (f"; says {code(f.get('stated'))}"
                                if f.get("stated") and f.get("stated") != f.get("license") else ""))
    return L


def _f2(r, _):
    L = _list("Divergences (reading A versus reading B)",
              [d for d in fnd(r, "02-reader", "read.divergence") if "skipped" not in d],
              lambda d: f"{loc(d)}: {d.get('reading')}, carrier {d.get('carrier')}"
                        + (f" ({d['how']})" if d.get("how") else "")  # how a drawn page hides it (2026-10-20)
                        + f", method {d.get('method')}: {code(d.get('text'))}")
    L += _list("Lines changed by folding", fnd(r, "02-reader", "read.fold"),
               lambda d: f"{loc(d)}: removed or replaced {', '.join(d.get('removed', []))}")
    L += _list("Non-Latin script runs", fnd(r, "02-reader", "read.script"),
               lambda d: f"{loc(d)}: {d.get('script')} {code(d.get('text'))}")
    L += _list("Passages in a language other than English (Latin script)",
               fnd(r, "02-reader", "read.language"),
               lambda d: f"{loc(d)}"
                         f"{'-' + str(d['end_line']) if d.get('end_line') not in (None, d.get('line')) else ''}: "
                         f"{d.get('rule')}, {d.get('other')} other-language words to {d.get('english')} English"
                         f"{' (' + ', '.join(d['matched']) + ')' if d.get('matched') else ''}: "
                         f"{code(d.get('text', '').splitlines()[0] if d.get('text') else '')}")
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
         f"load: a folder a config names, a code scan, wildcards in an instruction file; mention = only "
         f"through a folder or wildcards named elsewhere): {hs or 'none'}.", ""]
    L += _list("Entry points used", fnd(r, "03-graph", "graph.entry"),
               lambda f: f"{f['file']} ({f.get('kind')})")
    L += _list("Orphans (reachable from no entry point)", fnd(r, "03-graph", "graph.orphan"),
               lambda f: f["file"])
    L += _list("Files loaded only through a dynamic load (named by nothing)",
               [d for d in depth if d.get("via") == "dynamic"],
               lambda d: f"{d['file']} (depth {d['depth']}, from {d.get('from')})")
    L += _list("Files reached only through a mention of a folder or wildcards (not a load)",
               [d for d in depth if d.get("via") == "mention"],
               lambda d: f"{d['file']} (depth {d['depth']}, from {d.get('from')})")
    L += _list("Dynamic loads", fnd(r, "03-graph", "graph.dynamic"),
               lambda f: f"{loc(f)}: {f.get('source')} {code(f.get('pattern'))} "
                         f"({'load' if f.get('load') else 'mention'}) resolves to "
                         f"{n(len(f.get('resolves', [])), 'file')}")
    L += _list("On disk, left out of the manifest (a host that finds components by folder may "
               "still load them)", fnd(r, "03-graph", "graph.unlisted"),
               lambda f: f"{f['file']}: {f.get('kind')} not named by {f.get('manifest')}, which "
                         f"names {f.get('listed')} of the {f.get('on_disk')} on disk")
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
                  f"{' (matched only after folding)' if h.get('folded') else ''}"
                  f"{prohibition_note(h)}: "
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
                         f"{'stated as a prohibition' + prohibition_note(x, short=True) + ', ' if x.get('negated_action') else ''}"
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
    L += _list("Lines that look like committed secrets (values never shown)",
               fnd(r, "04-phrases", "secret.found"),
               lambda x: f"{loc(x)}: {', '.join(x.get('kinds') or [])} ({x.get('engine')}"
                         + (", test data" if x.get("audience") == "test-data" else "")
                         + (f"; likely not a secret: {x['likely_not_secret']}"
                            if x.get("likely_not_secret") else "") + ")")
    L += _list("Position of flagged lines in long files (first 10% / middle 80% / last 10%)",
               fnd(r, "04-phrases", "pos.density"),
               lambda d: f"{d['file']} ({d['lines']} lines): {d['first10']} / {d['middle80']} / "
                         f"{d['last10']}; {d['beyond_window']} past the reader window (after line "
                         f"{d['window_line']})")
    L += _list("Settings that restrict tools (a fact, never a risk)", fnd(r, "04-phrases", "limit.setting"),
               lambda x: f"{loc(x)}: {x.get('kind')} "
                         f"{', '.join(x['tools']) if x.get('tools') is not None else x.get('value')}"
                         f"; rules out {', '.join(x.get('rules_out') or []) or 'nothing'}"
                         f"{'; allows writing' if x.get('grants_write') else ''} ({x.get('audience')})")
    L += _list("Sentences repeated across files a model reads", fnd(r, "04-phrases", "rep.sentence"),
               lambda x: f"{loc(x)}: in {x['files']} files ({x['count']} times)"
                         + (f", flagged {', '.join(x['patterns'])}" if x.get("patterns") else "")
                         + f": {code(x['sentence'])}")
    return L


def _ev(f, full_by_key, reads=None):
    ev = full_by_key.get(_key(f), f).get("evidence", [])
    return [f"    - stage {e.get('stage')} {e.get('check')} {loc(e)}: {e.get('why')}"
            f"{' (' + CAPABILITY_ONLY_SHORT + ')' if e.get('why') == 'tool grant: inherits all' else ''}"
            f"{_mark(e, reads)}" for e in ev]


def _mark(e, reads) -> str:
    x = evidence_mark(e, reads or {})
    if not x:
        return ""
    return (f" (stage 6 reads this line as {x['label']}, with no instruction; {x.get('backend')} "
            f"p={x['probabilities'][x['label']]:.2f})")


def _key(f):
    return (f["check"], f.get("file"), f.get("line"), f.get("leg"), f.get("grant"), f.get("pair"),
            f.get("mechanism"), f.get("event"))


def _f5(r, capability_full):
    full_by_key = {_key(f): f for f in (capability_full or {}).get("findings", [])}
    L = ["A map of capability, derived from stages 1 to 4; it reaches no verdict. A Bash grant is "
         "counted as private-data "
         "access and execute posture; on its own it does not count as external communication.", "",
         "### Trifecta legs", ""]
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
    L += _list("Stated limits: read-only wording a model reads, and what backs it",
               fnd(r, "05-capability", "cap.limit"),
               lambda x: f"{loc(x)}: {x.get('status')}"
                         + (f" ({x['backed_by']})" if x.get("backed_by") else "")
                         + f"; {limit_words(x)}"
                         + (f" {limit_routes(x)}" if x.get("other_routes") else "")
                         + f" {code((x.get('quote') or '').strip())}")
    L += _list("Pairs: Test data a model-read file references directly",
               pairs(r, "testdata+loaded"),
               lambda p: f"{p['file']}: referenced from {p.get('from')}")
    L += _list("Pairs: Image a model-read file points at", pairs(r, "image+loaded"),
               lambda p: f"{p['file']}: referenced from {', '.join(p.get('froms') or [p.get('from')])}; "
                         f"text: {p.get('read')}{' (' + p['reason'] + ')' if p.get('reason') else ''}")
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
         f"Walkdown: {meta.get('tool', '?')} | optional deps: {meta.get('deps', 'see data/07-limits.md')}",
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
        L.append(f"| {stage} | {x.started} | {x.finished or ''} | {'data/' + stage + '.json' if x.ok else ''} | "
                 f"{res} | {st.text if st else ''} |")
    L += [f"| 07-limits | | {meta.get('finished', '')} | data/07-limits.md | written | |",
          f"| 08-report | | {meta.get('finished', '')} | summary.html, details.html, review.html, full.md | written | |",
          "", "A report about someone else's repository is not published until its author has "
          "seen it.", ""]
    return "\n".join(L) + "\n"


def limits_doc(meta, reports, notes, stamps, runs_ok) -> str:
    return "\n".join([f"# {meta['repo']} run {meta['run']}: not examined", ""]
                     + [f"- {x}" for x in limits(reports, notes, stamps, runs_ok)]) + "\n"
