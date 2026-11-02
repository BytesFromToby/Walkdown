"""The version of `02.4-phrases`'s search terms and matching code, recorded in every report so two runs
can tell a hit that comes from the repository from one that comes from Walkdown (review C22 b,
2026-10-19). Spec: specs/phrases.SPEC.md, termset.
"""
from __future__ import annotations

import ast
import hashlib
import io
import json
import sys
import tokenize
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "_shared"))
import library  # noqa: E402

# the fields of a pattern row that decide whether it hits; `note` and `source` never do
MATCH_FIELDS = ("check", "regex", "unless", "audiences", "paths", "where")
SHORT = 12


def _h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:SHORT]


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def row_versions(rows) -> dict[str, str]:
    """One short hash per row id, over the fields that decide a hit."""
    return {r.id: _h(_canon({k: getattr(r, k) for k in MATCH_FIELDS})) for r in rows}


def _no_sources(obj):
    """The word lists without their `source` labels, which never decide a hit (notes M15 a)."""
    if isinstance(obj, dict):
        return {k: _no_sources(v) for k, v in obj.items() if k != "source"}
    if isinstance(obj, list):
        return [_no_sources(v) for v in obj]
    return obj


def vocab_version(path=None) -> str | None:
    """The part 2 word lists as loaded (comments, layout, and `source` labels do not count); None
    when unreadable."""
    path = Path(path) if path else library.path("vocab.yaml")
    try:
        return _h(_canon(_no_sources(yaml.safe_load(path.read_text("utf-8")))))
    except (OSError, yaml.YAMLError):
        return None


SKIP = {tokenize.COMMENT, tokenize.NL, tokenize.ENCODING}
STARTS = {tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING}


def _code_tokens(source: bytes) -> bytes:
    """A script's tokens without its comments, blank lines, and docstrings (a statement that is only a
    string does nothing when it runs), so a comment or docstring edit is not a code change (2026-10-29,
    after step 8a). Source that does not tokenize counts as it is."""
    try:
        toks = [t for t in tokenize.tokenize(io.BytesIO(source).readline) if t.type not in SKIP]
    except (tokenize.TokenError, SyntaxError):
        return source
    keep, i, prev = [], 0, tokenize.ENCODING
    while i < len(toks):
        j = i
        while prev in STARTS and j < len(toks) and toks[j].type == tokenize.STRING:
            j += 1
        if j > i and j < len(toks) and toks[j].type == tokenize.NEWLINE:
            i, prev = j + 1, tokenize.NEWLINE  # a string statement: dropped with its NEWLINE
            continue
        keep.append(f"{tokenize.tok_name[toks[i].type]} {toks[i].string}")
        prev = toks[i].type
        i += 1
    return "\n".join(keep).encode("utf-8")


def invisible_list() -> bytes:
    """The invisible-character list as loaded (`Library/invisible.yaml`): each code point and its
    action, in code point order, and the run length. Names, kinds, dates, sources, and notes do not
    count. The list decides a hit as the code does (a keyword split by a listed character matches),
    so a change to it changes `code_version` (2026-10-29, P1)."""
    inv = library.invisible()
    rows = sorted((ord(ch), action) for action, chars in
                  (("strip", inv.strip), ("space", inv.space), ("run", inv.run)) for ch in chars)
    return _canon({"list": rows, "run_length": inv.run_length})


SHARED = HERE.parents[1] / "_shared"
# Shared modules the phrase step imports that decide no hit: what runs an earlier step, the step list, how a
# note is written, and the coverage counts. A module not named here counts, so a new import can read as a
# change to the matching code and can never hide one.
NOT_MATCHING = frozenset({"coverlines", "earlier_steps", "stagelist", "stagenote"})


def imported_shared(folder=None, shared=None) -> list[Path]:
    """The `stages/_shared/*.py` modules that a .py file directly in `folder` imports (`import x`,
    `from x import y`, at any depth, found by reading the imports with `ast`, so a new import is covered
    with no list to keep), by file name, leaving out `NOT_MATCHING`. A name that is also a file in `folder`
    means that file. A file that does not parse imports nothing. (2026-10-29, P1: the run decoding lives in
    `library.py`, which decides a hit as `readtext.py` always did, and neither was in the hash.)"""
    folder = Path(folder) if folder else HERE
    shared = Path(shared) if shared else SHARED
    own = {p.stem for p in folder.glob("*.py")}
    names = {p.stem: p for p in shared.glob("*.py") if p.stem not in own}
    found: set[str] = set()
    for p in folder.glob("*.py"):
        try:
            tree = ast.parse(p.read_bytes())
        except (SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module]
            else:
                continue
            found |= {m.split(".")[0] for m in mods} & names.keys()
    return [names[k] for k in sorted(found - NOT_MATCHING)]


def code_version(folder=None, shared=None) -> str:
    """`02.4-phrases`'s code: every .py file directly in the stage folder (tests are in a subfolder),
    by name, and the `stages/_shared` modules those files import that decide a hit (`imported_shared`), by
    file name after them, each as its tokens without comments and docstrings (`_code_tokens`), with line endings
    normalized so a Windows checkout and a Linux one agree, and the invisible-character list the
    code strips by (`invisible_list`)."""
    folder = Path(folder) if folder else HERE

    def part(prefix: str, p: Path) -> bytes:
        return prefix.encode("utf-8") + p.name.encode("utf-8") + b"\0" + _code_tokens(
            p.read_bytes().replace(b"\r\n", b"\n"))

    parts = [part("", p) for p in sorted(folder.glob("*.py"))]
    parts += [part("_shared/", p) for p in imported_shared(folder, shared)]
    parts.append(b"invisible\0" + invisible_list())
    return _h(b"\0\0".join(parts))


def describe(rows, vocab_path=None, code_folder=None, shared_folder=None) -> dict:
    """The `terms` block of the `02.4-phrases` report."""
    rv = row_versions(rows)
    vv = vocab_version(vocab_path)
    return {"version": _h(_canon({"rows": rv, "vocab": vv})), "count": len(rv),
            "rows": rv, "vocab": vv, "code": code_version(code_folder, shared_folder)}

