"""DOCX readings A and B and core properties. Spec: specs/read_docx.SPEC.md."""
from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass, field

from lxml import etree

import colors

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
MAX_MEMBER = 50 * 1024 * 1024
HIGHLIGHT = {"black": "000000", "blue": "0000FF", "cyan": "00FFFF", "green": "00FF00",
             "magenta": "FF00FF", "red": "FF0000", "yellow": "FFFF00", "white": "FFFFFF",
             "darkBlue": "000080", "darkCyan": "008080", "darkGreen": "008000",
             "darkMagenta": "800080", "darkRed": "800000", "darkYellow": "808000",
             "darkGray": "808080", "lightGray": "C0C0C0"}
OFF = {"0", "false", "off"}


def q(tag: str) -> str:
    return f"{{{W}}}{tag}"


@dataclass
class DocxReading:
    lines: list[str] = field(default_factory=list)
    divergences: list[dict] = field(default_factory=list)
    metadata: list[dict] = field(default_factory=list)
    unread: str | None = None


def _parser():
    return etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                           huge_tree=False)


def _member(z: zipfile.ZipFile, name: str) -> bytes | None:
    try:
        info = z.getinfo(name)
    except KeyError:
        return None
    if info.file_size > MAX_MEMBER:
        raise ValueError(f"{name} too large ({info.file_size} bytes)")
    return z.read(name)


def _rpr_props(rpr) -> dict:
    """Relevant run properties set by one w:rPr element."""
    out = {}
    if rpr is None:
        return out
    v = rpr.find(q("vanish"))
    if v is not None:
        out["vanish"] = (v.get(q("val")) or "true").lower() not in OFF
    c = rpr.find(q("color"))
    if c is not None and c.get(q("val")):
        out["color"] = c.get(q("val"))
    s = rpr.find(q("shd"))
    if s is not None and s.get(q("fill")):
        out["shd"] = s.get(q("fill"))
    h = rpr.find(q("highlight"))
    if h is not None and h.get(q("val")):
        out["highlight"] = h.get(q("val"))
    sz = rpr.find(q("sz"))
    if sz is not None and sz.get(q("val")):
        out["sz"] = sz.get(q("val"))
    return out


class _Styles:
    def __init__(self, root):
        self.defaults: dict = {}
        self.styles: dict = {}
        if root is None:
            return
        d = root.find(f"{q('docDefaults')}/{q('rPrDefault')}/{q('rPr')}")
        self.defaults = _rpr_props(d)
        for st in root.iter(q("style")):
            sid = st.get(q("styleId"))
            if not sid:
                continue
            based = st.find(q("basedOn"))
            self.styles[sid] = (based.get(q("val")) if based is not None else None,
                                _rpr_props(st.find(q("rPr"))),
                                _shd_fill(st.find(q("pPr"))))

    def chain(self, sid: str | None) -> dict:
        seq, seen = [], set()
        while sid and sid in self.styles and sid not in seen:
            seen.add(sid)
            seq.append(self.styles[sid][1])
            sid = self.styles[sid][0]
        out = {}
        for props in reversed(seq):
            out.update(props)
        return out

    def para_shd(self, sid: str | None) -> str | None:
        seen = set()
        while sid and sid in self.styles and sid not in seen:
            seen.add(sid)
            if self.styles[sid][2]:
                return self.styles[sid][2]
            sid = self.styles[sid][0]
        return None


def _shd_fill(ppr) -> str | None:
    if ppr is None:
        return None
    s = ppr.find(q("shd"))
    return s.get(q("fill")) if s is not None and s.get(q("fill")) else None


def _color(val: str | None):
    if not val or val.lower() == "auto":
        return None
    return colors.parse(val)


def _nearest_p(el):
    node = el.getparent()
    while node is not None and node.tag != q("p"):
        node = node.getparent()
    return node


def _run_text(r) -> str:
    parts = []
    for child in r.iter():
        if child.tag == q("t"):
            parts.append(child.text or "")
        elif child.tag == q("tab"):
            parts.append("\t")
        elif child.tag in (q("br"), q("cr")):
            parts.append(" ")
    return "".join(parts)


def _reason(props: dict, bg) -> str | None:
    if props.get("vanish"):
        return "vanish"
    try:
        if "sz" in props and int(props["sz"]) <= 2:
            return "tiny-font"
    except ValueError:
        pass
    fg = _color(props.get("color"))
    if fg is not None and colors.hides(fg, bg):
        return colors.carrier(fg, bg)
    return None


def _metadata(z: zipfile.ZipFile) -> list[dict]:
    out = []
    raw = _member(z, "docProps/core.xml")
    if raw:
        root = etree.fromstring(raw, _parser())
        for el in root:
            if isinstance(el.tag, str) and el.text and el.text.strip():
                out.append({"field": etree.QName(el).localname, "text": el.text})
    raw = _member(z, "docProps/custom.xml")
    if raw:
        root = etree.fromstring(raw, _parser())
        for prop in root:
            if not isinstance(prop.tag, str):
                continue
            text = "".join(prop.itertext())
            if text.strip():
                out.append({"field": f"custom:{prop.get('name')}", "text": text})
    return out


def read_docx(data: bytes) -> DocxReading:
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except (zipfile.BadZipFile, OSError, ValueError):
        return DocxReading(unread="not a zip")
    try:
        with z:
            raw = _member(z, "word/document.xml")
            if raw is None:
                return DocxReading(unread="no word/document.xml")
            doc = etree.fromstring(raw, _parser())
            styles_raw = _member(z, "word/styles.xml")
            styles = _Styles(etree.fromstring(styles_raw, _parser()) if styles_raw else None)
            meta = _metadata(z)
    except (ValueError, etree.XMLSyntaxError, zipfile.BadZipFile, KeyError,
            NotImplementedError, RuntimeError, OSError) as exc:
        return DocxReading(unread=f"{type(exc).__name__}: {exc}"[:300])

    out = DocxReading(metadata=meta)
    page_bg = colors.WHITE
    bgel = doc.find(q("background"))
    if bgel is not None:
        page_bg = _color(bgel.get(q("color"))) or colors.WHITE
    body = doc.find(q("body"))
    if body is None:
        return out
    for pi, p in enumerate(body.iter(q("p")), start=1):
        ppr = p.find(q("pPr"))
        pstyle = None
        if ppr is not None and ppr.find(q("pStyle")) is not None:
            pstyle = ppr.find(q("pStyle")).get(q("val"))
        base = dict(styles.defaults)
        base.update(styles.chain(pstyle))
        pshd = _color(_shd_fill(ppr)) or _color(styles.para_shd(pstyle))
        items = []
        for r in p.iter(q("r")):
            if _nearest_p(r) is not p:
                continue
            text = _run_text(r)
            if not text:
                continue
            rpr = r.find(q("rPr"))
            props = dict(base)
            if rpr is not None and rpr.find(q("rStyle")) is not None:
                props.update(styles.chain(rpr.find(q("rStyle")).get(q("val"))))
            props.update(_rpr_props(rpr))
            bg = (_color(props.get("shd")) or _color(HIGHLIGHT.get(props.get("highlight", ""), None))
                  or pshd or page_bg)
            items.append((text, _reason(props, bg)))
        out.lines.append("".join(t for t, _ in items))
        runs = []
        for text, reason in items:
            if reason and runs and runs[-1][0] == reason:
                runs[-1][1] += text
            elif reason:
                runs.append([reason, text])
            elif text.strip():
                runs.append([None, text])
        for reason, text in runs:
            if reason and text.strip():
                out.divergences.append({"text": text.strip(), "carrier": reason,
                                        "paragraph": pi, "text_line": pi})
    return out
