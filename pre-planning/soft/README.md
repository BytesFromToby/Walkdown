# Stage 6 (soft reads): working notes

Stage 6 is the meat of the build and will be built and rebuilt. This folder keeps
the thinking, the experiments, and the decisions, so each rebuild starts from what
was learned instead of from scratch.

The contract the code follows is `stages/06-soft/CONTEXT.md`. This folder is the
design conversation around it: when a discussion here settles something, the
decision is copied into CONTEXT.md (and METHOD, CHARTER, or CONTRACT where it
touches them) and marked settled here.

| File | What it holds |
|---|---|
| `EVAL.md` | Every measurement of the labeling and relational backends: sets, results, what they mean (was `pre-planning/SOFT-EVAL.md`) |
| `2026-09-30-discussion.md` | Overview of stage 6, the owner's ideas (keyword windows, chunking, scores), pushback, alternatives, and the open decisions |

Add a new dated file per discussion; keep `EVAL.md` as the one running record of
numbers.

## Open decisions (keep this list current)

| # | Decision | Status | Where discussed |
|---|---|---|---|
| D1 | Per-finding signal levels (from measured base rates), as distinct from the charter's ban on an overall score | **settled 2026-10-01**: CHARTER wording added; stage 4 points show base rates (`baserates.json`); stage 6 near-the-line band 0.7 to 0.9 | 2026-09-30-discussion.md |
| D2 | A model may act as a detector in stage 6 (a chunk sweep for text no pattern matches), with its own validation, never replacing stage 4 | **settled 2026-10-01**: built as an opt-in coverage sweep (`--sweep jev`), validated on `Fixtures/06-soft/sweep-repo` (11/12, 0/20 benign); METHOD and CLAUDE.md carry the exception | 2026-09-30-discussion.md, EVAL.md |
| D3 | Shrink labeling from five labels to the one bit the report uses ("is this an earnest instruction to do the matched action?") | waiting on the owner's second labeling of the review table | 2026-09-30-discussion.md, EVAL.md |
| D4 | Center the labeling window on the matched span and mark it | tried 2026-09-30: made Jev worse (high-confidence `do` 15/20 vs 9/9); reverted for labeling, stage 4 keeps `matches` | EVAL.md, 2026-09-30-discussion.md |
| D5 | Should a confident stage 6 label (description / other-sense at p >= 0.8) mark stage 5 evidence as "read as not an instruction"? Stage 5 runs before stage 6, so today a line like "without requiring a `pip install` step" (Plumbline mdtoc decision record) counts toward Takes outside input | **settled 2026-10-01**: mark, never demote. A non-`do` label at p >= 0.8 marks the evidence line in the full report; a leg whose every cited line is marked gets a note, and stays checked. The motivating mdtoc line read `description` at 0.66, below the bar, so it stays plain evidence | this README, EVAL.md |
