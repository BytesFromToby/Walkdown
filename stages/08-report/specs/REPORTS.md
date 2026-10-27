# The report set: spec

What a run gives its readers, who each output is for, what the reports may and may not say, and
how the specs stay true. Every output listed here has its own spec; this file is the index.

Status: decided by the owner 2026-10-20. Built: `summary.html` (the one page), `details.html`,
`review.html`, `full.md`, `changes.md`, the two cuts, marks that carry over, the Not
concerned boxes, and the docs (see "Build status").

## Two readers

1. **Deciding whether to use a repository** ("is this safe?"). Wants one page: what it can do,
   what Walkdown found that could be dangerous, and what to ask before using it.
2. **Improving or investigating a repository.** Wants every detail, and a way to work through
   it: mark what has been looked at, set aside what is fine, and see only what is new next time.

One page served both until 2026-10-20 and did neither well. Each reader now has their own.

## The outputs

A run folder (`docs/RUN-FOLDER.md`) holds the reports at the top and everything else in `data/`.

| File | Reader | What it is | Spec |
|---|---|---|---|
| `summary.html` | building (owner, 2026-10-26; before, deciding) | One page: will it trigger, what it costs against the expected context, what ships by how it is used, will it run elsewhere, is it ready for any AI, do the tools fit the job, is it current and clean, is it safe (the security concerns by fixed kinds), what it can do | `summary_html.SPEC.md` |
| `details.html` | improving | Every section in full, every list expandable, a Not concerned box on every row | `details_html.SPEC.md` |
| `review.html` | improving | The places to check, one at a time, each marked Concerned, Not concerned, or Not sure | `review_html.SPEC.md` |
| `full.md` | either | Every finding with file and line: the complete record, as text | `render.SPEC.md` |
| `changes.md` | either | What changed since the previous run of the same repository | `drift.SPEC.md` |
| `marks.json` | improving | The reader's marks, saved by the reader; carried to later runs | `marks.SPEC.md` |
| `LOG.md`, `data/` | either | Run log; stage outputs, notes, the text Walkdown read | `run.SPEC.md`, `layout.SPEC.md` |

Cut (owner, 2026-10-20): `summary.md` (the summary as text) and `summary-v1.html` (report v1,
kept while v2 settled). Report v1 stays retrievable at git tag `report-v1`.

The brief that `walkdown.py` prints names `summary.html` first, then `details.html`,
`review.html`, and `full.md`.

## What the reports may say

- **No verdict.** Never "do not use this", "safe", "unsafe", a score, a grade, or a rank of one
  place over another. (Owner, 2026-10-20; to revisit.)
- **"Security concerns" is allowed.** `summary.html` says Walkdown found security concerns when
  any of its fixed concern kinds has a place, and names them (`summary_html.SPEC.md`). The kinds
  and their order are fixed; nothing is picked by how bad it seems.
- **Nothing found never means safe.** `summary.html` says so once, in its footer, and names any
  step that did not run or did not pass its fixture check; what was not checked is in Other
  details on `details.html` and in `full.md` section 7.
- **Capability, never intent.** A box says what the repository could do. Whether it does is only
  seen by running it, and the cards say so.
- **Repository text is escaped and never run.** No page opens a link, loads a page, or shows a
  secret's value.

## Marks

One marking model across the pages: **Concerned**, **Not concerned**, **Not sure**. "Ignore" is
Not concerned. One `marks.json` per run, written only by the reader. Marks carry over to later
runs of the same repository, matched by what was flagged rather than by line number, so moved
lines keep their marks and changed lines get a fresh look (`marks.SPEC.md`).

## Keeping the specs true

This is how a change stays traceable from the owner's decision to the code and its tests.

- Every output and every script has a spec in `specs/`.
- A spec describes current behavior, top to bottom. A change to an output changes its spec in
  the same commit; the old wording goes, and one line is added to the spec's **History**.
- **History** is the last section of every spec: date, what changed, and why (an owner decision
  or a review item, such as `C36`).
- Each "Done when" item names the test that backs it.
- A part not yet built is marked **To build** where it is described, and loses the mark in the
  commit that builds it.
- The public docs (`docs/READING-THE-REPORT.md`, `docs/RUN-FOLDER.md`, `docs/HOW-IT-WORKS.md`)
  follow the specs in the same commit.

## Build status

| Part | State |
|---|---|
| This spec set | written 2026-10-20 |
| `summary.html`, one page | built 2026-10-20 |
| `details.html` (the long page, renamed) | built 2026-10-20 |
| Not concerned boxes on `details.html` | built 2026-10-20 |
| Marks carried over, stable keys | built 2026-10-20 (all three pages) |
| Cut `summary.md` and `summary-v1.html` | built 2026-10-20 (a re-render removes them) |
| Docs follow | built 2026-10-20 (README, docs/, CLAUDE.md, stage 8 CONTEXT, CHANGELOG, the skill) |

## History

- 2026-10-20: written (owner): two readers, two pages; no verdict, "security concerns" allowed;
  Not concerned replaces ignore; marks carry over; `summary.md` and `summary-v1.html` cut; specs
  describe current behavior and end with a history. Later the same day: no "Not checked" on
  `summary.html` (owner).
