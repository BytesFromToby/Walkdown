# invisible.py: spec

Strips invisible characters from a line before stage 3 matches references, so a
path split by a zero-width character still matches. A reimplementation of the
strip half of stage 2's fold (`stages/02-reader/specs/fold.SPEC.md`); stage 3 never
imports stage 2.

## Inputs

One line of decoded text (no line ending), or the bytes of a whole file.

## Outputs

`strip_line(line) -> str`:

1. Remove zero-width characters U+200B-U+200F, U+2060-U+2064, U+FEFF; bidi
   controls U+202A-U+202E, U+2066-U+2069; soft hyphen U+00AD; Unicode tag
   characters U+E0000-U+E007F.
2. NFKC normalize.

No confusable folding: a path that uses a lookalike letter is a different path
on disk, so it must not be made to match.

`decode(data) -> str | None`: the text of a file, or None when it is not text.
A BOM (UTF-8, UTF-16 LE/BE, UTF-32 LE/BE) picks the codec and is dropped; bytes
holding NUL without a BOM: bytes with NUL are binary when NUL is more than 1% of the bytes or the rest is not strict UTF-8; a few NULs in valid UTF-8 are text (2026-10-09: a literal `\0` sentinel in source made a file binary, so one NUL could hide any file); then UTF-8; then the encoding
`charset-normalizer` detects; else None.

## Must never

- Add or drop a line (callers split on `\n` and keep line numbers).
- Change an ASCII character.

## Done when (each backed by a test in `tests/test_invisible.py`)

1. `refer\u200bences/de\u200dtails.md` strips to `references/details.md`.
2. Bidi controls, a soft hyphen, and tag characters are removed; ASCII text is unchanged.
3. Fullwidth `ｄｏｃｓ／ａ.md` normalizes to `docs/a.md` (NFKC).
4. A Cyrillic `о` is kept (no confusable folding).
5. `decode` reads UTF-8, UTF-8 with BOM (BOM dropped), and UTF-16 with BOM; returns None for bytes holding NUL.

NUL (U+0000) is stripped like the other invisible characters (2026-10-09).
