"""The original lines of the files under review, as the AI stages show them. Spec: specs/shared.SPEC.md, linetext.

Moved here from the soft stage's packet.py (restructure step 5): Sweep cuts passages from these
lines and Pinpoint numbers a passage's lines for the second model, and both must read a file the
same way (the encoding `02.1-inventory` recorded, a BOM dropped, undecodable bytes replaced).
"""
from __future__ import annotations

import codecs
from pathlib import Path

BOMS = ((codecs.BOM_UTF32_LE, "utf-32-le"), (codecs.BOM_UTF32_BE, "utf-32-be"),
        (codecs.BOM_UTF8, "utf-8"), (codecs.BOM_UTF16_LE, "utf-16-le"),
        (codecs.BOM_UTF16_BE, "utf-16-be"))


def _decode(data: bytes, encoding: str | None) -> str:
    for mark, codec in BOMS:
        if data.startswith(mark):
            return data[len(mark):].decode(codec, "replace")
    enc = (encoding or "utf-8").lower()
    try:
        codecs.lookup(enc)
    except LookupError:
        enc = "utf-8"
    return data.decode(enc, "replace")


def _split(text: str) -> list[str]:
    if not text:
        return []
    parts = text.split("\n")
    if parts[-1] == "":
        parts.pop()
    return [p[:-1] if p.endswith("\r") else p for p in parts]


class Lines:
    """Original line text of files under input_dir, decoded with `02.1-inventory`'s encoding."""

    def __init__(self, input_dir, inventory: dict | None):
        self.root = Path(input_dir).resolve()
        self.enc = {f["file"]: f.get("encoding") for f in (inventory or {}).get("findings", [])
                    if f.get("check") == "inv.file" and f.get("file")}
        self.cache: dict[str, list[str] | None] = {}

    def lines(self, rel: str | None) -> list[str] | None:
        if not rel:
            return None
        if rel not in self.cache:
            p = (self.root / rel).resolve()
            try:
                p.relative_to(self.root)
                self.cache[rel] = _split(_decode(p.read_bytes(), self.enc.get(rel)))
            except (ValueError, OSError):
                self.cache[rel] = None
        return self.cache[rel]
