"""Tests for walkdown.py, written from specs/walkdown.SPEC.md. The front door only routes: the brief, the
reports, and the running of the steps have their own tests (stages/06-report/tests/test_brief.py,
stages/_shared/tests/test_runner.py)."""
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("walkdown_front", ROOT / "walkdown.py")
wd = importlib.util.module_from_spec(_s)
_s.loader.exec_module(wd)


@pytest.fixture
def tiny_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "SKILL.md").write_text(
        "---\nname: tiny\ndescription: \"A tiny skill.\"\n---\n\n# Tiny\n\nSee references/a.md.\n",
        encoding="utf-8")
    (repo / "references").mkdir()
    (repo / "references" / "a.md").write_text("# A\n\nPlain notes.\n", encoding="utf-8")
    return repo


@pytest.fixture(autouse=True)
def no_model_chosen_by_the_environment(monkeypatch):
    """A test never asks a model, and the machine's own WALKDOWN_SOFT_* variables do not decide a test
    (the parked ones would be refused; round 2 of step 5)."""
    for k in [k for k in os.environ if k.startswith("WALKDOWN_SOFT_")]:
        monkeypatch.delenv(k)


@pytest.fixture
def audits(monkeypatch):
    """The runner stands in: every call is recorded as (parsed options, interpreter) and the run 'did not finish'."""
    calls = []
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    monkeypatch.setattr(wd.runner, "audit", lambda a, python=None: calls.append((a, python)) or (None, 2))
    return calls


def test_the_parked_options_are_refused_before_a_run_starts(audits, capsys, monkeypatch):
    """Decision 5-A: --label, --compare, --relational, and --both are refused with a plain message
    and nothing runs."""
    for argv, flag in ((["x", "--label", "jev"], "--label"), (["x", "--compare", "laya"], "--compare"),
                       (["x", "--relational", "claude-cli"], "--relational"), (["x", "--both"], "--both")):
        assert wd.main(argv) == 2
        assert (f"error: {flag} is not available in this version: labeling is being rebuilt"
                in capsys.readouterr().err)
    assert audits == []
    # round 2: the variables of the parked reads are refused the same way, before anything runs
    for opt in ("LABEL", "COMPARE", "RELATIONAL", "BOTH"):
        var = f"WALKDOWN_SOFT_{opt}"
        monkeypatch.setenv(var, "jev")
        assert wd.main(["x"]) == 2
        assert f"error: {var} is not available in this version: labeling is being rebuilt" in capsys.readouterr().err
        monkeypatch.delenv(var)
    assert audits == []
    for off in ("none", "off", "0"):  # set, and asking for nothing: not refused (one off list, notes M14 a)
        monkeypatch.setenv("WALKDOWN_SOFT_LABEL", off)
        wd.main(["x"])
    assert len(audits) == 3  # only these calls got as far as the runner
    monkeypatch.delenv("WALKDOWN_SOFT_LABEL")
    audits.clear()
    # the two AI options still pass through
    wd.main(["x", "--sweep", "jev", "--pinpoint", "claude-cli"])
    assert (audits[0][0].sweep, audits[0][0].pinpoint) == ("jev", "claude-cli")


def test_a_bad_context_or_host_ends_the_run_before_it_starts(audits, capsys):
    assert wd.main(["x", "--context", "lots"]) == 2
    assert "error: --context 'lots' is not a token count" in capsys.readouterr().err
    assert wd.main(["x", "--hosts", "vim"]) == 2
    assert "error: --hosts: not a host: 'vim'" in capsys.readouterr().err
    assert audits == []


def test_python_with_the_packages_is_preferred(tmp_path, monkeypatch):
    monkeypatch.setattr(wd, "ROOT", tmp_path)  # an empty .venv in the Walkdown folder
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("", "utf-8")
    assert wd.python_exe() == (wd.sys.executable, [])  # the launching python has the packages
    monkeypatch.setattr(wd, "missing_modules", lambda py: ["yaml"] if py == wd.sys.executable else None)
    exe, lacks = wd.python_exe()
    assert exe == wd.sys.executable and lacks == ["yaml"]  # neither works: say what is missing


def test_a_python_without_the_packages_hands_over_to_the_venv(monkeypatch, audits):
    """2026-10-25 (review C41, an outside tester): started with a system Python, drift said
    "No module named 'yaml'" and diff crashed. Walkdown now runs itself again under the
    virtualenv's interpreter before cloning (intake, in the runner, is what clones), with
    the same arguments, and never twice."""
    venv = str(ROOT / ".venv" / "bin" / "python-test")
    monkeypatch.setattr(wd, "python_exe", lambda: (venv, []))
    calls = []
    monkeypatch.setattr(wd.subprocess, "run",
                        lambda cmd, **kw: calls.append((cmd, kw)) or subprocess.CompletedProcess(cmd, 7))
    monkeypatch.delenv(wd.CHOSEN, raising=False)
    argv = ["https://github.com/o/r", "--name", "x"]
    assert wd.main(argv) == 7
    assert calls[0][0] == [venv, str(ROOT / "walkdown.py"), *argv]
    assert calls[0][1]["env"][wd.CHOSEN] == "1"
    assert wd.main(["diff", "a", "b"]) == 7 and calls[1][0][2:] == ["diff", "a", "b"]
    assert audits == []  # handed over: nothing ran here
    monkeypatch.setenv(wd.CHOSEN, "1")  # already handed over: go on here, never again
    assert wd.main(argv) == 2 and len(calls) == 2  # no third run of walkdown.py
    assert len(audits) == 1 and audits[0][1] == venv  # the runner, under the interpreter chosen


def test_the_target_and_the_options_go_to_the_runner_as_given(audits, capsys):
    """Restructure step 2: intake (stages/01-intake) gets the copy. Restructure step 7: the router passes the
    target as it was given, and every option, to the runner, parsed once."""
    link = "https://github.com/o/r/tree/main/skills/x"
    wd.main([link])
    a = audits[0][0]
    assert (a.target, a.name, a.fresh, a.keep, a.sweep, a.pinpoint, a.revalidate, a.context, a.hosts) == (
        link, None, False, False, None, None, False, None, None)
    wd.main([link, "--name", "mine", "--fresh"])
    assert (audits[1][0].name, audits[1][0].fresh, audits[1][0].keep) == ("mine", True, False)
    wd.main(["https://github.com/o/r", "--keep", "--context", "8k", "--hosts", "codex", "--revalidate"])
    a = audits[2][0]
    assert (a.keep, a.context, a.hosts, a.revalidate) == (True, 8000, ["codex"], True)  # read once, here
    wd.main(["some/folder"])
    assert audits[3][0].target == "some/folder" and not hasattr(audits[3][0], "repo")  # the name comes from intake
    assert "Using Python at" in capsys.readouterr().err and audits[0][1] == wd.sys.executable


def test_a_target_intake_refuses_ends_the_run(tmp_path):
    """A file, and a path that is not a folder, are refused by intake with today's messages; the
    run stops, and intake's line is the only error (2026-10-29, restructure notes M10: no second
    line saying the run did not finish). (Run for real: no stage runs.)"""
    f = tmp_path / "SKILL.md"
    f.write_text("x", "utf-8")
    for target, message in ((f, "is a file; Walkdown audits a folder"),
                            (tmp_path / "gone", "not a folder or a git URL")):
        p = subprocess.run([wd.sys.executable, str(ROOT / "walkdown.py"), str(target)],
                           capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 2 and p.stdout == ""
        assert message in p.stderr and "did not finish" not in p.stderr
        assert p.stderr.count("error:") == 1


def test_a_model_name_the_terminal_cannot_print_ends_the_run_with_a_sentence_and_no_traceback(tmp_path):
    """M1 fix 1: a model name outside ASCII was let through and then crashed the front door when the brief (or the error)
    was written to a console that cannot print it. It is refused now, with a sentence that prints anywhere (run for real,
    on a console that holds only the Windows ANSI set). The test session's wall (the root `conftest.py`) is in the environment it
    inherits: if the rule ever let a name through, the run would find no `claude` and no key, and send nothing."""
    env = {**os.environ, "PYTHONIOENCODING": "cp1252:strict"}
    for typed in ("claude-cli:日本語", "claude-cli:😀", "日本語", "claude-cli:" + "L" * 3000):
        p = subprocess.run([wd.sys.executable, str(ROOT / "walkdown.py"), str(tmp_path), "--sweep", typed],
                           capture_output=True, text=True, encoding="utf-8", env=env)
        assert p.returncode == 2 and p.stdout == "", p.stderr
        assert "Traceback" not in p.stderr and p.stderr.startswith("error: --sweep: "), p.stderr
        assert len(p.stderr) < 300 and p.stderr.isascii()


def test_the_router_prints_the_brief_file_the_report_stage_wrote(tmp_path, monkeypatch, capsys):
    """It prints brief.md as it is and returns the runner's exit code; with no brief it says the run did not finish."""
    run = tmp_path / "RepoResults" / "demo" / "2026-10-02_abc1234"
    run.mkdir(parents=True)
    text = "Walkdown brief: demo\nFiles examined: 2.\n\nFinding nothing does not mean a repository is safe.\n"
    (run / "brief.md").write_text(text, "utf-8")
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    monkeypatch.setattr(wd.runner, "audit", lambda a, python=None: (run, 1))
    assert wd.main(["x"]) == 1
    assert capsys.readouterr().out == text  # as the file is: nothing before it, nothing added after it
    (run / "brief.md").unlink()
    assert wd.main(["x"]) == 1
    cap = capsys.readouterr()
    assert cap.out == "" and "error: the run did not finish; see the messages above" in cap.err
    monkeypatch.setattr(wd.runner, "audit", lambda a, python=None: (None, 0))
    assert wd.main(["x"]) == 1  # a run that did not finish never exits 0
    assert "error: the run did not finish" in capsys.readouterr().err  # and is never silent
    monkeypatch.setattr(wd.runner, "audit", lambda a, python=None: (None, 2))
    assert wd.main(["x"]) == 2 and "did not finish" not in capsys.readouterr().err  # the runner said why


def test_a_whole_run_through_the_router_prints_what_the_report_stage_saved(tiny_repo, tmp_path, monkeypatch, capsys):
    """The steps run, the report stage runs on the folder, and what is printed is brief.md (no grader here:
    validation is stubbed so the test stays fast; the real one is checked by the smoke comparison)."""
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    monkeypatch.setattr(wd.runner, "ROOT", tmp_path)
    monkeypatch.setattr(wd.runner.validate, "stamps", lambda *a, **k: {})
    assert wd.main([str(tiny_repo), "--name", "demo"]) == 0
    cap = capsys.readouterr()
    run = next((tmp_path / "RepoResults" / "demo").iterdir())
    assert cap.out == (run / "brief.md").read_text("utf-8")
    assert cap.out.startswith("Walkdown brief: demo\n") and str(run / "details.html") in cap.out
    assert "Everything behind each answer:" in cap.out and cap.err.startswith("Using Python at")
    assert "Changes since" not in cap.out  # a first run has nothing to compare
    assert wd.main([str(tiny_repo), "--name", "demo"]) == 0  # a second run: the one comparison reaches the brief
    second = max((tmp_path / "RepoResults" / "demo").iterdir(), key=lambda p: p.name)
    assert second != run and capsys.readouterr().out.endswith(
        f"\n\nChanges since {run.name}: same version, nothing to compare.\n")


@pytest.fixture
def resumes(monkeypatch):
    """The runner's `resume` stands in: every call is recorded as (parsed options, interpreter); a run folder with
    a brief is what it hands back."""
    calls = []
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    monkeypatch.setattr(wd.runner, "resume", lambda run_dir, a, python=None: calls.append((run_dir, a, python)) or (None, 2))
    monkeypatch.setattr(wd.runner, "audit", lambda a, python=None: calls.append(("audit", a)) or (None, 2))
    return calls


def test_continue_is_a_route_to_the_runner_and_prints_the_brief(resumes, tmp_path, monkeypatch, capsys):
    """O3: `walkdown.py continue <run folder>` is a route beside `diff`: its own options (intake's are not
    declared), parsed once and checked, then `runner.resume`, then the brief the report stage wrote."""
    run = tmp_path / "RepoResults" / "demo" / "2026-10-30_abc1234"
    run.mkdir(parents=True)
    (run / "brief.md").write_text("Walkdown brief: demo\n\nthe brief of the run as it went on\n", "utf-8")
    monkeypatch.setattr(wd.runner, "resume", lambda run_dir, a, python=None: resumes.append((run_dir, a, python)) or (run, 0))
    assert wd.main(["continue", str(run), "--sweep", "jev", "--until", "SWEEP", "--context", "8k", "--hosts", "codex",
                    "--revalidate"]) == 0
    got_dir, a, python = resumes[0]
    assert got_dir == str(run) and python == wd.sys.executable
    assert (a.run_dir, a.sweep, a.pinpoint, a.until, a.context, a.hosts, a.revalidate) == (
        str(run), "jev", None, "03-sweep", 8000, ["codex"], True)  # --until reaches the runner as the step's name
    cap = capsys.readouterr()
    assert cap.out == (run / "brief.md").read_text("utf-8") and cap.err.startswith("Using Python at")
    assert len(resumes) == 1  # nothing else ran: no audit
    # a refusal by the runner is its one line, exit 2, and no brief
    monkeypatch.setattr(wd.runner, "resume", lambda run_dir, a, python=None: (None, 2))
    assert wd.main(["continue", str(run)]) == 2
    cap = capsys.readouterr()
    assert cap.out == "" and "did not finish" not in cap.err
    # a run with no brief never exits 0
    (run / "brief.md").unlink()
    monkeypatch.setattr(wd.runner, "resume", lambda run_dir, a, python=None: (run, 0))
    assert wd.main(["continue", str(run)]) == 1 and "error: the run did not finish" in capsys.readouterr().err


def test_continue_checks_its_options_before_anything_runs(resumes, capsys, monkeypatch):
    for argv, message in ((["--until", "nonsense"], "error: --until 'nonsense' is not a step (names: 01-intake, "),
                          (["--until", "03-sweep"], "error: --until 03-sweep: that step runs only when chosen (--sweep)"),
                          (["--label", "jev"], "error: --label is not available in this version"),
                          (["--hosts", "vim"], "error: --hosts: not a host: 'vim'"),
                          (["--context", "lots"], "error: --context 'lots' is not a token count")):
        assert wd.main(["continue", "somewhere", *argv]) == 2
        assert capsys.readouterr().err.startswith(message), argv
    monkeypatch.setenv("WALKDOWN_SOFT_LABEL", "jev")
    assert wd.main(["continue", "somewhere"]) == 2 and "WALKDOWN_SOFT_LABEL is not available" in capsys.readouterr().err
    assert resumes == []  # none of them reached the runner
    for intake_only in (["--name", "x"], ["--fresh"], ["--keep"]):  # intake does not run again
        with pytest.raises(SystemExit):
            wd.main(["continue", "somewhere", *intake_only])
    capsys.readouterr()
    assert resumes == []
    # a run that is not a continue is not routed there: a folder named `continue` is still a target after a flag
    monkeypatch.delenv("WALKDOWN_SOFT_LABEL")
    wd.main(["--keep", "continue"])
    assert resumes[0][0] == "audit" and resumes[0][1].target == "continue"


def test_a_stop_and_continue_through_the_router_print_the_two_briefs(tiny_repo, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    monkeypatch.setattr(wd.runner, "ROOT", tmp_path)
    monkeypatch.setattr(wd.runner.validate, "stamps", lambda *a, **k: {})
    assert wd.main([str(tiny_repo), "--name", "demo", "--until", "02.3"]) == 0
    stopped = capsys.readouterr().out
    run = next((tmp_path / "RepoResults" / "demo").iterdir())
    assert stopped == (run / "brief.md").read_text("utf-8")
    assert 'Stopped after "What loads what", as asked (--until); the steps after it did not run.' in stopped
    assert f"To go on: python walkdown.py continue {run}\n" in stopped
    elsewhere = tmp_path / "elsewhere"  # a relative run folder from another working folder (the fix round)
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert wd.main(["continue", os.path.relpath(run, elsewhere)]) == 0
    whole = capsys.readouterr().out
    assert whole == (run / "brief.md").read_text("utf-8") and "Stopped after" not in whole and "To go on" not in whole
    assert whole.startswith("Walkdown brief: demo\n") and "Walkdown found none of the security concerns" in whole
    assert wd.main(["continue", str(run)]) == 2  # it went through: nothing to continue
    assert "did not stop" in capsys.readouterr().err


def test_diff_is_a_route_to_the_report_stages_comparison(monkeypatch):
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    calls = []
    monkeypatch.setattr(wd.subprocess, "run", lambda cmd, **kw: calls.append(cmd) or subprocess.CompletedProcess(cmd, 5))
    assert wd.main(["diff", "old", "new"]) == 5
    assert calls == [[wd.sys.executable, str(ROOT / "stages" / "06-report" / "drift.py"), "old", "new"]]


def test_walkdown_holds_only_routing():
    """Restructure step 7, done-when 2: no rendering, no LOG parsing, no drift, no brief, and no import of a
    stage; the paths it adds to sys.path are stages/_shared's alone."""
    src = (ROOT / "walkdown.py").read_text("utf-8")
    for word in ("def brief", "def stamps", "def stage_error", "def own_words", "def drift_lines", "LOG.md",
                 "details_html", "summary_html", "import render", "import drift", "STAGE8", "own_words"):
        assert word not in src, word
    assert re.findall(r"sys\.path\.insert\(0, (.+)\)", src) == ['str(ROOT / "stages" / "_shared")']
    assert len(src.splitlines()) <= 130


def test_walkdown_holds_no_fetch_code():
    """Restructure step 2, done-when 2: the fetch code lives in stages/01-intake/ only."""
    src = (ROOT / "walkdown.py").read_text("utf-8")
    for word in ("def fetch", "git clone", "ReposToExamine"):
        assert word not in src, word
    assert (ROOT / "stages" / "01-intake" / "fetch.py").is_file()


def test_the_stage_list_has_one_home():
    """Restructure step 1 and step 7: stages/stages.json names each stage, its folder, its plain name, its
    heading, and for an AI stage its option and variable. The router finds the report stage there, and every
    table keyed by a stage name is built from it."""
    doc = json.loads((ROOT / "stages" / "stages.json").read_text("utf-8"))
    names = [s["name"] for s in doc["stages"]]
    for mod in ("pipeline", "stagelist"):  # both are loaded by the router's imports
        assert importlib.util.find_spec(mod) is not None
    import pipeline
    import stagelist
    assert stagelist.STAGES == pipeline.STAGES == names and names[0] == pipeline.INTAKE == "01-intake"
    report = ROOT / "stages" / stagelist.stage_folder(stagelist.REPORT)
    assert report == ROOT / "stages" / doc["report"]["folder"] and (report / "run.py").is_file()
    assert (report / "drift.py").is_file()  # the diff route
    folder_stages = names[1:]
    assert tuple(s for s in folder_stages if s in ("03-sweep", "04-pinpoint")) == stagelist.AI_STAGES
    assert pipeline.FOLDER_STAGES == folder_stages and list(stagelist.PLAIN) == names
    for s in doc["stages"]:
        assert (ROOT / "stages" / s["folder"] / "run.py").is_file()


def test_a_held_run_prints_the_hold_brief_and_exits_1_and_continue_prints_the_report_brief(tiny_repo, tmp_path,
                                                                                         monkeypatch, capsys):
    """M9 slice B: a gap holds the run. The router prints what the check wrote, exits 1, and the folder holds no page;
    `continue` writes the report with what ran, prints its brief, and exits 0."""
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    monkeypatch.setattr(wd.runner, "ROOT", tmp_path)
    monkeypatch.setattr(wd.runner.validate, "stamps", lambda root, python, stages, env=None, cache=True: {
        s: wd.runner.validate.Stamp("FAIL" if s == "02.3-graph" else "PASS") for s in stages})
    assert wd.main([str(tiny_repo), "--name", "demo"]) == 1
    cap = capsys.readouterr()
    run = next((tmp_path / "RepoResults" / "demo").iterdir())
    assert cap.out == (run / "brief.md").read_text("utf-8")
    assert cap.out.splitlines() == [
        "Walkdown brief: demo",
        "This run is held before the report: the check of the run found 1 gap.",
        "",
        '  1. The step "What loads what" did not pass its fixture check: it gave FAIL.',
        "",
        f"No report was written. The saved outputs of the steps that ran are in {run / 'data'}.",
        f"To write the report with what ran: python walkdown.py continue {run}",
        "Or fix the cause and audit the repository again."]
    assert cap.err.strip().splitlines() == [f"Using Python at {wd.sys.executable}"]  # no error line: no step failed
    assert sorted(p.name for p in run.iterdir()) == ["brief.md", "data"]
    assert wd.main(["continue", str(run)]) == 0
    cap = capsys.readouterr()
    assert cap.out == (run / "brief.md").read_text("utf-8") and cap.out.startswith("Walkdown brief: demo\n")
    assert "Not every step worked in this run: What loads what did not pass its fixture check (FAIL)." in cap.out
    assert "This run is held" not in cap.out and (run / "summary.html").is_file()


def test_the_skill_relays_a_held_runs_brief_and_runs_continue_only_when_the_user_says_so():
    """M9 slice B: the skill is what a chat assistant follows, so the rule for a hold is in it."""
    flat = " ".join((ROOT / ".claude" / "skills" / "walkdown" / "SKILL.md").read_text("utf-8").split())
    assert 'begins "This run is held before the report"' in flat and "Relay that brief like any other" in flat
    assert "only when the user says so" in flat and "python walkdown.py continue <run folder>" in flat
    assert "no model option, no `--until`, and no `--revalidate`" in flat and "fix the cause and audit the repository again" in flat


# ---------------------------------------------------------------- the loaded-model build: --reads through the front door
# Nothing here reaches a model. The model reads are fakes: a `claude` program on a PATH of the test's own, and a `typesafe_sdk` in front
# of the wall's stub on PYTHONPATH, each writing a line to a log when it is called. The key is planted in the environment of the test.

PLANTED = "planted-key-7d41f0c2-must-not-appear-anywhere"

FAKE_CLAUDE = r'''
import json, os, sys, uuid
args = sys.argv[1:]
prompt = sys.stdin.buffer.read().decode("utf-8", "replace")
model = args[args.index("--model") + 1] if "--model" in args else None
tools = args[args.index("--tools") + 1] if "--tools" in args else "absent"
pin = prompt.startswith("FLAG:")
with open(os.path.join(os.environ["FAKE_CLAUDE_LOG"], uuid.uuid4().hex + ".json"), "w", encoding="utf-8") as fh:  # one file a call
    json.dump({"kind": "pinpoint" if pin else "sweep", "model": model, "tools": tools}, fh)
answer = json.dumps({"line": None, "quote": None, "plain": "A plain reading from the fake."}) if pin else (
    "secrets" if "tomato" in prompt.lower() else "none")
print(json.dumps({"result": answer, "is_error": False, "usage": {"input_tokens": 10, "output_tokens": 2},
                  "modelUsage": {model: {}}}))
'''

FAKE_SDK = r'''
import json, os, uuid
from types import SimpleNamespace as NS


class RetryPolicy:
    def __init__(self, max_retries=0):
        self.max_retries = max_retries


class TypeSafeClient:
    def __init__(self, api_key=None, retry=None):
        self.key_is_the_planted_one = api_key == os.environ.get("FAKE_EXPECTED_KEY")

    def system_one(self, state, questions, model):
        with open(os.path.join(os.environ["FAKE_JEV_LOG"], uuid.uuid4().hex + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"key": self.key_is_the_planted_one, "file": state["file"], "line": state["line"]}, fh)
        hot = "tomato" in state["text"].lower()
        p_none = 0.1 if hot else 0.9
        return NS(model="jev-fake", usage=NS(input_tokens=11, output_tokens=2),
                  answers={"label": NS(choice="secrets" if hot else "none", probabilities={"none": p_none, "secrets": 1 - p_none})})
'''


@pytest.fixture
def reads_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "SKILL.md").write_text(
        "---\nname: tiny\ndescription: \"A tiny skill.\"\n---\n\n# Tiny\n\nSee references/a.md.\n\nThe tomato rule applies to every file.\n",
        encoding="utf-8")
    (repo / "references").mkdir()
    (repo / "references" / "a.md").write_text("# A\n\nPlain notes.\n", encoding="utf-8")
    return repo


def machine_with(tmp_path, monkeypatch, jev, claude):
    """A machine that has what the arguments say, by fakes: `claude` is a program on a PATH folder of the test's own, and Jev is
    a key in the environment with a `typesafe_sdk` that opens no connection, found before the wall's stub. Returns the two logs."""
    logs = {"claude": tmp_path / "claude-calls", "jev": tmp_path / "jev-calls"}  # a folder each: a call writes a file of its own
    for folder in logs.values():
        folder.mkdir()
    monkeypatch.setenv("FAKE_CLAUDE_LOG", str(logs["claude"]))
    monkeypatch.setenv("FAKE_JEV_LOG", str(logs["jev"]))
    if claude:
        bin_dir = tmp_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        script = bin_dir / "fake_claude.py"
        script.write_text(FAKE_CLAUDE, encoding="utf-8")
        if os.name == "nt":
            (bin_dir / "claude.cmd").write_bytes(f'@echo off\r\n"{sys.executable}" -I "{script}" %*\r\n'.encode("utf-8"))
        else:
            shim = bin_dir / "claude"
            shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" -I "{script}" "$@"\n', encoding="utf-8")
            shim.chmod(0o755)
        monkeypatch.setenv("PATH", os.pathsep.join([str(bin_dir), os.environ["PATH"]]))
    if jev:
        sdk = tmp_path / "sdk"
        sdk.mkdir(exist_ok=True)
        (sdk / "typesafe_sdk.py").write_text(FAKE_SDK, encoding="utf-8")
        monkeypatch.setenv("PYTHONPATH", os.pathsep.join([str(sdk), os.environ.get("PYTHONPATH", "")]))
        monkeypatch.setenv("TYPESAFE_API_KEY", PLANTED)
        monkeypatch.setenv("FAKE_EXPECTED_KEY", PLANTED)
    return logs


def lines_of(folder):
    return [json.loads(p.read_text("utf-8")) for p in sorted(folder.glob("*.json"))]


def watch_the_machine(monkeypatch):
    """Everything a probe would use, watched where it starts: the real `shutil.which("claude")`, the search for the SDK
    (`importlib.util.find_spec`), and any open of the Windows registry. Nothing is refused, so the test's own machinery runs as it
    does; a call is recorded and the test asserts there is none. A registry open is recorded and refused, so no test opens the real
    registry."""
    import importlib.util
    seen = []
    real_which, real_find = shutil.which, importlib.util.find_spec

    def which(cmd, *a, **k):
        if str(cmd).lower().startswith("claude"):
            seen.append(("which", cmd))
        return real_which(cmd, *a, **k)

    def find_spec(name, *a, **k):
        if str(name).split(".")[0] == "typesafe_sdk":
            seen.append(("find_spec", name))
        return real_find(name, *a, **k)
    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(importlib.util, "find_spec", find_spec)
    winreg = sys.modules.get("winreg")
    if winreg is None:
        try:
            import winreg
        except ImportError:
            winreg = None
    def refused(*a, _name=None, **k):
        seen.append((_name,))
        raise FileNotFoundError(2, "the registry is not read here (a watched test)", _name)
    for name in ("OpenKey", "OpenKeyEx", "QueryValueEx") if winreg is not None else ():
        monkeypatch.setattr(winreg, name, lambda *a, _name=name, **k: refused(*a, _name=_name, **k))  # recorded and refused: the registry is never opened
    return seen


def front_door_with_stand_ins(monkeypatch, root):
    """The front door over a runner whose files are under `root`, and whose grader's stamps are all PASS (the grader is not what
    these tests are about); the choice each stamp was made with is returned."""
    monkeypatch.setattr(wd, "python_exe", lambda: (wd.sys.executable, []))
    monkeypatch.setattr(wd.runner, "ROOT", root)
    graded = []

    def stamps(_root, python, stages, env=None, cache=True):
        graded.append((list(stages), dict(env or {})))
        return {s: wd.runner.validate.Stamp("PASS") for s in stages}
    monkeypatch.setattr(wd.runner.validate, "stamps", stamps)
    return graded


ROWS = (  # (Jev available, claude found, the Sweep's backend, the Pinpoint's backend; None when it does not run)
    (True, True, "jev", "claude-cli:claude-opus-5-5"),
    (True, False, "jev", None),
    (False, True, "claude-cli:claude-opus-5-5", "claude-cli:claude-opus-5-5"),
)


@pytest.mark.parametrize("jev,claude,sweep,pinpoint", ROWS)
def test_a_whole_run_with_reads_on_each_row_of_the_table(reads_repo, tmp_path, monkeypatch, capsys, jev, claude, sweep, pinpoint):
    logs = machine_with(tmp_path, monkeypatch, jev, claude)
    graded = front_door_with_stand_ins(monkeypatch, tmp_path / "root")
    assert wd.main([str(reads_repo), "--name", "demo", "--reads", "claude-opus-5-5"]) == 0
    cap = capsys.readouterr()
    run = next((tmp_path / "root" / "RepoResults" / "demo").iterdir())
    assert cap.out == (run / "brief.md").read_text("utf-8")
    note = "note: --reads: Pinpoint needs the claude command, which was not found, so it does not run."
    assert cap.err.count(note) == (1 if pinpoint is None else 0) and cap.err.count("note:") == (1 if pinpoint is None else 0)
    rec = json.loads((run / "data" / "run.json").read_text("utf-8"))
    ran = {"03-sweep": sweep, "04-pinpoint": pinpoint}
    assert rec["backends"] == {k: v for k, v in ran.items() if v} and rec["chosen"] == [k for k, v in ran.items() if v]
    assert [s["stage"] for s in rec["steps"]].count("04-pinpoint") == (0 if pinpoint is None else 1)
    assert all(s["ok"] for s in rec["steps"]) and "held" not in rec
    swept = json.loads((run / "data" / "03-sweep.json").read_text("utf-8"))
    assert [(b["role"], b["backend"], b["remote"]) for b in swept["backends"]] == [("sweep", sweep.split(":")[0], True)]
    assert [f["kind"] for f in swept["findings"] if f.get("flagged")] == ["secrets"]  # the passage with the tomato rule
    # the grader's stamp is made with the choice --reads resolved to
    assert graded[0][1] == {"WALKDOWN_SOFT_SWEEP": sweep}
    # what the fakes were asked, and by whom
    claude_calls, jev_calls = lines_of(logs["claude"]), lines_of(logs["jev"])
    assert all(c["model"] == "claude-opus-5-5" and c["tools"] == "" for c in claude_calls)  # the model as typed, tools off
    assert [c["kind"] for c in claude_calls].count("pinpoint") == (0 if pinpoint is None else 1)
    passages = len([f for f in swept["findings"] if f["check"] == "soft.sweep"])
    assert passages >= 3
    assert [c["kind"] for c in claude_calls].count("sweep") == (passages if sweep.startswith("claude-cli") else 0)
    assert len(jev_calls) == (passages if sweep == "jev" else 0) and all(c["key"] for c in jev_calls)  # the key reached the client
    for page in ("summary.html", "details.html", "review.html", "full.md", "LOG.md"):
        assert (run / page).is_file(), page
    if pinpoint:
        assert json.loads((run / "data" / "04-pinpoint.json").read_text("utf-8"))["findings"]
    # the pages are the pages of the run the same options make: nothing of --reads is in the folder
    for p in run.rglob("*"):
        if p.is_file() and p.suffix in (".html", ".md", ".json", ".jsonl", ".txt"):
            assert "--reads" not in p.read_text("utf-8"), p.name


def test_reads_with_nothing_to_run_on_is_refused_before_anything_runs(reads_repo, tmp_path, monkeypatch, capsys):
    logs = machine_with(tmp_path, monkeypatch, False, False)
    graded = front_door_with_stand_ins(monkeypatch, tmp_path / "root")
    for argv in (["--reads"], ["--reads", "claude-opus-5-5"]):
        assert wd.main([str(reads_repo), "--name", "demo", *argv]) == 2
        cap = capsys.readouterr()
        assert cap.out == "" and cap.err == ("error: --reads: no model read can run here: Jev has no key or package, and no claude "
                                             "command was found.\n")
    assert not (tmp_path / "root").exists() and graded == [] and lines_of(logs["claude"]) == [] and lines_of(logs["jev"]) == []
    # a key with no package is no Jev, and a package with no key is none
    monkeypatch.setenv("TYPESAFE_API_KEY", PLANTED)
    monkeypatch.setitem(sys.modules, "typesafe_sdk", None)  # an import that is blocked
    assert wd.main([str(reads_repo), "--reads"]) == 2
    said = capsys.readouterr().err
    assert "no model read can run here" in said and PLANTED not in said
    monkeypatch.delenv("TYPESAFE_API_KEY")
    monkeypatch.setitem(sys.modules, "typesafe_sdk", type(sys)("typesafe_sdk"))  # imported, and there is no key
    assert wd.main([str(reads_repo), "--reads"]) == 2
    assert "no model read can run here" in capsys.readouterr().err


@pytest.mark.parametrize("claude", [True, False])
def test_the_key_is_in_no_output_or_file_of_a_run_with_reads(reads_repo, tmp_path, monkeypatch, capsys, claude):
    """The check that Jev is available reads the key and sends nothing; the sweep sends with it. Neither shows it: not on the
    terminal, not in the brief, not in any file of the run folder (the record, the notes, the call log, the answers, the pages). Both
    rows that run Jev are here: with `claude` there is no note, and without it the one note prints, which must not carry the key."""
    logs = machine_with(tmp_path, monkeypatch, True, claude)
    front_door_with_stand_ins(monkeypatch, tmp_path / "root")
    (tmp_path / "cwd").mkdir()
    monkeypatch.chdir(tmp_path / "cwd")  # a file written to the working folder would be under tmp_path too
    assert wd.main([str(reads_repo), "--name", "demo", "--reads", "opus"]) == 0
    cap = capsys.readouterr()
    run = next((tmp_path / "root" / "RepoResults" / "demo").iterdir())
    assert all(c["key"] for c in lines_of(logs["jev"])) and lines_of(logs["jev"])  # it did reach the client
    assert ("Pinpoint needs the claude command" in cap.err) is (not claude)  # the row without `claude` is the one that prints the note
    seen = {"stdout": cap.out, "stderr": cap.err}
    for p in tmp_path.rglob("*"):  # the run folder, the working folder, the fakes' logs: everything this test made
        if p.is_file():
            seen[p.relative_to(tmp_path).as_posix()] = p.read_bytes().decode("utf-8", "replace")
    assert len(seen) > 30 and any(k.startswith("root/RepoResults/demo/") for k in seen)  # the whole folder was looked at, and the terminal
    for where, text in seen.items():
        assert PLANTED not in text and PLANTED[:16] not in text, where
    # and the same for a run that is refused
    capsys.readouterr()
    assert wd.main([str(reads_repo), "--reads", "bad name"]) == 2
    cap = capsys.readouterr()
    assert PLANTED not in cap.out + cap.err


def test_a_default_run_probes_nothing(reads_repo, tmp_path, monkeypatch, capsys):
    """No `--reads`: in the front door's process the registry is not opened, no package is looked for, and the path is not searched for
    `claude`, and the helpers that read a key are not called. A step is a child process, outside this watch. The run is the run it was."""
    machine_with(tmp_path, monkeypatch, True, True)
    front_door_with_stand_ins(monkeypatch, tmp_path / "root")

    def probe(*a, **k):
        raise AssertionError("the machine was asked what it has")
    for name in ("available", "has_key", "read_key", "sdk_found"):
        monkeypatch.setattr(wd.options.jevkey, name, probe)
    monkeypatch.setattr(wd.options, "claude_found", probe)
    seen = watch_the_machine(monkeypatch)  # and the real calls under them: a direct `which("claude")`, `find_spec`, or registry open
    assert wd.main([str(reads_repo), "--name", "demo"]) == 0
    assert seen == [], seen
    run = next((tmp_path / "root" / "RepoResults" / "demo").iterdir())
    rec = json.loads((run / "data" / "run.json").read_text("utf-8"))
    assert not rec.get("chosen") and not rec.get("backends")
    assert not list((run / "data").glob("03-*")) and not list((run / "data").glob("04-*"))


def test_reads_reaches_the_runner_as_the_two_options_it_stands_for(audits, monkeypatch, capsys):
    for jev, claude, sweep, pinpoint in ((True, True, "jev", "claude-cli:opus"), (True, False, "jev", "none"),
                                         (False, True, "claude-cli:opus", "claude-cli:opus")):
        monkeypatch.setattr(wd.options.jevkey, "available", lambda *a, **k: jev)
        monkeypatch.setattr(wd.options, "claude_found", lambda: claude)
        audits.clear()
        wd.main(["x", "--reads", "opus"])
        a = audits[0][0]
        assert (a.sweep, a.pinpoint, a.reads) == (sweep, pinpoint, "opus")
    capsys.readouterr()
    wd.main(["x", "--sweep", "jev", "--pinpoint", "claude-cli"])  # the options that were always there are what they were
    a = audits[-1][0]
    assert (a.sweep, a.pinpoint, a.reads) == ("jev", "claude-cli", None)


def test_reads_refusals_and_the_note_through_the_front_door(audits, monkeypatch, capsys):
    monkeypatch.setattr(wd.options.jevkey, "available", lambda *a, **k: True)
    monkeypatch.setattr(wd.options, "claude_found", lambda: False)
    wd.main(["x", "--reads"])  # Jev, no claude: the run starts (the stand-in runner ends it), with one note before it
    cap = capsys.readouterr()
    assert cap.err.splitlines() == ["note: --reads: Pinpoint needs the claude command, which was not found, so it does not run.",
                                    f"Using Python at {wd.sys.executable}"]
    assert len(audits) == 1 and (audits[0][0].sweep, audits[0][0].pinpoint) == ("jev", "none")
    audits.clear()
    for argv, said in ((["x", "--reads", "--sweep", "jev"], "--reads: it cannot be given with --sweep or --pinpoint, which name the "
                                                           "reads themselves; give one or the other."),
                       (["x", "--reads", ""], "--reads: the model is empty; name one, or leave the model out."),
                       (["x", "--reads=-opus"], "--reads: '-opus' is refused: " + wd.options.MODEL_RULE),
                       (["x", "--reads", "a b"], "--reads: 'a b' is refused: " + wd.options.MODEL_RULE)):
        assert wd.main(argv) == 2
        cap = capsys.readouterr()
        assert cap.out == "" and cap.err == f"error: {said}\n", argv
    monkeypatch.setattr(wd.options.jevkey, "available", lambda *a, **k: False)
    assert wd.main(["x", "--reads"]) == 2
    assert capsys.readouterr().err == ("error: --reads: no model read can run here: Jev has no key or package, and no claude command "
                                       "was found.\n")
    assert audits == []  # none of them got as far as the runner


def test_continue_takes_reads_through_the_front_door(resumes, monkeypatch, capsys):
    monkeypatch.setattr(wd.options.jevkey, "available", lambda *a, **k: False)
    monkeypatch.setattr(wd.options, "claude_found", lambda: True)
    assert wd.main(["continue", "somewhere", "--reads", "opus"]) == 2  # the stand-in runner refuses
    a = resumes[0][1]
    assert (a.sweep, a.pinpoint, a.reads, a.continuing) == ("claude-cli:opus", "claude-cli:opus", "opus", True)
    monkeypatch.setattr(wd.options, "claude_found", lambda: False)
    assert wd.main(["continue", "somewhere", "--reads"]) == 2
    assert "error: --reads: no model read can run here: Jev has no key or package, and no claude command was found." in capsys.readouterr().err
    assert len(resumes) == 1


def test_reads_before_the_target_is_one_sentence_exit_2_and_no_traceback(tmp_path):
    """Run for real. `--reads` takes an optional value, so `walkdown.py --reads <repo>` reads the repository as the model; that
    ends the run with one sentence. Nothing here can get as far as a read: the parse fails first."""
    for argv, said in (
            (["--reads", str(tmp_path)], f"error: --reads took {wd.options.shown(str(tmp_path))} as its model and left no repository "
                                         "to audit; put the repository first, as in: walkdown.py <repo> --reads [model]\n"),
            (["--reads", "https://github.com/o/r", "--name", "x"], "error: --reads took 'https://github.com/o/r' as its model and "
                                                                    "left no repository to audit; put the repository first, as in: "
                                                                    "walkdown.py <repo> --reads [model]\n"),
            (["continue", "--reads", str(tmp_path)], f"error: --reads took {wd.options.shown(str(tmp_path))} as its model and left no run "
                                                     "folder to continue; put the run folder first, as in: walkdown.py continue "
                                                     "<run folder> --reads [model]\n")):
        p = subprocess.run([wd.sys.executable, str(ROOT / "walkdown.py"), *argv], capture_output=True, text=True, encoding="utf-8")
        assert p.returncode == 2 and p.stdout == "", p.stderr
        assert p.stderr == said and "Traceback" not in p.stderr and "usage:" not in p.stderr


def test_reads_after_the_target_with_nothing_to_run_on_is_one_sentence_exit_2_from_a_real_run(tmp_path):
    """Run for real, under the wall (no key, no `claude`, the stub for the SDK, no registry read) and behind a proxy that goes
    nowhere: the forms in the docs parse, and with nothing to read on they end before any step runs."""
    import offline_env  # the wall's own function, applied again to this process's environment: no key, no `claude`, the stub first
    env = offline_env.offline(dict(os.environ))
    env.update(HTTPS_PROXY="http://127.0.0.1:9", HTTP_PROXY="http://127.0.0.1:9", ALL_PROXY="http://127.0.0.1:9")
    env.pop("TYPESAFE_API_KEY", None)
    assert shutil.which("claude", path=env["PATH"]) is None
    for argv in ([str(tmp_path), "--reads"], [str(tmp_path), "--reads", "claude-opus-5-5"], ["continue", str(tmp_path), "--reads"]):
        p = subprocess.run([wd.sys.executable, str(ROOT / "walkdown.py"), *argv], capture_output=True, text=True, encoding="utf-8",
                           env=env, timeout=120)
        assert p.returncode == 2 and p.stdout == "", p.stderr
        assert p.stderr == ("error: --reads: no model read can run here: Jev has no key or package, and no claude command was "
                            "found.\n"), (argv, p.stderr)


def test_the_skill_asks_for_reads_with_its_own_model_id_and_only_when_the_user_asks():
    """The skill is what a chat assistant follows: model reads only when the user asks, with its own exact model ID, and it picks no
    other model."""
    flat = " ".join((ROOT / ".claude" / "skills" / "walkdown" / "SKILL.md").read_text("utf-8").split())
    assert "Add model-read flags only when the user asks for model reads." in flat
    assert "add `--reads <your own exact model ID>` after the target" in flat and "Use the ID you are loaded as, exactly." in flat
    # what Jev does: it replaces the model for Sweep, the passages go to a second service, and the user is told before the run
    assert "Pinpoint then runs on the same model you are, with its tools off." in flat
    assert ("When Jev is available here, Sweep runs on Jev in place of your model, so its passages go to TypeSafe, a second remote "
            "service, and your model reads only the passages the report shows from Sweep (flagged or near the line, with no phrase pattern "
            "inside). With no Jev, Sweep runs on your model too.") in flat
    assert ("Walkdown checks whether Jev is available when it starts; do not look for the key yourself. Before you run it, tell the "
            "user in one sentence that the text goes to the model that will run, and that Sweep's passages go to TypeSafe's Jev instead if "
            "its key and package are on this machine, and run it only on a yes.") in flat
    assert "and adds Jev" not in flat and "as well" not in flat.split("Add `--until")[0]  # the old claim: Jev added to the model
    assert ("With no `claude` command, Walkdown runs Sweep on Jev and prints one note, or, with no Jev either, refuses with one "
            "sentence; relay it as printed.") in flat
    assert "If you do not know your exact ID, add `--reads` alone, which runs `sonnet`" in flat and "and tell the user which model that is" in flat
    assert ("If you are not a Claude model, Walkdown cannot call you with tools off in this build: say so, and add nothing unless the "
            "user asks for `--sweep jev`.") in flat
    assert "Never pick another model for the user, suggest one, or add one to a command." in flat
    assert "Never choose a model" not in flat  # the line that was there
    assert "`--reads` cannot be given with them" in flat and "`--reads` there chooses only the reads that can still run" in flat
    assert "(`--reads <your own exact model ID>`, or `--sweep jev`, `--pinpoint claude-cli`)" in flat
    reads_words = flat[flat.index("Add model-read flags"):flat.index("Add `--until <step>`")]
    assert "\u2014" not in reads_words  # public words: no em-dash


def test_the_words_about_reads_say_that_jev_replaces_the_model_and_name_typesafe():
    """The words once said Jev is added to the model. In every place a reader meets them, Sweep runs on Jev when Jev is available, its
    passages go to TypeSafe, and otherwise it runs on the Claude model. The test holds the claim and pins no sentence: each place names
    TypeSafe and gives the choice as a choice, and none says the old thing."""
    def flat(rel):
        return " ".join((ROOT / rel).read_text("utf-8").split())

    def between(text, start, end):
        at = text.index(start)
        return text[at:text.index(end, at)]
    readme = flat("README.md")
    places = {
        "the help": " ".join(wd.options.READS_HELP.split()),
        "the docstring": between(" ".join(wd.__doc__.split()), "`--reads [model]` chooses", "give it after the target"),
        "the README's paragraph": between(readme, "`--reads [model]`, after the target", "- `--sweep jev`: TypeSafe"),
        "the README's table": between(readme, "| `--reads [model]` |", "| `--sweep jev`,"),
        "the CHANGELOG": between(flat("CHANGELOG.md"), "**`--reads` asks for the model reads", "- **A step that crashed is named"),
        "HOW-IT-WORKS": between(flat("docs/HOW-IT-WORKS.md"), "or with `--reads [model]`, which chooses it for you", " Then:"),
        "the contract": between(flat("stages/CONTRACT.md"), "`--reads [model]` names no backend", "so a report holds"),
        "the sweep's context": between(flat("stages/03-sweep/CONTEXT.md"), "or `--reads [model]`, which the front door", "Walkdown picks no model"),
        "the front door's spec": between(flat("specs/walkdown.SPEC.md"), "- `--reads [MODEL]` (the loaded-model build", "It is resolved once"),
        "the shared spec": between(flat("stages/_shared/specs/shared.SPEC.md"), "- **`--reads [model]`** (the loaded-model build", "Both `add_run_options`"),
        "the soft requirements": between(flat("requirements-soft.txt"), "# --reads uses whichever", "typesafe-sdk=="),
    }
    for where, text in places.items():
        assert "TypeSafe" in text, where
        assert " else " in text or " otherwise " in text, where
    for rel in ("README.md", "CHANGELOG.md", "docs/HOW-IT-WORKS.md", "specs/walkdown.SPEC.md", "stages/_shared/specs/shared.SPEC.md",
                "stages/CONTRACT.md", "stages/03-sweep/CONTEXT.md", "requirements-soft.txt", ".claude/skills/walkdown/SKILL.md", "walkdown.py",
                "stages/_shared/options.py"):
        text = flat(rel)
        for old in ("model you are loaded on", "adds Jev", "Jev for the sweep as well", "reads them too", "also reads every passage"):
            assert old not in text, (rel, old)
