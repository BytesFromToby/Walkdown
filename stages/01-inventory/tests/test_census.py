"""Tests for census.py, written from specs/census.SPEC.md."""
import io
import tarfile
import zipfile

import census

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + b"\x00" * 20


def zip_bytes():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("inside.txt", "hi")
    return buf.getvalue()


def flags(rel, data):
    return [f["flag"] for f in census.census_flags(rel, census.file_facts(rel, data, False))]


# Done when 1
def test_extension_rule():
    assert census.ext_of("docs/a.MD") == "md"
    assert census.ext_of(".gitignore") == "gitignore"
    assert census.ext_of("LICENSE") == ""
    assert census.ext_of("x.tar.gz") == "gz"


# Done when 2
def test_decoding_encoding_and_bom():
    f = census.file_facts("a.md", "héllo\n".encode("utf-8"), False)
    assert f.text and f.encoding == "utf-8" and f.bom is False
    f = census.file_facts("a.md", b"\xef\xbb\xbfhi\n", False)
    assert f.text and f.encoding == "utf-8" and f.bom is True and f.text_value == "hi\n"
    f = census.file_facts("a.txt", b"\xff\xfe" + "hi\n".encode("utf-16-le"), False)
    assert f.text and f.encoding == "utf-16-le" and f.bom is True and f.lines == 1
    f = census.file_facts("a.bin", b"ab\x00cd", False)
    assert not f.text and f.encoding is None and f.lines is None
    assert f.type == "application/octet-stream"


# Done when 3
def test_line_count_rule():
    assert census.file_facts("a", b"", False).lines == 0
    assert census.file_facts("a", b"x", False).lines == 1
    assert census.file_facts("a", b"x\n", False).lines == 1
    assert census.file_facts("a", b"x\ny", False).lines == 2
    assert census.file_facts("a", b"x\r\ny\r\n", False).lines == 2


# Done when 4
def test_png_in_md_is_mismatch_but_not_in_png():
    assert "ext-magic-mismatch" in flags("x.md", PNG)
    assert "ext-magic-mismatch" not in flags("x.png", PNG)
    assert census.file_facts("x.md", PNG, False).type == "image/png"


# Done when 5
def test_code_fence_markdown_is_not_mismatch():
    data = b"```bash\necho hi\n```\n\n# Doc\n\nfunction x() { return 1; }\n"
    f = census.file_facts("a.md", data, False)
    assert f.type == "text/plain" and f.magic is None
    assert flags("a.md", data) == []


# Done when 6
def test_zip_is_archive_and_mismatch_only_when_misnamed():
    z = zip_bytes()
    assert flags("s.zip", z) == ["archive"]
    assert sorted(flags("s.md", z)) == ["archive", "ext-magic-mismatch"]


# Done when 7
def test_reader_window_thresholds():
    assert flags("a.md", b"x\n" * 2000) == []
    assert flags("a.md", b"x\n" * 2001) == ["reader-window"]
    exact = (b"y" * 99 + b"\n") * 500  # 50,000 bytes, short lines
    assert len(exact) == 50000 and flags("a.md", exact) == []
    assert flags("a.md", exact + b"z") == ["reader-window"]
    both = census.census_flags("a.md", census.file_facts("a.md", b"x\n" * 30000, False))
    assert len(both) == 1 and "2000" in both[0]["detail"] and both[0]["line"] is None


# Done when 8
def test_long_line_at_its_line():
    data = b"short\n" + b"a" * 501 + b"\n" + b"b" * 500 + b"\n"
    found = census.census_flags("a.md", census.file_facts("a.md", data, False))
    assert [(f["flag"], f["line"]) for f in found] == [("long-line", 2)]
    assert found[0]["length"] == 501 and "501" in found[0]["detail"]
    # characters, not bytes
    wide = ("é" * 400 + "\n").encode("utf-8")
    assert flags("a.md", wide) == []


# Done when 9
def test_bom_flag():
    found = census.census_flags("b.md", census.file_facts("b.md", b"\xef\xbb\xbf# t\n", False))
    assert [f["flag"] for f in found] == ["bom"]
    assert found[0]["check"] == "struct.census" and found[0]["file"] == "b.md"


# Done when 10
def test_symlink_facts_and_flag():
    f = census.symlink_facts("l", "../../etc")
    assert f.type == "inode/symlink" and f.bytes == len("../../etc") and f.lines is None
    flag = census.symlink_flag("l", "../../etc")
    assert flag["flag"] == "symlink" and flag["detail"] == "../../etc" and flag["file"] == "l"


# Done when 11
def test_builtin_signatures():
    assert census.builtin_magic(PNG) == "image/png"
    assert census.builtin_magic(zip_bytes()) == "application/zip"
    assert census.builtin_magic(b"\x1f\x8b\x08\x00rest") == "application/gzip"
    assert census.builtin_magic(b"%PDF-1.7\n") == "application/pdf"
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as t:
        info = tarfile.TarInfo("a.txt")
        info.size = 2
        t.addfile(info, io.BytesIO(b"hi"))
    assert census.builtin_magic(buf.getvalue()) == "application/x-tar"
    assert census.builtin_magic(b"# plain markdown\n") is None


def test_few_nuls_in_utf8_are_text():
    """2026-10-09: a literal \\0 sentinel in source made the whole file binary."""
    from census import _decode
    src = b"const s = `\x00${i}\x00`;\n" + b"x" * 400
    assert _decode(src)[0].startswith("const s")
    assert _decode(b"\x00" * 50 + b"abc") is None
    assert _decode(b"\x00\xff\xfe" + b"a" * 400) is None
