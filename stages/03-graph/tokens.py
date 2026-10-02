"""Decide whether a token is a file reference, and its shape. Spec: specs/tokens.SPEC.md."""
from __future__ import annotations

import re
from dataclasses import dataclass

KNOWN_EXTS = {
    "md", "markdown", "mdx", "txt", "rst", "adoc", "org",
    "json", "jsonc", "json5", "yaml", "yml", "toml", "ini", "cfg", "conf", "xml",
    "csv", "tsv", "lock",
    "py", "pyi", "js", "mjs", "cjs", "jsx", "ts", "mts", "cts", "tsx", "sh", "bash", "zsh",
    "fish", "ps1", "psm1", "psd1", "bat", "cmd", "rb", "pl", "php", "lua", "go", "rs", "java",
    "kt", "swift", "c", "h", "cpp", "hpp", "cs", "r", "sql", "awk", "vue", "svelte",
    "html", "htm", "css", "scss", "svg", "png", "jpg", "jpeg", "gif", "webp", "ico", "bmp",
    "pdf", "docx", "doc", "xlsx", "pptx", "odt", "rtf", "epub",
    "zip", "tar", "gz", "tgz", "whl", "jar",
    "log", "patch", "diff", "tmpl", "template", "j2", "hbs", "mustache", "ipynb",
}

URL_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*://|mailto:|data:|javascript:|tel:)", re.I)
EXT_RE = re.compile(r"\.([A-Za-z0-9_-]{1,10})$")
PLACEHOLDER_RE = re.compile(r"^(?:\$\{[A-Za-z_][A-Za-z0-9_]*\}|\$[A-Za-z_][A-Za-z0-9_]*"
                            r"|%[A-Za-z_][A-Za-z0-9_]*%)[/\\]")
HOME_RE = re.compile(r"^(?:~|\$HOME\b|\$\{HOME\}|%USERPROFILE%|%HOMEPATH%|%APPDATA%"
                     r"|%LOCALAPPDATA%)", re.I)
CLASS_RE = re.compile(r"\[(?!\d+\])[^\]/]+\]")  # [0] is an index, not a class
MD_ESCAPE_RE = re.compile(r"\\([_*\[\]()#`~])")
TEMPLATE_RE = re.compile(r"<[^<>/\s]+>|(?<!\$)\{[^{}]*\}")
REGEX_RE = re.compile(r"\^|\$$|\\\.|\.[*+]|\(\?|\.\.\.")

LEAD = "([{<>@\"'`"
TRAIL = ")]}><\"'`,;:!?.\\"


@dataclass(frozen=True)
class Ref:
    written: str
    path: str
    shape: str
    may_dangle: bool


def clean(token: str) -> str:
    t = token
    while True:
        prev = t
        t = t.lstrip(LEAD)
        t = t.rstrip(TRAIL)
        t = re.sub(r"^\.{3,}(?=[A-Za-z_$])", "", t)  # a JS spread, not a path
        t = re.sub(r"^\*+(?![*/.])", "", t)
        t = re.sub(r"(?<=[^/*])\*+$", "", t)
        m = re.match(r"^(_+)(.+?)(_+)$", t)
        if m and m.group(1) == m.group(3):
            t = m.group(2)  # symmetric _emphasis_; never touches __init__.py
        if t == prev:
            return t


def _has_ext(segment: str) -> str | None:
    """The extension of a file-name segment, or None."""
    m = EXT_RE.search(segment)
    if not m or not re.search(r"[A-Za-z]", m.group(1)):
        return None
    return m.group(1).lower()


def _stem(segment: str) -> str:
    m = EXT_RE.search(segment)
    return segment[: m.start()] if m else segment


def classify(token: str, context: str) -> Ref | None:
    written = clean(MD_ESCAPE_RE.sub(lambda m: m.group(1), token))
    if not written or written.startswith("#") or URL_RE.match(written):
        return None
    if "://" in written:
        return None
    t = written.replace("\\", "/")
    if HOME_RE.match(t):
        return None
    if t.startswith("/") or re.match(r"^[A-Za-z]:/", t):
        return None
    if REGEX_RE.search(written) or TEMPLATE_RE.search(written):
        return None  # a regex or a template, not a fixed path
    t = PLACEHOLDER_RE.sub("", written).replace("\\", "/") if PLACEHOLDER_RE.match(written) else t
    if "$" in t or "%" in t.split("/")[0]:
        return None  # a variable left in the path: target not knowable here
    while t.startswith("./"):
        t = t[2:]
    t = t.split("#", 1)[0]
    if "?" in t:
        head, _, tail = t.partition("?")
        if "=" in tail or "&" in tail:
            t = head
    if not t or t in (".", ".."):
        return None
    if t.startswith("/") or t == ".git" or t.startswith(".git/"):
        return None  # .git/ is not part of the input

    last = t.rstrip("/").rsplit("/", 1)[-1]
    has_slash = "/" in t.rstrip("/") or t.endswith("/")
    ext = _has_ext(last)
    dotfile = last.startswith(".") and len(last) > 1 and "." not in last[1:]
    globby = ("*" in t or "?" in t or bool(CLASS_RE.search(t)))

    if globby:
        if "\\" in written:
            return None  # an escaped string (\n, \d), not a glob
        if has_slash or ext:
            if not re.search(r"[A-Za-z0-9]", t):
                return None
            return Ref(written, t, "glob", True)
        return None
    if t.endswith("/"):
        if not re.search(r"[A-Za-z0-9]", t):
            return None
        return Ref(written, t, "dir", True)
    if has_slash:
        if ext or dotfile:
            return Ref(written, t, "path", True)
        if context in ("code", "link", "config"):
            return Ref(written, t, "slashed" if context != "link" else "link",
                       context == "link")
        return None
    # no slash
    if dotfile:
        if context in ("prose", "comment"):
            return None
        return Ref(written, t, "bare", context == "link")
    if ext and _stem(last):
        if context == "link":
            dangle = True
        elif context in ("code", "config"):
            dangle = ext in KNOWN_EXTS
        else:
            dangle = False
        return Ref(written, t, "bare", dangle)
    if context == "link":
        return Ref(written, t, "link", True)
    return None
