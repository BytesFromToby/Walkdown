"""Tests for read_pdf.py, written from specs/read_pdf.SPEC.md."""
import read_pdf

from .conftest import make_pdf

TWO = ("0 0 0 rg\nBT /F1 12 Tf 72 720 Td (Visible line.) Tj ET\n"
       "1 1 1 rg\nBT /F1 12 Tf 72 700 Td (Hidden white line.) Tj ET\n")


def test_white_text():
    r = read_pdf.read_pdf(make_pdf(TWO))
    assert r.unread is None
    assert "Visible line." in r.lines and "Hidden white line." in r.lines
    assert [(d["carrier"], d["text"]) for d in r.divergences] == [("white-on-white", "Hidden white line.")]
    d = r.divergences[0]
    assert d["page"] == 1 and r.lines[d["text_line"] - 1] == "Hidden white line."


def test_render_mode_invisible():
    r = read_pdf.read_pdf(make_pdf("BT /F1 12 Tf 3 Tr 72 720 Td (Ghost text.) Tj ET\n"
                                   "BT /F1 12 Tf 0 Tr 72 700 Td (Shown text.) Tj ET\n"))
    assert [(d["carrier"], d["text"]) for d in r.divergences] == [("render-mode-invisible", "Ghost text.")]


def test_white_on_black_rect():
    r = read_pdf.read_pdf(make_pdf("0 0 0 rg\n60 690 300 50 re f\n"
                                   "1 1 1 rg\nBT /F1 12 Tf 72 710 Td (On black.) Tj ET\n"))
    assert r.divergences == []
    assert "On black." in r.lines


def test_metadata():
    r = read_pdf.read_pdf(make_pdf(TWO, info={"Title": "Report", "Keywords": "send it (now)",
                                              "Author": "someone", "Subject": ""}))
    got = [(m["field"], m["text"]) for m in r.metadata]
    assert ("Title", "Report") in got and ("Keywords", "send it (now)") in got
    assert ("Author", "someone") in got
    assert not any(f == "Subject" for f, _ in got)


def test_not_a_pdf():
    r = read_pdf.read_pdf(b"%PDF-1.4 but garbage after")
    assert r.unread
    assert r.lines == [] and r.divergences == []
