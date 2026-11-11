# specimen.py (added 2026-11-05, owner, R10)

The specimen run: made-up findings, at least one of every kind the pages know, so the whole report can be seen and judged at
once. A real run shows only what its repository holds, and the owner found the whole report hard to judge from one
repository's run. No repository is audited, no step runs, and no model is called. The findings come from
`stages/06-report/tests/specimen_run.py`, which reuses the report tests' builders (`test_render.py`) and, where a test does, the
builder step's own code (`trigger.findings`, `hosts.findings`), so each finding has the shape a step writes.

## Inputs

`python tools/specimen.py [--out DIR] [--variant NAME ...]`; the default out is `RepoResults/specimen` (not in git). With no
`--variant`, every variant is written.

## Outputs

- One folder per variant, `<out>/<variant>/`, written fresh: `summary.html`, `details.html`, `review.html`, `full.md`, and
  `brief.md`, drawn by the report stage's own writers (`run.write_reports`, `brief.write`). The check of the run is made from
  the same made-up facts by the check's own code (`qa_support.Q`).
- At the top of every page, and the first line of `full.md` and `brief.md`: "Specimen: every finding on this page is made up,
  to show what the report can say. No repository was audited.", the variant, what it shows, and a link to the index.
- `<out>/index.html`: every variant, a link to each of its pages, and what it shows.

## The variants (`specimen_run.VARIANTS`)

| Variant | Shows |
|---|---|
| `everything` | every kind of finding, every step passed, both model reads answered, changes since a run before |
| `nothing-found` | every step ran and passed, and found nothing: the clean states |
| `step-failed` | everything, one step failed its fixture check, one skipped part of its check for a missing tool |
| `step-did-not-run` | everything, one coded step left no output |
| `stopped` | a run stopped with `--until` after the coded steps, a model read's input written and not sent |
| `model-read-no-answer` | everything, the model read got no answer for any passage |
| `not-measured` | a run made before the builder checks: questions 1 to 6 and Misalignment say Not measured |
| `only-in-full-md` | every step passed, and the only lines found match patterns kept off the summary's list (a line that hides from the user, one that turns off confirmations, one that sends usage data): "None on the list", and how many lines `full.md` has (R28) |
| `every-pattern` | one made-up line for every pattern in `Library/patterns.yaml`, each on a line of its own from line 200: a pattern on the summary's list is a place under its family's title, any other is in `full.md` only and counted on the careful card (R30) |

## What "every kind" means

The kinds stored in the Library tables (`tools.yaml`, `hosts.yaml`, `fit.yaml`, `clean.yaml`) and in the
report code (Misalignment's groups, `render.FORMAT_GROUPS`; `summary_html.CONCERNS`, `details_html.CARRIER_PLAIN`, `details_html.FAMILY` (one
line per family, taken from `FAMILY` itself, R30), the reasons of
`details_html.file_concerns`, the tiers of `coverage.LABEL`), plus the sections and notes no table lists: What it can do, What
Walkdown examined, Misalignment (Skill Formatting, Descriptions too alike), What changed, the license line, web addresses, passwords and keys,
what installing it grants and what its wording asks for (R31: one grant from the settings, one from both, two from the wording
alone), and the notes on a place
(what hidden characters spell, what base64 decodes to, a line of an MCP server's code the AI reads, a command Cursor runs on
its own machine). The trigger kinds of `trigger.yaml` left the pages with question 1 (R13, 2026-11-05); the specimen
still makes them, and no page shows them.

## Must never

- Read, audit, or write inside a repository; call a model; or write outside `--out`.
- Leave a page without the line that its findings are made up.

## Done when (tests in `tests/test_specimen.py`)

1. Every variant has every page, each saying its findings are made up, and the index links them
   (`test_every_variant_is_written_with_every_page_and_says_its_findings_are_made_up`).
2. Every kind above shows on the `everything` pages, and a kind the pages know that the specimen does not hold fails the test
   by name (`test_every_kind_the_tables_and_the_pages_know_shows_in_everything`; checked 2026-11-05 by taking the overlap
   pair out: the test failed naming "Descriptions that overlap").
3. Each variant shows the state it is for (`test_each_variant_shows_the_state_it_is_for`); an unknown variant is refused
   (`test_a_variant_it_does_not_know_is_refused`).
4. In `every-pattern`, the patterns that are places are exactly the patterns on the summary's list, each shows under its
   family's title, the careful card counts the rest, and `full.md` cites every one
   (`test_every_pattern_shows_where_the_list_puts_it`).

## History

- 2026-11-07 (owner, R28 to R31: "This is where the tests and Specimen come in"): the variants `only-in-full-md` and
  `every-pattern`; the family lines of `everything` come from `details_html.FAMILY` (they were eleven fixed prefixes, so a
  new family was never shown); its grants carry `sources`, one from the settings, one from both, two from the wording. No
  run had triggered 47 patterns, so no page had shown where they land: 45 of them never reached the summary.
- 2026-11-05: built (owner: "build the specimen run"), from `pre-planning/REPORT-CHANGES-2026-11-05.md` R10.
- 2026-11-06 (R22): "everything"'s one-system finding carries `os: windows`, as real `port.os` findings carry `os`, so the
  system boxes show both states (Windows blue; Mac and Linux with a yellow outline).
- 2026-11-05 (owner, R17): "everything"'s `skills/d` sets `license` twice, for Skill Formatting's "Settings set more than once".
- 2026-11-05 (owner, R13): "everything" holds every Misalignment group (a skill with no settings block, one whose `compatibility` is over 500 characters, one with a `version` line); Nitty gritty and the trigger kinds left the pages, and the test of every kind looks for Misalignment's groups.
