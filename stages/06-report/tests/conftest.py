import importlib.util
import os
import shutil
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_shared"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # qa_support: the check of the run for a page drawn in a test


@pytest.fixture(autouse=True)
def no_model_chosen_by_the_environment(monkeypatch):
    """A test run never asks a model: no AI stage is chosen through the environment, whatever the
    machine's own variables say (restructure step 5)."""
    for k in [k for k in os.environ if k.startswith("WALKDOWN_SOFT_")]:
        monkeypatch.delenv(k)


def make_tiny_repo(base: Path) -> Path:
    repo = base / "repo"
    repo.mkdir()
    (repo / "SKILL.md").write_text(
        "---\nname: tiny\ndescription: \"A tiny skill.\"\n---\n\n# Tiny\n\nSee references/a.md.\n",
        encoding="utf-8")
    (repo / "references").mkdir()
    (repo / "references" / "a.md").write_text("# A\n\nPlain notes.\n", encoding="utf-8")
    return repo


@pytest.fixture
def tiny_repo(tmp_path):
    return make_tiny_repo(tmp_path)


def _snapshot(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): p.read_bytes()
            for p in sorted(folder.rglob("*")) if p.is_file()}


@pytest.fixture
def snapshot():
    return _snapshot


@pytest.fixture
def run_main():
    """The report stage's main: `run_main([run folder])` (or `--rerender <run folder>`)."""
    # every stage has a run.py; load this one by path under its own name
    spec = importlib.util.spec_from_file_location("walkdown_stage05_run", HERE / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main


@pytest.fixture
def audit_main():
    """The runner's main, to make a run folder: `audit_main([target, "--repo", ..., "--results", ...])`.
    It runs the steps and then the report stage on the folder."""
    import runner
    return runner.main


@pytest.fixture(scope="module")
def made_run(tmp_path_factory):
    """One finished run of a tiny skill, made once per test module (no validation, no model); a test
    asks for `run_dir` to get its own copy to change."""
    import runner
    base = tmp_path_factory.mktemp("made")
    repo = make_tiny_repo(base)
    with pytest.MonkeyPatch.context() as mp:
        for k in [k for k in os.environ if k.startswith("WALKDOWN_SOFT_")]:
            mp.delenv(k)
        assert runner.main([str(repo), "--repo", "tiny", "--results", str(base / "results"),
                            "--date", "2026-02-03", "--no-validate"]) == 0
    return next((base / "results" / "tiny").iterdir())


@pytest.fixture
def run_dir(made_run, tmp_path):
    """A copy of the finished run, in a results folder of its own."""
    dest = tmp_path / "results" / "tiny" / made_run.name
    shutil.copytree(made_run, dest)
    return dest
