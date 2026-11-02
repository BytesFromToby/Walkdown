"""Tests for fetch.py, written from specs/intake.SPEC.md. The first five moved here from
tests/test_walkdown.py (restructure step 2); the last two use a local git repository (a file://
URL) in place of a remote."""
import shutil
import stat
import subprocess

import pytest

import fetch as F

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")


def test_urls_folders_and_names(tmp_path):
    assert F.is_url("https://github.com/o/r") and F.is_url("git@github.com:o/r.git")
    assert not F.is_url("ReposToExamine/r")
    bare = tmp_path / "x.git"
    bare.mkdir()
    assert not F.is_url(str(bare))
    assert F.repo_name("https://github.com/o/super-powers.git") == "super-powers"
    assert F.repo_name("git@github.com:o/r.git") == "r"
    assert F.repo_name(r"C:\work\my repo" + "\\") == "my-repo"


def test_existing_folder_that_is_not_the_clone_is_never_touched(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "EXAMINE", tmp_path)
    (tmp_path / "repo").mkdir()
    (tmp_path / "repo" / "mine.txt").write_text("keep me")
    with pytest.raises(RuntimeError, match="not a clone"):
        F.fetch("https://github.com/o/repo", "repo", fresh=False)
    assert (tmp_path / "repo" / "mine.txt").read_text() == "keep me"
    assert F.fetch("https://github.com/o/repo", "repo", fresh=False, keep=True) == tmp_path / "repo"
    # --fresh does not change that: a folder that is not this URL's clone is not deleted
    with pytest.raises(RuntimeError, match="not a clone"):
        F.fetch("https://github.com/o/repo", "repo", fresh=True)
    assert (tmp_path / "repo" / "mine.txt").read_text() == "keep me"


def test_same_url_ignores_dot_git_slash_and_case():
    assert F._same_url("https://github.com/O/Repo.git", "https://github.com/o/repo/")
    assert not F._same_url("https://github.com/o/other", "https://github.com/o/repo")


def test_git_never_prompts_and_says_why_a_clone_failed(tmp_path, monkeypatch):
    """2026-10-25 (review C41): no login prompt, long paths on, a time limit; a missing or private
    repository, and no git, said in plain words."""
    monkeypatch.setattr(F, "EXAMINE", tmp_path)
    seen = []

    def fake(cmd, **kw):
        seen.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 128, "", "remote: Repository not found.\n"
                                                         "fatal: repository 'https://github.com/o/r/' not found")
    monkeypatch.setattr(F.subprocess, "run", fake)
    with pytest.raises(RuntimeError, match="not found, or it needs a login"):
        F.fetch("https://github.com/o/r", "r", fresh=False)
    cmd, kw = seen[0]
    assert cmd[:4] == ["git", "-c", "core.longpaths=true", "clone"] and cmd[-2:] == ["https://github.com/o/r", str(tmp_path / "r")]
    assert kw["env"]["GIT_TERMINAL_PROMPT"] == "0" and kw["env"]["GCM_INTERACTIVE"] == "never"
    assert kw["timeout"] == F.GIT_TIMEOUT and "GIT_SSH_COMMAND" in kw["env"]
    with pytest.raises(RuntimeError):
        F.fetch("https://github.com/o/r", "r2", fresh=False, ref="dev")
    assert seen[1][0][4:8] == ["--depth", "1", "--branch", "dev"]

    def missing(cmd, **kw):
        raise FileNotFoundError("git")
    monkeypatch.setattr(F.subprocess, "run", missing)
    with pytest.raises(RuntimeError, match="git is not installed"):
        F.fetch("https://github.com/o/r", "r3", fresh=False)

    def slow(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd, F.GIT_TIMEOUT)
    monkeypatch.setattr(F.subprocess, "run", slow)
    with pytest.raises(RuntimeError, match="took longer than 10 minutes"):
        F.fetch("https://github.com/o/r", "r4", fresh=False)


def test_github_links():
    """2026-10-25 (review C41): a /tree/ link names the repository, the branch, and the folder; a
    /blob/ link is an error that says to give a folder."""
    assert F.github_link("https://github.com/o/r/tree/main/skills/my%20skill/") == \
        ("https://github.com/o/r", "main", "skills/my skill")
    assert F.github_link("https://github.com/o/r.git/tree/v1") == ("https://github.com/o/r", "v1", "")
    assert F.github_link("https://github.com/o/r") is None
    with pytest.raises(ValueError, match="links to one file"):
        F.github_link("https://github.com/o/r/blob/main/SKILL.md")


@pytest.mark.parametrize("sub", ["..", "skills/../..", "a/%2e%2e/b", "a%2F..%2F..", "a\\..\\b"])
def test_a_folder_link_with_dot_dot_is_refused(sub):
    """2026-10-29 (restructure notes M9): the folder audited must sit inside the clone, so a link
    whose folder path holds `..`, written plainly or escaped, is refused before anything is cloned."""
    with pytest.raises(ValueError, match="'..' in its path"):
        F.github_link(f"https://github.com/o/r/tree/main/{sub}")
    assert F.github_link("https://github.com/o/r/tree/main/a..b/c")[2] == "a..b/c"  # a name, not a step up


@needs_git
def test_clone_update_keep_and_fresh_from_a_local_repository(origin, tmp_path, monkeypatch):
    """The four things fetch can do, each with the action it reports; git runs for real against
    a file:// origin. The clone is shallow, and an update goes to the remote's latest commit."""
    monkeypatch.setattr(F, "EXAMINE", tmp_path / "examine")
    dest = tmp_path / "examine" / "r"
    got, action = F.fetch_with_action(origin.url, "r", fresh=False)
    assert (got, action) == (dest, "cloned")
    assert (dest / "SKILL.md").read_text("utf-8") == "version one\n"
    assert (dest / ".git" / "shallow").is_file()  # --depth 1

    origin.commit("SKILL.md", "version two\n")
    (dest / "stray.txt").write_text("left by an earlier audit", "utf-8")
    assert F.fetch_with_action(origin.url, "r", fresh=False) == (dest, "updated")
    assert (dest / "SKILL.md").read_text("utf-8") == "version two\n"
    assert not (dest / "stray.txt").exists()  # clean -fdx

    origin.commit("SKILL.md", "version three\n")
    assert F.fetch_with_action(origin.url, "r", fresh=False, keep=True) == (dest, "kept as it is")
    assert (dest / "SKILL.md").read_text("utf-8") == "version two\n"  # --keep does not update

    # --fresh deletes the clone, read-only files included: git leaves its object files read-only,
    # which Windows would not delete (2026-10-29, restructure notes M8); one more is made here
    (dest / "SKILL.md").chmod(stat.S_IREAD)
    assert F.fetch_with_action(origin.url, "r", fresh=True) == (dest, "cloned again")
    assert (dest / "SKILL.md").read_text("utf-8") == "version three\n"
    assert F.fetch(origin.url, "r", fresh=False) == dest  # fetch is the path alone


@needs_git
def test_a_branch_is_cloned_and_updated_by_name(origin, tmp_path, monkeypatch):
    monkeypatch.setattr(F, "EXAMINE", tmp_path / "examine")
    origin.commit("SKILL.md", "on dev\n", branch="dev")
    dest, action = F.fetch_with_action(origin.url, "r", fresh=False, ref="dev")
    assert action == "cloned" and (dest / "SKILL.md").read_text("utf-8") == "on dev\n"
    origin.commit("SKILL.md", "dev again\n", branch="dev")
    assert F.fetch_with_action(origin.url, "r", fresh=False, ref="dev")[1] == "updated"
    assert (dest / "SKILL.md").read_text("utf-8") == "dev again\n"
    with pytest.raises(RuntimeError, match="that branch or tag is not in the repository"):
        F.fetch(origin.url, "r2", fresh=False, ref="nope")
    assert not (tmp_path / "examine" / "r2").exists()
