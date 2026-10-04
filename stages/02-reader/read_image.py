"""Image metadata and optional OCR. Spec: specs/read_image.SPEC.md."""
from __future__ import annotations

import io
import shutil
from dataclasses import dataclass, field

EXIF_IFD = 0x8769


@dataclass
class ImageReading:
    metadata: list[dict] = field(default_factory=list)
    ocr_text: str | None = None
    ocr_skipped: str | None = None
    unread: str | None = None


def ocr_available() -> tuple[bool, str]:
    try:
        import pytesseract  # noqa: F401
    except Exception:
        if shutil.which("tesseract") is None:
            return False, "tesseract not installed (no tesseract binary, no pytesseract)"
        return False, "pytesseract not installed"
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
    except Exception:
        return False, "tesseract not installed (pytesseract present, binary missing)"
    return True, "tesseract available"


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


OCR_SMALL = 2000   # an image under this many pixels on its longer side is enlarged for OCR
OCR_SCALE = 3


def for_ocr(im):
    """The image as Tesseract reads it best: grayscale, and small images enlarged OCR_SCALE
    times. Tiny text is a way to hide an instruction in an image; at its natural size
    Tesseract misses it (2026-10-04: the first CI run with Tesseract missed the class 11
    fixture's 11-pixel text)."""
    from PIL import Image
    g = im.convert("L")
    w, h = g.size
    if max(w, h) < OCR_SMALL:
        g = g.resize((w * OCR_SCALE, h * OCR_SCALE), Image.LANCZOS)
    return g


def read_image(data: bytes, ocr: bool = True) -> ImageReading:
    from PIL import ExifTags, Image
    out = ImageReading()
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception as exc:
        return ImageReading(unread=f"image not readable: {type(exc).__name__}: {exc}"[:300],
                            ocr_skipped="image not readable")

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

    if not ocr:
        out.ocr_skipped = "ocr disabled"
        return out
    ok, why = ocr_available()
    if not ok:
        out.ocr_skipped = why
        return out
    try:
        import pytesseract
        out.ocr_text = pytesseract.image_to_string(for_ocr(im))
    except Exception as exc:
        out.ocr_skipped = f"ocr failed: {type(exc).__name__}"
    return out
