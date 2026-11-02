"""Tests for the coverage lines of run.py (M9 slice C), written from specs/inventory.SPEC.md, run: "What the step looked at"."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

STAGES = Path(__file__).resolve().parents[3]
RUN = Path(__file__).resolve().parents[1] / "run.py"
sys.path.insert(0, str(STAGES / "_shared"))

import coverlines  # noqa: E402
import stagelist  # noqa: E402

STAGE = "02.1-inventory"


def load_runner():
    spec = importlib.util.spec_from_file_location("walkdown_s01_cov_run", RUN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def folder(root):
    files = {
        "skills/t/SKILL.md": "---\nname: t\ndescription: Does a thing.\n---\n# T\n",
        "agents/a.md": "---\nname: a\ndescription: Reads.\ntools: Read, Grep\n---\nBody\n",
        "hooks/hooks.json": json.dumps({"hooks": {"SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "x.sh"}]}]}}),
        "README.md": "hello\n",
        "scripts/a.py": "print(1)\n",
    }
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return root


def line_for(report, check):
    return next(x for x in report["coverage"] if check in x["checks"])


def test_every_check_has_a_line_and_the_counts_add_up_on_a_folder(tmp_path):
    report = load_runner().build_report(folder(tmp_path))
    assert coverlines.problems(stagelist.checks(STAGE), report) == []
    files = line_for(report, "inv.file")  # every entry has its facts taken and its census flags
    assert files["unit"] == "files" and files["of"] == 5 and files["looked_at"] == 5 and files["explained"] == 0
    assert files["found"] == sum(1 for f in report["findings"] if f["check"] in files["checks"])
    config = line_for(report, "struct.hooks")  # only a JSON or YAML file has a config to parse
    assert (config["of"], config["looked_at"], config["found"]) == (1, 1, 1)
    license_ = line_for(report, "inv.license")  # the three Markdown files, read for their frontmatter
    assert (license_["of"], license_["looked_at"], license_["found"]) == (3, 3, 0)
    markdown = line_for(report, "struct.description")  # only a Markdown file can have a description and a tools list
    assert (markdown["of"], markdown["looked_at"], markdown["found"]) == (3, 3, 3)  # two descriptions, one tools list
    assert line_for(report, "inv.pin") == {"checks": ["inv.pin"], "unit": "run", "of": 1, "looked_at": 1,
                                           "explained": 0, "found": 1}


def test_an_empty_folder_has_a_line_for_every_check_with_nothing_to_look_at(tmp_path):
    report = load_runner().build_report(tmp_path)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []
    files = line_for(report, "inv.file")
    assert (files["of"], files["looked_at"], files["explained"], files["found"]) == (0, 0, 0, 0)


def test_a_file_whose_bytes_cannot_be_read_is_explained_by_its_skip(tmp_path, monkeypatch):
    runner = load_runner()
    folder(tmp_path)
    real = Path.read_bytes

    def read_bytes(self):
        if self.name == "README.md":
            raise OSError("denied")
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    report = runner.build_report(tmp_path)
    skips = [f for f in report["findings"] if "skipped" in f]
    assert [f["file"] for f in skips] == ["README.md"]
    files = line_for(report, "inv.file")
    assert (files["of"], files["looked_at"], files["explained"]) == (5, 4, 1)
    for check in ("inv.license", "struct.description"):  # a Markdown name, so it was one of these lines' items
        got = line_for(report, check)
        assert (got["of"], got["looked_at"], got["explained"]) == (3, 2, 1)
    got = line_for(report, "struct.hooks")  # no JSON or YAML name, so it was never one of this line's items
    assert (got["of"], got["looked_at"], got["explained"]) == (1, 1, 0)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_file_the_checks_pass_over_without_saying_so_shows_as_a_shortfall(tmp_path, monkeypatch):
    """The point of the slice: `of` is the walk's list and `looked_at` is counted where the checks run on a file, so a pass
    that leaves a file out and writes no skip does not add up."""
    runner = load_runner()
    folder(tmp_path)
    real = runner.inspect_entry

    def skipping(w, e, acc):
        if e.rel == "agents/a.md":
            return  # no finding, no skip, nothing counted
        real(w, e, acc)

    monkeypatch.setattr(runner, "inspect_entry", skipping)
    report = runner.build_report(tmp_path)
    files = line_for(report, "inv.file")
    assert (files["of"], files["looked_at"], files["explained"]) == (5, 4, 0)
    assert files["looked_at"] + files["explained"] < files["of"]
    assert any("not of 5" in p for p in coverlines.problems(stagelist.checks(STAGE), report))
    assert not [f for f in report["findings"] if f.get("file") == "agents/a.md"]


def test_the_report_is_the_same_findings_as_before_the_lines_were_added(tmp_path):
    report = load_runner().build_report(folder(tmp_path))
    assert [f["check"] for f in report["findings"]][0] == "inv.pin"
    assert set(report) == {"stage", "contract", "findings", "coverage"}


def test_a_file_with_no_text_is_no_item_of_the_config_license_or_markdown_lines(tmp_path):
    """The hook, manifest, MCP, and license checks parse text, and the description and tools checks read a Markdown file's
    frontmatter, so a picture or a binary is counted by the facts line (every entry) and by none of those, whatever its name."""
    folder(tmp_path)
    (tmp_path / "icon.png").write_bytes(bytes([0x89]) + b"PNG" + bytes([13, 10, 26, 10]) + bytes(64))
    (tmp_path / "blob.bin").write_bytes(bytes([0, 1, 2, 255]) * 64)
    (tmp_path / "blob.json").write_bytes(bytes([0, 1, 2, 255]) * 64)
    report = load_runner().build_report(tmp_path)
    facts, config, license_, markdown = (line_for(report, c) for c in ("inv.file", "struct.hooks", "inv.license", "struct.description"))
    assert (facts["of"], facts["looked_at"]) == (8, 8)
    assert (config["of"], config["looked_at"], config["explained"]) == (1, 1, 0)
    assert (license_["of"], license_["looked_at"]) == (3, 3)
    assert (markdown["of"], markdown["looked_at"]) == (3, 3)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_line_counts_only_the_files_its_checks_read(tmp_path):
    """A script or a plain Markdown file has no config to parse, so the hook, manifest, and MCP line does not claim it; the
    license line counts license files, files that can declare a license, and Markdown, and no other file."""
    folder(tmp_path)
    for rel, text in {"a.yaml": "x: 1\n", "b.yml": "y: 2\n", ".mcp.json": "{}\n", "LICENSE": "MIT License\n",
                      "package.json": "{}\n", "pyproject.toml": "[project]\n", "notes.txt": "hello\n"}.items():
        (tmp_path / rel).write_bytes(text.encode("utf-8"))
    report = load_runner().build_report(tmp_path)
    config, license_ = line_for(report, "struct.hooks"), line_for(report, "inv.license")
    assert (config["of"], config["looked_at"]) == (5, 5)  # hooks.json, a.yaml, b.yml, .mcp.json, package.json
    assert (license_["of"], license_["looked_at"]) == (6, 6)  # the three Markdown files, LICENSE, package.json, pyproject.toml
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_file_the_structure_checks_are_not_run_on_shows_as_a_shortfall_on_its_own_line(tmp_path, monkeypatch):
    runner = load_runner()
    folder(tmp_path)
    real = runner.structure

    def skipping(acc, rel, text, doc, fm, is_hook, is_man):
        if rel == "hooks/hooks.json":
            return  # no hook config read, nothing counted
        real(acc, rel, text, doc, fm, is_hook, is_man)

    monkeypatch.setattr(runner, "structure", skipping)
    report = runner.build_report(tmp_path)
    config = line_for(report, "struct.hooks")
    assert (config["of"], config["looked_at"], config["explained"]) == (1, 0, 0)
    assert line_for(report, "inv.file")["looked_at"] == 5 and line_for(report, "struct.description")["looked_at"] == 3
    assert any("struct.hooks" in p and "not of 1" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def test_a_file_the_license_check_is_not_run_on_shows_as_a_shortfall_on_its_own_line(tmp_path, monkeypatch):
    runner = load_runner()
    folder(tmp_path)
    real = runner.structure

    def skipping(acc, rel, text, doc, fm, is_hook, is_man):
        if rel == "README.md":
            return
        real(acc, rel, text, doc, fm, is_hook, is_man)

    monkeypatch.setattr(runner, "structure", skipping)
    report = runner.build_report(tmp_path)
    got = line_for(report, "inv.license")
    assert (got["of"], got["looked_at"]) == (3, 2)
    assert line_for(report, "struct.hooks")["looked_at"] == 1
    assert any("inv.license" in p and "not of 3" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def test_a_markdown_file_the_description_check_is_not_run_on_shows_as_a_shortfall(tmp_path, monkeypatch):
    runner = load_runner()
    folder(tmp_path)
    real = runner.markdown_checks

    def skipping(acc, rel, fm, has_tools, entry_kind, counted):
        if rel == "README.md":
            return
        real(acc, rel, fm, has_tools, entry_kind, counted)

    monkeypatch.setattr(runner, "markdown_checks", skipping)
    report = runner.build_report(tmp_path)
    got = line_for(report, "struct.description")
    assert (got["of"], got["looked_at"]) == (3, 2)
    assert any("struct.description" in p and "not of 3" in p for p in coverlines.problems(stagelist.checks(STAGE), report))
