# summary_html.py: spec

Status: rebuilt 2026-10-26 as the builder's page (owner; plan for builders, slice 1,
`pre-planning/SPEC-SLICE1-2026-10-26.md`). Built 2026-10-20 as the page for someone deciding
whether to use a repository. Marks are the run's own or carried, matched by stable key as
`review.html` matches them (`marks.SPEC.md`).

The one page for someone building a skill or agent: what it costs in an AI's context against the
context they expect, what ships by how it is used, and whether it is safe. Everything else is one
click away in `details.html` and `review.html`.

## Reader and length

A builder asking "what does this cost, what ships, and is it safe?". The page answers with counts
and places, never with a verdict or a score (`REPORTS.md`). It fits about two laptop screens.

## Inputs

`render_page(meta, reports, stamps, notes, runs_ok, marks=None, changes=None) -> str`; `changes` is
`run.changes_for` (slice 6: its `cost_line` goes under What it costs). `meta["context"]` is the
expected context (default `render.DEFAULT_CONTEXT`). `marks` are the run's marks, this run's own
or carried from an earlier run (`marks.SPEC.md`). The places come from `details_html.first_items`,
the same set `review.html` walks.

## Output: `summary.html`

1. **Header.** As before.
2. **Headline**, two sentences (`cost_sentence`, then `headline`):
   - "<N> files; every session takes <X> tokens once installed, and the largest skill at its
     fullest <Y> (<Z> of a <C>-token context)." With no skill, agent, or command but project
     files: "every session in this folder takes <P> tokens (...)". Over the expected context, it
     adds "That is more than the expected context." With no stage 5 tiers, no first sentence.
   - The security headline, unchanged (rules below).
2b. **Will it trigger?** (`trigger_block`, id `trigger`; slice 4, owner 2026-10-26: first after the
   headline): how the entries trigger (`render.entries_line`), the listing lines
   (`render.listing_lines`), then one row per kind (`render.TRIG_KINDS` order) with its count, why,
   and its first place (`render.trig_parts`: the place in code, the rest as text); with entries and
   nothing found, "Every entry has frontmatter its host reads and follows the rules."; a link to
   `details.html#trigger`. A run without trigger findings says not measured.
3. **What it costs** (`cost_block`, id `cost`): `details_html.context_table` and `cost_notes`, and
   a link to `details.html#ship`. A run with no tiers says it was not measured.
4. **What you ship** (`ship_block`, id `ship`): the three bands with files, size, and tokens and
   their groups' counts; then, when there are any: "If the <n> files nothing points to and the
   <m> build files were left out of what you ship: <K> smaller, and <T> tokens no longer within an
   AI's reach." (owner, 2026-10-26: a fact with its saving, never an order); a link to the full list.
4b. **Will it run on someone else's machine?** (`elsewhere_block`, id `elsewhere`; slice 2, owner
   2026-10-26): "It uses: <programs>, and <n> packages (<names>)." and "Not declared anywhere:
   <names>." (or "Everything it uses is declared."), each list cut at 12 names ("and N more"; six
   for packages); then one row per kind of place that ties it to one machine (`render.PORT_KINDS`
   order), with its count, why it breaks elsewhere, and its first place; with none, "Nothing found
   that ties it to one machine."; a link to `details.html#elsewhere`. A run without stage 4 says not
   measured.
4c. **Is it ready for any AI?** (`ready_block`, id `ready`; slice 3, owner 2026-10-26): with
   `--hosts`, "For the hosts you named" and the to-do list first (`render.todo`); one line per
   host (`render.host_line`); when there are skills no host reads where they sit, how many and the
   first, and that a host reads them once installed; each pair of copies that differ, with which
   hosts read each (the first three, then how many more); one row per kind of one-host feature
   (`render.FEATURE_KINDS` order) with its count, why it matters, and its first place, or "No
   one-host feature found."; a link to `details.html#ready`. A run without host findings says not
   measured. Never says which host a repository should support.
4d. **Do the tools fit the job?** (`fit_block`, id `fit`; slice 5, owner 2026-10-26: after Is it
   ready for any AI, before Is it safe): one row per kind (`render.FIT_KINDS` order: never used, no
   tool to do it, inherits every tool, read-only claims contradicted, loops with no stated limit,
   hooks on every prompt or tool call) with its count, why, and first place (`render.fit_parts`);
   with none, "Every tool granted is one the words ask for, and nothing asks for a tool it lacks.";
   a link to `details.html#fit`. A run without `fit.checked` says not measured.
4e. **Is it current and clean?** (`clean_block`, id `clean`; slice 6, owner 2026-10-27: after Do
   the tools fit the job, before Is it safe): one row per kind (`render.CLEAN_KINDS` order: unfinished
   text, dated claims, pinned model IDs with how many distinct, older tool names) with its count,
   what it means, and the first place without the line's text; with none, "No unfinished text, dated
   claims, pinned model IDs, or older tool names."; a link to `details.html#clean`. A run without
   `clean.checked` says not measured.
5. **Is it safe?** (`concerns_block`, id `concerns`): the security concern rows as before (fixed
   kinds and order, one example each, the wording-only line, the model-read line).
6. **What it can do** (`capability`, id `can`): as before.
7. **A step that did not work**, and the **footer**, as before.

Questions before use moved to `details.html` (owner, 2026-10-26).

The security headline (`headline`), from the concern rows:

   - With concerns: "Walkdown found security concerns in this repository: <N> places, of <K>
     kinds." When the reader marked some Not concerned: "(<M> of them marked Not concerned)".
   - With none: "Walkdown found none of the security concerns it looks for." The page's one
     qualifier is in the footer.
   - When a step produced no output (`not_run`), never "found none": 'This run did not complete:
     the step "<name>" did not run' (or '<n> steps did not run, starting with "<name>"'), then
     either "so Walkdown cannot say whether this repository has the security concerns it looks
     for." or, with concerns from the steps that ran, "In the steps that ran, Walkdown found
     security concerns: ..." (2026-10-21, an outside tester: an empty .venv crashed stage 1 and
     the page read as clean).
   - With none, and a step that ran did not pass its fixture check (`failed_checks`: any result
     but PASS and INCOMPLETE), never plain "found none": "Walkdown found none of the security
     concerns it looks for, but not every step worked, so it may have missed some." (owner,
     2026-10-25, review C40: a FAIL had sat under "found none", with the warning at the bottom).
     With concerns, the headline stays as above and the warning at the bottom names the step.

The concern rows, the boxes, and the warning:

- **Is it safe?** One row per concern kind that has a place, in this fixed order
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
- **What it can do.** No lede (the footer covers what a static read can show). The three boxes in one row, checked first, colored as in `details.html`,
   with no lists, linked to `details.html#trifecta`. Under them, "Each one is ordinary on its
   own. A tool that does all three can be steered by text from outside into sending your data
   away." (`TOGETHER`, from `details_html.TRIFECTA_LEDE`), then one line naming the general
   risks present ("Also: runs commands on its own, adds text before you type, ...").
- **A step that did not work**, only then (`failed_steps`, `warning`; at the bottom, owner
   2026-10-21): "Not every step worked in this run.", each such step by its plain name with "did
   not run" (no output) or "did not pass its fixture check (<result>)" (FAIL, ERROR, or any
   result but PASS and INCOMPLETE). Two things never reach this page (owner, 2026-10-25): a step
   with nothing in this repository to test, and a fixture check that did not run because an
   optional tool is not installed (an INCOMPLETE stamp, on any stage, whether or not the
   repository has files that tool reads). `details.html` (Other details) and `full.md` still list
   both. Then that a step that did not work can miss places so the page may show
   fewer than there are, and a link to Other details on `details.html`. A run made without
   validation has no stamps and gets no line for them.
- **Footer** (`FOOTER`), the page's one qualifier, in plain words: "Walkdown reads a
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
   nothing found does not mean safe (`test_headline_with_and_without_concerns`); with a step
   that did not run, it says the run did not complete (`test_a_run_missing_a_step_never_reads_as_clean`);
   with none and a step that failed its fixture check, it says it may have missed some, and an
   INCOMPLETE stamp leaves "found none" as it is (`test_a_failed_check_never_reads_as_clean`).
2. Rows appear in the fixed order, only for kinds with places; each place is in exactly one row;
   wording-only places are one line (`test_rows_in_fixed_order_each_place_once`).
3. Each row has its count, one example linked to its review card, and a link to the details
   (`test_each_row_has_one_example_linked_and_a_more_link`); Not concerned marks are counted and
   skipped for the example (`test_not_concerned_marks_are_counted_and_skip_the_example`).
4. Model reads are one line and never concerns (`test_model_reads_are_one_line_and_never_concerns`).
5. The capability row and the questions; no not-checked line
   (`test_capability_and_questions_and_no_not_checked`, `test_questions_before_use_follow_the_evidence`).
6. A step that did not run or failed its fixture check is named at the bottom; an INCOMPLETE
   stamp on any stage is not, even when the repository has files the missing tool reads; with
   every step working, or no stamps, there is no warning
   (`test_a_step_that_did_not_work_is_named_at_the_bottom`).
7. No verdict words; artifact text escaped (`test_no_verdict_words_and_escaping`). Checked by eye
   on a Plumbline run (2026-10-20): about two laptop screens, nothing wider than the page.

## Done when, slice 1 (2026-10-26)

8. The sections come in the order above; the cost sentence gives files, every session, and the
   largest skill against the context; over the context it says so; the ship block gives the
   three bands and the saving; a run with no tiers says not measured; Questions before use is
   not on this page (`test_builders_page_costs_and_ships`).

## Done when, slice 2 (2026-10-26)

9. Will it run on someone else's machine? sits after What you ship; it names the programs and
   packages, what is not declared, and one row per kind with its first place; with nothing,
   "Nothing found that ties it to one machine." (`test_will_it_run_elsewhere`).

## Done when, slice 3 (2026-10-26)

10. Is it ready for any AI? sits after Will it run on someone else's machine?; the to-do list comes
    first only with `--hosts`; it gives the host lines, the skills to install, the copies that
    differ, and the feature rows; a run without host findings says not measured; the brief's line
    counts hosts, differing copies, features, and what the hosts named are missing
    (`test_is_it_ready_for_any_ai`).

## Done when, slice 6 (2026-10-27)

13. Is it current and clean? sits between Do the tools fit the job? and Is it safe?, with no line of
    the repository's; under What it costs, "Since run <name>: <cost line>." when the earlier run is
    comparable; the brief's line counts each kind (`test_is_it_current_and_clean_and_cost_since`).

## Done when, slice 5 (2026-10-26)

12. Do the tools fit the job? sits between Is it ready for any AI? and Is it safe?; one row per kind
    with its first place; a run without it says not measured; the brief's line counts unused grants,
    tasks with no tool, loops with no stated limit, and hooks on every prompt or tool call
    (`test_do_the_tools_fit_the_job`).

## Done when, slice 4 (2026-10-26)

11. Will it trigger? sits between the headline and What it costs; it gives the entries line, the
    listing, and the rows; a run without trigger findings says not measured; the brief's line counts
    entries by kind, places that break a host rule, guidance rows, and overlapping pairs
    (`test_will_it_trigger_comes_first`).

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
