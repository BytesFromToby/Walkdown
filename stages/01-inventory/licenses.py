"""Stated licenses: license files and declared license fields. Spec: specs/licenses.SPEC.md."""
from __future__ import annotations

import re
import tomllib

_NAME = re.compile(r"^(licen[cs]e|copying|unlicense|copyright)([-._].*)?$", re.I)
CODE_EXTS = {"py", "js", "mjs", "cjs", "ts", "tsx", "jsx", "json", "yaml", "yml", "toml", "sh",
             "go", "rs", "java", "rb", "php", "html", "htm", "css", "c", "h", "cpp", "cs", "kt",
             "swift", "lua", "ps1", "bat", "cmd", "xml", "ini", "cfg", "lock"}
DECLARING = {"package.json", "plugin.json", "plugin.yaml", "plugin.yml", "marketplace.json",
             "gemini-extension.json", "composer.json", "manifest.json"}
HEAD = 1000
STATED_MAX = 200

# Titles first: these licenses name each other in their bodies (GPL-3.0 section 13 names the
# Affero license), so the title in the head decides. Each entry: (id, phrases that must all be
# in the head).
_BY_TITLE = [
    ("AGPL-3.0", ["gnu affero general public license version 3"]),
    ("LGPL-3.0", ["gnu lesser general public license version 3"]),
    ("LGPL-2.1", ["gnu lesser general public license version 2.1"]),
    ("LGPL-2.0", ["gnu library general public license"]),
    ("GPL-3.0", ["gnu general public license version 3"]),
    ("GPL-2.0", ["gnu general public license version 2"]),
]
# Wording anywhere in the text. Order matters where one license's wording contains another's.
_BY_TEXT = [
    ("MPL-2.0", ["mozilla public license", "2.0"]),
    ("Apache-2.0", ["apache license version 2.0"]),
    ("Apache-2.0", ["licensed under the apache license, version 2.0"]),
    ("BSL-1.0", ["boost software license"]),
    ("Unlicense", ["this is free and unencumbered software released into the public domain"]),
    ("CC0-1.0", ["cc0 1.0"]),
    ("CC-BY-NC-SA-4.0", ["attribution-noncommercial-sharealike 4.0"]),
    ("CC-BY-NC-ND-4.0", ["attribution-noncommercial-noderivatives 4.0"]),
    ("CC-BY-NC-4.0", ["attribution-noncommercial 4.0"]),
    ("CC-BY-ND-4.0", ["attribution-noderivatives 4.0"]),
    ("CC-BY-SA-4.0", ["attribution-sharealike 4.0"]),
    ("CC-BY-4.0", ["attribution 4.0 international"]),
    ("MIT", ["permission is hereby granted, free of charge, to any person obtaining a copy"]),
    ("ISC", ["permission to use, copy, modify, and/or distribute this software for any purpose "
             "with or without fee is hereby granted", "provided that the above copyright notice"]),
    ("0BSD", ["permission to use, copy, modify, and/or distribute this software for any purpose "
              "with or without fee is hereby granted"]),
    ("BSD-3-Clause", ["redistribution and use in source and binary forms", "neither the name"]),
    ("BSD-2-Clause", ["redistribution and use in source and binary forms"]),
]
_TITLE_ONLY = [("MIT", "mit license"), ("Apache-2.0", "apache license"), ("ISC", "isc license"),
               ("Unlicense", "the unlicense")]
KNOWN = sorted({i for i, _ in _BY_TITLE + _BY_TEXT})
_ALIASES = {"apache 2.0": "Apache-2.0", "apache license 2.0": "Apache-2.0",
            "apache license, version 2.0": "Apache-2.0", "apache2": "Apache-2.0"}
_SPDX = re.compile(r"SPDX-License-Identifier:\s*([A-Za-z0-9.+\-() ]+?)\s*(?:\*/|-->|$)", re.M)


def is_license_file(rel: str) -> bool:
    base = rel.rsplit("/", 1)[-1]
    if not _NAME.match(base):
        return False
    return not ("." in base and base.rsplit(".", 1)[-1].lower() in CODE_EXTS)


def _fold(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def identify(text: str) -> tuple[str | None, str | None]:
    m = _SPDX.search(text)
    if m:
        return m.group(1).strip(), "spdx-tag"
    t = _fold(text)
    head = _fold(text[:HEAD * 2])[:HEAD]
    for lic, phrases in _BY_TITLE:
        if all(p in head for p in phrases):
            return lic, "text"
    for lic, phrases in _BY_TEXT:
        if all(p in t for p in phrases):
            return lic, "text"
    for lic, title in _TITLE_ONLY:
        if title in head:
            return lic, "title"
    return None, None


def normalize_declared(value) -> str | None:
    if not isinstance(value, str):
        return None
    v = value.strip()
    low = v.lower()
    if low in _ALIASES:
        return _ALIASES[low]
    low = re.sub(r"(-only|-or-later|\+)$", "", low)
    for k in KNOWN:
        if k.lower() == low:
            return k
    return None


def _first_line(text: str) -> str | None:
    for ln in text.splitlines():
        s = ln.strip()
        if s:
            return s[:STATED_MAX]
    return None


def file_finding(rel: str, text: str) -> dict:
    lic, how = identify(text)
    return {"check": "inv.license", "file": rel, "line": None, "source": "file", "field": None,
            "license": lic, "how": how, "stated": None if lic else _first_line(text)}


def _field(rel, field, value, line=None) -> dict:
    stated = value if isinstance(value, str) else str(value)
    return {"check": "inv.license", "file": rel, "line": line, "source": "field", "field": field,
            "license": normalize_declared(value), "how": "field", "stated": stated}


def _toml_value(v):
    if isinstance(v, dict):
        if isinstance(v.get("text"), str):
            return v["text"]
        if isinstance(v.get("file"), str):
            return f"file: {v['file']}"
        return None
    return v if isinstance(v, str) else None


def field_findings(rel: str, text: str | None, doc=None, fm=None) -> list[dict]:
    out = []
    if fm is not None and isinstance(fm.yaml, dict) and fm.yaml.get("license") is not None:
        out.append(_field(rel, "license", fm.yaml["license"], fm.key_line("license")))
    base = rel.rsplit("/", 1)[-1].lower()
    if base in DECLARING and isinstance(doc, dict):
        v = doc.get("license")
        if isinstance(v, dict):
            v = v.get("type")
        if isinstance(v, str):
            out.append(_field(rel, "license", v))
    if base in ("pyproject.toml", "cargo.toml") and text is not None:
        try:
            t = tomllib.loads(text)
        except (tomllib.TOMLDecodeError, ValueError):
            return out
        paths = ([("project.license", ("project", "license")),
                  ("tool.poetry.license", ("tool", "poetry", "license"))]
                 if base == "pyproject.toml" else [("package.license", ("package", "license"))])
        for name, keys in paths:
            cur = t
            for k in keys:
                cur = cur.get(k) if isinstance(cur, dict) else None
            v = _toml_value(cur)
            if v is not None:
                out.append(_field(rel, name, v))
    return out
