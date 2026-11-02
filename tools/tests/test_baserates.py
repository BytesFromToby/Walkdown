"""Tests for tools/baserates.py, written from specs/baserates.SPEC.md."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import baserates  # noqa: E402


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


def _f(pat, line, audience="model", check="phrase.L.override", **kw):
    return {"check": check, "file": "a.md", "line": line, "patterns": [pat], "audience": audience, **kw}


def test_count_lines_outside_human_files_once_per_line():
    rep = {"findings": [_f("L.ignore", 1), _f("L.ignore", 1, check="phrase.H.anti-review"),
                        _f("L.ignore", 2, audience="tool"), _f("L.ignore", 3, audience="human"),
                        _f("K.dns", 4, skipped="x"),
                        {"check": "term.def", "file": "a.md", "line": 5, "audience": "model"}]}
    assert baserates.count(rep) == {"L.ignore": 2}


def test_the_help_and_the_error_ask_for_neutral_labels(capsys, tmp_path):
    """Notes M15 b: the Library is public, so each input is labeled `repo-1`, `repo-2`, and not by
    the repository's name."""
    import pytest
    with pytest.raises(SystemExit):
        baserates.main(["--help"])
    help_text = " ".join(capsys.readouterr().out.split())
    assert "repo-1" in help_text and "neutrally" in help_text
    assert baserates.main(["no-equals-sign", "--out", str(tmp_path / "x.json")]) == 2
    assert "expected label=<folder>" in capsys.readouterr().err
    assert not (tmp_path / "x.json").exists()


def test_the_table_it_writes_carries_the_levels_the_report_reads(tmp_path, tiny_repo, monkeypatch):
    """The writer and the reader (`stages/_shared/rates.py`) agree on the three levels, and the
    table loads back through the reader."""
    import json
    import rates
    out = tmp_path / "t.json"
    assert baserates.main([f"repo-1={tiny_repo}", "--out", str(out)]) == 0
    table = json.loads(out.read_text("utf-8"))
    assert table["levels"] == rates.LEVELS and [r["name"] for r in table["repos"]] == ["repo-1"]
    assert rates.load(out) == table
