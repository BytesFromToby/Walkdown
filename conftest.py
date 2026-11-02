"""One wall for the whole test session: a test finds no real model to call, in this process and in the Python processes it starts
with the environment it inherits.

pytest loads this file before any test module is imported whenever it finds this repository's `pytest.ini`: from the root, from a stage
folder, and on a single test file (`tests/test_the_wall.py` starts pytest in each). A session started with `--noconftest`, with
`--confcutdir` set below the root, or with `-c` naming an ini file below the root does not load it, and has no wall. The wall is
raised here, at import (`tests/offline/offline_env.py`):

- `os.environ` has no TYPESAFE_API_KEY, ANTHROPIC_API_KEY, or WALKDOWN_SOFT_* variable, and PATH holds no folder with a `claude`
  program, so `shutil.which("claude")` is None; every subprocess inherits that;
- the stub for `typesafe_sdk` is first on `sys.path` and on PYTHONPATH, so an import in this process or in a subprocess ends in the
  stub (it makes no call and exits 97), never in the real package;
- the model keys are not read from the Windows user environment in the registry (`back_jev.read_key` falls back to it), here and in
  the Python processes a test starts with the environment it inherits.

A test that wants a fake puts its own fake on its own PATH, or passes its own runner. The only exemption is
`stages/_shared/tests/test_claude_isolation_live.py`, and only when WALKDOWN_LIVE_CLAUDE=1: it calls the real CLI on purpose. The
machine's PATH is saved here, before the wall, and that test alone gets it back, while it is collected and while it runs.

What the wall does not reach: a Python process started with `-I` or `-E`, or with an environment that has no PYTHONPATH (it still gets
the keys and the PATH the environment carries, but not the stub or the registry block); an environment a test builds from nothing instead
of copying `os.environ`; a program started by its full path (`claude` is taken off the PATH, and left on the disk); and the exemption above.

`tests/test_the_wall.py` proves each part, from inside a test and from a subprocess, and that this file loads from the root, from a
stage folder, and on a single file."""
from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tests" / "offline"))
import offline_env  # noqa: E402

LIVE_TEST = ROOT / "stages" / "_shared" / "tests" / "test_claude_isolation_live.py"
MACHINE = offline_env.raise_wall()  # the machine's PATH, saved for the one exemption; the wall is up from here on


def live_asked() -> bool:
    return os.environ.get("WALKDOWN_LIVE_CLAUDE") == "1"


@contextlib.contextmanager
def machine_path():
    """The machine's own PATH, for the one live test; the wall's PATH is put back after."""
    walled = os.environ.get("PATH")
    os.environ["PATH"] = MACHINE["PATH"]
    try:
        yield
    finally:
        os.environ["PATH"] = walled if walled is not None else ""


def is_live_test(path) -> bool:
    try:
        return Path(str(path)).resolve() == LIVE_TEST.resolve()
    except OSError:
        return False


def pytest_report_header(config):
    return ("walkdown test wall: up (no model key, no WALKDOWN_SOFT_* variable, no claude on PATH, stub typesafe_sdk first, "
            "registry key read blocked)" + ("; the live claude test has the machine's PATH" if live_asked() else ""))


@pytest.hookimpl(hookwrapper=True)
def pytest_make_collect_report(collector):
    """The live test looks for `claude` when its module is imported, so it gets the machine's PATH then (only when asked)."""
    if live_asked() and getattr(collector, "path", None) is not None and is_live_test(collector.path):
        with machine_path():
            yield
    else:
        yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item, nextitem):
    """...and while it runs, setup and teardown included."""
    if live_asked() and is_live_test(item.path):
        with machine_path():
            yield
    else:
        yield
