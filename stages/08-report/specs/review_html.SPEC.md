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
  summary's headline, the location linked to the run's own copy of the text (no link to the
  original file; on a model read no "(p=...)", since the score is in "What the model said";
  owner, 2026-10-13), "What was flagged:" (above the text, underlined like "What the model said:", owner 2026-10-13), the flagged line with `CONTEXT` lines either side,
  numbered, the flagged line marked and the matched words in `<mark>`. A passage longer than
  `MAX_SPAN` lines shows its first lines and counts the rest. With no text for the file or no
  line, the quote; with neither, nothing.
- "What was flagged": why a place of its kind is listed (`WHY`, for kinds the pattern words do
  not explain), each pattern's plain words with its id, the summary's note (base rate, the
  model's reading), every definition of a conflicting term.
- A model read opens with "What the model said:" (the model's reading, its score in the same
  sentence) and, in plain words, how far to trust it (owner, 2026-10-13). With a verified
  `soft.pinpoint` for a sweep card: "Where in the passage:" (the line or lines and the quote),
  "In plain words:", up to two "Also close" lines, and the note says two models read it; the
  text view opens around the pinpointed lines (`CONTEXT` either side, at most `MAX_SPAN`,
  counting the passage lines above and below) and only those lines are shaded. A pinpoint
  that named no line shows its sentence and that the place stays listed; an unverified one
  is not shown, only that its quote was not found.
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

1. One card per place (since 2026-10-16, C33 below; before that, one per summary item),
   deterministic places first, then places that hold only model reads.
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

## One card per place (added 2026-10-16, review C33)

The partner's marks on Compound Engineering (v3): 332 cards fell on 293 lines; 32 lines carried
71 cards, and on 16 of them the same reviewer marked the cards differently. `places(r)` now groups
the summary items (`findings_at`) into places:

- Every finding on one line is one place, whichever stage found it. A model read of that line
  joins the card ("What the model said:" for each read, tagged experimental); a place made only of
  model reads stays among the model reads at the end.
- A sentence repeated across files (`rep.sentence`) is one place that lists every location, and
  the findings at those locations join it, so the sentence is marked once.
- A passage (more than one line) and a place with no line stay on their own.
- The card leads with the first finding (the repeated sentence when there is one), says "and N more
  findings on this line" or "in N places", tags every stage that found something, and lists each
  finding under its own headline in "What was flagged".
- A place of one finding keeps that finding's id, so earlier marks still load; a merged place's id
  comes from its members' ids (marks saved on the separate cards before do not carry over).

Tests: `test_findings_on_one_line_are_one_card_with_every_finding`,
`test_a_model_read_of_the_same_line_joins_the_card`,
`test_a_repeated_sentence_is_one_card_listing_every_place`,
`test_a_lone_finding_keeps_its_id_and_a_passage_stays_alone`.

## Cards a reader can decide (added 2026-10-18, review C36)

The partner's v3 marks: 97 of 104 Not sure were on model reads, test data the model is pointed at,
and the image card; on rule findings the reader nearly always decided. Those cards now carry:

- **To decide:** one line under the location saying what the reader is deciding (`DECIDE`): on a
  card made only of model reads, and on test-data and image cards. Cards of rule findings get none.
- On a test-data or image card, **Where the AI is pointed at it**: the line in the model-read file
  that names it (stage 5 `from_line`) with two lines either side; then **The start of the file**
  (its first `START_LINES` lines and how many more), or **Text read from the image** (stage 2's
  image text). Nothing is shown from a file that holds what looks like a secret.
- A "do" read in plain words: "<backend> read this line as an instruction to do the flagged thing,
  with a <score> score", and, near the line, that a second read moves the score by about the drift
  so it could go either way.

Done when (tests in `tests/test_review_html.py`): a test-data card shows its question, the pointing
line, and the first lines with a count of the rest; an image card shows its text; a "do" read near
the line says so in a sentence and asks its question; a card of rule findings asks none.

Still open (owner): whether model reads stay in the same queue or move to a pass of their own.
