"""Run the stages once each into a run folder: the coded ones always, the AI ones when chosen.
Spec: specs/shared.SPEC.md, pipeline."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calllog  # noqa: E402
import coverlines  # noqa: E402
import layout  # noqa: E402
import secretmask  # noqa: E402
import stagenote  # noqa: E402
import steperror  # noqa: E402
import usage  # noqa: E402
# The stage list and the tables built from it live in `stagelist`; the names stay importable here.
from stagelist import (AI_ENV, AI_OPTION, AI_STAGES, FOLDER_STAGES, INTAKE, QA, STAGES,  # noqa: E402,F401
                       load_stage_list, position, stage_folder)
from options import OFF, REFUSAL, REFUSED, REFUSED_ENV, ai_chosen, refusal  # noqa: E402,F401


def stages_to_run(soft: dict | None = None, environ=None) -> list[str]:
    """The folder stages a run runs, in order: the coded ones always, an AI stage only when chosen,
    and Pinpoint only after Sweep (it reads Sweep's report)."""
    out = [s for s in FOLDER_STAGES if s not in AI_STAGES or ai_chosen(s, soft, environ)]
    if "04-pinpoint" in out and "03-sweep" not in out:
        out.remove("04-pinpoint")
    return out


SWEEP_NO_ANSWER = "sweep-no-answer"  # the record's reason for a chosen Pinpoint that was not started (M9)


def read_report(path) -> dict:
    """A step's saved output as a report; ValueError when it is not a document with a list of `findings`, each a dict with a
    `check` (a saved `[]` or `{}`, a number or an empty object among the findings, or text cut off by a full disk is valid or
    nearly valid JSON and is not one). A `coverage` it carries (M9 slice C) must be a list of lines, each an object with
    a list of check ids, a unit, and four whole counts (`coverlines.valid`); one that is not is a report that cannot be read, the
    same as bad findings, so the step has the one gap (`output-unreadable`) and no coverage line is taken from it. The one
    exception is an object under that name: `02.2-reader` wrote its counts there before slice C, so a run made before is read as
    a report with no lines. A `usage` it carries (M1 slice A) must be an object whose counts are whole numbers
    (`usage.valid`); one that is not (a word, a count that is a bool or a float or below zero) is a report that cannot be read
    in the same way. The check of the run, the report stage, and the comparison of two runs read a saved
    output by this one test, so an output is a report to all of them or to none."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    findings = doc.get("findings") if isinstance(doc, dict) else None
    if not isinstance(findings, list) or not all(isinstance(f, dict) and isinstance(f.get("check"), str) for f in findings):
        raise ValueError("not a report")
    saved = doc.get("coverage", [])
    if not (isinstance(saved, dict) or coverlines.valid(saved)):
        raise ValueError("not a report: its coverage is not a list of lines")
    if "usage" in doc and not usage.valid(doc["usage"]):
        raise ValueError("not a report: its usage is not counts of whole numbers")
    return doc


def first_finding(report) -> dict:
    """The first finding of a step's report (the inventory's pin), or an empty one when the report has none or is not a
    report: a step can print `{"findings": []}` and end well, and the runner must still name and file the run."""
    findings = (report or {}).get("findings") if isinstance(report, dict) else None
    return findings[0] if isinstance(findings, list) and findings and isinstance(findings[0], dict) else {}


def sweep_got_nothing(run_dir) -> bool:
    """Whether the run's saved Sweep report is one in which no passage got an answer (`calllog.got_nothing`). A run
    folder with no Sweep report, or one that cannot be read, is not."""
    try:
        report = read_report(Path(run_dir) / "03-sweep.json")
    except (OSError, ValueError):
        return False
    return calllog.got_nothing(report)


def mask_saved_reader(run_dir) -> None:
    """`data/02.2-reader.json` with the lines the secret scan flagged masked (`secretmask.mask_reader`). `02.2-reader` runs before
    the scan, and `02.5-capability` needs the hidden words to say a phrase hit is inside them, so this comes once that step has
    read them; no later step does. With nothing flagged the file stays as the step printed it. An output that is not a report is
    a gap the check of the run names, and it is left as it is."""
    saved = Path(run_dir) / "02.2-reader.json"
    try:
        reader, phrases = read_report(saved), read_report(Path(run_dir) / "02.4-phrases.json")
    except (OSError, ValueError):
        return
    if secretmask.mask_reader(reader, phrases):
        saved.write_text(json.dumps(reader, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# The last step that reads the words of the steps before the scan: its token cost reads a description's length, and it reads the
# hook commands `02.5-capability` kept. Sweep and Pinpoint read the inventory's file lists and the files themselves; Pinpoint's own
# answers quote lines, so its report is masked when it has run.
LAST_TO_READ_WORDS = "02.6-builder"
QUOTES_A_MODEL = "04-pinpoint"


def _save_if_changed(path: Path, doc, before: str) -> None:
    """A saved output rewritten when the mask changed it, whole or not at all (a full disk leaves no half), with the ending the
    file had."""
    now = json.dumps(doc, ensure_ascii=False, indent=1)
    if now == before:
        return
    tail = "\n" if path.read_text(encoding="utf-8").endswith("\n") else ""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(now + tail, encoding="utf-8")
    tmp.replace(path)


def mask_saved(run_dir) -> None:
    """Every saved output with the lines the secret scan flagged masked (`secretmask.mask_reports`), once the steps that read the
    words have read them, or a step failed and nothing will. A file that is not a report is a gap the check of the run names, and it
    is left as it is; with nothing flagged each stays as the step printed it. `data/normalized/` is the file's own text and stays."""
    run_dir = Path(run_dir)
    named = {stage: run_dir / f"{stage}.json" for stage in (secretmask.INVENTORY, secretmask.READ, secretmask.GRAPH, secretmask.PHRASES,
                                                            secretmask.CAPABILITY, secretmask.BUILDER, secretmask.PINPOINT)}
    reports, side, before = {}, [], {}
    for stage, path in named.items():
        try:
            reports[stage] = read_report(path)
        except (OSError, ValueError):
            continue
        before[path] = json.dumps(reports[stage], ensure_ascii=False, indent=1)
    if secretmask.PHRASES not in reports:
        return
    kept = run_dir / "capability.json"
    try:
        side.append(read_report(kept))
    except (OSError, ValueError):
        kept = None
    else:
        before[kept] = json.dumps(side[0], ensure_ascii=False, indent=1)
    graph_path = run_dir / "graph.json"
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        graph = None
    secretmask.mask_reports(reports, *side)
    for stage, path in named.items():
        if stage in reports:
            _save_if_changed(path, reports[stage], before[path])
    if kept is not None:
        _save_if_changed(kept, side[0], before[kept])
    if isinstance(graph, dict):
        saved = json.dumps(graph, ensure_ascii=False, indent=1)
        secretmask.mask_edges(graph, secretmask.secrets_of(reports[secretmask.PHRASES]))
        _save_if_changed(graph_path, graph, saved)


def cut_at(steps: list[str], until: str | None) -> tuple[list[str], list[str]]:
    """(to run, left out) for `--until`: the steps through the named one, in the list's order, and those
    after it. With no `until`, every step is to run. Intake (`until` its name) leaves every step out."""
    if until is None:
        return list(steps), []
    cut = position(until)
    return ([s for s in steps if position(s) <= cut], [s for s in steps if position(s) > cut])


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


NOTE = "note: "


def own_notes(text: str, finished: bool) -> list[str]:
    """The lines of a step's messages that the check of the run and the pages may use: the lines the step wrote as its
    own notes (`note: ...` from the first column, the prefix taken off; `stagenote.note` writes each on one line), and none
    at all from a step that did not finish. Anything else on a step's stderr is a library's words or an error's message,
    which can repeat text from the audited repository or a model's words; it stays in `data/<step>.notes.txt`. A line
    that is indented, or that holds `note: ` after other words, is not a note."""
    if not finished:
        return []
    return [line[len(NOTE):] for line in text.splitlines() if line.startswith(NOTE)]


def _args(stage: str, input_dir: Path, run_dir: Path, soft: dict | None = None,
          alone: bool = False, input_only: bool = False) -> list[str]:
    """How a stage is run. `alone`: as an earlier step for a stage that runs on its own (the grader,
    a test; `stages/_shared/earlier.py`): the same arguments with no `--out` for the steps that only
    write side files, and no `--normalized` (`02.2-reader`'s text copy), exactly what the stages that ran
    their own earlier steps always did. `input_only`: an AI stage told to write what it would send and
    stop (`--input-only`)."""
    only = ["--input-only"] if input_only else []
    inv = str(run_dir / "02.1-inventory.json")
    out = ["--out", str(run_dir)]
    side = [] if alone else out
    return {
        "02.1-inventory": [str(input_dir)],
        "02.2-reader": [str(input_dir), *side],
        "02.3-graph": [str(input_dir), "--inventory", inv, *out],
        "02.4-phrases": [str(input_dir), "--inventory", inv, *side,
                         *([] if alone else ["--normalized", str(run_dir / "normalized")])],  # `02.2-reader`'s extracted text
        "02.5-capability": [str(input_dir), "--reports", str(run_dir), *side],
        "02.6-builder": [str(input_dir), "--reports", str(run_dir)],
        # an AI stage gets its own option only when the person gave it; otherwise it reads the
        # environment variable that chose it
        "03-sweep": [str(input_dir), "--reports", str(run_dir), *out,
                     *(["--sweep", soft["sweep"]] if (soft or {}).get("sweep") else []), *only],
        "04-pinpoint": [str(input_dir), "--reports", str(run_dir), *out,
                        *(["--pinpoint", soft["pinpoint"]] if (soft or {}).get("pinpoint") else []), *only],
    }[stage]


def _spawn(cmd: list[str], show_progress: bool = False) -> subprocess.CompletedProcess:
    """A step as a subprocess, its output captured. With `show_progress`, the step's progress lines
    (`stagenote.is_progress`: `sweep: 25 of 431 passages done`) are written to this process's stderr as they come, so a long
    model read says it is working; they stay in the captured stderr too. Nothing else a step writes is shown.

    Two things `subprocess.run` does and this must too (M1 fix 3). The step's stderr is read to the end whatever happens to this
    process's own stderr: a failed write (a closed pipe, a console that is gone) is dropped for that line and the reading goes on,
    since a reader that stopped would let the step's stderr pipe fill and the step, and this call, wait for ever. And on any
    exception raised in the wait, the step is killed and waited for, so a model read does not go on running, and spending, with
    nobody waiting for it. On Windows the blocking read of the step's output is not interrupted by a Ctrl-C: the parent sees it when
    the read returns, which is when the step ends (normally because the console's Ctrl-C reached the step too), the same as with
    `subprocess.run`. So this does not shorten the wait for a step that ignores a Ctrl-C; it makes sure that an exception that does
    arrive leaves no step behind."""
    if not show_progress:
        return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8",
                             errors="replace")
    lines: list[str] = []

    def read_stderr():
        try:
            for line in child.stderr:
                lines.append(line)
                try:
                    stagenote.show_progress(line.rstrip("\r\n"))
                except (OSError, ValueError):
                    pass  # this process's stderr cannot be written to: the line is not shown, and the reading goes on
        except (OSError, ValueError):
            pass  # the pipe was closed under the reader (the step was killed)
    reader = threading.Thread(target=read_stderr, daemon=True)
    reader.start()
    try:
        out = child.stdout.read()
        child.wait()
        reader.join()
    except BaseException:  # as subprocess.run: KeyboardInterrupt too
        child.kill()
        child.wait()
        reader.join(5)  # the step is dead, so its stderr ends; if something else still holds the pipe, leave it open
        if not reader.is_alive():
            for pipe in (child.stdout, child.stderr):
                try:
                    pipe.close()
                except (AttributeError, OSError, ValueError):
                    pass
        raise
    child.stdout.close()
    child.stderr.close()
    return subprocess.CompletedProcess(cmd, child.returncode, out, "".join(lines))


def _run(stage: str, cmd: list[str], run_dir: Path, input_only: bool = False, alone: bool = False) -> StageRun:
    """One stage as a subprocess: its stdout saved as <run_dir>/<stage>.json once it parses, its
    stderr as <run_dir>/<stage>.notes.txt. A stage run with `--input-only` prints no report: nothing is
    parsed or saved, and exit 0 is all it needs to be ok. A stage of a run that crashed has the exit code and the
    error's type as its `error` (`exit 1: ValueError`); the end of its stderr can hold text from the audited repository or
    a model's words, so it stays in the notes file (M9 slice B). A stage run `alone` (for a stage
    that runs on its own: the grader's and the tests') has no record to keep it out of, and gives the end of its stderr,
    which is what the person running it needs."""
    started = _now()
    proc = _spawn(cmd, show_progress=stage in AI_STAGES and not input_only)
    notes = note_lines(proc.stderr)
    (run_dir / f"{stage}.notes.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        return StageRun(stage, False, started, notes=notes,
                        error=(f"exit {proc.returncode}: {proc.stderr.strip()[-500:]}" if alone
                               else steperror.exit_text(proc.returncode, proc.stderr)))
    if input_only:
        return StageRun(stage, True, started, _now(), None, notes)
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return StageRun(stage, False, started, notes=notes, error=f"invalid JSON: {e}")
    (run_dir / f"{stage}.json").write_text(proc.stdout, encoding="utf-8")
    return StageRun(stage, True, started, _now(), report, notes)


def intake_args(target, name: str | None = None, fresh: bool = False, keep: bool = False) -> list[str]:
    """What intake takes: the target as the person gave it, and the options that shape the copy."""
    return [str(target), *(["--name", name] if name else []), *(["--fresh"] if fresh else []),
            *(["--keep"] if keep else [])]


def run_intake(target, run_dir, stages_dir, python, name: str | None = None, fresh: bool = False,
               keep: bool = False) -> StageRun:
    """Intake, the first stage: gets the copy of the repository in place. Its one finding names
    the folder every later stage reads (`intake.source`). It runs before the run folder exists
    (the folder's name can come from its report), so `run_dir` is wherever its two files are
    written first."""
    stages_dir = Path(stages_dir)
    runner = stages_dir / stage_folder(INTAKE, stages_dir) / "run.py"
    cmd = [str(python), str(runner), *intake_args(target, name, fresh, keep)]
    return _run(INTAKE, cmd, Path(run_dir))


def run_stages(input_dir, run_dir, stages_dir, python, soft: dict | None = None,
               stages=None, alone: bool = False, not_started: list | None = None) -> list[StageRun]:
    """`soft`: the AI backends the user picked ({"sweep": "jev", "pinpoint": "claude-cli"}); an AI
    stage nobody chose does not run (`stages_to_run`). `stages`: a subset of FOLDER_STAGES to run,
    in order (default: `stages_to_run`, intake apart: `run_intake` runs first and names the
    folder; tools/baserates.py runs 1 and 4). `alone`: run them for a stage that runs on its own
    (`_args`). Pinpoint is not started after a Sweep in which no passage got an answer (M9): there is nothing to
    pinpoint, and it would fail the same way. `not_started`: a list the caller gives to learn of that;
    `{"stage", "why"}` is added to it."""
    input_dir, run_dir, stages_dir = Path(input_dir), Path(run_dir), Path(stages_dir)
    runs: list[StageRun] = []
    for stage in stages if stages is not None else stages_to_run(soft):  # an empty list runs nothing (`--until` intake)
        if stage == "04-pinpoint" and sweep_got_nothing(run_dir):
            if not_started is not None:
                not_started.append({"stage": stage, "why": SWEEP_NO_ANSWER})
            continue
        runner = stages_dir / stage_folder(stage, stages_dir) / "run.py"
        cmd = [str(python), str(runner), *_args(stage, input_dir, run_dir, soft, alone)]
        runs.append(_run(stage, cmd, run_dir, alone=alone))
        if stage == "02.5-capability" and not alone:  # that it failed changes nothing: the run reads no further
            mask_saved_reader(run_dir)
        if not alone and (stage in (LAST_TO_READ_WORDS, QUOTES_A_MODEL) or not runs[-1].ok):  # the same for a step that failed earlier
            mask_saved(run_dir)
        if not runs[-1].ok:
            break
    return runs


def run_qa(run_dir, stages_dir, python) -> StageRun:
    """The check of the run (`05-qa`, M9 slice B), after the steps, the validation, and the record: its report is saved as
    `<run_dir>/data/05-qa.json` and its messages as `05-qa.notes.txt`, as for any step. It is started with `--brief`, so a
    run with a gap has the brief of a held run (`brief.md`) written; it writes nothing else. The StageRun is not ok when
    the check itself crashed: there is then no `05-qa.json` and the report cannot be drawn."""
    stages_dir = Path(stages_dir)
    runner = stages_dir / stage_folder(QA, stages_dir) / "run.py"
    cmd = [str(python), str(runner), str(run_dir), "--brief"]
    return _run(QA, cmd, layout.data_dir(run_dir))


def gaps_in(report: dict | None) -> int:
    """How many gaps the check of the run found: its `qa.gap` findings."""
    return sum(1 for f in (report or {}).get("findings", []) if f.get("check") == "qa.gap")


def run_input_only(stage: str, input_dir, run_dir, stages_dir, python, soft: dict | None = None) -> StageRun:
    """An AI stage run to write what it would send and stop (`--input-only`; `--until` just before a model
    read): `<run_dir>/<stage>.input.jsonl` and its messages as `<stage>.notes.txt`. It makes no client, reads
    no key, sends nothing, and leaves no `<stage>.json`, so the run reads as one where the stage did not run.
    The StageRun is ok when the stage exited 0; its report is None."""
    input_dir, run_dir, stages_dir = Path(input_dir), Path(run_dir), Path(stages_dir)
    runner = stages_dir / stage_folder(stage, stages_dir) / "run.py"
    cmd = [str(python), str(runner), *_args(stage, input_dir, run_dir, soft, input_only=True)]
    return _run(stage, cmd, run_dir, input_only=True)
