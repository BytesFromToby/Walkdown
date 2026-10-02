"""Tests for read_md.py, written from specs/read_md.SPEC.md."""
import read_md


def by(carriers, kind):
    return [c for c in carriers if c["carrier"] == kind]


def test_comments():
    text = "# T\n<!-- one -->\ntext\n<!--\nmulti\nline\n-->\n"
    cs = by(read_md.carriers(text), "comment")
    assert [(c["line"], c["text"]) for c in cs] == [(2, "one"), (4, "multi\nline")]


def test_code_is_not_a_carrier():
    text = "```html\n<!-- in fence -->\n```\nUse `<!-- inline -->` here.\n~~~\n<!-- tilde -->\n~~~\n"
    assert read_md.carriers(text) == []


def test_details():
    text = "<details>\n<summary>More</summary>\nsecret body\n</details>\n<details open>\nshown\n</details>\n"
    ds = by(read_md.carriers(text), "details")
    assert len(ds) == 1
    assert ds[0]["line"] == 1 and "secret body" in ds[0]["text"] and "More" not in ds[0]["text"]


def test_hidden_html():
    text = "a\n<div hidden>gone</div>\n<span style=\"color:red; display: none\">also gone</span>\n"
    cs = read_md.carriers(text)
    assert [(c["carrier"], c["line"], c["text"]) for c in cs] == [
        ("hidden", 2, "gone"), ("display:none", 3, "also gone")]


def test_alt_titles():
    text = ('![the alt](img.png)\n[link](http://x.invalid "the title")\n'
            '<abbr title="attr title">A</abbr>\n')
    cs = read_md.carriers(text)
    assert ("alt", 1, "the alt") in [(c["carrier"], c["line"], c["text"]) for c in cs]
    assert ("link-title", 2, "the title") in [(c["carrier"], c["line"], c["text"]) for c in cs]
    assert ("title", 3, "attr title") in [(c["carrier"], c["line"], c["text"]) for c in cs]


def test_reference_definitions():
    text = "See [used one][u].\n\n[u]: http://a.invalid\n[unused]: http://b.invalid \"t\"\n[^1]: footnote\n"
    rs = by(read_md.carriers(text), "reference-definition")
    assert [(r["line"], r["used"]) for r in rs] == [(3, True), (4, False)]
    assert rs[1]["text"] == '[unused]: http://b.invalid "t"'


def test_frontmatter_and_count():
    text = "---\nname: x\ndescription: <!-- not markdown -->\n---\n<!-- a -->\n<!-- b -->\n<!---->\n"
    cs = read_md.carriers(text)
    assert [c["line"] for c in cs] == [5, 6]
    assert read_md.comment_count(text) == 2
