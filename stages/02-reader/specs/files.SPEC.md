# files.py: spec

Lists the files of an input folder, reads their bytes, decides each file's
format, and decodes text. Stage 2 foundation; no check of its own.

## Inputs

- `input_dir`: a folder (pinned repo copy or fixture folder). Read-only.
- For `classify` and `decode`: one file's relative path and bytes.

## Outputs

`list_files(input_dir) -> list[Entry]`, sorted by `rel`:

- `rel`: path relative to the input, forward slashes.
- `kind`: `file` or `symlink`.
- `target`: the link target string for a symlink, else None.

Walked with `os.scandir`, never following a symlink or a Windows junction. A
root-level `.git` folder is not walked.

`classify(rel, data) -> str`, one of:

| Kind | When |
|---|---|
| `pdf` | `%PDF-` in the first 1024 bytes |
| `image` | PNG, JPEG, GIF, WebP, BMP, TIFF, or ICO signature |
| `docx` | ZIP whose member list has `word/document.xml` |
| `office-other` | ZIP with `xl/` or `ppt/` members (XLSX, PPTX), or an OLE2 compound file (old `.doc`/`.xls`/`.ppt`) |
| `archive` | any other ZIP, gzip, bzip2, xz, 7z, RAR, zstd |
| `markdown` | decodes as text; extension `md`, `markdown`, `mdx`, `mdc` |
| `html` | decodes as text; extension `html`, `htm`, `xhtml` |
| `svg` | decodes as text; extension `svg` |
| `text` | decodes as text, any other extension |
| `binary` | does not decode |

`decode(data) -> (text, encoding) | None`: a UTF-8/16/32 BOM picks the codec
and is removed; otherwise bytes with NUL are binary when NUL is more than 1% of the bytes or the rest is not strict UTF-8; a few NULs in valid UTF-8 are text (2026-10-09: a literal `\0` sentinel in source made a file binary, so one NUL could hide any file); otherwise strict UTF-8; otherwise
charset-normalizer's best guess; otherwise None.

`split_lines(text) -> list[str]`: split on `\n`, a trailing `\r` removed from
each line, and no extra empty line after a final `\n`. `len(split_lines(t))`
equals the line count an editor shows (an empty file has 0 lines).

## Must never

- Follow a symlink or junction, or read outside `input_dir`.
- Write anything.
- Run anything from the input.

## Done when (each backed by a test in `tests/test_files.py`)

1. A folder lists every file sorted with forward-slash paths; a root `.git` folder is skipped.
2. A symlink is listed as `symlink` with its target and not followed (skipped where the platform cannot create symlinks).
3. `classify` names pdf, image (PNG), docx, office-other (XLSX), archive (plain ZIP, gzip), markdown, html, svg, text, and binary correctly from small inline bytes.
4. `decode` handles UTF-8, UTF-8 with BOM (removed), UTF-16 with BOM; NUL bytes without a BOM are binary, except a few NULs in valid UTF-8, which are text.
5. `split_lines` keeps line numbers: `"a\r\nb\n"` gives `["a", "b"]`, `"a\n\nb"` gives `["a", "", "b"]`, `""` gives `[]`.
