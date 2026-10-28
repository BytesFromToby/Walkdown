"""The details page (details.html), and the places every page shares. Spec: specs/details_html.SPEC.md.

Report v3 (owner, 2026-10-27): the page is the eight questions of glance.py as sections, with
everything behind each answer. This module also holds what the other pages and the brief share:
the places to check (`first_items`, which review.html walks and marks.py keys), the plain names
of stages, hidden-text kinds, risky-wording groups, and who reads a file, the trifecta's places
(`_leg_ev`), what installing it allows (`_allows`), the links, and the license line. Nothing here
detects or judges; marking is on review.html only (owner, 2026-10-27).
"""
from __future__ import annotations

import collections
import unicodedata
import html

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


# ---------------------------------------------------------------- report v2 sections (2026-10-16)

TRIFECTA_LEDE = ("Simon Willison's name for three things an AI tool can do. Each one is ordinary on its "
                 "own. A tool that does all three can be steered by text from outside into sending "
                 "your data away.")
READ_BY = {"model": "the AI", "subagent": "the AI", "tool": "scripts", "human": "people",
           "test-data": "test data"}
LIST_MAX = 6    # files named in a line of the stats before "+N more"
TOP_DIRS = ("", ".claude-plugin")  # where a repo's own license and manifest sit


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


# ---------------------------------------------------------------------------- Not concerned
# Owner, 2026-10-20: every row that names a place or an address could be marked Not concerned
# here until report v3 (2026-10-27: marking on review.html only). mark_rows keeps those rows so
# a marks file saved then still loads. A row's id is what marks.match matches it to: a place's
# review card id, anything else its stable key.


def _line_text(r) -> dict:
    """{(file, line): stage 4's quote of that line}, the text a trifecta place's key names."""
    out = {}
    for f in R.fnd(r, "04-phrases"):
        if f.get("quote") and f.get("file") and f.get("line") is not None:
            out.setdefault((f["file"], f["line"]), f["quote"])
    return out


def _ev_key(leg, e, texts) -> str:
    return M.evidence_key(leg, e.get("file"), texts.get((e.get("file"), e.get("line"))) or e.get("line"))


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


CHECK_GROUP = {"phrase.G.human": "runs", "phrase.K.exfil": "out", "phrase.creds": "out",
               "phrase.remote-load": "out", "phrase.E.perms": "lasting", "phrase.E.env": "lasting",
               "phrase.C.second-order": "lasting", "phrase.J.prohibited": "lasting"}
KIND_GROUP = {"hook": "runs", "hook+phrase": "runs", "secret": "out", "rubric.prohibited": "lasting",
              "rubric.redefined": "lasting", "limit.contradicted": "lasting"}


def action_group(it) -> str:
    """Which of ACTION_GROUPS an item falls in: by its kind, else by the phrase check behind it."""
    if it.get("kind") in KIND_GROUP:
        return KIND_GROUP[it["kind"]]
    src = it.get("src") or {}
    check = src.get("check") if str(src.get("check", "")).startswith("phrase.") else src.get("phrase_check")
    return CHECK_GROUP.get(check, "words")


def render_page(meta, r, stamps, notes, runs_ok, changes=None, marks=None) -> str:
    """Report v3 (owner, 2026-10-27): the eight questions as sections with everything behind
    them (glance.py), what changed since the earlier run, and what this run did not check.
    Marking is on review.html only (owner, 2026-10-27)."""
    import glance as G  # glance imports this module
    qs = G.questions(meta, r, stamps, runs_ok, marks)
    toc = "".join(f'<a href="#{q.id}">{esc(TOC[q.id])}</a>' for q in qs) + '<a href="#limits">Not checked</a>'
    body = (f'<header><h1>{esc(meta["repo"])} in detail</h1><p class="meta">{esc(G.meta_line(meta, r))} \u00b7 '
            f'<a href="summary.html">back to the summary</a></p>{license_line(r)}'
            f'<p class="what">{G.what_it_is(r)} Everything behind the summary, question by question; long lists '
            "are folded, tap to open them.</p></header>"
            f'<nav class="toc">{toc}</nav>' + "".join(G.section(q) for q in qs)
            + G.changes_section(changes) + G.not_checked(r, stamps, notes, runs_ok)
            + '<footer><p>Mark each place as you go: <a href="review.html">go through each place</a> \u00b7 '
            'every finding with its file and line: <a href="full.md">full.md</a></p>'
            f"<p>{esc(R.NOT_WHAT)}</p></footer>")
    return G.page(f"{meta['repo']} in detail", meta, r, body)


TOC = {"switch": "Switching on", "memory": "Memory", "package": "Package", "elsewhere": "Other computers",
       "hosts": "Other AI tools", "tools": "Tools", "clean": "Finished", "careful": "Careful"}
