# review_html.py and plain.py: spec

A page for walking the flagged places one at a time and marking each (review C21, owner
2026-10-08; built 2026-10-12). The D3 labeling page worked as a way to walk flagged lines one
by one; this gives the report reader the same. Walkdown still renders no verdict: the reader
makes the call, on the page, and the marks are the reader's own.

## Decisions (owner, 2026-10-12)

- **Places:** every place the summary's "Things to check" lists, one card each (not grouped,
  no card cap), then the stage 6 model reads, tagged experimental. The same set the summary
  counts, so "it flagged N places" matches the summary's tile.
- **Saving:** marks are kept in the browser as they are made; a download writes `marks.json`,
  which the reader saves in the run folder next to the page. A re-render reads it back into
  the page.
- **Carry-over to the next run of the same repository:** not in v1. Every run's page starts
  from its own `marks.json` only.
- Still open (C21): whether marks feed stage 6 calibration as labels. Not built; nothing reads
  `marks.json` except this page.

## plain.py

`PLAIN`: pattern id to plain words, one entry per row of `stages/04-phrases/patterns.yaml`.
Each says what the words are and "The worry: ..." (why a pattern would care), never whether
the line is a problem. Moved from `pre-planning/soft/d3/build.py`, which now imports it.
`describe(patterns)`: (id, words) per id, each once; an id with no entry (a retired pattern in
an old run) says the pattern no longer exists.

## Inputs

- `render_page(meta, reports, text_dir=None, text_href=None, marks=None, marks_error=None)`:
  `text_dir` is the run's `normalized/text/` folder (stage 2's true text, same line numbers
  stage 4 cites); `text_href` the same folder relative to the page; `marks` a parsed
  `marks.json`; `marks_error` why one could not be read.
- `load_marks(path)`: `(data, None)`, `(None, reason)` for a file that is not valid JSON or has
  no list of marks, `(None, None)` when there is no file.

## Output

`review.html`, written by `run.py` beside `summary.html` (fresh runs and `--rerender`):

- Header: a link back to `summary.html` at the top right; repository, source, pin, run; "Walkdown flagged N places" (and "a model read M more
  (experimental)"), the three marks with one line each, an index of every place with its mark,
  and whether a saved `marks.json` was loaded (with how many saved marks match no place).
- One card per place, in the summary's order: section tag in plain words, "Place k of N", the
  summary's headline, the location linked to the run's own copy of the text (and the original
  file, which may have changed since), the flagged line with `CONTEXT` lines either side,
  numbered, the flagged line marked and the matched words in `<mark>`. A passage longer than
  `MAX_SPAN` lines shows its first lines and counts the rest. With no text for the file or no
  line, the quote; with neither, nothing.
- "What was flagged": why a place of its kind is listed (`WHY`, for kinds the pattern words do
  not explain), each pattern's plain words with its id, the summary's note (base rate, the
  model's reading), every definition of a conflicting term, and for model reads that a
  model's reading can be wrong and never changes the findings.
- Three marks per card (Concerned, Not concerned, Not sure; pressing the chosen one again
  clears it) and an optional note.
- One place at a time with Back, Next, Next unmarked, and Show all; keys 1 to 3, arrows, N.
  Without the script, every card is listed and marking is off.
- "When you are done": counts per mark, Download `marks.json`, Copy, Load a marks file.
- `marks.json`: `{walkdown_review: 1, repo, run, pinned, saved, places, marks: [{id, place,
  section, headline, where, mark, note}]}`, marked or noted places only.
- Place ids: a hash of section, headline, location, and quote, so a re-render of the same run
  gives each place the same id and saved marks find their cards.
- Invisible characters in shown text appear as `U+XXXX` badges.
- Theme tokens for light and dark (as `summary.html`), phone width, print lists every card.

`summary.html` links to the page at the top right of its header, and again above "Things to
check" when it lists any place.

## Must never

- Show a score, severity, or verdict, or a mark the reader did not make.
- Emit unescaped text from the artifact. All artifact text is escaped in Python; the page
  script builds no markup from it; JSON embedded in the page cannot close its script tag.
- Show lines around a place in a file where stage 4 found what looks like a secret
  (`secret.found`): a secret can run over several lines. The flagged line shows stage 4's mask.
- Read the audited repository. Text comes from the run folder.
- Let marks change any finding, `summary.html`, `summary.md`, `full.md`, or `LOG.md`.
- Write `marks.json`. Only the reader does.

## Done when (each backed by a test in `tests/test_review_html.py` or `tests/test_plain.py`)

1. One card per summary item, deterministic places first, then model reads; the deterministic
   count equals the summary's "places to check".
2. A card shows the flagged line with `CONTEXT` lines either side from `text_dir`, the line
   marked and its matched words in `<mark>`; without text, the quote.
3. A passage longer than `MAX_SPAN` keeps its full location and counts the lines not shown.
4. Invisible characters show as `U+XXXX` badges.
5. Artifact text is escaped in cards and in the embedded marks (a `</script>` in a saved note
   cannot end the script).
6. No line around a place in a file with a `secret.found` finding is shown.
7. Every `patterns.yaml` row has a `PLAIN` entry and every entry names a row; each says
   "The worry:" and carries no em-dash.
8. Saved marks for places on the page are embedded; others are counted as matching no place;
   an unreadable `marks.json` is reported on the page and the page still renders.
9. Rendering the same reports twice gives the same place ids.
10. `run.py` writes `review.html`, and a re-render reads `marks.json` from the run folder
    (`tests/test_run.py`).
11. Each page links to the other at the top right of its header; the summary's line above
    the cards appears only when it lists a place.
12. No verdict words appear on the page.
