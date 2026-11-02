"""Tests for the coverage lines of run.py (M9 slice C), written from specs/reader.SPEC.md, run: "What the step looked at"."""
import importlib.util
import sys
from pathlib import Path

import pytest

STAGES = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1] / "run.py"
sys.path.insert(0, str(STAGES / "_shared"))

import coverlines  # noqa: E402
import pipeline  # noqa: E402
import stagelist  # noqa: E402

STAGE = "02.2-reader"
NO_TOOLS = {"tesseract": False, "tesseract_detail": "tesseract not installed",
            "playwright": False, "playwright_detail": "playwright not installed"}


def load_runner(monkeypatch):
    spec = importlib.util.spec_from_file_location("walkdown_s02_cov_run", RUN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.optional_tools = lambda: dict(NO_TOOLS)  # the same answer on every machine: no optional tool
    monkeypatch.setattr(mod.read_image, "ocr_available", lambda: (False, "tesseract not installed"))
    return mod


def folder(root):
    files = {
        "SKILL.md": "---\nname: s\ndescription: A skill.\n---\n# S\n\nThis skill explains how to write tests for the code.\n",
        "notes.txt": "These notes describe how the tests are run and where the results are kept.\n",
        "run.py": "print('hi')\n",
        "blob.bin": b"\x00\x01\x02\xff" * 40,
    }
    for rel, body in files.items():
        p = root / rel
        p.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    from PIL import Image
    Image.new("RGB", (6, 6), "white").save(root / "fixture.png")
    return root


def lines(report):
    return {x["checks"][0]: x for x in report["coverage"]}


def test_every_check_has_a_line_and_the_counts_add_up_with_no_optional_tool(tmp_path, monkeypatch):
    report = load_runner(monkeypatch).build_report(folder(tmp_path))
    assert coverlines.problems(stagelist.checks(STAGE), report) == []
    got = lines(report)
    # five files: the Markdown, the text, and the script were read; the binary is unread; the image is unread without OCR
    assert (got["read.unread"]["of"], got["read.unread"]["looked_at"], got["read.unread"]["explained"]) == (5, 3, 2)
    # the language check is to judge the Markdown, the prose text, and the image; the image is unread before it, with its skip
    assert (got["read.language"]["of"], got["read.language"]["looked_at"], got["read.language"]["explained"]) == (3, 2, 1)
    assert got["read.unread"]["found"] == 2  # the two unread rows; a skip is no result
    assert any("skipped" in f for f in report["findings"])  # the OCR skip the image's file is explained by


def test_the_object_that_was_called_coverage_is_reading_now(tmp_path, monkeypatch):
    report = load_runner(monkeypatch).build_report(folder(tmp_path))
    assert isinstance(report["coverage"], list) and set(report["reading"]) >= {"files", "files_read", "unread", "not_examined"}
    assert report["reading"]["files"] == 5 and report["reading"]["files_read"] == 3


def test_a_file_read_one_passes_over_without_saying_so_shows_as_a_shortfall(tmp_path, monkeypatch):
    """`of` is the file list and `looked_at` is counted where a branch of `read_one` reads a file: a branch that returns
    nothing for a file, with no finding and no unread row, leaves the line short."""
    runner = load_runner(monkeypatch)
    folder(tmp_path)
    real = runner.read_one

    def skipping(rel, data, kind, tools, state, session=None):
        if rel == "run.py":
            return [], None
        return real(rel, data, kind, tools, state, session)

    monkeypatch.setattr(runner, "read_one", skipping)
    report = runner.build_report(tmp_path)
    line = lines(report)["read.unread"]
    assert (line["of"], line["looked_at"], line["explained"]) == (5, 2, 2)
    assert line["looked_at"] + line["explained"] < line["of"]
    assert any("not of 5" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def test_only_a_file_with_two_readings_is_an_item_of_the_divergence_line(tmp_path, monkeypatch):
    """The text and the script file have one reading, so no divergence to look for: they are items of the first line (their lines
    are folded and their script runs found) and not of this one. The Markdown file and the picture have two."""
    mod = load_runner(monkeypatch)
    report = mod.build_report(folder(tmp_path))
    got = lines(report)
    assert got["read.unread"]["of"] == 5 and got["read.unread"]["checks"] == ["read.unread", "read.fold", "read.script"]
    assert (got["read.divergence"]["of"], got["read.divergence"]["looked_at"], got["read.divergence"]["explained"]) == (2, 2, 0)
    assert got["read.divergence"]["checks"] == ["read.divergence"]
    assert coverlines.problems(stagelist.checks(STAGE), report) == []
    real = mod.read_one
    monkeypatch.setattr(mod, "read_one", lambda rel, *a, **k: ([], None) if rel == "SKILL.md" else real(rel, *a, **k))
    report = mod.build_report(tmp_path)
    got = lines(report)["read.divergence"]
    assert (got["of"], got["looked_at"]) == (2, 1)
    assert any("read.divergence" in p and "not of 2" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def test_a_pdf_and_a_docx_are_each_counted_where_their_metadata_is_read(tmp_path, monkeypatch):
    """Metadata is read from three kinds of file (a PDF, a DOCX, a picture), each in its own branch; a branch that stopped
    counting the file it read leaves the line short. The picture of `folder` is the third."""
    import shutil
    fixtures = STAGES.parent / "Fixtures" / "02.2-reader"
    mod = load_runner(monkeypatch)
    folder(tmp_path)
    shutil.copy(fixtures / "class06-metadata.pdf", tmp_path / "paper.pdf")
    shutil.copy(fixtures / "class11-docx-hidden.docx", tmp_path / "note.docx")
    report = mod.build_report(tmp_path)
    got = lines(report)["read.metadata"]
    assert (got["of"], got["looked_at"], got["explained"]) == (3, 3, 0)
    assert {f["file"] for f in report["findings"] if f["check"] == "read.metadata"} >= {"paper.pdf"}
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_symlink_and_a_file_whose_bytes_cannot_be_read_are_each_explained_by_their_unread_row(tmp_path, monkeypatch):
    mod = load_runner(monkeypatch)
    folder(tmp_path)
    real_list, real_bytes = mod.files.list_files, Path.read_bytes
    monkeypatch.setattr(mod.files, "list_files", lambda d: [*real_list(d), mod.files.Entry("link.md", "symlink", "SKILL.md")])

    def read_bytes(self):
        if self.name == "notes.txt":
            raise OSError("denied")
        return real_bytes(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    report = mod.build_report(tmp_path)
    unread = {f["file"]: f["reason"] for f in report["findings"] if f["check"] == "read.unread"}
    assert unread["link.md"] == "symlink, not followed" and unread["notes.txt"].startswith("could not read bytes")
    got = lines(report)["read.unread"]
    assert (got["of"], got["looked_at"], got["explained"]) == (6, 2, 4)  # the Markdown and the script; the symlink, the bytes, the blob, the picture
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_prose_file_the_language_check_is_not_run_on_shows_as_a_shortfall(tmp_path, monkeypatch):
    runner = load_runner(monkeypatch)
    folder(tmp_path)

    def skipping(rel, lines_, markdown, state, line_based=True):
        return []  # the check is not run, and says nothing

    monkeypatch.setattr(runner, "language_checks", skipping)
    report = runner.build_report(tmp_path)
    got = lines(report)
    assert (got["read.language"]["of"], got["read.language"]["looked_at"], got["read.language"]["explained"]) == (3, 0, 1)
    assert got["read.unread"]["looked_at"] + got["read.unread"]["explained"] == got["read.unread"]["of"]  # the files line is whole
    assert any("read.language" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def test_an_optional_tool_that_is_absent_explains_its_items_and_leaves_no_gap(tmp_path, monkeypatch):
    """The check of the run counts the items a skip explains as explained: a run without Tesseract is a limit and no gap
    (owner, 2026-10-25)."""
    report = load_runner(monkeypatch).build_report(folder(tmp_path))
    report_json = {"stage": STAGE, "contract": 1, **report}
    assert coverlines.valid(report_json["coverage"])
    for line in report["coverage"]:
        assert line["looked_at"] + line["explained"] == line["of"]


def test_a_report_made_before_the_lines_reads_as_one_with_none(tmp_path):
    """The object that was called `coverage` is no list of lines: the report reads, and has none."""
    import json
    path = tmp_path / "02.2-reader.json"
    path.write_text(json.dumps({"stage": STAGE, "contract": 1, "findings": [], "coverage": {"files": 3}}), encoding="utf-8")
    assert coverlines.saved_lines(pipeline.read_report(path)) == []
