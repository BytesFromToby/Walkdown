"""Reading the base rates: how often each `02.4-phrases` pattern turned up in the repositories already
audited. Spec: specs/shared.SPEC.md, rates.

The table is `Library/baserates.json`. `tools/baserates.py` writes it; the report stage reads it
through this module (a stage never imports a tool, so the reading half lives here). A rate is a
published fact about a pattern, never a judgment of the artifact under review.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import library  # noqa: E402

DEFAULT_PATH = library.path("baserates.json")
# Levels name the base rate in words; they are bins of the count, never a judgment.
RARE, UNCOMMON, COMMON = "rare", "uncommon", "common"
LEVELS = {RARE: "no other audited repo", UNCOMMON: "one other audited repo",
          COMMON: "two or more other audited repos"}


def level(repos_hit: int) -> str:
    return RARE if repos_hit == 0 else UNCOMMON if repos_hit == 1 else COMMON


def rate(table: dict | None, pattern: str, exclude_hash: str | None = None) -> dict | None:
    """The base rate of one pattern over the corpus, leaving out the repo being audited
    (matched by hash) so a repo is never its own baseline. None without a table."""
    if not table:
        return None
    repos = [r for r in table.get("repos", []) if not exclude_hash or r.get("hash") != exclude_hash]
    hits = [r["lines"].get(pattern, 0) for r in repos]
    n_hit = sum(1 for h in hits if h)
    return {"pattern": pattern, "repos": len(repos), "repos_hit": n_hit, "lines": sum(hits),
            "level": level(n_hit)}


def phrase(rt: dict | None) -> str:
    """Plain words for a rate: 'rare: in 0 of 3 other audited repos'."""
    if not rt or not rt["repos"]:
        return ""
    of = f"{rt['repos_hit']} of {rt['repos']} other audited repo{'s' if rt['repos'] != 1 else ''}"
    lines = f", {rt['lines']} line{'s' if rt['lines'] != 1 else ''}" if rt["lines"] else ""
    return f"{rt['level']}: in {of}{lines}"


def load(path=DEFAULT_PATH) -> dict | None:
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except (OSError, ValueError):
        return None
