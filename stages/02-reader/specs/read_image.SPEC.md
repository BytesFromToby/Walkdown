# read_image.py: spec

Images: metadata and (optionally) OCR. Stage 2, checks `read.metadata`,
`read.divergence`, and `read.unread` for images.

## Inputs

The bytes of one image file (PNG, JPEG, GIF, WebP, BMP, TIFF, ICO).

## Outputs

`ocr_available() -> (bool, str)`: True when `pytesseract` imports and the
Tesseract binary answers; the string says what is missing otherwise.

`read_image(data, ocr=True) -> ImageReading` with:

- `metadata`: `{field, text}`, verbatim, non-empty only:
  - PNG text chunks (tEXt, zTXt, iTXt): `field` `png:<keyword>`;
  - EXIF tags with string (or decodable byte) values, including the Exif
    sub-IFD (UserComment, etc.): `field` `exif:<TagName>`;
  - JPEG / GIF comments: `field` `comment`.
  Byte values are decoded as UTF-8 (then Latin-1); an EXIF UserComment drops
  its 8-byte character-code prefix. Values that are not text are skipped.
- `ocr_text`: the OCR text when OCR ran, else None.
- `ocr_skipped`: None when OCR ran, else why it did not (`tesseract not
  installed` and so on).
- `unread`: None, or the reason Pillow could not open the image.

Reading A of an image is empty (no text layer). When OCR runs, its non-empty
text is reading B, so run.py reports it as a `B-only` divergence (carrier
`image-text`, method `ocr`). Without OCR run.py emits a `read.divergence` skip
and a `read.unread` finding.

## Must never

- Pass an image whose text was not read: no OCR means a skip, never silence.
- Decode an image beyond Pillow's decompression-bomb limit.

## Done when (each backed by a test in `tests/test_read_image.py`)

1. A PNG with a tEXt chunk reports `png:<keyword>` with its text.
2. A JPEG with an EXIF ImageDescription reports `exif:ImageDescription`.
3. A plain PNG reports no metadata.
4. With OCR disabled or unavailable, `ocr_skipped` is set and `ocr_text` is None.
5. Non-image bytes give `unread`.

## OCR preprocessing (2026-10-04; rebuilt 2026-10-18 from the OCR spike)

`ocr_views(im) -> list[Image]`: the grayscale views Tesseract reads, in reading order.
`ocr_read(im) -> str`: their OCR text joined with newlines (the views' texts in order). Both are
used for images and for rendered PDF pages (`read_pdf`).

1. Grayscale. The **background** is the most common gray value.
2. **Crop** to the pixels that differ from the background by more than `INK` (3), plus a
   `MARGIN` (12 px). An image with no such pixel has no views (no text).
3. A crop under `OCR_SMALL` (2000) px on its longer side is **one view**, enlarged `OCR_SCALE`
   (3) times, but never past `OCR_MAX` (6000) px.
4. A larger crop is cut into **tiles** of `TILE` (1000) px overlapping by `OVERLAP` (120) px,
   row by row; a tile with no ink is dropped; each tile is enlarged `TILE_SCALE` (2) times. Text
   on a tile edge can appear in two tiles, so a tiled image's OCR text can repeat a line.
5. Each view's **contrast is stretched** to the full range (`autocontrast`), and a view whose
   background is dark (under 128) is **inverted**, so the text is dark on light. Both happen
   before the view is enlarged: the other order reads faint small text worse (69% of words
   against 92%).

Why (`OCR-SPIKE-2026-10-18.md`): small text in a large image was read at its natural size and
missed (9 px text in a 2400 x 1600 image: 64% of words; 8 px light gray: 23%). With crop,
contrast, and tiling: 100% and 92%, and near-invisible text (`#EEE` on white) is still read.
Tiny text is a way to hide an instruction in an image (the first CI run with Tesseract missed
the class 11 fixture's 11-pixel text), and so is faint text.

Done when (tests in `tests/test_read_image.py`):

6. A small image gives one view, grayscale, cropped to its ink and enlarged 3x.
7. A blank image gives no views.
8. A dark image gives a view whose background is light.
9. A large image with ink in two far corners gives tiles for those corners only.
10. A view never exceeds `OCR_MAX` on its longer side.
11. With Tesseract installed: 9 px text in the corner of a 2400 x 1600 image, `#EEE` text on
    white, and 8 px light-gray text in a 2400 x 1600 image are read (most of their words in
    `ocr_read`).
