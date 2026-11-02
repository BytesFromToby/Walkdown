"""Tests for toolversion.py, written from specs/shared.SPEC.md, toolversion."""
import subprocess

import toolversion


def git(folder, *args):
    subprocess.run(["git", "-C", str(folder), *args], check=True, capture_output=True)


def test_the_version_is_the_version_file_and_the_commit(tmp_path):
    assert toolversion.tool_version(tmp_path) == "unversioned"  # no VERSION file, no git
    (tmp_path / "VERSION").write_text("1.2.3\n", encoding="utf-8")
    assert toolversion.tool_version(tmp_path) == "1.2.3"  # a downloaded zip: the version alone
    git(tmp_path, "init", "-q")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.test", "add", "VERSION")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.test", "commit", "-q", "-m", "x")
    head = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "--short", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    assert toolversion.tool_version(tmp_path) == f"1.2.3 ({head})"
    (tmp_path / "VERSION").write_text("1.2.4\n", encoding="utf-8")  # a tracked file changed
    assert toolversion.tool_version(tmp_path) == f"1.2.4 ({head}+modified)"


def put(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))


def test_release_is_the_version_number_alone():
    assert toolversion.release("0.4.0 (a5bf24e+modified)") == "0.4.0"
    assert toolversion.release("0.4.0 (a5bf24e)") == toolversion.release("0.4.0") == "0.4.0"
    assert toolversion.release(None) == ""


def test_the_code_hash_follows_what_a_run_runs_and_reads(tmp_path):
    """walkdown.py, stages/, and Library/ count; the tests, the specs, the documents, and the caches do not. Two
    sets of uncommitted edits have the same `tool_version` and a different hash."""
    put(tmp_path, "walkdown.py", "print(1)\n")
    put(tmp_path, "stages/_shared/a.py", "x = 1\n")
    put(tmp_path, "stages/stages.json", "{}\n")
    put(tmp_path, "Library/t.yaml", "a: 1\n")
    base = toolversion.code_hash(tmp_path)
    assert len(base) == 16 and toolversion.code_hash(tmp_path) == base
    for rel in ("stages/_shared/tests/test_a.py", "stages/_shared/specs/a.SPEC.md", "stages/_shared/CONTEXT.md",
                "Library/README.md", "stages/_shared/__pycache__/a.pyc", "README.md", "tests/test_x.py",
                "Library/.DS_Store", "stages/Thumbs.db", "stages/desktop.ini", "stages/_shared/a.py~",
                "stages/_shared/.a.py.swp", "stages/.ruff_cache/x", "stages/.mypy_cache/3.13/a.data.json",
                "Library/.hidden.yaml"):
        put(tmp_path, rel, "anything\n")
        assert toolversion.code_hash(tmp_path) == base, rel  # not part of the code
    put(tmp_path, "stages/_shared/tests/test_a.py", "changed\n")
    assert toolversion.code_hash(tmp_path) == base
    for rel, text in (("walkdown.py", "print(2)\n"), ("stages/_shared/a.py", "x = 2\n"), ("stages/stages.json", "[]\n"),
                      ("Library/t.yaml", "a: 2\n"), ("stages/new.py", "y = 1\n")):
        put(tmp_path, rel, text)
        changed = toolversion.code_hash(tmp_path)
        assert changed != base, rel  # a different set of edits is told apart
        base = changed
    put(tmp_path, "stages/_shared/a.py", "x = 2\r\n")  # line endings alone are not an edit
    assert toolversion.code_hash(tmp_path) == base
    other = tmp_path / "copy"
    for rel in ("walkdown.py", "stages/_shared/a.py", "stages/stages.json", "Library/t.yaml", "stages/new.py"):
        put(other, rel, (tmp_path / rel).read_bytes().decode("utf-8"))
    assert toolversion.code_hash(other) == base  # the same files in another folder: the same hash
    assert toolversion.code_hash(tmp_path / "nothing-here") == toolversion.code_hash(tmp_path / "nor-here")  # no files
