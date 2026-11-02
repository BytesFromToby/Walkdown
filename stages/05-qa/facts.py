"""What the check of the run reads: a run folder, as facts. Spec: specs/qa.SPEC.md, facts.

The check reads the run folder and nothing else: the record (`data/run.json`), each step's saved output
(`data/<step>.json`) and messages (`data/<step>.notes.txt`), and a model step's call log
(`data/<step>.calls.jsonl`). It never reads the audited repository and writes nothing here.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
import layout  # noqa: E402
import pipeline  # noqa: E402
import record  # noqa: E402
import stagelist  # noqa: E402
import steperror  # noqa: E402


class NotARun(Exception):
    """A folder the check cannot read: not a run folder, or made before this version of Walkdown."""


@dataclass
class Facts:
    steps: list                                      # the record's steps, intake first: stage, ok, started, finished, error
    stamps: dict                                     # {stage: validate.Stamp} from the record
    stop: dict | None = None                         # `record.stop_of`: where the run stopped as asked, or None
    not_started: list = field(default_factory=list)  # the record's chosen steps that were not started
    chosen: list = field(default_factory=list)       # the model reads the record says were chosen, by step name
    dropped: list = field(default_factory=list)      # the reads an earlier command chose and `continue` left out
    backends: dict = field(default_factory=dict)     # {step: the backend chosen} for the reads in `chosen` and `dropped`
    reports: dict = field(default_factory=dict)      # {stage: report} for each saved output that reads
    unreadable: set = field(default_factory=set)     # stages whose saved output is there and does not read
    notes: dict = field(default_factory=dict)        # {stage: the step's own notes (`pipeline.own_notes`)}
    errors: dict = field(default_factory=dict)       # {stage: (error type, missing import)} for a step that failed
    logs: dict = field(default_factory=dict)         # {stage: lines in its call log} for each log that is there


def call_log_lines(path: Path) -> int | None:
    """How many lines of a call log read as JSON, or None when the file is not there or holds a line that does not."""
    try:
        lines = [x for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
        for x in lines:
            json.loads(x)
    except (OSError, ValueError):
        return None
    return len(lines)


def load(run_dir) -> Facts:
    """The facts of a run folder. NotARun when it has no `data/` or its record is missing or of another format."""
    run_dir = Path(run_dir)
    data = layout.data_dir(run_dir)
    if not data.is_dir():
        raise NotARun(f"not a run folder (no data/): {run_dir}")
    rec = record.read(run_dir)
    if rec is None:
        raise NotARun("this run was made before this version of Walkdown, so it is not checked; "
                      "audit the repository again")
    facts = Facts(steps=rec.get("steps") or [], stamps=record.stamps_of(rec), stop=record.stop_of(rec),
                  not_started=rec.get("not_started") or [],
                  chosen=[s for s in stagelist.AI_STAGES if s in (rec.get("chosen") or [])],
                  dropped=[s for s in stagelist.AI_STAGES if s in (rec.get("dropped") or [])],
                  backends={k: v for k, v in (rec.get("backends") or {}).items() if isinstance(v, str)})
    rows = {s["stage"]: s for s in facts.steps}
    for stage in stagelist.STAGES:
        saved = data / f"{stage}.json"
        if saved.is_file():
            try:
                facts.reports[stage] = pipeline.read_report(saved)
            except (OSError, ValueError):
                facts.unreadable.add(stage)
        notes = data / f"{stage}.notes.txt"
        if notes.is_file():
            text = notes.read_text(encoding="utf-8", errors="replace")
            row = rows.get(stage)
            facts.notes[stage] = pipeline.own_notes(text, bool(row and row.get("ok")))
            if row is not None and not row.get("ok"):
                facts.errors[stage] = steperror.error_of(text)
        if stage in stagelist.AI_STAGES:
            lines = call_log_lines(data / layout.calls_file(stage))
            if lines is not None:
                facts.logs[stage] = lines
    return facts
