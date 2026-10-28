"""The eight questions both pages answer, as data. Spec: specs/glance.SPEC.md.

Report v3 (owner, 2026-10-27: "glance and know"): for someone with no computer skills, the same
eight questions on summary.html and details.html, each with a chip (a short label), a one-line
answer, plain bullets, and on details.html everything behind it. Every sentence is a template
filled from findings the stages already made; nothing here detects or judges. Token figures live
in question 2 only. HTML here escapes all repository text.
"""
from __future__ import annotations

import collections
import html
import posixpath
from dataclasses import dataclass, field

import details_html as D
import marks as M
import render as R
import summary_html as S

LOCAL, CLAUDE = R.DEFAULT_CONTEXT, R.CLAUDE_CONTEXT
SHARE = R.TRIGGER_TABLE["listing_share"]  # Claude Code's skill listing: about 1% of the context


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


@dataclass
class Q:
    """One question: `tone` is look, notes, fact, none, or unmeasured (the chip's color)."""
    id: str
    question: str
    chip: str
    tone: str
    answer: str                 # HTML, escaped
    bullets: list = field(default_factory=list)  # HTML, escaped; both pages
    more: str = ""              # HTML shown under the bullets on both pages (tables, charts)
    detail: str = ""            # HTML on details.html only


# ---------------------------------------------------------------- small builders

def n(x, word, plural=None) -> str:
    return R.n(x, word, plural)


def where(f) -> str:
    return f'<span class="where">{esc(R.where(f))}</span>'


def code(s) -> str:
    return f"<code>{esc(s)}</code>"


def short_name(path) -> str:
    """What a skill, helper, or command is called: a SKILL.md by its folder, any other by its file
    name without the extension; a SKILL.md at the top of the repository is "SKILL"."""
    parts = str(path).split("/")
    if parts[-1] == "SKILL.md" and len(parts) > 1:
        return parts[-2]
    return parts[-1].rsplit(".", 1)[0]


def names(xs) -> str:
    """a, b, and c (a comma before "and" when there are three or more)."""
    xs = list(xs)
    if len(xs) < 3:
        return " and ".join(xs)
    return ", ".join(xs[:-1]) + ", and " + xs[-1]


def top_folder(files) -> tuple[str, int] | None:
    """The top folder holding half or more of `files`, and how many (sentence: "N of those are in
    examples/"); None otherwise."""
    c = collections.Counter(f.split("/")[0] for f in files if "/" in f)
    if not c:
        return None
    folder, k = c.most_common(1)[0]
    return (folder, k) if k * 2 >= len(files) else None


def in_folder(files) -> str:
    t = top_folder(files)
    return f" ({t[1]} of them in {code(t[0] + '/')})" if t and t[1] < len(files) else (
        f" (all in {code(t[0] + '/')})" if t else "")


def fold(summary_html, inner, open_=False) -> str:
    return (f'<details class="fold"{" open" if open_ else ""}><summary>{summary_html}</summary>'
            f'<div class="fold-body">{inner}</div></details>')


def places(rows, text=None) -> str:
    """A list of places: `text(f)` beside each where, when given."""
    return '<ul class="places">' + "".join(
        f"<li>{where(f)}" + (f" {text(f)}" if text else "") + "</li>" for f in rows) + "</ul>"


def hbars(rows, unit="") -> str:
    """One series of horizontal bars: rows of (label, value, tooltip); values at the bar ends. A
    chart of one bar or none is no chart: callers say it in a sentence instead."""
    top = max((v for _, v, _ in rows), default=0) or 1
    out = ['<div class="hbars">']
    for label, v, tip in rows:
        out.append(f'<div class="hb" data-tip="{esc(tip)}"><span class="hb-l">{esc(label)}</span>'
                   f'<span class="hb-t"><span class="hb-f" style="width:{max(v * 100 / top, 0.6):.1f}%"></span>'
                   f'<span class="hb-v">{v:,}{esc(unit)}</span></span></div>')
    return "".join(out) + "</div>"


def by_file_chart(rows, what) -> str:
    """Places by file, the six with the most and the rest folded into one bar."""
    c = collections.Counter(f.get("file") for f in rows if f.get("file"))
    if len(c) < 2:
        return ""
    top = c.most_common(6)
    bars = [(p, k, f"{p}: {n(k, what)}") for p, k in top]
    rest = sum(c.values()) - sum(k for _, k in top)
    if rest:
        bars.append((f"{len(c) - len(top)} other files", rest, f"{n(rest, what)} in {len(c) - len(top)} other files"))
    return hbars(bars)


def meter_cell(tok, ctx) -> str:
    p = tok * 100 / ctx
    tip = f"{tok:,} of {ctx:,} tokens: {p:.1f}%"
    if p > 100:
        return (f'<td class="cell-meter" data-tip="{esc(tip)}"><span class="pct">more than fits</span>'
                '<div class="meter over"><span></span></div></td>')
    return (f'<td class="cell-meter" data-tip="{esc(tip)}"><span class="pct">{esc(R.pct(tok, ctx))}</span>'
            f'<div class="meter"><span style="width:{p:.1f}%"></span></div></td>')


def table(head, rows, cls="tbl") -> str:
    return (f'<div class="tablewrap"><table class="{cls}"><thead><tr>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def bullets_html(items) -> str:
    return '<ul class="bul">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>" if items else ""


def unmeasured(qid, question, why="this run was made before this check, or a step did not run") -> Q:
    return Q(qid, question, "Not measured", "unmeasured", esc(f"Not measured: {why}."))


def chip_for(look, notes, look_word="to look at") -> tuple[str, str]:
    if look:
        return f"{look} {look_word}", "look"
    if notes:
        return n(notes, "note"), "notes"
    return "Nothing to look at", "none"


# ---------------------------------------------------------------- what it is

def entries(r) -> list[dict]:
    return R.fnd(r, "04-phrases", "trig.entry")


def what_it_is(r) -> str:
    """The one sentence under the name: what the repository holds. Nothing when the inventory did
    not run."""
    if "01-inventory" not in r:
        return ""
    ents = entries(r)
    sk = sum(1 for e in ents if e["kind"] == "skill")
    cm = sum(1 for e in ents if e["kind"] == "command")
    ag = sum(1 for e in ents if e["kind"] == "agent")
    parts = []
    if sk:
        parts.append(f"<b>{n(sk, 'skill')}</b> (step-by-step instructions the AI follows for a task)")
    if cm:
        parts.append(f"<b>{n(cm, 'command')}</b> (instructions you start by typing their name)")
    if ag:
        parts.append(f"<b>{n(ag, 'helper')}</b> (assistants the AI can hand work to)")
    plugin = any(f["file"].endswith(".claude-plugin/plugin.json") or f["file"] == ".claude-plugin/plugin.json"
                 for f in R.fnd(r, "01-inventory", "inv.file"))
    if not parts:
        return "It holds no skills, commands, or helpers. Walkdown read its instruction files."
    lead = "A plugin for Claude Code: " if plugin else "It holds "
    return lead + names(parts) + "."


# ---------------------------------------------------------------- 1 switching on

TRIG_LOOK = ("not-read", "skipped", "rules", "values", "tools", "overlap", "cut")
GUIDANCE_PLAIN = {"no-when": "doesn't say when to use it, so the AI has less to go on when deciding whether to pick it",
                  "first-person": "is written as \u201cI\u201d instead of describing what it does",
                  "second-person": "is written as \u201cyou\u201d instead of describing what it does"}


def q_switch(r, ctx) -> Q:
    title = "Will its skills switch on when they should?"
    tr = R.trigger_of(r)
    if not tr["measured"]:
        return unmeasured("switch", title)
    ents = tr["entries"]
    if not ents:
        return Q("switch", title, "None here", "fact", "No skills, commands, or helpers here.")
    kinds = {k: p for k, _, _, p in tr["kinds"]}
    keys_near = [f for f in kinds.get("keys", []) if f.get("near")]
    keys_far = [f for f in kinds.get("keys", []) if not f.get("near")]
    look = sum(len(kinds.get(k, [])) for k in TRIG_LOOK) + len(keys_near)
    lst = tr["listing"] or {}
    over = round((lst.get("listing_chars") or 0) / R.BYTES_PER_TOKEN) > ctx * SHARE
    notes = sum(1 for x in (kinds.get("guidance"), keys_far, over) if x)
    chip, tone = chip_for(look, notes)
    sk = [e for e in ents if e["kind"] != "agent"]
    ag = [e for e in ents if e["kind"] == "agent"]
    broken = [e for e in ents if e["mode"] in ("unread", "skipped")]
    typed = [e for e in ents if e["mode"] == "typed"]
    whole = names([x for x in (n(len(sk), "skill") if sk else "", n(len(ag), "helper") if ag else "") if x])
    if broken:
        answer = f"{len(broken)} of the {whole} won't switch on as written: the AI can't read their settings, or skips them."
    elif typed:
        answer = (f"Yes. {len(ents) - len(typed)} of the {whole} switch on by themselves; {len(typed)} only when "
                  "you ask for them by name.")
    else:
        answer = (f"Yes. All {whole} are set up to switch on by themselves." if len(ents) > 1
                  else f"Yes. Its one {'helper' if ag else 'skill'} is set up to switch on by itself.")
    b = []
    if kinds.get("not-read"):
        b.append(f"{n(len(kinds['not-read']), 'file')} can't be read: the settings at the top are broken or not at the very "
                 "top, so the AI can't tell when to use them.")
    if kinds.get("skipped"):
        b.append(f"{n(len(kinds['skipped']), 'helper')} {'is' if len(kinds['skipped']) == 1 else 'are'} skipped: no name, "
                 "no description, or a name the AI refuses.")
    if kinds.get("rules"):
        b.append(f"{n(len(kinds['rules']), 'name or description', 'names or descriptions')} break a rule other AI tools or "
                 "claude.ai apply, so they may refuse the skill.")
    if keys_near:
        b.append(f"{n(len(keys_near), 'setting')} look{'s' if len(keys_near) == 1 else ''} like a typo, so the AI ignores "
                 + ("it" if len(keys_near) == 1 else "them") + ": "
                 + ", ".join(f"{code(f['key'])} (the AI knows {code(f['near'])})" for f in keys_near[:3]) + ".")
    if kinds.get("values"):
        b.append(f"{n(len(kinds['values']), 'setting')} {'has' if len(kinds['values']) == 1 else 'have'} a value the AI doesn't accept.")
    if kinds.get("tools"):
        b.append(f"{n(len(kinds['tools']), 'tool name')} the AI doesn't know, or an older name.")
    if kinds.get("overlap"):
        b.append(f"{n(len(kinds['overlap']), 'pair')} of skills describe themselves so alike that the AI may pick the wrong one.")
    if kinds.get("cut"):
        b.append(f"{n(len(kinds['cut']), 'description')} {'is' if len(kinds['cut']) == 1 else 'are'} too long; the end gets cut off.")
    for f in kinds.get("guidance", []):
        b.append(f"{code(short_name(f['file']))} "
                 f"{esc(GUIDANCE_PLAIN.get(f['kind'], f['kind']))}.")
    if over:
        b.append(f"On {esc(ctx_name(ctx, short=True))}, the list of skills is too long to show in full, so the ones used "
                 "least lose their descriptions. The numbers are under \u201cHow much of the AI's memory\u201d.")
    if keys_far:
        ks = sorted({f["key"] for f in keys_far})
        b.append((f"Each of {n(len(keys_far), 'skill')} has a {code(ks[0])} line the AI ignores" if len(ks) == 1
                  else f"{n(len(keys_far), 'setting')} the AI ignores ({', '.join(code(k) for k in ks[:4])})")
                 + ". It does no harm; it just does nothing.")
    rows = []
    for e in sorted(ents, key=lambda e: (e["kind"] == "agent", e["name"] or e["file"])):
        why = e.get("why") or ""
        on = "\u2713 by itself" if e["mode"] == "auto" else {"paths": "\u2713 on matching files", "typed": "when you type its name",
                                                            "unread": "\u2717 settings not read", "skipped": "\u2717 skipped"}[e["mode"]]
        rows.append(f"<tr><td><b>{esc(e['name'] or e['file'])}</b><small class=\"where\">{esc(e['file'])}</small></td>"
                    f"<td>{'helper' if e['kind'] == 'agent' else e['kind']}</td><td>{esc(on)}"
                    + (f"<small class=\"where\">{esc(why)}</small>" if why else "") + "</td></tr>")
    detail = fold(f"All {len(ents)}, one by one", table("<th>Name</th><th>Type</th><th>Switches on</th>", rows))
    for k, name, why, pl in tr["kinds"]:
        detail += fold(f"{esc(name)} ({len(pl)})",
                       f'<p class="where">{esc(why)}.</p><ul class="places">'
                       + "".join(f"<li>{code(R.trig_parts(k, f)[0])} {esc(R.trig_parts(k, f)[1])}</li>" for f in pl) + "</ul>")
    return Q("switch", title, chip, tone, esc(answer) if "<" not in answer else answer, b, detail=detail)


# ---------------------------------------------------------------- 2 memory

def ctx_name(ctx, short=False) -> str:
    """How the expected context is named: "a local AI" at the default (owner, 2026-10-27)."""
    if ctx == LOCAL:
        return "a local AI" if short else "Local AI"
    if ctx == CLAUDE:
        return "Claude"
    return "your AI" if short else "Your AI"


def fraction(p) -> str:
    """A share in words a reader without numbers can hold: "about a fifth"."""
    for v, w in ((50, "half"), (33.3, "a third"), (25, "a quarter"), (20, "a fifth"), (10, "a tenth"), (5, "a twentieth")):
        if abs(p - v) <= v * 0.12:
            return f"about {w}"
    return "under 1%" if p < 1 else f"about {p:.0f}%"


def memory_table(r, ctx) -> str:
    c = R.cost(r)
    files = R.fnd(r, "04-phrases", "trig.entry")
    sk = sum(1 for e in files if e["kind"] != "agent")
    ag = sum(1 for e in files if e["kind"] == "agent")
    rows = [("Always there once installed",
             "the short descriptions of its " + names([x for x in (n(sk, "skill") if sk else "", n(ag, "helper") if ag else "") if x] or ["entries"])
             + (" and its hooks' text" if (c["session"] or {}).get("hook_config") else ""), c["session"]["tokens"])]
    t = c["tiers"]
    if t:
        kind = {"agent": "helper", "skill": "skill", "command": "command"}.get(t["skill-max"].get("kind"), "entry")
        name = short_name(c["largest"])
        rows.append((f"Its biggest {kind} ({name}), with everything it reads",
                     "a helper works in its own memory, apart from yours" if kind == "helper" else "only while it runs",
                     t["skill-max"]["tokens"]))
    if c["project"]:
        folders = sorted({posixpath.dirname(f) for f in c["project"]["files"]})
        inside = ("this repository's own folder" if folders == [""]
                  else names([f + "/" for f in folders if f]) + (" and the main folder" if "" in folders else ""))
        rows.append((f"Extra, only when someone works inside {inside}",
                     "its instructions file; not loaded for people who install it", c["project"]["tokens"]))
    band = next((b for b in R.ship_bands(r) if b["name"] == "Not used at run time"), None)
    if band and band["files"]:
        rows.append(("Unused files, if the AI were told to open them all",
                     f"{n(band['files'], 'file')}; only opened if something asks for them", band["tokens"]))
    both = ctx != CLAUDE
    head = ("<th>What</th><th class=\"num\">Tokens</th>"
            f"<th>{esc(ctx_name(ctx))}<br>({ctx // 1000:,}k tokens)</th>"
            + ("<th>Claude<br>(200k tokens)</th>" if both else ""))
    trs = [f'<tr><td class="rowname">{esc(a)}<small>{esc(b)}</small></td><td class="num">{tok:,}</td>'
           + meter_cell(tok, ctx) + (meter_cell(tok, CLAUDE) if both else "") + "</tr>" for a, b, tok in rows]
    return table(head, trs, "mem")


def q_memory(r, ctx) -> Q:
    title = "How much of the AI's memory does it use?"
    c = R.cost(r)
    if c["session"] is None:
        return unmeasured("memory", title)
    t = c["tiers"]
    top = t["skill-max"]["tokens"] if t else c["session"]["tokens"]
    p, pc = top * 100 / ctx, top * 100 / CLAUDE
    claude = ("Very little on Claude" if pc < 5 else "A small part on Claude" if pc < 25 else f"About {pc:.0f}% on Claude")
    kind = {"agent": "helper", "skill": "skill", "command": "command"}.get((t or {}).get("skill-max", {}).get("kind"), "")
    what = f"its biggest {kind}" if t else "what it always loads"
    share = "more than all of the memory" if p > 100 else f"{fraction(p)} of the memory"
    answer = f"{claude}. On {ctx_name(ctx, short=True)}, {what} takes {share}."
    if ctx == CLAUDE:
        answer = f"On Claude, {what} takes {share}."
    explain = ('<div class="explain">The AI holds text in pieces called <b>tokens</b> (about \u00be of a word each). '
               + (f"A <b>local AI</b> running on your own computer typically holds about {ctx:,} tokens at once; "
                  if ctx == LOCAL else "" if ctx == CLAUDE
                  else f"<b>Your AI</b> holds about {ctx:,} tokens at once (set with --context); ")
               + ("<b>Claude</b> holds about 200,000 tokens at once." if ctx == CLAUDE else "<b>Claude</b> holds about 200,000.")
               + " These are estimates from file sizes.</div>")
    more = explain + memory_table(r, ctx)
    lst = (R.trigger_of(r).get("listing") or {})
    if lst.get("skills"):
        tok = round(lst["listing_chars"] / R.BYTES_PER_TOKEN)
        room = [(f"{ctx_name(ctx)}: about {round(ctx * SHARE):,} tokens of room", tok, ctx * SHARE)]
        if ctx != CLAUDE:
            room.append((f"Claude: about {round(CLAUDE * SHARE):,} tokens of room", tok, CLAUDE * SHARE))
        more += ("<h3>Room for the list of skills</h3><p class=\"where\">The AI keeps a short list of every skill you have "
                 f"installed, with a set amount of room. This repository's descriptions alone take about {tok:,} tokens.</p>"
                 '<div class="room">')
        for label, need, have in room:
            fits = need <= have
            more += (f'<div data-tip="{need:,} tokens of about {round(have):,} room: '
                     + (f'{need * 100 / have:.0f}%' if fits else f'{need / have:.1f} times the room') + '">'
                     f'<div class="lbl"><span>{esc(label)}</span><span class="pct">'
                     + (f"{need * 100 / have:.0f}%" if fits else "doesn't fit") + "</span></div>"
                     + (f'<div class="meter"><span style="width:{need * 100 / have:.1f}%"></span></div>' if fits
                        else '<div class="meter over"><span></span></div>') + "</div>")
        more += "</div>"
    maxes = sorted((x for x in R.fnd(r, "05-capability", "cap.context") if x["tier"] == "skill-max"),
                   key=lambda x: (-x["tokens"], x["file"]))
    detail = ""
    if len(maxes) > 1:
        kw = lambda x: {"agent": "helper"}.get(x.get("kind"), x.get("kind") or "")  # noqa: E731
        detail = ("<h3>How big each skill and helper gets</h3><p class=\"where\">Tokens each one uses at its fullest: its "
                  "own instructions plus every file it reads. Only the one in use is loaded.</p>"
                  + hbars([(f"{short_name(x['file'])} ({kw(x)})", x["tokens"],
                            f"{x['file']}: {x['tokens']:,} tokens, {x['tokens'] * 100 / ctx:.0f}% of {ctx_name(ctx, short=True)}")
                           for x in maxes]))
    return Q("memory", title, ("under 1%" if p < 1 else f"up to {R.pct(top, ctx)}") if p <= 100 else "more than fits", "fact", esc(answer),
             more=more, detail=detail)


# ---------------------------------------------------------------- 3 package

PACK = (("work", "c1", "do the work: the skills, the helpers, and the files they read"),
        ("people", "c2", "notes for people: the license, readme, and other documents"),
        ("build", "c3", "tests and tools for building it"),
        ("unused", "c4", "nothing refers to them"))
WORK = ("entry", "project", "on-demand", "maybe", "run", "config")


def q_package(r) -> Q:
    title = "What comes in the package?"
    ship = R.fnd(r, "05-capability", "cap.ship")
    if not ship:
        return unmeasured("package", title)
    group = collections.defaultdict(list)
    for x in ship:
        group["work" if x["group"] in WORK else x["group"]].append(x)
    total, extra = len(ship), len(ship) - len(group["work"])
    extra_files = [x["file"] for g in ("people", "build", "unused") for x in group[g]]
    t = top_folder(extra_files)
    answer = (f"{len(group['work'])} of its {total} files do the work. "
              + (f"The other {extra} come along without being used" + (f", and {t[1]} of those are in {code(t[0] + '/')}" if t else "")
                 + "." if extra else "Nothing else comes along."))
    segs = "".join(f'<div class="seg {c}" style="flex:{len(group[g])}" data-tip="{len(group[g])} files: {esc(lab)}">{len(group[g])}</div>'
                   for g, c, lab in PACK if group[g])
    legend = "".join(f'<li><span class="sw {c}"></span><span class="n">{len(group[g])}</span><span>{esc(lab)}</span></li>'
                     for g, c, lab in PACK if group[g])
    lo = R.left_out(r)
    saving = (f'<p class="where">None of the last groups is used when it runs. Leaving the tests and the files nothing '
              f'refers to out of what you share would make it {esc(R.kb(lo["bytes"]))} smaller.</p>'
              if lo["unused"] or lo["build"] else "")
    more = (f'<div class="stack" role="img" aria-label="{total} files by how they are used">{segs}</div>'
            f'<ul class="legend">{legend}</ul>' + (saving if extra else ""))
    detail = "<h3>Every file, by group</h3>" + "".join(
        fold(f'<span class="sw {c}"></span> {len(group[g])} {esc(lab)}',
             '<ul class="files">' + "".join(f"<li>{code(x['file'])} <span class=\"where\">{esc(R.kb(x['bytes']))}</span></li>"
                                            for x in sorted(group[g], key=lambda x: x["file"])) + "</ul>")
        for g, c, lab in PACK if group[g])
    worth = D.file_concerns(r)  # unknown or mismatched types, archives, symlinks, long files
    if worth:
        detail += "<h3>Files worth a look</h3>" + "".join(
            fold(f"{esc(t)} ({len(fs)})", '<ul class="files">' + "".join(f"<li>{code(f)}</li>" for f in fs) + "</ul>")
            for _, t, fs in worth)
    chip = (n(extra, "extra file"), "fact") if extra else ("Nothing extra", "none")
    return Q("package", title, chip[0], chip[1], answer, more=more, detail=detail)


# ---------------------------------------------------------------- 4 another computer

PORT_PLAIN = {
    "port.path": ("{n} place{s} name a folder on the builder's own computer (like C:\\Users\\name); nobody else has it.", "place"),
    "port.crlf": ("{n} shell script{s} {was} saved with Windows line endings; Mac and Linux can't run {them}.", "script"),
    "port.os": ("{n} script{s} or command{s} only work on one kind of computer (Windows, or Mac and Linux).", "place"),
    "port.backslash": ("{n} file path{s} use{v} backslashes; Mac and Linux read them as part of the name.", "path"),
    "port.exec": ("{n} script{s} {is} run directly but not marked as runnable; Mac and Linux refuse {them}.", "script"),
    "port.python": ("It tells the AI to run <code>python</code> in {n} place{s}. Many Macs and Linux computers only have "
                    "<code>python3</code>, so those steps may fail there.", "place"),
    "graph.case": ("{n} file name{s} only match{v2} if capital letters are ignored; that works on Windows and Mac, not Linux.", "name"),
}


def _fill(tpl, k) -> str:
    one = k == 1
    return tpl.format(n=k, s="" if one else "s", was="was" if one else "were", them="it" if one else "them",
                      v="s" if one else "", v2="es" if one else "", **{"is": "is" if one else "are"})


def q_elsewhere(r) -> Q:
    title = "Will it work on someone else's computer?"
    nd = R.needs_of(r)
    if not nd["measured"]:
        return unmeasured("elsewhere", title)
    count = (1 if nd["undeclared"] else 0) + len(nd["port"])
    b = []
    for check, _, _, pl in nd["port"]:
        b.append(_fill(PORT_PLAIN[check][0], len(pl)) + in_folder([f.get("file") or "" for f in pl]))
    undeclared = [c["command"] for c in nd["commands"] if not c.get("declared")]
    pk = [p["package"] for p in nd["packages"] if not p.get("declared")]
    if undeclared:
        said = [c["command"] for c in nd["commands"] if c.get("declared")]
        b.append(f"It expects these programs to be installed but never says so: <b>{esc(', '.join(undeclared))}</b>."
                 + (f" It says to install {esc(names(said))}." if said else ""))
    if pk:
        b.append(f"Its scripts use add-ons it never lists: <b>{esc(', '.join(pk[:8]))}</b>"
                 + (f" and {len(pk) - 8} more" if len(pk) > 8 else "") + ".")
        count += 0 if undeclared else 1
    if count:
        answer = (f"{'One thing' if count == 1 else ['Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight'][min(count, 8) - 2] + ' things'} "
                  f"could trip it up on another computer.")
        chip, tone = f"{count} to look at", "look"
    else:
        answer = "Yes. Everything it uses is something it says to install, and nothing ties it to one computer."
        chip, tone = "Nothing to look at", "none"
    rows = [f"<tr><td>{code(c['command'])}</td><td class=\"num\">{len(c['uses'])}</td>"
            f"<td>{'\u2713 says to install it' if c.get('declared') else 'never says'}</td></tr>"
            for c in sorted(nd["commands"], key=lambda c: (-len(c["uses"]), c["command"]))]
    detail = ""
    if nd["port"]:
        big = max(nd["port"], key=lambda x: len(x[3]))
        chart = by_file_chart(big[3], "place")
        if chart:
            detail += f"<h3>Where: {esc(big[1].lower())}</h3>" + chart
        for check, name, why, pl in nd["port"]:
            detail += fold(f"{esc(name)} ({len(pl)})", f'<p class="where">{esc(why)}.</p>' + places(pl))
    if rows:
        detail += "<h3>Programs it expects</h3>" + table(
            '<th>Program</th><th class="num">Places</th><th>Does it say to install it?</th>', rows)
    return Q("elsewhere", title, chip, tone, esc(answer), b, detail=detail)


# ---------------------------------------------------------------- 5 other AI tools

FEATURE_PLAIN = {
    "frontmatter": "skill settings only Claude Code reads (claude.ai and the Skills API refuse a skill with them)",
    "claude-words": "wording only Claude Code fills in, such as the folder where the plugin is installed",
    "claude-tool": "tool names only Claude Code has",
    "import": "\u201c@\u201d imports in AGENTS.md, which other tools show to the AI as written",
    "hooks": "hooks, which run on one tool only",
}


def q_hosts(r, targets=()) -> Q:
    title = "Will it work with AI tools other than Claude?"
    rd = R.ready_of(r)
    if not rd["measured"]:
        return unmeasured("hosts", title)
    cov = rd["coverage"]
    have = [c for c in cov if R.has_files(c)]
    claude_only = [c["host"] for c in have] == ["claude"]
    if targets:
        todo = [x for x in R.todo(r, targets) if not x.endswith(": nothing missing.")]
        chip = (f"{len(todo)} missing for your tools", "look") if todo else ("Nothing missing for your tools", "none")
    elif claude_only:
        chip = ("Claude Code only", "fact")
    else:
        chip = (f"{len(have)} of {len(cov)} tools", "fact")
    if claude_only:
        answer = "It is built for Claude Code. Other AI coding tools won't pick up its instructions."
    elif not have:
        answer = "No AI tool finds its files where they sit; each skill has to be installed first."
    else:
        answer = f"{len(have)} of the {len(cov)} AI tools Walkdown knows find its files where they sit."
    b = []
    if targets:
        b += [esc(x) for x in R.todo(r, targets)]
    missing = [c for c in cov if not R.has_files(c)]
    if missing and have:
        b.append("The other tools each look for their own files (most read a file named <code>AGENTS.md</code>). "
                 "None of those files are here.")
    if rd["loose"]:
        b.append(f"{n(len(rd['loose']), 'skill')} sit{'s' if len(rd['loose']) == 1 else ''} where no tool looks; a tool "
                 "reads them once they are installed.")
    for d in rd["differ"]:
        b.append(f"{code(d['file'])} and {code(d['other'])} say different things, so tools that read one see "
                 "different instructions from tools that read the other.")
    for kind, _, _, pl in rd["features"]:
        b.append(f"In {n(len(pl), 'place')} it uses {esc(FEATURE_PLAIN.get(kind, kind))}.")
    tiles = "".join(
        f'<div class="host{" has" if R.has_files(c) else ""}"><b>{"\u2713" if R.has_files(c) else "\u2717"} '
        f'{esc("Others" if c["host"] == "agents-md" else c["name"])}</b><span class="st">'
        + esc((n(c["skills"], "skill") if c["skills"] else "its instructions") if R.has_files(c)
              else ("tools that read AGENTS.md" if c["host"] == "agents-md" else "none of its files"))
        + "</span></div>" for c in cov)
    detail = "".join(fold(f"{esc(name)} ({len(pl)})", f'<p class="where">{esc(why)}.</p>'
                          + places(pl, lambda f: code(f.get("what") or "")))
                     for _, name, why, pl in rd["features"])
    if rd["loose"]:
        detail += fold(f"Skills to install ({len(rd['loose'])})", '<ul class="files">'
                       + "".join(f"<li>{code(s)}</li>" for s in rd["loose"]) + "</ul>")
    return Q("hosts", title, chip[0], chip[1], esc(answer), b, more=f'<div class="hosts">{tiles}</div>', detail=detail)


# ---------------------------------------------------------------- 6 tools

FAMILY_COLS = (("shell", "Run commands", {"Bash", "PowerShell", "Monitor"}),
               ("write", "Change files", {"Write", "Edit", "NotebookEdit", "MultiEdit"}),
               ("web", "Open web pages", {"WebFetch"}), ("search", "Search the web", {"WebSearch"}),
               ("agent", "Start helpers", {"Agent", "Task"}))
FIT_PLAIN = {
    "unused": lambda k: f"{n(k, 'tool')} {'is' if k == 1 else 'are'} allowed but never used by what the words ask for.",
    "missing": lambda k: f"{n(k, 'task')} the words ask for that no allowed tool can do.",
    "inherits": lambda k: f"{n(k, 'helper')} {'has' if k == 1 else 'have'} no tools list, so {'it gets' if k == 1 else 'they get'} every tool.",
    "readonly": lambda k: f"{n(k, 'place')} say{'s' if k == 1 else ''} read-only, but a tool or setting beside it can change files.",
    "loops": lambda k: f"{n(k, 'step')} repeat{'s' if k == 1 else ''} \u201cuntil it works\u201d with no limit stated.",
    "hooks": lambda k: f"{n(k, 'hook')} run{'s' if k == 1 else ''} by {'itself' if k == 1 else 'themselves'} on every message or action.",
}


def q_tools(r) -> Q:
    title = "Does it ask only for the tools it needs?"
    ft = R.fit_of(r)
    if not ft["measured"]:
        return unmeasured("tools", title)
    kinds = {k: p for k, _, _, p in ft["kinds"]}
    look = sum(len(kinds.get(k, [])) for k in ("unused", "missing", "readonly", "loops", "hooks"))
    c = ft["checked"]
    b = [esc(FIT_PLAIN[k](len(p))) for k, _, _, p in ft["kinds"]]
    if not kinds.get("loops"):
        b.append("No step repeats \u201cuntil it works\u201d without a limit.")
    if not ft["hooks"]:
        b.append("It has no hooks (commands that run by themselves on every message or action).")
    if look:
        answer = f"Walkdown found {n(look, 'place')} where the tools and the words don't match, or that keep running."
        chip, tone = f"{look} to look at", "look"
    elif c["with_grants"]:
        answer = "Yes. Every tool it is allowed to use is one it actually uses, and nothing it asks for is missing."
        chip, tone = "Nothing to look at", "none"
    else:
        answer = "None of its skills or helpers lists its tools; they use whatever the AI already has."
        chip, tone = "Nothing to look at", "none"
    helpers = sorted((e for e in entries(r) if e["kind"] == "agent" and e.get("grants") is not None
                      and e["mode"] not in ("unread", "skipped")), key=lambda e: e["name"] or "")
    more = ""
    if helpers:
        head = "<th>Helper</th>" + "".join(f'<th class="c">{esc(t)}</th>' for _, t, _ in FAMILY_COLS)
        rows = []
        for e in helpers:
            tools = {g.split("(")[0] for g in e["grants"]}
            rows.append(f"<tr><td><b>{esc(e['name'])}</b><small class=\"where\">{esc(', '.join(e['grants']))}</small></td>"
                        + "".join(f'<td class="c">{"\u2713" if tools & s else "\u00b7"}</td>' for _, _, s in FAMILY_COLS) + "</tr>")
        more = ("<h3>What each helper may do</h3><p class=\"where\">\u2713 = allowed. Skills don't limit their tools; they "
                "use whatever the AI already has.</p>" + table(head, rows, "tbl grid"))
    detail = "".join(fold(f"{esc(name)} ({len(pl)})", f'<p class="where">{esc(why)}.</p><ul class="places">'
                          + "".join(f"<li>{code(R.fit_parts(k, f)[0])} {esc(R.fit_parts(k, f)[1])}</li>" for f in pl) + "</ul>")
                     for k, name, why, pl in ft["kinds"])
    if ft["hooks"]:
        detail += fold(f"Every hook ({len(ft['hooks'])})", '<ul class="places">'
                       + "".join(f"<li>{code(R.where(h))} {esc(R.hook_text(h))}</li>" for h in ft["hooks"]) + "</ul>")
    return Q("tools", title, chip, tone, esc(answer), b, more=more, detail=detail)


# ---------------------------------------------------------------- 7 finished

def q_clean(r) -> Q:
    title = "Is it finished and up to date?"
    cl = R.clean_of(r)
    if not cl["measured"]:
        return unmeasured("clean", title)
    kinds = {k: p for k, _, _, p in cl["kinds"]}
    un, dated, older, models = (kinds.get(k, []) for k in ("unfinished", "dated", "older", "models"))
    notes = len(un) + len(dated) + len(older)
    words = {"todo": ("\u201cto do\u201d mark", "\u201cto do\u201d marks"), "placeholder": ("placeholder", "placeholders"),
             "draft": ("draft note", "draft notes")}
    parts = [n(k, *words[w]) for w, k in collections.Counter(f["kind"] for f in un).items()]
    if dated:
        parts.append(n(len(dated), "claim tied to a date", "claims tied to a date"))
    if older:
        parts.append(n(len(older), "older tool name"))
    answer = (f"Nearly. {names(parts)[0].upper() + names(parts)[1:]}" + in_folder([f["file"] for f in un + dated + older])
              + "." if parts else "Yes. No unfinished notes, no dates that will go stale, and no older tool names.")
    b = []
    for w in ("todo", "placeholder", "draft"):
        mine = [f for f in un if f["kind"] == w]
        if mine:
            b.append(f"{n(len(mine), *words[w])}: " + ", ".join(where(f) for f in mine[:4]) + (" and more" if len(mine) > 4 else ""))
    if dated:
        b.append(f"{n(len(dated), 'claim tied to a date', 'claims tied to a date')} (published guidance: text tied to a "
                 "date becomes wrong): " + ", ".join(where(f) for f in dated[:3]) + (" and more" if len(dated) > 3 else ""))
    if older:
        b.append(f"{n(len(older), 'tool name')} not in Claude Code's current list: "
                 + ", ".join(f"{code(f['tool'])} (now {code(f['now'])})" for f in older[:3]) + ".")
    b.append(f"It names {n(len(cl['models']), 'AI model version')} fixed in place: "
             + ", ".join(code(m) for m in cl["models"][:6]) + (f" and {len(cl['models']) - 6} more" if len(cl["models"]) > 6 else "")
             + ". A name like \u201csonnet\u201d follows the newest version; a full name stays on one."
             if models else "No AI model names fixed in place.")
    detail = "".join(fold(f"{esc(name)} ({R.clean_count(k, pl, cl['models'])})", f'<p class="where">{esc(why)}.</p><ul class="places">'
                          + "".join(f"<li>{code(R.clean_parts(k, f, True)[0])} {esc(R.clean_parts(k, f, True)[1])}</li>" for f in pl)
                          + "</ul>") for k, name, why, pl in cl["kinds"])
    chip, tone = (n(notes, "note"), "notes") if notes else ("Nothing to look at", "none")
    return Q("clean", title, chip, tone, answer if "<" in answer else esc(answer), b, detail=detail)


# ---------------------------------------------------------------- 8 careful

LEG_PLAIN = {"private-data": "Read your files", "untrusted-content": "Take in content from outside, such as web pages or files you didn't write",
             "external-comms": "Send your data somewhere"}
ALLOW_PLAIN = {"hooks": "runs commands by itself", "context": "adds its own text to the AI's memory before you type",
               "persistence": "can make changes that last after you close the session",
               "network": "connects to the internet", "elevated": "asks for more permissions than the default",
               "mcp": "connects to outside services", "agents": "has helpers with their own tools"}
ROW_PLAIN = {"hidden": "text hidden from people that the AI still reads, and it reads like an instruction",
             "runs": "steps that run code", "secret": "what looks like a saved password or key",
             "out": "steps that read secrets, call out, or share", "lasting": "changes or permissions that last"}
# The same rows, short enough to list several in one sentence.
ROW_SHORT = {"hidden": "hidden instructions", "runs": "steps that run code", "secret": "what looks like a saved key",
             "out": "steps that send data out", "lasting": "lasting changes"}


def marked_line(r, marks=None) -> str:
    """Marking is on review.html only (owner, 2026-10-27); both pages say how far it has got.
    Counts the rule-found places as review.html does, with any mark, own or carried."""
    import review_html  # imported here, as summary_html._place_marks does
    cards = [p for p in review_html.places(r) if not p["model"]]
    if not cards:
        return ""
    _, mark_of = S._place_marks(r, marks)
    done = sum(1 for p in cards if p["id"] in mark_of)
    return (f'<span class="marked">{done} of {n(len(cards), "place")} marked so far.</span> '
            '<a href="review.html">Go through each place and mark it</a>.')


def q_careful(r, stamps, runs_ok, marks=None) -> Q:
    title = "Anything to be careful about?"
    every = D.first_items(r)
    pl = [it for it in every if it["stage"] != 6]
    rs = S.rows(r, pl, marks)
    wording = S.wording_count(r, pl, rs, marks)
    missing = S.not_run(runs_ok)
    failed = S.failed_checks(S.results(stamps, runs_ok))
    total = S.total(rs)
    caveat = (" Not every step worked, so it may have missed some." if failed or missing else "")
    if not rs and missing:  # never "found none" when a step did not run (an outside tester, 2026-10-21)
        steps = (f'the step "{missing[0]}" did not run' if len(missing) == 1 else
                 f'{len(missing)} steps did not run, starting with "{missing[0]}"')
        answer = f"This run did not complete: {steps}, so Walkdown cannot say whether it has any of these."
        chip, tone = ("Not checked", "unmeasured")
    elif not rs:
        answer = "Walkdown found none of the security concerns it looks for." + caveat
        chip, tone = ("Nothing found", "none")
    else:
        if len(rs) == 1:
            row = rs[0]
            k = len(row["places"])
            answer = f"{n(k, 'place')} {'has' if k == 1 else 'have'} {ROW_PLAIN[row['key']]}."
            texts = {(it.get("quote") or "").strip() for it in row["places"]}
            if row["key"] == "hidden" and k > 1 and len(texts) == 1:
                answer += f" {'Both' if k == 2 else 'All'} are the same text."
        else:
            answer = f"Walkdown found {n(total, 'place')} worth a look, of {n(len(rs), 'kind')}: " + names([ROW_SHORT[x["key"]] for x in rs]) + "."
        answer += caveat
        chip, tone = f"{total} to look at", "look"
    b = []
    for row in rs:
        first = row["places"][0]
        src = first.get("src") or {}
        quote = (first.get("quote") or "").replace("<!--", " ").replace("-->", " ").strip()
        say = f"<b>{esc(row['name'])}</b> ({len(row['places'])}): {esc(first.get('where') or R.where(src))}"
        if row["key"] == "hidden" and quote:  # the one repository text the summary quotes (owner, 2026-10-27)
            say += f" says \u201c{esc(quote[:80])}{'\u2026' if len(quote) > 80 else ''}\u201d"
        b.append(say)
    if wording:
        b.append(f"{n(wording, 'more place' if rs else 'place')} {'is' if wording == 1 else 'are'} only wording that shapes how the AI makes "
                 f"decisions. {'It is' if wording == 1 else 'They are'} in the details.")
    line = marked_line(r, marks)
    if line:
        b.append(line)
    legs = {x["leg"]: x["present"] for x in R.fnd(r, "05-capability", "cap.leg")}
    allows = D._allows(r)
    if "05-capability" not in r:  # no boxes to tick when the step that ticks them did not run
        return Q("careful", title, chip, tone, esc(answer), b, detail=careful_detail(r, pl))
    more = '<p class="sub"><b>What it can do</b></p><ul class="can">' + "".join(
        f'<li><span class="mark {"yes" if legs.get(k) else "no"}">{"\u2713" if legs.get(k) else "\u2717"}</span>'
        f"<span>{esc(LEG_PLAIN[k])}</span></li>" for k in R.LEG_NAMES) + "</ul>"
    have = sum(1 for k in R.LEG_NAMES if legs.get(k))
    also = [ALLOW_PLAIN[k] for k, v in allows.items() if v[2] and k in ALLOW_PLAIN]
    more += (f'<p class="where">A tool that does all three could be tricked into sending your data away. This one does '
             + ("all three." if have == 3 else f'{["none", "one", "two"][have]} of the three.')
             + (f" It also {esc(names(also))}." if also else "") + "</p>")
    return Q("careful", title, chip, tone, esc(answer), b, more=more, detail=careful_detail(r, pl))


def place_li(it, pid) -> str:
    """One place on details.html: where (linked to its review card), what was found, Walkdown's note
    on it (a hook's host, what hidden text spells; never a pattern ID), and a model read that
    questions it (review C28)."""
    at = (f'<a href="review.html#{esc(pid)}">{esc(it["where"])}</a>' if pid
          else f'<span class="where">{esc(it["where"])}</span>')
    note = f" {esc(it['note'])}" if it.get("note") and it.get("kind") != "phrase" else ""
    text = (it.get("quote") or "").strip()  # details.html quotes every place (owner, 2026-10-27)
    said = f" <i>“{esc(text[:120])}{'…' if len(text) > 120 else ''}”</i>" if text else ""
    q = f' <span class="questioned">{esc(it["questioned"])}</span>' if it.get("questioned") else ""
    return f"<li>{at} {esc(it['title'])}.{said}{note}{q}</li>"


def careful_detail(r, pl) -> str:
    out = []
    legs = D._leg_ev(r)
    reasons = []
    for k in R.LEG_NAMES:
        ev, total = legs[k]
        if total:
            why = collections.Counter(D._ev_words(e.get("why") or "") for e in ev)
            reasons.append(f"<li><b>{esc(LEG_PLAIN[k])}</b>: {n(total, 'place')} ("
                           + esc("; ".join(f"{v} {w}" for w, v in why.most_common(3))) + ")</li>")
    if "05-capability" in r:  # the credit stays with the three boxes (as on the page before v3)
        out.append("<h3>Why it can do these</h3>"
                   f"<p class=\"where\">The three together are the lethal trifecta, {esc(D.TRIFECTA_LEDE)}</p>"
                   + ("<ul class=\"bul\">" + "".join(reasons) + "</ul>" if reasons else ""))
    rs = S.rows(r, pl)
    if rs:
        card_of, _ = S._place_marks(r, None)
        out.append("<h3>Every place, by kind</h3>" + "".join(
            fold(f"{esc(x['name'])} ({len(x['places'])})", '<ul class="places">' + "".join(
                place_li(it, card_of.get(M.place_key(it))) for it in x["places"]) + "</ul>") for x in rs))
    div = D._divergences(r)
    out.append("<h3>Text hidden from people</h3>")
    if div:
        kinds = collections.Counter(d.get("carrier") for d in div)
        out.append(f"<p>{n(len(div), 'place')} hold text that people don't see when the file is shown, but the AI reads: "
                   + esc(", ".join(f"{v} {D.CARRIER_PLAIN.get(k, k)}" for k, v in kinds.most_common())) + ".</p>")
        out.append(by_file_chart(div, "hidden place"))
        out.append(fold(f"Every hidden place ({len(div)})", places(div, lambda d: esc(D.CARRIER_PLAIN.get(d.get("carrier"), d.get("carrier") or "")))))
    folded = [f for f in R.fnd(r, "02-reader", "read.fold") if D.fold_meaning(f)]  # typography left out
    if folded:
        out.append(f"<p>{n(len(folded), 'line')} read{'s' if len(folded) == 1 else ''} differently once invisible "
                   f"characters or look-alike letters are swapped for plain ones: {esc(D.fold_kinds(folded))}.</p>"
                   + fold(f"Every such line ({len(folded)})", places(folded)))
    script = [x for x in R.fnd(r, "02-reader", "read.script") if "skipped" not in x]
    lang = [x for x in R.fnd(r, "02-reader", "read.language") if "skipped" not in x]
    if script or lang:
        out.append("<p>" + " ".join(x for x in (
            f"{n(len(script), 'stretch', 'stretches')} of text in another alphabet." if script else "",
            f"{n(len(lang), 'passage')} in a language other than English." if lang else "") if x)
            + " Walkdown reads English only, so it could not check what they ask for; read them yourself.</p>"
            + places(script + lang))
    if not (div or folded or script or lang or any(x["key"] == "hidden" for x in rs)):
        out.append("<p>Nothing hidden from people.</p>")
    hits = R.phrase_hits(r)
    if hits:
        aud = {}
        for h in hits:
            aud.setdefault((h["file"], h.get("line")), h.get("audience"))
        who = collections.Counter(D.READ_BY.get(a, "the AI") for a in aud.values())
        by = collections.Counter(h["check"] for h in hits)
        out.append("<h3>Wording that shapes how the AI decides</h3>"
                   f"<p>{n(len(aud), 'line')} match{'es' if len(aud) == 1 else ''} the wording of a risky request. Being "
                   "listed doesn't mean something is wrong; each is a place to read. Who reads them: "
                   + esc(", ".join(f"{k} ({v})" for k, v in who.most_common())) + ".</p>")
        out.append(hbars([(D.GROUP_PLAIN[g][:1].upper() + D.GROUP_PLAIN[g][1:], sum(by[c] for c in cs),
                           f"{sum(by[c] for c in cs)} lines") for g, cs in R.SUBGROUPS.items()]))
    rest = [it for it in pl if S.concern(it) is None]
    if rest:
        groups = collections.OrderedDict()
        for it in rest:
            groups.setdefault(it["title"], []).append(it)
        out.append("<p class=\"sub\"><b>Worth reading first</b></p><ul class=\"bul\">" + "".join(
            f"<li><b>{esc(t)}</b> ({len(v)}): " + ", ".join(f'<span class="where">{esc(it["where"])}</span>' for it in v[:4])
            + (" and more" if len(v) > 4 else "")
            + (f" <i>{esc((v[0].get('quote') or '').strip()[:100])}</i>" if v[0].get("quote") else "") + "</li>"
            for t, v in groups.items()) + "</ul>")
    links = D.link_rows(r)
    if links:
        lk = collections.defaultdict(list)
        for x in links:
            lk[x["host"]].append(x)
        out.append("<h3>Web addresses</h3>"
                   f'<p class="where">{n(len(links), "link")} to {n(len(lk), "site")}. Walkdown gathered them and opened none.</p>'
                   + table('<th>Site</th><th class="num">Links</th><th>Read by</th><th>Named in its docs</th>',
                           [f"<tr><td>{esc(h)}</td><td class=\"num\">{len(v)}</td><td>{esc(', '.join(sorted({x['who'] for x in v})))}</td>"
                            f"<td>{'yes' if v[0].get('documented') else 'no'}</td></tr>"
                            for h, v in sorted(lk.items(), key=lambda kv: (-len(kv[1]), kv[0]))]))
    found = R.fnd(r, "04-phrases", "secret.found")
    sec = [x for x in found if "skipped" not in x and not R.is_test_data(x.get("file")) and x.get("audience") != "test-data"]
    aside = sum(1 for x in found if "skipped" not in x) - len(sec)
    aside_s = f" {n(aside, 'more')} in test data {'is' if aside == 1 else 'are'} set aside." if aside else ""
    if any("skipped" in x for x in found):
        body = "<p>Not checked: no secret scanner was available for this run.</p>"
    elif sec:
        body = (f"<p>{n(len(sec), 'line')} look{'s' if len(sec) == 1 else ''} like a saved password, key, or token. The values are "
                f"never shown.{aside_s}</p>" + places(sec))
    else:
        body = f"<p>No lines look like a saved password, key, or token.{aside_s}</p>"
    out.append("<h3>Passwords and keys</h3>" + body)
    return "".join(out)


# ---------------------------------------------------------------- all eight

def questions(meta, r, stamps, runs_ok, marks=None) -> list[Q]:
    ctx = meta.get("context") or R.DEFAULT_CONTEXT
    return [q_switch(r, ctx), q_memory(r, ctx), q_package(r), q_elsewhere(r), q_hosts(r, meta.get("hosts") or []),
            q_tools(r), q_clean(r), q_careful(r, stamps, runs_ok, marks)]


# ---------------------------------------------------------------- the page shell (both pages)

CSS = """
:root {
  --bg: #f6f5f1; --card: #ffffff; --ink: #1f2328; --muted: #5d6470; --line: #e3e1da;
  --none-bg: #e8f1ea; --none-ink: #2f6b3c; --look-bg: #fbeed6; --look-ink: #8a5a00;
  --fact-bg: #e7eef8; --fact-ink: #2c5282;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100;   /* validated, light, on #ffffff */
  --meter: #2a78d6; --track: #cde2fb; --over: #2a78d6; --grid: #e1e0d9;
  --on-s1: #ffffff; --on-light: #1f2328;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    --bg: #17191c; --card: #212429; --ink: #e8e6e1; --muted: #a3a8b0; --line: #343840;
    --none-bg: #1f3325; --none-ink: #8fd19e; --look-bg: #3a2e14; --look-ink: #f2c46d;
    --fact-bg: #1e2a3a; --fact-ink: #9cbcf0;
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;   /* validated, dark, on #212429 */
    --meter: #3987e5; --track: #184f95; --grid: #2c2c2a;
    --on-s1: #ffffff; --on-light: #111316;
  }
}
:root[data-theme="dark"] {
  --bg: #17191c; --card: #212429; --ink: #e8e6e1; --muted: #a3a8b0; --line: #343840;
  --none-bg: #1f3325; --none-ink: #8fd19e; --look-bg: #3a2e14; --look-ink: #f2c46d;
  --fact-bg: #1e2a3a; --fact-ink: #9cbcf0;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
  --meter: #3987e5; --track: #184f95; --grid: #2c2c2a;
  --on-s1: #ffffff; --on-light: #111316;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 17px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 780px; margin: 0 auto; padding: 28px 16px 48px; }
header h1 { font-size: 2rem; margin: 0 0 4px; letter-spacing: -0.01em; }
.meta { color: var(--muted); font-size: 0.9rem; margin: 0 0 14px; }
.what { margin: 0 0 6px; }
.how { color: var(--muted); font-size: 0.95rem; margin: 0 0 26px; }
h2 { font-size: 1.05rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin: 0 0 10px; }
h3 { font-size: 0.98rem; margin: 18px 0 8px; }
.rows { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
details { background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
summary { list-style: none; cursor: pointer; padding: 14px 16px; display: grid;
          grid-template-columns: 1fr auto; gap: 4px 12px; align-items: start; }
summary::-webkit-details-marker { display: none; }
.q { font-weight: 650; font-size: 1.05rem; }
.a { grid-column: 1 / -1; }
.chip { font-size: 0.8rem; font-weight: 650; padding: 3px 10px; border-radius: 999px; white-space: nowrap; }
.none { background: var(--none-bg); color: var(--none-ink); }
.look, .notes { background: var(--look-bg); color: var(--look-ink); }
.fact { background: var(--fact-bg); color: var(--fact-ink); }
.more { grid-column: 1 / -1; color: var(--muted); font-size: 0.85rem; }
details[open] .more { display: none; }
.body { padding: 0 16px 16px; border-top: 1px solid var(--line); }
.body ul { margin: 12px 0 0; padding-left: 20px; }
.body li { margin: 6px 0; }
.where { color: var(--muted); font-size: 0.85rem; }
.explain { background: var(--bg); border-radius: 8px; padding: 10px 12px; font-size: 0.92rem; margin-top: 12px; }
code { font: 0.9em ui-monospace, "Cascadia Mono", Consolas, monospace; }

/* memory table with meters */
.tablewrap { overflow-x: auto; margin-top: 12px; }
table.mem { width: 100%; border-collapse: collapse; font-size: 0.93rem; }
table.mem th { text-align: left; font-weight: 650; color: var(--muted); font-size: 0.82rem;
               padding: 6px 8px; border-bottom: 1px solid var(--grid); vertical-align: bottom; }
table.mem td { padding: 9px 8px; border-bottom: 1px solid var(--grid); vertical-align: top; }
table.mem th.num, table.mem td.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.cell-meter { width: 24%; min-width: 64px; }
table.mem td.rowname { min-width: 10em; }
@media (max-width: 560px) {
  table.mem { font-size: 0.88rem; }
  table.mem th, table.mem td { padding-left: 5px; padding-right: 5px; }
  .rowname small { display: none; }
}
.pct { font-variant-numeric: tabular-nums; font-size: 0.85rem; }
.meter { height: 8px; background: var(--track); border-radius: 4px; margin-top: 4px; position: relative; }
.meter > span { position: absolute; left: 0; top: 0; bottom: 0; background: var(--meter); border-radius: 4px; min-width: 2px; }
.meter.over > span { width: 100%; }
.meter.over::after { content: ""; position: absolute; right: -6px; top: -3px; border-left: 7px solid var(--meter);
                     border-top: 7px solid transparent; border-bottom: 7px solid transparent; }
.rowname small { display: block; color: var(--muted); font-size: 0.8rem; }

/* skill list room */
.room { display: grid; gap: 10px; margin-top: 8px; }
.room .lbl { display: flex; justify-content: space-between; gap: 10px; font-size: 0.92rem; }

/* package stacked bar */
.stack { display: flex; gap: 2px; height: 30px; margin-top: 14px; background: var(--card); }
.seg { display: flex; align-items: center; justify-content: center; font-size: 0.85rem; font-weight: 650;
       font-variant-numeric: tabular-nums; cursor: default; }
.seg:first-child { border-radius: 4px 0 0 4px; } .seg:last-child { border-radius: 0 4px 4px 0; }
.seg.c1 { background: var(--s1); color: var(--on-s1); } .seg.c2 { background: var(--s2); color: var(--on-light); }
.seg.c3 { background: var(--s3); color: var(--on-light); } .seg.c4 { background: var(--s4); color: var(--on-light); }
.legend { list-style: none; padding: 0; margin: 10px 0 0; display: grid; gap: 6px; }
.legend li { display: flex; gap: 8px; align-items: baseline; margin: 0; }
.sw { width: 12px; height: 12px; border-radius: 3px; flex: none; transform: translateY(1px); }
.sw.c1 { background: var(--s1); } .sw.c2 { background: var(--s2); } .sw.c3 { background: var(--s3); } .sw.c4 { background: var(--s4); }
.legend .n { font-variant-numeric: tabular-nums; font-weight: 650; min-width: 1.6em; text-align: right; }

/* hosts */
.hosts { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-top: 12px; }
.host { border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px; font-size: 0.9rem; }
.host b { display: block; }
.host .st { color: var(--muted); font-size: 0.82rem; }
.host.has { border-color: var(--s1); }
.host.has .st { color: var(--ink); }

/* what it can do */
.can { list-style: none; padding: 0; margin: 12px 0 8px; display: grid; gap: 6px; }
.can li { display: flex; gap: 10px; align-items: baseline; }
.mark { font-weight: 700; width: 1.4em; text-align: center; }
.yes { color: var(--look-ink); } .no { color: var(--none-ink); }

/* tooltip */
[data-tip] { cursor: default; }
#tip { position: fixed; pointer-events: none; z-index: 10; background: var(--ink); color: var(--card);
       font-size: 0.82rem; padding: 6px 9px; border-radius: 6px; max-width: 260px; display: none; }

footer { margin-top: 28px; color: var(--muted); font-size: 0.9rem; }
footer a { color: var(--fact-ink); }

.sec { background: var(--card); border: 1px solid var(--line); border-radius: 12px; padding: 16px; margin: 0 0 14px; }
.sec-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
.sec h2 { font-size: 1.2rem; text-transform: none; letter-spacing: 0; color: var(--ink); margin: 0; }
.sec .a { margin: 6px 0 4px; font-size: 1.02rem; }
.bul { margin: 10px 0 0; padding-left: 20px; } .bul li { margin: 5px 0; }
.places { margin: 8px 0 0; padding-left: 20px; } .places li { margin: 5px 0; overflow-wrap: anywhere; }
.files { list-style: none; padding: 0; margin: 6px 0 0; columns: 2 300px; } .files li { margin: 3px 0; break-inside: avoid; overflow-wrap: anywhere; }
details.fold { border: none; border-radius: 0; margin-top: 10px; }
details.fold > summary { display: block; padding: 6px 0; color: var(--fact-ink); font-weight: 600; font-size: 0.93rem; }
details.fold > summary::before { content: "▸ "; } details.fold[open] > summary::before { content: "▾ "; }
.fold-body { padding: 0 0 4px; }
table.tbl { width: 100%; border-collapse: collapse; font-size: 0.92rem; margin-top: 8px; }
table.tbl th { text-align: left; color: var(--muted); font-size: 0.82rem; font-weight: 650; padding: 6px 8px; border-bottom: 1px solid var(--grid); }
table.tbl td { padding: 7px 8px; border-bottom: 1px solid var(--grid); vertical-align: top; }
table.tbl .num { text-align: right; font-variant-numeric: tabular-nums; }
table.grid .c { text-align: center; } table.grid td.c { font-weight: 700; }
table.grid small { display: block; font-size: 0.78rem; }
.hbars { display: grid; gap: 7px; margin: 10px 0 4px; }
.hb { display: grid; grid-template-columns: minmax(10em, 44%) 1fr; gap: 10px; align-items: center; font-size: 0.86rem; }
.hb-l { overflow-wrap: break-word; min-width: 0; }
.hb-t { display: flex; align-items: center; gap: 6px; }
.hb-f { height: 14px; background: var(--meter); border-radius: 0 4px 4px 0; min-width: 2px; }
.hb-v { font-variant-numeric: tabular-nums; color: var(--muted); white-space: nowrap; }
nav.toc { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 0.9rem; margin: 0 0 18px; }
nav.toc a { color: var(--fact-ink); }

.chip.unmeasured { background: var(--track); color: var(--muted); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; }
.card-head { padding: 14px 16px; display: grid; grid-template-columns: 1fr auto; gap: 4px 12px; align-items: start; }
.sub { margin: 14px 0 0; }
.since { margin: 10px 0 0; font-size: 0.92rem; }
.warnline { background: var(--look-bg); color: var(--ink); border-radius: 12px; padding: 12px 16px; margin-top: 14px; font-size: 0.95rem; }
.warnline a { color: var(--fact-ink); }
"""

SCRIPT = """<div id="tip" role="tooltip"></div>
<script>
(function () {
  var tip = document.getElementById("tip");
  function show(ev) {
    var t = ev.currentTarget.getAttribute("data-tip"); if (!t) return;
    tip.textContent = t; tip.style.display = "block";
    var b = ev.currentTarget.getBoundingClientRect();
    var x = (ev.clientX || b.left) + 12, y = (ev.clientY || b.top) + 14;
    tip.style.left = Math.min(x, window.innerWidth - tip.offsetWidth - 8) + "px"; tip.style.top = y + "px";
  }
  function hide() { tip.style.display = "none"; }
  document.querySelectorAll("[data-tip]").forEach(function (el) {
    el.setAttribute("tabindex", "0");
    el.addEventListener("mousemove", show); el.addEventListener("mouseleave", hide);
    el.addEventListener("focus", show); el.addEventListener("blur", hide);
  });
})();
</script>"""

MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
          "November", "December")


def day(iso) -> str:
    """2026-10-27 as 27 October 2026."""
    try:
        y, m, d = (int(x) for x in str(iso).split("-")[:3])
        return f"{d} {MONTHS[m - 1]} {y}"
    except (ValueError, IndexError):
        return str(iso)


def short_license(r) -> str:
    """The header's license: the name of the top-level license only, never a file's text (the
    summary quotes the repository only for hidden instructions). details.html adds the full
    line (details_html.license_line). A run made before the check says nothing."""
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    if not pin.get("license_checked"):
        return ""
    rows = [x for x in R.fnd(r, "01-inventory", "inv.license")
            if not R.is_test_data(x["file"]) and D._dir(x["file"]) in D.TOP_DIRS]
    lead = [x for x in rows if x.get("source") == "file"] or [x for x in rows if x.get("source") == "field"]
    if not lead:
        return "No license found"
    known = list(dict.fromkeys(x["license"] for x in lead if x.get("license")))
    return "License: " + (", ".join(known) if known else "not one Walkdown recognizes")


def meta_line(meta, r) -> str:
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    h = str(meta.get("hash") or "")[:7]
    version = f"version {h}" if meta.get("hash_kind") == "git" else f"folder {h}"
    lic = short_license(r)
    files = n(pin["files"], "file") if pin.get("files") is not None else ""
    return " \u00b7 ".join(x for x in (f"Checked {day(meta.get('date'))}", version, files, lic) if x)


def page(title, meta, r, body) -> str:
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{esc(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n<main>\n{body}\n</main>\n"
            f"{SCRIPT}\n</body>\n</html>\n")


def card(q: Q) -> str:
    """A question on summary.html: the head always shown; bullets and tables behind "More"."""
    inner = bullets_html(q.bullets) + q.more
    head = (f'<span class="q">{esc(q.question)}</span><span class="chip {q.tone}">{esc(q.chip)}</span>'
            f'<span class="a">{q.answer}</span>')
    if not inner:
        return f'<li id="{q.id}"><div class="card"><div class="card-head">{head}</div></div></li>'
    return (f'<li id="{q.id}"><details class="card"><summary>{head}<span class="more">More \u203a</span></summary>'
            f'<div class="body">{inner}</div></details></li>')


def section(q: Q) -> str:
    """A question on details.html: everything, the long lists folded."""
    return (f'<section id="{q.id}" class="sec"><div class="sec-head"><h2>{esc(q.question)}</h2>'
            f'<span class="chip {q.tone}">{esc(q.chip)}</span></div><p class="a">{q.answer}</p>'
            f"{bullets_html(q.bullets)}{q.more}{q.detail}</section>")


def since_line(changes) -> str:
    """Under question 2: the cost since the earlier run of the same repository (slice 6)."""
    line = (changes or {}).get("cost_line")
    if not line or not line.startswith("cost: "):
        return ""
    return f'<p class="since">Since run {esc(changes["since"])}: {esc(line[len("cost: "):])}.</p>'


def not_checked(r, stamps, notes, runs_ok) -> str:
    """details.html's last section: what this run did not check, plainly (steps that did not work,
    checks skipped in this run as render.glance names them, the optional model reads), then every
    limit."""
    steps = S.failed_steps(stamps, runs_ok)
    soft = [x for x in R.fnd(r, "06-soft", "soft.label") if "skipped" not in x and x.get("label")]
    lines = [f"Not every step worked: {esc('; '.join(steps))}. A step that did not work can miss places." if steps
             else "Every step ran and passed its own checks."]
    skipped, _ = R.glance(r, notes, stamps, runs_ok)
    if skipped:
        lines.append("Skipped in this run, most often because an optional tool is not installed:"
                     '<ul class="bul">' + "".join(f"<li>{esc(x)}</li>" for x in skipped) + "</ul>")
    if not soft:
        lines.append("The optional model reads (a second opinion from an AI) were not run.")
    lim = R.limits(r, notes, stamps, runs_ok)
    return ('<section id="limits" class="sec"><div class="sec-head"><h2>What Walkdown didn\'t check</h2></div>'
            + "".join(f'<div class="a">{x}</div>' if "<ul" in x else f'<p class="a">{x}</p>' for x in lines)
            + fold(f"Every limit of this run ({len(lim)})", '<ul class="places">'
                   + "".join(f"<li>{esc(x)}</li>" for x in lim) + "</ul>") + "</section>")


def changes_section(changes) -> str:
    """details.html: what changed since the earlier run, in Walkdown's words (drift)."""
    if not changes or (changes.get("same") and not changes.get("differs")):
        return ""
    lines = "".join(f"<li>{esc(x[:1].upper() + x[1:])}</li>" for x in changes.get("lines", []))
    return (f'<section id="changes" class="sec"><div class="sec-head"><h2>What changed since run {esc(changes["since"])}</h2>'
            f'</div><ul class="bul">{lines}</ul><p class="where">Every change, file by file: '
            '<a href="changes.md">changes.md</a>.</p></section>')
