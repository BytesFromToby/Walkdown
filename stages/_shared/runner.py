"""The runner: from a target to a run folder. Spec: specs/shared.SPEC.md, runner.

    python stages/_shared/runner.py <target> [--name N] [--fresh | --keep] [--sweep B] [--pinpoint B] [--reads [M]]
                                    [--until STEP] [--revalidate] [--context N] [--hosts a,b]
                                    [--repo R] [--results DIR] [--date D] [--no-validate]
    python stages/_shared/runner.py continue <run folder> [--sweep B] [--pinpoint B] [--reads [M]] [--until STEP]
                                    [--revalidate] [--context N] [--hosts a,b] [--no-validate]

It runs the steps in `stages/stages.json` order: intake first (it gets the copy and names the run),
then the coded steps and the AI stages a person chose, each as a subprocess; then the validation (the
grader's stamps); then it writes the run's record (`data/run.json`), has the check of the run (`05-qa`) read the
saved run, and starts the report stage on the run folder unless the check found a gap, in which case the run is held:
the record gains `held`, no report is written, and the brief the check wrote is the answer (exit 1). It writes no report
and reads none. `walkdown.py` is a router over this module (restructure
step 7, notes F1, F3, O1): it parses the options once, calls `audit`, and prints the brief file the
report stage wrote. Run alone it prints the run folder's path.

`--until STEP` stops the run after a step (parked item O3); `continue` (`resume`) goes on in the same run
folder: the steps after the stop, the validation of those, the record rewritten, the check of the run again, and the
report stage. `continue` on a held run runs no step: it releases the hold and writes the report with what the run has.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import common_lines  # noqa: E402
import layout  # noqa: E402
import options  # noqa: E402
import pipeline  # noqa: E402
import record  # noqa: E402
import stagelist  # noqa: E402
import toolversion  # noqa: E402
import validate  # noqa: E402

STAGES = HERE.parent  # stages/
ROOT = STAGES.parent
SWEEP, PINPOINT = stagelist.AI_STAGES[0], stagelist.AI_STAGES[-1]
INVENTORY = stagelist.CODED[0]
STOPPED = re.compile(r"(\d{4}-\d{2}-\d{2})_stopped(?:-\d+)?")  # a run that stopped before it had a pin


def free_name(parent: Path, base: str) -> Path:
    """`parent/base`, else `parent/base-2`, `-3`, ...: the first name nothing is using."""
    p, i = parent / base, 2
    while p.exists():
        p, i = parent / f"{base}-{i}", i + 1
    return p


def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def soft_grade_env(a) -> dict:
    """The AI choice the grader's stamp runs with, so Sweep's stamp measures the backend the run
    used (Pinpoint has no fixture set, so its choice is not passed). It is the choice the Sweep step itself reads
    (`options.ai_choice`: the option, else the variable at a run), as the backend and the model the person typed it, since
    the stamp is cached by what it is run with. A `claude-cli` that names no model runs `WALKDOWN_SOFT_CLAUDE_MODEL`, which
    is part of the choice too: another model is another stamp."""
    choice = options.ai_choice(SWEEP, soft_of(a), options.ai_environ(a))
    if not choice:
        return {}
    env = {stagelist.AI_ENV[SWEEP]: choice}
    try:
        backend, model = options.parse_choice(SWEEP, choice, "--sweep")
    except ValueError:  # `options.check` refuses these before a run gets here
        return env
    if backend == "claude-cli" and model is None and os.environ.get(options.MODEL_ENV):
        env[options.MODEL_ENV] = os.environ[options.MODEL_ENV]
    return env


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def soft_of(a) -> dict:
    """The AI choices on the parsed options: {option name: its value}."""
    return {option: getattr(a, option, None) for option in stagelist.AI_OPTION.values()}


def prepare_next(left, runs, input_dir, data: Path, py: str, soft: dict, environ=None, not_started=None):
    """When a stop leaves a chosen AI step next (`left`: the steps the stop left out, in order), that step
    writes what it would send and stops (`--input-only`). Returns (the step as a failure to record, or None;
    the record's `prepared` entry, or None). Nothing is prepared after a step that failed. `environ` is the
    environment that can choose the step (`continue` passes an empty one). A Pinpoint that follows a Sweep in which no
    passage got an answer is not prepared, as it would not be run: no input file is written, and `{"stage", "why"}` is
    added to `not_started`, the list the caller gives (the same hold as `pipeline.run_stages`)."""
    if not left or left[0] not in stagelist.AI_STAGES or not all(r.ok for r in runs):
        return None, None
    stage = left[0]
    if stage == PINPOINT and pipeline.sweep_got_nothing(data):
        if not_started is not None:
            not_started.append({"stage": stage, "why": pipeline.SWEEP_NO_ANSWER})
        return None, None
    step = pipeline.run_input_only(stage, input_dir, data, STAGES, py, soft)
    path = data / layout.input_file(stage)
    if step.ok and not path.is_file():
        step = pipeline.StageRun(stage, False, step.started, notes=step.notes, error="no input file written")
    if not step.ok:
        return step, None
    items = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    return None, {"stage": stage, "items": items, "backend": options.ai_choice(stage, soft, environ)}


NOT_STARTED_NOTE = {pipeline.SWEEP_NO_ANSWER: "no passage got an answer from the step \"{plain}\", so there is nothing to pinpoint"}


def without_held(left, not_started) -> list[str]:
    """The steps a stop left out, less those that were held and so have nothing left to run: a run whose only step
    after the stop is a held Pinpoint went all the way, and is not a stop."""
    held = {n["stage"] for n in not_started}
    return [s for s in left if s not in held]


def say_not_started(not_started) -> None:
    """On the terminal, why a chosen AI step was not started (M9)."""
    for held in not_started:
        why = NOT_STARTED_NOTE[held["why"]].format(plain=stagelist.PLAIN[SWEEP])
        print(f'note: the step "{stagelist.PLAIN[held["stage"]]}" did not run: {why}', file=sys.stderr)


def say_failed(steps) -> list:
    """On the terminal, the first step that failed: its name and its exit code and error's type (never the end of its
    messages: those are in `data/<step>.notes.txt`). Returns the failed steps."""
    failed = [r for r in steps if not r.ok]
    if failed:
        print(f"stage {failed[0].stage} failed: {failed[0].error}", file=sys.stderr)
    return failed


def run_report(py: str, run_dir: Path, extra=()) -> int:
    """Start the report stage on the run folder; its exit code. `extra`: more arguments for it."""
    report = STAGES / stagelist.stage_folder(stagelist.REPORT) / "run.py"
    return subprocess.run([py, str(report), str(run_dir), *extra], stdout=subprocess.PIPE, text=True,
                          encoding="utf-8", cwd=ROOT).returncode


def report_stage(py: str, run_dir: Path, steps) -> tuple[Path, int]:
    """Start the report stage on the run folder; name the first step that failed. The exit code is the report
    stage's unless a step failed."""
    code = run_report(py, run_dir)
    if say_failed(steps):
        return run_dir, code or 1
    return run_dir, code


def clear_report(run_dir: Path, keep_check: bool = False) -> None:
    """Take out what the report stage and the check of the run write for a run: the pages, `changes.md`, `LOG.md`,
    `brief.md`, `data/limits.md`, and, unless `keep_check`, `data/05-qa.json`. The reader's `marks.json` stays. A run
    that is held, or is being gone on with, has none of these, so a page or a brief from an earlier pass is never read
    as this run's (a check that crashes in the middle of a `continue` leaves a folder with no page)."""
    for name in (*layout.REPORTS, *layout.RETIRED, layout.CHANGES, layout.BRIEF, record.LOG):
        (run_dir / name).unlink(missing_ok=True)
    data = layout.data_dir(run_dir)
    (data / layout.LIMITS).unlink(missing_ok=True)
    if not keep_check:
        (data / f"{stagelist.QA}.json").unlink(missing_ok=True)


def check_then_report(py: str, run_dir: Path, steps) -> tuple[Path, int]:
    """The check of the run (`05-qa`) on the saved run, then the report stage unless the check found a gap (M9 slice B).
    The record was written first, so the check reads it. A run with a gap is held: the check wrote the brief
    (`brief.md`, Walkdown's own words, the two ways on), the record gains `held`, no report is written, and the exit code is
    1; the first step that failed is named on the terminal as for a run that was reported. A check that crashed leaves no
    `data/05-qa.json`, so there is nothing to draw the report from: the run did not finish."""
    qa = pipeline.run_qa(run_dir, STAGES, py)
    if not qa.ok:
        print(f"stage {qa.stage} failed: {qa.error}", file=sys.stderr)
        return run_dir, 1
    record.amend(run_dir, qa={"started": qa.started, "finished": qa.finished})
    gaps = pipeline.gaps_in(qa.report)
    if not gaps:
        return report_stage(py, run_dir, steps)
    record.hold(run_dir, gaps, stagelist.QA)
    say_failed(steps)
    return run_dir, 1


def audit(a, python=None) -> tuple[Path | None, int]:
    """Run an audit from parsed options (`options.add_run_options`, already checked by
    `options.check`). Returns the run folder (None when the run never got a folder: intake could not
    get the copy, or the results folder would sit inside it) and the exit code: 0 when every step
    ran, 1 when a step failed or the check of the run found a gap (a step that failed is a gap, so the run is held and no
    report is written until `continue`), 2 for a target intake
    cannot use or a results folder inside the input. With `--until` the run stops after that step (when a
    step of the list comes after it): the steps after it do not run, and an AI step that would come next
    writes its input file and stops."""
    py = str(python or sys.executable)
    date = getattr(a, "date", None) or dt.date.today().isoformat()
    # absolute from here on: the report stage starts in Walkdown's own folder, so a relative path would name
    # another folder there
    results = Path(getattr(a, "results", None) or ROOT / "RepoResults").resolve()
    with tempfile.TemporaryDirectory(prefix="walkdown-intake-") as held:
        # intake first: it names the folder to audit, and the run's name can come from it, so its
        # two files wait here until the run folder exists
        got = pipeline.run_intake(a.target, held, STAGES, py, a.name, a.fresh, a.keep)
        said = Path(held, f"{got.stage}.notes.txt")
        if said.is_file():  # what the person sees on the terminal: the notes, or the error
            sys.stderr.write(said.read_text(encoding="utf-8"))
        if not got.ok:
            if not said.is_file() or not said.read_text(encoding="utf-8").strip():
                print(f"error: {got.stage} failed: {got.error}", file=sys.stderr)
            return None, 2
        held_files = {p.name: p.read_bytes() for p in Path(held).iterdir()}
    source = got.report["findings"][0]
    inp = Path(source["folder"])
    repo = getattr(a, "repo", None) or source["name"]

    repo_dir = results / repo
    if inside(repo_dir, inp):
        print("error: the run folder would be inside the input", file=sys.stderr)
        return None, 2
    repo_dir.mkdir(parents=True, exist_ok=True)
    work = free_name(repo_dir, f".running-{date}")
    work.mkdir()

    soft = soft_of(a)
    ran = pipeline.stages_to_run(soft)  # the AI stages only when chosen (restructure S5)
    if options.ai_chosen(PINPOINT, soft) and PINPOINT not in ran:
        print("note: --pinpoint needs --sweep; no pinpoint questions asked", file=sys.stderr)
    until = getattr(a, "until", None)
    todo, left = pipeline.cut_at(ran, until)  # a stop is only a stop when a step comes after it
    data = work / layout.DATA
    data.mkdir()
    for name, content in held_files.items():  # intake's two files, byte for byte
        (data / name).write_bytes(content)
    not_started: list[dict] = []
    runs = pipeline.run_stages(inp, data, STAGES, py, soft, stages=todo, not_started=not_started)
    reports = {r.stage: r.report for r in runs if r.ok}
    failed_prepare, prepared = prepare_next(left, runs, inp, data, py, soft, not_started=not_started)
    say_not_started(not_started)
    left = without_held(left, not_started)
    if failed_prepare is not None:
        runs.append(failed_prepare)
    stopped = bool(left) and all(r.ok for r in runs)  # the run went as far as it was asked to

    first = INVENTORY  # the inventory: its pin names the run
    pin = pipeline.first_finding(reports.get(first))
    h = pin.get("hash") or "nohash"
    name = f"{date}_{h[:7]}" if first in reports else f"{date}_stopped" if stopped else f"{date}_failed"
    run_dir = free_name(repo_dir, name)
    work.rename(run_dir)

    graded = [s for s in todo if s not in {n["stage"] for n in not_started}]  # a step that was not started gets no stamp
    # The check of the run is stamped with the steps, before the record: its stamp is made from its own fixtures and needs
    # nothing from this run, and the record then holds it, so the check reads it like any step's (qa.SPEC.md).
    stamps = {} if getattr(a, "no_validate", False) else validate.stamps(
        ROOT, py, [pipeline.INTAKE, *graded, stagelist.QA], soft_grade_env(a) if SWEEP in graded else {},
        cache=not a.revalidate)
    chosen = [s for s in ran if s in stagelist.AI_STAGES]  # the model reads this command chose
    steps = [got, *runs]  # the record's table has intake's row; no report has its section
    record.write(run_dir, steps, stamps, a.context or options.DEFAULT_CONTEXT, a.hosts or [], now(),
                 version=toolversion.tool_version(ROOT), code=toolversion.code_hash(ROOT),
                 until=until if stopped else None, prepared=prepared, not_started=not_started,
                 chosen=chosen, backends={s: options.ai_choice(s, soft) for s in chosen})
    return check_then_report(py, run_dir, steps)


def _plain(stage: str) -> str:
    return stagelist.PLAIN.get(stage, stage)


def remaining_steps(done: set, soft: dict) -> list[str]:
    """The steps a continued run runs, in the list's order: every coded step not yet done, and an AI step
    only when its option is given at this command and it has not run. The first command's choice is not
    carried, and neither is an environment variable (WALKDOWN_SOFT_SWEEP, WALKDOWN_SOFT_PINPOINT): choosing
    at `continue` is the consent to send, and only the option chooses. Pinpoint needs a sweep, one that ran or
    one chosen now."""
    out = [s for s in stagelist.FOLDER_STAGES
           if s not in done and (s not in stagelist.AI_STAGES or options.ai_chosen(s, soft, {}))]
    if PINPOINT in out and SWEEP not in out and SWEEP not in done:
        out.remove(PINPOINT)
    return out


def reads_left_out(rec: dict, done: set, chosen_now: list, soft: dict) -> tuple[list[str], dict]:
    """(the model reads an earlier command chose that this `continue` leaves out, the backends the record keeps). A read
    chosen at the first command is not run at `continue` unless it is chosen again here: choosing at `continue` is the
    consent to send. It is not dropped silently: the record keeps it (`dropped`), the person gets a note when it happens, and
    the pages say it. A read that ran, one chosen here, and one held back because the read before it got no answer
    (`not_started`) are not dropped. Reads dropped at an earlier `continue` stay dropped until they are chosen."""
    held = {n["stage"] for n in rec.get("not_started") or []}
    earlier = [*(rec.get("chosen") or []), *(rec.get("dropped") or [])]
    dropped = [s for s in stagelist.AI_STAGES if s in earlier and s not in done and s not in chosen_now and s not in held]
    kept = rec.get("backends") if isinstance(rec.get("backends"), dict) else {}
    backends = {s: kept[s] for s in stagelist.AI_STAGES if s in kept and (s in done or s in dropped)}
    backends.update({s: options.ai_choice(s, soft, {}) for s in chosen_now})
    return dropped, {s: backends[s] for s in stagelist.AI_STAGES if s in backends}


def cannot_continue(run_dir: Path, a, py: str) -> tuple[str | None, dict | None, Path | None]:
    """Whether the run in `run_dir` can be gone on with by this command: (the one error line, None, None), or
    (None, the record, the folder the run audited). Reads the folder and writes nothing in it. The cheap
    checks come first, in this order: a run folder, made by this version, no failed step, a stop, the same
    version and the same code, every step's output in place, `--until` after the stop, something to run, the
    audited folder there. Last, the inventory is run again into a temporary folder to see whether the audited
    folder is as it was."""
    data = layout.data_dir(run_dir)
    if not run_dir.is_dir() or not data.is_dir():
        return f"not a run folder: {run_dir}", None, None
    rec = record.read(run_dir)
    if rec is None:
        return ("this run was made before this version of Walkdown, so it cannot be continued; "
                "audit the repository again"), None, None
    bad = next((s for s in rec["steps"] if not s["ok"]), None)
    if bad is not None:
        return (f'the step "{_plain(bad["stage"])}" failed in this run, so it cannot be continued; '
                "audit the repository again"), None, None
    stop = record.stop_of(rec)
    if stop is None:
        return "this run did not stop, so there is nothing to continue", None, None
    here = toolversion.tool_version(ROOT)
    if toolversion.release(rec.get("version")) != toolversion.release(here):
        return (f"this run was stopped by Walkdown {rec.get('version') or 'of an unknown version'}; "
                f"this is {here}; audit the repository again"), None, None
    if rec.get("code") != toolversion.code_hash(ROOT):  # the same version number can hold other code
        return "the code of Walkdown changed since this run stopped; audit the repository again", None, None
    for s in rec["steps"]:  # every step that ran has its saved output; a folder missing one is not the run that stopped
        if not (data / f"{s['stage']}.json").is_file():
            return (f'the run folder is missing the output of "{_plain(s["stage"])}"; '
                    "audit the repository again"), None, None
    until = getattr(a, "until", None)
    if until is not None and stagelist.position(until) <= stagelist.position(stop["after"]):
        return (f'--until {until}: the run already stopped after "{_plain(stop["after"])}"; '
                "name a later step"), None, None
    done = {s["stage"] for s in rec["steps"]}
    if not remaining_steps(done, soft_of(a)):
        nxt = next((s for s in stagelist.AI_STAGES if s not in done), None)
        return (f'nothing to run after "{_plain(stop["after"])}"'
                + (f"; choose --{stagelist.AI_OPTION[nxt]} to go on" if nxt else "")), None, None
    try:
        folder = Path(json.loads((data / f"{stagelist.INTAKE}.json").read_text(encoding="utf-8"))
                      ["findings"][0]["folder"])
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        return "this run has no intake report that can be read; audit the repository again", None, None
    if not folder.is_dir():
        return "the folder this run audited is gone; audit it again", None, None
    if INVENTORY in done:  # a run stopped after intake has no inventory to compare
        with tempfile.TemporaryDirectory(prefix="walkdown-resume-") as tmp:
            again = pipeline.run_stages(folder, tmp, STAGES, py, stages=[INVENTORY])
        try:
            saved = pipeline.read_report(data / f"{INVENTORY}.json")
        except (OSError, ValueError):  # the saved inventory is not a report: the fault is in the run folder
            return (f'the run folder has no readable output of "{_plain(INVENTORY)}"; '
                    "audit the repository again"), None, None
        if not (again and again[0].ok and again[0].report == saved):
            return "the folder changed since the run stopped; audit it again", None, None
    return None, rec, folder


def cannot_release(run_dir: Path, rec: dict, a, soft: dict) -> str | None:
    """Whether the held run in `run_dir` can be released by this command: the one error line, or None. `continue` on a held
    run writes the report with what the run has and runs no step and no grader, so a model option, `--until`, or
    `--revalidate` would ask for what it does not do: it is refused and never ignored (choosing a model read at `continue`
    is the consent to send). The run must have been held
    by this Walkdown: the pages are drawn by this code from what that code made, the rule `cannot_continue` applies to a
    stopped run. The folder that was audited is not read again: no step runs."""
    if getattr(a, options.READS, None) is not None:  # named as the person typed it: the options it resolved to are not theirs
        asked = [f"--{options.READS}"]
    else:
        asked = [f"--{option}" for stage, option in stagelist.AI_OPTION.items() if options.ai_chosen(stage, soft, {})]
    asked += ["--until"] if getattr(a, "until", None) else []
    asked += ["--revalidate"] if getattr(a, "revalidate", False) else []
    if asked:
        return (f"this run is held, and continue writes the report with what ran and runs no step, so "
                f"{' and '.join(asked)} cannot be given; leave {'it' if len(asked) == 1 else 'them'} out, or audit "
                "the repository again")
    here = toolversion.tool_version(ROOT)
    if toolversion.release(rec.get("version")) != toolversion.release(here):
        return (f"this run was held by Walkdown {rec.get('version') or 'of an unknown version'}; "
                f"this is {here}; audit the repository again")
    if rec.get("code") != toolversion.code_hash(ROOT):
        return "the code of Walkdown changed since this run was held; audit the repository again"
    return None


def release(run_dir: Path, rec: dict, a, py: str, soft: dict) -> tuple[Path | None, int]:
    """`continue` on a held run (M9 slice B): the report stage writes the report with what the run has (the pages name every
    gap, as a step that did not work and in section 7), and no step runs; once it has, the hold becomes a release with the
    time. The record says released only after the report is written, so a command killed in the middle leaves a run that is
    still held, and `continue` works again. A held run with a step that failed is released like any: O3's
    refusal of a failed step is for a stopped run. `--context` and `--hosts` given here are handed to the report stage and
    kept in the record, as at any `continue`. Exit code as for a reported run: 1 when a step failed."""
    error = cannot_release(run_dir, rec, a, soft)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return None, 2
    brief = run_dir / layout.BRIEF
    kept = brief.read_bytes() if brief.is_file() else None  # the hold's brief, for the case the report cannot be written
    (run_dir / record.LOG).unlink(missing_ok=True)  # a held run has none; the report stage writes it from the record
    steps = [pipeline.StageRun(s["stage"], s["ok"], s["started"], s["finished"], None, [], s["error"])
             for s in rec["steps"]]
    at = now()
    extra = ["--released-at", at]
    extra += ["--context", str(a.context)] if a.context else []
    extra += ["--hosts", ",".join(a.hosts)] if a.hosts is not None else []
    code = run_report(py, run_dir, extra)
    if code:
        return held_again(run_dir, kept, code)
    record.amend(run_dir, context=a.context or rec["context"],
                 hosts=a.hosts if a.hosts is not None else rec["hosts"])
    record.release(run_dir, at)
    return run_dir, 1 if say_failed(steps) else 0


def held_again(run_dir: Path, brief: bytes | None, code: int) -> tuple[Path, int]:
    """The report stage failed while `continue` released a held run. The record was not touched (it says released only once
    the report is written), so the run is held as it was: what is left is to take out what the report stage wrote and write
    the hold's brief back. A brief that said "No report was written" stays true, and `continue` can be run again once the
    cause is gone."""
    clear_report(run_dir, keep_check=True)
    if brief is not None:
        (run_dir / layout.BRIEF).write_bytes(brief)
    folder = f'"{run_dir}"' if " " in str(run_dir) else str(run_dir)
    print(f"error: the report stage failed (exit {code}), so no report was written and the run is held again; "
          f"python walkdown.py continue {folder} tries again", file=sys.stderr)
    return run_dir, code


def resume(run_dir, a, python=None) -> tuple[Path | None, int]:
    """`walkdown.py continue <run folder>`: go on in a run that stopped (`--until`). Returns the run folder
    (None when it refused) and the exit code, as `audit` does: 2 for a refusal, with one error line and the
    folder as it was. It runs the steps after the stop that this command asks for (every coded one; an AI
    one only when chosen here), validates those and keeps the saved stamps of the rest, rewrites the record
    (`until` and `prepared` as this command's own stop, or gone; `continued` gains `{after, at}`), has the check of the
    run read the run again, and starts the report stage unless that check holds the run again. Past its refusals and before
    any step runs it takes out the pages, the brief, the limits, and the check's output of the stop (`clear_report`), so
    the report stage writes them again from the record; `marks.json` stays. A held run is gone on with by
    `release` instead: no step runs. A run stopped after intake has no pin: its folder, named `<date>_stopped`, is renamed
    `<date>_<hash7>` once the inventory has run. The run folder is made absolute first: the report stage
    starts in Walkdown's own folder. Only the option chooses an AI step here; a set environment variable gets a
    note, since it is not read."""
    py = str(python or sys.executable)
    run_dir = Path(run_dir).resolve()
    soft = soft_of(a)
    for said in options.env_not_read_notes(soft):
        print(f"note: {said}", file=sys.stderr)
    held = record.read(run_dir)
    if record.held_of(held) is not None:  # the check of the run held it: release it, whatever else it is
        return release(run_dir, held, a, py, soft)
    error, rec, inp = cannot_continue(run_dir, a, py)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return None, 2
    clear_report(run_dir)  # the refusals are past: from here the folder is no longer the one that stopped
    stop = record.stop_of(rec)
    done = {s["stage"] for s in rec["steps"] if s["ok"]}
    for stage in stagelist.AI_STAGES:
        if stage in done and options.ai_chosen(stage, soft, {}):
            print(f'note: --{stagelist.AI_OPTION[stage]} ignored: the step "{_plain(stage)}" already ran',
                  file=sys.stderr)
    todo_all = remaining_steps(done, soft)
    chosen_now = [s for s in todo_all if s in stagelist.AI_STAGES]
    dropped, backends = reads_left_out(rec, done, chosen_now, soft)
    if options.ai_chosen(PINPOINT, soft, {}) and PINPOINT not in done and PINPOINT not in todo_all:
        print("note: --pinpoint needs --sweep; no pinpoint questions asked", file=sys.stderr)
    until = getattr(a, "until", None)
    todo, left = pipeline.cut_at(todo_all, until)
    data = layout.data_dir(run_dir)
    not_started: list[dict] = []
    runs = pipeline.run_stages(inp, data, STAGES, py, soft, stages=todo, not_started=not_started)
    failed_prepare, prepared = prepare_next(left, runs, inp, data, py, soft, {}, not_started)
    say_not_started(not_started)
    left = without_held(left, not_started)
    if failed_prepare is not None:
        runs.append(failed_prepare)
    stopped = bool(left) and all(r.ok for r in runs)
    for stage in dropped:
        if not options.ai_chosen(stage, soft, {}):  # chosen here too, it could not run: the note above says why
            print("note: " + common_lines.DROPPED_NOTE.format(
                plain=_plain(stage), how=common_lines.dropped_how(stage, backends, stopped)), file=sys.stderr)

    if STOPPED.fullmatch(run_dir.name):  # the pin exists now: the folder takes the name a full run gets
        pin = next((pipeline.first_finding(r.report) for r in runs if r.stage == INVENTORY and r.ok), {})
        h = pin.get("hash")
        target = free_name(run_dir.parent, f"{STOPPED.fullmatch(run_dir.name).group(1)}_{h[:7] if h else 'failed'}")
        try:
            run_dir = run_dir.rename(target)
        except OSError as exc:
            print(f"note: the run folder was not renamed: {exc}", file=sys.stderr)
        data = layout.data_dir(run_dir)

    graded = [s for s in todo if s not in {n["stage"] for n in not_started}]  # a step that was not started gets no stamp
    kept = record.stamps_of(rec)
    to_grade = [*graded, *([stagelist.QA] if stagelist.QA not in kept else [])]  # the check of the run, once per record
    new = {} if getattr(a, "no_validate", False) or not to_grade else validate.stamps(
        ROOT, py, to_grade, soft_grade_env(a) if SWEEP in graded else {}, cache=not a.revalidate)
    stamps = {**kept, **new}
    before = [pipeline.StageRun(s["stage"], s["ok"], s["started"], s["finished"], None, [], s["error"])
              for s in rec["steps"]]
    steps = [*before, *runs]
    went_on = [*(rec.get("continued") or []), {"after": stop["after"], "at": now()}]
    record.write(run_dir, steps, stamps, a.context or rec["context"],
                 a.hosts if a.hosts is not None else rec["hosts"], now(),
                 version=toolversion.tool_version(ROOT), code=toolversion.code_hash(ROOT),
                 until=until if stopped else None, prepared=prepared, continued=went_on,
                 not_started=not_started, dropped=dropped, backends=backends,
                 chosen=[s for s in stagelist.AI_STAGES if s in done or s in chosen_now])  # what ran, and what is chosen now
    return check_then_report(py, run_dir, steps)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    go_on = argv[:1] == ["continue"]
    ap = options.Parser(prog="runner.py continue" if go_on else "runner.py", description=__doc__.split("\n\n")[0])
    if go_on:
        options.add_continue_options(ap, developer=True)
    else:
        options.add_run_options(ap, developer=True)
    a = ap.parse_args(argv[1:] if go_on else argv)
    error = options.check(a)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    run_dir, code = resume(a.run_dir, a) if go_on else audit(a)
    if run_dir is not None:
        print(str(run_dir))
    return code


if __name__ == "__main__":
    sys.exit(main())
