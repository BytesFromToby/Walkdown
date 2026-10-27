# Reading a Walkdown report

A run produces these reports, at the top of its run folder
(`RepoResults/<name>/<date>_<hash7>/`):

| File | For | What it holds |
|---|---|---|
| `summary.html` | building a skill or agent | one page: what it costs in an AI's context, what you ship by how it is used, and whether it is safe (the security concerns by kind, with one example each; what it can do) |
| `details.html` | improving or investigating it | every section in full, every list expandable, and a Not concerned box on every row |
| `review.html` | walking through the places | one card per place, with the lines around it, for you to mark |
| `full.md` | checking a point | every finding, by stage, with file and line |

Start with `summary.html`. Each page links the others at the top right. Go to `full.md` for the
evidence behind a point. `LOG.md`, next to them, says whether each stage passed its validation;
the data the reports were built from is in `data/` ([RUN-FOLDER.md](RUN-FOLDER.md)). What each
check means, and why it exists, is in [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

Runs made before 2026-10-20 also had `summary.md` (the summary as text) and `summary-v1.html` (an
earlier summary page). Re-rendering such a run removes them.

## Three rules behind every page

1. **Every finding is a location.** It says "this text, at this file and line, matches this
   shape". It does not say the author meant harm.
2. **No score.** Nothing is added up into a rating. Counts come with what they were counted over.
3. **Clean means not found.** An empty section means these stages found nothing there. Check
   what was not checked (Other details on `details.html`) before trusting a zero.

## A suggested reading order

1. **`summary.html`**: whether it triggers, what it costs, what ships, whether it runs elsewhere, whether it is ready for any AI, whether the tools fit the job, whether it is current and clean, the security concerns, and what it can do.
2. **`review.html`**, to walk the places one at a time and mark each.
3. **`details.html`** for everything else: the files, every outside link, every hidden place,
   and Other details, which says what the run did not check and whether every step passed its
   fixtures. A step that did not pass puts a pill on that heading; do not trust its findings in
   this run.
4. **`full.md`** for any point you want to check.

## summary.html

One page for someone building a skill or agent (since 2026-10-26; before, it was written for
someone deciding whether to use one). It says what the repository costs in an AI's context, what
ships, and what Walkdown found that could be a security concern. It never says the repository is
safe or unsafe, never tells you to use it or not, and gives no score.

**The headline.** Two sentences. The first: "N files; every session takes X tokens once
installed, and the largest skill at its fullest Y (Z% of a C-token context)." When that is more
than the expected context, it says so. The second: "Walkdown found security concerns in this
repository: N places, of K kinds." When you have marked some Not concerned, it says how many.
With none: "Walkdown found none of the security concerns it looks for.", and Is it safe? says
"Nothing to point out here." The page's footer says the one thing to keep in mind: Walkdown reads
the files without running anything, leaves the judgment to you, and finding nothing does not mean
a repository is safe.

**Will it trigger?** How each skill, command, and agent triggers: Claude chooses it by its
description, only on matching files, only when typed, or it never loads. Then the descriptions'
size against Claude Code's skill listing, which holds about 1% of the context for every installed
skill, and one row per kind of problem: frontmatter its host does not read (YAML that does not
parse, `---` not on the first line), agents Claude Code does not load, names and descriptions that
break a rule (each place says whose: the Agent Skills spec, claude.ai uploads, or Claude Code),
keys, values, and tool names no host takes (with the one it is closest to), descriptions that
overlap so Claude may choose the wrong one, descriptions cut in the listing, and published guidance
(say when to use it; write in the third person). The overlap measure is Walkdown's own: two
descriptions in one listing sharing at least half the words of the shorter, and at least four,
once the words most of the listing shares are set aside. Every rule is dated, with its source,
in `stages/04-phrases/trigger.yaml`.

**What it costs.** What an AI loads, and when, against the context you expect: every session once
installed (each skill's, agent's, and command's description, and hook text), every session for
whoever works in the folder (CLAUDE.md, AGENTS.md, and what they import), and the largest skill:
when it runs, with everything it names, and with its wildcard and folder loads. Each row gives
tokens and its share of your expected context (`--context`, default 32,000 tokens) and of 200,000
(Claude). A skill reaches the files in its own folder (only that folder installs with it); what
it names outside is listed, not counted. An agent runs in its own context. Tokens are estimated
from size, about 4 bytes of English text per token; hook output and MCP servers' tool lists show
only when they run, so they are named, not counted.

**What you ship.** Every file in one of three bands: loads into the AI (skills, agents, commands,
project instructions, files they name, files reached only by a wildcard or folder read), used
another way (scripts it runs, configs the host reads), and not used at run time (written for
people, build material, and files nothing points to). Then, when there are any: "If the N files
nothing points to and the M build files were left out of what you ship: K smaller, and T tokens
no longer within an AI's reach." That is a fact with its saving; whether to leave them out is
yours. Every file is listed on `details.html`.

**Will it run on someone else's machine?** What it uses, the programs Walkdown recognizes and the
packages its scripts import, and what of that the repository never declares (in a dependency
file, a skill's `compatibility` field, or an install line). Then one row per kind of place that
ties it to the machine it was built on: personal paths, shell scripts committed with Windows
line endings, scripts or commands for one system only, references written with backslashes,
scripts run without the executable bit, `python` where many systems have only `python3`, and
references whose letter case only matches on Windows and macOS. Each row gives its count, why
it breaks elsewhere, and its first place; `details.html` lists every one.

**Is it ready for any AI?** One line per AI host (Claude Code, Codex, Gemini CLI, Cursor, GitHub
Copilot, Windsurf, and the other tools that read `AGENTS.md`): the instruction files, skills, MCP
config, and hooks here that it reads, or what it would read. What each host reads is a dated list
with its sources (`stages/04-phrases/hosts.yaml`). Then the skills no host reads where they sit
(a host reads them once they are installed), copies kept for two hosts that say different things
(`CLAUDE.md` and `AGENTS.md`, say: Claude Code reads one, the others read the other), and one row
per kind of feature only one host understands in text meant for any AI: skill frontmatter keys
outside the Agent Skills set (claude.ai and the Skills API refuse such a skill), Claude Code's own
words such as `$ARGUMENTS` and its tool names, `@` imports in `AGENTS.md`, and hooks. Run with
`--hosts claude,codex` (any of `claude`, `codex`, `gemini`, `cursor`, `copilot`, `windsurf`,
`agents-md`) and the section starts with what each host you named is missing. Which hosts to
support is yours; without `--hosts`, every host is a plain fact.

**Do the tools fit the job?** Each skill's, agent's, and command's own words, over the files it
reads, against the tools it grants. One row per kind: tools granted that run, write, reach out, or
start subagents and that nothing it reads asks for (a skill's `allowed-tools` only pre-approve, so
those are "pre-approved and never used"); work its words ask for that no tool it may use can do (a
subagent's `tools` list is an allowlist); agents with no tools list, which get every tool and MCP
tool; read-only claims a tool beside them contradicts; loops with no stated limit ("repeat until
the tests pass" with no number of tries or give-up on that line or the next; a limit may be stated
elsewhere); and hooks that run on every prompt or tool call, with how large their output is when it
becomes context. Reading tools (Read, Grep, Glob) are never reported. The cue lists are in
`stages/04-phrases/asks.yaml` and the tool families and hook facts in
`stages/05-capability/fit.yaml`, dated, with sources.

**Is it current and clean?** Facts with locations, never a judgment: TODO and FIXME markers,
placeholders, and draft notes in what ships (a template's placeholders are left out); claims
tied to a date in text the AI reads ("before August 2025, use the old API" is the published
guidance's own example of text that becomes wrong; a bare date is a record and is left out);
pinned model IDs, with how many are distinct (an alias such as `sonnet` follows the provider's
recommended version, a full ID stays on one, and Walkdown never says one is retired); and older
tool names named in text. When an earlier run of the same repository exists, "What it costs"
adds a line with what changed since then, before and now.

When a step did not work in this run (it did not run, or it did not pass its fixture check), a line at
the bottom of the page names it: a step that did not work can miss places, so the page may show
fewer than there are. Other details on `details.html` says why. When Walkdown found nothing, the
headline says so too: "but not every step worked, so it may have missed some." A missing optional
tool (OCR, HTML as a browser draws it) is never named on this page; Other details on
`details.html` and `full.md` list what it left unread.

**Is it safe?** One row per security concern kind that has places, always in this order:

1. **Hidden text that reads like an instruction**: text the AI receives and a person does not
   see, which also matches the wording of an instruction.
2. **Runs code**: hooks, commands run when the skill loads, commands you are asked to run.
3. **Looks like a committed secret**: a password, key, or token saved in the files (test data and
   lines that only look like one are left out).
4. **Reads secrets, calls out, or shares**: credentials, network calls, data sent elsewhere.
5. **Lasting changes or permissions**: settings, profiles, permissions, actions that are hard to
   undo, and read-only claims a tools list contradicts.

Each place is in one row only, the first that fits. A row gives its count, how many you marked
Not concerned, and one example linked to its card on the review page; "N more" opens that section
of `details.html`. Nothing inside a row is ranked. Under the rows, one line counts the places that
are wording only (instructions that change how the AI reads, decides, or answers), and one line
counts model reads when a model ran; model reads are never concerns.

**What it can do.** The three trifecta boxes in one row (see below), what they mean together
(each is ordinary on its own; a tool that does all three can be steered by text from outside into
sending your data away), and one line naming the general risks present, such as running commands on its own or adding text before you type.

**Questions before use** are on `details.html` (since 2026-10-26): the questions the findings
raise for someone deciding whether to install it, in place of a verdict: **permissions
to hold back** (agents with no tools list, a shell, writing files, the web, hooks, MCP servers,
each with where it is listed), **what to try first** (the parts of the repository with the most
places to check, test folders left out), and **before you leave it running unattended** (the
places that run code or make lasting changes, lines telling the AI it need not ask, read-only
claims a tools list contradicts, hidden instructions, committed secrets). Only questions with
evidence in this run appear. The answers are yours.

What was not checked, and whether every step passed its fixtures, are under Other details on
`details.html`.

## details.html

Every section in full, for someone improving or investigating the repository. The page follows
the questions a reader brings, in this order. Every section says so in words when it found
nothing ("No outside links", "Nothing hidden"), or that it was not checked when its stage did not
run.

### Header

"Walkdown report on" the repository, where the copy came from, the version it was pinned to, the
run, and the Walkdown version. At the top right, links to the summary and to `review.html`.

Under those, one line on the license: the license each top-level license file matches ("License:
MIT (LICENSE)."), or that the file is not a license Walkdown recognizes and how it begins. With no
license file it gives what a top-level `license` field says (`package.json`, a plugin manifest),
and with neither, "No license found". "Also stated" lists any different license found in a
subfolder or another field, such as a skill that ships its own. Walkdown matches the license's
wording; it does not say what the license allows. Every license file and field is in `full.md`
section 1.

### Not concerned

Every row that names a place or an address has a **Not concerned** box: the places under each
trifecta box, Worth a look files, outside links, hidden places, secrets, and the places under
each risky-ask headline. Tick it when you have read the row and it is fine for what the
repository is for. A ticked row is dimmed, its section's heading says how many are marked, and
"Hide Not concerned" in the bar under the header folds them away. A place's box and its card on
`review.html` are the same mark; a place you marked Concerned or Not sure there says so beside
its box. Saving and carrying marks over: see [Your marks](#your-marks).

### The lethal trifecta

Three boxes, one per leg of what Simon Willison calls the
[lethal trifecta](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents):

| Leg | Checked when the repository... |
|---|---|
| **Can read your data** | can read the user's data wherever it lives: files, secrets, settings, connected accounts |
| **Can take outside input** | can bring in text the user didn't write: the web, other people's issues or email, MCP tools, third-party code |
| **Can send data out** | can move data off the machine or into shared places: web requests, webhooks, pushes, posts |

The names start with "Can" because a static read shows what a skill could do; whether it does
is only seen by running it.

A box is checked when at least one piece of evidence supports it; under each checked box is the
number of places that do. Click it to open the list: each place links to its card on the review
page when it has one, or else to this run's copy of the file, and has its Not concerned box (all
of them are also in `full.md` section 5). Each box is ordinary on its own. A tool that does
all three can be steered by text from outside into sending your data away.

Checked boxes come first, then unchecked ones, colored by how many there are: the first green,
the second yellow, the third red. Red means all three at once, the combination the trifecta warns
about. The color never says one leg is worse than another. If a model read every line cited for a
leg as not an instruction (a quote, a description), a note says so under the box. The box stays
checked: a model's read never removes a finding.

Under the boxes, what installing it allows, in plain words. Two belong to a box and sit in its
column: connects to outside services (MCP servers, by name) under **Can take outside input**, and
connects to the internet under **Can send data out**. The rest is **General risks**: runs commands
on its own (each hook, with its event and command), adds text to the AI's context before you type
(how many bytes), makes changes that last after the session, asks for more permissions than the
default, and agents with their own tools (and how many have no tools list, so they can use every
tool the AI has). What was not found is one "Not found" line. Details: [HOW-IT-WORKS.md](HOW-IT-WORKS.md#install-grants-capgrant).

### Files

In the open: how many files, how many file types, and their total size. **Worth a look** appears
only when there is something to see: a file of unknown type, contents of a different type than
the name says, archives (their contents are not read), symlinks, and files the AI reads that are
longer than a reviewer's viewer shows (2,000 lines or 50 KB). Each file is listed with its box;
a long list opens from its count.

Behind "Files and map": every file type and script language, the largest files, the files a tool
loads first, the descriptions always in the AI's context, platform manifests, long lines, and the
map: how files are reached from the starting points (by a reference, only through a folder or use
of wildcards, or only mentioned that way), the files nothing points to, and broken file references
(paths written in the files that point at files not in the folder). Some files are named only when
code runs, so the map can miss links.

### Outside links

Every web address the skill names. Walkdown gathers them and **opens none of them**, so nothing
here says whether a link works or what it serves. In the open: how many links, to how many
different domains, how many sit in text the AI reads, and how many domains the skill's docs never
mention. Behind the toggle: a table grouped by domain, one row per link, with the file and line
and who reads that file (the AI, people, scripts, or test data), and a Not concerned column. A
long link is shortened on the page; its Copy button copies the whole address. A box marks the
address, so every row with the same address takes the same mark. Runs made before this list
existed show domains.

### Hidden text

Text the AI receives that a person reading the file on screen would not see. First the count of
places, and how many are in files the AI reads, which opens the list of every hidden place (where,
linked to this run's copy of the file, and how it hides); then their kinds: hidden comments,
invisible characters, text colored like its background, image descriptions, and the like. Hidden text that
also reads like an instruction is called out in a yellow box: its count opens the list of those
places, each linked to its card on the review page. It also counts the other direction for images and PDFs:
text inside an image, or drawn on a PDF page but missing from the PDF's text layer (a picture
of an instruction), which a model that reads the page as an image sees. A location in a PDF,
DOCX, or image reads "file (extracted text, page N, line M)": the line in the text Walkdown read
from it, since such a file has no lines of its own. Then lines that hold invisible characters or letters
from another alphabet that look like plain ones (the two kinds that can make a line say something
other than what a person sees), counted by kind. Typography (curly quotes, dashes, ellipses,
non-breaking spaces, symbols) is left off this page; the full report lists every changed line.
Then stretches in a
non-Latin script, and passages in another language written in the same alphabet (Spanish, German,
and so on). The risky-ask patterns read English only, so a passage in any other language is one
to read yourself; the full report lists each one.

### Committed secrets

Lines that look like a password, key, or token saved in the files, which scanner found them, and
what was set aside (lines in test data; hashes, variable names, plain words, local test passwords).
One row per place, linked to its review card. The value is never shown: open the file to check it. When no scanner ran, the section says it was
not checked.

### Risky asks and things to check

**The numbers.** How many lines match the wording of a risky request, and who reads them (the AI,
scripts, people, test data); the matches by kind (reaching out, taking the wheel, changing the
environment, talking to you); when a model labeled them, how many it read as a real instruction to
do the flagged thing; how many actions that should ask you first have no step asking you, with
the ones the text forbids counted apart; and how many read-only lines the AI follows are backed by
a tool setting, stated in the text only, or owned by a tools list that can write.

**Things to check.** The headlines, with how many places each covers. Each headline opens its
places: the location linked to its review card, the quote, and the "A reviewer model's reading
questions this" line when a model read questions it. Hidden text and secrets are left to their own
sections.

| Headline | What it means |
|---|---|
| Runs commands on its own | a hook that runs whenever the host fires its event, without anyone asking |
| Nothing refers to this file / Loaded only by a folder or use of wildcards, named by nothing, and it reads like an instruction | a file a reviewer following references would not open, which also matches a phrase pattern |
| Matches the wording of ... | the text matches a phrase pattern; the quote lets you judge, and the note gives the pattern's base rate |
| ..., stated as a prohibition | the same, on a line that forbids the action ("Never have the user paste an API key"); kept so you can read it, and said so, with any exception ("unless ...") |
| A word is defined more than one way / Redefines a safety word / An irreversible or prohibited action with no confirmation step | from stage 4's tables of definitions and guarded actions; an action the line forbids is never listed as one with no confirmation step |
| Flagged text past the reader window | in a long file the AI reads, flagged lines after the point where a reviewer's viewer may stop showing it |
| The same flagged sentence in several files | a sentence a pattern flagged, repeated across files |
| An image the model is pointed at | an image a file the AI reads references or loads; the note says whether this run could read text in it |
| Test data that the model is pointed at | a file in a test or fixture folder that a file the AI reads references directly |
| An instruction the model sees before you type anything | text a context-injecting hook prints into the session |

**Base rates.** A "Matches the wording" note says how often its pattern turns up in the other
audited repositories: **rare** (none of them), **uncommon** (one), **common** (two or more). A rare
pattern is more worth reading. The level describes the pattern across repositories; it says
nothing about this one.

**What is kept off this list.** Hits in human-facing files (README, docs, changelog) and in test
data (tests, fixtures) are counted, never listed: installing the artifact does not put them in
front of a model. They are all in `full.md`.

When a model ran (stage 6), one line says how many model reads (experimental) are on the review
page, with a link to how accurate they measured: [MODEL-ACCURACY.md](MODEL-ACCURACY.md).

### Changes since an earlier run

Only when an earlier run of the same repository was a different version, or the same version
and Walkdown changed since: what changed, in counts and Walkdown's own words, with every change,
file by file, in `changes.md`. New and gone phrase hits say where they came from: changes in the
repository, Walkdown's search terms, or Walkdown's matching code. With the same version, the
section says so first, since every difference then comes from Walkdown.

### Recommendations

Suggestions for the builder, each tied to a file and line, each conditional ("if this skill does
not need X, ..."), each naming a narrower way to do the same thing. Never ranked: ranking by
importance would be a score by another name.

### Other details

Closed by default. **What was not checked**: checks that apply to this repository and did not run,
split into not built yet, skipped in this run (usually an optional tool not installed), and not
needed here, with the full list behind its own toggle, including the limits of every run (static
only, English only, patterns can miss). **Fixture results**: before a run is trusted, each step
runs on small test repositories with known contents and is scored against an answer sheet it
never reads; PASS for each step, and a pill on the heading when one did not pass.

## review.html

Every place to check, one card at a time: places the fixed rules found first, places only a model
flagged at the end.

**One card per place.** Every finding on the same line is one card, whichever step found it. A
file loaded only by a folder load whose line also matches two patterns is one card that says "and
2 more findings on this line" and tags each step that found something. A model read of that line
joins the same card under "What the model said", marked experimental. A sentence repeated across
files is one card that lists every place it appears, and the findings at those places join it. A
passage of several lines stays on its own card.

**On each card**: the file and line, linked to the text this run read; "What was flagged", one
block per finding, each pattern described once in plain words (what it looks for, and why a
pattern would care); when the line tells the AI to stay read-only, "Is it enforced?", which says
whether a tool setting backs it (a restricting flag on the line, or the owner's tools list), or that
it is stated in the text only, and names other routes in the same skill that can write; then the
line with three lines either side (from `data/normalized/text/`),
the matched words highlighted. Invisible characters show as `U+XXXX`. In a file where the run
found what looks like a secret, no lines around the place are shown.

When a model read of the line says it is not an instruction (a prohibition, a description, a
quote, the words in another sense), the card says so in one line: "A reviewer model's reading
questions this", with who read it and the score. The finding stays; the same line appears under
the place on `details.html`. Each card ends with one line on what only running the skill can
show for that kind of place ("Only running it shows whether the AI acts on this line"); cards
that state a fixed fact, such as a committed secret, have none. A line that tells the AI to stay
read-only in a skill whose own tools list can write is a place of its own: "Says read-only, but
its tools list can write".

Cards that are harder to judge say what you are deciding, under **To decide:**: model reads, test
data the AI is pointed at, and images. A test-data or image card also shows **where the AI is
pointed at it** (the line that names the file, with context) and what is in it (the start of the
file, or the text read from the image).

You mark each place **Concerned** (you want to look into it, or change it), **Not concerned**
(you read it, and it is fine for what the skill is for), or **Not sure**, with an optional note.
One mark per card. Walkdown makes no call on any place. The marks are yours, and they change
nothing in the other reports.

The walk comes in passes, chosen with the buttons above the progress bar: **Rule findings** (the
places a rule found, walked first), **Model reads, optional** (an optional pass of their own,
numbered "Model read 1 of N"), and **Not sure, again** (the places you marked Not sure, taken
when you open it, so the list holds still while you mark them again). Back, Next, and Next
unmarked move within the pass you are in; the index lists the model reads under their own
heading.

## Your marks

The marks on `review.html` and the Not concerned boxes on `details.html` are one set. They are
yours: Walkdown never sets one, and a mark changes no finding and nothing in `full.md`.

Marks are kept in your browser as you go. To keep them with the run, use "Download marks.json"
(at the end of `review.html`, or in the bar at the top of `details.html`) and save the file in
the run folder, next to the pages. Each download holds the marks from both pages that the run
already had, so saving from either one keeps the other's. "Load a marks file" reads a saved file
into the page you are on. Re-rendering the reports
(`python stages/08-report/run.py --rerender <run folder>`) reads the file into all three pages;
`summary.html` counts your Not concerned marks.

**Marks carry over.** A new run of the same repository with no `marks.json` of its own starts
from the newest earlier run's marks. Each mark names what was flagged (the file and the text of
the line, or the address, or the file and the reason), never the line number alone, so a mark
follows its line when lines move and drops away when the line itself changes. A carried mark says
which run it is from until you change it, and `review.html` says how many earlier marks match
nothing in this run. Files saved before 2026-10-20 still load, matched by place id.

## full.md

Every finding, grouped by stage:

| Section | Holds |
|---|---|
| 1 What ships | entry points, the structural census, descriptions, tool grants, hooks, manifests |
| 2 What the model actually reads | divergences (raw against rendered, and PDF pages as drawn against their text layer), lines changed by folding, non-Latin runs, passages in another language, metadata, unread files |
| 3 What loads what | entry points used, orphans, load-only files, dynamic loads, components on disk a manifest leaves out, dangling references, depth |
| 4 What the text asks for | every hit, by group (4a to 4d) and check, then the tables: endpoints, guarded actions, conditionals, definitions, conflicts, safety words |
| 5 What this touches | each trifecta leg with every citation, install grants with evidence, bytes in context at load, agent posture, pairs |
| 6 Needs a human read | the stage 6 models used, the sweep's flagged passages, every question and every answer |
| 7 Not examined | the same list as `data/07-limits.md` |

Every line in it has a file and line you can open.

## Stage 6 in the reports

Stage 6 is optional and experimental; with no model chosen, its section says "packet only". When
models ran:

- **Sweep passages** with no stage 4 hit come first, strongest first.
- **"Do" reads** are listed at p >= 0.9; 0.7 to 0.9 is counted as near the line; lower reads are
  counted only. For the sweep the bands are p >= 0.6 listed and 0.4 to 0.6 near the line.
- **Why bands:** the same line read twice moves by up to about 0.1, so a single cutoff would put
  lines in or out of the review page by chance.
- **Evidence marks:** a confident read that a line is not an instruction marks it where stage 5
  cites it as evidence, and never removes it.

How accurate these reads are, and what that was measured on: [MODEL-ACCURACY.md](MODEL-ACCURACY.md).

## Worked example: Walkdown on itself

Walkdown is a security tool, so its repository is full of attack text: test fixtures with
hidden exfiltration instructions and fake plugins with injecting hooks, and design documents that
quote attacks to describe them.

- **Test data.** About 950 findings sit in `Fixtures/` and the test folders. They are set aside,
  counted in section 5, and kept off the summary. The "runs at load" grant disappears with them:
  every hook in the repository is a fixture.
- **What remains.** All three trifecta legs and many stage 4 points, almost all from the design
  documents and stage specs, which describe attacks in detail. Stage 6 reads most of those lines
  as descriptions or quotes, and the sweep flagged one passage across all the prose a model
  reads outside the fixtures.
- **The lesson.** The report shows where everything is. A repository whose documentation
  discusses attacks will read as capable of them, and section 6 is where the quotes separate from
  the instructions.
