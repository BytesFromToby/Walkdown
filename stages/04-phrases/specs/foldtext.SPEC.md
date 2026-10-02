# foldtext.py: spec

The folded copy stage 4 greps, and the text decoder. A reimplementation of
stage 2's fold (`stages/02-reader/specs/fold.SPEC.md`); stage 4 never imports
stage 2 (CONTEXT "Inputs"). Named `foldtext` rather than `fold` because the
stages share one pytest session and stage 2 already has a module `fold`.

## Inputs

One line of decoded text (no line ending), or the bytes of a whole file.

## Outputs

`fold_line(line) -> str`, in this order:

1. Strip zero-width characters U+200B-U+200F, U+2060-U+2064, U+FEFF; bidi
   controls U+202A-U+202E, U+2066-U+2069; soft hyphen U+00AD; Unicode tag
   characters U+E0000-U+E007F.
2. Replace U+2028, U+2029, and U+0085 with one space each.
3. NFKC normalize.
4. Fold confusables to ASCII: each **non-ASCII** character that
   `confusable_homoglyphs` maps to an all-ASCII homoglyph is replaced by the
   first such homoglyph. ASCII characters are never changed; a character whose
   only homoglyphs are non-ASCII (an em-dash) is kept.

`decode(data) -> str | None`: the text of a file, or None when it is not text.
A BOM (UTF-8, UTF-16 LE/BE, UTF-32 LE/BE) picks the codec and is dropped;
bytes holding NUL without a BOM are binary; then UTF-8; then the encoding
`charset-normalizer` detects; else None.

`split_lines(text) -> list[str]`: the lines of a text, split on `\n` only
(never on U+2028, U+2029, U+0085, form feed, or other characters Python's
`splitlines` treats as breaks), one trailing `\r` removed from each line. A
final empty piece after a trailing newline is not a line. Line `i` of the
result is line `i + 1` of the file.

## Must never

- Add or drop a line.
- Change an ASCII character.
- Import stage 2.

## Done when (each backed by a test in `tests/test_foldtext.py`)

1. `ig​no​re all` folds to `ignore all`.
2. Bidi controls, a soft hyphen, and tag characters are stripped; the visible text around them is kept.
3. Fullwidth `ｉｇｎｏｒｅ` folds to `ignore`; a Cyrillic `о` inside a Latin word folds to `o`.
4. U+2028, U+2029, U+0085 each become one space; `split_lines` does not split on them.
5. Plain ASCII, an em-dash, and `café` are unchanged; ASCII `l`, `1`, `0` are never changed.
6. `decode` reads UTF-8, UTF-8 with BOM (dropped), UTF-16 with BOM; returns None for bytes holding NUL.
7. `split_lines("a\r\nb\n")` is `["a", "b"]`; `split_lines("a\n\nb")` is `["a", "", "b"]`.
