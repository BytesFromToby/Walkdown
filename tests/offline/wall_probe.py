"""What the wall guarantees, as questions a Python process asks about itself (`facts`), and the same as tests.

`tests/test_the_wall.py` uses `facts()` from inside its own test and from a subprocess, and runs this file as a test file in a
pytest session it starts on a fake machine (a PATH with a `claude`, model keys, a package standing for the real SDK): where the
conftest did not load, the questions are answered the way the machine would answer them, and the tests below fail. The file is not
named `test_*.py`, so a normal run does not collect it."""
from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STUBS = HERE / "stub"
KEYS = ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY")


def facts() -> dict:
    """The wall as this process sees it. Nothing here imports the SDK (importing the stub ends the process)."""
    spec = importlib.util.find_spec("typesafe_sdk")
    paths = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep) if p]
    try:
        import winreg
        walled = bool(getattr(winreg.QueryValueEx, "walled", False))
        got = []
        if walled:  # asked only where the read is blocked: a probe that found the wall down would otherwise read the machine's key
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
                    got = [name for name in KEYS if _readable(winreg, k, name)]
            except OSError:
                pass
    except ImportError:
        walled, got = None, []
    return {
        "claude": shutil.which("claude"),
        "keys": sorted(k for k in os.environ if k.upper() in KEYS or k.upper().startswith("WALKDOWN_SOFT_")),
        "sdk": spec.origin if spec else None,
        "sdk_dirs": [p for p in sys.path if p and ((Path(p) / "typesafe_sdk.py").exists() or (Path(p) / "typesafe_sdk" / "__init__.py").exists())],
        "pythonpath_first": paths[0] if paths else None,
        "registry_blocked": walled,
        "registry_keys_readable": got,
    }


def _readable(winreg, key, name) -> bool:
    try:
        winreg.QueryValueEx(key, name)
        return True
    except OSError:
        return False


def problems(f: dict | None = None) -> list[str]:
    """What is wrong with the wall, in words: an empty list when it holds."""
    f = facts() if f is None else f
    out = []
    if f["claude"]:
        out.append(f"shutil.which('claude') finds {f['claude']}")
    if f["keys"]:
        out.append(f"the environment has {f['keys']}")
    if f["sdk"] is None or Path(f["sdk"]).resolve() != (STUBS / "typesafe_sdk.py").resolve():
        out.append(f"import typesafe_sdk would load {f['sdk']}, not the stub")
    if not f["sdk_dirs"] or Path(f["sdk_dirs"][0]).resolve() != STUBS.resolve():
        out.append(f"the stub is not first on sys.path among the folders that hold typesafe_sdk ({f['sdk_dirs']})")
    if f["pythonpath_first"] is None or Path(f["pythonpath_first"]).resolve() != STUBS.resolve():
        out.append(f"the stub is not first on PYTHONPATH ({f['pythonpath_first']})")
    if f["registry_blocked"] is False or f["registry_keys_readable"]:
        out.append(f"the registry read of a model key is not blocked ({f['registry_keys_readable']})")
    return out


def test_the_wall_holds_in_this_session():
    found = problems()
    assert not found, "the wall has a hole: " + "; ".join(found)


def test_a_key_is_not_read_from_the_registry_here():
    """The jev backend's own reader, as a stage would call it, finds no key."""
    sys.path.insert(0, str(HERE.parents[1] / "stages" / "_shared"))
    sys.path.insert(0, str(HERE.parents[1] / "stages" / "03-sweep"))
    import back_jev
    import pytest
    winreg = pytest.importorskip("winreg")
    assert getattr(winreg.QueryValueEx, "walled", False), "the registry read of a model key is not blocked"  # asked before it is read
    found = back_jev.read_key({}) is not None  # a bool, so a failure can never print a key
    assert not found, "back_jev.read_key found a model key in the registry"


if __name__ == "__main__":  # a subprocess asks the same: `python wall_probe.py` prints the problems, one for each line
    found = problems()
    if found:
        print("\n".join(found))
    sys.exit(1 if found else 0)
