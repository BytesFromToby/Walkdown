"""Tests for inputs.py, written from specs/inputs.SPEC.md. Fake runners only; no real stage runs."""
import json
import sys

import pytest

import inputs

NAMES = {"01": "01-inventory", "02": "02-reader", "03": "03-graph", "04": "04-phrases"}


def report(key, findings=()):
    return {"stage": NAMES[key], "contract": 1, "findings": list(findings)}


def save_dir(d, graph=True, **over):
    for key, name in NAMES.items():
        doc = over.get(f"r{key}", report(key))
        if doc is None:
            continue
        (d / f"{name}.json").write_text(json.dumps(doc), "utf-8")
    if graph:
        (d / "graph.json").write_text(json.dumps({"nodes": [], "edges": []}), "utf-8")
    return d


def test_load_dir(tmp_path):
    reps, g = inputs.load_dir(save_dir(tmp_path))
    assert sorted(reps) == ["01", "02", "03", "04"]
    assert reps["03"]["stage"] == "03-graph"
    assert g == {"nodes": [], "edges": []}
    d2 = tmp_path / "b"
    d2.mkdir()
    _, g = inputs.load_dir(save_dir(d2, graph=False))
    assert g is None


def test_load_dir_errors(tmp_path):
    for i, over in enumerate([{"r02": None},
                              {"r03": report("04")},
                              {"r04": dict(report("04"), contract=2)}]):
        d = tmp_path / str(i)
        d.mkdir()
        save_dir(d, **over)
        with pytest.raises(inputs.ReportError):
            inputs.load_dir(d)


FAKE = """import json, sys, pathlib
args = sys.argv[1:]
log = pathlib.Path(__file__).parent / "args.json"
log.write_text(json.dumps(args))
if "--out" in args:
    out = pathlib.Path(args[args.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "graph.json").write_text(json.dumps({"nodes": [], "edges": [], "fake": True}))
if %(fail)s:
    sys.stderr.write("boom")
    sys.exit(3)
print(json.dumps({"stage": %(stage)r, "contract": 1, "findings": []}))
"""


def fake_stages(root, fail=None):
    for key, name in NAMES.items():
        d = root / name
        d.mkdir(parents=True)
        (d / "run.py").write_text(FAKE % {"stage": name, "fail": key == fail}, "utf-8")
    return root


def test_run_stages(tmp_path):
    stages = fake_stages(tmp_path / "stages")
    inp = tmp_path / "input"
    inp.mkdir()
    work = tmp_path / "work"
    work.mkdir()
    reps, g = inputs.run_stages(inp, stages, sys.executable, work)
    assert [reps[k]["stage"] for k in sorted(reps)] == list(NAMES.values())
    assert g.get("fake") is True
    saved = str(work / "01-inventory.json")
    for name in ("03-graph", "04-phrases"):
        args = json.loads((stages / name / "args.json").read_text())
        assert args[args.index("--inventory") + 1] == saved
    assert json.loads((work / "01-inventory.json").read_text())["stage"] == "01-inventory"


def test_run_stages_failure(tmp_path):
    stages = fake_stages(tmp_path / "stages", fail="02")
    inp = tmp_path / "input"
    inp.mkdir()
    work = tmp_path / "work"
    work.mkdir()
    with pytest.raises(inputs.StageFailure) as exc:
        inputs.run_stages(inp, stages, sys.executable, work)
    assert "02-reader" in str(exc.value)


def test_skips():
    reps = {k: report(k) for k in NAMES}
    reps["02"]["findings"].append({"check": "read.divergence", "file": "a.png", "line": None,
                                   "skipped": "tesseract not installed"})
    out = inputs.skips(reps)
    assert len(out) == 1 and out[0][0] == "02" and out[0][1]["file"] == "a.png"
