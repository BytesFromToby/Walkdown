"""Tests for run.py, written from specs/run.SPEC.md."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1] / "run.py"
STAGE1 = Path(__file__).resolve().parents[2] / "01-inventory" / "run.py"

FILES = {
    "SKILL.md": ("---\nname: t\ndescription: A test skill.\n---\n# T\n"
                 "See references/a.md for more.\n"
                 "Also references/gone.md.\n"
                 "Load every file under extra/*.md.\n"
                 "Mentions nothere.md in prose.\n"
                 "Run `absent.sh` too.\n"),
    "references/a.md": "Next: b.md\n",
    "references/b.md": "leaf\n",
    "extra/g.md": "only by glob\n",
    "lonely.md": "nobody names me\n",
    "tools/scan.py": 'import os\nfor n in os.listdir("prompts"):\n    pass\n',
    "prompts/p1.md": "p1\n",
    "prompts/p2.md": "p2\n",
    "README.md": "Run `tools/scan.py`.\n",
}


def build(root):
    for rel, text in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))


def run(*args):
    p = subprocess.run([sys.executable, str(RUN), *map(str, args)], capture_output=True)
    return p.returncode, p.stdout, p.stderr


def report(*args):
    code, out, err = run(*args)
    assert code == 0, err.decode("utf-8", "replace")
    return json.loads(out.decode("utf-8"))


def by(doc, check):
    return [f for f in doc["findings"] if f["check"] == check]


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_contract(tmp_path):
    build(tmp_path / "in")
    doc = report(tmp_path / "in")
    assert doc["stage"] == "03-graph" and doc["contract"] == 1
    for f in doc["findings"]:
        assert {"check", "file", "line"} <= set(f)


def test_graph_findings(tmp_path):
    build(tmp_path / "in")
    doc = report(tmp_path / "in")
    entries = {f["file"]: f["kind"] for f in by(doc, "graph.entry")}
    assert entries == {"SKILL.md": "skill", "README.md": "readme"}
    assert [f["file"] for f in by(doc, "graph.orphan")] == ["lonely.md"]
    dang = by(doc, "graph.dangling")
    assert {"file": "SKILL.md", "line": 7, "target": "references/gone.md",
            "context": "prose"}.items() <= next(
        d for d in dang if d["target"] == "references/gone.md").items()
    dyn = [d for d in by(doc, "graph.dynamic") if d["source"] == "glob"]
    assert len(dyn) == 1 and dyn[0]["pattern"] == "extra/*.md"
    assert dyn[0]["resolves"] == ["extra/g.md"] and dyn[0]["line"] == 8
    depth = {f["file"]: f for f in by(doc, "graph.depth")}
    assert depth["SKILL.md"]["depth"] == 0 and depth["SKILL.md"]["from"] is None
    assert depth["references/a.md"]["depth"] == 1
    assert depth["references/b.md"]["depth"] == 2
    assert depth["references/b.md"]["from"] == "references/a.md"
    assert depth["extra/g.md"]["via"] == "dynamic"
    assert "lonely.md" not in depth


def test_bare_names(tmp_path):
    build(tmp_path / "in")
    dang = by(report(tmp_path / "in"), "graph.dangling")
    assert not any(d["target"] == "nothere.md" for d in dang)
    hit = [d for d in dang if d["target"] == "absent.sh"]
    assert len(hit) == 1 and hit[0]["context"] == "code"


def test_inventory_flag(tmp_path):
    build(tmp_path / "in")
    inv = subprocess.run([sys.executable, str(STAGE1), str(tmp_path / "in")],
                         capture_output=True).stdout
    (tmp_path / "inv.json").write_bytes(inv)
    a = report(tmp_path / "in")
    b = report(tmp_path / "in", "--inventory", tmp_path / "inv.json")
    assert a == b


def test_out(tmp_path):
    build(tmp_path / "in")
    report(tmp_path / "in", "--out", tmp_path / "out")
    g = json.loads((tmp_path / "out" / "graph.json").read_text("utf-8"))
    assert g["complete"] is False
    paths = {n["path"]: n for n in g["nodes"]}
    assert paths["SKILL.md"]["entry"] == "skill" and paths["lonely.md"]["depth"] is None
    e = next(e for e in g["edges"] if e["to"] == "references/a.md")
    assert e["from"] == "SKILL.md" and e["kind"] == "static" and e["line"] == 6
    assert any(e["kind"] == "dynamic" and e["to"] == "extra/g.md" for e in g["edges"])
    code, out, _ = run(tmp_path / "in", "--out", tmp_path / "in" / "o")
    assert code != 0 and out == b"" and not (tmp_path / "in" / "o").exists()


def test_pdf_unscanned(tmp_path):
    build(tmp_path / "in")
    (tmp_path / "in" / "doc.pdf").write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<<>>\nendobj\n")
    un = by(report(tmp_path / "in"), "graph.unscanned")
    assert [u["file"] for u in un] == ["doc.pdf"] and un[0]["reason"]


def test_missing_input_and_readonly(tmp_path):
    code, out, _ = run(tmp_path / "nope")
    assert code != 0 and out == b""
    build(tmp_path / "in")
    before = snapshot(tmp_path / "in")
    report(tmp_path / "in")
    assert snapshot(tmp_path / "in") == before


def test_code_scan(tmp_path):
    build(tmp_path / "in")
    doc = report(tmp_path / "in")
    dyn = [d for d in by(doc, "graph.dynamic") if d["source"] == "code"]
    assert len(dyn) == 1 and dyn[0]["file"] == "tools/scan.py" and dyn[0]["line"] == 2
    assert dyn[0]["pattern"] == "prompts"
    assert dyn[0]["resolves"] == ["prompts/p1.md", "prompts/p2.md"]
    depth = {f["file"]: f for f in by(doc, "graph.depth")}
    assert depth["prompts/p1.md"]["depth"] == 2 and depth["prompts/p1.md"]["via"] == "dynamic"


def test_folder_mention_versus_load(tmp_path):
    # README names docs/ in prose (a mention); a manifest names skills/ (a load)
    root = tmp_path / "in"
    files = {
        "README.md": "Design notes live in docs/.\n",
        "docs/plan.md": "a plan\n",
        ".claude-plugin/plugin.json": '{"name": "x", "skills": "./skills/"}\n',
        "skills/one/SKILL.md": "---\nname: one\ndescription: One.\n---\nbody\n",
        "skills/one/extra.md": "unnamed, loaded with the folder\n",
    }
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    doc = report(root)
    depth = {f["file"]: f for f in by(doc, "graph.depth")}
    assert depth["docs/plan.md"]["via"] == "mention"
    assert depth["skills/one/extra.md"]["via"] == "dynamic"
    assert "docs/plan.md" not in {f["file"] for f in by(doc, "graph.orphan")}
    loads = {f["pattern"]: f["load"] for f in by(doc, "graph.dynamic")}
    assert loads["docs/"] is False and loads["skills/"] is True
