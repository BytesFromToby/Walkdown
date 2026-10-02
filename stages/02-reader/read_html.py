"""HTML readings A and B from static style. Spec: specs/read_html.SPEC.md."""
from __future__ import annotations

import re
import warnings

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from bs4.element import CData, Declaration, Doctype, ProcessingInstruction

import colors

ATTR_CARRIERS = ("alt", "title", "aria-label")
NONPAINT = {"script": "script", "template": "template", "noscript": "noscript",
            "title": "document-title"}
BLACK = (0, 0, 0, 1.0)
ZERO_SIZE = re.compile(r"^0(?:\.0*)?(?:px|pt|em|rem|%|vw|vh)?$")
ZERO_OPACITY = re.compile(r"^0(?:\.0*)?%?$")


def collapse(s: str) -> str:
    return " ".join(s.split())


def _strip_important(v: str) -> tuple[str, bool]:
    imp = "!important" in v.lower()
    return re.sub(r"!\s*important", "", v, flags=re.I).strip(), imp


def parse_decls(block: str) -> list[tuple[str, str, bool]]:
    out = []
    for part in block.split(";"):
        if ":" not in part:
            continue
        prop, val = part.split(":", 1)
        val, imp = _strip_important(val)
        out.append((prop.strip().lower(), val.strip(), imp))
    return out


def parse_css(css: str) -> list[tuple[str, str]]:
    """Top-level (selector, declarations) pairs; at-rules skipped."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules, i, n = [], 0, len(css)
    while i < n:
        brace = css.find("{", i)
        if brace < 0:
            break
        sel = css[i:brace].strip()
        depth, j = 1, brace + 1
        while j < n and depth:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
            j += 1
        body = css[brace + 1:j - 1]
        semi = sel.rfind(";")
        if semi >= 0:  # e.g. "@import x; .a"
            sel = sel[semi + 1:].strip()
        if sel and not sel.startswith("@"):
            rules.append((sel, body))
        i = j
    return rules


def specificity(sel: str) -> tuple[int, int, int]:
    ids = len(re.findall(r"#[\w-]+", sel))
    cls = len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:(?!:)[\w-]+", sel))
    types = len(re.findall(r"(?:^|[\s>+~])([a-zA-Z][\w-]*)", sel))
    return ids, cls, types


def _computed_styles(soup) -> dict[int, dict[str, str]]:
    entries: dict[int, list] = {}
    order = 0
    for st in soup.find_all("style"):
        for sel_group, body in parse_css(st.get_text()):
            decls = parse_decls(body)
            for sel in sel_group.split(","):
                sel = sel.strip()
                if not sel:
                    continue
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        matched = soup.select(sel)
                except Exception:
                    continue
                spec = specificity(sel)
                for el in matched:
                    for prop, val, imp in decls:
                        entries.setdefault(id(el), []).append(((imp, 0) + spec + (order,), prop, val))
                order += 1
    styles: dict[int, dict[str, str]] = {}
    for el in soup.find_all(True):
        ranked = sorted(entries.get(id(el), []), key=lambda e: e[0])
        inline = el.get("style")
        if isinstance(inline, str):
            for prop, val, imp in parse_decls(inline):
                ranked.append(((imp, 1, 0, 0, 0, 0), prop, val))
            ranked.sort(key=lambda e: e[0])
        if ranked:
            styles[id(el)] = {prop: val for _, prop, val in ranked}
    return styles


def _bg_of(decl: dict) -> tuple | None:
    for prop in ("background-color", "background"):
        v = decl.get(prop)
        if not v:
            continue
        c = colors.parse(v)
        if c is None:
            for tok in re.findall(r"rgba?\([^)]*\)|#[0-9a-fA-F]+|[a-zA-Z]+", v):
                c = colors.parse(tok)
                if c is not None:
                    break
        if c is not None and c[3] > 0:
            return c
    return None


def read_html(text: str) -> dict:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        soup = BeautifulSoup(text, "html.parser")
    styles = _computed_styles(soup)

    text_items: list[tuple] = []   # (key, carrier, line, text)
    painted_items: list[tuple] = []  # (key, text)
    extra: list[dict] = []          # comments and attributes
    cursor = [0]

    def comment_line(node, parent_line):
        needle = "<!--" + str(node)
        pos = text.find(needle, cursor[0])
        if pos < 0:
            pos = text.find(needle)
        if pos < 0:
            return parent_line
        cursor[0] = pos + len(needle)
        return text.count("\n", 0, pos) + 1

    def walk(el: Tag, st: dict):
        decl = styles.get(id(el), {})
        line = el.sourceline
        name = (el.name or "").lower()
        st = dict(st)
        if name == "style":
            return
        for attr in ATTR_CARRIERS:
            v = el.get(attr)
            if isinstance(v, list):
                v = " ".join(v)
            if isinstance(v, str) and v.strip():
                extra.append({"line": line, "text": collapse(v), "carrier": attr})
        if name in NONPAINT and st["hard"] is not None and st["hard"][0] == "head":
            st["hard"] = (NONPAINT[name], el)
        if st["hard"] is None:
            if name == "head":
                st["hard"] = ("head", el)
            elif name in NONPAINT:
                st["hard"] = (NONPAINT[name], el)
            elif el.has_attr("hidden"):
                st["hard"] = ("hidden", el)
            elif decl.get("display", "").lower() == "none":
                st["hard"] = ("display:none", el)
            elif ZERO_OPACITY.match(decl.get("opacity", "").strip().lower() or "x"):
                st["hard"] = ("opacity:0", el)
        vis = decl.get("visibility", "").lower()
        if vis:
            st["vis"] = vis
        fs = decl.get("font-size", "").strip().lower()
        if fs:
            st["size0"] = bool(ZERO_SIZE.match(fs))
        c = colors.parse(decl.get("color")) if decl.get("color") else None
        if c is not None:
            st["color"] = c
        bg = _bg_of(decl)
        if bg is not None:
            st["bg"] = bg

        for child in el.children:
            if isinstance(child, Comment):
                body = collapse(str(child))
                if body:
                    extra.append({"line": comment_line(child, line), "text": body,
                                  "carrier": "comment"})
            elif isinstance(child, (Doctype, Declaration, CData, ProcessingInstruction)):
                continue
            elif isinstance(child, NavigableString):
                t = str(child)
                if not t.strip():
                    continue
                if st["hard"] is not None:
                    carrier, root = st["hard"]
                    text_items.append(((carrier, id(root)), carrier, root.sourceline, t))
                elif st["vis"] in ("hidden", "collapse"):
                    text_items.append((("visibility:hidden", id(el)), "visibility:hidden", line, t))
                elif st["size0"]:
                    text_items.append((("font-size:0", id(el)), "font-size:0", line, t))
                elif colors.hides(st["color"], st["bg"]):
                    carrier = colors.carrier(st["color"], st["bg"])
                    text_items.append(((carrier, id(el)), carrier, line, t))
                else:
                    painted_items.append((id(el), t))
            elif isinstance(child, Tag):
                walk(child, st)

    root_state = {"hard": None, "vis": "visible", "size0": False, "color": BLACK,
                  "bg": colors.WHITE}
    top = Tag(name="[document]")
    for child in list(soup.children):
        if isinstance(child, Comment):
            body = collapse(str(child))
            if body:
                extra.append({"line": comment_line(child, 1), "text": body, "carrier": "comment"})
        elif isinstance(child, Tag):
            walk(child, root_state)
        elif isinstance(child, NavigableString) and not isinstance(
                child, (Doctype, Declaration, CData, ProcessingInstruction)) and str(child).strip():
            painted_items.append((id(top), str(child)))

    painted = _merge_painted(painted_items)
    painted_set = set(painted)
    merged = []
    for key, carrier, line, t in text_items:
        if merged and merged[-1][0] == key:
            merged[-1][3].append(t)
        else:
            merged.append([key, carrier, line, [t]])
    divergences = [{"line": line, "text": collapse(" ".join(parts)), "carrier": carrier}
                   for _, carrier, line, parts in merged]
    divergences += extra
    divergences = [d for d in divergences if d["text"] and d["text"] not in painted_set]
    divergences.sort(key=lambda d: (d["line"] or 0))
    return {"divergences": divergences, "painted": painted}


def _merge_painted(items):
    out = []
    last = None
    for key, t in items:
        if out and key == last:
            out[-1] += " " + t
        else:
            out.append(t)
        last = key
    return [c for c in (collapse(x) for x in out) if c]
