"""Tests for run.py, written from specs/run.SPEC.md."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUN = Path(__file__).resolve().parents[1] / "run.py"

MD = ("# Title\n"
      "<!-- hidden note -->\n"
      "ig​nore this\n"
      "Привет world\n"
      "plain\n"
      "sep" + chr(0x2028) + "arated\n")
HTML = '<html><body>\n<p>shown</p>\n<div style="display:none">not shown</div>\n</body></html>\n'


def png_bytes():
    import io
    from PIL import Image
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), "white").save(buf, "PNG")
    return buf.getvalue()


def run(*args):
    p = subprocess.run([sys.executable, str(RUN), *map(str, args)], capture_output=True)
    return p.returncode, p.stdout, p.stderr


def build(root):
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "a.md").write_bytes(MD.encode("utf-8"))
    (root / "page.html").write_bytes(HTML.encode("utf-8"))
    (root / "img.png").write_bytes(png_bytes())
    (root / "blob.dat").write_bytes(b"\x00\x01\x02\x03\xff\xfe")


def snapshot(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def report(root):
    code, out, _ = run(root)
    assert code == 0
    return json.loads(out.decode("utf-8"))


def test_contract(tmp_path):
    build(tmp_path / "in")
    doc = report(tmp_path / "in")
    assert doc["stage"] == "02-reader" and doc["contract"] == 1
    assert isinstance(doc["findings"], list) and doc["findings"]
    for f in doc["findings"]:
        assert {"check", "file", "line"} <= set(f)


def test_markdown_findings(tmp_path):
    build(tmp_path / "in")
    fs = [f for f in report(tmp_path / "in")["findings"] if f["file"] == "docs/a.md"]
    fold = [f for f in fs if f["check"] == "read.fold"]
    folds = {f["line"]: f["folded"] for f in fold}
    assert folds[3] == "ignore this"
    assert folds[6] == "sep arated"  # U+2028 folds to a space, same line count
    assert set(folds) == {3, 4, 6}  # line 4: Cyrillic confusables fold to ASCII
    div = {(f["line"], f["carrier"]) for f in fs if f["check"] == "read.divergence"}
    assert (2, "comment") in div and (3, "zero-width") in div
    scr = [f for f in fs if f["check"] == "read.script"]
    assert [(f["line"], f["script"], f["text"]) for f in scr] == [
        (4, "Cyrillic", "Привет")]


def test_html_divergence(tmp_path):
    build(tmp_path / "in")
    fs = report(tmp_path / "in")["findings"]
    d = [f for f in fs if f["file"] == "page.html" and f["check"] == "read.divergence"]
    assert any(f["carrier"] == "display:none" and f["text"] == "not shown" and f["line"] == 3
               and f["method"] == "static-style" and f["reading"] == "A-only" for f in d)


def test_image_skip_and_unread(tmp_path):
    build(tmp_path / "in")
    fs = report(tmp_path / "in")["findings"]
    img = [f for f in fs if f["file"] == "img.png"]
    checks = {f["check"] for f in img}
    # Ask the reader whether OCR can run here; inferring it from findings fails when OCR runs
    # and the image hides nothing (2026-10-04: first CI run, Linux with Tesseract installed).
    import read_image
    ocr_ok, _ = read_image.ocr_available()
    if ocr_ok:
        assert not any(f["check"] == "read.divergence" and "skipped" in f for f in img)
    else:
        assert "read.unread" in checks
        assert any(f["check"] == "read.divergence" and "skipped" in f for f in img)
    assert any(f["check"] == "read.unread" and f["file"] == "blob.dat" for f in fs)


def test_out_dir(tmp_path):
    build(tmp_path / "in")
    code, out, _ = run(tmp_path / "in", "--out", tmp_path / "o")
    assert code == 0
    fs = json.loads(out.decode("utf-8"))["findings"]
    text = (tmp_path / "o" / "normalized" / "text" / "docs" / "a.md.txt").read_bytes().decode("utf-8")
    folded = (tmp_path / "o" / "normalized" / "folded" / "docs" / "a.md.txt").read_bytes().decode("utf-8")
    tl, fl = text.split("\n"), folded.split("\n")
    assert len(tl) == len(fl) == len(MD.split("\n"))
    fired = {f["line"] for f in fs if f["check"] == "read.fold" and f["file"] == "docs/a.md"}
    differ = {i + 1 for i, (a, b) in enumerate(zip(tl, fl)) if a != b}
    assert differ == fired
    assert (tmp_path / "o" / "normalized" / "text" / "page.html.txt").is_file()


def test_out_inside_input_and_readonly(tmp_path):
    root = tmp_path / "in"
    build(root)
    before = snapshot(root)
    code, out, _ = run(root, "--out", root / "o")
    assert code != 0 and out == b""
    report(root)
    assert snapshot(root) == before


def test_missing_folder(tmp_path):
    code, out, _ = run(tmp_path / "nope")
    assert code != 0 and out == b""
