# Reading a Walkdown report

A run produces three reports, at the top of its run folder
(`RepoResults/<name>/<date>_<hash7>/`):

| File | For | What it holds |
|---|---|---|
| `summary.html` | most readers | what to look at first, the trifecta checklist, one plain sentence per stage |
| `summary.md` | the same, as text | one status line per stage and up to five points under each |
| `full.md` | checking a point | every finding, by stage, with file and line |

Start with `summary.html`. Go to `full.md` for the evidence behind a point. `LOG.md`, next to
them, says whether each stage passed its validation; the data the reports were built from is in
`data/` ([RUN-FOLDER.md](RUN-FOLDER.md)). What each check means, and why it exists, is in
[HOW-IT-WORKS.md](HOW-IT-WORKS.md).

## Three rules behind every page

1. **Every finding is a location.** It says "this text, at this file and line, matches this
   shape". It does not say the author meant harm.
2. **No score.** Nothing is added up into a rating. Counts come with what they were counted over.
3. **Clean means not found.** An empty section means these stages found nothing there. Check
   section 7 before trusting a zero.

## A suggested reading order

1. **LOG.md, the Validation column.** Every stage should say PASS. INCOMPLETE means a check was
   skipped (usually an optional tool not installed); FAIL means do not trust that stage's
   findings in this run.
2. **The trifecta checklist** at the top of `summary.html`: what the repository can do.
3. **Look at these first**: the short list of points.
4. **Section 7, Not examined**: what the run could not see.
5. **`full.md`** for any point you want to check.

## summary.html

### Header and tiles

The header names the repository, where the copy came from, and the version it was pinned to.
The tiles count files examined, things to look at first, and things not examined.

### What it can do: the trifecta checklist

Three boxes, one per leg of the lethal trifecta
([Simon Willison's term](https://simonw.substack.com/p/the-lethal-trifecta-for-ai-agents)):

| Leg | Checked when the repository... |
|---|---|
| **Reads your data** | reads the user's data wherever it lives: files, secrets, settings, connected accounts |
| **Takes outside input** | brings in text the user didn't write: the web, other people's issues or email, MCP tools, third-party code |
| **Sends data out** | moves data off the machine or into shared places: web requests, webhooks, pushes, posts |

A box is checked when at least one piece of evidence supports it, and the evidence is listed in
`full.md` section 5. **Three checked boxes are common in well-built repositories**: an agent
that reads files, uses the web, and pushes commits has all three. The combination raises risk.
It is not an issue on its own.

Under the boxes: the install grants (runs at load, injects context, persists, uses the network,
elevated permissions), explained in [HOW-IT-WORKS.md](HOW-IT-WORKS.md#install-grants-capgrant).

If stage 6 read every line cited for a leg as not an instruction (a quote, a description), a note
says so under the box. The box stays checked: a model's read never removes a finding.

### Look at these first

Cards in stage order: a stage tag, a headline, the places it applies to, the quoted text, and
sometimes a note. Places with the same headline share one card.

| Headline | Stage | What it means |
|---|---|---|
| Runs commands on its own | 1 | a hook that runs whenever the host fires its event, without anyone asking |
| Hidden when rendered, and reads like an instruction | 2 | text the model receives that a person viewing the file does not see, which also matches a phrase pattern |
| Nothing refers to this file / Loaded only by a folder or glob, named by nothing, and it reads like an instruction | 3 | a file a reviewer following references would not open, which also matches a phrase pattern |
| Matches the wording of ... | 4 | the text matches a phrase pattern; the quote lets you judge, and the note gives the pattern's base rate |
| A word is defined more than one way / Redefines a safety word / An irreversible or prohibited action with no confirmation step | 4 | from stage 4's tables of definitions and guarded actions |
| Test data that the model is pointed at | 5 | a file in a test or fixture folder that a model-read file references directly, so it is read like any other file |
| An instruction the model sees before you type anything | 5 | text a context-injecting hook prints into the session |
| No pattern matched, but a model read this as an instruction | 6 (model reads block) | the coverage sweep flagged a passage stage 4 had no hit in |
| Read as a real instruction to do the flagged thing | 6 | a model's confident reading of a flagged line |
| Near the line | 6 | a model reading close enough to the cutoff that a repeat read could flip it |

**Base rates.** A stage 4 card's note says how often its pattern turns up in the other audited
repositories: **rare** (none of them), **uncommon** (one), **common** (two or more). A rare
pattern is more worth reading. The level describes the pattern across repositories; it says
nothing about this one.

**What is kept off this list.** Hits in human-facing files (README, docs, changelog) and in test
data (tests, fixtures) are counted, never listed: installing the artifact does not put them in
front of a model. They are all in `full.md`.

### Model reads (experimental)

When stage 6 ran with a model, its cards follow "Look at these first" in their own block: sweep
passages no pattern matched, confident "do" reads, and reads near the line. A model's reading
can be wrong and repeat reads vary, so these are kept apart from the findings the fixed rules
produced, and they never change them. The tile counts only the rule-based places and says how
many model reads follow.

### Stage by stage

One plain sentence per stage, with a pill when the stage did not pass validation. "Technical
detail" opens the status line from `summary.md`.

### Recommendations

Suggestions for the builder, each tied to a file and line, each conditional ("if this skill does
not need X, ..."), each naming a narrower way to do the same thing. Listed in stage order and
never ranked: ranking by importance would be a score by another name.

## Section 4's numbers

The status line says how many lines have hits and where they are: read by a model, in scripts,
human-facing, test data. On superpowers, 109 of 626 such lines are text a model reads. When
stage 6 labels ran, it also gives the **benign share**: of the labeled lines a model reads, how
many the model read as an instruction to do the matched action and how many as a description,
quote, or other use. That is a model's reading, with measured accuracy; without labels the line
says the share was not measured.

## summary.md

The same content as text. Each stage has one **status line** (counts, with what they were
counted over) and up to five **points** under it. Lines such as "+4 more in the full report" or
"3 more hits on these patterns in test data" say what was left off and where it is.

## full.md

Every finding, grouped by stage:

| Section | Holds |
|---|---|
| 1 What ships | entry points, the structural census, descriptions, tool grants, hooks, manifests |
| 2 What the model actually reads | divergences (raw against rendered), lines changed by folding, non-Latin runs, metadata, unread files |
| 3 What loads what | entry points used, orphans, load-only files, dynamic loads, dangling references, depth |
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
  lines in or out of the summary by chance.
- **Evidence marks:** a confident read that a line is not an instruction marks it where stage 5
  cites it as evidence, and never removes it.

Accuracy is measured in `pre-planning/soft/EVAL.md`.

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
