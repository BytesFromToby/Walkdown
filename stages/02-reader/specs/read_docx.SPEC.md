# read_docx.py: spec

DOCX readings A and B and core properties. Stage 2, checks `read.divergence`,
`read.metadata`, and `read.unread` for DOCX.

## Inputs

The bytes of one DOCX file (a ZIP package).

## Outputs

`read_docx(data) -> DocxReading` with:

- `lines`: reading A, one entry per paragraph (`w:p`) of `word/document.xml`
  in document order: the text of every run (`w:t`; `w:tab` as a tab; `w:br` and
  `w:cr` as a space). Runs inside hyperlinks, insertions, smart tags, and
  content controls belong to their paragraph. Deleted text (`w:delText`) is not
  in either reading.
- `divergences`: `{text, carrier, paragraph, text_line}`, reading `A-only`,
  method `static-style`. Reading B drops runs that are:
  - hidden (`w:vanish` on, carrier `vanish`);
  - colored so they `hide` against their background (carriers from
    `colors.carrier`); background is the run shading or highlight, else the
    paragraph shading, else the document background (`w:background`), else
    white; color `auto` is always visible;
  - at most 1 point in size (`w:sz` at most 2 half-points, carrier `tiny-font`).
  Run properties resolve as document defaults, then the paragraph style chain,
  then the run style chain (`w:basedOn`), then direct formatting; an explicit
  `w:val` of `0`, `false`, or `off` turns a toggle off. Consecutive hidden runs
  of one paragraph with the same carrier are one divergence, `text` stripped.
- `metadata`: `{field, text}` for every element of `docProps/core.xml` with
  non-empty text (`field` the element's local name, such as `creator`,
  `description`, `keywords`), then each custom property of
  `docProps/custom.xml` (`field` `custom:<name>`).
- `unread`: None, or the reason (`not a zip`, `no word/document.xml`, member too
  large, XML error). When set, the other fields are empty.

XML is parsed with lxml with entity resolution and network access off. A ZIP
member over 50 MB uncompressed is not read.

## Must never

- Run macros, follow external relationships, or fetch a URL.
- Interpret the text.

## Done when (each backed by a test in `tests/test_read_docx.py`)

1. A `w:vanish` run is reported as `vanish`; the visible paragraph is not.
2. A white run (`w:color FFFFFF`) is reported as `white-on-white`; a white run on black shading is not.
3. A paragraph style with `w:vanish` hides its runs; a direct `w:vanish w:val="0"` overrides it.
4. `lines` holds one entry per paragraph including hidden text.
5. Core properties with text are reported by local name; empty ones are not.
6. Bytes that are not a ZIP give `unread`.
