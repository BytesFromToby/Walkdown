"""Stage 6 findings and summary from the packet and the backend results. Spec: specs/ask.SPEC.md.
Calls no backend; changes no earlier stage's findings."""
from __future__ import annotations

from collections import Counter

import chunks as chunks_mod

LABEL_FIELDS = ("qid", "backend", "model", "label", "probabilities", "confidence", "truncated")
READ_FIELDS = ("qid", "backend", "model", "answer", "capped")
# Carried only when the backend gives them: claude-cli's self-reported confidence, and
# jev --both's two separate reads (2026-10-01).
OPTIONAL_FIELDS = ("confidence_kind", "reads")


def _loc(q) -> dict:
    return {"file": q["file"], "line": q["line"]}


def _index(results) -> dict:
    return {r["qid"]: r for r in results or []}


def _answer(check, q, r, fields, missing) -> dict:
    if r is None:
        return {"check": check, **_loc(q), "qid": q["qid"], "skipped": missing}
    if "skipped" in r:
        return {"check": check, **_loc(q), "qid": q["qid"], "backend": r.get("backend"),
                "skipped": r["skipped"]}
    out = {"check": check, **_loc(q), **{k: r.get(k) for k in fields}}
    out.update({k: r[k] for k in OPTIONAL_FIELDS if k in r})
    return out


def findings(questions, primary, compare, reads) -> list[dict]:
    labels = [q for q in questions if q["kind"] == "label"]
    rels = [q for q in questions if q["kind"] == "relational"]
    out = [{"check": "soft.question", **_loc(q), "kind": q["kind"], "qid": q["qid"],
            "question": q["question"], "sources": q["sources"]} for q in questions]
    p_idx, c_idx, r_idx = _index(primary), _index(compare), _index(reads)
    for q in labels:
        if primary is None:
            out.append({"check": "soft.label", **_loc(q), "qid": q["qid"],
                        "skipped": "no labeling backend"})
        else:
            out.append(_answer("soft.label", q, p_idx.get(q["qid"]), LABEL_FIELDS,
                               "no answer returned"))
    if compare is not None:
        for q in labels:
            out.append(_answer("soft.compare", q, c_idx.get(q["qid"]), LABEL_FIELDS,
                               "no answer returned"))
    if primary is not None and compare is not None:
        for q in labels:
            a, b = p_idx.get(q["qid"]), c_idx.get(q["qid"])
            if a and b and "skipped" not in a and "skipped" not in b:
                out.append({"check": "soft.agree", **_loc(q), "qid": q["qid"],
                            "primary": a["label"], "compare": b["label"],
                            "agree": a["label"] == b["label"]})
    for q in rels:
        if reads is None:
            out.append({"check": "soft.read", **_loc(q), "qid": q["qid"],
                        "skipped": "no relational backend"})
        else:
            out.append(_answer("soft.read", q, r_idx.get(q["qid"]), READ_FIELDS,
                               "no answer returned"))
    return out


SWEEP_FIELDS = ("qid", "backend", "model", "kind", "probabilities", "p_any", "flagged")


def sweep_findings(chunks, results, s4_findings) -> list[dict]:
    """Soft D2: one soft.sweep finding per chunk, with `covered`: the stage 4 patterns
    that hit inside its lines (empty: no pattern matched this text). None: no sweep."""
    if results is None:
        return []
    idx = _index(results)
    out = []
    for c in chunks:
        loc = {"file": c["file"], "line": c["line"], "end_line": c["end_line"]}
        r = idx.get(c["qid"])
        if r is None or "skipped" in r:
            out.append({"check": "soft.sweep", **loc, "qid": c["qid"],
                        "backend": (r or {}).get("backend"),
                        "skipped": (r or {}).get("skipped", "no answer returned")})
            continue
        out.append({"check": "soft.sweep", **loc, **{k: r.get(k) for k in SWEEP_FIELDS},
                    "covered": chunks_mod.covered(c, s4_findings)})
    return out


def summary(questions, fs) -> list[str]:
    kinds = Counter(q["kind"] for q in questions)
    lines = [f"questions: {len(questions)} ({kinds.get('label', 0)} label, "
             f"{kinds.get('relational', 0)} relational)"]
    checks_of = {q["qid"]: sorted({s["check"] for s in q["sources"]}) for q in questions}
    for check, role in (("soft.label", "label"), ("soft.compare", "compare")):
        done = [f for f in fs if f["check"] == check and "skipped" not in f]
        if not done:
            continue
        backend = done[0].get("backend")
        by_label = Counter(f["label"] for f in done)
        lines.append(f"{role} ({backend}): {len(done)} answered: "
                     + ", ".join(f"{k} {v}" for k, v in sorted(by_label.items())))
        per_check: dict[str, Counter] = {}
        for f in done:
            for c in checks_of.get(f["qid"], []):
                per_check.setdefault(c, Counter())[f["label"]] += 1
        for c in sorted(per_check):
            lines.append(f"  {c}: " + ", ".join(f"{k} {v}"
                                                for k, v in sorted(per_check[c].items())))
        trunc = sum(1 for f in done if f.get("truncated"))
        if trunc:
            lines.append(f"  {trunc} answered on a truncated state")
    agree = [f for f in fs if f["check"] == "soft.agree"]
    if agree:
        n = sum(1 for f in agree if f["agree"])
        lines.append(f"agree {n} of {len(agree)} ({round(100 * n / len(agree))}%)")
    sw = [f for f in fs if f["check"] == "soft.sweep" and "skipped" not in f]
    if sw:
        flagged = [f for f in sw if f["flagged"]]
        lines.append(f"sweep ({sw[0].get('backend')}): {len(sw)} chunks, {len(flagged)} flagged, "
                     f"{sum(1 for f in flagged if not f['covered'])} of them with no stage 4 hit")
    reads = [f for f in fs if f["check"] == "soft.read" and "skipped" not in f]
    if reads:
        lines.append(f"relational ({reads[0].get('backend')}): {len(reads)} answered")
    skips = Counter((f["check"], f["skipped"]) for f in fs if "skipped" in f)
    for (check, reason), n in sorted(skips.items()):
        lines.append(f"skipped: {check} x{n}: {reason}")
    return lines


def record(role, r) -> dict:
    row = {"role": role, "qid": r.get("qid"), "backend": r.get("backend"),
           "model": r.get("model"), "request": r.get("request"), "response": r.get("response")}
    if "skipped" in r:
        row["skipped"] = r["skipped"]
    else:
        for k in ("label", "probabilities", "confidence", "truncated", "answer", "capped",
                  "confidence_kind", "reads", "kind", "p_any", "flagged"):
            if k in r:
                row[k] = r[k]
    return row
