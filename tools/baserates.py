"""Measured base rates of stage 4 patterns over the audited corpus. Spec: specs/baserates.SPEC.md.

    python tools/baserates.py repo-1=<input_dir> [repo-2=<input_dir> ...] [--out baserates.json]

Runs the inventory and the phrase steps on each corpus repo and counts, per pattern, the lines it
hit outside human-facing files (the same lines the places to check draw from). The table is a
published fact about each pattern, recomputed as the corpus grows; it judges no artifact (CHARTER,
signal levels). `Library/` is public, so label each input neutrally (`repo-1`, `repo-2`, ...), never
with the repository's name.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STAGES = HERE.parent / "stages"
sys.path.insert(0, str(STAGES / "_shared"))

import pipeline  # noqa: E402
import rates  # noqa: E402

DEFAULT_OUT = rates.DEFAULT_PATH
SKIP_AUDIENCES = ("human", "test-data")
INVENTORY, PHRASES = "02.1-inventory", "02.4-phrases"


def count(report04: dict) -> dict:
    """{pattern id: lines hit} over phrase findings outside human-facing files."""
    lines: dict[str, set] = {}
    for f in report04.get("findings", []):
        if not str(f.get("check", "")).startswith("phrase.") or "skipped" in f:
            continue
        if f.get("audience") in SKIP_AUDIENCES:
            continue
        for p in f.get("patterns") or []:
            lines.setdefault(p, set()).add((f.get("file"), f.get("line")))
    return {p: len(v) for p, v in sorted(lines.items())}


def measure(name, input_dir, python=sys.executable) -> dict:
    with tempfile.TemporaryDirectory(prefix="walkdown-baserates-") as tmp:
        runs = pipeline.run_stages(input_dir, Path(tmp), STAGES, python, stages=[INVENTORY, PHRASES])
    by = {r.stage: r for r in runs}
    for stage in (INVENTORY, PHRASES):
        if stage not in by or not by[stage].ok:
            err = by[stage].error if stage in by else "did not run"
            raise RuntimeError(f"{name}: stage {stage} failed: {err}")
    pin = by[INVENTORY].report["findings"][0]
    return {"name": name, "hash": pin.get("hash"), "lines": count(by[PHRASES].report)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="baserates.py")
    ap.add_argument("corpus", nargs="+",
                    help="label=input_dir, one per audited repo. Label each one neutrally (repo-1, "
                         "repo-2, ...): the table is written into the public Library, so a real "
                         "repository name stays out of it")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    repos = []
    for item in a.corpus:
        name, sep, path = item.partition("=")
        if not sep or not Path(path).is_dir():
            print(f"error: expected label=<folder>, got {item!r}", file=sys.stderr)
            return 2
        repos.append(measure(name, Path(path)))
    table = {"generated": dt.date.today().isoformat(),
             "what": "lines outside human-facing files hit by each stage 4 pattern, per "
                     "audited repo",
             "levels": rates.LEVELS,
             "repos": repos}
    Path(a.out).write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8")
    for r in repos:
        print(f"{r['name']} {str(r['hash'])[:7]}: {sum(r['lines'].values())} pattern-lines, "
              f"{len(r['lines'])} patterns", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
