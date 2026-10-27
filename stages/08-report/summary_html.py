"""The one page (summary.html), for someone building a skill or agent (owner, 2026-10-26; before,
for someone deciding whether to use one). Spec: specs/summary_html.SPEC.md.

What it costs in an AI's context against the builder's expected context, what ships by how it is
used, and whether it is safe: the security concerns by fixed kinds in a fixed order and what the
repository can do. Everything else is in details.html and review.html, except a step that did not
work: that is named at the bottom of the page, since the page's counts lean on it. Same facts as
the other reports; nothing here detects or judges, and nothing is picked by how bad it seems.
"""
from __future__ import annotations

import collections
import html

import details_html as D
import marks as M
import render as R

# Every rule-found place falls in exactly one row, taken by the first that fits; the rest is
# wording only (owner, 2026-10-20). (key, row name, details.html section the "more" link opens)
CONCERNS = (
    ("hidden", "Hidden text that reads like an instruction", "hidden"),
    ("runs", "Runs code", "risky"),
    ("secret", "Looks like a committed secret", "secrets"),
    ("out", "Reads secrets, calls out, or shares", "risky"),
    ("lasting", "Lasting changes or permissions", "risky"),
)
WORDING = "{n} {be} wording only: instructions that change how the AI reads, decides, or answers."
NOTHING = "Nothing to point out here."
# Under the three boxes (owner, 2026-10-20): the trifecta's point, as details.html words it.
TOGETHER = D.TRIFECTA_LEDE.split(". ", 1)[1]
# The page's one qualifier, in plain words for someone who is not technical (owner, 2026-10-20).
# details.html and full.md keep render.NOT_WHAT.
FOOTER = ("Walkdown reads a repository's files without running anything. It points out what it "
          "finds and leaves the judgment to you. Finding nothing does not mean a repository is safe.")


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def concern(it) -> str | None:
    """The concern row an item belongs to, or None for wording only."""
    if it.get("kind") == "hidden+phrase":
        return "hidden"
    group = D.action_group(it)
    if group == "runs":
        return "runs"
    if it.get("kind") == "secret":
        return "secret"
    return group if group in ("out", "lasting") else None


def _where(it) -> tuple:
    src = it.get("src") or {}
    return (it["stage"], src.get("file") or it.get("where") or "", src.get("line") or 0)


def _place_marks(r, marks) -> tuple[dict, dict]:
    """({place key: review card id}, {card id: mark}) from the run's marks, own or carried,
    matched by stable key as review.html matches them (marks.py)."""
    import review_html  # imported here, as details_html._place_ids does
    cards = [p for p in review_html.places(r) if not p["model"]]
    card_of = {k: p["id"] for p in cards for k in p["keys"]}
    saved, _ = M.match(marks, [(p["id"], p["keys"]) for p in cards]) if marks else ({}, 0)
    return card_of, {pid: m["mark"] for pid, m in saved.items() if m["mark"]}


def rows(r, places, marks=None) -> list[dict]:
    """The concern rows with places, in order: {key, name, section, places, not_concerned,
    example}. An example is the first place (stage, file, line) not marked Not concerned."""
    card_of, mark_of = _place_marks(r, marks)
    out = []
    for key, name, section in CONCERNS:
        mine = sorted((it for it in places if concern(it) == key), key=_where)
        if not mine:
            continue
        pid = lambda it: card_of.get(M.place_key(it))  # noqa: E731
        nc = [it for it in mine if mark_of.get(pid(it)) == "not-concerned"]
        rest = [it for it in mine if it not in nc]
        ex = rest[0] if rest else None
        out.append({"key": key, "name": name, "section": section, "places": mine,
                    "not_concerned": len(nc), "example": ex, "example_id": pid(ex) if ex else None})
    return out


def not_run(runs_ok) -> list[str]:
    """The steps that produced no output in this run, by their plain names."""
    return [D.PLAIN_STAGE[st] for st in R.ORDER[:6] if st not in runs_ok]


def failed_checks(results) -> list[str]:
    """The steps that ran and did not pass their fixture check, by their plain names. `results`:
    {stage: result word} for the stages that ran. INCOMPLETE is never counted (owner, 2026-10-25):
    a check that did not run for a missing optional tool stays in details.html and full.md."""
    return [D.PLAIN_STAGE[st] for st in R.ORDER[:6]
            if st in results and results[st] not in ("PASS", "INCOMPLETE")]


def headline(rs, missing=(), failed=()) -> str:
    """`missing`: steps that did not run (`not_run`); `failed`: steps that ran and failed their
    fixture check (`failed_checks`). A run missing a step never says it found none (2026-10-21,
    an outside tester: an empty .venv crashed stage 1 and the page said "found none"), and with
    no concerns a failed check is said here, not only at the bottom (owner, 2026-10-25, C40)."""
    n = sum(len(x["places"]) for x in rs)
    if missing:
        steps = (f'the step "{missing[0]}" did not run' if len(missing) == 1 else
                 f'{len(missing)} steps did not run, starting with "{missing[0]}"')
        if rs:
            return (f"This run did not complete: {steps}. In the steps that ran, Walkdown found "
                    f"security concerns: {R.n(n, 'place')}, of {R.n(len(rs), 'kind')}.")
        return (f"This run did not complete: {steps}, so Walkdown cannot say whether this "
                "repository has the security concerns it looks for.")
    if rs:
        nc = sum(x["not_concerned"] for x in rs)
        return (f"Walkdown found security concerns in this repository: {R.n(n, 'place')}, of "
                f"{R.n(len(rs), 'kind')}." + (f" ({nc} of them marked Not concerned.)" if nc else ""))
    if failed:
        return ("Walkdown found none of the security concerns it looks for, but not every step "
                "worked, so it may have missed some.")
    return "Walkdown found none of the security concerns it looks for."


def concerns_block(rs, wording, model) -> str:
    items = []
    for x in rs:
        ex = x["example"]
        if ex is not None:
            where = esc(ex["where"])
            link = (f'<a href="review.html#p-{x["example_id"]}">{where}</a>' if x["example_id"]
                    else f"<code>{where}</code>")
            example = f'<div class="c-ex">{esc(ex["title"])}: {link}</div>'
        else:
            example = '<div class="c-ex">Every place of this kind is marked Not concerned.</div>'
        more = len(x["places"]) - 1
        more_link = (f' <a class="c-more" href="details.html#{x["section"]}">{more} more</a>'
                     if more > 0 else "")
        nc = f' <span class="c-nc">{x["not_concerned"]} marked Not concerned</span>' if x["not_concerned"] else ""
        items.append(f'<li class="concern"><div class="c-head"><span class="c-name">{esc(x["name"])}</span> '
                     f'<span class="c-count">{esc(R.n(len(x["places"]), "place"))}</span>{nc}</div>'
                     f'{example}{more_link}</li>')
    body = f'<ol class="concerns">{"".join(items)}</ol>' if items else D._p(NOTHING)
    if wording:
        n = R.n(wording, "more place" if items else "place")
        body += (f'<p class="note">{esc(WORDING.format(n=n, be="is" if wording == 1 else "are"))} '
                 f'<a href="details.html#risky">In the details</a>.</p>')
    if model:
        body += (f'<p class="note">{esc(R.n(model, "model read"))}, experimental, on the '
                 f'<a href="review.html">review page</a>.</p>')
    lede = (esc("By fixed kinds, in a fixed order. Each row gives one example; the details and the "
                "review page have every place.") if items else "")  # owner, 2026-10-20: none, no lede
    return D._section("concerns", "Is it safe?", lede, body)


def capability(r) -> str:
    legs = {x["leg"]: bool(x.get("present")) for x in R.fnd(r, "05-capability", "cap.leg")}
    order = [k for k in R.LEG_NAMES if legs.get(k)] + [k for k in R.LEG_NAMES if not legs.get(k)]
    lis = []
    for i, k in enumerate(order, 1):
        on = legs.get(k)
        data_n = f' data-n="{i}"' if on else ""
        lis.append(f'<li class="leg {"on" if on else "off"}"{data_n}>'
                   f'<span class="box" role="img" aria-label="{"yes" if on else "no"}">'
                   f'{D.CHECK if on else D.BOX}</span><div><div class="leg-name">{esc(R.LEG_NAMES[k])}</div></div></li>')
    allows = D._allows(r)
    also = [allows[k][0] for k in D.GENERAL if allows[k][2]]
    also_line = (f'<p class="note">Also: {esc(", ".join(a[:1].lower() + a[1:] for a in also))}.</p>'
                 if also else "")
    return D._section("can", "What it can do", "",  # no lede: the footer covers it (owner, 2026-10-20)
                      f'<ul class="legs compact">{"".join(lis)}</ul><p>{esc(TOGETHER)}</p>{also_line}'
                      '<p class="note"><a href="details.html#trifecta">The places behind each box</a>.</p>')


def results(stamps, runs_ok) -> dict:
    """{stage: result word} for the stages that ran and have a stamp."""
    return {st: s.result for st, s in (stamps or {}).items() if st in runs_ok}


def failed_steps(stamps, runs_ok) -> list[str]:
    """Steps that did not work in this run (owner, 2026-10-20): a step with no output, or one that
    ran and failed its fixture check. Never a step with nothing here to test, or a check that did
    not run for a missing optional tool (INCOMPLETE, any stage; owner, 2026-10-25): Other details
    on details.html lists those. A run made without validation has no stamps and adds none here."""
    return not_working(results(stamps, runs_ok), runs_ok)


def not_working(res, runs_ok) -> list[str]:
    """`failed_steps` from {stage: result word}; the brief reads LOG.md's stamps this way."""
    failed = set(failed_checks(res))
    out = []
    for st in R.ORDER[:6]:
        name = D.PLAIN_STAGE[st]
        if st not in runs_ok:
            out.append(f"{name} did not run")
        elif name in failed:
            out.append(f"{name} did not pass its fixture check ({res[st]})")
    return out


def warning(steps) -> str:
    """One line at the bottom of the page, above the footer, only when a step did not work
    (owner, 2026-10-21)."""
    if not steps:
        return ""
    return (f'<section class="block warn" id="warning"><p><b>Not every step worked in this run.</b> '
            f'{esc("; ".join(steps))}. A step that did not work can miss places, so this page may show '
            f'fewer than there are. <a href="details.html#other">Other details</a> says why.</p></section>')


def cost_sentence(r, ctx: int) -> str | None:
    """The headline's first sentence (slice 1): files, every session, and the largest skill at its
    fullest against the expected context. None with no stage 5 tiers."""
    c = R.cost(r)
    if c["session"] is None:
        return None
    files = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0].get("files")
    lead = f"{R.n(files, 'file')}; " if isinstance(files, int) else ""
    t = c["tiers"]
    if t:
        top = t["skill-max"]["tokens"]
        s = (f"{lead}every session takes {c['session']['tokens']:,} tokens once installed, and the largest "
             f"{R.what(t['skill-runs'].get('kind'))} at its fullest {top:,} ({R.pct(top, ctx)} of a "
             f"{ctx:,}-token context).")
    elif c["project"]:
        top = c["project"]["tokens"]
        s = (f"{lead}every session in this folder takes {top:,} tokens ({R.pct(top, ctx)} of a "
             f"{ctx:,}-token context).")
    else:
        top = c["session"]["tokens"]
        s = f"{lead}every session takes {top:,} tokens once installed."
    s = s[0].upper() + s[1:]
    return s + (" That is more than the expected context." if top > ctx else "")


def cost_block(r, ctx: int, changes=None) -> str:
    table = D.context_table(r, ctx)
    body = (table + D.cost_notes(r) + '<p class="more"><a href="details.html#ship">Every skill and file, '
            "by tier and group</a></p>") if table else D._empty(
        "Not measured: this run has no context tiers (it was made before they were counted, or stage 3 "
        "or 5 did not run).")
    line = (changes or {}).get("cost_line")
    if table and line and line.startswith("cost: "):  # slice 6: since the earlier run
        body += f'<p class="since">Since run {esc(changes["since"])}: {esc(line[len("cost: "):])}.</p>'
    return D._section("cost", "What it costs", "", body)


def ship_block(r) -> str:
    bands = R.ship_bands(r)
    if not any(b["files"] for b in bands):
        return D._section("ship", "What you ship", "", D._empty("Not measured: this run has no file groups."))
    def groups(b):
        return "; ".join(f'{R.in_sentence(R.SHIP_GROUPS[g])}: {v["files"]:,}' for g, v in b["groups"].items())
    lis = "".join(
        f'<li><b>{esc(b["name"])}</b>: {esc(R.n(b["files"], "file"))}, {esc(R.kb(b["bytes"]))}, '
        f'{b["tokens"]:,} tokens'
        + (f'<div class="c-ex">{esc(groups(b))}</div>' if b["groups"] else "") + "</li>" for b in bands)
    lo = R.left_out(r)
    what = " and ".join(x for x in (
        (f"the {R.n(lo['unused'], 'file')} nothing points to" if lo["unused"] else ""),
        (f"the {R.n(lo['build'], 'build file')}" if lo["build"] else "")) if x)
    saving = (f'<p>If {esc(what)} were left out of what you ship: {esc(R.kb(lo["bytes"]))} smaller, and '
              f'{lo["tokens"]:,} tokens no longer within an AI\'s reach.</p>') if what else ""
    return D._section("ship", "What you ship", "",
                      f'<ul class="bands">{lis}</ul>{saving}'
                      '<p class="more"><a href="details.html#ship">Every file, by group</a></p>')


def elsewhere_block(r) -> str:
    """Will it run on someone else's machine? (slice 2): what it uses and what is not declared,
    then one row per kind of place that ties it to one machine, with one example."""
    n_ = R.needs_of(r)
    title = "Will it run on someone else's machine?"
    if not n_["measured"]:
        return D._section("elsewhere", title, "", D._empty("Not measured: stage 4 did not run."))
    cmds = [c["command"] for c in n_["commands"]]
    pkgs = [p["package"] for p in n_["packages"]]
    parts = []
    def some(names, cap=12):
        return ", ".join(names[:cap]) + (f", and {len(names) - cap} more" if len(names) > cap else "")
    if cmds or pkgs:
        uses = some(cmds) + (", and " if cmds and pkgs else "") + (
            f"{R.n(len(pkgs), 'package')} ({some(pkgs, 6)})" if pkgs else "")
        parts.append(f"<p>It uses: {esc(uses)}.</p>")
        parts.append(f"<p>Not declared anywhere: {esc(some(n_['undeclared']))}.</p>" if n_["undeclared"]
                     else "<p>Everything it uses is declared.</p>")
    rows = "".join(
        f'<li class="concern"><div class="c-head"><b>{esc(name)}</b> <span class="count">{len(places):,}</span></div>'
        f'<div class="c-ex">{esc(why)}: <code>{esc(R.where(places[0]))}</code></div></li>'
        for _, name, why, places in n_["port"])
    parts.append(f'<ul class="concerns">{rows}</ul>' if rows else "<p>Nothing found that ties it to one machine.</p>")
    parts.append('<p class="more"><a href="details.html#elsewhere">Every program, package, and place</a></p>')
    return D._section("elsewhere", title, "", "".join(parts))


def trigger_block(r, ctx: int) -> str:
    """Will it trigger? (slice 4, owner 2026-10-26: first on the page): how the entries trigger,
    the listing, then one row per kind of finding with what the host does and one example."""
    tr = R.trigger_of(r)
    title = "Will it trigger?"
    if not tr["measured"]:
        return D._section("trigger", title, "", D._empty(
            "Not measured: this run has no trigger findings (stage 4 did not run, or the run was made "
            "before they were counted)."))
    parts = [f"<p>{esc(R.entries_line(tr))}</p>"] + [f"<p>{esc(x)}</p>" for x in R.listing_lines(tr, ctx)]
    rows = "".join(
        f'<li class="concern"><div class="c-head"><b>{esc(name)}</b> <span class="count">{len(places):,}</span></div>'
        f'<div class="c-ex">{esc(why)}: <code>{esc(R.trig_parts(kind, places[0])[0])}</code> '
        f'{esc(R.trig_parts(kind, places[0])[1])}</div></li>'
        for kind, name, why, places in tr["kinds"])
    if rows:
        parts.append(f'<ul class="concerns">{rows}</ul>')
    elif tr["entries"]:
        parts.append("<p>Every entry has frontmatter its host reads and follows the rules.</p>")
    if tr["entries"]:
        parts.append('<p class="more"><a href="details.html#trigger">Every entry and place</a></p>')
    return D._section("trigger", title, "", "".join(parts))


def brief_trigger_line(r) -> str | None:
    """The brief's line (slice 4): counts only."""
    tr = R.trigger_of(r)
    if not tr["measured"]:
        return None
    ents = tr["entries"]
    if not ents:
        return "Will it trigger: no skill, agent, or command here."
    k = collections.Counter(e["kind"] for e in ents)
    c = R.brief_trigger_counts(tr)
    have = ", ".join(R.n(k[x], x) for x in ("skill", "command", "agent") if k[x])
    return (f"Will it trigger: {have}; {R.n(c['host'], 'place')} that {'breaks' if c['host'] == 1 else 'break'} "
            f"a host rule, {c['guidance']} from guidance; {R.n(c['overlap'], 'pair')} of descriptions that overlap.")


def ready_block(r, targets=()) -> str:
    """Is it ready for any AI? (slice 3): for the hosts named, what is missing; then one line per
    host, the skills no host reads where they sit, copies that differ, and one row per kind of
    one-host feature with one example."""
    rd = R.ready_of(r)
    title = "Is it ready for any AI?"
    if not rd["measured"]:
        return D._section("ready", title, "", D._empty(
            "Not measured: this run has no host findings (stage 4 did not run, or the run was made "
            "before they were counted)."))
    parts = []
    if targets:
        items = "".join(f"<li>{esc(x)}</li>" for x in R.todo(r, targets))
        parts.append(f'<h3>For the hosts you named</h3><ul class="todo">{items}</ul>')
    if targets:
        parts.append("<h3>Each host</h3>")
    parts.append('<ul class="hosts">' + "".join(f"<li>{esc(R.host_line(c))}</li>" for c in rd["coverage"]) + "</ul>")
    if rd["loose"]:
        parts.append(f"<p>{esc(R.n(len(rd['loose']), 'skill'))} no host reads where "
                     f"{'it sits' if len(rd['loose']) == 1 else 'they sit'} (first: <code>{esc(rd['loose'][0])}</code>); "
                     "a host reads them once they are installed (copied into its skill folder, or added as a plugin).</p>")
    for d in rd["differ"][:3]:
        parts.append(f"<p>{esc(R.drift_line(d, rd['coverage']))}</p>")
    if len(rd["differ"]) > 3:
        parts.append(f"<p>And {R.n(len(rd['differ']) - 3, 'more pair')} that differ.</p>")
    rows = "".join(
        f'<li class="concern"><div class="c-head"><b>{esc(name)}</b> <span class="count">{len(places):,}</span></div>'
        f'<div class="c-ex">{esc(why)}: <code>{esc(R.where(places[0]))}</code></div></li>'
        for _, name, why, places in rd["features"])
    parts.append(f'<ul class="concerns">{rows}</ul>' if rows else "<p>No one-host feature found.</p>")
    parts.append('<p class="more"><a href="details.html#ready">Every host, copy, and place</a></p>')
    return D._section("ready", title, "", "".join(parts))


def brief_ready_line(r, targets=()) -> str | None:
    """The brief's line (slice 3): counts only."""
    rd = R.ready_of(r)
    if not rd["measured"]:
        return None
    have = sum(1 for c in rd["coverage"] if R.has_files(c))
    s = (f"Ready for: {have} of {len(rd['coverage'])} hosts have their files here; copies that differ: "
         f"{len(rd['differ'])}; one-host features: {sum(len(p) for *_, p in rd['features'])}.")
    if targets:
        left = [x for x in R.todo(r, targets) if not x.endswith(": nothing missing.")]
        s += f" For the hosts named: {R.n(len(left), 'thing')} missing."
    return s


def fit_block(r) -> str:
    """Do the tools fit the job? (slice 5, owner 2026-10-26: after Ready for any AI, before Is it
    safe): one row per kind with its count, why, and first place."""
    ft = R.fit_of(r)
    title = "Do the tools fit the job?"
    if not ft["measured"]:
        return D._section("fit", title, "", D._empty(
            "Not measured: this run has no tool-fit findings (stages 4 and 5 did not run, or the run was "
            "made before they were counted)."))
    rows = "".join(
        f'<li class="concern"><div class="c-head"><b>{esc(name)}</b> <span class="count">{len(places):,}</span></div>'
        f'<div class="c-ex">{esc(why)}: <code>{esc(R.fit_parts(kind, places[0])[0])}</code> '
        f'{esc(R.fit_parts(kind, places[0])[1])}</div></li>'
        for kind, name, why, places in ft["kinds"])
    body = (f'<ul class="concerns">{rows}</ul>' if rows else
            "<p>Every tool granted is one the words ask for, and nothing asks for a tool it lacks.</p>")
    return D._section("fit", title, "", body + '<p class="more"><a href="details.html#fit">Every entry, hook, and place</a></p>')


def clean_block(r) -> str:
    """Is it current and clean? (slice 6, owner 2026-10-27: after Do the tools fit the job, before
    Is it safe): one row per kind with its count, what it means, and the first place."""
    cl = R.clean_of(r)
    title = "Is it current and clean?"
    if not cl["measured"]:
        return D._section("clean", title, "", D._empty(
            "Not measured: this run has no current-and-clean findings (stage 4 did not run, or the run was "
            "made before they were counted)."))
    rows = "".join(
        f'<li class="concern"><div class="c-head"><b>{esc(name)}</b> <span class="count">'
        f'{esc(R.clean_count(kind, places, cl["models"]))}</span></div>'
        f'<div class="c-ex">{esc(why)}: <code>{esc(R.clean_parts(kind, places[0])[0])}</code> '
        f'{esc(R.clean_parts(kind, places[0])[1])}</div></li>'
        for kind, name, why, places in cl["kinds"])
    body = (f'<ul class="concerns">{rows}</ul>' if rows
            else "<p>No unfinished text, dated claims, pinned model IDs, or older tool names.</p>")
    return D._section("clean", title, "", body + '<p class="more"><a href="details.html#clean">Every place</a></p>')


def brief_clean_line(r) -> str | None:
    """The brief's line (slice 6): counts only."""
    cl = R.clean_of(r)
    if not cl["measured"]:
        return None
    k = {kind: len(p) for kind, _, _, p in cl["kinds"]}
    m = k.get("models", 0)
    return (f"Current and clean: {k.get('unfinished', 0)} unfinished, {R.n(k.get('dated', 0), 'dated claim')}, "
            f"{R.n(m, 'pinned model ID')}" + (f" ({len(cl['models'])} distinct)" if m and len(cl["models"]) != m else "")
            + f", {R.n(k.get('older', 0), 'older tool name')}.")


def brief_fit_line(r) -> str | None:
    """The brief's line (slice 5): counts only."""
    ft = R.fit_of(r)
    if not ft["measured"]:
        return None
    c = R.brief_fit_counts(ft)
    return (f"Tools fit: {c['unused']} granted and never used, {R.n(c['missing'], 'task')} with no tool, "
            f"{R.n(c['loops'], 'loop')} with no stated limit; {R.n(c['hooks'], 'hook')} "
            f"{'runs' if c['hooks'] == 1 else 'run'} on every prompt or tool call.")


def brief_needs_line(r) -> str | None:
    """The brief's line (slice 2): counts only; package names come from the repository."""
    n_ = R.needs_of(r)
    if not n_["measured"]:
        return None
    places = sum(len(p) for *_, p in n_["port"])
    return (f"Needs: {R.n(len(n_['commands']), 'program')}, {R.n(len(n_['packages']), 'package')}; "
            f"{len(n_['undeclared'])} not declared. Ties to one machine: {R.n(places, 'place')}.")


def brief_cost_lines(r, ctx: int) -> list[str]:
    """The brief's two lines (slice 1): counts only, no file or skill name."""
    c = R.cost(r)
    if c["session"] is None:
        return []
    t = c["tiers"]
    first = f"Every session: {c['session']['tokens']:,} tokens."
    if t:
        top = t["skill-max"]["tokens"]
        first += (f" Largest {R.what(t['skill-runs'].get('kind'))} at its fullest: {top:,} tokens "
                  f"({R.pct(top, ctx)} of {ctx:,}).")
    if c["project"]:
        first += f" Every session in this folder: {c['project']['tokens']:,} tokens."
    band = next((b for b in R.ship_bands(r) if b["name"] == "Not used at run time"), None)
    second = (f"Not used at run time: {R.n(band['files'], 'file')} ({band['tokens']:,} tokens)."
              if band and band["files"] else "")
    return [x for x in (first, second) if x]


def render_page(meta, r, stamps, notes, runs_ok, marks=None, changes=None) -> str:
    """`stamps`, `notes`, `runs_ok` are taken as details.html takes them. What was not checked is
    on that page only (owner, 2026-10-20); a step that did not work is named at the bottom of this
    one (`warning`)."""
    every = D.first_items(r)
    places = [it for it in every if it["stage"] != 6]
    model = sum(1 for it in every if it["stage"] == 6)
    rs = rows(r, places, marks)
    wording = sum(1 for it in places if concern(it) is None)
    head = D.header(meta, r, links=(("details.html", "Details"), ("review.html", "Review each place →")))
    ctx = meta.get("context") or R.DEFAULT_CONTEXT
    first = cost_sentence(r, ctx)
    body = [head,
            '<section class="block lead" id="headline">'
            + (f'<p class="headline">{esc(first)}</p>' if first else "")
            + f'<p class="headline">{esc(headline(rs, not_run(runs_ok), failed_checks(results(stamps, runs_ok))))}</p></section>',
            trigger_block(r, ctx),  # slice 4, owner 2026-10-26: first
            cost_block(r, ctx, changes), ship_block(r),  # slice 1, owner 2026-10-26
            elsewhere_block(r),  # slice 2
            ready_block(r, meta.get("hosts") or []),  # slice 3
            fit_block(r),  # slice 5
            clean_block(r),  # slice 6
            concerns_block(rs, wording, model), capability(r),
            warning(failed_steps(stamps, runs_ok)), f'<footer><p>{esc(FOOTER)}</p></footer>']
    return ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
            f"<title>{esc('Walkdown summary: ' + meta['repo'])}</title>\n" + D.FONTS
            + f"<style>{D.CSS}{CSS}</style>\n</head>\n"
            f"<body>\n<main class=\"wrap\">\n{''.join(body)}\n</main>\n</body>\n</html>\n")


CSS = """
.lead { padding-top: .9rem; padding-bottom: .9rem; }
.block.warn { border-left: 4px solid var(--leg-3); background: var(--flag-bg); padding-top: .8rem; padding-bottom: .8rem; }
.block.warn p { margin: 0; }
.block.warn a { color: var(--accent); font-weight: 600; }
.headline { font: 600 1.15rem/1.45 var(--body); margin: 0; max-width: 70ch; }
.headline + .headline { margin-top: .5rem; }
.bands { list-style: none; margin: 0 0 .6rem; padding: 0; display: grid; gap: .5rem; }
.more a { color: var(--accent); font-weight: 600; }
.concerns { list-style: none; margin: 0; padding: 0; display: grid; gap: .7rem; }
.concern { border-left: 4px solid var(--leg-2); background: var(--flag-bg); border-radius: 6px; padding: .6rem .8rem; }
.c-head { display: flex; flex-wrap: wrap; gap: .3rem .7rem; align-items: baseline; }
.c-name { font-weight: 600; }
.c-count { color: var(--muted); font-variant-numeric: tabular-nums; }
.c-nc { color: var(--muted); font-size: .88rem; }
.c-ex { margin-top: .25rem; font-size: .92rem; overflow-wrap: anywhere; }
.c-ex a, .c-ex code { font: .8rem/1.4 var(--mono); }
.c-more { font-size: .88rem; }
.legs.compact { gap: .6rem; }
.hosts, .todo { list-style: disc; margin: 0 0 .7rem; padding-left: 1.2rem; }
.hosts li, .todo li { margin: .15rem 0; overflow-wrap: anywhere; }
@media print { .block { break-inside: avoid; } }
"""
