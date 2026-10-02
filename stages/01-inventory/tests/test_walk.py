"""Tests for walk.py, written from specs/walk.SPEC.md."""
import os
import shutil
import subprocess

import pytest

import walk


def make(root, files):
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


# Done when 1
def test_plain_folder_lists_sorted_forward_slash_paths(tmp_path):
    make(tmp_path, {"b.md": b"b", "a/z.txt": b"z", "a/y.sh": b"y"})
    w = walk.walk(tmp_path)
    assert [e.rel for e in w.entries] == ["a/y.sh", "a/z.txt", "b.md"]
    assert all(e.kind == "file" for e in w.entries)
    assert w.hash_kind == "sha256" and w.channel == "directory"
    assert len(w.hash) == 64


# Done when 2
def test_sha256_pin_tracks_content_and_names(tmp_path):
    make(tmp_path, {"a.md": b"one", "b.md": b"two"})
    first = walk.walk(tmp_path).hash
    assert walk.walk(tmp_path).hash == first
    (tmp_path / "a.md").write_bytes(b"ONE")
    changed = walk.walk(tmp_path).hash
    assert changed != first
    (tmp_path / "a.md").rename(tmp_path / "c.md")
    assert walk.walk(tmp_path).hash not in (first, changed)


# Done when 3
@needs_git
def test_subfolder_of_repo_is_directory_mode(tmp_path):
    git(tmp_path, "init", "-q")
    make(tmp_path, {"sub/a.md": b"a"})
    w = walk.walk(tmp_path / "sub")
    assert w.channel == "directory" and w.hash_kind == "sha256"
    assert [e.rel for e in w.entries] == ["a.md"]


# Done when 4
@needs_git
def test_git_top_level_lists_tracked_and_pins_head(tmp_path):
    git(tmp_path, "init", "-q")
    make(tmp_path, {"t.md": b"tracked", "u.md": b"untracked"})
    git(tmp_path, "add", "t.md")
    git(tmp_path, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "x")
    head = subprocess.run(["git", "-C", str(tmp_path), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    w = walk.walk(tmp_path)
    assert w.channel == "git" and w.hash_kind == "git" and w.hash == head
    assert [e.rel for e in w.entries] == ["t.md"]
    assert w.untracked == 1
    assert w.entries[0].exec_source == "git-index"


# Done when 5
def test_symlink_listed_not_followed(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"s")
    root = tmp_path / "in"
    root.mkdir()
    (root / "a.md").write_bytes(b"a")
    try:
        os.symlink(str(outside), str(root / "link"), target_is_directory=True)
        os.symlink(str(outside / "secret.txt"), str(root / "flink"))
    except (OSError, NotImplementedError):
        pytest.skip("platform cannot create symlinks")
    w = walk.walk(root)
    by = {e.rel: e for e in w.entries}
    assert set(by) == {"a.md", "flink", "link"}
    assert by["link"].kind == "symlink" and by["link"].target == str(outside)
    assert by["flink"].kind == "symlink"
    assert not any("secret" in r for r in by)


# Done when 6
def test_pin_finding_has_contract_fields(tmp_path):
    make(tmp_path, {"a.md": b"abc"})
    w = walk.walk(tmp_path)
    f = walk.pin_finding(w, files=1, bytes_total=3)
    assert f["check"] == "inv.pin" and f["file"] is None and f["line"] is None
    for k in ("source", "hash", "hash_kind", "files", "bytes"):
        assert k in f
    assert f["files"] == 1 and f["bytes"] == 3 and f["hash"] == w.hash
