# read_pdf.py: spec

PDF readings A and B and PDF metadata. Stage 2, checks `read.divergence`,
`read.metadata`, and `read.unread` for PDF.

## Inputs

The bytes of one PDF file.

## Outputs

`read_pdf(data) -> PdfReading` with:

- `lines`: reading A, the text layer from pdfminer.six, one entry per text line
  in page order (layout analysis order), with an empty line between pages.
- `divergences`: `{text, carrier, page, text_line}`, reading `A-only`, method
  `static-style`. Reading B is the text layer minus characters a render does not
  show:
  - text render mode 3 (invisible; carrier `render-mode-invisible`);
  - fill color that `hides` against the background (carriers from
    `colors.carrier`); the background at a character is the fill color of the
    smallest filled rectangle containing the character's center, else white;
  - character box entirely outside the page's media box (carrier `off-page`).
  Consecutive hidden characters of one text line with the same carrier are one
  divergence; `text` is stripped of surrounding whitespace; `text_line` is its
  1-based line in `lines`.
- `metadata`: `{field, text}` for each document information dictionary entry
  whose value is a non-empty string (`field` without the leading `/`), then each
  XMP element with non-empty text (`field` `xmp:<name>`; list items take the
  name of their property).
- `unread`: None, or the reason the PDF could not be read (`encrypted`, or a
  parse error). When set, the other fields are empty.

Colors: gray, RGB, and CMYK fill values are converted to RGB; pattern or
unknown colors count as visible.

OCR of rendered pages (poppler + Tesseract) is optional and not used in v1;
run.py notes that the image-only direction (text painted but absent from the
text layer) is not examined.

## Must never

- Run PDF JavaScript, open embedded files, or fetch a URL.
- Interpret the text.

## Done when (each backed by a test in `tests/test_read_pdf.py`)

1. A PDF with black and white text on a white page gives both lines in `lines` and one `white-on-white` divergence for the white text only.
2. Text in render mode 3 gives `render-mode-invisible`.
3. White text on a black filled rectangle is not reported.
4. Info dictionary entries with text (Title, Keywords, Author) are reported verbatim; empty ones are not.
5. Bytes that are not a PDF give `unread` with a reason and no exception.
