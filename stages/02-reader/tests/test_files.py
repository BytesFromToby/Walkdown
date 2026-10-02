"""Tests for files.py, written from specs/files.SPEC.md."""
import gzip
import io
import os
import zipfile

import pytest

import files


def test_lists_sorted_skips_git(tmp_path):
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "z.md").write_text("z")
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "HEAD").write_text("ref")
    entries = files.list_files(tmp_path)
    assert [e.rel for e in entries] == ["a.txt", "b/z.md"]
    assert all(e.kind == "file" for e in entries)


def test_symlink_not_followed(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("secret")
    root = tmp_path / "root"
    root.mkdir()
    try:
        os.symlink(outside, root / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("platform cannot create symlinks")
    entries = files.list_files(root)
    assert [(e.rel, e.kind) for e in entries] == [("link", "symlink")]
    assert entries[0].target.endswith("outside")


def _zip(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in names:
            z.writestr(n, "x")
    return buf.getvalue()


@pytest.mark.parametrize("rel,data,kind", [
    ("a.pdf", b"%PDF-1.4\n...", "pdf"),
    ("a.png", b"\x89PNG\r\n\x1a\n" + b"\0" * 20, "image"),
    ("a.docx", _zip(["word/document.xml"]), "docx"),
    ("a.xlsx", _zip(["xl/workbook.xml"]), "office-other"),
    ("a.zip", _zip(["readme.txt"]), "archive"),
    ("a.gz", gzip.compress(b"hello"), "archive"),
    ("a.md", b"# hi\n", "markdown"),
    ("a.HTML", b"<p>x</p>", "html"),
    ("a.svg", b"<svg/>", "svg"),
    ("a.py", b"print(1)\n", "text"),
    ("a.bin", b"\x00\x01\x02\xff", "binary"),
])
def test_classify(rel, data, kind):
    assert files.classify(rel, data) == kind


def test_decode():
    assert files.decode("héllo".encode("utf-8")) == ("héllo", "utf-8")
    text, enc = files.decode(b"\xef\xbb\xbfhi")
    assert text == "hi"
    text, enc = files.decode("hi".encode("utf-16"))
    assert text == "hi" and enc.startswith("utf-16")
    assert files.decode(b"a\x00b") is None


def test_split_lines():
    assert files.split_lines("a\r\nb\n") == ["a", "b"]
    assert files.split_lines("a\n\nb") == ["a", "", "b"]
    assert files.split_lines("") == []
