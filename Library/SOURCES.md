# Sources

Where the Library's tables get their facts, listed once. A table says where a fact came from by
an ID from this file, or by a section of the two public reference documents. This file says what
each source is, when it was last checked, and what Walkdown took from it.

## How a table cites a source

A `source` field (or each value of a `sources` mapping) in a Library table holds one or more
references, joined with `; `. A reference is one of:

- **An outside source**: `S01` to `S20`, below. The only place a link to an outside page is written.
- **A Walkdown document**: `I01` to `I15`, below. `I01` and `I02` are the two public reference
  documents (`PHRASES.md`, `THREATS.md`). The others are Walkdown's own design documents. Some are in
  the repository: a stage's `CONTEXT.md` and spec files ship with the code. Others are not published:
  anything under `pre-planning/`, and a tool that was removed. Each entry says which.
- **A section of a public document**: `PHRASES:<set>` (a lettered set in `PHRASES.md`) or
  `THREATS:<class>` (a numbered class in `THREATS.md`, or `trifecta`). The section is a heading in
  that file.

No table holds a raw link. A made-up address on a reserved name, like `https://x.invalid/a.sh` in
`patterns.yaml`, is part of an example, not a source. `stages/_shared/tests/test_library_docs.py`
checks that every reference in a table resolves here or to a heading, and that no table holds a link.

**Titles** are Walkdown's short labels for each page, not the page's own heading. **Last checked** is
the date the citing table gives. Walkdown copies none of these pages; "Taken" says what its table
holds because of the page.

## Outside sources

### S01 Agent Skills specification
- Link: https://agentskills.io/specification
- Last checked: 2026-10-26 (`trigger.yaml`, `loading.yaml`)
- Taken: the frontmatter keys of the open skill format; the rule for a skill's name (1 to 64
  characters, lowercase letters, digits, single hyphens, matching its folder); that only name and
  description load at startup, the whole SKILL.md loads when the skill is used, and other files load
  when needed; the size guidance.
- Cited in: `trigger.yaml` (`sources.spec`), `loading.yaml` (fact 1), `hosts.yaml` (a comment on
  `skill_keys`, "the frontmatter keys of the Agent Skills format").

### S02 Agent skill best practices (Anthropic)
- Link: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- Last checked: 2026-10-27 (`clean.yaml`); 2026-10-26 (`trigger.yaml`)
- Taken: the published advice that a description says what the skill does and when to use it, in the
  third person; and that text with a date that can expire ("before August 2025, use the old API") ages.
- Cited in: `trigger.yaml` (`sources.guidance`), `clean.yaml` (`sources.guidance`).

### S03 Claude Code: skills
- Link: https://code.claude.com/docs/en/skills
- Last checked: 2026-10-26 (`trigger.yaml`, `fit.yaml`, `loading.yaml`, `hosts.yaml`)
- Taken: which frontmatter keys Claude Code reads in a skill; that skill descriptions stay in the AI's
  context every session and the full skill loads only when used, then stays; that a description plus
  its when-to-use text is cut at 1,536 characters in the listing; that scripts are run, not loaded;
  where Claude Code looks for skills.
- Cited in: `trigger.yaml` (`sources.skills`), `fit.yaml` (`sources.skills`), `loading.yaml` (fact 2),
  `hosts.yaml` (`hosts.claude.source`).

### S04 Claude Code: subagents
- Link: https://code.claude.com/docs/en/sub-agents
- Last checked: 2026-10-26 (`trigger.yaml`, `fit.yaml`, `loading.yaml`)
- Taken: the frontmatter keys and documented values of an agent definition (model, color, permission
  mode, effort, isolation, memory); that a subagent's description loads at session start and its body
  only when it runs, in its own context.
- Cited in: `trigger.yaml` (`sources.subagents`), `fit.yaml` (`sources.subagents`), `loading.yaml`
  (fact 3).

### S05 Claude Code: tools reference
- Link: https://code.claude.com/docs/en/tools-reference
- Last checked: 2026-10-26 (`trigger.yaml`)
- Taken: the exact names of Claude Code's built-in tools, so a name no host knows can be listed.
- Cited in: `trigger.yaml` (`sources.tools`; the `tools` list).

### S06 Claude Code: hooks
- Link: https://code.claude.com/docs/en/hooks
- Last checked: 2026-10-26 (`fit.yaml`)
- Taken: the names of Claude Code's hook events, how often each runs (every prompt, every tool call,
  every turn, once a session), which put plain output in the AI's context, and the output size cap.
- Cited in: `fit.yaml` (`sources.hooks`).

### S07 Claude Code: memory
- Link: https://code.claude.com/docs/en/memory
- Last checked: 2026-10-26 (`hosts.yaml`, `loading.yaml`)
- Taken: which instruction files Claude Code reads and where (CLAUDE.md in several places, the rules
  folder, AGENTS.md only when there is no CLAUDE.md); that they load at launch; that `@path` imports
  expand up to four hops deep.
- Cited in: `hosts.yaml` (`hosts.claude.source`), `loading.yaml` (fact 4).

### S08 Claude Code: model configuration
- Link: https://code.claude.com/docs/en/model-config
- Last checked: 2026-10-27 (`clean.yaml`)
- Taken: which names are aliases (sonnet, opus, haiku) as opposed to a pinned model ID.
- Cited in: `clean.yaml` (`sources.models`).

### S09 Codex: build skills
- Link: https://learn.chatgpt.com/docs/build-skills
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: that Codex reads AGENTS.md and looks for skills in `.agents/skills`.
- Cited in: `hosts.yaml` (`hosts.codex.source`).

### S10 Gemini CLI: GEMINI.md context files
- Link: https://geminicli.com/docs/cli/gemini-md.md
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: that Gemini CLI reads GEMINI.md, and AGENTS.md too when its settings name that file.
- Cited in: `hosts.yaml` (`hosts.gemini.source`).

### S11 Gemini CLI: skills
- Link: https://geminicli.com/docs/cli/skills/
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: the folders Gemini CLI looks in for skills.
- Cited in: `hosts.yaml` (`hosts.gemini.source`).

### S12 Cursor: rules
- Link: https://cursor.com/docs/context/rules
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: which instruction files Cursor reads (its rules folder, AGENTS.md, the older rules file).
- Cited in: `hosts.yaml` (`hosts.cursor.source`).

### S13 Cursor: skills
- Link: https://cursor.com/docs/skills
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: the folders Cursor looks in for skills, including ones other hosts use.
- Cited in: `hosts.yaml` (`hosts.cursor.source`).

### S14 Cursor: hooks
- Link: https://cursor.com/docs/agent/hooks
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: the files where Cursor takes its hooks.
- Cited in: `hosts.yaml` (`hosts.cursor.source`).

### S15 GitHub Copilot: customization cheat sheet
- Link: https://docs.github.com/en/copilot/reference/customization-cheat-sheet
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: which files Copilot reads for instructions, skills, hooks, and MCP servers.
- Cited in: `hosts.yaml` (`hosts.copilot.source`).

### S16 Windsurf: Cascade memories and rules
- Link: https://docs.windsurf.com/windsurf/cascade/memories.md
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: which files Windsurf reads for rules (its rules folder, AGENTS.md, the older rules file).
- Cited in: `hosts.yaml` (`hosts.windsurf.source`).

### S17 AGENTS.md
- Link: https://agents.md/
- Last checked: 2026-10-26 (`hosts.yaml`)
- Taken: that AGENTS.md is a shared instruction file several tools read.
- Cited in: `hosts.yaml` (`hosts.agents-md.source`).

### S18 RFC 2606, reserved top-level domain names
- Link: https://www.rfc-editor.org/rfc/rfc2606
- Last checked: no date in the table (`vocab.yaml` carries none for it)
- Taken: that `invalid`, `test`, `example`, and `localhost` are names reserved so examples can use
  them; Walkdown counts them as domain endings so inert fixtures and docs examples are still seen.
- Cited in: `vocab.yaml` (the comment above `endpoints.tlds`).

### S19 Unicode Character Database: Default_Ignorable_Code_Point
- Link: https://www.unicode.org/Public/UCD/latest/ucd/DerivedCoreProperties.txt
- Last checked: 2026-10-29 (`invisible.yaml`; the property is read from the `regex` package's copy of the database in a test)
- Taken: which code points the Unicode standard marks as default-ignorable, meaning a renderer draws
  nothing for them when it has no glyph. Every range in the table whose code points have the property
  cites this entry, and a test holds the table to it: every assigned code point with the property is
  listed. The interlinear annotation marks (U+FFF9 to U+FFFB) and the blank braille cell (U+2800) do
  not have the property and do not cite it.
- Cited in: `invisible.yaml` (`source`, on each range whose code points have the property).

### S20 NVIDIA SkillSpector
- Link: https://github.com/NVIDIA/SkillSpector
- Last checked: 2026-11-03 (commit e14c450; Apache-2.0)
- Taken: the idea for five pattern rows and for reading MCP descriptions as model text, from its rule list: AR1 (refusal
  suppression) for `L.never-refuse`, AR2 (disclaimer suppression) for `L.no-disclaimer`, SC3 (obfuscated code) for `E.decode-exec`,
  TM3 (unsafe defaults: disabled TLS) for `E.tls-off`, SC10 (dependency source redirection) for `E.registry-config`, and TP1 and TP3
  (hidden instructions in MCP tool and parameter descriptions) for `02.4-phrases`'s `tooltext`. Walkdown's regexes and code are its
  own; none of its rules or tests were copied, and its scores and labels are not used.
- Cited in: `patterns.yaml` (`source` of the five rows); `02.4-phrases`'s spec (`tooltext`).

### Named in a table, not listed above
- `tools.yaml` says it was "checked 2026-10-26 against each system's own tools" and lists Node's
  built-in modules. It names no page and gives no link, so there is no entry to write. The same
  holds for the Claude Code version note in `trigger.yaml` (booleans, "v2.1.218+").

## Walkdown's own documents

### I01 PHRASES
- Where: in the repository (`Library/PHRASES.md`), public
- What it holds: the lettered sets of wording the pattern rows look for (A to E, G to L), each with
  what it is, why it matters, what Walkdown looks for, and the pattern ids that cite it. Each set is
  a heading; a table cites one as `PHRASES:<set>`.
- Cited in: `patterns.yaml` (the rows that cite a lettered set; some rows cite a set and a class
  both), `vocab.yaml` (`rubric.source`, `terms.source`).

### I02 THREATS
- Where: in the repository (`Library/THREATS.md`), public
- What it holds: the threat classes the tables cite (1 to 5, 7, 8, 13 to 17, 19 to 22) and the
  trifecta frame, each with what it is, why it matters, what Walkdown looks for, and the pattern
  ids that cite it. Each class is a heading; a table cites one as `THREATS:<class>`. The numbers are
  stable tags on findings.
- Cited in: `patterns.yaml` (the rows that cite a numbered class), `vocab.yaml`
  (`rubric.source`, `endpoints.source`, `terms.source`), `softreads.yaml` (the sweep and its seven
  options: `sweep.options.none.source` cites the document as a whole), `invisible.yaml` (class 4,
  hidden and obfuscated instructions), `capability.yaml` (`source`, the trifecta).

## Other Walkdown documents

These are Walkdown's own design documents, specs, and notes. The tables cite them by ID. Each entry
says where the file lives: "in the repository" for a stage file (it ships with the code), or "not
published" for a file under `pre-planning/` or a tool that was removed.

### I03 02.4-phrases spec, part 2
- Where: in the repository (`stages/02-coded/02.4-phrases/specs/phrases.SPEC.md`)
- What it holds: part 2 of its "The stage" section, the contract for the second half of 02.4-phrases (it
  was a separate file, `CONTEXT-part2.md`, until restructure step 8a): the harness rubric (section 1:
  the confirmation words and the negation forms), the endpoint census (section 2: schemes, domain
  endings, registries, local hosts), and the term table (section 4: the definition cues and the
  safety vocabulary).
- Cited in: `vocab.yaml` (every `source` in the file).

### I04 Reporting design
- Where: not published (`pre-planning/REPORTING.md`)
- What it holds: how results are reported; section 4.1 is the undocumented-endpoints idea behind the
  endpoint census.
- Cited in: `vocab.yaml` (`endpoints.source`).

### I05 Method
- Where: not published (`pre-planning/METHOD.md`)
- What it holds: the ordered stages of the audit; the 02.4-phrases term table and its safety vocabulary.
- Cited in: `vocab.yaml` (`terms.source`, `terms.safety.source`).

### I06 Red team
- Where: not published (`pre-planning/RED-TEAM.md`)
- What it holds: how an attacker would approach Walkdown; section 11 is writing for the subagent.
- Cited in: `patterns.yaml` (`C.guard-instruction`).

### I07 02.4-phrases spec, part 1
- Where: in the repository (`stages/02-coded/02.4-phrases/specs/phrases.SPEC.md`)
- What it holds: its "The stage" section before part 2, the contract for 02.4-phrases, part 1: the pattern
  table and what each check means, including the core shape of a data flow (a private data source, a
  sending verb, and a destination in one sentence).
- Cited in: `patterns.yaml` (`K.data-flow`).

### I08 02.5-capability spec, the rules
- Where: in the repository (`stages/02-coded/02.5-capability/specs/capability.SPEC.md`)
- What it holds: its "The rules" section, the contract for 02.5-capability: what makes each trifecta leg,
  what each install grant is, injection paths and bytes at load, and agent posture.
- Cited in: `capability.yaml` (`source`; every table in it).

### I09 Fold spec
- Where: in the repository (`stages/02-coded/02.2-reader/specs/reader.SPEC.md`)
- What it holds: its `fold` section, how 02.2-reader folds a file's text: which invisible characters are removed (item 1,
  with the runs of variation selectors) and which are turned into a space (item 2), what it does with
  a NUL, and which characters it reports as hidden.
- Cited in: `invisible.yaml` (every range).

### I10 Phrase-stage fold spec
- Where: in the repository (`stages/02-coded/02.4-phrases/specs/phrases.SPEC.md`)
- What it holds: its `foldtext` section, how 02.4-phrases folds a line before matching it; its item 2 is the same turn-into-a-space
  rule as 02.2-reader's.
- Cited in: `invisible.yaml` (the two separator ranges).

### I11 Sweep decision (D2)
- Where: not published (`pre-planning/soft/README.md`)
- What it holds: the decisions for the optional model reads; D2 is a model used as a coverage
  detector for passages no pattern matched, never replacing 02.4-phrases.
- Cited in: `softreads.yaml` (`sweep.source`).

### I12 Pinpoint decision and spec
- Where: partly both. The owner's decision of 2026-10-13 is recorded in the spec's opening lines and its
  History, and the spec is in the repository (`stages/04-pinpoint/specs/pinpoint.SPEC.md`). The
  prototype is not published (`pre-planning/soft/pinpoint/proto_pinpoint.py`).
- What it holds: why the pinpoint question exists (a sweep passage is too big for a newcomer to see
  which part is the issue), the prototype that tried it, and the spec of the stage.
- Cited in: `softreads.yaml` (`pinpoint.source`).

### I13 Endpoint extractor (removed)
- Where: not published (`tools/extract_urls.py`, a tool removed 2026-10-03; only the private git
  history has it)
- What it holds: an early script that pulled addresses from text. Its lesson, kept in the endpoint
  rules: script and file names (`.md`, `.sh`, `.py`) are not domains.
- Cited in: `vocab.yaml` (`endpoints.source`, and the comment above `endpoints.tlds`).

### I14 Plan for builders
- Where: not published (`pre-planning/PLAN-BUILDERS-2026-10-26.md`)
- What it holds: the plan, in slices 0 to 6, for the builder step's checks: what ships, what it
  costs, what ties it to one machine, which hosts read it, what triggers it, whether the tools fit,
  and whether it is current.
- Cited in: the opening comments of `hosts.yaml`, `trigger.yaml`, `tools.yaml`, `asks.yaml`,
  `clean.yaml`, `fit.yaml`, and `loading.yaml` (with the owner's decision and its date).

### I15 Builder spec
- Where: in the repository (`stages/02-coded/02.6-builder/specs/builder.SPEC.md`)
- What it holds: the spec of the builder checks, with a History of each list and the repositories it
  was measured on.
- Cited in: the opening comments of `asks.yaml` and `clean.yaml`.

### Decisions with a date
The tables' comments also record the owner's decisions with their dates (for example "owner,
2026-10-26"). A decision is not a document, so it has no ID; the comment is its record.

## Measured data

`baserates.json` cites no document. It counts how often each 02.4-phrases pattern hit in four audited
repositories, labeled `repo-1` to `repo-4`, each with the commit hash it was measured at, and is
written by `tools/baserates.py`.
