"""Tests for run.py, written from specs/intake.SPEC.md: the `intake.source` finding for each kind
of target and each action, and the failures."""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import fetch as F

RUN = Path(__file__).resolve().parents[1] / "run.py"
needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git is not installed")

FIELDS = ["check", "file", "line", "target", "kind", "action", "folder", "name", "url", "ref",
          "subfolder"]


@pytest.fixture
def intake():
    spec = importlib.util.spec_from_file_location("walkdown_intake_run", RUN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def run(*args):
    p = subprocess.run([sys.executable, str(RUN), *map(str, args)], capture_output=True)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


def make_folder(tmp_path, name="my-skill"):
    d = tmp_path / name
    (d / "sub").mkdir(parents=True)
    (d / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n", encoding="utf-8")
    (d / "sub" / "a.md").write_text("a\n", encoding="utf-8")
    return d


# ---------------------------------------------------------------- a folder

def test_a_folder_is_read_where_it_is(tmp_path):
    d = make_folder(tmp_path)
    before = snapshot(d)
    code, out, err = run(d)
    assert code == 0
    report = json.loads(out)
    assert report["stage"] == "01-intake" and report["contract"] == 1
    assert len(report["findings"]) == 1
    f = report["findings"][0]
    assert list(f) == FIELDS
    assert f == {"check": "intake.source", "file": None, "line": None, "target": str(d),
                 "kind": "folder", "action": "read in place", "folder": d.resolve().as_posix(),
                 "name": "my-skill", "url": None, "ref": None, "subfolder": None}
    assert snapshot(d) == before  # nothing is written there


def test_a_folder_given_a_relative_way_is_named_in_full(tmp_path, monkeypatch):
    d = make_folder(tmp_path)
    monkeypatch.chdir(tmp_path)
    f = json.loads(run("my-skill/sub")[1])["findings"][0]
    assert f["target"] == "my-skill/sub" and f["folder"] == (d / "sub").resolve().as_posix()
    assert f["folder"].startswith("/") or f["folder"][1:3] == ":/"  # absolute, forward slashes
    assert "\\" not in f["folder"] and f["name"] == "sub"


def test_name_option_names_the_run(tmp_path):
    d = make_folder(tmp_path)
    assert json.loads(run(d, "--name", "mine")[1])["findings"][0]["name"] == "mine"


def test_the_notes_go_to_stderr_and_nothing_else_to_stdout(tmp_path):
    code, out, err = run(make_folder(tmp_path))
    assert code == 0 and out.startswith("{") and json.loads(out) and err == ""


# ---------------------------------------------------------------- a git URL

@needs_git
def test_a_url_is_cloned_updated_kept_and_cloned_again(intake, origin, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(F, "EXAMINE", tmp_path / "examine")
    dest = (tmp_path / "examine" / "origin").resolve().as_posix()

    def show(**kw):
        f = intake.source(origin.url, **kw)
        assert list(f) == FIELDS
        return f
    f = show()
    assert f == {"check": "intake.source", "file": None, "line": None, "target": origin.url,
                 "kind": "url", "action": "cloned", "folder": dest, "name": "origin",
                 "url": origin.url, "ref": None, "subfolder": None}
    origin.commit("SKILL.md", "version two\n")
    assert show()["action"] == "updated"
    assert "updated the existing clone in" in capsys.readouterr().err
    origin.commit("SKILL.md", "version three\n")
    assert show(keep=True)["action"] == "kept as it is"
    assert "--keep: auditing the existing copy in" in capsys.readouterr().err
    assert (tmp_path / "examine" / "origin" / "SKILL.md").read_text("utf-8") == "version two\n"
    assert show(fresh=True)["action"] == "cloned again"  # git's read-only files deleted too (M8)
    assert (tmp_path / "examine" / "origin" / "SKILL.md").read_text("utf-8") == "version three\n"
    assert show(name="mine")["name"] == "mine" and show(name="mine")["folder"].endswith("/examine/mine")


@needs_git
def test_a_url_through_main_prints_the_report(intake, origin, tmp_path, monkeypatch, capsys):
    """main prints the one-finding report on stdout; the clone's notes stay on stderr."""
    monkeypatch.setattr(F, "EXAMINE", tmp_path / "examine")
    assert intake.main([origin.url, "--name", "mine"]) == 0
    first = json.loads(capsys.readouterr().out)["findings"][0]
    assert (first["kind"], first["action"], first["name"], first["url"]) == (
        "url", "cloned", "mine", origin.url)
    assert (tmp_path / "examine" / "mine" / "SKILL.md").is_file()
    assert intake.main([origin.url, "--name", "mine"]) == 0
    cap = capsys.readouterr()
    assert json.loads(cap.out)["findings"][0]["action"] == "updated"
    assert cap.err.startswith("note: updated the existing clone in ")


# ---------------------------------------------------------------- a GitHub folder link

def test_a_github_folder_link_names_the_branch_and_the_folder(intake, tmp_path, monkeypatch):
    dest = tmp_path / "r"
    (dest / "skills" / "x").mkdir(parents=True)
    got = {}

    def fake(url, name, fresh, keep=False, ref=None):
        got.update(url=url, name=name, fresh=fresh, keep=keep, ref=ref)
        return dest, "updated"
    monkeypatch.setattr(F, "fetch_with_action", fake)
    link = "https://github.com/o/r/tree/main/skills/x"
    f = intake.source(link)
    assert got == {"url": "https://github.com/o/r", "name": "r", "fresh": False, "keep": False,
                   "ref": "main"}  # the clone is named for the repository
    assert f == {"check": "intake.source", "file": None, "line": None, "target": link,
                 "kind": "github-folder", "action": "updated",
                 "folder": (dest / "skills" / "x").resolve().as_posix(), "name": "x",
                 "url": "https://github.com/o/r", "ref": "main", "subfolder": "skills/x"}
    f = intake.source(link, name="mine", fresh=True, keep=False)  # --name names the clone too
    assert got["name"] == "mine" and f["name"] == "mine" and got["fresh"] is True
    f = intake.source("https://github.com/o/r/tree/v1")  # a branch with no folder: the whole repo
    assert f["kind"] == "github-folder" and f["subfolder"] is None and f["ref"] == "v1"
    assert f["folder"] == dest.resolve().as_posix() and f["name"] == "r"
    # a repository link with no /tree/ is a plain URL
    f = intake.source("https://github.com/o/r")
    assert (f["kind"], f["ref"], f["subfolder"], f["url"]) == ("url", None, None, "https://github.com/o/r")


def test_a_github_link_to_a_missing_folder_or_a_file_fails(intake, tmp_path, monkeypatch):
    (tmp_path / "r").mkdir()
    monkeypatch.setattr(F, "fetch_with_action", lambda *a, **k: (tmp_path / "r", "cloned"))
    with pytest.raises(RuntimeError, match="the folder skills/gone is not in https://github.com/o/r at main"):
        intake.source("https://github.com/o/r/tree/main/skills/gone")
    with pytest.raises(ValueError, match="links to one file"):
        intake.source("https://github.com/o/r/blob/main/SKILL.md")
    assert intake.main(["https://github.com/o/r/tree/main/skills/gone"]) == 2
    assert intake.main(["https://github.com/o/r/blob/main/SKILL.md"]) == 2


# ---------------------------------------------------------------- failures

def test_a_file_is_refused_with_the_message(tmp_path):
    f = tmp_path / "SKILL.md"
    f.write_text("x", "utf-8")
    code, out, err = run(f)
    assert code == 2 and out == ""
    assert err.strip() == f"error: {f} is a file; Walkdown audits a folder: give the folder that holds it"


def test_not_a_folder_or_url_is_refused_with_the_message(tmp_path):
    gone = tmp_path / "nothing-here"
    code, out, err = run(gone)
    assert code == 2 and out == "" and err.strip() == f"error: not a folder or a git URL: {gone}"


def test_a_failed_copy_is_a_failure_with_the_message(intake, tmp_path, monkeypatch, capsys):
    """No report, exit 2, today's message: a missing or private repository, an existing folder
    that is not a clone of the URL, git not installed."""
    monkeypatch.setattr(F, "EXAMINE", tmp_path / "examine")

    def not_found(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 128, "", "remote: Repository not found.\n")
    monkeypatch.setattr(F.subprocess, "run", not_found)
    assert intake.main(["https://github.com/o/r"]) == 2
    cap = capsys.readouterr()
    assert cap.out == "" and cap.err.strip() == (
        "error: git clone failed: the repository was not found, or it needs a login "
        "(Walkdown never asks for one)")

    (tmp_path / "examine" / "r").mkdir()
    assert intake.main(["https://github.com/o/r"]) == 2
    err = capsys.readouterr().err
    assert "is not a clone of https://github.com/o/r; pass --name to use another folder" in err
    assert intake.main(["https://github.com/o/r", "--keep"]) == 0  # --keep audits what is there

    def no_git(cmd, **kw):
        raise FileNotFoundError("git")
    monkeypatch.setattr(F.subprocess, "run", no_git)
    assert intake.main(["https://github.com/o/new"]) == 2
    assert "git is not installed" in capsys.readouterr().err
