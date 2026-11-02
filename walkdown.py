"""Walkdown: audit the instruction layer of an AI skill or agent repository.

    python walkdown.py <path or git URL> [--name NAME] [--fresh | --keep] [--revalidate] [--until STEP]
                       [--sweep jev|claude-cli[:model]] [--pinpoint claude-cli[:model]] [--reads [model]]
                       [--context 32k] [--hosts claude,codex]
    python walkdown.py continue <run folder> [--until STEP] [--sweep jev|claude-cli[:model]] [--pinpoint claude-cli[:model]]
                       [--reads [model]]
    python walkdown.py diff <old run folder> <new run folder>

(`--sweep` and `--pinpoint` are the two optional AI reads; a run without them uses no model. `--reads [model]` chooses
them without naming a backend: the sweep on TypeSafe's Jev when Jev is available, else on the Claude model named; the pinpoint on the
Claude model named; tools off; give it after the target. `--until STEP` stops after a step, and `continue` goes on in the same run folder; choosing an AI read at
`continue` is the consent to send. `--label`, `--compare`, `--relational`, and `--both` are parked and
refused: restructure step 5.)

This file only routes. It picks the Python, parses the options once, hands them to the runner
(stages/_shared/runner.py), and prints the brief file the report stage wrote. The runner gets the copy
(a git URL is cloned, shallow, or an earlier clone updated; a GitHub folder link
(.../tree/<branch>/<path>) clones the repository at that branch and audits the folder; a path is
audited where it is: stages/01-intake), runs the steps, validates them, has the check of the run read the saved run
(stages/05-qa), and starts the report stage. The run lands in RepoResults/<name>/<date>_<hash7>/, and the last thing printed is its brief (brief.md):
counts, trifecta legs, whether a step failed its fixture checks, and the path to the report. The brief is
written by Walkdown itself and quotes nothing from the audited repository, so it is safe to hand to
a chat assistant. When the check finds a gap the run is held: no report is written, the brief printed is the one the
check wrote (the gaps and two ways on), and the exit code is 1; `walkdown.py continue <run folder>` then writes the report
with what ran. Spec: specs/walkdown.SPEC.md.
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "stages" / "_shared"))
import layout  # noqa: E402  (these need no package: --version and --help work without one)
import options  # noqa: E402
from packages import CORE_MODULES  # noqa: E402  (the import names of requirements.txt's packages: what every stage needs)
import runner  # noqa: E402
import stagelist  # noqa: E402

MISSING = ("import importlib.util, sys; "
           "print(' '.join(m for m in sys.argv[1:] if importlib.util.find_spec(m) is None))")
# Set when Walkdown runs itself again under the interpreter it chose, so it never does twice.
CHOSEN = "WALKDOWN_CHOSEN_PYTHON"


def missing_modules(python: str) -> list[str] | None:
    """The core modules `python` cannot import; None when it does not run at all."""
    if Path(python).resolve() == Path(sys.executable).resolve():
        return [m for m in CORE_MODULES if importlib.util.find_spec(m) is None]
    try:
        p = subprocess.run([python, "-c", MISSING, *CORE_MODULES], capture_output=True, text=True,
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout.split() if p.returncode == 0 else None


def python_exe() -> tuple[str, list[str]]:
    """The interpreter that runs the stages, and what it lacks: the one Walkdown was started
    with when it has every core module, else the project virtualenv's when that has them
    (2026-10-21, an outside tester: an empty .venv in the Walkdown folder was preferred over the
    working python they ran, and every stage failed). With neither, this interpreter and what
    it lacks."""
    here = missing_modules(sys.executable) or []
    if not here:
        return sys.executable, []
    for p in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python"):
        if p.is_file() and missing_modules(str(p)) == []:
            return str(p), []
    return sys.executable, here


def diff_main(args: list[str], python: str) -> int:
    """walkdown.py diff <old run folder> <new run folder>: the report stage's comparison."""
    drift = ROOT / "stages" / stagelist.stage_folder(stagelist.REPORT) / "drift.py"
    return subprocess.run([python, str(drift), *args]).returncode


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    python = sys.executable
    if not {"--version", "-h", "--help"} & set(argv):
        python, lacks = python_exe()
        if lacks:
            print(f"error: Python at {python} cannot import {', '.join(lacks)}; install Walkdown's "
                  f"packages first: {python} -m pip install -r {ROOT / 'requirements.txt'}",
                  file=sys.stderr)
            return 2
        if Path(python).resolve() != Path(sys.executable).resolve() and not os.environ.get(CHOSEN):
            # the virtualenv has the packages and this Python lacks them: everything runs there,
            # the brief, drift, and diff included (2026-10-25, review C41)
            return subprocess.run([python, str(ROOT / "walkdown.py"), *argv],
                                  env=dict(os.environ, **{CHOSEN: "1"})).returncode
    if argv[:1] == ["diff"]:
        return diff_main(argv[1:], python)
    go_on = argv[:1] == ["continue"]  # a route to runner.resume, as diff is to the report stage's comparison
    ap = options.Parser(prog="walkdown.py continue" if go_on else "walkdown.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", action="version",
                    version="walkdown " + (ROOT / "VERSION").read_text(encoding="utf-8").strip())
    (options.add_continue_options if go_on else options.add_run_options)(ap)
    a = ap.parse_args(argv[1:] if go_on else argv)
    error = options.check(a)  # the parked options, --until, --hosts, and --context are looked at before anything runs
    if error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Using Python at {python}", file=sys.stderr)
    run_dir, code = runner.resume(a.run_dir, a, python) if go_on else runner.audit(a, python)
    if run_dir is None and code:  # intake, or the runner, already said why on the terminal (M10)
        return code
    brief = None if run_dir is None else layout.report_dir(run_dir) / layout.BRIEF
    if brief is None or not brief.is_file():
        print("error: the run did not finish; see the messages above", file=sys.stderr)
        return code or 1
    sys.stdout.write(brief.read_text(encoding="utf-8"))
    return code


if __name__ == "__main__":
    sys.exit(main())
