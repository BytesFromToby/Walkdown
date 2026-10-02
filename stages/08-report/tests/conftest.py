import importlib.util
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))


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


def _snapshot(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): p.read_bytes()
            for p in sorted(folder.rglob("*")) if p.is_file()}


@pytest.fixture
def snapshot():
    return _snapshot


@pytest.fixture
def run_main():
    # every stage has a run.py; load this one by path under its own name
    spec = importlib.util.spec_from_file_location("walkdown_stage08_run", HERE / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.main
