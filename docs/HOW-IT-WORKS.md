# How Walkdown works

This is the reference for what each stage checks, why, and how to read the result. It is
written for someone who wants to follow a finding back to the rule that produced it.

- How to read a report: [READING-THE-REPORT.md](READING-THE-REPORT.md)
- What a run folder holds: [RUN-FOLDER.md](RUN-FOLDER.md)
- The design history and measurements behind these rules: `pre-planning/`

## The shape of a run

```
the repository
   |
   1 Inventory     what ships
   2 Reader        what the model actually receives
   3 Graph         what loads what
   4 Phrases       what the text asks for
   5 Capability    what installing it grants          (derived from 1 to 4, detects nothing new)
   6 Soft reads    what a pattern cannot settle       (optional model reads)
   7 Not examined  what this run was blind to
   8 Report        assembles 1 to 7
```

Stages 1 to 5 are scripts: no model, the same answer every time. Stage 6 is optional and uses
a model you pick when you run it. Stage 8 writes the reports.

### Rules every stage follows

- **A finding is a location.** It says "this text, at this file and line, has this shape". It
  does not say the author meant harm. Intent cannot be read from a repository.
- **No score.** Nothing is added up into a rating. Two per-finding signals exist (a pattern's
  base rate, and a model read's "near the line" band); both are measurements, shown with the
  numbers behind them, never summed.
- **Benign hits are kept.** A pattern that matches innocent text is still recorded and counted.
  How often a pattern is innocent is what tells you how much a hit means.
- **Every stage is validated before it is trusted.** Each stage runs against fixtures, small
  repositories with known contents, and a grader scores it against an answer sheet the stage
  code never reads. The result is stamped in the run's LOG.md.
- **No model holds tools.** The stage 6 models get text and a question, and nothing else.

### Audience: who a file is written for

Most checks care about who reads a file. Walkdown decides it from the path:

| Audience | Files | Treated as |
|---|---|---|
| model | SKILL.md, CLAUDE.md, reference docs, anything not matched below | instructions the model reads |
| subagent | files under `agents/` or `commands/`, `*prompt*.md` | instructions a dispatched agent reads |
| tool | scripts (`.py`, `.sh`, `.js`, ...), hook configs, build and lock files | code; counted, read by tools |
| human | README, CHANGELOG, LICENSE, INSTALL, guides, anything under `docs/` or `.github/` | written for people; counted, kept out of capability |
| test-data | anything under `tests/`, `fixtures/`, `__tests__/`, `testdata/`, `spec/` and the like, or named `test_*.py`, `*.test.*`, `*.spec.*`, `conftest.py` | never loaded on install; counted, kept out of capability and the summary |

Human-facing and test-data hits are still recorded and listed in the full report. They are
kept out of the summary's points and out of stage 5's capability map, because installing the
artifact does not put them in front of a model. One exception: **test data that a model-read
file references directly** (a skill that says "read tests/fixtures/setup.md and follow it")
counts like any other file, and stage 5 lists it as a pair.

---

## Stage 1: Inventory, "What ships"

**Why.** You cannot judge what you have not counted. This stage lists every file and the
structures a host loads on its own: skills, agents, hooks, manifests, MCP servers.

| Check | What it records | Why it matters |
|---|---|---|
| `inv.pin` | the source, and its git commit or sha256 | every later finding is about exactly this version |
| `inv.file` | each file: type, size, lines, encoding, executable bit, and whether it is an entry point (skill, agent, command, hook config, manifest, MCP config, readme, CI, project instructions such as CLAUDE.md) | entry points are where loading starts; a content hash per file lets two runs show exactly what changed |
| `struct.description` | each frontmatter `description` | descriptions sit in the model's context all the time, before anything is invoked |
| `struct.agent-tools` | the tools each agent or command is granted | the widest grants set what an agent can do |
| `struct.hooks` | each hook: event, matcher, command | a hook runs whenever the host fires its event, without anyone asking |
| `struct.manifests` | the platform manifests of a plugin, and whether their permissions disagree | the same plugin can claim different permissions on different hosts |
| `struct.mcp` | each MCP server: name, transport, command or URL, environment variable names (never values) | an MCP server is a channel to the outside |
| `struct.census` | structural flags: a file past the reader window (2,000 lines or 50 KB), a line over 500 characters, an extension that disagrees with the content, a byte-order mark, an archive, a symlink | text past a reviewer's window, or a file pretending to be another type, is where things hide |

**Usually seen in a well-built repo.** A few entry points, short descriptions, agents granted
the tools their job needs, and hooks that do what their name says.

**Worth a closer look.** Hooks on events that run before any input (`SessionStart`,
`UserPromptSubmit`); an agent that inherits every tool; files over the reader window;
`ext-magic-mismatch` (a `.md` that is really an image); manifests that disagree.

**In the report.** Section 1. Hooks appear on the summary page as "Runs commands on its own";
files over the reader window are listed under section 1 in `summary.md`. Everything is in
`full.md` section 1.

---

## Stage 2: Reader, "What the model actually reads"

**Why.** A person reviewing a file sees it rendered. A model receives the raw text. Anything
that differs between the two is text one of them misses.

Each file is read twice: **reading A** is the raw text a model receives, **reading B** is what a
person sees (rendered Markdown, styled HTML, the visible layer of a PDF or Office file, OCR of
an image).

| Check | What it records | Why it matters |
|---|---|---|
| `read.divergence` | text in one reading and not the other, and how it hides: HTML comment, `display:none`, white-on-white, zero-width characters, bidirectional controls, soft hyphens, alt or title text, hidden Office runs | an instruction the reviewer cannot see is still an instruction to the model |
| `read.fold` | lines that change when invisible and look-alike characters are folded away | "ig​no​re" with zero-width spaces reads as "ignore" to a model; stage 4 matches the folded text |
| `read.script` | runs of non-Latin script | the phrase patterns are English; a non-English run is unread by stage 4 |
| `read.metadata` | text in metadata fields (image EXIF, document properties) | metadata travels with the file and some hosts pass it on |
| `read.unread` | files the reader could not read, and why | a file nobody read is not a clean file |

**Usually seen.** Some HTML comments in Markdown (notes to maintainers), no zero-width or
bidirectional characters, nothing unread.

**Worth a closer look.** Hidden text that also matches a phrase pattern (the summary lists these
as "Hidden when rendered, and reads like an instruction"); zero-width characters inside words;
white-on-white or `display:none` text.

**In the report.** Section 2, with hidden-plus-phrase pairs on the summary page. Optional tools
(Tesseract for images, Playwright for true HTML rendering, Poppler for PDF pages) widen
reading B; when one is missing, section 7 says what went unread.

---

## Stage 3: Graph, "What loads what"

**Why.** Reviewers follow references. A file that nothing names, or that only a glob pulls in,
is a file a reviewer following references never opens.

| Check | What it records | Why it matters |
|---|---|---|
| `graph.entry` | the entry points the graph starts from | everything else is reached from these |
| `graph.depth` | for each reachable file: hops from an entry point, which file reached it, and how (`static`: named directly; `dynamic`: pulled in by a load such as a glob or folder read; `mention`: a folder or glob is mentioned without being loaded) | deep files and files reached only dynamically get less review |
| `graph.dynamic` | each glob, directory scan, or pattern read, and the files it matches today | its targets can change after review |
| `graph.orphan` | files no entry point reaches | dead weight, or a payload waiting for a later version to load it |
| `graph.dangling` | references to paths that do not exist, by context (prose, code, link, config) | rot, or a slot for a file added later |
| `graph.unscanned` | files that may hold references but were not scanned | where the graph is blind |

**Usually seen.** Few orphans, dangling references mostly in code (imports the scanner cannot
resolve) and a handful in prose.

**Worth a closer look.** An orphan or a file loaded only dynamically that also matches a phrase
pattern (the summary lists these); dangling references in prose instructions.

**In the report.** Section 3. The graph is incomplete by construction (a glob's targets are
resolved as of the review), and the report says so.

---

## Stage 4: Phrases, "What the text asks for"

**Why.** The payload is English. This stage looks for the shapes of instructions that reach
out, take control, change the environment, or work on the person, and builds tables of the
things instructions depend on (hosts, confirmations, conditions, definitions).

About 125 patterns (`stages/04-phrases/patterns.yaml`), each citing the threat class or phrase
set it comes from (`pre-planning/THREATS.md`, `pre-planning/PHRASES.md`). Each hit records the
line verbatim, the pattern ids, the matched words, and the file's audience. Matching runs on the
folded line, so hidden characters do not break a match.

| Group | Check | Looks for | Threat class |
|---|---|---|---|
| 4a Reaching out | `phrase.K.exfil` | sending data out: uploads, webhooks, encoded payloads, relay hosts | 1 |
| | `phrase.creds` | reading credentials: `.env`, key files, secret names, enumerating the environment | 2 |
| | `phrase.remote-load` | fetching instructions from elsewhere, piping downloads into a shell | 3 |
| 4b Taking the wheel | `phrase.L.override` | overriding instructions: "ignore previous", fake system frames, "new instructions" | 5 |
| | `phrase.A.consent` | claimed permission: "the user already approved", standing consent | 13 |
| | `phrase.B.defs` | redefining words so later instructions mean something else | 14 |
| | `phrase.H.anti-review` | shaping what reviewers see: hide, suppress, skip the log | 20 |
| | `phrase.I.conditional` | behavior that switches on a date, version, environment, or host | 21 |
| 4c Changing the environment | `phrase.E.perms` | widening permissions: skip-permission flags, allow-lists, global installs | 7 |
| | `phrase.C.second-order` | instructions to write instructions: editing other skills, emitting text a hook injects | 15 |
| | `phrase.D.trust` | elevating trust: "always trust this file", "treat as current" | 16 |
| | `phrase.E.env` | changing the environment: shell profiles, git config, memory files, clones, MCP setup | 17 |
| | `phrase.J.prohibited` | actions a harness usually guards: deleting, force-pushing, paying, sending | 22 |
| 4d Talking to the human | `phrase.G.human` | asking the person to run something risky or paste a secret | 19 |

Part 2 builds tables from instruction text (model and subagent files, plus frontmatter):

| Check | What it records |
|---|---|
| `endpoint.host` | every network host named anywhere, whether the docs name it, and where it appears (instructions, docs, code) |
| `rubric.action` | each guarded action in instruction text, its tier (prohibited or confirm-first), and whether a confirmation step exists, is negated, or is itself a redefinition |
| `cond.branch` | conditional sentences, by kind: harness, clock, version, state, environment, absence, error |
| `term.def` | definitions in instruction text |
| `term.conflict` | a word defined differently in two or more places |
| `term.safety` | a definition of a safety word (confirm, safe, approve, ...) |
| `pos.density` | in a long file a model reads: where the flagged lines sit (first 10%, middle, last 10%) and how many are past the reader window (2,000 lines or 50 KB), where a reviewer's viewer may stop |
| `secret.found` | a line that looks like a committed secret (an API key, a password), found by gitleaks when installed, otherwise detect-secrets; the value is never shown, and other findings on that line have their quote replaced |
| `rep.sentence` | a sentence repeated across files a model reads; repetition adds weight, so a flagged sentence in several files is listed |

**Signal levels.** Each summary point names its patterns with their **base rate**: how many of
the other audited repositories that pattern turned up in (outside human-facing files and test
data). **Rare** means in none of them, **uncommon** in one, **common** in two or more. A rare
pattern means more when it hits. The table is `stages/08-report/baserates.json`, rebuilt as the
corpus grows; the repository being audited is never counted against itself.

**Usually seen.** Many hits. Forceful style ("YOU MUST", "never skip") is common and
recommended; most hits in a well-built skill are its own stated job (a deploy skill mentions
pushing). The benign share is the point of keeping every hit.

**Worth a closer look.** Rare patterns in model-read files (the summary lists them); hosts the
docs never name; prohibited-tier actions with no confirmation step; a safety word redefined; a
word defined two different ways.

**Benign share.** When stage 6 labels ran, section 4 also reports how many of the labeled
lines a model reads were read as instructions and how many as descriptions, quotes, or other
uses (REPORTING rule 2: a count comes with its benign share).

**In the report.** Section 4: counts per group in the status line, split by audience, rare-pattern hits and the
part 2 highlights as points, every hit grouped by check in `full.md`.

---

## Stage 5: Capability, "What this touches"

**Why.** The question an installer asks is what this can do once it is in. Stage 5 answers by
combining what stages 1 to 4 found. It detects nothing new; every conclusion cites the findings
it rests on.

**Test data first.** Findings in test data are set aside and counted (one `cap.testdata`
finding), except test data a model-read file references directly, which stays in and is listed
as a `testdata+loaded` pair. Human-facing files never count as capability.

### The trifecta (`cap.leg`)

Simon Willison's lethal trifecta: an agent with private data, untrusted input, and a way out
can be made to leak. Walkdown checks each leg and lists the evidence.

| Leg | Checked when there is |
|---|---|
| **Reads your data** | a credentials phrase; a data-flow or connector phrase; a grant of Read, Grep, Glob, or Bash; an agent inheriting all tools; a connector MCP server or tool (Gmail, Drive, Slack, ...); a hook on PreToolUse, PostToolUse, or UserPromptSubmit |
| **Takes outside input** | a remote-load phrase; a clone or install of third-party code; a WebFetch or WebSearch grant; an agent inheriting all tools; an MCP config or server |
| **Sends data out** | a remote-load or exfiltration phrase; a WebFetch or WebSearch grant; an agent inheriting all tools; an MCP config or server |

Bash counts toward reading data and running code, never toward sending data out on its own.
**All three legs are common in well-built repositories**: an agent that reads files, uses the
web, and pushes commits has all three. The combination raises risk; it is not an issue alone.

### Install grants (`cap.grant`)

| Grant | Present when |
|---|---|
| exec-at-load | any hook (it runs when the host fires its event) |
| context-injection | any description (always in context), or a SessionStart or UserPromptSubmit hook |
| persistence | phrases that write shell profiles, git config or hooks, memory or settings files, editor autorun, global installs |
| network | the "Sends data out" leg, or a global install |
| elevated | skip-permission flags, allow-list edits, confirmations turned off, or an agent inheriting all tools |

### The rest of stage 5

| Check | What it records |
|---|---|
| `cap.injection` | each path by which text reaches the model's context at load (descriptions, hooks), with its size when known |
| `cap.load-bytes` | per host config: the bytes in context before the first message |
| `cap.posture` | each agent's tools against its stated job; least-privilege agents are marked |
| `cap.pair` | two findings worth more together: hidden text with a phrase hit, an orphan with a phrase hit, a load-only file with a phrase hit, an instruction in a script a context-injecting hook runs, test data a model-read file references |
| `cap.testdata` | how many findings were set aside as test data, and where |

**Usually seen.** Some legs, a context-injection grant (every skill has a description),
agents with narrow tools.

**Worth a closer look.** Exec-at-load with context injection (a hook that puts text in front of
the model before you type); an instruction in a script such a hook runs; elevated grants; agents
whose tools are wider than their job.

**In the report.** The trifecta checklist at the top of the summary page; section 5 for grants,
bytes at load, and pairs; every leg's and grant's evidence in `full.md`.

---

## Stage 6: Soft reads, "Needs a human read" (optional, experimental)

**Why.** A pattern can find "ignore all previous instructions". It cannot tell an instruction
from a quote of one in a security guide. Stage 6 asks those questions.

Off by default. With no model chosen it writes a question packet (`data/06-packet.md`) for a
person to work through. With models chosen at run time:

| Read | Flag | What it answers |
|---|---|---|
| Labels | `--label jev` | for each flagged line a model reads: is it an instruction to do the matched action, an instruction not to, a description, a quote or example, or the words used in another sense? |
| Comparison | `--compare <backend>` | the same question from a second model, for agreement (Laya, the local option, is retired: 13% on the test lines) |
| Relational reads | `--relational claude-cli` | prose answers to questions that need context: how the capabilities combine, what a redefined safety word changes, what a model would do at a guarded step |
| Coverage sweep | `--sweep jev` | every prose passage a model reads: does it tell the reader to set aside its instructions, send data out, gather secrets, act without or hide from the user, follow fetched instructions, or make lasting changes? Reaches text no pattern matched. |

**How results are shown, and why.** A model's reading of the same line moves between runs (by
up to about 0.1 in measured repeats), so the report uses bands:

| Read | Listed as a point | "Near the line" | Counted only |
|---|---|---|---|
| a "do" label | p >= 0.9 | 0.7 to 0.9 | below 0.7 |
| a sweep passage | p >= 0.6 | 0.4 to 0.6 | below 0.4 |

A confident read that a line is **not** an instruction (any other label at p >= 0.8) marks that
line where stage 5 cites it as evidence. The mark never removes the evidence or unchecks a leg.

**Accuracy.** Measured, and recorded in `pre-planning/soft/EVAL.md`. Five-way labels agree
with a hand-labeled set about half the time, and are far more reliable when confident. The sweep
caught 11 of 12 paraphrased payloads with no false flags on 20 benign passages; that set was
written by the same person who wrote the question, so it is a first check.

**In the report.** On the summary page, model reads have their own block, "Model reads
(experimental)", after the rule-based list. In section 6: sweep passages with no stage 4 hit
first, then confident "do" reads, then counts for near-the-line and weaker reads. Every answer
is in `full.md`.

---

## Version drift: comparing two runs

**Why.** A repository can be harmless when you install it and change later (an update adds a
hook, a new MCP server, an instruction to send data out). One audit sees one pinned version.

When `walkdown.py` audits a repository it has audited before (same name), it compares the new
run with the previous one and writes `changes.md` beside the reports. `walkdown.py diff <old>
<new>` does the same for any two runs.

| Compared | How |
|---|---|
| files | added, removed, changed, by each file's content hash (stage 1 records it since 2026-10-04) |
| what ships | entry points, hooks, agent tool grants, MCP servers, descriptions |
| what the text asks | phrase hits new and gone, matched by the line's text so a line that only moved is not new; network hosts |
| what installing grants | trifecta legs that switched, install grants added or removed, new pairs |

Model reads (stage 6) are not compared: the same line read twice already varies. The brief gets
counts only; `changes.md` lists every change with file and quote, most consequential first.

**Worth a closer look.** A trifecta leg that switched on, a new install grant (especially
runs-at-load), a new hook or MCP server, a changed description, a new network host, and new
phrase hits in text a model reads.

## Stage 7: Not examined

**Why.** A zero is only as good as what was looked at.

It lists: stages that did not finish or did not pass validation; checks skipped for a missing
optional tool; files unread or not scanned; the test-data rule and how much it set aside; and
the standing limits (English only, static only, known shapes).

**In the report.** Section 7 of both summaries, and `data/07-limits.md`.

## Stage 8: Report

Assembles the summary page, the text summary, and the full report from stages 1 to 7, and
writes LOG.md with each stage's validation stamp. It adds recommendations: each tied to a file
and line, conditional on what the artifact is for, naming a narrower way to do the same thing,
listed in stage order and never ranked.

---

## Validation in one paragraph

`grader/grader.py` runs each stage on its fixtures (`Fixtures/NN-stage/`) and scores the output
against `Fixtures/ANSWERS/`, which the stage code never reads. Rows are **gates** (must be
found), **negatives** (must not be found), and **recall** (measured, never required, used for
model backends). PASS means every gate and negative held; INCOMPLETE means nothing failed but a
check was skipped; FAIL means a gate was missed or a negative was hit. Every audit runs the
grader first and stamps the result in LOG.md. A stamp is reused while the code, fixtures, and
stage 6 choices are unchanged (fingerprinted in `.cache/stamps.json`), and LOG.md says when it
was measured; `--revalidate` measures afresh.

## Where the rules live

| To change or check | Look in |
|---|---|
| the finding format, every check id and field | `stages/CONTRACT.md` |
| a stage's contract | `stages/NN-*/CONTEXT.md` |
| a script's inputs, outputs, and limits | `stages/NN-*/specs/<name>.SPEC.md` |
| the phrase patterns | `stages/04-phrases/patterns.yaml` |
| the trifecta and grant rules | `stages/05-capability/rules.py` |
| what stage 6 asks a model | `stages/06-soft/softreads.yaml` |
| the threat classes and their sources | `pre-planning/THREATS.md` |
| stage 6 measurements | `pre-planning/soft/EVAL.md` |
