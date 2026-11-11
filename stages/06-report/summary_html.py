"""The one page (summary.html), and the counts the brief shares. Spec: specs/report.SPEC.md, summary_html.

Report v3 (owner, 2026-10-27: "glance and know"): the four questions of glance.py as cards for
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
import qaview
import render as R
import stagelist
import common_lines
import coverage

# Every rule-found place falls in exactly one row, taken by the first that fits; the rest is
# wording only (owner, 2026-10-20). (key, row name, details.html section the "more" link opens)
CONCERNS = (
    ("hidden", "Hidden text that reads like an instruction", "hidden"),
    ("spelled", "Hidden characters that spell out text", "hidden"),
    ("runs", "Runs code", "risky"),
    ("secret", "Passwords, keys, and secrets", "secrets"),  # R27 (owner 2026-11-06: "rename the group so the counts match"), was "Looks like a committed secret"
    ("out", "Reads secrets, calls out, or shares", "risky"),
    ("lasting", "Lasting changes or permissions", "risky"),
)
WORDING = "{n} {be} wording only: instructions that change how the AI reads, decides, or answers."
# R28 (owner, 2026-11-07, after an outside tester's report): a phrase hit becomes a place only through its pattern
# (`render.point_hits`), so a line no place holds reached full.md only and the pages said Nothing found. They never say
# "found none" now without the lines full.md has, and with places they count them too.
NONE_FOUND = "Walkdown found none of the security concerns it looks for."
NONE_ON_LIST = "Walkdown found none of the security concerns on its list."
OFF_LIST = "full.md has {n} with risky wording, not listed here (section 4)."
# The careful card's lines on the summary (R26, owner 2026-11-06: "Each line should have a color code. And we'll order them by color."; "Password and key should be a red section"; "color list is fin"; "Yes build on that plan."; the color list in
# pre-planning/REPORT-CHANGES-2026-11-05.md): a line per kind, red, then yellow, then blue, the first three under
# "Passwords, keys, and secrets". A place a concern row holds that no kind here names takes its row's color: steps that
# run code and lasting changes yellow, reading secrets, calling out, or sharing red. The answer and the brief still count
# by CONCERNS.
LINES = (
    ("secret", "red", "Looks like a saved password, key, or token"),
    ("creds", "red", "Wording that gathers secrets or credentials"),
    ("enter-secret", "red", "Wording that asks for a password or key"),
    ("hidden", "red", "Hidden text that reads like an instruction"),
    ("spelled", "red", "Hidden characters that spell out text"),
    ("decode-exec", "red", "Decodes hidden code and runs it"),
    ("send", "red", "Wording that sends data out"),
    ("redirect", "red", "Names a variable that redirects network traffic"),
    ("out-other", "red", "Other wording that reads secrets, calls out, or shares"),
    ("hook", "yellow", "A hook that runs commands by itself"),
    ("context-hook", "yellow", "A hook that adds text to the AI's memory before you type"),
    ("human", "yellow", "Tells a person to run something risky"),
    ("fetch", "yellow", "Fetches instructions from elsewhere"),
    ("prompt-leak", "yellow", "Asks the AI to reveal its own instructions"),
    ("persist", "yellow", "Writes to a shell profile or git hooks"),
    ("git-keys", "yellow", "Names a git setting that persists"),
    ("memory", "yellow", "Names a memory or local-settings file"),
    ("irreversible", "yellow", "An irreversible action with no confirmation step"),
    ("redefined", "yellow", "A confirmation step that is redefined"),
    ("read-only", "yellow", "Says read-only, but its tools can write"),
    ("runs-other", "yellow", "Other steps that run code"),
    ("lasting-other", "yellow", "Other lasting changes or permissions"),
    ("cloud", "blue", "Cursor's cloud setup runs commands on Cursor's machine, not yours"),
)
SECRET_LINES = ("secret", "creds", "enter-secret")  # "Passwords, keys, and secrets", first and red
KIND_LINE = {"secret": "secret", "hidden+phrase": "hidden", "hidden+spelled": "spelled", "hook+phrase": "context-hook",
             "rubric.prohibited": "irreversible", "rubric.redefined": "redefined", "limit.contradicted": "read-only"}
PATTERN_LINE = (("creds.", "creds"), ("J.enter-secret", "enter-secret"), ("E.decode-exec", "decode-exec"),
                ("K.prompt-leak", "prompt-leak"), ("K.", "send"), ("E.redirect-var", "redirect"), ("G.", "human"),
                ("RL.", "fetch"), ("E.persist", "persist"), ("E.git-keys", "git-keys"), ("E.memory", "memory"))
# Under the three boxes (owner, 2026-10-20): the trifecta's point, as details.html words it.
TOGETHER = D.TRIFECTA_LEDE.split(". ", 1)[1]
# The page's one qualifier, in plain words for someone who is not technical (owner, 2026-10-20).
# details.html and full.md keep render.NOT_WHAT.
FOOTER = ("Walkdown reads a repository's files without running anything. It points out what it "
          "finds and leaves the judgment to you. Finding nothing does not mean a repository is safe.")
# Under the title (owner, 2026-11-05, R3), in place of "Walkdown reads the files without running anything. It points things
# out; you decide what matters. Tap a line for more." The footer still says the first two.
MADE_BY = ("This report on {name} was made by Walkdown, which checks AI skill and agent repositories for security and how "
           "well they are built.")  # "and agent": owner, 2026-11-05 (R7)
# The page's title (owner, 2026-11-05, R6; it was the name alone); details.html adds ", in detail".
TITLE = "A Walkdown of {name}"


def made_by(name) -> str:
    return MADE_BY.format(name=name)


def title(name) -> str:
    return TITLE.format(name=name)


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def concern(it) -> str | None:
    """The concern row an item belongs to, or None for wording only."""
    if it.get("kind") == "hidden+phrase":
        return "hidden"
    if it.get("kind") == "hidden+spelled":
        return "spelled"
    group = D.action_group(it)
    if group == "runs":
        return "runs"
    if it.get("kind") == "secret":
        return "secret"
    pats = (it.get("src") or {}).get("patterns") or []
    if any(p.startswith("creds.") or p == "J.enter-secret" for p in pats):  # wording about secrets joins them (R27)
        return "secret"
    return group if group in ("out", "lasting") else None


def _where(it) -> tuple:
    src = it.get("src") or {}
    return (stagelist.position(it["stage"]), src.get("file") or it.get("where") or "", src.get("line") or 0)


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


def line_of(it) -> str | None:
    """The careful line a place falls in (R26), or None for wording only: by its kind, else by the phrase pattern behind
    it, else its concern row's "other" line."""
    row = concern(it)
    if row is None:
        return None
    kind = it.get("kind")
    if kind == "hook":
        return "cloud" if (it.get("src") or {}).get("format") == "cursor-environment" else "hook"
    if kind in KIND_LINE:
        return KIND_LINE[kind]
    pats = (it.get("src") or {}).get("patterns") or []
    for prefix, key in PATTERN_LINE:
        if any(p.startswith(prefix) for p in pats):
            return key
    return f"{row}-other"


def lines(r, places, marks=None) -> list[dict]:
    """The careful card's lines with places, in LINES order (R26): {key, color, label, row, places, ids}. A place counts
    once in a line, by its review card, as in `rows`."""
    card_of, _ = _place_marks(r, marks)
    out = []
    for key, color, label in LINES:
        mine, seen = [], set()
        for it in sorted((it for it in places if line_of(it) == key), key=_where):
            c = card_of.get(M.place_key(it)) or ("item", id(it))
            if c not in seen:
                seen.add(c)
                mine.append(it)
        if mine:
            out.append({"key": key, "color": color, "label": label, "row": concern(mine[0]), "places": mine, "ids": seen})
    return out


def total(rs) -> int:
    """Places across the rows, each place once (rows from `rows`; a bare row counts its places)."""
    if all("ids" in x for x in rs):
        return len(set().union(*(x["ids"] for x in rs)))
    return sum(len(x["places"]) for x in rs)


def off_list(r, places) -> int:
    """The lines full.md lists under What the text asks for that no place on the pages is on (R28): `02.4-phrases` hits
    outside human-facing files and test data, as places are, on a line no place holds."""
    at = lambda x: (x.get("file"), x.get("line"), x.get("page"))  # noqa: E731
    held = {at(h) for h, _ in R.point_hits(r)} | {at(it.get("src") or {}) for it in places}
    return len({at(h) for h in R.phrase_hits(r)
                if h.get("audience") not in ("human", "test-data") and "skipped" not in h} - held)


def off_list_sentence(k) -> str:
    """"full.md has 3 more lines with risky wording, not listed here (section 4)." (R28)"""
    return OFF_LIST.format(n=R.n(k, "more line"))


def wording_count(r, places, rs, marks=None) -> int:
    """The places that are wording only, each once, leaving out a place a concern row holds."""
    card_of, _ = _place_marks(r, marks)
    held = set().union(*(x.get("ids", ()) for x in rs))
    return len({card_of.get(M.place_key(it)) or ("item", id(it)) for it in places if concern(it) is None} - held)


def not_run(qa, ai: bool = False) -> list[str]:
    """The steps that produced no output in this run, by their plain names: the check of the run's `step-missing` gaps. The
    coded steps, and with `ai` a chosen AI step that was started and left none; an AI step nobody chose is never named
    (restructure step 5). A coded step the run's stop left out is not one that failed: the check makes it a limit, not
    a gap, so it is not named here."""
    return [D.PLAIN_STAGE[st] for st in qa.steps_missing() if ai or st not in R.AI_STAGES]


def model_down(qa) -> list[str]:
    """The model reads that did not work, by their plain names (M9): a chosen step that left no output (it failed), and
    one that ran and got no answer for any passage, even after the retry. A model read never adds a security
    concern, so the headline says these apart from the coded steps that did not run (`not_run` names those alone)."""
    return [D.PLAIN_STAGE[g["step"]] for g in qa.gaps
            if g["kind"] == "model-no-answer" or (g["kind"] == "step-missing" and g["step"] in R.AI_STAGES)]


def incomplete_checks(qa) -> list[str]:
    """The coded steps whose fixture check is INCOMPLETE (a check skipped for a missing optional tool), by their plain
    names. They are not failures (owner, 2026-10-25), but they are why a run cannot say its coded checks are complete."""
    return [D.PLAIN_STAGE[f["step"]] for f in qa.of("fixture-incomplete") if f["step"] in R.NAMED]


def model_down_sentence(failed=(), incomplete=()) -> str:
    """What the headline and question 8 add when a model read did not work. With every coded step passing its fixture
    check: the coded checks are complete. With a coded step that failed it (`failed`): only that the read did not work,
    since the coded checks are not complete. With a coded step INCOMPLETE (`incomplete`, a check skipped for a missing
    tool): the coded checks ran, and where the skipped ones are named."""
    if failed:
        return R.MODEL_READ_DOWN.capitalize() + "."
    if incomplete:
        return ("The coded checks ran, and \"What this run covered\" names any skipped for a missing tool; "
                f"{R.MODEL_READ_DOWN}.")
    return f"The coded checks are complete; {R.MODEL_READ_DOWN}."


def failed_checks(qa) -> list[str]:
    """The steps that ran and did not pass their fixture check, or whose check could not be made, by their plain names (the
    check of the run's `fixture-failed` and `fixture-unchecked` gaps). INCOMPLETE is never one (owner, 2026-10-25): a check
    that did not run for a missing optional tool stays in details.html and full.md. A step with no fixture set (Pinpoint) has
    nothing to fail (restructure step 5, decision 5-C). A step whose coverage does not add up (a check looked at fewer
    items than it should have, and does not say why; M9 slice C) is named here too: its zeros are as little to be
    trusted, once each however many of its checks fell short."""
    names = [D.PLAIN_STAGE[f["step"]] for f in qa.of("fixture-failed", *common_lines.COVERAGE_KINDS)]
    return list(dict.fromkeys(names))


def unchecked_checks(qa) -> list[str]:
    """The steps whose fixture check could not be made (ERROR, SETUP ERROR, NOT BUILT, `no fixture set`), by their plain
    names. They ran and wrote their output; their zeros are not validated, which is not the same as a step that did not work."""
    return [D.PLAIN_STAGE[f["step"]] for f in qa.of("fixture-unchecked")]


def unchecked_sentence(qa) -> str | None:
    """The one sentence the pages and the brief say of the steps whose check could not be made, without its full stop, or
    None. One step is named with what its check gave; several are counted once (`8 steps could not be checked against their
    fixtures, so their zeros are not measured`) in one sentence."""
    got = qa.of("fixture-unchecked")
    if not got:
        return None
    if len(got) == 1:
        return f"{D.PLAIN_STAGE[got[0]['step']]} {common_lines.unchecked_phrase(got[0]['result'])}"
    return common_lines.UNCHECKED_MANY.format(n=len(got))


def headline(rs, missing=(), failed=(), stop=None, model=(), incomplete=(), unchecked=None, off=0) -> str:
    """`missing`: coded steps that did not run (`not_run`); `failed`: steps that ran and failed their
    fixture check (`failed_checks`). A run missing a step never says it found none (2026-10-21,
    an outside tester: an empty .venv crashed `02.1-inventory` and the page said "found none"), and with
    no concerns a failed check is said here, not only at the bottom (owner, 2026-10-25, C40). A run that
    stopped as asked before its last coded step (`stop`, from the record) says so, in the same two forms,
    since the steps after the stop are not ones that failed (O3). `model`: model reads that did not work
    (`model_down`); a model read never adds a concern, so the headline says the coded checks are complete and the
    read did not work, and does not say it cannot say (M9, restructure M14 b); `incomplete`: coded steps with a
    check skipped for a missing tool (`incomplete_checks`), for which "complete" is worded truly. `unchecked`: the one
    sentence for steps whose fixture check could not be made (`unchecked_sentence`); they ran, so it is not "not every step
    worked", and it follows the answer. `off`: the lines full.md has that no place holds (`off_list`, R28); with no
    concerns the line says "on its list" and counts them."""
    n = total(rs)
    if missing:
        steps = (f'the step "{missing[0]}" did not run' if len(missing) == 1 else
                 f'{len(missing)} steps did not run, starting with "{missing[0]}"')
        if rs:
            return (f"This run did not complete: {steps}. In the steps that ran, Walkdown found "
                    f"security concerns: {R.n(n, 'place')}, of {R.n(len(rs), 'kind')}.")
        return (f"This run did not complete: {steps}, so Walkdown cannot say whether this "
                "repository has the security concerns it looks for.")
    if R.stopped_left(stop):
        said = f'This run stopped after the step "{R.stop_plain(stop)}", as asked'
        if rs:
            return (f"{said}. In the steps that ran, Walkdown found security concerns: "
                    f"{R.n(n, 'place')}, of {R.n(len(rs), 'kind')}.")
        return f"{said}, so Walkdown cannot say whether this repository has the security concerns it looks for."
    down = (f" {model_down_sentence(failed, incomplete)}" if model else "") + (f" {unchecked}." if unchecked else "")
    if rs:
        nc = sum(x["not_concerned"] for x in rs)
        return (f"Walkdown found security concerns in this repository: {R.n(n, 'place')}, of "
                f"{R.n(len(rs), 'kind')}." + (f" ({nc} of them marked Not concerned.)" if nc else "") + down)
    # R32 ("brief follows the summary"): with no concerns, no "found none"; what is left is what full.md has that no place
    # holds, and that not every step worked or the model read did not; it may be nothing at all
    more = off_list_sentence(off) if off else ""
    if failed:
        return " ".join(x for x in (more, "Not every step worked, so Walkdown may have missed some." + down) if x)
    return (more + down).strip()


def not_working_pairs(qa) -> list[tuple[str, str]]:
    """(stage, words) for each step that did not work in this run (owner, 2026-10-20): the check of the run's gaps, in its
    order. A step with no output, one that ran and failed its fixture check, and a model read that got no answer for any
    passage, even after the retry (M9). Never a step with nothing here to test, a check that did not run for a missing
    optional tool (INCOMPLETE; owner, 2026-10-25), or a step the run's stop left out (O3): "What this run covered"
    on details.html lists those. A run made without validation has no stamps and adds none here. A gap of a kind
    this does not know (a later check's) is worded from what it found."""
    out = []
    for g in qa.gaps:
        name = D.PLAIN_STAGE[g["step"]]
        if g["kind"] == "fixture-unchecked":  # said once, apart (`unchecked_sentence`): the step ran
            continue
        out.append((g["step"], f"{name} did not run" if g["kind"] == "step-missing" else
                    f"{name} did not pass its fixture check ({g['result']})" if g["kind"] == "fixture-failed" else
                    f"{name} got no answer for any passage" if g["kind"] == "model-no-answer" else
                    common_lines.coverage_page_words(g) if g["kind"] in common_lines.COVERAGE_KINDS else
                    f"{name}: {g.get('found')}"))
    return out


def not_working(qa) -> list[str]:
    """The steps that did not work in this run, in words: the summary's warning, details.html's first line, and the brief
    all say these."""
    return [words for _, words in not_working_pairs(qa)]


def only_model_reads(qa) -> bool:
    """Whether every step that did not work is a model read. A model read never adds a security concern, so then the
    pages do not say that a step that did not work can miss places."""
    pairs = not_working_pairs(qa)
    return bool(pairs) and all(st in R.AI_STAGES for st, _ in pairs)


def warning(steps, model_only=False, unchecked=None) -> str:
    """One line at the bottom of the page, above the footer, only when a step did not work
    (owner, 2026-10-21). When the only step that did not work is a model read (`model_only`), it does not say the page
    may show fewer places than there are: a model read adds none of the places this page counts. `unchecked`: the one
    sentence for steps whose fixture check could not be made; they ran, so with no other trouble the line is that sentence
    alone and does not say a step did not work."""
    link = '<a href="details.html#limits">What Walkdown didn\'t check</a> says why.'
    if not steps:
        return f'<p class="warnline" id="warning"><b>{esc(unchecked)}.</b> {link}</p>' if unchecked else ""
    may_miss = "" if model_only else (" A step that did not work can miss places, so this page may show fewer than "
                                      "there are.")
    return (f'<p class="warnline" id="warning"><b>Not every step worked in this run.</b> '
            f'{esc("; ".join(steps))}.{may_miss}{" " + esc(unchecked) + "." if unchecked else ""} {link}</p>')


def stop_note(stop) -> str:
    """One line under the cards of a run that stopped just before a model read (O3): where it stopped, what the
    waiting read would send and the file that holds it, and that nothing was sent. Empty for any other run."""
    line = R.stop_input_line(stop)
    return f'<p class="since" id="stopped">{esc(line)}</p>' if line else ""


def model_note(qa) -> str:
    """One line under the cards when a model read has some passages that got no answer, or a chosen step was not
    started (M9): the count, as the details page says it. A read that got no answer for any passage is not counted
    here: the headline and the warning already say it. Empty for any other run."""
    lines = R.model_read_lines(qa, exclude=R.model_read_nothing(qa)) + R.not_started_lines(qa)
    return f'<p class="since" id="modelread">{esc(" ".join(lines))}</p>' if lines else ""


# R32 (owner, 2026-11-07: "brief follows the summary"): a brief line says what was found; a count of none is left out, and a
# line with nothing found is no line.
def _found(parts) -> list[str]:
    """The parts whose count is not zero: [(count, words), ...] -> [words]."""
    return [w for k, w in parts if k]


def brief_misalign_line(r) -> str | None:
    """The brief's line (R13, 2026-11-05; it took the place of "Will it trigger"): counts only, as the page has them; only
    what was found (R32)."""
    m = R.misalign_of(r)
    if not m["measured"] or not m["skills"]:
        return None
    places = sum(len(v) for v in m["groups"].values())
    found = _found(((places, f"{R.n(places, 'place')} that {'differs' if places == 1 else 'differ'} from the Agent Skills "
                              "standard"),
                    (len(m["alike"]), f"{R.n(len(m['alike']), 'pair')} of skills described alike")))
    return f"Misalignment: {R.n(m['skills'], 'skill')}; " + "; ".join(found) + "." if found else None


def brief_ready_line(r, targets=()) -> str | None:
    """The brief's line (slice 3): counts only."""
    rd = R.ready_of(r)
    if not rd["measured"]:
        return None
    have = sum(1 for c in rd["coverage"] if R.has_files(c))
    feats = sum(len(p) for *_, p in rd["features"])
    found = _found(((have, f"{have} of {len(rd['coverage'])} hosts have their files here"),
                    (len(rd["differ"]), f"copies that differ: {len(rd['differ'])}"), (feats, f"one-host features: {feats}")))
    left = [x for x in R.todo(r, targets) if not x.endswith(": nothing missing.")] if targets else []
    s = ("Ready for: " + "; ".join(found) + "." if found else "") + (
        f" For the hosts named: {R.n(len(left), 'thing')} missing." if left else "")
    return s.strip() or None


def brief_clean_line(r) -> str | None:
    """The brief's line (slice 6): counts only."""
    cl = R.clean_of(r)
    if not cl["measured"]:
        return None
    k = {kind: len(p) for kind, _, _, p in cl["kinds"]}
    m = k.get("models", 0)
    found = _found(((k.get("unfinished", 0), f"{k.get('unfinished', 0)} unfinished"),
                    (k.get("dated", 0), R.n(k.get("dated", 0), "dated claim")),
                    (m, R.n(m, "pinned model ID") + (f" ({len(cl['models'])} distinct)" if m and len(cl["models"]) != m else "")),
                    (k.get("older", 0), R.n(k.get("older", 0), "older tool name"))))
    return "Current and clean: " + ", ".join(found) + "." if found else None


def brief_fit_line(r) -> str | None:
    """The brief's line (slice 5): counts only."""
    ft = R.fit_of(r)
    if not ft["measured"]:
        return None
    c = R.brief_fit_counts(ft)
    first = ", ".join(_found(((c["unused"], f"{c['unused']} granted and never used"),
                              (c["missing"], f"{R.n(c['missing'], 'task')} with no tool"),
                              (c["loops"], f"{R.n(c['loops'], 'loop')} with no stated limit"))))
    hooks = (f"{R.n(c['hooks'], 'hook')} {'runs' if c['hooks'] == 1 else 'run'} on every prompt or tool call" if c["hooks"] else "")
    said = "; ".join(x for x in (first, hooks) if x)
    return f"Tools fit: {said}." if said else None


def brief_needs_line(r) -> str | None:
    """The brief's line (slice 2): counts only; package names come from the repository."""
    n_ = R.needs_of(r)
    if not n_["measured"]:
        return None
    places = sum(len(p) for *_, p in n_["port"])
    uses = ", ".join(_found(((len(n_["commands"]), R.n(len(n_["commands"]), "program")),
                             (len(n_["packages"]), R.n(len(n_["packages"]), "package")))))
    needs = "; ".join(x for x in (uses, f"{len(n_['undeclared'])} not declared" if n_["undeclared"] else "") if x)
    s = (f"Needs: {needs}." if needs else "") + (f" Ties to one machine: {R.n(places, 'place')}." if places else "")
    return s.strip() or None


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
    """Report v3 (owner, 2026-10-27: "glance and know"): the four questions as cards, then Misalignment as one more card (R24)
    (glance.py), a step that did not work at the bottom, and the one caveat. `marks` are the
    run's marks; `changes` is run.changes_for (its cost line goes under Size and Shape's memory part, last)."""
    import glance as G  # glance imports this module
    qs = G.questions(meta, r, stamps, runs_ok, marks)
    for q in qs:
        if q.id == "size":
            q.more += G.since_line(changes)
    # the parts details.html has, so a Details button never points at one it lacks (R1)
    known = ({q.id for q in qs} | G.ids_in("".join(q.more + q.detail for q in qs)) | {"examined", "can"}
             | G.ids_in(G.misalign_detail(r, meta.get("stop"))))
    examined = coverage.section_html(r).replace(
        "<h2>What Walkdown examined</h2>", f'<div class="head-row" id="examined"><h2>{G.icon("examined")}What Walkdown examined</h2>{G.go("examined")}</div>', 1)
    body = (f'<header><h1>{esc(title(meta["repo"]))}</h1><p class="meta">{esc(G.meta_line(meta, r))}</p>'
            f'<p class="how">{esc(made_by(meta["repo"]))}</p><p class="what">{G.what_it_is(r, meta["repo"])}</p></header>'
            + G.draw_goes(G.can_section(r), "can", known)
            + G.draw_goes(examined, "examined", known)
            + '<h2>At a glance</h2><ul class="rows">' + "".join(G.card(q, known) for q in qs)
            + G.card(G.misalign_card(r, meta.get("stop")), known) + "</ul>"  # the last card, nothing to open (R24)
            + stop_note(meta.get("stop"))
            + model_note(qaview.of(meta))
            + warning(not_working(qaview.of(meta)), only_model_reads(qaview.of(meta)), unchecked_sentence(qaview.of(meta)))
            + '<footer><p>Everything behind this page: <a href="details.html">details</a> \u00b7 '
            '<a href="review.html">go through each place and mark it</a> \u00b7 every finding with its file '
            f'and line: <a href="full.md">full.md</a></p><p>{esc(FOOTER)}</p></footer>')
    return G.page(title(meta["repo"]), meta, r, body)
