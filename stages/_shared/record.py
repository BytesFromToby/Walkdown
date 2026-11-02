"""The record of how a run went, as data. Spec: specs/shared.SPEC.md, record.

The runner writes it into the run folder (`data/run.json`) after the steps and the validation; the
report stage reads it to write LOG.md and the reports. It holds what no stage output holds: each step's
start, finish, and result, the validation stamps, and the options the reports depend on (the expected
context and the target hosts). Nothing is read back out of LOG.md's text (restructure step 7, notes F1).
"""
from __future__ import annotations

import datetime as dt
import functools
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import layout  # noqa: E402
import stagelist  # noqa: E402
from validate import Stamp  # noqa: E402

# The shape of the data a run holds, not only of this file. 2 since restructure step 7b (2026-10-29): the
# data inside a run named its stages by number before, and names them now (specs/shared.SPEC.md, record, History).
# O3 added keys (`version`, `code`, `until`, `prepared`, `continued`) and kept 2: a record without `until` is a run
# that went through, so every run made before reads as it did. M9 slice A added `not_started` the same way.
# 3 since M9 slice B (2026-10-30): a run has a new output, `data/05-qa.json`, and section 7 and the lists of steps that did
# not work are drawn from it instead of gathered by the report stage, so a run made before has no such file and is not
# re-rendered or compared (owner, 2026-10-30; `made_before`).
FORMAT = 3
LOG = "LOG.md"


def write(run_dir, steps, stamps: dict, context: int, hosts: list, finished: str, version: str | None = None,
         until: str | None = None, prepared: dict | None = None, continued=(), code: str | None = None,
         not_started=(), chosen=(), dropped=(), backends=None) -> Path:
    """Save the record. `steps`: the `pipeline.StageRun`s in run order (intake first); `stamps`:
    {stage: Stamp} (empty for a run made without validation); `finished`: when the run ended (UTC);
    `version`: the Walkdown that made it (`toolversion.tool_version`); `code`: a hash of its code
    (`toolversion.code_hash`), which `continue` checks; `until`: the step the run stopped
    after, only for a run that stopped as asked; `prepared`: `{"stage", "items", "backend"}` for the AI step
    whose input file was written and not sent; `continued`: `{"after", "at"}` for each time the run went on;
    `not_started`: `{"stage", "why"}` for a chosen AI step that was not started because the step before it
    got no answer (M9: Pinpoint after a Sweep in which no passage got an answer); `chosen`: the model reads this
    command chose, by step name (M9 slice B), so a chosen read that never started can be told from one nobody chose;
    `dropped`: the reads an earlier command chose that `continue` left out (it is not run, and the person is told);
    `backends`: {step: the backend chosen} for the reads in `chosen` and `dropped`, which a command to go on needs."""
    doc = {"format": FORMAT, "finished": finished, "context": context, "hosts": list(hosts),
           "steps": [{"stage": s.stage, "ok": s.ok, "started": s.started, "finished": s.finished,
                      "error": s.error} for s in steps],
           "stamps": {stage: st.to_dict() for stage, st in stamps.items()}}
    for key, value in (("version", version), ("code", code), ("until", until), ("prepared", prepared)):
        if value:
            doc[key] = value
    if continued:
        doc["continued"] = [dict(c) for c in continued]
    if not_started:
        doc["not_started"] = [dict(n) for n in not_started]
    if chosen:
        doc["chosen"] = list(chosen)
    if dropped:
        doc["dropped"] = list(dropped)
    if backends:
        doc["backends"] = dict(backends)
    path = layout.data_dir(run_dir) / layout.RECORD
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return path


def amend(run_dir, **keys) -> dict:
    """Add keys to the record already written (the check of the run's times, a hold, a release). A key whose value is
    None is taken out. Returns the record. Only the runner calls it, after the steps, the validation, and the record."""
    path = layout.data_dir(run_dir) / layout.RECORD
    doc = json.loads(path.read_text(encoding="utf-8"))
    for key, value in keys.items():
        if value is None:
            doc.pop(key, None)
        else:
            doc[key] = value
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return doc


def hold(run_dir, gaps: int, by: str) -> dict:
    """The check of the run found `gaps` gaps: the run is held, and no report is written (M9 slice B). Any earlier release
    is gone: the run was checked again."""
    return amend(run_dir, held={"by": by, "gaps": gaps}, released=None)


def release(run_dir, at: str) -> dict:
    """`continue` on a held run: the hold becomes a release with the time, and the report is written with what the run
    has. Nothing else changes."""
    held = held_of(read(run_dir)) or {}
    return amend(run_dir, held=None, released={**held, "at": at})


def held_of(doc: dict | None) -> dict | None:
    """What the record says of a hold, `{"by": the step, "gaps": how many}`, or None for a run that was not held (or was
    held and released)."""
    held = (doc or {}).get("held")
    return held if isinstance(held, dict) else None


def read_any(run_dir) -> dict | None:
    """The record whatever its format, or None when the run has none or it cannot be read. Only what is the
    same in every format may be taken from it: the times that order runs (`times`). Anything else goes
    through `read`."""
    try:
        doc = json.loads((layout.data_dir(run_dir) / layout.RECORD).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return doc if isinstance(doc, dict) else None


def read(run_dir) -> dict | None:
    """The record, or None when the run has none, it cannot be read, or its format is not the current one
    (a run made before this version)."""
    doc = read_any(run_dir)
    return doc if doc is not None and doc.get("format") == FORMAT else None


def made_before(run_dir) -> bool:
    """A run made before this version of Walkdown: it has no readable record, or its record is of an older
    format (the data inside the run changed shape since). The one rule for every reader of a run that is not
    the one being made: it is re-rendered or compared only when this is False. That covers a run with the
    stage outputs at the top (before 2026-10-02), one with the old stage names (before step 1), one made
    between step 1 and step 7 (no record), and one made between step 7 and step 7b (a format 1 record).
    Which run is earlier (`earlier_runs`) and the marks carried from it do not ask: they work on any run."""
    return read(run_dir) is None


def stamps_of(doc: dict) -> dict:
    """{stage: Stamp} from a record."""
    return {stage: Stamp.from_dict(d) for stage, d in (doc.get("stamps") or {}).items()}


def stop_of(doc: dict | None) -> dict | None:
    """What the record says of a stop: `{"after": the step, "prepared": the AI step whose input was written
    or None}`, or None for a run that went through (no `until`, or one that names no step of the list)."""
    until = (doc or {}).get("until")
    if until not in stagelist.STAGES:
        return None
    return {"after": until, "prepared": doc.get("prepared") or None}


def stopped_early(run_dir) -> bool:
    """A run that stopped as asked before its last coded step: one that cannot be compared with another run,
    since the steps the comparison reads did not all run. A run stopped after the last coded step, or one that
    went through, is compared as usual."""
    stop = stop_of(read(run_dir))
    return stop is not None and stagelist.position(stop["after"]) < stagelist.position(stagelist.CODED[-1])


# ---------------------------------------------------------------- which run came before this one

def _epoch(text) -> float | None:
    try:
        return dt.datetime.fromisoformat(str(text)).timestamp()
    except ValueError:
        return None


def _when(run_dir) -> tuple[float, float, bool]:
    """(started, finished, from the record) of a run, in seconds since the epoch. The record of any format
    counts: a run made by an older version is still ordered by the times it recorded."""
    rec = read_any(run_dir)
    if rec:
        steps = rec.get("steps") or []
        started = _epoch(steps[0].get("started")) if steps and isinstance(steps[0], dict) else None
        finished = _epoch(rec.get("finished"))
        if finished is not None or started is not None:
            finished = started if finished is None else finished
            return (finished if started is None else started), finished, True
    try:
        m = (layout.report_dir(run_dir) / LOG).stat().st_mtime
    except OSError:
        return 0.0, 0.0, False
    return m, m, False


def times(run_dir) -> tuple[float, float]:
    """(started, finished) of a run, as seconds since the epoch. From its record: the first step's start
    (intake) and the finish the runner wrote. For a run without one (made before this version): its LOG.md's
    modification time for both. (0, 0) when nothing says."""
    return _when(run_dir)[:2]


_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def folder_date(run_dir) -> str:
    """The date a run folder's name starts with (`YYYY-MM-DD_...`); for a name without one, the date of the
    run's own time ('' when it has none)."""
    name = Path(run_dir).name
    if _DATE.match(name):
        return name[:10]
    when = _when(run_dir)[1]
    return dt.datetime.fromtimestamp(when).date().isoformat() if when else ""


def _name_key(name: str) -> tuple[str, int]:
    """A run folder's name for ordering: the name without its `-2`, `-3`, ... suffix, then the suffix as a
    number (no suffix is 1), so `-2` sorts before `-10`."""
    m = re.fullmatch(r"(.*?)(?:-(\d+))?", name)
    return m.group(1), int(m.group(2) or 1)


def earlier_runs(run_dir) -> list[Path]:
    """The other runs of the same repository that finished before this one started, newest first. The one rule
    for "an earlier run" (restructure step 7, notes F2): the comparison with the previous run (`changes.md`, the
    brief, the details page) and the marks carried from an earlier run all read it.

    Runs are ordered by time, not by name: two runs on one day with different commits have names that sort by
    commit hash. Two runs with records are ordered by the times in them. A run without one (made before this
    version) is ordered first by the date in its folder name, because its LOG.md's time moves when the run is
    rendered again; its LOG.md's time counts only against a run of the same date. The folder name (a `-2` suffix
    counted as a number) breaks a tie. A name that starts with a dot is a run in progress and is never one.
    This run is never one of its own earlier runs, and neither is a later one, so re-rendering an old run never
    compares it with a newer one."""
    run_dir = Path(run_dir).resolve()
    try:
        sib = [p for p in run_dir.parent.iterdir()
               if p.is_dir() and not p.name.startswith(".") and p != run_dir]
    except OSError:
        return []
    me = _Run(run_dir)
    return [r.path for r in sorted((r for r in map(_Run, sib) if r.before(me)),
                                   key=functools.cmp_to_key(_order), reverse=True)]


class _Run:
    """A run folder with what ordering it needs."""

    def __init__(self, path: Path):
        self.path = path
        self.started, self.finished, self.recorded = _when(path)
        self.date = folder_date(path)
        self.name = _name_key(path.name)

    def point(self) -> float:
        """The one time compared with a run that has no record: a record's start, or the log's time."""
        return self.started if self.recorded else self.finished

    def before(self, other: "_Run") -> bool:
        """This run came before `other`. Both recorded: it finished before the other started. Otherwise, the
        folder dates decide, and on the same date the record's start (or the log's time) is compared; the name
        breaks a tie."""
        if self.recorded and other.recorded:
            return (self.finished, self.name) < (other.started, other.name)
        if self.date != other.date:
            return self.date < other.date
        return (self.point(), self.name) < (other.point(), other.name)


def _order(a: _Run, b: _Run) -> int:
    """For sorting earlier runs: two recorded runs by their finish; otherwise as `before`."""
    if a.recorded and b.recorded:
        ka, kb = (a.finished, a.name), (b.finished, b.name)
        return -1 if ka < kb else 1 if kb < ka else 0
    return -1 if a.before(b) else 1 if b.before(a) else 0


def previous_run(run_dir) -> Path | None:
    """The newest earlier run that has a LOG.md (a finished run) and was not stopped before its coded steps
    were all done (`stopped_early`: the next full run is compared with the last run that went through),
    or None when there is none."""
    for p in earlier_runs(run_dir):
        if (p / LOG).is_file() and not stopped_early(p):
            return p
    return None
