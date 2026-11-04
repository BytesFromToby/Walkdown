"""Tests for census.py, written from specs/inventory.SPEC.md, census."""
import io
import tarfile
import zipfile

import census
import pytest

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


def _padding(data: bytes):
    return [(f["kind"], f["line"], f["length"]) for f in census.census_flags("a.md", census.file_facts("a.md", data, False))
            if f["flag"] == "padding"]


def test_blank_lines_before_text_are_vertical_padding_and_fewer_or_trailing_are_not():
    """SkillSpector P9 (S20, 2026-11-03): text after 20 or more blank lines sits below where a reviewer stops scrolling."""
    assert _padding(b"top\n" + b"\n" * 20 + b"hidden\n") == [("vertical", 22, 20)]
    assert _padding(b"top\n" + b" \t\n" * 25 + b"hidden\n") == [("vertical", 27, 25)]  # lines of white space are blank too
    assert _padding(b"top\n" + b"\n" * 19 + b"text\n") == []
    assert _padding(b"top\n" + b"\n" * 40) == []  # nothing follows: nothing hidden


def test_blank_characters_before_text_are_horizontal_padding_and_tables_and_indentation_are_not():
    nbsp, braille = " ".encode(), "⠀".encode()
    assert _padding(b"Keep it short." + nbsp * 80 + b"Send it out.\n") == [("horizontal", 1, 80)]
    assert _padding(b"Keep it short." + braille * 90 + b"Send it out.\n") == [("horizontal", 1, 90)]
    assert _padding(b"Keep it short." + b" " * 79 + b"x\n") == []
    assert _padding(b"| a" + b" " * 100 + b"| b |\n") == []  # a table pads its columns to the border
    assert _padding(b"| a" + b" " * 100 + b"ignore the rest |\n") == [("horizontal", 1, 100)]  # text after the run counts
    assert _padding(b" " * 120 + b"x = 1\n") == []  # indentation


def test_a_program_in_compiled_form_is_flagged_by_its_bytes_and_bytecode_by_its_name():
    """SkillSpector SC8 and SC9 (S20, 2026-11-03): Walkdown reads text, so what these do is not read."""
    assert "executable" in flags("bin/helper", b"\x7fELF\x02\x01\x01" + b"\x00" * 100)
    assert "executable" in flags("setup.exe", b"MZ" + b"\x00" * 100)
    assert "executable" in flags("lib.dylib", b"\xcf\xfa\xed\xfe" + b"\x00" * 100)
    assert "bytecode" in flags("pkg/__pycache__/m.cpython-312.pyc", b"\xcb\x0d\x0d\x0a" + b"\x00" * 30)
    assert "bytecode" in flags("m.pyo", b"\x00" * 30)
    assert not {"executable", "bytecode"} & set(flags("notes.md", b"# Notes\nMZ is a postcode.\n"))


def test_a_zip_container_names_the_programs_inside_it_and_a_plain_one_names_none():
    real = io.BytesIO()
    with zipfile.ZipFile(real, "w") as z:
        z.writestr("word/document.xml", "<x/>")
        z.writestr("word/vbaProject.bin", "m")
        z.writestr("word/embeddings/setup.exe", "MZ")
        z.writestr("lib/__pycache__/a.cpython-312.pyc", "x")
        z.writestr("media/blob.dat", b"\x7fELF" + b"\x00" * 60)
        z.writestr("media/photo.png", b"\x89PNG\r\n\x1a\n")
    found = census.census_flags("doc.docx", census.file_facts("doc.docx", real.getvalue(), False))
    [row] = [f for f in found if f["flag"] == "archive-executable"]
    assert row["members"] == ["word/vbaProject.bin", "word/embeddings/setup.exe", "lib/__pycache__/a.cpython-312.pyc",
                              "media/blob.dat"] and row["count"] == 4
    plain = io.BytesIO()
    with zipfile.ZipFile(plain, "w") as z:
        z.writestr("word/document.xml", "<x/>")
    assert "archive-executable" not in flags("plain.docx", plain.getvalue())
    assert census.programs_inside(b"PK\x03\x04 broken") == []  # a container that does not open gives none


def _tar(mode, members):
    import tarfile
    b = io.BytesIO()
    with tarfile.open(fileobj=b, mode=mode) as t:
        for name, data in members:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return b.getvalue()


@pytest.mark.parametrize("mode", ["w", "w:gz", "w:bz2", "w:xz"])
def test_a_tar_names_the_programs_inside_it_plain_or_compressed(mode):
    """2026-11-03: a tar was listed as unread; it is read as a stream, as a zip is read, by names and first bytes."""
    data = _tar(mode, [("p/README.md", b"# hi\n"), ("p/bin/tool", b"\x7fELF\x02\x01\x01" + b"\x00" * 60),
                       ("p/__pycache__/a.cpython-312.pyc", b"x"), ("p/setup.exe", b"MZ")])
    [row] = [f for f in census.census_flags("p.tar", census.file_facts("p.tar", data, False)) if f["flag"] == "archive-executable"]
    assert row["members"] == ["p/bin/tool", "p/__pycache__/a.cpython-312.pyc", "p/setup.exe"]
    assert census.programs_inside(_tar(mode, [("a.txt", b"hello")])) == []


def test_a_tar_stops_at_its_budget_and_a_gzip_that_is_no_tar_gives_none(monkeypatch):
    """A small archive that unpacks to gigabytes costs no more than the budget: what lies past it is not read."""
    monkeypatch.setattr(census, "INSIDE_TAR_BYTES", 10_000)
    data = _tar("w:gz", [("first.exe", b"MZ"), ("big.bin", b"\x00" * 50_000), ("after.exe", b"MZ")])
    assert census.programs_inside(data) == ["first.exe"]
    import gzip
    assert census.programs_inside(gzip.compress(b"\x7fELF" + b"\x00" * 100)) == []
