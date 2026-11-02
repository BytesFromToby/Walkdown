"""The test wall (`conftest.py`, `tests/offline/`): a test finds no real model to call, in this process and in the Python processes it starts with the environment it inherits.

Each part is proved from inside a test and from a subprocess a test starts: `claude` is not on the PATH, the keys are not in the
environment, `import typesafe_sdk` finds the stub, and the registry read of a key finds nothing. Then, on a fake machine (a PATH with a
`claude` on it, model keys, a package that stands for the real SDK), that the wall is raised when pytest starts from the
root, from a stage folder, and on a single file. And that the one exemption, the live `claude` test, is the machine's only when
WALKDOWN_LIVE_CLAUDE=1, and for that one file. What the wall does not reach is in `conftest.py`'s docstring.

Nothing here uses a real key or a real `claude`: the fake machine has fakes, and a check that something is *not* reachable never
reaches for it. A `claude` or an SDK that a fake launches or imports is written to a log, and the tests read the log."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "offline"))
import offline_env  # noqa: E402
import wall_probe  # noqa: E402

PROBE = ROOT / "tests" / "offline" / "wall_probe.py"
HAS_WINREG = importlib.util.find_spec("winreg") is not None  # the registry is a Windows thing: elsewhere there is no read to block
PROBE_PASSED = 2 if HAS_WINREG else 1  # the probe's registry test is skipped where there is no registry


def passed(n):
    """The summary line of a quiet pytest session says `n passed`."""
    return re.compile(rf"\b{n} passed\b")


def fake_claude(folder: Path, log: Path) -> Path:
    """A `claude` that is a real program for this platform, and only writes a line to `log` when it is started: `claude.cmd` on
    Windows, an executable `claude` script elsewhere (POSIX `shutil.which` finds exactly `claude`, with the execute bit)."""
    folder.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        path = folder / "claude.cmd"
        path.write_bytes(f'@echo off\r\necho claude launched>>"{log}"\r\nexit /b 1\r\n'.encode("utf-8"))
    else:
        path = folder / "claude"
        path.write_text(f'#!/bin/sh\necho "claude launched" >> "{log}"\nexit 1\n', encoding="utf-8")
        path.chmod(0o755)
    return path


LIVE = ROOT / "stages" / "_shared" / "tests" / "test_claude_isolation_live.py"


def run(args, env=None, cwd=None, timeout=300):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=dict(os.environ) if env is None else env, cwd=str(cwd or ROOT), timeout=timeout)


# ---------------------------------------------------------------- inside a test

def test_inside_a_test_claude_is_not_on_the_machines_path():
    assert shutil.which("claude") is None
    assert not any(offline_env.has_claude(p) for p in os.environ["PATH"].split(os.pathsep))


def test_inside_a_test_the_model_keys_and_the_soft_variables_are_not_in_the_environment():
    assert [k for k in os.environ if k.upper() in ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY")] == []
    assert [k for k in os.environ if k.upper().startswith("WALKDOWN_SOFT_")] == []


def test_inside_a_test_import_typesafe_sdk_is_the_stub_first_on_sys_path_and_on_pythonpath():
    """Not imported here: importing the stub ends the process. Where the import would land is asked of the finder."""
    stub = (ROOT / "tests" / "offline" / "stub" / "typesafe_sdk.py").resolve()
    spec = importlib.util.find_spec("typesafe_sdk")
    assert spec is not None and Path(spec.origin).resolve() == stub
    holders = [p for p in sys.path if p and ((Path(p) / "typesafe_sdk.py").exists() or (Path(p) / "typesafe_sdk" / "__init__.py").exists())]
    assert holders and Path(holders[0]).resolve() == stub.parent  # of every folder on sys.path that holds an SDK, the stub's is first
    assert Path(os.environ["PYTHONPATH"].split(os.pathsep)[0]).resolve() == stub.parent
    assert "typesafe_sdk" not in sys.modules  # nothing imported the real one before the wall, and nothing since


def test_inside_a_test_the_registry_read_of_a_key_gives_nothing():
    winreg = pytest.importorskip("winreg")
    assert getattr(winreg.QueryValueEx, "walled", False)
    sys.path.insert(0, str(ROOT / "stages" / "_shared"))
    sys.path.insert(0, str(ROOT / "stages" / "03-sweep"))
    import back_jev
    found = back_jev.read_key({}) is not None  # the registry fallback of the jev backend, as a stage would take it; a bool, so a
    assert not found, "back_jev.read_key found a model key in the registry"  # failure can never print a key
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        for name in ("TYPESAFE_API_KEY", "ANTHROPIC_API_KEY", "typesafe_api_key"):
            with pytest.raises(FileNotFoundError):
                winreg.QueryValueEx(k, name)


def test_the_registry_block_stops_a_key_and_nothing_else():
    """Its logic, on a stand-in for `winreg`: the registry itself is not touched."""
    fake = types.SimpleNamespace(QueryValueEx=lambda key, name: f"value of {name}")
    assert offline_env.block_registry(module=fake) is True and offline_env.block_registry(module=fake) is True  # twice is once
    for name in ("TYPESAFE_API_KEY", "typesafe_api_key", "ANTHROPIC_API_KEY"):
        with pytest.raises(FileNotFoundError):
            fake.QueryValueEx(None, name)
    assert fake.QueryValueEx(None, "TEMP") == "value of TEMP"


def test_the_whole_wall_in_one_question():
    assert wall_probe.problems() == []


def test_a_test_that_wants_a_fake_can_put_one_on_its_own_path(tmp_path):
    fake_claude(tmp_path, tmp_path / "launched.log")
    assert shutil.which("claude", path=str(tmp_path)) is not None  # the wall takes the machine's claude, not a test's own
    assert shutil.which("claude") is None


# ---------------------------------------------------------------- from a subprocess

def test_a_subprocess_inherits_the_wall():
    p = run([sys.executable, str(PROBE)])
    assert p.returncode == 0 and p.stdout == "", p.stdout + p.stderr


def test_in_a_subprocess_claude_is_not_found_with_the_machines_path_and_the_keys_are_absent():
    p = run([sys.executable, "-c", "import os, shutil; print(shutil.which('claude')); "
             "print(sorted(k for k in os.environ if k.upper() in ('TYPESAFE_API_KEY', 'ANTHROPIC_API_KEY') "
             "or k.upper().startswith('WALKDOWN_SOFT_')))"])
    assert p.returncode == 0 and p.stdout.split("\n")[:2] == ["None", "[]"], p.stdout + p.stderr


def test_in_a_subprocess_import_typesafe_sdk_ends_in_the_stub_and_no_except_clause_catches_it():
    p = run([sys.executable, "-c", "try:\n    import typesafe_sdk\nexcept BaseException:\n    print('caught')\nprint('went on')"])
    assert p.returncode == 97 and p.stdout == "" and "must not call a model" in p.stderr


SUBPROCESS_HEAD = ("import sys\nsys.path[:0] = [%r, %r]\nimport back_jev, winreg\n"
                   "walled = bool(getattr(winreg.QueryValueEx, 'walled', False))\nprint(walled, flush=True)\n") % (
    str(ROOT / "stages" / "_shared"), str(ROOT / "stages" / "03-sweep"))
# Every subprocess below asks first whether the registry read is blocked, and reads only behind the block: a wall that has failed
# must not make the test read the machine's key (it prints booleans in any case, so a key is never shown).


def test_in_a_subprocess_the_registry_read_of_a_key_gives_nothing():
    pytest.importorskip("winreg")
    p = run([sys.executable, "-c", SUBPROCESS_HEAD + "if walled:\n    print(back_jev.read_key({}) is None)\n"])
    assert p.returncode == 0 and p.stdout.split() == ["True", "True"], p.stdout + p.stderr


def test_the_jev_backends_own_key_reader_and_client_factory_end_at_the_wall_in_a_subprocess():
    """What a step does to send: ask for the key, then build the client. The key is not found and the client is the stub."""
    pytest.importorskip("winreg")
    code = (SUBPROCESS_HEAD + "if walled:\n    print(back_jev.read_key() is None, flush=True)\n"
            "back_jev._default_factory('a key')\nprint('built a client')\n")
    p = run([sys.executable, "-c", code])
    assert p.returncode == 97 and p.stdout.split() == ["True", "True"] and "built a client" not in p.stdout, p.stdout + p.stderr


# ---------------------------------------------------------------- where pytest is started from: a fake machine

@pytest.fixture(scope="module")
def machine(tmp_path_factory):
    """A machine that is not walled: a PATH with a `claude` on it, model keys, a WALKDOWN_SOFT_* variable, and a package that stands
    for the real SDK. The fakes only write to `launched.log`. The rest of the environment is this session's, which has no key or
    `claude` in it, so nothing real is near."""
    base = tmp_path_factory.mktemp("machine")
    log = base / "launched.log"
    fake_claude(base / "bin", log)
    (base / "sdk").mkdir()
    (base / "sdk" / "typesafe_sdk.py").write_text(
        f"open({str(log)!r}, 'a').write('the real sdk was imported\\n')\nraise SystemExit(0)\n", encoding="utf-8")
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([str(base / "bin"), env["PATH"]])
    env.update({"TYPESAFE_API_KEY": "fake-key-of-the-machine", "ANTHROPIC_API_KEY": "fake-key-of-the-machine",
                "WALKDOWN_SOFT_SWEEP": "jev", "PYTHONPATH": str(base / "sdk")})
    env.pop("PYTEST_ADDOPTS", None)
    assert shutil.which("claude", path=env["PATH"]) is not None  # the fake machine does have a claude
    return types.SimpleNamespace(env=env, log=log, base=base)


def launched(m) -> str:
    return m.log.read_text(encoding="utf-8") if m.log.exists() else ""


PYTEST = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider"]


@pytest.mark.parametrize("cwd", ["", "stages/03-sweep", "stages/_shared/tests", "tests"])
def test_the_wall_is_up_wherever_pytest_is_started_and_the_probe_passes_on_a_machine_that_has_claude_and_keys(machine, cwd):
    p = run([*PYTEST, "-q", str(PROBE)], env=machine.env, cwd=ROOT / cwd)
    assert p.returncode == 0, p.stdout[-1500:] + p.stderr[-500:]
    assert passed(PROBE_PASSED).search(p.stdout) and launched(machine) == ""


def test_the_probe_fails_loudly_where_the_wall_is_not_up(machine, tmp_path):
    """The probe is the proof only if it sees a hole: outside the repository (no root conftest) it answers as the machine would."""
    copy = tmp_path / "probe"
    copy.mkdir()
    text = PROBE.read_text(encoding="utf-8").replace("HERE = Path(__file__).resolve().parent", f"HERE = Path({str(PROBE.parent)!r})")
    (copy / "wall_probe.py").write_text(text, encoding="utf-8")
    (copy / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    p = run([*PYTEST, "-q", "--rootdir", str(copy), "wall_probe.py::test_the_wall_holds_in_this_session"], env=machine.env, cwd=copy)
    said = p.stdout + p.stderr
    assert p.returncode != 0, said[-800:]
    holes = ["shutil.which('claude') finds", "the environment has", "typesafe_sdk would load",
             "not first on sys.path among the folders that hold typesafe_sdk", "not first on PYTHONPATH"]
    if HAS_WINREG:  # without a registry there is no read to block, and the probe does not ask
        holes.append("registry read of a model key is not blocked")
    for hole in holes:
        assert hole in said, (hole, said[-1500:])
    assert launched(machine) == ""  # asking is not launching: the fake claude was found and never started


@pytest.mark.parametrize("cwd, args", [
    ("", ["tests/test_offline.py"]),                      # the root, a single test file
    ("stages/01-intake", []),                             # a stage folder, the whole of its tests
    ("stages/01-intake/tests", ["test_run.py"]),          # its tests folder, a single file
    ("stages/_shared", ["tests/test_options.py"]),        # another folder, a single file
])
def test_the_conftest_loads_wherever_pytest_starts_and_says_so_in_its_header(machine, cwd, args):
    p = run([*PYTEST, "--collect-only", "-q", *args], env=machine.env, cwd=ROOT / cwd)
    assert p.returncode == 0, p.stdout[-800:] + p.stderr[-500:]
    h = run([*PYTEST, "--collect-only", *args], env=machine.env, cwd=ROOT / cwd)  # not quiet: the header
    assert "walkdown test wall: up" in h.stdout, h.stdout[:800]
    assert launched(machine) == ""


def test_a_test_that_imports_the_sdk_fails_with_the_walls_line_and_the_session_goes_on(machine):
    """In a test the stub does not end the pytest process (its line would be lost with it): the import raises a BaseException that
    no `except Exception` hides, that test fails and shows the line, and the next test runs. On the fake machine, which has a package
    that stands for the real SDK, the stub is still what is imported."""
    p = run([*PYTEST, "-q", str(ROOT / "tests" / "offline" / "wall_breach_probe.py")], env=machine.env)
    out = p.stdout + p.stderr
    assert p.returncode == 1 and "1 failed, 1 passed" in out, out[-1200:]
    assert "typesafe_sdk was imported by a test that must not call a model" in out and "WallBreach" in out
    assert launched(machine) == ""


def test_importing_the_real_sdk_is_what_the_fake_machines_package_would_do(machine):
    """The control for the proofs above: on the fake machine, outside the wall, the package that stands for the real SDK is found
    and imported, so a probe that says the wall holds says something."""
    p = run([sys.executable, "-c", "import typesafe_sdk"], env=machine.env)
    assert p.returncode == 0 and "the real sdk was imported" in launched(machine)
    machine.log.unlink()


# ---------------------------------------------------------------- the one exemption

SPY = '''"""A pytest plugin for the wall's own test: it records what the live claude test would see, and skips its body."""
import json, os, shutil
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if item.path.name == "test_claude_isolation_live.py":
        mod = item.module
        with open(os.environ["SPY_LOG"], "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"EXE": getattr(mod, "EXE", None), "LIVE": getattr(mod, "LIVE", None),
                                 "which": shutil.which("claude")}) + "\\n")
        pytest.skip("the wall's spy: the live body is not run")
'''


def live_run(machine, tmp_path, live, extra=()):
    spy = tmp_path / "wall_spy.py"
    spy.write_text(SPY, encoding="utf-8")
    spy_log = tmp_path / "spy.log"
    env = dict(machine.env)
    env["PYTHONPATH"] = os.pathsep.join([str(tmp_path), env["PYTHONPATH"]])
    env["SPY_LOG"] = str(spy_log)
    if live:
        env["WALKDOWN_LIVE_CLAUDE"] = "1"
    else:
        env.pop("WALKDOWN_LIVE_CLAUDE", None)
    p = run([*PYTEST, "-q", "-p", "wall_spy", "-rs", str(LIVE), *extra], env=env)
    seen = [json.loads(x) for x in spy_log.read_text(encoding="utf-8").splitlines()] if spy_log.exists() else []
    return p, seen


def test_the_live_claude_test_is_skipped_behind_the_wall_unless_it_is_asked_for(machine, tmp_path):
    p, seen = live_run(machine, tmp_path, live=False)
    assert p.returncode == 0 and "1 skipped" in p.stdout, p.stdout[-800:] + p.stderr[-300:]
    assert all(s["EXE"] is None and s["which"] is None for s in seen) and launched(machine) == ""  # nothing found, nothing launched


def test_the_live_claude_test_alone_gets_the_machines_path_when_it_is_asked_for_and_the_rest_keep_the_wall(machine, tmp_path):
    p, seen = live_run(machine, tmp_path, live=True, extra=[str(PROBE)])
    assert p.returncode == 0, p.stdout[-1200:] + p.stderr[-300:]
    claude = shutil.which("claude", path=machine.env["PATH"])
    assert len(seen) == 1 and seen[0]["LIVE"] is True and seen[0]["EXE"] == claude and seen[0]["which"] == claude, seen
    assert passed(PROBE_PASSED).search(p.stdout)  # the probe, run after the live file, still finds the wall: the PATH was put back
    assert launched(machine) == ""  # the spy skipped the body: the fake claude was never started


def test_the_flag_alone_does_not_open_the_wall_to_any_other_file(machine, tmp_path):
    env = dict(machine.env)
    env["WALKDOWN_LIVE_CLAUDE"] = "1"
    p = run([*PYTEST, "-q", str(PROBE)], env=env)
    assert p.returncode == 0 and passed(PROBE_PASSED).search(p.stdout), p.stdout[-800:]
