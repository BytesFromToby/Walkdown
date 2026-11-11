"""Image metadata. Spec: specs/reader.SPEC.md, read_image.

The text drawn inside an image is not examined (R35, owner 2026-11-11: "Tesseract removal I think is fine. We state we do
not examine images."): Walkdown installs with pip and nothing else, and reading pixels took a program installed apart.
The text an image carries as data (PNG text chunks, a comment, EXIF fields) is read here.
"""
from __future__ import annotations

import io
from dataclasses import dataclass, field

EXIF_IFD = 0x8769
# The reason every readable image is listed as unread: its metadata is read, the text drawn in it is not (run.read_one).
NOT_EXAMINED = "image: the text drawn in it is not examined (its metadata is read)"


@dataclass
class ImageReading:
    metadata: list[dict] = field(default_factory=list)
    unread: str | None = None  # the image could not be opened


def _text(value) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        for prefix in (b"ASCII\x00\x00\x00", b"UNICODE\x00", b"JIS\x00\x00\x00\x00\x00",
                       b"\x00\x00\x00\x00\x00\x00\x00\x00"):
            if value.startswith(prefix):
                value = value[len(prefix):]
                if prefix == b"UNICODE\x00":
                    try:
                        return value.decode("utf-16").rstrip("\x00")
                    except UnicodeDecodeError:
                        return None
                break
        if b"\x00" in value.rstrip(b"\x00"):
            return None
        value = value.rstrip(b"\x00")
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            s = value.decode("latin-1")
            return s if all(c.isprintable() or c in "\r\n\t" for c in s) else None
    return None


def read_image(data: bytes) -> ImageReading:
    """The text an image carries as metadata: PNG text chunks, a comment, and EXIF fields (with the Exif IFD)."""
    from PIL import ExifTags, Image
    out = ImageReading()
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as exc:
        return ImageReading(unread=f"image not readable: {type(exc).__name__}: {exc}"[:300])

    text_chunks = getattr(im, "text", None) or {}
    for k, v in text_chunks.items():
        t = _text(v)
        if t and t.strip():
            out.metadata.append({"field": f"png:{k}", "text": t})
    comment = im.info.get("comment")
    t = _text(comment)
    if t and t.strip():
        out.metadata.append({"field": "comment", "text": t})
    try:
        exif = im.getexif()
    except Exception:
        exif = {}
    tags = dict(exif.items()) if exif else {}
    try:
        tags.update(exif.get_ifd(EXIF_IFD).items())
    except Exception:
        pass
    for tag, value in tags.items():
        t = _text(value)
        if t and t.strip():
            name = ExifTags.TAGS.get(tag, f"0x{tag:04X}")
            out.metadata.append({"field": f"exif:{name}", "text": t})
    return out
