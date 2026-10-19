# Adding, changing, or retiring a search term

The search terms are the rows of `patterns.yaml` (stage 4, part 1) and the word lists in
`vocab.yaml` (part 2). What counts as dangerous moves fast, so a term change is a routine with a
fixed order. Follow it for every add, every narrowing, and every retirement (review C22,
2026-10-17). Run commands from the repository root with the project's Python
(`.venv/Scripts/python` on Windows).

## The steps, in order

1. **Source first.** Write down why the term matters, dated: an incident, a threat class, a
   phrase set, a miss found in a run, or an owner decision. The row's `source` field cites it
   (`PHRASES:<set> <row>` or `THREATS:<class> <bullet>`); a narrowing or a judgment call also gets
   a `note`.

2. **Fixtures first.** Write the case before the regex:
   - a positive that must hit, and a benign twin that must not, in wording of your own (never a
     sentence copied from an audited repository or from the docs, or the test only proves the
     regex matches its own example);
   - for a narrowing, also a line that has both shapes, so the real hit on it is shown to survive.

   Append the lines to the class's fixture file in `Fixtures/04-phrases/` (at the end, so existing
   line numbers and answer rows stay valid), and add rows to `Fixtures/ANSWERS/04-phrases.json`:
   `gate` for must-hit, `negative` for must-not, `recall` for measured. Fixtures and answers are
   byte-exact with LF line endings: on Windows, Python's `write_text` writes CRLF, so write bytes.
   Re-read the fixture, then `python grader/grader.py --rehash 04`.

3. **See it fail.** `python grader/grader.py 04` before touching the row: the new negative fires,
   or the new positive misses. A fixture that passes before the change tests nothing.

4. **The row.** In `patterns.yaml`: `id` (the family prefix, such as `L.` or `E.`), `check`, `regex`
   (case-insensitive, run on the folded line), `source`, and `note` when there is a narrowing.
   Two ways to narrow:
   - a **lookahead or lookbehind** on the alternative that over-matches. It drops only that phrase;
     another hit on the same line still fires. Prefer this.
   - **`unless:`**, a regex that cancels the hit when it also matches the line. It cancels the whole
     line, real hits included, and it needs a `note` with the reason.

   Every narrowed row gets cases in `stages/04-phrases/tests/test_table.py`: the benign shape in
   `test_narrowed`, the class still firing in `test_narrowed_rows_still_fire_on_their_class`.

5. **Plain words.** Add the row to `PLAIN` in `stages/08-report/plain.py`: what the words are, then
   "The worry: ...". The review page and the summary show it to readers. `tests/test_plain.py`
   fails until every row has one and every entry names a row.

6. **Grade everything.** `python grader/grader.py all` and `python -m pytest`. One stage is not
   enough: a term change moves other stages. A line that loses its only hit also loses its stage 6
   question, so its rows in `Fixtures/ANSWERS/06-soft.json` become `negative` with a note saying why;
   a hit that fed a stage 5 leg or pair can take the leg or a place to check with it.

7. **Recount.** Count what moved on the audited repositories' latest runs: hits per pattern, places
   to check, legs. Say what disappeared and why. When a term changes how widely a pattern turns up,
   refresh the base rates:
   `python stages/08-report/baserates.py <name>=<input_dir> [...] --out stages/08-report/baserates.json`.

8. **Record it.** A CHANGELOG line saying what a reader will notice, and a line in the review list.
   There is no version to bump: every run records the term set (`termset.py`), so the next audit
   of a repository Walkdown has seen before names the changed term in `changes.md` and counts the
   hits it moved under Walkdown's search terms.

## Retiring a term

Retiring is a change too. Delete the row and leave a tombstone comment where it was, with the date
and the reason (see `H.report-only`, retired 2026-10-08). Remove its `PLAIN` entry, turn its fixture
rows into negatives, handle the stage 6 answer rows as in step 6, and recount.

## Part 2 word lists (`vocab.yaml`)

The same order: source, fixtures in `Fixtures/04-phrases/part2-repo/` with answer rows, see them
fail, the list change, `grader.py all`, recount, record.

## Still open (review C22)

Where new terms come from (incident watch, other scanners' rule sets, misses in runs, reader marks,
labeling); how often to review the terms; whether outside contributors can propose one. (The term
set's version was built 2026-10-19: `termset.py`.)
