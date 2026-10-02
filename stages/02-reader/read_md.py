"""Markdown carriers: raw content a rendered view hides. Spec: specs/read_md.SPEC.md."""
from __future__ import annotations

import bisect
import re

FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
TAG = re.compile(r"<([a-zA-Z][\w-]*)((?:\s(?:[^<>\"']|\"[^\"]*\"|'[^']*')*)?)/?>")
ATTR = re.compile(r"([a-zA-Z_:][\w:.-]*)(?:\s*=\s*(\"([^\"]*)\"|'([^']*)'|([^\s\"'=<>`]+)))?")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
        "source", "track", "wbr"}
IMAGE = re.compile(r"!\[((?:[^\[\]\n]|\[[^\[\]\n]*\])*)\](?=[\(\[])")
LINK_TITLE = re.compile(r"\]\(\s*(?:<[^<>\n]*>|[^\s()<>]+(?:\([^\s()]*\))?)\s+"
                        r"(?:\"([^\"]*)\"|'([^']*)'|\(([^()]*)\))\s*\)")
REF_DEF = re.compile(r"^ {0,3}\[([^\]\^][^\]]*)\]:[ \t]*(\S+)(.*)$")
BRACKET = re.compile(r"\[([^\[\]\n]+)\]")
STYLE_HIDES = [("display:none", re.compile(r"display\s*:\s*none", re.I)),
               ("visibility:hidden", re.compile(r"visibility\s*:\s*hidden", re.I)),
               ("font-size:0", re.compile(r"font-size\s*:\s*0(?:\.0*)?(?:px|pt|em|rem|%)?\s*(?:;|$|!)", re.I)),
               ("opacity:0", re.compile(r"(?<![\w-])opacity\s*:\s*0(?:\.0*)?\s*(?:;|$|!)", re.I))]


def _blank(chars: list[str], a: int, b: int) -> None:
    for i in range(a, b):
        if chars[i] != "\n":
            chars[i] = " "


def _attrs(s: str) -> dict:
    out = {}
    for m in ATTR.finditer(s or ""):
        val = m.group(3) if m.group(3) is not None else (
            m.group(4) if m.group(4) is not None else m.group(5))
        out[m.group(1).lower()] = val if val is not None else ""
    return out


class _Doc:
    def __init__(self, text: str):
        self.text = text
        self.starts = [0] + [i + 1 for i, c in enumerate(text) if c == "\n"]

    def line(self, pos: int) -> int:
        return bisect.bisect_right(self.starts, pos)


def _mask_blocks(text: str) -> list[str]:
    """Blank the YAML frontmatter and fenced code blocks."""
    chars = list(text)
    lines = text.split("\n")
    offs, o = [], 0
    for ln in lines:
        offs.append(o)
        o += len(ln) + 1
    i = 0
    if lines and lines[0].rstrip("\r") == "---":
        for j in range(1, len(lines)):
            if lines[j].rstrip("\r") in ("---", "..."):
                _blank(chars, 0, offs[j] + len(lines[j]))
                i = j + 1
                break
    while i < len(lines):
        m = FENCE_OPEN.match(lines[i].rstrip("\r"))
        if m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            fence = m.group(1)
            close = re.compile(r"^ {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}\s*$")
            j = i + 1
            while j < len(lines) and not close.match(lines[j].rstrip("\r")):
                j += 1
            end = offs[j] + len(lines[j]) if j < len(lines) else len(text)
            _blank(chars, offs[i], end)
            i = j + 1
            continue
        i += 1
    return chars


def _scan_inline(masked: list[str]) -> tuple[list[tuple[int, int, int, int]], list[str]]:
    """Find comments and code spans left to right. Returns comment spans
    (start, end, inner_start, inner_end) and a copy with code and comments blanked."""
    s = "".join(masked)
    out = list(masked)
    comments = []
    pos, n = 0, len(s)
    token = re.compile(r"`+|<!--")
    while pos < n:
        m = token.search(s, pos)
        if not m:
            break
        if m.group(0) == "<!--":
            start = m.start()
            if s.startswith(">", m.end()) or s.startswith("->", m.end()):
                end = s.index(">", m.end()) + 1
                _blank(out, start, end)
                pos = end
                continue
            close = s.find("-->", m.end())
            end = n if close < 0 else close + 3
            inner_end = n if close < 0 else close
            comments.append((start, end, m.end(), inner_end))
            _blank(out, start, end)
            pos = end
        else:
            run = len(m.group(0))
            closer = re.compile(r"(?<!`)`{" + str(run) + r"}(?!`)")
            c = closer.search(s, m.end())
            if c:
                _blank(out, m.start(), c.end())
                pos = c.end()
            else:
                pos = m.end()
    return comments, out


def _closing(s: str, tag: str, start: int) -> tuple[int, int] | None:
    """(inner_end, end) of the element whose open tag ends at `start`."""
    pat = re.compile(r"<(/?)" + re.escape(tag) + r"(?=[\s>/])[^>]*>", re.I)
    depth = 1
    for m in pat.finditer(s, start):
        if m.group(1):
            depth -= 1
            if depth == 0:
                return m.start(), m.end()
        elif not m.group(0).endswith("/>"):
            depth += 1
    return None


def carriers(text: str) -> list[dict]:
    doc = _Doc(text)
    blocks = _mask_blocks(text)
    comments, masked_list = _scan_inline(blocks)
    masked = "".join(masked_list)
    found: list[tuple[int, dict]] = []

    def add(pos, carrier, value, **extra):
        value = value.strip()
        if value:
            found.append((pos, {"line": doc.line(pos), "text": value, "carrier": carrier, **extra}))

    for start, _end, a, b in comments:
        add(start, "comment", text[a:b])

    hidden_ranges: list[tuple[int, int]] = []
    for m in TAG.finditer(masked):
        name = m.group(1).lower()
        attrs = _attrs(m.group(2))
        if "alt" in attrs:
            add(m.start(), "alt", attrs["alt"])
        if "title" in attrs:
            add(m.start(), "title", attrs["title"])
        if name in VOID or m.group(0).endswith("/>"):
            continue
        if any(a <= m.start() < b for a, b in hidden_ranges):
            continue
        kind = None
        if name == "details":
            if "open" in attrs:
                continue
            kind = "details"
        elif "hidden" in attrs:
            kind = "hidden"
        else:
            style = attrs.get("style", "")
            for label, pat in STYLE_HIDES:
                if pat.search(style):
                    kind = label
                    break
        if not kind:
            continue
        close = _closing(masked, name, m.end())
        if not close:
            continue
        inner = text[m.end():close[0]]
        if kind == "details":
            inner = re.sub(r"<summary\b[^>]*>.*?</summary\s*>", "", inner, count=1,
                           flags=re.I | re.S)
        hidden_ranges.append((m.start(), close[1]))
        add(m.start(), kind, inner)

    for m in IMAGE.finditer(masked):
        add(m.start(), "alt", text[m.start(1):m.end(1)])
    for m in LINK_TITLE.finditer(masked):
        g = next(i for i in (1, 2, 3) if m.group(i) is not None)
        add(m.start(g), "link-title", text[m.start(g):m.end(g)])

    lines = masked.split("\n")
    def_lines = set()
    defs = []
    off = 0
    for i, ln in enumerate(lines):
        r = REF_DEF.match(ln.rstrip("\r"))
        if r:
            def_lines.add(i)
            defs.append((off, r.group(1), i))
        off += len(ln) + 1
    if defs:
        rest = "\n".join(ln for i, ln in enumerate(lines) if i not in def_lines)
        refs = {" ".join(b.split()).casefold() for b in BRACKET.findall(rest)}
        raw_lines = text.split("\n")
        for pos, label, i in defs:
            used = " ".join(label.split()).casefold() in refs
            add(pos, "reference-definition", raw_lines[i].rstrip("\r"), used=used)

    found.sort(key=lambda t: t[0])
    return [f for _, f in found]


def comment_count(text: str) -> int:
    return sum(1 for c in carriers(text) if c["carrier"] == "comment")
