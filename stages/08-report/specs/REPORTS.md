# The report set: spec

What a run gives its readers, who each output is for, what the reports may and may not say, and
how the specs stay true. Every output listed here has its own spec; this file is the index.

Status: decided by the owner 2026-10-20; the two pages rebuilt as report v3, "glance and know",
2026-10-27 (owner; `glance.SPEC.md`). Built: `summary.html`, `details.html`, `review.html`,
`full.md`, `changes.md`, marks that carry over, and the docs (see "Build status").

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
| `summary.html` | anyone, no computer skills needed (owner, 2026-10-27) | One page, eight questions at a glance, each with a short label and a one-line answer: will its skills switch on, how much of the AI's memory it uses (the one place for tokens), what comes in the package, will it work on someone else's computer, with other AI tools, does it ask only for the tools it needs, is it finished and up to date, anything to be careful about | `summary_html.SPEC.md`, `glance.SPEC.md` |
| `details.html` | improving | The same eight questions with everything behind them: tables, charts, and every place in folded lists; then what Walkdown didn't check | `details_html.SPEC.md`, `glance.SPEC.md` |
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
- **"Security concerns" is allowed.** Question 8 counts the places in the fixed concern kinds
  and names the kinds (`summary_html.SPEC.md`). The kinds and their order are fixed; nothing is
  picked by how bad it seems.
- **Plain words.** The summary is for a reader with no computer skills: fixed templates, file
  names only in small "where" notes, tokens in question 2 only, and no repository text but hidden
  text that reads like an instruction (80 characters; owner, 2026-10-27).
- **Nothing found never means safe.** `summary.html` says so once, in its footer, and names any
  step that did not run or did not pass its fixture check; what was not checked is in "What
  Walkdown didn't check" on `details.html` and in `full.md` section 7. A question whose check did
  not run says "Not measured", never "nothing".
- **Capability, never intent.** A box says what the repository could do. Whether it does is only
  seen by running it, and the cards say so.
- **Repository text is escaped and never run.** No page opens a link, loads a page, or shows a
  secret's value.

## Marks

One marking model: **Concerned**, **Not concerned**, **Not sure**, made on `review.html` only
(owner, 2026-10-27); the other two pages say how many places are marked. "Ignore" is Not
concerned. One `marks.json` per run, written only by the reader. Marks carry over to later
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
| Not concerned boxes on `details.html` | built 2026-10-20; removed 2026-10-27 (report v3) |
| Report v3: `summary.html` and `details.html` as eight questions (`glance.py`) | built 2026-10-27 |
| Marks carried over, stable keys | built 2026-10-20 (all three pages) |
| Cut `summary.md` and `summary-v1.html` | built 2026-10-20 (a re-render removes them) |
| Docs follow | built 2026-10-20 (README, docs/, CLAUDE.md, stage 8 CONTEXT, CHANGELOG, the skill) |

## History

- 2026-10-20: written (owner): two readers, two pages; no verdict, "security concerns" allowed;
  Not concerned replaces ignore; marks carry over; `summary.md` and `summary-v1.html` cut; specs
  describe current behavior and end with a history. Later the same day: no "Not checked" on
  `summary.html` (owner).
- 2026-10-26 (owner, plan for builders): `summary.html` became the builder's page.
- 2026-10-27 (owner, report v3, "glance and know"): both pages rebuilt as eight questions for a
  reader with no computer skills; marking on `review.html` only; the old pages replaced outright.
