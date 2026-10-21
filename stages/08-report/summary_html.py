"""The one page (summary.html), for someone deciding whether to use a repository. Spec:
specs/summary_html.SPEC.md.

What Walkdown found that could be dangerous, by fixed kinds in a fixed order; what the repository
can do; the questions before use. Everything else, what was not checked included (owner,
2026-10-20), is in details.html and review.html, except a step that did not work: that is named
at the bottom of the page, since the page's counts lean on it. Same facts as the other reports; nothing here detects or judges, and nothing is
picked by how bad it seems (owner, 2026-10-20).
"""
from __future__ import annotations

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


def headline(rs, missing=()) -> str:
    """`missing`: steps that did not run (`not_run`). A run missing a step never says it found
    none (2026-10-21, an outside tester: an empty .venv crashed stage 1 and the page said "found
    none"); the step-did-not-work line stays at the bottom for a step that ran but skipped part
    (owner, 2026-10-21)."""
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
    return D._section("concerns", "Security concerns", lede, body)


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


def failed_steps(stamps, runs_ok, r=None, notes=None) -> list[str]:
    """Steps that did not work in this run (owner, 2026-10-20): a step with no output, or one whose
    fixture check failed. An INCOMPLETE stamp counts only when a missing optional tool reads files
    this repository has (`render.tool_items`; owner, 2026-10-21): without them it changes nothing
    here, and Other details on details.html lists it. A run made without validation has no
    stamps and adds none here."""
    out = []
    for st in R.ORDER[:6]:
        name = D.PLAIN_STAGE[st]
        if st not in runs_ok:
            out.append(f"{name} did not run")
        elif st in (stamps or {}) and stamps[st].result == "INCOMPLETE":
            gaps = R.tool_items(r or {}, notes or {})[0] if st == "02-reader" else []
            if gaps:
                out.append(f"{name} skipped part of this repository: "
                           + "; ".join(f"{w[:1].lower()}{w[1:]}, {y}" for w, y in gaps))
        elif st in (stamps or {}) and stamps[st].result != "PASS":
            out.append(f"{name} did not pass its fixture check ({stamps[st].result})")
    return out


def warning(steps) -> str:
    """One line at the bottom of the page, above the footer, only when a step did not work
    (owner, 2026-10-21)."""
    if not steps:
        return ""
    return (f'<section class="block warn" id="warning"><p><b>Not every step worked in this run.</b> '
            f'{esc("; ".join(steps))}. A step that did not work can miss places, so this page may show '
            f'fewer than there are. <a href="details.html#other">Other details</a> says why.</p></section>')


def render_page(meta, r, stamps, notes, runs_ok, marks=None) -> str:
    """`stamps`, `notes`, `runs_ok` are taken as details.html takes them. What was not checked is
    on that page only (owner, 2026-10-20); a step that did not work is named at the bottom of this
    one (`warning`)."""
    every = D.first_items(r)
    places = [it for it in every if it["stage"] != 6]
    model = sum(1 for it in every if it["stage"] == 6)
    rs = rows(r, places, marks)
    wording = sum(1 for it in places if concern(it) is None)
    head = D.header(meta, r, links=(("details.html", "Details"), ("review.html", "Review each place →")))
    body = [head,
            f'<section class="block lead" id="headline"><p class="headline">'
            f'{esc(headline(rs, not_run(runs_ok)))}</p></section>',
            concerns_block(rs, wording, model), capability(r), D.before_use(r, places),
            warning(failed_steps(stamps, runs_ok, r, notes)), f'<footer><p>{esc(FOOTER)}</p></footer>']
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
@media print { .block { break-inside: avoid; } }
"""
