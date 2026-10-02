"""Test data set aside from the capability map. Spec: specs/testdata.SPEC.md.

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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "04-phrases"))

from audience import audience, is_test_data  # noqa: E402

READ_BY_MODEL = ("model", "subagent")


def _in_test_data(f: dict, key: str) -> bool:
    if key == "04":
        return f.get("audience") == "test-data"
    return bool(f.get("file")) and is_test_data(f["file"])


def set_aside(reports: dict, loaded=()) -> tuple[dict, list[dict]]:
    """(reports without test-data findings in stages 1 and 4, one cap.testdata finding or none).
    Files in `loaded` (test data a model-read file references) are never set aside: what the
    model is pointed at counts like any other file."""
    out, counts, folders = dict(reports), Counter(), Counter()
    loaded = set(loaded)
    for key in ("01", "04"):
        doc = reports.get(key) or {}
        keep = []
        for f in doc.get("findings", []):
            if _in_test_data(f, key) and f.get("file") not in loaded:
                counts[key] += 1
                folders[f["file"].split("/")[0]] += 1
            else:
                keep.append(f)
        out[key] = dict(doc, findings=keep)
    if not counts:
        return out, []
    return out, [{"check": "cap.testdata", "file": None, "line": None,
                  "stage1": counts["01"], "stage4": counts["04"],
                  "top_folders": [name for name, _ in folders.most_common(5)]}]


def loaded_pairs(reports: dict) -> list[dict]:
    """cap.pair testdata+loaded: a test-data file reached by a direct reference from a file a
    model or subagent reads."""
    out = []
    for f in (reports.get("03") or {}).get("findings", []):
        if f.get("check") != "graph.depth" or "skipped" in f or f.get("via") != "static":
            continue
        src, dst = f.get("from"), f.get("file")
        if dst and src and is_test_data(dst) and not is_test_data(src) \
                and audience(src) in READ_BY_MODEL:
            out.append({"check": "cap.pair", "file": dst, "line": None, "pair": "testdata+loaded",
                        "from": src, "evidence": [{"stage": "03", "check": "graph.depth",
                                                   "file": dst, "line": None,
                                                   "why": f"referenced directly from {src}"}]})
    return out
