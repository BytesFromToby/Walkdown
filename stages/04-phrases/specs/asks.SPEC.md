# asks.py: spec

What the text asks a tool to do, and loops with no stated limit (plan for builders, slice 5,
owner 2026-10-26; the slice spec is `pre-planning/SPEC-SLICE5-2026-10-26.md`). Stage 4 calls it
with the texts it reads, the scripts and hook configs its audience rules use, and the MCP servers
the entries grant tools from (`servers_of`, over slice 4's `trig.entry` grants). It runs nothing.

## Data: `asks.yaml`

Dated: the cue rules for each family of work (a rule is patterns that must all match one
sentence), the tool names that count when named outright, and the loop and limit patterns.
Measured on the audited repositories before they were kept (see History).

## What it reads

Every file whose audience is `model` or `subagent` (text the AI reads), with its frontmatter
blanked (a tools list names tools; it asks for nothing), line numbers kept. A **sentence** is a
line joined with the next while it does not end in `.`, `!`, `?`, `:`, or `;`, never across a
blank line, a list item, a heading, a quote, a table row, or fenced code, which is left out.

## Findings

- **`ask.tools`**, one per file and family (`shell`, `write`, `web`, `search`, `agent`) the file
  asks for: `family`, `lines` (each sentence's first line), `line` (the first), `audience`. A
  family is asked for when a sentence matches one of its rules; `shell` also from slice 2's
  command scan of a Markdown file (a known program in a shell block or inline code).
- **`ask.named`**, one per tool named outright (`` `Bash` ``, "the Bash tool", `Bash(`), and one
  per granted MCP server named (`mcp__<server>` or the server's name as a word, as
  `mcp__<server>`): `tool`, `lines`. A named tool counts as used, never as a task asked for (the
  line may forbid it).
- **`fit.loop`**: a line outside fenced code that matches a loop pattern, with no limit pattern on
  it or the next line: `quote`, `audience`. "No stated limit", never "no limit": a limit may be
  stated elsewhere (owner, 2026-10-26).

Stage 4 adds these last, after `trig.*`.

## Must never

- Read a file written for people, a script, or test data; count frontmatter or fenced code (other
  than slice 2's shell scan) as asking for anything.

## Done when

1. Fixture `asks-repo` (grader 04, rows `ask-*`, `loop*`): each family on its line, a named tool,
   a loop with no stated limit; negatives: a writing verb with no object, a limit on the loop's
   line or the next, a README written for people.
2. `tests/test_asks.py`: sentences joined and split, fenced code and frontmatter left out, MCP
   servers named, loop limits on the next line only.

## History

- 2026-10-26: built (slice 5).
