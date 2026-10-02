"""Tests for read_svg.py, written from specs/read_svg.SPEC.md."""
import pytest

import read_svg

SVG = b"""<!-- lead comment -->
<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200">
  <title>T words</title>
  <desc>D words</desc>
  <metadata>M words</metadata>
  <script>S words</script>
  <text x="1" y="10" fill="#000">Painted</text>
  <text x="1" y="20" fill="none">No fill</text>
  <text x="1" y="30" fill="transparent">Clear fill</text>
  <text x="1" y="40" fill="#ffffff">White page</text>
  <defs><text id="d">In defs</text></defs>
  <text x="1" y="50" style="display:none">Styled none</text>
  <rect x="0" y="100" width="200" height="40" fill="#eee"/>
  <text x="1" y="120" fill="#fff">On gray</text>
  <rect x="0" y="150" width="100%" height="50" fill="#000"/>
  <text x="1" y="170" fill="#fff">On black</text>
</svg>
"""


def got():
    return {(d["carrier"], d["line"], d["text"]) for d in read_svg.read_svg(SVG)["divergences"]}


def test_text_carriers():
    g = got()
    for item in [("comment", 1, "lead comment"), ("title", 3, "T words"), ("desc", 4, "D words"),
                 ("metadata", 5, "M words"), ("script", 6, "S words")]:
        assert item in g


def test_fills():
    g = got()
    assert ("fill:none", 8, "No fill") in g
    assert ("transparent", 9, "Clear fill") in g
    assert ("white-on-white", 10, "White page") in g
    assert "Painted" in read_svg.read_svg(SVG)["painted"]
    assert not any(t == "Painted" for _, _, t in g)


def test_rect_background():
    g = got()
    assert ("white-on-white", 14, "On gray") in g
    assert not any(t == "On black" for _, _, t in g)


def test_defs_and_style():
    g = got()
    assert ("defs", 11, "In defs") in g
    assert ("display:none", 12, "Styled none") in g


def test_dedupe_malformed_entities():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><title>Same</title><text x="1" y="1">Same</text></svg>'
    assert read_svg.read_svg(svg)["divergences"] == []
    with pytest.raises(read_svg.SvgError):
        read_svg.read_svg(b"<svg><text>unclosed</svg>")
    ent = (b'<?xml version="1.0"?><!DOCTYPE svg [<!ENTITY x "EXPANDED">]>'
           b'<svg xmlns="http://www.w3.org/2000/svg"><desc>&x;</desc></svg>')
    try:
        texts = [d["text"] for d in read_svg.read_svg(ent)["divergences"]]
    except read_svg.SvgError:
        texts = []
    assert "EXPANDED" not in texts
