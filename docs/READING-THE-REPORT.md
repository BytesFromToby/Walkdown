# Reading a Walkdown report

A run produces these reports, at the top of its run folder
(`RepoResults/<name>/<date>_<hash7>/`):

| File | For | What it holds |
|---|---|---|
| `summary.html` | anyone, no computer skills needed | one page, eight questions at a glance, each with a short label and a one-line answer; tap a line for more |
| `details.html` | improving or investigating it | the same eight questions with everything behind them: tables, charts, and every place in folded lists; then what Walkdown didn't check |
| `review.html` | walking through the places | one card per place, with the lines around it, for you to mark |
| `full.md` | checking a point | every finding, by stage, with file and line |

Start with `summary.html`. Its footer links the other pages; `details.html` links back to it, and
`review.html` links both at the top right. Go to `full.md` for the evidence behind a point.
`LOG.md`, next to them, says whether each stage passed its validation; the data the reports were
built from is in `data/` ([RUN-FOLDER.md](RUN-FOLDER.md)). What each check means, and why it
exists, is in [HOW-IT-WORKS.md](HOW-IT-WORKS.md).

Runs made before 2026-10-20 also had `summary.md` (the summary as text) and `summary-v1.html` (an
earlier summary page). Re-rendering such a run removes them. Re-rendering any older run draws its
pages in the current design; a question the older run did not check says "Not measured".

## Three rules behind every page

1. **Every finding is a location.** It says "this text, at this file and line, matches this
   shape". It does not say the author meant harm.
2. **No score.** Nothing is added up into a rating. Counts come with what they were counted over.
3. **Clean means not found.** "Nothing to look at" means these checks found nothing there. Read
   "What Walkdown didn't check" on `details.html` before trusting it.

## A suggested reading order

1. **`summary.html`**: the eight answers.
2. **`review.html`**, to walk the places one at a time and mark each.
3. **`details.html`** for everything behind an answer, and for what this run did not check.
4. **`full.md`** for any point you want to check.

## summary.html

One page, written for someone with no computer skills (since 2026-10-27). It never says the
repository is safe or unsafe, never tells you to use it or not, and gives no score.

**The header.** The name; when it was checked, the version, how many files, and the license by
name; and what it is in one sentence, such as "A plugin for Claude Code: 9 skills (step-by-step
instructions the AI follows for a task) and 7 helpers (assistants the AI can hand work to)."

**Eight questions**, always in this order. Each has a **label** and a **one-line answer**; tap it
for a few plain bullets.

| Label | Means |
|---|---|
| **N to look at** (amber) | something a rule found: a host's rule broken, a security kind, the tools against the words |
| **N notes** (amber) | published guidance and harmless facts |
| a measure (blue) | a fact such as "up to 21%" or "3 of 7 tools" |
| **Nothing to look at** (green) | the question's checks ran and found nothing |
| **Not measured** (grey) | the run was made before this check, or a step did not run |

1. **Will its skills switch on when they should?** Whether each skill, command, and helper will
   be picked up as written: settings at the top the AI can't read, names and descriptions that
   break a rule, settings that look like a typo, tool names the AI doesn't know, descriptions that
   overlap or are cut short, and published guidance (say when to use it; describe what it does
   instead of writing "I" or "you"). Every rule is dated, with its source, in
   `stages/04-phrases/trigger.yaml`.
2. **How much of the AI's memory does it use?** The one place the page counts **tokens** (pieces
   of text, about ¾ of a word each). The table shows what is always there once installed, its
   biggest skill or helper with everything it reads, any extra for someone working inside the
   repository's own folder, and the files nothing uses. Each row gives its share of a local AI
   (`--context`, default 32,000 tokens; "Your AI" when you set another) and of Claude (200,000).
   Then the room the AI keeps for its list of skills. Tokens are estimated from file sizes, about
   4 bytes of English per token. When an earlier run of the same repository exists, a line says
   what changed since then.
3. **What comes in the package?** Every file in one of four groups, as one bar: the files that do
   the work (skills, helpers, the files they read, scripts they run, settings the host reads),
   notes for people, tests and build tools, and files nothing refers to. Then how much smaller it
   would be without the last two groups. That is a fact; whether to leave them out is yours.
4. **Will it work on someone else's computer?** Programs it expects but never says to install, add-ons
   its scripts use but never list, and places that tie it to the computer it was built on: personal
   paths, scripts saved with Windows line endings, commands for one system only, backslashes in
   paths, scripts not marked as runnable, `python` where many computers have only `python3`, and
   file names that match only when capital letters are ignored.
5. **Will it work with AI tools other than Claude?** Which of seven AI tools (Claude Code, Codex,
   Gemini CLI, Cursor, GitHub Copilot, Windsurf, and others that read `AGENTS.md`) find its files
   where they sit, copies kept for two tools that say different things, and features only one tool
   understands. Run with `--hosts claude,codex` (any of `claude`, `codex`, `gemini`, `cursor`,
   `copilot`, `windsurf`, `agents-md`) and the label counts what the tools you named are missing.
   Which tools to support is yours. What each tool reads is a dated list in
   `stages/04-phrases/hosts.yaml`.
6. **Does it ask only for the tools it needs?** Each skill's, command's, and helper's own words,
   over the files it reads, against the tools it is allowed: tools allowed and never used, work it
   asks for that no allowed tool can do, helpers with no tools list (they get every tool), read-only
   claims a tool beside them contradicts, steps that repeat "until it works" with no stated limit,
   and hooks that run on every message or action. The cue lists are in `stages/04-phrases/asks.yaml`
   and `stages/05-capability/fit.yaml`.
7. **Is it finished and up to date?** "To do" marks and placeholders in what ships, claims tied to
   a date ("before August 2025, use the old API" becomes wrong), AI model versions fixed in place
   (a fact: a name like "sonnet" follows the newest version), and older tool names. The summary
   shows no line of the repository's here; `details.html` quotes each one.
8. **Anything to be careful about?** The places in five fixed security kinds, always in this order:
   1. **Hidden text that reads like an instruction**: text the AI receives and a person does not
      see, which also matches the wording of an instruction. The summary quotes what it says, up
      to 80 characters: the only text from the repository on this page.
   2. **Runs code**: hooks, commands run when the skill loads, commands you are asked to run.
   3. **Looks like a committed secret**: a password, key, or token saved in the files (test data
      and lines that only look like one are left out).
   4. **Reads secrets, calls out, or shares**: credentials, network calls, data sent elsewhere.
   5. **Lasting changes or permissions**: settings, profiles, permissions, actions that are hard to
      undo, and read-only claims a tools list contradicts.

   A place counts once, as `review.html` counts it, even when it falls in two kinds. Each kind
   gives its count and its first place. Then how many more places are only wording that shapes
   how the AI decides, and how many places you have marked so far, with a link to the review page.
   "More" shows **what it can do**: three boxes, ticked or crossed (read your files; take in
   content from outside; send your data somewhere), what all three together risk, and what
   installing it allows (runs commands by itself, adds its own text before you type, and so on).
   Model reads are never counted here.

When a step did not work in this run (it did not run, or it did not pass its fixture check), a
line at the bottom names it: a step that did not work can miss places, so the page may show fewer
than there are. When Walkdown found nothing, question 8 says so too: "Not every step worked, so it
may have missed some." When a step did not run at all, it never says "found none". A missing
optional tool (OCR, HTML as a browser draws it) is never named on this page; "What Walkdown didn't
check" on `details.html` and `full.md` list what it left unread.

The footer says the one thing to keep in mind: Walkdown reads the files without running anything,
leaves the judgment to you, and finding nothing does not mean a repository is safe.

## details.html

The same eight questions, each opening with the same label and answer, then everything behind it.
A bar under the header jumps to each question. Long lists are folded; tap to open them.

### Header

The name, when it was checked, the version, how many files, and a link back to the summary. Under
those, one line on the license: the license each top-level license file matches ("License: MIT
(LICENSE)."), or that the file is not a license Walkdown recognizes and how it begins. With no
license file it gives what a top-level `license` field says (`package.json`, a plugin manifest),
and with neither, "No license found". "Also stated" lists any different license found in a
subfolder or another field, such as a skill that ships its own. Walkdown matches the license's
wording; it does not say what the license allows. Every license file and field is in `full.md`
section 1.

### Behind each question

1. **Switching on**: every skill, command, and helper in a table (how it switches on), and every
   place by kind with why.
2. **Memory**: the summary's table, the room for the list of skills, and how big each skill and
   helper gets, as bars.
3. **Package**: every file by group, with its size; then **Files worth a look**, when there is
   something: a file of unknown type, contents of a different type than the name says, archives
   (their contents are not read), symlinks, and files the AI reads that are longer than a
   reviewer's viewer shows (2,000 lines or 50 KB).
4. **Other computers**: the places by file, the programs it expects and whether it says to install
   each, and every place by kind.
5. **Other AI tools**: every tool with the files here it reads, the skills to install, every copy
   kept for two tools, and every one-tool feature by kind.
6. **Tools**: every place by kind, and each helper with its tools.
7. **Finished**: every place by kind, with its line quoted.
8. **Careful**: below.

### Careful, in full

**Why it can do these.** The three boxes are what Simon Willison calls the
[lethal trifecta](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents):

| Box | Ticked when the repository... |
|---|---|
| **Read your files** | can read the user's data wherever it lives: files, secrets, settings, connected accounts |
| **Take in content from outside** | can bring in text the user didn't write: the web, other people's issues or email, MCP tools, third-party code |
| **Send your data somewhere** | can move data off the machine or into shared places: web requests, webhooks, pushes, posts |

A box is ticked when at least one piece of evidence supports it, and the line under the boxes
says how many places do and why. A static read shows what a skill could do; whether it does is
only seen by running it. Each one is ordinary on its own. A tool that does all three can be
steered by text from outside into sending your data away. Every citation is in `full.md`
section 5.

**Every place, by kind.** One folded list per security kind, each place linked to its card on the
review page, with what was found, the line quoted, Walkdown's note (a hook's host, what hidden
characters spell), and a model read that questions it, when one did ("A reviewer model's reading
questions this").

**Text hidden from people.** Text the AI receives that a person reading the file on screen would
not see: how many places, by how they hide (hidden comments, invisible characters, text colored
like its background, image descriptions, and the like), by file, and every one. It also counts the
other direction for images and PDFs: text inside an image, or drawn on a PDF page but missing from
the PDF's text layer (a picture of an instruction), which a model that reads the page as an image
sees. A location in a PDF, DOCX, or image reads "file (extracted text, page N, line M)": the line
in the text Walkdown read from it, since such a file has no lines of its own. Then lines that hold
invisible characters or letters from another alphabet that look like plain ones, counted by kind;
typography (curly quotes, dashes, ellipses, non-breaking spaces, symbols) is left off this page,
and the full report lists every changed line. Then stretches of text in another alphabet and
passages in another language. The risky-ask patterns read English only, so a passage in any other
language is one to read yourself.

**Wording that shapes how the AI decides.** How many lines match the wording of a risky request,
who reads them (the AI, scripts, people, test data), and the matches by group: reaching out,
taking the wheel, changing the environment, talking to you. Then **Worth reading first**: the
wording-only places by kind, with a few locations and a quote. Hits in files for people (README,
docs, changelog) and in test data are counted, never listed: installing the artifact does not put
them in front of a model. They are all in `full.md`.

**Web addresses.** Every site the skill names, how many links, who reads them, and whether its
docs name the site. Walkdown gathers them and **opens none of them**, so nothing here says whether
a link works or what it serves.

**Passwords and keys.** Lines that look like a password, key, or token saved in the files, and how
many in test data were set aside. The value is never shown: open the file to check it. When no
scanner ran, it says it was not checked.

### What changed since an earlier run

Only when an earlier run of the same repository was a different version, or the same version and
Walkdown changed since: what changed, in counts and Walkdown's own words, with every change, file
by file, in `changes.md`. New and gone phrase hits say where they came from: changes in the
repository, Walkdown's search terms, or Walkdown's matching code.

### What Walkdown didn't check

Last on the page: a step that did not work, the optional model reads when they did not run, or
that every step ran and passed its own checks. Then every limit of this run, folded: checks
skipped (usually an optional tool not installed), and the limits of every run (static only,
English only, patterns can miss). Recommendations for the builder, each tied to a file and line
and never ranked, are in `full.md`.

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

You mark places on `review.html`; `summary.html` and `details.html` say how many are marked so
far. The marks are yours: Walkdown never sets one, and a mark changes no finding and nothing in
`full.md`.

Marks are kept in your browser as you go. To keep them with the run, use "Download marks.json"
at the end of `review.html` and save the file in the run folder, next to the pages. "Load a marks
file" reads a saved file into the page. Re-rendering the reports
(`python stages/08-report/run.py --rerender <run folder>`) reads the file into all three pages, and
the other two count your marks. A file saved from the Not concerned boxes `details.html` had
before 2026-10-27 still loads, and its marks are kept.

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
