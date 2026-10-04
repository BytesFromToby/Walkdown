"""Instruction position and repetition (REPORTING 4.4, 4.5). Spec: specs/position.SPEC.md.

Both work on "instruction-shaped" lines, defined here as lines a stage 4 phrase pattern flagged
in a file a model or subagent reads. Position: where those lines sit in a long file, and how
many are past the reader window. Repetition: sentences (in files a model reads) that appear
in more than one file, with the phrase patterns on their lines. Both locate; neither accuses:
a checklist at the end of a skill and shared boilerplate are normal (REPORTING "Not").
"""
from __future__ import annotations

import math
import re

# The reader window (REPORTING "Publish the thresholds"; stage 1 census uses the same numbers)
READER_LINES = 2000
READER_BYTES = 50_000
READ_BY_MODEL = ("model", "subagent")
MIN_WORDS = 6        # shorter sentences repeat by accident ("Run the tests.")
WHERE_CAP = 20
PROSE_EXTS = (".md", ".mdc", ".markdown", ".txt")  # repetition is about sentences, not config lines

_FENCE = re.compile(r"^\s{0,3}(```|~~~)")
_LEAD = re.compile(r"^\s*(?:[#>]+\s*|[-*+]\s+|\d+[.)]\s+|\|)+")
_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-z0-9']+")


def _over_window(lines: list[str], nbytes: int) -> bool:
    return len(lines) > READER_LINES or nbytes > READER_BYTES


def _window_line(lines: list[str]) -> int:
    """The last line inside the reader window (by lines and by bytes, whichever comes first)."""
    total = 0
    for n, line in enumerate(lines, start=1):
        total += len(line.encode("utf-8", "surrogatepass")) + 1
        if total > READER_BYTES or n > READER_LINES:
            return n - 1
    return len(lines)


def density(texts: dict, phrase_findings: list[dict]) -> list[dict]:
    """pos.density: one per model-read file over the reader window that has phrase hits."""
    hit_lines: dict[str, set] = {}
    for f in phrase_findings:
        if "skipped" not in f and f.get("audience") in READ_BY_MODEL:
            hit_lines.setdefault(f["file"], set()).add(f["line"])
    out = []
    for rel in sorted(texts):
        aud, lines, nbytes = texts[rel]
        if aud not in READ_BY_MODEL or not _over_window(lines, nbytes) or rel not in hit_lines:
            continue
        n = len(lines)
        edge = max(1, math.ceil(n * 0.1))
        hs = sorted(hit_lines[rel])
        first = sum(1 for x in hs if x <= edge)
        last = sum(1 for x in hs if x > n - edge)
        window = _window_line(lines)
        beyond = [x for x in hs if x > window]
        out.append({"check": "pos.density", "file": rel, "line": None, "lines": n,
                    "first10": first, "middle80": len(hs) - first - last, "last10": last,
                    "window_line": window, "beyond_window": len(beyond),
                    "beyond_lines": beyond[:WHERE_CAP]})
    return out


def sentences(lines: list[str]):
    """(line number, original sentence, normalized key) for prose sentences of MIN_WORDS or
    more, outside code fences and leading YAML frontmatter."""
    fence = False
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in ("---", "..."):
                start = i + 1
                break
    for n, raw in enumerate(lines, start=1):
        if n <= start:
            continue
        if _FENCE.match(raw):
            fence = not fence
            continue
        if fence:
            continue
        text = _LEAD.sub("", raw).strip()
        for part in _SPLIT.split(text):
            words = _WORD.findall(part.lower().replace("’", "'"))
            if len(words) >= MIN_WORDS:
                yield n, part.strip(), " ".join(words)


def repetition(texts: dict, phrase_findings: list[dict]) -> list[dict]:
    """rep.sentence: one per sentence (normalized) that appears in two or more model-read files."""
    pats: dict[tuple, set] = {}
    for f in phrase_findings:
        if "skipped" not in f:
            pats.setdefault((f["file"], f["line"]), set()).update(f.get("patterns") or [])
    seen: dict[str, list] = {}
    for rel in sorted(texts):
        aud, lines, _ = texts[rel]
        if aud not in READ_BY_MODEL or not rel.lower().endswith(PROSE_EXTS):
            continue
        for n, original, key in sentences(lines):
            seen.setdefault(key, []).append((rel, n, original))
    # sentences repeated at exactly the same places are one finding (a line split into two
    # sentences would otherwise be reported twice)
    groups: dict[tuple, list] = {}
    for key, occ in seen.items():
        if len({o[0] for o in occ}) < 2:
            continue
        places = tuple(sorted((r, n) for r, n, _ in occ))
        groups.setdefault(places, []).append(occ)
    out = []
    for places, occs in groups.items():
        files = sorted({r for r, _ in places})
        first = min(occs[0])
        text = " ".join(min(o)[2] for o in occs)
        found = set()
        for rel, n in places:
            found |= pats.get((rel, n), set())
        out.append({"check": "rep.sentence", "file": first[0], "line": first[1],
                    "sentence": text[:240], "files": len(files), "count": len(places),
                    "where": [{"file": r, "line": n} for r, n in list(places)[:WHERE_CAP]],
                    "patterns": sorted(found)})
    out.sort(key=lambda f: (-f["files"], -f["count"], f["file"], f["line"]))
    return out
