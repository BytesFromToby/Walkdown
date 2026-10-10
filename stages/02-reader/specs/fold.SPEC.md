# fold.py: spec

The folded copy and invisible-character detection. Stage 2, check `read.fold`,
and the invisible-character part of `read.divergence` for every text file.

## Inputs

One line of decoded text (no line ending).

## Outputs

`fold_line(line) -> (folded, removed)`:

1. Strip zero-width characters U+200B-U+200F, U+2060-U+2064, U+FEFF; bidi
   controls U+202A-U+202E, U+2066-U+2069; soft hyphen U+00AD; Unicode tag
   characters U+E0000-U+E007F (they can spell invisible ASCII).
2. Replace line and paragraph separators U+2028, U+2029, and U+0085 with one
   space each, so every tool counts the same lines (the line is split on `
`
   only; these never start a new line).
3. NFKC normalize.
4. Fold confusables to ASCII: each **non-ASCII** character that
   confusable_homoglyphs maps to an all-ASCII homoglyph is replaced by it (the
   first such). ASCII characters are never changed. A character whose only
   homoglyphs are non-ASCII (an em-dash) is kept.

`removed`: each removed or replaced code point of the original line as
`U+XXXX` (at least four hex digits, uppercase), once per occurrence, in line
order. When the line changes only by NFKC composition, the non-ASCII code
points absent from the folded line are listed.

`fold_finding(file, line_no, raw) -> dict | None`: the `read.fold` finding
(`check`, `file`, `line`, `folded`, `removed`) when the folded line differs
from the raw line, else None.

`hidden_chars(line) -> list[(char, kind)]`: every invisible character in the
line, with kind `zero-width` (the zero-width set above), `bidi`, `soft-hyphen`,
or `tag-chars` (Unicode Tags block U+E0000-U+E007F, and U+180E MONGOLIAN VOWEL
SEPARATOR, which is detected but not stripped by the fold). Line separators
are not listed here: they are folded (`read.fold`) but are layout characters,
not invisible text, so they do not by themselves make a `read.divergence`.

Tag characters are now both folded (`read.fold`, stripped, listed in
`removed`) and reported as a `read.divergence` with carrier `tag-chars`. Both
stay: the fold gives stage 4 a greppable line, and the divergence records the
fact that the raw line carries text a human cannot see (class 4, class 11).

`invisible_finding(file, line_no, raw) -> dict | None`: one `read.divergence`
finding for a line holding invisible characters: `reading` `A-only`, `text`
the raw line verbatim, `carrier` the kinds present joined by `+` in the order
zero-width, bidi, soft-hyphen, tag-chars, `method` `static-style`, and
`chars` (the code points as `U+XXXX`).

## Must never

- Drop or add a line: one line in, one line out.
- Change an ASCII character.
- Interpret what the line says.

## Done when (each backed by a test in `tests/test_fold.py`)

1. `ig​no​re all` folds to `ignore all` with `removed` `["U+200B", "U+200B"]`.
2. A line with U+202E and U+202C folds with both removed and listed in order.
3. A soft hyphen inside a word is removed.
4. NFKC: fullwidth `ｉｇｎｏｒｅ` folds to `ignore`; Cyrillic `о` inside a Latin word folds to `o`; a right single quote folds to `'`.
5. An em-dash, `café`, and plain ASCII lines are unchanged and give no finding.
6. ASCII characters with ASCII homoglyphs (`l`, `1`, `0`, `m`) are never changed.
7. A line holding tag characters spelling ASCII (U+E0069 U+E0067 ...) folds with them stripped and each listed in `removed`; the visible text around them is kept.
8. U+2028, U+2029, and U+0085 inside a line are each replaced by one space and listed in `removed`; the fold of a multi-line text keeps its line count.
9. `hidden_chars` names zero-width, bidi, soft-hyphen, and tag characters; `invisible_finding` carries the raw line and the joined carrier.

## NUL (2026-10-09)

NUL (U+0000) is stripped by the fold and is its own hidden-character kind, `nul` (last in the carrier order), so a NUL in a text file gives a `read.divergence` (`A-only`) and a `read.fold`.
