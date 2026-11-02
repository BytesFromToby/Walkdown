"""Test data set aside from the capability map. Spec: specs/capability.SPEC.md, testdata.

Fixtures and tests are never loaded as instructions when an artifact is installed, so their
hooks, grants, and phrase hits say nothing about what installing it grants (2026-10-02,
Walkdown self-audit). They are kept out of legs, grants, injection, posture, and pairs, and
counted. A test-data file that a model-read file references directly comes back as a pair:
a folder name alone never hides text a model is pointed at.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))

from audience import audience, is_test_data  # noqa: E402
import coverlines as cov  # noqa: E402

READ_BY_MODEL = ("model", "subagent")
INVENTORY, PHRASES = "02.1-inventory", "02.4-phrases"
TESTDATA = "cap.testdata"  # the key of its coverage line


def _in_test_data(f: dict, stage: str) -> bool:
    if stage == PHRASES:
        return f.get("audience") == "test-data"
    return bool(f.get("file")) and is_test_data(f["file"])


def set_aside(reports: dict, loaded=()) -> tuple[dict, list[dict]]:
    """(reports without test-data findings from the inventory and the phrases, one cap.testdata
    finding or none). `inventory_set_aside` and `phrases_set_aside` count what was set aside from each
    (named for the step since restructure step 7b).
    Files in `loaded` (test data a model-read file references) are never set aside: what the
    model is pointed at counts like any other file."""
    out, counts, folders = dict(reports), Counter(), Counter()
    loaded = set(loaded)
    for stage in (INVENTORY, PHRASES):
        doc = reports.get(stage) or {}
        keep = []
        for f in doc.get("findings", []):
            cov.look(TESTDATA)  # each finding of the inventory and the phrase step is kept or set aside here
            if _in_test_data(f, stage) and f.get("file") not in loaded:
                counts[stage] += 1
                folders[f["file"].split("/")[0]] += 1
            else:
                keep.append(f)
        out[stage] = dict(doc, findings=keep)
    if not counts:
        return out, []
    return out, [{"check": "cap.testdata", "file": None, "line": None,
                  "inventory_set_aside": counts[INVENTORY], "phrases_set_aside": counts[PHRASES],
                  "top_folders": [name for name, _ in folders.most_common(5)]}]


def loaded_pairs(reports: dict, graph: dict | None = None) -> list[dict]:
    """cap.pair testdata+loaded: a test-data file reached by a direct reference from a file a
    model or subagent reads. `from_line` (review C36, 2026-10-18): the line in `from` that names
    it, from the graph's static edge, so a card can show where the model is pointed at it."""
    lines = {}
    for e in (graph or {}).get("edges") or []:
        if e.get("kind") == "static" and e.get("line") is not None:
            lines.setdefault((e.get("from"), e.get("to")), e["line"])
    out = []
    reached = [f for f in (reports.get("02.3-graph") or {}).get("findings", [])
               if f.get("check") == "graph.depth" and "skipped" not in f and f.get("via") == "static"]
    for f in reached:
        cov.look("cap.pair")
        src, dst = f.get("from"), f.get("file")
        if dst and src and is_test_data(dst) and not is_test_data(src) \
                and audience(src) in READ_BY_MODEL:
            out.append({"check": "cap.pair", "file": dst, "line": None, "pair": "testdata+loaded",
                        "from": src, "from_line": lines.get((src, dst)), "evidence": [{"stage": "02.3-graph", "check": "graph.depth",
                                                   "file": dst, "line": None,
                                                   "why": f"referenced directly from {src}"}]})
    return out
