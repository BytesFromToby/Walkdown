"""The four questions both pages answer, as data. Spec: specs/report.SPEC.md, glance.

Report v3 (owner, 2026-10-27: "glance and know"): for someone with no computer skills, the same
four questions on summary.html and details.html, each with a chip (a short label), a one-line
answer, plain bullets, and on details.html everything behind it. Every sentence is a template
filled from findings the stages already made; nothing here detects or judges. Token figures live
in Size and Shape's memory part only. HTML here escapes all repository text.
"""
from __future__ import annotations

import collections
import html
import itertools
import posixpath
import re
from dataclasses import dataclass, field

import details_html as D
import marks as M
import qaview
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
    details_body: str = ""      # HTML for details.html in place of bullets, more, and detail (Size and Shape, R21)
    none: list = field(default_factory=list)  # R32: what its checks did not find, HTML, escaped; details.html only
    face: str = ""             # HTML on the card's face (summary) and at the top of its section (details): a chart, boxes (R33)


# ---------------------------------------------------------------- the visual pass (R33, prototype 2026-11-07)
# One glyph per section, the same on both pages, so a reader coming from the summary recognizes where they landed.
# Stroke icons in the text colour: identity only, no colour of their own (colour on the pages means a kind, never a grade).
_ICON_PATHS = {
    "can": '<path d="M12 3l8 3v6c0 4.5-3.5 7.8-8 9-4.5-1.2-8-4.5-8-9V6z"/>',
    "examined": '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    "size": '<path d="M3 7l9-4 9 4v10l-9 4-9-4z"/><path d="M3 7l9 4 9-4M12 11v10"/>',
    "transfer": '<rect x="3" y="4" width="8" height="6" rx="1"/><rect x="13" y="14" width="8" height="6" rx="1"/>'
                '<path d="M11 7h5a3 3 0 0 1 3 3v2M13 17H8a3 3 0 0 1-3-3v-2"/>',
    "tools": '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.6 2.6-2.1-.4-.4-2.1z"/>',
    "careful": '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/>',
    "misalign": '<rect x="3" y="9" width="18" height="6" rx="1"/><path d="M7 9v3M11 9v3M15 9v3M19 9v3"/>',
    "changes": '<path d="M4 12a8 8 0 0 1 14-5M20 12a8 8 0 0 1-14 5"/><path d="M18 3v4h-4M6 21v-4h4"/>',
    "limits": '<circle cx="12" cy="12" r="8"/><path d="M6.5 6.5l11 11"/>',
}


def icon(sid) -> str:
    """The section's glyph, or nothing for a section that has none."""
    d = _ICON_PATHS.get(sid)
    if not d:
        return ""
    return f'<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">{d}</svg>'


def careful_face(ls, wording) -> str:
    """The careful card's face: one dot per place, red, then yellow, then blue, each colour followed by its count; the
    wording-only places are blue. Counts only, the same ones the lines under it give; nothing is added up across colours."""
    counts = {c: sum(len(x["places"]) for x in ls if x["color"] == c) for c in COLORS}
    counts["blue"] += wording
    if not any(counts.values()):
        return ""
    groups = []
    for c in COLORS:
        k = counts[c]
        if k:
            dots = "".join(f'<i class="kd {c}"></i>' for _ in range(min(k, 24))) + ('<i class="kd-more">\u2026</i>' if k > 24 else "")
            groups.append(f'<span class="kgroup">{dots}<span class="kn">{k}</span></span>')
    label = ", ".join(f"{counts[c]} {c}" for c in COLORS if counts[c])
    return f'<div class="face kinds" role="img" aria-label="{esc(label)}">' + "".join(groups) + "</div>"


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


# The two pages linked part to part (owner, 2026-11-05, R1): a "Details →" on the summary opens details.html at the part, and
# every fold there has a "← Summary" back. `go(target)` marks a line for a button: summary.html draws it, details.html drops it.
# A fold's back link names "@" until `section` gives it the question's id; "" is the top of the summary.
GO_MARK = re.compile(r"<!--go:([a-z0-9-]+)-->")
GO_WORD, BACK_WORD = "Details →", "← Summary"  # owner, 2026-11-05: B, "simple, and the arrows"


def go(target) -> str:
    return f"<!--go:{target}-->"


def slug(*parts) -> str:
    """An id from words: lower case, anything but letters and digits a hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", "-".join(str(p) for p in parts).lower()).strip("-")


def back(home="@") -> str:
    return f'<a class="back" href="summary.html{"#" + home if home else ""}">{BACK_WORD}</a>'


def fold(summary_html, inner, open_=False, fid=None, home="@", cls="fold") -> str:
    """A fold on details.html, closed (owner, 2026-11-05: every fold closed but the one linked to). Its back link is on its
    own title line, shown while it is open, so a fold inside another never shows two side by side."""
    return (f'<details class="{cls}"' + (f' id="{fid}"' if fid else "") + (" open" if open_ else "")
            + f'><summary>{summary_html}{back(home)}</summary><div class="fold-body">{inner}</div></details>')


# R32 (owner, 2026-11-07: "things not found (say an API Key written plainly is not found) I do not want that fact in the
# summary. I can see the use in details, listed after found things in each section, a not found section that starts
# collapsed."; "Keep the question, drop the card's answer line"; "yes drop the chip"): the summary says what was found; what
# a check did not find is a line in the closed fold at the end of its section on details.html.
NOT_FOUND = "Not found"


def not_found(lines, sid) -> str:
    """details.html, the end of a section (R32): the closed fold of what its checks did not find. Nothing when there is none."""
    return (fold(f"{NOT_FOUND} ({len(lines)})", bullets_html(lines), fid=f"{sid}-none") if lines else "")


def part(pid, title, inner, home="@") -> str:
    """A part of a question on details.html, folded under its heading."""
    return fold(f"<h3>{esc(title)}</h3>", inner, fid=pid, home=home, cls="fold part")


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
        others = n(len(c) - len(top), "other file")
        bars.append((others, rest, f"{n(rest, what)} in {others}"))
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
    return R.fnd(r, R.BUILDER, "trig.entry")


def subject(name) -> str:
    """The repository's name to start a sentence, its first letter a capital (owner, 2026-11-05, R2)."""
    name = str(name or "")
    return name[:1].upper() + name[1:] if name else "It"


def what_it_is(r, name=None) -> str:
    """The one sentence under the name: what the repository holds, starting with its name (owner, 2026-11-05, R2:
    "<Name> is a plugin for Claude Code: ..."; "<Name> holds ..."). Nothing when the inventory did not run."""
    if "02.1-inventory" not in r:
        return ""
    who = esc(subject(name))
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
                 for f in R.fnd(r, "02.1-inventory", "inv.file"))
    if not parts:
        return f"{who} holds no skills, commands, or helpers. Walkdown read its instruction files."
    lead = f"{who} is a plugin for Claude Code: " if plugin else f"{who} holds "
    return lead + names(parts) + "."


# ---------------------------------------------------------------- Misalignment (R13)

# R13 (owner, 2026-11-05: "Let's adopt the agentskills.io specs. Forget anthropic specific ones."; "New section called 'Skill
# Formatting' under a new section called 'Misalignment'. Temp name while we build it."): after the questions on both pages.
# It took the place of question 1, "Will its skills switch on when they should?", and of "Nitty gritty" (R9), whose only
# catch, a setting no tool knows, is one of the settings the standard doesn't define.
MIS_LEDE = ("Where its skills differ from the Agent Skills standard, the open format for skills that many AI tools read "
            "(agentskills.io).")
ALIKE_NONE = "No two skills describe themselves alike."


def misalign_unmeasured(stop=None) -> str:
    return (f'Not measured: the run stopped after the step "{R.stop_plain(stop)}", as asked.' if R.stopped_left(stop)
            else "Not measured: this run was made before this check, or a step did not run.")


def format_line(m, g) -> str:
    """Skill Formatting's sentence for one group, HTML: at the head of its fold on details.html (R24; on the summary, a line
    each with its Details button, R13 to R23)."""
    pl = m["groups"][g]
    c = len({f["file"] for f in pl})
    if g == "bare":
        return (f"{n(c, 'skill')} {'has' if c == 1 else 'have'} no header at the top. The standard requires one, with a name "
                "and a description.")
    if g == "yaml":
        return (f"{n(c, 'skill')} {'has a header' if c == 1 else 'have headers'} not in the expected format (YAML), so a tool "
                f"that follows the standard can't read {'it' if c == 1 else 'them'}.")
    if g == "twice":  # R17 (owner, 2026-11-05: "duplicates only")
        k, keys = len(pl), collections.Counter(f["key"] for f in pl).most_common()
        return (f"{n(k, 'setting')} {'is' if k == 1 else 'are'} set more than once in {'its' if k == 1 else 'their'} header: "
                + ", ".join(code(x) + (f" ({m_})" if m_ > 1 else "") for x, m_ in keys[:4])
                + (", and others" if len(keys) > 4 else "") + ". YAML allows each setting once, and some tools quietly keep "
                "just the last value.")
    if g == "name":
        return (f"{n(c, 'skill name')} {"doesn't" if c == 1 else "don't"} follow the standard: lowercase letters, digits, and "
                "single hyphens, at most 64 characters, and the same as the skill's folder.")
    if g == "description":
        return (f"{n(c, 'skill description')} {"doesn't" if c == 1 else "don't"} follow the standard: every skill has one, of at "
                "most 1,024 characters.")
    if g == "compatibility":
        return f"{n(len(pl), 'compatibility note')} {'is' if len(pl) == 1 else 'are'} over the standard's 500 characters."
    keys = collections.Counter(f["key"] for f in pl).most_common()
    return (f"{n(len(pl), 'setting')} the standard doesn't define: "
            + ", ".join(code(x) + (f" ({m_})" if m_ > 1 else "") for x, m_ in keys[:4]) + (", and others" if len(keys) > 4 else "")
            + ".")


def format_none(m) -> str:
    return "No skills here; the standard covers skills only." if not m["skills"] else "Every skill's header follows the standard."


def alike_line(m) -> str:
    c = len(m["alike"])
    return f"{n(c, 'pair')} of skills with descriptions so alike that the AI may pick the wrong one."


MIS_SUB = "Things that are not standard but are not security flaws."


def misalign_card(r, stop=None) -> Q:
    """summary.html, the last card (R24, owner 2026-11-06: "For misalignment. Should be another section like Is this transferable to other machines? but no expand. the subtitle says 'Things that are not standard but are not security flaws. (# of issues)'"): no label and nothing to open; its Details button opens the
    section on details.html, which holds every line and place. Issues: the places that differ from the standard and the
    pairs of skills described alike."""
    m = R.misalign_of(r)
    issues = sum(len(v) for v in m["groups"].values()) + len(m["alike"])
    if not m["measured"]:
        said = misalign_unmeasured(stop)
    elif not m["skills"] or not issues:  # R32: no skills, or none that differ: the card is its question
        said = ""
    else:
        said = f"{MIS_SUB} ({n(issues, 'issue')})"
    return Q("misalign", "Misalignment", "", "fact", esc(said), detail=misalign_detail(r, stop))


def misalign_detail(r, stop=None) -> str:
    """details.html, after the questions: Misalignment, folded. Closed, the counts; inside, the standard and its six fields,
    then a fold for each Skill Formatting group, its sentence and then every place, and one for the skills too alike."""
    m = R.misalign_of(r)
    if not m["measured"]:
        said = misalign_unmeasured(stop)
        return fold_section("misalign", icon("misalign") + "<h2>Misalignment</h2>", f'<span class="a">{esc(said)}</span>',
                            f'<p class="where">{esc(said)}</p>', "misalign")
    g = m["groups"]
    total = sum(len(v) for v in g.values())
    none = []  # R32
    answer = f"Skill Formatting: {n(total, 'place')} to look at." if total else ""
    if not total:
        none.append(format_none(m))
    if m["skills"] > 1 and m["alike"]:
        answer += f" Descriptions too alike: {n(len(m['alike']), 'pair')}."
    elif m["skills"] > 1:
        none.append(ALIKE_NONE)
    answer = answer.strip()
    inside = (f'<p class="where">{esc(MIS_LEDE)} A skill\'s header is the block between the two {code("---")} lines at the '
              f"top of its SKILL.md, written in YAML: lines such as {code('name: my-skill')}. The standard: "
              f'<a href="{R.SPEC_LINK}">{R.SPEC_LINK}</a>. Its six settings: ' + ", ".join(code(k) for k in R.SPEC_FIELDS)
              + ". Blank lines before the header and a byte-order mark are not called out; a header below blank lines is "
              "still checked.</p>" + ("<h3>Skill Formatting</h3>" if total else ""))
    folds = "".join(fold(f"{esc(title)} ({len(g[k])})", f'<p class="lead">{format_line(m, k)}</p><ul class="places">' + "".join(
        f"<li>{code(R.misalign_place(k, f)[0])} " + (code(f["key"]) if k == "fields" else esc(R.misalign_place(k, f)[1])) + "</li>"
        for f in g[k]) + "</ul>", fid="misalign-" + k, home="misalign") for k, title in R.FORMAT_GROUPS if g[k])
    inside += folds
    if m["skills"] > 1 and m["alike"]:
        _, name, why = next(x for x in R.TRIG_KINDS if x[0] == "overlap")
        inside += "<h3>Descriptions too alike</h3>" + fold(
            f"{n(len(m['alike']), 'pair')}", f'<p class="lead">{esc(alike_line(m))}</p><p class="where">{esc(name)}: {esc(why)}.</p>'
            '<ul class="places">'
            + "".join(f"<li>{code(f['file'])} and {code(f['other'])}: {esc(R.alike_text(f))}</li>" for f in m["alike"]) + "</ul>",
            fid="misalign-alike", home="misalign")
    inside += not_found([esc(x) for x in none], "misalign").replace('href="summary.html#@"', 'href="summary.html#misalign"')
    return fold_section("misalign", icon("misalign") + "<h2>Misalignment</h2>", f'<span class="a">{esc(answer)}</span>' if answer
                        else "", inside, "misalign")


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
    files = R.fnd(r, R.BUILDER, "trig.entry")
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
               + (f"A <b>local AI</b> estimate of {ctx:,} tokens represents a typical high-end computer; "  # R19
                  if ctx == LOCAL else "" if ctx == CLAUDE
                  else f"<b>Your AI</b> holds about {ctx:,} tokens at once (set with --context); ")
               + ("<b>Claude</b> holds about 200,000 tokens at once." if ctx == CLAUDE else "<b>Claude</b> holds about 200,000.")
               + " Token counts are estimates.</div>")  # R20 (owner, 2026-11-06)
    more = explain + memory_table(r, ctx)
    lst = (R.trigger_of(r).get("listing") or {})
    if lst.get("skills"):
        tok = round(lst["listing_chars"] / R.BYTES_PER_TOKEN)
        room = [(f"{ctx_name(ctx)}: about {round(ctx * SHARE):,} tokens of room", tok, ctx * SHARE)]
        if ctx != CLAUDE:
            room.append((f"Claude: about {round(CLAUDE * SHARE):,} tokens of room", tok, CLAUDE * SHARE))
        more += ('<h3 id="memory-room">Room for the list of skills' + go("memory-room") + "</h3><p class=\"where\">The AI keeps a short list of every skill you have "
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
    maxes = sorted((x for x in R.fnd(r, R.BUILDER, "cap.context") if x["tier"] == "skill-max"),
                   key=lambda x: (-x["tokens"], x["file"]))
    detail = ""
    if len(maxes) > 1:
        kw = lambda x: {"agent": "helper"}.get(x.get("kind"), x.get("kind") or "")  # noqa: E731
        detail = part("memory-sizes", "How big each skill and helper gets", "<p class=\"where\">Tokens each one uses at its fullest: its "
                  "own instructions plus every file it reads. Only the one in use is loaded.</p>"
                  + hbars([(f"{short_name(x['file'])} ({kw(x)})", x["tokens"],
                            f"{x['file']}: {x['tokens']:,} tokens, {x['tokens'] * 100 / ctx:.0f}% of {ctx_name(ctx, short=True)}")
                           for x in maxes]))
    more = more.replace("</table></div>", "</table></div>" + f'<p class="go-row">{go("memory-sizes" if detail else "size")}</p>', 1)
    return Q("memory", title, ("under 1%" if p < 1 else f"up to {R.pct(top, ctx)}") if p <= 100 else "more than fits", "fact", esc(answer),
             more=more, detail=detail)


# ---------------------------------------------------------------- 3 package

PACK = (("work", "c1", "do the work: the skills, the helpers, and the files they read"),
        ("people", "c2", "notes for people: the license, readme, and other documents"),
        ("build", "c3", "tests and tools for building it"),
        ("unused", "c4", "files not linked or referred to"))  # owner, 2026-11-05 (R14), was "nothing refers to them"
WORK = ("entry", "project", "on-demand", "maybe", "run", "config")


def q_package(r) -> Q:
    title = "What comes in the package?"
    ship = R.fnd(r, R.BUILDER, "cap.ship")
    if not ship:
        return unmeasured("package", title)
    group = collections.defaultdict(list)
    for x in ship:
        group["work" if x["group"] in WORK else x["group"]].append(x)
    total, extra = len(ship), len(ship) - len(group["work"])
    extra_files = [x["file"] for g in ("people", "build", "unused") for x in group[g]]
    t = top_folder(extra_files)
    answer = (f"{len(group['work'])} of its {total} files do the work."
              + (f" The other {extra} come along without being used" + (f", and {t[1]} of those are in {code(t[0] + '/')}" if t else "")
                 + "." if extra else ""))
    none = [] if extra else ["Every file does the work; nothing else comes along."]  # R32
    segs = "".join(f'<div class="seg {c}" style="flex:{len(group[g])}" data-tip="{n(len(group[g]), "file")}: {esc(lab)}">{len(group[g])}</div>'
                   for g, c, lab in PACK if group[g])
    legend = "".join(f'<li><span class="sw {c}"></span><span class="n">{len(group[g])}</span><span>{esc(lab)}</span>{go("package-" + g)}</li>'
                     for g, c, lab in PACK if group[g])
    lo = R.left_out(r)
    saving = (f'<p class="where">None of the last groups is used when it runs. Leaving the tests and the files not linked '
              f'or referred to out of what you share would make it {esc(R.kb(lo["bytes"]))} smaller.</p>'
              if lo["unused"] or lo["build"] else "")
    face = (f'<div class="face"><div class="stack" role="img" aria-label="{total} files by how they are used">{segs}</div>'
            f'<ul class="legend">{legend}</ul></div>')  # R33: the bar and its legend on the card's face
    more = saving if extra else ""
    detail = part("package-files", "Every file, by group", "".join(
        fold(f'<span class="sw {c}"></span> {len(group[g])} {esc(lab)}',
             '<ul class="files">' + "".join(f"<li>{code(x['file'])} <span class=\"where\">{esc(R.kb(x['bytes']))}</span></li>"
                                            for x in sorted(group[g], key=lambda x: x["file"])) + "</ul>", fid="package-" + g)
        for g, c, lab in PACK if group[g]))
    worth = D.file_concerns(r)  # unknown or mismatched types, archives, symlinks, long files
    if worth:
        detail += part("package-worth", "Files worth a look", "".join(
            fold(f"{esc(t)} ({len(fs)})", '<ul class="files">' + "".join(f"<li>{code(f)}</li>" for f in fs) + "</ul>",
                 fid=slug("package-worth", rid))
            for rid, t, fs in worth))
    chip = (n(extra, "extra file"), "fact") if extra else ("", "none")  # R32: no "Nothing extra"
    return Q("package", title, chip[0], chip[1], answer, more=more, detail=detail, none=none, face=face)


# ---------------------------------------------------------------- 1 size and shape

PACK_HEAD, MEMORY_HEAD = "What comes in the package", "How much of the AI's memory it uses"


def joined(qid, title, parts) -> Q:
    """One question made of parts, each a Q under its heading (`h3.piece`): its More (boxes, bars, tables) first, then its
    lines; on details.html each part's detail follows it (R21, R22). The chips joined by " \u00b7 ", the answers on lines of
    their own; "look" when a part has something to look at, else "fact" when one is a measure. Not measured when no part
    is; a part not measured says so in the answer and has no heading."""
    measured = [(q, head) for q, head in parts if q.tone != "unmeasured"]
    if not measured:
        return unmeasured(qid, title)
    tones = [q.tone for q, _ in measured if q.chip]
    # a part with nothing found has no heading on either page (R32): its not-found lines go to the section's fold
    piece = lambda q, h, d=False: (f'<h3 class="piece">{esc(h)}</h3>' + q.more + bullets_html(q.bullets)  # noqa: E731
                                   if q.more or q.bullets or q.answer or (d and q.detail) else "")
    return Q(qid, title, " \u00b7 ".join(q.chip for q, _ in measured if q.chip),
             "look" if "look" in tones else "fact" if "fact" in tones else (tones[0] if tones else "none"),
             "<br>".join(q.answer for q, _ in parts if q.answer),
             more="".join(piece(q, h) for q, h in measured), detail="".join(q.detail for q, _ in measured),
             details_body="".join(piece(q, h, True) + q.detail for q, h in measured),
             none=[x for q, _ in measured for x in q.none], face="".join(q.face for q, _ in measured))


def q_size(r, ctx) -> Q:
    """Size and Shape (R21, owner 2026-11-06: "combine the How much of the AI's memory does it use? and What comes in the package? into one section ... Let's call it Size and Shape for now"; "the what comes in the package comes first. the 4 notes on what the bar is should be 2 columns"):
    the package part, then the memory part, each under its heading; on details.html each part's detail follows it."""
    return joined("size", "Size and Shape", ((q_package(r), PACK_HEAD), (q_memory(r, ctx), MEMORY_HEAD)))


# ---------------------------------------------------------------- 4 another computer

# One sentence per kind of place, as a template (Library/tools.yaml, `port_kinds`).
PORT_PLAIN = {k["check"]: k["plain"] for k in R.TOOLS_TABLE["port_kinds"]}
# The systems each kind trips (Library/tools.yaml: `systems`; `port.os` by its program's `os`, `os_systems`), R22.
PORT_SYSTEMS = {k["check"]: tuple(k.get("systems") or ()) for k in R.TOOLS_TABLE["port_kinds"]}
OS_SYSTEMS = {k: tuple(v) for k, v in R.TOOLS_TABLE["os_systems"].items()}
SYSTEMS = (("linux", "Linux"), ("windows", "Windows"), ("mac", "Mac"))


def system_hits(nd) -> dict:
    """{system: how many kinds found trip it} for Linux, Windows, and Mac (R22)."""
    hits = {s: 0 for s, _ in SYSTEMS}
    for check, _, _, pl in nd["port"]:
        trips = ({s for f in pl for s in OS_SYSTEMS.get(f.get("os"), ())} if check == "port.os"
                 else set(PORT_SYSTEMS.get(check, ())))
        for s in trips:
            hits[s] += 1
    return hits


def system_tiles(nd) -> str:
    """The boxes for Linux, Windows, and Mac (owner, 2026-11-06, R22): a yellow outline and the count of kinds found that trip
    the system. A system nothing found trips has no box (R32: it is a line under Not found on details.html). Personal paths
    and programs it never says to install trip any other computer, whatever its system, so they are in the lines under the
    boxes and in no box."""
    hits = system_hits(nd)
    if not any(hits.values()):
        return ""
    return '<div class="hosts systems">' + "".join(
        f'<div class="host"><b>\u2717 {esc(name)}</b><span class="st">{esc(n(hits[s], "thing") + " to look at")}</span></div>'
        for s, name in SYSTEMS if hits[s]) + "</div>"


def _fill(tpl, k) -> str:
    """A Library sentence for a count of k: {n} is k; the other braces take the singular or plural
    form of the word the sentence needs."""
    one = k == 1
    return tpl.format(n=k, s="" if one else "s", was="was" if one else "were", them="it" if one else "them",
                      v="s" if one else "", v2="es" if one else "", has="has" if one else "have",
                      it_gets="it gets" if one else "they get", itself="itself" if one else "themselves",
                      **{"is": "is" if one else "are"})


def q_elsewhere(r) -> Q:
    title = "Will it work on someone else's computer?"
    nd = R.needs_of(r)
    if not nd["measured"]:
        return unmeasured("elsewhere", title)
    count = (1 if nd["undeclared"] else 0) + len(nd["port"])
    b = []
    for check, _, _, pl in nd["port"]:
        b.append(_fill(PORT_PLAIN[check], len(pl)) + in_folder([f.get("file") or "" for f in pl]) + go(slug("elsewhere", check)))
    undeclared = [c["command"] for c in nd["commands"] if not c.get("declared")]
    pk = [p["package"] for p in nd["packages"] if not p.get("declared")]
    if undeclared:
        said = [c["command"] for c in nd["commands"] if c.get("declared")]
        b.append(f"It expects these programs to be installed but never says so: <b>{esc(', '.join(undeclared))}</b>."
                 + (f" It says to install {esc(names(said))}." if said else "") + go("elsewhere-programs"))
    if pk:
        b.append(f"Its scripts use add-ons it never lists: <b>{esc(', '.join(pk[:8]))}</b>"
                 + (f" and {len(pk) - 8} more" if len(pk) > 8 else "") + ".")
        count += 0 if undeclared else 1
    none = []
    if count:
        answer = (f"{'One thing' if count == 1 else ['Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight'][min(count, 8) - 2] + ' things'} "
                  f"could trip it up on another computer.")
        chip, tone = f"{count} to look at", "look"
    else:  # R32: no answer line and no chip; the line is under Not found
        answer, chip, tone = "", "", "none"
        none.append("Everything it uses is something it says to install, and nothing ties it to one computer.")
    clear = [name for s, name in SYSTEMS if not system_hits(nd)[s]]
    if clear:
        none.append(f"Nothing found against {names(clear)}.")
    rows = [f"<tr><td>{code(c['command'])}</td><td class=\"num\">{len(c['uses'])}</td>"
            f"<td>{'\u2713 says to install it' if c.get('declared') else 'never says'}</td></tr>"
            for c in sorted(nd["commands"], key=lambda c: (-len(c["uses"]), c["command"]))]
    detail = ""
    if nd["port"]:
        big = max(nd["port"], key=lambda x: len(x[3]))
        chart = by_file_chart(big[3], "place")
        if chart:
            detail += part("elsewhere-where", f"Where: {big[1].lower()}", chart)
        for check, name, why, pl in nd["port"]:
            detail += fold(f"{esc(name)} ({len(pl)})", f'<p class="where">{esc(why)}.</p>' + places(pl), fid=slug("elsewhere", check))
    if rows:
        detail += part("elsewhere-programs", "Programs it expects", table(
            '<th>Program</th><th class="num">Places</th><th>Does it say to install it?</th>', rows))
    tiles = system_tiles(nd)
    return Q("elsewhere", title, chip, tone, esc(answer), b, detail=detail, none=[esc(x) for x in none],
             face=f'<div class="face">{tiles}</div>' if tiles else "")  # R33; R32: no box, no face, when nothing trips


# ---------------------------------------------------------------- 5 other AI tools

# What each one-tool feature is, in a phrase (Library/hosts.yaml, `feature_kinds`).
FEATURE_PLAIN = {k["kind"]: k["plain"] for k in R.HOST_TABLE["feature_kinds"]}


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
        chip = (f"{len(todo)} missing for your tools", "look") if todo else ("", "none")  # R32
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
    b, none = [], []
    if targets:
        b += [esc(x) for x in R.todo(r, targets) if not x.endswith(": nothing missing.")]
        none += [esc(x) for x in R.todo(r, targets) if x.endswith(": nothing missing.")]
    missing = [c for c in cov if not R.has_files(c)]
    if missing and have:  # R32: under Not found
        none.append("The other tools each look for their own files (most read a file named <code>AGENTS.md</code>). "
                    "None of those files are here: " + esc(names(["tools that read AGENTS.md" if c["host"] == "agents-md"
                                                                   else c["name"] for c in missing])) + ".")
    if rd["loose"]:
        b.append(f"{n(len(rd['loose']), 'skill')} sit{'s' if len(rd['loose']) == 1 else ''} where no tool looks; a tool "
                 "reads them once they are installed." + go("hosts-loose"))
    for d in rd["differ"]:
        b.append(f"{code(d['file'])} and {code(d['other'])} say different things, so tools that read one see "
                 "different instructions from tools that read the other.")
    for kind, _, _, pl in rd["features"]:
        b.append(f"In {n(len(pl), 'place')} it uses {esc(FEATURE_PLAIN.get(kind, kind))}." + go(slug("hosts", kind)))
    tiles = "".join(  # a tool that finds none of its files has no box (R32)
        f'<div class="host has"><b>\u2713 {esc("Others" if c["host"] == "agents-md" else c["name"])}</b><span class="st">'
        + esc(n(c["skills"], "skill") if c["skills"] else "its instructions") + "</span></div>" for c in cov if R.has_files(c))
    detail = ""  # in the order of the summary's lines (R11): the skills to install, then each one-tool feature
    if rd["loose"]:
        detail += fold(f"Skills to install ({len(rd['loose'])})", '<ul class="files">'
                       + "".join(f"<li>{code(s)}</li>" for s in rd["loose"]) + "</ul>", fid="hosts-loose")
    detail += "".join(fold(f"{esc(name)} ({len(pl)})", f'<p class="where">{esc(why)}.</p>'
                           + places(pl, lambda f: code(f.get("what") or "")), fid=slug("hosts", kind))
                      for kind, name, why, pl in rd["features"])
    return Q("hosts", title, chip[0], chip[1], esc(answer), b, more=f'<div class="hosts">{tiles}</div>' if tiles else "",
             detail=detail, none=none)


SYSTEMS_HEAD, TOOLS_HEAD = "Operating systems", "Other AI tools"


def q_transfer(r, targets=()) -> Q:
    """Is this transferable to other machines? (R22, owner 2026-11-06: "let's combine the will it work under other machines. Is it transferable to other machines? Yeah, that's good wording"; three boxes "for Linux, Windows, and Mac"; "When it's not highlighted, have a yellow outline and keep the blue for good ones"; "put the boxes, the judgment boxes under the title instead of after the list of things"): other operating systems, then other AI tools, each under its
    heading with its boxes first and then its lines."""
    return joined("transfer", "Is this transferable to other machines?",
                  ((q_elsewhere(r), SYSTEMS_HEAD), (q_hosts(r, targets), TOOLS_HEAD)))


# ---------------------------------------------------------------- 6 tools

FAMILY_COLS = (("shell", "Run commands", {"Bash", "PowerShell", "Monitor"}),
               ("write", "Change files", {"Write", "Edit", "NotebookEdit", "MultiEdit"}),
               ("web", "Open web pages", {"WebFetch"}), ("search", "Search the web", {"WebSearch"}),
               ("agent", "Start helpers", {"Agent", "Task"}))
# One sentence per kind of fit finding, as a template filled by `_fill` (Library/fit.yaml, `fit_kinds`).
FIT_PLAIN = {k["kind"]: k["plain"] for k in R.FIT_TABLE["fit_kinds"]}


def q_tools(r) -> Q:
    title = "Does it ask only for the tools it needs?"
    ft = R.fit_of(r)
    if not ft["measured"]:
        return unmeasured("tools", title)
    kinds = {k: p for k, _, _, p in ft["kinds"]}
    look = sum(len(kinds.get(k, [])) for k in ("unused", "missing", "readonly", "loops", "hooks"))
    c = ft["checked"]
    b = [esc(_fill(FIT_PLAIN[k], len(p))) + go(slug("tools", k)) for k, _, _, p in ft["kinds"]]
    none = []  # R32: what the checks did not find, under Not found on details.html
    if not kinds.get("loops"):
        none.append("No step repeats \u201cuntil it works\u201d without a limit.")
    if not ft["hooks"]:
        none.append("It has no hooks (commands that run by themselves on every message or action).")
    if look:
        answer = f"Walkdown found {n(look, 'place')} where the tools and the words don't match, or that keep running."
        chip, tone = f"{look} to look at", "look"
    elif c["with_grants"]:
        answer, chip, tone = "", "", "none"
        none.insert(0, "Every tool it is allowed to use is one it actually uses, and nothing it asks for is missing.")
    else:  # a fact about it, not a check that came up empty: it stays
        answer = "None of its skills or helpers lists its tools; they use whatever the AI already has."
        chip, tone = "", "none"
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
        more = ('<h3 id="tools-helpers">What each helper may do' + go("tools-helpers") + "</h3><p class=\"where\">\u2713 = allowed. Skills don't limit their tools; they "
                "use whatever the AI already has.</p>" + table(head, rows, "tbl grid"))
    detail = "".join(fold(f"{esc(name)} ({len(pl)})", f'<p class="where">{esc(why)}.</p><ul class="places">'
                          + "".join(f"<li>{code(R.fit_parts(k, f)[0])} {esc(R.fit_parts(k, f)[1])}</li>" for f in pl) + "</ul>",
                          fid=slug("tools", k))
                     for k, name, why, pl in ft["kinds"])
    if ft["hooks"]:
        detail += fold(f"Every hook ({len(ft['hooks'])})", '<ul class="places">'
                       + "".join(f"<li>{code(R.where(h))} {esc(R.hook_text(h))}</li>" for h in ft["hooks"]) + "</ul>", fid="tools-hooks")
    return Q("tools", title, chip, tone, esc(answer), b, more=more, detail=detail, none=[esc(x) for x in none])


# ---------------------------------------------------------------- 7 finished

CLEAN_ORDER = ("unfinished", "dated", "older", "models")  # details.html's folds in the order of the summary's lines (R11)


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
              + "." if parts else "")
    none = [] if parts else ["No unfinished notes, no dates that will go stale, and no older tool names."]  # R32
    b = []
    for w in ("todo", "placeholder", "draft"):
        mine = [f for f in un if f["kind"] == w]
        if mine:
            b.append(f"{n(len(mine), *words[w])}: " + ", ".join(where(f) for f in mine[:4]) + (" and more" if len(mine) > 4 else "")
                     + go("clean-unfinished"))
    if dated:
        b.append(f"{n(len(dated), 'claim tied to a date', 'claims tied to a date')} (published guidance: text tied to a "
                 "date becomes wrong): " + ", ".join(where(f) for f in dated[:3]) + (" and more" if len(dated) > 3 else "")
                 + go("clean-dated"))
    if older:
        b.append(f"{n(len(older), 'tool name')} not in Claude Code's current list: "
                 + ", ".join(f"{code(f['tool'])} (now {code(f['now'])})" for f in older[:3]) + "." + go("clean-older"))
    if models:
        b.append(f"It names {n(len(cl['models']), 'AI model version')} fixed in place: "
                 + ", ".join(code(m) for m in cl["models"][:6]) + (f" and {len(cl['models']) - 6} more" if len(cl["models"]) > 6 else "")
                 + ". A name like \u201csonnet\u201d follows the newest version; a full name stays on one." + go("clean-models"))
    else:
        none.append("No AI model names fixed in place.")
    detail = "".join(fold(f"{esc(name)} ({R.clean_count(k, pl, cl['models'])})", f'<p class="where">{esc(why)}.</p><ul class="places">'
                          + "".join(f"<li>{code(R.clean_parts(k, f, True)[0])} {esc(R.clean_parts(k, f, True)[1])}</li>" for f in pl)
                          + "</ul>", fid=slug("clean", k))
                     for k, name, why, pl in sorted(cl["kinds"], key=lambda x: CLEAN_ORDER.index(x[0])))
    chip, tone = (n(notes, "note"), "notes") if notes else ("", "none")  # R32: no "Nothing to look at"
    return Q("clean", title, chip, tone, answer if "<" in answer else esc(answer), b, detail=detail,
             none=[esc(FINISHED_HEAD + ": " + x[0].lower() + x[1:]) for x in none])


# ---------------------------------------------------------------- 8 careful

LEG_PLAIN = {"private-data": "Read your files", "untrusted-content": "Take in content from outside, such as web pages or files you didn't write",
             "external-comms": "Send your data somewhere"}
ALLOW_PLAIN = {"hooks": "runs commands by itself", "context": "adds its own text to the AI's memory before you type",
               "persistence": "can make changes that last after you close the session",
               "network": "connects to the internet", "elevated": "asks for more permissions than the default",
               "mcp": "connects to outside services", "agents": "has helpers with their own tools"}
ROW_PLAIN = {"hidden": "text hidden from people that the AI still reads, and it reads like an instruction",
             "spelled": "text hidden from people that the AI still reads, spelled out in invisible characters",
             "runs": "steps that run code", "secret": "a saved password, key, or token, or wording that gathers or asks for one",
             "out": "steps that read secrets, call out, or share", "lasting": "changes or permissions that last"}
# The same rows, short enough to list several in one sentence.
ROW_SHORT = {"hidden": "hidden instructions", "spelled": "hidden characters that spell out text", "runs": "steps that run code", "secret": "passwords, keys, and secrets",
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


def q_careful(r, qa, marks=None, stop=None) -> Q:
    title = "Anything to be careful about?"
    every = D.first_items(r)
    pl = [it for it in every if not D.is_model_read(it)]
    rs = S.rows(r, pl, marks)
    wording = S.wording_count(r, pl, rs, marks)
    off = S.off_list(r, pl)
    missing = S.not_run(qa)  # the coded steps: a model read that did not work is said apart (M9)
    down = S.model_down(qa)
    failed = S.failed_checks(qa)
    incomplete = S.incomplete_checks(qa)
    unchecked = S.unchecked_sentence(qa)  # steps that ran and whose fixture check could not be made
    stopped = R.stop_plain(stop) if R.stopped_left(stop) else None  # the run was asked to stop; no step failed
    total = S.total(rs)
    none = []  # R32: under Not found on details.html
    caveat = (" Not every step worked, so it may have missed some." if failed or missing else
              f' The run stopped after the step "{stopped}", as asked, so it may have missed some.' if stopped else
              f" {S.model_down_sentence(incomplete=incomplete)}" if down else "") + (f" {unchecked}." if unchecked else "")
    if not rs and missing:  # never "found none" when a step did not run (an outside tester, 2026-10-21)
        steps = (f'the step "{missing[0]}" did not run' if len(missing) == 1 else
                 f'{len(missing)} steps did not run, starting with "{missing[0]}"')
        answer = f"This run did not complete: {steps}, so Walkdown cannot say whether it has any of these."
        chip, tone = ("Not checked", "unmeasured")
    elif not rs and stopped:
        answer = (f'This run stopped after the step "{stopped}", as asked, so Walkdown cannot say whether it '
                  "has any of these.")
        chip, tone = ("Not checked", "unmeasured")
    elif not rs and off:  # R28; R32: the lines full.md has are found, "none on its list" is not
        answer = S.off_list_sentence(off) + caveat.replace(", so it may have missed some", ", so Walkdown may have missed some")
        chip, tone = ("", "none")
        none.append(S.NONE_ON_LIST)
    elif not rs:  # R32: no answer line and no chip; a step that did not work is still said
        answer = caveat.strip().replace(", so it may have missed some", ", so Walkdown may have missed some")
        chip, tone = ("", "none")
        none.append(S.NONE_FOUND)
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
    ls = S.lines(r, pl, marks)  # a line per kind, red, then yellow, then blue (R26)

    def say(x):
        first = x["places"][0]
        src = first.get("src") or {}
        quote = (first.get("quote") or "").replace("<!--", " ").replace("-->", " ").strip()
        s = f"{dot(x['color'])}<b>{esc(x['label'])}</b> ({len(x['places'])}): {esc(first.get('where') or R.where(src))}"
        if x["key"] == "hidden" and quote:  # the one repository text the summary quotes (owner, 2026-10-27)
            s += f" says \u201c{esc(quote[:80])}{'\u2026' if len(quote) > 80 else ''}\u201d"
        return s + go("careful-keys" if x["key"] in S.SECRET_LINES else "careful-" + x["row"])

    pw = [x for x in ls if x["key"] in S.SECRET_LINES]
    if pw:  # "Password and key should be a red section" (owner, 2026-11-06); the scan's limits stay on details (2026-11-01)
        b.append(f'{dot("red")}<b>{esc(SECRETS_HEAD)}</b><ul class="bul">' + "".join(f"<li>{say(x)}</li>" for x in pw)
                 + f"<li>{esc(VALUES_NOTE)}</li></ul>")
    b += [say(x) for x in sorted((x for x in ls if x["key"] not in S.SECRET_LINES), key=lambda x: COLORS.index(x["color"]))]
    if wording:
        b.append(dot("blue") + f"{n(wording, 'more place' if ls else 'place')} {'is' if wording == 1 else 'are'} only wording that shapes how the AI makes "
                 f"decisions. {'It is' if wording == 1 else 'They are'} in the details." + go("careful-wording"))
    if off and rs:  # with no place the answer says it (R28)
        b.append(dot("blue") + esc(S.off_list_sentence(off)))
    line = marked_line(r, marks)
    if line:
        b.append(dot("blue") + line)
    # What it can do is a section of its own at the top of the summary since 2026-11-05 (R4, `can_section`); the rest of
    # what was under the boxes is on details.html, under "Why it can do these".
    detail = careful_detail(r, pl, none)
    return Q("careful", title, chip, tone, esc(answer), b, detail=detail, none=[esc(x) for x in none],
             face=careful_face(ls, wording))


ALL_THREE = "A tool that does all three could be tricked into sending your data away."  # the one sentence the summary keeps (R4)


def can_boxes(r) -> str:
    """The three boxes, ticked or crossed, side by side (R4, owner 2026-11-05: "3 boxes across instead of a list"). Nothing
    when `02.5-capability` did not run: no boxes to tick when the step that ticks them did not run."""
    if "02.5-capability" not in r:
        return ""
    legs = {x["leg"]: x["present"] for x in R.fnd(r, "02.5-capability", "cap.leg")}
    return '<ul class="can">' + "".join(
        f'<li class="{"yes" if legs.get(k) else "no"}"><span class="mark {"yes" if legs.get(k) else "no"}">'
        f'{"\u2713" if legs.get(k) else "\u2717"}</span><span>{esc(LEG_PLAIN[k])}</span></li>' for k in R.LEG_NAMES) + "</ul>"


# What the wording alone asks for (R31, owner 2026-11-07): said apart from what installing it allows.
ASK_PLAIN = {"exec-at-load": "run commands by itself", "context-injection": "add its own text to the AI's memory before you type",
             "persistence": "make changes that last after you close the session", "network": "connect to the internet",
             "elevated": "have more permissions than the default"}
GRANT_PLAIN = {"exec-at-load": "Runs commands on its own", "context-injection": "Adds text to the AI's context before you type",
               "persistence": "Makes changes that last after the session", "network": "Connects to the internet",
               "elevated": "Asks for more permissions than the default"}


def can_rest(r) -> str:
    """What the summary said under the boxes before R4, after its first sentence: how many of the three this one does, and
    what else installing it allows. details.html says it under "Why it can do these". What only the wording asks for is
    its own sentence (R31)."""
    legs = {x["leg"]: x["present"] for x in R.fnd(r, "02.5-capability", "cap.leg")}
    have = sum(1 for k in R.LEG_NAMES if legs.get(k))
    also = [ALLOW_PLAIN[k] for k, v in D._allows(r).items() if v[2] and k in ALLOW_PLAIN]
    ask = [f"{ASK_PLAIN.get(g['grant'], g['grant'])} ({n(R.grant_sources(g)['wording'], 'line')})"
           for g in R.grant_split(r)[1]]
    return ("This one does " + ("all three." if have == 3 else f'{["none", "one", "two"][have]} of the three.')
            + (f" It also {esc(names(also))}." if also else "")
            + (f" Its wording asks to {esc(names(ask))}; no setting grants {'it' if len(ask) == 1 else 'them'}."
               if ask else ""))


def grants_detail(r) -> str:
    """details.html, What it can do (R31): what installing it grants, each with its reasons, and what its wording asks for,
    each with where the lines are. Nothing when there is neither."""
    granted, asked = R.grant_split(r)
    out = ""
    if granted:
        rows = []
        for g in granted:
            src = R.grant_sources(g) or {"settings": 0, "wording": 0}
            why = collections.Counter(R.grant_reason(e.get("why")) for e in g.get("evidence") or []
                                      if e.get("stage") != "02.4-phrases")
            said = "; ".join(f"{w} ({k})" for w, k in why.most_common()) or "its settings"
            if src["wording"]:
                said += f"; and {n(src['wording'], 'line')} of wording"
            rows.append(f"<li><b>{esc(GRANT_PLAIN.get(g['grant'], g['grant']))}</b>: {esc(said)}</li>")
        out += '<h3>What installing it grants</h3><ul class="bul">' + "".join(rows) + "</ul>"
    if asked:
        rows = []
        for g in asked:
            k = R.grant_sources(g)["wording"]
            at = [R.loc(e) for e in g.get("evidence") or [] if e.get("stage") == "02.4-phrases"][:4]
            rows.append(f"<li><b>{esc(GRANT_PLAIN.get(g['grant'], g['grant']))}</b>: {n(k, 'line')}, "
                        + ", ".join(f'<span class="where">{esc(x)}</span>' for x in at) + (" and more" if k > len(at) else "")
                        + "</li>")
        out += ("<h3>What its wording asks for</h3><p class=\"where\">No setting grants these: each comes from wording only. "
                "full.md section 5 cites every line.</p><ul class=\"bul\">" + "".join(rows) + "</ul>")
    return out


def can_section(r) -> str:
    """summary.html, under what it is (R4): What it can do, the three boxes across, the one sentence, and a Details button
    to "Why it can do these". Nothing when the boxes are not measured."""
    boxes = can_boxes(r)
    if not boxes:
        return ""
    return (f'<div class="head-row" id="can"><h2>{icon("can")}What it can do</h2>{go("can")}</div>{boxes}'
            f'<p class="where can-note">{esc(ALL_THREE)}</p>')


def place_li(it, pid) -> str:
    """One place on details.html: where (linked to its review card), what was found, Walkdown's note
    on it (a hook's host, what hidden text spells; never a pattern ID)."""
    at = (f'<a href="review.html#{esc(pid)}">{esc(it["where"])}</a>' if pid
          else f'<span class="where">{esc(it["where"])}</span>')
    note = "".join(f" {esc(c)}" for c in it.get("context") or [])  # what Walkdown says of the line, for every kind
    note += f" {esc(it['note'])}" if it.get("note") and it.get("kind") != "phrase" else ""
    text = (it.get("quote") or "").strip()  # details.html quotes every place (owner, 2026-10-27)
    said = f" <i>“{esc(text[:120])}{'…' if len(text) > 120 else ''}”</i>" if text else ""
    return f"<li>{at} {esc(it['title'])}.{said}{note}</li>"


def can_detail(r) -> str:
    """details.html, in the summary's place, under what it is (R11, owner 2026-11-05: "the detail should match the order of
    the summary"): What it can do as a section of its own. Closed, it shows the summary's one sentence; inside, the three
    boxes, how many of the three this one does and what installing it allows, the credit, and why each box is ticked.
    Nothing when `02.5-capability` did not run."""
    boxes = can_boxes(r)
    if not boxes:
        return ""
    reasons = []
    for k in R.LEG_NAMES:
        ev, total = D._leg_ev(r)[k]
        if total:
            why = collections.Counter(D._ev_words(e.get("why") or "") for e in ev)
            reasons.append(f"<li><b>{esc(LEG_PLAIN[k])}</b>: {n(total, 'place')} ("
                           + esc("; ".join(f"{v} {w}" for w, v in why.most_common(3))) + ")</li>")
    inside = (boxes + f'<p class="where">{can_rest(r)}</p>'  # the credit stays with the three boxes (as on the page before v3)
              + f"<h3>Why it can do these</h3><p class=\"where\">The three together are the lethal trifecta, {esc(D.TRIFECTA_LEDE)}</p>"
              + ("<ul class=\"bul\">" + "".join(reasons) + "</ul>" if reasons else "") + grants_detail(r))
    return fold_section("can", icon("can") + "<h2>What it can do</h2>", f'<span class="a">{esc(ALL_THREE)}</span>', inside, "can")


COLORS = ("red", "yellow", "blue")
SECRETS_HEAD = "Passwords, keys, and secrets"  # was "Passwords and keys" (owner, 2026-11-06, R26)
VALUES_NOTE = "Values are not shown in these reports."  # a secret finding keeps its file, line, and kind, never the value


def dot(color) -> str:
    """A line's color on the careful card (R26): red, yellow, or blue."""
    return f'<span class="dot {color}" role="img" aria-label="{color}"></span>'


def secret_scan(r) -> dict:
    """The secret scan's lines and limits: {sec, aside, unscanned, left_out, none} (`none`: no scanner ran)."""
    found = R.fnd(r, "02.4-phrases", "secret.found")
    sec = [x for x in found if "skipped" not in x and not R.is_test_data(x.get("file")) and x.get("audience") != "test-data"]
    none = any("skipped" in x and not x.get("file") for x in found)
    return {"sec": sec, "aside": sum(1 for x in found if "skipped" not in x) - len(sec), "none": none,
            "unscanned": [x for x in found if "skipped" in x and x.get("file")],  # one file each: the rest of the scan stands
            "left_out": [] if none else (r.get("02.4-phrases") or {}).get("secret_left_out") or []}


def careful_detail(r, pl, none=None) -> str:
    """details.html, the careful section's parts. `none` (R32): a list the lines of what was not found are added to."""
    none = [] if none is None else none
    out = []
    rs = S.rows(r, pl)
    card_of, _ = S._place_marks(r, None)
    folds = [x for x in rs if x["key"] != "secret"]  # the passwords part holds that row (R26, R27)
    if folds:
        out.append(part("careful-places", "Every place, by kind", "".join(
            fold(f"{esc(x['name'])} ({len(x['places'])})", '<ul class="places">' + "".join(
                place_li(it, card_of.get(M.place_key(it))) for it in x["places"]) + "</ul>", fid="careful-" + x["key"])
            for x in folds)))
    div = D._divergences(r)
    hid = []  # the part "Text hidden from people"
    if div:
        kinds = collections.Counter(d.get("carrier") for d in div)
        hid.append(f"<p>{n(len(div), 'place')} hold text that people don't see when the file is shown, but the AI reads: "
                   + esc(", ".join(f"{v} {D.carrier_plain(k)}" for k, v in kinds.most_common())) + ".</p>")
        hid.append(by_file_chart(div, "hidden place"))
        secret = D.secret_lines(r)

        def hidden_words(d) -> str:
            note = "" if (d.get("file"), d.get("line")) in secret else D.spelled_note(d.get("text"))
            return esc(D.carrier_plain(d.get("carrier"))) + (f" <i>{esc(note)}</i>" if note else "")

        hid.append(fold(f"Every hidden place ({len(div)})", places(div, hidden_words), fid="careful-hidden-all"))
    folded = [f for f in R.fnd(r, "02.2-reader", "read.fold") if D.fold_meaning(f)]  # typography left out
    if folded:
        hid.append(f"<p>{n(len(folded), 'line')} read{'s' if len(folded) == 1 else ''} differently once invisible "
                   f"characters or look-alike letters are swapped for plain ones: {esc(D.fold_kinds(folded))}.</p>"
                   + fold(f"Every such line ({len(folded)})", places(folded), fid="careful-folded"))
    script = [x for x in R.fnd(r, "02.2-reader", "read.script") if "skipped" not in x]
    lang = [x for x in R.fnd(r, "02.2-reader", "read.language") if "skipped" not in x]
    if script or lang:
        hid.append("<p>" + " ".join(x for x in (
            f"{n(len(script), 'stretch', 'stretches')} of text in another alphabet." if script else "",
            f"{n(len(lang), 'passage')} in a language other than English." if lang else "") if x)
            + " Walkdown reads English only, so it could not check what they ask for; read them yourself.</p>"
            + places(script + lang))
    if not (div or folded or script or lang or any(x["key"] == "hidden" for x in rs)):
        none.append("Nothing hidden from people.")  # R32
    if hid:
        out.append(part("careful-hidden-text", "Text hidden from people", "".join(hid)))
    hits = R.phrase_hits(r)
    words = []  # the part "Wording that shapes how the AI decides"
    if hits:
        aud = {}
        for h in hits:
            aud.setdefault((h["file"], h.get("line")), h.get("audience"))
        who = collections.Counter(D.READ_BY.get(a, "the AI") for a in aud.values())
        by = collections.Counter(h["check"] for h in hits)
        words.append(f"<p>{n(len(aud), 'line')} match{'es' if len(aud) == 1 else ''} the wording of a risky request. Being "
                   "listed doesn't mean something is wrong; each is a place to read. Who reads them: "
                   + esc(", ".join(f"{k} ({v})" for k, v in who.most_common())) + ".</p>")
        words.append(hbars([(D.GROUP_PLAIN[g][:1].upper() + D.GROUP_PLAIN[g][1:], sum(by[c] for c in cs),
                           n(sum(by[c] for c in cs), "line")) for g, cs in R.SUBGROUPS.items()]))
    rest = [it for it in pl if S.concern(it) is None]
    if rest:
        groups = collections.OrderedDict()
        for it in rest:
            groups.setdefault(it["title"], []).append(it)
        words.append("<p class=\"sub\"><b>Worth reading first</b></p><ul class=\"bul\">" + "".join(
            f"<li><b>{esc(t)}</b> ({len(v)}): " + ", ".join(f'<span class="where">{esc(it["where"])}</span>' for it in v[:4])
            + (" and more" if len(v) > 4 else "")
            + (f" <i>{esc((v[0].get('quote') or '').strip()[:100])}</i>" if v[0].get("quote") else "") + "</li>"
            for t, v in groups.items()) + "</ul>")
    if words:
        out.append(part("careful-wording", "Wording that shapes how the AI decides", "".join(words)))
    links = D.link_rows(r)
    if links:
        lk = collections.defaultdict(list)
        for x in links:
            lk[x["host"]].append(x)
        out.append(part("careful-links", "Web addresses",
                   f'<p class="where">{n(len(links), "link")} to {n(len(lk), "site")}. Walkdown gathered them and opened none.</p>'
                   + table('<th>Site</th><th class="num">Links</th><th>Read by</th><th>Named in its docs</th>',
                           [f"<tr><td>{esc(h)}</td><td class=\"num\">{len(v)}</td><td>{esc(', '.join(sorted({x['who'] for x in v})))}</td>"
                            f"<td>{'yes' if v[0].get('documented') else 'no'}</td></tr>"
                            for h, v in sorted(lk.items(), key=lambda kv: (-len(kv[1]), kv[0]))])))
    scan = secret_scan(r)
    sec, aside, unscanned, left_out = scan["sec"], scan["aside"], scan["unscanned"], scan["left_out"]
    aside_s = f" {n(aside, 'more')} in test data {'is' if aside == 1 else 'are'} set aside." if aside else ""
    if scan["none"]:
        body = "<p>Not checked: no secret scanner was available for this run.</p>"
    elif sec:
        body = f"<p>{n(len(sec), 'line')} look{'s' if len(sec) == 1 else ''} like a saved password, key, or token.{aside_s}</p>" + places(sec)
    else:  # R32: the owner's own example, "an API Key written plainly is not found"
        none.append("No lines look like a saved password, key, or token.")
        body = (f"<p>{n(aside, 'line')} in test data look{'s' if aside == 1 else ''} like a saved password, key, or token, "
                f"and {'is' if aside == 1 else 'are'} set aside.</p>" if aside else "")
    for x in (x for x in S.lines(r, pl) if x["key"] in ("creds", "enter-secret")):  # moved here (owner, 2026-11-06, R26)
        body += (f"<p><b>{esc(x['label'])}</b> ({len(x['places'])}):</p><ul class=\"places\">"
                 + "".join(place_li(it, card_of.get(M.place_key(it))) for it in x["places"]) + "</ul>")
    if unscanned:
        body += (f"<p>The secret scan could not scan {n(len(unscanned), 'file')}, so {'it' if len(unscanned) == 1 else 'they'} "
                 f"may hold one:</p>" + places(unscanned))
    if left_out:
        body += (f"<p>The secret scan left out {n(len(left_out), 'lock file')}, since the hashes in a lock file look like keys, so "
                 f"{'it' if len(left_out) == 1 else 'they'} may hold one:</p>" + places([{"file": rel, "line": None} for rel in left_out]))
    if body:
        out.append(part("careful-keys", SECRETS_HEAD, body + f'<p class="where">{esc(VALUES_NOTE)}</p>'))
    return "".join(out)


# ---------------------------------------------------------------- all seven

def questions(meta, r, stamps, runs_ok, marks=None) -> list[Q]:
    ctx = meta.get("context") or R.DEFAULT_CONTEXT
    stop = meta.get("stop")
    qs = [q_size(r, ctx), q_transfer(r, meta.get("hosts") or []),  # R21: memory and package; R22: other systems and AI tools
          q_clean(r), q_careful(r, qaview.of(meta), marks, stop),  # question 1 retired (R13)
          q_tools(r)]  # R33 (owner, 2026-11-08): Anything to be careful about? above Does it ask only for the tools it needs?
    if R.stopped_left(stop):  # a card no step measured says why, when the run was asked to stop (O3)
        for q in qs:
            if q.tone == "unmeasured" and q.id != "careful":
                q.answer = esc(f'Not measured: the run stopped after the step "{R.stop_plain(stop)}", as asked.')
    return finished_under_careful(qs)


FINISHED_HEAD = "Finished and up to date"


def finished_under_careful(qs) -> list[Q]:
    """R23 (owner 2026-11-06: "I think is it finished and up to date can be moved under anything to be careful about. It should get its own header under there. So it's distinct, but it doesn't need its own full tab."; "Finished and up to date under careful, go ahead"):
    the clean question's answer, label, lines, and folds go under their own heading at the end of the careful card and
    section; the careful card keeps its own label and answer. Every other question as it was."""
    clean = next(q for q in qs if q.id == "clean")
    careful = next(q for q in qs if q.id == "careful")
    # R32: with nothing found the part has no heading on either page; its lines go to the careful section's Not found
    found = clean.answer or clean.bullets or clean.more
    head = (f'<p class="finished-a">{clean.answer}' + (f' <span class="chip {clean.tone}">{esc(clean.chip)}</span>' if clean.chip else "")
            + "</p>" if clean.answer or clean.chip else "")
    piece = (f'<h3 class="piece" id="finished">{esc(FINISHED_HEAD)}</h3>{head}' + bullets_html(clean.bullets) + clean.more
             if found else "")
    careful.none += clean.none
    careful.details_body = bullets_html(careful.bullets) + careful.more + careful.detail + piece + clean.detail
    careful.more += piece
    careful.detail += clean.detail
    return [q for q in qs if q.id != "clean"]


# ---------------------------------------------------------------- the page shell (both pages)

CSS = """
:root {
  --bg: #f6f5f1; --card: #ffffff; --ink: #1f2328; --muted: #5d6470; --line: #e3e1da;
  --none-bg: #e8f1ea; --none-ink: #2f6b3c; --look-bg: #fbeed6; --look-ink: #8a5a00;
  --fact-bg: #e7eef8; --fact-ink: #2c5282; --red-bg: #fbe3de; --red-ink: #a3361f;
  --s1: #2a78d6; --s2: #eb6834; --s3: #1baf7a; --s4: #eda100;   /* validated, light, on #ffffff */
  --meter: #2a78d6; --track: #cde2fb; --over: #2a78d6; --grid: #e1e0d9;
  --on-s1: #ffffff; --on-light: #1f2328;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    --bg: #17191c; --card: #212429; --ink: #e8e6e1; --muted: #a3a8b0; --line: #343840;
    --none-bg: #1f3325; --none-ink: #8fd19e; --look-bg: #3a2e14; --look-ink: #f2c46d;
    --fact-bg: #1e2a3a; --fact-ink: #9cbcf0; --red-bg: #3d1d17; --red-ink: #f2a08c;
    --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;   /* validated, dark, on #212429 */
    --meter: #3987e5; --track: #184f95; --grid: #2c2c2a;
    --on-s1: #ffffff; --on-light: #111316;
  }
}
:root[data-theme="dark"] {
  --bg: #17191c; --card: #212429; --ink: #e8e6e1; --muted: #a3a8b0; --line: #343840;
  --none-bg: #1f3325; --none-ink: #8fd19e; --look-bg: #3a2e14; --look-ink: #f2c46d;
  --fact-bg: #1e2a3a; --fact-ink: #9cbcf0; --red-bg: #3d1d17; --red-ink: #f2a08c;
  --s1: #3987e5; --s2: #d95926; --s3: #199e70; --s4: #c98500;
  --meter: #3987e5; --track: #184f95; --grid: #2c2c2a;
  --on-s1: #ffffff; --on-light: #111316;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 17px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 1400px; margin: 0 auto; padding: 28px 24px 48px; }  /* a 1920-pixel monitor (owner, 2026-11-06, R18) */
header h1 { font-size: 2rem; margin: 0 0 4px; letter-spacing: -0.01em; }
.meta { color: var(--muted); font-size: 0.9rem; margin: 0 0 14px; }
.how { margin: 0 0 6px; }
.what { margin: 0 0 26px; }
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
.legend { list-style: none; padding: 0; margin: 10px 0 0; display: grid; gap: 6px 28px;
          grid-template-columns: repeat(2, minmax(0, 1fr)); }  /* two columns (owner, 2026-11-06, R21) */
@media (max-width: 560px) { .legend { grid-template-columns: 1fr; } }
h3.piece { font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted);
           margin: 22px 0 6px; padding-top: 14px; border-top: 1px solid var(--line); }
.body > h3.piece:first-child, .sec-body > h3.piece:first-child { border-top: 0; padding-top: 0; margin-top: 12px; }
.legend li { display: flex; gap: 8px; align-items: baseline; margin: 0; }
.sw { width: 12px; height: 12px; border-radius: 3px; flex: none; transform: translateY(1px); }
.sw.c1 { background: var(--s1); } .sw.c2 { background: var(--s2); } .sw.c3 { background: var(--s3); } .sw.c4 { background: var(--s4); }
.legend .n { font-variant-numeric: tabular-nums; font-weight: 650; min-width: 1.6em; text-align: right; }

/* hosts */
.hosts { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-top: 12px; }
.host { border: 1px solid var(--look-ink); border-radius: 8px; padding: 8px 10px; font-size: 0.9rem; }  /* yellow (R22) */
.host b { display: block; }
.host .st { color: var(--muted); font-size: 0.82rem; }
.host.has { border-color: var(--s1); }
.host.has .st { color: var(--ink); }

/* what it can do: three boxes across (R4), one under another on a phone */
.can { list-style: none; padding: 0; margin: 0 0 8px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.can li { display: flex; gap: 8px; align-items: flex-start; background: var(--card); border: 1px solid var(--line);
          border-radius: 12px; padding: 12px 14px; font-size: 0.95rem; }
.can li.yes { border-color: var(--look-ink); }
@media (max-width: 560px) { .can { grid-template-columns: 1fr; } }
.can-note { margin: 0 0 26px; }
.fold-body .can { margin-top: 10px; }
.mark { font-weight: 700; width: 1.4em; text-align: center; flex: none; }
.yes { color: var(--look-ink); } .no { color: var(--none-ink); }

/* the two pages linked (R1): Details on the summary, Summary on details */
a.go, a.back { font-size: 0.8rem; font-weight: 600; padding: 2px 10px; border: 1px solid var(--line); border-radius: 999px;
               color: var(--fact-ink); background: var(--card); text-decoration: none; white-space: nowrap; }
a.go:hover, a.back:hover, a.go:focus-visible, a.back:focus-visible { border-color: var(--fact-ink); }
a.go { margin-left: 8px; display: inline-block; }
a.back { float: right; margin: 0 0 0 12px; }
details:not([open]) > summary > a.back { display: none; }
details.secfold[open] > summary { display: flex; flex-direction: column; }
details.secfold[open] > summary > a.back { float: none; align-self: flex-end; margin: 8px 0 0; }
header > a.back { margin-top: 10px; }
.go-row { text-align: right; margin: 12px 0 0; }
.card-head .go-row { grid-column: 1 / -1; display: block; margin: 4px 0 0; }
.head-row { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin: 0 0 10px; }
.lead { margin: 10px 0 6px; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 7px; }  /* R26 */
.dot.red { background: var(--red-ink); } .dot.yellow { background: var(--look-ink); } .dot.blue { background: var(--s1); }
.bul .bul { margin: 6px 0 2px; }
.bul li:has(> .dot:first-child) { list-style: none; }  /* the dot takes the bullet's place (R26) */
.head-row h2 { margin: 0; }
h3 a.go { font-weight: 600; }
[id] { scroll-margin-top: 14px; }
.landed { animation: landed 2.4s ease-out; border-radius: 8px; }
@keyframes landed { 0%, 35% { outline: 3px solid var(--s1); outline-offset: 3px; } 100% { outline: 3px solid transparent; outline-offset: 3px; } }

/* tooltip */
[data-tip] { cursor: default; }
#tip { position: fixed; pointer-events: none; z-index: 10; background: var(--ink); color: var(--card);
       font-size: 0.82rem; padding: 6px 9px; border-radius: 6px; max-width: 260px; display: none; }

footer { margin-top: 28px; color: var(--muted); font-size: 0.9rem; }
footer a { color: var(--fact-ink); }

.sec { margin: 0 0 14px; }
details.secfold > summary { display: block; padding: 16px; }
details.secfold > summary .a { display: block; margin: 6px 0 4px; font-size: 1.02rem; }
.sec-body { padding: 0 16px 16px; border-top: 1px solid var(--line); }
details.part { margin-top: 12px; }
details.part > summary { color: var(--ink); }
details.part > summary h3 { display: inline; margin: 0; }
.sec-head { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
details.secfold > summary .more { display: block; margin-top: 2px; }
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
/* What Walkdown examined (2026-11-04): white, yellow, red */
.tiers { margin-bottom: 26px; }
.tier { border-radius: 12px; padding: 12px 16px; font-size: 0.95rem; border: 1px solid var(--line); }
.t-examined { background: var(--card); }
.t-archive { background: var(--look-bg); }
.t-archive b { color: var(--look-ink); }
.t-not { background: var(--red-bg); border-color: var(--red-ink); }
.t-not b { color: var(--red-ink); }
.tier-files { margin: 8px 0 0; padding-left: 20px; font-size: 0.9rem; overflow-wrap: anywhere; }

/* R33, the visual pass (prototype 2026-11-07): a brand line, glyphs, card faces, the examined bar, the details rail */
.brand { height: 4px; background: linear-gradient(90deg, var(--s1) 0 40%, var(--s2) 40% 60%, var(--s3) 60% 80%, var(--s4) 80%); }
header h1 { font-size: 2.4rem; font-weight: 750; letter-spacing: -0.02em; line-height: 1.1; margin-bottom: 8px; }
.ico { width: 1.15em; height: 1.15em; vertical-align: -0.2em; margin-right: 0.45em; flex: none; color: var(--fact-ink);
       stroke-linecap: round; stroke-linejoin: round; }
summary, .card-head { grid-template-columns: auto 1fr auto; }  /* glyph, question, chip */
summary > .ico, .card-head > .ico { width: 1.4em; height: 1.4em; margin: 0.1em 0 0; }
summary > .more, .card-head > .go-row { order: 9; }  /* drawn after the face */
.sec-head { align-items: center; justify-content: flex-start; flex-wrap: wrap; }
.sec-head h2 { flex: 1 1 0; min-width: 0; }
.sec-head .ico { width: 1.5em; height: 1.5em; margin-right: 0.35em; }
.head-row h2 .ico { width: 1.3em; height: 1.3em; }
.face { grid-column: 1 / -1; margin-top: 8px; }
.face .stack { margin-top: 2px; height: 22px; }
.face .hosts { margin-top: 2px; }
.sec-body > .face { margin: 14px 0 0; }
.kinds { display: flex; flex-wrap: wrap; gap: 6px 20px; align-items: center; }
.kgroup { display: inline-flex; align-items: center; gap: 3px; }
.kd { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }
.kd.red { background: var(--red-ink); } .kd.yellow { background: var(--look-ink); } .kd.blue { background: var(--s1); }
.kn { margin-left: 6px; font-weight: 650; font-variant-numeric: tabular-nums; font-size: 0.9rem; }
.kd-more { font-style: normal; color: var(--muted); }
details.card, div.card, .can li { transition: box-shadow .15s ease, border-color .15s ease; }
details.card:hover, div.card:hover { box-shadow: 0 3px 14px rgba(0, 0, 0, .07); }
.can li { padding: 14px 16px; align-items: center; }
.can li .mark { font-size: 1.45rem; width: 1.2em; line-height: 1; }
.tierbar { display: flex; height: 12px; border-radius: 6px; overflow: hidden; margin: 0 0 10px; border: 1px solid var(--line);
           background: var(--card); gap: 1px; }
.tseg { display: block; min-width: 4px; }
.tseg.t-examined { background: var(--card); } .tseg.t-archive { background: var(--look-ink); } .tseg.t-not { background: var(--red-ink); }
.rail { display: none; }
@media (min-width: 1000px) {
  .layout { display: grid; grid-template-columns: 210px minmax(0, 1fr); gap: 30px; align-items: start; }
  .rail { display: flex; flex-direction: column; gap: 2px; position: sticky; top: 18px; }
  .rail a { display: flex; align-items: center; gap: 9px; padding: 8px 10px; border-radius: 8px; color: var(--muted);
            text-decoration: none; font-size: 0.92rem; border-left: 3px solid transparent; }
  .rail a .ico { margin: 0; color: inherit; width: 1.25em; height: 1.25em; }
  .rail a:hover { background: var(--card); color: var(--ink); }
  .rail a.cur { color: var(--ink); background: var(--card); border-left-color: var(--s1); font-weight: 650; }
  .rail a.back { float: none; margin: 0 0 12px; align-self: flex-start; border: 1px solid var(--line); color: var(--fact-ink);
                 padding: 4px 12px; display: inline-flex; }
  .layout nav.toc { display: none; }
}
"""

SCRIPT = """<div id="tip" role="tooltip"></div>
<script>
(function () {
  function openAround(el) {
    for (var p = el; p; p = p.parentElement) { if (p.tagName === "DETAILS") p.open = true; }
    var own = el.querySelector(":scope > details"); if (own) own.open = true;
  }
  function land(first) {
    var id = decodeURIComponent(location.hash.slice(1)), el = id && document.getElementById(id);
    if (!el) return;
    openAround(el);
    var from = first && new URLSearchParams(location.search).get("from");
    if (from) el.querySelectorAll("a.back").forEach(function (a) { a.setAttribute("href", "summary.html#" + from); });
    if (from) document.querySelectorAll(".rail a.back").forEach(function (a) { a.setAttribute("href", "summary.html#" + from); });
    var spot = el.classList.contains("go") ? (el.closest("li, h3, .go-row, .head-row") || el) : el;
    spot.scrollIntoView({block: "start"});
    spot.classList.remove("landed"); void spot.offsetWidth; spot.classList.add("landed");
  }
  window.addEventListener("hashchange", function () { land(false); });
  land(true);
})();
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
(function () {
  var links = document.querySelectorAll(".rail a[data-sec]"); if (!links.length) return;
  var secs = Array.prototype.map.call(links, function (a) { return document.getElementById(a.getAttribute("data-sec")); });
  function mark() {
    var y = window.scrollY + Math.min(window.innerHeight / 3, 240), cur = 0;
    secs.forEach(function (s, i) { if (s && s.offsetTop <= y) cur = i; });
    links.forEach(function (a, i) { a.classList.toggle("cur", i === cur); });
  }
  window.addEventListener("scroll", mark, {passive: true}); window.addEventListener("hashchange", mark); mark();
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
    pin = (R.fnd(r, "02.1-inventory", "inv.pin") or [{}])[0]
    if not pin.get("license_checked"):
        return ""
    rows = [x for x in R.fnd(r, "02.1-inventory", "inv.license")
            if not R.is_test_data(x["file"]) and D._dir(x["file"]) in D.TOP_DIRS]
    lead = [x for x in rows if x.get("source") == "file"] or [x for x in rows if x.get("source") == "field"]
    if not lead:
        return "No license found"
    known = list(dict.fromkeys(x["license"] for x in lead if x.get("license")))
    return "License: " + (", ".join(known) if known else "not one Walkdown recognizes")


def meta_line(meta, r) -> str:
    pin = (R.fnd(r, "02.1-inventory", "inv.pin") or [{}])[0]
    h = str(meta.get("hash") or "")[:7]
    version = f"version {h}" if meta.get("hash_kind") == "git" else f"folder {h}"
    lic = short_license(r)
    files = n(pin["files"], "file") if pin.get("files") is not None else ""
    return " \u00b7 ".join(x for x in (f"Checked {day(meta.get('date'))}", version, files, lic) if x)


def page(title, meta, r, body) -> str:
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
            f"<title>{esc(title)}</title>\n<style>{CSS}</style>\n</head>\n<body>\n<div class=\"brand\" aria-hidden=\"true\"></div>\n<main>\n{body}\n</main>\n"
            f"{SCRIPT}\n</body>\n</html>\n")


def go_button(target, gid) -> str:
    """summary.html: the button to a part of details.html. `from` names the button, so the part's back link returns to it."""
    return f'<a class="go" id="{gid}" href="details.html?from={gid}#{target}">{GO_WORD}</a>'


def ids_in(html_text) -> set:
    return set(re.findall(r' id="([a-z0-9-]+)"', html_text))


def draw_goes(html_text, qid, known=None, k=None) -> str:
    """The marks as buttons, `go-<qid>-<n>` each; a mark whose part details.html does not have (`known`) is left out."""
    k = k or itertools.count(1)
    return GO_MARK.sub(lambda m: go_button(m.group(1), f"go-{qid}-{next(k)}")
                       if known is None or m.group(1) in known else "", html_text)


def drop_goes(html_text) -> str:
    """details.html: the marks gone, and a line that held only a mark with them."""
    return GO_MARK.sub("", re.sub(r'<p class="go-row"><!--go:[a-z0-9-]+--></p>', "", html_text))


def card(q: Q, known=None) -> str:
    """A question on summary.html: the head always shown; bullets and tables behind "More". A Details button on each line
    with a part of its own on details.html, and one at the bottom for the question (R1); `known`: the ids details.html has."""
    k = itertools.count(1)
    inner = draw_goes(bullets_html(q.bullets) + q.more, q.id, known, k)
    head = (f'{icon(q.id)}<span class="q">{esc(q.question)}</span>'
            + (f'<span class="chip {q.tone}">{esc(q.chip)}</span>' if q.chip else "")  # Misalignment has none (R24); R32
            + (f'<span class="a">{q.answer}</span>' if q.answer else ""))  # R32: a card that found nothing is its question
    if not inner:  # nothing more on this page: no "More", and the Details button on the card's face when details.html has more
        face = f'<span class="go-row">{go_button(q.id, "go-" + q.id)}</span>' if q.detail or q.none else ""
        return f'<li id="{q.id}"><div class="card"><div class="card-head">{head}{face}{q.face}</div></div></li>'  # R33
    inner += f'<p class="go-row">{go_button(q.id, "go-" + q.id)}</p>'
    return (f'<li id="{q.id}"><details class="card"><summary>{head}<span class="more">More \u203a</span>{q.face}</summary>'  # the face shows closed or open (R33)
            f'<div class="body">{inner}</div></details></li>')


def section(q: Q) -> str:
    """A question on details.html, folded like a card (R1): the head shows the question, chip, and answer; inside, a back
    link to the summary, then everything, every part folded."""
    inside = drop_goes((q.details_body or f"{bullets_html(q.bullets)}{q.more}{q.detail}")
                       + not_found(q.none, q.id)).replace('href="summary.html#@"', f'href="summary.html#{q.id}"')
    return fold_section(q.id, f'{icon(q.id)}<h2>{esc(q.question)}</h2>' + (f'<span class="chip {q.tone}">{esc(q.chip)}</span>'
                                                                         if q.chip else ""),
                        f'<span class="a">{q.answer}</span>' if q.answer else "", q.face + inside, q.id)


def fold_section(sid, head, answer, inside, home) -> str:
    """A section of details.html, folded: `<section>` keeps its id; the fold inside opens on a link to it."""
    return (f'<section id="{sid}" class="sec"><details class="secfold"><summary><span class="sec-head">{head}</span>{answer}'
            f'<span class="more">More \u203a</span>{back(home)}</summary><div class="sec-body">{inside}</div></details></section>')


def since_line(changes) -> str:
    """Under Size and Shape's memory part: the cost since the earlier run of the same repository (slice 6)."""
    line = (changes or {}).get("cost_line")
    if not line or not line.startswith("cost: "):
        return ""
    return f'<p class="since">Since run {esc(changes["since"])}: {esc(line[len("cost: "):])}.</p>'


NOT_EXAMINED_HEAD = "Not examined, in the files this repository has:"  # R35, R36: Words the owner's


def not_checked(r, notes, qa, stop=None) -> str:
    """details.html's last section: what this run did not check, plainly (steps that did not work,
    checks skipped in this run as render.glance names them, the optional model reads), then every
    limit. A run that stopped as asked (`stop`, O3) says what it left out in lines of their own, apart from the
    checks skipped for a missing tool; no step failed. A model read's passages that got no answer, and a chosen
    step that was not started, have a line of their own beside the first line (M9), with the reasons by kind and the
    call log; the fold of every limit leaves those lines out, since the page says each once. When the only step that did
    not work is a model read, the first line does not say that a step that did not work can miss places. The steps that
    did not work and every limit are the check of the run's (`qa`)."""
    steps = S.not_working(qa)
    unchecked = S.unchecked_sentence(qa)  # the steps that ran and could not be checked against their fixtures: one sentence
    prepared = (stop or {}).get("prepared")
    may_miss = "" if S.only_model_reads(qa) else " A step that did not work can miss places."
    lines = [f"Not every step worked: {esc('; '.join(steps))}.{may_miss}{' ' + esc(unchecked) + '.' if unchecked else ''}" if steps
             else f"{esc(unchecked)}." if unchecked
             else "Every step that ran passed its own checks."  # the lines below say where the run stopped
             if stop else "Every step ran and passed its own checks."]
    own = R.model_read_lines(qa, full=True) + R.not_started_lines(qa)
    lines += [esc(x) for x in own]
    lines += [esc(x) for x in (R.stopped_steps_line(stop), R.stop_input_line(stop)) if x]
    skipped, _ = R.glance(r, notes, qa, stop)
    if skipped:  # no coded check waits on an installed program since R35 and R36 (2026-11-11)
        lines.append("Skipped in this run:"
                     '<ul class="bul">' + "".join(f"<li>{esc(x)}</li>" for x in skipped) + "</ul>")
    unseen = R.not_examined(notes)  # R35, R36 (owner 2026-11-11: "We state we do not examine images")
    if unseen:
        lines.append(NOT_EXAMINED_HEAD + '<ul class="bul">' + "".join(f"<li>{esc(x)}</li>" for x in unseen) + "</ul>")
    if not prepared and not any(r.get(stage) is not None for stage in R.AI_STAGES):  # no AI stage left a report
        lines.append("The optional model reads (a second opinion from an AI) were not run.")
    every = R.limits(qa)
    lim = [x for x in every if x not in own]
    title = "Every limit of this run" if len(lim) == len(every) else "Every other limit of this run"
    none = R.checked_steps(qa)  # M9 slice C: no limits, so a fold of their own after the limits, a line for each step
    found_none = (fold(f"{R.CHECKED_HEADING} ({sum(n for _, n in none)})", '<ul class="places">'
                       + "".join(f"<li>{esc(x)}</li>" for x, _ in none) + "</ul>", fid="limits-none", home="") if none else "")
    inside = ("".join(f'<div class="a">{x}</div>' if "<ul" in x else f'<p class="a">{x}</p>' for x in lines[1:])
              + fold(f"{title} ({len(lim)})", '<ul class="places">'
                     + "".join(f"<li>{esc(x)}</li>" for x in lim) + "</ul>", fid="limits-all", home="") + found_none)
    return fold_section("limits", icon("limits") + "<h2>What this run covered</h2>", f'<span class="a">{lines[0]}</span>', inside, "")


def changes_section(changes) -> str:
    """details.html: what changed since the earlier run, in Walkdown's words (drift)."""
    if not changes or (changes.get("same") and not changes.get("differs")):
        return ""
    lines = "".join(f"<li>{esc(x[:1].upper() + x[1:])}</li>" for x in changes.get("lines", []))
    return fold_section("changes", icon("changes") + f'<h2>What changed since run {esc(changes["since"])}</h2>', "",
                        f'<ul class="bul">{lines}</ul><p class="where">Every change, file by file: '
                        '<a href="changes.md">changes.md</a>.</p>', "")
