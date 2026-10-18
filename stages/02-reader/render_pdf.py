"""PDF pages drawn and read as images. Spec: specs/render_pdf.SPEC.md."""
from __future__ import annotations

import difflib
import unicodedata
from dataclasses import dataclass, field

import regex

import read_image

RENDER_SCALE = 3      # 216 dpi: 6 pt text is 18 px
RENDER_MAX = 8000     # a page is never drawn past this many pixels on its longer side
MAX_PAGES = 50
MIN_WORDS = 3
UNSEEN_SHARE = 0.6
SLIP = 0.8            # difflib ratio at or above which an OCR word is a misread layer word
SLIP_MIN = 5          # ... for words this long or longer ("then" is not a slip of "the")
CONF = 70             # an OCR line under this median word confidence is set aside (spec, Measured)

WORD = regex.compile(r"[\p{L}\p{N}]{2,}")


@dataclass
class PageOcr:
    pages: list[str] = field(default_factory=list)
    low: list[str] = field(default_factory=list)  # per page: the lines under CONF, set aside
    total: int = 0
    skipped: str | None = None


def page_ocr(data: bytes, max_pages: int = MAX_PAGES, ocr: bool = True) -> PageOcr:
    out = PageOcr()
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(data)  # forms and JavaScript are never initialized
        out.total = len(pdf)
    except Exception as exc:
        out.skipped = f"pdf render error: {type(exc).__name__}"
        return out
    if not ocr:
        out.skipped = "ocr disabled"
        return out
    ok, why = read_image.ocr_available()
    if not ok:
        out.skipped = why
        return out
    try:
        for i in range(min(out.total, max_pages)):
            page = pdf[i]
            w, h = page.get_size()
            scale = min(RENDER_SCALE, RENDER_MAX / max(w, h, 1))
            im = page.render(scale=scale, grayscale=True).to_pil()
            lines = read_image.ocr_lines(im, enlarge=False)
            out.pages.append("\n".join(t for t, c in lines if c >= CONF))
            out.low.append("\n".join(t for t, c in lines if c < CONF))
    except Exception as exc:
        out.skipped = f"pdf render error on page {len(out.pages) + 1}: {type(exc).__name__}"
    return out


def words(text: str) -> list[str]:
    return WORD.findall(unicodedata.normalize("NFKC", text).lower())


def _seen(word: str, layer: set[str], by_len: dict[int, list[str]]) -> bool:
    if word in layer:
        return True
    if len(word) < SLIP_MIN:
        return False
    near = [w for n in range(len(word) - 2, len(word) + 3) for w in by_len.get(n, ())]
    return bool(difflib.get_close_matches(word, near, n=1, cutoff=SLIP))


def unseen(ocr_text: str, layer_lines: list[str]) -> list[list[str]]:
    layer = {w for line in layer_lines for w in words(line)}
    by_len: dict[int, list[str]] = {}
    for w in layer:
        by_len.setdefault(len(w), []).append(w)
    blocks, cur = [], []
    for line in ocr_text.splitlines():
        ws = words(line)
        if not ws:
            continue  # a blank or punctuation-only line neither opens nor ends a block
        out = sum(1 for w in ws if not _seen(w, layer, by_len))
        if len(ws) < MIN_WORDS:
            if cur and out == len(ws):  # a short line joins an open block, never opens one
                cur.append(line.strip())
        elif out >= UNSEEN_SHARE * len(ws):
            cur.append(line.strip())
        elif cur:
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    return blocks
