"""Tests for upstream.py, written from specs/upstream.SPEC.md. Fake runners print canned reports."""
import json
import sys

import pytest

import upstream

NAMES = upstream.NAMES


def rep(key, findings=()):
    return {"stage": NAMES[key], "contract": 1, "findings": list(findings)}


def write_reports(d, keys=("01", "02", "03", "04", "05")):
    d.mkdir(parents=True, exist_ok=True)
    for k in keys:
        (d / f"{NAMES[k]}.json").write_text(json.dumps(rep(k)), "utf-8")
    return d


def test_load_dir_all_five(tmp_path):
    r = upstream.load_dir(write_reports(tmp_path / "r"))
    assert sorted(r) == ["01", "02", "03", "04", "05"]
    assert r["05"]["stage"] == "05-capability"


def test_load_dir_required_only(tmp_path):
    r = upstream.load_dir(write_reports(tmp_path / "r", ("01", "04", "05")))
    assert sorted(r) == ["01", "04", "05"]


def test_missing_required_raises(tmp_path):
    with pytest.raises(upstream.ReportError):
        upstream.load_dir(write_reports(tmp_path / "r", ("01", "04")))


def test_wrong_stage_or_contract_raises(tmp_path):
    d = write_reports(tmp_path / "r")
    (d / "04-phrases.json").write_text(json.dumps({"stage": "03-graph", "contract": 1,
                                                    "findings": []}), "utf-8")
    with pytest.raises(upstream.ReportError, match="04-phrases"):
        upstream.load_dir(d)
    d2 = write_reports(tmp_path / "r2")
    (d2 / "05-capability.json").write_text(json.dumps({"stage": "05-capability", "contract": 2,
                                                       "findings": []}), "utf-8")
    with pytest.raises(upstream.ReportError):
        upstream.load_dir(d2)


FAKE = r'''
import json, sys
from pathlib import Path
name = {name!r}
args = sys.argv[1:]
log = Path({log!r})
with log.open("a", encoding="utf-8") as fh:
    fh.write(json.dumps({{"stage": name, "args": args}}) + "\n")
if name == "03-graph":
    out = Path(args[args.index("--out") + 1])
    (out / "graph.json").write_text("{{}}", encoding="utf-8")
if name == "05-capability":
    rd = Path(args[args.index("--reports") + 1])
    have = sorted(p.name for p in rd.glob("*.json"))
    print(json.dumps({{"stage": name, "contract": 1, "findings": [], "saw": have}}))
else:
    if {fail!r} == name:
        sys.exit(3)
    print(json.dumps({{"stage": name, "contract": 1, "findings": []}}))
'''


def make_stages(root, log, fail=None):
    for k, name in NAMES.items():
        d = root / name
        d.mkdir(parents=True)
        (d / "run.py").write_text(FAKE.format(name=name, log=str(log), fail=fail), "utf-8")
    return root


def test_run_stages_passes_inventory_and_reports(tmp_path):
    log = tmp_path / "log.jsonl"
    stages = make_stages(tmp_path / "stages", log)
    work = tmp_path / "work"
    work.mkdir()
    inp = tmp_path / "in"
    inp.mkdir()
    r = upstream.run_stages(inp, stages, sys.executable, work)
    assert sorted(r) == ["01", "02", "03", "04", "05"]
    calls = [json.loads(line) for line in log.read_text("utf-8").splitlines()]
    by = {c["stage"]: c["args"] for c in calls}
    inv = str(work / "01-inventory.json")
    assert by["03-graph"][by["03-graph"].index("--inventory") + 1] == inv
    assert by["04-phrases"][by["04-phrases"].index("--inventory") + 1] == inv
    assert by["05-capability"][by["05-capability"].index("--reports") + 1] == str(work)
    assert {"01-inventory.json", "02-reader.json", "03-graph.json",
            "04-phrases.json"} <= set(r["05"]["saw"])


def test_failing_runner_raises_stage_failure(tmp_path):
    stages = make_stages(tmp_path / "stages", tmp_path / "log", fail="02-reader")
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(upstream.StageFailure, match="02-reader"):
        upstream.run_stages(tmp_path, stages, sys.executable, work)


def test_skips_lists_stage():
    reports = {"02": {"findings": [{"check": "read.divergence", "skipped": "no tesseract"}]},
               "04": {"findings": [{"check": "phrase.x"}]}}
    assert upstream.skips(reports) == [("02", {"check": "read.divergence",
                                                "skipped": "no tesseract"})]
