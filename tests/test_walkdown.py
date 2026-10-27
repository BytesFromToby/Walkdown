"""Tests for walkdown.py, written from specs/walkdown.SPEC.md."""
import importlib.util
import json
import sys
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
    for stage in ("02-reader", "03-graph", "06-soft"):  # a complete run has every step's output
        f(stage, [])
    (d / "LOG.md").write_text("| 01-inventory | a | b | c | x | PASS (gate 1/1) |\n", "utf-8")
    return d


def test_brief_has_the_facts_and_none_of_the_repository_text(tmp_path):
    b = wd.brief(_run_dir(tmp_path))
    assert SENTINEL not in b
    assert "[x] Can read your data" in b and "[ ] Can send data out" in b and "Install grants: network." in b
    # summary.html's terms (owner, 2026-10-21): its headline, concern kinds, wording line, footer
    assert "Walkdown found security concerns in this repository: 1 place, of 1 kind." in b
    assert "  Runs code (1)" in b and "stage 1:" not in b
    assert "3 more places are wording only:" in b and "Things to check" not in b
    assert "Each one is ordinary on its own." in b and "capability only" not in b
    assert "Fixture checks: no step failed." in b and "PASS" not in b and "Validation (" not in b
    assert "summary.html" in b and "details.html" in b and "full.md" in b
    assert b.rstrip().endswith("Finding nothing does not mean a repository is safe.")


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
    assert "[x] Can read your data" in b and str(d / "summary.html") in b
    assert "Walkdown found security concerns in this repository:" in b


def test_brief_headline_follows_a_failed_check(tmp_path):
    """Owner, 2026-10-25 (review C40): the brief uses summary.html's headline, so with no concerns
    a failed fixture check says it may have missed some; INCOMPLETE and no stamp do not. The
    fixture-check line names a failed check and never a check skipped for a missing tool."""
    d = _run_dir(tmp_path)
    (d / "04-phrases.json").write_text(json.dumps({"stage": "04-phrases", "contract": 1, "findings": []}), "utf-8")
    (d / "01-inventory.json").write_text(json.dumps({"stage": "01-inventory", "contract": 1, "findings": [
        {"check": "inv.pin", "file": None, "line": None, "hash": "abc1234def", "hash_kind": "git", "files": 7}]}),
        "utf-8")
    log = "| 01-inventory | a | b | c | x | PASS (gate 1/1) |\n| 02-reader | a | b | c | x | INCOMPLETE (gate 1/2) |\n"
    (d / "LOG.md").write_text(log, "utf-8")
    b = wd.brief(d)
    assert "Walkdown found none of the security concerns it looks for.\n" in b
    assert "Fixture checks: no step failed." in b and "INCOMPLETE" not in b
    (d / "LOG.md").write_text(log + "| 03-graph | a | b | c | x | FAIL (gate 1/2) |\n", "utf-8")
    b = wd.brief(d)
    assert ("Walkdown found none of the security concerns it looks for, but not every step worked, "
            "so it may have missed some.") in b
    assert "Not every step worked in this run: What loads what did not pass its fixture check (FAIL)." in b
    assert "INCOMPLETE" not in b and "What the model actually reads" not in b
    (d / "LOG.md").write_text("", "utf-8")
    assert "Fixture checks: none, this run was made without validation." in wd.brief(d)


def test_a_crashed_run_says_it_did_not_complete(tmp_path):
    """2026-10-21, an outside tester: every stage "not run", yet the brief said found none."""
    d = tmp_path / "RepoResults" / "demo" / "2026-10-21_failed"
    (d / "data").mkdir(parents=True)
    (d / "LOG.md").write_text("| 01-inventory | a | b | c | x | not run |\n", "utf-8")
    (d / "data" / "01-inventory.notes.txt").write_text(
        f"Traceback (most recent call last):\n  File \"/x/{SENTINEL}/a.py\", line 1\n"
        "ModuleNotFoundError: No module named 'yaml'\n", "utf-8")
    b = wd.brief(d)
    assert "found none" not in b and SENTINEL not in b
    assert 'This run did not complete: 6 steps did not run, starting with "What ships"' in b
    assert "What ships stopped with ModuleNotFoundError (No module named 'yaml')." in b
    (d / "data" / "01-inventory.notes.txt").write_text(f"ValueError: bad thing in {SENTINEL}/x.md\n", "utf-8")
    b = wd.brief(d)
    assert "What ships stopped with ValueError." in b and SENTINEL not in b  # type only


def test_python_with_the_packages_is_preferred(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "ROOT", tmp_path)  # an empty .venv in the Walkdown folder
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("", "utf-8")
    assert wd.python_exe() == (wd.sys.executable, [])  # the launching python has the packages
    monkeypatch.setattr(wd, "missing_modules", lambda py: ["yaml"] if py == wd.sys.executable else None)
    exe, lacks = wd.python_exe()
    assert exe == wd.sys.executable and lacks == ["yaml"]  # neither works: say what is missing


def test_a_python_without_the_packages_hands_over_to_the_venv(monkeypatch):
    """2026-10-25 (review C41, an outside tester): started with a system Python, drift said
    "No module named 'yaml'" and diff crashed. Walkdown now runs itself again under the
    virtualenv's interpreter before cloning, with the same arguments, and never twice."""
    import subprocess
    import pytest
    venv = str(ROOT / ".venv" / "bin" / "python-test")
    monkeypatch.setattr(wd, "python_exe", lambda: (venv, []))
    monkeypatch.setattr(wd, "fetch", lambda *a, **k: pytest.fail("cloned before the handover"))
    calls = []
    monkeypatch.setattr(wd.subprocess, "run",
                        lambda cmd, **kw: calls.append((cmd, kw)) or subprocess.CompletedProcess(cmd, 7))
    monkeypatch.delenv(wd.CHOSEN, raising=False)
    argv = ["https://github.com/o/r", "--name", "x"]
    assert wd.main(argv) == 7
    assert calls[0][0] == [venv, str(ROOT / "walkdown.py"), *argv]
    assert calls[0][1]["env"][wd.CHOSEN] == "1"
    assert wd.main(["diff", "a", "b"]) == 7 and calls[1][0][2:] == ["diff", "a", "b"]
    monkeypatch.setenv(wd.CHOSEN, "1")  # already handed over: go on here, never again

    def no_clone(*a, **k):
        raise RuntimeError("stop")
    monkeypatch.setattr(wd, "fetch", no_clone)
    assert wd.main(argv) == 2 and len(calls) == 2


def test_git_never_prompts_and_says_why_a_clone_failed(tmp_path, monkeypatch):
    """2026-10-25 (review C41): no login prompt, long paths on, a time limit; a missing or private
    repository, and no git, said in plain words."""
    import subprocess
    import pytest
    monkeypatch.setattr(wd, "EXAMINE", tmp_path)
    seen = []

    def fake(cmd, **kw):
        seen.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, 128, "", "remote: Repository not found.\n"
                                                         "fatal: repository 'https://github.com/o/r/' not found")
    monkeypatch.setattr(wd.subprocess, "run", fake)
    with pytest.raises(RuntimeError, match="not found, or it needs a login"):
        wd.fetch("https://github.com/o/r", "r", fresh=False)
    cmd, kw = seen[0]
    assert cmd[:4] == ["git", "-c", "core.longpaths=true", "clone"] and cmd[-2:] == ["https://github.com/o/r", str(tmp_path / "r")]
    assert kw["env"]["GIT_TERMINAL_PROMPT"] == "0" and kw["env"]["GCM_INTERACTIVE"] == "never"
    assert kw["timeout"] == wd.GIT_TIMEOUT and "GIT_SSH_COMMAND" in kw["env"]
    with pytest.raises(RuntimeError):
        wd.fetch("https://github.com/o/r", "r2", fresh=False, ref="dev")
    assert seen[1][0][4:8] == ["--depth", "1", "--branch", "dev"]

    def missing(cmd, **kw):
        raise FileNotFoundError("git")
    monkeypatch.setattr(wd.subprocess, "run", missing)
    with pytest.raises(RuntimeError, match="git is not installed"):
        wd.fetch("https://github.com/o/r", "r3", fresh=False)


def test_github_folder_links_and_files(tmp_path, monkeypatch, capsys):
    """2026-10-25 (review C41): a /tree/ link clones the repository at its branch and audits the
    folder; a /blob/ link and a file are errors that say to give a folder."""
    import subprocess
    import pytest
    assert wd.github_link("https://github.com/o/r/tree/main/skills/my%20skill/") == \
        ("https://github.com/o/r", "main", "skills/my skill")
    assert wd.github_link("https://github.com/o/r.git/tree/v1") == ("https://github.com/o/r", "v1", "")
    assert wd.github_link("https://github.com/o/r") is None
    with pytest.raises(ValueError, match="links to one file"):
        wd.github_link("https://github.com/o/r/blob/main/SKILL.md")
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    dest = tmp_path / "r"
    (dest / "skills" / "x").mkdir(parents=True)
    got = {}
    monkeypatch.setattr(wd, "fetch", lambda url, name, fresh, keep=False, ref=None:
                        got.update(url=url, name=name, ref=ref) or dest)
    runs = []
    monkeypatch.setattr(wd.subprocess, "run",
                        lambda cmd, **kw: runs.append(cmd) or subprocess.CompletedProcess(cmd, 0, ""))
    wd.main(["https://github.com/o/r/tree/main/skills/x"])
    assert got == {"url": "https://github.com/o/r", "name": "r", "ref": "main"}
    assert runs[0][2] == str(dest / "skills" / "x") and runs[0][3:5] == ["--repo", "x"]
    wd.main(["https://github.com/o/r/tree/main/skills/x", "--name", "mine"])  # names the clone too
    assert got["name"] == "mine" and runs[1][3:5] == ["--repo", "mine"]
    assert wd.main(["https://github.com/o/r/tree/main/skills/gone"]) == 2
    assert "the folder skills/gone is not in https://github.com/o/r at main" in capsys.readouterr().err
    assert wd.main(["https://github.com/o/r/blob/main/SKILL.md"]) == 2
    f = tmp_path / "SKILL.md"
    f.write_text("x", "utf-8")
    assert wd.main([str(f)]) == 2
    assert "is a file; Walkdown audits a folder" in capsys.readouterr().err


def test_brief_cost_lines(tmp_path):
    """Slice 1 (2026-10-26): two lines on cost, counts only, against the run's expected context."""
    d = _run_dir(tmp_path)
    caps = json.loads((d / "05-capability.json").read_text("utf-8"))
    caps["findings"] += [
        {"check": "cap.context", "file": None, "line": None, "tier": "session", "tokens": 1200, "bytes": 4800,
         "files": [f"{SENTINEL}/SKILL.md"], "unknown": []},
        *[{"check": "cap.context", "file": f"{SENTINEL}/SKILL.md", "line": None, "tier": t, "kind": "skill",
           "tokens": k, "bytes": k * 4, "files": [f"{SENTINEL}/SKILL.md"], "not_text": []}
          for t, k in (("skill-runs", 300), ("skill-full", 900), ("skill-max", 1600))],
        {"check": "cap.ship", "file": f"{SENTINEL}/old.md", "line": None, "group": "unused", "bytes": 400, "tokens": 100}]
    (d / "05-capability.json").write_text(json.dumps(caps), "utf-8")
    (d / "LOG.md").write_text("Expected context: 8,000 tokens\n" + (d / "LOG.md").read_text("utf-8"), "utf-8")
    b = wd.brief(d)
    assert "Every session: 1,200 tokens. Largest skill at its fullest: 1,600 tokens (20% of 8,000)." in b
    assert "Not used at run time: 1 file (100 tokens)." in b and SENTINEL not in b


def test_brief_ready_line(tmp_path):
    """Slice 3 (2026-10-26): one line on hosts, counts only, with the to-do count for the hosts
    named in the run's LOG.md."""
    sys.path.insert(0, str(ROOT / "stages" / "04-phrases"))
    import hosts
    d = _run_dir(tmp_path)
    ph = json.loads((d / "04-phrases.json").read_text("utf-8"))
    texts = {"CLAUDE.md": f"{SENTINEL}\n", "AGENTS.md": "other\n",
             f".claude/skills/{SENTINEL}/SKILL.md": f"---\nname: x\ndescription: d\nargument-hint: [{SENTINEL}]\n---\n"}
    ph["findings"] += hosts.findings(texts, [{"check": "inv.file", "file": f} for f in texts], [])
    (d / "04-phrases.json").write_text(json.dumps(ph), "utf-8")
    (d / "LOG.md").write_text("Target hosts: codex\n" + (d / "LOG.md").read_text("utf-8"), "utf-8")
    b = wd.brief(d)
    assert ("Ready for: 6 of 7 hosts have their files here; copies that differ: 1; one-host features: 1. "
            "For the hosts named: 2 things missing.") in b
    assert SENTINEL not in b


def test_brief_trigger_line(tmp_path):
    """Slice 4 (2026-10-26): one line on triggering, counts only, before the cost lines."""
    sys.path.insert(0, str(ROOT / "stages" / "04-phrases"))
    import trigger
    d = _run_dir(tmp_path)
    ph = json.loads((d / "04-phrases.json").read_text("utf-8"))
    texts = {f".claude/skills/{SENTINEL}/SKILL.md": f"---\nname: x\ndescription: {SENTINEL}\n{SENTINEL}: 1\n---\n"}
    ph["findings"] += trigger.findings(texts, [{"check": "inv.file", "file": f, "entry_point": "skill"} for f in texts])
    (d / "04-phrases.json").write_text(json.dumps(ph), "utf-8")
    b = wd.brief(d)
    line = ("Will it trigger: 1 skill; 2 places that break a host rule, 1 from guidance; "
            "0 pairs of descriptions that overlap.")
    assert line in b and SENTINEL not in b
    assert b.index(line) < b.index("What it can do:")


def test_brief_fit_line(tmp_path):
    """Slice 5 (2026-10-26): one line on tools, counts only."""
    d = _run_dir(tmp_path)
    caps = json.loads((d / "05-capability.json").read_text("utf-8"))
    caps["findings"] += [
        {"check": "fit.unused", "file": f"{SENTINEL}/a.md", "line": 4, "kind_of": "agent", "tool": SENTINEL,
         "family": "web", "pre_approved": False},
        {"check": "fit.hook", "file": f"{SENTINEL}.json", "line": None, "event": "PreToolUse", "host": "claude",
         "matcher": None, "how_often": "every-tool-call", "adds_context": False, "bytes": None, "over_cap": False},
        {"check": "fit.checked", "file": None, "line": None, "entries": 1, "with_grants": 1, "inheriting": 0}]
    (d / "05-capability.json").write_text(json.dumps(caps), "utf-8")
    b = wd.brief(d)
    assert ("Tools fit: 1 granted and never used, 0 tasks with no tool, 0 loops with no stated limit; "
            "1 hook runs on every prompt or tool call.") in b
    assert SENTINEL not in b


def test_brief_clean_line(tmp_path):
    """Slice 6 (2026-10-27): one line on current and clean, counts only."""
    d = _run_dir(tmp_path)
    ph = json.loads((d / "04-phrases.json").read_text("utf-8"))
    ph["findings"] += [
        {"check": "clean.unfinished", "file": f"{SENTINEL}.md", "line": 1, "kind": "todo", "quote": SENTINEL},
        {"check": "clean.model", "file": f"{SENTINEL}.md", "line": 2, "model": SENTINEL, "where": "text"},
        {"check": "clean.checked", "file": None, "line": None, "files": 1}]
    (d / "04-phrases.json").write_text(json.dumps(ph), "utf-8")
    b = wd.brief(d)
    assert "Current and clean: 1 unfinished, 0 dated claims, 1 pinned model ID, 0 older tool names." in b
    assert SENTINEL not in b
