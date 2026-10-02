"""Term table: definitions, conflicts, safety-word definitions. Spec: specs/terms.SPEC.md."""
from __future__ import annotations

import re

from conditionals import split_sentences

HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
QUOTE_CHARS = "\"'`“”‘’*_~"
TRAIL = ".,;:!?"
TAIL_TOKEN = re.compile(
    r"(?:[\"“'‘`]([^\"”'’`]+)[\"”'’`]|\*\*([^*]+)\*\*|\*([^*]+)\*|_([^_]+)_)\s*$")
BY_ANY = re.compile(r"\bby\s*(no|any|all|some)?\s*$", re.IGNORECASE)
LEAD_WORDS = {"the", "a", "an"}
BAD_LAST = {"this", "that", "it", "which", "what", "these", "those", "so", "a", "an", "the",
            "any", "no", "all", "some", "by", "is", "are", "was", "were", "be"}
GLOSS_BOLD = re.compile(r"^\s*(?:[-*+]\s+)?\*\*(?P<t>[^*]+?):\*\*\s*(?P<d>.+)$|"
                        r"^\s*(?:[-*+]\s+)?\*\*(?P<t2>[^*]+?)\*\*\s*:\s*(?P<d2>.+)$")
GLOSS_ITEM = re.compile(r"^\s*[-*+]\s+(?P<t>[^:*]+?):\s+(?P<d>.+)$")
SOURCES = ["explicit", "mapping", "glossary", "procedural"]
LIST_LEAD = re.compile(r"^\s*(?:[-*+>]\s+|\d+[.)]\s+)+")
WORDY = re.compile(r"\w")


def normalize_term(t: str) -> str:
    s = "".join(c for c in t if c not in QUOTE_CHARS).lower()
    s = " ".join(s.split())
    return s.rstrip(TRAIL).strip()


def _norm_def(d: str) -> str:
    return " ".join(d.lower().split()).rstrip(TRAIL).strip()


def _explicit_term(pre: str, vocab) -> str | None:
    if BY_ANY.search(pre):
        return None
    m = TAIL_TOKEN.search(pre)
    if m:
        term = normalize_term(next(g for g in m.groups() if g is not None))
    else:
        clause = re.split(r"[,;:()\[\]|]", pre)[-1]
        clause = LIST_LEAD.sub("", clause)
        words = normalize_term(clause).split()
        while words and words[0] in LEAD_WORDS:
            words = words[1:]
        if len(words) >= 2 and words[0] in ("word", "term"):
            words = words[1:]
        term = " ".join(words)
    words = term.split()
    if not words or len(words) > vocab.max_term_words:
        return None
    if term in vocab.not_terms or words[-1] in BAD_LAST:
        return None
    return term


def _sentence_defs(s: str, vocab) -> list[tuple[str, str, str]]:
    out = []
    m = vocab.explicit_by.search(s)
    if m:
        term = normalize_term(m.group(1))
        d = s[m.end():].strip()
        if term and d and len(term.split()) <= vocab.max_term_words:
            out.append((term, d, "explicit"))
    for m in vocab.explicit_kw.finditer(s):
        term = _explicit_term(s[:m.start()], vocab)
        d = s[m.end():].strip()
        if term and d:
            out.append((term, d, "explicit"))
            break
    m = vocab.mapping.search(s)
    if m:
        rest = s[m.end():]
        q = re.match(r"\s*([\"“'‘`])(.+?)[\"”'’`]", rest)
        if q:
            term, d = normalize_term(q.group(2)), rest[q.end():].lstrip(" ,").strip()
        else:
            parts = rest.split(",", 1)
            term = normalize_term(parts[0]) if len(parts) == 2 else ""
            words = term.split()
            while words and words[0] in LEAD_WORDS:
                words = words[1:]
            term = " ".join(words)
            d = parts[1].strip() if len(parts) == 2 else ""
        if term and d:
            out.append((term, d, "mapping"))
    return out


def defs_file(rel, raw, folded, instr, audience, vocab) -> list[dict]:
    src = [r if r == f else f for r, f in zip(raw, folded)]
    headings: dict[int, tuple[int, str]] = {}
    in_fence = False
    for i, line in enumerate(src, start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            h = HEADING.match(line)
            if h:
                headings[i] = (len(h.group(1)), h.group(2))

    found: list[dict] = []

    def add(n, term, d, source):
        if not term or not WORDY.search(d or ""):
            return
        if any(x["line"] == n and x["term"] == term for x in found):
            return
        found.append({"check": "term.def", "file": rel, "line": n, "quote": raw[n - 1],
                      "audience": audience, "term": term, "definition": d, "source": source})

    gloss_level = None
    for n, line in enumerate(src, start=1):
        if n in headings:
            level, text = headings[n]
            if gloss_level is not None and level <= gloss_level:
                gloss_level = None
            if vocab.glossary_heading.search(text):
                gloss_level = level
            p = vocab.procedural_heading.match(line)
            if p and n in instr:
                nxt = next((k for k in range(n + 1, len(src) + 1) if src[k - 1].strip()), None)
                term = normalize_term(p.group(2))
                if nxt is not None and nxt not in headings and term:
                    add(n, term, src[nxt - 1].strip(), "procedural")
            continue
        if n not in instr:
            continue
        for a, b in split_sentences(line):
            for term, d, source in _sentence_defs(line[a:b], vocab):
                add(n, term, d, source)
        if gloss_level is not None:
            g = GLOSS_BOLD.match(line) or GLOSS_ITEM.match(line)
            if g:
                t = g.group("t") if g.group("t") is not None else g.groupdict().get("t2")
                d = g.group("d") if g.group("d") is not None else g.groupdict().get("d2")
                term = normalize_term(t or "")
                if term and d and len(term.split()) <= vocab.max_term_words:
                    add(n, term, d.strip(), "glossary")
    found.sort(key=lambda x: (x["line"], SOURCES.index(x["source"])))
    return found


def conflicts(defs) -> list[dict]:
    by: dict[str, list[dict]] = {}
    for d in defs:
        by.setdefault(d["term"], []).append(d)
    out = []
    for term in sorted(by):
        rows = sorted(by[term], key=lambda d: (d["file"], d["line"]))
        if len({_norm_def(d["definition"]) for d in rows}) >= 2:
            out.append({"check": "term.conflict", "file": None, "line": None, "term": term,
                        "definitions": [{"file": d["file"], "line": d["line"],
                                         "text": d["definition"]} for d in rows]})
    return out


def safety(defs, vocab) -> list[dict]:
    return [{"check": "term.safety", "file": d["file"], "line": d["line"], "quote": d["quote"],
             "audience": d.get("audience"), "term": d["term"]}
            for d in defs if any(vocab.safety.match(w) for w in d["term"].split())]
