# Walkdown

[![tests](https://github.com/BytesFromToby/Walkdown/actions/workflows/ci.yml/badge.svg)](https://github.com/BytesFromToby/Walkdown/actions/workflows/ci.yml)

**Status: alpha, version 0.4.0** ([CHANGELOG](CHANGELOG.md)). It runs end to end and produces a report you can read. Parts of it are
experimental, and they are marked as such below.

Walkdown examines the instruction layer of AI skills and agents: the SKILL.md files, agent
definitions, reference docs, hooks, and manifests that get loaded into a model's context and
run with your permissions. It answers two questions, each answer cited to a file and line:

1. What does this text ask the model to do?
2. What does installing it grant?

Ordinary security scanners read code. Here the payload is English, so they miss it.

For someone building a skill or agent, the same reading answers the builder's questions too: will
it trigger, what does it cost in an AI's context (against the context you expect), what do you
ship that nothing uses, will it run on someone else's machine, is it ready for AI hosts other
than Claude Code, do the tools it grants fit what its words ask for, and is it current and clean.

Walkdown reports what an artifact *can* do and where that is written. It does not guess at the
author's intent, it gives no score, and it reaches no verdict. You read the evidence and decide.

The name comes from engineering: a walkdown is the step where someone walks a system as it was
actually built and records what is there, before anyone decides whether to run it.

## Looking for feedback

This is an early release, and it needs outside eyes right now.
If you try it, I would like to hear about any of these:

- **Wrong flags.** Run it on a skill or agent repository you know well. What did it flag that
  is not a concern?
- **Misses.** What did it not catch that you would expect an audit like this to find?
- **The report.** Read `summary.html`, then `details.html`. Was it clear what to look at, and
  what would you do next? If the answer is nothing, why?
- **The approach.** Walkdown gives no verdict and no score, only evidence. Does that help you,
  or does it leave you without an answer you needed?

Open an issue at https://github.com/BytesFromToby/Walkdown/issues with what you ran it on (a
link or a commit is enough) and what you saw. Short reports are welcome. If what you found is a
security problem in someone else's repository, please don't post the details in a public
issue; contact the repository's author first.

## What a run produces

One command runs every step and writes a run folder:

```
RepoResults/<name>/<date>_<hash7>/
  summary.html    one page, four questions at a glance: its size and shape (what comes in the
                  package, how much of the AI's memory it uses), is it transferable to other
                  machines (operating systems, other AI tools), does it ask only for the tools
                  it needs, anything to be careful about (finished and up to date is part of
                  it); then where its skills differ from the Agent Skills standard (Misalignment)
  details.html    the same four questions and Misalignment with everything behind them, every place folded
  review.html     one card per place to check, one at a time, for you to mark
  full.md         every finding, with file and line
  brief.md        the short summary the command prints, with no text from the repository
  LOG.md          what ran, when, and each step's validation stamp
  changes.md      what changed since the previous run of the same repository (when there is one)
  data/           everything the reports were built from: each step's raw findings, the run's
                  record (run.json), the limits (limits.md), working files
```

The documentation:

| Read | For |
|---|---|
| [docs/READING-THE-REPORT.md](docs/READING-THE-REPORT.md) | how to read the reports, part by part |
| [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) | every step and check: what it looks for, why, and where it shows |
| [docs/RUN-FOLDER.md](docs/RUN-FOLDER.md) | every file a run leaves, LOG.md, and the raw data |
| [docs/MODEL-ACCURACY.md](docs/MODEL-ACCURACY.md) | how accurate the optional model reads measured, and how far to trust them |
| [docs/STRUCTURE.md](docs/STRUCTURE.md) | how the build is laid out, with a map |

## The steps

Each step has a folder under `stages/` and a name the reports use.

| Folder | Name in the reports | Question it answers |
|---|---|---|
| `01-intake` | | Which copy is audited? A folder is read in place, a URL is cloned or an earlier clone updated |
| `02-coded/02.1-inventory` | What ships | What ships? Files, formats, hooks, agents, manifests, MCP servers |
| `02-coded/02.2-reader` | What the model actually reads | What does the model actually receive? Hidden text, invisible characters, rendered vs raw, text in images and on PDF pages, text in another language |
| `02-coded/02.3-graph` | What loads what | What loads what? Entry points, references, files nothing names, components a manifest leaves out |
| `02-coded/02.4-phrases` | What the text asks for | What does the text ask for? About 130 patterns for reaching out, taking the wheel, changing the environment, talking to the human |
| `02-coded/02.5-capability` | What this touches | What does installing it grant? The three legs of Simon Willison's lethal trifecta, install grants, pairs worth reading |
| `02-coded/02.6-builder` | Builder checks | The builder's questions: what triggers it, what it costs, what ships, what ties it to one machine, which hosts read it, whether the tools fit, whether it is current and clean |
| `03-sweep` | Needs a human read | Optional model read: is there prose no pattern matched that tells the AI to do something risky? (experimental) |
| `04-pinpoint` | The line behind each flag | Optional model read after the sweep: which line inside a flagged passage does it? (experimental) |
| `05-qa` | Checking the run | Is everything that should have run there, with its results? Looks at the saved run before the report and holds the report back when a step failed, a fixture check did not pass, a chosen model read got no answer for any passage, or a check looked at fewer items than it should have |
| `06-report` | Not examined (the limits) | Writes every report, and lists what this run was blind to |

The `02-coded` steps are deterministic: scripts, no model, the same answer every time, and so is
`05-qa`. The two model reads run only when you choose them. No model in the pipeline holds tools.

## Install

You need Python 3.12 or 3.13 (both are tested; older versions are not) and, to audit a URL,
git. In the Walkdown folder:

Windows (PowerShell or Command Prompt):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

macOS and Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The other commands in this README are written for macOS and Linux; on Windows write
`.venv\Scripts\python` where they say `.venv/bin/python`.

On Windows, keep the Walkdown folder on a short path outside OneDrive (for example
`C:\src\Walkdown`): in a deep folder, git can stop with "Filename too long".
`git config --global core.longpaths true` lifts that limit for every repository. The
repositories Walkdown audits are cloned with long paths on.

That is all the coded steps and the report need: nothing else is installed, no OCR program and no browser. Two
things follow, and a run says them under "What this run covered" when the repository has such files:

- The text drawn inside images, and on PDF pages that are only a picture, is not examined. An image's metadata is
  read, and the image is listed among the files no tests are run on.
- HTML is read from its own styles and the style sheets it links in the repository (hidden elements, `@media` rules for
  one screen, text placed off the page or clipped away, text under 2 px, text a style sheet adds, a closed
  `<details>`). How a page looks once drawn, one element over another or text over a background image, is not examined.

One optional extra, installed into the same `.venv`:

- **Model reads** (`requirements-soft.txt`), chosen at run time:
  - `--reads [model]`, after the target (`walkdown.py <target> --reads claude-opus-5-5`): the way to ask for the
    reads without naming a backend. The sweep runs on Jev when Jev is available (its key can be read and its package is found), and
    then its passages go to TypeSafe, a second remote service, in place of the Claude model; otherwise the sweep runs on the Claude
    model. The pinpoint runs on the Claude model. The Claude model is the Claude Code command (installed and logged in), run with
    `<model>` exactly as you typed it and with its tools off; a bare `--reads` names `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`. With
    Jev and `claude` both there, the sweep runs on Jev and the pinpoint on `claude`. With Jev alone, the sweep runs on Jev, the
    pinpoint does not run, and one note says so. With `claude` alone, both run on `claude`. With neither, it is refused before
    anything runs. It is resolved once, before the run starts, into
    `--sweep` and `--pinpoint`, so the run, the record, and the reports are those options' (they do not name `--reads`). It cannot be
    given with them, which stay for naming exactly what runs. It chooses nothing unless it is given, and at `continue` it chooses
    only the reads that can still run. It is put after the target: `walkdown.py --reads <target>` reads the target as the model and
    ends with a sentence that says so.
  - `--sweep jev`: TypeSafe's Jev, a remote model. Needs `TYPESAFE_API_KEY` in the environment
    (on Windows it is also read from the user environment in the registry).
  - `--sweep claude-cli` and `--pinpoint claude-cli` (the pinpoint only after `--sweep`): a read through an
    installed, logged-in Claude Code CLI, run with no tools and no project context. Name the model after a
    colon, as `claude-cli:<model>` (written as you want it); with none, it runs `WALKDOWN_SOFT_CLAUDE_MODEL`, then
    `sonnet`. Walkdown picks no model for a run where you named nothing (nothing is sent), lists no models, and asks nothing; a
    `claude-cli` with no model named runs `sonnet`, as above. The Jev
    option takes no model name (`jev:<anything>` is refused), and Jev does not read for the pinpoint.
  - A model that takes text answers with the name of one kind of instruction and no number: no model is asked
    how sure it is. The report says "(this model gives no probability)" where Jev's number would be.
  - The brief ends a read with the tokens it used: `Model reads used: Sweep 596,200 in, 31,464 out; Pinpoint 1,490 in, 73 out;
    Sweep's fixture check 39,823 in.` ("not reported" for a read whose backend gave none; "(from 5 of 9 calls)" after a total
    that only some of the calls reported, so a partial total does not read as the whole), and, under the fixture
    checks, what the sweep found in Walkdown's own test passages: `Sweep on jev: found 33 of 34 in its fixtures.`
    A long read writes a line on the terminal every 25 passages.
  - A call that gets no answer is tried once more after 2 seconds, and logged in
    `data/<step>.calls.jsonl`. The reports say how many passages still got no answer.

## Run an audit

Give it a GitHub URL, a link to a folder in a GitHub repository, or a folder on your machine.
Windows:

```powershell
.venv\Scripts\python walkdown.py https://github.com/<owner>/<repo>
.venv\Scripts\python walkdown.py https://github.com/<owner>/<repo>/tree/<branch>/<folder>
.venv\Scripts\python walkdown.py path\to\a\folder
```

macOS and Linux:

```bash
.venv/bin/python walkdown.py https://github.com/<owner>/<repo>
.venv/bin/python walkdown.py https://github.com/<owner>/<repo>/tree/<branch>/<folder>
.venv/bin/python walkdown.py path/to/a/folder
```

Started with another Python, Walkdown switches to the `.venv` one when that has its packages.

`--context 8k` (or `32k`, `200k`, `8192`) sets the context you expect the skill to run in, for
example a local model's; the default is 32,000 tokens, and the reports show 200,000 beside it.
`--hosts claude,codex,cursor` names the AI hosts you build for (any of `claude`, `codex`,
`gemini`, `cursor`, `copilot`, `windsurf`, `agents-md`); the report then says what each is missing.
`--name <name>` files the run under another name than the repository's. `--revalidate` measures
the fixture checks afresh instead of reusing a stamp.

`--until <step>` stops the run after a step, so you can look before it goes on: after getting the
copy (`--until intake`, "is this the copy I meant?"), after any of the coded steps (`--until 02.3`, or
`--until phrases`; a step can be named by its name, its number, or its word), or after all of them
(`--until coded`). The run folder, its pages, and its brief are made for the steps that ran, and the brief
says the run stopped as you asked and which steps did not run (none of them failed). To go on in
the same folder:

```bash
.venv/bin/python walkdown.py continue RepoResults/<name>/<run>
```

`continue` runs the steps after the stop, writes the whole run's pages, and prints the new brief. It
refuses, in one line and without changing the folder, when the audited folder changed since the run
stopped (audit it again), when a different Walkdown stopped the run (another version, or the same version
with other edits to its code), when the run folder lost the output of a step, or when there is nothing left to
run. A relative run folder works from any working folder.

**A held run.** Before the report is written, `05-qa` checks the saved run: did every step that should have run
leave its output, did every step that ran pass its fixture check, did a chosen model read get an answer for at
least one passage, and did every check say what it looked at, with nothing left unexplained? If not, the run is held: no report is written, the command exits 1, and the brief it prints
(from Walkdown alone: no text from the repository) names each gap and gives two ways on. To write the report
with what ran, with every gap named on the pages and in section 7:

```bash
.venv/bin/python walkdown.py continue RepoResults/<name>/<run>
```

or fix the cause (a missing key, say) and audit the repository again. A check skipped for a missing optional tool,
the steps a `--until` stop left out, and a model read that answered some passages do not hold a run.

A URL is cloned into `ReposToExamine/<repo>` (running it again updates that clone to the
latest commit; `--keep` audits it as it is, and `--fresh` clones it again). A folder link clones
the repository at that branch and audits only that folder. A repository that is not there, or is
private, stops at once: Walkdown never asks for a login. A folder is examined where it is. The run
lands in `RepoResults/<repo>/`, and the command ends with a short brief (`brief.md`) in the summary
page's terms: how many skills, commands, and agents it has and how many places break a host rule,
the tokens it takes every session and at its largest, the files not used at run time, what it
needs and how much of that is not declared, how many AI hosts have their files here, tools granted and never used, unfinished text and pinned model IDs, the
trifecta legs, the security concerns by kind, whether any step failed its fixture checks, and the paths to the
reports. Open `summary.html` first.

### Version drift

Audit the same repository again later (same URL or `--name`) and Walkdown compares the new run
with the previous one: files added and changed, new hooks, tool grants, MCP servers, changed
descriptions, new phrase hits, new network hosts, and trifecta legs or install grants that
switched on. The brief gives the counts; `changes.md` next to the new reports gives the details.
Each new or gone phrase hit says whether it came from the repository or from Walkdown's own
search terms or matching, so updating Walkdown is never mistaken for a change in the repository.
A repository that is fine when you install it can change later; this is how you see what
changed. To compare any two runs:

```bash
.venv/bin/python walkdown.py diff RepoResults/<name>/<old run> RepoResults/<name>/<new run>
```

A run made by an earlier version of Walkdown (before 0.4.0) is not compared with a new run and is
not re-rendered: the new run says so in one line. Audit the repository again to get a run in the
current form. Your marks from the earlier run still carry over.

### From a chat

Open Claude Code in the Walkdown folder and ask in plain words, for example
"walk down https://github.com/owner/repo". The `walkdown` skill in `.claude/skills/` runs the
command and relays the brief. (A web chat such as claude.ai cannot run programs on your machine,
so this needs Claude Code or another assistant that can run commands here.)

The skill relays only the brief, and never reads the audited repository or the report itself.
The brief is written by Walkdown and contains no text from the repository; the report quotes
that text, and text in a repository under audit can be written to steer the model that reads
it. You read the report.

### The optional model reads

Both are off by default, and a run that chooses neither uses no model. Each writes down exactly
what it will show the model (`data/03-sweep.input.jsonl`, `data/04-pinpoint.input.jsonl`) before
anything is sent, and keeps every answer as it came back. A line the secret scan flagged is left out of what is sent, and the
report says how many.

To read that file before anything is sent, stop the run just before the read:

```bash
.venv/bin/python walkdown.py <target> --sweep jev --until coded
```

The coded steps run, the sweep writes `data/03-sweep.input.jsonl` and stops (it reads no key and sends
nothing), and the brief names the file and the command to go on. When you are content with what it holds,
`walkdown.py continue <run folder> --sweep jev` goes on. Choosing a model option at `continue` is the
consent to send: the choice from the first command is not carried, and neither is an environment variable. A
`continue` that leaves a chosen read out says so in a note and in the report.
`WALKDOWN_SOFT_SWEEP` and `WALKDOWN_SOFT_PINPOINT` can choose a model read for a first command, but `continue`
does not read them (it prints a note when one is set); give `--reads`, `--sweep <backend>`, or `--pinpoint <backend>` to
send. The same works for the pinpoint, after the sweep (`--sweep jev --pinpoint claude-cli --until sweep`,
then `continue --pinpoint claude-cli`), unless the sweep got no answer for any passage: the pinpoint then has
nothing to read, writes no input file, and the run ends there with a note (and `05-qa` holds it, as above).

| Option | What it adds |
|---|---|
| `--reads [model]` | chooses the two reads below without naming a backend: the sweep on Jev (its passages go to TypeSafe) when Jev is available, else on the Claude Code command; the pinpoint on the Claude Code command; the model as you typed it, tools off |
| `--sweep jev`, `--sweep claude-cli[:model]` | reads every prose passage a model reads, to find instructions no pattern matched |
| `--pinpoint claude-cli[:model]` | after a sweep, names the line behind each flagged passage |

Labeling, and the other model reads of earlier versions, are not in this version, and Walkdown
refuses their options with a plain message. How accurate the model reads are:
[docs/MODEL-ACCURACY.md](docs/MODEL-ACCURACY.md).

Re-render an existing run's reports after a change to the report code (maintainers):

```bash
.venv/bin/python stages/06-report/run.py RepoResults/<name>/<run>
```

`ReposToExamine/` and `RepoResults/` are kept out of git. Copies of other people's repositories,
and reports about them, stay on your machine.

## How it is checked

Every step has one spec, in the `specs/` folder inside its own folder, and pytest tests written from it:

```bash
.venv/bin/python -m pytest -q
```

Every step also has fixtures, small repositories with known contents, and a grader scores the
step against an answer sheet the step's code never reads:

```bash
.venv/bin/python tools/grader/grader.py all
```

The same tests and graders run on GitHub on every push (Ubuntu 24.04 and 26.04 with Python 3.12
and 3.13, macOS 15 and Windows Server 2025 with Python 3.13; nothing installed but the requirements), shown by the badge at the top. Each audit runs the grader first, and the result is the step's validation stamp in `LOG.md`. A
step that fails its fixtures says so in the report. A stamp is reused while the code and
fixtures are unchanged (LOG.md says when it was measured); `--revalidate` measures afresh.

## Known limits

- **English only.** The phrase patterns are English. On other languages a clean result means
  nothing, and the report says so: it lists text in a non-Latin script, and prose passages in
  another language written in Latin script (found by common short words, with no install). The
  language check misses some one-line instructions and does not read code comments or config.
- **Static only.** Nothing is executed. Walkdown makes no claim about what a skill does when it runs.
- **Known shapes.** "What the text asks for" finds the phrasings it has patterns for. A new
  phrasing of a hostile instruction can get through; the sweep exists to narrow that gap, and is
  experimental.
- **Test data is recognized by name.** Files under folders such as `tests/` and `fixtures/`,
  or named like `test_*.py`, are set aside from the capability map and the summary, and
  counted. Test data a model-read file references directly still counts. A repository whose
  documentation discusses attacks (any security tool, Walkdown included) still reads as capable
  of them. The optional model reads are the only place Walkdown tries to tell a quote from an
  instruction, and they are experimental.
- **The model reads are experimental.** The sweep caught 11 of 12 paraphrased payloads and
  flagged none of 20 benign passages on a set written by the person who wrote the question, so it
  is a first check. The reports list only confident flags, show a "near the line" band where
  repeat reads drift, and never change a coded finding. Measurements:
  [docs/MODEL-ACCURACY.md](docs/MODEL-ACCURACY.md).
- **Secrets are found, never shown.** A line that looks like a committed secret is reported by
  location; its value is not shown in the report, and a model read does not send that line. The scan can miss a key, and one kind
  of flagged line can still show one: [Reading the report](docs/READING-THE-REPORT.md), under "Passwords and keys".

## What it is not

Not a verdict, a score, or a certification. "Clean" means these checks found nothing; it does
not mean safe. Not a linter for forceful language: "YOU MUST" is common, recommended style.
Not a judgment of authors: findings name files and lines, never people.

The full statement is `pre-planning/CHARTER.md`.

## Layout

```
walkdown.py       the router: a URL or folder in, a run folder and a brief out
.claude/skills/   the walkdown skill, for running it from Claude Code
stages/           the pipeline, one folder per step, each with CONTEXT.md (its contract), scripts,
                  specs/ (its one spec), tests/
  01-intake/ 02-coded/ (02.1 to 02.6) 03-sweep/ 04-pinpoint/ 05-qa/ 06-report/
  _shared/        code more than one step needs; not a step
  CONTRACT.md     the report format every step emits
  stages.json     the step list: each step's name, folder, and plain name
Library/          the tables, lists, and sources the steps look things up in (data only; README.md is the index)
tools/            the factory's tools: grader/ (runs a step on its fixtures and scores it),
                  compare_runs.py, baserates.py, specimen.py, fixture-generators/, model-eval/
Fixtures/         fixture repositories per step; ANSWERS/ is read only by the grader
pre-planning/     the design: charter, method, threat classes, reporting standard
docs/             reading the report, how it works, what a run leaves, the structure map
ReposToExamine/   your copies of repositories to audit (not in git)
RepoResults/      audit runs (not in git)
```

## Credits

Walkdown builds on prior research, tools, and Simon Willison's lethal trifecta: see
[CREDITS.md](CREDITS.md).

## License

Apache License 2.0: see [LICENSE](LICENSE) and [NOTICE](NOTICE). The test data in
`tools/model-eval/real-lines/` includes short excerpts from MIT-licensed repositories, which keep
their own licenses ([THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)).
