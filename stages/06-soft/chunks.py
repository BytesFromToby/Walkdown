"""Split the prose a model reads into chunks for the coverage sweep. Spec: specs/chunks.SPEC.md.

Soft D2 (2026-10-01): stage 6 asks a model about every chunk, so text no stage 4 pattern
matches still gets a read. Reads only; asks no model.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "04-phrases"))

from audience import audience  # noqa: E402

PROSE_EXTS = {"md", "mdc", "markdown", "txt"}
SWEEP_AUDIENCES = ("model", "subagent")
CAP = 1200  # characters per chunk; a section longer than this is split at blank lines, then lines
HEADING = re.compile(r"^\s{0,3}#{1,6}\s")
FENCE = re.compile(r"^\s{0,3}(```|~~~)")


def sweep_files(inventory: dict | None) -> list[str]:
    """Text files a model reads: prose extension, audience model or subagent (stage 4's
    path rule), readable, not a symlink."""
    out = []
    for f in (inventory or {}).get("findings", []):
        if f.get("check") != "inv.file" or "skipped" in f or not f.get("encoding"):
            continue
        rel = f.get("file") or ""
        if f.get("type") == "inode/symlink" or "target" in f:
            continue
        ext = rel.rsplit(".", 1)[1].lower() if "." in rel.rsplit("/", 1)[-1] else ""
        if ext in PROSE_EXTS and audience(rel) in SWEEP_AUDIENCES:
            out.append(rel)
    return sorted(out)


def _sections(lines: list[str]) -> list[tuple[int, int]]:
    """(start, end) 1-based inclusive: a leading frontmatter block, then one section per
    heading (a heading inside a code fence does not start one)."""
    starts, n = [], len(lines)
    i = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, n):
            if lines[j].strip() in ("---", "..."):
                starts.append(1)
                i = j + 1
                break
    if i < n:
        starts.append(i + 1)
    fence = False
    for k in range(i, n):
        if FENCE.match(lines[k]):
            fence = not fence
        elif not fence and HEADING.match(lines[k]) and k + 1 not in starts:
            starts.append(k + 1)
    starts = sorted(set(starts))
    return [(s, (starts[x + 1] - 1) if x + 1 < len(starts) else n) for x, s in enumerate(starts)]


def _size(lines, a, b) -> int:
    return sum(len(x) + 1 for x in lines[a - 1:b])


def _split(lines, a, b) -> list[tuple[int, int]]:
    """Cut a section over CAP at blank lines; a paragraph still over CAP at line ends; a
    single line over CAP stays whole (never cut mid-line)."""
    if _size(lines, a, b) <= CAP:
        return [(a, b)]
    out, start, size = [], a, 0
    for k in range(a, b + 1):
        size += len(lines[k - 1]) + 1
        blank = not lines[k - 1].strip()
        if (blank and size >= CAP // 2) or size >= CAP:
            out.append((start, k))
            start, size = k + 1, 0
    if start <= b:
        out.append((start, b))
    return out


def chunk_text(rel: str, lines: list[str]) -> list[dict]:
    out = []
    for a, b in _sections(lines):
        for s, e in _split(lines, a, b):
            text = "\n".join(lines[s - 1:e]).strip()
            if text:
                out.append({"file": rel, "line": s, "end_line": e, "text": text})
    return out


def build(inventory, lines_reader) -> list[dict]:
    """Every chunk of every sweep file, in file then line order. `lines_reader(rel)` gives
    the decoded lines (packet.Lines.lines) or None."""
    out = []
    for rel in sweep_files(inventory):
        ls = lines_reader(rel)
        if ls:
            out.extend(chunk_text(rel, ls))
    return out


def covered(chunk: dict, s4_findings) -> list[str]:
    """Stage 4 phrase patterns that hit inside the chunk's lines (any audience)."""
    pats = set()
    for f in s4_findings or []:
        if (str(f.get("check", "")).startswith("phrase.") and "skipped" not in f
                and f.get("file") == chunk["file"] and isinstance(f.get("line"), int)
                and chunk["line"] <= f["line"] <= chunk["end_line"]):
            pats.update(f.get("patterns") or [])
    return sorted(pats)
