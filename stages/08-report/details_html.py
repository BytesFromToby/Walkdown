"""The details page (details.html), for someone improving or investigating a repository.
Spec: specs/details_html.SPEC.md.

In the owner's order: what it is, the lethal trifecta with its places and General risks, the
files, outside links, hidden text, committed secrets, risky asks and things to check, changes
since the last run, recommendations, other details. Same facts as the other reports, from
render.py's fixed rules; nothing here detects or judges. Report v2 of the summary page
(2026-10-16), renamed when summary.html became the one page (owner, 2026-10-20). Every row that
names a place or an address has a Not concerned box (owner, 2026-10-20); the marks are the same
set review.html makes (marks.py), and neither page writes marks.json.
"""
from __future__ import annotations

import collections
import html
import json
import unicodedata
import urllib.parse

import marks as M
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
    spelled = R.tag_text(quote)  # review C42: say what hidden tag characters spell
    if spelled:
        note = f"The hidden tag characters spell: \u201c{spelled}\u201d." + (f" {note}" if note else "")
    if (src or {}).get("decoded_text"):  # review C42: an instruction hidden in base64
        note = f"Decoded from base64: \u201c{src['decoded_text']}\u201d." + (f" {note}" if note else "")
    return {"stage": stage, "title": title, "where": where, "quote": quote, "note": note,
            "lead": lead, "kind": kind, "src": src}


HOOK_NOTE = "A hook runs whenever the harness fires its event, without anyone asking."
# Where a host-run command runs, by its hook format (review C31, 2026-10-17).
HOOK_NOTES = {
    "cursor-environment": "Cursor runs this on its own cloud machine when it sets up or starts a cloud "
                          "agent for this repository, without anyone asking. It does not run on your "
                          "computer.",
}


def first_items(r) -> list[dict]:
    """The places to check, as plain items, stage order: listed on details.html, one card each on
    review.html, sorted into concern kinds on summary.html."""
    out = []
    for h in [h for h in R.fnd(r, "01-inventory", "struct.hooks") if not R.is_test_data(h.get("file"))]:
        out.append(_item(1, "Runs commands on its own", h["file"],
                         f"{h.get('event')}: {h.get('command')}",
                         HOOK_NOTES.get(h.get("format"), HOOK_NOTE), kind="hook", src=h))
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
    for h, pats in R.point_hits(r):
        title = _family(pats)
        if h.get("negated"):  # review C25: kept, and said how it is stated
            title += (", stated as a prohibition with an exception" if h.get("carve_out")
                      else ", stated as a prohibition")
        out.append(_item(4, title, R.loc(h), h["quote"].strip(), R.rates_note(r, pats),
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
        elif x.get("tier") == "prohibited" and not x.get("confirmation") and not x.get("negated_action"):
            out.append(_item(4, "An irreversible or prohibited action with no confirmation step",
                             R.loc(x), x["quote"].strip(), kind="rubric.prohibited", src=x))
    for p in R.pairs(r, "testdata+loaded"):
        out.append(_item(5, "Test data that the model is pointed at", p["file"],
                         note=f"Referenced directly from {p.get('from')}, which the model reads.",
                         kind="testdata+loaded", src=p))
    for p in R.pairs(r, "image+loaded"):
        out.append(_item(5, "An image the model is pointed at", p["file"], note=R.image_note(p),
                         kind="image+loaded", src=p))
    for x in R.fnd(r, "05-capability", "cap.limit"):  # owner, 2026-10-20, review C32
        if x.get("status") == "contradicted" and not R.is_test_data(x.get("file")):
            out.append(_item(5, "Says read-only, but its tools list can write", R.loc(x),
                             (x.get("quote") or "").strip(), kind="limit.contradicted", src=x))
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
    reads = R.not_instruction_reads(r)  # review C28: a model read that questions a finding
    for it in out:
        q = R.questioned(reads, it.get("src")) if it["stage"] < 6 else None
        if q:
            it["questioned"] = q
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
            g = {**it, "wheres": [it["where"]], "quotes": [it["quote"]] if it.get("quote") else [],
                 "questions": []}
            by[k] = g
            out.append(g)
        if it.get("questioned"):
            g["questions"].append((it["where"], it["questioned"]))
    return out


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
    "white-on-white": "text colored like its background", "image-text": "text inside images or drawn on PDF pages",
    "vanish": "hidden Word text", "display:none": "elements styled not to show",
    "not-rendered": "text the page never shows", "aria-label": "screen-reader labels",
    "desc": "image descriptions inside SVG files", "metadata": "SVG metadata", "script": "SVG scripts",
    "rendered": "web page text a browser does not show, or shows from the style sheet only",
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


CHECK = ('<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="1.5" y="1.5" width="17" height="17" rx="3"/>'
         '<path d="M5.5 10.5l3 3 6-7"/></svg>')
BOX = '<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="1.5" y="1.5" width="17" height="17" rx="3"/></svg>'


# ---------------------------------------------------------------- report v2 sections (2026-10-16)

TRIFECTA_LEDE = ("Simon Willison's name for three things an AI tool can do. Each one is ordinary on its "
                 "own. A tool that does all three can be steered by text from outside into sending "
                 "your data away.")
READ_BY = {"model": "the AI", "subagent": "the AI", "tool": "scripts", "human": "people",
           "test-data": "test data"}
LINK_SHOW = 72  # characters of an address shown in the links table; Copy takes the whole address
LIST_MAX = 6    # files named in a line of the stats before "+N more"
TOP_DIRS = ("", ".claude-plugin")  # where a repo's own license and manifest sit
OWN_SECTIONS = {"hidden+phrase", "secret"}  # item kinds with a section of their own


def _size(b: int) -> str:
    if b < 1000:
        return f"{b:,} bytes"
    for unit in ("KB", "MB", "GB"):
        b /= 1000
        if b < 1000 or unit == "GB":
            return f"{b:.1f} {unit}"
    return ""


def _files(xs) -> str:
    xs = list(dict.fromkeys(xs))
    return ", ".join(xs[:LIST_MAX]) + (f", +{len(xs) - LIST_MAX} more" if len(xs) > LIST_MAX else "")


def read_by(path) -> str:
    """Who reads a file, in plain words, from stage 4's audience rule (by path)."""
    return READ_BY.get(R.audience(path) if path else "model", "the AI")


def _section(sid, title, lede, body, cls="") -> str:
    lede_html = f'<p class="lede">{lede}</p>' if lede else ""
    return (f'<section class="block {cls}" id="{sid}"><h2>{esc(title)}</h2>{lede_html}{body}</section>')


def _p(text) -> str:
    return f"<p>{esc(text)}</p>"


def _empty(text) -> str:
    return f'<p class="empty">{esc(text)}</p>'


# ---------------------------------------------------------------------------- Not concerned
# Owner, 2026-10-20: a Not concerned box on every row that names a place or an address. A row's
# id is what marks.match matches it to: a place's review card id (so a mark made on either page
# is the same mark), anything else its stable key.


def _cards_by_key(r) -> dict:
    """{place key: review card} for every card on review.html."""
    import review_html  # imported here: review_html imports this module
    return {k: p for p in review_html.places(r) for k in p["keys"]}


def _nc(row, key, kind, where, headline, short=False) -> str:
    """The Not concerned box for one row, and where the page says a mark's other state. `short`:
    the words for screen readers only, in a table whose column heading says them."""
    words = '<span class="sr">Not concerned</span>' if short else " Not concerned"
    return (f'<label class="nc"><input type="checkbox" class="ncbox" data-row="{esc(row)}" '
            f'data-key="{esc(key)}" data-kind="{kind}" data-where="{esc(where)}" '
            f'data-headline="{esc(headline)}">{words}</label><span class="nc-tag"></span>')


def _place_row(it, cards, note=False) -> str:
    """One place (a first_items item): its location linked to its review card, its quote, and
    the box; `note`: also its note, for places whose notes differ."""
    k = M.place_key(it)
    card = cards.get(k)
    where = esc(it["where"])
    link = f'<a href="review.html#p-{card["id"]}">{where}</a>' if card else f"<code>{where}</code>"
    q = f'<pre class="quote">{esc(it["quote"])}</pre>' if it.get("quote") else ""
    nt = (f'<p class="note">{esc((it.get("lead") or "") + it["note"])}</p>'
          if note and it.get("note") else "")
    qs = f'<p class="questioned">{esc(it["questioned"])}</p>' if it.get("questioned") else ""
    return (f'<li class="row"><div class="row-main">{link}{q}{nt}{qs}</div>'
            f'{_nc(card["id"] if card else k, k, "place", it["where"], it["title"])}</li>')


def _line_text(r) -> dict:
    """{(file, line): stage 4's quote of that line}, the text a trifecta place's key names."""
    out = {}
    for f in R.fnd(r, "04-phrases"):
        if f.get("quote") and f.get("file") and f.get("line") is not None:
            out.setdefault((f["file"], f["line"]), f["quote"])
    return out


def _ev_key(leg, e, texts) -> str:
    return M.evidence_key(leg, e.get("file"), texts.get((e.get("file"), e.get("line"))) or e.get("line"))


def _divergences(r) -> list[dict]:
    return [d for d in R.fnd(r, "02-reader", "read.divergence") if "skipped" not in d]


def _hidden_key(d) -> str:
    return M.hidden_key(d.get("file"), d.get("carrier"), d.get("text") or d.get("line"))


def mark_rows(r, cap_full=None) -> list[tuple[str, list[str]]]:
    """Every row a mark can name in this run, as (row id, keys) for marks.match: each review
    card (answering to the key of every finding on it), each outside link, each Worth a look
    file, each place under a trifecta box, each hidden place. review.html and this page read
    marks against the same rows, so a download from either keeps the other's marks."""
    import review_html
    rows = [(p["id"], p["keys"]) for p in review_html.places(r)]
    texts = _line_text(r)
    ks = ({M.link_key(x["url"]) for x in link_rows(r)}
          | {M.file_key(rid, f) for rid, _, fs in file_concerns(r) for f in fs}
          | {_ev_key(leg, e, texts) for leg, (ev, _) in _leg_ev(r, cap_full).items() for e in ev}
          | {_hidden_key(d) for d in _divergences(r)})
    return rows + [(k, [k]) for k in sorted(ks)]


def marks_bar(r, cap_full, marks, carried) -> str:
    """Under the header: how marks are kept, Hide Not concerned, download and load. The run's
    marks (own or carried) are embedded for the page script; artifact text is escaped by
    json.dumps and "<" is written as \\u003c, so nothing closes the script tag."""
    rows = mark_rows(r, cap_full)
    saved, _ = M.match(marks, rows) if marks else ({}, 0)
    lookup = {k: rid for rid, ks in rows for k in ks}
    def payload(x):
        return json.dumps(x, ensure_ascii=True, sort_keys=True).replace("<", "\\u003c")
    came = (f' Marks carried from run {esc(carried)} show which run they are from.' if carried and saved else "")
    return (f'<div class="marksbar" id="marks"><p><b>Not concerned</b>: tick the box on any row you have '
            f'read and are fine with. <span id="nc-total"></span>{came}</p>'
            f'<div class="nav"><label class="hide-l"><input type="checkbox" id="hide-nc"> Hide Not concerned</label>'
            f'<button type="button" id="nc-dl">Download marks.json</button>'
            f'<label class="file-l">Load a marks file<input type="file" id="nc-load" accept=".json,application/json"></label>'
            f'<span class="note" id="nc-msg" role="status"></span></div>'
            f'<p class="note">Save the file as <code>marks.json</code> in this run folder. review.html and '
            f'summary.html read the same file when the report is re-rendered, and the next run of this '
            f'repository carries it over.</p></div>'
            f'<script type="application/json" id="nc-saved">{payload(saved)}</script>'
            f'<script type="application/json" id="nc-rows">{payload(lookup)}</script>')


HEADER_LINKS = (("summary.html", "← Summary"), ("review.html", "Review each place →"))


def header(meta, r=None, links=HEADER_LINKS) -> str:
    """The title, the run's facts, the license line, and the links to the other pages, top right."""
    bits = [meta.get("source", ""), f"{meta.get('hash_kind', '?')} {str(meta.get('hash', ''))[:12]}",
            f"retrieved {meta.get('date', '')}", f"run {meta.get('run', '')}"]
    if meta.get("tool"):
        bits.append(f"Walkdown {meta['tool']}")
    top = "".join(f'<a class="pagelink" href="{esc(h)}">{esc(t)}</a>' for h, t in links)
    return (f'<header class="card"><div class="top">{top}</div>'
            f'<h1><span class="h1-lead">Walkdown report on</span> {esc(meta["repo"])}</h1>'
            f'<div class="meta">{"".join(f"<span>{esc(b)}</span>" for b in bits if b)}</div>'
            f'{license_line(r) if r is not None else ""}</header>')


def _dir(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def license_line(r) -> str:
    """The licenses the repo states (stage 1 inv.license, class demo feedback 2026-10-17): the
    top-level license file first, then any other license stated elsewhere. Says which license
    text a file matches, never what it allows. A run made before the check says nothing."""
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    if not pin.get("license_checked"):
        return ""
    rows = [x for x in R.fnd(r, "01-inventory", "inv.license") if not R.is_test_data(x["file"])]
    files = [x for x in rows if x.get("source") == "file" and _dir(x["file"]) in TOP_DIRS]
    fields = [x for x in rows if x.get("source") == "field" and _dir(x["file"]) in TOP_DIRS]
    if files:
        lead = files
        line = "License: " + "; ".join(
            f"{x['license']} ({x['file']})" if x.get("license") else
            f"{x['file']} is not a license Walkdown recognizes; it begins “{x.get('stated') or ''}”"
            for x in files) + "."
    elif fields:
        lead = fields
        line = ("No license file at the top level; " +
                "; ".join(f"{x['file']} says {x.get('stated')}" for x in fields) + ".")
    else:
        lead = []
        line = "No license found: no license file and no license field at the top level."
    shown = {x.get("license") for x in lead}
    also, unknown = collections.defaultdict(list), []
    for x in rows:
        if x in lead:
            continue
        if x.get("license") and x["license"] not in shown:
            also[x["license"]].append(x["file"])
        elif not x.get("license") and x.get("source") == "file":
            unknown.append(x["file"])
    if also:
        line += " Also stated: " + "; ".join(f"{k} ({_files(v)})" for k, v in sorted(also.items())) + "."
    if unknown:
        line += f" {R.n(len(unknown), 'other license file')} Walkdown does not recognize ({_files(unknown)})."
    return f'<p class="license">{esc(line)}</p>'


def trifecta(r, cap_full=None, text_href=None) -> str:
    """The three legs as columns, checked first and colored by position (owner, 2026-10-12). Each
    checked column opens to the places that back it, linked (owner, 2026-10-20), and carries what
    installing it allows that belongs to that leg; the rest follows under General risks."""
    legs = {x["leg"]: x for x in R.fnd(r, "05-capability", "cap.leg")}
    on = {k: bool(legs.get(k, {}).get("present")) for k in R.LEG_NAMES}
    marked = R.all_marked_legs(r)
    allows = _allows(r)
    places = _place_ids(r)
    texts = _line_text(r)
    every = _leg_ev(r, cap_full)
    order = [k for k in R.LEG_NAMES if on[k]] + [k for k in R.LEG_NAMES if not on[k]]
    rows = []
    for i, k in enumerate(order, 1):
        ev, n = every[k]
        backing = _leg_places(k, ev, n, places, text_href, texts) if on[k] and n else ""
        mk = ('<div class="leg-def">Every line cited for this was read by a model as not an '
              'instruction. The box stays checked; see 5 in the full report.</div>'
              if on[k] and k in marked else "")
        extra = _allow_list([allows[a] for a in LEG_ALLOWS.get(k, ()) if allows[a][2]])
        data_n = f' data-n="{i}"' if on[k] else ""
        rows.append(f'<li class="leg {"on" if on[k] else "off"}"{data_n}><span class="box" role="img" '
                    f'aria-label="{"yes" if on[k] else "no"}">{CHECK if on[k] else BOX}</span>'
                    f'<div><div class="leg-name">{esc(R.LEG_NAMES[k])}</div>'
                    f'<div class="leg-def">{esc(R.LEG_DEFS[k])}</div>{backing}{mk}{extra}</div></li>')
    n_on = sum(on.values())
    foot = R.TRIFECTA_ALL if n_on == 3 else R.TRIFECTA_SOME.format(n=n_on)
    return (f'<section class="trifecta block" id="trifecta"><h2>The lethal trifecta</h2>'
            f'<p class="lede">{esc(TRIFECTA_LEDE)}</p><ul class="legs">{"".join(rows)}</ul>'
            f'<p class="leg-foot">{esc(foot)}</p>{general(allows)}</section>')


def _leg_ev(r, cap_full=None) -> dict:
    """{leg: (cited places, how many in all)}, every citation from capability.json when given."""
    legs = {x["leg"]: x for x in R.fnd(r, "05-capability", "cap.leg")}
    full = {x["leg"]: x for x in ((cap_full or {}).get("findings") or []) if x.get("check") == "cap.leg"}
    out = {}
    for k in R.LEG_NAMES:
        x = full.get(k) or legs.get(k, {})
        ev = x.get("evidence") or []
        out[k] = (ev, x.get("evidence_total", len(ev)))
    return out


# What installing it allows (stage 1 and stage 5 grants), by key. Two belong to a leg and show in
# its column (owner, 2026-10-20: "uses the internet" connects out); the rest is General risks.
LEG_ALLOWS = {"untrusted-content": ("mcp",), "external-comms": ("network",)}
GENERAL = ("hooks", "context", "persistence", "elevated", "agents")
SHOWN_PER_LEG = 400  # places listed under one box; the rest are in full.md section 5


def _allows(r) -> dict:
    """{key: (name, details, present)} for what installing it allows, in plain words."""
    grants = {g["grant"]: g for g in R.fnd(r, "05-capability", "cap.grant")}
    hooks = [h for h in R.fnd(r, "01-inventory", "struct.hooks") if not R.is_test_data(h.get("file"))]
    mcp = [m for m in R.fnd(r, "01-inventory", "struct.mcp") if not R.is_test_data(m.get("file"))]
    agents = [a for a in R.fnd(r, "01-inventory", "struct.agent-tools") if not R.is_test_data(a.get("file"))]
    out = {"hooks": ("Runs commands on its own",
                     [f"{h.get('event')}: {h.get('command')} ({h['file']}"
                      + ("; runs on Cursor's cloud machine, not your computer"
                         if h.get("host") == "cursor-cloud" else "") + ")" for h in hooks[:4]]
                     + ([f"+{len(hooks) - 4} more"] if len(hooks) > 4 else []),
                     bool(hooks) or "exec-at-load" in grants)}
    desc = [i for i in R.fnd(r, "05-capability", "cap.injection") if i.get("mechanism") == "description"]
    per = [x for x in R.fnd(r, "05-capability", "cap.load-bytes") if x.get("file") and x.get("bytes") is not None]
    inj = f"{sum(i.get('bytes') or 0 for i in desc):,} bytes of descriptions" if desc else ""
    if per:
        inj += (", " if inj else "") + f"about {max(x['bytes'] for x in per):,} bytes with the startup hook"
    out["context"] = ("Adds text to the AI's context before you type", inj, "context-injection" in grants)
    for g, key, name in (("persistence", "persistence", "Makes changes that last after the session"),
                         ("network", "network", "Connects to the internet"),
                         ("elevated", "elevated", "Asks for more permissions than the default")):
        x = grants.get(g, {})
        out[key] = (name, R.n(x.get("evidence_total", len(x.get("evidence") or [])), "place") if x else "",
                    g in grants)
    out["mcp"] = ("Connects to outside services (MCP servers)",
                  ", ".join(m.get("name") or "?" for m in mcp), bool(mcp))
    inherit = [a for a in agents if not a.get("tools")]
    out["agents"] = ("Agents with their own tools",
                     f"{R.n(len(agents), 'agent or command definition')}"
                     + (f", {len(inherit)} with no tools list (they can use every tool the AI has; "
                        f"{R.CAPABILITY_ONLY})" if inherit else ""), bool(agents))
    return out


def _allow_list(rows) -> str:
    lis = "".join(f'<li><span class="g-name">{esc(n)}</span>'
                  + "".join(f'<span class="g-detail">{esc(x)}</span>'
                            for x in ([d] if isinstance(d, str) else d) if x) + "</li>" for n, d, _ in rows)
    return f'<ul class="grants">{lis}</ul>' if rows else ""


def general(allows) -> str:
    """General risks: what installing it allows that is not one of the three legs."""
    have = [allows[k] for k in GENERAL if allows[k][2]]
    lack = [allows[k][0] for k in GENERAL if not allows[k][2]]
    body = _allow_list(have) or _empty("Nothing beyond its files: it loads nothing on its own.")
    if lack:
        body += f'<p class="g-none">Not found: {esc(", ".join(n[:1].lower() + n[1:] for n in lack))}.</p>'
    return f'<div class="gets-in"><h3>General risks</h3>{body}</div>'


def _place_ids(r) -> dict:
    """{(file, line): review card id} for the places the review page shows (rule findings)."""
    import review_html  # imported here: review_html imports this module
    return {(p.get("file"), p.get("line")): p["id"] for p in review_html.places(r) if not p["model"]}


def _ev_words(why) -> str:
    """Walkdown's reason for one piece of leg evidence, in plain words."""
    why = str(why or "")
    if why == "tool grant: inherits all":
        return f"No tools list: it can use every tool ({R.CAPABILITY_ONLY_SHORT})"
    if why.startswith("tool grant: "):
        return "Tools list: " + why[len("tool grant: "):]
    if why.startswith("phrase."):
        return _family([why.split(": ", 1)[-1]])
    return why


def _leg_places(leg, ev, total, places, text_href, texts) -> str:
    """The places behind one box, collapsed: each links to its review card, or else to this run's
    copy of the file, with its Not concerned box (owner, 2026-10-20)."""
    rows = []
    for e in sorted(ev, key=lambda e: (e.get("file") or "", e.get("line") or 0))[:SHOWN_PER_LEG]:
        pid = places.get((e.get("file"), e.get("line")))
        href = (f"review.html#p-{pid}" if pid else
                f"{text_href}/{urllib.parse.quote(e['file'])}.txt" if text_href and e.get("file") else None)
        where = esc(R.loc(e))
        link = f'<a href="{esc(href)}">{where}</a>' if href else f"<code>{where}</code>"
        k = _ev_key(leg, e, texts)
        rows.append(f'<li class="row"><div class="row-main">{link} <span class="ev-why">'
                    f'{esc(_ev_words(e.get("why")))}</span></div>'
                    f'{_nc(k, k, "evidence", R.loc(e), R.LEG_NAMES[leg])}</li>')
    shown = min(len(ev), SHOWN_PER_LEG)
    if total > shown:
        rows.append(f'<li class="more">{total - shown} more in full.md, section 5.</li>')
    return (f'<details class="leg-ev"><summary>{R.n(total, "place")} in the files</summary>'
            f'<ul>{"".join(rows)}</ul></details>')


def file_concerns(r) -> list[tuple[str, str, list[str]]]:
    """What in the files is worth a look, shown above the collapsed stats: (reason id, plain
    line, files). The reason id is part of each file's mark key (marks.file_key)."""
    census = R.fnd(r, "01-inventory", "struct.census")
    files = R.fnd(r, "01-inventory", "inv.file")
    by = collections.defaultdict(list)
    for c in census:
        by[c.get("flag")].append(c["file"])
    out = []
    unknown = [f["file"] for f in files if (f.get("type") in (None, "", "application/octet-stream"))
               and not R.is_test_data(f["file"])]
    if unknown:
        out.append(("unknown-type", "Unknown file type", unknown))
    if by["ext-magic-mismatch"]:
        out.append(("ext-magic-mismatch", "Contents are a different type than the file name says",
                    by["ext-magic-mismatch"]))
    if by["archive"]:
        out.append(("archive", "Archives (their contents were not read)", by["archive"]))
    if by["symlink"]:
        out.append(("symlink", "Links to another file or folder (symlinks)", by["symlink"]))
    long = [f for f in by["reader-window"] if R.audience(f) in ("model", "subagent")]
    if long:
        out.append(("reader-window", "Files the AI reads that are longer than a reviewer's viewer shows "
                    "(2,000 lines or 50 KB)", long))
    return out


def stats(r) -> str:
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    files = R.fnd(r, "01-inventory", "inv.file")
    ext = pin.get("extensions") or {}
    total = pin.get("files", len(files))
    head = f"{total:,} files, {R.n(len(ext), 'file type')}, {_size(pin.get('bytes') or 0)} in all."
    concerns = file_concerns(r)
    callout = ""
    if concerns:
        lis = ""
        for rid, t, fs in concerns:
            rows = "".join(f'<li class="row"><div class="row-main"><code>{esc(f)}</code></div>'
                           f'{_nc(M.file_key(rid, f), M.file_key(rid, f), "file", f, t)}</li>' for f in fs)
            shown = (f'<ul class="rows">{rows}</ul>' if len(fs) <= LIST_MAX else
                     f'<details class="rows"><summary>{R.n(len(fs), "file")}</summary><ul class="rows">{rows}</ul></details>')
            lis += f'<li><b>{esc(t)}</b> <span class="count">{len(fs)}</span>{shown}</li>'
        callout = f'<div class="callout"><h3>Worth a look</h3><ul>{lis}</ul></div>'
    lines = [file_types(r)]
    big = sorted((f for f in files if not R.is_test_data(f["file"])), key=lambda f: -(f.get("bytes") or 0))[:3]
    if big:
        lines.append("Largest: " + ", ".join(f"{f['file']} ({_size(f.get('bytes') or 0)})" for f in big) + ".")
    kinds = collections.Counter(f.get("entry_point") for f in files if f.get("entry_point"))
    if kinds:
        lines.append("Files a tool loads first: " + ", ".join(
            f"{k.replace('-', ' ')} {v}" for k, v in kinds.most_common()) + ".")
    desc = R.fnd(r, "01-inventory", "struct.description")
    if desc:
        lines.append(f"{R.n(len(desc), 'description')} always in the AI's context (the text that tells "
                     "it when to use each skill or agent).")
    mans = sum(len(m.get("files", [])) for m in R.fnd(r, "01-inventory", "struct.manifests"))
    if mans:
        lines.append(f"{R.n(mans, 'platform manifest')} (files that tell each AI tool what the plugin holds).")
    longl = [c for c in R.fnd(r, "01-inventory", "struct.census") if c.get("flag") == "long-line"]
    if longl:
        lines.append(f"{_count(len(longl), 'line')} over 500 characters, in "
                     f"{R.n(len({c['file'] for c in longl}), 'file')}.")
    if "03-graph" in r:
        depth = R.fnd(r, "03-graph", "graph.depth")
        direct = sum(1 for d in depth if d.get("via") == "static")
        loaded = sum(1 for d in depth if d.get("via") == "dynamic")
        mention = sum(1 for d in depth if d.get("via") == "mention")
        orphans = [o["file"] for o in R.fnd(r, "03-graph", "graph.orphan")]
        orph = len(orphans)
        lines.append(f"Map: {R.n(len(R.fnd(r, '03-graph', 'graph.entry')), 'starting point')} (files a "
                     f"tool loads first); {_count(direct, 'file')} reached by following references, "
                     f"{loaded:,} only through a folder or wildcard load, {mention:,} only mentioned "
                     f"through a folder or wildcard, {orph:,} that nothing points to"
                     + (f" ({_files(orphans)})" if orphans else "") + ".")
        dang = R.fnd(r, "03-graph", "graph.dangling")
        if dang:
            ctx = collections.Counter(d.get("context", "?") for d in dang)
            away = sum(1 for d in dang if d.get("folder_missing"))
            lines.append(f"Broken file references: {len(dang):,} paths written in the files point at files "
                         "that are not in the folder (" + ", ".join(f"{v:,} in {k}" for k, v in
                                                                 ctx.most_common()) + ")"
                         + (f"; {away:,} of them point into a folder the repository does not have, "
                            "often one the workflow creates when it runs" if away else "") + ".")
        lines.append("Some files are named only when code runs, so the map can miss links.")
    inner = "".join(_p(x) for x in lines if x)
    body = (f'<p class="headline">{esc(head)}</p>{callout}'
            f'<details class="fold"><summary>Files and map</summary><div class="facts">{inner}</div></details>')
    return _section("files", "Files", "", body)


def link_rows(r) -> list[dict]:
    """One row per address per line: domain, address, file, line, who reads the file. A run made
    before 2026-10-16 has no addresses saved; its rows show the domain."""
    rows = []
    for h in R.fnd(r, "04-phrases", "endpoint.host"):
        for o in h.get("occurrences", []):
            who = read_by(o.get("file"))
            for a in (o.get("urls") or [h["host"]]):
                rows.append({"host": h["host"], "url": a, "file": o.get("file"), "line": o.get("line"),
                             "who": who, "documented": h.get("documented")})
    return rows


def links(r) -> str:
    hosts = R.fnd(r, "04-phrases", "endpoint.host")
    lede = "Every web address the skill names. Walkdown gathered these and opened none of them."
    if "04-phrases" not in r:
        return _section("links", "Outside links", lede, _empty("Not checked: this run has no stage 4 output."))
    if not hosts:
        return _section("links", "Outside links", lede, _empty("No outside links: the skill names no web address."))
    rows = link_rows(r)
    ai = sum(1 for x in rows if x["who"] == "the AI")
    undoc = sum(1 for h in hosts if not h.get("documented") and not h.get("local"))
    head = (f"{_count(len(rows), 'link')} to {R.n(len(hosts), 'different domain')}. "
            f"{ai:,} in text the AI reads. "
            f"{R.n(undoc, 'domain')} the skill's docs never mention.")
    trs = []
    by_host = {h["host"]: h for h in hosts}
    for host in sorted({x["host"] for x in rows}):
        mine = [x for x in rows if x["host"] == host]
        look = R.lookalike_note(by_host.get(host, {}))  # review C42
        trs.append(f'<tr class="dom"><th colspan="4">{esc(host)}{esc(look)} <span class="count">{len(mine)}</span></th></tr>')
        for x in sorted(mine, key=lambda x: (x["file"] or "", x["line"] or 0, x["url"])):
            shown = x["url"] if len(x["url"]) <= LINK_SHOW else x["url"][:LINK_SHOW - 1] + "…"
            where = f"{x['file']}:{x['line']}" if x.get("line") is not None else (x["file"] or "")
            trs.append(f'<tr><td class="url"><code title="{esc(x["url"])}">{esc(shown)}</code>'
                       f'<button type="button" class="copy" data-url="{esc(x["url"])}" '
                       f'aria-label="Copy the whole link">Copy</button></td>'
                       f'<td class="loc"><code>{esc(where)}</code></td><td class="who">{esc(x["who"])}</td>'
                       f'<td class="nc-c">{_nc(M.link_key(x["url"]), M.link_key(x["url"]), "link", x["url"], where, short=True)}</td></tr>')
    table = (f'<details class="fold"><summary>All {len(rows):,} links, by domain</summary>'
             f'<div class="tablewrap"><table class="links"><thead><tr><th>Link</th><th>File, line</th>'
             f'<th>Read by</th><th class="nc-h">Not concerned</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div></details>')
    return _section("links", "Outside links", esc(lede), f'<p class="headline">{esc(head)}</p>{table}')


def hidden(r, raw, cards=None, text_href=None) -> str:
    """`raw`: first_items (one per finding); `cards`: _cards_by_key."""
    lede = "Text the AI receives that a person reading the file on screen would not see."
    if "02-reader" not in r:
        return _section("hidden", "Hidden text", esc(lede), _empty("Not checked: this run has no stage 2 output."))
    cards = _cards_by_key(r) if cards is None else cards
    div = _divergences(r)
    fold = [f for f in R.fnd(r, "02-reader", "read.fold") if fold_meaning(f)]  # typography left out
    script = R.fnd(r, "02-reader", "read.script")
    lang = R.fnd(r, "02-reader", "read.language")
    mine = [it for it in raw if it.get("kind") == "hidden+phrase"]
    if not div and not fold and not script and not lang:
        return _section("hidden", "Hidden text", esc(lede),
                        _empty("Nothing hidden: what the AI reads matches what a person sees."))
    head, lines = "", []
    if div:  # owner, 2026-10-20: the count, then the callout, then the other lines
        ai = sum(1 for d in div if R.audience(d.get("file")) in ("model", "subagent"))
        cs = collections.Counter(d.get("carrier", "?") for d in div)
        kinds = ", ".join(f"{CARRIER_PLAIN.get(k, 'mixed invisible characters' if '+' in k else k)} {v}"
                          for k, v in cs.most_common())
        head = (f'<details class="rows hl"><summary>{esc(R.n(len(div), "place"))} ({ai:,} in files the AI '
                f'reads)</summary>{_hidden_rows(div, text_href)}</details><p class="note">{esc(kinds)}</p>')
    if fold:
        lines.append(f"{_count(len(fold), 'line')} read differently once invisible characters or look-alike "
                     f"letters are swapped for plain ones: {fold_kinds(fold)}.")
    if script:
        lines.append(f"{R.n(len(script), 'stretch', 'stretches')} of text in a non-Latin script; the "
                     "risky-ask patterns read English only.")
    if lang:
        ai = sum(1 for d in lang if R.audience(d.get("file")) in ("model", "subagent"))
        lines.append(f"{R.n(len(lang), 'passage')} in a language other than English, written in the "
                     f"same alphabet ({ai:,} in files the AI reads); the risky-ask patterns read English "
                     "only, so read these yourself. The full report lists each one.")
    body = head + (_instruction_callout(mine, cards) if mine else "")
    if lines:
        body += '<ul class="hidden-more">' + "".join(f"<li>{esc(x)}</li>" for x in lines) + "</ul>"
    return _section("hidden", "Hidden text", esc(lede), body)


# What stage 2's fold swapped, by kind (owner, 2026-10-20: exact counts, never "most"). Only the
# kinds that can make a line say something other than what a person sees are shown or counted;
# typography (curly quotes, dashes, ellipses, special spaces, symbols such as x) is left to the full
# report (owner, 2026-10-20).
FOLD_KINDS = ("invisible characters", "look-alike letters")


def _fold_kind(code: str) -> str:
    try:
        cp = int(str(code).replace("U+", ""), 16)
    except ValueError:
        return "other symbols"
    ch = chr(cp)
    cat = unicodedata.category(ch)
    if cat in ("Cf", "Cc", "Co", "Cn") or 0xE0000 <= cp <= 0xE007F:
        return "invisible characters"
    if cat.startswith("L"):
        return "look-alike letters"
    if cat == "Zs":
        return "special spaces"
    if cp == 0x2026:
        return "ellipses (…)"
    if cat == "Pd" or cp == 0x2212:
        return "dashes"
    if cat in ("Pi", "Pf") or cp in (0x201A, 0x201E, 0x2032, 0x2033, 0xFF02, 0xFF07):
        return "typographic quotes"
    return "other symbols"


def fold_meaning(f) -> bool:
    """A folded line that holds an invisible character or a look-alike letter."""
    return any(_fold_kind(code) in FOLD_KINDS for code in f.get("removed") or [])


def fold_kinds(fold) -> str:
    """'invisible characters in 3, look-alike letters in 1': lines per kind, from each read.fold's
    `removed`, typography not counted; a line with both kinds counts in both."""
    lines: collections.Counter = collections.Counter()
    for f in fold:
        lines.update({k for k in map(_fold_kind, f.get("removed") or []) if k in FOLD_KINDS})
    parts = [f"{k} in {lines[k]:,}" for k in FOLD_KINDS if lines[k]]
    more = " (a line can have both)" if sum(lines.values()) > len(fold) else ""
    return ", ".join(parts) + more if parts else "characters not recorded"


def _hidden_rows(div, text_href) -> str:
    """Every hidden place: where (linked to this run's copy of the file), how it hides, the box."""
    rows = []
    for d in sorted(div, key=lambda d: (d.get("file") or "", d.get("line") or 0))[:SHOWN_PER_LEG]:
        where = esc(R.loc(d))
        link = (f'<a href="{esc(text_href)}/{esc(urllib.parse.quote(d["file"]))}.txt">{where}</a>'
                if text_href and d.get("file") else f"<code>{where}</code>")
        c = d.get("carrier", "?")
        how = CARRIER_PLAIN.get(c, "mixed invisible characters" if "+" in c else c)
        how += f" ({d['how']})" if d.get("how") else ""
        k = _hidden_key(d)
        rows.append(f'<li class="row"><div class="row-main">{link} <span class="ev-why">{esc(how)}</span></div>'
                    f'{_nc(k, k, "hidden", R.loc(d), how)}</li>')
    if len(div) > SHOWN_PER_LEG:
        rows.append(f'<li class="more">{len(div) - SHOWN_PER_LEG} more in full.md.</li>')
    return f'<ul class="rows">{"".join(rows)}</ul>'


def _instruction_callout(mine, cards) -> str:
    """Hidden, and it reads like an instruction: one yellow box, its count opening the places, each
    linked to its review card, with its box (owner, 2026-10-20)."""
    rows = "".join(_place_row(it, cards) for it in mine)
    return (f'<div class="callout"><h3>Hidden, and it reads like an instruction</h3>'
            f'<details><summary>{esc(R.n(len(mine), "place"))}</summary><ul class="rows">{rows}</ul>'
            f'</details></div>')


def secrets(r, raw, cards=None) -> str:
    lede = "Lines that look like a password, key, or token saved in the files. Values are never shown here."
    allf = [x for x in R.fnd(r, "04-phrases", "secret.found")]
    if "04-phrases" not in r:
        return _section("secrets", "Committed secrets", esc(lede), _empty("Not checked: this run has no stage 4 output."))
    if any("skipped" in x for x in allf):
        return _section("secrets", "Committed secrets", esc(lede),
                        _empty("Not checked: no secret scanner was installed for this run."))
    real = [it for it in raw if it.get("kind") == "secret"]
    test = sum(1 for x in allf if x.get("audience") == "test-data")
    plain = sum(1 for x in allf if x.get("likely_not_secret") and x.get("audience") != "test-data")
    engine = allf[0].get("engine") if allf else None
    aside = []
    if plain:
        aside.append(f"{plain} that look like hashes, variable names, plain words, or local test passwords")
    if test:
        aside.append(f"{test} in test data")
    note = f" Set aside: {'; '.join(aside)}." if aside else ""
    by = f" Checked by {engine}." if engine else ""
    if not real:
        return _section("secrets", "Committed secrets", esc(lede),
                        _empty(f"No lines look like committed secrets.{by}{note}"))
    return _section("secrets", "Committed secrets", esc(lede),
                    _p(f"{R.n(len(real), 'line')} look like committed secrets.{by}{note}")
                    + '<ul class="rows cards">' + "".join(_place_row(it, cards if cards is not None else
                                                                     _cards_by_key(r), note=True)
                                                          for it in real) + "</ul>")


def risky(r, items, model_items, raw=None, cards=None) -> str:
    """`items`: grouped places; `raw`: first_items, for the places under each headline."""
    lede = ("Lines whose wording matches a known risky request, and the places picked by fixed rules. "
            "Each is a place to read; being listed does not mean something is wrong.")
    if "04-phrases" not in r:
        return _section("risky", "Risky asks and things to check", esc(lede),
                        _empty("Not checked: this run has no stage 4 output."))
    hits = R.phrase_hits(r)
    aud = {}
    for h in hits:
        aud.setdefault((h.get("file"), h.get("line")), h.get("audience"))
    lines = []
    if hits:
        where = collections.Counter(READ_BY.get(a, "the AI") for a in aud.values())
        lines.append(f"{_count(len(aud), 'line')} match the wording of a risky request. Who reads them: "
                     + ", ".join(f"{k} {where[k]:,}" for k in dict.fromkeys(READ_BY.values())
                                 if where[k]) + ".")
        by = collections.Counter(h["check"] for h in hits)
        lines.append("By kind: " + "; ".join(f"{GROUP_PLAIN[g]} {sum(by[c] for c in cs):,}"
                                             for g, cs in R.SUBGROUPS.items()) + ".")
    labels = [x for x in R.fnd(r, "06-soft", "soft.label") if "skipped" not in x and x.get("label")]
    if labels:
        do = sum(1 for x in labels if x["label"] == "do")
        lines.append(f"A second opinion ({labels[0].get('backend')}) read {do} of the {len(labels)} lines "
                     "the AI reads as a real instruction to do the flagged thing, and the rest as "
                     "something else (a description, a quote, or the words in another sense). Such a "
                     "read says a line tells the AI to do it; it does not say doing it is harmful.")
    rub = R.fnd(r, "04-phrases", "rubric.action")
    if rub:
        unconf = sum(1 for x in rub if not x.get("confirmation") and not x.get("negated_action"))
        forbid = sum(1 for x in rub if x.get("negated_action"))
        lines.append(f"Actions that should ask you first (sending, publishing, paying, entering passwords): "
                     f"{len(rub)} in text the AI follows, {unconf} with no step asking you"
                     + (f", {forbid} where the text forbids the action" if forbid else "") + ".")
    lim = R.fnd(r, "05-capability", "cap.limit")
    if lim:  # review C32
        st = collections.Counter(x.get("status") for x in lim)
        lines.append(f"Read-only wording the AI follows: {_count(len(lim), 'line')}; {st['backed']} backed by a "
                     f"tool setting, {st['stated']} stated in the text only, {st['contradicted']} where the "
                     "owner's tools list can write. A static read cannot see whether a setting is used at run "
                     "time.")
    body = "".join(_p(x) for x in lines) if lines else _empty("No line matches the wording of a risky request.")
    listed = [it for it in items if it.get("kind") not in OWN_SECTIONS]
    if listed:
        raw = first_items(r) if raw is None else raw
        cards = _cards_by_key(r) if cards is None else cards
        lis = ""
        for it in listed:
            mine = [x for x in raw if (x["stage"], x["title"]) == (it["stage"], it["title"])]
            nt = f'<p class="note">{esc((it.get("lead") or "") + it["note"])}</p>' if it.get("note") else ""
            lis += (f'<li><details class="rows"><summary>{esc(it["title"])} <span class="count">'
                    f'{R.n(len(it["wheres"]), "place")}</span></summary>{nt}<ul class="rows">'
                    f'{"".join(_place_row(x, cards) for x in mine)}</ul></details></li>')
        body += f'<h3>Things to check</h3><ul class="checks">{lis}</ul>'
    else:
        body += _empty("Nothing to check: no place met the rules.")
    if model_items:
        n = sum(len(it["wheres"]) for it in model_items)
        body += (f'<p class="note">Plus {R.n(n, "model read")} (optional, experimental), on the review page. '
                 f'Measured accuracy: <a href="{ACCURACY_URL}">MODEL-ACCURACY</a>.</p>')
    if items or model_items:
        body += ('<p class="review-link"><a href="review.html">Walk through every place one at a time</a>, '
                 'with the lines around it, and mark each one Concerned, Not concerned, or Not sure.</p>')
    return _section("risky", "Risky asks and things to check", esc(lede), body)


def changes(ch) -> str:
    """When an earlier run of the same repository is a different version, or the same version and
    Walkdown changed since (review C22 b, 2026-10-19); a re-run with nothing different says nothing."""
    if not ch or (ch.get("same") and not ch.get("differs")):
        return ""
    lead = ""
    if ch.get("same") and not ch.get("on_disk"):
        lead = _p("Same version of the repository as that run. Walkdown changed since then, so every "
                  "difference here comes from Walkdown.")
    elif ch.get("same"):  # same commit, but files differ on disk (2026-10-20)
        lead = _p("Same commit of the repository as that run, but some files differ on disk. "
                  "Differences in the other files come from Walkdown.")
    body = (lead + "".join(_p(x[:1].upper() + x[1:] + ("" if x.endswith(".") else ".")) for x in ch.get("lines", []))
            + '<p class="note">Every change, file by file: <a href="changes.md">changes.md</a>.</p>')
    return _section("changes", f"Changes since run {ch['since']}", "", body)


def recs(r) -> str:
    rs = R.recommendations(r)
    body = (f'<ul class="recs">{"".join(f"<li>{esc(x)}</li>" for x in rs)}</ul>' if rs
            else _empty("None: no finding matched a recommendation."))
    return _section("recs", f"Recommendations ({len(rs)})",
                    "Changes to consider. Each depends on what the skill is for. Unranked.", body)


def other(r, stamps, notes, runs_ok) -> str:
    skipped, idle = R.glance(r, notes, stamps, runs_ok)
    lim = R.limits(r, notes, stamps, runs_ok)
    todo = [x[:-len(NOT_BUILT)] for x in skipped if x.endswith(NOT_BUILT)]
    rest = [x for x in skipped if not x.endswith(NOT_BUILT)]
    parts = ['<h3>What was not checked</h3>',
             _p(f"{R.n(len(skipped), 'check')} that apply to this repository did not run. A clean result "
                "says nothing about these.")]
    if todo:
        parts.append(_p(f"Not built yet: {'; '.join(todo)}."))
    if rest:
        parts.append(_p(f"Skipped in this run: {'; '.join(rest)}."))
    if idle:
        parts.append(_p(f"Not needed here: {'; '.join(idle)}."))
    parts.append(f"<details><summary>Every limit, including those of every run ({len(lim)})</summary>"
                 f"<ul class=\"lims\">{''.join(f'<li>{esc(x)}</li>' for x in lim)}</ul></details>")
    parts.append('<h3>Fixture results</h3>'
                 '<p>Before a run is trusted, each step is run on small test repositories with known '
                 'contents and scored against an answer sheet it never reads.</p>')
    rows = []
    bad = 0
    for st in R.ORDER:
        if st == "07-limits" or st not in r:  # a step this run did not include has no result
            continue
        s = stamps.get(st)
        text = s.text if s else "not validated"
        if s is None or s.result != "PASS":
            bad += 1
        rows.append(f'<li><span>{esc(PLAIN_STAGE[st])}</span><code>{esc(text)}</code></li>')
    parts.append(f'<ul class="stamps">{"".join(rows)}</ul>')
    parts.append('<p>Every finding, with file and line, is in <code>full.md</code> next to this page.</p>')
    flag = f' <span class="pill">{R.n(bad, "step")} not passed</span>' if bad else ""
    return (f'<section class="block" id="other"><details class="fold big"><summary><h2>Other details{flag}</h2>'
            f'</summary>{"".join(parts)}</details></section>')


# Review C29 (owner, 2026-10-20): for someone deciding whether to use the repository. The places
# to check, grouped by what they could lead to, in a fixed order (the review page keeps every card
# for the author); and the questions the findings raise before use. Neither is a verdict or a
# score, and neither ranks one place above another inside a group.
ACTION_GROUPS = (
    ("runs", "Runs code", "Commands that run on their own, or that you are asked to run."),
    ("out", "Reads secrets, calls out, or shares", "Credentials, network calls, and data sent elsewhere."),
    ("lasting", "Lasting changes or permissions",
     "Settings, profiles, permissions, and actions that are hard to undo."),
    ("words", "Wording only", "Instructions that change how the AI reads, decides, or answers."),
)
CHECK_GROUP = {"phrase.G.human": "runs", "phrase.K.exfil": "out", "phrase.creds": "out",
               "phrase.remote-load": "out", "phrase.E.perms": "lasting", "phrase.E.env": "lasting",
               "phrase.C.second-order": "lasting", "phrase.J.prohibited": "lasting"}
KIND_GROUP = {"hook": "runs", "hook+phrase": "runs", "secret": "out", "rubric.prohibited": "lasting",
              "rubric.redefined": "lasting", "limit.contradicted": "lasting"}
TOOL_ASKS = ((("Bash",), "a shell"), (("Write", "Edit", "MultiEdit", "NotebookEdit"), "to write files"),
             (("WebFetch", "WebSearch"), "the web"))


def action_group(it) -> str:
    """Which of ACTION_GROUPS an item falls in: by its kind, else by the phrase check behind it."""
    if it.get("kind") in KIND_GROUP:
        return KIND_GROUP[it["kind"]]
    src = it.get("src") or {}
    check = src.get("check") if str(src.get("check", "")).startswith("phrase.") else src.get("phrase_check")
    return CHECK_GROUP.get(check, "words")


def _part(where: str) -> str:
    """The part of the repository a place belongs to: skills/<name>, agents/<file>, or the top folder."""
    path = where.split(" (")[0].rsplit(":", 1)[0] if ":" in where.split(" (")[0] else where.split(" (")[0]
    parts = path.split("/")
    if parts[0] in ("skills", "agents", "commands", "plugins") and len(parts) > 2:
        return "/".join(parts[:2])
    return parts[0] if len(parts) > 1 else path


def _tool_names(a) -> set:
    return {str(t).split("(")[0].strip() for t in a.get("tools") or []}


def before_use(r, places) -> str:
    """Questions the findings raise for someone deciding whether to use the repository (C29).
    `places`: first_items without the model reads, one per place."""
    own = lambda xs: [x for x in xs if not R.is_test_data(x.get("file"))]  # noqa: E731
    agents = own(R.fnd(r, "01-inventory", "struct.agent-tools"))
    hooks = own(R.fnd(r, "01-inventory", "struct.hooks"))
    mcp = own(R.fnd(r, "01-inventory", "struct.mcp"))
    hold = []
    inherit = [a for a in agents if not a.get("tools")]
    if inherit:
        hold.append(f"Should its {R.n(len(inherit), 'agent or command definition')} with no tools list "
                    "get every tool you have? With no list, each can use all of them (capability only).")
    for tools, what in TOOL_ASKS:
        who = sorted({a["file"] for a in agents if _tool_names(a) & set(tools)})
        if who:
            hold.append(f"Does it need {what}? Listed for {R.n(len(who), 'definition')}: {_files(who)}.")
    if hooks:
        events = sorted({str(h.get("event")) for h in hooks})
        hold.append(f"Do you want its {R.n(len(hooks), 'hook')} to run on "
                    f"{'its' if len(hooks) == 1 else 'their'} own ({', '.join(events)})?")
    if mcp:
        names = sorted({str(m.get("name")) for m in mcp})
        hold.append(f"Do you want to connect its MCP servers ({_files(names)})?")
    per = collections.Counter(_part(it["where"]) for it in places
                              if not R.is_test_data((it.get("src") or {}).get("file") or it["where"]))
    first = []
    if per:
        top = per.most_common(3)
        first.append("Which part will you try first? The parts with the most places to check: "
                      + ", ".join(f"{p} ({c})" for p, c in top) + ".")
    g = collections.Counter(action_group(it) for it in places)
    left = []
    if g["runs"] or g["lasting"]:
        left.append(f"Which of the {R.n(g['runs'] + g['lasting'], 'place')} that run code or make lasting "
                    "changes have you read?")
    skip = [h for h in R.phrase_hits(r) if "L.skip-confirm" in (h.get("patterns") or [])
            and h.get("audience") in ("model", "subagent") and not h.get("negated")]
    if skip:
        left.append(f"{R.n(len(skip), 'line')} {'tells' if len(skip) == 1 else 'tell'} the AI it need not "
                    "ask before acting. Is that what "
                    "you want when you are not watching?")
    kinds = collections.Counter(it.get("kind") for it in places)
    if kinds["limit.contradicted"]:
        left.append(f"{R.n(kinds['limit.contradicted'], 'line')} "
                    f"{'says' if kinds['limit.contradicted'] == 1 else 'say'} read-only in a part whose tools "
                    "list can write. Does it write?")
    if kinds["hidden+phrase"]:
        left.append(f"What is the hidden text that reads like an instruction for "
                    f"({R.n(kinds['hidden+phrase'], 'place')})?")
    if kinds["secret"]:
        left.append(f"Are the {R.n(kinds['secret'], 'value')} that look like committed secrets real, "
                    "and still live?")
    blocks = [(t, qs) for t, qs in (("Permissions to hold back", hold), ("What to try first", first),
                                    ("Before you leave it running unattended", left)) if qs]
    body = ("".join(f"<h3>{esc(t)}</h3><ul>" + "".join(f"<li>{esc(q)}</li>" for q in qs) + "</ul>"
                    for t, qs in blocks) if blocks else _p("No questions from these findings."))
    lede = (esc("These are the questions the findings raise for someone deciding whether to use this "
                "repository. The answers, and what to do about them, are yours.") if blocks else "")
    return _section("beforeuse", "Questions before use", lede, body)  # owner, 2026-10-20


def render_page(meta, r, stamps, notes, runs_ok, changes_since=None, cap_full=None,
                text_href=None, marks=None, carried=None) -> str:
    """`cap_full`: stage 5 with every citation (capability.json), for the places under each box;
    `text_href`: the run's normalized text folder relative to this page, for file links;
    `marks`, `carried`: the run's marks from marks.for_run."""
    raw = first_items(r)
    every = grouped(raw)
    items = [it for it in every if it["stage"] != 6]
    model_items = [it for it in every if it["stage"] == 6]
    cards = _cards_by_key(r)
    body = [header(meta, r), marks_bar(r, cap_full, marks, carried), trifecta(r, cap_full, text_href), stats(r),
            links(r), hidden(r, raw, cards, text_href), secrets(r, raw, cards),
            risky(r, items, model_items, raw, cards),  # First pass and the questions are on summary.html now
            changes(changes_since), recs(r), other(r, stamps, notes, runs_ok),
            f'<footer><p>{esc(R.NOT_WHAT)}</p></footer>']
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            f"<title>{esc('Walkdown: ' + meta['repo'])}</title>\n" + FONTS + f"<style>{CSS}</style>\n</head>\n"
            f'<body class="no-js">\n<main class="wrap" data-repo="{esc(meta["repo"])}" data-run="{esc(meta.get("run", ""))}" '
            f'data-hash="{esc(meta.get("hash", ""))}">\n{"".join(body)}\n</main>\n<script>{JS}</script>\n</body>\n</html>\n')


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700'
         '&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap">\n')

JS = """
document.addEventListener('click', function (e) {
  var b = e.target.closest && e.target.closest('button.copy');
  if (!b) return;
  var u = b.getAttribute('data-url');
  function done() { b.textContent = 'Copied'; setTimeout(function () { b.textContent = 'Copy'; }, 1500); }
  function fallback() {
    var t = document.createElement('textarea'); t.value = u; document.body.appendChild(t); t.select();
    try { document.execCommand('copy'); done(); } catch (x) {}
    t.remove();
  }
  if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(u).then(done, fallback);
  else fallback();
});
(function () {
  "use strict";
  // Not concerned boxes (owner, 2026-10-20). Marks are kept in this browser as they are made and
  // leave as marks.json; the page builds no markup from repository text.
  var body = document.body, main = document.querySelector("main");
  var $ = function (id) { return document.getElementById(id); };
  var boxes = Array.prototype.slice.call(document.querySelectorAll(".ncbox"));
  if (!$("nc-saved")) return;
  body.classList.remove("no-js");
  var RUN = main.dataset.run, STORE = "walkdown-details:" + main.dataset.repo + ":" + RUN;
  var OTHER = {"concerned": "Marked Concerned", "not-sure": "Marked Not sure"};
  var marks = {}, rows = {};
  try { marks = JSON.parse($("nc-saved").textContent) || {}; } catch (e) { marks = {}; }
  try { rows = JSON.parse($("nc-rows").textContent) || {}; } catch (e) { rows = {}; }
  try { var mine = JSON.parse(localStorage.getItem(STORE) || "{}");
    Object.keys(mine).forEach(function (k) { marks[k] = mine[k]; }); } catch (e) {}
  function out() {
    var list = [];
    Object.keys(marks).forEach(function (row) {
      var m = marks[row];
      if (!m || (!m.mark && !m.note)) return;
      list.push({key: m.key, id: m.id || null, kind: m.kind || "place", where: m.where || "", headline: m.headline || "",
                 mark: m.mark || null, note: m.note || "", from: m.from || RUN});
    });
    return JSON.stringify({walkdown_marks: 2, repo: main.dataset.repo, run: RUN, pinned: main.dataset.hash,
      saved: new Date().toISOString().slice(0, 10), marks: list}, null, 1);
  }
  function paint() {
    var seen = {};
    boxes.forEach(function (b) {
      var m = marks[b.dataset.row], nc = !!m && m.mark === "not-concerned";
      b.checked = nc;
      var row = b.closest(".row, tr"); if (row) row.classList.toggle("is-nc", nc);
      var t = m && OTHER[m.mark] ? OTHER[m.mark] : "";
      if (m && m.mark && m.from && m.from !== RUN) t += (t ? ", " : "") + "from run " + m.from;
      b.parentNode.nextElementSibling.textContent = t;
      if (nc) seen[b.dataset.row] = 1;
    });
    document.querySelectorAll("main > section").forEach(function (s) {
      var k = {}, h = s.querySelector("h2");
      s.querySelectorAll(".ncbox").forEach(function (b) { if (b.checked) k[b.dataset.row] = 1; });
      if (!h) return;
      var sp = h.querySelector(".nc-n");
      if (!sp) { sp = document.createElement("span"); sp.className = "nc-n"; h.appendChild(sp); }
      var n = Object.keys(k).length;
      sp.textContent = n ? n + " marked Not concerned" : "";
    });
    var n = Object.keys(seen).length;
    $("nc-total").textContent = n ? n + (n === 1 ? " row" : " rows") + " marked so far." : "";
  }
  function save() { try { localStorage.setItem(STORE, JSON.stringify(marks)); } catch (e) {} }
  boxes.forEach(function (b) {
    b.addEventListener("change", function () {
      var id = b.dataset.row, m = marks[id];
      if (b.checked) {
        marks[id] = {key: (m && m.key) || b.dataset.key, id: (m && m.id) || (b.dataset.kind === "place" && id !== b.dataset.key ? id : null),
                     kind: b.dataset.kind, where: (m && m.where) || b.dataset.where, headline: (m && m.headline) || b.dataset.headline,
                     mark: "not-concerned", note: (m && m.note) || "", from: RUN};
      } else if (m) {
        m.mark = null; m.from = RUN;
        if (!m.note) delete marks[id];
      }
      save(); paint();
    });
  });
  $("hide-nc").onchange = function (e) { body.classList.toggle("hide-nc", e.target.checked); };
  $("nc-dl").onclick = function () {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([out()], {type: "application/json"}));
    a.download = "marks.json"; a.click(); $("nc-msg").textContent = "Downloaded. Save it in this run folder as marks.json.";
  };
  $("nc-load").onchange = function (e) {
    var f = e.target.files[0]; if (!f) return; var rd = new FileReader();
    rd.onload = function () {
      var n = 0, stray = 0, ids = {};
      Object.keys(rows).forEach(function (k) { ids[rows[k]] = 1; });
      try {
        (JSON.parse(rd.result).marks || []).forEach(function (m) {
          var id = m && (rows[m.key] || (ids[m.id] ? m.id : null));
          if (!id) { stray++; return; }
          marks[id] = {key: m.key, id: m.id || null, kind: m.kind || "place", where: m.where || "", headline: m.headline || "",
                       mark: ["concerned", "not-concerned", "not-sure"].indexOf(m.mark) >= 0 ? m.mark : null,
                       note: typeof m.note === "string" ? m.note : "", from: typeof m.from === "string" ? m.from : null};
          n++;
        });
        save(); paint(); $("nc-msg").textContent = "Loaded " + n + " marks" + (stray ? "; " + stray + " match nothing here." : ".");
      } catch (err) { $("nc-msg").textContent = "That file is not a marks file."; }
    };
    rd.readAsText(f);
  };
  paint();
})();
"""

CSS = """
:root {
  --paper: #f5f7f8; --sheet: #ffffff; --ink: #17222e; --muted: #5a6875; --rule: #d8dee4;
  --accent: #1d6a86; --flag: #9a5b00; --flag-bg: #fdf3e4; --quote-bg: #eef2f5;
  --leg-1: #2f7d46; --leg-2: #d9a40b; --leg-3: #b42318; --leg-mark: #ffffff; --leg-2-mark: #17222e;
  --display: "Archivo", "Arial Narrow", Arial, sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", Consolas, "Courier New", monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833;
  --leg-1: #6cc488; --leg-2: #e8c14a; --leg-3: #f2776b; --leg-mark: #0f151b; --leg-2-mark: #0f151b; color-scheme: dark; } }
:root[data-theme="dark"] {
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833;
  --leg-1: #6cc488; --leg-2: #e8c14a; --leg-3: #f2776b; --leg-mark: #0f151b; --leg-2-mark: #0f151b; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font: 17px/1.55 var(--body); }
.wrap { max-width: 58rem; margin: 0 auto; padding-inline: 16px; padding-block: 2rem 4rem; display: grid; gap: 1.6rem; }
header.card, .block { background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; padding: 1.2rem 1.4rem; min-width: 0; }
header.card { padding: 1.4rem 1.6rem 1.2rem; }
.top { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: .4rem 1.2rem; }
.pagelink { font: 600 .88rem/1.2 var(--body); color: var(--accent); text-decoration: none; border: 1px solid var(--rule); border-radius: 999px; padding: .35rem .75rem; white-space: nowrap; }
.pagelink:hover, .pagelink:focus-visible { border-color: var(--accent); }
h1 { font: 700 clamp(1.9rem, 4vw, 2.6rem)/1.1 var(--display); margin: .3rem 0 .6rem; text-wrap: balance; overflow-wrap: anywhere; }
.h1-lead { color: var(--muted); font-weight: 500; }
.license { margin: .7rem 0 0; color: var(--ink); max-width: 72ch; overflow-wrap: anywhere; }
.meta { font: .82rem/1.5 var(--mono); color: var(--muted); display: flex; flex-wrap: wrap; gap: .3rem 1.2rem; overflow-wrap: anywhere; }
h2 { font: 700 1.35rem/1.2 var(--display); margin: 0 0 .7rem; }
h3 { font: 600 1.02rem/1.3 var(--body); margin: 1.1rem 0 .5rem; }
.lede { color: var(--muted); margin: -.3rem 0 .9rem; max-width: 68ch; }
.headline { font-weight: 600; margin: 0 0 .6rem; }
.block p { margin: .35rem 0; max-width: 72ch; overflow-wrap: anywhere; }
.empty { color: var(--muted); font-style: italic; }
.note { color: var(--muted); }
.questioned { color: var(--muted); border-left: 3px solid var(--muted); padding-left: .6rem; }
.count { font: 400 .85rem var(--body); color: var(--muted); }
ol, ul { margin: 0; padding: 0; list-style: none; }
details summary { cursor: pointer; color: var(--accent); font-weight: 600; }
details summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
details.fold > summary { margin: .4rem 0; }
details.fold[open] > summary { margin-bottom: .6rem; }
details.big > summary { list-style: none; display: flex; gap: .5rem; align-items: baseline; }
details.big > summary::-webkit-details-marker { display: none; }
details.big > summary::before { content: "\\25B8"; color: var(--accent); }
details.big[open] > summary::before { content: "\\25BE"; }
details.big > summary h2 { margin: 0; color: var(--ink); display: flex; gap: .6rem; align-items: center; flex-wrap: wrap; }
.facts p { font-size: .92rem; color: var(--muted); }
.legs { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.1rem; }
.leg { display: grid; grid-template-columns: 1.6rem minmax(0, 1fr); gap: .6rem; align-items: start; }
.box svg { width: 1.5rem; height: 1.5rem; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }
.leg.on .box svg rect { fill: var(--leg-1); stroke: var(--leg-1); }
.leg.on .box svg path { stroke: var(--leg-mark); stroke-width: 2.4; }
.leg.on[data-n="2"] .box svg rect { fill: var(--leg-2); stroke: var(--leg-2); }
.leg.on[data-n="2"] .box svg path { stroke: var(--leg-2-mark); }
.leg.on[data-n="3"] .box svg rect { fill: var(--leg-3); stroke: var(--leg-3); }
.leg.off .box svg rect { stroke: var(--muted); }
.leg-name { font: 600 1.05rem/1.3 var(--body); }
.leg.off .leg-name { color: var(--muted); }
.leg-def { font-size: .88rem; color: var(--muted); margin-top: .15rem; }
.hl { font-weight: 600; margin: .2rem 0 .6rem; }
.callout { background: var(--flag-bg); border-left: 4px solid var(--leg-2); border-radius: 6px; padding: .7rem .9rem; margin: .4rem 0 .8rem; }
.callout h3 { margin: 0 0 .3rem; font-size: 1rem; }
.callout summary { cursor: pointer; font-weight: 600; color: var(--accent); }
.callout ul { list-style: none; margin: .4rem 0 0; padding: 0; }
.callout li { margin: .4rem 0; overflow-wrap: anywhere; }
.callout li a, .callout li code { font: .8rem/1.4 var(--mono); }
.hidden-more { margin: .4rem 0 0; padding-left: 1.2rem; list-style: disc; }
.hidden-more li { margin: .25rem 0; }
details.leg-ev { margin-top: .35rem; font-size: .88rem; }
details.leg-ev summary { cursor: pointer; font-weight: 600; color: var(--accent); }
details.leg-ev ul { list-style: none; margin: .35rem 0 0; padding: 0; max-height: 16rem; overflow: auto; }
details.leg-ev li { padding: .15rem 0; overflow-wrap: anywhere; }
details.leg-ev li a, details.leg-ev li code { font: .78rem/1.4 var(--mono); }
.ev-why { color: var(--muted); }
.leg .grants { margin-top: .5rem; }
.leg-foot { margin: 1rem 0 0; padding-top: .8rem; border-top: 1px solid var(--rule); color: var(--muted); font-size: .92rem; }
.gets-in { margin-top: .4rem; }
.grants { display: grid; gap: .45rem; }
.grants li { display: grid; gap: .1rem; padding-left: 1rem; border-left: 3px solid var(--flag); }
.g-name { font-weight: 600; }
.g-detail { font: .8rem/1.45 var(--mono); color: var(--muted); overflow-wrap: anywhere; }
.g-none { color: var(--muted); font-size: .9rem; }
.callout { background: var(--flag-bg); border-radius: 4px; padding: .7rem 1rem; margin: .6rem 0; }
.callout h3 { margin: 0 0 .4rem; color: var(--flag); }
.callout li { padding: .25rem 0; }
.where { display: block; margin-top: .25rem; font: .8rem/1.4 var(--mono); color: var(--accent); overflow-wrap: anywhere; }
.cards { display: grid; gap: .7rem; }
.item { border: 1px solid var(--rule); border-left: 4px solid var(--flag); border-radius: 4px; padding: .8rem 1rem; min-width: 0; }
.item h3 { margin: 0; }
.quote { margin: .5rem 0 0; padding: .55rem .8rem; background: var(--quote-bg); border-radius: 3px; font: .82rem/1.5 var(--mono); white-space: pre-wrap; overflow-wrap: anywhere; max-height: 9rem; overflow: auto; }
.more { color: var(--muted); }
.tablewrap { overflow-x: auto; }
table.links { width: 100%; border-collapse: collapse; font-size: .85rem; }
table.links th, table.links td { text-align: left; padding: .35rem .5rem; border-bottom: 1px solid var(--rule); vertical-align: top; }
table.links thead th { font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
table.links tr.dom th { background: var(--quote-bg); font: 600 .9rem var(--mono); }
td.url { display: flex; gap: .5rem; align-items: baseline; }
td.url code, td.loc code { font: .8rem/1.4 var(--mono); overflow-wrap: anywhere; }
td.who { white-space: nowrap; color: var(--muted); }
button.copy { font: 600 .72rem/1 var(--body); color: var(--accent); background: none; border: 1px solid var(--rule); border-radius: 999px; padding: .2rem .5rem; cursor: pointer; flex-shrink: 0; }
button.copy:hover, button.copy:focus-visible { border-color: var(--accent); }
.checks li { padding: .3rem 0; border-bottom: 1px solid var(--rule); }
.review-link { margin-top: .9rem; }
.review-link a { color: var(--accent); font-weight: 600; }
.recs li { padding: .55rem 0; border-bottom: 1px solid var(--rule); max-width: 75ch; overflow-wrap: anywhere; }
.lims { list-style: disc; padding-left: 1.2rem; font-size: .88rem; color: var(--muted); }
.stamps li { display: flex; justify-content: space-between; gap: 1rem; flex-wrap: wrap; padding: .3rem 0; border-bottom: 1px solid var(--rule); }
.stamps code { font: .78rem var(--mono); color: var(--muted); }
.pill { font: 600 .7rem/1 var(--body); letter-spacing: .06em; text-transform: uppercase; color: var(--flag); border: 1px solid var(--flag); border-radius: 999px; padding: .25rem .5rem; }
footer { border-top: 2px solid var(--ink); padding-top: 1rem; color: var(--muted); max-width: 70ch; }
.marksbar { background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; padding: .8rem 1.4rem; }
.marksbar p { margin: .3rem 0; max-width: 72ch; }
.marksbar .nav { display: flex; flex-wrap: wrap; gap: .5rem 1rem; align-items: center; margin: .4rem 0; }
.marksbar button, .file-l { font: 600 .85rem/1.2 var(--body); color: var(--accent); background: none; border: 1px solid var(--rule); border-radius: 999px; padding: .35rem .75rem; cursor: pointer; }
.file-l input { display: none; }
.hide-l { font-size: .9rem; display: inline-flex; gap: .35rem; align-items: center; }
.no-js .marksbar, .no-js .nc, .no-js .nc-c, .no-js .nc-tag { display: none; }
ul.rows { display: grid; gap: .1rem; margin: .3rem 0 0; }
.row { display: flex; flex-wrap: wrap; gap: .2rem .8rem; align-items: baseline; justify-content: space-between; padding: .25rem 0; border-bottom: 1px solid var(--rule); }
.row:last-child { border-bottom: 0; }
.row-main { flex: 1 1 16rem; min-width: 0; overflow-wrap: anywhere; }
.row-main a, .row-main code { font: .8rem/1.4 var(--mono); }
.row-main .quote { margin: .25rem 0 0; }
.nc { font-size: .8rem; color: var(--muted); display: inline-flex; gap: .3rem; align-items: center; white-space: nowrap; cursor: pointer; }
.nc input { accent-color: var(--accent); margin: 0; }
.nc-tag { font-size: .78rem; color: var(--muted); }
.nc-tag:empty { display: none; }
.is-nc .row-main, tr.is-nc td:not(.nc-c) { opacity: .5; }
.hide-nc .is-nc { display: none; }
.nc-n { font: 400 .85rem var(--body); color: var(--muted); margin-left: .6rem; }
.nc-n:empty { display: none; }
td.nc-c { white-space: nowrap; text-align: center; }
th.nc-h { width: 5.5rem; }
td.loc { min-width: 8.5rem; }
td.nc-c .nc-tag { display: block; white-space: normal; }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
details.rows > summary { margin: .3rem 0; }
.checks details.rows > summary { color: var(--ink); font-weight: 400; }
details.leg-ev .row { display: block; }
details.leg-ev .nc { margin-top: .1rem; }
details.hl > summary { color: var(--ink); }
@media (max-width: 640px) { .legs { grid-template-columns: 1fr; } header.card, .block { padding: 1rem; } td.who { white-space: normal; } .marksbar { padding: .8rem 1rem; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""
