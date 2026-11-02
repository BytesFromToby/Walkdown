import os
import sys
from pathlib import Path

import pytest

SHARED = Path(__file__).resolve().parents[1]
TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))
if str(SHARED) not in sys.path:
    sys.path.insert(0, str(SHARED))


@pytest.fixture(autouse=True)
def no_model_chosen_by_the_environment(monkeypatch):
    """A test run never asks a model: no AI stage is chosen through the environment, whatever the
    machine's own variables say (restructure step 5)."""
    for k in [k for k in os.environ if k.startswith("WALKDOWN_SOFT_")]:
        monkeypatch.delenv(k)


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
