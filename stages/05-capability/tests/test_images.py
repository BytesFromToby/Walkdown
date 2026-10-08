"""Tests for images.py, written from specs/images.SPEC.md."""
import images


def reports(s1=(), s2=(), s3=()):
    return {"01": {"findings": list(s1)}, "02": {"findings": list(s2)},
            "03": {"findings": list(s3)}, "04": {"findings": []}}


def inv(rel, ext, typ="application/octet-stream"):
    return {"check": "inv.file", "file": rel, "line": None, "ext": ext, "type": typ}


S1 = [inv("SKILL.md", "md", "text/plain"), inv("assets/steps.png", "png", "image/png"),
      inv("assets/banner.png", "png", "image/png"), inv("assets/flow.svg", "svg", "image/svg+xml"),
      inv("tests/shot.png", "png", "image/png"), inv("docs/logo", "", "image/png")]


def edge(src, dst, kind="static", load=None, line=3):
    return {"from": src, "to": dst, "line": line, "kind": kind, "load": load}


def test_skill_reference_pairs_with_every_source():
    g = {"edges": [edge("SKILL.md", "assets/steps.png"),
                   edge("agents/a.md", "assets/steps.png", line=9),
                   edge("SKILL.md", "assets/steps.png", line=12)]}
    [p] = images.image_pairs(reports(S1), g)
    assert (p["file"], p["pair"], p["from"]) == ("assets/steps.png", "image+loaded", "SKILL.md")
    assert p["froms"] == ["SKILL.md", "agents/a.md"] and len(p["evidence"]) == 3


def test_readme_test_data_and_mentions_do_not_pair():
    g = {"edges": [edge("README.md", "assets/banner.png"),
                   edge("tests/case.md", "tests/shot.png"),
                   edge("SKILL.md", "assets/flow.svg", kind="dynamic", load=False),
                   edge("SKILL.md", "SKILL.md")]}
    assert images.image_pairs(reports(S1), g) == []


def test_load_and_content_type_count():
    g = {"edges": [edge("SKILL.md", "docs/logo", kind="dynamic", load=True),
                   edge("SKILL.md", "tests/shot.png")]}
    assert [p["file"] for p in images.image_pairs(reports(S1), g)] == ["docs/logo", "tests/shot.png"]


def test_read_says_what_stage2_got():
    s2 = [{"check": "read.unread", "file": "assets/steps.png", "line": None,
           "reason": "image: no text layer; OCR not run (tesseract not installed)"},
          {"check": "read.divergence", "file": "assets/banner.png", "line": None,
           "carrier": "image-text"}]
    g = {"edges": [edge("SKILL.md", x) for x in
                   ("assets/steps.png", "assets/banner.png", "assets/flow.svg", "tests/shot.png")]}
    got = {p["file"]: (p["read"], p.get("reason")) for p in images.image_pairs(reports(S1, s2), g)}
    assert got["assets/steps.png"][0] == "unread" and "tesseract" in got["assets/steps.png"][1]
    assert got["assets/banner.png"] == ("ocr-text", None)
    assert got["assets/flow.svg"] == ("svg", None)
    assert got["tests/shot.png"] == ("ocr-empty", None)


def test_graph_depth_stands_in_without_graph_json():
    s3 = [{"check": "graph.depth", "file": "assets/steps.png", "line": None, "via": "static",
           "from": "SKILL.md", "depth": 1},
          {"check": "graph.depth", "file": "assets/banner.png", "line": None, "via": "mention",
           "from": "SKILL.md", "depth": 1}]
    assert [p["file"] for p in images.image_pairs(reports(S1, s3=s3))] == ["assets/steps.png"]


def test_manifest_and_config_references_do_not_pair():
    g = {"edges": [dict(edge(".codex-plugin/plugin.json", "assets/flow.svg"), form="config"),
                   edge("settings.yaml", "assets/steps.png"),
                   dict(edge(".claude-plugin/marketplace.json", "assets/banner.png",
                             kind="dynamic", load=True), form="config")]}
    assert images.image_pairs(reports(S1), g) == []
