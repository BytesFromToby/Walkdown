"""Tests for run.py, written from specs/run.SPEC.md. Inputs are inline stage reports (--reports)."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1] / "run.py"
NAMES = {"01": "01-inventory", "02": "02-reader", "03": "03-graph", "04": "04-phrases"}


def rep(key, findings):
    return {"stage": NAMES[key], "contract": 1, "findings": findings}


S1 = [
    {"check": "inv.file", "file": "SKILL.md", "line": None, "bytes": 100, "entry_point": "skill"},
    {"check": "inv.file", "file": "agents/t.md", "line": None, "bytes": 50, "entry_point": "agent"},
    {"check": "inv.file", "file": "notes.md", "line": None, "bytes": 30, "entry_point": None},
    {"check": "struct.description", "file": "SKILL.md", "line": 3, "text": "Does things."},
    {"check": "struct.agent-tools", "file": "agents/t.md", "line": 4,
     "tools": ["WebFetch", "Read"], "description": "Reads the web."},
]
S2 = [{"check": "read.divergence", "file": "x.png", "line": None,
       "skipped": "tesseract not installed"}]
S3 = [{"check": "graph.orphan", "file": "notes.md", "line": None}]
S4 = [{"check": "phrase.L.override", "file": "notes.md", "line": 5, "quote": "Ignore all.",
       "patterns": ["L.ignore"], "audience": "model"}]


def make_reports(d, s4=None):
    d.mkdir(parents=True, exist_ok=True)
    data = {"01": S1, "02": S2, "03": S3, "04": S4 if s4 is None else s4}
    for key, name in NAMES.items():
        (d / f"{name}.json").write_text(json.dumps(rep(key, data[key])), "utf-8")
    (d / "graph.json").write_text(json.dumps({"nodes": [], "edges": []}), "utf-8")
    return d


def make_input(d):
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text("---\ndescription: Does things.\n---\n", "utf-8")
    return d


def run(*args):
    p = subprocess.run([sys.executable, str(RUN), *map(str, args)], capture_output=True)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


def tree_hash(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_report_shape(tmp_path):
    inp = make_input(tmp_path / "in")
    code, out, err = run(inp, "--reports", make_reports(tmp_path / "r"))
    assert code == 0, err
    doc = json.loads(out)
    assert doc["stage"] == "05-capability" and doc["contract"] == 1
    for f in doc["findings"]:
        for k in ("check", "file", "line", "evidence", "evidence_total"):
            assert k in f, (k, f)
    assert [f["leg"] for f in doc["findings"] if f["check"] == "cap.leg"] == [
        "private-data", "untrusted-content", "external-comms"]


ORDER = ["cap.leg", "cap.grant", "cap.injection", "cap.load-bytes", "cap.posture", "cap.pair"]


def test_order_and_three_legs(tmp_path):
    inp = make_input(tmp_path / "in")
    code, out, _ = run(inp, "--reports", make_reports(tmp_path / "r"))
    doc = json.loads(out)
    checks = [f["check"] for f in doc["findings"]]
    assert checks == sorted(checks, key=ORDER.index)
    assert set(checks) == set(ORDER)
    assert all(f["present"] for f in doc["findings"] if f["check"] == "cap.leg")
    assert sum(1 for c in checks if c == "cap.load-bytes") == 1


def test_evidence_cap_and_out(tmp_path):
    inp = make_input(tmp_path / "in")
    many = [{"check": "phrase.creds", "file": "SKILL.md", "line": i, "quote": "q",
             "patterns": ["creds.path"]} for i in range(1, 31)]
    reps = make_reports(tmp_path / "r", s4=many)
    out_dir = tmp_path / "out"
    code, out, err = run(inp, "--reports", reps, "--out", out_dir)
    assert code == 0, err
    leg = [f for f in json.loads(out)["findings"] if f.get("leg") == "private-data"][0]
    assert len(leg["evidence"]) == 20 and leg["evidence_total"] == 31
    full = json.loads((out_dir / "capability.json").read_text("utf-8"))
    leg = [f for f in full["findings"] if f.get("leg") == "private-data"][0]
    assert len(leg["evidence"]) == 31 and leg["evidence_total"] == 31
    code, out, _ = run(inp, "--reports", reps, "--out", inp / "o")
    assert code == 2 and out == ""
    assert not (inp / "o").exists()


def test_skip_carried_forward(tmp_path):
    inp = make_input(tmp_path / "in")
    code, _, err = run(inp, "--reports", make_reports(tmp_path / "r"))
    assert code == 0
    assert "x.png" in err and "tesseract not installed" in err


def test_bad_inputs(tmp_path):
    code, out, _ = run(tmp_path / "missing", "--reports", make_reports(tmp_path / "r"))
    assert code == 2 and out == ""
    inp = make_input(tmp_path / "in")
    reps = make_reports(tmp_path / "r2")
    (reps / "04-phrases.json").unlink()
    code, out, _ = run(inp, "--reports", reps)
    assert code == 2 and out == ""
    before = tree_hash(inp)
    run(inp, "--reports", make_reports(tmp_path / "r3"))
    assert tree_hash(inp) == before


def walk_keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk_keys(v)


def test_no_verdict_fields(tmp_path):
    inp = make_input(tmp_path / "in")
    _, out, _ = run(inp, "--reports", make_reports(tmp_path / "r"))
    keys = set(walk_keys(json.loads(out)))
    assert not keys & {"risk", "severity", "score", "verdict"}
