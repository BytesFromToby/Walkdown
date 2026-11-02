"""Plain words for what each `02.4-phrases` pattern looks for. Spec: specs/report.SPEC.md, review_html.

The words are data (Library/README.md): each row of Library/patterns.yaml has a `plain` field, and
this file only reads them. They were written here until restructure step 3b (2026-10-29), after
review C21 (2026-10-12): the owner found the pattern notes ("confirm-first tier with no
confirmation") to be jargon while labeling D3, and the review page shows the same descriptions to
the report reader. Each entry says what the words are and why a pattern would care ("The worry:
..."), never whether the line is a problem. Every row of Library/patterns.yaml has one
(tests/test_plain.py); a new pattern needs its plain description too.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
import library  # noqa: E402

# pattern id -> its plain words, in the table's order
PLAIN = {row["id"]: row["plain"] for row in library.load_yaml("patterns.yaml")["patterns"]
         if row.get("plain")}


def describe(patterns) -> list[tuple[str, str]]:
    """(id, plain words) per pattern id, in the order given, each once. An id with no entry
    (a retired pattern in an old run) keeps its id and says so."""
    out, seen = [], set()
    for p in patterns or []:
        if p in seen:
            continue
        seen.add(p)
        out.append((p, PLAIN.get(p) or "A search pattern this version of Walkdown no longer has."))
    return out
