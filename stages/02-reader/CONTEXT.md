# Stage 2: Reader

**Question:** what does the model actually receive?
**Kind of evidence:** two independent readings of every file; where they
disagree is recorded as a fact.
**Report heading:** What the model actually reads.

Every later stage is only as good as this one: if the reader misses hidden text,
stage 4 reports a clean file with total confidence (METHOD, "Note on the
reader"). This is the highest-value stage.

Sources for every rule below: `pre-planning/METHOD.md` (Stage 2),
`pre-planning/THREATS.md` (classes 4, 6, 11), `pre-planning/REPORTING.md`
(Section 2), `pre-planning/TOOLING.md` (Stage 2 and "Usable by everyone"),
`stages/CONTRACT.md`. Nothing here comes from the answer sheet; a builder of this
stage never opens `Fixtures/ANSWERS/`.

---

## Inputs

- `<input_dir>`: a pinned repo copy or a fixture folder. Read-only.
- Stage 2 does not need stage 1's output in v1; it walks the input itself with
  the same rules (never follow symlinks out of the tree).

## Outputs

- `run.py <input_dir>` prints one contract-1 report to stdout.
- `run.py <input_dir> --out <dir>` also writes the normalized text (METHOD):
  - `<dir>/normalized/text/<path>.txt`: the true text of each readable file
    (reading A), one file per source file, mirroring the tree. For text
    formats, **line numbers match the original**.
  - `<dir>/normalized/folded/<path>.txt`: the same text folded (below), **same
    line count** as its `text/` twin, so stage 4 can grep folded and cite
    original lines.
  - Never writes inside `<input_dir>`.

## Readings per format

| Format | Reading A (what a parser or model gets) | Reading B (what a human sees) |
|---|---|---|
| Markdown / text | raw decoded text | rendered text: HTML comments, reference-link definitions, link titles, image alt text, `<details>` bodies and `hidden` / `display:none` HTML removed |
| HTML | all DOM text, including attributes a model may read (`alt`, `title`, `aria-label`) and comments | text a browser would paint: drop `display:none`, `visibility:hidden`, `hidden`, and text whose color equals its background, resolving inline styles and `<style>` class rules; drop attributes and comments |
| SVG | all XML text: `<title>`, `<desc>`, `<metadata>`, comments, `<script>`, every `<text>` | painted `<text>` only: drop text whose fill is `none`, transparent, or the background color |
| PDF | text layer | painted text: text layer minus characters drawn in the page background color (white by default) or with invisible render mode (`static-style`); and each page drawn (pypdfium2) and read by OCR: lines the text layer lacks are `B-only`, carrier `image-text`, method `ocr`, and are appended to the reading-A lines, so `read.fold`, `read.script`, and `read.language` read them and `--out` writes them (stage 4 does not read stage 2's normalized text yet). Needs Tesseract; without it, a **skip** per PDF, and a PDF with no text layer is `read.unread` |
| DOCX | every run in `word/document.xml` | visible body: drop `w:vanish` runs and runs colored as the page background (white by default) |
| Images (PNG, JPEG, …) | none (no text layer) | OCR. Needs Tesseract; without it, emit a **skip**, never a pass |

One `read.divergence` finding per divergent text span: `reading` `A-only` or
`B-only`, `text` verbatim, `carrier` naming the hiding mechanism, `method`
naming how reading B was obtained (`static-style`, `ocr`).

## Checks

| Check ID | Rule | Source |
|---|---|---|
| `read.fold` | Fold every text line: NFKC normalize; strip zero-width characters (U+200B-U+200F, U+2060-U+2064, U+FEFF), bidi controls (U+202A-U+202E, U+2066-U+2069), soft hyphen (U+00AD) and Unicode tag characters (U+E0000-U+E007F, which can spell invisible ASCII; THREATS class 4); replace line and paragraph separators (U+2028, U+2029, U+0085) with a space so every tool counts the same lines; fold confusables to ASCII where a mapping exists. One finding per line whose folded text differs from the raw text: `folded` (the folded line) and `removed` (each removed or replaced code point as `U+XXXX`, once per occurrence) | METHOD "Folded copy"; THREATS class 4; TOOLING Unicode table |
| `read.script` | Flag every run of letters in a non-Latin script (Unicode Script property; ignore Common and Inherited), with its line and `script` name | METHOD "Language / script shift"; CHARTER scope |
| `read.language` | Flag every prose passage in Latin script that reads as a language other than English: function words of one listed language outnumber English ones, or (unlisted languages) heavy diacritics and no English. Prose is Markdown outside code fences, `.txt` / `.rst` / `.adoc`, PDF and DOCX text, and OCR text. Answers "is this English?" and never names the language. Deterministic, no dependency (`specs/language.SPEC.md`, with its measured base rate and recall; 2026-10-18, replacing the planned lingua) | METHOD "Language / script shift"; CHARTER scope |
| `read.divergence` | Reading A versus reading B per the table above | METHOD Stage 2; THREATS class 11 |
| `read.metadata` | Every metadata field carrying text: PDF info dictionary and XMP, DOCX core properties, image EXIF and PNG text chunks. `field` and `text` verbatim | METHOD "Metadata"; THREATS class 6 |
| `read.unread` | Every file neither reading could read, with `reason` | REPORTING 2.1, 2.2 |

A check that cannot run because an optional tool is missing emits a **skip**
finding for that file (CONTRACT). Stage 7 lists it; the grader reports it as
INCOMPLETE, never as a pass.

## Dependencies

Core, pip-installable, pinned in `requirements.txt` at the project root:
`pdfminer.six` (PDF text layer with character colors), `pypdf` (PDF metadata),
`beautifulsoup4` + `lxml` (HTML), `python-docx` (DOCX), `Pillow` (image
metadata), `regex` (Unicode script property), `confusable_homoglyphs`
(confusables; check its license at pin time, TOOLING), `charset-normalizer`
(encodings), `PyYAML`.

`pypdfium2` (PDF page rendering, BSD-3-Clause / Apache-2.0; replaced the planned poppler,
2026-10-18, `OCR-SPIKE-2026-10-18.md`).

Optional, never required: Tesseract via `pytesseract` (OCR of images and PDF pages). A missing
Tesseract is reported on stderr and as skips. HTML as a browser draws it is **built**
(2026-10-20, `render_html.py`, `specs/render_html.SPEC.md`): Playwright with its Chromium,
optional; without it each HTML file gets a skip naming carrier `rendered`.
A pip-only OCR engine (RapidOCR) was measured against Tesseract and not taken: it missed
near-invisible text (the spike). Language within Latin script was planned on
`lingua`; it is built instead with no dependency (`read.language`, 2026-10-18), because the
check needs "is this English?", not the language's name, and every optional tool is one more
thing a user has to install.

All development and runs use the project virtualenv: `.venv/` (gitignored),
created with `python -m venv .venv` and `.venv/Scripts/pip install -r requirements.txt`.

## Must never

- Interpret what divergent or hidden text says. Record it verbatim.
- Execute anything from the input (no scripts in HTML or SVG, no macros), fetch
  a URL, or follow a symlink out of the tree.
- Write inside `<input_dir>`.
- Drop a line when folding: folded and original files keep the same line count.
- Pass a file it could not read. An unreadable file is `read.unread` or a skip.

## Done when

1. Every script in this folder has a `specs/<name>.SPEC.md` and pytest tests written
   from it, and they pass.
2. `.venv/Scripts/python grader/grader.py 02` reports PASS, or INCOMPLETE where
   the only skips are checks needing Tesseract (and the report says so).
3. Run on `ReposToExamine/superpowers-main/superpowers-main/` it completes.
   Recount 2026-09-25: 46 HTML comments in its 94 markdown files, 32 of them
   outside code blocks (hidden when rendered). Case 001's "71" was the old
   script's total output (54 comments in all text files plus 17 CSS-hiding
   matches), not a markdown comment count.
