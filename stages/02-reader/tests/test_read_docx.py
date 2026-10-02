"""Tests for read_docx.py, written from specs/read_docx.SPEC.md."""
import read_docx

from .conftest import make_docx


def p(text, rpr="", ppr=""):
    return (f"<w:p>{ppr}<w:r>" + (f"<w:rPr>{rpr}</w:rPr>" if rpr else "")
            + f"<w:t>{text}</w:t></w:r></w:p>")


def test_vanish():
    r = read_docx.read_docx(make_docx(p("Shown.") + p("Gone.", "<w:vanish/>")))
    assert r.unread is None
    assert [(d["carrier"], d["text"]) for d in r.divergences] == [("vanish", "Gone.")]
    assert r.divergences[0]["paragraph"] == 2 and r.divergences[0]["text_line"] == 2


def test_white_and_shading():
    body = (p("White.", '<w:color w:val="FFFFFF"/>')
            + p("On black.", '<w:color w:val="FFFFFF"/><w:shd w:val="clear" w:fill="000000"/>'))
    r = read_docx.read_docx(make_docx(body))
    assert [(d["carrier"], d["text"]) for d in r.divergences] == [("white-on-white", "White.")]


def test_style_vanish_and_override():
    styles = '<w:style w:type="paragraph" w:styleId="Secret"><w:rPr><w:vanish/></w:rPr></w:style>'
    ppr = '<w:pPr><w:pStyle w:val="Secret"/></w:pPr>'
    body = p("Styled gone.", ppr=ppr) + p("Styled back.", '<w:vanish w:val="0"/>', ppr=ppr)
    r = read_docx.read_docx(make_docx(body, styles=styles))
    assert [d["text"] for d in r.divergences] == ["Styled gone."]


def test_lines():
    r = read_docx.read_docx(make_docx(p("One.") + p("Two.", "<w:vanish/>") + "<w:p/>"))
    assert r.lines == ["One.", "Two.", ""]


def test_core_properties():
    core = "<dc:creator>Ann</dc:creator><dc:description>desc text</dc:description><dc:title/>"
    r = read_docx.read_docx(make_docx(p("x"), core=core))
    assert [(m["field"], m["text"]) for m in r.metadata] == [("creator", "Ann"),
                                                             ("description", "desc text")]


def test_not_zip():
    r = read_docx.read_docx(b"not a zip at all")
    assert r.unread and r.lines == []
