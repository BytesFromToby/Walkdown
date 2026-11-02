# reader: spec

One spec for the `02.2-reader` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. Merged from the per-script specs in restructure step 8a.

## run

The single entry point for `02.2-reader`. Wires `files`, `fold`, `script_runs`, `language`, and
the format readers together and prints one contract-1 report
(`stages/CONTRACT.md`).

### Inputs

```
python stages/02-coded/02.2-reader/run.py <input_dir> [--out <dir>]
```

### Outputs

stdout: one JSON document, UTF-8:

```json
{"stage": "02.2-reader", "contract": 1, "findings": [...], "reading": {...}, "coverage": [...]}
```

Per file, in path order, by kind (`files.classify`):

| Kind | Reading A text | Findings |
|---|---|---|
| markdown, html, svg, text | decoded text, original lines | `read.fold` and `read.script` per line; `read.divergence` for invisible characters per line (`fold.invisible_finding`); plus markdown carriers (`read_md`), HTML (`read_html`), or SVG (`read_svg`) divergences; `read.language` (`language.language_findings`) for markdown and for text files with a prose extension (`txt`, `text`, `rst`, `adoc`, `asciidoc`) |
| pdf | `read_pdf` lines, then the OCR lines of each page the text layer lacks (`render_pdf.unseen`), after a blank line | `read.fold` / `read.script` / `read.language` over those lines; static divergences; one `B-only` `image-text` divergence (method `ocr`, `page`, `text_line` of its first appended line) per unseen block; `read.metadata`. Without Tesseract: a `read.divergence` skip per PDF, with `carrier` `image-text` (only the OCR is skipped; the static readings ran); a render error or pages past `render_pdf.MAX_PAGES` are skips too |
| docx | `read_docx` lines | same as pdf |
| image | none | `read.metadata`; OCR text as a `B-only` divergence, or a `read.divergence` skip plus `read.unread` |
| office-other, archive, binary | none | `read.unread` with the reason |
| symlink | none | `read.unread` (`symlink, not followed`, plus `target`) |

Every `read.divergence` carries `reading`, `text`, `carrier`, `method`
(`static-style` or `ocr`). Text formats use the original line number in `line`.
In a text format, a divergence whose text reaches past its first line also has `end_line`, the last line it reaches
(`reach`: its words found in order from `line`, in each line as written and with its entities decoded). The mask of a line the
secret scan flags needs it (`stages/_shared/secretmask.py`), since a parser's text has lost its line breaks, stripped or
collapsed. A word that cannot be found (tags between its letters glue it, a browser made it) leaves the reach unknown, so
`end_line` is the last line of the file.
PDF and DOCX findings are not line-based: `line` is null and `text_line` gives
the line in the normalized text (`page` / `paragraph` too). A file that cannot
be read by its reader gives `read.unread` with the reason; an SVG that is not
well-formed still gets its text checks and a `read.divergence` skip.

Within a file, findings are ordered: `read.unread`, `read.divergence`,
`read.fold`, `read.script`, `read.language`, `read.metadata`, skips.

`reading` (called `coverage` until M9 slice C gave that name to the coverage lines, below): `files`, `files_read`, `bytes`, `bytes_read`, `unread` (list of
paths), `carriers` (count of divergences per carrier), `markdown_files`,
`markdown_comments`, `language` (`files` checked for language, paragraphs `judged`, and
paragraphs too `short` to judge), `pdf_pages` (`total` pages in PDFs, pages `read` by OCR),
`html` (`files` HTML files seen, `drawn` by a browser; added 2026-10-20),
`optional_tools` (Tesseract and Playwright present or absent), and
`not_examined`: what this run left unchecked, each item saying why, "(tesseract not
installed)" or "(not built)".

stderr: notes, including a missing Tesseract and what it skips, a missing Playwright
(`note: html render: <why>`, 2026-10-20), and one `note: not built:`
line for each check in `NOT_BUILT` (empty since HTML render was built, 2026-10-20), on every run (2026-10-12:
these were once reported as missing tools, though no code uses those tools, so installing one
hid the gap), and one `note: v1 limit:` line saying what the language check does not read
(code, config, HTML, paragraphs under five words). Language within Latin script left
`NOT_BUILT` when `language.py` was built, and PDF render + OCR when `render_pdf.py` was
(2026-10-18). A PDF with no text layer is read by OCR when Tesseract is installed, and is
`read.unread` when it is not (or when no page could be read).

`--out <dir>` also writes `<dir>/normalized/text/<rel>.txt` (reading A) and
`<dir>/normalized/folded/<rel>.txt` (each line folded), one per file with
reading-A text, same line count in both. It refuses (exit 2) an out dir inside
the input.

Exit 0 whenever a report was produced. Exit 2 with a message on stderr for a
missing or non-folder argument or a bad `--out`.

### Must never

- Print anything but the report to stdout.
- Write inside the input folder.
- Run anything from the input, follow a symlink, or fetch a URL.
- Emit a skip for a check that did run (a check not built is a stderr note, not a skip).
- Report a check as waiting on a tool when no code would use the tool.

### Done when (each backed by a test in `tests/test_run.py`)

1. On a small mixed folder, stdout parses as a contract-1 report with stage `02.2-reader`, and the exit code is 0.
2. A markdown file with a zero-width line, a comment, and a Cyrillic line gives `read.fold`, `read.divergence` (invisible and comment), and `read.script` findings at the right lines.
3. An HTML file with a `display:none` div gives a `display:none` divergence with method `static-style`.
4. A PNG without OCR gives a `read.divergence` skip and a `read.unread` finding; an unknown binary gives `read.unread`.
5. `--out` writes text and folded files with equal line counts, and folded lines differ only where `read.fold` fired.
6. `--out` inside the input exits non-zero; the input folder is byte-identical after a run.
7. A missing folder exits non-zero without printing a report.
8. A markdown file with a Spanish line in an English list gives one `read.language` finding at that line; the same line in a `.py` file gives none; a PDF line gives one with `text_line`; `reading.language` counts files and paragraphs; stderr has no `not built: language` line and has the language `v1 limit` line.
9. A PDF whose page shows text its text layer lacks gives one `image-text` divergence with `page` and a `text_line` after the layer, and the text is in `--out`'s normalized text; a scanned PDF is read, not unread; `reading.pdf_pages` counts pages. Without Tesseract: one skip per PDF, a PDF with no text layer is `read.unread`, and `not_examined` names image and PDF page OCR.

10. Hidden text that reaches past its first line says how far, in Markdown, HTML, and SVG (`test_hidden_text_that_reaches_past_its_first_line_says_how_far`, `test_a_markdown_comment_keeps_an_entity_as_written`); one-line hidden text and a line of hidden characters have no `end_line` (`test_a_line_of_hidden_characters_has_no_reach`); a word that cannot be placed runs to the end of the file (`test_a_word_that_cannot_be_placed_runs_to_the_end_of_the_file`).

### History

- 2026-11-01: `end_line` on a divergence that reaches past its first line, for the mask of a flagged line. `02.5-capability` still goes by the line breaks in `text`, as it did.

### HTML drawn (added 2026-10-20)

Each HTML file, after its static reading, is drawn by `render_html.Session` (`html_drawn`): one
browser for the run, closed at the end even when a file fails. Its findings are
`read.divergence` with `carrier` `rendered`, `method` `render`, and `how`
(the `render_html` section). Without Playwright, past `render_html.MAX_FILES`, or when a page
fails to load, the file gets a skip naming carrier `rendered`; `not_examined` lists "HTML as a
browser draws it (<why>)" when the tool is missing. Test: `tests/test_run.py`
(`test_html_not_drawn_without_playwright`).

## colors

Color parsing and the "text colored as its background" test shared by the HTML,
SVG, PDF, and DOCX readers. No check of its own.

### Inputs

Color strings as they appear in CSS, SVG, or DOCX, or RGB tuples from PDF.

### Outputs

`parse(value) -> (r, g, b, a) | None` with r, g, b in 0-255 and a in 0-1:
`#rgb`, `#rgba`, `#rrggbb`, `#rrggbbaa`, bare 6-digit hex (DOCX `FFFFFF`),
`rgb()` / `rgba()` with numbers or percentages, CSS named colors
(case-insensitive), and `transparent` (alpha 0). `none`, `auto`, `inherit`,
`currentColor`, and anything else unknown give None. `!important` is ignored.

`luminance(rgb) -> float`: WCAG relative luminance.

`contrast(fg, bg) -> float`: WCAG contrast ratio (1 to 21).

`hides(fg, bg) -> bool`: True when `fg` has alpha 0, or when the contrast
ratio of fg against bg is below `MIN_CONTRAST` (1.25: text a reader cannot
tell from its background).

`carrier(fg, bg) -> str`: `transparent` when fg alpha is 0; `white-on-white`
when fg and bg are both light (luminance at least 0.7); otherwise
`color-matches-background`.

`WHITE`: the default background (255, 255, 255, 1).

### Must never

- Raise on an unparseable color; it returns None.

### Done when (each backed by a test in `tests/test_colors.py`)

1. `#fff`, `#ffffff`, `FFFFFF`, `white`, `rgb(255,255,255)`, `rgb(100%,100%,100%)` all parse to white; `transparent` has alpha 0; `none` and `auto` give None.
2. White on white hides with carrier `white-on-white`; white on `#eee` hides; black on white does not.
3. Black on black hides with carrier `color-matches-background`.
4. Contrast of black on white is 21.

## files

Lists the files of an input folder, reads their bytes, decides each file's
format, and decodes text. `02.2-reader` foundation; no check of its own.

### Inputs

- `input_dir`: a folder (pinned repo copy or fixture folder). Read-only.
- For `classify` and `decode`: one file's relative path and bytes.

### Outputs

`list_files(input_dir) -> list[Entry]`, sorted by `rel`:

- `rel`: path relative to the input, forward slashes.
- `kind`: `file` or `symlink`.
- `target`: the link target string for a symlink, else None.

Walked with `os.scandir`, never following a symlink or a Windows junction. A
root-level `.git` folder is not walked.

`classify(rel, data) -> str`, one of:

| Kind | When |
|---|---|
| `pdf` | `%PDF-` in the first 1024 bytes |
| `image` | PNG, JPEG, GIF, WebP, BMP, TIFF, or ICO signature |
| `docx` | ZIP whose member list has `word/document.xml` |
| `office-other` | ZIP with `xl/` or `ppt/` members (XLSX, PPTX), or an OLE2 compound file (old `.doc`/`.xls`/`.ppt`) |
| `archive` | any other ZIP, gzip, bzip2, xz, 7z, RAR, zstd |
| `markdown` | decodes as text; extension `md`, `markdown`, `mdx`, `mdc` |
| `html` | decodes as text; extension `html`, `htm`, `xhtml` |
| `svg` | decodes as text; extension `svg` |
| `text` | decodes as text, any other extension |
| `binary` | does not decode |

`decode(data) -> (text, encoding) | None`: a UTF-8/16/32 BOM picks the codec
and is removed; otherwise bytes with NUL are binary when NUL is more than 1% of the bytes or the rest is not strict UTF-8; a few NULs in valid UTF-8 are text (2026-10-09: a literal `\0` sentinel in source made a file binary, so one NUL could hide any file); otherwise strict UTF-8; otherwise
charset-normalizer's best guess; otherwise None.

`split_lines(text) -> list[str]`: split on `\n`, a trailing `\r` removed from
each line, and no extra empty line after a final `\n`. `len(split_lines(t))`
equals the line count an editor shows (an empty file has 0 lines).

### Must never

- Follow a symlink or junction, or read outside `input_dir`.
- Write anything.
- Run anything from the input.

### Done when (each backed by a test in `tests/test_files.py`)

1. A folder lists every file sorted with forward-slash paths; a root `.git` folder is skipped.
2. A symlink is listed as `symlink` with its target and not followed (skipped where the platform cannot create symlinks).
3. `classify` names pdf, image (PNG), docx, office-other (XLSX), archive (plain ZIP, gzip), markdown, html, svg, text, and binary correctly from small inline bytes.
4. `decode` handles UTF-8, UTF-8 with BOM (removed), UTF-16 with BOM; NUL bytes without a BOM are binary, except a few NULs in valid UTF-8, which are text.
5. `split_lines` keeps line numbers: `"a\r\nb\n"` gives `["a", "b"]`, `"a\n\nb"` gives `["a", "", "b"]`, `""` gives `[]`.

## fold

The folded copy and invisible-character detection. `02.2-reader`, check `read.fold`,
and the invisible-character part of `read.divergence` for every text file.

### Inputs

One line of decoded text (no line ending).

### Outputs

`fold_line(line) -> (folded, removed)`:

1. Strip the characters `Library/invisible.yaml` lists with action `strip`: zero-width characters
   U+200B-U+200F, U+2060-U+2064, U+FEFF, and, since 2026-10-29, U+180E, U+034F, U+206A-U+206F,
   U+FFF9-U+FFFB, U+1D173-U+1D17A, U+1BCA0-U+1BCA3; bidi controls U+202A-U+202E, U+2066-U+2069, and
   U+061C; soft hyphen U+00AD; the blank letters and cells U+115F, U+1160, U+3164, U+FFA0, U+17B4,
   U+17B5, U+2800; Unicode tag characters U+E0000-U+E007F (they can spell invisible ASCII); NUL.
   Strip, too, every character with action `run` (the variation selectors U+FE00-U+FE0F and
   U+E0100-U+E01EF, and the Mongolian free variation selectors U+180B-U+180D and U+180F) where
   two or more stand in a run (`library.runs`; the number is `run_length` in the file). A run is
   selectors in a row, or separated only by characters the list strips (a zero-width space, a soft
   hyphen, a tag character between two selectors does not break it); it begins and ends with a
   selector. The whole stretch is stripped and reported: the selectors under `variation-selectors`
   and each stripped character between them under its own kind. One selector alone is ordinary,
   after an emoji or a CJK character, and stays in the line and out of the report, even with a
   stripped character after it. A run is found in the line as it is written; a visible character, a
   space, or a line separator between two selectors ends the run.
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
line, with the kind the list gives it: `zero-width` (the zero-width set above, U+180E among it
since 2026-10-29), `bidi`, `soft-hyphen`, `filler` (the blank letters and cells), `tag-chars`
(Unicode Tags block U+E0000-U+E007F), `variation-selectors` (only the characters that stand in a
run), or `nul`. Line separators
are not listed here: they are folded (`read.fold`) but are layout characters,
not invisible text, so they do not by themselves make a `read.divergence`.

Tag characters are now both folded (`read.fold`, stripped, listed in
`removed`) and reported as a `read.divergence` with carrier `tag-chars`. Both
stay: the fold gives `02.4-phrases` a greppable line, and the divergence records the
fact that the raw line carries text a human cannot see (class 4, class 11).

`invisible_finding(file, line_no, raw) -> dict | None`: one `read.divergence`
finding for a line holding invisible characters: `reading` `A-only`, `text`
the raw line verbatim, `carrier` the kinds present joined by `+` in the order
zero-width, bidi, soft-hyphen, filler, tag-chars, variation-selectors, nul (the list's `kind_order`),
`method` `static-style`, and
`chars` (the code points as `U+XXXX`). When the line holds tag characters U+E0020-U+E007E,
`decoded` is the ASCII they spell, each run joined by a space (`library.tag_texts`; 2026-10-25, review
C42, an outside tester: the report listed 69 code points and never the sentence they spelled). A tag
character between the selectors of a run joins the ones beside it, as `02.4-phrases` reads it. A run of
variation selectors whose bytes (U+FE00-U+FE0F are 0 to 15, U+E0100-U+E01EF are 16 to 255) are UTF-8
of printable characters with a word of two letters or more adds the text it spells to `decoded`,
after the tag runs' (`library.run_text`). The text comes from the byte selectors alone, so a Mongolian
selector among them hides nothing. A run that spells nothing, and a run of Mongolian selectors only,
adds nothing and is still reported.

The characters to strip, the runs, the separators, and the kinds are not listed in this script: they are read
from `Library/invisible.yaml` through `stages/_shared/library.py`, the one list `02.2-reader`, `02.3-graph`, `02.4-phrases`,
`02.5-capability`, and `06-report` share (restructure step 3, 2026-10-29), and so is the rule for a run. A
range added to the file is stripped and reported here with no change to this script.

### Must never

- Drop or add a line: one line in, one line out.
- Change an ASCII character.
- Interpret what the line says.

### Done when (each backed by a test in `tests/test_fold.py`)

1. `ig​no​re all` folds to `ignore all` with `removed` `["U+200B", "U+200B"]`.
2. A line with U+202E and U+202C folds with both removed and listed in order.
3. A soft hyphen inside a word is removed.
4. NFKC: fullwidth `ｉｇｎｏｒｅ` folds to `ignore`; Cyrillic `о` inside a Latin word folds to `o`; a right single quote folds to `'`.
5. An em-dash, `café`, and plain ASCII lines are unchanged and give no finding.
6. ASCII characters with ASCII homoglyphs (`l`, `1`, `0`, `m`) are never changed.
7. A line holding tag characters spelling ASCII (U+E0069 U+E0067 ...) folds with them stripped and each listed in `removed`; the visible text around them is kept.
8. U+2028, U+2029, and U+0085 inside a line are each replaced by one space and listed in `removed`; the fold of a multi-line text keeps its line count.
9. `hidden_chars` names zero-width, bidi, soft-hyphen, filler, tag, variation-selector (in a run only), and NUL characters; `invisible_finding` carries the raw line and the joined carrier, and `decoded` with the ASCII a tag run spells and the text a variation-selector run spells (none without either).
10. Each new character is stripped and reported with its kind: U+180E, U+034F, U+206A, U+FFF9, U+1D173, and U+1BCA0 as `zero-width`, U+061C as `bidi`, the Hangul fillers, Khmer vowels, and U+2800 as `filler` (`test_the_new_characters_are_stripped_and_reported_with_their_kinds`, `test_u180e_is_stripped_as_zero_width_not_detected_as_a_tag_character`).
11. Two variation selectors in a row are stripped and reported with carrier `variation-selectors`; one alone, after an emoji, a keycap, or a CJK character, gives no `read.fold` and no `read.divergence`; selectors with only stripped characters between them (a zero-width space) are one run, reported whole, and one selector with a stripped character after it is not a run (`test_a_run_of_variation_selectors_is_stripped_and_reported_a_lone_one_is_not`, `test_selectors_with_only_stripped_characters_between_them_are_one_run`, `test_one_selector_with_a_stripped_character_after_it_is_not_a_run`).
12. A run that spells text puts it in `decoded`, after any tag text; the carrier follows the list's kind order (`test_a_run_that_spells_text_is_decoded_in_the_finding`, `test_tag_and_selector_decodes_join_with_a_space_tags_first`, `test_the_carrier_follows_the_kind_order_of_the_list`); the text is read from the selectors alone, so zero-width spaces between them hide nothing (`test_a_run_interleaved_with_zero_width_spaces_still_spells_its_text`), and so does a Mongolian selector among the byte selectors (`test_a_mongolian_selector_inside_a_run_does_not_hide_its_text`). The fixture lines are `Fixtures/02.2-reader/class04-invisible-more.md`.

### NUL (2026-10-09)

NUL (U+0000) is stripped by the fold and is its own hidden-character kind, `nul` (last in the carrier order), so a NUL in a text file gives a `read.divergence` (`A-only`) and a `read.fold`.

### What the step looked at (added 2026-10-30, M9 slice C)

The report's `coverage` list (`stages/CONTRACT.md`, "Coverage lines") has four lines, unit `files`. A check counts the files in its
scope where the kind of file is known (`cov.of`, before the file is read) and where it has handled each one (`cov.look`).

- `read.unread`, `read.fold`, `read.script`: `of` is the files `files.list_files` lists, counted before the loop; `looked_at` is the
  files `read_one` read, counted at the end of each branch that read the file (a PDF with no text layer, and an image whose text
  was not read, are listed as unread and are not counted here); `explained` is the files with a `read.unread` finding (a symlink,
  bytes that cannot be read, a format the reader does not read, a reader error), counted in the loop where the unread row is seen.
- `read.divergence`: `of` is the files with two readings (Markdown, HTML, SVG, a PDF, a DOCX, a picture: `DIVERGENCE_KINDS`);
  `looked_at` is counted in the branch of each, where its readings are set against each other; `explained` is such a file that is
  unread before that. A plain text or script file has one reading and is not one of them.
- `read.metadata`: `of` is the PDFs, DOCX files, and images (the files that carry metadata); `looked_at` is counted where the
  metadata is read; `explained` is such a file that is unread before its metadata was read.
- `read.language`: `of` is the files the language check is to judge (Markdown, plain-text prose, and the text of a PDF, a DOCX, or
  an image: `prose_candidate`); `looked_at` is counted inside `language_checks`; `explained` is such a file that is unread before the
  check ran.

An image with no OCR (Tesseract not installed) is such a file: it is explained by its `read.unread` row and its skip, so a missing
optional tool leaves the run as it was and no gap. A file a branch passes over without a finding or a skip leaves a line short.
The tests are in `tests/test_coverage.py`, with one for each line that makes the reader leave a file out, and one with a PDF and a
DOCX that counts the metadata where each is read.
13. A tag character between the selectors of a run reads as one word in `decoded` (`test_a_tag_character_between_selectors_reads_as_one_word`).

### History

- 2026-10-30: M9 slice C: the report has a `coverage` list of lines (what the step looked at). The object that was called `coverage` is `reading` now (same keys and values), because the list takes the name; a report made before has the object under `coverage`, and `pipeline.read_report` reads it as a report with no lines. The findings are unchanged.
- 2026-10-29 (P1): `Library/invisible.yaml` gained the characters an outside note (2026-10-28) and the
  measurement the same day found: U+180E (it was detected under the `tag-chars` kind and never
  stripped; it is stripped as `zero-width` now), U+034F, the deprecated format controls, interlinear
  annotation, the musical and shorthand format controls, U+061C, the blank letters and cells (a new
  kind, `filler`), and the variation selectors, a run of which hides bytes after one visible character
  (a new kind, `variation-selectors`, and a new list action, `run`). `fold.py` changed to read them
  from the list; the `detect` action is gone with its only character.
- 2026-10-29 (P1, review before verification): a run is selectors in a row or separated only by
  characters the list strips. A zero-width space between two selectors had ended the run, so a selector
  run interleaved with zero-width spaces was neither reported as a run nor decoded. The text is read
  from the selectors alone.
- 2026-10-29 (P1, after verification): the text of a run is decoded from its byte selectors alone, so one
  Mongolian selector inside a run no longer hides it from `decoded` (the run was read as spelling
  nothing).
- 2026-10-30: M9 slice B: this step writes its notes through `stagenote`, so a note that names a file or a path from the repository is one line, and a name with a line break cannot pass for a note of its own.
- 2026-10-31: M9 slice C, fix round: `read.metadata` is a line of its own (it handles only the files that carry metadata), so the first line names only checks that handle every file. The findings are unchanged.
- 2026-10-31: M9 slice C, last fix round: `read.divergence` is a line of its own, counted for the files with two readings (it counted every file with the text checks). A test counts the PDF and the DOCX where their metadata is read. The findings are unchanged.
- 2026-11-01: the tag decode moved to `library.tag_texts`, and a tag character between selectors reads as one word in `decoded` ("open"; it read "o p e n", where `02.4-phrases` read "open").

## language

Language shift within Latin script. `02.2-reader`, check `read.language` (2026-10-18).

The phrase patterns are English, so a passage in Spanish or German is unread by `02.4-phrases`, and a
clean result on it means nothing (CHARTER scope). `read.script` catches non-Latin scripts;
this catches non-English text in Latin script. It answers one question, "is this passage
English?", and never names the language: naming needs a model, and a wrong name costs more
than no name. Deterministic, no dependency, no model.

### Method

Words are runs of Latin letters, with one inner apostrophe (`don't`), lowercased; the curly
apostrophe counts as `'`. A word is **English** when it is in `ENGLISH`, a list of English
function words. For each language in `OTHER` (Spanish, Portuguese, French, German, Italian,
Dutch, Swedish, Polish, Turkish, Indonesian, Romanian, Czech, Swahili), a word is **that language's** when it is in its
function-word list and not in `ENGLISH`. Only words of two letters or more count for another
language. `other` is the highest count among those languages, taken per language and never
summed across them, so `de` plus `la` plus `der` from three languages does not add up to one.

A unit of text is flagged when either rule holds:

- **function-words**: at least `MIN_WORDS` (5) words, at least two *distinct* other-language
  words, and `other > english`. Distinct, because one word repeated is usually an acronym or a
  prefix (`MIT License` three times, `SOM`, `non-null`), as measured on 1,109 English skill
  files (below).
- **diacritics** (for languages with no list): a paragraph of at least `MIN_WORDS_DIACRITIC`
  (12) words with `english * 20 < words` (under 5%) and at least 15% of its words carrying a
  letter outside ASCII; or one line of at least `MIN_WORDS_DIACRITIC_LINE` (6) words with no
  English word and at least 30% of its words carrying one.

### Inputs

`passages(lines, markdown) -> list[dict]` takes a file's lines (reading A, original line
order) and whether the file is Markdown.

- Prose is everything outside fenced code blocks (```` ``` ```` or `~~~` fences, in Markdown
  only). A fence that never closes is not a fence: the model reads the rest of the file either
  way, and an unclosed fence must not hide it. Before counting words, a line loses inline code spans, URLs, link targets
  (`](...)`), and HTML tags; the text of an HTML comment is kept, its markers are not.
- A paragraph is a run of prose lines with no blank line and no fence between them.

### Outputs

`passages` returns one dict per flagged unit: `line` (1-based, the unit's first line),
`end_line` (its last line), `rule`, `words` (count), `english`, `other`, and `matched` (the
other-language words in the order met, at most 10; empty for the diacritics rule).

- Every paragraph is tested. A paragraph flagged by function words is one unit, less any
  lines at its start or end with no other-language word (the counts are then the span's), so
  the unit cites the foreign text and not the English around it.
- In a paragraph that is not flagged, each line is tested on its own: the function-words rule
  (paragraphs of two lines or more; a one-line paragraph was already tested) and the line form
  of the diacritics rule, so one Spanish line inside an English paragraph is still found.

`language_findings(file, lines, markdown, line_based=True) -> list[dict]`: one
`read.language` finding per unit: `check`, `file`, `line`, `end_line`, `rule`, `words`,
`english`, `other`, `matched`, and `text` (the unit's lines joined with `\n`, verbatim, cut
at 500 characters with `truncated: true` when longer). When `line_based` is false (PDF, DOCX,
OCR text), `line` is null and `text_line` / `end_text_line` give the lines in the extracted
text.

`stats(lines, markdown) -> dict`: `paragraphs` (prose paragraphs), `judged` (paragraphs with
at least `MIN_WORDS` words), `short` (the rest, too short to judge).

### Measured (2026-10-18)

The four audited repositories at their audited commits: 165 files checked, 4,860 paragraphs
judged, 0 hits.

English base rate: three large public skill repositories (1,109 prose
files, 37,248 paragraphs, 20,574 long enough to judge) plus this repository's docs, stages,
and fixtures (306 files): 6 hits before the distinct-word rule, all a repeated acronym or
prefix; 0 after, and 0 after the lists were widened.

Recall on short instructions written for this check (one line inside an English paragraph):
38 of 42 on the set the lists were tuned on (12 listed languages plus Vietnamese and Swahili,
three lines each), 16 of 24 on a held-out set (12 languages, two lines each), measured before
three plain omissions were fixed (`de` in Portuguese and Romanian, `du` in Swedish). The misses
are lines of five to eight words with one function word or none, mostly Polish, Czech, and
Turkish. A paragraph is easier than a line. The optional `03-sweep` read is the backstop for what this
misses.

### Must never

- Flag an English passage for one borrowed word or a single quoted phrase (`de facto`,
  `café`, `per se`).
- Count words inside a fenced code block, inline code, or a URL.
- Name, translate, or interpret the passage.
- Add a word to another language's list when it is an English word too (`die`, `was`,
  `men`, `son`, `plus`, `come`, `non`), or when it is common in technical English text (`com`, `em`,
  `es`, `var`, `van`, `en`, `et`, `op`, `sin`, `pro`).

### Done when (each backed by a test in `tests/test_language.py`)

1. A Spanish line inside an English bullet list is one function-words unit at its line, with
   the Spanish words in `matched`.
2. A German paragraph hard-wrapped over three lines is one unit, `line` to `end_line`; a flagged
   list paragraph whose first and last items are short English lines cites only the middle line.
3. English prose, a terse English command list, and English with `de facto`, `café`, and
   `per se` give no units.
4. Spanish inside a fenced code block, inline code, or a URL gives no units; Spanish after a
   fence that never closes is a unit.
5. A word repeated (`MIT` three times, `non`) is not two distinct words.
6. A paragraph in a language with no list and heavy diacritics (Vietnamese) is a diacritics
   unit; the same words without diacritics are not; one Vietnamese line inside an English
   paragraph is a diacritics unit at its line, and a line of accented names is not.
7. Words from three different languages (`de`, `la`, `der`) in an English line are not added
   together.
8. `language_findings` carries the contract fields, cuts long text, and uses `text_line` when
   not line-based.
9. `stats` counts paragraphs and the ones too short to judge.

## read_docx

DOCX readings A and B and core properties. `02.2-reader`, checks `read.divergence`,
`read.metadata`, and `read.unread` for DOCX.

### Inputs

The bytes of one DOCX file (a ZIP package).

### Outputs

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

### Must never

- Run macros, follow external relationships, or fetch a URL.
- Interpret the text.

### Done when (each backed by a test in `tests/test_read_docx.py`)

1. A `w:vanish` run is reported as `vanish`; the visible paragraph is not.
2. A white run (`w:color FFFFFF`) is reported as `white-on-white`; a white run on black shading is not.
3. A paragraph style with `w:vanish` hides its runs; a direct `w:vanish w:val="0"` overrides it.
4. `lines` holds one entry per paragraph including hidden text.
5. Core properties with text are reported by local name; empty ones are not.
6. Bytes that are not a ZIP give `unread`.

## read_html

HTML readings A and B from static style. `02.2-reader`, check `read.divergence` for
HTML. Nothing in the page runs; no URL is fetched.

### Inputs

The decoded text of one HTML file.

### Outputs

`read_html(text) -> {"divergences": [...], "painted": [str]}`.

Reading A is all DOM text plus comments and the attributes `alt`, `title`,
`aria-label`. Reading B is the text a browser would paint, from static style:

- Style sources: `<style>` rules (selectors matched with soupsieve, cascade by
  specificity then source order; at-rules skipped) and inline `style`
  attributes (win over rules). Unmatchable selectors are ignored.
- An element is not painted when it or an ancestor has `display:none`,
  `visibility:hidden` (inherited, a child may set `visible`), the `hidden`
  attribute, `opacity:0`, or `font-size:0`; or its text color (inherited,
  default black) `hides` against its effective background (nearest ancestor
  or self with a background color, default white) per `colors.py`.
- CSS variables (2026-10-21): custom properties (`--name`) inherit down the tree as in CSS,
  and `var(--name)` / `var(--name, fallback)` in `color`, `background`, or `background-color`
  resolves against them. A color or background an element declares that still cannot be read
  (a variable nobody defines, a gradient, an image, `currentColor`) is **unknown**, inherited as
  such, and an unknown color or background never makes a color claim: Walkdown cannot say the
  text is hidden when it cannot say what is under it (an outside tester's
  `button{background:var(--acc);color:#fff}` was reported white-on-white against the page).
- `<head>` content, `<title>`, `<script>`, `<template>`, and `<noscript>` are
  not painted. `<style>` content is CSS, not text, and is in neither reading.

Each divergence is `{line, text, carrier}` (reading `A-only`): `text` is the
hidden text with whitespace runs collapsed to one space; `line` the source line
of the element (or of the comment); carriers `display:none`,
`visibility:hidden`, `hidden`, `opacity:0`, `font-size:0`, `white-on-white` /
`color-matches-background` / `transparent`, `comment`, `alt`, `title`,
`aria-label`, `script`, `document-title`, `head`, `template`, `noscript`.
Consecutive hidden text under the same hiding element is one divergence. A
candidate whose text equals a painted text block is dropped (it is in both
readings).

`painted`: the painted text blocks, whitespace collapsed, in document order.

### Must never

- Run a script, load a stylesheet or image, or fetch a URL.
- Interpret the hidden text.

### Done when (each backed by a test in `tests/test_read_html.py`)

1. A class rule `display:none` and an inline `display:none` hide their text, reported with the element's line.
2. White-on-white via a class rule setting `color` and `background` is reported as `white-on-white`; visible text is not reported.
7. White text on a button whose background is `var(--acc)` (a green defined on `:root`) is not reported; text colored `var(--bg)` with `--bg` white on a white page is `white-on-white`; a background that is a gradient, an image, or an undefined variable makes no color claim.
3. `alt`, `title`, and `aria-label` values and comments are reported with their carriers and lines.
4. `visibility:hidden` on a parent with a `visible` child reports only the parent's own text.
5. A `<title>` equal to a painted heading is not reported; any other `<title>` is reported as `document-title`.
6. The `hidden` attribute is reported; painted text appears in `painted`.

## read_image

Images: metadata and (optionally) OCR. `02.2-reader`, checks `read.metadata`,
`read.divergence`, and `read.unread` for images.

### Inputs

The bytes of one image file (PNG, JPEG, GIF, WebP, BMP, TIFF, ICO).

### Outputs

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

### Must never

- Pass an image whose text was not read: no OCR means a skip, never silence.
- Decode an image beyond Pillow's decompression-bomb limit.

### Done when (each backed by a test in `tests/test_read_image.py`)

1. A PNG with a tEXt chunk reports `png:<keyword>` with its text.
2. A JPEG with an EXIF ImageDescription reports `exif:ImageDescription`.
3. A plain PNG reports no metadata.
4. With OCR disabled or unavailable, `ocr_skipped` is set and `ocr_text` is None.
5. Non-image bytes give `unread`.

### OCR preprocessing (2026-10-04; rebuilt 2026-10-18 from the OCR spike)

`ocr_views(im, enlarge=True) -> list[Image]`: the grayscale views Tesseract reads, in reading
order. `ocr_lines(im, enlarge=True) -> list[(text, confidence)]`: the OCR lines of every view,
in order, each with the median of Tesseract's word confidences (0 to 100); used by
`render_pdf`, which drops low-confidence lines (image OCR keeps every line). `ocr_read(im, enlarge=True) -> str`: their OCR text joined with newlines (the views'
texts in order). Both are used for images and, with `enlarge=False`, for rendered PDF pages
(`render_pdf`): one view of the crop, steps 1, 2 and 5 only, never enlarged or tiled.

1. Grayscale. The **background** is the most common gray value.
2. **Crop** to the pixels that differ from the background by more than `INK` (3), plus a
   `MARGIN` (12 px). An image with no such pixel has no views (no text).
3. A crop under `OCR_SMALL` (2000) px on its longer side is **one view**, enlarged `OCR_SCALE`
   (3) times, but never past `OCR_MAX` (6000) px.
4. A larger crop is read whole first, at its own size, then cut into **tiles** of `TILE`
   (1000) px overlapping by `OVERLAP` (120) px, row by row; a tile with no ink is dropped; each
   tile is enlarged `TILE_SCALE` (2) times. The whole view keeps words in large type that
   straddle a tile overlap (2026-10-18: a 2752 x 1536 banner's title, read whole by the old
   preprocessing, was cut to "Claude Fami" by tiles alone); the tiles add the small text the
   whole view misses. `ocr_read` keeps a line read by more than one view once; a line cut
   differently in two views can still appear twice.
5. Each view's **contrast is stretched** to the full range (`autocontrast`), and a view whose
   background is dark (under 128) is **inverted**, so the text is dark on light. Both happen
   before the view is enlarged. Measured over 60 faint small cases (5 fonts, 7 to 9 px, gray
   170 and 210, two lines, in a 2400 x 1600 image): this order read more words in 13, fewer in
   4, the same in 43 (mean 0.814 against 0.804). One DejaVu case had shown 0.92 against 0.69;
   with Pillow's built-in font the same case goes the other way, so the gain is small and
   font-dependent, not the 23-point gap one case suggested.

Why (`pre-planning/history/02.2-reader/OCR-SPIKE-2026-10-18.md`): small text in a large image was read at its natural size and
missed (9 px text in a 2400 x 1600 image: 64% of words; 8 px light gray: 23%). With crop,
contrast, and tiling: 100% and 92%, and near-invisible text (`#EEE` on white) is still read.
Tiny text is a way to hide an instruction in an image (the first CI run with Tesseract missed
the class 11 fixture's 11-pixel text), and so is faint text.

Done when (tests in `tests/test_read_image.py`):

6. A small image gives one view, grayscale, cropped to its ink and enlarged 3x.
7. A blank image gives no views.
8. A dark image gives a view whose background is light.
9. A large image with ink in two far corners gives the whole crop, then tiles for those
   corners only.
10. A view never exceeds `OCR_MAX` on its longer side.
12. `enlarge=False` gives one view the size of the crop, however large.
13. With Tesseract installed: a word in large type across a tile overlap of a large image is
    read whole, and a line read by two views appears once.
11. With Tesseract installed: 9 px text in the corner of a 2400 x 1600 image, `#EEE` text on
    white, and 8 px light-gray text in a 2400 x 1600 image are read (most of their words in
    `ocr_read`), drawn with Pillow's built-in font so the test runs on any OS. The bars test
    that the text is read at all (the old preprocessing read 64% and 23% of such words), not one
    Tesseract version's exact score.

## read_md

Markdown reading B: content present in the raw text (reading A) that a
rendered view does not show. `02.2-reader`, check `read.divergence` for markdown.

### Inputs

The decoded text of one markdown file.

### Outputs

`carriers(text) -> list[dict]`, each `{line, text, carrier}` (line 1-based in
the original, where the hidden content starts, or for an HTML element or
attribute the line of its opening tag; `text` the hidden content
verbatim, surrounding whitespace stripped), sorted by position:

| Carrier | What |
|---|---|
| `comment` | HTML comment `<!-- ... -->`; `text` is the inner content. Unterminated: to end of file. Empty comments are skipped |
| `details` | `<details>` body (minus its `<summary>`) when the element has no `open` attribute |
| `hidden` / `display:none` / `visibility:hidden` / `font-size:0` / `opacity:0` | an inline HTML element with the `hidden` attribute or that inline style; `text` is its inner content |
| `alt` | image alt text, markdown `![alt](...)` / `![alt][ref]` or HTML `alt="..."` |
| `link-title` | the title of an inline link or image, `[t](url "title")` |
| `title` | an HTML `title="..."` attribute |
| `reference-definition` | a reference-style link definition line `[label]: url "title"` (footnotes `[^x]:` excluded); `text` the line; extra `used`: whether `[label]` is referenced elsewhere |

Nothing inside a fenced code block, an inline code span, or the YAML
frontmatter at the top of the file is a carrier: a render shows code verbatim.

`comment_count(text) -> int`: the number of `comment` carriers (for the Case
001 comparison).

### Must never

- Report content inside code fences or inline code.
- Interpret the hidden content.

### Done when (each backed by a test in `tests/test_read_md.py`)

1. A one-line and a multi-line comment are reported with their start lines and inner text.
2. A comment inside a fenced code block and inside an inline code span is not reported.
3. A closed `<details>` body is reported without its summary; an `open` one is not.
4. A `<div hidden>` and a `<span style="display:none">` are reported with their carriers.
5. Image alt text, a link title, and an HTML title attribute are reported.
6. A reference definition is reported with `used` true when referenced and false when not; a footnote definition is not reported.
7. Frontmatter is not scanned; `comment_count` counts comments.

## read_pdf

PDF readings A and B and PDF metadata. `02.2-reader`, checks `read.divergence`,
`read.metadata`, and `read.unread` for PDF.

### Inputs

The bytes of one PDF file.

### Outputs

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

The other direction, text painted on the page but absent from the text layer, is
`render_pdf` (pages drawn by pypdfium2 and read by Tesseract, 2026-10-18); run.py
compares the two.

### Must never

- Run PDF JavaScript, open embedded files, or fetch a URL.
- Interpret the text.

### Done when (each backed by a test in `tests/test_read_pdf.py`)

1. A PDF with black and white text on a white page gives both lines in `lines` and one `white-on-white` divergence for the white text only.
2. Text in render mode 3 gives `render-mode-invisible`.
3. White text on a black filled rectangle is not reported.
4. Info dictionary entries with text (Title, Keywords, Author) are reported verbatim; empty ones are not.
5. Bytes that are not a PDF give `unread` with a reason and no exception.

## read_svg

SVG readings A and B. `02.2-reader`, check `read.divergence` for SVG. SVG is XML
text, not an unread image.

### Inputs

The bytes of one SVG file.

### Outputs

`read_svg(data) -> {"divergences": [...], "painted": [str]}`, or raises
`SvgError` when the XML is not well-formed.

Parsed with lxml with entity resolution, DTD loading, and network access off.
Reading A: every text node, including `<title>`, `<desc>`, `<metadata>`,
`<script>`, comments (also those before the root element), and every `<text>`.
Reading B: painted `<text>` only.

A `<text>` element (with its `tspan` / `textPath` content) is not painted when:

- it sits inside `defs`, `symbol`, `clipPath`, `mask`, `pattern`, or `marker`
  (carrier `defs`);
- it or an ancestor has `display` `none` or `visibility` `hidden` (attribute
  or inline style; carriers `display:none`, `visibility:hidden`), or `opacity`
  / `fill-opacity` 0 (carrier `opacity:0`);
- its fill (attribute or inline style, inherited, default black) is `none`
  (carrier `fill:none`), transparent (carrier `transparent`), or `hides`
  against the background (carriers from `colors.carrier`).

The background at a `<text>` is the fill of the last `<rect>` earlier in the
document (outside `defs`) that covers the text's `x, y` (percent sizes count as
covering), else white.

Divergences are `{line, text, carrier}`, reading `A-only`, `text` with
whitespace collapsed, carriers also `title`, `desc`, `metadata`, `script`,
`comment`, and `not-rendered` (character data outside any `<text>`, which SVG
does not draw; text in `foreignObject` counts as painted). `<style>` content is
CSS and in neither reading; class-based SVG styling is not resolved in v1. A
candidate whose text equals a painted text is dropped. A comment's `line` is its
first line (lxml's `sourceline` of a comment is its last).

### Must never

- Resolve entities, load a DTD, fetch a URL, or run a script.
- Interpret the hidden text.

### Done when (each backed by a test in `tests/test_read_svg.py`)

1. Title, desc, metadata, script, and a comment before the root are reported with carriers and lines.
2. `<text fill="none">`, a transparent fill, and white text on a white page are reported; black text is painted.
3. White text over a covering `#eee` rect is reported; white text over a covering black rect is painted.
4. Text in `defs` and text with `display:none` in style are reported.
5. A title equal to a painted text is dropped; malformed XML raises `SvgError`; an entity declaration is not expanded.
6. A comment names its first line, before the root, inside it, and after it (`test_a_comment_names_its_first_line`).

### History

- 2026-11-01: a multi-line comment's `line` is its first line. It named its last, so the words above it were outside the lines the mask of a flagged line goes by.

## render_html

Added 2026-10-20.

HTML as a browser draws it. `02.2-reader`'s static reader (`read_html.py`) works out what is painted
from inline style and `<style>` rules; a browser also applies `@media` rules (and the CSS variables set inside them),
selectors the static matcher cannot run, positioning, clipping, and elements drawn over others,
and shows text that a style sheet adds with `::before` and `::after`. This module draws each
HTML file in a headless Chromium and reports what a person would and would not see. It was the
last check listed as "not built".

### Inputs

- The input folder (the run's root) and each HTML file's path in it.
- The file's text and the static reader's divergences (to leave out what it already found).

Optional: Playwright and its Chromium (`pip install playwright`, then
`python -m playwright install chromium-headless-shell`). `available()` checks without starting a
browser: the package is importable and the Chromium build it launches is installed, read from
the package's own `browsers.json` (`chromium_headless_shell-<revision>`; 2026-10-21: any
Chromium was enough before, so a build for another Playwright version passed the check and then
failed on every page). A Chromium for another version gives its own reason. When
`browsers.json` cannot be read, any Chromium counts, as before; `PLAYWRIGHT_BROWSERS_PATH` `0`
means the bundled browsers. Without them every HTML file gets a skip. A browser that does not
start gives a skip whose reason is the error's first line only.

### How a page is drawn

- One browser per `02.2-reader` run (`Session`), started at the first HTML file and closed at the
  end; a fresh browser context per file.
- The page's own JavaScript is off; the context is offline; downloads and service workers are
  off; every request is aborted unless it is a `file:` URL inside the input folder, so a page can
  load its own style sheets and images from the repository and nothing else.
- The page is loaded from its file (a 1280 x 800 window, 10 s limit), then a fixed probe runs in
  it. With the page's scripts off, the functions the probe calls are the browser's own.
- At most `MAX_FILES` (200) files are drawn per run; the rest get a skip saying so.

### Outputs

The probe returns, for each text node under `<body>` that a person would not see, its text and
`how` (checked in this order):

| `how` | Meaning |
|---|---|
| `collapsed` | inside a closed `<details>`, outside its summary: on screen only after the reader opens it (one item per section) |
| `not-rendered` | no box at all (`display:none`, including inside `@media`, and the like) |
| `invisible` | `visibility` is not `visible` |
| `transparent` | the element or an ancestor has opacity 0 |
| `zero-size` | every box is under 1 px wide or high |
| `tiny-text` | font size under 2 px |
| `off-page` | every box lies outside the page (left of 0, above 0, or past its width or height) |
| `clipped-or-covered` | at the middle of each box the browser finds another element: the text is clipped by an ancestor or covered (not tested when the text ignores the pointer) |
| `transparent-text` | the text color has alpha 0 |
| `color-matches-background` | contrast with the nearest background color under 1.15 (not judged over a background image) |

and each plain string a `::before` or `::after` adds (three letters or more; counters, `attr()`
and images are not read) as `how` `css-content`.

Form controls (`select`, `option`, `optgroup`, `datalist`, `textarea`) and everything in
`head`, `script`, `style`, `template`, `noscript`, `title` are left out.

`divergences(probe, source, static_texts)` turns that into `{line, text, how, reading}`: hidden
text is `A-only` (the model reads it, a person does not), consecutive text of one element hidden
the same way is one item, and any text that the static reader already reported (either text
inside the other) is left out; generated text is `B-only` with `pseudo`. `line` is where the text
starts in the source (`line_of`: the whole text, its first 40 characters, or its first words with
tags, entities, or white space between), or null.

`02.2-reader` (`run.html_drawn`) reports each as `read.divergence` with `carrier` `rendered`,
`method` `render`, and `how`. A file not drawn gets a skip with `carrier` `rendered`
(`html not drawn (<why>)`), so the grader skips only the rows about drawn HTML. Coverage gains
`html: {files, drawn}`; without Playwright, `not_examined` lists "HTML as a browser draws it" and
the notes say so.

### Must never

- Run the page's scripts, fetch anything from the network, or read a file outside the input
  folder.
- Report again what static style found.
- Judge what the hidden text means.

### Done when (tests in `tests/test_render_html.py`)

1. (`available` is `stages/_shared/playwright_check.py`'s since restructure step 7, and its tests are there; `render_html.available` is that function.) `available` is false without the package or without a Chromium, with the reason; with a Chromium build for another Playwright version it is false and says so, and with the build `browsers.json` names it is true.
2. `line_of` finds the line by the whole text, by its start, and across tags and entities, and
   gives null when the text is not in the source.
3. `divergences` merges one element's text, leaves out what static style found (either way),
   and reports generated text as `B-only`.
4. The request filter lets through only `file:` URLs inside the input folder.
5. With Playwright present: text off the page, clipped, hidden by `@media`, colored like the page
   through a CSS variable set in an `@media` rule, covered, and in a closed `<details>` (its summary visible) is found with
   the right `how`; text a `::after` adds is
   `B-only`; visible text and text far down a long page are not reported; a page script that
   would reveal or add text does not run.
6. Without Playwright, an HTML file gets the `rendered` skip and the run says so (`tests/test_run.py`).

Measured 2026-10-20: Compound Engineering at 7a68002, 10 HTML files, 6 findings, all closed
`<details>` sections in plan pages (before `collapsed` existed, the same text gave 114
`clipped-or-covered` findings, one per text node: Chrome lays a closed section out and paints
nothing there); a second repository, 1 file, none.

Fixture: `Fixtures/02.2-reader/class11-html-render.html` (grader rows `rd-render-*`; the drawn rows
are skipped without Playwright).

- 2026-10-29: restructure step 7: `available` and its helpers moved to `stages/_shared/playwright_check.py` (notes M13); this module imports them.

## render_pdf

PDF pages drawn and read as images (2026-10-18). `02.2-reader`, `read.divergence` (carrier
`image-text`, method `ocr`) and the reading of a PDF that has no text layer.

The text layer is what a parser hands a model; a page as drawn can carry more: a screenshot of
an instruction, text drawn as shapes, a scanned page. A model that reads the page as an image
sees it. Reading the text layer alone misses it.

### Inputs

The bytes of one PDF file, and the PDF's text layer (`read_pdf` lines).

### Outputs

`page_ocr(data, max_pages=MAX_PAGES) -> PageOcr` with:

- `pages`: one OCR text per page read, in page order. Each page is rendered by **pypdfium2**
  (core dependency, pip, BSD-3-Clause / Apache-2.0; no poppler) at `RENDER_SCALE` (3, which is
  216 dpi, so 6 pt text is 18 px), then read by `read_image.ocr_views(..., enlarge=False)` and
  Tesseract: cropped to the ink, contrast stretched, dark pages inverted, not enlarged and not
  tiled (a rendered page's text is already large enough). Only lines whose median word
  confidence is `CONF` (70) or more are kept; `low` holds the rest, per page, so the runner can
  count what was set aside (`reading.pdf_pages.low_confidence`: unseen lines set aside).
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

### Measured (2026-10-18)

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

### Must never

- Run PDF JavaScript, open an embedded file, or fetch a URL (pypdfium2 renders; forms and
  JavaScript are not initialized).
- Report a page as clean when it was not read: no Tesseract, a render error, or a page past
  the cap is a skip.
- Call text unseen for one misread word: an OCR slip of a word in the layer is still seen.

### Done when (each backed by a test in `tests/test_render_pdf.py`)

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

## script_runs

Language / script shift. `02.2-reader`, check `read.script`.

### Inputs

One line of decoded text.

### Outputs

`script_of(ch) -> str`: the Unicode Script property value of one character, by
long name (`Latin`, `Cyrillic`, `Greek`, `Han`, `Common`, `Inherited`, ...), via
the `regex` module's `\p{Script=...}`. `Unknown` when none matches.

`runs(line) -> list[dict]` with `script`, `text`, and `col` (0-based start):

- Only letters (general category `L*`) open or extend a run.
- A letter whose script is Latin, Common, Inherited, or Unknown closes any
  open run and opens none.
- A letter of another script extends the open run when the scripts match, and
  otherwise closes it and opens a new run.
- Non-letters (spaces, digits, punctuation, marks) neither open nor close a
  run. A run's `text` spans from its first letter to its last letter, verbatim.

`script_findings(file, line_no, line) -> list[dict]`: one `read.script`
finding per run (`check`, `file`, `line`, `script`, `text`, plus `col`).

Language shift within Latin script is `language.py` (`read.language`), not this
check.

### Must never

- Flag accented Latin letters (`café`) or plain ASCII.
- Interpret or translate the run.

### Done when (each backed by a test in `tests/test_script_runs.py`)

1. `script_of` gives Latin, Cyrillic, Greek, Han, Common for sample characters.
2. A Cyrillic sentence with spaces is one run; Latin letters in the middle (`.env`) split it into two runs, each trimmed to its letters.
3. Accented Latin and ASCII give no runs.
4. Adjacent Greek and Cyrillic words give two runs with their own scripts.
5. `script_findings` carries `check`, `file`, `line`, `script`, `text`.
