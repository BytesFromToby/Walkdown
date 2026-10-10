"""Cross-stage pairs: phrase hit on an orphan, a dynamic-only file, or hidden text.
Spec: specs/pairs.SPEC.md."""
from __future__ import annotations

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


def pairs(reports: dict, graph: dict | None = None) -> list[dict]:
    s2, s3, s4 = (_findings(reports, k) for k in ("02", "03", "04"))
    emitters = _hook_emitters(reports, graph)
    orphans = {f["file"]: f for f in s3 if f.get("check") == "graph.orphan"}
    dynamic = {f["file"]: f for f in s3
               if f.get("check") == "graph.depth" and f.get("via") == "dynamic"}
    hidden: dict[str, list[tuple[int, int, dict, str]]] = {}
    for f in s2:
        if f.get("line") is None or not f.get("file"):
            continue
        if f.get("check") == "read.divergence" and f.get("reading") == "A-only":
            span = str(f.get("text") or "").count("\n")
            hidden.setdefault(f["file"], []).append(
                (f["line"], f["line"] + span, f, f"hidden text: {f.get('carrier')}"))
        elif f.get("check") == "read.fold":
            hidden.setdefault(f["file"], []).append((f["line"], f["line"], f, "folded line"))

    out = []
    # phrase hits only: part 2 tables (rubric, endpoints, conditionals, terms) are
    # descriptions of phrase hits or of the text, not hits to pair (2026-09-29)
    for h in (x for x in s4 if str(x.get("check", "")).startswith("phrase.")):
        file, line = h.get("file"), h.get("line")
        if not file or line is None:
            continue
        halves: dict[str, list[dict]] = {}
        if file in orphans:
            halves["orphan+phrase"] = [entry("03", orphans[file], "orphan file")]
        if file in dynamic:
            halves["dynamic+phrase"] = [entry("03", dynamic[file],
                                              "reached only by a dynamic load")]
        # a folded line covers the hit only when the hit needs the fold (stage 4 `folded`):
        # an en dash or a "×" folds too, and a hit that matches the raw line is not hidden
        # by it (2026-10-09, caveman: 30 of 38 hidden pairs were typographic folds)
        cover = [entry("02", f, why) for lo, hi, f, why in hidden.get(file, [])
                 if lo <= line <= hi and (f.get("check") != "read.fold" or h.get("folded"))]
        carrier_only = set(h.get("patterns") or []) <= CARRIER_PATTERNS
        if cover and not carrier_only:
            halves["hidden+phrase"] = cover
        if file in emitters and set(h.get("patterns") or []) & HOOK_INSTRUCTION_PATTERNS:
            hk = emitters[file]
            halves["hook+phrase"] = [entry("01", hk, f"run by the {hk.get('event')} hook, "
                                                    "whose output reaches the model")]
        for kind in PAIRS:
            if kind in halves:
                out.append({"check": "cap.pair", "file": file, "line": line, "pair": kind,
                            "phrase_check": h.get("check"), "patterns": h.get("patterns") or [],
                            "quote": h.get("quote"),
                            "evidence": [entry("04", h, "phrase hit")] + halves[kind]})
    out.sort(key=lambda p: (p["file"], p["line"], p["phrase_check"] or "",
                            PAIRS.index(p["pair"])))
    return out
