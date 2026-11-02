"""`02.1-inventory` to `02.4-phrases` reports for one input, read from a saved folder (`--reports`). A stage run on its own
gets them run first by `stages/_shared/earlier_steps.py`. Spec: specs/capability.SPEC.md, inputs.
Stage code is never imported."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import stagelist  # noqa: E402

STAGE = "02.5-capability"
# The earlier steps this one reads, from stages.json. The reports are keyed by these names.
READS = stagelist.reads(STAGE)


class ReportError(Exception):
    pass


def _check(name: str, doc) -> dict:
    if not isinstance(doc, dict):
        raise ReportError(f"{name}: report is not a JSON object")
    if doc.get("contract") != 1:
        raise ReportError(f"{name}: contract {doc.get('contract')!r}, expected 1")
    if doc.get("stage") != name:
        raise ReportError(f"{name}: report says stage {doc.get('stage')!r}")
    if not isinstance(doc.get("findings"), list):
        raise ReportError(f"{name}: no findings list")
    return doc


def load_dir(reports_dir) -> tuple[dict, dict | None]:
    d = Path(reports_dir)
    reports = {}
    for name in READS:
        p = d / f"{name}.json"
        try:
            doc = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise ReportError(f"{name}: cannot read {p}: {exc}")
        reports[name] = _check(name, doc)
    graph = None
    g = d / "graph.json"
    if g.is_file():
        try:
            graph = json.loads(g.read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise ReportError(f"02.3-graph: cannot read {g}: {exc}")
    return reports, graph


def skips(reports: dict) -> list[tuple[str, dict]]:
    """[(stage name, finding)] for every finding with `skipped`, in name order."""
    return [(name, f) for name in sorted(reports)
            for f in reports[name].get("findings", []) if "skipped" in f]
