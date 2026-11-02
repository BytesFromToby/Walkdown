"""The wall: an environment in which a test finds no real model to call, in this process and in the Python processes it starts with
that environment.

The root `conftest.py` raises it for the whole pytest session, before any test module is imported (`raise_wall`):

- no model key in the environment (TYPESAFE_API_KEY, ANTHROPIC_API_KEY) and no WALKDOWN_SOFT_* variable, so a variable on the
  machine chooses nothing;
- no folder holding a `claude` program on the PATH, so `shutil.which("claude")` finds nothing;
- `typesafe_sdk` is the stub in `stub/` (imported, it ends a process with exit code 97, and fails the test that imported it when
  pytest is running one), first on `sys.path` and first on PYTHONPATH, so an import in this process or in one a test starts ends
  there and never in the real package;
- the model keys are not read from the Windows user environment in the registry, in this process (`block_registry`) or in a
  Python process a test starts (`stub/sitecustomize.py`, which the stub's place on PYTHONPATH loads).

A subprocess inherits all of it. A test that wants a fake puts its own fake on its own PATH, or passes its own runner. The one
exemption is `stages/_shared/tests/test_claude_isolation_live.py`, and only when WALKDOWN_LIVE_CLAUDE=1 (see `conftest.py`).

The wall does not reach a Python process started with `-I` or `-E`, or with an environment that has no PYTHONPATH (it gets the keys
and the PATH its environment carries, but not the stub or the registry block), an environment a test builds from nothing, a program
started by its full path (`claude` is taken off the PATH and left on the disk), or a session that does not load the root `conftest.py`
(`--noconftest`, `--confcutdir` below the root, `-c` of an ini file below the root).

`offline(dict(os.environ))` is the same wall for a dict: a copy of `environ` made unable to reach a model. A test that builds an
environment of its own (a fake machine, for the wall's own tests) uses it, or builds one without a model in it."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

STUBS = Path(__file__).resolve().parent / "stub"
KEYS = ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY")
CLAUDE_NAMES = ("claude", "claude.exe", "claude.cmd", "claude.bat", "claude.ps1")


def has_claude(folder: str) -> bool:
    """Whether `folder` holds a program the shell would run as `claude`: one of the usual names, or `claude` with any extension
    the machine runs (PATHEXT)."""
    if not folder:
        return False
    names = {*CLAUDE_NAMES, *("claude" + ext.lower() for ext in os.environ.get("PATHEXT", "").split(os.pathsep) if ext)}
    try:
        return any((Path(folder) / name).is_file() for name in names)
    except OSError:
        return False


def offline(environ: dict) -> dict:
    """`environ` made unable to reach a model (see the module's docstring). A copy: the caller's dict is not changed."""
    env = {k: v for k, v in environ.items() if k.upper() not in KEYS and not k.upper().startswith("WALKDOWN_SOFT_")}
    for k in [k for k in env if k.upper() == "PATH"]:  # Windows keeps the name as it was set: Path
        env[k] = os.pathsep.join(p for p in env[k].split(os.pathsep) if not has_claude(p))
    rest = [p for p in env.get("PYTHONPATH", "").split(os.pathsep) if p and p != str(STUBS)]
    env["PYTHONPATH"] = os.pathsep.join([str(STUBS), *rest])  # first, and once
    return env


def block_registry(names=KEYS, module=None) -> bool:
    """Make reading a model key from the Windows user environment (`HKCU\\Environment`, which `back_jev.read_key` falls back to)
    find nothing, in this process: `QueryValueEx` of `winreg` (or of `module`, for a test of this function) for one of `names`
    raises FileNotFoundError, as for a value that is not set. Any other value is read as it always was. False where there is no
    registry."""
    if module is None:
        try:
            import winreg as module
        except ImportError:
            return False
    if getattr(module.QueryValueEx, "walled", False):
        return True
    real = module.QueryValueEx
    blocked = {n.upper() for n in names}

    def query(key, value_name):
        if str(value_name).upper() in blocked:
            raise FileNotFoundError(2, "the test wall: a model key is not read from the registry (tests/offline)", value_name)
        return real(key, value_name)
    query.walled = True
    module.QueryValueEx = query
    return True


def raise_wall(environ=None) -> dict:
    """Raise the wall in this process (the root `conftest.py` calls it before any test module is imported). `os.environ` loses the
    keys, the WALKDOWN_SOFT_* variables, and the folders that hold `claude`, and gets the stub first on PYTHONPATH; the stub is first
    on `sys.path` too, and a `typesafe_sdk` already imported is forgotten, so the next import finds the stub; the registry read of
    a key is blocked. Returns what the one exemption needs, taken before anything changed: `{"PATH": the machine's PATH}`."""
    env = os.environ if environ is None else environ
    saved = {"PATH": next((v for k, v in env.items() if k.upper() == "PATH"), "")}
    clean = offline(dict(env))
    for k in [k for k in env if k not in clean]:
        del env[k]
    for k, v in clean.items():
        if env.get(k) != v:
            env[k] = v
    sys.path[:] = [str(STUBS), *[p for p in sys.path if p != str(STUBS)]]
    sys.modules.pop("typesafe_sdk", None)
    importlib.invalidate_caches()
    block_registry()
    return saved
