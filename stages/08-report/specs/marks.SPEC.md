# marks.py: spec

Status: built 2026-10-20 (owner decision the same day): `review.html`, `summary.html`, and the
Not concerned boxes on `details.html`.

The reader's marks: one model, one file, carried to later runs of the same repository.

## The model

Three marks: **Concerned** (look into it, or change it), **Not concerned** (read it; fine for what
the repository is for), **Not sure**. "Ignore" is Not concerned (owner, 2026-10-20). A mark
belongs to the reader: Walkdown never sets one, and a mark changes no finding, no count in
`full.md`, and nothing in `data/`.

Marks are made on `review.html` (any of the three) and `details.html` (the Not concerned box).
`summary.html` shows how many places are marked Not concerned, and makes no marks.

## The file: `marks.json`

Saved by the reader in the run folder, next to the pages (a download from either page). Walkdown
never writes it.

`{walkdown_marks: 2, repo, run, pinned, saved, marks: [{key, id, kind, where, headline, mark,
note, from}]}`

- `key`: the row's stable key (below). `id`: the place id on `review.html` (a hash of section,
  headline, location, and quote), for places only.
- `kind`: `place`, `link`, `file`, `evidence`, `hidden`. `where`: the location as shown.
  `headline`.
- `mark`: `concerned`, `not-concerned`, `not-sure`; `note`: the reader's words, optional.
- `from`: the run the mark was made in. It is kept when the mark carries over and when the
  reader only adds a note; changing the mark makes it this run's.

A `walkdown_review: 1` file (made before this spec) still loads: its marks match by `id`.

## The code: `marks.py`

- `place_key(item)`, `link_key(url)`, `file_key(reason, path)`, `evidence_key(box, file, text)`,
  `hidden_key(file, carrier, text)`: the keys below, each a hash of its row kind and parts with
  white space collapsed.
- `load(path)`: `(data, None)`; `(None, reason)` for a file that is not JSON or has no list of
  marks; `(None, None)` when there is none.
- `for_run(run_dir)`: `{data, error, carried}`: the run's own file, or the carried one with the
  name of the run it came from.
- `match(data, rows)`: rows are (row id, every key the row answers to); a mark matches by key,
  else by id; returns ({row id: the mark's record}, how many match no row). The rows of a run
  are `details_html.mark_rows`; both pages match against them, and each page's download holds
  every mark that matched, so saving from either page keeps the other's marks.

On `review.html` a card answers to the key of every finding on it, so a carried mark finds its
card when the findings on a line change but one of them is still there.

## Stable keys

A key names what was flagged, never the line number alone, so a mark follows its line when lines
move and drops away when the line itself changes:

| Row | Key |
|---|---|
| A place | section, headline, file, and the flagged text with white space collapsed (the quote; for a place with no quote, the location) |
| A repeated sentence | section, headline, and the sentence |
| An outside link | the whole address |
| A Worth a look file | the reason (`unknown-type`, `ext-magic-mismatch`, `archive`, `symlink`, `reader-window`) and the file path |
| A trifecta place | the box, the file, and the text of the cited line (from stage 4's quote at that line, else the line number) |
| A hidden place | the file, how it hides (`carrier`), and the hidden text (else the line number) |

## Carry-over

When `run.py` writes a run's pages (a new run or `--rerender`):

1. The run's own `marks.json`, when there is one, is the run's marks.
2. Otherwise, the newest earlier run of the same repository (a sibling run folder whose name
   sorts before this one, as `run.changes_for`) with a `marks.json` gives **carried** marks:
   each matched to this run's rows by key. Marks whose key matches no row are dropped and
   counted ("<n> earlier marks match nothing in this run").
3. A carried mark shows as the reader's mark with "Your mark from run <name>." (on
   `details.html`, "from run <name>" beside its box), and can be changed. Saving from the page writes it into this run's `marks.json` (`from` as above).
   `review.html` says how many marks were carried from which run, and how many match nothing.

All three marks carry over. A Concerned mark stays until the reader changes it.

## Must never

- Write `marks.json`, or change a finding or count because of a mark.
- Match a mark by line number alone.
- Carry marks between different repositories (different run folder parents).

## Done when (tests in `tests/test_marks.py`)

1. A place's key is the same when its line number changes and different when its text changes
   (`test_place_key_follows_the_line_not_its_number`).
2. Each row kind gets its key as in the table (`test_each_row_kind_gets_its_key`).
3. A new run with no `marks.json` takes the newest earlier run's marks, matched by key; unmatched
   marks are counted; a run with its own `marks.json` ignores earlier ones; other repositories
   and later runs are never read (`test_carry_over_from_the_newest_earlier_run`).
4. A carried mark keeps `from`; `review.html` and `summary.html` show it
   (`test_a_carried_mark_keeps_from_and_the_pages_show_it`). The page script, driven in a browser
   (2026-10-20): carried marks labeled with their run, a changed mark becomes this run's, a note
   keeps the run, the download is `walkdown_marks: 2`.
5. A `walkdown_review: 1` file loads by id (`test_a_walkdown_review_1_file_loads_by_id`).
   Marks are one set across the pages (`tests/test_details_html.py`,
   `test_marks_are_one_set_across_the_pages`).
6. End to end, two runs with the line moved: the mark carries; nothing in `data/`, `full.md`, or
   `changes.md` differs with and without marks; Walkdown writes no `marks.json`
   (`test_marks_carry_to_a_later_run_and_change_nothing_else`).

## History

- 2026-10-12: `marks.json` from `review.html` (C21): one run, no carry-over.
- 2026-10-20: owner: one model across pages, Not concerned replaces ignore, marks carry over.
  Built the same day: `review.html` and `summary.html` (`walkdown_marks: 2`), then the Not
  concerned boxes on `details.html` with the `link`, `file`, `evidence`, and `hidden` kinds.
