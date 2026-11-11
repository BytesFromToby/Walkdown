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
| markdown, html, svg, text | decoded text, original lines | `read.fold` and `read.script` per line; `read.divergence` for invisible characters per line (`fold.invisible_finding`); plus markdown carriers (`read_md`), HTML (`read_html`, with the style sheets the file links in the input folder: `css_loader`), or SVG (`read_svg`) divergences; `read.language` (`language.language_findings`) for markdown and for text files with a prose extension (`txt`, `text`, `rst`, `adoc`, `asciidoc`) |
| pdf | `read_pdf` lines | `read.fold` / `read.script` / `read.language` over those lines; static divergences; `read.metadata`. A PDF with no text layer is `read.unread`, "pdf: no text layer; the text on its pages is not examined" (R35) |
| docx | `read_docx` lines | same as pdf |
| image | none | `read.metadata`; and `read.unread`, "image: the text drawn in it is not examined (its metadata is read)" (R35): one reading, so no divergence and no language check |
| office-other, archive, binary | none | `read.unread` with the reason |
| symlink | none | `read.unread` (`symlink, not followed`, plus `target`) |

Every `read.divergence` carries `reading`, `text`, `carrier`, `method`
(`static-style`; `ocr` and `render` in runs made before R35 and R36). Text formats use the original line number in `line`.
A `css-content` divergence (text a style sheet adds, `B-only`) also has `pseudo`, `before` or `after`.
In a text format, a divergence whose text reaches past its first line also has `end_line`, the last line it reaches
(`reach`: its words found in order from `line`, in each line as written and with its entities decoded). The mask of a line the
secret scan flags needs it (`stages/_shared/secretmask.py`), since a parser's text has lost its line breaks, stripped or
collapsed. A word that cannot be found (tags between its letters glue it, a style sheet made it) leaves the reach unknown, so
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
paragraphs too `short` to judge), `images` (images seen), `pdf_no_text_layer` (PDFs with none),
`html` (`files` HTML files seen, `css_files` linked style sheets read), and
`not_examined`: what this run does not examine in the repository's files (the three notes below), and any check in
`NOT_BUILT` with "(not built)". `pdf_pages`, `optional_tools`, and `html.drawn` left with R35 and R36 (2026-11-11).

stderr: notes. What the step does not examine, one note each and only when the repository has such a file (R35, R36;
owner 2026-11-11: "We state we do not examine images"; the report lists them under What this run covered):
`note: not examined: the text drawn inside images (<n> images); their metadata is read`,
`note: not examined: the text on PDF pages that are only a picture (<n> PDFs with no text layer)`, and
`note: not examined: how a web page looks once drawn (<n> HTML files): one element drawn over another, clipping that
depends on where things land, text over a background image; the page's own styles are read`. One `note: not built:`
line for each check in `NOT_BUILT` (empty since 2026-10-20), and one `note: v1 limit:` line saying what the language check
does not read (code, config, HTML, paragraphs under five words). No check waits on an installed program: Walkdown installs
with pip and nothing else, so a run reads the same on every machine.

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
- Read a style sheet from outside the input folder or from a URL (`css_loader` gives None for either).

### Done when (each backed by a test in `tests/test_run.py`)

1. On a small mixed folder, stdout parses as a contract-1 report with stage `02.2-reader`, and the exit code is 0.
2. A markdown file with a zero-width line, a comment, and a Cyrillic line gives `read.fold`, `read.divergence` (invisible and comment), and `read.script` findings at the right lines.
3. An HTML file with a `display:none` div gives a `display:none` divergence with method `static-style`.
4. A PNG gives a `read.unread` finding saying the text drawn in it is not examined, no skip, and the run's note with the
   count; an unknown binary gives `read.unread` (`test_an_image_is_unread_and_its_drawn_text_not_examined`).
5. `--out` writes text and folded files with equal line counts, and folded lines differ only where `read.fold` fired.
6. `--out` inside the input exits non-zero; the input folder is byte-identical after a run.
7. A missing folder exits non-zero without printing a report.
8. A markdown file with a Spanish line in an English list gives one `read.language` finding at that line; the same line in a `.py` file gives none; a PDF line gives one with `text_line`; `reading.language` counts files and paragraphs; stderr has no `not built: language` line and has the language `v1 limit` line.
9. A PDF with no text layer is `read.unread` saying the text on its pages is not examined, with no skip, and the run's
   note counts it (`test_a_pdf_with_no_text_layer_is_unread_and_its_pages_not_examined`).
11. An HTML file is read with the style sheets it links in the input folder and never one outside it or at a URL; no
    check is skipped; the run's note says how a page looks once drawn is not examined
    (`test_html_is_read_from_its_styles_and_its_linked_sheets_inside_the_folder_only`).

10. Hidden text that reaches past its first line says how far, in Markdown, HTML, and SVG (`test_hidden_text_that_reaches_past_its_first_line_says_how_far`, `test_a_markdown_comment_keeps_an_entity_as_written`); one-line hidden text and a line of hidden characters have no `end_line` (`test_a_line_of_hidden_characters_has_no_reach`); a word that cannot be placed runs to the end of the file (`test_a_word_that_cannot_be_placed_runs_to_the_end_of_the_file`).

### History

- 2026-11-01: `end_line` on a divergence that reaches past its first line, for the mask of a flagged line. `02.5-capability` still goes by the line breaks in `text`, as it did.
- 2026-11-11 (owner, R35 and R36: "Tesseract removal I think is fine. We state we do not examine images."; "go with option
  1"): no OCR program and no browser. `render_pdf.py` (PDF pages drawn by pypdfium2 and read by Tesseract, 2026-10-18) and
  `render_html.py` (HTML drawn in Playwright's Chromium, 2026-10-20), with `optional_tools`, are gone; an image and a PDF
  with no text layer are `read.unread` with a reason that says what is not examined; `read_html` reads what style alone can
  tell (its section), with the linked style sheets in the input folder (`css_loader`); the step says, in a note each, what
  it does not examine in the repository's files. No check is skipped for a missing tool any more, so the step is never
  INCOMPLETE for one. Grader: the drawn-HTML rows moved to the static carriers; the covered paragraph is a recall row
  (only drawing finds it); the OCR rows of a picture on a PDF page are retired.

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
- `read.divergence`: `of` is the files with two readings (Markdown, HTML, SVG, a PDF, a DOCX: `DIVERGENCE_KINDS`; a picture
  has one since R35, its metadata);
  `looked_at` is counted in the branch of each, where its readings are set against each other; `explained` is such a file that is
  unread before that. A plain text or script file has one reading and is not one of them.
- `read.metadata`: `of` is the PDFs, DOCX files, and images (the files that carry metadata); `looked_at` is counted where the
  metadata is read; `explained` is such a file that is unread before its metadata was read.
- `read.language`: `of` is the files the language check is to judge (Markdown, plain-text prose, and the text of a PDF or a
  DOCX: `prose_candidate`; an image is no prose since R35); `looked_at` is counted inside `language_checks`; `explained` is such a file that is unread before the
  check ran.

An image is such a file: its text drawn in it is not examined (R35), and it is explained by its `read.unread` row, a limit
and no gap. A file a branch passes over without a finding or a skip leaves a line short.
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
at 500 characters with `truncated: true` when longer). When `line_based` is false (PDF,
DOCX), `line` is null and `text_line` / `end_text_line` give the lines in the extracted
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

Since R36 (owner, 2026-11-11: "go with option 1": teach the static reader, drop the browser) it does what the browser check
did where style alone can tell; how a page looks once drawn (one element over another, clipping that depends on where
things land, contrast over a background image) is not examined, and the run says so.

### Inputs

The decoded text of one HTML file.

### Outputs

`read_html(text, load_css=None) -> {"divergences": [...], "painted": [str]}`. `load_css(href) -> str | None`: the text of
a style sheet the page links, read from the input folder by the caller (`run.css_loader`), or None; it fetches nothing.

Reading A is all DOM text plus comments and the attributes `alt`, `title`,
`aria-label`. Reading B is the text a browser would paint, from static style:

- Style sources, in document order: `<style>` rules and, with `load_css`, the `<link rel="stylesheet">` files of the
  repository (up to `CSS_CAP`, 1 MB, each); a `media` attribute that does not hold on the screen leaves its sheet out.
  Selectors matched with soupsieve, cascade by importance, then specificity, then source order; inline `style`
  attributes win over rules. Unmatchable selectors are ignored.
- `@media` (R36): its rules apply when its query holds on one screen, `SCREEN` (1280 x 800, light, landscape, a mouse,
  as the browser check drew it): `all` and `screen` hold, `print` and other types do not; `not` and `only`; `min-` and
  `max-width` and `-height` (px, pt, em, rem, vw, vh), the range forms (`width >= 1000px`), `orientation`,
  `prefers-color-scheme`, `hover`, `pointer`, and the like (`media_matches`). A query with a feature Walkdown does not
  know does not hold, so a rule in it makes no claim (as an unknown color makes none). `@supports` rules apply; every
  other at-rule is skipped.
- An element is not painted when it or an ancestor has `display:none`,
  `visibility:hidden` (inherited, a child may set `visible`), the `hidden`
  attribute, `opacity:0`, or `font-size:0`; or its text color (inherited,
  default black) `hides` against its effective background (nearest ancestor
  or self with a background color, default white) per `colors.py`.
- Since R36, also: text placed **off the page** (`off_page`: an absolutely or fixed positioned box with `left`, `top`,
  `right`, or `bottom` 1,000 px or more negative, `FAR_PX`; a `text-indent`, `margin-left`, or `margin-top` that far
  negative; a `translate` that far), **clipped** away (`clipped`: `clip` to a rectangle with no area on a positioned box,
  `clip-path: inset(50%)` or more, `circle(0)`), in a box with **no size** (`zero_size`: `width`, `height`, `max-width`,
  or `max-height` 1 px or less with `overflow` hidden or clip, or a `scale(0)`), and inside a closed `<details>` outside
  its `<summary>`. Each holds for the element's children too, as `display:none` does. The usual screen-reader-only class
  (absolute, 1 px, overflow hidden, `clip: rect(0 0 0 0)`) is `clipped`.
- Font size (R36) is followed down the tree from 16 px (`font_px`: px, pt, em, rem, %, keywords, `smaller` and
  `larger`); text under 2 px (`TINY_PX`) is `tiny-text`. A size Walkdown cannot read (`calc()`) makes no claim.
- Text a style sheet adds (R36): the plain strings of a `::before` or `::after` `content` (one or two colons; counters,
  `attr()`, and images are not read; CSS escapes are decoded) with three letters or more, on an element that is shown, is a
  `B-only` divergence with carrier `css-content` and `pseudo` `before` or `after`: a person sees it, the model reading the
  page's text does not.
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
`aria-label`, `script`, `document-title`, `head`, `template`, `noscript`, and since R36 `off-page`, `clipped`,
`zero-size`, `tiny-text`, `details`, and `css-content` (`B-only`).
Consecutive hidden text under the same hiding element is one divergence. A
candidate whose text equals a painted text block is dropped (it is in both
readings).

`painted`: the painted text blocks, whitespace collapsed, in document order.

### Must never

- Run a script, load an image, or fetch a URL; read a style sheet other than through `load_css`.
- Interpret the hidden text.
- Claim text is hidden by a media query, a size, or a color it cannot read.

### Done when (each backed by a test in `tests/test_read_html.py`)

1. A class rule `display:none` and an inline `display:none` hide their text, reported with the element's line.
2. White-on-white via a class rule setting `color` and `background` is reported as `white-on-white`; visible text is not reported.
7. White text on a button whose background is `var(--acc)` (a green defined on `:root`) is not reported; text colored `var(--bg)` with `--bg` white on a white page is `white-on-white`; a background that is a gradient, an image, or an undefined variable makes no color claim.
3. `alt`, `title`, and `aria-label` values and comments are reported with their carriers and lines.
4. `visibility:hidden` on a parent with a `visible` child reports only the parent's own text.
5. A `<title>` equal to a painted heading is not reported; any other `<title>` is reported as `document-title`.
6. The `hidden` attribute is reported; painted text appears in `painted`.
8. A linked style sheet from the repository is read; with no loader only the page's own styles are; a print sheet does
   not apply (`test_a_linked_style_sheet_from_the_repository_is_read_and_a_url_is_not_fetched`).
9. `@media` rules apply for the one screen, and a query with an unknown feature makes no claim
   (`test_media_rules_apply_for_one_screen_and_an_unknown_feature_makes_no_claim`).
10. Text a style sheet adds before or after an element is `css-content`, `B-only`, with `pseudo`; under three letters, on a
    hidden element, or from a counter or `attr()` it is not (`test_text_a_style_sheet_adds_before_or_after_an_element`).
11. Text under 2 px is `tiny-text` (`test_text_under_two_pixels_is_tiny`).
12. Text placed off the page, clipped away, or in a box with no size is reported, and a small nudge or a zero width that
    lets text spill is not (`test_text_placed_off_the_page_clipped_away_or_in_a_box_with_no_size`); a visually hidden
    class hides its children (`test_a_visually_hidden_class_hides_its_children_too`).
13. Text in a closed `<details>` outside its summary is `details`; an open one is shown
    (`test_text_in_a_closed_details_outside_its_summary`).

## read_image

Images: their metadata. `02.2-reader`, checks `read.metadata` and `read.unread` for images.

The text drawn inside an image is not examined (R35, owner 2026-11-11: "Tesseract removal I think is fine. We state we do
not examine images."): Walkdown installs with pip and nothing else, and reading pixels took a program installed apart.

### Inputs

The bytes of one image file (PNG, JPEG, GIF, WebP, BMP, TIFF, ICO).

### Outputs

`read_image(data) -> ImageReading` with:

- `metadata`: `{field, text}`, verbatim, non-empty only:
  - PNG text chunks (tEXt, zTXt, iTXt): `field` `png:<keyword>`;
  - EXIF tags with string (or decodable byte) values, including the Exif
    sub-IFD (UserComment, etc.): `field` `exif:<TagName>`;
  - JPEG / GIF comments: `field` `comment`.
  Byte values are decoded as UTF-8 (then Latin-1); an EXIF UserComment drops
  its 8-byte character-code prefix. Values that are not text are skipped.
- `unread`: None, or the reason Pillow could not open the image.

`NOT_EXAMINED`, "image: the text drawn in it is not examined (its metadata is read)": the reason run.py gives every
readable image's `read.unread`, so the image is a file no tests are run on, and says why.

### Must never

- Pass an image as read: the text drawn in it is not examined, and its `read.unread` says so.
- Decode an image beyond Pillow's decompression-bomb limit.

### Done when (each backed by a test in `tests/test_read_image.py`)

1. A PNG with a tEXt chunk reports `png:<keyword>` with its text.
2. A JPEG with an EXIF ImageDescription reports `exif:ImageDescription`.
3. A plain PNG reports no metadata.
4. Non-image bytes give `unread`.
5. There is no OCR, and the reason says the text drawn in an image is not examined
   (`test_the_text_drawn_in_an_image_is_not_examined`).

### History

- 2026-10-04 to 2026-11-11: OCR with Tesseract, its preprocessing rebuilt 2026-10-18 from the OCR spike
  (`pre-planning/history/02.2-reader/OCR-SPIKE-2026-10-18.md`). Removed by R35; git history keeps it.

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

The other direction, text painted on the page but absent from the text layer, is not examined since R35 (2026-11-11);
`render_pdf` drew and read the pages with Tesseract from 2026-10-18 until then.

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
