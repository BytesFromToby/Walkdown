# licenses.py: spec

Finds the licenses a repository states. Stage 1, check `inv.license` (added
2026-10-17, from class demo feedback: "add the license info of the repo you are
investigating"). Matching a license file against fixed license wording is a
lookup, like magic bytes: it says which known license text a file carries, never
what the license allows. Walkdown gives no legal advice.

## Inputs

- A file's relative path and decoded text (license files, manifests,
  `pyproject.toml` / `Cargo.toml`).
- A parsed frontmatter block (markdown files).
- A parsed JSON / YAML document (`configs.load`).

## Outputs

`is_license_file(rel) -> bool`: the file name (any folder, case ignored) is
`LICENSE`, `LICENCE`, `COPYING`, `UNLICENSE`, or `COPYRIGHT`, alone or followed
by `.`, `-`, or `_` and more (`LICENSE.md`, `LICENSE-MIT`, `COPYING.LESSER`).
A name ending in a code or config extension (`license.py`, `license.json`) is not
a license file.

`identify(text) -> (id | None, how | None)`: the SPDX id of the license the text
carries, and how it was found, in this order:

1. `spdx-tag`: an `SPDX-License-Identifier:` line gives the id verbatim.
2. `text`: fixed wording, matched on the text lowercased with runs of white space
   folded to one space. Licenses whose own text names another (GPL-3.0 mentions
   the Affero license) are decided by their title in the first 1,000 characters.
   Known: AGPL-3.0, LGPL-3.0, LGPL-2.1, LGPL-2.0, GPL-3.0, GPL-2.0, MPL-2.0,
   Apache-2.0, BSL-1.0, Unlicense, CC0-1.0, the CC BY 4.0 family, MIT, ISC,
   0BSD, BSD-3-Clause, BSD-2-Clause.
3. `title`: no wording matched but the first 1,000 characters name a known
   license (`MIT License`).

Otherwise `(None, None)`.

`normalize_declared(value) -> id | None`: a declared license string that equals
a known id, ignoring case, an `-only` / `-or-later` / `+` suffix, and the
spellings `Apache 2.0` / `Apache License 2.0` / `Apache License, Version 2.0`,
gives that id (GPL-3.0-or-later gives GPL-3.0). Anything else gives None.

`file_finding(rel, text) -> finding`: `{"check": "inv.license", "file": rel,
"line": null, "source": "file", "field": null, "license": id, "how": how,
"stated": ...}`. `stated` is null when the license was identified, otherwise the
first non-empty line, trimmed to 200 characters, so the reader sees what the
file says.

`field_findings(rel, text, doc, fm) -> list[finding]`: declared license fields,
`source` `field`, `how` `field`, `stated` the value verbatim, `license` from
`normalize_declared`:

- a frontmatter `license` key (`line` = its line);
- the top-level `license` of `package.json`, `plugin.json` / `.yaml` / `.yml`,
  `marketplace.json`, `gemini-extension.json`, `composer.json`, `manifest.json`
  (a string, or an object's `type`);
- `pyproject.toml`: `project.license` (a string, or a table's `text`; a table's
  `file` is recorded as `file: <path>`) and `tool.poetry.license`;
- `Cargo.toml`: `package.license`.

`field` names the key (`license`, `project.license`, ...).

## Must never

- Read a file that is not a license file by name, or a README, for a license.
- Say what a license permits, or call one good or bad.
- Fail on a file it cannot parse: it gives no finding.

## Done when (each backed by a test in `tests/test_licenses.py`)

1. License file names are recognized in any folder and in any case; code and
   config files named `license` are not.
2. MIT, Apache-2.0, BSD-3-Clause, BSD-2-Clause, ISC, and the Unlicense are
   identified from their wording; an SPDX tag wins over wording.
3. GPL-3.0 text that mentions the Affero license is GPL-3.0; AGPL-3.0 and
   LGPL-2.1 are told apart by title.
4. An unrecognized license file gives `license` null and its first line in
   `stated`.
5. Declared fields: frontmatter (with its line), `package.json` string and
   object forms, `pyproject.toml` string and table forms, `Cargo.toml`; an
   unknown declared value keeps `stated` and gives `license` null.
6. `normalize_declared` maps the listed spellings and suffixes.
