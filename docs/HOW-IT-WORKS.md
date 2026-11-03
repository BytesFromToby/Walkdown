# How Walkdown works

This is the reference for what each step checks, why, and how to read the result. It is
written for someone who wants to follow a finding back to the rule that produced it.

- How to read a report: [READING-THE-REPORT.md](READING-THE-REPORT.md)
- What a run folder holds: [RUN-FOLDER.md](RUN-FOLDER.md)
- How the build is laid out, with a map: [STRUCTURE.md](STRUCTURE.md)
- The tables the steps look things up in, with their sources: `Library/README.md`
- The design history and measurements behind these rules: `pre-planning/`

## The shape of a run

```
the repository
   |
   01 Intake            which copy is audited
   02 Coded steps       every coded finding, no model
        02.1 Inventory         what ships
        02.2 Reader            what the model actually receives
        02.3 Graph             what loads what
        02.4 Phrases           what the text asks for
        02.5 Capability        what installing it grants   (derived from 02.1 to 02.4, detects nothing new)
        02.6 Builder checks    the builder's questions     (needs, hosts, trigger, asks, clean, fit, cost)
   03 Sweep             what a pattern cannot settle: prose no pattern matched   (optional model read)
   04 Pinpoint          the line behind each sweep flag                          (optional model read)
   05 Check of the run  what should be there and is not, and what this run did not examine; a gap holds the run
   06 Report            every report, and what this run was blind to (Not examined)
```

Each step has a folder under `stages/`. The names the reports use for them are in the headings below.
`02.1` to `02.6` are scripts: no model, the same answer every time. `03` and `04` run only when you
choose them, and use a model you pick when you run it. `05` checks the saved run (no model), and `06` writes the
reports unless `05` holds the run.

### Rules every step follows

- **A finding is a location.** It says "this text, at this file and line, has this shape". It
  does not say the author meant harm. Intent cannot be read from a repository.
- **No score.** Nothing is added up into a rating. Two per-finding signals exist (a pattern's
  base rate, and a model read's "near the line" band); both are measurements, shown with the
  numbers behind them, never summed.
- **Benign hits are kept.** A pattern that matches innocent text is still recorded and counted.
  How often a pattern is innocent is what tells you how much a hit means.
- **Every step is validated before it is trusted.** Each step runs against fixtures, small
  repositories with known contents, and a grader scores it against an answer sheet the step's
  code never reads. The result is stamped in the run's LOG.md.
- **No model holds tools.** The models of the two optional reads get text and a question, and
  nothing else.

### Audience: who a file is written for

Most checks care about who reads a file. Walkdown decides it from the path:

| Audience | Files | Treated as |
|---|---|---|
| model | SKILL.md, CLAUDE.md, reference docs, anything not matched below | instructions the model reads |
| subagent | files under `agents/` or `commands/`, `*prompt*.md` | instructions a dispatched agent reads |
| tool | scripts (`.py`, `.sh`, `.js`, ...), hook configs, build and lock files | code; counted, read by tools. In an MCP server's code (Python, JavaScript, TypeScript, Go), the descriptions of its tools, prompts, resources, and parameters, the text its prompts return, and the text of its tools' replies are read as model text: a client sends them to the model |
| human | README, CHANGELOG, LICENSE, NOTICE and other license files (THIRD_PARTY_NOTICES, COPYING, CREDITS), INSTALL, guides, anything under `docs/` or `.github/` | written for people; counted, kept out of capability |
| test-data | anything under `tests/`, `fixtures/`, `__tests__/`, `testdata/`, `spec/` and the like, or named `test_*.py`, `*.test.*`, `*.spec.*`, `conftest.py`, `*.fixtures.*` | never loaded on install; counted, kept out of capability and the pages |

Human-facing and test-data hits are still recorded and listed in the full report. They are
kept out of the places the pages list and out of the capability map, because installing the
artifact does not put them in front of a model. One exception: **test data that a model-read
file references directly** (a skill that says "read tests/fixtures/setup.md and follow it")
counts like any other file, and "What this touches" lists it as a pair.

---

## Intake (`01-intake`)

**Why.** Everything after it is about one pinned copy. Intake makes sure the folder to audit exists.

A folder is read where it is. A git URL is cloned (shallow) into `ReposToExamine/<name>/`, or an
earlier clone of the same URL is updated to the latest commit (`--keep` audits it as it is, `--fresh`
clones it again). A GitHub folder link (`.../tree/<branch>/<path>`) clones the repository at that
branch and audits the folder. A folder in `ReposToExamine/` that is not a clone of the URL is never
touched, and a repository that needs a login stops the run: Walkdown never asks for one.

| Check | What it records | Why it matters |
|---|---|---|
| `intake.source` | exactly one: the target as given, whether it was a folder, a URL, or a GitHub folder link, what was done (read in place, cloned, updated, kept as it is, cloned again), the folder audited, the name the run is filed under | the run says which copy it examined and how it got it |

**In the report.** Intake has no section of its own. Its row is in `LOG.md`, with its validation
stamp, and its finding is in `data/01-intake.json`.

---

## What ships (`02.1-inventory`)

**Why.** You cannot judge what you have not counted. This step lists every file and the
structures a host loads on its own: skills, agents, hooks, manifests, MCP servers.

| Check | What it records | Why it matters |
|---|---|---|
| `inv.pin` | the source, and its git commit or sha256 | every later finding is about exactly this version |
| `inv.file` | each file: type, size, lines, encoding, executable bit, and whether it is an entry point (skill, agent, command, hook config, manifest, MCP config, readme, CI, project instructions such as CLAUDE.md) | entry points are where loading starts; a content hash per file lets two runs show exactly what changed |
| `struct.description` | each frontmatter `description` | descriptions sit in the model's context all the time, before anything is invoked |
| `struct.agent-tools` | the tools each agent or command is granted | the grants an agent has set what it can do |
| `struct.hooks` | each hook: event, matcher, command | a hook runs whenever the host fires its event, without anyone asking |
| `struct.manifests` | the platform manifests of a plugin, and whether their permissions disagree | the same plugin can claim different permissions on different hosts |
| `struct.mcp` | each MCP server: name, transport, command or URL, environment variable names (never values) | an MCP server is a channel to the outside |
| `inv.license` | each license file (`LICENSE`, `COPYING`, ...) and declared license field (frontmatter, `package.json`, plugin manifests, `pyproject.toml`, `Cargo.toml`), with the license its wording matches | what you may do with the repo is set by its license; a skill inside can ship a different one. Matching wording is a lookup, not legal advice |
| `struct.census` | structural flags: a file past the reader window (2,000 lines or 50 KB), a line over 500 characters, an extension that disagrees with the content, a byte-order mark, an archive, a symlink | text past a reviewer's window, or a file pretending to be another type, is where things hide |

**Worth a closer look.** Hooks on events that run before any input (`SessionStart`,
`UserPromptSubmit`); an agent that inherits every tool; files over the reader window;
`ext-magic-mismatch` (a `.md` that is really an image); manifests that disagree.

**In the report.** Section 1, "What ships". The license is one line under the title of `details.html`. Hooks
are a "Runs code" concern on `summary.html`, and on `details.html` appear under "General risks"
and in Things to check as "Runs commands on its own"; files over the reader window are listed
under "Worth a look" in the Files section (files the AI reads). Everything is in `full.md`
section 1.

---

## What the model actually reads (`02.2-reader`)

**Why.** A person reviewing a file sees it rendered. A model receives the raw text. Anything
that differs between the two is text one of them misses.

Each file is read twice: **reading A** is the raw text a model receives, **reading B** is what a
person sees (rendered Markdown, styled HTML, the visible layer of a PDF or Office file, OCR of
an image).

| Check | What it records | Why it matters |
|---|---|---|
| `read.divergence` | text in one reading and not the other, and how it hides: HTML comment, `display:none`, white-on-white, zero-width and other format characters, bidirectional controls, soft hyphens, letters and cells that draw as a blank (Hangul fillers, the blank braille cell), Unicode tag characters and runs of variation selectors (each with the text it spells, when it spells any), alt or title text, hidden Office runs | an instruction the reviewer cannot see is still an instruction to the model |
| `read.fold` | lines that change when invisible and look-alike characters are folded away | "ig​no​re" with zero-width spaces reads as "ignore" to a model; "What the text asks for" matches the folded text |
| `read.script` | runs of non-Latin script | the phrase patterns are English; a non-English run is unread by "What the text asks for" |
| `read.language` | prose passages in Latin script that read as another language: one language's common short words (`el`, `und`, `och`) outnumber the English ones, or heavy accents with no English. It never names the language | the same: Spanish in a Markdown list is unread by the phrase patterns, and a clean result on it means nothing |
| `read.metadata` | text in metadata fields (image EXIF, document properties) | metadata travels with the file and some hosts pass it on |
| `read.unread` | files the reader could not read, and why | a file nobody read is not a clean file |

The invisible characters it folds away are listed once, in `Library/invisible.yaml`. One variation
selector after an emoji or a CJK character is ordinary and is left alone; two or more in a row are
folded away and reported, because a run of them can hide bytes after one visible character. Zero-width
characters between the selectors do not break the run, and the text they spell is read from the
selectors alone.

**Worth a closer look.** Hidden text that also matches a phrase pattern (listed as places to
check, as "Hidden when rendered, and reads like an instruction"); zero-width characters inside words;
white-on-white or `display:none` text.

**In the report.** Hidden text that reads like an instruction is the first concern on
`summary.html`, and hidden characters that spell out text no pattern matched are the second, each
with a card on `review.html`. Section 2, and the Hidden text section of `details.html`, whose count
opens every hidden place and says what each one's characters spell, with a callout for hidden text
that reads like an instruction. Tesseract, when
installed, reads text inside images and on PDF pages (each page is drawn and read, and lines
its text layer lacks are listed, as when a page shows a picture of an instruction); when it is
missing, section 7 says so. Playwright, when installed with its Chromium, draws each HTML file
as a browser would, with the page's own scripts off and nothing fetched from the network, and
lists what static style cannot see: text in a closed `<details>` section, moved off the page,
clipped or covered by another element, hidden or colored like the page by an `@media` rule (carrier
`rendered`, with `how`), and text a style sheet adds with `::before` or `::after`, which a
person sees and the model never receives. When it is missing, section 7 says so. The language
check needs nothing installed; it reads prose only (not code comments, config values, or HTML),
and section 7 says so.

---

## What loads what (`02.3-graph`)

**Why.** Reviewers follow references. A file that nothing names, or that only a folder or use of wildcards
(a file-name pattern like `skills/*/SKILL.md`) pulls in, is a file a reviewer following references never opens.

| Check | What it records | Why it matters |
|---|---|---|
| `graph.entry` | the entry points the graph starts from | everything else is reached from these |
| `graph.depth` | for each reachable file: hops from an entry point, which file reached it, and how (`static`: named directly; `dynamic`: pulled in by a load such as a glob or folder read; `mention`: a folder or glob is mentioned without being loaded) | deep files and files reached only dynamically get less review |
| `graph.dynamic` | each glob, directory scan, or pattern read, and the files it matches today | its targets can change after review |
| `graph.orphan` | files no entry point reaches | dead weight, or a payload waiting for a later version to load it |
| `graph.dangling` | references to paths that do not exist, by context (prose, code, link, config) | rot, or a slot for a file added later |
| `graph.case` | a reference that matches a file only when letter case is ignored | works on Windows and macOS, breaks on Linux |
| `graph.unlisted` | skills, agents, or commands on disk that their manifest leaves out, for the kinds it names (a manifest's paths are read from its plugin root) | a reviewer reads the manifest to learn what a plugin holds; a host that finds components by folder can still load the one it leaves out |
| `graph.unscanned` | files that may hold references but were not scanned | where the graph is blind |

**Worth a closer look.** An orphan or a file loaded only dynamically that also matches a phrase
pattern (listed as places to check); dangling references in prose instructions.

**In the report.** Section 3, "What loads what". The graph is incomplete by construction (what a wildcard pattern
matches is resolved as of the review), and the report says so.

---

## What the text asks for (`02.4-phrases`)

**Why.** The payload is English. This step looks for the shapes of instructions that reach
out, take control, change the environment, or work on the person, and builds tables of the
things instructions depend on (hosts, confirmations, definitions).

About 130 patterns (`Library/patterns.yaml`), each citing the threat class or phrase
set it comes from (`Library/THREATS.md`, `Library/PHRASES.md`), with the plain words the review
page shows beside it. Each hit records
the line verbatim, the pattern ids, the matched words, and the file's audience. Matching runs on the
folded line, so hidden characters do not break a match: zero-width and other invisible
characters are dropped, look-alike letters read as the letters they imitate, accents on Latin
letters are dropped (`ignóre` reads `ignore`), and a sentence written in Unicode tag characters
or in a run of variation selectors reads as the text it spells. Readable text hidden in base64 is decoded and matched too, and the
hit says so. A frontmatter value written over several lines (`description: >-`) is matched as
one. In Markdown, each line is also matched joined with the next
lines of its paragraph (up to four lines), so an instruction hard-wrapped across lines is caught;
that hit is cited at the line where it starts, quotes every line, and is kept only when no
single line or shorter run hits it. The reverse holds too: a pattern that makes an exception
("don't ask", but not "don't ask hypothetical questions") reads the line together with the
start of the next one, so the exception works across a line break. PDF, DOCX, and image files are matched too, on the text "What the model actually reads" read from them (the text
layer, text drawn on PDF pages, the text in images); those hits are cited as "extracted text,
line N", and the tables below are built from text files only.

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
| | `phrase.J.prohibited` | actions AI tools commonly leave to the user or ask about first: deleting, force-pushing, paying, sending | 22 |
| 4d Talking to the human | `phrase.G.human` | asking the person to run something risky or paste a secret | 19 |

The groups (4a to 4d) are the headings of section 4 of `full.md`. A second set of checks builds
tables from instruction text (model and subagent files, plus frontmatter):

| Check | What it records |
|---|---|
| `endpoint.host` | every network host named anywhere, whether the docs name it, and where it appears (instructions, docs, code), with each whole address as written; a host written with look-alike letters (`gіthub.com` with a Cyrillic `і`) is listed as written and marked with the host it imitates and its punycode; nothing is opened |
| `rubric.action` | each guarded action in instruction text, its tier (prohibited or confirm-first), and whether a confirmation step exists, is negated, or is itself a redefinition |
| `term.def` | definitions in instruction text |
| `term.conflict` | a word defined differently in two or more places |
| `term.safety` | a definition of a safety word (confirm, safe, approve, ...) |
| `pos.density` | in a long file a model reads: where the flagged lines sit (first 10%, middle, last 10%) and how many are past the reader window (2,000 lines or 50 KB), where a reviewer's viewer may stop |
| `secret.found` | a line that looks like a committed secret (an API key, a password), found by detect-secrets, plus an Anthropic key by its shape; the value is never shown, and whatever any step keeps from that line (a quote, a description, a hook's command, a link's address, hidden text that reaches it) is replaced. A hash, a test-host password, a variable name, a plain word, or a placeholder such as `abc123...` is marked likely not a secret and kept off the summary. A file the scanner could not scan, such as an `.svg` or `.css` file detect-secrets leaves out by name, is named as such on `details.html` and in `full.md`. Every text file is read, build files and pattern lists included, except a lock file, whose hashes look like keys: `details.html` names it and `full.md` counts it. A comment in the repository asking a scanner to skip a line changes nothing |
| `rep.sentence` | a sentence repeated across files a model reads; repetition adds weight, so a flagged sentence in several files is listed |
| `limit.setting` | a flag or setting that restricts what tools an agent can use, in any file: `--tools` with a list, `--disallowedTools` or a JSON deny list, a `--sandbox` mode, a `--permission-mode`; what it rules out (writing, shell, network) and whether it allows writing. `--allowedTools` is not counted: it pre-approves tools and leaves the rest available. A fact for "What this touches", never a risk |

**Prohibitions.** A hit whose line forbids the matched action ("Never have the user paste an API
key into chat") is kept and tagged `negated`, with the forbidding word and any exception
("unless the user asks"). Only forbidding words count (never, do not, must not, should not, may
not, avoid, and the like) and only in the same clause; double negatives and descriptions ("don't
forget to", "does not") do not. A guarded action the line forbids is never reported as one with
no confirmation step. Procedures ("How to start") are cited at their first sentence, and two
procedures alone never make a conflicting definition.

**Signal levels.** Each summary point names its patterns with their **base rate**: how many of
the other audited repositories that pattern turned up in (outside human-facing files and test
data). **Rare** means in none of them, **uncommon** in one, **common** in two or more. A rare
pattern means more when it hits. The table is `Library/baserates.json`, rebuilt as the
corpus grows (`tools/baserates.py`); the repository being audited is never counted against itself.

**Worth a closer look.** Rare patterns, the shape of sending data out (a private source, a
sending verb, and a destination in one line), and credentials named on a line that sends, in
model-read files (listed as places to check); hosts the
docs never name; prohibited-tier actions with no confirmation step; a safety word redefined; a
word defined two different ways.

**Benign share.** This version has no labeling, so it does not say how many hits are
instructions and how many are descriptions or quotes. Section 4 says the benign share is not
measured (REPORTING rule 2: a count comes with its benign share, so the report says when it has
none).

**In the report.** Section 4 of `full.md`, "What the text asks for": counts per group in the status line, split by
audience, and every hit grouped by check. Those hits and the part 2 highlights are places
to check, listed under Risky asks on `details.html` and walked on `review.html`.

---

## What this touches (`02.5-capability`)

**Why.** The question an installer asks is what this can do once it is in. This step answers by
combining what the steps before it found. It detects nothing new; every conclusion cites the findings
it rests on.

**Test data first.** Findings in test data are set aside and counted (one `cap.testdata`
finding), except test data a model-read file references directly, which stays in and is listed
as a `testdata+loaded` pair. Human-facing files never count as capability.

The rules (which evidence makes each leg, which grants count) are a table in `Library/capability.yaml`.

### The trifecta (`cap.leg`)

Simon Willison's lethal trifecta: an agent with private data, untrusted input, and a way out
can be made to leak. Walkdown checks each leg and lists the evidence.

| Leg | Checked when there is |
|---|---|
| **Can read your data** | a credentials phrase; a data-flow or connector phrase; a grant of Read, Grep, Glob, or Bash; an agent inheriting all tools; a connector MCP server or tool (Gmail, Drive, Slack, ...); a hook on PreToolUse, PostToolUse, or UserPromptSubmit |
| **Can take outside input** | a remote-load phrase; a clone or install of third-party code; a WebFetch or WebSearch grant; an agent inheriting all tools; an MCP config or server |
| **Can send data out** | a remote-load or exfiltration phrase; a WebFetch or WebSearch grant; an agent inheriting all tools; an MCP config or server |

Bash counts toward reading data and running code, never toward sending data out on its own. An
agent with no tools list can use every tool, so it counts toward all three legs; the report marks
that as capability only: what it could use, with no evidence that it does.
Each leg is ordinary on its own. A tool with all three can be steered by text from outside into
sending your data away.

### Install grants (`cap.grant`)

| Grant | Present when |
|---|---|
| exec-at-load | any hook (it runs when the host fires its event) |
| context-injection | any description (always in context), or a SessionStart or UserPromptSubmit hook |
| persistence | phrases that write shell profiles, git config or hooks, memory or settings files, editor autorun, global installs |
| network | the "Can send data out" leg, or a global install |
| elevated | skip-permission flags, allow-list edits, confirmations turned off, or an agent inheriting all tools |

### The rest of "What this touches"

| Check | What it records |
|---|---|
| `cap.injection` | each path by which text reaches the model's context at load (descriptions, hooks), with its size when known |
| `cap.load-bytes` | per host config: the bytes in context before the first message |
| `cap.posture` | each agent's tools against its stated job; least-privilege agents are marked |
| `cap.limit` | read-only wording a model reads, paired with what could back it: a restricting setting on the same line, the tools list of the skill or agent that owns the file, and other routes in the same skill that can write. Backed, contradicted by the owner's tools list, or stated in the text only (a static read cannot see whether a setting is used at run time) |
| `cap.pair` | two findings worth more together: hidden text with a phrase hit, an orphan with a phrase hit, a load-only file with a phrase hit, an instruction in a script a context-injecting hook runs, test data a model-read file references |
| `cap.testdata` | how many findings were set aside as test data, and where |

**Worth a closer look.** Exec-at-load with context injection (a hook that puts text in front of
the model before you type); an instruction in a script such a hook runs; elevated grants; agents
whose tools are wider than their job.

**In the report.** The three boxes in one row on `summary.html`. "The lethal trifecta" at the top of `details.html`, each box opening to its places, with what installing it allows beside the box it belongs to and the rest under "General risks"; section 5 of `full.md` for grants,
bytes at load, and pairs; every leg's and grant's evidence in `full.md`.

---

## Builder checks (`02.6-builder`)

**Why.** Someone building a skill or agent asks questions a security reading does not: will it
trigger, what does it cost, what ships, will it run elsewhere. This step answers them from the same
files and the earlier steps' findings. Each is a fact with a location, from a dated table in
`Library/` with its sources, never a judgment.

| Check | What it records | Where its table lives |
|---|---|---|
| `need.command` | each program a script, an instruction, a hook, or an MCP server runs (from a dated list, so an ordinary word never counts), where, and whether the repository declares it (a dependency file, a skill's `compatibility`, an install line) | `Library/tools.yaml` |
| `need.package` | each package a bundled Python or JavaScript file imports (not the standard library, a built-in, or the repository's own module), and whether it is declared | `Library/tools.yaml` |
| `port.path`, `port.crlf`, `port.os`, `port.backslash`, `port.exec`, `port.python` | what ties it to one machine: a personal path in a file that runs or the AI reads; a shell script committed with Windows line endings; a script or command for one system only; a reference written with backslashes; a script run directly that git records as not executable; running `python` where many systems have only `python3` | `Library/tools.yaml` |
| `host.coverage` | for each AI host (Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot, Windsurf, and the other tools that read `AGENTS.md`), the instruction files, skills, MCP config, and hooks here that it reads, from a dated list of what each host reads. A fact per host, never a fault | `Library/hosts.yaml` |
| `host.drift` | two hosts' instruction files in one folder (`CLAUDE.md` and `AGENTS.md`, say): the same text, one pointing to the other, or different, with the lines only in each. Claude Code reads only `CLAUDE.md` when both exist, so a different `AGENTS.md` is what the other hosts see | `Library/hosts.yaml` |
| `host.feature` | in a `SKILL.md` or `AGENTS.md`, something only one host understands: a frontmatter key Claude Code knows outside the Agent Skills set (claude.ai and the Skills API refuse the skill), Claude Code's words (`$ARGUMENTS`, `${CLAUDE_PLUGIN_ROOT}`) and tool names, an `@path` import in `AGENTS.md`; and each hook file, which runs on one host only | `Library/hosts.yaml` |
| `trig.entry` | each skill, command, and subagent, and how it triggers: Claude chooses it by its description, only on matching files, only when typed, or it is not loaded (frontmatter not read, or a subagent with no name or no description) | `Library/trigger.yaml` |
| `trig.frontmatter`, `trig.rule` | frontmatter its host does not read (YAML that does not parse, `---` not on the first line), and the name and description rules of the Agent Skills spec, claude.ai uploads, and Claude Code, each place saying whose rule it is | `Library/trigger.yaml` |
| `trig.key`, `trig.value`, `trig.tool` | a frontmatter key, value, or tool name no host takes, with the known one it is closest to (`allowed_tools` is `allowed-tools`) | `Library/trigger.yaml` |
| `trig.overlap`, `trig.guidance`, `trig.listing` | descriptions in one listing that share most of their words (Walkdown's own measure); published guidance a description does not follow (no "when", first or second person); and the descriptions' size against Claude Code's listing, about 1% of the context | `Library/trigger.yaml` |
| `ask.tools`, `ask.named`, `fit.loop` | in text the AI reads: the lines asking for each kind of work (running commands, writing files, fetching pages, searching the web, starting subagents), not counting a verb a negation governs, a verb used as a noun, or a quoted example; tools named outright; and loops ("repeat until the tests pass") with no number of tries, give-up, or time on the line or the next | `Library/asks.yaml` |
| `fit.unused`, `fit.missing`, `fit.inherits`, `fit.hook`, `fit.checked` | each skill, agent, and command's own words, over what it reads, against its grants: tools that run, write, reach out, or spawn that nothing asks for (a skill's are only pre-approved); work it asks for that no tool it may use does (a subagent's tools list, or disallowed tools); agents with no tools list, so every tool; and each hook with how often it runs (every prompt, every tool call, once a session) and, for Claude Code, whether its output becomes context and about how large | `Library/fit.yaml` |
| `clean.unfinished`, `clean.dated`, `clean.model`, `clean.older`, `clean.checked` | in what ships (not files for people, not test data): TODO and FIXME markers, placeholders, and draft notes; in text the AI reads, claims tied to a date ("before August 2025", "since 2024", "as of"; a bare date is a record, not a claim); pinned model IDs, Claude's and other vendors', never an alias; and older tool names named in text. Facts with locations: none says a date is past or a model retired | `Library/clean.yaml` |
| `cap.ship` | every file's group: loaded into the AI (a skill, agent, or command; project instructions such as CLAUDE.md and their `@` imports; files a loaded file names; files reached only by a wildcard or folder read), used another way (scripts it runs, configs), or not used at run time (for people, build material, written for the AI but never pointed to); size and estimated tokens | `Library/loading.yaml` |
| `cap.context` | the context it takes, in tiers: every session (descriptions, hook text), every session in this folder (project instructions), and per skill: when it runs, with everything it names, with its wildcard loads; tokens estimated from size (about 4 bytes per token) | `Library/loading.yaml` |

**In the report.** The eight questions of `summary.html` and `details.html` answer from these
checks (questions 1 to 7) and from the security checks (question 8). The checks are listed in
`full.md` under "What ships" (what it needs, what ties it to one machine), "What the text asks for"
(will it trigger, ready for any AI, current and clean), and "What this touches" (what it costs and
what ships, do the tools fit the job). A step of this kind that did not work is named on the pages
and in the brief as "Builder checks".

---

## Needs a human read (`03-sweep`, optional and experimental)

**Why.** A pattern can find "ignore all previous instructions". It cannot find a sentence that
means the same thing in words no pattern knows. The sweep asks a model about every prose passage a
model reads, so text no pattern matched still gets a read.

Off by default. It runs only with `--sweep jev` or `--sweep claude-cli` (with `claude-cli:<model>` to name the model;
the person names it; a `claude-cli` with no model named runs `sonnet`; Walkdown picks no model for a run where nothing is named),
or with `--reads [model]`, which chooses it for you: Jev when it is available (its key can be read and its package is found; the
passages then go to TypeSafe), else the Claude Code command with the model you typed after `--reads` (a bare `--reads` runs `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`). Then:

- It cuts the prose into passages (front matter, then one passage per heading; long ones are split
  at blank lines) and writes exactly what the model will be shown to `data/03-sweep.input.jsonl`,
  before anything is sent to a remote model. A line the secret scan flagged is left out, as a blank at its place, with the rest of a private
  key and whatever else stands on that line, and a file the scan did not read is not sent. `details.html` and section 7 of `full.md` say
  how many lines were left out and name each such file. To open that file first, stop the run just before the
  read: `--sweep jev --until coded` runs the coded steps and writes the file without reading a key or
  sending anything, and `walkdown.py continue <run folder> --sweep jev` goes on (choosing the read
  there is the consent to send). A `continue` that leaves the option out does not run the read and says so: it
  prints a note, and the report names the read as one an earlier command chose and `continue` did not.
- It asks the model, one question per passage: does this passage tell the reader to set aside its
  instructions, send data out, gather secrets, act without or hide from the user, follow fetched
  instructions, or make lasting changes? Each answer is kept as it came back in
  `data/03-sweep.answers.jsonl`. Jev answers with a probability for each kind. A model that takes text (the Claude Code
  command) is shown the same question, the kinds with their descriptions and examples, and the passage marked as data
  it must not obey, and answers with the name of one kind and nothing else. An answer that is anything else (a name
  with an explanation, two names, nothing) is a call with no answer. No model is asked how sure it is: Claude rated
  itself 0.9 or more 27 times and was right 12. So a model that takes text gives no probability, a passage is flagged
  when its answer is not `none`, and the report says "(this model gives no probability)" where Jev's number would be.
- The brief ends with what the reads used: `Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint 1,490 in, 73 out;
  Sweep's fixture check 39,823 in.` Each count is what the backend reported; a read whose backend reported none says "not
  reported", a total that only some of the calls reported says so ("500 in, 15 out (from 5 of 9 calls)", a lower bound), and a fixture check that was reused from an earlier run spent none and is not named. Under the fixture checks
  it says what the sweep found in its own fixtures (passages with known answers): `Sweep on jev: found 33 of 34 in its
  fixtures.` A low count shows and holds nothing.
- A long read writes a plain line on the terminal every 25 passages (`sweep: 25 of 431 passages done`).
- A call that gets no answer (an error from the service, or an answer that is not one of the options) is
  tried once more after 2 seconds. If the second try answers, that answer is used. If not, the passage is
  skipped with the second try's reason. The Jev library's own retries are switched off, so a passage is
  sent at most twice. A key the service rejects again stops the later calls: those
  passages are skipped as "not sent". With no key, or without the package, nothing is called and nothing
  is tried again. Every passage whose first try got no answer, or that was not sent, has a line in
  `data/03-sweep.calls.jsonl` (no key, no passage text, and no error message; its `qid`
  names the file and line). Why a passage got no answer is kept as a kind of failure and a status. The error's
  own text is left out, since it can repeat the passage or the model's words.
- Each passage becomes one `soft.sweep` finding, with the phrase patterns that already hit inside it.

## The line behind each flag (`04-pinpoint`, optional and experimental)

**Why.** A flagged passage can be a dozen lines, and a reader new to this cannot tell which part is
the issue.

It runs only with `--pinpoint claude-cli` (or with `--reads`, when the `claude` command is found), and only after a sweep. For each passage the report shows
as a place of its own (flagged, or near the line, with no phrase pattern inside), a second model, the
Claude Code CLI run with no tools, no settings, and no project files, names the line that does the
flagged kind of action and quotes it. A quote is kept only when it is found in the passage word for
word. Its question leaves out the same lines the sweep does. Its input and answers are `data/04-pinpoint.input.jsonl` and `data/04-pinpoint.answers.jsonl`;
`--sweep jev --pinpoint claude-cli --until sweep` runs the sweep (which sends its passages to Jev),
then writes the pinpoint's input and stops before the pinpoint sends anything (unless the sweep got no
answer for any passage: then there is nothing to pinpoint, no input file is written, and the run is over).
As in the sweep, a call
that gets no answer (an error, or an answer with no JSON in it) is tried once more after 2 seconds and
logged in `data/04-pinpoint.calls.jsonl`. The pinpoint does not run after a sweep in which no passage
got an answer: there is nothing to pinpoint, and the brief says so.

**How results are shown, and why.** A model's reading of the same passage moves between runs (by
up to about 0.1 in measured repeats), so the report uses bands:

| Read | Listed as a point | "Near the line" | Counted only |
|---|---|---|---|
| a sweep passage | p >= 0.6 | 0.4 to 0.6 | below 0.4 |

A model that gives no probability has no bands: the passages it flagged are listed with the first column, and the rest are
counted only.

**Accuracy.** Measured, in [MODEL-ACCURACY.md](MODEL-ACCURACY.md). The sweep caught 11 of 12
paraphrased payloads with no false flags on 20 benign passages; that set was written by the same
person who wrote the question, so it is a first check. Pinpoint has not been measured.

**In the report.** `details.html` lists the sweep's passages under "Needs a human read" (never as
concerns), and the review page is where a read joins its card, marked experimental. In section 6 of
`full.md`: sweep passages with no phrase pattern hit first, then those a pattern already matched, then
the near-the-line ones. A run that chose neither says so in one line. A model read never changes a
coded finding. Every answer is in `data/`.

---

## Version drift: comparing two runs

**Why.** A repository can be harmless when you install it and change later (an update adds a
hook, a new MCP server, an instruction to send data out). One audit sees one pinned version.

When `walkdown.py` audits a repository it has audited before (same name), the report step compares the new
run with the previous one and writes `changes.md` beside the reports. `walkdown.py diff <old>
<new>` does the same for any two runs. The previous run is the newest other run of the same
repository that finished before this one started.

| Compared | How |
|---|---|
| files | added, removed, changed, by each file's content hash; a file whose line endings alone changed is listed apart and not counted as edited |
| what ships | entry points, hooks, agent tool grants, MCP servers, descriptions |
| what the text asks | phrase hits new and gone, matched by the line's text so a line that only moved is not new; network hosts |
| what installing grants | trifecta legs that switched, install grants added or removed, new pairs |

Model reads are not compared: the same passage read twice already varies. The brief gets
counts only; `changes.md` lists every change with file and quote, most consequential first.

**Repository or Walkdown.** A new or gone phrase hit can come from the repository or from
Walkdown itself (a new search term, a narrowed one, a change in how lines are matched). The
phrase step records the version of its search terms and its matching code in every run (`terms`:
one short hash per pattern row, the word lists, and the step's code). Each hit is then traced: its file
was added, removed, or edited (the repository), or the file is the same and the hit's search term
was added, changed, or retired (Walkdown's search terms), or only the matching code changed
(Walkdown's matching code). `changes.md` names the terms that changed by id. Re-auditing the same
version of a repository says nothing when nothing differs; when something does, every difference
comes from Walkdown, and the brief says so.

**Runs from before 0.4.0.** A run made by an earlier version has its data in another shape, so it is
not compared field by field: the new run says the earlier one is not comparable. It is not
re-rendered either. Marks carry over regardless.

**Worth a closer look.** A trifecta leg that switched on, a new install grant (especially
runs-at-load), a new hook or MCP server, a changed description, a new network host, and new
phrase hits in text a model reads.

---

## Not examined

**Why.** A zero is only as good as what was looked at.

It lists: steps that did not finish or did not pass validation; checks skipped for a missing
optional tool; files unread or not scanned; the test-data rule and how much it set aside; and
the standing limits (English only, static only, known shapes); and, for each model read that has
passages with no answer, how many ("5 of 12 passages got no answer, after one retry"), the reasons
counted, and the call log. Each step names its own skips in its output, and the report step gathers
them.

**In the report.** Section 7 of `full.md`, "What Walkdown didn't check" on `details.html`, and
`data/limits.md`, all drawn from the check of the run's output (`data/05-qa.json`). A step that did not run or did not pass validation is also named at the
bottom of `summary.html`, and in its headline when it found nothing. A missing optional tool is
not named there. A model read in which no passage got an answer, even after the retry, is named as a
step that did not work, and the headline then says the coded checks are complete and the model read
did not work: a model read never adds a security concern, so a missing one does not make the coded
result less complete. (When a coded check was skipped for a missing tool, the headline says the coded
checks ran, and that "What Walkdown didn't check" names any skipped.) Each fact about a model read is
said once on a page: the count and its reasons in section 7 and on the details page, and on the summary
for a read that answered some.

## The check of the run (`05-qa`)

After the steps, the validation, and the run's record, and before the report, `05-qa` reads the saved run and asks
the question the owner put as "confirm everything that should have ran has results expected". It is coded, reads only
the run folder (the record, each step's output and messages, the call logs), and writes `data/05-qa.json`.

A **gap** is something that should be there and is not: a step that should have run (every coded step, and a model
read that was chosen, even one that never started because a step before it crashed) with no output, or that failed; a step
that ran and did not pass its fixture check (its "found none" cannot be trusted); a step whose fixture check could not be
made at all (`ERROR`, `SETUP ERROR`, `NOT BUILT`, or `no fixture set` for any step but the pinpoint, which has no fixtures);
a chosen model read in which no passage got an answer, even after the retry; a check that looked at fewer items than it
should have and does not say why (below). A run with a gap is
**held**: no report is written, the exit code is 1, and the brief says what is missing and gives two ways on, to write the
report with what ran (`walkdown.py continue <run folder>`) or to fix the cause and audit again. After a crash the brief
counts what followed from it (`found 4 gaps (1 step failed, and the 3 after it did not start)`). Steps that ran and
whose fixture check could not be made are counted in one line (`8 steps could not be checked against their fixtures,
so a "none" from them is not measured.`). The brief holds Walkdown's own words only. If the report cannot be written when `continue` tries, the run is held again as it was.

**What each check looked at.** Every step from the inventory to the model reads says, for every check it makes, how many
items the check should have looked at (counted from the step's inputs before the check runs), how many it handled (counted
where the check handles each one), how many it did not look at and explains (a skip, an unread or not-scanned file), and how
many it found. A check that skips an item and says nothing leaves those counts short, and the run is held: `The check
"phrase.remote-load" of the step "What the text asks for" looked at 3 of 5 files; 2 are not explained.` A check that has no
line at all is a gap too, and so is a count that adds up to more than there were. A line that names a check the step does not make (another step's too), or a check twice, and a `found` that is not the results among
the findings, are gaps. So is a finding whose check is not on the step's list. A check skipped for a missing optional tool
explains its items by the skip it already writes, so it is no gap. Where a check found nothing, `full.md` (a heading at the end
of section 7) and a fold of `details.html` say how much it looked at: `What the text asks for: phrase.K.exfil, phrase.creds and 19
more checked 83 files, found none.` in `full.md` (a line for each pass), and `What the text asks for: checked 83 files with 21 checks
and 20 entries with 1 check, found none.` on the page (a line for each step). They are `qa.checked` findings and no limits. A step
gets them only when its fixture check passed, or passed with a check skipped for a missing tool, and asked at least one row. A line
counts the items its checks read: the files a check does not read (a README for a check of what a model follows) are not counted. The list of checks each step makes is in `stages/stages.json`; the lines are in the `coverage` list of each step's saved
output (`stages/CONTRACT.md`, "Coverage lines"). A line holds the checks that handle the same items in one pass, and the counts
are of the pass: one check inside a pass that stops working while its siblings run shows only in the step's fixture check.

A **limit** is something the run did not examine and says so, and it holds nothing: a check skipped because an optional
tool is not installed, the steps a stop left out, a model read in which some passages got no answer, the skips the steps
name, and the limits that stand for every run. The check gathers them in the order section 7 lists them; the report
only words them. A check is validated on `Fixtures/05-qa/`, small run folders with a known gap of each kind and runs that
must not be held, and a failed fixture check of its own is a gap like any step's.

## The reports (`06-report`)

Assembles the one-page summary, the details page, the review page, the full report, and the brief
from the steps' outputs and the run's record (`data/run.json`), and writes LOG.md with each step's
validation stamp. The reader's marks are kept in `marks.json` and carried to the next run. It adds
recommendations: each tied to a file and line, conditional on what the artifact is for, naming a
narrower way to do the same thing, listed in step order and never ranked. The report step runs
nothing: it reads the files the other steps wrote, so a change to the report is shown by
re-rendering a run, without auditing again.

---

## Validation in one paragraph

`tools/grader/grader.py` runs each step on its fixtures (`Fixtures/<step>/`) and scores the output
against `Fixtures/ANSWERS/`, which the step's code never reads. Rows are **gates** (must be
found), **negatives** (must not be found), and **recall** (measured, never required, used for
model backends). PASS means every gate and negative held; INCOMPLETE means nothing failed but a
check was skipped; FAIL means a gate was missed or a negative was hit. A step with no fixture set
(`04-pinpoint`) shows "no fixture set" in LOG.md: not a pass, and not a failure. Every audit runs
the grader after the steps and stamps the result in LOG.md. A stamp is reused while the code, the Library,
the fixtures, and the model choices are unchanged (fingerprinted in `.cache/stamps.json`), and
LOG.md says when it was measured; `--revalidate` measures afresh.

## Where the rules live

| To change or check | Look in |
|---|---|
| the finding format, every check id and field | `stages/CONTRACT.md` |
| a step's contract | `stages/<step>/CONTEXT.md` (`stages/02-coded/<step>/` for the coded steps) |
| a step's inputs, outputs, and limits (one spec per step) | `stages/<step>/specs/` |
| the phrase patterns | `Library/patterns.yaml` |
| the trifecta and grant rules | `Library/capability.yaml` |
| what the sweep and pinpoint ask a model | `Library/softreads.yaml` |
| the builder tables (programs, hosts, triggers, asks, clean, fit, cost) | `Library/tools.yaml`, `hosts.yaml`, `trigger.yaml`, `asks.yaml`, `clean.yaml`, `fit.yaml`, `loading.yaml` |
| the threat classes and phrase sets | `Library/THREATS.md`, `Library/PHRASES.md` |
| where each table's facts come from | `Library/SOURCES.md` |
| model read measurements | [MODEL-ACCURACY.md](MODEL-ACCURACY.md) |
