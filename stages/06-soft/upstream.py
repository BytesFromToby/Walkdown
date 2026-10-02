"""Stage 1 to 5 reports for one input: from a saved folder or by running the runners.
Spec: specs/upstream.SPEC.md. Stage code is never imported."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

NAMES = {"01": "01-inventory", "02": "02-reader", "03": "03-graph", "04": "04-phrases",
         "05": "05-capability"}
REQUIRED = ("01", "04", "05")


class ReportError(Exception):
    pass


class StageFailure(Exception):
    pass


def _check(key: str, doc) -> dict:
    name = NAMES[key]
    if not isinstance(doc, dict):
        raise ReportError(f"{name}: report is not a JSON object")
    if doc.get("contract") != 1:
        raise ReportError(f"{name}: contract {doc.get('contract')!r}, expected 1")
    if doc.get("stage") != name:
        raise ReportError(f"{name}: report says stage {doc.get('stage')!r}")
    if not isinstance(doc.get("findings"), list):
        raise ReportError(f"{name}: no findings list")
    return doc


def load_dir(reports_dir) -> dict:
    d = Path(reports_dir)
    reports = {}
    for key, name in NAMES.items():
        p = d / f"{name}.json"
        if not p.is_file():
            if key in REQUIRED:
                raise ReportError(f"{name}: missing {p}")
            continue
        try:
            doc = json.loads(p.read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise ReportError(f"{name}: cannot read {p}: {exc}")
        reports[key] = _check(key, doc)
    return reports


def _run(python, runner: Path, args: list[str], key: str) -> tuple[dict, bytes]:
    name = NAMES[key]
    p = subprocess.run([str(python), str(runner), *args], capture_output=True)
    if p.returncode != 0:
        raise StageFailure(f"{name} failed (exit {p.returncode}): "
                           + p.stderr.decode("utf-8", "replace")[-1500:])
    try:
        return _check(key, json.loads(p.stdout.decode("utf-8"))), p.stdout
    except (ValueError, ReportError) as exc:
        raise StageFailure(f"{name} printed no valid report: {exc}")


def run_stages(input_dir, stages_root, python, work_dir) -> dict:
    root, work = Path(stages_root), Path(work_dir)
    inp = str(input_dir)
    runner = {k: root / n / "run.py" for k, n in NAMES.items()}
    inv = work / "01-inventory.json"
    reports, raw = {}, {}
    reports["01"], raw["01"] = _run(python, runner["01"], [inp], "01")
    inv.write_bytes(raw["01"])
    reports["02"], raw["02"] = _run(python, runner["02"], [inp], "02")
    reports["03"], raw["03"] = _run(python, runner["03"],
                                    [inp, "--inventory", str(inv), "--out", str(work)], "03")
    reports["04"], raw["04"] = _run(python, runner["04"], [inp, "--inventory", str(inv)], "04")
    for key in ("02", "03", "04"):
        (work / f"{NAMES[key]}.json").write_bytes(raw[key])
    reports["05"], _ = _run(python, runner["05"], [inp, "--reports", str(work)], "05")
    return reports


def skips(reports: dict) -> list[tuple[str, dict]]:
    return [(key, f) for key in sorted(reports)
            for f in reports[key].get("findings", []) if "skipped" in f]
