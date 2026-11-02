"""Tests for readtext.py, written from specs/shared.SPEC.md, readtext."""
from readtext import PATTERN_LISTS, decode, read_row, split_lines


def test_decode():
    assert decode("héllo".encode("utf-8")) == "héllo"
    assert decode(b"\xef\xbb\xbfhi") == "hi"
    assert decode("hi".encode("utf-16")) == "hi"
    assert decode(b"ab\x00cd") is None


def test_split_lines():
    assert split_lines("a\r\nb\n") == ["a", "b"]
    assert split_lines("a\n\nb") == ["a", "", "b"]
    assert split_lines("") == []


def test_split_lines_only_on_line_feed():
    assert split_lines("one two\nthree") == ["one two", "three"]


def test_read_row_reads_text(tmp_path):
    (tmp_path / "a.md").write_bytes("héllo\r\nbye\r\n".encode("utf-8"))
    got = read_row(tmp_path, {"file": "a.md", "encoding": "utf-8"})
    assert got.text == "héllo\r\nbye\r\n" and got.size == len("héllo\r\nbye\r\n".encode("utf-8"))
    assert got.why is None and got.binary is False


def test_read_row_says_why_a_file_is_not_read(tmp_path):
    (tmp_path / "bad.bin").write_bytes(b"ab\x00cd" * 40)
    (tmp_path / ".gitignore").write_bytes(b"node_modules\n")
    rows = {
        "skip": {"file": "x", "skipped": "too large"},
        "link": {"file": "l", "type": "inode/symlink", "encoding": "utf-8"},
        "target": {"file": "l2", "target": "elsewhere", "encoding": "utf-8"},
        "png": {"file": "i.png", "type": "image/png"},
        "plain": {"file": "i.dat"},
        "ignore": {"file": ".gitignore", "encoding": "utf-8"},
        "gone": {"file": "missing.md", "encoding": "utf-8"},
        "nul": {"file": "bad.bin", "encoding": "utf-8"},
    }
    why = {k: read_row(tmp_path, r) for k, r in rows.items()}
    assert all(g.text is None for g in why.values())
    assert why["skip"].why == "unreadable: too large"
    assert why["link"].why == why["target"].why == "symlink (never followed)"
    assert why["png"].why == "not text (image/png)" and why["png"].binary
    assert why["plain"].why == "not text (binary)" and why["plain"].binary
    assert why["ignore"].why == "pattern list (not instruction text)" and not why["ignore"].binary
    assert why["gone"].why.startswith("unreadable: ") and not why["gone"].binary
    assert why["nul"].why == "undecodable text"
    assert ".gitignore" in PATTERN_LISTS


def test_read_row_checks_in_stage_4s_order(tmp_path):
    """A skip beats a symlink beats not-text beats a pattern list: the first reason is the one said."""
    assert read_row(tmp_path, {"file": ".gitignore", "skipped": "x", "type": "inode/symlink"}).why == "unreadable: x"
    assert read_row(tmp_path, {"file": ".gitignore", "type": "inode/symlink"}).why == "symlink (never followed)"
    assert read_row(tmp_path, {"file": ".gitignore"}).why == "not text (binary)"


def test_a_row_is_a_text_candidate_a_pattern_list_or_neither():
    import readtext
    text = {"file": "a/notes.md", "encoding": "utf-8"}
    listed = {"file": "a/.GitModules", "encoding": "utf-8"}
    assert readtext.text_candidate(text) and not readtext.pattern_list(text)
    assert readtext.pattern_list(listed) and not readtext.text_candidate(listed)
    for row in ({"file": ".gitignore", "encoding": "utf-8", "skipped": "x"}, {"file": ".gitignore", "encoding": "utf-8", "type": "inode/symlink"},
                {"file": ".gitignore", "encoding": "utf-8", "target": "b"}, {"file": ".gitignore"}, {"file": "a.bin"}):
        assert not readtext.pattern_list(row) and not readtext.text_candidate(row), row
