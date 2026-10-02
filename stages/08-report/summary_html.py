"""The summary page as readable HTML. Spec: specs/summary_html.SPEC.md.

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
]
MAX_FIRST = 12


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def _family(patterns) -> str:
    for p in patterns or []:
        for prefix, name in FAMILY:
            if p.startswith(prefix):
                return name
    return "Matches a pattern worth reading"


def _item(stage, title, where, quote=None, note=None, lead=None) -> dict:
    """`lead`: words shown once before the card's notes, however many are merged."""
    return {"stage": stage, "title": title, "where": where, "quote": quote, "note": note,
            "lead": lead}


def first_items(r) -> list[dict]:
    """Everything the summary's points of attention name, as plain items, stage order."""
    out = []
    for h in [h for h in R.fnd(r, "01-inventory", "struct.hooks") if not R.is_test_data(h.get("file"))]:
        out.append(_item(1, "Runs commands on its own", h["file"],
                         f"{h.get('event')}: {h.get('command')}",
                         "A hook runs when the harness fires the event, not when you ask."))
    model, _ = R._split_audience(r, R.pairs(r, "hidden+phrase"))
    for p in model:
        out.append(_item(2, "Hidden when rendered, and reads like an instruction", R.loc(p), p["quote"].strip()))
    both = R.pairs(r, "orphan+phrase") + R.pairs(r, "dynamic+phrase")
    listed, _ = R._split_audience(r, both)
    for p in listed:
        why = ("Nothing refers to this file" if p["pair"] == "orphan+phrase"
               else "Loaded only by a folder or glob, named by nothing")
        out.append(_item(3, why + ", and it reads like an instruction", R.loc(p), p["quote"].strip()))
    hits = [h for h in R.phrase_hits(r) if R.POINT_PATTERNS & set(h.get("patterns", []))
            and h.get("audience") not in ("human", "test-data")]
    for h in hits:
        pats = sorted(R.POINT_PATTERNS & set(h["patterns"]))
        out.append(_item(4, _family(pats), R.loc(h), h["quote"].strip(), R.rates_note(r, pats),
                         lead="How often this pattern turns up elsewhere: "))
    for c in R.fnd(r, "04-phrases", "term.conflict"):
        d = c["definitions"][0]
        out.append(_item(4, f"The word “{c['term']}” is defined {len(c['definitions'])} different ways",
                         f"{d['file']}:{d['line']}"))
    for t in R.fnd(r, "04-phrases", "term.safety"):
        out.append(_item(4, f"Redefines the safety word “{t['term']}”", R.loc(t), t.get("quote", "").strip()))
    for x in R.fnd(r, "04-phrases", "rubric.action"):
        if x.get("confirm_redefined"):
            out.append(_item(4, "An action whose confirmation step is a redefinition", R.loc(x), x["quote"].strip()))
        elif x.get("tier") == "prohibited" and not x.get("confirmation"):
            out.append(_item(4, "An irreversible or prohibited action with no confirmation step",
                             R.loc(x), x["quote"].strip()))
    for p in R.pairs(r, "testdata+loaded"):
        out.append(_item(5, "Test data that the model is pointed at", p["file"],
                         note=f"Referenced directly from {p.get('from')}, which the model reads."))
    for p in R.pairs(r, "hook+phrase"):
        out.append(_item(5, "An instruction the model sees before you type anything", R.loc(p),
                         p["quote"].strip(), "A context-injecting hook runs this script."))
    s = R._soft(r)
    new, _, near_sw = R.sweep_split(s)
    for x in new:
        out.append(_item(6, "No pattern matched, but a model read this as an instruction",
                         f"{R.span(x)} (p={x['p_any']:.2f})",
                         note=R.SWEEP_PLAIN.get(R.sweep_kind(x), R.sweep_kind(x)),
                         lead=f"Read by {x['backend']} as telling the reader to: "))
    for x in near_sw:
        if x.get("covered"):
            continue
        out.append(_item(6, "Near the line: no pattern matched, and a model may read this as an "
                            "instruction", f"{R.span(x)} (p={x['p_any']:.2f})",
                         note=R.SWEEP_PLAIN.get(R.sweep_kind(x), R.sweep_kind(x)),
                         lead=f"Repeat sweeps vary by about {R.SWEEP_DRIFT}, so each could go "
                              f"either way. Read by {x['backend']} as telling the reader to: "))
    for x in s["reads"]:
        if x.get("file") and x.get("answer"):
            flat = " ".join(x["answer"].replace("**", "").split())
            out.append(_item(6, "A reviewer model's reading", R.loc(x),
                             note=flat[:320] + ("…" if len(flat) > 320 else "")))
    clear, near = R.do_reads(s["labels"])
    for x in clear:
        out.append(_item(6, "Read as a real instruction to do the flagged thing",
                         f"{R.loc(x)} (p={R.p_do(x):.2f})",
                         note=f"Read by {x['backend']}, at p >= {R.DO_CLEAR_P}."))
    for x in near:
        out.append(_item(6, "Near the line: may be a real instruction",
                         f"{R.loc(x)} (p={R.p_do(x):.2f})",
                         note=f"Read by {x['backend']}, at p {R.DO_NEAR_P} to {R.DO_CLEAR_P}. "
                              f"Repeat reads of one line vary by about {R.DRIFT}, so each of "
                              "these could go either way."))
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
        return (f"{R.n(len(f('graph.entry')), 'entry point')}. {R.n(len(f('graph.orphan')), 'file')} "
                f"nothing refers to, {R.n(loaded, 'file')} loaded only by a folder or glob.")
    if stage == "04-phrases":
        hits = R.phrase_hits(r)
        hosts = f("endpoint.host")
        undoc = [h for h in hosts if not h.get("documented") and not h.get("local")]
        return (f"{len(hits):,} lines match a pattern (a location to read, not a finding). "
                f"{R.n(len(hosts), 'network host')}, {len(undoc)} not named in the docs.")
    if stage == "05-capability":
        legs = {x["leg"]: x["present"] for x in f("cap.leg")}
        have = [R.LEG_NAMES[k].lower() for k in R.LEG_NAMES if legs.get(k)]
        if len(have) == 3:
            return ("It reads your data, takes outside input, and sends data out: all three legs of the "
                    "lethal trifecta. That raises risk. It is not an issue on its own.")
        return ("Of the three trifecta legs it " + (", ".join(have) if have else "shows none") + "."
                if have else "It shows none of the three trifecta legs.")
    if stage == "06-soft":
        s = R._soft(r)
        if not s["backends"]:
            return f"{R.n(len(s['questions']), 'question')} written for a person to read. No model was asked."
        names = ", ".join(sorted({b["backend"] for b in s["backends"]}))
        return (f"{R.n(len(s['questions']), 'question')} a pattern could not settle, answered by {names}. "
                "Answers are readings, not verdicts.")
    return ""


def _wheres(ws) -> str:
    uniq = list(dict.fromkeys(ws))
    return "  ·  ".join(uniq[:4]) + (f"  ·  +{len(uniq) - 4} more" if len(uniq) > 4 else "")


CHECK = ('<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="1.5" y="1.5" width="17" height="17" rx="3"/>'
         '<path d="M5.5 10.5l3 3 6-7"/></svg>')
BOX = '<svg viewBox="0 0 20 20" aria-hidden="true"><rect x="1.5" y="1.5" width="17" height="17" rx="3"/></svg>'


def _trifecta(legs, marked=()) -> str:
    """The three legs as a checklist: a box per plain term, a one-line definition under each.
    `marked`: legs whose every cited line stage 6 read as not an instruction (soft D5)."""
    rows = []
    for k, name in R.LEG_NAMES.items():
        on = bool(legs.get(k))
        mk = ('<div class="leg-def">Every line cited for this was read in stage 6 as not an '
              'instruction. The box stays checked; see 5 in the full report.</div>'
              if on and k in marked else "")
        rows.append(f'<li class="leg {"on" if on else "off"}"><span class="box" role="img" '
                    f'aria-label="{"yes" if on else "no"}">{CHECK if on else BOX}</span>'
                    f'<div><div class="leg-name">{esc(name)}</div>'
                    f'<div class="leg-def">{esc(R.LEG_DEFS[k])}</div>{mk}</div></li>')
    n_on = sum(1 for k in R.LEG_NAMES if legs.get(k))
    if n_on == 3:
        foot = "All three legs of the lethal trifecta. That raises risk. It is not an issue on its own."
    else:
        foot = (f"{n_on} of the three legs of the lethal trifecta. Capability, not a verdict: the "
                "danger is all three together.")
    return (f'<section class="trifecta" aria-label="What it can do"><h2>What it can do</h2>'
            f'<ul class="legs">{"".join(rows)}</ul><p class="leg-foot">{esc(foot)}</p></section>')


def _tile(label, value, sub="") -> str:
    return (f'<div class="tile"><div class="tile-v">{esc(value)}</div>'
            f'<div class="tile-l">{esc(label)}</div>{f"<div class=tile-s>{esc(sub)}</div>" if sub else ""}</div>')


def render_page(meta, r, stamps, notes, runs_ok) -> str:
    items = grouped(first_items(r))
    lim = R.limits(r, notes, stamps, runs_ok)
    recs = R.recommendations(r)
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    legs = {x["leg"]: x["present"] for x in R.fnd(r, "05-capability", "cap.leg")}
    total, unread = pin.get("files", 0), len(R.fnd(r, "02-reader", "read.unread"))
    tiles = [_tile("files examined", f"{total:,}", f"{total - unread:,} read in full"),
             _tile("things to look at first", len(items)),
             _tile("things not examined", len(lim))]
    trifecta = _trifecta(legs, R.all_marked_legs(r))
    first = []
    for it in items[:MAX_FIRST]:
        quotes = "\n".join(it["quotes"][:6])
        q = f'<pre class="quote">{esc(quotes)}</pre>' if quotes else ""
        nt = (f'<p class="note">{esc((it.get("lead") or "") + it["note"])}</p>'
              if it.get("note") else "")
        places = len(it["wheres"])
        count = f' <span class="count">{places} places</span>' if places > 1 else ""
        first.append(f'<li class="item"><div class="item-h"><span class="stage-tag">Stage {it["stage"]}</span>'
                     f'<h3>{esc(it["title"])}{count}</h3></div>'
                     f'<code class="where">{esc(_wheres(it["wheres"]))}</code>{q}{nt}</li>')
    more = len(items) - MAX_FIRST
    if more > 0:
        first.append(f'<li class="more">{more} more in the full report.</li>')
    if not items:
        first.append('<li class="more">Nothing on the attention list. See each stage below.</li>')
    stages = []
    for i, stage in enumerate(R.ORDER, 1):
        if stage == "07-limits":
            plain = f"{R.n(len(lim), 'thing')} this run could not look at. A clean result says nothing about these."
            detail = "".join(f"<li>{esc(x)}</li>" for x in lim)
            detail = f"<ul>{detail}</ul>"
        else:
            plain = plain_status(r, stamps, stage)
            tech = R.status(r, stamps, stage).replace("\n" + " " * R.COL, " ")
            st = stamps.get(stage)
            stamp = f'<p class="stamp">Checked against its test fixtures: {esc(st.text)}</p>' if st else ""
            detail = f"<p>{esc(tech)}</p>{stamp}"
        warn = ""
        st = stamps.get(stage)
        if st is not None and st.result != "PASS":
            warn = f'<span class="pill">validation {esc(st.result.lower())}</span>'
        stages.append(f'<li class="stage"><span class="num">{i}</span><div class="stage-b">'
                      f'<h3>{esc(PLAIN_STAGE[stage])} {warn}</h3><p class="plain">{esc(plain)}</p>'
                      f'<details><summary>Technical detail</summary>{detail}</details></div></li>')
    recs_html = ("".join(f"<li>{esc(x)}</li>" for x in recs) if recs
                 else "<li>None. No finding matched a recommendation template.</li>")
    return PAGE.format(
        title=esc(f"Walkdown: {meta['repo']}"), repo=esc(meta["repo"]), source=esc(meta["source"]),
        hash=esc(f"{meta['hash_kind']} {meta['hash'][:12]}"), date=esc(meta["date"]), run=esc(meta["run"]),
        tiles="".join(tiles), trifecta=trifecta, first="".join(first), stages="".join(stages), recs=recs_html,
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
/* Layout: an inspection record. Header card, a strip of four counts, "look at these first" as the
   main column, then the seven stages as a numbered checklist (the order is the method's order). */
:root {{
  --paper: #f5f7f8; --sheet: #ffffff; --ink: #17222e; --muted: #5a6875; --rule: #d8dee4;
  --accent: #1d6a86; --flag: #9a5b00; --flag-bg: #fdf3e4; --quote-bg: #eef2f5;
  --display: "Archivo", "Arial Narrow", Arial, sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", Consolas, "Courier New", monospace;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--paper); color: var(--ink); font: 17px/1.55 var(--body); }}
.wrap {{ max-width: 58rem; margin: 0 auto; padding-inline: 16px; padding-block: 2rem 4rem; display: grid; gap: 2.2rem; }}
header.card {{ background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; padding: 1.6rem 1.6rem 1.3rem; }}
.eyebrow {{ font: 600 .78rem/1 var(--body); letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }}
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
ol, ul {{ margin: 0; padding: 0; list-style: none; }}
.first {{ display: grid; gap: .8rem; }}
.item {{ background: var(--sheet); border: 1px solid var(--rule); border-left: 4px solid var(--flag); border-radius: 4px; padding: .9rem 1.1rem; min-width: 0; }}
.item-h {{ display: flex; gap: .7rem; align-items: baseline; flex-wrap: wrap; }}
.item h3 {{ margin: 0; font: 600 1.05rem/1.3 var(--body); }}
.count {{ font: 400 .85rem var(--body); color: var(--muted); }}
.stage-tag {{ font: 600 .72rem/1 var(--body); letter-spacing: .08em; text-transform: uppercase; color: var(--flag); background: var(--flag-bg); padding: .3rem .5rem; border-radius: 3px; white-space: nowrap; }}
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
details summary {{ cursor: pointer; color: var(--accent); font-size: .9rem; }}
details summary:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
details p, details li {{ font-size: .88rem; color: var(--muted); overflow-wrap: anywhere; }}
details ul {{ list-style: disc; padding-left: 1.2rem; margin-top: .4rem; }}
.stamp {{ font-family: var(--mono); font-size: .78rem; }}
.recs li {{ padding: .6rem 0; border-bottom: 1px solid var(--rule); max-width: 75ch; overflow-wrap: anywhere; }}
footer {{ border-top: 2px solid var(--ink); padding-top: 1rem; color: var(--muted); max-width: 70ch; }}
.trifecta {{ background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; padding: 1.2rem 1.4rem; }}
.trifecta h2 {{ margin-bottom: .7rem; }}
.legs {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.1rem; }}
.leg {{ display: grid; grid-template-columns: 1.6rem minmax(0, 1fr); gap: .6rem; align-items: start; }}
.box svg {{ width: 1.5rem; height: 1.5rem; fill: none; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; }}
.leg.on .box svg rect {{ fill: var(--accent); stroke: var(--accent); }}
.leg.on .box svg path {{ stroke: var(--sheet); stroke-width: 2.4; }}
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
    <div class="eyebrow">Walkdown report</div>
    <h1>{repo}</h1>
    <div class="meta"><span>{source}</span><span>{hash}</span><span>retrieved {date}</span><span>run {run}</span></div>
    <p class="static">Static examination only. Nothing in it was installed or run.</p>
  </header>
  <section class="tiles" aria-label="At a glance">{tiles}</section>
  {trifecta}
  <section>
    <h2>Look at these first</h2>
    <p class="lede">Locations picked by fixed rules, in stage order. Each is a place to read, not a finding against the author.</p>
    <ol class="first">{first}</ol>
  </section>
  <section>
    <h2>Stage by stage</h2>
    <ol class="stages">{stages}</ol>
  </section>
  <section>
    <h2>Recommendations ({nrecs})</h2>
    <p class="lede">Each depends on what the skill is for. Unranked, in stage order.</p>
    <ul class="recs">{recs}</ul>
  </section>
  <footer><p>{notwhat}</p><p>Every finding, with file and line, is in <code>full.md</code> next to this page.</p></footer>
</main>
</body>
</html>
"""
