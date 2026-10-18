"""Tests for licenses.py, written from specs/licenses.SPEC.md."""
import json

import frontmatter
import licenses

MIT = ("MIT License\n\nCopyright (c) 2026 A\n\nPermission is hereby granted, free of charge, to any\n"
       "person obtaining a copy of this software.\n")
APACHE = "\n      Apache License\n      Version 2.0, January 2004\n   TERMS AND CONDITIONS\n"
BSD3 = ("Copyright (c) 2026 A\nRedistribution and use in source and binary forms, with or without\n"
        "modification, are permitted.\n3. Neither the name of the copyright holder nor ...\n")
BSD2 = "Copyright (c) 2026 A\nRedistribution and use in source and binary forms, with or without\n"
ISC = ("ISC License\nPermission to use, copy, modify, and/or distribute this software for any\n"
       "purpose with or without fee is hereby granted, provided that the above copyright notice\n")
UNLICENSE = "This is free and unencumbered software released into the public domain.\n"
GPL3 = ("    GNU GENERAL PUBLIC LICENSE\n       Version 3, 29 June 2007\n\n"
        "13. Use with the GNU Affero General Public License.\n")
AGPL3 = "    GNU AFFERO GENERAL PUBLIC LICENSE\n       Version 3, 19 November 2007\n"
LGPL21 = ("   GNU LESSER GENERAL PUBLIC LICENSE\n     Version 2.1, February 1999\n"
          "GNU General Public License\n")


# Done when 1
def test_license_file_names():
    for rel in ["LICENSE", "LICENCE", "license.md", "LICENSE.txt", "LICENSE-MIT", "COPYING",
                "COPYING.LESSER", "UNLICENSE", "skills/x/LICENSE.txt", "vendor/LICENSE-GPL"]:
        assert licenses.is_license_file(rel), rel
    for rel in ["src/license.py", "license.json", "docs/licensing.md", "README.md",
                "LICENSES-notes", "my-LICENSE"]:
        assert not licenses.is_license_file(rel), rel


# Done when 2
def test_identify_by_wording():
    assert licenses.identify(MIT) == ("MIT", "text")
    assert licenses.identify(APACHE) == ("Apache-2.0", "text")
    assert licenses.identify(BSD3) == ("BSD-3-Clause", "text")
    assert licenses.identify(BSD2) == ("BSD-2-Clause", "text")
    assert licenses.identify(ISC) == ("ISC", "text")
    assert licenses.identify(UNLICENSE) == ("Unlicense", "text")
    assert licenses.identify("MIT License\n\nSee the website.\n") == ("MIT", "title")


def test_spdx_tag_wins():
    text = "SPDX-License-Identifier: GPL-2.0-or-later\n" + MIT
    assert licenses.identify(text) == ("GPL-2.0-or-later", "spdx-tag")


# Done when 3
def test_gpl_family_by_title():
    assert licenses.identify(GPL3)[0] == "GPL-3.0"
    assert licenses.identify(AGPL3)[0] == "AGPL-3.0"
    assert licenses.identify(LGPL21)[0] == "LGPL-2.1"


# Done when 4
def test_unrecognized_file_keeps_first_line():
    f = licenses.file_finding("LICENSE.md", "\n\nCopyright 2026 X. All rights reserved.\nNo copying.\n")
    assert f["check"] == "inv.license" and f["source"] == "file" and f["line"] is None
    assert f["license"] is None and f["how"] is None
    assert f["stated"] == "Copyright 2026 X. All rights reserved."
    g = licenses.file_finding("LICENSE", MIT)
    assert g["license"] == "MIT" and g["stated"] is None


# Done when 5
def test_frontmatter_field_with_line():
    fm = frontmatter.parse("---\nname: x\nlicense: Complete terms in LICENSE.txt\n---\nbody\n")
    rows = licenses.field_findings("skills/x/SKILL.md", None, None, fm)
    assert len(rows) == 1
    r = rows[0]
    assert r["field"] == "license" and r["line"] == 3 and r["source"] == "field"
    assert r["license"] is None and r["stated"] == "Complete terms in LICENSE.txt"


def test_package_json_forms():
    s = licenses.field_findings("package.json", None, json.loads('{"license": "MIT"}'))
    assert [(r["license"], r["stated"]) for r in s] == [("MIT", "MIT")]
    o = licenses.field_findings("package.json", None, {"license": {"type": "ISC", "url": "u"}})
    assert o[0]["license"] == "ISC"
    assert licenses.field_findings("data/other.json", None, {"license": "MIT"}) == []


def test_toml_forms():
    t = '[project]\nname = "a"\nlicense = {text = "MIT"}\n'
    assert [(r["field"], r["license"]) for r in licenses.field_findings("pyproject.toml", t)] == [
        ("project.license", "MIT")]
    f = '[project]\nlicense = {file = "LICENSE"}\n'
    assert licenses.field_findings("pyproject.toml", f)[0]["stated"] == "file: LICENSE"
    p = '[tool.poetry]\nlicense = "Apache-2.0"\n'
    assert licenses.field_findings("pyproject.toml", p)[0]["field"] == "tool.poetry.license"
    c = '[package]\nname = "a"\nlicense = "MIT OR Apache-2.0"\n'
    r = licenses.field_findings("crate/Cargo.toml", c)[0]
    assert r["field"] == "package.license" and r["license"] is None and r["stated"] == "MIT OR Apache-2.0"
    assert licenses.field_findings("pyproject.toml", "not = [toml") == []


# Done when 6
def test_normalize_declared():
    assert licenses.normalize_declared("mit") == "MIT"
    assert licenses.normalize_declared("Apache 2.0") == "Apache-2.0"
    assert licenses.normalize_declared("Apache License, Version 2.0") == "Apache-2.0"
    assert licenses.normalize_declared("GPL-3.0-or-later") == "GPL-3.0"
    assert licenses.normalize_declared("GPL-2.0+") == "GPL-2.0"
    assert licenses.normalize_declared("Proprietary") is None
    assert licenses.normalize_declared(None) is None
