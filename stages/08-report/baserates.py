"""Measured base rates of stage 4 patterns over the audited corpus. Spec: specs/baserates.SPEC.md.

    python stages/08-report/baserates.py <name>=<input_dir> [...] [--out baserates.json]

Runs stages 1 and 4 on each corpus repo and counts, per pattern, the lines it hit outside
human-facing files (the same lines the summary's points draw from). The table is a published fact about each
pattern, recomputed as the corpus grows; it judges no artifact (CHARTER, signal levels).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pipeline  # noqa: E402

DEFAULT_OUT = HERE / "baserates.json"
SKIP_AUDIENCES = ("human", "test-data")
# Levels name the base rate in words; they are bins of the count, never a judgment.
RARE, UNCOMMON, COMMON = "rare", "uncommon", "common"


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
        runs = pipeline.run_stages(input_dir, Path(tmp), HERE.parent, python,
                                   stages=["01-inventory", "04-phrases"])
    by = {r.stage: r for r in runs}
    for stage in ("01-inventory", "04-phrases"):
        if stage not in by or not by[stage].ok:
            err = by[stage].error if stage in by else "did not run"
            raise RuntimeError(f"{name}: stage {stage} failed: {err}")
    pin = by["01-inventory"].report["findings"][0]
    return {"name": name, "hash": pin.get("hash"), "lines": count(by["04-phrases"].report)}


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


def load(path=DEFAULT_OUT) -> dict | None:
    try:
        return json.loads(Path(path).read_text("utf-8"))
    except (OSError, ValueError):
        return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="baserates.py")
    ap.add_argument("corpus", nargs="+", help="name=input_dir, one per audited repo")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    repos = []
    for item in a.corpus:
        name, sep, path = item.partition("=")
        if not sep or not Path(path).is_dir():
            print(f"error: expected name=<folder>, got {item!r}", file=sys.stderr)
            return 2
        repos.append(measure(name, Path(path)))
    table = {"generated": dt.date.today().isoformat(),
             "what": "lines outside human-facing files hit by each stage 4 pattern, per "
                     "audited repo",
             "levels": {RARE: "no other audited repo", UNCOMMON: "one other audited repo",
                        COMMON: "two or more other audited repos"},
             "repos": repos}
    Path(a.out).write_text(json.dumps(table, indent=1) + "\n", encoding="utf-8")
    for r in repos:
        print(f"{r['name']} {str(r['hash'])[:7]}: {sum(r['lines'].values())} pattern-lines, "
              f"{len(r['lines'])} patterns", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
