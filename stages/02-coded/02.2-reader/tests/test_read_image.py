"""Tests for read_image.py, written from specs/reader.SPEC.md, read_image."""
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
    r = read_image.read_image(png({"Comment": "hidden words"}))
    assert {"field": "png:Comment", "text": "hidden words"} in r.metadata


def test_jpeg_exif():
    im = Image.new("RGB", (4, 4), "white")
    exif = Image.Exif()
    exif[0x010E] = "exif words"
    buf = io.BytesIO()
    im.save(buf, "JPEG", exif=exif)
    r = read_image.read_image(buf.getvalue())
    assert {"field": "exif:ImageDescription", "text": "exif words"} in r.metadata


def test_plain_png():
    r = read_image.read_image(png())
    assert r.metadata == [] and r.unread is None


def test_not_an_image():
    r = read_image.read_image(b"definitely not an image")
    assert r.unread


def test_the_text_drawn_in_an_image_is_not_examined():
    """R35 (owner, 2026-11-11: "We state we do not examine images"): no OCR; the reader reads metadata only, and the reason
    every readable image is listed as unread says so."""
    assert not hasattr(read_image, "ocr_available") and not hasattr(read_image, "ocr_read")
    assert read_image.NOT_EXAMINED == "image: the text drawn in it is not examined (its metadata is read)"
    assert set(read_image.ImageReading.__dataclass_fields__) == {"metadata", "unread"}
