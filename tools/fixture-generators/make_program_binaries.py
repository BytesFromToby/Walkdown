#!/usr/bin/env python3
"""WALKDOWN FIXTURE GENERATOR :: stage 1 programs in compiled form (2026-11-03, SkillSpector SC8 and SC9, S20).
Inert: each "program" is a file header padded with zero bytes; nothing in these files can run. Produces, in
02.1-inventory/class18-reader-limit/:
  tool.bin                                (ELF magic bytes, then zeros: an executable by its bytes)
  __pycache__/helper.cpython-312.pyc      (Python 3.12 bytecode header, then zeros: bytecode by its name)
  macros.docx                             (a zip document holding Office macros, an .exe, and an ELF member named .dat)
  plain.docx                              (a zip document with no program in it: the negative)
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
