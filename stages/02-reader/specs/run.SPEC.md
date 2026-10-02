# run.py: spec

The single entry point for stage 2. Wires `files`, `fold`, `script_runs`, and
the format readers together and prints one contract-1 report
(`stages/CONTRACT.md`).

## Inputs

```
python stages/02-reader/run.py <input_dir> [--out <dir>]
```

## Outputs

stdout: one JSON document, UTF-8:

```json
{"stage": "02-reader", "contract": 1, "findings": [...], "coverage": {...}}
```

Per file, in path order, by kind (`files.classify`):

| Kind | Reading A text | Findings |
|---|---|---|
| markdown, html, svg, text | decoded text, original lines | `read.fold` and `read.script` per line; `read.divergence` for invisible characters per line (`fold.invisible_finding`); plus markdown carriers (`read_md`), HTML (`read_html`), or SVG (`read_svg`) divergences |
| pdf | `read_pdf` lines | `read.fold` / `read.script` over its lines; divergences; `read.metadata` |
| docx | `read_docx` lines | same as pdf |
| image | none | `read.metadata`; OCR text as a `B-only` divergence, or a `read.divergence` skip plus `read.unread` |
| office-other, archive, binary | none | `read.unread` with the reason |
| symlink | none | `read.unread` (`symlink, not followed`, plus `target`) |

Every `read.divergence` carries `reading`, `text`, `carrier`, `method`
(`static-style` or `ocr`). Text formats use the original line number in `line`.
PDF and DOCX findings are not line-based: `line` is null and `text_line` gives
the line in the normalized text (`page` / `paragraph` too). A file that cannot
be read by its reader gives `read.unread` with the reason; an SVG that is not
well-formed still gets its text checks and a `read.divergence` skip.

Within a file, findings are ordered: `read.unread`, `read.divergence`,
`read.fold`, `read.script`, `read.metadata`, skips.

`coverage`: `files`, `files_read`, `bytes`, `bytes_read`, `unread` (list of
paths), `carriers` (count of divergences per carrier), `markdown_files`,
`markdown_comments`, `optional_tools` (present or absent), and
`not_examined` (what the missing tools left unchecked).

stderr: notes, including each missing optional tool and what it skips.

`--out <dir>` also writes `<dir>/normalized/text/<rel>.txt` (reading A) and
`<dir>/normalized/folded/<rel>.txt` (each line folded), one per file with
reading-A text, same line count in both. It refuses (exit 2) an out dir inside
the input.

Exit 0 whenever a report was produced. Exit 2 with a message on stderr for a
missing or non-folder argument or a bad `--out`.

## Must never

- Print anything but the report to stdout.
- Write inside the input folder.
- Run anything from the input, follow a symlink, or fetch a URL.
- Emit a skip for a check that did run (a missing lingua is a stderr note, not
  a `read.script` skip).

## Done when (each backed by a test in `tests/test_run.py`)

1. On a small mixed folder, stdout parses as a contract-1 report with stage `02-reader`, and the exit code is 0.
2. A markdown file with a zero-width line, a comment, and a Cyrillic line gives `read.fold`, `read.divergence` (invisible and comment), and `read.script` findings at the right lines.
3. An HTML file with a `display:none` div gives a `display:none` divergence with method `static-style`.
4. A PNG without OCR gives a `read.divergence` skip and a `read.unread` finding; an unknown binary gives `read.unread`.
5. `--out` writes text and folded files with equal line counts, and folded lines differ only where `read.fold` fired.
6. `--out` inside the input exits non-zero; the input folder is byte-identical after a run.
7. A missing folder exits non-zero without printing a report.
