"""The reports of the stages that ran before an AI stage. Spec: specs/shared.SPEC.md, upstream.

Moved here from the soft stage (restructure step 5), cut down to what two stages share: reading a
saved `NN-name.json` and checking it against the report contract (`stages/CONTRACT.md`). Stage
code is never imported. (Named `upstream`, not `inputs`, so it never collides with `02.5-capability`'s
module of that name in one test session.) Since step 7b the reports are keyed by stage name.
"""
from __future__ import annotations

import json
from pathlib import Path


class ReportError(Exception):
    pass


def check(name: str, doc) -> dict:
    """`doc` as a contract-1 report of stage `name`, else ReportError naming the stage."""
    if not isinstance(doc, dict):
        raise ReportError(f"{name}: report is not a JSON object")
    if doc.get("contract") != 1:
        raise ReportError(f"{name}: contract {doc.get('contract')!r}, expected 1")
    if doc.get("stage") != name:
        raise ReportError(f"{name}: report says stage {doc.get('stage')!r}")
    if not isinstance(doc.get("findings"), list):
        raise ReportError(f"{name}: no findings list")
    return doc


def load_dir(reports_dir, names, required=None) -> dict:
    """{stage name: report} for each stage in `names` whose `<name>.json` is in the folder.
    A name in `required` (default: all of them) with no file is a ReportError."""
    d = Path(reports_dir)
    need = tuple(names) if required is None else tuple(required)
    reports = {}
    for name in names:
        p = d / f"{name}.json"
        if not p.is_file():
            if name in need:
                raise ReportError(f"{name}: missing {p}")
            continue
        try:
            doc = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise ReportError(f"{name}: cannot read {p}: {exc}")
        reports[name] = check(name, doc)
    return reports


def skips(reports: dict) -> list[tuple[str, dict]]:
    """[(stage name, finding)] for every finding with `skipped`, in name order (the numbers lead the
    names, so that is run order)."""
    return [(name, f) for name in sorted(reports)
            for f in reports[name].get("findings", []) if "skipped" in f]
