# Reading a Walkdown report

A run produces these reports, at the top of its run folder
(`RepoResults/<name>/<date>_<hash7>/`):

| File | For | What it holds |
|---|---|---|
| `summary.html` | anyone, no computer skills needed | one page, four questions at a glance, each with a short label and a one-line answer, then Misalignment; tap a line for more |
| `details.html` | improving or investigating it | the same four questions and Misalignment with everything behind them: tables, charts, and every place in folded lists; then what this run covered |
| `review.html` | walking through the places | one card per place, with the lines around it, for you to mark |
| `full.md` | checking a point | every finding, by section, with file and line |

Start with `summary.html`. Its footer links the other pages; `details.html` links back to it, and
`review.html` links both at the top right. Go to `full.md` for the evidence behind a point.
`LOG.md`, next to them, says whether each step passed its validation; `brief.md` is the short
summary the command printed; the data the reports were built from is in `data/`
([RUN-FOLDER.md](RUN-FOLDER.md)). What each check means, and why it exists, is in
[HOW-IT-WORKS.md](HOW-IT-WORKS.md).

A run made by an earlier version of Walkdown (before 0.4.0) is not re-rendered, and a new run of the
same repository does not compare itself with it: audit the repository again to get the current
pages. The marks you saved on the earlier run still carry over to the new one.

## Three rules behind every page

1. **Every finding is a location.** It says "this text, at this file and line, matches this
   shape". It does not say the author meant harm.
2. **No score.** Nothing is added up into a rating. Counts come with what they were counted over.
3. **Clean means not found.** A question on the summary with no answer and no label means its checks found nothing
   there; `details.html` lists what each check did not find in a closed "Not found" fold at the end of its section. Read
   "What this run covered" on `details.html` before trusting it.

## A suggested reading order

1. **`summary.html`**: the eight answers.
2. **`review.html`**, to walk the places one at a time and mark each.
3. **`details.html`** for everything behind an answer, and for what this run did not check.
4. **`full.md`** for any point you want to check.

## summary.html

One page, written for someone with no computer skills (since 2026-10-27). It never says the
repository is safe or unsafe, never tells you to use it or not, and gives no score.

**The header.** The title ("A Walkdown of demo"); when it was checked, the version, how many files, and the
license by name; who made the report ("This report on demo was made by Walkdown, which checks AI skill and agent
repositories for security and how well they are built."); and what it is in one sentence, starting with its name, such as "Demo is
a plugin for Claude Code: 9 skills (step-by-step instructions the AI follows for a task) and 7 helpers (assistants the
AI can hand work to)."

**What it can do**: three boxes side by side, ticked or crossed: read your files; take in content from outside, such
as web pages or files you didn't write; send your data somewhere. Under them, what the three together risk: "A tool
that does all three could be tricked into sending your data away." How many of the three this one does, and what
installing it allows, are under "What it can do" at the top of `details.html`.

**What Walkdown examined** (since 2026-11-04), in three colours, by file type (its extension):

- **White, Examined:** the checks read the file's text. It decodes as text, or the reader drew text out of it (a PDF,
  a Word document).
- **Yellow, Archives, looked inside for programs only:** archives and zip-based documents (zip, tar, 7z, RAR, zstd,
  a spreadsheet). Walkdown looked inside for programs, compiled Python, and Office macros; the text inside was not
  read.
- **Red, No tests are run on these file types:** everything else, such as a `.wasm`, a `.pkl`, a font, a compiled
  program, an image (its metadata is read; the text drawn in it is not examined), or a file that could not be read: "Walkdown does not analyze files with
  these extensions. Use with caution." The line says how many of them the AI loads.

Red marks what Walkdown cannot see, not a risk in the repository. Walkdown will never read every kind of file; this
says which ones it did not. `details.html` names the yellow and red files, and `full.md` lists every one with why.

**Four questions**, always in this order. Each has a **label** and a **one-line answer**; tap it
for a few plain bullets.

**Details →** buttons take you to `details.html`: one ends each line that has a part of its own there, and one at the
bottom of each question opens its section. The page opens at that part, with the rest closed, and its **← Summary**
button brings you back to the line you left. Each question has a small glyph, the same on both pages, so you land on the
one you left; on a wide screen `details.html` keeps the sections down its left side, the one on screen marked, with the
**← Summary** button at the top of that list. Three cards show a picture on their face, open or closed: the package bar,
the three system boxes, and one dot per place found, by colour.

| Label | Means |
|---|---|
| **N to look at** (amber) | something a rule found: a host's rule broken, a security kind, the tools against the words |
| **N notes** (amber) | published guidance and harmless facts |
| a measure (blue) | a fact such as "up to 21%" or "3 of 7 tools" |
| no label, no answer | the question's checks ran and found nothing (the "Not found" fold on `details.html` says what each did not find) |
| **Not measured** (grey) | a step did not run, or the run was stopped before it (`--until`) |

1. **Size and Shape** (a working name). Two parts, the package first:
   - **What comes in the package.** Every file in one of four groups, as one bar with its legend in two columns: the files that do
     the work (skills, helpers, the files they read, scripts they run, settings the host reads),
     notes for people, tests and build tools, and files not linked or referred to. Then how much smaller it
     would be without the last two groups. That is a fact; whether to leave them out is yours.
   - **How much of the AI's memory it uses.** The one place the page counts **tokens** (pieces
     of text, about ¾ of a word each). The table shows what is always there once installed, its
     biggest skill or helper with everything it reads, any extra for someone working inside the
     repository's own folder, and the files nothing uses. Each row gives its share of a local AI
     (`--context`, default 32,000 tokens; "Your AI" when you set another) and of Claude (200,000).
     Then the room the AI keeps for its list of skills. Tokens are estimated from file sizes, about
     4 bytes of English per token. When an earlier run of the same repository exists, a line says
     what changed since then.
2. **Is this transferable to other machines?** Two parts:
   - **Operating systems.** Three boxes first, Linux, Windows, and Mac: blue when nothing found trips
     that system, a yellow outline and a count when something does. Then programs it expects but never says to install, add-ons
     its scripts use but never list, and places that tie it to the computer it was built on: personal
     paths, scripts saved with Windows line endings, commands for one system only, backslashes in
     paths, scripts not marked as runnable, `python` where many computers have only `python3`, and
     file names that match only when capital letters are ignored.
   - **Other AI tools.** A box per tool first, blue when it finds files here. Which of seven AI tools (Claude Code, Codex,
     Gemini CLI, Cursor, GitHub Copilot, Windsurf, and others that read `AGENTS.md`) find its files
     where they sit, copies kept for two tools that say different things, and features only one tool
     understands. Run with `--hosts claude,codex` (any of `claude`, `codex`, `gemini`, `cursor`,
     `copilot`, `windsurf`, `agents-md`) and the label counts what the tools you named are missing.
     Which tools to support is yours. What each tool reads is a dated list in
     `Library/hosts.yaml`.
3. **Does it ask only for the tools it needs?** Each skill's, command's, and helper's own words,
   over the files it reads, against the tools it is allowed: tools allowed and never used, work it
   asks for that no allowed tool can do, helpers with no tools list (they get every tool), read-only
   claims a tool beside them contradicts, steps that repeat "until it works" with no stated limit,
   and hooks that run on every message or action. The cue lists are in `Library/asks.yaml`
   and `Library/fit.yaml`.
4. **Anything to be careful about?** The places in six fixed security kinds, always in this order:
   1. **Hidden text that reads like an instruction**: text the AI receives and a person does not
      see, which also matches the wording of an instruction. The summary quotes what it says, up
      to 80 characters: the only text from the repository on this page.
   2. **Hidden characters that spell out text**: invisible characters in a file the AI reads that
      spell words no pattern matched. The summary names the place; `details.html` and the place's
      card on `review.html` say what they spell.
   3. **Runs code**: hooks, commands run when the skill loads, commands you are asked to run.
   4. **Passwords, keys, and secrets**: a password, key, or token saved in the files (test data
      and lines that only look like one are left out), and wording that gathers secrets or asks for a
      password or key.
   5. **Reads secrets, calls out, or shares**: network calls, data sent elsewhere, instructions
      fetched from elsewhere.
   6. **Lasting changes or permissions**: settings, profiles, permissions, actions that are hard to
      undo, and read-only claims a tools list contradicts.

   A place counts once, as `review.html` counts it, even when it falls in two kinds. On the summary,
   each line is one kind of place with a colored dot, red, yellow, or blue, and the lines run red first.
   The first red lines sit under **Passwords, keys, and secrets**: a saved password, key, or token,
   wording that gathers secrets, and wording that asks for one, ending "Values are not shown in these
   reports." Each line gives its count and its first place. Then how many more places are only wording that shapes
   how the AI decides, and how many places you have marked so far, with a link to the review page.
   What it can do is at the top of the page (above). Model reads are never counted here.

   **Finished and up to date**, a heading at the end of this card with its own label: "To do" marks and placeholders in what ships, claims tied to
   a date ("before August 2025, use the old API" becomes wrong), AI model versions fixed in place
   (a fact: a name like "sonnet" follows the newest version), and older tool names. The summary
   shows no line of the repository's here; `details.html` quotes each one.

**Misalignment**, the last card: "Things that are not standard but are not security flaws.", with the number of
issues, and nothing to open; its **Details →** opens the section on `details.html`, which holds the rest: where its
skills differ from the
[Agent Skills standard](https://agentskills.io/specification), the open format for skills that many AI tools read
(developed by Anthropic and released as an open standard). Only skills are looked at; the standard does not cover
commands or helpers. A skill's header is the block between the two `---` lines at the top of its `SKILL.md`, written in
YAML (lines such as `name: my-skill`). Under **Skill Formatting**, a fold for each way a skill differs, opening with
a sentence and then every place: no header at the top; a header not in the expected format (YAML); a setting set more than once in a
header (YAML allows each once); a name that isn't lowercase letters, digits, and single
hyphens, is over 64 characters, or isn't the skill's folder's name; a missing, empty, or over-long description; a
`compatibility` note over 500 characters; and settings the standard doesn't define (it defines six: `name`,
`description`, `license`, `compatibility`, `metadata`, `allowed-tools`), such as `version` or Claude Code's own
`model`. Blank lines before the header and a hidden byte-order mark are not called out; a header below blank lines is
still checked. Under **Descriptions too
alike**, the pairs of skills that describe themselves so alike that the AI may pick the wrong one (Walkdown's own
measure). The rules are dated, with their source, in `Library/trigger.yaml` and `Library/hosts.yaml`.

When a model read got an answer for some passages and none for others, one line under the cards gives how many
("Needs a human read: 5 of 12 passages got no answer, after one retry."). When a step did not work in this run
(it did not run, it did not pass its fixture check, or a model read got no answer for any passage), a
line at the bottom names it. A step that did not work can miss places, so the page may show fewer
than there are; a model read adds no place to this page, so that is left out when the model read is the only
step that did not work. When Walkdown found nothing, question 7 says so too: "Not every step worked, so it
may have missed some." Steps that ran and whose fixture check could not be made are said in a sentence of their
own ('8 steps could not be checked against their fixtures, so a "none" from them is not measured.'), which does not say a
step failed. When a step did not run at all, it never says "found none". A run you
stopped with `--until` says it stopped after a step as you asked, and the steps after it are not
named as steps that did not work; the cards no step measured say "Not measured" and why. What Walkdown does not
examine in this repository's files (the text drawn in images, how HTML looks once drawn) is listed under "What this run
covered" on `details.html`, and `full.md` lists every file it left unread.

The footer says the one thing to keep in mind: Walkdown reads the files without running anything,
leaves the judgment to you, and finding nothing does not mean a repository is safe.

## details.html

The same four questions, each opening with the same label and answer, then everything behind it, then Misalignment.
Every question, and every part inside it, is folded and closed when you open the page; tap one to open it. A bar
under the header jumps to each question. A part you reach from a Details button on the summary opens by itself, and
every open fold has a **← Summary** button back to the summary.

### Header

The title ("A Walkdown of demo, in detail"), when it was checked, the version, how many files, and a **← Summary**
button. Under the header, the
summary's **What Walkdown examined**, with the yellow and red files named: the ones the AI loads first, then the
rest, up to 50 a colour, and a count of those in test or fixture folders. Under
those, one line on the license: the license each top-level license file matches ("License: MIT
(LICENSE)."), or that the file is not a license Walkdown recognizes and how it begins. With no
license file it gives what a top-level `license` field says (`package.json`, a plugin manifest),
and with neither, "No license found". "Also stated" lists any different license found in a
subfolder or another field, such as a skill that ships its own. Walkdown matches the license's
wording; it does not say what the license allows. Every license file and field is in `full.md`
section 1.

### Behind each question

1. **Size and Shape**: the package part, every file by group, with its size; then **Files worth a look**, when there is
   something: contents of a different type than the name says, programs in compiled
   form and compiled Python (which Walkdown cannot read, and which can run without their source), archives
   or documents that hold a program or Office macros, archives (looked inside for programs; the text inside is
   not read), symlinks, files
   the AI reads where blank lines or spaces push text out of view, and files the AI reads that are longer
   than a reviewer's viewer shows (2,000 lines or 50 KB). Then the memory part: the summary's table, the room for the
   list of skills, and how big each skill and helper gets, as bars.
2. **Other machines**: the other-systems part, the places by file, the programs it expects and whether it says to
   install each, and every place by kind; then the other-AI-tools part, every tool with the files here it reads, the
   skills to install, every copy kept for two tools, and every one-tool feature by kind.
3. **Tools**: every place by kind, and each helper with its tools.
4. **Careful**: below; then **Finished and up to date**, every place by kind, with its line quoted.

After the four questions, **Misalignment**: the standard and its six settings, then a fold for each Skill Formatting
line with every place, and one for the skills too alike.

### Careful, in full

**What it can do** is at the top of `details.html`, as on the summary: the three boxes, ticked or crossed; how many of
the three this one does and what installing it allows (runs commands by itself, adds its own text before you type, and so
on); and, under "Why it can do these", why each box is ticked. The details page follows the summary's order throughout. The
three boxes are what Simon Willison calls the
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
review page, with what was found, the line quoted, and Walkdown's note (a hook's host, what hidden
characters spell).

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

**Passwords, keys, and secrets.** Lines that look like a password, key, or token saved in the files, and how
many in test data were set aside; then the wording that gathers secrets or asks for a password or key. Values are not
shown in these reports: open the file to check one. When no
scanner ran, it says it was not checked. A file the scanner could not scan is named here as well,
and it may hold one. So is a lock file, which the scan leaves out because the hashes in one look like keys. A model read does not send a line flagged here, so it did not read what else stands on that line: "What this run
covered" says how many lines, and names a file a read did not send because the scanner could not scan it.

The scan goes by the shapes of known keys and by keywords, so finding nothing here does not prove no key is there. It does not flag a key
in a shape it does not know, a key spelled only in hidden characters, a password in a sentence ("the password is ..."), `token = value`,
or `password = value` with no quotes in a Markdown file. Nothing marks such a line, so a page can show it and a model read sends it. One
kind of flagged line also keeps its text: when everything flagged on a line is base64 that decodes to readable words, the line reads as
holding no key, so a key the scanner did not flag beside that text can still show in `full.md` and `data/`. A model read leaves that line
out. When a key does stand beside such text, the line is hidden and the decoded words are still shown, since a key never decodes to
readable words. The decoded words are scanned too: a key in them is flagged at the line, its kind ends in "(in text decoded from
base64)", and the decoded words are hidden with the line.

### What changed since an earlier run

Only when an earlier run of the same repository was a different version, or the same version and
Walkdown changed since: what changed, in counts and Walkdown's own words, with every change, file
by file, in `changes.md`. New and gone phrase hits say where they came from: changes in the
repository, Walkdown's search terms, or Walkdown's matching code.

### What this run covered

Last on the page: a step that did not work, the optional model reads when they did not run, or
that every step ran and passed its own checks. Then every limit of this run, folded: checks
skipped (usually an optional tool not installed), and the limits of every run (static only, English only, MCP servers read in Python, JavaScript, TypeScript, and Go only,
patterns can miss).
The files no check read are one line there, "Files the checks did not read: ... (What Walkdown examined, at the top)": the
yellow and red rows at the top of the page name them, so this list does not count them again (since 2026-11-04).
After that, in a fold of its own, "Checks that found nothing (N)": what the checks that found nothing looked at, a line for each step,
as counts ("What the text asks for: checked 64 files with 9 checks and 20 entries with 1 check, found none. Some were skipped
(listed above)."; "What this touches: checked 382 findings with 1 check, found none. 1 check had nothing to look at."). N counts
checks. `full.md` says it under "Checks that found nothing" at the end of section 7, a line for each pass, with the check ids.
Recommendations for the builder, each tied to a file and line and never ranked, are in `full.md`.

How far to trust "found none". A step's "found none" is as good as its fixture check, and a count of what it looked at is as good as
the count. Walkdown says "checked N, found none" only for a step whose fixture check passed, or passed with a check skipped for a missing tool,
and asked at least one row (a model read whose rows were all skipped asked none), never for a step that has no fixtures (the
pinpoint), failed its check, or could not be checked. And the count is of the files the check reads: a check of what a model
follows does not count the README written for people. And the counts have a limit: the checks
that run in one pass over the same files are counted together, so one check inside a pass that stops working while the checks
beside it run shows in the step's fixture check and nowhere in the counts. The page says "checked 66 files with 2 checks", and that is
all it knows about those 2 checks.

**After a hold.** Before the report is written, Walkdown checks that everything that should have run
is there with its results (`05-qa`). When a step failed, a step did not pass its fixture check (or the
check could not be made), a chosen model read got no answer for any passage, or a check looked at fewer files than it
should have and does not say why ("The check ... looked at 3 of 5 files; 2 are not explained."), the command stops with a brief and no report, and asks
which way you want to go: `walkdown.py continue <run folder>` writes the report with what ran, or you fix
the cause and audit again. If you continue, this section and section 7 of `full.md` name each gap in the
same words as any other step that did not work ("The step ... did not run to completion", "... did not pass
its fixture check (FAIL)", "... could not be checked against its fixtures: it gave SETUP ERROR", "... has no fixtures to
be checked against", "... got no answer for any passage"), and the page's last line says not every
step worked (the steps that only could not be checked against their fixtures are in the sentence of their own above;
they ran). A model read that the first command chose and `continue` left out is named in section 6, in the log, and
in section 7 as not run. Read a page like that as the part of the run that did work: a step that did not run can
miss places, so the page may show fewer than there are.

## review.html

Every place to check, one card at a time: places the fixed rules found first, places only an
optional model read flagged at the end.

**One card per place.** Every finding on the same line is one card, whichever step found it. A
file loaded only by a folder load whose line also matches two patterns is one card that says "and
2 more findings on this line" and tags each step that found something. A sentence repeated across
files is one card that lists every place it appears, and the findings at those places join it. A
passage of several lines stays on its own card. A passage the optional sweep flagged, with no
pattern hit inside it, is a card of its own: "What the model said" comes first, with its score, then
(when the pinpoint read ran and its quote is found in the passage) "Where in the passage", the line
it names and a plain sentence on it. Those cards are marked experimental.

**On each card**: the file and line, linked to the text this run read; "What was flagged", one
block per finding, each pattern described once in plain words (what it looks for, and why a
pattern would care); when the line tells the AI to stay read-only, "Is it enforced?", which says
whether a tool setting backs it (a restricting flag on the line, or the owner's tools list), or that
it is stated in the text only, and names other routes in the same skill that can write; then the
line with three lines either side (from `data/normalized/text/`),
the matched words highlighted. Invisible characters show as `U+XXXX`: every character on the
invisible-character list, a variation selector where two or more stand together (one selector after an
emoji is ordinary and shows as it is), and any other format or control character. When a place's line hides text in tag characters or in a run of
variation selectors, the card's note says what it spells. In a file where the run
found what looks like a secret, no lines around the place are shown.

Each card ends with one line on what only running the skill can
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
(`python stages/06-report/run.py <run folder>`) reads the file into all three pages, and
the other two count your marks. A file saved from the Not concerned boxes `details.html` had
before 2026-10-27 still loads, and its marks are kept.

**Marks carry over.** A new run of the same repository with no `marks.json` of its own starts
from the newest earlier run's marks. Each mark names what was flagged (the file and the text of
the line, or the address, or the file and the reason), never the line number alone, so a mark
follows its line when lines move and drops away when the line itself changes. A carried mark says
which run it is from until you change it, and `review.html` says how many earlier marks match
nothing in this run. Files saved before 2026-10-20 still load, matched by place id. Marks saved
before 0.4.0 still carry over too: the pages recognize a place by either of its two keys.

## full.md

Every finding, grouped by section:

| Section | Holds |
|---|---|
| 1 What ships | entry points, the structural census, descriptions, tool grants, hooks, manifests |
| 2 What the model actually reads | divergences (raw against rendered, and PDF pages as drawn against their text layer), lines changed by folding, non-Latin runs, passages in another language, metadata, unread files |
| 3 What loads what | entry points used, orphans, load-only files, dynamic loads, components on disk a manifest leaves out, dangling references, depth |
| 4 What the text asks for | every hit, by group (4a to 4d) and check, then the tables: endpoints, guarded actions, definitions, conflicts, safety words; and the builder checks on triggering, other AI hosts, and what is current and clean |
| 5 What this touches | each trifecta leg with every citation, install grants with evidence (what the settings grant, then what only the wording asks for), bytes in context at load, agent posture, pairs; and the builder checks on what it costs and what ships, and whether the tools fit |
| 6 Needs a human read | the model reads that ran (the sweep's flagged passages, with the pinpoint's line when it ran), or one line saying none was chosen |
| 7 Not examined | the same list as `data/limits.md`, including, for each model read that has passages with no answer, how many ("5 of 12 passages got no answer, after one retry"), the reasons counted, and the call log |

Every line in it has a file and line you can open.

## The optional model reads in the reports

The sweep and the pinpoint are optional and experimental; with neither chosen, section 6 says "No
model read was chosen" and names the two options. `--reads` chooses them without naming a backend, and the reports then name the
backends it chose, as they do for `--sweep` and `--pinpoint`. When they ran:

- **Sweep passages** with no phrase pattern hit come first, strongest first.
- **Bands.** A sweep passage is listed at p >= 0.6; 0.4 to 0.6 is counted as near the line; lower
  reads are counted only. A model that takes text gives no probability: its flagged passages are listed with the words
  "(this model gives no probability)" where the number would be, and it has no near-the-line band.
- **Tokens.** Section 6 and the brief name what each read used: `Model reads used: Sweep 596,200 in, 31,464 out;
  Pinpoint 1,490 in, 73 out; Sweep's fixture check 39,823 in.` These are the counts the backends reported ("not
  reported" where one gave none). A total with "(from 5 of 9 calls)" after it is partial: only 5 of the 9 calls reported a count, so
  the real total is higher. The fixture check is named only when it was run in this run.
- **The sweep's own fixtures.** The brief says `Sweep on jev: found 33 of 34 in its fixtures.`: how many of Walkdown's
  own test passages, which have known answers, the model read as expected. It is a number to look at and holds
  nothing.
- **Why bands:** the same passage read twice moves by up to about 0.1, so a single cutoff would
  put passages in or out of the review page by chance.
- **No effect on findings.** A model read never changes, removes, or adds a coded finding, and a
  confident read of a passage does not uncheck a trifecta leg.
- **A call that got no answer** (an error from the service, an answer that is not one of the options,
  an answer that cannot be read) is tried once more after 2 seconds, and logged in
  `data/03-sweep.calls.jsonl` or `data/04-pinpoint.calls.jsonl`. A passage that still has no answer is
  skipped. Section 7 and the details page say how many passages got no answer, with the reasons by kind of
  failure and a status (429, 503), and the summary says it for a read that answered some. A read in
  which no passage got an answer (no key, a rejected key, the service down) is named as a step that did
  not work, and the headline says the coded checks are complete and the model read did not work (with a
  check skipped for a missing tool, that the coded checks ran, and where the skipped ones are named). The
  pinpoint does not run after a sweep like that.

How accurate these reads are, and what that was measured on: [MODEL-ACCURACY.md](MODEL-ACCURACY.md).

## Worked example: Walkdown on itself

Walkdown is a security tool, so its repository is full of attack text: test fixtures with
hidden exfiltration instructions and fake plugins with injecting hooks, and design documents that
quote attacks to describe them.

- **Test data.** About 950 findings sit in `Fixtures/` and the test folders. They are set aside,
  counted in section 5, and kept off the summary. The "runs at load" grant disappears with them:
  every hook in the repository is a fixture.
- **What remains.** All three trifecta legs and many phrase points, almost all from the design
  documents and the specs, which describe attacks in detail. The review page walks each place, and
  you tell the quotes from the instructions. In the audit of 2026-10-02 the optional sweep also
  flagged one passage across all the prose a model reads outside the fixtures.
- **The lesson.** The report shows where everything is. A repository whose documentation
  discusses attacks will read as capable of them, and the review page is where the quotes separate
  from the instructions.
