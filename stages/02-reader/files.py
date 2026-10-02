"""List, classify, and decode the files of an input folder. Spec: specs/files.SPEC.md."""
from __future__ import annotations

import io
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path

MARKDOWN_EXTS = {"md", "markdown", "mdx", "mdc"}
HTML_EXTS = {"html", "htm", "xhtml"}

IMAGE_SIGS = [b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"BM",
              b"II*\x00", b"MM\x00*", b"\x00\x00\x01\x00"]
ARCHIVE_SIGS = [b"\x1f\x8b", b"BZh", b"\xfd7zXZ\x00", b"7z\xbc\xaf\x27\x1c", b"Rar!\x1a\x07",
                b"\x28\xb5\x2f\xfd"]
OLE2 = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"

BOMS = [(b"\xff\xfe\x00\x00", "utf-32-le"), (b"\x00\x00\xfe\xff", "utf-32-be"),
        (b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be")]


@dataclass
class Entry:
    rel: str
    kind: str  # "file" or "symlink"
    target: str | None = None


def _is_link(de: os.DirEntry) -> bool:
    if de.is_symlink():
        return True
    is_junction = getattr(de, "is_junction", None)
    return bool(is_junction and is_junction())


def _readlink(path: str) -> str:
    try:
        target = os.readlink(path)
    except OSError:
        return ""
    if target.startswith("\\\\?\\"):
        target = target[4:]
    return target


def list_files(input_dir: str | Path) -> list[Entry]:
    root = Path(input_dir).resolve()
    out: list[Entry] = []
    stack = [(root, "")]
    while stack:
        folder, prefix = stack.pop()
        with os.scandir(folder) as it:
            for de in it:
                rel = prefix + de.name
                if _is_link(de):
                    out.append(Entry(rel, "symlink", _readlink(de.path)))
                elif de.is_dir(follow_symlinks=False):
                    if prefix == "" and de.name == ".git":
                        continue
                    stack.append((Path(de.path), rel + "/"))
                elif de.is_file(follow_symlinks=False):
                    out.append(Entry(rel, "file"))
    out.sort(key=lambda e: e.rel)
    return out


def ext_of(rel: str) -> str:
    base = rel.rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[1].lower() if "." in base else ""


def _zip_kind(data: bytes) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError, NotImplementedError):
        return "archive"
    if "word/document.xml" in names:
        return "docx"
    if any(n.startswith(("xl/", "ppt/")) for n in names):
        return "office-other"
    return "archive"


def classify(rel: str, data: bytes) -> str:
    head = data[:1024]
    if b"%PDF-" in head:
        return "pdf"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image"
    if any(data.startswith(s) for s in IMAGE_SIGS):
        # BM and the ICO signature are short; confirm they are not text
        if data.startswith((b"BM", b"\x00\x00\x01\x00")) and decode(data) is not None:
            pass
        else:
            return "image"
    if data.startswith(b"PK\x03\x04") or data.startswith(b"PK\x05\x06"):
        return _zip_kind(data)
    if data.startswith(OLE2):
        return "office-other"
    if any(data.startswith(s) for s in ARCHIVE_SIGS):
        return "archive"
    if decode(data) is None:
        return "binary"
    ext = ext_of(rel)
    if ext in MARKDOWN_EXTS:
        return "markdown"
    if ext in HTML_EXTS:
        return "html"
    if ext == "svg":
        return "svg"
    return "text"


def decode(data: bytes) -> tuple[str, str] | None:
    for mark, codec in BOMS:
        if data.startswith(mark):
            try:
                return data[len(mark):].decode(codec), codec
            except UnicodeDecodeError:
                return None
    if b"\x00" in data:
        return None
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best is not None and best.encoding:
            return str(best), best.encoding
    except Exception:
        pass
    return None


def split_lines(text: str) -> list[str]:
    if text == "":
        return []
    parts = text.split("\n")
    if text.endswith("\n"):
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]
