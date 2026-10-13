# How accurate the model reads are

Stage 6 is optional and experimental. It asks a model the questions a pattern cannot settle,
and the report shows those answers in their own block, labeled as model reads. A model's
reading never changes a finding in stages 1 to 5. This page gives the measurements behind how
the report uses the answers: what was measured, on what, and how far to trust it. Figures as of
2026-10-12.

- What stage 6 does, and the bands the report uses: [HOW-IT-WORKS.md](HOW-IT-WORKS.md), stage 6
- Where model reads appear in the report: [READING-THE-REPORT.md](READING-THE-REPORT.md)

## What it was measured on

| Set | Lines | Where | Labeled by |
|---|---|---|---|
| real lines | 119 | every line stage 6 asked about in three audited repositories, as five-line excerpts in `Fixtures/06-soft/real-lines/` | one labeler, with judgment calls marked; a second labeler checked 38 of them |
| look-alike pairs | 14 | written for the test, in `Fixtures/06-soft/labels-repo/` | the same labeler |
| sweep passages | 32 | 12 paraphrased payloads and 20 benign passages, in `Fixtures/06-soft/sweep-repo/` | written by the author of the sweep question |

The labels sit with the grader (`Fixtures/ANSWERS/06-soft.json`), so a backend never sees them.
The 14-line synthetic set scored 100% and the real lines 44%: measure on real text.

## Labeling: is this an instruction to do the flagged thing?

The labeler (Jev, by default) reads each line a pattern matched in text a model sees and picks
one of five labels: an instruction to do it, an instruction not to, a description, an example
or quote, or the words used in another sense.

**Overall it is a weak classifier.** Five-way agreement with the hand labels: 52 of 119 (44%);
on a held-out half, 28 of 59 (47%). It does worst on words used in another sense ("start over"
meaning rewrite the code): 9 of 39.

**Confident answers are much better, and the report uses only those.**

| Jev confidence | Answers right |
|---|---|
| 0.8 or more | 11 of 12 |
| 0.6 to 0.8 | 13 of 25 |
| below 0.6 | 28 of 82 |

The summary lists a line as a real instruction only at p >= 0.9, and calls 0.7 to 0.9 "near
the line". On the real lines, every "do" read at 0.8 or more was right: 9 of 9.

**Repeat reads drift.** The same line read twice moves by a median of 0.02, 95% of the time
by 0.09 or less, at most 0.14; between 6% and 10% of labels change between two runs. That is
why the report uses a band around its cutoff instead of a single line.

**Claude as a labeler** (optional, `--label claude-cli`): 42% five-way, about the same as Jev,
at about 65 times the cost. Its self-reported confidence is not calibrated: answers it rated
0.9 or more were right 12 times in 27. Jev stays the default labeler.

| Labeler | "do" precision | "do" recall | F1 | confident "do" reads right |
|---|---|---|---|---|
| Jev | 54% | 58% | 0.56 | 9 of 9 at p >= 0.8 |
| Claude | 52% | 35% | 0.42 | 1 of 1 at self-reported >= 0.9 |

## A line read as not an instruction

When stage 5 cites a line as evidence and the labeler reads it confidently as something other
than an instruction (any other label at p >= 0.8), the full report marks that evidence. The
mark never removes the evidence or unchecks a leg.

| Read | Truly not an instruction |
|---|---|
| another label at p >= 0.8 | 7 of 7 (and 9 of 9 on a second run) |
| another label at p >= 0.6 | 20 of 23 |
| p(do) of 0.1 or less, any label | 21 of 26 |

A low p(do) on its own is no evidence: 5 real instructions scored 0.1 or less.

## The coverage sweep

The optional sweep (`--sweep jev`) reads prose no pattern matched and flags passages a model
reads as telling it to do something risky. The bar (0.5) was fixed before the fixtures were
written.

| Flag above | Payloads caught | Benign passages flagged |
|---|---|---|
| 0.3 | 11 of 12 | 1 of 20 |
| 0.5 (the bar) | 11 of 12 | 0 of 20 |
| 0.9 | 10 of 12 | 0 of 20 |

The same person wrote the question and the fixtures, so this is a first check; a set written
by someone else is still owed. On four real repositories it flagged 11 of 1,147 passages (1%),
5 of them with no pattern hit; two of the 11 were misreads, both under 0.75. Repeat sweeps move
a passage by a median of 0.00, at most 0.10, so the report lists 0.6 and above and calls 0.4 to
0.6 near the line.

## The labels are the ceiling

Two different models, each with two wordings of the question, score between 38% and 48%, and on
26 of the 119 lines the two models agree with each other against the hand label. A second
person labeled 38 of the lines blind (34 compared): five-way agreement with the first labeler was 32% (kappa
0.04), and on the one bit the report uses (an instruction to do it, or not) 68% (kappa 0.34).
Most of the split was over what "do" means: any instruction, or an instruction to do the
flagged action. So the five-way figure measures how reproducible the labels are as much as how
good a model is. The question is being rebuilt to name the action ("Does this line tell the AI
to send data out?").

## Relational reads

Claude also answers questions about a finding's context (a safety word's definition, a hook
that runs a script, the capability legs). Those answers are prose and carry no score. Seen so
far: told that pattern evidence can be wrong, it questions weak citations instead of building
on them; it connected a credential chain the patterns had only located; about $0.03 a question.
Since 2026-10-12 it runs with no settings, hooks, or project files loaded (`--safe-mode`).

## Limits

- Three repositories supplied the real lines; another skill author's style may score differently.
- One primary labeler; the second labeling covers 38 lines.
- Jev is a remote service and its answers vary between runs.
- Laya (a local CPU model) was measured at 13% and retired.
