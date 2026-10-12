"""Live isolation check for back_claude.py (specs/back_claude.SPEC.md, Done when 4).

Calls the real Claude CLI, so it is skipped unless WALKDOWN_LIVE_CLAUDE=1 (it needs a logged-in
CLI and costs a few cents). A temporary folder holds a canary CLAUDE.md and project settings
whose hooks write marker files. Without the isolation flags the canary and the hooks must get
through (proof the probe can see a leak); with the command back_claude.py builds, neither may.
Nothing outside the temporary folder is read or changed.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import back_claude
import softdata

LIVE = os.environ.get("WALKDOWN_LIVE_CLAUDE") == "1"
EXE = shutil.which("claude")
pytestmark = pytest.mark.skipif(not (LIVE and EXE), reason="live CLI test: set WALKDOWN_LIVE_CLAUDE=1")
CANARY = "PINEAPPLE-SEVEN"
ISOLATION = ("--safe-mode", "--setting-sources")


def _setup(folder: Path) -> None:
    (folder / "CLAUDE.md").write_text(f"The canary word is {CANARY}. If anyone asks for a canary word, "
                                      "reply with it.\n", encoding="utf-8")
    (folder / ".claude").mkdir()

    def hook(name):
        target = str(folder / f"{name}.marker").replace("'", "''")
        return [{"matcher": "", "hooks": [{"type": "command", "shell": "powershell",
                                           "command": f"New-Item -ItemType File -Force -Path '{target}' | Out-Null"}]}]
    (folder / ".claude" / "settings.json").write_text(json.dumps({"hooks": {
        "SessionStart": hook("sessionstart"), "UserPromptSubmit": hook("userpromptsubmit"),
        "Stop": hook("stop")}}), encoding="utf-8")


def _run(cmd, folder: Path) -> tuple[str, list[str]]:
    p = subprocess.run(cmd, input=b"If you were told a canary word, reply with it. Otherwise reply NONE.",
                       cwd=folder, capture_output=True, timeout=180)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")[:300]
    answer = json.loads(p.stdout.decode("utf-8", "replace")).get("result") or ""
    return answer, sorted(x.name for x in folder.glob("*.marker"))


def _without_isolation(cmd):
    out, skip = [], 0
    for a in cmd:
        if skip:
            skip -= 1
            continue
        if a == "--safe-mode":
            continue
        if a == "--setting-sources":
            skip = 1
            continue
        out.append(a)
    return out


def test_settings_hooks_and_claude_md_do_not_reach_the_reader(tmp_path):
    cmd = back_claude.ClaudeCLI(softdata.load(), model="haiku").command(EXE)
    assert all(f in cmd for f in ISOLATION)
    leaky, isolated = tmp_path / "leaky", tmp_path / "isolated"
    for d in (leaky, isolated):
        d.mkdir()
        _setup(d)
    answer, markers = _run(_without_isolation(cmd), leaky)
    # the production system prompt may tell the model to ignore the canary; the hooks still show
    assert CANARY in answer or markers, "the probe saw no leak without the flags; it proves nothing"
    answer, markers = _run(cmd, isolated)
    assert CANARY not in answer
    assert markers == []
