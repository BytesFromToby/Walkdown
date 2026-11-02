"""Sweep findings, the stderr summary, and the answers-file rows. Spec: specs/sweep.SPEC.md, Findings (findings.py).
Calls no backend; changes no earlier stage's findings."""
from __future__ import annotations

from collections import Counter

import chunks as chunks_mod
import coverlines as cov

SWEEP_FIELDS = ("qid", "backend", "model", "kind", "probabilities", "p_any", "flagged")
# A model that gives no probability (a text model) has neither of these: the finding leaves them out, and nothing invents them.
NUMBERS = ("probabilities", "p_any")


def _index(results) -> dict:
    return {r["qid"]: r for r in results or []}


def sweep_findings(chunks, results, s4_findings) -> list[dict]:
    """One soft.sweep finding per chunk, with `covered`: the `02.4-phrases` patterns that hit inside its
    lines (empty: no pattern matched this text). `results` None: no sweep, no findings."""
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
            cov.explain("soft.sweep")  # a passage that got no answer is explained by its skip
            continue
        out.append({"check": "soft.sweep", **loc, **{k: r.get(k) for k in SWEEP_FIELDS if k not in NUMBERS or k in r},
                    "covered": chunks_mod.covered(c, s4_findings)})
        cov.look("soft.sweep")  # a passage that got an answer is looked at
    return out


def summary(fs) -> list[str]:
    """The stderr lines: how many passages were read and flagged, and the skips by reason."""
    lines = []
    sw = [f for f in fs if f["check"] == "soft.sweep" and "skipped" not in f]
    if sw:
        flagged = [f for f in sw if f["flagged"]]
        lines.append(f"sweep ({sw[0].get('backend')}): {len(sw)} chunks, {len(flagged)} flagged, "
                     f"{sum(1 for f in flagged if not f['covered'])} of them with no stage 4 hit")
    skips = Counter((f["check"], f["skipped"]) for f in fs if "skipped" in f)
    for (check, reason), n in sorted(skips.items()):
        lines.append(f"skipped: {check} x{n}: {reason}")
    return lines


def record(r) -> dict:
    """One row of data/03-sweep.answers.jsonl: the answer as the backend gave it, with the exact
    request sent and the raw response."""
    row = {"role": "sweep", "qid": r.get("qid"), "backend": r.get("backend"),
           "model": r.get("model"), "request": r.get("request"), "response": r.get("response")}
    if "skipped" in r:
        row["skipped"] = r["skipped"]
    else:
        for k in ("kind", "probabilities", "p_any", "flagged"):
            if k in r:
                row[k] = r[k]
    return row
