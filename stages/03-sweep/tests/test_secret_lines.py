"""A chosen model read sends no line the secret scan flagged, from specs/sweep.SPEC.md, "What is left out". Every key here is made up
when the test runs. The real steps run behind the test session's wall (the root `conftest.py`): no key, no `claude` on the PATH, and
nothing a call could reach. A stub backend stands in where a test needs an answer."""
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RUN = Path(__file__).resolve().parents[1] / "run.py"
ROOT = RUN.parents[2]
sys.path.insert(0, str(RUN.parent))
sys.path.insert(0, str(RUN.parents[1] / "_shared"))
import secretmask  # noqa: E402
_spec = importlib.util.spec_from_file_location("walkdown_stage03_run_secrets", RUN)
runmod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runmod)

CLEAN_ENV = dict(os.environ)
BACKENDS = ("jev", "claude-cli:made-up-model")
LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
UPPER = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"


def made_up(seed, n, alphabet=LETTERS):
    h = hashlib.sha256(seed.encode()).digest() * 4
    return "".join(alphabet[b % len(alphabet)] for b in h)[:n]


KEYS = {
    "aws": "AKIA" + made_up("aws", 16, UPPER),
    "github": "ghp_" + made_up("gh", 36),
    "anthropic": "sk-ant-api03-" + made_up("an", 40),
    "stripe": "sk_live_" + made_up("st", 24),
    "keyword": made_up("pw", 22),
    "alone": "AKIA" + made_up("alone", 16, UPPER),
    "second github": "ghp_" + made_up("gh2", 36),
    "repeated": "ghp_" + made_up("rep", 36),
    "in a heading": "AKIA" + made_up("head", 16, UPPER),
    "beside base64": made_up("hex", 40, "0123456789abcdef"),
    "key body 1": made_up("pem1", 64),
    "key body 2": made_up("pem2", 64),
}
READABLE = "VGhpcyBpcyBhIHBsYWluIHNlbnRlbmNlIG9mIHJlYWRhYmxlIHRleHQgaGVyZQ=="
SKILL = f"""---
name: made-up
description: A made-up skill.
---
# Setup
Set the key first: {KEYS['aws']}
Then call the service.

GITHUB_TOKEN="{KEYS['github']}"
export KEY={KEYS['anthropic']}
stripe_secret = "{KEYS['stripe']}"
password = "{KEYS['keyword']}"

# Nothing but a key
{KEYS['alone']}

# A second GitHub token
{KEYS['second github']}

# Repeated, first
token = "{KEYS['repeated']}"
Plain words after it.

# Repeated, second
Use token "{KEYS['repeated']}" again here.
More plain words.

# Heading with a key {KEYS['in a heading']}
Words under the heading.

# A private key
-----BEGIN RSA PRIVATE KEY-----
{KEYS['key body 1']}
{KEYS['key body 2']}
-----END RSA PRIVATE KEY-----
Words after the key.

# Readable base64 beside a key
data = "{READABLE}" and "{KEYS['beside base64']}"
Words after the base64.

# Plain
Nothing here at all.
"""


def make_skill(d):
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_bytes(SKILL.encode("utf-8"))
    return d


def run(*args):
    p = subprocess.run([sys.executable, str(RUN), *map(str, args)], capture_output=True, env=dict(CLEAN_ENV))
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


def holds_a_key(text):
    return [name for name, value in KEYS.items() if value in text]


@pytest.mark.parametrize("backend", BACKENDS)
def test_input_only_writes_no_flagged_key(tmp_path, backend):
    """The real inventory and phrase steps, the real scanner, and the file a person opens before choosing to send."""
    out = tmp_path / "out"
    rc, stdout, err = run(make_skill(tmp_path / "in"), "--sweep", backend, "--out", out, "--input-only")
    assert rc == 0 and stdout == "" and holds_a_key(err) == []
    sent = (out / "03-sweep.input.jsonl").read_text("utf-8")
    assert holds_a_key(sent) == []
    assert "Then call the service." in sent and "Plain words after it." in sent and "Nothing here at all." in sent
    assert "Words after the key." in sent and "Words after the base64." in sent
    assert secretmask.SECRET_MASK not in sent and "-----BEGIN" not in sent  # a blank, and no words in its place


@pytest.mark.parametrize("backend", BACKENDS)
def test_a_real_run_behind_the_wall_keeps_no_flagged_key_in_any_file(tmp_path, backend):
    """Nothing to call behind the wall, so every passage is a skip that keeps its request: the answers file holds what would have
    gone, and the report, the notes, and the call log are read too."""
    out = tmp_path / "out"
    rc, stdout, err = run(make_skill(tmp_path / "in"), "--sweep", backend, "--out", out)
    assert rc == 0 and holds_a_key(stdout) == [] and holds_a_key(err) == []
    files = sorted(out.glob("03-sweep.*"))
    assert {p.name for p in files} >= {"03-sweep.input.jsonl", "03-sweep.answers.jsonl"}
    for p in files:
        assert holds_a_key(p.read_text("utf-8")) == [], p.name


@pytest.mark.parametrize("data", [
    pytest.param(lambda t: t.encode("utf-16"), id="utf-16 with a mark"),
    pytest.param(lambda t: t.replace("First", "Fir\u00e9t").encode("latin-1"), id="latin-1"),
    pytest.param(lambda t: t.replace("First words.", "First\rwords.").encode("utf-8"), id="a lone CR above the key"),
    pytest.param(lambda t: t.replace("First words.", "First\fwords.").encode("utf-8"), id="a form feed above the key"),
    pytest.param(lambda t: t.replace("First words.", "First\u2028words.").encode("utf-8"), id="U+2028 above the key"),
])
def test_a_flagged_line_is_left_out_however_the_file_is_written(tmp_path, data):
    """The scan numbers a line through `readtext` and this step reads it through `linetext`: the mask is by number, so both must count alike."""
    inp = tmp_path / "in"
    inp.mkdir()
    (inp / "SKILL.md").write_bytes(data(f"# Rules\nFirst words.\nexport KEY={KEYS['anthropic']}\nLast words.\n"))
    out = tmp_path / "out"
    rc, _, err = run(inp, "--sweep", "jev", "--out", out, "--input-only")
    assert rc == 0 and holds_a_key(err) == []
    sent = (out / "03-sweep.input.jsonl").read_text("utf-8")
    assert holds_a_key(sent) == [] and "Last words." in sent


def test_every_line_sent_stands_at_its_own_number(tmp_path):
    out = tmp_path / "out"
    rc, _, _ = run(make_skill(tmp_path / "in"), "--sweep", "jev", "--out", out, "--input-only")
    assert rc == 0
    states = [json.loads(x)["state"] for x in (out / "03-sweep.input.jsonl").read_text("utf-8").splitlines()]
    lines = SKILL.split("\n")
    for s in states:
        spans = lines[s["line"] - 1:s["end_line"]]
        for text in s["text"].split("\n"):
            assert not text.strip() or text in spans


class Stub:
    """Answers every passage and keeps what it was given, as a service would."""
    usage = None
    model = "stub-m"

    def __init__(self):
        self.seen = []

    def request(self, c):
        return {"text": c["text"]}

    def sweep(self, chunks):
        self.seen = list(chunks)
        return [{"qid": c["qid"], "backend": "jev", "model": "stub-m", "kind": "none", "probabilities": {"none": 1.0},
                 "p_any": 0.0, "flagged": False, "request": self.request(c), "response": {"echo": c["text"]}} for c in chunks]


def reports(d, phrases, files=("SKILL.md",)):
    d.mkdir(parents=True, exist_ok=True)
    inv = [{"check": "inv.file", "file": f, "line": None, "encoding": "utf-8"} for f in files]
    for name, fs in (("02.1-inventory", inv), ("02.4-phrases", phrases)):
        (d / f"{name}.json").write_text(json.dumps({"stage": name, "contract": 1, "findings": fs}), "utf-8")
    return d


def stubbed(tmp_path, capsys, phrases, text, extra=None):
    inp = tmp_path / "in"
    inp.mkdir()
    (inp / "SKILL.md").write_text(text, "utf-8")
    for name, body in (extra or {}).items():
        (inp / name).write_text(body, "utf-8")
    files = ["SKILL.md", *(extra or {})]
    stub = Stub()
    out = tmp_path / "out"
    rc = runmod.main([str(inp), "--reports", str(reports(tmp_path / "r", phrases, files)), "--out", str(out), "--sweep", "jev"],
                     environ={}, factories={"jev": lambda data: stub})
    return rc, stub, out, capsys.readouterr()


def flagged(line, *kinds, **kw):
    return {"check": "secret.found", "file": "SKILL.md", "line": line, "kinds": list(kinds) or ["Secret Keyword"], **kw}


def test_a_stub_is_never_given_a_flagged_line_and_the_files_hold_none(tmp_path, capsys):
    secret = KEYS["keyword"]
    rc, stub, out, cap = stubbed(tmp_path, capsys, [flagged(3)], f"# Rules\nKeep it short.\npassword = {secret}\nAsk first.\n")
    assert rc == 0 and len(stub.seen) == 1
    assert stub.seen[0]["text"] == "# Rules\nKeep it short.\n\nAsk first."
    assert (stub.seen[0]["line"], stub.seen[0]["end_line"]) == (1, 4)
    for p in out.glob("03-sweep.*"):
        assert secret not in p.read_text("utf-8"), p.name
    assert secret not in cap.err and secret not in cap.out


def test_the_note_says_how_many_lines_were_left_out(tmp_path, capsys):
    _, _, _, cap = stubbed(tmp_path, capsys, [flagged(2), flagged(3)], "# Rules\nKey one\nKey two\nAsk first.\n")
    assert secretmask.left_out_note(2) in cap.err


def test_with_nothing_flagged_there_is_no_note_and_the_passage_is_as_it_was(tmp_path, capsys):
    text = "# Rules\nKeep it short.\nAsk first.\n"
    _, stub, _, cap = stubbed(tmp_path, capsys, [], text)
    assert stub.seen[0]["text"] == text.strip() and "left out" not in cap.err


def test_a_passage_with_nothing_left_is_no_passage(tmp_path, capsys):
    rc, stub, _, cap = stubbed(tmp_path, capsys, [flagged(1)], "KEY\n\n# Plain\nWords.\n")
    assert rc == 0 and [c["text"] for c in stub.seen] == ["# Plain\nWords."]
    line = json.loads(cap.out)["coverage"][0]
    assert line["of"] == line["looked_at"] == 1


def test_a_file_the_scan_could_not_read_is_not_sent_and_says_so(tmp_path, capsys):
    could_not = {"check": "secret.found", "file": "other.md", "line": None, "skipped": "the secret scan could not scan this file"}
    secret = KEYS["keyword"]
    rc, stub, out, cap = stubbed(tmp_path, capsys, [could_not], "# Rules\nKeep it short.\n", {"other.md": f"# Other\n{secret}\n"})
    assert rc == 0 and {c["file"] for c in stub.seen} == {"SKILL.md"}
    rep = json.loads(cap.out)
    assert [f for f in rep["findings"] if "skipped" in f] == [
        {"check": "soft.sweep", "file": "other.md", "line": None, "skipped": secretmask.NOT_READ}]
    assert secret not in (out / "03-sweep.input.jsonl").read_text("utf-8")
    line = rep["coverage"][0]
    assert line["of"] == line["looked_at"] == 1 and line["explained"] == 0


def test_no_scanner_sends_nothing_and_says_so_for_each_file(tmp_path, capsys):
    none = {"check": "secret.found", "file": None, "line": None, "skipped": "no secret scanner available"}
    rc, stub, out, cap = stubbed(tmp_path, capsys, [none], "# Rules\nKeep it short.\n")
    assert rc == 0 and stub.seen == []
    rep = json.loads(cap.out)
    assert [(f["file"], f["skipped"]) for f in rep["findings"]] == [("SKILL.md", secretmask.NOT_READ)]
    assert (out / "03-sweep.input.jsonl").read_text("utf-8") == ""


def test_the_skip_for_a_file_gets_no_second_line_on_the_pages(tmp_path, capsys):
    """The check of the run reads the skip finding, and a `skipped:` note too unless the passages are counted. It has one of them."""
    could_not = {"check": "secret.found", "file": "SKILL.md", "line": None, "skipped": "the secret scan could not scan this file"}
    _, _, _, cap = stubbed(tmp_path, capsys, [could_not], "# Rules\nKeep it short.\n")
    assert "skipped: soft.sweep" not in cap.err


@pytest.mark.parametrize("rel", ["agents/requirements.txt", "commands/requirements-dev.txt", "agents/.eslintrc.md", "commands/vite.config.txt"])
def test_a_model_read_file_with_a_build_name_goes_out_without_its_flagged_line(tmp_path, rel):
    """The real steps: the scan reads a file of this name, so its key is flagged and goes nowhere, and the rest of it is read as any file is."""
    inp = make_skill(tmp_path / "in")
    (inp / rel).parent.mkdir()
    (inp / rel).write_text(f"# Rules\nSet it: {KEYS['aws']}\nLast words of the file.\n", "utf-8")
    out = tmp_path / "out"
    rc, stdout, err = run(inp, "--sweep", "jev", "--out", out)
    assert rc == 0 and holds_a_key(stdout) == [] and holds_a_key(err) == []
    sent = (out / "03-sweep.input.jsonl").read_text("utf-8")
    assert holds_a_key(sent) == [] and "Last words of the file." in sent and "Nothing here at all." in sent
    assert {"check": "soft.sweep", "file": rel, "line": None, "skipped": secretmask.NOT_READ} not in json.loads(stdout)["findings"]


def test_no_lock_file_is_a_file_a_model_read_takes():
    """`ToSend` calls a file with no skip row read, and the scan writes no row for a lock file. That is safe because a read takes prose
    only and no lock file's name has a prose extension. A new name on either list has to answer this."""
    sys.path.insert(0, str(RUN.parents[1] / "02-coded" / "02.4-phrases"))
    import chunks
    import secret_scan
    for name in secret_scan.LOCK_FILES:
        assert name.rsplit(".", 1)[-1] not in chunks.PROSE_EXTS, name


def test_a_run_stopped_before_the_read_writes_no_flagged_key(tmp_path):
    """`--sweep jev --until 02.6-builder` through the runner, as `walkdown.py` starts it: the coded steps run, the input file is written,
    and nothing is sent."""
    inp, results = make_skill(tmp_path / "in"), tmp_path / "res"
    p = subprocess.run([sys.executable, str(ROOT / "stages" / "_shared" / "runner.py"), str(inp), "--sweep", "jev", "--until", "02.6-builder",
                        "--results", str(results), "--no-validate"], capture_output=True, env=dict(CLEAN_ENV))
    assert p.returncode == 0 and holds_a_key(p.stdout.decode("utf-8")) == [] and holds_a_key(p.stderr.decode("utf-8")) == []
    [sent] = list(results.rglob("03-sweep.input.jsonl"))
    assert holds_a_key(sent.read_text("utf-8")) == []
    assert list(results.rglob("03-sweep.answers.jsonl")) == []


def test_the_pages_say_what_was_left_out_and_hold_no_flagged_key(tmp_path):
    """The whole run behind the wall: no passage gets an answer, so the run is held, and `continue` writes the report with what ran."""
    inp, results = make_skill(tmp_path / "in"), tmp_path / "res"
    (inp / "agents").mkdir()
    # The library dropped this name and the read said it did not send the file; the scan reads it now (2026-11-03), so its key line
    # is one more line left out, and the rest of the file is read.
    (inp / "agents" / "swagger-notes.md").write_text(f"# Notes\ntoken = \"{KEYS['alone']}\"\n", "utf-8")
    runner = [sys.executable, str(ROOT / "stages" / "_shared" / "runner.py")]
    p = subprocess.run([*runner, str(inp), "--sweep", "jev", "--results", str(results), "--no-validate"],
                       capture_output=True, env=dict(CLEAN_ENV))
    assert p.returncode == 1  # the read got no answer: behind the wall there is no key
    [run_dir] = list(results.glob("*/*"))
    p = subprocess.run([*runner, "continue", str(run_dir), "--no-validate"], capture_output=True, env=dict(CLEAN_ENV))
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")[-400:]
    full, details = (run_dir / "full.md").read_text("utf-8"), (run_dir / "details.html").read_text("utf-8")
    for page in (full, details):
        assert secretmask.left_out_note(16) in page.replace("\n", " ")
        assert secretmask.NOT_READ not in page.replace("\n", " ")
    for p in [*run_dir.glob("*.*"), *(run_dir / "data").glob("03-sweep.*")]:
        assert holds_a_key(p.read_text("utf-8")) == [], p.name
