"""M9 slice A, fix round: no text of an error reaches a report.

An error from the service or the program can repeat the passage, the prompt, or the model's own words (and the Jev SDK's
carries an endpoint and a request id). This test makes a run with a Sweep and a Pinpoint whose every failing call says
all of that, and reads each file a person reads: the call logs, the step reports, section 7, the limits file, the
summary, the details, and the brief. None of the text may be in any of them. Both model reads are fakes, built with
injected clients and runners; nothing is sent, and the stages that start as subprocesses run in the offline
environment (tests/offline)."""
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stages" / "_shared"))
import runner  # noqa: E402

# Nothing here finds a model to call: the test session's wall (the root `conftest.py`, and `tests/offline`) has no key and no `claude`,
# the typesafe_sdk stub that ends the process, and no registry read of a key, for the steps that run in this process and for the
# ones that start as subprocesses.


def load_stage(folder, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "stages" / folder / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# every passage but the first is one the sweep cannot read; the words below are in them and in what the errors say
PASSAGES = {"A": "ALPHATOKEN", "B": "BRAVOTOKEN", "C": "CHARLIETOKEN", "D": "DELTATOKEN"}
SKILL = "---\nname: x\ndescription: \"A tiny skill.\"\n---\n" + "".join(
    f"\n## Part {k}\n\nSome plain notes about part {k}, {t}.\n" for k, t in PASSAGES.items())
ERROR_WORDS = ("MODELWORDS", "x.invalid", "request_id=r-77", "echoed PROMPTWORDS")


class ApiError(Exception):
    """What the SDK raises: a status, and a text with an endpoint, a request id, the passage, and the model's words."""

    def __init__(self, state, n):
        super().__init__(f"POST https://x.invalid/v1 502 bad gateway echoed {state['text']} MODELWORDS (request_id=r-77{n})")
        self.status = 502


class Client:
    """Answers the first passage (flagged, so the Pinpoint has a passage to ask about); the others fail, every time."""

    def __init__(self):
        self.n = 0

    def system_one(self, state, questions, model):
        self.n += 1
        if "ALPHATOKEN" in state["text"]:
            probs = {"none": 0.1, "skip-user": 0.9}
            ans = SimpleNamespace(type="choice", choice="skip-user", confidence=0.9, probabilities=probs)
            return SimpleNamespace(model="jev-2", usage=None, answers={"label": ans})
        raise ApiError(state, self.n)


def cli_that_fails(cmd, input=None, cwd=None, capture_output=None, timeout=None, **kw):
    said = input.decode("utf-8") + " MODELWORDS echoed PROMPTWORDS request_id=r-77"
    body = json.dumps({"type": "result", "is_error": True, "result": said})
    return SimpleNamespace(returncode=1, stdout=body.encode("utf-8"), stderr=said.encode("utf-8"))


def make_run(tmp_path, capsysbinary):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "SKILL.md").write_text(SKILL, encoding="utf-8")
    res = tmp_path / "results"
    assert runner.main([str(repo), "--repo", "x", "--results", str(res), "--date", "2026-01-02", "--no-validate"]) == 0
    capsysbinary.readouterr()
    run_dir = next((res / "x").iterdir())
    data = run_dir / "data"
    sweep, pin = load_stage("03-sweep", "m9_sweep_run"), load_stage("04-pinpoint", "m9_pin_run")
    import back_claude  # on the path now: each run.py puts its own folder there
    import back_jev
    client = Client()
    steps = []
    for mod, folder, option, factories in (
            (sweep, "03-sweep", "--sweep", {"jev": lambda d: back_jev.Jev(d, client_factory=lambda k: client,
                                                                          key_reader=lambda: "k", workers=1,
                                                                          sleep=lambda s: None)}),
            (pin, "04-pinpoint", "--pinpoint", {"claude-cli": lambda d: pin.pinpoint.Reader(d, back_claude.ClaudeCLI(
                d, runner=cli_that_fails, which=lambda n: "claude", sleep=lambda s: None))})):
        choice = "jev" if option == "--sweep" else "claude-cli"
        rc = mod.main([str(repo), "--reports", str(data), "--out", str(data), option, choice], environ={},
                      factories=factories)
        cap = capsysbinary.readouterr()
        assert rc == 0
        (data / f"{folder}.json").write_bytes(cap.out)
        (data / f"{folder}.notes.txt").write_bytes(cap.err)
        steps.append({"stage": folder, "ok": True, "started": "t0", "finished": "t1", "error": None})
    rec = json.loads((data / "run.json").read_text(encoding="utf-8"))
    rec["steps"] += steps
    (data / "run.json").write_text(json.dumps(rec), encoding="utf-8")
    (run_dir / "LOG.md").unlink()
    q = subprocess.run([sys.executable, str(ROOT / "stages" / "05-qa" / "run.py"), str(run_dir)],  # the check of the run
                       capture_output=True, text=True, env=dict(os.environ))
    assert q.returncode == 0, q.stderr
    (data / "05-qa.json").write_text(q.stdout, encoding="utf-8")  # the pages are drawn from its output (M9 slice B)
    p = subprocess.run([sys.executable, str(ROOT / "stages" / "06-report" / "run.py"), str(run_dir)],
                       capture_output=True, text=True, env=dict(os.environ))
    assert p.returncode == 0, p.stderr
    return run_dir


def test_no_text_of_an_error_reaches_a_log_a_report_a_page_or_the_brief(tmp_path, capsysbinary):
    run_dir = make_run(tmp_path, capsysbinary)
    data = run_dir / "data"
    # the files that hold the failures, and every page and the brief
    named = ["data/03-sweep.calls.jsonl", "data/04-pinpoint.calls.jsonl", "data/03-sweep.json", "data/04-pinpoint.json",
             "data/limits.md", "full.md", "summary.html", "details.html", "brief.md"]
    for rel in named:
        text = html.unescape((run_dir / rel).read_text(encoding="utf-8"))
        for words in (*ERROR_WORDS, "BRAVOTOKEN", "CHARLIETOKEN", "DELTATOKEN"):
            assert words not in text, (rel, words)
    # the logs and section 7 are where the passage and the model would show if they were kept: the flagged passage too
    for rel in ("data/03-sweep.calls.jsonl", "data/04-pinpoint.calls.jsonl", "data/limits.md"):
        assert "ALPHATOKEN" not in (run_dir / rel).read_text(encoding="utf-8"), rel
    # what is kept: the kind and the status, and the qid that names the file and line
    rows = [json.loads(x) for x in (data / "03-sweep.calls.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 4 and all(r["qid"].startswith("sweep:SKILL.md:") for r in rows)  # the file and the line
    assert all(r["first"] == {"kind": "ApiError", "status": 502} for r in rows)
    pin_rows = [json.loads(x) for x in (data / "04-pinpoint.calls.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["first"] for r in pin_rows] == [{"kind": "error", "status": 1}]
    skips = {f["skipped"] for f in json.loads((data / "03-sweep.json").read_text(encoding="utf-8"))["findings"]
             if "skipped" in f}
    assert skips == {"jev: ApiError, status 502"}


def test_section_7_counts_failures_that_differ_only_in_a_request_id_as_one_reason(tmp_path, capsysbinary):
    """Four passages fail (the front matter and three parts), each with its own request id in the error's text: one
    reason, counted 4."""
    run_dir = make_run(tmp_path, capsysbinary)
    full = (run_dir / "full.md").read_text(encoding="utf-8")
    section7 = full[full.index("## 7 "):]
    line = next(x for x in section7.splitlines() if x.startswith("- Needs a human read: "))
    assert line == ("- Needs a human read: 4 of 5 passages got no answer, after one retry. Reasons: "
                    "jev: ApiError, status 502 (4). The call log is data/03-sweep.calls.jsonl.")
    pin = next(x for x in section7.splitlines() if x.startswith("- The line behind each flag: "))
    assert pin == ("- The line behind each flag: 1 of 1 passage got no answer, after one retry. Reasons: "
                   "claude-cli: error, exit code 1 (1). The call log is data/04-pinpoint.calls.jsonl.")
    assert (run_dir / "data" / "limits.md").read_text(encoding="utf-8").count("Reasons:") == 2
