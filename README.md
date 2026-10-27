# Walkdown

[![tests](https://github.com/BytesFromToby/Walkdown/actions/workflows/ci.yml/badge.svg)](https://github.com/BytesFromToby/Walkdown/actions/workflows/ci.yml)

**Status: alpha, version 0.3.0** ([CHANGELOG](CHANGELOG.md)). It runs end to end and produces a report you can read. Parts of it are
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

This is an early release, and outside eyes are the most useful thing it can get right now.
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

One command runs every stage and writes a run folder:

```
RepoResults/<name>/<date>_<hash7>/
  summary.html    one page for a builder: will it trigger, what it costs, what ships, will it run
                  elsewhere, is it ready for any AI, do the tools fit, is it current, is it safe
  details.html    every section in full, with a Not concerned box on every row
  review.html     one card per place to check, one at a time, for you to mark
  full.md         every finding, with file and line
  LOG.md          what ran, when, and each stage's validation stamp
  data/           everything the reports were built from: each stage's raw findings, limits, working files
```

The documentation:

| Read | For |
|---|---|
| [docs/READING-THE-REPORT.md](docs/READING-THE-REPORT.md) | how to read the reports, part by part |
| [docs/HOW-IT-WORKS.md](docs/HOW-IT-WORKS.md) | every stage and check: what it looks for, why, and where it shows |
| [docs/RUN-FOLDER.md](docs/RUN-FOLDER.md) | every file a run leaves, LOG.md, and the raw data |
| [docs/MODEL-ACCURACY.md](docs/MODEL-ACCURACY.md) | how accurate the optional model reads measured, and how far to trust them |

## The stages

| # | Stage | Question it answers |
|---|---|---|
| 1 | Inventory | What ships? Files, formats, hooks, agents, manifests, MCP servers |
| 2 | Reader | What does the model actually receive? Hidden text, invisible characters, rendered vs raw, text in images and on PDF pages, text in another language |
| 3 | Graph | What loads what? Entry points, references, files nothing names, components a manifest leaves out |
| 4 | Phrases | What does the text ask for? About 125 patterns for reaching out, taking the wheel, changing the environment, talking to the human |
| 5 | Capability | What does installing it grant? The three legs of Simon Willison's lethal trifecta, install grants, pairs worth reading |
| 6 | Soft reads | What can a pattern not settle? Optional model reads (experimental) |
| 7 | Not examined | What was this run blind to? |
| 8 | Report | Assembles 1 to 7 |

Stages 1 to 5 are deterministic: scripts, no model. Stage 6 is optional and uses a model you
choose at run time. No model in the pipeline holds tools.

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

That is all stages 1 to 5 and the report need. Optional extras, installed into the same `.venv`:

- **Tesseract** (OCR of text in images and on PDF pages, stage 2): the program itself
  (Windows `winget install UB-Mannheim.TesseractOCR`, macOS `brew install tesseract`, Linux
  `apt install tesseract-ocr`) and its Python wrapper,
  `.venv/bin/python -m pip install pytesseract==0.3.13`; both
  are needed. Without it, that text is listed as not examined. PDF pages are drawn by `pypdfium2`,
  which `requirements.txt` installs.
- **Playwright** (HTML as a browser draws it, stage 2):
  `.venv/bin/python -m pip install playwright==1.64.0`, then
  `.venv/bin/python -m playwright install chromium-headless-shell`. Pages are drawn with their own scripts
  off and nothing fetched from the network. Without it, HTML is read from static style only and
  the rest is listed as not examined.

Without Tesseract or Playwright, stage 2's validation stamp reads INCOMPLETE: the fixture checks
for what that tool reads are skipped, and everything else in stage 2 is still checked.
- **Stage 6 backends** (`requirements-soft.txt`):
  - `jev`: TypeSafe's Jev, a remote labeling model. Needs `TYPESAFE_API_KEY` in the environment
    (on Windows it is also read from the user environment in the registry).
  - `laya`: a small local model, **retired** (2026-10-03). It labeled 13% of the test lines
    correctly; the code stays, but it is not recommended and not part of any plan.
  - `claude-cli`: relational reads through an installed, logged-in Claude Code CLI, run with no
    tools and no project context.

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

A URL is cloned into `ReposToExamine/<repo>` (running it again updates that clone to the
latest commit; `--keep` audits it as it is). A folder link clones the repository at that branch
and audits only that folder. A repository that is not there, or is private, stops at once:
Walkdown never asks for a login. A folder is examined where it is. The run lands in
`RepoResults/<repo>/`, and the command ends with a short brief in the summary page's terms: how
many skills, commands, and agents it has and how many places break a host rule, the tokens it takes every session and at its largest, the files not used at run time, what it
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

### From a chat

Open Claude Code in the Walkdown folder and ask in plain words, for example
"walk down https://github.com/owner/repo". The `walkdown` skill in `.claude/skills/` runs the
command and relays the brief. (A web chat such as claude.ai cannot run programs on your machine,
so this needs Claude Code or another assistant that can run commands here.)

The skill relays only the brief, and never reads the audited repository or the report itself.
The brief is written by Walkdown and contains no text from the repository; the report quotes
that text, and text in a repository under audit can be written to steer the model that reads
it. You read the report.

Stage 6 options (all off by default; with none set, stage 6 writes a question packet a person
can work through):

| Flag | What it adds |
|---|---|
| `--label jev` | labels each flagged line: an instruction to do it, not to do it, a description, a quote, or the words used in another sense |
| `--compare <backend>` | a second labeler, for agreement (Laya, the local option, is retired) |
| `--relational claude-cli` | prose reads of questions that need context (a redefined safety word, a hook that injects text, how the capabilities combine) |
| `--sweep jev` | reads every prose passage a model reads, to find instructions no pattern matched |
| `--both` | research option: Jev reads each line twice (plain, and with the matched words marked) and averages; tests were inconclusive |

Re-render an existing run's report after a change to the report code (maintainers):

```bash
.venv/bin/python stages/08-report/run.py --rerender RepoResults/<name>/<run>
```

`ReposToExamine/` and `RepoResults/` are kept out of git. Copies of other people's repositories,
and reports about them, stay on your machine.

## How it is checked

Every script has a spec (`stages/NN-*/specs/`) and pytest tests written from it:

```bash
.venv/bin/python -m pytest -q
```

Every stage also has fixtures, small repositories with known contents, and a grader scores the
stage against an answer sheet the stage code never reads:

```bash
.venv/bin/python grader/grader.py all
```

The same tests and graders run on GitHub on every push (Ubuntu 24.04 and 26.04 with Python 3.12
and 3.13, macOS 15 and Windows Server 2025 with Python 3.13; Tesseract and Playwright installed), shown by the badge at the top. Each audit runs the grader first, and the result is the stage's validation stamp in `LOG.md`. A
stage that fails its fixtures says so in the report. A stamp is reused while the code and
fixtures are unchanged (LOG.md says when it was measured); `--revalidate` measures afresh.

## Known limits

- **English only.** The phrase patterns are English. On other languages a clean result means
  nothing, and the report says so: it lists text in a non-Latin script, and prose passages in
  another language written in Latin script (found by common short words, with no install). The
  language check misses some one-line instructions and does not read code comments or config.
- **Static only.** Nothing is executed. Walkdown makes no claim about what a skill does when it runs.
- **Known shapes.** Stage 4 finds the phrasings it has patterns for. A new phrasing of a hostile
  instruction can get through; the stage 6 sweep exists to narrow that gap, and is experimental.
- **Test data is recognized by name.** Files under folders such as `tests/` and `fixtures/`,
  or named like `test_*.py`, are set aside from the capability map and the summary, and
  counted. Test data a model-read file references directly still counts. A repository whose
  documentation discusses attacks (any security tool, Walkdown included) still reads as capable
  of them; stage 6 is where quotes separate from instructions.
- **Stage 6 is experimental.** Model labels agree with a hand-labeled set about half the time
  overall, and are far more reliable when confident. The report lists only confident reads,
  shows a "near the line" band where repeat reads drift, and never changes a stage 1 to 5
  finding. Measurements: [docs/MODEL-ACCURACY.md](docs/MODEL-ACCURACY.md).
- **Secrets are found, never shown.** A line that looks like a committed secret is reported by
  location; its value never appears in a report.

## What it is not

Not a verdict, a score, or a certification. "Clean" means these stages found nothing; it does
not mean safe. Not a linter for forceful language: "YOU MUST" is common, recommended style.
Not a judgment of authors: findings name files and lines, never people.

The full statement is `pre-planning/CHARTER.md`.

## Layout

```
walkdown.py       the front door: a URL or folder in, a run folder and a brief out
.claude/skills/   the walkdown skill, for running it from Claude Code
stages/           the pipeline: one folder per stage (CONTEXT.md contract, scripts, specs/, tests/)
stages/CONTRACT.md  the report format every stage emits
grader/           runs a stage on its fixtures and scores it
Fixtures/         fixture repositories per stage; ANSWERS/ is read only by the grader
pre-planning/     the design: charter, method, threat classes, phrase sets, reporting standard
docs/             reading the report, how it works, what a run leaves
ReposToExamine/   your copies of repositories to audit (not in git)
RepoResults/      audit runs (not in git)
```

## Credits

Walkdown builds on prior research, tools, and Simon Willison's lethal trifecta: see
[CREDITS.md](CREDITS.md).

## License

Apache License 2.0: see [LICENSE](LICENSE) and [NOTICE](NOTICE). The test data in
`Fixtures/06-soft/real-lines/` includes short excerpts from MIT-licensed repositories, which keep
their own licenses ([THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)).
