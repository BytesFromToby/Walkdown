"""Report v1: the summary page as it was at git tag report-v1 (2026-10-16), kept frozen beside
v2 while the owner redesigns the page; written as summary-v1.html. Drop it once v2 settles.
Spec: specs/summary_v1_html.SPEC.md.

The summary page as readable HTML.

Same facts as summary.md, rewritten for a reader who is not a specialist: what to look
at first, one plain sentence per stage, technical detail behind a disclosure. Nothing
here detects or judges; every item comes from render.py's fixed rules.
"""
from __future__ import annotations

import collections
import html

import render as R

PLAIN_STAGE = {
    "01-inventory": "What ships", "02-reader": "What the model actually reads",
    "03-graph": "What loads what", "04-phrases": "What the text asks for",
    "05-capability": "What this touches", "06-soft": "Needs a human read",
    "07-limits": "Not examined",
}
# Plain names for pattern families (stage 4), used as the headline of an item.
FAMILY = [  # "Matches ..." states what the pattern found, never what the author meant
    ("L.", "Matches the wording of an instruction override"),
    ("RL.", "Matches the wording of fetching instructions from elsewhere"),
    ("K.", "Matches the wording of sending data out"),
    ("A.", "Matches the wording of a claimed permission"),
    ("J.enter-secret", "Matches the wording of asking for a password or key"),
    ("E.redirect-var", "Names a variable that redirects network traffic"),
    ("E.git-keys", "Names a git setting that persists"),
    ("E.memory", "Names a memory or local-settings file"),
    ("E.persist", "Writes to a shell profile or git hooks"),
    ("G.", "Matches the wording of telling a person to run something risky"),
    ("creds.", "Matches the wording of gathering secrets or credentials"),
]
MAX_FIRST = 12
# "Walkdown Results Breakdown" rows (owner, 2026-10-12): a question, what the step does, its result,
# and its numbers in the open; numbers longer than OPEN_LIMIT characters go behind a toggle.
STAGE_QUESTION = {
    "01-inventory": "What ships?", "02-reader": "What does the model actually read?",
    "03-graph": "What loads what?", "04-phrases": "What does the text ask for?",
    "05-capability": "What does it touch?", "06-soft": "What needs a human read?",
    "07-limits": "What was not examined?",
}
STAGE_DESC = {
    "01-inventory": "A breakdown of how many and what type of files are in the folder.",
    "02-reader": "What a model receives from each file, compared with what a person sees: hidden or "
                 "invisible text, comments, text in images.",
    "03-graph": "Which files point to which, starting from the files a tool loads first, and which "
                "files nothing points to.",
    "04-phrases": "Every line whose wording matches a known risky instruction, plus the definitions, "
                  "conditions, and web addresses in the text.",
    "05-capability": "What installing it grants: the three capabilities above, and what runs or loads "
                     "without anyone asking.",
    "06-soft": "Questions a pattern cannot settle, put to an optional model. Its answers never change "
               "the findings.",
    "07-limits": "What this run could not look at, and why.",
}
OPEN_LIMIT = 500
NOT_BUILT = ": not built yet"  # how render.glance marks a check with no code (2026-10-12)
ACCURACY_URL = "https://github.com/BytesFromToby/Walkdown/blob/main/docs/MODEL-ACCURACY.md"  # the published copy; a run folder has no docs/


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def _family(patterns) -> str:
    for p in patterns or []:
        for prefix, name in FAMILY:
            if p.startswith(prefix):
                return name
    return "Matches a pattern worth reading"


def _item(stage, title, where, quote=None, note=None, lead=None, kind=None, src=None) -> dict:
    """`lead`: words shown once before the card's notes, however many are merged. `kind` and
    `src` (the finding the item came from) are for the review page (review_html.py, 2026-10-12);
    this page does not show them."""
    return {"stage": stage, "title": title, "where": where, "quote": quote, "note": note,
            "lead": lead, "kind": kind, "src": src}


def first_items(r) -> list[dict]:
    """Everything the summary's points of attention name, as plain items, stage order."""
    out = []
    for h in [h for h in R.fnd(r, "01-inventory", "struct.hooks") if not R.is_test_data(h.get("file"))]:
        out.append(_item(1, "Runs commands on its own", h["file"],
                         f"{h.get('event')}: {h.get('command')}",
                         "A hook runs whenever the harness fires its event, without anyone asking.",
                         kind="hook", src=h))
    model, _ = R._split_audience(r, R.pairs(r, "hidden+phrase"))
    for p in model:
        out.append(_item(2, R.hidden_how(p).capitalize() + ", and reads like an instruction",
                         R.loc(p), p["quote"].strip(), kind="hidden+phrase", src=p))
    both = R.pairs(r, "orphan+phrase") + R.pairs(r, "dynamic+phrase")
    listed, _ = R._split_audience(r, both)
    for p in listed:
        why = ("Nothing refers to this file" if p["pair"] == "orphan+phrase"
               else "Loaded only by a folder or use of wildcards, named by nothing")
        out.append(_item(3, why + ", and it reads like an instruction", R.loc(p), p["quote"].strip(),
                         kind=p["pair"], src=p))
    hits = [h for h in R.phrase_hits(r) if R.POINT_PATTERNS & set(h.get("patterns", []))
            and h.get("audience") not in ("human", "test-data")]
    for h in hits:
        pats = sorted(R.POINT_PATTERNS & set(h["patterns"]))
        out.append(_item(4, _family(pats), R.loc(h), h["quote"].strip(), R.rates_note(r, pats),
                         lead="How often this pattern turns up elsewhere: ", kind="phrase", src=h))
    for c in R.fnd(r, "04-phrases", "term.conflict"):
        d = c["definitions"][0]
        out.append(_item(4, f"The word “{c['term']}” is defined {len(c['definitions'])} different ways",
                         f"{d['file']}:{d['line']}", kind="term.conflict", src=c))
    for t in R.fnd(r, "04-phrases", "term.safety"):
        out.append(_item(4, f"Redefines the safety word “{t['term']}”", R.loc(t), t.get("quote", "").strip(),
                         kind="term.safety", src=t))
    for x in R.fnd(r, "04-phrases", "secret.found"):
        if x.get("audience") != "test-data" and not x.get("likely_not_secret"):
            out.append(_item(4, "Looks like a committed secret", R.loc(x),
                             note=f"{', '.join(x.get('kinds') or [])}, found by {x.get('engine')}. "
                                  "The value is not shown in this report; open the file to check it.",
                             kind="secret", src=x))
    for d in R.fnd(r, "04-phrases", "pos.density"):
        if d.get("beyond_window"):
            out.append(_item(4, "Flagged text past the reader window", d["file"],
                             note=f"{d['beyond_window']} flagged line(s) after line {d['window_line']} "
                                  f"of {d['lines']}: where a reviewer's viewer may stop showing the file.",
                             kind="pos.density", src=d))
    for x in R.fnd(r, "04-phrases", "rep.sentence"):
        if x.get("patterns"):
            out.append(_item(4, "The same flagged sentence in several files", R.loc(x), x["sentence"],
                             f"In {x['files']} files. {_family(x['patterns'])}.", kind="rep.sentence", src=x))
    for x in R.fnd(r, "04-phrases", "rubric.action"):
        if x.get("confirm_redefined"):
            out.append(_item(4, "An action whose confirmation step is a redefinition", R.loc(x), x["quote"].strip(),
                             kind="rubric.redefined", src=x))
        elif x.get("tier") == "prohibited" and not x.get("confirmation"):
            out.append(_item(4, "An irreversible or prohibited action with no confirmation step",
                             R.loc(x), x["quote"].strip(), kind="rubric.prohibited", src=x))
    for p in R.pairs(r, "testdata+loaded"):
        out.append(_item(5, "Test data that the model is pointed at", p["file"],
                         note=f"Referenced directly from {p.get('from')}, which the model reads.",
                         kind="testdata+loaded", src=p))
    for p in R.pairs(r, "image+loaded"):
        out.append(_item(5, "An image the model is pointed at", p["file"], note=R.image_note(p),
                         kind="image+loaded", src=p))
    for p in R.pairs(r, "hook+phrase"):
        out.append(_item(5, "An instruction the model sees before you type anything", R.loc(p),
                         p["quote"].strip(), "A context-injecting hook runs this script.",
                         kind="hook+phrase", src=p))
    s = R._soft(r)
    new, _, near_sw = R.sweep_split(s)
    for x in new:
        out.append(_item(6, "No pattern matched, but a model read this as asking for a risky action",
                         f"{R.span(x)} (p={x['p_any']:.2f})",
                         note=R.SWEEP_PLAIN.get(R.sweep_kind(x), R.sweep_kind(x)),
                         lead=f"Read by {x['backend']} as telling the reader to: ", kind="sweep", src=x))
    for x in near_sw:
        if x.get("covered"):
            continue
        out.append(_item(6, "Near the line: no pattern matched, and a model may read this as "
                            "asking for a risky action", f"{R.span(x)} (p={x['p_any']:.2f})",
                         note=R.SWEEP_PLAIN.get(R.sweep_kind(x), R.sweep_kind(x)),
                         lead=f"Repeat sweeps vary by about {R.SWEEP_DRIFT}, so each could go "
                              f"either way. Read by {x['backend']} as telling the reader to: ",
                         kind="sweep", src=x))
    for x in s["reads"]:
        if x.get("file") and x.get("answer"):
            flat = " ".join(x["answer"].replace("**", "").split())
            out.append(_item(6, "A reviewer model's reading", R.loc(x),
                             note=flat[:320] + ("…" if len(flat) > 320 else ""), kind="read", src=x))
    clear, near = R.do_reads(s["labels"])
    for x in clear:
        out.append(_item(6, "Read as a real instruction to do the flagged thing",
                         f"{R.loc(x)} (p={R.p_do(x):.2f})",
                         note=f"Read by {x['backend']}, at p >= {R.DO_CLEAR_P}.", kind="label", src=x))
    for x in near:
        out.append(_item(6, "Near the line: may be a real instruction",
                         f"{R.loc(x)} (p={R.p_do(x):.2f})",
                         note=f"Read by {x['backend']}, at p {R.DO_NEAR_P} to {R.DO_CLEAR_P}. "
                              f"Repeat reads of one line vary by about {R.DRIFT}, so each of "
                              "these could go either way.", kind="label", src=x))
    return unique(out)


def unique(items) -> list[dict]:
    """One item per place: the same headline at the same location with the same quote is one
    place, however many findings name it (2026-10-12: three pairs on one line of the self-audit
    were counted and listed as three places). The first item stays; the other findings go in
    its `also`, and distinct notes are joined."""
    out, by = [], {}
    for it in items:
        k = (it["stage"], it["title"], it["where"], it.get("quote"))
        if k in by:
            g = by[k]
            g["also"].append(it.get("src"))
            if it.get("note") and it["note"] not in (g.get("note") or "").split("; "):
                g["note"] = f"{g['note']}; {it['note']}" if g.get("note") else it["note"]
            continue
        by[k] = {**it, "also": []}
        out.append(by[k])
    return out


def grouped(items) -> list[dict]:
    """Merge items with the same stage and headline into one card listing every place."""
    out, by = [], {}
    for it in items:
        k = (it["stage"], it["title"])
        if k in by:
            g = by[k]
            g["wheres"].append(it["where"])
            if it.get("quote"):
                g["quotes"].append(it["quote"])
            if it.get("note") and it["note"] not in (g.get("note") or "").split(" · "):
                g["note"] = f"{g['note']} · {it['note']}" if g.get("note") else it["note"]
        else:
            g = {**it, "wheres": [it["where"]], "quotes": [it["quote"]] if it.get("quote") else []}
            by[k] = g
            out.append(g)
    return out


def plain_status(r, stamps, stage) -> str:
    """One plain sentence per stage."""
    if stage not in r or r.get(stage) is None:
        return "This stage did not run."
    f = lambda check: R.fnd(r, stage, check)  # noqa: E731
    if stage == "01-inventory":
        pin = f("inv.pin")[0]
        hooks = f("struct.hooks")
        mans = sum(len(m.get("files", [])) for m in f("struct.manifests"))
        return (f"{pin['files']:,} files. {R.n(len(hooks), 'hook')} that run on their own, "
                f"{R.n(len(f('struct.agent-tools')), 'agent or command definition')}, "
                f"{R.n(mans, 'platform manifest')}.")
    if stage == "02-reader":
        total = R.fnd(r, "01-inventory", "inv.pin")[0]["files"]
        unread = len(f("read.unread"))
        div = [d for d in f("read.divergence") if "skipped" not in d]
        return (f"The model reads {total - unread:,} of {total:,} files. In {R.n(len(div), 'place')}, "
                f"what the model reads differs from what a person sees.")
    if stage == "03-graph":
        depth = f("graph.depth")
        loaded = sum(1 for d in depth if d.get("via") == "dynamic")
        return (f"{R.n(len(f('graph.entry')), 'entry point')} (files a tool loads first). "
                f"{R.n(len(f('graph.orphan')), 'file')} nothing refers to, {R.n(loaded, 'file')} loaded "
                "only by a folder or use of wildcards (a file-name pattern, like skills/*/SKILL.md).")
    if stage == "04-phrases":
        hits = R.phrase_hits(r)
        labels = [x for x in R.fnd(r, "06-soft", "soft.label") if "skipped" not in x and x.get("label")]
        lines = len({(h.get("file"), h.get("line")) for h in hits})
        share = ""
        if labels:
            do = sum(1 for x in labels if x["label"] == "do")
            share = (f" Of the {len(labels)} that a model sees, {labels[0].get('backend')} read {do} as a "
                     f"real instruction to do the flagged thing and {len(labels) - do} as something else "
                     "(a description, a quote, or the words in another sense).")
        return (f"{_count(lines, 'line')} match the wording of a risky instruction. Each is a place to "
                f"read, and none is a finding on its own.{share}")
    if stage == "05-capability":
        legs = {x["leg"]: x["present"] for x in f("cap.leg")}
        have = [R.LEG_NAMES[k].lower() for k in R.LEG_NAMES if legs.get(k)]
        if len(have) == 3:
            return R.TRIFECTA_ALL
        if not have:
            return "None of the three: it does not read your data, take outside input, or send data out."
        return (f"It {' and '.join(have)}: {len(have)} of the 3 that carry risk only when a tool "
                "has all three at once.")
    if stage == "06-soft":
        s = R._soft(r)
        if not s["backends"]:
            return f"{R.n(len(s['questions']), 'question')} written for a person to read. No model was asked."
        names = ", ".join(sorted({b["backend"] for b in s["backends"]}))
        return (f"{R.n(len(s['questions']), 'question')} a pattern could not settle, answered by {names}. "
                "Answers are readings; they reach no verdict.")
    return ""


def file_types(r) -> str:
    """Stage 1's file types and script languages, by count: "File types: md 94, sh 41, ..."."""
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    ext = sorted((pin.get("extensions") or {}).items(), key=lambda kv: (-kv[1], kv[0]))
    langs = sorted(((k, len(v)) for k, v in (pin.get("script_languages") or {}).items()),
                   key=lambda kv: (-kv[1], kv[0]))
    out = "File types: " + ", ".join(f"{k or 'no extension'} {v}" for k, v in ext) + "." if ext else ""
    if langs:
        out += " Scripts: " + ", ".join(f"{k} {v}" for k, v in langs) + "."
    return out.strip()


# Plain names for how stage 2 saw text differ (`carrier`) and for install grants (stage 5).
CARRIER_PLAIN = {
    "comment": "hidden comments", "alt": "image descriptions (alt text)", "title": "hover titles",
    "details": "collapsed sections", "reference-definition": "unused link definitions",
    "document-title": "document titles", "zero-width": "invisible characters",
    "bidi": "text-direction controls", "soft-hyphen": "soft hyphens",
    "white-on-white": "text colored like its background", "image-text": "text inside images",
    "vanish": "hidden Word text", "display:none": "elements styled not to show",
    "not-rendered": "text the page never shows", "aria-label": "screen-reader labels",
    "desc": "image descriptions inside SVG files", "metadata": "SVG metadata", "script": "SVG scripts",
}
GROUP_PLAIN = {  # stage 4's four groups (CONTRACT), named by what they look for
    "4a Reaching out": "reaching out (sending data, secrets, loading text from elsewhere)",
    "4b Taking the wheel": "taking the wheel (overriding instructions, claimed permission, redefined "
                           "words, steering a review, conditions)",
    "4c Changing the environment": "changing the environment (permissions, settings, scripts and hooks, "
                                   "actions that need your OK)",
    "4d Talking to the human": "talking to you (steps a person is told to run)",
}
AUDIENCE_PLAIN = {"model": "a model", "subagent": "a model", "tool": "scripts",
                  "human": "people (READMEs and docs)", "test-data": "test data"}
COND_PLAIN = {
    "error": "on errors", "absence": "when something is missing", "harness": "by which AI tool runs it",
    "clock": "by date or time", "version": "by version", "state": "first run versus later runs",
    "environment": "by machine or repository",
}
GRANT_PLAIN = {
    "exec-at-load": "runs commands as soon as it loads",
    "context-injection": "adds text to the model's context without being asked",
    "persistence": "makes changes that last after the session",
    "network": "uses the network",
    "elevated": "asks for more permissions than the default",
}


def _count(x: int, word: str) -> str:
    """'1,551 dangling references': R.n with a thousands separator."""
    return f"{x:,} {word if x == 1 else word + 's'}"


def facts(r, stage) -> list[str] | None:
    """A row's numbers in plain words, never repeating its plain sentence, each term explained
    where it appears (owner, 2026-10-12: "What is a glob? What is a dangling reference?").
    None: no plain version; the row shows the technical status line instead."""
    f = lambda check: R.fnd(r, stage, check)  # noqa: E731
    if stage not in r or r.get(stage) is None:
        return None
    if stage == "01-inventory":
        return [x for x in [file_types(r)] if x]
    if stage == "02-reader":
        div = [d for d in f("read.divergence") if "skipped" not in d]
        cs = collections.Counter(d.get("carrier", "?") for d in div)
        out = []
        if cs:
            out.append("Where they differ: " + ", ".join(
                f"{CARRIER_PLAIN.get(k, 'mixed invisible characters' if '+' in k else k)} {v}"
                for k, v in cs.most_common()) + ".")
        fold = len(f("read.fold"))
        if fold:
            out.append(f"{_count(fold, 'line')} read differently once look-alike or invisible "
                       "characters are swapped for plain ones.")
        script = len(f("read.script"))
        if script:
            out.append(f"{R.n(script, 'stretch', 'stretches')} of text in a non-Latin script "
                       "(Walkdown reads English only).")
        return out
    if stage == "03-graph":
        dang = f("graph.dangling")
        out = []
        if dang:
            ctx = collections.Counter(d.get("context", "?") for d in dang)
            out.append(f"{_count(len(dang), 'dangling reference')}: file paths written in the repository "
                       "that point at files not in it (" + ", ".join(
                           f"{v:,} in {k}" for k, v in ctx.most_common()) + ").")
        mentioned = sum(1 for d in f("graph.depth") if d.get("via") == "mention")
        if mentioned:
            out.append(f"{_count(mentioned, 'more file')} reached only through a mention of a folder or "
                       "wildcards, without a tool loading them.")
        if f("graph.dynamic"):
            out.append("Some files are only named when code runs, so this map can miss links.")
        return out
    if stage == "04-phrases":
        hits = R.phrase_hits(r)
        out = []
        by = collections.Counter(h["check"] for h in hits)
        kinds = [f"{GROUP_PLAIN[g]} {sum(by[c] for c in cs):,}" for g, cs in R.SUBGROUPS.items()]
        out.append("Matches by kind: " + "; ".join(kinds) + ".")
        aud = {}
        for h in hits:
            aud.setdefault((h.get("file"), h.get("line")), h.get("audience"))
        where = collections.Counter(AUDIENCE_PLAIN.get(a, "a model") for a in aud.values())
        out.append("Who reads those lines: " + ", ".join(
            f"{k} {where[k]:,}" for k in dict.fromkeys(AUDIENCE_PLAIN.values()) if where[k]) + ".")
        hosts = f("endpoint.host")
        if hosts:
            undoc = [h for h in hosts if not h.get("documented") and not h.get("local")]
            out.append(f"Web addresses: {_count(len(hosts), 'site')} named, {len(undoc)} of them not "
                       "mentioned in the docs.")
        rub = f("rubric.action")
        if rub:
            unconf = [x for x in rub if not x.get("confirmation")]
            out.append(f"Actions the AI tool's rules say need your OK first, or never allow (sending, "
                       f"publishing, paying, entering passwords): {len(rub)} in text a model follows, "
                       f"{len(unconf)} with no step asking you first.")
        conds = collections.Counter(c.get("kind") for c in f("cond.branch"))
        if conds:
            out.append("Conditions that change what it does: " + ", ".join(
                f"{v} {COND_PLAIN.get(k, k)}" for k, v in conds.most_common()) + ".")
        defs = f("term.def")
        if defs:
            conflicts, safety = len(f("term.conflict")), len(f("term.safety"))
            out.append(f"Words given their own meaning: {_count(len(defs), 'definition')}"
                       + (f", {_count(conflicts, 'word')} defined more than one way" if conflicts else "")
                       + (f", {_count(safety, 'safety word')} (like done or verified) redefined" if safety
                          else "") + ".")
        reps = [x for x in f("rep.sentence") if x.get("patterns")]
        if reps:
            out.append(f"{_count(len(reps), 'flagged sentence')} repeated across files a model reads.")
        far = sum(1 for d in f("pos.density") if d.get("beyond_window"))
        if far:
            out.append(f"{_count(far, 'long file')} with flagged lines past where a reviewer's viewer "
                       "may stop showing the file.")
        out.append(R.secrets_line(r))
        return out
    if stage == "05-capability":
        grants = [g["grant"] for g in f("cap.grant")]
        out = ["What installing it grants: " + ("; ".join(GRANT_PLAIN.get(g, g) for g in grants)
                                               if grants else "nothing beyond its files") + "."]
        desc = [i for i in f("cap.injection") if i.get("mechanism") == "description"]
        per = [x for x in f("cap.load-bytes") if x.get("file") and x.get("bytes") is not None]
        if desc:
            line = (f"Text in the model's context before you type: {sum(i.get('bytes') or 0 for i in desc):,} "
                    "bytes of skill and agent descriptions")
            if per:
                lo, hi = min(x["bytes"] for x in per), max(x["bytes"] for x in per)
                line += (f", about {hi:,} bytes with the startup hook" if lo == hi else
                         f", {lo:,} to {hi:,} bytes with the startup hook, depending on the AI tool")
            out.append(line + ".")
        for t in f("cap.testdata"):
            k = t.get("stage1", 0) + t.get("stage4", 0)
            if k:
                out.append(f"{R.n(k, 'finding')} in test or fixture folders set aside; "
                           "they count toward none of this.")
        return out
    if stage == "06-soft":
        s = R._soft(r)
        if not s["backends"]:
            return ["No model was asked. The questions are saved for a person to answer, in "
                    "data/06-packet.md."]
        out = []
        for b in s["backends"]:
            who = f"{b['backend']} ({'remote' if b.get('remote') else 'local'})"
            if b["role"] == "label":
                lc = collections.Counter(x["label"] for x in s["labels"])
                words = dict(R.LABEL_WORDS)
                out.append(f"{who} read the {len(s['labels'])} matched lines a model sees: " + ", ".join(
                    f"{lc[k]} as {words.get(k, k)}" for k, _ in R.LABEL_WORDS if lc[k]) + ".")
            elif b["role"] == "relational":
                out.append(f"{who} answered {R.n(len(s['reads']), 'question')} about a finding's context.")
            elif b["role"] == "sweep":
                new, old, near_sw = R.sweep_split(s)
                out.append(f"{who} read {len(s['sweep']):,} passages no pattern matched and flagged "
                           f"{len(new) + len(old)} ({len(new)} not already found by a pattern); "
                           f"{len(near_sw)} more are near the line.")
            elif b["role"] == "compare":
                agree = sum(1 for x in s["agree"] if x.get("agree"))
                out.append(f"{who} agreed with the first labeler on {agree} of {len(s['agree'])}.")
        return out + ["Their answers are in the model reads at the end."]
    return None


def _wheres(ws) -> str:
    uniq = list(dict.fromkeys(ws))
    return "  ·  ".join(uniq[:4]) + (f"  ·  +{len(uniq) - 4} more" if len(uniq) > 4 else "")


CHECK = ('<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="1.5" y="1.5" width="17" height="17" rx="3"/>'
         '<path d="M5.5 10.5l3 3 6-7"/></svg>')
BOX = '<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="1.5" y="1.5" width="17" height="17" rx="3"/></svg>'


def _trifecta(legs, marked=()) -> str:
    """The three legs as a checklist: a box per plain term, a one-line definition under each.
    `marked`: legs whose every cited line stage 6 read as not an instruction (soft D5).
    Checked legs come first, then unchecked (owner, 2026-10-12). Each checked box takes a color
    by its position among the checked ones, green, yellow, red (`data-n` 1 to 3): the risk is
    in having all three at once, so the third check is the red one, whichever leg it is."""
    order = [k for k in R.LEG_NAMES if legs.get(k)] + [k for k in R.LEG_NAMES if not legs.get(k)]
    rows = []
    for i, k in enumerate(order, 1):
        on = bool(legs.get(k))
        mk = ('<div class="leg-def">Every line cited for this was read in stage 6 as not an '
              'instruction. The box stays checked; see 5 in the full report.</div>'
              if on and k in marked else "")
        n = f' data-n="{i}"' if on else ""
        rows.append(f'<li class="leg {"on" if on else "off"}"{n}><span class="box" role="img" '
                    f'aria-label="{"yes" if on else "no"}">{CHECK if on else BOX}</span>'
                    f'<div><div class="leg-name">{esc(R.LEG_NAMES[k])}</div>'
                    f'<div class="leg-def">{esc(R.LEG_DEFS[k])}</div>{mk}</div></li>')
    n_on = sum(1 for k in R.LEG_NAMES if legs.get(k))
    foot = R.TRIFECTA_ALL if n_on == 3 else R.TRIFECTA_SOME.format(n=n_on)
    return (f'<section class="trifecta" aria-label="What it can do"><h2>What it can do</h2>'
            f'<ul class="legs">{"".join(rows)}</ul><p class="leg-foot">{esc(foot)}</p></section>')


def _tile(label, value, sub="") -> str:
    return (f'<div class="tile"><div class="tile-v">{esc(value)}</div>'
            f'<div class="tile-l">{esc(label)}</div>{f"<div class=tile-s>{esc(sub)}</div>" if sub else ""}</div>')


def _cards(items, empty: str) -> list[str]:
    out = []
    for it in items[:MAX_FIRST]:
        quotes = "\n".join(it["quotes"][:6])
        q = f'<pre class="quote">{esc(quotes)}</pre>' if quotes else ""
        nt = (f'<p class="note">{esc((it.get("lead") or "") + it["note"])}</p>'
              if it.get("note") else "")
        places = len(it["wheres"])
        count = f' <span class="count">{places} places</span>' if places > 1 else ""
        num = it["stage"]
        out.append(f'<li class="item"><div class="item-h"><a class="stage-tag" href="#stage-{num}">'
                   f'{esc(PLAIN_STAGE[R.ORDER[num - 1]])}</a>'
                   f'<h3>{esc(it["title"])}{count}</h3></div>'
                   f'<code class="where">{esc(_wheres(it["wheres"]))}</code>{q}{nt}</li>')
    more = len(items) - MAX_FIRST
    if more > 0:
        out.append(f'<li class="more">{more} more in the full report.</li>')
    if not items:
        out.append(f'<li class="more">{empty}</li>')
    return out


def _models_section(r, items) -> str:
    """Stage 6 reads in their own block (2026-10-03 review C14): model reads are optional and
    experimental, so the deterministic findings lead and these follow, labeled as such. Since
    2026-10-12 (owner) the block comes last, after the recommendations, closed by default with
    its count on the toggle: on superpowers 21 model reads had outweighed 2 places to check."""
    if not items:
        return ""
    names = ", ".join(sorted({b["backend"] for b in R._soft(r)["backends"]})) or "a model"
    cards = "".join(_cards(items, ""))
    count = sum(len(it["wheres"]) for it in items)
    return (f'<section class="models"><details><summary><h2>Model reads (experimental)</h2>'
            f'<span class="count">{R.n(count, "place")}</span></summary>'
            f'<p class="lede">Optional stage 6 reads by '
            f'{esc(names)}. A model\'s reading can be wrong, and repeat reads of one line vary; '
            f'these never change the findings above. Measured accuracy: '
            f'<a href="{ACCURACY_URL}">docs/MODEL-ACCURACY.md</a>.</p><ol class="first">{cards}</ol>'
            f'</details></section>')


def render_page(meta, r, stamps, notes, runs_ok) -> str:
    every = grouped(first_items(r))
    items = [it for it in every if it["stage"] != 6]
    model_items = [it for it in every if it["stage"] == 6]
    lim = R.limits(r, notes, stamps, runs_ok)
    skipped, idle = R.glance(r, notes, stamps, runs_ok)
    recs = R.recommendations(r)
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    legs = {x["leg"]: x["present"] for x in R.fnd(r, "05-capability", "cap.leg")}
    total, unread = pin.get("files", 0), len(R.fnd(r, "02-reader", "read.unread"))
    tiles = [_tile("files examined", f"{total:,}", f"{total - unread:,} read in full"),
             _tile("places to check", sum(len(it["wheres"]) for it in items),
                   f"under {len(items)} heading{'s' if len(items) != 1 else ''}"
                   + (f"; {sum(len(it['wheres']) for it in model_items)} model reads at the end"
                      if model_items else "")),
             _tile("checks skipped", len(skipped), "that apply to this repository")]
    trifecta = _trifecta(legs, R.all_marked_legs(r))
    first = _cards(items, "Nothing to check: no location met the rules. See each stage below.")
    models = _models_section(r, model_items)
    stages = []
    for i, stage in enumerate(R.ORDER, 1):
        stamp, tech = "", None
        more = ""
        if stage == "07-limits":
            plain = (f"This run skipped {R.n(len(skipped), 'check')} that apply to this repository. A clean "
                     "result says nothing about these.")
            todo = [x[:-len(NOT_BUILT)] for x in skipped if x.endswith(NOT_BUILT)]
            other = [x for x in skipped if not x.endswith(NOT_BUILT)]
            texts = ([f"Not built yet: {'; '.join(todo)}."] if todo else []) \
                + ([f"Skipped in this run: {'; '.join(other)}."] if other else []) \
                + ([f"Not needed here: {'; '.join(idle)}."] if idle else [])
            detail = "".join(f"<p>{esc(t)}</p>" for t in texts)
            more = (f'<details><summary>Every limit, including those of every run ({len(lim)})</summary>'
                    f"<ul>{''.join(f'<li>{esc(x)}</li>' for x in lim)}</ul></details>")
        else:
            plain = plain_status(r, stamps, stage)
            tech = R.status(r, stamps, stage).replace("\n" + " " * R.COL, " ")
            texts = facts(r, stage)
            if texts is None:  # no plain version: the technical line, behind the toggle when long
                texts = [tech]
            detail = "".join(f"<p>{esc(t)}</p>" for t in texts if t)
            st = stamps.get(stage)
            if st:
                stamp = f'<p class="stamp">Checked against its test fixtures: {esc(st.text)}</p>'
        # numbers in the open when short; behind a toggle when long (owner, 2026-10-12)
        label = "Technical detail" if texts and texts[0] == tech else "More detail"
        numbers = ("" if not texts else f'<div class="facts">{detail}</div>'
                   if sum(len(t) for t in texts) < OPEN_LIMIT
                   else f'<details><summary>{label}</summary>{detail}</details>') + more
        warn = ""
        st = stamps.get(stage)
        if st is not None and st.result != "PASS":
            warn = f'<span class="pill">validation {esc(st.result.lower())}</span>'
        stages.append(f'<li class="stage" id="stage-{i}"><span class="num">{i}</span><div class="stage-b">'
                      f'<h3>{esc(STAGE_QUESTION[stage])} {warn}</h3>'
                      f'<p class="desc">{esc(STAGE_DESC[stage])}</p><p class="plain">{esc(plain)}</p>'
                      f'{numbers}{stamp}</div></li>')
    recs_html = ("".join(f"<li>{esc(x)}</li>" for x in recs) if recs
                 else "<li>None. No finding matched a recommendation template.</li>")
    review = ('<p class="review-link"><a href="review.html">Walk through every place one at a time</a>, '
              'with the lines around it, and mark each one Concerned, Not concerned, or Not sure.</p>'
              if every else "")
    return PAGE.format(
        title=esc(f"Walkdown: {meta['repo']}"), review=review, repo=esc(meta["repo"]), source=esc(meta["source"]),
        hash=esc(f"{meta['hash_kind']} {meta['hash'][:12]}"), date=esc(meta["date"]), run=esc(meta["run"]),
        tiles="".join(tiles), trifecta=trifecta, first="".join(first), models=models, stages="".join(stages), recs=recs_html,
        nrecs=len(recs), notwhat=esc(R.NOT_WHAT))


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
/* Layout: an inspection record. Header card, a strip of three counts, "things to check" as the
   main column, then the seven stages as a numbered checklist (the order is the method's order). */
:root {{
  --paper: #f5f7f8; --sheet: #ffffff; --ink: #17222e; --muted: #5a6875; --rule: #d8dee4;
  --accent: #1d6a86; --flag: #9a5b00; --flag-bg: #fdf3e4; --quote-bg: #eef2f5;
  --leg-1: #2f7d46; --leg-2: #d9a40b; --leg-3: #b42318; --leg-mark: #ffffff; --leg-2-mark: #17222e;
  --display: "Archivo", "Arial Narrow", Arial, sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", Consolas, "Courier New", monospace;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833;
  --leg-1: #6cc488; --leg-2: #e8c14a; --leg-3: #f2776b; --leg-mark: #0f151b; --leg-2-mark: #0f151b; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833;
  --leg-1: #6cc488; --leg-2: #e8c14a; --leg-3: #f2776b; --leg-mark: #0f151b; --leg-2-mark: #0f151b; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--paper); color: var(--ink); font: 17px/1.55 var(--body); }}
.wrap {{ max-width: 58rem; margin: 0 auto; padding-inline: 16px; padding-block: 2rem 4rem; display: grid; gap: 2.2rem; }}
header.card {{ background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; padding: 1.6rem 1.6rem 1.3rem; }}
.eyebrow {{ font: 600 .78rem/1 var(--body); letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }}
.top {{ display: flex; gap: .75rem; justify-content: space-between; align-items: flex-start; }}
.top .eyebrow {{ min-width: 0; line-height: 1.3; padding-top: .3rem; }}
.pagelink {{ font: 600 .88rem/1.2 var(--body); color: var(--accent); text-decoration: none; border: 1px solid var(--rule); border-radius: 999px; padding: .35rem .75rem; white-space: nowrap; flex-shrink: 0; }}
.pagelink:hover, .pagelink:focus-visible {{ border-color: var(--accent); }}
h1 {{ font: 700 clamp(1.9rem, 4vw, 2.6rem)/1.1 var(--display); margin: .5rem 0 .6rem; text-wrap: balance; }}
.meta {{ font: .82rem/1.5 var(--mono); color: var(--muted); display: flex; flex-wrap: wrap; gap: .3rem 1.2rem; overflow-wrap: anywhere; }}
.static {{ margin: .9rem 0 0; color: var(--muted); }}
.tiles {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1px; background: var(--rule); border: 1px solid var(--rule); border-radius: 6px; overflow: hidden; }}
.tile {{ background: var(--sheet); padding: 1rem 1.1rem; }}
.tile-v {{ font: 700 1.9rem/1 var(--display); font-variant-numeric: tabular-nums; }}
.tile-l {{ margin-top: .35rem; font-weight: 600; }}
.tile-s {{ font-size: .85rem; color: var(--muted); }}
h2 {{ font: 700 1.35rem/1.2 var(--display); margin: 0 0 .9rem; }}
.lede {{ color: var(--muted); margin: -.4rem 0 1rem; max-width: 65ch; }}
.review-link {{ margin: -.4rem 0 1rem; max-width: 65ch; }}
.review-link a {{ color: var(--accent); font-weight: 600; }}
ol, ul {{ margin: 0; padding: 0; list-style: none; }}
.first {{ display: grid; gap: .8rem; }}
.item {{ background: var(--sheet); border: 1px solid var(--rule); border-left: 4px solid var(--flag); border-radius: 4px; padding: .9rem 1.1rem; min-width: 0; }}
.item-h {{ display: flex; gap: .7rem; align-items: baseline; flex-wrap: wrap; }}
.item h3 {{ margin: 0; font: 600 1.05rem/1.3 var(--body); }}
.count {{ font: 400 .85rem var(--body); color: var(--muted); }}
.stage-tag {{ font: 600 .72rem/1 var(--body); letter-spacing: .08em; text-transform: uppercase; color: var(--flag); background: var(--flag-bg); padding: .3rem .5rem; border-radius: 3px; white-space: nowrap; text-decoration: none; }}
a.stage-tag:hover, a.stage-tag:focus-visible {{ text-decoration: underline; }}
.where {{ display: block; margin-top: .4rem; font: .8rem/1.4 var(--mono); color: var(--accent); overflow-wrap: anywhere; }}
.quote {{ margin: .6rem 0 0; padding: .6rem .8rem; background: var(--quote-bg); border-radius: 3px; font: .82rem/1.5 var(--mono); white-space: pre-wrap; overflow-wrap: anywhere; max-height: 9rem; overflow: auto; }}
.note {{ margin: .5rem 0 0; color: var(--muted); max-width: 70ch; }}
.more {{ color: var(--muted); padding: .2rem .2rem; }}
.stages {{ display: grid; gap: 0; border-top: 1px solid var(--rule); }}
.stage {{ display: grid; grid-template-columns: 2.6rem minmax(0, 1fr); gap: .9rem; padding: 1rem 0; border-bottom: 1px solid var(--rule); }}
.num {{ font: 700 1.5rem/1 var(--display); color: var(--accent); font-variant-numeric: tabular-nums; padding-top: .15rem; }}
.stage h3 {{ margin: 0; font: 600 1.08rem/1.3 var(--body); display: flex; gap: .6rem; align-items: center; flex-wrap: wrap; }}
.plain {{ margin: .25rem 0 .3rem; max-width: 68ch; }}
.pill {{ font: 600 .7rem/1 var(--body); letter-spacing: .06em; text-transform: uppercase; color: var(--flag); border: 1px solid var(--flag); border-radius: 999px; padding: .25rem .5rem; }}
details summary {{ cursor: pointer; }}
details summary:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
.stage details summary {{ color: var(--accent); font-size: .9rem; }}
.stage details p, .stage details li, .stage .facts p {{ font-size: .88rem; color: var(--muted); overflow-wrap: anywhere; }}
.stage .facts p {{ margin: .3rem 0 0; }}
.stage details ul {{ list-style: disc; padding-left: 1.2rem; margin-top: .4rem; }}
.desc {{ margin: .2rem 0 .1rem; color: var(--muted); font-size: .92rem; font-style: italic; max-width: 68ch; }}
.models summary {{ display: flex; gap: .4rem .8rem; align-items: baseline; flex-wrap: wrap; list-style: none; }}
.models summary::-webkit-details-marker {{ display: none; }}
.models summary::before {{ content: "\\25B8"; color: var(--accent); }}
.models details[open] > summary::before {{ content: "\\25BE"; }}
.models summary h2 {{ margin: 0; }}
.models summary .count {{ color: var(--muted); }}
.models details[open] > summary {{ margin-bottom: 1rem; }}
.stamp {{ font-family: var(--mono); font-size: .78rem; }}
.recs li {{ padding: .6rem 0; border-bottom: 1px solid var(--rule); max-width: 75ch; overflow-wrap: anywhere; }}
footer {{ border-top: 2px solid var(--ink); padding-top: 1rem; color: var(--muted); max-width: 70ch; }}
.trifecta {{ background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; padding: 1.2rem 1.4rem; }}
.trifecta h2 {{ margin-bottom: .7rem; }}
.legs {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.1rem; }}
.leg {{ display: grid; grid-template-columns: 1.6rem minmax(0, 1fr); gap: .6rem; align-items: start; }}
.box svg {{ width: 1.5rem; height: 1.5rem; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }}
.leg.on .box svg rect {{ fill: var(--leg-1); stroke: var(--leg-1); }}
.leg.on .box svg path {{ stroke: var(--leg-mark); stroke-width: 2.4; }}
.leg.on[data-n="2"] .box svg rect {{ fill: var(--leg-2); stroke: var(--leg-2); }}
.leg.on[data-n="2"] .box svg path {{ stroke: var(--leg-2-mark); }}
.leg.on[data-n="3"] .box svg rect {{ fill: var(--leg-3); stroke: var(--leg-3); }}
.leg.off .box svg rect {{ stroke: var(--muted); }}
.leg-name {{ font: 600 1.05rem/1.3 var(--body); }}
.leg.off .leg-name {{ color: var(--muted); }}
.leg-def {{ font-size: .88rem; color: var(--muted); margin-top: .15rem; }}
.leg-foot {{ margin: 1rem 0 0; padding-top: .8rem; border-top: 1px solid var(--rule); color: var(--muted); font-size: .92rem; }}
@media (max-width: 640px) {{ .legs {{ grid-template-columns: 1fr; }} }}
@media (max-width: 640px) {{ .tiles {{ grid-template-columns: repeat(3, minmax(0, 1fr)); }} header.card {{ padding: 1.2rem; }} }}
@media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; }} }}
</style>
</head>
<body>
<main class="wrap">
  <header class="card">
    <div class="top"><div class="eyebrow">Walkdown report</div><a class="pagelink" href="review.html">Review each place →</a></div>
    <h1>{repo}</h1>
    <div class="meta"><span>{source}</span><span>{hash}</span><span>retrieved {date}</span><span>run {run}</span></div>
    <p class="static">Static examination only. Nothing in it was installed or run.</p>
  </header>
  <section class="tiles" aria-label="At a glance">{tiles}</section>
  {trifecta}
  <section>
    <h2>Walkdown Results Breakdown</h2>
    <ol class="stages">{stages}</ol>
  </section>
  <section>
    <h2>Things to check</h2>
    <p class="lede">Locations picked by fixed rules, in the order of the stages above. Each is a place to read; being listed does not mean something is wrong, and none is a finding against the author.</p>
    {review}
    <ol class="first">{first}</ol>
  </section>
  <section>
    <h2>Recommendations ({nrecs})</h2>
    <p class="lede">Each depends on what the skill is for. Unranked, in stage order.</p>
    <ul class="recs">{recs}</ul>
  </section>
  {models}
  <footer><p>{notwhat}</p><p>Every finding, with file and line, is in <code>full.md</code> next to this page.</p></footer>
</main>
</body>
</html>
"""
