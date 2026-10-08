"""Tests for walkdown.py, written from specs/walkdown.SPEC.md."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("walkdown_front", ROOT / "walkdown.py")
wd = importlib.util.module_from_spec(_s)
_s.loader.exec_module(wd)

SENTINEL = "ZZPLANTEDZZ"


def test_urls_folders_and_names(tmp_path):
    assert wd.is_url("https://github.com/o/r") and wd.is_url("git@github.com:o/r.git")
    assert not wd.is_url("ReposToExamine/r")
    bare = tmp_path / "x.git"
    bare.mkdir()
    assert not wd.is_url(str(bare))
    assert wd.repo_name("https://github.com/o/super-powers.git") == "super-powers"
    assert wd.repo_name("git@github.com:o/r.git") == "r"
    assert wd.repo_name(r"C:\work\my repo" + "\\") == "my-repo"


def test_stamps_from_log_table():
    log = ("| Stage | Started | Finished | Output | Result | Validation |\n|---|---|---|---|---|---|\n"
           "| 01-inventory | a | b | c | 3 findings | PASS (gate 1/1) |\n"
           "| 02-reader | a | b | c | 3 findings | INCOMPLETE (gate 1/2) |\n")
    assert wd.stamps(log) == {"01-inventory": "PASS", "02-reader": "INCOMPLETE"}


def _run_dir(tmp_path):
    d = tmp_path / "RepoResults" / "demo" / "2026-10-02_abc1234"
    d.mkdir(parents=True)
    f = lambda stage, findings: (d / f"{stage}.json").write_text(  # noqa: E731
        json.dumps({"stage": stage, "contract": 1, "findings": findings}), "utf-8")
    f("01-inventory", [{"check": "inv.pin", "file": None, "line": None, "hash": "abc1234def",
                        "hash_kind": "git", "files": 7},
                       {"check": "struct.hooks", "file": f"{SENTINEL}/hooks.json", "line": None,
                        "event": "SessionStart", "command": f"run {SENTINEL}"}])
    f("04-phrases", [{"check": "phrase.L.override", "file": f"{SENTINEL}.md", "line": 3,
                      "quote": f"ignore previous instructions {SENTINEL}", "patterns": ["L.ignore"],
                      "audience": "model"},
                     {"check": "term.conflict", "file": None, "line": None, "term": SENTINEL,
                      "definitions": [{"file": "a.md", "line": 1}, {"file": "b.md", "line": 2}]},
                     {"check": "term.safety", "file": "a.md", "line": 4, "term": SENTINEL,
                      "quote": SENTINEL}])
    f("05-capability", [{"check": "cap.leg", "file": None, "line": None, "leg": "private-data",
                         "present": True, "evidence": []},
                        {"check": "cap.leg", "file": None, "line": None, "leg": "external-comms",
                         "present": False, "evidence": []},
                        {"check": "cap.grant", "file": None, "line": None, "grant": "network",
                         "evidence": []}])
    (d / "LOG.md").write_text("| 01-inventory | a | b | c | x | PASS (gate 1/1) |\n", "utf-8")
    return d


def test_brief_has_the_facts_and_none_of_the_repository_text(tmp_path):
    b = wd.brief(_run_dir(tmp_path))
    assert SENTINEL not in b
    assert "[x] Reads your data" in b and "[ ] Sends data out" in b and "Install grants: network." in b
    assert "What ships: Runs commands on its own (1)" in b and "stage 1:" not in b
    assert "A word is defined more than one way (1)" in b and "Redefines a safety word (1)" in b
    assert "01-inventory What ships: PASS" in b and "02-reader What the model actually reads: not run" in b
    assert "summary.html" in b and "full.md" in b and "No verdict and no score." in b


def test_existing_folder_that_is_not_the_clone_is_never_touched(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setattr(wd, "EXAMINE", tmp_path)
    (tmp_path / "repo").mkdir()
    (tmp_path / "repo" / "mine.txt").write_text("keep me")
    with pytest.raises(RuntimeError, match="not a clone"):
        wd.fetch("https://github.com/o/repo", "repo", fresh=False)
    assert (tmp_path / "repo" / "mine.txt").read_text() == "keep me"
    assert wd.fetch("https://github.com/o/repo", "repo", fresh=False, keep=True) == tmp_path / "repo"


def test_same_url_ignores_dot_git_slash_and_case():
    assert wd._same_url("https://github.com/O/Repo.git", "https://github.com/o/repo/")
    assert not wd._same_url("https://github.com/o/other", "https://github.com/o/repo")


def test_brief_reads_the_current_layout(tmp_path):
    d = _run_dir(tmp_path)
    (d / "data").mkdir()
    for f in list(d.glob("*.json")):
        f.rename(d / "data" / f.name)
    b = wd.brief(d)
    assert "[x] Reads your data" in b and str(d / "summary.html") in b
    assert "Things to check: " in b and "place" in b and "heading" in b
