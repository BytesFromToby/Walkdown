"""Tests for scans.py, written from specs/scans.SPEC.md."""
from scans import find_scans, is_script


def first(rel, text):
    s = find_scans(rel, text)
    assert s, text
    return s[0]


def test_glob_literal():
    s = first("a.py", 'import glob\nfor p in glob.glob("skills/*/SKILL.md"):\n')
    assert s.literal and s.pattern == "skills/*/SKILL.md" and s.line == 2


def test_listdir_non_literal():
    s = first("a.py", "names = os.listdir(folder)\n")
    assert not s.literal and "os.listdir(folder)" in s.pattern and not s.recursive


def test_recursive():
    assert first("a.py", 'for r, d, f in os.walk("docs"):\n').recursive
    s = first("a.py", 'Path("x").rglob("*.md")\n')
    assert s.recursive and s.pattern == "*.md"


def test_js_readdir():
    s = first("a.js", 'const f = fs.readdirSync(path.join(__dirname, "skills"));\n')
    assert not s.literal


def test_shell():
    s = first("run.sh", "for f in $(ls prompts/); do\n")
    assert s.literal and s.pattern == "prompts/"
    s = first("run.sh", "find \"$DIR\" -name '*.md'\n")
    assert not s.literal and s.recursive


def test_powershell():
    s = first("a.ps1", "Get-ChildItem -Recurse agents\n")
    assert s.recursive and s.pattern == "agents" and s.literal


def test_markdown_ignored():
    assert find_scans("a.md", 'call os.listdir("x")\n') == []
    assert not is_script("a.md", "hi")
    assert is_script("tool", "#!/usr/bin/env python3\n")
