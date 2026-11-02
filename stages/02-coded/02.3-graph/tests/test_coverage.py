"""Tests for the coverage lines of run.py (M9 slice C), written from specs/graph.SPEC.md, run: "What the step looked at"."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

CODED = Path(__file__).resolve().parents[2]
STAGES = CODED.parent
sys.path.insert(0, str(STAGES / "_shared"))

import coverlines  # noqa: E402
import stagelist  # noqa: E402

STAGE = "02.3-graph"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def folder(root):
    files = {
        "SKILL.md": "---\nname: s\ndescription: A skill.\n---\nSee references/a.md and references/gone.md.\n",
        "references/a.md": "Notes. See ../scripts/run.py.\n",
        "scripts/run.py": "print('hi')\n",
        "orphan.md": "Nobody points here.\n",
        "manual.pdf": b"%PDF-1.4\n%binary document\n",
        "icon.png": b"\x89PNG\r\n\x1a\n" + b"\x00" * 40,
    }
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body if isinstance(body, bytes) else body.encode("utf-8"))
    return root


def graph_run(root):
    inventory = load("walkdown_s03_cov_inv", CODED / "02.1-inventory" / "run.py").build_report(root)
    # a second module for the graph itself: it reads the inventory it is given
    mod = load("walkdown_s03_cov_run", CODED / "02.3-graph" / "run.py")
    return mod, inventory


def lines(report):
    return {x["checks"][0]: x for x in report["coverage"]}


def test_every_check_has_a_line_and_the_counts_add_up(tmp_path):
    mod, inventory = graph_run(folder(tmp_path))
    report, _ = mod.build_report(tmp_path, inventory)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []
    got = lines(report)
    # six files, none a symlink: four hold text and are scanned, the PDF is a binary document and is explained, and the picture
    # has no text and no reference to read, so it is not one of the items of the line
    scan = got["graph.dangling"]
    assert (scan["of"], scan["looked_at"], scan["explained"]) == (5, 4, 1) and scan["unit"] == "files"
    assert scan["found"] == sum(1 for f in report["findings"] if f["check"] in scan["checks"])
    assert [x for x in report["findings"] if x["check"] == "graph.unscanned"][0]["file"] == "manual.pdf"
    assert got["graph.entry"]["of"] == got["graph.entry"]["looked_at"] >= 1
    reach = got["graph.orphan"]
    assert (reach["of"], reach["looked_at"], reach["explained"]) == (6, 6, 0)
    assert got["graph.unlisted"] == {"checks": ["graph.unlisted"], "unit": "entries", "of": 0, "looked_at": 0,
                                     "explained": 0, "found": 0}


def test_a_symlink_is_a_node_and_not_a_file_to_scan(tmp_path):
    mod, inventory = graph_run(folder(tmp_path))
    inventory["findings"].append({"check": "inv.file", "file": "link.md", "line": None, "type": "inode/symlink",
                                  "target": "SKILL.md", "ext": "md", "encoding": None})
    report, _ = mod.build_report(tmp_path, inventory)
    got = lines(report)
    assert got["graph.dangling"]["of"] == 5  # the symlink is not one of them
    assert got["graph.orphan"]["of"] == 7 and got["graph.orphan"]["looked_at"] == 7  # but it is a node of the graph
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_file_the_scan_leaves_out_without_saying_so_shows_as_a_shortfall(tmp_path, monkeypatch):
    """The point of the slice: `of` counts the inventory's files and `looked_at` is counted where `references` reads a file's
    text, so a scan that skips a file and writes no `graph.unscanned` for it does not add up."""
    mod, inventory = graph_run(folder(tmp_path))
    real = mod.references

    def skipping(rel, text):
        if rel == "references/a.md":
            return [], []  # nothing read, nothing counted
        return real(rel, text)

    monkeypatch.setattr(mod, "references", skipping)
    report, _ = mod.build_report(tmp_path, inventory)
    scan = lines(report)["graph.dangling"]
    assert (scan["of"], scan["looked_at"], scan["explained"]) == (5, 3, 1)
    assert scan["looked_at"] + scan["explained"] < scan["of"]
    assert any("graph.dangling" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def test_a_file_the_reachability_pass_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    mod, inventory = graph_run(folder(tmp_path))
    real = mod.reach_mod.reach

    def forgetful(nodes, entries, edges):
        r = real(nodes, entries, edges)
        r.orphans = [n for n in r.orphans if n != "orphan.md"]  # an orphan that is neither listed nor reached
        return r

    monkeypatch.setattr(mod.reach_mod, "reach", forgetful)
    report, _ = mod.build_report(tmp_path, inventory)
    reach = lines(report)["graph.orphan"]
    assert (reach["of"], reach["looked_at"]) == (6, 5)
    assert not [f for f in report["findings"] if f.get("file") == "orphan.md" and f["check"] == "graph.orphan"]
    assert any("graph.orphan" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def test_a_picture_is_no_item_of_the_scan_line_and_one_this_step_cannot_read_is_one_it_says_it_did_not_scan(tmp_path, monkeypatch):
    """A picture holds no reference to read, so the scan line does not count it; if the step cannot read it when it comes to it,
    that is a file it says it did not scan, and the line counts it as an item explained by that finding."""
    mod, inventory = graph_run(folder(tmp_path))
    report, _ = mod.build_report(tmp_path, inventory)
    assert (lines(report)["graph.dangling"]["of"], lines(report)["graph.dangling"]["looked_at"]) == (5, 4)
    assert not [f for f in report["findings"] if f["check"] == "graph.unscanned" and f["file"] == "icon.png"]
    real = Path.read_bytes

    def read_bytes(self):
        if self.name == "icon.png":
            raise OSError("denied")
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    report, _ = mod.build_report(tmp_path, inventory)
    scan = lines(report)["graph.dangling"]
    assert (scan["of"], scan["looked_at"], scan["explained"]) == (6, 4, 2)
    assert [f["file"] for f in report["findings"] if f["check"] == "graph.unscanned" and "denied" in f["reason"]] == ["icon.png"]
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def two_plugins(root):
    for name in ("a", "b"):
        (root / name / ".claude-plugin").mkdir(parents=True)
        (root / name / ".claude-plugin" / "plugin.json").write_text(
            f'{{"name": "{name}", "skills": "./skills/"}}', encoding="utf-8")
        (root / name / "skills" / "s").mkdir(parents=True)
        (root / name / "skills" / "s" / "SKILL.md").write_text(
            "---\nname: s\ndescription: A skill.\n---\nBody.\n", encoding="utf-8")
    return root


def test_each_manifest_is_compared_with_the_disk_and_counted_where_it_is(tmp_path):
    mod, inventory = graph_run(two_plugins(tmp_path))
    report, _ = mod.build_report(tmp_path, inventory)
    unl = lines(report)["graph.unlisted"]
    assert (unl["of"], unl["looked_at"], unl["explained"]) == (2, 2, 0)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_manifest_the_unlisted_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch, capsys):
    """The step's `main` on a folder with two manifests, the comparison given one: the count is made before it, from the
    graph's entries, and the check counts a manifest where it compares it."""
    mod, inventory = graph_run(two_plugins(tmp_path))
    saved = tmp_path.parent / (tmp_path.name + "-inventory.json")
    saved.write_text(json.dumps(inventory), encoding="utf-8")
    real = mod.unlisted
    monkeypatch.setattr(mod, "unlisted", lambda manifests, nodes, edges: real(sorted(manifests)[:1], nodes, edges))
    assert mod.main([str(tmp_path), "--inventory", str(saved)]) == 0
    printed = json.loads(capsys.readouterr().out)
    unl = {x["checks"][0]: x for x in printed["coverage"]}["graph.unlisted"]
    assert (unl["of"], unl["looked_at"], unl["explained"]) == (2, 1, 0)
    assert any("graph.unlisted" in p and "not of 2" in p for p in coverlines.problems(stagelist.checks(STAGE), printed))


def test_a_file_that_cannot_be_read_is_explained_by_its_unscanned_finding(tmp_path, monkeypatch):
    mod, inventory = graph_run(folder(tmp_path))
    real = Path.read_bytes

    def read_bytes(self):
        if self.name == "a.md":
            raise OSError("denied")
        return real(self)

    monkeypatch.setattr(Path, "read_bytes", read_bytes)
    report, _ = mod.build_report(tmp_path, inventory)
    scan = lines(report)["graph.dangling"]
    assert (scan["of"], scan["looked_at"], scan["explained"]) == (5, 3, 2)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []
