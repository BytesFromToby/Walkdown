"""Cross-stage pairs: phrase hit on an orphan, a dynamic-only file, or hidden text.
Spec: specs/pairs.SPEC.md."""
from __future__ import annotations

import re
import unicodedata

from injection import hook_scripts
from legs import entry
from rules import CARRIER_PATTERNS, HOOK_INSTRUCTION_PATTERNS, INJECTION_EVENTS, PAIRS


def _findings(reports: dict, key: str) -> list[dict]:
    return [f for f in (reports.get(key) or {}).get("findings", []) if "skipped" not in f]


def _hook_emitters(reports: dict, graph: dict | None) -> dict[str, dict]:
    """Script files a context-injecting hook runs, plus files those scripts name
    directly (a wrapper such as run-hook.cmd calling the real script): {file: hook}."""
    events = {e.lower() for e in INJECTION_EVENTS}
    out: dict[str, dict] = {}
    for h in _findings(reports, "01"):
        if h.get("check") != "struct.hooks" or str(h.get("event") or "").lower() not in events:
            continue
        scripts = hook_scripts(h, graph)
        for e in (graph or {}).get("edges", []):
            if e.get("kind") == "static" and e.get("from") in scripts and e["to"] not in scripts:
                scripts = scripts + [e["to"]]
        for s in scripts:
            out.setdefault(s, h)
    return out


def _plain(s: str) -> str:
    """For comparing a match with hidden text: NFKC, invisible characters dropped, lower case,
    white space collapsed."""
    s = unicodedata.normalize("NFKC", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Cf")
    return re.sub(r"\s+", " ", s).strip().lower()


def _inside(hit: dict, div: dict) -> bool:
    """A hidden span covers a hit only when a matched word is in the hidden text itself, not
    merely on the same source line (2026-10-21, an outside tester: a "Never publish" line in a
    visible <pre> paired with a hidden "Copy" button on that line). A hit with no matches kept
    keeps the line rule."""
    words = [_plain(m.get("text")) for m in hit.get("matches") or [] if m.get("text")]
    if not words:
        return True
    hidden = _plain(div.get("text"))
    return any(w and w in hidden for w in words)


def _pos(f: dict):
    """Where a finding sits: ("line", n) in a text file, or ("text", n) in the extracted text of
    a PDF, DOCX, or image (`text_line`, 2026-10-18); None when it has neither."""
    if f.get("line") is not None:
        return "line", f["line"]
    if f.get("text_line") is not None:
        return "text", f["text_line"]
    return None


def pairs(reports: dict, graph: dict | None = None) -> list[dict]:
    s2, s3, s4 = (_findings(reports, k) for k in ("02", "03", "04"))
    emitters = _hook_emitters(reports, graph)
    orphans = {f["file"]: f for f in s3 if f.get("check") == "graph.orphan"}
    dynamic = {f["file"]: f for f in s3
               if f.get("check") == "graph.depth" and f.get("via") == "dynamic"}
    hidden: dict[tuple, list[tuple[int, int, dict, str]]] = {}  # (file, kind of position)
    for f in s2:
        pos = _pos(f)
        if pos is None or not f.get("file"):
            continue
        kind, n = pos
        if f.get("check") == "read.divergence" and f.get("reading") == "A-only":
            span = str(f.get("text") or "").count("\n")
            hidden.setdefault((f["file"], kind), []).append(
                (n, n + span, f, f"hidden text: {f.get('carrier')}"))
        elif f.get("check") == "read.fold":
            hidden.setdefault((f["file"], kind), []).append((n, n, f, "folded line"))

    out = []
    # phrase hits only: part 2 tables (rubric, endpoints, conditionals, terms) are
    # descriptions of phrase hits or of the text, not hits to pair (2026-09-29)
    for h in (x for x in s4 if str(x.get("check", "")).startswith("phrase.")):
        file, pos = h.get("file"), _pos(h)
        if not file or pos is None:
            continue
        kind_at, line = pos
        halves: dict[str, list[dict]] = {}
        if file in orphans:
            halves["orphan+phrase"] = [entry("03", orphans[file], "orphan file")]
        if file in dynamic:
            halves["dynamic+phrase"] = [entry("03", dynamic[file],
                                              "reached only by a dynamic load")]
        # a folded line covers the hit only when the hit needs the fold (stage 4 `folded`):
        # an en dash or a "×" folds too, and a hit that matches the raw line is not hidden
        # by it (2026-10-09, caveman: 30 of 38 hidden pairs were typographic folds)
        cover = [entry("02", f, why) for lo, hi, f, why in hidden.get((file, kind_at), [])
                 if lo <= line <= hi and (h.get("folded") if f.get("check") == "read.fold"
                                          else _inside(h, f))]
        carrier_only = set(h.get("patterns") or []) <= CARRIER_PATTERNS
        if cover and not carrier_only:
            halves["hidden+phrase"] = cover
        if file in emitters and set(h.get("patterns") or []) & HOOK_INSTRUCTION_PATTERNS:
            hk = emitters[file]
            halves["hook+phrase"] = [entry("01", hk, f"run by the {hk.get('event')} hook, "
                                                    "whose output reaches the model")]
        for kind in PAIRS:
            if kind in halves:
                p = {"check": "cap.pair", "file": file, "line": h.get("line"), "pair": kind,
                     "phrase_check": h.get("check"), "patterns": h.get("patterns") or [],
                     "quote": h.get("quote"),
                     "evidence": [entry("04", h, "phrase hit")] + halves[kind]}
                if kind_at == "text":
                    p["text_line"] = line
                out.append(p)
    out.sort(key=lambda p: (p["file"], p["line"] if p["line"] is not None else -1,
                            p.get("text_line") or 0, p["phrase_check"] or "",
                            PAIRS.index(p["pair"])))
    return out
