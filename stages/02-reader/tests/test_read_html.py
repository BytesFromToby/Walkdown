"""Tests for read_html.py, written from specs/read_html.SPEC.md."""
import read_html

PAGE = """<!DOCTYPE html>
<html>
<head>
<title>Guide</title>
<style>
  .gone { display: none; }
  .ghost { color: #ffffff; background: #ffffff; }
</style>
</head>
<body>
<h1>Guide</h1>
<p>Visible text here.</p>
<div class="gone">Class hidden text.</div>
<p style="display:none">Inline hidden text.</p>
<p class="ghost">White text.</p>
<!-- a comment -->
<img src="x.png" alt="Alt words">
<a href="#" title="Title words" aria-label="Label words">link</a>
<div style="visibility:hidden">Parent text <span style="visibility:visible">child shown</span></div>
<section hidden>Attr hidden.</section>
</body>
</html>
"""


def divs():
    return read_html.read_html(PAGE)["divergences"]


def find(carrier):
    return [(d["line"], d["text"]) for d in divs() if d["carrier"] == carrier]


def test_display_none():
    assert find("display:none") == [(13, "Class hidden text."), (14, "Inline hidden text.")]


def test_white_on_white():
    assert find("white-on-white") == [(15, "White text.")]
    texts = [d["text"] for d in divs()]
    assert "Visible text here." not in texts


def test_attributes_and_comments():
    assert find("comment") == [(16, "a comment")]
    assert find("alt") == [(17, "Alt words")]
    assert find("title") == [(18, "Title words")]
    assert find("aria-label") == [(18, "Label words")]


def test_visibility_child():
    assert find("visibility:hidden") == [(19, "Parent text")]
    assert "child shown" in read_html.read_html(PAGE)["painted"]


def test_title_equal_to_heading_dropped():
    assert find("document-title") == []


def test_hidden_attribute_and_painted():
    assert find("hidden") == [(20, "Attr hidden.")]
    painted = read_html.read_html(PAGE)["painted"]
    assert "Visible text here." in painted and "Guide" in painted
    assert "White text." not in painted


def test_other_title_reported_as_document_title():
    page = "<html><head>\n<title>Tab only</title>\n</head><body><p>Body</p></body></html>"
    ds = read_html.read_html(page)["divergences"]
    assert [(d["carrier"], d["line"], d["text"]) for d in ds] == [("document-title", 2, "Tab only")]
