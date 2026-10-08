# summary_html.py: spec

The summary page as HTML for a reader who is not a specialist (added 2026-09-30:
the owner found `summary.md` busy and hard to read). Same facts as `summary.md`,
from the same fixed rules in `render.py`; nothing new is detected or judged.

## Output

`render_page(meta, reports, stamps, notes, runs_ok) -> str`: one self-contained HTML
document (`summary.html`):

- Header: artifact name, source, pin, retrieval date, run; "Static examination only".
- Three counts: files examined (and read in full), places to check, and checks
  skipped that apply to this repository (`render.glance`, 2026-10-07).
- "Things to check" (renamed from "Look at these first", 2026-10-07): the summary's
  points of attention as plain items in stage order, each with a tag naming its section
  in plain words (a link to that row of "Stage by stage", never "Stage N"), a plain
  headline, the locations, and the quoted line. The lede says being listed does not mean
  something is wrong; with nothing listed it says "Nothing to check". Items with the same stage and headline are one card listing every place
  (`grouped`). At most `MAX_FIRST` cards, then a count.
- Stage 4 headlines say what matched ("Matches the wording of ...", `FAMILY`),
  never what the author meant.
- "Stage by stage": one plain sentence per stage (`plain_status`), a pill when a
  stage's validation is not PASS, and the technical status line behind a
  disclosure. Row 7 names the skipped checks and the tools not needed; its disclosure
  keeps every line of `render.limits`.
- No pattern IDs and no weighting words in a card: the repeated-sentence card names
  the pattern family in plain words (`FAMILY`).
- The trifecta foot is in plain words (`render.TRIFECTA_ALL`, `TRIFECTA_SOME`); the
  named term stays in the docs.
- Recommendations, then "What this is not".
- Theme tokens for light and dark (`prefers-color-scheme` and `data-theme`), phone
  width, every artifact string HTML-escaped.

## Signal levels (added 2026-10-01, soft D1)

Stage 4 items carry their base rates as the note ("How often this pattern turns up
elsewhere: …"); grouped cards keep each distinct note. Stage 6 "do" reads name their p
beside each place; near-the-line reads get their own card, "Near the line: may be a real
instruction", whose note states the band and the drift once.

## Marked legs (added 2026-10-01, soft D5)

A leg in `render.all_marked_legs` keeps its checked box and gains one line: every line
cited for it was read in stage 6 as not an instruction; see 5 in the full report.

## Sweep card (added 2026-10-01, soft D2)

Uncovered flagged passages get the first stage 6 card, "No pattern matched, but a model
read this as an instruction", each place with its p, and the plain kinds as notes.
Uncovered passages near the line (p_any 0.4 to 0.6) get their own card, "Near the line: no
pattern matched, and a model may read this as an instruction", with the drift stated once.

## Must never

- Show a score, severity, or verdict; drop the trifecta qualifier.
- Emit unescaped text from the artifact.

## Done when (each backed by a test in `tests/test_summary_html.py`)

1. The page has the header, the seven stage rows, both sections, and dark-theme tokens.
2. Artifact text is escaped.
3. Same-headline items group into one card with every location.
4. Stage 4 headlines start "Matches the wording".
5. A stage whose stamp is not PASS shows a pill.
6. The trifecta qualifier is present and no verdict words appear.
7. Cards name their section in plain words and link to its row.
8. The repeated-sentence card carries no pattern ID or "adds weight".
9. The skipped tile counts only checks that apply; a tool for a missing file kind is
   "not needed"; a standing limit is not counted.

## Model reads in their own block (added 2026-10-03, review C14)

Stage 6 cards are kept out of "Look at these first" and shown after it under "Model reads
(experimental)", with a lede naming the backends and saying a model's reading can be wrong,
repeat reads vary, and these never change the findings above. The tile counts deterministic
places only and adds "N model reads below" when there are any. No model reads: no block.
Section 4's plain sentence adds the stage 6 label split when labels ran (review C15).
