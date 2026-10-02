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
