"""Tests for linetext.py, written from specs/shared.SPEC.md, linetext (moved from the soft stage's
packet.Lines tests, restructure step 5)."""
import linetext


def test_a_file_is_decoded_with_the_encoding_stage_one_recorded(tmp_path):
    (tmp_path / "a.md").write_bytes("one\ntwo\nthree\n".encode("utf-16"))
    (tmp_path / "b.md").write_bytes(b"\xef\xbb\xbfalpha\nbeta\n")
    (tmp_path / "c.md").write_bytes("café\n".encode("latin-1"))
    lines = linetext.Lines(tmp_path, {"findings": [
        {"check": "inv.file", "file": "a.md", "encoding": "utf-16"},
        {"check": "inv.file", "file": "b.md", "encoding": "utf-8"},
        {"check": "inv.file", "file": "c.md", "encoding": "latin-1"}]})
    assert lines.lines("a.md") == ["one", "two", "three"]  # a BOM picks the codec and is dropped
    assert lines.lines("b.md") == ["alpha", "beta"]
    assert lines.lines("c.md") == ["café"]


def test_an_unknown_or_missing_encoding_reads_as_utf8_and_bad_bytes_are_replaced(tmp_path):
    (tmp_path / "a.md").write_bytes(b"ok \xff bad\n")
    assert linetext.Lines(tmp_path, None).lines("a.md") == ["ok � bad"]
    lines = linetext.Lines(tmp_path, {"findings": [
        {"check": "inv.file", "file": "a.md", "encoding": "no-such-codec"}]})
    assert lines.lines("a.md") == ["ok � bad"]


def test_lines_split_on_line_feed_only_with_one_carriage_return_removed(tmp_path):
    (tmp_path / "a.md").write_bytes(b"one\r\ntwo\xe2\x80\xa8still two\nthree\n\n")
    assert linetext.Lines(tmp_path, None).lines("a.md") == ["one", "two still two", "three", ""]
    (tmp_path / "e.md").write_bytes(b"")
    assert linetext.Lines(tmp_path, None).lines("e.md") == []


def test_a_path_outside_the_input_or_unreadable_reads_nothing(tmp_path):
    d = tmp_path / "in"
    d.mkdir()
    (tmp_path / "secret.md").write_text("x\n", "utf-8")
    lines = linetext.Lines(d, {"findings": []})
    assert lines.lines("../secret.md") is None
    assert lines.lines("missing.md") is None and lines.lines(None) is None and lines.lines("") is None


def test_a_file_is_read_once(tmp_path):
    (tmp_path / "a.md").write_text("one\n", "utf-8")
    lines = linetext.Lines(tmp_path, None)
    assert lines.lines("a.md") == ["one"]
    (tmp_path / "a.md").write_text("changed\n", "utf-8")
    assert lines.lines("a.md") == ["one"]
