# Walkdown

**Status: alpha.** It runs end to end and produces a report you can read. Parts of it are
experimental, and they are marked as such below.

Walkdown examines the instruction layer of AI skills and agents: the SKILL.md files, agent
definitions, reference docs, hooks, and manifests that get loaded into a model's context and
run with your permissions. It answers two questions, each answer cited to a file and line:

1. What does this text ask the model to do?
2. What does installing it grant?

Ordinary security scanners read code. Here the payload is English, so they miss it.

Walkdown reports what an artifact *can* do and where that is written. It does not guess at the
author's intent, it gives no score, and it reaches no verdict. You read the evidence and decide.

The name comes from engineering: a walkdown is the step where someone walks a system as it was
actually built and records what is there, before anyone decides whether to run it.

## What a run produces

One command runs every stage and writes a run folder:

```
RepoResults/<name>/<date>_<hash7>/
  LOG.md                 what ran, when, and each stage's validation stamp
  07-limits.md           what this run could not see
  report/summary.html    the page for people: what to look at first, one sentence per stage
  report/summary.md      the same summary as text
  report/full.md         every finding, with file and line
  0N-*.json              each stage's raw findings
```

How to read a report, section by section: [docs/READING-THE-REPORT.md](docs/READING-THE-REPORT.md).

## The stages

| # | Stage | Question it answers |
|---|---|---|
| 1 | Inventory | What ships? Files, formats, hooks, agents, manifests, MCP servers |
| 2 | Reader | What does the model actually receive? Hidden text, invisible characters, rendered vs raw |
| 3 | Graph | What loads what? Entry points, references, files nothing names |
| 4 | Phrases | What does the text ask for? About 125 patterns for reaching out, taking the wheel, changing the environment, talking to the human |
| 5 | Capability | What does installing it grant? The three legs of the lethal trifecta, install grants, pairs worth reading |
| 6 | Soft reads | What can a pattern not settle? Optional model reads (experimental) |
| 7 | Not examined | What was this run blind to? |
| 8 | Report | Assembles 1 to 7 |

Stages 1 to 5 are deterministic: scripts, no model. Stage 6 is optional and uses a model you
choose at run time. No model in the pipeline holds tools.

## Install

Built and tested on Python 3.13; older versions are untested.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt      # Windows
.venv/bin/python -m pip install -r requirements.txt          # macOS / Linux
```

That is all stages 1 to 5 and the report need. Optional extras:

- **Tesseract** (OCR of text in images, stage 2). Without it, image text is listed as not examined.
- **Stage 6 backends** (`requirements-soft.txt`):
  - `jev`: TypeSafe's Jev, a remote labeling model. Needs `TYPESAFE_API_KEY` in the environment
    (on Windows it is also read from the user environment in the registry).
  - `laya`: a small local model (CPU torch; see the comment in `requirements-soft.txt`).
  - `claude-cli`: relational reads through an installed, logged-in Claude Code CLI, run with no
    tools and no project context.

## Run an audit

Give it a GitHub URL or a folder:

```bash
python walkdown.py https://github.com/<owner>/<repo>
python walkdown.py path/to/a/folder
```

A URL is cloned into `ReposToExamine/<repo>`; a folder is examined where it is. The run lands in
`RepoResults/<repo>/`, and the command ends with a short brief: the trifecta legs, what to look
at first, each stage's validation stamp, and the path to `report/summary.html`. Open that page.

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
| `--compare laya` | a second labeler, for agreement |
| `--relational claude-cli` | prose reads of questions that need context (a redefined safety word, a hook that injects text, how the capabilities combine) |
| `--sweep jev` | reads every prose passage a model reads, to find instructions no pattern matched |
| `--both` | Jev reads each line twice (plain, and with the matched words marked) and averages |

Re-render an existing run's report after a change to the report code (maintainers):

```bash
python stages/08-report/run.py --rerender RepoResults/<name>/<run>
```

`ReposToExamine/` and `RepoResults/` are kept out of git. Copies of other people's repositories,
and reports about them, stay on your machine.

## How it is checked

Every script has a spec (`stages/NN-*/specs/`) and pytest tests written from it:

```bash
python -m pytest -q
```

Every stage also has fixtures, small repositories with known contents, and a grader scores the
stage against an answer sheet the stage code never reads:

```bash
python grader/grader.py all
```

Each audit runs the grader first, and the result is the stage's validation stamp in `LOG.md`. A
stage that fails its fixtures says so in the report.

## Known limits

- **English only.** The phrase patterns are English. On other languages a clean result means
  nothing, and the report says so.
- **Static only.** Nothing is executed. Walkdown makes no claim about what a skill does when it runs.
- **Known shapes.** Stage 4 finds the phrasings it has patterns for. A new phrasing of a hostile
  instruction can get through; the stage 6 sweep exists to narrow that gap, and is experimental.
- **No notion of test data.** A repository that ships attack samples (any security tool,
  Walkdown included) reads as hostile: Walkdown's own self-audit lights every stage from its
  test fixtures and quoted threat descriptions.
- **Stage 6 is experimental.** Model labels agree with a hand-labeled set about half the time
  overall, and are far more reliable when confident. The report lists only confident reads,
  shows a "near the line" band where repeat reads drift, and never changes a stage 1 to 5
  finding. Measurements: `pre-planning/soft/EVAL.md`.
- **Not built yet:** position and repetition checks, gitleaks secret scanning, version-to-version
  drift.

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
docs/             reading the report
ReposToExamine/   your copies of repositories to audit (not in git)
RepoResults/      audit runs (not in git)
```

## License

Apache License 2.0: see [LICENSE](LICENSE) and [NOTICE](NOTICE). The test data in
`Fixtures/06-soft/real-lines/` includes short excerpts from MIT-licensed repositories, which keep
their own licenses ([THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)).
