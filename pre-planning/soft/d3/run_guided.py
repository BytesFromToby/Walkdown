"""Re-run model labelers on the 119 real lines with the ordered (guided) label question.

    python pre-planning/soft/d3/run_guided.py jev [claude-cli]

D3 fairness (2026-10-04): the owner labels with the ordered decision on label.html; the
saved model runs used the flat definitions. This writes the same GUIDE (build.py) into a
temporary copy of stages/06-soft/softreads.yaml, runs stage 6 on Fixtures/06-soft/real-lines
with each backend, saves model-labels/<backend>-guided.json, and always restores the original
softreads.yaml. Nothing in the product changes.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
DATA = ROOT / "stages" / "06-soft" / "softreads.yaml"
sys.path.insert(0, str(HERE))

from build import GUIDE  # noqa: E402

QUESTION = (
    "Decide in order and stop at the first that fits. 1. Do the flagged words mean what the "
    "pattern in `matched` is looking for? If not: other-sense. 2. If they do: is the line "
    "showing the wording as an example, sample, quote, template, or text for a person to read, "
    "instead of saying it directly? If so: example-or-quote. 3. Otherwise: does the line tell "
    "the reader (the AI agent reading the file) to do the matched action (do; includes setup "
    "lines such as a config entry, and instructions to hide or not tell), tell it not to "
    "(not-to), or only state a fact (description)?")


def guided_doc(doc: dict) -> dict:
    by_key = {a["key"]: a for g in GUIDE for a in g["answers"]}
    for key, opt in doc["label"]["options"].items():
        a = by_key[key]
        opt["what"] = f"{a['title']}. {a['what']}"
        opt["examples"] = list(a["examples"])
    doc["label"]["question"] = QUESTION
    return doc


def run(backend: str) -> Path:
    py = ROOT / ".venv" / "Scripts" / "python.exe"
    py = py if py.is_file() else Path(sys.executable)
    proc = subprocess.run([str(py), str(ROOT / "stages/06-soft/run.py"),
                           str(ROOT / "Fixtures/06-soft/real-lines"), "--label", backend],
                          capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env={**os.environ}, cwd=ROOT)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-800:])
    rep = json.loads(proc.stdout)
    keep = [{k: x.get(k) for k in ("file", "line", "label", "probabilities", "confidence",
                                   "backend", "model")}
            for x in rep["findings"] if x["check"] == "soft.label" and "skipped" not in x]
    skipped = sum(1 for x in rep["findings"] if x["check"] == "soft.label" and "skipped" in x)
    out = HERE / "model-labels" / f"{backend.replace('-cli', '')}-guided.json"
    out.write_text(json.dumps({"source": f"run_guided.py {backend}", "skipped": skipped,
                               "labels": keep}, indent=1), encoding="utf-8")
    print(f"{backend}: {len(keep)} labels, {skipped} skipped -> {out.name}")
    return out


def main(argv=None) -> int:
    backends = (argv or sys.argv[1:]) or ["jev"]
    backup = DATA.with_suffix(".yaml.d3-backup")
    shutil.copy2(DATA, backup)
    try:
        doc = yaml.safe_load(DATA.read_text("utf-8"))
        DATA.write_text(yaml.safe_dump(guided_doc(doc), sort_keys=False, allow_unicode=True,
                                       width=100), encoding="utf-8")
        for b in backends:
            run(b)
    finally:
        shutil.copy2(backup, DATA)
        backup.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
