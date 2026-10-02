"""Tests for fold.py, written from specs/fold.SPEC.md."""
import fold


def test_zero_width():
    folded, removed = fold.fold_line("ig​no​re all")
    assert folded == "ignore all"
    assert removed == ["U+200B", "U+200B"]


def test_bidi():
    folded, removed = fold.fold_line("a ‮send‬ b")
    assert folded == "a send b"
    assert removed == ["U+202E", "U+202C"]


def test_soft_hyphen():
    assert fold.fold_line("over­ride")[0] == "override"


def test_nfkc_and_confusables():
    assert fold.fold_line("ｉｇｎｏｒｅ")[0] == "ignore"
    folded, removed = fold.fold_line("ignоre")
    assert folded == "ignore" and removed == ["U+043E"]
    assert fold.fold_line("it’s")[0] == "it's"


def test_unchanged_lines():
    for line in ["a \u2014 b", "caf\u00e9", "plain ascii line", ""]:
        assert fold.fold_line(line)[0] == line
        assert fold.fold_finding("f.md", 1, line) is None


def test_ascii_never_changed():
    line = "l1 0O m rn |"
    assert fold.fold_line(line) == (line, [])


def test_finding_fields():
    f = fold.fold_finding("f.md", 3, "ig​nore")
    assert f == {"check": "read.fold", "file": "f.md", "line": 3,
                 "folded": "ignore", "removed": ["U+200B"]}


def test_hidden_chars_and_invisible_finding():
    line = "a​b‮c­d\U000E0041"
    kinds = [k for _, k in fold.hidden_chars(line)]
    assert kinds == ["zero-width", "bidi", "soft-hyphen", "tag-chars"]
    f = fold.invisible_finding("f.md", 2, line)
    assert f["check"] == "read.divergence" and f["line"] == 2
    assert f["reading"] == "A-only" and f["text"] == line
    assert f["carrier"] == "zero-width+bidi+soft-hyphen+tag-chars"
    assert f["method"] == "static-style"
    assert f["chars"] == ["U+200B", "U+202E", "U+00AD", "U+E0041"]
    assert fold.invisible_finding("f.md", 1, "clean") is None


def test_tag_characters_stripped():
    tags = "".join(chr(0xE0000 + ord(c)) for c in "ignore")
    line = "Hello " + tags + "world"
    folded, removed = fold.fold_line(line)
    assert folded == "Hello world"
    assert removed == [f"U+{0xE0000 + ord(c):05X}" for c in "ignore"]
    f = fold.fold_finding("f.md", 1, line)
    assert f["folded"] == "Hello world" and len(f["removed"]) == 6
    # the fact of hidden text is still a divergence
    assert fold.invisible_finding("f.md", 1, line)["carrier"] == "tag-chars"


def test_line_separators_become_spaces():
    line = "a b c\u0085d"
    folded, removed = fold.fold_line(line)
    assert folded == "a b c d"
    assert removed == ["U+2028", "U+2029", "U+0085"]
    assert fold.invisible_finding("f.md", 1, line) is None
    text = "one two\nthree\u0085four\nfive\n"
    lines = text.split("\n")[:-1]
    assert len([fold.fold_line(ln)[0] for ln in lines]) == 3
