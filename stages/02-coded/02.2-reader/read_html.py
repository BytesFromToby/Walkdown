"""HTML readings A and B from static style. Spec: specs/reader.SPEC.md, read_html.

Nothing in the page runs and nothing is fetched. Since R36 (owner, 2026-11-11: "go with option 1"; Walkdown installs with
pip and nothing else) this reader does what the browser check (Playwright) did where style alone can tell: the
repository's own linked style sheets, `@media` for one screen, `::before` / `::after` text, text under 2 px, text placed
off the page, clipped away, or in a box with no size, and text in a closed `<details>`. How a page looks once drawn (one
element over another, clipping that depends on where things land, text over a background image) is not examined.
"""
from __future__ import annotations

import re
import warnings
from collections.abc import Callable

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from bs4.element import CData, Declaration, Doctype, ProcessingInstruction

import colors

ATTR_CARRIERS = ("alt", "title", "aria-label")
NONPAINT = {"script": "script", "template": "template", "noscript": "noscript",
            "title": "document-title"}
BLACK = (0, 0, 0, 1.0)
ZERO_SIZE = re.compile(r"^0(?:\.0*)?(?:px|pt|em|rem|%|vw|vh)?$")
ZERO_OPACITY = re.compile(r"^0(?:\.0*)?%?$")

# The one screen `@media` is read for (as the browser check drew it, 1280 x 800, light, a mouse).
SCREEN = {"width": 1280.0, "height": 800.0}
ROOT_PX = 16.0      # the default font size
TINY_PX = 2.0       # text under this many pixels cannot be read (`tiny-text`)
FAR_PX = 1000.0     # an offset this far negative puts text off the page (`off-page`)
CSS_CAP = 1_000_000  # bytes read of one linked style sheet
FONT_KEYWORDS = {"xx-small": 9.0, "x-small": 10.0, "small": 13.0, "medium": 16.0, "large": 18.0,
                 "x-large": 24.0, "xx-large": 32.0, "xxx-large": 48.0}
PSEUDO = re.compile(r"::?(before|after)\s*$", re.I)


def collapse(s: str) -> str:
    return " ".join(s.split())


def _strip_important(v: str) -> tuple[str, bool]:
    imp = "!important" in v.lower()
    return re.sub(r"!\s*important", "", v, flags=re.I).strip(), imp


def parse_decls(block: str) -> list[tuple[str, str, bool]]:
    out = []
    for part in _split_top(block, ";"):
        if ":" not in part:
            continue
        prop, val = part.split(":", 1)
        val, imp = _strip_important(val)
        out.append((prop.strip().lower(), val.strip(), imp))
    return out


def _split_top(s: str, sep: str) -> list[str]:
    """`s` split on `sep` outside quotes and brackets (a `content` string may hold a semicolon)."""
    out, cur, depth, quote = [], [], 0, None
    for ch in s:
        if quote:
            cur.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append("".join(cur))
    return out


# ---------------------------------------------------------------- @media, for one screen

MEDIA_FEATURE = re.compile(r"\(\s*([a-z-]+)\s*(?::\s*([^)]*))?\)")
MEDIA_RANGE = re.compile(r"\(\s*(width|height)\s*(<=|>=|<|>|=)\s*([^)]+)\)")


def _px(value: str, font_px: float | None = ROOT_PX) -> float | None:
    """A length in pixels: px, pt, em (of `font_px`), rem, vw, vh, or a bare 0; None for anything else."""
    m = re.fullmatch(r"\s*(-?\d*\.?\d+)\s*(px|pt|em|rem|vw|vh)?\s*", value or "", re.I)
    if not m:
        return None
    n, unit = float(m.group(1)), (m.group(2) or "").lower()
    if unit == "":
        return n if n == 0 else None
    if unit == "em":
        return None if font_px is None else n * font_px
    return {"px": n, "pt": n * 4 / 3, "rem": n * ROOT_PX, "vw": n * SCREEN["width"] / 100,
            "vh": n * SCREEN["height"] / 100}[unit]


def _feature(name: str, value: str | None) -> bool | None:
    """One media feature on the screen: True, False, or None when Walkdown does not know it."""
    v = (value or "").strip().lower()
    for side in ("width", "height"):
        if name in (side, f"min-{side}", f"max-{side}"):
            px = _px(v)
            if px is None:
                return None
            return {side: SCREEN[side] == px, f"min-{side}": SCREEN[side] >= px,
                    f"max-{side}": SCREEN[side] <= px}[name]
    known = {"orientation": "landscape", "prefers-color-scheme": "light", "prefers-reduced-motion": "no-preference",
             "hover": "hover", "any-hover": "hover", "pointer": "fine", "any-pointer": "fine", "scan": "progressive",
             "prefers-contrast": "no-preference", "forced-colors": "none", "update": "fast"}
    if name in known:
        return v == "" or v == known[name]
    if name == "color":
        return True
    return None


def _range(name: str, op: str, value: str) -> bool | None:
    px = _px(value.strip().lower())
    if px is None:
        return None
    s = SCREEN[name]
    return {"<=": s <= px, ">=": s >= px, "<": s < px, ">": s > px, "=": s == px}[op]


def media_matches(query: str) -> bool:
    """Whether a media query list holds on the one screen. A query Walkdown cannot read does not hold, so no rule in it
    makes a claim (as an unknown color makes none)."""
    query = (query or "").strip()
    if not query:
        return True
    for one in _split_top(query, ","):
        q = one.strip().lower()
        negate = q.startswith("not ")
        q = re.sub(r"^(not|only)\s+", "", q)
        ok: bool | None = True
        mtype = re.match(r"^([a-z]+)\b", q)
        if mtype and mtype.group(1) not in ("and",):
            ok = mtype.group(1) in ("all", "screen")
            q = q[mtype.end():]
        for m in MEDIA_RANGE.finditer(q):
            r = _range(m.group(1), m.group(2), m.group(3))
            ok = None if r is None or ok is None else ok and r
        for m in MEDIA_FEATURE.finditer(MEDIA_RANGE.sub("", q)):
            f = _feature(m.group(1), m.group(2))
            ok = None if f is None or ok is None else ok and f
        if ok is None:
            continue  # unknown: this query makes no claim either way
        if ok != negate:
            return True
    return False


def parse_css(css: str) -> list[tuple[str, str]]:
    """(selector, declarations) pairs in source order: top-level rules, and the rules inside an `@media` that holds on the
    one screen (`media_matches`) or an `@supports`; every other at-rule is skipped."""
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
        low = sel.lower()
        if low.startswith("@media"):
            if media_matches(sel[6:]):
                rules += parse_css(body)
        elif low.startswith("@supports"):
            rules += parse_css(body)
        elif sel and not sel.startswith("@"):
            rules.append((sel, body))
        i = j
    return rules


def specificity(sel: str) -> tuple[int, int, int]:
    ids = len(re.findall(r"#[\w-]+", sel))
    cls = len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:(?!:)[\w-]+", sel))
    types = len(re.findall(r"(?:^|[\s>+~])([a-zA-Z][\w-]*)", sel))
    return ids, cls, types


def _sheets(soup, load_css: Callable[[str], str | None] | None) -> list[str]:
    """The style sheets of the page in document order: `<style>` blocks, and with `load_css` the repository's own
    `<link rel="stylesheet">` files (the loader fetches nothing; it reads a file inside the input folder or gives None).
    A `media` attribute that does not hold on the one screen leaves its sheet out."""
    out = []
    for el in soup.find_all(["style", "link"]):
        media = el.get("media")
        if isinstance(media, str) and not media_matches(media):
            continue
        if el.name == "style":
            out.append(el.get_text())
            continue
        rel = el.get("rel") or []
        rel = rel if isinstance(rel, list) else str(rel).split()
        href = el.get("href")
        if load_css is not None and "stylesheet" in [r.lower() for r in rel] and isinstance(href, str):
            css = load_css(href)
            if css:
                out.append(css[:CSS_CAP])
    return out


def _computed_styles(soup, load_css=None) -> tuple[dict[int, dict[str, str]], dict[tuple[int, str], dict[str, str]]]:
    """(the declarations that win on each element, those of its `::before` and `::after`), by the cascade: importance,
    then inline style over rules, then specificity, then source order."""
    entries: dict[int, list] = {}
    pseudo: dict[tuple[int, str], list] = {}
    order = 0
    for css in _sheets(soup, load_css):
        for sel_group, body in parse_css(css):
            decls = parse_decls(body)
            for sel in _split_top(sel_group, ","):
                sel = sel.strip()
                if not sel:
                    continue
                m = PSEUDO.search(sel)
                base = (sel[:m.start()].strip() or "*") if m else sel
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        matched = soup.select(base)
                except Exception:
                    continue
                spec = specificity(sel)
                for el in matched:
                    for prop, val, imp in decls:
                        rank = ((imp, 0) + spec + (order,), prop, val)
                        if m:
                            pseudo.setdefault((id(el), m.group(1).lower()), []).append(rank)
                        else:
                            entries.setdefault(id(el), []).append(rank)
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
    pseudo_styles = {k: {prop: val for _, prop, val in sorted(v, key=lambda e: e[0])} for k, v in pseudo.items()}
    return styles, pseudo_styles


UNKNOWN = "unknown"  # a color or background that cannot be read: no color claim (spec)
VAR = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*(?:\([^()]*\)[^()]*)*))?\)")
NO_PAINT = {"none", "inherit", "initial", "unset", "revert", "transparent"}


def resolve_vars(value: str, custom: dict, depth: int = 0) -> str | None:
    """`value` with each var(--x[, fallback]) replaced from the inherited custom properties;
    None when a variable is not defined and has no fallback."""
    if "var(" not in value:
        return value
    if depth > 8:
        return None
    missing = []

    def sub(m):
        v = custom.get(m.group(1))
        if v is None:
            v = m.group(2)
        if v is None:
            missing.append(m.group(1))
            return ""
        return v
    out = VAR.sub(sub, value)
    return None if missing else resolve_vars(out, custom, depth + 1)


def _color_of(value: str | None, custom: dict):
    """A declared color: the parsed color, UNKNOWN when it cannot be read, None when not set."""
    if not value:
        return None
    v = resolve_vars(value, custom)
    if v is None:
        return UNKNOWN
    if v.strip().lower() in ("inherit", "unset"):
        return None
    c = colors.parse(v)
    return UNKNOWN if c is None else c


def _bg_of(decl: dict, custom: dict | None = None):
    """The background an element declares: a color, UNKNOWN (an image, a gradient, a variable
    nobody defines), or None (not set, or nothing painted)."""
    for prop in ("background-color", "background"):
        v = decl.get(prop)
        if not v:
            continue
        v = resolve_vars(v, custom or {})
        if v is None or re.search(r"url\(|gradient\(", v, re.I):
            return UNKNOWN
        if v.strip().lower() in NO_PAINT:
            continue
        c = colors.parse(v)
        if c is None:
            for tok in re.findall(r"rgba?\([^)]*\)|#[0-9a-fA-F]+|[a-zA-Z]+", v):
                c = colors.parse(tok)
                if c is not None:
                    break
        if c is not None and c[3] > 0:
            return c
        if c is None:
            return UNKNOWN
    return None


# ---------------------------------------------------------------- size, place, and clipping (R36)

def font_px(value: str, parent: float | None) -> float | None:
    """The font size a declaration gives, in pixels, from its parent's; None when it cannot be read."""
    v = (value or "").strip().lower()
    if not v or v in ("inherit", "unset"):
        return parent
    if v in ("initial", "revert"):
        return ROOT_PX
    if v in FONT_KEYWORDS:
        return FONT_KEYWORDS[v]
    if v in ("smaller", "larger"):
        return None if parent is None else (parent / 1.2 if v == "smaller" else parent * 1.2)
    m = re.fullmatch(r"(-?\d*\.?\d+)%", v)
    if m:
        return None if parent is None else parent * float(m.group(1)) / 100
    return _px(v, parent)


def _far(value: str | None, size: float | None) -> bool:
    px = _px(value or "", size)
    return px is not None and px <= -FAR_PX


def _translated_far(transform: str, size: float | None) -> bool:
    for m in re.finditer(r"translate(?:x|y|3d)?\(([^)]*)\)", transform or "", re.I):
        if any(_far(p.strip(), size) for p in re.split(r"[,\s]+", m.group(1)) if p.strip()):
            return True
    return False


def off_page(decl: dict, size: float | None) -> bool:
    """Text placed far off the page: an absolutely or fixed positioned box offset 1,000 px or more the wrong way, a
    `text-indent` or margin that far negative, or a transform that moves it that far."""
    positioned = decl.get("position", "").strip().lower() in ("absolute", "fixed")
    if positioned and any(_far(decl.get(side), size) for side in ("left", "top", "right", "bottom")):
        return True
    if _far(decl.get("text-indent"), size):
        return True
    if any(_far(decl.get(p), size) for p in ("margin-left", "margin-top")):
        return True
    return _translated_far(decl.get("transform", ""), size)


def clipped(decl: dict, size: float | None) -> bool:
    """Text clipped away: `clip` to a rectangle with no area on a positioned box, or `clip-path` to nothing."""
    clip = decl.get("clip", "")
    m = re.fullmatch(r"\s*rect\(([^)]*)\)\s*", clip, re.I)
    if m and decl.get("position", "").strip().lower() in ("absolute", "fixed"):
        parts = [p for p in re.split(r"[,\s]+", m.group(1).strip()) if p]
        if len(parts) == 4:
            top, right, bottom, left = (_px(p, size) for p in parts)
            if None not in (top, bottom) and bottom <= top or None not in (left, right) and right <= left:
                return True
    cp = decl.get("clip-path", "").strip().lower()
    m = re.fullmatch(r"inset\(\s*(\d*\.?\d+)%[^)]*\)", cp)
    if m and float(m.group(1)) >= 50:
        return True
    return bool(re.fullmatch(r"circle\(\s*0(?:\.0*)?(?:px|%)?\s*(?:at [^)]*)?\)", cp))


def zero_size(decl: dict, size: float | None) -> bool:
    """Text in a box 1 px or smaller that hides what overflows it, or scaled to nothing."""
    overflow = {decl.get(p, "").strip().lower() for p in ("overflow", "overflow-x", "overflow-y")}
    if overflow & {"hidden", "clip"}:
        for prop in ("width", "height", "max-width", "max-height"):
            px = _px(decl.get(prop, ""), size)
            if px is not None and px <= 1:
                return True
    return bool(re.search(r"scale[xy]?\(\s*0(?:\.0*)?\s*[,)]", decl.get("transform", ""), re.I))


def css_content(decl: dict) -> str:
    """The plain strings a `content` declaration adds (counters, `attr()`, images, and quotes are not read)."""
    if decl.get("display", "").strip().lower() == "none":
        return ""
    v = decl.get("content", "")
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'', v)
    text = "".join(a or b for a, b in parts)
    text = re.sub(r"\\([0-9a-fA-F]{1,6})\s?", lambda m: chr(int(m.group(1), 16)), text)
    return collapse(re.sub(r"\\(.)", r"\1", text))


# ---------------------------------------------------------------- the readings

def read_html(text: str, load_css: Callable[[str], str | None] | None = None) -> dict:
    """{"divergences": [...], "painted": [str]}. `load_css`: href -> the text of a style sheet in the repository, or
    None (it fetches nothing)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        soup = BeautifulSoup(text, "html.parser")
    styles, pseudo = _computed_styles(soup, load_css)

    text_items: list[tuple] = []   # (key, carrier, line, text)
    painted_items: list[tuple] = []  # (key, text)
    extra: list[dict] = []          # comments, attributes, and text a style sheet adds
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
        fs = decl.get("font-size", "").strip().lower()
        if fs:
            st["size0"] = bool(ZERO_SIZE.match(fs))
            st["fpx"] = font_px(fs, st["fpx"])
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
            elif off_page(decl, st["fpx"]):
                st["hard"] = ("off-page", el)
            elif clipped(decl, st["fpx"]):
                st["hard"] = ("clipped", el)
            elif zero_size(decl, st["fpx"]):
                st["hard"] = ("zero-size", el)
        vis = decl.get("visibility", "").lower()
        if vis:
            st["vis"] = vis
        custom = {k: v for k, v in decl.items() if k.startswith("--")}
        if custom:
            st["vars"] = {**st["vars"], **custom}
        c = _color_of(decl.get("color"), st["vars"])
        if c is not None:
            st["color"] = c
        bg = _bg_of(decl, st["vars"])
        if bg is not None:
            st["bg"] = bg

        def shown() -> bool:
            return (st["hard"] is None and st["vis"] not in ("hidden", "collapse") and not st["size0"]
                    and not (st["fpx"] is not None and st["fpx"] < TINY_PX))

        added = {p: css_content(pseudo.get((id(el), p), {})) for p in ("before", "after")}
        if added["before"] and len(re.findall(r"[^\W\d_]", added["before"])) >= 3 and shown():
            extra.append({"line": line, "text": added["before"], "carrier": "css-content", "reading": "B-only",
                          "pseudo": "before"})

        closed = name == "details" and not el.has_attr("open")
        summary = next((c for c in el.children if isinstance(c, Tag) and (c.name or "").lower() == "summary"), None) \
            if closed else None
        for child in el.children:
            cst = st
            if closed and child is not summary and st["hard"] is None:
                cst = {**st, "hard": ("details", el)}
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
                if cst["hard"] is not None:
                    carrier, root = cst["hard"]
                    text_items.append(((carrier, id(root)), carrier, root.sourceline, t))
                elif st["vis"] in ("hidden", "collapse"):
                    text_items.append((("visibility:hidden", id(el)), "visibility:hidden", line, t))
                elif st["size0"]:
                    text_items.append((("font-size:0", id(el)), "font-size:0", line, t))
                elif st["fpx"] is not None and st["fpx"] < TINY_PX:
                    text_items.append((("tiny-text", id(el)), "tiny-text", line, t))
                elif UNKNOWN not in (st["color"], st["bg"]) and colors.hides(st["color"], st["bg"]):
                    carrier = colors.carrier(st["color"], st["bg"])
                    text_items.append(((carrier, id(el)), carrier, line, t))
                else:
                    painted_items.append((id(el), t))
            elif isinstance(child, Tag):
                walk(child, cst)
        if added["after"] and len(re.findall(r"[^\W\d_]", added["after"])) >= 3 and shown():
            extra.append({"line": line, "text": added["after"], "carrier": "css-content", "reading": "B-only",
                          "pseudo": "after"})

    root_state = {"hard": None, "vis": "visible", "size0": False, "fpx": ROOT_PX, "color": BLACK,
                  "bg": colors.WHITE, "vars": {}}
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
    divergences = [d for d in divergences if d["text"] and (d.get("reading") == "B-only" or d["text"] not in painted_set)]
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
