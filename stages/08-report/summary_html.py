"""The one page (summary.html), and the counts the brief shares. Spec: specs/summary_html.SPEC.md.

Report v3 (owner, 2026-10-27: "glance and know"): the eight questions of glance.py as cards for
someone with no computer skills, a step that did not work at the bottom, and the one caveat. This
module also holds the security concern kinds in their fixed order (`CONCERNS`, `rows`), the
headline rules, the failed-step rules, and the brief's lines (`brief_*`), which walkdown.py
prints. Same facts as the other reports; nothing here detects or judges, and nothing is picked by
how bad it seems.
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
    """The concern rows with places, in order: {key, name, section, places, ids, not_concerned,
    example}. An example is the first place (stage, file, line) not marked Not concerned. Findings
    that review.html shows as one place (one line named by several) count once in a row, and
    `ids` are the places' review cards, so a place in two rows counts once in all (owner,
    2026-10-12; report v3 recount, 2026-10-27)."""
    card_of, mark_of = _place_marks(r, marks)
    pid = lambda it: card_of.get(M.place_key(it))  # noqa: E731
    out = []
    for key, name, section in CONCERNS:
        mine, seen = [], set()
        for it in sorted((it for it in places if concern(it) == key), key=_where):
            c = pid(it) or ("item", id(it))
            if c not in seen:
                seen.add(c)
                mine.append(it)
        if not mine:
            continue
        nc = [it for it in mine if mark_of.get(pid(it)) == "not-concerned"]
        rest = [it for it in mine if it not in nc]
        ex = rest[0] if rest else None
        out.append({"key": key, "name": name, "section": section, "places": mine, "ids": seen,
                    "not_concerned": len(nc), "example": ex, "example_id": pid(ex) if ex else None})
    return out


def total(rs) -> int:
    """Places across the rows, each place once (rows from `rows`; a bare row counts its places)."""
    if all("ids" in x for x in rs):
        return len(set().union(*(x["ids"] for x in rs)))
    return sum(len(x["places"]) for x in rs)


def wording_count(r, places, rs, marks=None) -> int:
    """The places that are wording only, each once, leaving out a place a concern row holds."""
    card_of, _ = _place_marks(r, marks)
    held = set().union(*(x.get("ids", ()) for x in rs))
    return len({card_of.get(M.place_key(it)) or ("item", id(it)) for it in places if concern(it) is None} - held)


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
    n = total(rs)
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


def results(stamps, runs_ok) -> dict:
    """{stage: result word} for the stages that ran and have a stamp."""
    return {st: s.result for st, s in (stamps or {}).items() if st in runs_ok}


def failed_steps(stamps, runs_ok) -> list[str]:
    """Steps that did not work in this run (owner, 2026-10-20): a step with no output, or one that
    ran and failed its fixture check. Never a step with nothing here to test, or a check that did
    not run for a missing optional tool (INCOMPLETE, any stage; owner, 2026-10-25): "What Walkdown
    didn't check" on details.html lists those. A run made without validation has no stamps and adds
    none here."""
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
    return (f'<p class="warnline" id="warning"><b>Not every step worked in this run.</b> '
            f'{esc("; ".join(steps))}. A step that did not work can miss places, so this page may show '
            f'fewer than there are. <a href="details.html#limits">What Walkdown didn\'t check</a> says why.</p>')


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
    """Report v3 (owner, 2026-10-27: "glance and know"): the eight questions as cards
    (glance.py), a step that did not work at the bottom, and the one caveat. `marks` are the
    run's marks; `changes` is run.changes_for (its cost line goes under question 2)."""
    import glance as G  # glance imports this module
    qs = G.questions(meta, r, stamps, runs_ok, marks)
    for q in qs:
        if q.id == "memory":
            q.more += G.since_line(changes)
    body = (f'<header><h1>{esc(meta["repo"])}</h1><p class="meta">{esc(G.meta_line(meta, r))}</p>'
            f'<p class="what">{G.what_it_is(r)}</p><p class="how">Walkdown reads the files without running '
            "anything. It points things out; you decide what matters. Tap a line for more.</p></header>"
            '<h2>At a glance</h2><ul class="rows">' + "".join(G.card(q) for q in qs) + "</ul>"
            + warning(failed_steps(stamps, runs_ok))
            + '<footer><p>Everything behind this page: <a href="details.html">details</a> \u00b7 '
            '<a href="review.html">go through each place and mark it</a> \u00b7 every finding with its file '
            f'and line: <a href="full.md">full.md</a></p><p>{esc(FOOTER)}</p></footer>')
    return G.page(f"{meta['repo']} at a glance", meta, r, body)
