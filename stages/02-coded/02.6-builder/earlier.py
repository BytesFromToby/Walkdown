"""What the builder step reads from the steps before it. Spec: specs/builder.SPEC.md, run.py (the runner) and earlier.py (what it reads).

From a folder of saved outputs (`--reports`, a run's data folder). A step run on its own gets that
folder from `stages/_shared/earlier_steps.py`, which runs the earlier steps into one. The earlier
steps' code is never imported. Named `earlier` so it shares no module name with another stage's
`inputs.py` or `upstream.py` in one pytest session.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import stagelist  # noqa: E402

STAGE = "02.6-builder"
INVENTORY, PHRASES, CAPABILITY = "02.1-inventory", "02.4-phrases", "02.5-capability"
# The earlier steps this one reads: from stages.json (the three above are the ones it uses).
READS = stagelist.reads(STAGE)


class ReportError(Exception):
    """A saved output that is missing or is not a contract-1 report of the step it should be."""


class Earlier(NamedTuple):
    """The four things the builder checks need.

    inventory:  02.1's report (a whole contract-1 document)
    graph:      02.3's graph.json, or None when there is none (cost and fit then report nothing
                that needs edges, as they always did)
    capability: 02.5's findings: `cap.injection` (what a hook adds) for `fit.hook` and the session
                tier, and the `testdata+loaded` pairs that say which test-data files stay in
    secrets:    02.4's `secret.found` findings, so a quote on a secret's line is masked here too
    """
    inventory: dict
    graph: dict | None
    capability: list
    secrets: list


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


def _read(reports_dir: Path, name: str) -> dict:
    p = reports_dir / f"{name}.json"
    try:
        return _check(name, json.loads(p.read_text("utf-8")))
    except (OSError, ValueError) as exc:
        raise ReportError(f"{name}: cannot read {p}: {exc}")


def _graph(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text("utf-8"))
    except (OSError, ValueError) as exc:
        raise ReportError(f"02.3-graph: cannot read {path}: {exc}")


def load_dir(reports_dir) -> Earlier:
    """The saved outputs of a run: 02.1-inventory.json, 02.4-phrases.json, 02.5-capability.json,
    and graph.json when there is one."""
    d = Path(reports_dir)
    inv = _read(d, INVENTORY)
    phrases = _read(d, PHRASES)
    capability = _read(d, CAPABILITY)
    return Earlier(inv, _graph(d / "graph.json"), capability["findings"],
                   [f for f in phrases["findings"] if f.get("check") == "secret.found"])
