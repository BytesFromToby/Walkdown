# glance.py: spec

Status: built 2026-10-27 (report v3, "glance and know"; the design and the owner's decisions are
in `pre-planning/SPEC-REPORT-V3-2026-10-27.md`).

The eight questions both pages answer, as data, and the page shell both pages use. It reads the
same findings as every other output and detects nothing.

## The reader

Someone with no computer skills. Plain words, file names only in small grey "where" notes, and
tokens named in one place only (question 2). Every sentence is a fixed template filled from
findings, so it says the same thing on any repository.

## Inputs

`questions(meta, reports, stamps, runs_ok, marks=None) -> list[Q]`. `meta["context"]` is the
expected context (default `render.DEFAULT_CONTEXT`, 32,000); `meta["hosts"]` the tools named with
`--hosts`; `marks` the run's marks, own or carried (`marks.SPEC.md`).

`Q`: `id`, `question`, `chip`, `tone` (`look`, `notes`, `fact`, `none`, `unmeasured`), `answer`
(escaped HTML), `bullets` (HTML), `more` (on both pages), `detail` (on `details.html` only).

## Chips

Never a verdict. **N to look at** (amber: a host rule, a security kind, or the words against the
grants found something), **N notes** (amber: published guidance and harmless facts), a **fact**
(blue: a measure), **Nothing to look at** (green: the checks ran and found nothing), **Not
measured** (grey: the run was made before the check, or a step did not run; never "nothing").

## The eight questions, in order

1. **Will its skills switch on when they should?** (`switch`; slice 4). Not measured without
   `trig.entry`. To look at: frontmatter not read, agents not loaded, name and description rules,
   unknown keys with a near match, values, tool names, overlaps, cut descriptions; notes: guidance,
   unknown keys with no near match, the listing over its room. Answers: "<N> of the <skills and
   helpers> won't switch on as written: ..."; "Yes. <N> of the ... switch on by themselves; <M>
   only when you ask for them by name."; "Yes. All <...> are set up to switch on by themselves.";
   "Yes. Its one skill is set up to switch on by itself." Detail: every entry in a table, every
   place by kind.
2. **How much of the AI's memory does it use?** (`memory`; slice 1; the one place for tokens). Not
   measured without stage 5's cost. Chip (fact): "under 1%", "up to N%", or "more than fits": the
   largest entry at its fullest (or what it always loads) against the expected context. Answer:
   "<Very little | A small part | About N%> on Claude. On <a local AI | your AI>, its biggest <kind>
   takes <about a fifth | ...> of the memory."; at Claude's context, "On Claude, ...". More: what a
   token is; the table (rows: Always there once installed; Its biggest <kind> (<name>), with
   everything it reads; Extra, only when someone works inside <folder>; Unused files, if the AI were
   told to open them all), columns "Local AI (32k tokens)" at the default, "Your AI (<N>k tokens)"
   otherwise, then "Claude (200k tokens)" unless the context is Claude's; the room for the skill
   list; "Since run <name>: <cost line>." when the earlier run is comparable (`since_line`).
   Detail: how big each skill and helper gets, as bars.
3. **What comes in the package?** (`package`; slice 1). Not measured without file groups. Chip
   (fact): "<N> extra files" or "Nothing extra". Answer: "<W> of its <F> files do the work. The other
   <N> come along without being used." More: one stacked bar of the four groups (do the work, notes
   for people, tests and build tools, nothing refers to them), the legend, and the saving (a fact,
   never an order). Detail: every file by group; **Files worth a look** (`details_html.file_concerns`:
   unknown or mismatched types, archives, symlinks, files longer than a reviewer's viewer shows).
4. **Will it work on someone else's computer?** (`elsewhere`; slice 2). Not measured unless the run
   found programs, packages, or places here, or holds slice 3's `host.coverage` (there is no marker
   finding; `render.needs_of`). Chip: one to look at per kind (programs never declared, or packages
   when every program is; each `port.*` kind; case-only references). Answer: "<Two> things could
   trip it up on another computer." or "Yes. Everything it uses is something it says to install,
   and nothing ties it to one computer." Bullets: one template per kind (`PORT_PLAIN`), with "(N
   of them in <folder>/)" when one top folder holds half or more. Detail: the largest kind by file,
   the programs table, every place by kind.
5. **Will it work with AI tools other than Claude?** (`hosts`; slice 3). Not measured without host
   findings. Chip (fact): "Claude Code only" when no other tool has files; "<N> of 7 tools"; with
   `--hosts`, "<N> missing for your tools" or "Nothing missing for your tools". Answer: "<N> of the
   7 AI tools Walkdown knows find its files where they sit." Bullets: the to-do list first with
   `--hosts`; copies that differ; one line per kind of one-tool feature (`FEATURE_PLAIN`); a tile
   per tool. Never says which tool a repository should support.
6. **Does it ask only for the tools it needs?** (`tools`; slice 5). Not measured without
   `fit.checked`. To look at: unused grants, tasks with no tool, read-only claims contradicted,
   loops with no stated limit, hooks on every prompt or tool call. Answer with none: "Yes. Every
   tool it is allowed to use is one it actually uses, and nothing it asks for is missing." Bullets:
   one per kind (`FIT_PLAIN`). Detail: every place by kind, the helpers and their tools.
7. **Is it finished and up to date?** (`clean`; slice 6). Not measured without `clean.checked`.
   Notes: unfinished text, dated claims, older tool names; pinned model IDs are a fact inside.
   Answers: "Nearly. <counts>." or "Yes. No unfinished notes, no dates that will go stale, and no
   older tool names." The summary shows no line of the repository's; details quotes each place.
8. **Anything to be careful about?** (`careful`). Rows from `summary_html.rows` (the fixed concern
   kinds and order). Chip: "<N> to look at"; "Nothing found" (never "safe"); "Not checked" when a
   step did not run and nothing was found. Answers: one kind, "<N> place(s) has/have <plain row
   name>." ("Both are the same text." when the hidden places share their text); several, "Walkdown
   found <N> places worth a look, of <K> kinds: <short names>."; none, "Walkdown found none of the
   security concerns it looks for." with " Not every step worked, so it may have missed some." when
   a step failed its fixture check or did not run; a step that did not run and nothing found, "This
   run did not complete: ..., so Walkdown cannot say whether it has any of these." Bullets: per row,
   its name, count, and first place; for hidden text, what it says, up to 80 characters with comment
   marks taken out (the one repository text on the summary); the wording-only count; "<M> of <N>
   places marked so far. Go through each place and mark it." (`marked_line`: the rule-found review
   cards, any mark, own or carried). More: What it can do (the three boxes ticked or crossed; left
   out when stage 5 did not run), what all three together risk, and what installing it allows.
   Detail: the credit (the lethal trifecta, Simon Willison's name) and why it can do these; **Every
   place, by kind** (a fold per row, each place linked to its review card, quoted, with Walkdown's
   note for any kind but a phrase match, and a model read that questions it); hidden text (by how
   it hides, by file, every place; lines read differently once invisible characters or look-alike
   letters are swapped, typography left out; text in another alphabet or language; "Nothing hidden
   from people." only when there is none of these); wording that shapes how the AI decides, by
   group; worth reading first; web addresses by site (gathered, never opened); passwords and keys
   (never the value; test data set aside; "Not checked" without a scanner).

**Counting.** A place counts once, as `review.html` counts it: findings on one line are one place
(`summary_html.rows` ids, `total`, `wording_count`). A place may fall in two rows; the answer's
total counts it once.

## The page shell

`CSS` (theme tokens for light and dark, the validated palette, phone width with no page-wide
scroll), `SCRIPT` (tooltips on `data-tip`, by mouse and keyboard), `page`, `card` (the head always
shown; "More ›" only when there is more), `section`, `meta_line` ("Checked <day> · version <hash7>
(or folder) · <N> files · <license>"), `short_license` (the license's name only, never a file's
text; `details.html` adds the full line), `what_it_is` (nothing when stage 1 did not run),
`since_line`, `changes_section`, `not_checked` (steps that did not work, model reads not run,
every limit folded).

## Must never

- Say "safe", "unsafe", or "do not use", or give a score, grade, or rank.
- Name tokens on the summary outside question 2.
- Quote the repository on the summary, but for hidden text that reads like an instruction (80
  characters); never a license file's text there.
- Say "nothing" for a check that did not run.
- Show a secret's value, or open, fetch, or check a link.
- Emit unescaped repository text.

## Done when

Tests in `tests/test_summary_html.py` (the cards), `tests/test_details_html.py` (the sections),
`tests/test_review_html.py`, `tests/test_run.py`, and `tests/test_marks.py`:

1. Eight questions in order, title, footer, theme tokens (`test_eight_questions_in_order_title_and_footer`,
   `test_order_title_toc_and_theme_tokens`).
2. Each question's chip, answer, and bullets on fixture findings (`test_switch_question_comes_first`,
   `test_memory_question_one_table_and_the_since_line`, `test_package_question`,
   `test_elsewhere_question`, `test_hosts_question`, `test_tools_question`, `test_clean_question`,
   `test_careful_card_answer_bullets_and_what_it_can_do`, `test_one_kind_answer_names_it`), and
   everything behind them on details (`test_question_sections_carry_everything_behind_them`).
3. Not measured, never "nothing", for a check the run did not make (`test_unmeasured_questions_say_so`,
   `test_elsewhere_question`); a step that did not run or failed never reads as clean
   (`test_a_failed_check_never_reads_as_clean`, `test_a_run_missing_a_step_never_reads_as_clean`).
4. Tokens in question 2 only (`test_tokens_are_named_in_one_place`); the summary quotes only hidden
   text (`test_summary_quotes_only_hidden_text`); the license by name only
   (`test_license_line_in_header`, `test_license_line_unrecognized_field_none_and_old_run`).
5. A place counts once (`test_a_place_counts_once_as_review_html_counts_it`,
   `test_one_card_for_one_place_named_by_several_findings`); marks counted
   (`test_marks_are_counted_and_skip_the_example`, `test_a_carried_mark_keeps_from_and_the_pages_show_it`).
6. Every place by kind, linked and quoted; hidden text, folded lines, other languages, secrets,
   links, the trifecta credit, files worth a look (the details tests of those names).
7. Checked by eye on an audited plugin's run (2026-10-27) in a browser, at desktop and phone width,
   in the light theme (the dark theme's tokens are tested, not seen).

## History

- 2026-10-27: built (owner: "Let build the back end for the new reports"), from the two pages the
  owner approved on an audited plugin's run. Owner decisions: the old pages replaced outright; marking on
  `review.html` only; "Yes." answers kept; the summary quotes only hidden instructions. The recount
  on every audited run the same day: a place counts once, as on `review.html`; question 4 says Not
  measured on a run made before slice 2; "under 1%" as a chip; one entry in the singular; the
  license by name only on the summary; Files worth a look, the trifecta credit, the folded-line
  count, and other alphabets kept from the page before.
