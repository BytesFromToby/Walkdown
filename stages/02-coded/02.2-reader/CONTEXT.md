# 02.2-reader: what the model actually reads

**Question:** what does the model actually receive?
**Kind of evidence:** two independent readings of every file; where they disagree is recorded as a fact.
**Plain name:** What the model actually reads (its heading in `full.md`).

## Inputs

- `<input_dir>`: the folder audited, read-only.
  `python stages/02-coded/02.2-reader/run.py <input_dir> [--out <dir>]`
- Nothing from `data/` (`reads` in `stages/stages.json` is empty): it walks the folder itself, with
  02.1's rules.
- `Library/invisible.yaml`, through `stages/_shared/library.py`: the one list of invisible characters.
- Optional tools: Tesseract through `pytesseract` (OCR of images and PDF pages) and Playwright with its
  Chromium (HTML drawn as a browser draws it). A missing tool gives a skip, never a pass.

## Process

Each file by kind (`files.py`) is read as reading A (what a parser or model gets) and reading B (what a
human sees): Markdown (`read_md.py`), HTML (`read_html.py`, `render_html.py`), SVG (`read_svg.py`), PDF
(`read_pdf.py`, `render_pdf.py`), DOCX (`read_docx.py`), images (`read_image.py`). The checks:

- `read.fold` (`fold.py`): each line folded (NFKC, invisible characters removed, confusables to ASCII);
  one finding per line the fold changes.
- `read.script` (`script_runs.py`) and `read.language` (`language.py`): runs of non-Latin script, and
  prose in Latin script that reads as another language than English.
- `read.divergence`: reading A against reading B, with the carrier and the method.
- `read.metadata`: PDF, DOCX, and image metadata text. `read.unread`: a file neither reading could read.

Never: interpret what hidden text says (it is recorded verbatim); run anything from the input (no script,
no macro), fetch a URL, or follow a symlink out of the tree; write inside `<input_dir>`; drop a line when
folding; pass a file it could not read.

## Outputs

- stdout: one contract-1 report; the runner saves it as `data/02.2-reader.json`, and stderr as
  `data/02.2-reader.notes.txt`.
- With `--out <dir>` (the runner gives `data/`): `data/normalized/text/<path>.txt`, the true text of each
  readable file (reading A, line numbers as in the original), and `data/normalized/folded/<path>.txt`, the
  same text folded with the same line count. It refuses an `--out` inside the input.

## The human check

A divergence quotes the hidden text verbatim and names the carrier (a comment, `display:none`, a zero-width
character, an image), so a person can open the file at that line and see it. The fixtures
`Fixtures/02.2-reader/` (one hidden-text case per format and carrier) and
`python tools/grader/grader.py 02.2-reader` give the validation stamp in `LOG.md`; without Tesseract the
stamp is INCOMPLETE and says so, and `data/limits.md` lists what was not read.

## Spec

`specs/reader.SPEC.md`: one section per script, `run` first and the others in alphabetical order
(`colors`, `files`, `fold`, `language`, `read_docx`, `read_html`, `read_image`, `read_md`, `read_pdf`,
`read_svg`, `render_html`, `render_pdf`, `script_runs`).
