#!/usr/bin/env python3
"""WALKDOWN FIXTURE GENERATOR :: stage 1 programs in compiled form (2026-11-03, SkillSpector SC8 and SC9, S20).
Inert: each "program" is a file header padded with zero bytes; nothing in these files can run. Produces, in
02.1-inventory/class18-reader-limit/:
  tool.bin                                (ELF magic bytes, then zeros: an executable by its bytes)
  __pycache__/helper.cpython-312.pyc      (Python 3.12 bytecode header, then zeros: bytecode by its name)
  macros.docx                             (a zip document holding Office macros, an .exe, and an ELF member named .dat)
  plain.docx                              (a zip document with no program in it: the negative)
  bundle.tar.gz                           (a gzip tar holding an ELF program and Python bytecode)
  plain.tar.gz                            (a gzip tar holding text only: the negative)
  bundle.tar.zst, plain.tar.zst           (the same two tars in zstd frames; 2026-11-04)
  bundle.7z                               (a 7z holding bytecode, an ELF program named .dat, and an .exe; 2026-11-04)
  plain.7z                                (a 7z holding text only: the negative)
  bundle.rar                              (a RAR 5 holding an ELF program and Python bytecode, stored; 2026-11-04)
  plain.rar                               (a RAR 5 holding text only: the negative)
The 7z, RAR, and zstd files are written here byte by byte with the standard library, as 7-Zip writes a 7z (an LZMA2 folder,
an LZMA2 and BCJ folder for programs, a header packed with LZMA) and as RAR 5 stores a file, so they are the same on every run;
7-Zip 23.01 (`7z t`) and rarfile 4.5 read them back whole.
Regenerate: python make_program_binaries.py"""
import os
import zipfile

HERE = os.path.dirname(__file__)
R18 = os.path.normpath(os.path.join(HERE, "..", "..", "Fixtures", "02.1-inventory", "class18-reader-limit"))
STAMP = (1980, 1, 1, 0, 0, 0)  # fixed member times, so the bytes (and the answer sheet's hashes) are the same each run


def member(z, name, data):
    z.writestr(zipfile.ZipInfo(name, date_time=STAMP), data)


with open(os.path.join(R18, "tool.bin"), "wb") as f:
    f.write(b"\x7fELF\x02\x01\x01" + b"\x00" * 121)

os.makedirs(os.path.join(R18, "__pycache__"), exist_ok=True)
with open(os.path.join(R18, "__pycache__", "helper.cpython-312.pyc"), "wb") as f:
    f.write(b"\xcb\x0d\x0d\x0a" + b"\x00" * 60)

with zipfile.ZipFile(os.path.join(R18, "macros.docx"), "w") as z:
    member(z, "[Content_Types].xml", "<Types/>")
    member(z, "word/document.xml", "<w:document>WALKDOWN FIXTURE :: a document with programs inside (POSITIVE)</w:document>")
    member(z, "word/vbaProject.bin", b"\x00" * 32)
    member(z, "word/embeddings/setup.exe", b"MZ" + b"\x00" * 126)
    member(z, "word/media/blob.dat", b"\x7fELF\x02\x01\x01" + b"\x00" * 57)

with zipfile.ZipFile(os.path.join(R18, "plain.docx"), "w") as z:
    member(z, "[Content_Types].xml", "<Types/>")
    member(z, "word/document.xml", "<w:document>WALKDOWN FIXTURE :: a document with no program in it (NEGATIVE)</w:document>")


# Tar archives (2026-11-03): a gzip-compressed tar holding a program and bytecode, and one holding only text (the negative).
# Fixed member times and a gzip header with mtime 0, so the bytes are the same each run.
import gzip  # noqa: E402
import io  # noqa: E402
import tarfile  # noqa: E402


def tar_bytes(members):
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w", format=tarfile.USTAR_FORMAT) as t:
        for name, data in members:
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(data), 0, 0o644
            t.addfile(info, io.BytesIO(data))
    return raw.getvalue()


def targz(path, members):
    with open(path, "wb") as out, gzip.GzipFile(fileobj=out, mode="wb", mtime=0, filename="") as gz:
        gz.write(tar_bytes(members))


TAR_BUNDLE = [
    ("bundle/README.md", b"WALKDOWN FIXTURE :: a tar holding programs (POSITIVE)\n"),
    ("bundle/bin/helper", b"\x7fELF\x02\x01\x01" + b"\x00" * 57),
    ("bundle/lib/__pycache__/util.cpython-312.pyc", b"\xcb\x0d\x0d\x0a" + b"\x00" * 28),
]
TAR_PLAIN = [
    ("docs/README.md", b"WALKDOWN FIXTURE :: a tar holding text only (NEGATIVE)\n"),
]
targz(os.path.join(R18, "bundle.tar.gz"), TAR_BUNDLE)
targz(os.path.join(R18, "plain.tar.gz"), TAR_PLAIN)


# 7z, RAR, and zstd (2026-11-04). Formats: 7-Zip's 7zFormat.txt, RAR 5's technote, RFC 8878 (zstd).
import lzma  # noqa: E402
import struct  # noqa: E402
import zlib  # noqa: E402


def zstd_raw(data):
    """A zstd frame of raw (unpacked) blocks: the frame's size in the header, blocks of at most 128 KB."""
    out = b"\x28\xb5\x2f\xfd" + bytes([0xA0]) + struct.pack("<I", len(data))  # one segment, a 4-byte size
    blocks = [data[i:i + 131072] for i in range(0, len(data), 131072)] or [b""]
    for k, block in enumerate(blocks):
        out += struct.pack("<I", (len(block) << 3) | (k == len(blocks) - 1))[:3] + block
    return out


def number7(v):
    for n in range(8):
        if v < 1 << (8 * n + 7 - n):
            return bytes([(0xFF << (8 - n)) & 0xFF | (v >> (8 * n))]) + (v & ((1 << 8 * n) - 1)).to_bytes(n, "little")
    return b"\xff" + v.to_bytes(8, "little")


def bits7(flags):
    out = bytearray((len(flags) + 7) // 8)
    for i, f in enumerate(flags):
        if f:
            out[i // 8] |= 0x80 >> (i % 8)
    return bytes(out)


LZMA2_1M = (b"\x21", b"\x10")  # LZMA2, a 1 MB dictionary
BCJ = (b"\x03\x03\x01\x03", b"")  # x86 branch filter
LZMA_64K = (b"\x03\x01\x01", b"\x5d\x00\x00\x01\x00")  # LZMA lc3 lp0 pb2, a 64 KB dictionary
FILTER = {LZMA2_1M: {"id": lzma.FILTER_LZMA2, "dict_size": 1 << 20}, BCJ: {"id": lzma.FILTER_X86},
          LZMA_64K: {"id": lzma.FILTER_LZMA1, "dict_size": 1 << 16, "lc": 3, "lp": 0, "pb": 2}}


def folder7(coders):
    """A folder as 7-Zip writes one: the packed stream's coder first, each later coder fed by the one before it."""
    out = number7(len(coders))
    for cid, props in coders:
        out += bytes([len(cid) | (0x20 if props else 0)]) + cid + (number7(len(props)) + props if props else b"")
    for i in range(len(coders) - 1):
        out += number7(i + 1) + number7(i)
    return out


def streams7(pack_pos, packs, folders, members=None):
    """StreamsInfo: `folders` is (coders, unpacked size) for each pack; `members`, each folder's member sizes and CRCs."""
    out = b"\x06" + number7(pack_pos) + number7(len(packs)) + b"\x09" + b"".join(number7(len(p)) for p in packs) + b"\x00"
    out += b"\x07\x0b" + number7(len(folders)) + b"\x00" + b"".join(folder7(c) for c, _ in folders)
    out += b"\x0c" + b"".join(number7(size) for c, size in folders for _ in c) + b"\x00"
    if members:
        out += b"\x08\x0d" + b"".join(number7(len(m)) for m in members)
        out += b"\x09" + b"".join(number7(len(d)) for m in members for d in m[:-1])
        out += b"\x0a\x01" + b"".join(struct.pack("<I", zlib.crc32(d)) for m in members for d in m) + b"\x00"
    return out + b"\x00"


def pack7(coders, data):
    return lzma.compress(data, format=lzma.FORMAT_RAW, filters=[FILTER[c] for c in reversed(coders)])


def sevenzip(path, entries):
    """`entries`: (name, data, folder number) for a member, (name, None, None) for a directory; folder 0 is LZMA2, folder 1
    LZMA2 and BCJ, as 7-Zip packs programs."""
    kinds = [[LZMA2_1M], [LZMA2_1M, BCJ]]
    groups = [[d for _, d, f in entries if f == k] for k in range(2)]
    used = [k for k in range(2) if groups[k]]
    packs = [pack7(kinds[k], b"".join(groups[k])) for k in used]
    names = b"\x00" + b"".join(n.encode("utf-16-le") + b"\x00\x00" for n, _, _ in entries)
    empty = [d is None for _, d, _ in entries]
    files = b"\x05" + number7(len(entries))
    if any(empty):
        files += b"\x0e" + number7(len(bits7(empty))) + bits7(empty)
    files += b"\x11" + number7(len(names)) + names + b"\x00"
    header = b"\x01\x04" + streams7(0, packs, [(kinds[k], sum(map(len, groups[k]))) for k in used],
                                    [groups[k] for k in used]) + files + b"\x00"
    packed_header = pack7([LZMA_64K], header)
    body = b"".join(packs) + packed_header
    head_pos = len(body) - len(packed_header)
    encoded = b"\x17" + streams7(head_pos, [packed_header], [([LZMA_64K], len(header))])
    tail = struct.pack("<QQI", len(body), len(encoded), zlib.crc32(encoded))
    with open(path, "wb") as f:
        f.write(b"7z\xbc\xaf\x27\x1c\x00\x04" + struct.pack("<I", zlib.crc32(tail)) + tail + body + encoded)


def vint(v):
    out = bytearray()
    while True:
        out.append((v & 0x7F) | (0x80 if v >> 7 else 0))
        v >>= 7
        if not v:
            return bytes(out)


def rar5_block(kind, fields, data=b""):
    head = vint(kind) + vint(0x02 if data else 0) + (vint(len(data)) if data else b"") + fields
    sized = vint(len(head)) + head
    return struct.pack("<I", zlib.crc32(sized)) + sized + data


def rar5(path, entries):
    """`entries`: (name, data) for a stored member, (name, None) for a directory; Unix, no times."""
    out = b"Rar!\x1a\x07\x01\x00" + rar5_block(1, vint(0))
    for name, data in entries:
        raw = name.encode("utf-8")
        if data is None:
            fields = vint(0x01) + vint(0) + vint(0o40755) + vint(0) + vint(1) + vint(len(raw)) + raw
            out += rar5_block(2, fields)
        else:
            fields = vint(0x04) + vint(len(data)) + vint(0o100644) + struct.pack("<I", zlib.crc32(data))
            out += rar5_block(2, fields + vint(0) + vint(1) + vint(len(raw)) + raw, data)
    with open(path, "wb") as f:
        f.write(out + rar5_block(5, vint(0)))


with open(os.path.join(R18, "bundle.tar.zst"), "wb") as f:
    f.write(zstd_raw(tar_bytes(TAR_BUNDLE)))
with open(os.path.join(R18, "plain.tar.zst"), "wb") as f:
    f.write(zstd_raw(tar_bytes(TAR_PLAIN)))
sevenzip(os.path.join(R18, "bundle.7z"), [
    ("bundle/docs", None, None),
    ("bundle/README.md", b"WALKDOWN FIXTURE :: a 7z holding programs (POSITIVE)\n", 0),
    ("bundle/lib/__pycache__/util.cpython-312.pyc", b"\xcb\x0d\x0d\x0a" + b"\x00" * 28, 0),
    ("bundle/media/blob.dat", b"\x7fELF\x02\x01\x01" + b"\x00" * 121, 1),
    ("bundle/setup.exe", b"MZ" + b"\x00" * 126, 1),
])
sevenzip(os.path.join(R18, "plain.7z"), [
    ("docs/README.md", b"WALKDOWN FIXTURE :: a 7z holding text only (NEGATIVE)\n", 0),
])
rar5(os.path.join(R18, "bundle.rar"), [
    ("bundle", None),
    ("bundle/README.md", b"WALKDOWN FIXTURE :: a RAR holding programs (POSITIVE)\n"),
    ("bundle/bin/helper", b"\x7fELF\x02\x01\x01" + b"\x00" * 57),
    ("bundle/lib/__pycache__/util.cpython-312.pyc", b"\xcb\x0d\x0d\x0a" + b"\x00" * 28),
])
rar5(os.path.join(R18, "plain.rar"), [
    ("docs/README.md", b"WALKDOWN FIXTURE :: a RAR holding text only (NEGATIVE)\n"),
])
