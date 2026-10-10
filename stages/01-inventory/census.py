"""Per-file facts and structural flags. Spec: specs/census.SPEC.md."""
from __future__ import annotations

import codecs
from dataclasses import dataclass

READER_LINES = 2000
READER_BYTES = 50_000
LONG_LINE = 500

BOMS = [  # longest first: UTF-32 LE starts with the UTF-16 LE mark
    (codecs.BOM_UTF32_LE, "utf-32-le", "UTF-32 LE"),
    (codecs.BOM_UTF32_BE, "utf-32-be", "UTF-32 BE"),
    (codecs.BOM_UTF8, "utf-8", "UTF-8"),
    (codecs.BOM_UTF16_LE, "utf-16-le", "UTF-16 LE"),
    (codecs.BOM_UTF16_BE, "utf-16-be", "UTF-16 BE"),
]

ARCHIVES = {"application/zip", "application/gzip", "application/x-bzip2", "application/x-xz",
            "application/x-7z-compressed", "application/vnd.rar", "application/x-rar-compressed",
            "application/zstd", "application/x-tar", "application/x-gzip", "application/x-zstd",
            "application/x-lzip", "application/x-compress", "application/x-archive",
            "application/java-archive"}

ZIP_EXTS = {"zip", "jar", "war", "ear", "apk", "aab", "docx", "xlsx", "pptx", "docm", "xlsm",
            "pptm", "dotx", "odt", "ods", "odp", "epub", "whl", "nupkg", "vsix", "xpi", "crx",
            "ipa", "kmz", "3mf", "sketch", "mcpack", "skill", "plugin"}

# MIME -> extensions that name that format
EXT_FOR = {
    "image/png": {"png", "apng"},
    "image/jpeg": {"jpg", "jpeg", "jpe", "jfif"},
    "image/gif": {"gif"},
    "image/webp": {"webp"},
    "image/bmp": {"bmp", "dib"},
    "image/x-icon": {"ico", "cur"},
    "image/vnd.microsoft.icon": {"ico", "cur"},
    "image/tiff": {"tif", "tiff"},
    "application/pdf": {"pdf", "ai"},
    "application/zip": ZIP_EXTS,
    "application/java-archive": ZIP_EXTS,
    "application/gzip": {"gz", "tgz", "gzip"},
    "application/x-gzip": {"gz", "tgz", "gzip"},
    "application/x-bzip2": {"bz2", "tbz", "tbz2"},
    "application/x-xz": {"xz", "txz"},
    "application/x-7z-compressed": {"7z"},
    "application/vnd.rar": {"rar"},
    "application/x-rar-compressed": {"rar"},
    "application/zstd": {"zst", "zstd", "tzst"},
    "application/x-zstd": {"zst", "zstd", "tzst"},
    "application/x-tar": {"tar"},
    "application/x-executable": {"", "elf", "so", "o", "bin", "out"},
    "application/x-elf": {"", "elf", "so", "o", "bin", "out"},
    "application/x-sharedlib": {"", "so", "elf"},
    "application/x-msdownload": {"exe", "dll", "sys", "com", "scr", "ocx", "cpl", "efi", "pyd"},
    "application/vnd.microsoft.portable-executable": {"exe", "dll", "sys", "scr", "efi", "pyd"},
    "application/x-mach-binary": {"", "dylib", "bundle", "so", "o"},
    "application/wasm": {"wasm"},
    "application/vnd.sqlite3": {"sqlite", "sqlite3", "db", "db3"},
    "application/x-sqlite3": {"sqlite", "sqlite3", "db", "db3"},
    "application/java-vm": {"class"},
    "application/x-java-applet": {"class"},
}

SIGNATURES = [  # (offset, bytes, mime)
    (0, b"\x89PNG\r\n\x1a\n", "image/png"),
    (0, b"\xff\xd8\xff", "image/jpeg"),
    (0, b"GIF87a", "image/gif"),
    (0, b"GIF89a", "image/gif"),
    (0, b"BM", None),  # checked below, too short to trust alone
    (0, b"\x00\x00\x01\x00", "image/x-icon"),
    (0, b"II*\x00", "image/tiff"),
    (0, b"MM\x00*", "image/tiff"),
    (0, b"%PDF-", "application/pdf"),
    (0, b"PK\x03\x04", "application/zip"),
    (0, b"PK\x05\x06", "application/zip"),
    (0, b"PK\x07\x08", "application/zip"),
    (0, b"\x1f\x8b", "application/gzip"),
    (0, b"BZh", "application/x-bzip2"),
    (0, b"\xfd7zXZ\x00", "application/x-xz"),
    (0, b"7z\xbc\xaf\x27\x1c", "application/x-7z-compressed"),
    (0, b"Rar!\x1a\x07", "application/vnd.rar"),
    (0, b"\x28\xb5\x2f\xfd", "application/zstd"),
    (257, b"ustar", "application/x-tar"),
    (0, b"\x7fELF", "application/x-executable"),
    (0, b"MZ", "application/x-msdownload"),
    (0, b"\xfe\xed\xfa\xce", "application/x-mach-binary"),
    (0, b"\xfe\xed\xfa\xcf", "application/x-mach-binary"),
    (0, b"\xce\xfa\xed\xfe", "application/x-mach-binary"),
    (0, b"\xcf\xfa\xed\xfe", "application/x-mach-binary"),
    (0, b"\x00asm", "application/wasm"),
    (0, b"SQLite format 3\x00", "application/vnd.sqlite3"),
    (0, b"\xca\xfe\xba\xbe", "application/java-vm"),
]


def builtin_magic(data: bytes) -> str | None:
    for off, sig, mime in SIGNATURES:
        if data[off:off + len(sig)] != sig:
            continue
        if sig == b"BM":
            # BMP: file size field matches, reserved bytes zero
            if len(data) >= 14 and int.from_bytes(data[2:6], "little") == len(data) \
                    and data[6:10] == b"\x00\x00\x00\x00":
                return "image/bmp"
            continue
        if sig == b"MZ" and len(data) < 64:
            continue
        if sig == b"\x00\x00\x01\x00" and len(data) < 22:
            continue
        return mime
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def _make_backend():
    try:
        import magic  # type: ignore
        m = magic.Magic(mime=True)
        m.from_buffer(b"test")
        return "python-magic", lambda data: m.from_buffer(data[:65536])
    except Exception:
        pass
    try:
        import filetype  # type: ignore

        def ft(data):
            kind = filetype.guess(data[:65536])
            return kind.mime if kind else None
        return "filetype", ft
    except Exception:
        pass
    return "builtin", builtin_magic


_BACKEND_NAME, _BACKEND = _make_backend()


def magic_backend() -> str:
    return _BACKEND_NAME


def _non_text(mime: str | None) -> str | None:
    if not mime:
        return None
    mime = mime.split(";")[0].strip().lower()
    if mime.startswith("text/") or mime in ("application/octet-stream", "inode/x-empty",
                                            "application/x-empty", "image/svg+xml",
                                            "application/json", "application/xml",
                                            "application/javascript", "application/x-ndjson"):
        return None
    return mime


def detect_magic(data: bytes) -> str | None:
    """MIME of a non-text format the magic bytes identify, else None."""
    try:
        found = _non_text(_BACKEND(data))
    except Exception:
        found = None
    if found is None and _BACKEND_NAME != "builtin":
        found = _non_text(builtin_magic(data))
    return found


def ext_of(rel: str) -> str:
    base = rel.rsplit("/", 1)[-1]
    if "." not in base:
        return ""
    return base.rsplit(".", 1)[1].lower()


@dataclass
class Facts:
    ext: str
    bytes: int
    magic: str | None
    text: bool
    encoding: str | None
    bom: bool
    bom_kind: str | None
    lines: int | None
    type: str
    exec: bool
    text_value: str | None


def _decode(data: bytes):
    """-> (text, encoding, bom_kind) or None for binary."""
    for mark, codec, label in BOMS:
        if data.startswith(mark):
            try:
                return data[len(mark):].decode(codec), codec, label
            except UnicodeDecodeError:
                return None
    # A few NUL bytes in otherwise valid UTF-8 are text: a source file with a literal \0
    # sentinel was skipped whole, and one NUL could hide any file (2026-10-09, caveman)
    if b"\x00" in data:
        if data.count(b"\x00") * 100 > len(data):
            return None
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return None
        return text, "utf-8", None
    try:
        return data.decode("utf-8"), "utf-8", None
    except UnicodeDecodeError:
        pass
    try:
        from charset_normalizer import from_bytes  # type: ignore
        best = from_bytes(data).best()
        if best is not None and best.encoding:
            return str(best), best.encoding, None
    except Exception:
        pass
    return None


def count_lines(text: str) -> int:
    n = text.count("\n")
    if text and not text.endswith("\n"):
        n += 1
    return n


def file_facts(rel: str, data: bytes, exec_bit: bool | None) -> Facts:
    magic = detect_magic(data) if data else None
    decoded = None if magic else _decode(data)
    if decoded is None:
        return Facts(ext_of(rel), len(data), magic, False, None, False, None, None,
                     magic or "application/octet-stream", bool(exec_bit), None)
    text, enc, bom_kind = decoded
    return Facts(ext_of(rel), len(data), None, True, enc, bom_kind is not None, bom_kind,
                 count_lines(text), "text/plain", bool(exec_bit), text)


def symlink_facts(rel: str, target: str) -> Facts:
    return Facts(ext_of(rel), len(target.encode("utf-8")), None, False, None, False, None,
                 None, "inode/symlink", False, None)


def _flag(rel, flag, detail, line=None, **extra):
    f = {"check": "struct.census", "file": rel, "line": line, "flag": flag, "detail": detail}
    f.update(extra)
    return f


def census_flags(rel: str, f: Facts) -> list[dict]:
    out = []
    if f.text:
        over = []
        if f.lines is not None and f.lines > READER_LINES:
            over.append(f"{f.lines} lines exceeds the {READER_LINES}-line window")
        if f.bytes > READER_BYTES:
            over.append(f"{f.bytes} bytes exceeds the {READER_BYTES}-byte (50 KB) window")
        if over:
            out.append(_flag(rel, "reader-window", "; ".join(over)))
        for i, line in enumerate(f.text_value.split("\n"), start=1):
            line = line.rstrip("\r")
            if len(line) > LONG_LINE:
                out.append(_flag(rel, "long-line",
                                 f"line {i}: {len(line)} characters (limit {LONG_LINE})",
                                 line=i, length=len(line)))
    if f.magic and f.ext not in EXT_FOR.get(f.magic, set()):
        ext = f".{f.ext}" if f.ext else "(no extension)"
        out.append(_flag(rel, "ext-magic-mismatch",
                         f"extension {ext}; magic bytes identify {f.magic}",
                         detected=f.magic))
    if f.bom:
        out.append(_flag(rel, "bom", f"{f.bom_kind} byte-order mark at offset 0"))
    if f.magic in ARCHIVES:
        out.append(_flag(rel, "archive", f"magic bytes identify {f.magic}", detected=f.magic))
    return out


def symlink_flag(rel: str, target: str) -> dict:
    return _flag(rel, "symlink", target)
