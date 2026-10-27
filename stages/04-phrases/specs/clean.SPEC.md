# clean.py: spec

Is it current and clean? (plan for builders, slice 6, owner 2026-10-27; the slice spec is
`pre-planning/SPEC-SLICE6-2026-10-27.md`). Stage 4 calls it with the texts it reads and the
scripts and hook configs its audience rules use. Facts with locations: nothing here says a date
is past, a model retired, or a TODO matters.

## Data: `clean.yaml`

Dated, with sources (the skill-authoring best practices; Claude Code's model configuration): the
unfinished-text patterns by kind, the template paths, the dated-claim patterns, and the model ID
patterns. Measured on the audited repositories before they were kept (History).

## What it reads

Every file but those written for people and test data (`audience`). In Markdown, each line is
`frontmatter`, `code` (fenced), or `text`, and inline code spans and quoted text are set aside in
text; any other file is `code`.

## Findings

Each with `file`, `line`, `audience`:

- **`clean.unfinished`** `kind`, `quote`: `todo` (TODO, FIXME, XXX, HACK, in their case) anywhere
  but fenced Markdown code; `placeholder` ("lorem ipsum", "[placeholder]", "[insert ...]",
  "REPLACE_ME", `{{name}}`) and `draft` (DRAFT, WIP, "work in progress", "not yet implemented",
  "coming soon", "under construction") in Markdown outside code only (in code, `{{x}}` is an
  f-string's brace). No placeholder in a `templates/` folder or a file named `*template*`.
- **`clean.dated`** `quote`: in Markdown text the AI reads (audience `model` or `subagent`), a date,
  month and year, or year after "before", "after", "since", "until", or "by"; a quarter
  ("Q3 2025"); or "as of". Published guidance ("avoid time-sensitive information"), never "out
  of date". A bare date is not a claim (owner's rule as measured, below).
- **`clean.model`** `model`, `where` (`frontmatter`, `code`, `text`): a pinned model ID, Claude's
  or another vendor's, once per line; never an alias, an ID ending in `-latest`, or a file name.
- **`clean.older`** `tool`, `now`: in Markdown text the AI reads, a tool named outright (`` `Task` ``,
  "the Task tool", `Task(`) that slice 4's `older_tools` lists; frontmatter is slice 4's
  (`trig.tool`).

Stage 4 adds these last, after slice 5's.

## Must never

- Say a date is past, a model retired, or an ID stale; read a file for people or test data.

## Done when

1. Fixture `clean-repo` (grader 04, rows `clean-*`): each kind on its line, a script's FIXME and
   model ID; negatives: a template's placeholder, a relative word, an alias, a README's TODO, a
   TODO in a fenced example.
2. `tests/test_clean.py`: regions, code versus text, file names, quoted mentions, the dated rule.

## History

- 2026-10-27: built (slice 6). Measured first: a full date alone counted 745 lines in Walkdown's
  own notes ("Done 2026-09-25", "(owner, 2026-10-20)"), records of when rather than claims that
  expire, so a date counts only after before, after, since, until, or by (39 left, each a
  "since ..." or "as of ..."); `{{...}}` in Python validators (f-string braces) made 75
  "placeholders" in one repository, so placeholders and drafts are read in Markdown only; a file
  name (`claude-fable-5.md`) read as a model ID.
