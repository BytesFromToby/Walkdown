"""Tests for colors.py, written from specs/colors.SPEC.md."""
import colors


def test_parse_white_forms():
    for v in ["#fff", "#ffffff", "FFFFFF", "white", "WHITE", "rgb(255,255,255)",
              "rgb(100%, 100%, 100%)", "#ffffff !important"]:
        assert colors.parse(v)[:3] == (255, 255, 255), v
    assert colors.parse("transparent")[3] == 0
    assert colors.parse("none") is None
    assert colors.parse("auto") is None
    assert colors.parse("garbage(") is None


def test_hides_white():
    w = colors.parse("#fff")
    assert colors.hides(w, colors.WHITE)
    assert colors.carrier(w, colors.WHITE) == "white-on-white"
    assert colors.hides(w, colors.parse("#eee"))
    assert not colors.hides(colors.parse("black"), colors.WHITE)


def test_black_on_black():
    b = colors.parse("#000")
    assert colors.hides(b, b)
    assert colors.carrier(b, b) == "color-matches-background"


def test_contrast():
    assert round(colors.contrast(colors.parse("#000"), colors.WHITE), 2) == 21.0
