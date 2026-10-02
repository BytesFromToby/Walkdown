"""SVG readings A and B. Spec: specs/read_svg.SPEC.md."""
from __future__ import annotations

import re

from lxml import etree

import colors

TEXT_CARRIERS = {"title": "title", "desc": "desc", "metadata": "metadata", "script": "script"}
DEFS = {"defs", "symbol", "clippath", "mask", "pattern", "marker"}
BLACK = (0, 0, 0, 1.0)
NUM = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?", re.I)


class SvgError(Exception):
    pass


def _parser():
    return etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False,
                           dtd_validation=False, huge_tree=False, recover=False)


def collapse(s: str) -> str:
    return " ".join(s.split())


def _local(el) -> str:
    try:
        return etree.QName(el).localname.lower()
    except (ValueError, TypeError):
        return ""


def _style(el) -> dict:
    out = {}
    for part in (el.get("style") or "").split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = re.sub(r"!\s*important", "", v, flags=re.I).strip()
    return out


def _prop(el, name: str) -> str | None:
    st = _style(el)
    if name in st:
        return st[name]
    v = el.get(name)
    return v.strip() if isinstance(v, str) else None


def _zero(v: str | None) -> bool:
    if v is None:
        return False
    try:
        return float(v.strip().rstrip("%")) == 0
    except ValueError:
        return False


def _num(v: str | None) -> float | None:
    if not v:
        return None
    m = NUM.search(v)
    return float(m.group(0)) if m else None


def _own_text(el) -> str:
    """Text of an element and its element descendants, skipping comments and PIs."""
    parts = [el.text or ""]
    for child in el:
        if isinstance(child.tag, str):
            parts.append(_own_text(child))
        parts.append(child.tail or "")
    return "".join(parts)


def _covers(rect, x: float, y: float) -> bool:
    def span(pos_attr, size_attr, point):
        size = rect.get(size_attr) or ""
        if size.strip().endswith("%"):
            return True
        w = _num(size)
        if not w or w <= 0:
            return False
        start = _num(rect.get(pos_attr)) or 0.0
        return start <= point <= start + w
    return span("x", "width", x) and span("y", "height", y)


def read_svg(data: bytes) -> dict:
    try:
        root = etree.fromstring(data, _parser())
    except etree.XMLSyntaxError as exc:
        raise SvgError(str(exc)) from exc
    if root is None:
        raise SvgError("empty document")

    candidates: list[dict] = []
    painted: list[str] = []
    rects: list[tuple] = []  # (element, fill)

    def add(line, text, carrier):
        t = collapse(text)
        if t:
            candidates.append({"line": line, "text": t, "carrier": carrier})

    for sib in reversed(list(root.itersiblings(preceding=True))):
        if sib.tag is etree.Comment:
            add(sib.sourceline, sib.text or "", "comment")
    tail_sibs = list(root.itersiblings())

    def walk(el, st):
        if el.tag is etree.Comment:
            add(el.sourceline, el.text or "", "comment")
            return
        if not isinstance(el.tag, str):
            return
        name = _local(el)
        st = dict(st)
        if name in DEFS:
            st["hide"] = st["hide"] or "defs"
        if st["hide"] is None:
            if (_prop(el, "display") or "").lower() == "none":
                st["hide"] = "display:none"
            elif _zero(_prop(el, "opacity")):
                st["hide"] = "opacity:0"
        vis = (_prop(el, "visibility") or "").lower()
        if vis:
            st["vis"] = vis
        fill = _prop(el, "fill")
        if fill:
            st["fill"] = fill
        if _prop(el, "fill-opacity") is not None:
            st["fill_zero"] = _zero(_prop(el, "fill-opacity"))

        if name in TEXT_CARRIERS:
            add(el.sourceline, _own_text(el), TEXT_CARRIERS[name])
            for child in el.iter(etree.Comment):
                add(child.sourceline, child.text or "", "comment")
            return
        if name == "style":
            return
        if name == "rect" and st["hide"] is None and st["vis"] not in ("hidden", "collapse"):
            f = (st["fill"] or "black").strip().lower()
            c = colors.parse(f)
            if f != "none" and c is not None and c[3] > 0 and not st["fill_zero"]:
                rects.append((el, c))
        if name == "text":
            body = _own_text(el)
            for child in el.iter(etree.Comment):
                add(child.sourceline, child.text or "", "comment")
            carrier = _text_carrier(el, st, rects)
            if carrier is None:
                t = collapse(body)
                if t:
                    painted.append(t)
            else:
                add(el.sourceline, body, carrier)
            return
        # Character data outside <text> is not rendered (except in foreignObject).
        for child in el:
            walk(child, st)
            if isinstance(child.tag, str) and child.tail and child.tail.strip() and name != "foreignobject":
                add(child.sourceline, child.tail, "not-rendered")
        if el.text and el.text.strip() and name not in ("foreignobject",):
            add(el.sourceline, el.text, "not-rendered")
        elif el.text and el.text.strip():
            painted.append(collapse(el.text))

    walk(root, {"hide": None, "vis": "visible", "fill": None, "fill_zero": False})
    for sib in tail_sibs:
        if sib.tag is etree.Comment:
            add(sib.sourceline, sib.text or "", "comment")

    painted_set = set(painted)
    divs = [d for d in candidates if d["text"] not in painted_set]
    divs.sort(key=lambda d: d["line"] or 0)
    return {"divergences": divs, "painted": painted}


def _text_carrier(el, st, rects) -> str | None:
    if st["hide"]:
        return st["hide"]
    if st["vis"] in ("hidden", "collapse"):
        return "visibility:hidden"
    if st["fill_zero"]:
        return "opacity:0"
    fill = (st["fill"] or "black").strip().lower()
    if fill == "none":
        return "fill:none"
    fg = colors.parse(fill)
    if fg is None:
        return None  # gradients, currentColor: treated as painted
    x = _num(el.get("x")) or 0.0
    y = _num(el.get("y")) or 0.0
    bg = colors.WHITE
    for rect, c in rects:
        if _covers(rect, x, y):
            bg = c
    if colors.hides(fg, bg):
        return colors.carrier(fg, bg)
    return None
