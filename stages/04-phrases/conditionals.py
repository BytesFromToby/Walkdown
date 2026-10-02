"""Conditional table: branches in instruction text by kind. Spec: specs/conditionals.SPEC.md."""
from __future__ import annotations

import re

URL = re.compile(r"\b[a-z][a-z0-9+.-]*://\S+", re.IGNORECASE)
DELIM = re.compile(r",|:|\s+then\b", re.IGNORECASE)
LEAD = re.compile(r"^[\s\-*+>#_`~]*(?:\d+[.)]\s*)?[\s*_`~]*$")
# no split after e.g., i.e., etc., vs.
SENT_END = re.compile(r"(?<!\be\.g)(?<!\bi\.e)(?<!\betc)(?<!\bvs)[.!?]+(?=\s)", re.IGNORECASE)


def _mask(s: str) -> str:
    return URL.sub(lambda m: "_" * len(m.group(0)), s)


def split_sentences(line: str) -> list[tuple[int, int]]:
    masked = _mask(line)
    spans, start = [], 0
    for m in SENT_END.finditer(masked):
        spans.append((start, m.end()))
        start = m.end()
    spans.append((start, len(line)))
    out = []
    for a, b in spans:
        while a < b and line[a].isspace():
            a += 1
        while b > a and line[b - 1].isspace():
            b -= 1
        if a < b:
            out.append((a, b))
    return out


def _kinds(condition: str, word: str, vocab) -> list[str]:
    if word == "on":
        allowed = vocab.on_kinds
    elif word == "in":
        allowed = vocab.in_kinds
    else:
        allowed = None
    kinds = []
    for kind, rx in vocab.kinds:
        if allowed is not None:
            if kind not in allowed:
                continue
            hit = vocab.harness_names.search(condition) if kind == "harness" else rx.search(condition)
        else:
            hit = rx.search(condition)
        if hit:
            kinds.append(kind)
    return kinds


def branch(sentence: str, vocab) -> dict | None:
    masked = _mask(sentence)
    for m in vocab.cond_words.finditer(masked):
        word = m.group(1).lower()
        if word in ("on", "in") and not LEAD.match(masked[:m.start()]):
            continue
        d = DELIM.search(masked, m.end())
        if d:
            cond_end, body_start = d.start(), d.end()
        else:
            cond_end, body_start = len(sentence), len(sentence)
        condition = sentence[m.start():cond_end].strip()
        kinds = _kinds(masked[m.start():cond_end], word, vocab)
        if not kinds:
            continue
        lead = sentence[:m.start()]
        before = "" if LEAD.match(lead) else lead.strip()
        after = sentence[body_start:].strip()
        body = " ".join(x for x in (before, after) if x)
        return {"word": word, "condition": condition, "body": body, "kinds": kinds,
                "kind": kinds[0]}
    return None


def cond_file(rel, raw, folded, instr, audience, vocab) -> list[dict]:
    out = []
    for n in sorted(instr):
        if n < 1 or n > len(folded):
            continue
        src = raw[n - 1] if raw[n - 1] == folded[n - 1] else folded[n - 1]
        for a, b in split_sentences(src):
            br = branch(src[a:b], vocab)
            if br is not None:
                out.append({"check": "cond.branch", "file": rel, "line": n,
                            "quote": raw[n - 1], "audience": audience, "kind": br["kind"],
                            "kinds": br["kinds"], "word": br["word"],
                            "condition": br["condition"], "body": br["body"]})
    return out
