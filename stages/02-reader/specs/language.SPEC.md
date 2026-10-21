# language.py: spec

Language shift within Latin script. Stage 2, check `read.language` (2026-10-18).

The phrase patterns are English, so a passage in Spanish or German is unread by stage 4, and a
clean result on it means nothing (CHARTER scope). `read.script` catches non-Latin scripts;
this catches non-English text in Latin script. It answers one question, "is this passage
English?", and never names the language: naming needs a model, and a wrong name costs more
than no name. Deterministic, no dependency, no model.

## Method

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

## Inputs

`passages(lines, markdown) -> list[dict]` takes a file's lines (reading A, original line
order) and whether the file is Markdown.

- Prose is everything outside fenced code blocks (```` ``` ```` or `~~~` fences, in Markdown
  only). A fence that never closes is not a fence: the model reads the rest of the file either
  way, and an unclosed fence must not hide it. Before counting words, a line loses inline code spans, URLs, link targets
  (`](...)`), and HTML tags; the text of an HTML comment is kept, its markers are not.
- A paragraph is a run of prose lines with no blank line and no fence between them.

## Outputs

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

## Measured (2026-10-18)

The four audited repositories at their audited commits (superpowers v6.3.0, Plumbline
`28295e9`, claude-familiar `6ce7504`, backlog `b449d9f`): 165 files checked, 4,860 paragraphs
judged, 0 hits.

English base rate: obra/superpowers, anthropics/skills, and wshobson/agents (1,109 prose
files, 37,248 paragraphs, 20,574 long enough to judge) plus this repository's docs, stages,
and fixtures (306 files): 6 hits before the distinct-word rule, all a repeated acronym or
prefix; 0 after, and 0 after the lists were widened.

Recall on short instructions written for this check (one line inside an English paragraph):
38 of 42 on the set the lists were tuned on (12 listed languages plus Vietnamese and Swahili,
three lines each), 16 of 24 on a held-out set (12 languages, two lines each), measured before
three plain omissions were fixed (`de` in Portuguese and Romanian, `du` in Swedish). The misses
are lines of five to eight words with one function word or none, mostly Polish, Czech, and
Turkish. A paragraph is easier than a line. Stage 6's sweep is the backstop for what this
misses.

## Must never

- Flag an English passage for one borrowed word or a single quoted phrase (`de facto`,
  `café`, `per se`).
- Count words inside a fenced code block, inline code, or a URL.
- Name, translate, or interpret the passage.
- Add a word to another language's list when it is an English word too (`die`, `was`,
  `men`, `son`, `plus`, `come`, `non`), or when it is common in technical English text (`com`, `em`,
  `es`, `var`, `van`, `en`, `et`, `op`, `sin`, `pro`).

## Done when (each backed by a test in `tests/test_language.py`)

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
