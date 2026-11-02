"""Tests for inputs.py, written from specs/capability.SPEC.md, inputs. Reads saved reports only; running the
earlier steps for a stage on its own is `stages/_shared/earlier_steps.py` (its tests are there)."""
import json

import pytest

import inputs

READS = ("02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases")


def report(name, findings=()):
    return {"stage": name, "contract": 1, "findings": list(findings)}


def save_dir(d, graph=True, **over):
    for name in READS:
        doc = over.get(name, report(name))
        if doc is None:
            continue
        (d / f"{name}.json").write_text(json.dumps(doc), "utf-8")
    if graph:
        (d / "graph.json").write_text(json.dumps({"nodes": [], "edges": []}), "utf-8")
    return d


def test_the_steps_it_reads_come_from_the_stage_list():
    """Restructure step 7: no table of its own; stages.json says what 02.5 reads."""
    assert inputs.READS == READS


def test_load_dir(tmp_path):
    reps, g = inputs.load_dir(save_dir(tmp_path))
    assert sorted(reps) == list(READS)  # keyed by stage name (restructure step 7b)
    assert reps["02.3-graph"]["stage"] == "02.3-graph"
    assert g == {"nodes": [], "edges": []}
    d2 = tmp_path / "b"
    d2.mkdir()
    _, g = inputs.load_dir(save_dir(d2, graph=False))
    assert g is None


def test_load_dir_errors(tmp_path):
    for i, over in enumerate([{"02.2-reader": None},
                              {"02.3-graph": report("02.4-phrases")},
                              {"02.4-phrases": dict(report("02.4-phrases"), contract=2)}]):
        d = tmp_path / str(i)
        d.mkdir()
        save_dir(d, **over)
        with pytest.raises(inputs.ReportError):
            inputs.load_dir(d)


def test_skips():
    reps = {name: report(name) for name in READS}
    reps["02.2-reader"]["findings"].append({"check": "read.divergence", "file": "a.png", "line": None,
                                            "skipped": "tesseract not installed"})
    out = inputs.skips(reps)
    assert len(out) == 1 and out[0][0] == "02.2-reader" and out[0][1]["file"] == "a.png"
