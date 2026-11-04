"""The members of a 7z or RAR archive, read from the archive's own headers: each member's name, and its first bytes where Python
can get them without extracting anything. Spec: specs/inventory.SPEC.md, census (`archive-executable`).

7z (2026-11-04): the header is read, decoded first when it is compressed (LZMA, LZMA2, Deflate, BZip2). A member's first bytes
are read when its folder's coders are ones Python's `lzma`, `zlib`, or `bz2` decode, in a single line (no BCJ2, no AES), up to
`budget` bytes unpacked across the archive. RAR 4 and RAR 5: the file headers give the names; a stored member's first bytes lie
in the archive as they are. A compressed RAR member gives its name only, since RAR's own compression is not one Python decodes.
An archive whose headers are encrypted gives no members; a broken one gives what was read before the break."""
from __future__ import annotations

import bz2
import lzma
import struct
import zlib

SEVEN_Z = b"7z\xbc\xaf\x27\x1c"
RAR4 = b"Rar!\x1a\x07\x00"
RAR5 = b"Rar!\x1a\x07\x01\x00"
CHUNK = 1 << 20  # bytes unpacked at a time
HEADER_BYTES = 16 << 20  # a 7z header unpacks to no more than this (one listing 5,000 members is near 200 KB)


class _Bad(Exception):
    """The archive does not read as its format says."""


def members(data: bytes, budget: int, limit: int, head: int) -> list[tuple[str, bytes | None]]:
    """(name, first `head` bytes or None) for each of the first `limit` members that are not folders, in archive order."""
    if data.startswith(SEVEN_Z):
        return _sevenzip(data, budget, limit, head)
    if data.startswith(RAR5):
        return _rar5(data, limit, head)
    if data.startswith(RAR4):
        return _rar4(data, limit, head)
    return []


# --- 7z -------------------------------------------------------------------------------------------------------------------

class _Buf:
    def __init__(self, data: bytes):
        self.d, self.p = data, 0

    def byte(self) -> int:
        if self.p >= len(self.d):
            raise _Bad
        self.p += 1
        return self.d[self.p - 1]

    def take(self, n: int) -> bytes:
        if n < 0 or self.p + n > len(self.d):
            raise _Bad
        self.p += n
        return self.d[self.p - n:self.p]

    def num(self) -> int:
        """7z's NUMBER: the leading one bits of the first byte say how many bytes follow."""
        first, mask, value = self.byte(), 0x80, 0
        for i in range(8):
            if not first & mask:
                return value | ((first & (mask - 1)) << (8 * i))
            value |= self.byte() << (8 * i)
            mask >>= 1
        return value

    def count(self) -> int:
        """A NUMBER that counts things the header lists: never more than the header has bytes."""
        n = self.num()
        if n > len(self.d):
            raise _Bad
        return n

    def bits(self, n: int) -> list[bool]:
        out, b = [], 0
        for i in range(n):
            if i % 8 == 0:
                b = self.byte()
            out.append(bool(b & (0x80 >> (i % 8))))
        return out

    def defined(self, n: int) -> list[bool]:
        return [True] * n if self.byte() else self.bits(n)


def _folder(b: _Buf) -> dict:
    coders, ins, outs = [], 0, 0
    for _ in range(b.count()):
        flag = b.byte()
        if flag & 0x80:
            raise _Bad  # alternative methods: in the format's notes, never written
        cid = b.take(flag & 0x0F)
        n_in, n_out = (b.count(), b.count()) if flag & 0x10 else (1, 1)
        props = b.take(b.count()) if flag & 0x20 else b""
        coders.append((cid, props, n_in, n_out))
        ins, outs = ins + n_in, outs + n_out
    pairs = [(b.num(), b.num()) for _ in range(outs - 1)]
    packed = ins - len(pairs)
    if packed > 1:
        for _ in range(packed):
            b.num()
    return {"coders": coders, "pairs": pairs, "outs": outs, "packed": max(packed, 0)}


def _digests(b: _Buf, n: int) -> list[bool]:
    have = b.defined(n)
    for h in have:
        if h:
            b.take(4)
    return have


def _streams(b: _Buf) -> dict:
    """StreamsInfo: where the packed streams lie, the folders that unpack them, and the size of each member's stream."""
    s = {"pack_pos": 0, "pack_sizes": [], "folders": [], "streams": None, "sizes": None}
    crcs: list[bool] = []
    while (pid := b.byte()) != 0x00:
        if pid == 0x06:  # PackInfo
            s["pack_pos"], n = b.num(), b.count()
            while (q := b.byte()) != 0x00:
                if q == 0x09:
                    s["pack_sizes"] = [b.num() for _ in range(n)]
                elif q == 0x0A:
                    _digests(b, n)
                else:
                    raise _Bad
        elif pid == 0x07:  # UnPackInfo
            if b.byte() != 0x0B:
                raise _Bad
            n = b.count()
            if b.byte() != 0:
                raise _Bad  # folders kept elsewhere: not written by 7-Zip
            s["folders"] = [_folder(b) for _ in range(n)]
            if b.byte() != 0x0C:
                raise _Bad
            for f in s["folders"]:
                sizes = [b.num() for _ in range(f["outs"])]
                bound = {o for _, o in f["pairs"]}
                final = [i for i in range(f["outs"]) if i not in bound]
                if not final:
                    raise _Bad
                f["size"] = sizes[final[0]]
            crcs = [False] * n
            while (q := b.byte()) != 0x00:
                if q == 0x0A:
                    crcs = _digests(b, n)
                else:
                    raise _Bad
        elif pid == 0x08:  # SubStreamsInfo
            folders = s["folders"]
            streams = [1] * len(folders)
            q = b.byte()
            if q == 0x0D:
                streams = [b.count() for _ in folders]
                q = b.byte()
            sizes = []
            if q == 0x09:
                for f, n in zip(folders, streams):
                    if n:
                        part = [b.num() for _ in range(n - 1)]
                        sizes += part + [f["size"] - sum(part)]
                q = b.byte()
            else:
                for f, n in zip(folders, streams):
                    if n > 1:
                        raise _Bad
                    sizes += [f["size"]] * n
            while q != 0x00:
                if q == 0x0A:
                    _digests(b, sum(n for n, c in zip(streams, crcs) if not (n == 1 and c)))
                else:
                    raise _Bad
                q = b.byte()
            s["streams"], s["sizes"] = streams, sizes
        else:
            raise _Bad
    if s["streams"] is None:  # no SubStreamsInfo: one stream to a folder
        s["streams"] = [1] * len(s["folders"])
        s["sizes"] = [f["size"] for f in s["folders"]]
    return s


LZMA_FILTERS = {b"\x03\x03\x01\x03": lzma.FILTER_X86, b"\x03\x03\x02\x05": lzma.FILTER_POWERPC,
                b"\x03\x03\x04\x01": lzma.FILTER_IA64, b"\x03\x03\x05\x01": lzma.FILTER_ARM,
                b"\x03\x03\x07\x01": lzma.FILTER_ARMTHUMB, b"\x03\x03\x08\x05": lzma.FILTER_SPARC}


class _Copy:
    eof = False

    def __init__(self):
        self.rest = None

    def decompress(self, data: bytes, max_length: int) -> bytes:
        if self.rest is None:
            self.rest = memoryview(data)
        out, self.rest = bytes(self.rest[:max_length]), self.rest[max_length:]
        return out


class _Inflate:
    eof = False

    def __init__(self):
        self.z = zlib.decompressobj(-15)
        self.started = False

    def decompress(self, data: bytes, max_length: int) -> bytes:
        tail = data if not self.started else self.z.unconsumed_tail
        self.started = True
        out = self.z.decompress(tail, max_length)
        self.eof = self.z.eof
        return out


def _decoder(folder: dict, budget: int):
    """A decompressor for a folder whose coders form one line, each with one stream in and one out, or None."""
    coders = folder["coders"]
    if any(n_in != 1 or n_out != 1 for _, _, n_in, n_out in coders):
        return None
    # each coder has stream i in and stream i out; a bind pair feeds coder `o`'s output into coder `i`. From the coder whose
    # output is the folder's, follow the pairs back to the packed stream (7-Zip lists the coders in either order)
    feeds = dict(folder["pairs"])
    final = [c for c in range(len(coders)) if c not in set(feeds.values())]
    if len(final) != 1:
        return None
    order = final
    while order[-1] in feeds and len(order) <= len(coders):
        order = order + [feeds[order[-1]]]
    if sorted(order) != list(range(len(coders))):
        return None
    coders = [coders[c] for c in order]  # the output's coder first, the packed stream's last: `lzma`'s filter order
    ids = [cid for cid, _, _, _ in coders if cid != b"\x00"]  # Copy changes nothing
    if not ids:
        return _Copy()
    if ids == [b"\x04\x01\x08"]:
        return _Inflate()
    if ids == [b"\x04\x02\x02"]:
        return bz2.BZ2Decompressor()
    chain = []
    for cid, props, _, _ in coders:
        # what is unpacked never reaches further back than the budget, so the dictionary need not be larger: a header asking
        # for gigabytes is given no more
        if cid == b"\x00":
            continue
        if cid == b"\x21" and len(props) == 1:  # LZMA2
            p = props[0]
            if p > 40:
                return None
            size = 0xFFFFFFFF if p == 40 else (2 | (p & 1)) << (p // 2 + 11)
            chain.append({"id": lzma.FILTER_LZMA2, "dict_size": max(4096, min(size, budget))})
        elif cid == b"\x03\x01\x01" and len(props) == 5:  # LZMA
            d = props[0]
            if d >= 9 * 5 * 5:
                return None
            size = struct.unpack("<I", props[1:5])[0]
            chain.append({"id": lzma.FILTER_LZMA1, "lc": d % 9, "lp": d // 9 % 5, "pb": d // 45,
                          "dict_size": max(4096, min(size, budget))})
        elif cid in LZMA_FILTERS:
            chain.append({"id": LZMA_FILTERS[cid]})
        elif cid == b"\x03" and len(props) == 1:  # Delta
            chain.append({"id": lzma.FILTER_DELTA, "dist": props[0] + 1})
        else:
            return None  # AES, BCJ2, PPMd, ARM64, and the rest: names only
    if chain[-1]["id"] not in (lzma.FILTER_LZMA1, lzma.FILTER_LZMA2):
        return None
    return lzma.LZMADecompressor(format=lzma.FORMAT_RAW, filters=chain)


class _Unpacked:
    """A folder's unpacked bytes, read forward a chunk at a time and never held whole."""

    def __init__(self, dec, packed: bytes):
        self.dec, self.packed, self.buf, self.pos = dec, packed, b"", 0

    def _pull(self, n: int) -> bytes:
        if getattr(self.dec, "eof", False):
            return b""
        data, self.packed = self.packed, b""
        return self.dec.decompress(data, max_length=n)

    def at(self, offset: int, n: int) -> bytes:
        """The `n` bytes at `offset` (fewer at the end); offsets rise from one call to the next."""
        while True:
            drop = min(len(self.buf), max(0, offset - self.pos))
            self.buf, self.pos = self.buf[drop:], self.pos + drop
            if self.pos + len(self.buf) >= offset + n:
                break
            chunk = self._pull(min(CHUNK, offset + n - self.pos - len(self.buf)))
            if not chunk:
                break
            self.buf += chunk
        start = offset - self.pos
        return self.buf[start:start + n] if start >= 0 else b""


def _packed_of(data: bytes, s: dict) -> list[bytes | None]:
    """Each folder's packed bytes (its one packed stream), or None for a folder with several."""
    out, at, k = [], 32 + s["pack_pos"], 0
    sizes = s["pack_sizes"]
    for f in s["folders"]:
        if f["packed"] == 1 and k < len(sizes):
            out.append(data[at:at + sizes[k]])
        else:
            out.append(None)
        at += sum(sizes[k:k + f["packed"]])
        k += f["packed"]
    return out


def _files(b: _Buf) -> list[tuple[str, bool, bool]]:
    """FilesInfo: (name, has a stream, is a folder) for each member."""
    n = b.count()
    names, empty, empty_file = [""] * n, [False] * n, None
    while (kind := b.num()) != 0x00:
        body = _Buf(b.take(b.count()))
        if kind == 0x0E:
            empty = body.bits(n)
        elif kind == 0x0F:
            empty_file = body.bits(sum(empty))
        elif kind == 0x11:
            if body.byte() != 0:
                raise _Bad
            got = bytes(body.d[body.p:]).decode("utf-16-le", "replace").split("\x00")
            names = (got + [""] * n)[:n]
    out, k = [], 0
    for name, e in zip(names, empty):
        folder = False
        if e:
            folder = not (empty_file[k] if empty_file and k < len(empty_file) else False)
            k += 1
        out.append((name.replace("\\", "/"), not e, folder))
    return out


def _sevenzip(data: bytes, budget: int, limit: int, head: int) -> list[tuple[str, bytes | None]]:
    try:
        if len(data) < 32:
            return []
        off, size = struct.unpack_from("<QQ", data, 12)
        if size == 0:
            return []
        hdr = data[32 + off:32 + off + size]
        if len(hdr) != size:
            return []
        for _ in range(4):  # a header packed with the header's own streams: unpacked (once, as 7-Zip writes it)
            b = _Buf(hdr)
            pid = b.byte()
            if pid == 0x01:
                break
            if pid != 0x17:
                return []
            s = _streams(b)
            dec, packed = (_decoder(s["folders"][0], HEADER_BYTES), _packed_of(data, s)[0]) if s["folders"] else (None, None)
            want = s["folders"][0]["size"] if s["folders"] else 0
            if dec is None or packed is None or want > HEADER_BYTES:
                return []  # encrypted, or a coder Python does not have: no names
            hdr = _Unpacked(dec, packed).at(0, want)
            if len(hdr) != want:
                return []
        else:
            return []
        main, files = None, []
        while (pid := b.byte()) != 0x00:
            if pid == 0x02:  # ArchiveProperties
                while b.byte() != 0x00:
                    b.take(b.count())
            elif pid == 0x03:
                _streams(b)
            elif pid == 0x04:
                main = _streams(b)
            elif pid == 0x05:
                files = _files(b)
            else:
                raise _Bad
    except Exception:  # broken past where a name could be had: no names
        return []
    # the members with a stream take the streams in order, folder by folder
    where: list[tuple[int, int, int] | None] = []
    if main:
        sizes, k = main["sizes"], 0
        for fi, n in enumerate(main["streams"]):
            offset = 0
            for _ in range(n):
                if k < len(sizes):
                    where.append((fi, offset, sizes[k]))
                    offset += sizes[k]
                k += 1
    picked, by_folder, w = [], {}, 0  # by_folder: folder -> [(member, (folder, offset, size))], in member order
    for name, has_stream, folder in files:
        ref = None
        if has_stream:
            ref = where[w] if w < len(where) else None
            w += 1
        if not folder:
            if ref:
                by_folder.setdefault(ref[0], []).append((len(picked), ref))
            picked.append(name)
        if len(picked) >= limit:
            break
    heads: dict[int, bytes] = {}
    if main:
        packed = _packed_of(data, main)
        spent = 0
        for fi in sorted(by_folder):
            refs, folder = by_folder[fi], main["folders"][fi]
            if spent >= budget:
                break
            try:
                dec = _decoder(folder, budget) if packed[fi] is not None else None
                if dec is None:
                    continue
                u = _Unpacked(dec, packed[fi])
                for i, (_, offset, size) in refs:
                    if offset + min(head, size) > budget - spent:
                        break
                    got = u.at(offset, min(head, size))
                    if len(got) == min(head, size):  # fewer: the decoder held the last bytes back (BCJ with no end mark)
                        heads[i] = got
                spent += u.pos + len(u.buf)
            except Exception:
                continue  # what was read stands; the rest of this folder gives names only
    return [(name, heads.get(i)) for i, name in enumerate(picked)]


# --- RAR ------------------------------------------------------------------------------------------------------------------

def _rar4(data: bytes, limit: int, head: int) -> list[tuple[str, bytes | None]]:
    out, pos = [], len(RAR4)
    try:
        while pos + 7 <= len(data) and len(out) < limit:
            _, kind, flags, size = struct.unpack_from("<HBHH", data, pos)
            if size < 7:
                break
            add = struct.unpack_from("<I", data, pos + 7)[0] if flags & 0x8000 or kind in (0x74, 0x7A) else 0
            if kind == 0x73 and flags & 0x0080:
                break  # the headers are encrypted: no names
            if kind == 0x74:  # a file
                packed, _, _, _, _, _, method, name_len, _ = struct.unpack_from("<IIBIIBBHI", data, pos + 7)
                q = pos + 32
                if flags & 0x0100:  # sizes past 4 GB
                    add += struct.unpack_from("<I", data, q)[0] << 32
                    q += 8
                name = _rar4_name(data[q:q + name_len], bool(flags & 0x0200)).replace("\\", "/")
                if (flags & 0x00E0) != 0x00E0:  # not a folder
                    # stored, not encrypted, and not the rest of a member split across volumes
                    stored = method == 0x30 and not flags & 0x0004 and not flags & 0x0001
                    out.append((name, data[pos + size:pos + size + min(head, packed)] if stored else None))
            if kind == 0x7B:
                break
            pos += size + add
    except Exception:  # broken here: what was read stands
        pass
    return out


def _vint(data: bytes, p: int) -> tuple[int, int]:
    value = 0
    for i in range(10):
        if p >= len(data):
            raise _Bad
        b = data[p]
        p += 1
        value |= (b & 0x7F) << (7 * i)
        if not b & 0x80:
            return value, p
    raise _Bad


def _rar5(data: bytes, limit: int, head: int) -> list[tuple[str, bytes | None]]:
    out, pos = [], len(RAR5)
    try:
        while pos + 4 < len(data) and len(out) < limit:
            size, p = _vint(data, pos + 4)
            end = p + size
            if size == 0 or end > len(data):
                break
            kind, p = _vint(data, p)
            flags, p = _vint(data, p)
            extra = data_size = 0
            if flags & 0x01:
                extra, p = _vint(data, p)
            if flags & 0x02:
                data_size, p = _vint(data, p)
            if kind == 4:
                break  # archive encryption: the headers that follow are encrypted
            if kind == 2:  # a file
                file_flags, p = _vint(data, p)
                _, p = _vint(data, p)  # unpacked size
                _, p = _vint(data, p)  # attributes
                p += (4 if file_flags & 0x02 else 0) + (4 if file_flags & 0x04 else 0)
                compression, p = _vint(data, p)
                _, p = _vint(data, p)  # host OS
                name_len, p = _vint(data, p)
                name = data[p:p + name_len].decode("utf-8", "replace")
                if not file_flags & 0x01:  # not a folder
                    # stored, not encrypted, not a link or a copy of another member, and not the rest of a split member
                    stored = ((compression >> 7) & 0x07 == 0 and not flags & 0x08
                              and not _rar5_records(data[end - extra:end] if extra else b"") & {1, 5})
                    out.append((name, data[end:end + min(head, data_size)] if stored else None))
            if kind == 5:
                break
            pos = end + data_size
    except Exception:  # broken here: what was read stands
        pass
    return out


def _rar5_records(extra: bytes) -> set[int]:
    """The kinds of record in a file header's extra area: 1 is encryption, 5 a link or a copy of another member."""
    kinds, p = set(), 0
    try:
        while p < len(extra):
            size, q = _vint(extra, p)
            kinds.add(_vint(extra, q)[0])
            if size == 0:
                break
            p = q + size
    except _Bad:
        pass
    return kinds


def _rar4_name(raw: bytes, unicode: bool) -> str:
    """A RAR 4 file name: UTF-8, or RAR 3's packed Unicode after a plain name (the format's own scheme: two bits a
    character say whether its UTF-16 code unit is one byte, one byte under a shared high byte, two bytes, or a run taken from
    the plain name), or a plain name in the system's code page, read as Latin-1 when it is not UTF-8."""
    if unicode and b"\x00" in raw:
        plain, enc = raw.split(b"\x00", 1)
        try:
            high, i, units, flags, bits = enc[0], 1, [], 0, 0
            while i < len(enc):
                if bits == 0:
                    flags, i, bits = enc[i], i + 1, 8
                bits -= 2
                kind = (flags >> bits) & 3
                if kind == 0:
                    units.append(enc[i])
                    i += 1
                elif kind == 1:
                    units.append(enc[i] | high << 8)
                    i += 1
                elif kind == 2:
                    units.append(enc[i] | enc[i + 1] << 8)
                    i += 2
                else:
                    n = enc[i]
                    i += 1
                    if n & 0x80:
                        add, i = enc[i], i + 1
                        for _ in range((n & 0x7F) + 2):
                            units.append(((plain[len(units)] if len(units) < len(plain) else 0) + add) & 0xFF | high << 8)
                    else:
                        for _ in range(n + 2):
                            units.append(plain[len(units)] if len(units) < len(plain) else 0)
            return b"".join(u.to_bytes(2, "little") for u in units).decode("utf-16-le", "replace")
        except IndexError:
            return plain.decode("latin-1")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")
