# Reading a Walkdown report

A run writes one folder: `RepoResults/<name>/<date>_<hash7>/`. This page walks through what is
in it, section by section, and how to read each signal. Examples come from Walkdown's audit of
its own repository.

## The files

| File | For | What it holds |
|---|---|---|
| `report/summary.html` | most readers | what to look at first, one sentence per stage, the trifecta checklist |
| `report/summary.md` | the same, as text | one status line per stage and up to five points under each |
| `report/full.md` | checking a point | every finding, grouped by stage, with file and line |
| `LOG.md` | trust in the run | the source and its hash, the Walkdown version, which models ran, each stage's validation stamp |
| `07-limits.md` | trust in a zero | everything this run could not see |
| `0N-*.json` | tools | each stage's raw findings in the format of `stages/CONTRACT.md` |
| `06-packet.md` | a person doing stage 6 by hand | the stage 6 questions, with the text each one is about |

Start with `summary.html`. Go to `full.md` when you want the evidence behind a point.

## Three rules behind every page

1. **Every finding is a location.** It says "this text, at this file and line, matches this
   shape". It does not say the author meant harm.
2. **No score.** Nothing is added up into a rating. Counts always come with what they were
   counted over.
3. **Clean means not found.** A section with nothing in it means these stages found nothing
   there. Check `07-limits.md` before trusting a zero.

## The summary page

### Header and tiles

The header names the repository, where the copy came from, and the hash it was pinned to, so a
later reader can tell exactly which version was examined. The tiles count files examined, things
to look at first, and things not examined.

### What it can do: the trifecta checklist

Three boxes, one per leg of the lethal trifecta:

| Leg | Checked when the repository... |
|---|---|
| **Reads your data** | reads the user's data wherever it lives: files, secrets, settings, connected accounts |
| **Takes outside input** | brings in text the user didn't write: the web, other people's issues or email, MCP tools, third-party code |
| **Sends data out** | moves data off the machine or into shared places: web requests, webhooks, pushes, posts |

A box is checked when at least one piece of evidence supports it. **Three checked boxes are
common in well-built repositories**: any agent that reads files, uses the web, and pushes
commits has all three. The combination raises risk. It is not an issue on its own. The evidence
for each leg is listed under section 5 of `full.md`.

If stage 6 read every line cited for a leg as not an instruction (a quote, a description), a note
says so under the box. The box stays checked: a model's read never removes a finding.

### Look at these first

Cards, in stage order. Each card has a stage tag, a headline, the places it applies to, the
quoted text, and sometimes a note. Places with the same headline share one card.

How to read the headline:

- **"Matches the wording of ..."** (stage 4): the text matches a phrase pattern. The pattern
  can match innocent text; the quote lets you judge. The note says how often that pattern turns
  up in other audited repositories:
  - **rare**: in none of them
  - **uncommon**: in one
  - **common**: in two or more

  A rare pattern in your report is more worth reading than a common one. The level is a fact
  about the pattern, measured over the repositories audited so far; it says nothing about this
  repository.
- **"Hidden when rendered, and reads like an instruction"** (stage 2): the model receives text a
  person viewing the file does not see (an HTML comment, a zero-width character, white-on-white).
- **"Loaded only by a folder or glob, named by nothing"** (stage 3): no file names it directly,
  so a reviewer following references would not find it.
- **"Runs commands on its own"** (stage 1): a hook that runs whenever the host fires its
  event, without you asking.
- **"An instruction the model sees before you type anything"** (stage 5): text that a
  context-injecting hook prints into the session.
- **Stage 6 cards** (only when stage 6 ran with a model; see below).

### Stage by stage

One plain sentence per stage, with a pill when the stage did not pass its validation (see
"Validation stamps"). "Technical detail" opens the status line from `summary.md`.

### Recommendations

Suggestions for the builder, each tied to a file and line, each conditional ("if this skill
does not need X, ...") and each naming a narrower way to do the same thing. They are listed in
stage order and never ranked: ranking by importance would be a score by another name.

## The sections

### 1 What ships

Every file, its format, and the structures that matter: entry points (skills, agents, commands,
hooks, manifests, MCP configs, project instructions such as CLAUDE.md), descriptions that are
always in context, tool grants, hooks.

> Self-audit: 451 files, 5 hooks (4 host configs), 10 agent or command definitions.

All five hooks are in Walkdown's test fixtures. Walkdown itself ships none.

### 2 What the model actually reads

Each file is read twice: as raw text (what a model receives) and as rendered (what a person
sees). Differences are **divergences**: comments, zero-width characters, bidirectional controls,
hidden HTML, white-on-white, text in image metadata. Lines that change when invisible
characters are folded away are listed too, because a pattern may only match the folded line.

### 3 What loads what

The graph of references from entry points. Watch for:

- **orphans**: files no entry point reaches
- **files loaded only through a dynamic load**: a glob or folder read pulls them in, but nothing
  names them
- **dangling references**: a path that is named but does not exist

The graph is incomplete by construction (a glob's targets are resolved as of the review).

### 4 What the text asks for

Phrase patterns, in four groups:

| Group | Covers |
|---|---|
| 4a Reaching out | sending data out, reading secrets, loading remote instructions |
| 4b Taking the wheel | overriding instructions, claimed consent, redefined words, anti-review, conditionals |
| 4c Changing the environment | permissions, persistence, installs, settings, prohibited actions |
| 4d Talking to the human | telling the person to run something risky |

Plus four tables:

- **endpoints**: hosts named anywhere, and whether the docs name them
- **confirm-first and prohibited actions**: and whether a confirmation step exists
- **conditionals**: behavior that changes on the clock, the environment, the version, or the harness
- **definitions**: and words defined more than one way, or safety words redefined

Each hit carries its **audience**, decided by path:

| Audience | Files |
|---|---|
| model | skills, CLAUDE.md, agent prompts |
| subagent | prompts for agents it dispatches |
| tool | scripts, build files |
| human | README, docs, changelog |

Human-facing hits are counted but kept out of the summary's points and never count as capability.

### 5 What this touches

The trifecta legs with their evidence, then **install grants**:

| Grant | Meaning |
|---|---|
| exec-at-load | something runs when the artifact loads |
| context-injection | text enters the session on its own |
| persistence | changes that outlive the session |
| network | reaches outside the machine |
| elevated | widened permissions |

Then **text in context at load**, in bytes per host, and **agent posture**: each agent's tools
against its stated job, with least-privilege agents noted. Last come **pairs**: two findings on
the same line that are worth more together, such as hidden text that also matches a pattern.

### 6 Needs a human read

Questions a pattern cannot settle. Stage 6 is optional and **experimental**. With no model
chosen, it writes `06-packet.md` for a person to work through. With models, three kinds of
answer appear:

- **Labels** (`--label`): for each line a pattern flagged, is it an instruction to do the
  matched action, not to do it, a description, a quote or example, or the words in another
  sense? The summary lists a line as a real instruction only at **p >= 0.9**. Reads between 0.7
  and 0.9 are **near the line**: the same line read twice moves by up to about 0.1, so those
  could go either way. They are counted in the summary and tagged in `full.md`.
- **Relational reads** (`--relational`): prose answers to questions that need context, such as
  how the capabilities combine, or what a redefined safety word changes. The reader is told the
  evidence came from pattern matching and may be wrong, and to say so when it is.
- **Sweep** (`--sweep`): a model reads every prose passage, looking for instructions no pattern
  matched. A passage is listed at **p >= 0.6**; 0.4 to 0.6 is near the line. Passages with **no
  stage 4 hit inside** come first, because they are the only stage 6 points about text nothing
  else located. Each says which kind of action it was read as asking for:

  | Kind | The passage tells the reader to... |
  |---|---|
  | override | set aside its other instructions |
  | send-out | send data out |
  | secrets | gather secrets or private files |
  | skip-user | act without asking the user, or keep something from them |
  | remote-instructions | fetch outside text and follow it |
  | persist | make lasting changes outside the task |

Every stage 6 answer is a located observation. None changes a finding in sections 1 to 5. Their
accuracy is measured and recorded in `pre-planning/soft/EVAL.md`.

> Self-audit: the sweep read 1,506 passages. Outside the test fixtures it flagged one, a passage
> in the red-team notes that quotes a permission flag.

### 7 Not examined

What the run was blind to: optional tools that were missing (Tesseract, Playwright), checks not
built yet, files that could not be read, stages whose validation did not pass. A zero in a
section is only as good as this list allows.

## Validation stamps

Before an audit, every stage runs against its fixtures, small repositories with known
contents, and a grader scores it against an answer sheet the stage code never reads. `LOG.md`
records the result per stage:

| Stamp | Meaning |
|---|---|
| **PASS** | every required check found what it should, and nothing it shouldn't |
| **INCOMPLETE** | nothing failed, but a check was skipped, usually for a missing optional tool. The self-audit's stage 2 is INCOMPLETE because Tesseract was not installed, so text inside images went unread. |
| **FAIL** | the stage missed something it is required to catch, or flagged something it must not. Its findings in this run should not be trusted. |

"Recall" numbers next to a stamp are measured and never required: they say how much a model
backend got right on the labeled fixtures.

## Worked example: Walkdown on itself

Walkdown's own report lights up every stage. It has all three trifecta legs, five install
grants, and over a thousand phrase hits.

Almost all of it comes from two places:

- **Test fixtures.** `Fixtures/` holds deliberately hostile samples: hidden exfiltration
  instructions, fake plugins with injecting hooks, paraphrased payloads. Every hook and the
  exec-at-load and context-injection grants come from there.
- **Design docs and case reports.** They quote attacks in order to describe them. Stage 6 reads
  most of those lines correctly as descriptions or quotes.

This is a known limit, and the reason for this example. Walkdown has no notion of test data, so
any security tool that ships attack samples will read as hostile. The report still shows you
where everything is, and section 6 separates the quotes from the instructions.
