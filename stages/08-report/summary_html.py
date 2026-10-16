"""The summary page, report v2 (owner redesign, 2026-10-16). Spec: specs/summary_html.SPEC.md.

Built around a reader's questions, in the owner's order: what it is, the lethal trifecta and how
it gets in, the files (collapsed), outside links, hidden text, committed secrets, risky asks and
things to check, changes since the last run, recommendations, other details (collapsed). Same
facts as before, from render.py's fixed rules; nothing here detects or judges. Report v1 is kept
frozen as summary_v1_html.py (git tag report-v1) while v2 settles.
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


def _wheres(ws) -> str:
    uniq = list(dict.fromkeys(ws))
    return "  ·  ".join(uniq[:4]) + (f"  ·  +{len(uniq) - 4} more" if len(uniq) > 4 else "")


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


def _cards(items) -> str:
    out = []
    for it in items[:MAX_FIRST]:
        quotes = "\n".join(it["quotes"][:6])
        q = f'<pre class="quote">{esc(quotes)}</pre>' if quotes else ""
        nt = f'<p class="note">{esc((it.get("lead") or "") + it["note"])}</p>' if it.get("note") else ""
        places = len(it["wheres"])
        count = f' <span class="count">{places} places</span>' if places > 1 else ""
        out.append(f'<li class="item"><h3>{esc(it["title"])}{count}</h3>'
                   f'<code class="where">{esc(_wheres(it["wheres"]))}</code>{q}{nt}</li>')
    if len(items) > MAX_FIRST:
        out.append(f'<li class="more">{len(items) - MAX_FIRST} more on the review page.</li>')
    return f'<ol class="cards">{"".join(out)}</ol>'


def header(meta) -> str:
    bits = [meta.get("source", ""), f"{meta.get('hash_kind', '?')} {str(meta.get('hash', ''))[:12]}",
            f"retrieved {meta.get('date', '')}", f"run {meta.get('run', '')}"]
    if meta.get("tool"):
        bits.append(f"Walkdown {meta['tool']}")
    return ('<header class="card"><div class="top"><a class="pagelink" href="review.html">'
            'Review each place →</a></div>'
            f'<h1><span class="h1-lead">Walkdown report on</span> {esc(meta["repo"])}</h1>'
            f'<div class="meta">{"".join(f"<span>{esc(b)}</span>" for b in bits if b)}</div></header>')


def trifecta(r) -> str:
    """The three legs as a checklist, checked first and colored by position (owner, 2026-10-12),
    each with how many places back it; then how it gets in: grants and what loads on its own."""
    legs = {x["leg"]: x for x in R.fnd(r, "05-capability", "cap.leg")}
    on = {k: bool(legs.get(k, {}).get("present")) for k in R.LEG_NAMES}
    marked = R.all_marked_legs(r)
    order = [k for k in R.LEG_NAMES if on[k]] + [k for k in R.LEG_NAMES if not on[k]]
    rows = []
    for i, k in enumerate(order, 1):
        x = legs.get(k, {})
        n = x.get("evidence_total", len(x.get("evidence") or []))
        backing = f'<div class="leg-n">{R.n(n, "place")} in the files</div>' if on[k] and n else ""
        mk = ('<div class="leg-def">Every line cited for this was read by a model as not an '
              'instruction. The box stays checked; see 5 in the full report.</div>'
              if on[k] and k in marked else "")
        data_n = f' data-n="{i}"' if on[k] else ""
        rows.append(f'<li class="leg {"on" if on[k] else "off"}"{data_n}><span class="box" role="img" '
                    f'aria-label="{"yes" if on[k] else "no"}">{CHECK if on[k] else BOX}</span>'
                    f'<div><div class="leg-name">{esc(R.LEG_NAMES[k])}</div>'
                    f'<div class="leg-def">{esc(R.LEG_DEFS[k])}</div>{backing}{mk}</div></li>')
    n_on = sum(on.values())
    foot = R.TRIFECTA_ALL if n_on == 3 else R.TRIFECTA_SOME.format(n=n_on)
    return (f'<section class="trifecta block" id="trifecta"><h2>The lethal trifecta</h2>'
            f'<p class="lede">{esc(TRIFECTA_LEDE)}</p><ul class="legs">{"".join(rows)}</ul>'
            f'<p class="leg-foot">{esc(foot)}</p>{gets_in(r)}</section>')


def gets_in(r) -> str:
    """What installing it allows, and what loads on its own, in plain words."""
    grants = {g["grant"]: g for g in R.fnd(r, "05-capability", "cap.grant")}
    hooks = [h for h in R.fnd(r, "01-inventory", "struct.hooks") if not R.is_test_data(h.get("file"))]
    mcp = [m for m in R.fnd(r, "01-inventory", "struct.mcp") if not R.is_test_data(m.get("file"))]
    agents = [a for a in R.fnd(r, "01-inventory", "struct.agent-tools") if not R.is_test_data(a.get("file"))]
    have, lack = [], []

    def row(name, detail, present):
        (have if present else lack).append((name, detail))

    row("Runs commands on its own",
        [f"{h.get('event')}: {h.get('command')} ({h['file']})" for h in hooks[:4]]
        + ([f"+{len(hooks) - 4} more"] if len(hooks) > 4 else []),
        bool(hooks) or "exec-at-load" in grants)
    desc = [i for i in R.fnd(r, "05-capability", "cap.injection") if i.get("mechanism") == "description"]
    per = [x for x in R.fnd(r, "05-capability", "cap.load-bytes") if x.get("file") and x.get("bytes") is not None]
    inj = f"{sum(i.get('bytes') or 0 for i in desc):,} bytes of descriptions" if desc else ""
    if per:
        inj += (", " if inj else "") + f"about {max(x['bytes'] for x in per):,} bytes with the startup hook"
    row("Adds text to the AI's context before you type", inj, "context-injection" in grants)
    for g, name in (("persistence", "Makes changes that last after the session"),
                    ("network", "Uses the network"),
                    ("elevated", "Asks for more permissions than the default")):
        x = grants.get(g, {})
        row(name, R.n(x.get("evidence_total", len(x.get("evidence") or [])), "place") if x else "", g in grants)
    row("Connects to outside services (MCP servers)",
        ", ".join(m.get("name") or "?" for m in mcp), bool(mcp))
    inherit = [a for a in agents if not a.get("tools")]
    row("Agents with their own tools",
        f"{R.n(len(agents), 'agent or command definition')}"
        + (f", {len(inherit)} with no tools list (they can use every tool the AI has)" if inherit else ""),
        bool(agents))
    lis = "".join(f'<li><span class="g-name">{esc(n)}</span>'
                  + "".join(f'<span class="g-detail">{esc(x)}</span>'
                            for x in ([d] if isinstance(d, str) else d) if x) + "</li>" for n, d in have)
    body = f'<ul class="grants">{lis}</ul>' if have else _empty("Nothing beyond its files: it loads nothing on its own.")
    if lack:
        body += f'<p class="g-none">Not found: {esc(", ".join(n[:1].lower() + n[1:] for n, _ in lack))}.</p>'
    return f'<div class="gets-in"><h3>How it gets in</h3>{body}</div>'


def file_concerns(r) -> list[tuple[str, list[str]]]:
    """What in the files is worth a look, shown above the collapsed stats: (plain line, files)."""
    census = R.fnd(r, "01-inventory", "struct.census")
    files = R.fnd(r, "01-inventory", "inv.file")
    by = collections.defaultdict(list)
    for c in census:
        by[c.get("flag")].append(c["file"])
    out = []
    unknown = [f["file"] for f in files if (f.get("type") in (None, "", "application/octet-stream"))
               and not R.is_test_data(f["file"])]
    if unknown:
        out.append(("Unknown file type", unknown))
    if by["ext-magic-mismatch"]:
        out.append(("Contents are a different type than the file name says", by["ext-magic-mismatch"]))
    if by["archive"]:
        out.append(("Archives (their contents were not read)", by["archive"]))
    if by["symlink"]:
        out.append(("Links to another file or folder (symlinks)", by["symlink"]))
    long = [f for f in by["reader-window"] if R.audience(f) in ("model", "subagent")]
    if long:
        out.append(("Files the AI reads that are longer than a reviewer's viewer shows "
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
        lis = "".join(f'<li><b>{esc(t)}</b> <span class="count">{len(fs)}</span>'
                      f'<code class="where">{esc(_files(fs))}</code></li>' for t, fs in concerns)
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
            lines.append(f"Broken file references: {len(dang):,} paths written in the files point at files "
                         "that are not in the folder (" + ", ".join(f"{v:,} in {k}" for k, v in
                                                                 ctx.most_common()) + ").")
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
    for host in sorted({x["host"] for x in rows}):
        mine = [x for x in rows if x["host"] == host]
        trs.append(f'<tr class="dom"><th colspan="3">{esc(host)} <span class="count">{len(mine)}</span></th></tr>')
        for x in sorted(mine, key=lambda x: (x["file"] or "", x["line"] or 0, x["url"])):
            shown = x["url"] if len(x["url"]) <= LINK_SHOW else x["url"][:LINK_SHOW - 1] + "…"
            where = f"{x['file']}:{x['line']}" if x.get("line") is not None else (x["file"] or "")
            trs.append(f'<tr><td class="url"><code title="{esc(x["url"])}">{esc(shown)}</code>'
                       f'<button type="button" class="copy" data-url="{esc(x["url"])}" '
                       f'aria-label="Copy the whole link">Copy</button></td>'
                       f'<td class="loc"><code>{esc(where)}</code></td><td class="who">{esc(x["who"])}</td></tr>')
    table = (f'<details class="fold"><summary>All {len(rows):,} links, by domain</summary>'
             f'<div class="tablewrap"><table class="links"><thead><tr><th>Link</th><th>File, line</th>'
             f'<th>Read by</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div></details>')
    return _section("links", "Outside links", esc(lede), f'<p class="headline">{esc(head)}</p>{table}')


def hidden(r, items) -> str:
    lede = "Text the AI receives that a person reading the file on screen would not see."
    if "02-reader" not in r:
        return _section("hidden", "Hidden text", esc(lede), _empty("Not checked: this run has no stage 2 output."))
    div = [d for d in R.fnd(r, "02-reader", "read.divergence") if "skipped" not in d]
    fold = R.fnd(r, "02-reader", "read.fold")
    script = R.fnd(r, "02-reader", "read.script")
    mine = [it for it in items if it.get("kind") == "hidden+phrase"]
    if not div and not fold and not script:
        return _section("hidden", "Hidden text", esc(lede),
                        _empty("Nothing hidden: what the AI reads matches what a person sees."))
    lines = []
    if div:
        cs = collections.Counter(d.get("carrier", "?") for d in div)
        ai = sum(1 for d in div if R.audience(d.get("file")) in ("model", "subagent"))
        lines.append(f"In {R.n(len(div), 'place')}, what the AI reads differs from what a person sees "
                     f"({ai:,} in files the AI reads): " + ", ".join(
                         f"{CARRIER_PLAIN.get(k, 'mixed invisible characters' if '+' in k else k)} {v}"
                         for k, v in cs.most_common()) + ".")
    if fold:
        lines.append(f"{_count(len(fold), 'line')} read differently once look-alike or invisible characters "
                     "are swapped for plain ones (most are typographic quotes and dashes).")
    if script:
        lines.append(f"{R.n(len(script), 'stretch', 'stretches')} of text in a non-Latin script; the "
                     "risky-ask patterns read English only.")
    body = "".join(_p(x) for x in lines)
    if mine:
        body += '<h3>Hidden, and it reads like an instruction</h3>' + _cards(mine)
    return _section("hidden", "Hidden text", esc(lede), body)


def secrets(r, items) -> str:
    lede = "Lines that look like a password, key, or token saved in the files. Values are never shown here."
    allf = [x for x in R.fnd(r, "04-phrases", "secret.found")]
    if "04-phrases" not in r:
        return _section("secrets", "Committed secrets", esc(lede), _empty("Not checked: this run has no stage 4 output."))
    if any("skipped" in x for x in allf):
        return _section("secrets", "Committed secrets", esc(lede),
                        _empty("Not checked: no secret scanner was installed for this run."))
    real = [it for it in items if it.get("kind") == "secret"]
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
                    _p(f"{R.n(len(real), 'line')} look like committed secrets.{by}{note}") + _cards(real))


def risky(r, items, model_items) -> str:
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
                     "something else (a description, a quote, or the words in another sense).")
    rub = R.fnd(r, "04-phrases", "rubric.action")
    if rub:
        unconf = sum(1 for x in rub if not x.get("confirmation") and not x.get("negated_action"))
        forbid = sum(1 for x in rub if x.get("negated_action"))
        lines.append(f"Actions that should ask you first (sending, publishing, paying, entering passwords): "
                     f"{len(rub)} in text the AI follows, {unconf} with no step asking you"
                     + (f", {forbid} where the text forbids the action" if forbid else "") + ".")
    body = "".join(_p(x) for x in lines) if lines else _empty("No line matches the wording of a risky request.")
    listed = [it for it in items if it.get("kind") not in OWN_SECTIONS]
    if listed:
        lis = "".join(f'<li>{esc(it["title"])} <span class="count">{R.n(len(it["wheres"]), "place")}</span></li>'
                      for it in listed)
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
    """Only when an earlier run of the same repository is a different version: a re-run of the
    same version has nothing to say here."""
    if not ch or ch.get("same"):
        return ""
    body = ("".join(_p(x[:1].upper() + x[1:] + ("" if x.endswith(".") else ".")) for x in ch.get("lines", []))
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


def render_page(meta, r, stamps, notes, runs_ok, changes_since=None) -> str:
    every = grouped(first_items(r))
    items = [it for it in every if it["stage"] != 6]
    model_items = [it for it in every if it["stage"] == 6]
    body = [header(meta), trifecta(r), stats(r), links(r), hidden(r, items), secrets(r, items),
            risky(r, items, model_items), changes(changes_since), recs(r), other(r, stamps, notes, runs_ok),
            f'<footer><p>{esc(R.NOT_WHAT)}</p></footer>']
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            f"<title>{esc('Walkdown: ' + meta['repo'])}</title>\n" + FONTS + f"<style>{CSS}</style>\n</head>\n"
            f"<body>\n<main class=\"wrap\">\n{''.join(body)}\n</main>\n<script>{JS}</script>\n</body>\n</html>\n")


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
.top { display: flex; justify-content: flex-end; }
.pagelink { font: 600 .88rem/1.2 var(--body); color: var(--accent); text-decoration: none; border: 1px solid var(--rule); border-radius: 999px; padding: .35rem .75rem; white-space: nowrap; }
.pagelink:hover, .pagelink:focus-visible { border-color: var(--accent); }
h1 { font: 700 clamp(1.9rem, 4vw, 2.6rem)/1.1 var(--display); margin: .3rem 0 .6rem; text-wrap: balance; overflow-wrap: anywhere; }
.h1-lead { color: var(--muted); font-weight: 500; }
.meta { font: .82rem/1.5 var(--mono); color: var(--muted); display: flex; flex-wrap: wrap; gap: .3rem 1.2rem; overflow-wrap: anywhere; }
h2 { font: 700 1.35rem/1.2 var(--display); margin: 0 0 .7rem; }
h3 { font: 600 1.02rem/1.3 var(--body); margin: 1.1rem 0 .5rem; }
.lede { color: var(--muted); margin: -.3rem 0 .9rem; max-width: 68ch; }
.headline { font-weight: 600; margin: 0 0 .6rem; }
.block p { margin: .35rem 0; max-width: 72ch; overflow-wrap: anywhere; }
.empty { color: var(--muted); font-style: italic; }
.note { color: var(--muted); }
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
.leg-def, .leg-n { font-size: .88rem; color: var(--muted); margin-top: .15rem; }
.leg-n { font-weight: 600; }
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
@media (max-width: 640px) { .legs { grid-template-columns: 1fr; } header.card, .block { padding: 1rem; } td.who { white-space: normal; } }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""
