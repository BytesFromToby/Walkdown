"""The review page: walk the flagged places one at a time and mark each. Spec: specs/review_html.SPEC.md.

Review C21 (owner, 2026-10-08; built 2026-10-12). The places are the summary's "Things to
check" (summary_html.first_items), one card each, then the stage 6 model reads. A card shows
the line with three lines either side, taken from the text this run read
(data/normalized/text/), what was flagged in plain words (plain.py), and three marks:
Concerned, Not concerned, Not sure. Walkdown makes no call on any place; the reader does, on
the page. Marks are kept in the browser as they are made and leave as marks.json, which the
reader saves into the run folder; a re-render reads that file back into the page. Marks never
change a finding, the summary, or full.md.

Every string from the audited repository is escaped here, in Python. The page script handles
marks and navigation only and never builds markup from repository text.
"""
from __future__ import annotations

import hashlib
import html
import json
import unicodedata
from pathlib import Path
from urllib.parse import quote as urlquote

import plain
import render as R
import summary_html as S

CONTEXT = 3          # lines shown before and after the flagged line
MAX_SPAN = 12        # a stage 6 passage longer than this shows its first lines only
LINE_CAP = 300       # characters shown of a context line
FOCUS_CAP = 420      # characters shown of the flagged line, around its first match
MARKS_FILE = "marks.json"
MARKS = (("concerned", "Concerned", "You want to look into it, or change it."),
         ("not-concerned", "Not concerned", "You read it, and it is fine for what this skill is for."),
         ("not-sure", "Not sure", "You cannot tell from what is shown."))
MARK_KEYS = tuple(k for k, _, _ in MARKS)
# Stage 4's words (stages/04-phrases/run.py SECRET_MASK): a report never repeats a secret.
SECRET_MASK = "[line not shown: it holds what looks like a secret; open the file to see it]"
NO_CONTEXT_SECRET = ("Lines around this place are not shown: the file holds what looks like a "
                     "secret, and a secret can run over several lines. Open the file to read it.")

# Why a place of each kind is listed, for kinds whose pattern words alone do not say it.
WHY = {
    "hidden+phrase": "What the model reads here differs from what a person sees on the rendered "
                     "page, and the line matches the wording of an instruction.",
    "orphan+phrase": "No file in the repository refers to this one, so a reviewer following links "
                     "never reaches it. It still ships, and it matches the wording of an instruction.",
    "dynamic+phrase": "No file names this one. It loads only because a folder or use of wildcards pulls it in, "
                      "so a reviewer following links never reaches it, and it matches the wording of "
                      "an instruction.",
    "hook+phrase": "A hook runs this script when a session starts or a prompt is sent, and its output "
                   "reaches the model before you type anything.",
    "term.conflict": "The same word is defined in more than one way. A model may follow whichever "
                     "definition it read last.",
    "term.safety": "A word the rules lean on (done, verified, safe, and the like) is given its own "
                   "meaning here. What the model counts as that word follows this line.",
    "rubric.redefined": "The step asks for confirmation, and the confirmation word is itself "
                        "redefined, so the confirmation may not mean what it says.",
    "rubric.prohibited": "Claude Code's rules say the model never takes this kind of action, or "
                         "takes it only after the user confirms. No confirmation appears in the "
                         "same step.",
}
WHY_SAYS_NOTE = {"hook+phrase"}  # kinds whose WHY already says what the summary's note says
PIN_NOTE = ("These are two models' readings (one flagged the passage, a second pointed at the "
            "line), not a pattern match.")
MODEL_NOTE = ("This is one model's reading, not a pattern match. Models can be wrong, and reading "
              "the same passage again can give a different answer. Nothing checks it after the "
              "model: you are the check. It does not change any other finding.")


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


# ---------------------------------------------------------------------------- the places


def _file_line(it) -> tuple[str | None, int | None, int | None]:
    """(file, first line, last line) of an item's place; lines are None when it has none."""
    src = it.get("src") or {}
    if it.get("kind") == "term.conflict":
        d = (src.get("definitions") or [{}])[0]
        return d.get("file"), d.get("line"), d.get("line")
    line = src.get("line")
    return src.get("file"), line, src.get("end_line") or line


def _question_patterns(r) -> dict:
    """Stage 6 question id -> the stage 4 patterns behind it (labels carry only the qid)."""
    out = {}
    for q in R._soft(r)["questions"]:
        pats = []
        for s in q.get("sources") or []:
            pats += [p for p in s.get("patterns") or [] if p not in pats]
        out[q.get("qid")] = pats
    return out


def _hit_index(r) -> dict:
    """(file, line) -> the stage 4 phrase hits there (their patterns and matched text)."""
    out = {}
    for h in R.phrase_hits(r):
        out.setdefault((h.get("file"), h.get("line")), []).append(h)
    return out


def _patterns(it, qpats) -> list[str]:
    """Every pattern behind the place, from its finding and any merged into it (`also`);
    for a stage 4 point, the point patterns first."""
    out = []
    for src in [it.get("src")] + list(it.get("also") or []):
        src = src or {}
        pats = (qpats.get(src.get("qid"), []) if it.get("kind") in ("label", "read")
                else src.get("patterns") or [])
        out += [p for p in pats if p not in out]
    if it.get("kind") == "phrase":
        point = sorted(R.POINT_PATTERNS & set(out))
        out = point + [p for p in out if p not in point]
    return out


def place_id(it) -> str:
    """Stable within a run's saved outputs: the same place gets the same id on a re-render."""
    key = "\x1f".join(str(x) for x in (it["stage"], it["title"], it["where"], it.get("quote") or ""))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def findings_at(r) -> list[dict]:
    """One entry per summary item, in its order: deterministic items, then model reads."""
    qpats = _question_patterns(r)
    hits = _hit_index(r)
    pins = {f.get("sweep_qid"): f for f in R.fnd(r, "06-soft", "soft.pinpoint") if "skipped" not in f}
    out = []
    for it in S.first_items(r):  # one item per finding already (summary_html.unique)
        f, line, end = _file_line(it)
        pats = _patterns(it, qpats)
        matches = []
        for h in hits.get((f, line), []):
            matches += [m for m in h.get("matches") or [] if not pats or m.get("pattern") in pats]
        out.append({**it, "id": place_id(it), "file": f, "line": line, "end_line": end,
                    "patterns": pats, "matches": matches, "model": it["stage"] == 6,
                    "pin": pins.get((it.get("src") or {}).get("qid")) if it.get("kind") == "sweep" else None})
    return out


def _rep_locations(x) -> list[tuple]:
    return [(w.get("file"), w.get("line")) for w in (x.get("src") or {}).get("where") or []]


def places(r) -> list[dict]:
    """One card per place (review C33, 2026-10-16; partner's v3: 332 cards on 293 lines). Every
    finding on one line is one place, whichever stage found it, and a model read of that line
    joins it; a sentence repeated across files is one place, with every location listed, and the
    findings at those locations join it. A passage (more than one line) or a place with no line
    stays on its own. The first member leads the card (a repeated sentence leads its group);
    every member stays on the card as `parts`. A place of one finding keeps that finding's id,
    so a reader's marks carry over; a merged place's id comes from its members' ids."""
    base = findings_at(r)
    rep_of = {}
    for x in base:
        if x.get("kind") == "rep.sentence":
            for loc in _rep_locations(x):
                rep_of.setdefault(loc, x["id"])
    groups: dict[tuple, list] = {}
    for x in base:
        one_line = x.get("file") and x.get("line") is not None and x.get("end_line") in (None, x["line"])
        loc = (x.get("file"), x.get("line"))
        if x.get("kind") == "rep.sentence":
            gk = ("rep", x["id"])
        elif one_line and loc in rep_of:
            gk = ("rep", rep_of[loc])
        elif one_line:
            gk = ("line",) + loc
        else:
            gk = ("one", x["id"])
        groups.setdefault(gk, []).append(x)
    out = []
    for members in groups.values():
        lead = (next((m for m in members if m.get("kind") == "rep.sentence"), None)
                or next((m for m in members if not m["model"]), members[0]))
        parts = [lead] + [m for m in members if m is not lead]
        matches = []
        for m in parts:
            if (m.get("file"), m.get("line")) == (lead.get("file"), lead.get("line")):
                matches += [x for x in m["matches"] if x not in matches]
        pid = lead["id"] if len(parts) == 1 else hashlib.sha1(
            "".join(sorted(m["id"] for m in parts)).encode("utf-8")).hexdigest()[:12]
        out.append({**lead, "id": pid, "parts": parts, "matches": matches,
                    "patterns": [p for m in parts for p in m["patterns"]],
                    "model": all(m["model"] for m in parts)})
    det = [p for p in out if not p["model"]]
    return det + [p for p in out if p["model"]]


# ---------------------------------------------------------------------------- the text


def _secret_files(r) -> set:
    return {x.get("file") for x in R.fnd(r, "04-phrases", "secret.found") if "skipped" not in x}


def read_lines(text_dir, file) -> list[str] | None:
    """The true text of `file` as this run read it (stage 2's normalized/text copy), or None."""
    if text_dir is None or not file:
        return None
    p = Path(text_dir) / f"{file}.txt"
    try:
        return p.read_text(encoding="utf-8", errors="replace").split("\n")
    except OSError:
        return None


def _invisible(ch: str) -> bool:
    cp = ord(ch)
    return ch != "\t" and (unicodedata.category(ch) in ("Cf", "Cc", "Zl", "Zp")
                           or 0xE0000 <= cp <= 0xE007F)


def _spans(line: str, matches) -> list[tuple[int, int]]:
    """Where each matched text sits in the true line. Offsets are on the folded line, so use
    them when the text is there, else search for it; a match that cannot be placed is left out."""
    out, low = [], line.lower()
    for m in matches or []:
        t = str(m.get("text") or "")
        if not t:
            continue
        s = m.get("start")
        if isinstance(s, int) and low[s:s + len(t)] == t.lower():
            out.append((s, s + len(t)))
            continue
        i = low.find(t.lower())
        if i >= 0:
            out.append((i, i + len(t)))
    return sorted(out)


def render_line(line: str, spans=(), cap: int = LINE_CAP) -> str:
    """One line as HTML: escaped, matched spans in <mark>, invisible characters shown as
    U+XXXX badges, and long lines cut around the first match with the cut counted."""
    a, b = 0, len(line)
    if b > cap:
        first = spans[0][0] if spans else 0
        a = max(0, min(first - cap // 3, b - cap))
        b = min(len(line), a + cap)
    on = [False] * len(line)
    for s, e in spans:
        for i in range(max(s, a), min(e, b)):
            on[i] = True
    parts, cur, cur_on = [], [], None

    def flush():
        if cur:
            txt = "".join(cur)
            parts.append(f"<mark>{txt}</mark>" if cur_on else txt)

    for i in range(a, b):
        ch = line[i]
        piece = (f'<span class="inv" title="invisible character">U+{ord(ch):04X}</span>'
                 if _invisible(ch) else esc(ch))
        if on[i] != cur_on:
            flush()
            cur, cur_on = [], on[i]
        cur.append(piece)
    flush()
    head = f'<span class="cut">… {a:,} characters · </span>' if a else ""
    tail = f'<span class="cut"> · {len(line) - b:,} more characters</span>' if b < len(line) else ""
    return head + "".join(parts) + tail


def context_html(p, lines, secret: bool) -> str:
    """The flagged line(s) with CONTEXT lines either side, numbered; or the quote when the
    file's text is not available; or a note when the file holds a possible secret."""
    if secret:
        q = (f'<pre class="ctx">{_row("▶", esc(SECRET_MASK), True)}</pre>'
             if p.get("line") is not None else "")
        return q + f'<p class="hint">{esc(NO_CONTEXT_SECRET)}</p>'
    line, end = p.get("line"), p.get("end_line")
    if lines is None or line is None or not (1 <= line <= len(lines)):
        quote = p.get("quote")
        if not quote:
            return ""
        return f'<pre class="ctx">{_row("▶", render_line(quote, _spans(quote, p["matches"]), FOCUS_CAP), True)}</pre>'
    end = min(end or line, len(lines))
    pin = p.get("pin") or {}
    spans = ([(pin["pin_line"], pin.get("pin_end") or pin["pin_line"])]
             + [(a["line"], a.get("line_end") or a["line"]) for a in pin.get("also") or []]
             if pin.get("verified") and pin.get("pin_line") is not None else [])
    if spans:  # a pinpointed passage opens around the named lines, and only they are shaded
        first = max(line, min(s for s, _ in spans) - CONTEXT)
        last = min(end, max(e for _, e in spans) + CONTEXT, first + MAX_SPAN - 1)
        lo, hi, shown = first, last, last
        if first > line:
            rows = [_row("", f'<span class="cut">{esc(R.n(first - line, "line"))} above in this '
                             f'passage.</span>', False)]
        else:
            rows = []
    else:
        shown = min(end, line + MAX_SPAN - 1)  # a long passage shows its first MAX_SPAN lines
        lo, hi = max(1, line - CONTEXT), min(len(lines), shown + (CONTEXT if shown == end else 0))
        rows = []
    for n in range(lo, hi + 1):
        text = lines[n - 1].rstrip("\r")
        target = (any(s <= n <= e for s, e in spans) if spans else line <= n <= shown)
        body = (render_line(text, _spans(text, p["matches"]) if n == line else (), FOCUS_CAP)
                if target else render_line(text))
        rows.append(_row(str(n), body, target))
    if shown < end:
        rows.append(_row("", f'<span class="cut">{esc(R.n(end - shown, "more line"))} in this '
                             f'passage; open the file to read {"it" if end - shown == 1 else "them"}.</span>',
                         False))
    return f'<pre class="ctx">{"".join(rows)}</pre>'


def _row(num: str, body: str, target: bool) -> str:
    """One numbered line of a context block; `body` is HTML already escaped."""
    return (f'<span class="ln{" t" if target else ""}"><span class="n">{num}</span>'
            f'<span class="tx">{body or " "}</span></span>')


# ---------------------------------------------------------------------------- the page


def _links(p, text_href) -> str:
    """The location, linked to the run's own copy of the text. No link to the original file and,
    on a model read, no "(p=...)": the score is in "What the model said" (owner, 2026-10-13)."""
    f = p.get("file")
    if not f:
        return ""
    where = f"{f}:{p['line']}" if p.get("line") is not None else f
    if p.get("end_line") and p.get("line") is not None and p["end_line"] != p["line"]:
        where += f"-{p['end_line']}"
    extra = p["where"][len(where):].strip() if p["where"].startswith(where) else ""
    if p["model"]:
        extra = ""
    out = []
    if text_href:
        out.append(f'<a href="{esc(text_href.rstrip("/") + "/" + urlquote(f) + ".txt")}" '
                   f'title="The text this run read, kept in the run folder">{esc(where)}</a>')
    else:
        out.append(f"<span>{esc(where)}</span>")
    tail = f' <span class="muted">{esc(extra)}</span>' if extra else ""
    return f'<div class="where">{" · ".join(out)}{tail}</div>'


def _flagged(p) -> str:
    """What was flagged: every finding on the place, each under its own headline when there is
    more than one (review C33)."""
    parts = [m for m in p.get("parts") or [p] if not m["model"]] if not p["model"] else [p]
    seen: set = set()  # a pattern is described once per card
    home = (p.get("file"), p.get("line"))
    blocks = [_flagged_one(m, title=len(parts) > 1, seen=seen,
                           at=None if (m.get("file"), m.get("line")) == home else m.get("where"))
              for m in parts]
    blocks = [b for b in blocks if b]
    if not blocks:
        return ""
    return f'<div class="flagged"><h3>What was flagged:</h3>{"".join(blocks)}</div>'


def _flagged_one(p, title=False, seen=None, at=None) -> str:
    seen = set() if seen is None else seen
    rows = [f'<li>{esc(words)} <code class="pid">{esc(pid)}</code></li>'
            for pid, words in plain.describe([x for x in p["patterns"] if x not in seen])]
    seen.update(p["patterns"])
    why = WHY.get(p.get("kind"))
    if why:
        rows.insert(0, f"<li>{esc(why)}</li>")
    if p.get("note") and p.get("kind") not in WHY_SAYS_NOTE and not p["model"]:
        rows.append(f'<li class="muted">{esc((p.get("lead") or "") + p["note"])}</li>')
    if p.get("kind") == "term.conflict":
        defs = (p.get("src") or {}).get("definitions") or []
        rows += [f'<li class="muted">Defined at {esc(d.get("file"))}:{esc(d.get("line"))}: '
                 f'“{esc(str(d.get("text", "")).strip())}”</li>' for d in defs]
    if p.get("kind") == "rep.sentence":
        locs = _rep_locations(p)
        rows.append(f'<li class="muted">The same sentence is in {len(locs)} places: '
                    + ", ".join(esc(f"{f}:{ln}") for f, ln in locs) + ".</li>")
    if not rows and not title:
        return ""
    label = S.PLAIN_STAGE[R.ORDER[p["stage"] - 1]] + (f" · {at}" if at else "")
    head = f'<h4>{esc(p["title"])} <span class="muted">({esc(label)})</span></h4>' if title else ""
    return f'{head}<ul>{"".join(rows)}</ul>'


def _sure(p):
    """How sure the model was, 0 to 1, when the read carries a number."""
    src = p.get("src") or {}
    if p.get("kind") == "sweep" and src.get("p_any") is not None:
        return src["p_any"]
    if p.get("kind") == "label":
        return R.p_do(src)
    return None


def _model_said(p) -> str:
    """Top of a model-read card (owner, 2026-10-13): what the model said comes first, then how
    far to trust it, in plain words; the stage number means nothing to a reader."""
    said = ((p.get("lead") or "") + (p.get("note") or "")).rstrip(". ")
    sure = _sure(p)
    score = f", with a <b>{sure:.2f}</b> score" if sure is not None else ""
    note = esc(MODEL_NOTE)
    pin, add = p.get("pin"), ""
    if pin and pin.get("verified") and pin.get("pin_line") is not None:
        span = (f"Line {pin['pin_line']}" if pin.get("pin_end") in (None, pin["pin_line"])
                else f"Lines {pin['pin_line']}-{pin['pin_end']}")
        also = "".join(f'<li>line {esc(a["line"])}: “{esc(a["quote"])}”</li>' for a in pin.get("also") or [])
        add = (f'<h3>Where in the passage:</h3><p>{span}: “{esc(pin["quote"])}”</p>'
               f'<h3>In plain words:</h3><p>{esc(pin.get("plain"))}</p>'
               + (f'<p class="muted">Also close:</p><ul class="muted">{also}</ul>' if also else ""))
        note = esc(PIN_NOTE + MODEL_NOTE[len("This is one model's reading, not a pattern match."):])
    elif pin and pin.get("verified"):
        add = (f'<h3>Second read:</h3><p>{esc(pin.get("plain"))}</p>'
               '<p class="muted">The second model found no line that does this. The place stays '
               'listed; you are still the check.</p>')
    elif pin:
        add = ('<p class="muted">A second model was asked which line does this, but its quote was '
               'not found in the file, so its answer is not shown.</p>')
    return (f'<div class="said"><h3>What the model said:</h3><p>{esc(said)}{score}.</p>{add}'
            f'<p class="muted">{note}</p></div>')


def _card(p, k, n, lines, secret, text_href) -> str:
    parts = p.get("parts") or [p]
    stages = list(dict.fromkeys(m["stage"] for m in parts if not m["model"])) or [p["stage"]]
    tag = "".join(f'<span class="tag">{esc(S.PLAIN_STAGE[R.ORDER[st - 1]])}</span>' for st in stages)
    reads = [m for m in parts if m["model"]]
    model = '<span class="tag model">Model read · experimental</span>' if reads else ""
    others = len(parts) - 1
    more = ""
    if p.get("kind") == "rep.sentence":
        more = f' <span class="more">in {R.n(len(_rep_locations(p)), "place")}</span>'
    elif others:
        more = f' <span class="more">and {R.n(others, "more finding")} on this line</span>'
    marks = "".join(f'<button type="button" class="mark" data-mark="{key}" aria-pressed="false">'
                    f'<b>{i}</b> {esc(name)}<span class="what">{esc(what)}</span></button>'
                    for i, (key, name, what) in enumerate(MARKS, 1))
    plain_where = f'<div class="where">{esc(p["where"])}</div>'
    return (f'<article class="place" id="p-{p["id"]}" data-id="{p["id"]}" data-n="{k}" '
            f'data-stage="{p["stage"]}" data-title="{esc(p["title"])}" data-where="{esc(p["where"])}">'
            f'<div class="place-h">{tag}{model}'
            f'<span class="num">Place {k} of {n}</span></div>'
            f'<h2>{esc(p["title"])}{more}</h2>'
            f'{_links(p, text_href) or plain_where}'
            f'{"".join(_model_said(m) for m in reads)}'
            f'{_flagged(p)}{context_html(p, lines, secret)}'  # what was flagged above the text (owner, 2026-10-13)
            f'<div class="marks" role="group" aria-label="Your mark">{marks}</div>'
            f'<label class="note-l">Note (optional)<textarea class="note" rows="2"></textarea></label>'
            f'</article>')


def saved_marks(data, ids) -> tuple[dict, int]:
    """Marks from a marks.json the reader saved: {place id: {mark, note}} for places on this
    page, and how many saved marks match no place here."""
    out, stray = {}, 0
    rows = data.get("marks") if isinstance(data, dict) else None
    for m in rows if isinstance(rows, list) else []:
        if not isinstance(m, dict):
            continue
        mark = m.get("mark") if m.get("mark") in MARK_KEYS else None
        note = m.get("note") if isinstance(m.get("note"), str) else ""
        if not mark and not note:
            continue
        if m.get("id") not in ids:
            stray += 1
            continue
        out[m["id"]] = {"mark": mark, "note": note}
    return out, stray


def load_marks(path) -> tuple[dict | None, str | None]:
    """A marks.json the reader saved in the run folder: (parsed, None), (None, why it could not
    be read), or (None, None) when there is none."""
    p = Path(path)
    if not p.is_file():
        return None, None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "it is not valid JSON"
    if not isinstance(data, dict) or not isinstance(data.get("marks"), list):
        return None, "it has no list of marks"
    return data, None


def render_page(meta, r, text_dir=None, text_href=None, marks=None, marks_error=None) -> str:
    """The whole page. `text_dir`: the run's normalized/text folder; `text_href`: the same
    folder relative to the page; `marks`: a parsed marks.json from the run folder, or None;
    `marks_error`: why a marks.json there could not be read."""
    ps = places(r)
    pin = (R.fnd(r, "01-inventory", "inv.pin") or [{}])[0]
    source = meta.get("source") or pin.get("source") or ""
    secret = _secret_files(r)
    cache = {}
    cards = []
    for k, p in enumerate(ps, 1):
        if p.get("file") not in cache:
            cache[p.get("file")] = read_lines(text_dir, p.get("file"))
        cards.append(_card(p, k, len(ps), cache[p.get("file")], p.get("file") in secret,
                           text_href))
    n_det = sum(1 for p in ps if not p["model"])
    n_mod = len(ps) - n_det
    lede = (f"Walkdown flagged {R.n(n_det, 'place')} in this repository"
            + (f", and a model read {n_mod} more (experimental)" if n_mod else "") + ".")
    saved, stray = saved_marks(marks, {p["id"] for p in ps}) if marks is not None else ({}, 0)
    loaded = ""
    if marks_error:
        loaded = f'<p class="warn">{esc(MARKS_FILE)} in the run folder could not be read: {esc(marks_error)}</p>'
    elif marks is not None:
        loaded = (f'<p class="hint">Marks loaded from {esc(MARKS_FILE)} in the run folder: '
                  f'{len(saved)}' + (f"; {stray} saved marks match no place on this page" if stray else "")
                  + ".</p>")
    index = "".join(f'<li><a href="#p-{p["id"]}" data-go="{k - 1}"><span class="chip" data-for="{p["id"]}">'
                    f'</span>{k}. {esc(p["title"])} <code>{esc(p["where"])}</code></a></li>'
                    for k, p in enumerate(ps, 1))
    payload = json.dumps(saved, ensure_ascii=True).replace("<", "\\u003c")
    legend = "".join(f"<li><b>{esc(name)}</b>: {esc(what)}</li>" for _, name, what in MARKS)
    empty = ('<p class="none">Nothing to check: no location met the rules. Each stage\'s result is in '
             '<a href="summary.html">the summary</a>.</p>') if not ps else ""
    return PAGE.format(
        title=esc(f"Walkdown review: {meta['repo']}"), repo=esc(meta["repo"]), source=esc(source),
        hash=esc(f"{meta.get('hash_kind', '?')} {str(meta.get('hash', ''))[:12]}"), run=esc(meta["run"]),
        lede=esc(lede), legend=legend, loaded=loaded, index=index, n=len(ps), cards="".join(cards),
        empty=empty, saved=payload, notwhat=esc(R.NOT_WHAT),
        meta_repo=esc(meta["repo"]), meta_run=esc(meta["run"]), meta_hash=esc(str(meta.get("hash", ""))),
        hidden="" if ps else " hidden")


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400&display=swap">
<style>
/* Same tokens as summary.html. One place at a time when the script runs; every place in a list
   when it does not (and when printed). */
:root {{
  --paper: #f5f7f8; --sheet: #ffffff; --ink: #17222e; --muted: #5a6875; --rule: #d8dee4;
  --accent: #1d6a86; --flag: #9a5b00; --flag-bg: #fdf3e4; --quote-bg: #eef2f5; --hit: #ffe7a8;
  --c-concerned: #a3361f; --c-not-concerned: #2f6f3e; --c-not-sure: #6a5a8c;
  --display: "Archivo", "Arial Narrow", Arial, sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", Consolas, "Courier New", monospace;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833; --hit: #5a4714;
  --c-concerned: #f08a70; --c-not-concerned: #7cc98d; --c-not-sure: #b9a8e0; color-scheme: dark; }} }}
:root[data-theme="dark"] {{
  --paper: #0f151b; --sheet: #16202a; --ink: #e3e9ee; --muted: #93a2b0; --rule: #2a3744;
  --accent: #6fb7d3; --flag: #f0b45c; --flag-bg: #2d2415; --quote-bg: #1c2833; --hit: #5a4714;
  --c-concerned: #f08a70; --c-not-concerned: #7cc98d; --c-not-sure: #b9a8e0; color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--paper); color: var(--ink); font: 17px/1.55 var(--body); }}
.wrap {{ max-width: 58rem; margin: 0 auto; padding-inline: 16px; padding-block: 2rem 4rem; display: grid; gap: 1.4rem; }}
header.card, .place, .done, .bar-wrap {{ background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; }}
header.card {{ padding: 1.5rem 1.6rem 1.2rem; }}
.eyebrow {{ font: 600 .78rem/1 var(--body); letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }}
.top {{ display: flex; gap: .75rem; justify-content: space-between; align-items: flex-start; }}
.top .eyebrow {{ min-width: 0; line-height: 1.3; padding-top: .3rem; }}
.pagelink {{ font: 600 .88rem/1.2 var(--body); color: var(--accent); text-decoration: none; border: 1px solid var(--rule); border-radius: 999px; padding: .35rem .75rem; white-space: nowrap; flex-shrink: 0; }}
.pagelink:hover, .pagelink:focus-visible {{ border-color: var(--accent); }}
h1 {{ font: 700 clamp(1.8rem, 4vw, 2.4rem)/1.1 var(--display); margin: .5rem 0 .6rem; text-wrap: balance; }}
.meta {{ font: .82rem/1.5 var(--mono); color: var(--muted); display: flex; flex-wrap: wrap; gap: .3rem 1.2rem; overflow-wrap: anywhere; }}
.lede {{ margin: .9rem 0 .4rem; max-width: 68ch; }}
.legend {{ margin: .4rem 0 0; padding-left: 1.2rem; color: var(--muted); font-size: .95rem; }}
.hint, .muted {{ color: var(--muted); font-size: .9rem; }}
.warn {{ color: var(--flag); font-size: .9rem; }}
.bar-wrap {{ padding: .7rem 1rem; display: grid; gap: .5rem; scroll-margin-top: .5rem; }}
@media (min-width: 641px) {{ .bar-wrap {{ position: sticky; top: 0; z-index: 2; box-shadow: 0 2px 6px rgba(0,0,0,.06); }} }}
@media (hover: none) {{ .keys {{ display: none; }} }}
.bar-top {{ display: flex; flex-wrap: wrap; gap: .5rem 1rem; align-items: center; justify-content: space-between; }}
.prog {{ font-variant-numeric: tabular-nums; font-weight: 600; }}
.bar {{ height: 6px; background: var(--rule); border-radius: 3px; overflow: hidden; }}
.bar > div {{ height: 100%; width: 0; background: var(--accent); }}
.nav {{ display: flex; flex-wrap: wrap; gap: .4rem; }}
button, .file-l {{ font: 600 .92rem/1 var(--body); padding: .55rem .8rem; border-radius: 5px; border: 1px solid var(--rule); background: var(--sheet); color: var(--ink); cursor: pointer; }}
button:hover, .file-l:hover {{ border-color: var(--accent); }}
button:focus-visible, a:focus-visible, textarea:focus-visible, summary:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
details.index {{ margin-top: .8rem; }}
details.index summary {{ cursor: pointer; color: var(--accent); font-size: .92rem; }}
details.index ol {{ list-style: none; margin: .5rem 0 0; padding: 0; max-height: 18rem; overflow: auto; }}
details.index li a {{ display: block; padding: .25rem .2rem; color: var(--ink); text-decoration: none; font-size: .9rem; overflow-wrap: anywhere; }}
details.index li a:hover {{ background: var(--quote-bg); }}
details.index code {{ font-size: .75rem; color: var(--muted); }}
.chip {{ display: inline-block; width: .75rem; height: .75rem; border-radius: 50%; border: 1.5px solid var(--muted); margin-right: .45rem; vertical-align: -1px; }}
.chip.concerned {{ background: var(--c-concerned); border-color: var(--c-concerned); }}
.chip.not-concerned {{ background: var(--c-not-concerned); border-color: var(--c-not-concerned); }}
.chip.not-sure {{ background: var(--c-not-sure); border-color: var(--c-not-sure); }}
.places {{ display: grid; gap: 1rem; }}
.place {{ padding: 1.1rem 1.2rem 1.2rem; border-left: 4px solid var(--flag); min-width: 0; scroll-margin-top: 7rem; }}
.js.one .place:not(.current) {{ display: none; }}
.place-h {{ display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }}
.tag {{ font: 600 .72rem/1 var(--body); letter-spacing: .08em; text-transform: uppercase; color: var(--flag); background: var(--flag-bg); padding: .3rem .5rem; border-radius: 3px; }}
.tag.model {{ color: var(--accent); background: var(--quote-bg); }}
.num {{ margin-left: auto; color: var(--muted); font-size: .85rem; font-variant-numeric: tabular-nums; }}
.place h2 {{ font: 600 1.15rem/1.3 var(--body); margin: .6rem 0 .2rem; }}
.where {{ font: .82rem/1.5 var(--mono); color: var(--muted); overflow-wrap: anywhere; }}
.where a {{ color: var(--accent); }}
pre.ctx {{ margin: .7rem 0 0; padding: .6rem 0; background: var(--quote-bg); border-radius: 4px; font: .8rem/1.6 var(--mono); white-space: pre-wrap; }}
.ln {{ display: grid; grid-template-columns: max-content minmax(0, 1fr); padding: 0 .8rem 0 0; }}
.ln .tx {{ overflow-wrap: anywhere; }}
.ln.t {{ background: var(--flag-bg); box-shadow: inset 3px 0 0 var(--flag); }}
.ln .n {{ min-width: 3.2em; padding: 0 .8rem 0 .6rem; text-align: right; color: var(--muted); user-select: none; }}
mark {{ background: var(--hit); color: inherit; border-radius: 2px; padding: 0 1px; }}
.inv {{ font-size: .7rem; border: 1px solid var(--flag); color: var(--flag); border-radius: 3px; padding: 0 2px; margin: 0 1px; }}
.cut {{ color: var(--muted); font-style: italic; }}
.flagged h3, .said h3 {{ font: 600 .95rem/1.3 var(--body); margin: .9rem 0 .3rem; }}
.said p {{ margin: .2rem 0; max-width: 72ch; }}
.said h3, .flagged h3 {{ text-decoration: underline; text-underline-offset: .2em; }}
.flagged ul {{ margin: 0; padding-left: 1.2rem; display: grid; gap: .3rem; max-width: 72ch; }}
.flagged h4 {{ font: 600 .92rem/1.3 var(--body); margin: .6rem 0 .25rem; }}
.place h2 .more {{ font: 400 .9rem var(--body); color: var(--muted); }}
.pid {{ font: .72rem var(--mono); color: var(--muted); }}
.marks {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: .5rem; margin-top: 1rem; }}
.mark {{ text-align: left; font-weight: 600; line-height: 1.3; padding: .6rem .7rem; }}
.mark b {{ display: inline-block; min-width: 1.1em; color: var(--muted); }}
.mark .what {{ display: block; font-weight: 400; font-size: .82rem; color: var(--muted); margin-top: .15rem; }}
.mark[aria-pressed="true"] {{ color: #fff; }}
.mark[aria-pressed="true"] .what, .mark[aria-pressed="true"] b {{ color: inherit; opacity: .9; }}
.mark[data-mark="concerned"][aria-pressed="true"] {{ background: var(--c-concerned); border-color: var(--c-concerned); }}
.mark[data-mark="not-concerned"][aria-pressed="true"] {{ background: var(--c-not-concerned); border-color: var(--c-not-concerned); }}
.mark[data-mark="not-sure"][aria-pressed="true"] {{ background: var(--c-not-sure); border-color: var(--c-not-sure); }}
:root[data-theme="dark"] .mark[aria-pressed="true"] {{ color: #0f151b; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) .mark[aria-pressed="true"] {{ color: #0f151b; }} }}
.note-l {{ display: block; margin-top: .7rem; font-size: .85rem; color: var(--muted); }}
textarea {{ display: block; width: 100%; margin-top: .25rem; font: .95rem/1.4 var(--body); padding: .5rem; border-radius: 5px; border: 1px solid var(--rule); background: var(--sheet); color: var(--ink); }}
.no-js .marks, .no-js .note-l, .no-js .bar-wrap, .no-js .done {{ display: none; }}
.done {{ padding: 1.1rem 1.2rem; }}
.done h2 {{ font: 700 1.2rem/1.2 var(--display); margin: 0 0 .5rem; }}
.counts {{ display: flex; flex-wrap: wrap; gap: .4rem 1.2rem; margin: 0 0 .8rem; padding: 0; list-style: none; }}
.done .nav {{ margin-top: .6rem; align-items: center; }}
.file-l input {{ display: none; }}
#out {{ font: .75rem/1.4 var(--mono); min-height: 6rem; margin-top: .7rem; }}
.none {{ background: var(--sheet); border: 1px solid var(--rule); border-radius: 6px; padding: 1rem 1.2rem; }}
footer {{ border-top: 2px solid var(--ink); padding-top: 1rem; color: var(--muted); max-width: 70ch; font-size: .92rem; }}
@media (max-width: 640px) {{ .marks {{ grid-template-columns: 1fr; }} header.card {{ padding: 1.2rem; }} .num {{ margin-left: 0; width: 100%; }} }}
@media print {{ .bar-wrap, .marks, .note-l, .done {{ display: none; }} .js.one .place:not(.current) {{ display: block; }} }}
</style>
</head>
<body class="no-js">
<main class="wrap" data-repo="{meta_repo}" data-run="{meta_run}" data-hash="{meta_hash}" data-source="{source}">
  <header class="card">
    <div class="top"><div class="eyebrow">Walkdown review</div><a class="pagelink" href="summary.html">← Summary</a></div>
    <h1>{repo}</h1>
    <div class="meta"><span>{source}</span><span>{hash}</span><span>run {run}</span></div>
    <p class="lede">{lede} Walk through them one at a time and mark each the way you read it. Walkdown makes no call on any of them; the marks are yours.</p>
    <ul class="legend">{legend}</ul>
    {loaded}
    <details class="index"{hidden}><summary>All {n} places</summary><ol>{index}</ol></details>
    <p class="hint keys"{hidden}>Keys: 1 Concerned, 2 Not concerned, 3 Not sure (press again to clear), arrows move, N next unmarked.</p>
    <p class="hint"{hidden}>Marks are kept in this browser as you go. To keep them with the report, download them at the end.</p>
    <noscript><p class="hint">Marking needs JavaScript. Every place is listed below.</p></noscript>
  </header>
  {empty}
  <section class="bar-wrap"{hidden} aria-label="Progress">
    <div class="bar-top"><span class="prog" id="prog"></span>
      <div class="nav"><button type="button" id="prev">Back</button><button type="button" id="next">Next</button>
      <button type="button" id="nextun">Next unmarked</button><button type="button" id="mode">Show all</button></div></div>
    <div class="bar"><div id="fill"></div></div>
  </section>
  <div class="places" id="places">{cards}</div>
  <section class="done"{hidden} aria-label="When you are done">
    <h2>When you are done</h2>
    <ul class="counts" id="counts"></ul>
    <p class="hint">Download your marks and save the file as <code>marks.json</code> in this run folder, next to this page. Walkdown reads it back when it re-renders the report, so the marks come back with the page on any computer. If the download is blocked, copy the text below into that file.</p>
    <div class="nav"><button type="button" id="dl">Download marks.json</button><button type="button" id="cp">Copy marks</button>
      <label class="file-l">Load a marks file<input type="file" id="load" accept=".json,application/json"></label>
      <span class="hint" id="msg" role="status"></span></div>
    <textarea id="out" readonly aria-label="Marks as JSON"></textarea>
  </section>
  <footer><p>{notwhat}</p><p>The summary is <a href="summary.html">summary.html</a>; every finding, with file and line, is in <code>full.md</code>.</p></footer>
</main>
<script type="application/json" id="saved">{saved}</script>
<script>
(function () {{
  "use strict";
  var body = document.body, main = document.querySelector("main");
  var cards = Array.prototype.slice.call(document.querySelectorAll(".place"));
  if (!cards.length) return;
  body.classList.remove("no-js"); body.classList.add("js", "one");
  var KEYS = ["concerned", "not-concerned", "not-sure"];
  var NAMES = {{"concerned": "Concerned", "not-concerned": "Not concerned", "not-sure": "Not sure"}};
  var STORE = "walkdown-review:" + main.dataset.repo + ":" + main.dataset.run;
  var $ = function (id) {{ return document.getElementById(id); }};
  var marks = {{}};
  try {{ marks = JSON.parse($("saved").textContent) || {{}}; }} catch (e) {{ marks = {{}}; }}
  try {{ var mine = JSON.parse(localStorage.getItem(STORE) || "{{}}");
    Object.keys(mine).forEach(function (k) {{ marks[k] = mine[k]; }}); }} catch (e) {{}}
  var i = 0;
  function get(id) {{ return marks[id] || {{mark: null, note: ""}}; }}
  function save() {{ try {{ localStorage.setItem(STORE, JSON.stringify(marks)); }} catch (e) {{}} out(); }}
  function isMarked(id) {{ return !!get(id).mark; }}
  function paint() {{
    var done = 0, c = {{"concerned": 0, "not-concerned": 0, "not-sure": 0}};
    cards.forEach(function (el, k) {{
      var m = get(el.dataset.id);
      if (m.mark) {{ done++; c[m.mark]++; }}
      el.classList.toggle("current", k === i);
      el.querySelectorAll(".mark").forEach(function (b) {{ b.setAttribute("aria-pressed", String(b.dataset.mark === m.mark)); }});
      var ta = el.querySelector(".note"); if (document.activeElement !== ta) ta.value = m.note || "";
      var chip = document.querySelector('.chip[data-for="' + el.dataset.id + '"]');
      if (chip) chip.className = "chip" + (m.mark ? " " + m.mark : "");
    }});
    $("prog").textContent = (body.classList.contains("one") ? "Place " + (i + 1) + " of " + cards.length + " · " : cards.length + " places · ") + done + " marked";
    $("fill").style.width = (100 * done / cards.length) + "%";
    $("counts").innerHTML = "";
    KEYS.forEach(function (k) {{ var li = document.createElement("li"); li.textContent = NAMES[k] + ": " + c[k]; $("counts").appendChild(li); }});
    var li = document.createElement("li"); li.textContent = "Not marked: " + (cards.length - done); $("counts").appendChild(li);
  }}
  function out() {{
    var rows = [];
    cards.forEach(function (el) {{
      var m = get(el.dataset.id);
      if (!m.mark && !m.note) return;
      rows.push({{id: el.dataset.id, place: +el.dataset.n, section: +el.dataset.stage, headline: el.dataset.title,
                 where: el.dataset.where, mark: m.mark, note: m.note || ""}});
    }});
    $("out").value = JSON.stringify({{walkdown_review: 1, repo: main.dataset.repo, run: main.dataset.run,
      pinned: main.dataset.hash, saved: new Date().toISOString().slice(0, 10), places: cards.length, marks: rows}}, null, 1);
  }}
  function set(id, patch) {{ var m = get(id); marks[id] = {{mark: "mark" in patch ? patch.mark : m.mark, note: "note" in patch ? patch.note : m.note}}; save(); paint(); }}
  function pick(key) {{
    var id = cards[i].dataset.id, cur = get(id).mark;
    set(id, {{mark: cur === key ? null : key}});
    if (cur !== key && body.classList.contains("one")) setTimeout(function () {{ go(1); }}, 180);
  }}
  function go(d) {{ i = Math.max(0, Math.min(cards.length - 1, i + d)); paint(); show(); }}
  function show() {{
    if (body.classList.contains("one")) document.querySelector(".bar-wrap").scrollIntoView({{block: "start"}});
    else cards[i].scrollIntoView({{block: "start"}});
    try {{ history.replaceState(null, "", "#p-" + cards[i].dataset.id); }} catch (e) {{}}
  }}
  function nextUn() {{ for (var k = 1; k <= cards.length; k++) {{ var j = (i + k) % cards.length;
    if (!isMarked(cards[j].dataset.id)) {{ i = j; paint(); show(); return; }} }} }}
  cards.forEach(function (el, k) {{
    el.querySelectorAll(".mark").forEach(function (b) {{ b.addEventListener("click", function () {{ i = k; pick(b.dataset.mark); }}); }});
    el.querySelector(".note").addEventListener("input", function (e) {{ set(el.dataset.id, {{note: e.target.value}}); }});
    el.addEventListener("focusin", function () {{ if (!body.classList.contains("one") && i !== k) {{ i = k; paint(); }} }});
  }});
  document.querySelectorAll("[data-go]").forEach(function (a) {{ a.addEventListener("click", function (e) {{
    e.preventDefault(); i = +a.dataset.go; paint(); show(); }}); }});
  $("prev").onclick = function () {{ go(-1); }}; $("next").onclick = function () {{ go(1); }}; $("nextun").onclick = nextUn;
  $("mode").onclick = function () {{ var one = body.classList.toggle("one");
    $("mode").textContent = one ? "Show all" : "One at a time"; paint(); show(); }};
  document.addEventListener("keydown", function (e) {{
    var t = e.target.tagName; if (t === "TEXTAREA" || t === "INPUT" || e.ctrlKey || e.metaKey || e.altKey) return;
    var n = "123".indexOf(e.key);
    if (n >= 0) pick(KEYS[n]); else if (e.key === "ArrowRight") go(1); else if (e.key === "ArrowLeft") go(-1);
    else if (e.key === "n" || e.key === "N") nextUn();
  }});
  $("dl").onclick = function () {{ out(); var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([$("out").value], {{type: "application/json"}}));
    a.download = "marks.json"; a.click(); $("msg").textContent = "Downloaded. Save it in this run folder as marks.json."; }};
  $("cp").onclick = function () {{ out(); navigator.clipboard.writeText($("out").value).then(
    function () {{ $("msg").textContent = "Copied."; }}, function () {{ $("out").select(); $("msg").textContent = "Select and copy the text below."; }}); }};
  $("load").onchange = function (e) {{ var f = e.target.files[0]; if (!f) return; var rd = new FileReader();
    rd.onload = function () {{ var n = 0, stray = 0, ids = {{}};
      cards.forEach(function (el) {{ ids[el.dataset.id] = 1; }});
      try {{ (JSON.parse(rd.result).marks || []).forEach(function (m) {{
        if (!m || !ids[m.id]) {{ stray++; return; }}
        marks[m.id] = {{mark: KEYS.indexOf(m.mark) >= 0 ? m.mark : null, note: typeof m.note === "string" ? m.note : ""}}; n++; }});
        save(); paint(); $("msg").textContent = "Loaded " + n + " marks" + (stray ? "; " + stray + " match no place here." : ".");
      }} catch (err) {{ $("msg").textContent = "That file is not a marks file."; }} }};
    rd.readAsText(f); }};
  var h = location.hash.replace("#p-", ""), at = cards.findIndex(function (el) {{ return el.dataset.id === h; }});
  if (at >= 0) i = at; else {{ var un = cards.findIndex(function (el) {{ return !isMarked(el.dataset.id); }}); i = un < 0 ? 0 : un; }}
  paint(); out();
}})();
</script>
</body>
</html>
"""
