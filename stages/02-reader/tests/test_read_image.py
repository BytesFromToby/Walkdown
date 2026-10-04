"""Tests for read_image.py, written from specs/read_image.SPEC.md."""
import io

from PIL import Image, PngImagePlugin

import read_image


def png(text_chunks=None):
    im = Image.new("RGB", (4, 4), "white")
    info = PngImagePlugin.PngInfo()
    for k, v in (text_chunks or {}).items():
        info.add_text(k, v)
    buf = io.BytesIO()
    im.save(buf, "PNG", pnginfo=info)
    return buf.getvalue()


def test_png_text_chunk():
    r = read_image.read_image(png({"Comment": "hidden words"}), ocr=False)
    assert {"field": "png:Comment", "text": "hidden words"} in r.metadata


def test_jpeg_exif():
    im = Image.new("RGB", (4, 4), "white")
    exif = Image.Exif()
    exif[0x010E] = "exif words"
    buf = io.BytesIO()
    im.save(buf, "JPEG", exif=exif)
    r = read_image.read_image(buf.getvalue(), ocr=False)
    assert {"field": "exif:ImageDescription", "text": "exif words"} in r.metadata


def test_plain_png():
    r = read_image.read_image(png(), ocr=False)
    assert r.metadata == [] and r.unread is None


def test_no_ocr_is_a_skip():
    r = read_image.read_image(png(), ocr=False)
    assert r.ocr_text is None and r.ocr_skipped
    ok, why = read_image.ocr_available()
    assert isinstance(ok, bool) and isinstance(why, str)


def test_not_an_image():
    r = read_image.read_image(b"definitely not an image", ocr=False)
    assert r.unread


def test_for_ocr_enlarges_small_images_and_keeps_large_ones():
    from PIL import Image
    import read_image
    small = read_image.for_ocr(Image.new("RGB", (760, 120), "white"))
    assert small.mode == "L" and small.size == (760 * read_image.OCR_SCALE, 120 * read_image.OCR_SCALE)
    big = read_image.for_ocr(Image.new("RGB", (2400, 1000), "white"))
    assert big.size == (2400, 1000)
