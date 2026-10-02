"""Tests for pipeline.py, written from specs/pipeline.SPEC.md."""
import shutil
import sys
from pathlib import Path

from pipeline import STAGES, note_lines, run_stages

STAGES_DIR = Path(__file__).resolve().parents[2]


def test_all_stages_run(tiny_repo, tmp_path, snapshot):
    before = snapshot(tiny_repo)
    run = tmp_path / "run"
    run.mkdir()
    runs = run_stages(tiny_repo, run, STAGES_DIR, sys.executable)
    assert [r.stage for r in runs] == STAGES and all(r.ok for r in runs)
    for s in STAGES:
        assert (run / f"{s}.json").is_file() and (run / f"{s}.notes.txt").is_file()
    assert snapshot(tiny_repo) == before


def test_failed_stage_stops(tiny_repo, tmp_path):
    fake = tmp_path / "stages"
    for s in STAGES[:2]:
        shutil.copytree(STAGES_DIR / s, fake / s, ignore=shutil.ignore_patterns("tests", "__pycache__"))
    (fake / "03-graph").mkdir(parents=True)
    (fake / "03-graph" / "run.py").write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    run = tmp_path / "run"
    run.mkdir()
    runs = run_stages(tiny_repo, run, fake, sys.executable)
    assert len(runs) == 3 and runs[2].ok is False and runs[2].error
    assert not (run / "04-phrases.json").exists()


def test_note_lines():
    assert note_lines("note: a\n\n  b  \nnote: c\n") == ["a", "b", "c"]


def test_soft_flags_pass_through_and_true_is_a_bare_flag(tmp_path):
    import pipeline
    args = pipeline._args("06-soft", tmp_path, tmp_path,
                          {"label": "jev", "compare": None, "both": True})
    assert args[-3:] == ["--label", "jev", "--both"]
    args = pipeline._args("06-soft", tmp_path, tmp_path, {"label": "jev", "both": False})
    assert "--both" not in args
