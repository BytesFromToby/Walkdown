"""PDF readings A and B and metadata. Spec: specs/read_pdf.SPEC.md."""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field

import colors

for _name in ("pdfminer", "pypdf"):
    logging.getLogger(_name).setLevel(logging.ERROR)

NEUTRAL = object()


@dataclass
class PdfReading:
    lines: list[str] = field(default_factory=list)
    divergences: list[dict] = field(default_factory=list)
    metadata: list[dict] = field(default_factory=list)
    unread: str | None = None


def _device_class():
    from pdfminer.converter import PDFPageAggregator

    class Device(PDFPageAggregator):
        _render_mode = 0

        def render_string(self, textstate, seq, ncs, graphicstate):
            self._render_mode = getattr(textstate, "render", 0)
            return super().render_string(textstate, seq, ncs, graphicstate)

        def render_char(self, *args, **kwargs):
            adv = super().render_char(*args, **kwargs)
            try:
                self.cur_item._objs[-1].walkdown_render = self._render_mode
            except (AttributeError, IndexError):
                pass
            return adv

    return Device


def to_rgb(value) -> tuple | None:
    """PDF fill color (gray, RGB, CMYK in 0-1) to an RGBA tuple; None if unknown."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        vals = [float(value)]
    elif isinstance(value, (list, tuple)):
        try:
            vals = [float(v) for v in value]
        except (TypeError, ValueError):
            return None
    else:
        return None
    vals = [max(0.0, min(1.0, v)) for v in vals]
    if len(vals) == 1:
        g = round(vals[0] * 255)
        return (g, g, g, 1.0)
    if len(vals) == 3:
        return (round(vals[0] * 255), round(vals[1] * 255), round(vals[2] * 255), 1.0)
    if len(vals) == 4:
        c, m, y, k = vals
        return (round(255 * (1 - c) * (1 - k)), round(255 * (1 - m) * (1 - k)),
                round(255 * (1 - y) * (1 - k)), 1.0)
    return None


def _walk(obj, fn):
    fn(obj)
    try:
        children = list(obj)
    except TypeError:
        return
    from pdfminer.layout import LTTextLine
    if isinstance(obj, LTTextLine):
        return
    for child in children:
        _walk(child, fn)


def _reason(ch, page_bbox, rects) -> str | None:
    if getattr(ch, "walkdown_render", 0) == 3:
        return "render-mode-invisible"
    x0, y0, x1, y1 = ch.bbox
    px0, py0, px1, py1 = page_bbox
    if x1 < px0 or x0 > px1 or y1 < py0 or y0 > py1:
        return "off-page"
    gs = getattr(ch, "graphicstate", None)
    fg = to_rgb(getattr(gs, "ncolor", None)) if gs is not None else None
    if fg is None:
        return None
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    bg, best = colors.WHITE, None
    for (rx0, ry0, rx1, ry1), c in rects:
        if rx0 <= cx <= rx1 and ry0 <= cy <= ry1:
            area = (rx1 - rx0) * (ry1 - ry0)
            if best is None or area < best:
                bg, best = c, area
    if colors.hides(fg, bg):
        return colors.carrier(fg, bg)
    return None


def _line_runs(items) -> list[tuple[str, str]]:
    """items: (char, reason|None|NEUTRAL). Runs of hidden chars as (carrier, text)."""
    runs, cur, pending = [], None, ""
    for ch, reason in items:
        if reason is NEUTRAL:
            if cur:
                pending += ch
            continue
        if reason is None:
            if cur:
                runs.append(tuple(cur))
            cur, pending = None, ""
            continue
        if cur and cur[0] == reason:
            cur[1] += pending + ch
        else:
            if cur:
                runs.append(tuple(cur))
            cur = [reason, ch]
        pending = ""
    if cur:
        runs.append(tuple(cur))
    return [(c, t.strip()) for c, t in runs if t.strip()]


def _text_layer(data: bytes, out: PdfReading) -> None:
    from pdfminer.layout import LAParams, LTAnno, LTChar, LTCurve, LTTextLine
    from pdfminer.pdfdocument import PDFDocument
    from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
    from pdfminer.pdfpage import PDFPage
    from pdfminer.pdfparser import PDFParser

    parser = PDFParser(io.BytesIO(data))
    doc = PDFDocument(parser)
    rsrc = PDFResourceManager()
    device = _device_class()(rsrc, laparams=LAParams(all_texts=True))
    interp = PDFPageInterpreter(rsrc, device)
    for page_no, page in enumerate(PDFPage.create_pages(doc), start=1):
        interp.process_page(page)
        layout = device.get_result()
        if page_no > 1:
            out.lines.append("")
        rects, lines = [], []

        def collect(obj):
            if isinstance(obj, LTCurve) and getattr(obj, "fill", False):
                c = to_rgb(getattr(obj, "non_stroking_color", None))
                if c is not None:
                    rects.append((obj.bbox, c))
            elif isinstance(obj, LTTextLine):
                lines.append(obj)

        _walk(layout, collect)
        for tl in lines:
            items = []
            for ch in tl:
                if isinstance(ch, LTChar):
                    items.append((ch.get_text(), _reason(ch, layout.bbox, rects)))
                elif isinstance(ch, LTAnno):
                    items.append((ch.get_text(), NEUTRAL))
            text = "".join(c for c, _ in items).rstrip("\n")
            out.lines.append(text)
            for carrier, span in _line_runs([(c, r) for c, r in items if c != "\n"]):
                out.divergences.append({"text": span, "carrier": carrier, "page": page_no,
                                        "text_line": len(out.lines)})


def _meta_value(v) -> str | None:
    try:
        v = v.get_object()
    except AttributeError:
        pass
    from pypdf.generic import ByteStringObject, NameObject, TextStringObject
    if isinstance(v, NameObject):
        return None
    if isinstance(v, TextStringObject):
        return str(v)
    if isinstance(v, (ByteStringObject, bytes)):
        return bytes(v).decode("latin-1")
    if isinstance(v, str):
        return v
    return None


def _xmp(reader) -> list[dict]:
    from lxml import etree
    try:
        root = reader.trailer["/Root"].get_object()
        if "/Metadata" not in root:
            return []
        raw = root["/Metadata"].get_object().get_data()
        parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                                 recover=True)
        tree = etree.fromstring(raw.strip(), parser)
    except Exception:
        return []
    if tree is None:
        return []
    out = []
    containers = {"Bag", "Seq", "Alt", "li", "Description", "RDF", "xmpmeta"}
    for el in tree.iter():
        if not isinstance(el.tag, str) or len(el) or not (el.text and el.text.strip()):
            continue
        node = el
        while node is not None and etree.QName(node).localname in containers:
            node = node.getparent()
        if node is None:
            continue
        out.append({"field": "xmp:" + etree.QName(node).localname, "text": el.text.strip()})
    return out


def _metadata(data: bytes) -> tuple[list[dict], str | None]:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data), strict=False)
    if reader.is_encrypted:
        try:
            if not reader.decrypt(""):
                return [], "encrypted"
        except Exception:
            return [], "encrypted"
    out = []
    info = reader.metadata or {}
    for key in list(info.keys()):
        try:
            val = _meta_value(info[key])
        except Exception:
            val = None
        if val is not None and val.strip():
            out.append({"field": str(key).lstrip("/"), "text": val})
    out.extend(_xmp(reader))
    return out, None


def read_pdf(data: bytes) -> PdfReading:
    out = PdfReading()
    try:
        meta, reason = _metadata(data)
    except Exception as exc:
        return PdfReading(unread=f"pdf parse error: {type(exc).__name__}: {exc}"[:300])
    if reason:
        return PdfReading(unread=reason)
    try:
        _text_layer(data, out)
    except Exception as exc:
        name = type(exc).__name__
        if "Password" in name or "Encrypt" in name:
            return PdfReading(unread="encrypted")
        return PdfReading(unread=f"pdf parse error: {name}: {exc}"[:300])
    out.metadata = meta
    return out
