"""Find every reference a text file makes. Spec: specs/extract.SPEC.md."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

import tokens
from invisible import strip_line

CONFIG_EXTS = {"json", "jsonc", "yaml", "yml", "toml"}
SCRIPT_EXTS = {"py", "js", "mjs", "cjs", "ts", "mts", "cts", "sh", "bash", "zsh", "ps1",
               "psm1", "rb", "pl"}
SHELL_EXTS = {"sh", "bash", "zsh", "ps1", "psm1"}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "fish", "pwsh", "powershell"}

SPLIT_RE = re.compile(r"[\s|,;=()\"'`]+")
TOKEN_RE = re.compile(r"[^\s|,;=()\"'`]+")
HTML_TAG_RE = re.compile(
    r"</?(?:a|b|i|u|s|em|strong|code|kbd|pre|br|hr|p|div|span|img|details|summary|sup|sub"
    r"|li|ul|ol|dl|dt|dd|table|thead|tbody|tr|td|th|h[1-6]|mark|small|center|font|blockquote"
    r"|picture|source|video|audio|figure|figcaption|section|article|nav|header|footer|script"
    r"|style|link|meta|html|head|body|title|svg|path|g|text)\b[^<>]*>", re.I)
# Pattern-list files: every line is a match rule for a tool, not a load.
PATTERN_LISTS = {".gitignore", ".gitattributes", ".npmignore", ".dockerignore",
                 ".prettierignore", ".eslintignore", ".ignore", ".rgignore", ".gcloudignore",
                 ".vscodeignore", "CODEOWNERS"}
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
MD_LINK_RE = re.compile(r"(!?)\[((?:[^\[\]]|\[[^\[\]]*\])*)\]\(\s*(<[^>]*>|[^\s)]+)"
                        r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)")
REF_DEF_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(<[^>]*>|\S+)")
HTML_ATTR_RE = re.compile(r"\b(?:href|src)\s*=\s*(\"[^\"]*\"|'[^']*')", re.I)
CODE_SPAN_RE = re.compile(r"(`+)(.+?)\1")
STRING_RE = re.compile(r"\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)'|`((?:[^`\\]|\\.)*)`")


@dataclass(frozen=True)
class Found:
    line: int
    ref: tokens.Ref
    context: str
    form: str


def ext_of(rel: str) -> str:
    base = rel.rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[1].lower() if "." in base else ""


def shebang(text: str) -> str | None:
    if not text.startswith("#!"):
        return None
    words = text.split("\n", 1)[0][2:].strip().split()
    if not words:
        return ""
    interp = words[0].rsplit("/", 1)[-1]
    if interp == "env":
        rest = [w for w in words[1:] if not w.startswith("-")]
        interp = rest[0] if rest else ""
    return re.sub(r"[\d.]+$", "", interp)


def script_kind(rel: str, text: str) -> str | None:
    """'shell', 'script', or None."""
    ext = ext_of(rel)
    if ext in SHELL_EXTS:
        return "shell"
    if ext in SCRIPT_EXTS:
        return "script"
    interp = shebang(text)
    if interp is None:
        return None
    return "shell" if interp in SHELLS else "script"


def split_lines(text: str) -> list[str]:
    return [strip_line(l[:-1] if l.endswith("\r") else l) for l in text.split("\n")]


class _Out:
    def __init__(self):
        self.items: list[Found] = []
        self.seen: set[tuple[int, str]] = set()

    def add(self, line: int, raw: str, context: str, form: str) -> None:
        ref = tokens.classify(raw, context)
        if ref is None:
            return
        key = (line, ref.path)
        if key in self.seen:
            return
        self.seen.add(key)
        self.items.append(Found(line, ref, context, form))

    def words(self, line: int, text: str, context: str, form: str) -> None:
        text = HTML_TAG_RE.sub(" ", text)
        for m in TOKEN_RE.finditer(text):
            w = m.group(0)
            if m.end() < len(text) and text[m.end()] == "(" and "/" not in w:
                continue  # a call such as console.log(...), not a file
            self.add(line, w, context, form)


# ---------- config ----------

def _load_config(ext: str, text: str):
    try:
        if ext == "json":
            return json.loads(text)
        if ext == "jsonc":
            no_comments = re.sub(r"(?m)^\s*//.*$", "", text)
            return json.loads(no_comments)
        if ext in ("yaml", "yml"):
            import yaml
            return list(yaml.safe_load_all(text))
        if ext == "toml":
            import tomllib
            return tomllib.loads(text)
    except Exception:
        return None
    return None


def _strings(doc):
    if isinstance(doc, str):
        yield doc
    elif isinstance(doc, dict):
        for v in doc.values():
            yield from _strings(v)
    elif isinstance(doc, (list, tuple)):
        for v in doc:
            yield from _strings(v)


def _config(lines: list[str], doc) -> list[Found]:
    out = _Out()
    cursor = 0

    def locate(needle: str) -> int:
        nonlocal cursor
        for i in range(cursor, len(lines)):
            if needle in lines[i]:
                cursor = i
                return i + 1
        for i, l in enumerate(lines):
            if needle in l:
                return i + 1
        return 0

    for s in _strings(doc):
        s = strip_line(s).strip()
        parts = [s] if not re.search(r"\s", s) else SPLIT_RE.split(s)
        for w in parts:
            if not w:
                continue
            ref = tokens.classify(w, "config")
            if ref is None:
                continue
            ln = locate(ref.written)
            if not ln and "\\" in ref.written:
                ln = locate(ref.written.replace("\\", "\\\\"))
            if not ln:
                ln = locate(ref.path)
            ln = ln or 1
            key = (ln, ref.path)
            if key in out.seen:
                continue
            out.seen.add(key)
            out.items.append(Found(ln, ref, "config", "config"))
    return out.items


# ---------- scripts ----------

def _script(lines: list[str], shell: bool) -> list[Found]:
    out = _Out()
    for i, line in enumerate(lines, 1):
        if shell:
            out.words(i, line, "code", "script")
        else:
            for m in STRING_RE.finditer(line):
                body = next(g for g in m.groups() if g is not None)
                out.words(i, body, "code", "script")
    return out.items


# ---------- text / markdown ----------

def _prose_line(out: _Out, i: int, line: str) -> None:
    """Links, then code spans, then prose, on one line outside fences and comments."""
    rest = line
    m = REF_DEF_RE.match(rest)
    if m:
        out.add(i, m.group(1).strip("<>"), "link", "reference-def")
        rest = rest[: m.start(1)] + " " + rest[m.end(1):]

    def link_sub(m: re.Match) -> str:
        out.add(i, m.group(3).strip("<>"), "link", "image" if m.group(1) else "markdown-link")
        return " " + m.group(2) + " "

    rest = MD_LINK_RE.sub(link_sub, rest)

    def attr_sub(m: re.Match) -> str:
        out.add(i, m.group(1)[1:-1], "link", "html-attr")
        return " "

    rest = HTML_ATTR_RE.sub(attr_sub, rest)

    def code_sub(m: re.Match) -> str:
        out.words(i, m.group(2), "code", "code-span")
        return " "

    rest = CODE_SPAN_RE.sub(code_sub, rest)
    out.words(i, rest, "prose", "prose")


def _is_fence_close(line: str, fence: str) -> bool:
    m = FENCE_RE.match(line)
    if not m:
        return False
    mark = m.group(1)
    return (mark[0] == fence[0] and len(mark) >= len(fence)
            and not line[m.end():].strip())


def _text(lines: list[str]) -> list[Found]:
    out = _Out()
    fence: str | None = None
    in_comment = False
    for i, line in enumerate(lines, 1):
        if fence is not None:
            if _is_fence_close(line, fence):
                fence = None
            else:
                out.words(i, line, "code", "fenced")
            continue
        if not in_comment:
            m = FENCE_RE.match(line)
            if m:
                fence = m.group(1)
                continue
        pos = 0
        comments: list[str] = []
        texts: list[str] = []
        while True:
            if in_comment:
                end = line.find("-->", pos)
                if end < 0:
                    comments.append(line[pos:])
                    break
                comments.append(line[pos:end])
                pos = end + 3
                in_comment = False
            else:
                start = line.find("<!--", pos)
                if start < 0:
                    texts.append(line[pos:])
                    break
                texts.append(line[pos:start])
                pos = start + 4
                in_comment = True
        for c in comments:
            out.words(i, c, "comment", "comment")
        joined = " ".join(texts)
        if joined.strip():
            _prose_line(out, i, joined)
    return out.items


def extract(rel: str, text: str) -> list[Found]:
    if rel.rsplit("/", 1)[-1] in PATTERN_LISTS:
        return []
    lines = split_lines(text)
    ext = ext_of(rel)
    if ext in CONFIG_EXTS:
        doc = _load_config(ext, text)
        if doc is not None:
            return _config(lines, doc)
    kind = script_kind(rel, text)
    if kind is not None:
        return _script(lines, kind == "shell")
    return _text(lines)
