"""Tests for tests/offline: the environment in which a test may start a real stage without any way to call a model.

The sweep, the pinpoint, and the runner tests run the real stages as subprocesses with `--input-only`. Should a
change make a stage send instead, it must hit a wall and fail the test before it can reach Jev with the owner's key
or start the Claude CLI. This file checks the wall."""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "offline"))
import offline_env  # noqa: E402


def test_the_offline_environment_has_no_key_no_cli_and_an_sdk_that_ends_the_process(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    (bin_dir / "claude.cmd").write_text("", encoding="utf-8")  # a claude on the PATH, as the owner's machine has
    other = tmp_path / "other"
    other.mkdir()
    given = {"TYPESAFE_API_KEY": "k", "ANTHROPIC_API_KEY": "k", "WALKDOWN_SOFT_SWEEP": "jev",
             "WALKDOWN_SOFT_PINPOINT": "claude-cli", "Path": os.pathsep.join([str(bin_dir), str(other)]),
             "PYTHONPATH": "kept", "HOME": "h"}
    env = offline_env.offline(given)
    assert not {"TYPESAFE_API_KEY", "ANTHROPIC_API_KEY", "WALKDOWN_SOFT_SWEEP", "WALKDOWN_SOFT_PINPOINT"} & set(env)
    assert env["Path"] == str(other) and env["HOME"] == "h"  # the folder holding claude is off the PATH, the rest stays
    assert env["PYTHONPATH"].split(os.pathsep) == [str(offline_env.STUBS), "kept"]
    assert given["TYPESAFE_API_KEY"] == "k" and "kept" == given["PYTHONPATH"]  # the caller's dict is not changed
    assert shutil.which("claude", path=env["Path"]) is None


def run(code, **kw):
    env = offline_env.offline(dict(os.environ))
    return subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, **kw)


def test_importing_the_sdk_ends_the_process_and_no_except_clause_catches_it():
    p = run("try:\n    import typesafe_sdk\nexcept Exception:\n    print('caught')\nprint('went on')")
    assert p.returncode == 97 and p.stdout == "" and "must not call a model" in p.stderr


def test_the_jev_backends_own_client_factory_ends_the_process():
    """What `--sweep jev` would do to send: back_jev builds its client from the SDK."""
    code = (f"import sys\nsys.path.insert(0, {str(ROOT / 'stages' / '_shared')!r})\n"
            f"sys.path.insert(0, {str(ROOT / 'stages' / '03-sweep')!r})\nimport back_jev\n"
            "back_jev._default_factory('a key')\nprint('built a client')")
    p = run(code)
    assert p.returncode == 97 and "built a client" not in p.stdout


def test_the_claude_cli_is_not_found_on_the_offline_path():
    p = run("import shutil, os\nprint(shutil.which('claude'))")
    assert p.returncode == 0 and p.stdout.strip() == "None"


def test_the_claude_backend_a_chosen_sweep_makes_finds_no_cli_on_the_offline_path_and_calls_nothing():
    """`--sweep claude-cli` and `--pinpoint claude-cli` build this backend. With `claude` off the path it skips every passage
    as not installed and starts no program."""
    code = (f"import sys, json\nsys.path.insert(0, {str(ROOT / 'stages' / '_shared')!r})\n"
            "import back_claude, softdata\n"
            "b = back_claude.ClaudeCLI(softdata.load(), model='some-model')\n"
            "res = b.ask([{'qid': 'q', 'system': 's', 'prompt': 'p'}])\n"
            "print(json.dumps([r.get('skipped') for r in res]), json.dumps(b.usage.block()))")
    p = run(code)
    assert p.returncode == 0 and p.stdout.strip() == '["claude-cli: not installed"] {"calls": 0, "reported": 0}', p.stderr
