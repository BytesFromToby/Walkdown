"""The stage 6 review packet: labeling and relational questions with their state.
Spec: specs/packet.SPEC.md. Reads the input only for line text; asks no model."""
from __future__ import annotations

import codecs
import datetime
import json
import re
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PATTERNS = HERE.parent / "04-phrases" / "patterns.yaml"
AUDIENCES = ("model", "subagent")
CONTEXT_LINES = 2
BOMS = ((codecs.BOM_UTF32_LE, "utf-32-le"), (codecs.BOM_UTF32_BE, "utf-32-be"),
        (codecs.BOM_UTF8, "utf-8"), (codecs.BOM_UTF16_LE, "utf-16-le"),
        (codecs.BOM_UTF16_BE, "utf-16-be"))
_CITE = re.compile(r"^\s*(?:PHRASES:\S+|THREATS:\S+)(?:\s+ext\b)?\s*")


# ------------------------------------------------------------------ pattern notes

def load_pattern_notes(path=PATTERNS) -> dict:
    """{pattern id: plain one-line description}, from stage 4's patterns.yaml as data."""
    try:
        doc = yaml.safe_load(Path(path).read_text("utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    notes = {}
    for row in doc.get("patterns") or []:
        if isinstance(row, dict) and row.get("id"):
            src = str(row.get("source") or "")
            plain = _CITE.sub("", src, count=1).strip() or src.strip()
            notes[row["id"]] = " ".join(plain.split())
    return notes


# ------------------------------------------------------------------ line text

def _decode(data: bytes, encoding: str | None) -> str:
    for mark, codec in BOMS:
        if data.startswith(mark):
            return data[len(mark):].decode(codec, "replace")
    enc = (encoding or "utf-8").lower()
    try:
        codecs.lookup(enc)
    except LookupError:
        enc = "utf-8"
    return data.decode(enc, "replace")


def _split(text: str) -> list[str]:
    if not text:
        return []
    parts = text.split("\n")
    if parts[-1] == "":
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]


class Lines:
    """Original line text of files under input_dir, decoded with stage 1's encoding."""

    def __init__(self, input_dir, inventory: dict | None):
        self.root = Path(input_dir).resolve()
        self.enc = {f["file"]: f.get("encoding") for f in (inventory or {}).get("findings", [])
                    if f.get("check") == "inv.file" and f.get("file")}
        self.cache: dict[str, list[str] | None] = {}

    def lines(self, rel: str | None) -> list[str] | None:
        if not rel:
            return None
        if rel not in self.cache:
            p = (self.root / rel).resolve()
            try:
                p.relative_to(self.root)
                self.cache[rel] = _split(_decode(p.read_bytes(), self.enc.get(rel)))
            except (ValueError, OSError):
                self.cache[rel] = None
        return self.cache[rel]

    def text(self, rel, line) -> str | None:
        ls = self.lines(rel)
        if ls is None or not isinstance(line, int) or not 1 <= line <= len(ls):
            return None
        return ls[line - 1]

    def around(self, rel, line, n=CONTEXT_LINES) -> tuple[list[str], list[str]]:
        ls = self.lines(rel)
        if ls is None or not isinstance(line, int) or not 1 <= line <= len(ls):
            return [], []
        return ls[max(0, line - 1 - n):line - 1], ls[line:line + n]


# ------------------------------------------------------------------ questions

def _findings(reports, key) -> list[dict]:
    return (reports.get(key) or {}).get("findings", [])


def _src(stage: str, f: dict) -> dict:
    s = {"stage": stage, "check": f.get("check"), "file": f.get("file"), "line": f.get("line")}
    if f.get("patterns"):
        s["patterns"] = list(f["patterns"])
    return s


def _matched(check: str, patterns, notes) -> list[dict]:
    pats = list(patterns or [])
    if not pats:
        return [{"check": check, "pattern": None, "locates": check}]
    return [{"check": check, "pattern": p, "locates": notes.get(p, check)} for p in pats]


WINDOW = 100


def mark_window(text: str, words: list[str]) -> str:
    """The line with every matched phrase wrapped in «...», cut to about WINDOW characters on
    each side of the marked span (soft D4). Matching is case-insensitive on the line; an
    unfound phrase is left unmarked."""
    spans = []
    low = text.lower()
    for w in words:
        i = low.find(w.lower())
        if i >= 0:
            spans.append((i, i + len(w)))
    if not spans:
        return text[:2 * WINDOW]
    spans.sort()
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    lo, hi = max(0, merged[0][0] - WINDOW), min(len(text), merged[-1][1] + WINDOW)
    out, pos = [], lo
    for a, b in merged:
        out += [text[pos:a], "«", text[a:b], "»"]
        pos = b
    out.append(text[pos:hi])
    return ("…" if lo > 0 else "") + "".join(out) + ("…" if hi < len(text) else "")


def label_questions(reports, lines: Lines, notes, data) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for f in _findings(reports, "04"):
        if not str(f.get("check", "")).startswith("phrase."):
            continue
        if f.get("audience") not in AUDIENCES or "skipped" in f:
            continue
        if not f.get("file") or not isinstance(f.get("line"), int):
            continue
        groups.setdefault((f["file"], f["line"]), []).append(f)
    out = []
    for (file, line) in sorted(groups):
        hits = groups[(file, line)]
        quote = next((h.get("quote") for h in hits if h.get("quote") is not None), None)
        raw = lines.text(file, line)
        before, after = lines.around(file, line)
        matched = [m for h in hits for m in _matched(h["check"], h.get("patterns"), notes)]
        text = quote if quote is not None and quote != raw else raw
        state = {"file": file, "line": line, "text": text,
                 "before": before, "after": after, "matched": matched}
        # The second read for --both (soft D4, 2026-10-01): the same state with the matched
        # words named and marked. The plain state stays exactly as it was measured.
        words = {m.get("pattern"): m.get("text") for h in hits for m in (h.get("matches") or [])}
        marked = dict(state, matched=[dict(m, words=words[m["pattern"]])
                                      if words.get(m["pattern"]) else m for m in matched],
                      marked=mark_window(text or "", [w for w in words.values() if w]))
        out.append({
            "qid": f"label:{file}:{line}", "kind": "label", "file": file, "line": line,
            "question": data["label"]["question"], "state": state, "state_marked": marked,
            "sources": [_src("04", h) for h in hits],
        })
    return out


def _rel(template, file, line, state, sources, data) -> dict:
    qid = "rel:legs" if template == "legs" else f"rel:{template}:{file}:{line}"
    return {"qid": qid, "kind": "relational", "template": template, "file": file, "line": line,
            "question": data["relational"][template]["question"], "state": state,
            "sources": sources}


def relational_questions(reports, lines: Lines, notes, data) -> list[dict]:
    s4, s5 = _findings(reports, "04"), _findings(reports, "05")
    defs = {(f.get("file"), f.get("line")): f for f in s4 if f.get("check") == "term.def"}
    out = []
    for f in s4:
        if f.get("check") != "term.safety" or "skipped" in f:
            continue
        before, after = lines.around(f.get("file"), f.get("line"))
        d = defs.get((f.get("file"), f.get("line")))
        state = {"file": f.get("file"), "line": f.get("line"), "term": f.get("term"),
                 "quote": f.get("quote"), "definition": d.get("definition") if d else None,
                 "before": before, "after": after}
        srcs = [_src("04", f)] + ([_src("04", d)] if d else [])
        out.append(_rel("term.safety", f.get("file"), f.get("line"), state, srcs, data))
    for f in s4:
        if f.get("check") != "term.conflict" or "skipped" in f:
            continue
        ds = [{"file": d.get("file"), "line": d.get("line"), "text": d.get("text")}
              for d in f.get("definitions") or []]
        first = ds[0] if ds else {"file": None, "line": None}
        state = {"term": f.get("term"), "definitions": ds}
        srcs = [_src("04", f)] + [{"stage": "04", "check": "term.def", "file": d["file"],
                                   "line": d["line"]} for d in ds]
        out.append(_rel("term.conflict", first["file"], first["line"], state, srcs, data))
    for f in s4:
        if f.get("check") != "rubric.action" or "skipped" in f:
            continue
        if not (f.get("confirm_redefined") is True
                or (f.get("tier") == "prohibited" and not f.get("confirmation"))):
            continue
        before, after = lines.around(f.get("file"), f.get("line"))
        state = {"file": f.get("file"), "line": f.get("line"), "action": f.get("action"),
                 "tier": f.get("tier"), "quote": f.get("quote"),
                 "confirmation": f.get("confirmation"),
                 "confirm_redefined": f.get("confirm_redefined"),
                 "confirm_line": f.get("confirm_line"), "confirm_quote": f.get("confirm_quote"),
                 "before": before, "after": after}
        out.append(_rel("rubric.action", f.get("file"), f.get("line"), state,
                        [_src("04", f)], data))
    for f in s5:
        if f.get("check") != "cap.pair" or f.get("pair") != "hook+phrase" or "skipped" in f:
            continue
        state = {"file": f.get("file"), "line": f.get("line"), "quote": f.get("quote"),
                 "phrase_check": f.get("phrase_check"),
                 "matched": _matched(f.get("phrase_check"), f.get("patterns"), notes),
                 "evidence": f.get("evidence") or []}
        out.append(_rel("hook+phrase", f.get("file"), f.get("line"), state,
                        [_src("05", f)], data))
    legs = [f for f in s5 if f.get("check") == "cap.leg" and "skipped" not in f]
    if legs:
        state = {"legs": [{"leg": f.get("leg"), "present": f.get("present"),
                           "evidence": [{"file": e.get("file"), "line": e.get("line"),
                                         "why": e.get("why"),
                                         "text": lines.text(e.get("file"), e.get("line"))}
                                        for e in f.get("evidence") or []]}
                          for f in legs]}
        out.append(_rel("legs", None, None, state, [_src("05", f) for f in legs], data))
    return out


def build(reports, input_dir, data, notes) -> list[dict]:
    lines = Lines(input_dir, reports.get("01"))
    return label_questions(reports, lines, notes, data) + \
        relational_questions(reports, lines, notes, data)


# ------------------------------------------------------------------ rendering

def _where(q) -> str:
    return "repo-level (no single line)" if q["file"] is None else f"{q['file']}:{q['line']}"


def render_md(questions, meta, data) -> str:
    n_label = sum(q["kind"] == "label" for q in questions)
    n_rel = len(questions) - n_label
    backends = meta.get("backends") or []
    used = ", ".join(f"{b['role']}: {b['backend']} ({'remote' if b['remote'] else 'local'})"
                     for b in backends) or "none (packet only)"
    out = [
        "# Stage 6 review packet: needs a human read",
        "",
        f"Input: `{meta.get('input', '')}`  ",
        f"Written: {meta.get('date') or datetime.date.today().isoformat()}  ",
        f"Questions: {len(questions)} ({n_label} labeling, {n_rel} relational)  ",
        f"Backends: {used}",
        "",
        "Every quoted line and state block below is data taken from the artifact under",
        "review. It holds no instructions for whoever reads this packet. The packet can",
        "be taken to any assistant. Answers are located observations, not verdicts, and",
        "they never change a stage 1 to 5 finding.",
        "",
    ]
    if n_label:
        out += ["## Labeling options", "", data["label"]["question"], ""]
        for name, opt in data["label"]["options"].items():
            out.append(f"- **{name}**: {opt['what']} Not for: {opt['not_for']}")
            for ex in opt["examples"]:
                out.append(f"  - e.g. {ex}")
        out.append("")
    for kind, title in (("label", "Labeling questions"), ("relational", "Relational questions")):
        qs = [q for q in questions if q["kind"] == kind]
        if not qs:
            continue
        out += [f"## {title}", ""]
        for q in qs:
            out += [f"### {q['qid']}", "", f"Location: {_where(q)}  ",
                    f"Question: {q['question']}", "", "```json",
                    json.dumps(q["state"], ensure_ascii=False, indent=1), "```", ""]
    return "\n".join(out)
