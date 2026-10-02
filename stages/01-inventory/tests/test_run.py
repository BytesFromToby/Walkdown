"""Tests for run.py, written from specs/run.SPEC.md."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1] / "run.py"

FILE_FIELDS = ("check", "file", "line", "ext", "bytes", "lines", "exec", "encoding", "bom",
               "type", "entry_point")


def run(path):
    p = subprocess.run([sys.executable, str(RUN), str(path)], capture_output=True)
    return p.returncode, p.stdout, p.stderr


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def build(root):
    files = {
        "skills/t/SKILL.md": "---\nname: t\ndescription: Does a thing.\n---\n# T\n",
        "agents/a.md": "---\nname: a\ndescription: Reads.\ntools: Read, Grep\n---\nBody\n",
        "hooks/hooks.json": json.dumps({"hooks": {"SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "x.sh"}]}]}}),
        "p1/plugin.json": json.dumps({"name": "w", "tools": ["Read"]}),
        "p2/plugin.json": json.dumps({"name": "w", "tools": ["Read", "Bash"]}),
        "README.md": "hello\n" + "z" * 600 + "\n",
        "scripts/go": "#!/usr/bin/env bash\necho hi\n",
        "scripts/a.py": "print(1)\n",
    }
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    (root / "bom.md").write_bytes(b"\xef\xbb\xbfhi\n")


# Done when 1, 2, 3, 6
def test_report_on_mixed_folder(tmp_path):
    build(tmp_path)
    before = snapshot(tmp_path)
    code, out, err = run(tmp_path)
    assert code == 0, err
    report = json.loads(out.decode("utf-8"))
    assert report["stage"] == "01-inventory" and report["contract"] == 1
    fs = report["findings"]
    assert fs[0]["check"] == "inv.pin" and fs[0]["files"] == 9
    rows = {f["file"]: f for f in fs if f["check"] == "inv.file"}
    assert len(rows) == 9
    for r in rows.values():
        for k in FILE_FIELDS:
            assert k in r, (r["file"], k)
    assert rows["skills/t/SKILL.md"]["entry_point"] == "skill"
    assert rows["agents/a.md"]["entry_point"] == "agent"
    assert rows["hooks/hooks.json"]["entry_point"] == "hook-config"
    assert rows["p1/plugin.json"]["entry_point"] == "manifest"
    assert rows["README.md"]["entry_point"] == "readme"
    assert rows["bom.md"]["bom"] is True

    census = {(f["file"], f["flag"]) for f in fs if f["check"] == "struct.census"}
    assert census == {("README.md", "long-line"), ("bom.md", "bom")}
    desc = {f["file"]: f["text"] for f in fs if f["check"] == "struct.description"}
    assert desc == {"skills/t/SKILL.md": "Does a thing.", "agents/a.md": "Reads."}
    tools = [f for f in fs if f["check"] == "struct.agent-tools"]
    assert [(t["file"], t["tools"]) for t in tools] == [("agents/a.md", ["Read", "Grep"])]
    hooks = [f for f in fs if f["check"] == "struct.hooks"]
    assert [(h["event"], h["matcher"], h["command"]) for h in hooks] == [
        ("SessionStart", "startup", "x.sh")]
    man = [f for f in fs if f["check"] == "struct.manifests"]
    assert len(man) == 1 and man[0]["divergent"] is True

    pin = fs[0]
    assert pin["extensions"] == {"md": 4, "json": 3, "": 1, "py": 1}
    assert pin["script_languages"] == {"bash": ["scripts/go"], "Python": ["scripts/a.py"]}
    assert snapshot(tmp_path) == before


# Done when 4
def test_empty_folder(tmp_path):
    code, out, _ = run(tmp_path)
    assert code == 0
    fs = json.loads(out)["findings"]
    assert [f["check"] for f in fs] == ["inv.pin"] and fs[0]["files"] == 0


# Done when 5
def test_missing_folder(tmp_path):
    code, out, _ = run(tmp_path / "nope")
    assert code != 0 and out.strip() == b""
