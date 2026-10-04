# summary_html.py: spec

The summary page as HTML for a reader who is not a specialist (added 2026-09-30:
the owner found `summary.md` busy and hard to read). Same facts as `summary.md`,
from the same fixed rules in `render.py`; nothing new is detected or judged.

## Output

`render_page(meta, reports, stamps, notes, runs_ok) -> str`: one self-contained HTML
document (`summary.html`):

- Header: artifact name, source, pin, retrieval date, run; "Static examination only".
- Four counts: files examined (and read in full), things to look at first, trifecta
  legs ("capability, not a verdict"), things not examined.
- "Look at these first": the summary's points of attention as plain items in stage
  order, each with a stage tag, a plain headline, the locations, and the quoted
  line. Items with the same stage and headline are one card listing every place
  (`grouped`). At most `MAX_FIRST` cards, then a count.
- Stage 4 headlines say what matched ("Matches the wording of ...", `FAMILY`),
  never what the author meant.
- "Stage by stage": one plain sentence per stage (`plain_status`), a pill when a
  stage's validation is not PASS, and the technical status line behind a
  disclosure.
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

## Model reads in their own block (added 2026-10-03, review C14)

Stage 6 cards are kept out of "Look at these first" and shown after it under "Model reads
(experimental)", with a lede naming the backends and saying a model's reading can be wrong,
repeat reads vary, and these never change the findings above. The tile counts deterministic
places only and adds "N model reads below" when there are any. No model reads: no block.
Section 4's plain sentence adds the stage 6 label split when labels ran (review C15).
