"""Tests for needs.py, written from specs/needs.SPEC.md."""
import needs


def run(texts, rows=None, hooks=(), mcp=(), compat=None):
    rows = rows or [{"check": "inv.file", "file": r} for r in texts]
    return needs.findings(texts, rows, list(hooks), list(mcp), compat or {})


def by(fs, check):
    return [f for f in fs if f["check"] == check]


def test_needs_rules():
    assert needs.first_words("$ FOO=1 sudo jq '.x' a.json | gh pr list && git push; echo $(rg x)") == \
        ["jq", "gh", "git", "echo", "rg"]
    texts = {
        "scripts/a.py": "import subprocess, yaml\nfrom lib.util import x\nsubprocess.run(['docker', 'ps'])\n"
                        "import os\nos.system('ffmpeg -i a b')\n",
        "lib/util.py": "x = 1\n",
        "scripts/b.js": "const { execSync } = require('child_process');\nexecSync('npx foo');\n"
                        "import chalk from 'chalk';\nconst s = require('@scope/pkg/sub');\n",
        "package.json": '{"dependencies": {"chalk": "^5"}}',
        "pyproject.toml": '[project]\ndependencies = ["PyYAML>=6"]\n',
        "README.md": "Install with `brew install ffmpeg` first.\n",
        "SKILL.md": "---\nname: s\ndescription: d\ncompatibility: Needs Docker\n---\n\n```console\n$ jq . a\n```\n",
        "docs/notes.md": "Saved at /Users/jesse/work/plan.md\n",
        "hooks/run.sh": "#!/bin/sh\r\necho hi\r\n",
        "hooks/b.sh": "#!/bin/sh\r\necho hi\r\n",
    }
    rows = [{"check": "inv.file", "file": r} for r in texts]
    for r in rows:
        if r["file"] == "hooks/run.sh":
            r["eol_committed"] = "lf"  # written CRLF by this checkout, committed LF
    fs = run(texts, rows, hooks=[{"file": "hooks/hooks.json", "line": 3, "command": "python hooks/x.py"}],
             compat={"SKILL.md": "Needs Docker"})  # stage 1 passes the parsed field
    cmd = {f["command"]: f for f in by(fs, "need.command")}
    assert {"docker", "ffmpeg", "npx", "jq", "python"} <= set(cmd)
    assert cmd["docker"]["declared"] and cmd["ffmpeg"]["declared"] and not cmd["jq"]["declared"]
    pkg = {f["package"]: f for f in by(fs, "need.package")}
    assert set(pkg) == {"PyYAML", "chalk", "@scope/pkg"} and pkg["PyYAML"]["declared"] and pkg["chalk"]["declared"]
    assert [f["file"] for f in by(fs, "port.crlf")] == ["hooks/b.sh"]
    assert not by(fs, "port.path")
    assert [(f["file"], f["line"]) for f in by(fs, "port.python")] == [("hooks/hooks.json", 3)]
    exec_rows = [{"check": "inv.file", "file": "SKILL.md"},
                 {"check": "inv.file", "file": "run.sh", "exec": False, "exec_source": "git-index"},
                 {"check": "inv.file", "file": "go.sh", "exec": False, "exec_source": "stat-windows"}]
    t2 = {"SKILL.md": "```bash\n./run.sh\n./go.sh\n```\n", "run.sh": "echo\n", "go.sh": "echo\n"}
    assert [(f["file"], f["script"]) for f in by(run(t2, exec_rows), "port.exec")] == [("SKILL.md", "run.sh")]


def test_path_aliases_are_not_packages():
    fs = run({"src/a.ts": "import x from '~/lib/x';\nimport y from '@/y';\nimport z from '#z';\nimport w from 'left-pad';\n"})
    assert [f["package"] for f in by(fs, "need.package")] == ["left-pad"]
