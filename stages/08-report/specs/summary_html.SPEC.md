# summary_html.py: spec

Status: built 2026-10-20 (owner decision the same day). Marks are the run's own or carried,
matched by stable key as `review.html` matches them (`marks.SPEC.md`).

The one page for someone deciding whether to use a repository: what Walkdown found that could
be dangerous, by fixed kinds, what the repository can do, and what to ask before using it.
Everything else, what was not checked included, is one click away in `details.html` and
`review.html`.

## Reader and length

Someone asking "is this safe?". The page answers with what was found and where to look, never
with a verdict (`REPORTS.md`). It fits one laptop screen, about two printed pages: counts and one
example per row, never lists.

## Inputs

`render_page(meta, reports, stamps, notes, runs_ok, marks=None) -> str`. `marks` are the run's
marks, this run's own or carried from an earlier run (`marks.SPEC.md`). The places come from
`details_html.first_items`, the same set `review.html` walks.

## Output: `summary.html`

1. **Header.** "Walkdown report on <name>"; source, pin, retrieval date, run, Walkdown version;
   the license line (as `details_html`); links at the top right to "Details" (`details.html`) and
   "Review each place" (`review.html`).
2. **The headline sentence**, from the concern rows below:
   - With concerns: "Walkdown found security concerns in this repository: <N> places, of <K>
     kinds." When the reader marked some Not concerned: "(<M> of them marked Not concerned)".
   - With none: "Walkdown found none of the security concerns it looks for." The page's one
     qualifier is in the footer.
3. **Security concerns.** One row per concern kind that has a place, in this fixed order
   (`CONCERNS`). Each place falls in exactly one row; a place is taken by the first row that fits:
   1. **Hidden text that reads like an instruction** (kind `hidden+phrase`).
   2. **Runs code**: hooks, commands run at load, commands the person is asked to run
      (`details_html.action_group` = `runs`).
   3. **Looks like a committed secret** (kind `secret`; test data and likely-not-secrets are
      already left out of the places).
   4. **Reads secrets, calls out, or shares** (`action_group` = `out`).
   5. **Lasting changes or permissions** (`action_group` = `lasting`; includes read-only lines a
      tools list contradicts).

   Each row: the kind, its place count, how many of those the reader marked Not concerned, and
   one example: the first place (stage order, then file, then line) not marked Not concerned,
   with its headline and location, linked to its card in `review.html`. "<n> more" links to the
   matching section of `details.html`.

   With no concern rows, the section has no lede and says "Nothing to point out here."

   Then one line: "<W> more places are wording only: instructions that change how the AI reads,
   decides, or answers." ("<W> places are ..." with no rows above; `action_group` = `words`),
   linked to `details.html#risky`. Model reads
   are not concerns: when any ran, one line counts them ("<R> model reads, experimental, on the
   review page").
4. **What it can do.** No lede (the footer covers what a static read can show). The three boxes in one row, checked first, colored as in `details.html`,
   with no lists, linked to `details.html#trifecta`. Under them, "Each one is ordinary on its
   own. A tool that does all three can be steered by text from outside into sending your data
   away." (`TOGETHER`, from `details_html.TRIFECTA_LEDE`), then one line naming the general
   risks present ("Also: runs commands on its own, adds text before you type, ...").
5. **Questions before use** (`details_html.before_use`, as built 2026-10-20): only questions with
   evidence, in its three groups, under one lede: "These are the questions the findings raise for
   someone deciding whether to use this repository. The answers, and what to do about them, are
   yours." With no questions: "No questions from these findings." and no lede.
6. **A step that did not work**, only then (`failed_steps`, `warning`; at the bottom, owner
   2026-10-21): "Not every step worked in this run.", each such step by its plain name with "did
   not run" (no output), "did not pass its fixture check (<result>)" (FAIL or ERROR), or, for an
   INCOMPLETE stage 2, "skipped part of this repository: <what>, <why>" when a missing optional
   tool reads files this repository has (`render.tool_items`); an INCOMPLETE stamp with no such
   files adds nothing. Then that a step that did not work can miss places so the page may show
   fewer than there are, and a link to Other details on `details.html`. A run made without
   validation has no stamps and gets no line for them.
7. **Footer** (`FOOTER`), the page's one qualifier, in plain words: "Walkdown reads a
   repository's files without running anything. It points out what it finds and leaves the
   judgment to you. Finding nothing does not mean a repository is safe." (`details.html` and
   `full.md` keep `render.NOT_WHAT`.)

What was not checked, and the fixture results, are on `details.html` (Other details) only,
apart from the warning above. The
owner found a "Not checked" line here unnerving: on most runs it named only the optional model
reads, a run setting (2026-10-20).

Theme tokens for light and dark, phone width with no page-wide horizontal scroll, artifact text
escaped, print on one or two pages.

## Must never

- Say "do not use", call the repository safe or unsafe, or give a score, grade, or rank.
- Choose concerns by anything but the fixed kinds and order above.
- List more than one example per row.
- Show a secret's value, or open, fetch, or check a link.
- Emit unescaped artifact text.

## Done when (tests in `tests/test_summary_html.py`)

1. With concerns, the headline gives places and kinds; with none, it says none and that
   nothing found does not mean safe (`test_headline_with_and_without_concerns`).
2. Rows appear in the fixed order, only for kinds with places; each place is in exactly one row;
   wording-only places are one line (`test_rows_in_fixed_order_each_place_once`).
3. Each row has its count, one example linked to its review card, and a link to the details
   (`test_each_row_has_one_example_linked_and_a_more_link`); Not concerned marks are counted and
   skipped for the example (`test_not_concerned_marks_are_counted_and_skip_the_example`).
4. Model reads are one line and never concerns (`test_model_reads_are_one_line_and_never_concerns`).
5. The capability row and the questions; no not-checked line
   (`test_capability_and_questions_and_no_not_checked`, `test_questions_before_use_follow_the_evidence`).
6. A step that did not run or failed its fixture check is named at the bottom; an INCOMPLETE
   stage 2 only when the repository has files the missing tool reads; with every step working,
   or no stamps, there is no warning (`test_a_step_that_did_not_work_is_named_at_the_bottom`).
7. No verdict words; artifact text escaped (`test_no_verdict_words_and_escaping`). Checked by eye
   on a Plumbline run (2026-10-20): about two laptop screens, nothing wider than the page.

## History

- 2026-09-29: first summary (text, `summary.md`).
- 2026-10-07: HTML summary page (report v1).
- 2026-10-16: report v2, the long page in the owner's order (now `details_html.SPEC.md`).
- 2026-10-20: owner: two readers, two pages. This spec becomes the one page; the long page moves
  to `details.html`. No verdict, "security concerns" allowed. Built the same day. Then the "Not
  checked" section and the headline's count of checks that did not run were removed, and a
  warning under the headline names a step that did not work (owner). Then fewer caveats (owner,
  on the first run with no concerns): "it looks for" in the headline, no "nothing found" line
  there, "Nothing to point out here." and no ledes on empty sections, no "no verdict and no score"
  sentence, and a plain footer as the page's one qualifier. 2026-10-21 (owner, after a fresh
  install showed the warning on every run without the optional tools): the warning moved to the
  bottom, and an INCOMPLETE stage 2 counts only when the missing tool reads files the repository
  has. Under the three boxes, what they mean
  together, and no lede above them (owner).
