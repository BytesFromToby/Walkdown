# render_pdf.py: spec

PDF pages drawn and read as images (2026-10-18). Stage 2, `read.divergence` (carrier
`image-text`, method `ocr`) and the reading of a PDF that has no text layer.

The text layer is what a parser hands a model; a page as drawn can carry more: a screenshot of
an instruction, text drawn as shapes, a scanned page. A model that reads the page as an image
sees it. Reading the text layer alone misses it.

## Inputs

The bytes of one PDF file, and the PDF's text layer (`read_pdf` lines).

## Outputs

`page_ocr(data, max_pages=MAX_PAGES) -> PageOcr` with:

- `pages`: one OCR text per page read, in page order. Each page is rendered by **pypdfium2**
  (core dependency, pip, BSD-3-Clause / Apache-2.0; no poppler) at `RENDER_SCALE` (3, which is
  216 dpi, so 6 pt text is 18 px), then read by `read_image.ocr_views(..., enlarge=False)` and
  Tesseract: cropped to the ink, contrast stretched, dark pages inverted, not enlarged and not
  tiled (a rendered page's text is already large enough). Only lines whose median word
  confidence is `CONF` (70) or more are kept; `low` holds the rest, per page, so the runner can
  count what was set aside (`coverage.pdf_pages.low_confidence`: unseen lines set aside).
- `total`: the page count. `skipped`: None, or why no page was read (`tesseract not
  installed`, a render error). Pages after `max_pages` (`MAX_PAGES`, 50) are not read; the
  runner says so as a skip.

`unseen(ocr_text, layer_lines) -> list[list[str]]`: the blocks of consecutive OCR lines the
text layer does not hold. Words are runs of two or more letters or digits, lowercased, NFKC
folded. An OCR line is **unseen** when it has at least `MIN_WORDS` (3) words and at least
`UNSEEN_SHARE` (60%) of them are neither in the text layer nor within one OCR slip of a word in
it (`difflib` ratio 0.8 or more against a layer word of similar length; words of five letters
or more only, since `then` is no slip of `the`). A line of three words
or more that fails is **seen** and ends the block. A shorter line never opens a block; it joins
an open one when none of its words is in the layer, and otherwise is passed over. A line with
no words is passed over. A PDF with no text layer has every OCR line of three words or more
unseen.

## Measured (2026-10-18)

150 PDFs sampled from the pdf.js test corpus (`mozilla/pdf.js` `test/pdfs`, deliberately odd
files: broken fonts, CJK, forms), first three pages each: 142 read, 165 pages, 1 render error.
Without the confidence floor, 13 PDFs gave an unseen block: 4 real text missing from the text
layer (an embedded picture's caption, a calendar header drawn as shapes, a statement title,
"Hello World"), 9 OCR garbage from pictures, symbols, and CJK read as English. Median word
confidence separated them: every real line 94 to 96, every fixture line 94 to 96, garbage 0 to
37 with outliers at 57.5 and 76. Run again at 70: 4 PDFs with a block, 3 of them the real text
(the caption, the calendar header, the statement title) and one a font-test page of repeated
glyph rows with no text layer (drawn text, arguably real); "Hello World" fell out as a
two-word line. The cost: a real instruction drawn degraded enough to fall under 70 is set
aside, and counted, not listed. Image OCR keeps every line (the class 11 image fixture's first
line scores 34).

0.8 seconds per page on this run's CPU (131 s for 165 pages); the first 50 pages of a PDF are
read.

## Must never

- Run PDF JavaScript, open an embedded file, or fetch a URL (pypdfium2 renders; forms and
  JavaScript are not initialized).
- Report a page as clean when it was not read: no Tesseract, a render error, or a page past
  the cap is a skip.
- Call text unseen for one misread word: an OCR slip of a word in the layer is still seen.

## Done when (each backed by a test in `tests/test_render_pdf.py`)

1. `unseen` gives nothing when the OCR lines are the text layer with OCR slips
   (`sumrnary`, `Summarlze`); a short word close to a layer word (`then`, `the`) is not a slip.
2. `unseen` gives a block of the lines that are not in the text layer, and two blocks when a
   seen line sits between them.
3. A line of fewer than three words never opens a block; one with no layer word joins an open
   block.
4. With no text layer, every OCR line of three words or more is unseen.
5. With Tesseract installed: a PDF whose text layer says one thing and whose page carries an
   image of an instruction gives the instruction in `pages` and in `unseen`; an image-only
   (scanned) PDF gives its text; a picture of Chinese text, which English OCR reads as garbage
   at low confidence, puts nothing unseen in `pages` and the garbage in `low`.
6. Without Tesseract (`ocr=False`), `page_ocr` gives no pages and a `skipped` reason; the page
   cap gives `total` larger than `len(pages)`.
