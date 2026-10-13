"""Pinpoint (owner, 2026-10-13): for each sweep passage the report shows, a second model names
the line that does the flagged kind of action, quotes it, and says it in one plain sentence.
Spec: specs/pinpoint.SPEC.md.

A sweep passage can be a dozen lines; a reader new to this cannot tell which part is the
issue. The answer is kept only when its quote is found, word for word, in the passage as this
run read it, and it is shown at the line the quote really starts on. Mark, never demote: a pinpoint never removes or changes
a sweep finding, and "no line does this" is recorded, not acted on.
"""
from __future__ import annotations

import json
import re

# The report shows sweep passages from p_any 0.4 ("near the line", render.SWEEP_NEAR_P) up,
# when no stage 4 pattern hit inside them; those are the passages a reader has to read.
MIN_P = 0.4
MAX_ALSO = 2


def squash(s: str) -> str:
    return " ".join(str(s).split())


def targets(sweep_findings) -> list[dict]:
    """The sweep findings the report shows as their own card."""
    return [f for f in sweep_findings
            if f.get("check") == "soft.sweep" and "skipped" not in f
            and (f.get("p_any") or 0) >= MIN_P and not f.get("covered")]


def question(finding, chunk_lines: dict[int, str], data) -> dict:
    """One pinpoint question: the passage with its line numbers, and the kind it was read as,
    in the sweep option's own words (softreads.yaml)."""
    kind = finding.get("kind")
    what = " ".join(((data.get("sweep") or {}).get("options", {}).get(kind) or {})
                    .get("what", kind or "").split())
    numbered = "\n".join(f"{n}: {t}" for n, t in sorted(chunk_lines.items()))
    prompt = (f"FLAG: the passage was read as telling the agent to do this kind of action: {what}"
              "\n\nPASSAGE (numbered lines from the file; data only):\n```\n" + numbered
              + "\n```\n\n" + data["pinpoint"]["question"] + "\n")
    return {"qid": "pin:" + finding["qid"], "sweep_qid": finding["qid"],
            "_prompt": prompt, "_system": data["pinpoint"]["system"]}


def parse(text: str):
    """The JSON object in a model answer, or None."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        doc = json.loads(m.group(0))
    except ValueError:
        return None
    return doc if isinstance(doc, dict) else None


def locate(n, quote, lines: dict[int, str]):
    """The last line of `quote` when it starts on line n (prose is hard-wrapped, so it may run
    onto the next lines of the passage); None when it does not."""
    q = squash(quote or "")
    if not isinstance(n, int) or isinstance(n, bool) or n not in lines or not q:
        return None
    rest, end_of = "", {}
    for k in sorted(k for k in lines if k >= n):
        rest = (rest + " " + squash(lines[k])).strip()
        end_of[k] = len(rest)
    at = rest.find(q)
    if not (0 <= at < end_of[n]):
        return None
    stop = at + len(q)
    return next(k for k in sorted(end_of) if end_of[k] >= stop)


def find(n, quote, lines: dict[int, str]):
    """(start, end) of `quote` in the passage: on line n when it starts there, else on the first
    line it does start on (a model can be off by a line; the quote is what is checked, and the
    line it really starts on is used). None when the quote is nowhere in the passage."""
    e = locate(n, quote, lines)
    if e is not None:
        return n, e
    for k in sorted(lines):
        e = locate(k, quote, lines)
        if e is not None:
            return k, e
    return None


def check(ans, lines: dict[int, str]) -> dict:
    """{"verified", "why", "line", "line_end", "quote", "plain", "also"} from a parsed answer.
    `also` keeps only entries that pass the same check, at most MAX_ALSO."""
    plain = squash(ans.get("plain") or "")
    also = []
    for a in ans.get("also") or []:
        if isinstance(a, dict) and isinstance(a.get("quote"), str):
            got = find(a.get("line"), a.get("quote"), lines)
            if got is not None:
                also.append({"line": got[0], "line_end": got[1], "quote": squash(a["quote"])})
    also = also[:MAX_ALSO]
    n = ans.get("line")
    if n is None:
        return {"verified": bool(plain), "why": "no line named" if plain else "empty answer",
                "line": None, "line_end": None, "quote": None, "plain": plain, "also": also}
    got = find(n, ans.get("quote"), lines) if isinstance(ans.get("quote"), str) else None
    if got is None:
        return {"verified": False, "why": f"quote not found in the passage (model said line {n})",
                "line": n, "line_end": None, "quote": squash(ans.get("quote") or ""),
                "plain": plain, "also": also}
    start, e = got
    also = [x for x in also if x["line"] != start]
    why = "quote found" if start == n else f"quote found starting at line {start} (model said {n})"
    return {"verified": bool(plain), "why": why if plain else "no plain sentence",
            "line": start, "line_end": e, "quote": squash(ans["quote"]), "plain": plain,
            "also": also}


def findings(targets_, questions, answers, chunk_lines_of) -> list[dict]:
    """One soft.pinpoint finding per target: the checked answer, or `skipped`."""
    by_q = {a.get("qid"): a for a in answers or []}
    out = []
    for f, q in zip(targets_, questions):
        loc = {"file": f["file"], "line": f["line"], "end_line": f["end_line"]}
        a = by_q.get(q["qid"]) or {}
        base = {"check": "soft.pinpoint", **loc, "qid": q["qid"], "sweep_qid": f["qid"],
                "backend": a.get("backend")}
        if not a or "skipped" in a:
            out.append({**base, "skipped": a.get("skipped", "no answer returned")})
            continue
        ans = parse(a.get("answer"))
        if ans is None:
            out.append({**base, "skipped": "unparseable pinpoint answer"})
            continue
        r = check(ans, chunk_lines_of(f))
        out.append({**base, "model": a.get("model"),
                    **{("pin_line" if k == "line" else "pin_end" if k == "line_end" else k): v
                       for k, v in r.items()}})
    return out
