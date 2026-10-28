# summary_html.py: spec

Status: rebuilt 2026-10-27 as report v3, "glance and know" (owner; `glance.SPEC.md` holds the
eight questions). Before: the builder's page of 2026-10-26 (slice 1), and the page for someone
deciding whether to use a repository of 2026-10-20.

The one page: eight questions, each with a short label and a one-line answer, that someone with no
computer skills can read at a glance. Everything behind each answer is one tap away ("More ›"),
and the rest is on `details.html`, `review.html`, and `full.md`. It also holds the concern rows,
the security headline, and the brief's lines that `walkdown.py` prints, so the page and the
brief count the same way.

## Inputs

`render_page(meta, reports, stamps, notes, runs_ok, marks=None, changes=None) -> str`. `changes`
is `run.changes_for` (its cost line goes under question 2); `marks` the run's marks, own or
carried (`marks.SPEC.md`). The places come from `details_html.first_items`, the same set
`review.html` walks.

## Output: `summary.html`

1. **Header.** The name; "Checked <day> · version <hash7> · <N> files · License: <name>"
   (`glance.meta_line`); what it is in one sentence (`glance.what_it_is`: "A plugin for Claude
   Code: 9 skills (step-by-step instructions the AI follows for a task) and 7 helpers ..."); and
   "Walkdown reads the files without running anything. It points things out; you decide what
   matters. Tap a line for more."
2. **At a glance**: the eight questions as cards (`glance.card`), in order: switch, memory,
   package, elsewhere, hosts, tools, clean, careful. Each card shows the question, its chip, and
   its answer; "More ›" opens the bullets and, for question 2, the memory table.
3. **A step that did not work**, only then (`failed_steps`, `warning`): "Not every step worked in
   this run.", each such step by its plain name with "did not run" (no output) or "did not pass its
   fixture check (<result>)" (any result but PASS and INCOMPLETE); that a step that did not work can
   miss places, so this page may show fewer than there are; and a link to "What Walkdown didn't
   check" on `details.html`. A step with nothing in this repository to test, and a fixture check
   that did not run because an optional tool is not installed (INCOMPLETE, any stage), never reach
   this page (owner, 2026-10-25); `details.html` and `full.md` list both. A run made without
   validation has no stamps and gets no line for them.
4. **Footer**: links to `details.html`, `review.html` ("go through each place and mark it"), and
   `full.md`; then the page's one qualifier (`FOOTER`): "Walkdown reads a repository's files
   without running anything. It points out what it finds and leaves the judgment to you. Finding
   nothing does not mean a repository is safe."

Marking is on `review.html` only (owner, 2026-10-27); question 8 says how many places are marked.

## The concern rows (`CONCERNS`, `rows`)

One row per concern kind that has a place, in this fixed order; each place falls in the first row
that fits:

1. **Hidden text that reads like an instruction** (kind `hidden+phrase`).
2. **Runs code**: hooks, commands run at load, commands the person is asked to run
   (`details_html.action_group` = `runs`).
3. **Looks like a committed secret** (kind `secret`; test data and likely-not-secrets already left
   out).
4. **Reads secrets, calls out, or shares** (`action_group` = `out`).
5. **Lasting changes or permissions** (`action_group` = `lasting`; includes read-only lines a tools
   list contradicts).

The rest is wording only (`action_group` = `words`). A row holds each place once: findings that
`review.html` shows as one card (one line named by several) count once, and a row's `ids` are its
places' review cards. `total(rows)` counts every place once across the rows (a place may be in two);
`wording_count` counts the wording-only places once, leaving out any a row holds. A row's
`not_concerned` counts the places the reader marked Not concerned, and its `example` is the first
place (stage, file, line) not so marked. Model reads are never concerns.

## The security headline (`headline`), for the brief

- With concerns: "Walkdown found security concerns in this repository: <N> places, of <K> kinds."
  (`total`), with "(<M> of them marked Not concerned.)" when the reader marked some.
- With none: "Walkdown found none of the security concerns it looks for."
- When a step produced no output (`not_run`), never "found none": 'This run did not complete: the
  step "<name>" did not run' (or '<n> steps did not run, starting with "<name>"'), then "so Walkdown
  cannot say whether this repository has the security concerns it looks for." or, with concerns
  from the steps that ran, "In the steps that ran, Walkdown found security concerns: ..."
  (2026-10-21, an outside tester: an empty .venv crashed stage 1 and the page read as clean).
- With none and a step that failed its fixture check (`failed_checks`), never plain "found none":
  "..., but not every step worked, so it may have missed some." (owner, 2026-10-25, review C40).

Question 8 on the page says the same things in its own templates (`glance.SPEC.md`).

## The brief's lines

`brief_trigger_line`, `brief_cost_lines`, `brief_needs_line`, `brief_ready_line`, `brief_fit_line`,
`brief_clean_line`: counts only, no repository text but package names; `None` when the run did not
make the check. `TOGETHER` (what the three boxes mean together) and `WORDING` are the brief's too.

## Must never

- Say "do not use", call the repository safe or unsafe, or give a score, grade, or rank.
- Choose concerns by anything but the fixed kinds and order above.
- Show a secret's value, or open, fetch, or check a link.
- Emit unescaped repository text.

## Done when (tests in `tests/test_summary_html.py`)

1. The page: eight questions in order, title, footer links and qualifier
   (`test_eight_questions_in_order_title_and_footer`).
2. Rows in the fixed order, each place once (`test_rows_in_fixed_order_each_place_once`,
   `test_a_place_counts_once_as_review_html_counts_it`); marks counted and skipped for the example
   (`test_marks_are_counted_and_skip_the_example`); model reads never concerns
   (`test_model_reads_are_never_concerns`).
3. The headline and question 8 never read as clean when a step did not run or failed
   (`test_a_failed_check_never_reads_as_clean`, `test_a_run_missing_a_step_never_reads_as_clean`).
4. A step that did not work is named at the bottom; an INCOMPLETE stamp is not
   (`test_a_step_that_did_not_work_is_named_at_the_bottom`).
5. The brief's lines (in the question tests: `test_switch_question_comes_first`,
   `test_memory_question_one_table_and_the_since_line`, `test_elsewhere_question`,
   `test_hosts_question`, `test_tools_question`, `test_clean_question`).
6. No verdict words; repository text escaped (`test_no_verdict_words_and_escaping`). Checked by eye
   on an audited plugin's run (2026-10-27).

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
- 2026-10-26 (owner, plan for builders, slice 1): rebuilt as the builder's page: what it costs,
  what you ship, is it safe; Questions before use moved to `details.html`.
- 2026-10-25 (owner, after an outside tester's report, review C40): what reaches this page is a
  step that did not run or a step that ran and failed its fixture check; with no concerns, a
  failed check changes the headline. A step with nothing to test and a check skipped for a
  missing optional tool stay in `details.html` and `full.md` (this ends the 2026-10-21 stage 2
  line, "skipped part of this repository", and with it the "pDF" and "hTML" in that line).
- 2026-10-27 (owner, report v3): rebuilt as eight questions at a glance (`glance.py`): tokens in one
  place, plain words for a reader with no computer skills, charts, "What you ship" as one bar of how
  the files are used. The old blocks (trigger, cost, ship, elsewhere, ready, fit, clean, concerns,
  can) are gone; the concern rows, headline, warning, and brief lines stay here. Recount the same
  day: a place counts once in the rows and the headline, as on `review.html`.
