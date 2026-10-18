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


OCR_SMALL = 2000   # a crop under this many pixels on its longer side is one view
OCR_SCALE = 3      # ... enlarged this many times
OCR_MAX = 6000     # ... but never past this many pixels
TILE, OVERLAP, TILE_SCALE = 1000, 120, 2   # a larger crop is read in tiles
INK, MARGIN = 3, 12


def _background(g) -> int:
    hist = g.histogram()
    return max(range(256), key=hist.__getitem__)


def _ink_box(g, bg):
    """The bounding box of the pixels that differ from the background by more than INK."""
    return g.point(lambda v: 255 if abs(v - bg) > INK else 0).getbbox()


def _view(g, bg, scale):
    """Contrast stretched first, then enlarged: the other order reads faint small text worse
    (8 px light gray in a large image, 69% of words against 92%; OCR spike)."""
    from PIL import Image, ImageOps
    g = ImageOps.autocontrast(g, cutoff=0)
    if bg < 128:
        g = ImageOps.invert(g)
    w, h = g.size
    k = max(1, min(scale, OCR_MAX // max(w, h)))
    return g.resize((w * k, h * k), Image.LANCZOS) if k > 1 else g


def ocr_views(im):
    """The grayscale views Tesseract reads, in reading order (spec, OCR preprocessing): cropped
    to the ink, contrast stretched, dark backgrounds inverted, enlarged; a large crop in tiles.
    Small or faint text is a way to hide an instruction in an image (OCR-SPIKE-2026-10-18.md)."""
    g = im.convert("L")
    bg = _background(g)
    box = _ink_box(g, bg)
    if box is None:
        return []
    x0, y0, x1, y1 = box
    g = g.crop((max(0, x0 - MARGIN), max(0, y0 - MARGIN),
                min(g.width, x1 + MARGIN), min(g.height, y1 + MARGIN)))
    if max(g.size) < OCR_SMALL:
        return [_view(g, bg, OCR_SCALE)]
    views, step = [], TILE - OVERLAP
    for y in range(0, max(1, g.height - OVERLAP), step):
        for x in range(0, max(1, g.width - OVERLAP), step):
            t = g.crop((x, y, min(x + TILE, g.width), min(y + TILE, g.height)))
            if _ink_box(t, bg) is not None:
                views.append(_view(t, bg, TILE_SCALE))
    return views


def ocr_read(im) -> str:
    """OCR text of an image: each view's text, in order, joined with newlines."""
    import pytesseract
    return "\n".join(t.strip("\n") for t in (pytesseract.image_to_string(v) for v in ocr_views(im))
                     if t.strip())


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
        out.ocr_text = ocr_read(im)
    except Exception as exc:
        out.ocr_skipped = f"ocr failed: {type(exc).__name__}"
    return out
