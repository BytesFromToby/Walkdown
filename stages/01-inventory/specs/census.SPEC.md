# census.py: spec

Per-file facts and structural flags. Stage 1, checks `inv.file` (all fields but
`entry_point`) and `struct.census`. Measures bytes; never reads for meaning.

## Inputs

- The bytes of one file, its relative path, and its exec bit (from `walk.py`).
- For a symlink: its relative path and target only (the link is not followed).

## Outputs

`file_facts(rel, data, exec_bit) -> Facts` with:

| Field | Rule |
|---|---|
| `ext` | lowercase text after the last `.` of the basename, no dot. A dotfile's name counts (`.gitignore` gives `gitignore`). No dot gives `""`. |
| `bytes` | `len(data)` |
| `magic` | MIME type the magic bytes identify as a **non-text** format, or None |
| `text` | True when `magic` is None and the bytes decode (rule below) |
| `encoding` | codec name for text (`utf-8`, `utf-16-le`, `utf-16-be`, `utf-32-le`, `utf-32-be`, or the charset-normalizer guess), None for binary |
| `bom` | True when a text file starts with a UTF-8, UTF-16, or UTF-32 byte-order mark |
| `lines` | text only: count of `\n` plus 1 if the text is non-empty and does not end in `\n`. None for binary |
| `type` | `magic` if set, else `text/plain` for text, else `application/octet-stream` |
| `exec` | the exec bit as given (False when unknown) |
| `text_value` | the decoded text (BOM removed), for other stage 1 parsers |

**Decoding:** a BOM picks the codec. Otherwise bytes with NUL are binary when NUL is more than 1% of the bytes or the rest is not strict UTF-8; a few NULs in valid UTF-8 are text (2026-10-09: a literal `\0` sentinel in source made a file binary, so one NUL could hide any file);
bytes that decode as UTF-8 are `utf-8`; else charset-normalizer's best guess, if
installed and it finds one; else binary.

**Magic detection** (`detect_magic(data)`): python-magic if importable, else the
`filetype` package if importable, else a built-in signature table (PNG, JPEG,
GIF, WebP, BMP, ICO, TIFF, PDF, ZIP, gzip, bzip2, xz, 7z, RAR, zstd, tar,
ELF, PE, Mach-O, WebAssembly, SQLite, Java class). `magic_backend()` names the
backend in use. Any backend result that is `text/*` or absent counts as None:
text-versus-text is detector noise and never a finding.

`census_flags(rel, facts) -> list[finding]`, each a `struct.census` finding:

| Flag | When | `line` | `detail` |
|---|---|---|---|
| `reader-window` | text file with more than 2000 lines or more than 50,000 bytes; one finding per file | null | each exceeded threshold with the measured value |
| `long-line` | each text line longer than 500 characters (decoded, line ending excluded) | the line | line number and length; `length` field too |
| `ext-magic-mismatch` | `magic` is set and the extension is not one that names that format (table in code: `png` for `image/png`, `zip`/`docx`/`jar`/... for `application/zip`, and so on) | null | extension and detected type |
| `bom` | `bom` is True | null | which BOM |
| `archive` | `magic` is an archive type (zip, gzip, bzip2, xz, 7z, RAR, zstd, tar) | null | detected type |

`symlink_facts(rel, target)` returns the `inv.file` facts for a symlink
(`type` `inode/symlink`, `bytes` = UTF-8 length of the target, no encoding, no
lines, `exec` False) and `symlink_flag(rel, target)` the `symlink` census
finding with the target as `detail`.

## Must never

- Judge. A flag is a location and a measurement, never a verdict.
- Flag a text-versus-text disagreement (markdown opening with a code fence).
- Fail when python-magic, filetype, or charset-normalizer is missing.

## Done when (each backed by a test in `tests/test_census.py`)

1. Extension rule: `a.MD` gives `md`, `.gitignore` gives `gitignore`, `LICENSE` gives `""`, `x.tar.gz` gives `gz`.
2. UTF-8, UTF-8 with BOM, and UTF-16 with BOM decode, report encoding and BOM; NUL bytes without BOM are binary, except a few NULs in valid UTF-8, which are text.
3. Line count follows the rule, including a missing final newline and an empty file.
4. PNG bytes in a `.md` give `ext-magic-mismatch`; the same bytes in a `.png` do not.
5. A markdown file opening with a code fence gives no `ext-magic-mismatch` and type `text/plain`.
6. ZIP bytes give `archive`; in a `.zip` no mismatch, in a `.md` both flags.
7. A 2001-line file and a 50,001-byte file each give one `reader-window`; 2000 lines and 50,000 bytes give none.
8. A 501-character line gives `long-line` at its line number; 500 does not.
9. A BOM file gives the `bom` flag.
10. A symlink gives `inode/symlink` facts and a `symlink` flag with its target.
11. The built-in signature table recognizes PNG, ZIP, gzip, PDF, and tar.
