"""How a file's bytes become the lines a stage reads. Spec: specs/shared.SPEC.md, readtext.

Moved here from `02.4-phrases` (restructure step 4) because two sub-steps read the repository's text the
same way: `02.4-phrases` scans it and `02.6-builder` asks what it needs, triggers on, and costs.
They must find the same files and the same lines, so the rule is written once.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

BOMS = [(b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\xef\xbb\xbf", "utf-8"), (b"\xfe\xff", "utf-16-be"), (b"\xff\xfe", "utf-16-le")]

# Lists of path patterns read by git and tools; nothing in them is followed or executed, so phrase
# hits there are noise (2026-09-30, a .gitignore).
PATTERN_LISTS = {".gitignore", ".gitattributes", ".npmignore", ".dockerignore", ".prettierignore",
                 ".eslintignore", "codeowners", ".gitmodules", ".mailmap"}


def decode(data: bytes) -> str | None:
    for mark, codec in BOMS:
        if data.startswith(mark):
            try:
                return data[len(mark):].decode(codec)
            except UnicodeDecodeError:
                return None
    # A few NUL bytes in otherwise valid UTF-8 are text: a source file with a literal \0
    # sentinel was skipped whole, and one NUL could hide any file (2026-10-09)
    if b"\x00" in data:
        if data.count(b"\x00") * 100 > len(data):
            return None
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return None
        return text
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best is not None and best.encoding:
            return str(best)
    except Exception:
        pass
    return None


def split_lines(text: str) -> list[str]:
    if not text:
        return []
    parts = text.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]


class Read(NamedTuple):
    """What reading one `inv.file` row gave. `text` is None when the file is not read as text;
    `why` then says why, in the words `02.4-phrases` lists beside the file; `binary` is true when `02.1-inventory`
    found the file not to be text (a PDF, a DOCX, an image), the one case `02.4-phrases` may still read
    from `02.2-reader`'s extracted copy."""
    text: str | None
    size: int
    why: str | None
    binary: bool


def _opens_as_text(row: dict) -> bool:
    """Not a file `02.1-inventory` could not read, not a symlink, and not a file it found not to be text."""
    return not ("skipped" in row or row.get("type") == "inode/symlink" or "target" in row or not row.get("encoding"))


def text_candidate(row: dict) -> bool:
    """Whether `read_row` will try to read this `inv.file` row as text, from the row alone: not a file `02.1-inventory`
    could not read, not a symlink, not a file it found not to be text, and not a pattern list. A candidate can still fail to
    be read (it cannot be opened, or its bytes do not decode), which `read_row` says in its reason. The count of what a check
    that reads text is to look at (`coverlines`) is made from this, outside the loop that reads."""
    return _opens_as_text(row) and row["file"].rsplit("/", 1)[-1].lower() not in PATTERN_LISTS


def pattern_list(row: dict) -> bool:
    """Whether this `inv.file` row is a pattern list `read_row` turns down by name alone. The secret scan reads these (2026-11-01): a
    phrase in one is noise, and a token in a `.gitmodules` address is still a token."""
    return _opens_as_text(row) and row["file"].rsplit("/", 1)[-1].lower() in PATTERN_LISTS


def read_row(input_dir, row: dict) -> Read:
    """The text of one file, by the rules `02.4-phrases` has always used, in this order: a file `02.1-inventory`
    could not read, a symlink (never followed), a file `02.1-inventory` found not to be text, a pattern
    list, a file that cannot be opened, bytes `decode` cannot read."""
    rel = row["file"]
    if "skipped" in row:
        return Read(None, 0, f"unreadable: {row['skipped']}", False)
    if row.get("type") == "inode/symlink" or "target" in row:
        return Read(None, 0, "symlink (never followed)", False)
    if not row.get("encoding"):
        return Read(None, 0, f"not text ({row.get('type') or 'binary'})", True)
    if rel.rsplit("/", 1)[-1].lower() in PATTERN_LISTS:
        return Read(None, 0, "pattern list (not instruction text)", False)
    try:
        data = (Path(input_dir) / rel).read_bytes()
    except OSError as exc:
        return Read(None, 0, f"unreadable: {exc}", False)
    text = decode(data)
    if text is None:
        return Read(None, len(data), "undecodable text", False)
    return Read(text, len(data), None, False)
