# review_html.py and plain.py: spec

The page that walks the places to check one at a time, for the reader to mark each Concerned, Not
concerned, or Not sure. Walkdown renders no verdict: the reader makes the call, and the marks are
the reader's own (`REPORTS.md`, `marks.SPEC.md`).

Status: built (C21 2026-10-12; C33, C36, C31 part B, C32, C28 since; marks through `marks.py`,
carried from an earlier run, and shared with `details.html`, 2026-10-20).

## Inputs

- `render_page(meta, reports, text_dir=None, text_href=None, marks=None, marks_error=None,
  carried=None, cap_full=None)`: `text_dir` is the run's `data/normalized/text/` (stage 2's text,
  the line numbers stage 4 cites); `text_href` the same folder relative to the page; `marks`,
  `marks_error`, `carried`: from `marks.for_run` (the run's own marks, or an earlier run's and that
  run's name); `cap_full`: `capability.json`, so marks are matched against the same rows as on
  `details.html` (`details_html.mark_rows`).
- `load_marks`: `marks.load`.

## Places

`places(r)`: the places `details_html.first_items` lists, grouped so that one place is one card:

- Every finding on one line is one place, whichever stage found it (`findings_at`). The card
  leads with the first finding, says "and N more findings on this line", tags every stage that
  found something, and lists each finding under its own headline in "What was flagged".
- A sentence repeated across files (`rep.sentence`) is one place listing every location; the
  findings at those locations join it.
- A passage (more than one line) and a place with no line stay alone.
- A model read of a place's line joins its card; a place made only of model reads is a model
  read, walked in its own pass.
- Place ids: a hash of section, headline, location, and quote; a merged place's id comes from its
  members'. A re-render of the same run gives the same ids. Each card also carries its lead's
  stable key and every member's (`data-key`, `data-keys`; `marks.place_key`), which marks match.

## Each card

- Section tags in plain words; "Place k of N" (rule findings) or "Model read k of N"; the
  headline; the location linked to this run's copy of the text (never the original file; no
  "(p=...)" on a model read).
- **To decide:** one line on what the reader is deciding (`DECIDE`), on cards made only of model
  reads and on test-data and image cards.
- **A reviewer model's reading questions this** (`render.questioned`): when a confident stage 6
  read calls the line not an instruction; the finding stays.
- **What the model said:** for each model read: who read it, what it read, and the score in one
  sentence, near the line said in words; how far to trust it (`MODEL_NOTE`). A verified
  `soft.pinpoint` adds "Where in the passage:", "In plain words:", and up to two "Also close"
  lines, and the text opens on those lines; an unverified pinpoint shows only that its quote was
  not found.
- **What was flagged:** why a place of this kind is listed (`WHY`), each pattern in plain words
  (`plain.describe`) with its id, the item's note (base rate, model reading), every definition of
  a conflicting term.
- **Is it enforced?** on a read-only line (`render.limit_words`, `limit_routes`).
- On a test-data or image card: **Where the AI is pointed at it** (the line that names the file,
  two lines either side) and **The start of the file** (`START_LINES` lines and how many more) or
  **Text read from the image**.
- The text: the flagged line with `CONTEXT` lines either side, numbered, the flagged lines shaded
  and the matched words in `<mark>`, on every line of a wrapped match (stage 4 `spans`). A
  passage longer than `MAX_SPAN` lines shows its first lines and counts the rest. Without the
  file's text, the quote; without either, nothing. Invisible characters show as `U+XXXX`.
- One closing line on what only running it shows (`RUNTIME`; a prohibition has its own;
  fixed-fact kinds have none).
- Three marks (pressing the chosen one again clears it) and an optional note.

## The page

- Header: links at the top right to `summary.html` and `details.html`; repository, source, pin,
  run; "Walkdown flagged N places" and "a model read M more (experimental)", saying the model
  reads are a separate, optional pass; the three marks with one line each; an index of every
  place with its mark, model reads under their own heading; whether saved marks were loaded and
  how many match nothing in this run, or how many were carried from which run and how many
  earlier marks match nothing in this run.
- **Passes** (C36): Rule findings; Model reads, optional (only when there are any); Not sure,
  again (the places marked Not sure when it is opened, held while they are marked again). Back,
  Next, Next unmarked, and the progress line work within the pass; marking a card or following
  the index to another pass switches to it. The page opens on the first unmarked rule finding,
  or on the card the address names.
- One place at a time, or Show all; keys 1 to 3, arrows, N. Without the script, every card is
  listed and marking is off; print lists every card.
- "When you are done": counts per mark, what is left, the next pass; Download `marks.json`, Copy,
  Load a marks file (matched by key, else by id).
- Marks are kept in the browser as they are made. The page starts from the run's marks, its own
  or carried; a carried mark says "Your mark from run <name>." under the buttons until the
  reader changes it; the download is `walkdown_marks: 2` with stable keys (`marks.SPEC.md`), and
  it keeps the marks made on `details.html` (links, files, trifecta and hidden places) as they
  are.
- Theme tokens for light and dark, phone width.

## plain.py

`PLAIN`: pattern id to plain words, one entry per row of `stages/04-phrases/patterns.yaml`, each
saying what the words are and "The worry: ...", never whether the line is a problem.
`describe(patterns)`: (id, words) per id, once each; an id with no entry (a retired pattern in an
old run) says the pattern no longer exists.

## Must never

- Show a score, severity, or verdict, or a mark the reader did not make.
- Emit unescaped artifact text. All artifact text is escaped in Python; the script builds no
  markup from it; JSON embedded in the page cannot close its script tag.
- Show lines around a place in a file where stage 4 found what looks like a secret; the flagged
  line shows stage 4's mask.
- Read the audited repository; text comes from the run folder.
- Let marks change any finding or any other report; write `marks.json`.

## Done when (tests in `tests/test_review_html.py`, `tests/test_plain.py`)

1. One card per place, rule findings first, model reads after (`test_one_card_per_summary_item_model_reads_last`,
   `test_findings_on_one_line_are_one_card_with_every_finding`,
   `test_a_model_read_of_the_same_line_joins_the_card`,
   `test_a_repeated_sentence_is_one_card_listing_every_place`,
   `test_a_lone_finding_keeps_its_id_and_a_passage_stays_alone`).
2. The text with `CONTEXT` lines, the line marked, matched words in `<mark>`, wrapped matches on
   every line (`test_wrapped_match_is_marked_on_each_line`); without text, the quote.
3. A long passage keeps its location and counts the lines not shown; invisible characters as
   badges.
4. Escaping in cards and in the embedded marks; no lines around a secret.
5. Every pattern row has a `PLAIN` entry with "The worry:" and no em-dash.
6. Saved marks for places on the page are embedded, others counted; an unreadable file is
   reported and the page still renders; same ids on a re-render.
7. To decide, the pointed-at line and start of file, image text, "do" reads in a sentence
   (`test_test_data_card_shows_where_and_what`, `test_image_card_shows_its_text`,
   `test_do_read_in_plain_words_with_a_question`).
8. The runtime line per kind and the questioning line (`test_runtime_line_per_kind_of_card`,
   `test_questioned_line_on_the_card`).
9. Passes, numbering within the pass, the index heading
   (`test_model_reads_are_a_separate_pass_and_not_sure_can_be_walked_again`); the script driven
   in a browser on a superpowers run with no page errors (2026-10-20).
10. No verdict words; each page links the others at the top right.
11. Carried marks shown with their run; stable keys written (`tests/test_marks.py`).

## History

- 2026-10-12: built (C21); places, marks, `marks.json` per run.
- 2026-10-13: model reads in plain words; optional pinpoint.
- 2026-10-16: one card per place (C33).
- 2026-10-18: cards a reader can decide (C36, first half); wrapped lines marked (C37).
- 2026-10-20: runtime line (C31 part B), contradicted read-only places (C32), questioning reads
  (C28), passes and Not sure again (C36); wrapped matches on every line.
- 2026-10-20: owner: marks carry over and are shared with `details.html`. Built the same day
  (`marks.py`, `walkdown_marks: 2`).
