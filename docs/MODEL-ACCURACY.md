# How accurate the model reads are

The model reads are optional and experimental. This version has two: the coverage sweep
(`--sweep jev`, or `--sweep claude-cli[:model]`), which asks a model about prose no pattern matched, and the pinpoint
(`--pinpoint claude-cli`), which asks a second model for the line behind a sweep flag. (`--reads` chooses both without naming a
backend, so nothing here changes with it: the measurements are of the reads it resolves to.) The report
shows their answers in their own block, labeled as model reads. A model's reading never changes a
coded finding. This page gives the measurements behind how the report uses the answers: what was
measured, on what, and how far to trust it. Figures as of 2026-10-12; nothing has been measured
since.

- What the reads do, and the bands the report uses: [HOW-IT-WORKS.md](HOW-IT-WORKS.md), "Needs a
  human read" and "The line behind each flag"
- Where model reads appear in the report: [READING-THE-REPORT.md](READING-THE-REPORT.md)

## What is measured now

| Set | Passages | Where | Written by |
|---|---|---|---|
| sweep passages | 32 | 12 paraphrased payloads and 20 benign passages, in `Fixtures/03-sweep/sweep-repo/` | the author of the sweep question |
| four audited repositories | 1,147 | every prose passage a model reads in four repositories | not labeled: a check of how often the sweep flags |

The answers for the sweep fixture sit with the grader, so a backend never sees them. The pinpoint
read has no fixture set and has not been measured; its one check is that the line it quotes is found
word for word in the passage, and an answer whose quote is not found is not shown.

## The coverage sweep

The sweep reads prose no pattern matched and flags passages a model reads as telling it to do
something risky. The bar (0.5) was fixed before the fixtures were written.

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

A flag is a place to read, and a passage with no flag is not cleared: a model's miss is not safety.

## Limits

- One set, written by the author of the question; a second is owed.
- Four repositories supplied the real passages; another skill author's style may score differently.
- Jev is a remote service and its answers vary between runs.
- The Claude Code command can read the sweep too (`--sweep claude-cli[:model]`). It gives a name and no probability, so it has no
  bands; it has not been measured here beyond the fixtures, which the brief reports (`Sweep on claude-cli: found N of M in its
  fixtures.`). The fixtures now hold 34 rows: the 32 of the first check, and two passages that speak to the model reading
  them (one tells it to answer `none`, one tells it to use a tool).
- No model is asked how sure it is: Claude rated itself 0.9 or more 27 times and was right 12.
- The pinpoint read is not measured.

## Parked: labeling and the other reads of earlier versions

Before 0.4.0 the model reads also included a labeler (is this flagged line an instruction to do the
matched thing, an instruction not to, a description, an example or quote, or the words used in
another sense), a second labeler for agreement, and relational reads in prose. They are not in this
version and Walkdown refuses their options. They are kept here because the measurements are why the
labeling is being rebuilt, around a question that names the action ("Does this line tell the AI to
send data out?"). The measured sets, with their answers, are parked under `tools/model-eval/` for
that work: the real lines in `tools/model-eval/real-lines/` and the look-alike pairs in
`tools/model-eval/labels-repo/`.

| Set | Lines | Labeled by |
|---|---|---|
| real lines | 119 | one labeler, with judgment calls marked; a second labeler checked 38 of them. Every line the labeler was asked about in three audited repositories, as five-line excerpts |
| look-alike pairs | 14 | the same labeler; written for the test |

The 14-line synthetic set scored 100% and the real lines 44%: measure on real text.

**Overall the labeler was a weak classifier.** Five-way agreement with the hand labels was 52 of
119 (44%); on a held-out half, 28 of 59 (47%). It did worst on words used in another sense ("start
over" meaning rewrite the code): 9 of 39.

**Confident answers were much better.**

| Jev confidence | Answers right |
|---|---|
| 0.8 or more | 11 of 12 |
| 0.6 to 0.8 | 13 of 25 |
| below 0.6 | 28 of 82 |

Every "do" read at 0.8 or more was right: 9 of 9. A "do" read said the line tells the AI to do the
flagged thing; it did not say the thing is harmful.

**Repeat reads drifted.** The same line read twice moved by a median of 0.02, 95% of the time by
0.09 or less, at most 0.14; between 6% and 10% of labels changed between two runs.

**Claude as a labeler**, once: 42% five-way, about the same as Jev, at about 65 times the cost. Its
self-reported confidence was not calibrated: answers it rated 0.9 or more were right 12 times in 27.

| Labeler | "do" precision | "do" recall | F1 | confident "do" reads right |
|---|---|---|---|---|
| Jev | 54% | 58% | 0.56 | 9 of 9 at p >= 0.8 |
| Claude | 52% | 35% | 0.42 | 1 of 1 at self-reported >= 0.9 |

**A line read as not an instruction.**

| Read | Truly not an instruction |
|---|---|
| another label at p >= 0.8 | 7 of 7 (and 9 of 9 on a second run) |
| another label at p >= 0.6 | 20 of 23 |
| p(do) of 0.1 or less, any label | 21 of 26 |

A low p(do) on its own is no evidence: 5 real instructions scored 0.1 or less.

**The labels were the ceiling.** Two different models, each with two wordings of the question, scored
between 38% and 48%, and on 26 of the 119 lines the two models agreed with each other against the hand
label. A second person labeled 38 of the lines blind (34 compared): five-way agreement with the first
labeler was 32% (kappa 0.04), and on the one bit the report used (an instruction to do it, or not) 68%
(kappa 0.34). Most of the split was over what "do" means: any instruction, or an instruction to do the
flagged action. So the five-way figure measured how reproducible the labels were as much as how good a
model was.

**Relational reads.** Claude also answered questions about a finding's context (a safety word's
definition, a hook that runs a script, the capability legs). Those answers were prose and carried no
score. Seen: told that pattern evidence can be wrong, it questioned weak citations instead of building
on them; it connected a credential chain the patterns had only located; about $0.03 a question. They
ran with no settings, hooks, or project files loaded.

**Laya**, a local CPU model, was measured at 13% and retired (2026-10-03).
