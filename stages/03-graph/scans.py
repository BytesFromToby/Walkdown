"""Find code that lists or globs a folder. Spec: specs/scans.SPEC.md."""
from __future__ import annotations

import re
from dataclasses import dataclass

from extract import script_kind, split_lines


@dataclass(frozen=True)
class Scan:
    line: int
    call: str
    pattern: str
    literal: bool
    recursive: bool


# (regex for the call name up to its "(", call label, recursive: True/False/None=pattern decides)
FUNC_CALLS = [
    (re.compile(r"\bos\.listdir\s*\("), "os.listdir", False),
    (re.compile(r"\bos\.scandir\s*\("), "os.scandir", False),
    (re.compile(r"\bos\.walk\s*\("), "os.walk", True),
    (re.compile(r"\bglob\.i?glob\s*\("), "glob.glob", None),
    (re.compile(r"\.rglob\s*\("), "rglob", True),
    (re.compile(r"(?<!\bglob)\.glob\s*\("), ".glob", None),
    (re.compile(r"\breaddirSync\s*\("), "readdirSync", False),
    (re.compile(r"(?<![\w.])(?:fs\.|fsp\.|promises\.)?readdir\s*\("), "readdir", False),
    (re.compile(r"\bopendir(?:Sync)?\s*\("), "opendir", False),
    (re.compile(r"(?<![\w.])glob(?:Sync)?\s*\("), "glob", None),
]
SHELL_CMD = re.compile(r"(?:^|;|&&|\|\||\||\$\(|`)\s*(ls|find|Get-ChildItem|gci)\b(?!-)",
                       re.I)
LITERAL_RE = re.compile(r"\s*(?:[rRbBuUfF]{0,2})(\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)'"
                        r"|`((?:[^`\\$]|\\.)*)`)\s*[,)]")


def is_script(rel: str, text: str) -> bool:
    return script_kind(rel, text) is not None


def _call_text(line: str, start: int, open_paren: int) -> str:
    depth = 0
    for j in range(open_paren, len(line)):
        if line[j] == "(":
            depth += 1
        elif line[j] == ")":
            depth -= 1
            if depth == 0:
                return line[start:j + 1]
    return line[start:].rstrip()


def _globby(p: str) -> bool:
    return any(c in p for c in "*?[")


def _func_scans(i: int, line: str) -> list[Scan]:
    out: list[Scan] = []
    taken: set[int] = set()
    for rx, label, rec in FUNC_CALLS:
        for m in rx.finditer(line):
            paren = m.end() - 1
            if paren in taken:
                continue
            taken.add(paren)
            lit = LITERAL_RE.match(line, paren + 1)
            if lit:
                pattern = next(g for g in lit.groups()[1:] if g is not None)
                literal = True
            else:
                pattern = _call_text(line, m.start(), paren).lstrip(".")
                literal = False
            recursive = rec if rec is not None else ("**" in pattern)
            out.append(Scan(i, label, pattern, literal, recursive))
    return out


def _shell_scans(i: int, line: str) -> list[Scan]:
    out: list[Scan] = []
    for m in SHELL_CMD.finditer(line):
        cmd = m.group(1)
        rest = line[m.end():]
        stop = re.search(r"[;|)&`]", rest)
        args_text = rest[: stop.start()] if stop else rest
        args = args_text.split()
        low = cmd.lower()
        if low == "find":
            recursive = True
        elif low == "ls":
            recursive = any(a.startswith("-") and not a.startswith("--") and "R" in a
                            for a in args)
        else:
            recursive = any(a.lower() == "-recurse" for a in args)
        target = None
        skip_next = False
        for a in args:
            if skip_next:
                skip_next = False
                continue
            if a.startswith("-"):
                if cmd.lower() in ("get-childitem", "gci") and a.lower() in (
                        "-filter", "-include", "-exclude", "-depth"):
                    skip_next = True
                continue
            target = a
            break
        if target is None:
            out.append(Scan(i, cmd, ".", False, recursive))
            continue
        pattern = target.strip("\"'")
        literal = not any(c in target for c in "$%`")
        out.append(Scan(i, cmd, pattern, literal, recursive))
    return out


def find_scans(rel: str, text: str) -> list[Scan]:
    kind = script_kind(rel, text)
    if kind is None:
        return []
    out: list[Scan] = []
    for i, line in enumerate(split_lines(text), 1):
        stripped = line.lstrip()
        if stripped.startswith("#") and not stripped.startswith("#!"):
            continue  # a comment line is not a call
        if stripped.startswith("//"):
            continue
        out.extend(_func_scans(i, line))
        if kind == "shell":
            out.extend(_shell_scans(i, line))
    return out
