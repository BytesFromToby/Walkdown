"""Run stages 1 to 6 once each into a run folder. Spec: specs/pipeline.SPEC.md."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

STAGES = ["01-inventory", "02-reader", "03-graph", "04-phrases", "05-capability", "06-soft"]


@dataclass
class StageRun:
    stage: str
    ok: bool
    started: str
    finished: str | None = None
    report: dict | None = None
    notes: list[str] = field(default_factory=list)
    error: str | None = None


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def note_lines(text: str) -> list[str]:
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("note: "):
            line = line[len("note: "):]
        out.append(line)
    return out


def _args(stage: str, input_dir: Path, run_dir: Path, soft: dict | None = None) -> list[str]:
    inv = str(run_dir / "01-inventory.json")
    out = ["--out", str(run_dir)]
    return {
        "01-inventory": [str(input_dir)],
        "02-reader": [str(input_dir), *out],
        "03-graph": [str(input_dir), "--inventory", inv, *out],
        "04-phrases": [str(input_dir), "--inventory", inv, *out],
        "05-capability": [str(input_dir), "--reports", str(run_dir), *out],
        "06-soft": [str(input_dir), "--reports", str(run_dir), *out,
                    *[x for k, v in (soft or {}).items() if v
                      for x in ((f"--{k}",) if v is True else (f"--{k}", v))]],
    }[stage]


def run_stages(input_dir, run_dir, stages_dir, python, soft: dict | None = None,
               stages=None) -> list[StageRun]:
    """`soft`: stage 6 backends the user picked ({"label": "jev", ...}); None or empty
    values leave stage 6 to its own defaults (environment, else packet only). `stages`:
    a subset of STAGES to run, in order (default all; baserates.py runs 1 and 4)."""
    input_dir, run_dir, stages_dir = Path(input_dir), Path(run_dir), Path(stages_dir)
    runs: list[StageRun] = []
    for stage in stages or STAGES:
        started = _now()
        cmd = [str(python), str(stages_dir / stage / "run.py"), *_args(stage, input_dir, run_dir, soft)]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        notes = note_lines(proc.stderr)
        (run_dir / f"{stage}.notes.txt").write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            runs.append(StageRun(stage, False, started, notes=notes,
                                 error=f"exit {proc.returncode}: {proc.stderr.strip()[-500:]}"))
            break
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            runs.append(StageRun(stage, False, started, notes=notes, error=f"invalid JSON: {e}"))
            break
        (run_dir / f"{stage}.json").write_text(proc.stdout, encoding="utf-8")
        runs.append(StageRun(stage, True, started, _now(), report, notes))
    return runs
