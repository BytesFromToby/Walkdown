# Stage 6 discussion, 2026-09-30

Owner and orchestrator session. Stage 6 had just had its first real measurements
(`EVAL.md`): labeling near 45% for every model, relational reads useful.

## 1. What stage 6 is for (as it stood)

Stages 1 to 5 **locate**; they cannot settle what a line means ("detection never
concludes", METHOD). Stage 6 reads meaning, under fixed rules: no verdict; never
changes a stage 1 to 5 finding; a review packet is always written; the model holds
no tools and treats the artifact as data.

Two jobs (METHOD):

- **Labeling**: sort pattern hits, real form versus house-word noise. Cheap,
  many lines.
- **Relational reads**: questions that need reasoning (a surprising
  redefinition, what hook-emitted text leads a model to do, how capabilities
  combine, a language-shifted passage).

As built: a labeling question per instruction-text line with a stage 4 hit (five
labels: do, not-to, description, example-or-quote, other-sense); relational
questions from fixed templates; backends chosen at run time (Jev, Laya, Claude
CLI); the report lists relational reads and high-confidence `do` reads.

What the measurements say: relational reads work (they connected a credential
chain the patterns had only located; they critique weak evidence once told the evidence can be wrong); five-way
labeling does not (about 45% whatever the model or wording, models disagree with
each other half the time); Jev's high-confidence `do` reads were 9/9 correct;
`other-sense` is the dominant noise; Laya does not work here.

## 2. Where the design was shaky (orchestrator)

1. The labeling taxonomy is richer than its consumer: the report uses one bit.
2. Labeling is per line; the real risk is flows (what moves where), which is the
   relational side.
3. Relational reads inherit stage 5's evidence noise (test files, pattern false
   positives).
4. Relational reads are unmeasured: no fixture, no ground truth.
5. The reviewing model is an attack surface (RED-TEAM §8) never tested with a
   hostile fixture.
6. One labeler behind every number.

## 3. Owner's ideas, pushback, alternatives

**Premise: it is easier to find potential issues in smaller chunks than in big
ones.** True for what a model reads, with a limit: too big dilutes a single bad
sentence; too small loses context; some attacks span chunks (RED-TEAM §3, split
definitions across files) and no chunk contains them.

### Idea 1: keyword plus about 100 characters each side, classified for a "suspiciousness index"

- Mostly already how it works: stage 4 is the keyword search, stage 6's state is
  the line plus two lines each side.
- **What it improves:** a fixed character window centered on the match is more
  uniform than a markdown line (a line can be a 2,000-character paragraph or
  four words), and fits Laya's 512-token cap.
- **Gap it exposed:** the model is never told *which words* matched. It gets the
  pattern's description and the whole line, and has to guess that "Start over" is
  the flagged phrase. Plausibly a main cause of the `other-sense` failures.
  → **D4: center the window on the match and mark the span**
  (`...Delete it. «Start over».`).
- **Pushback on the index:** a per-hit number framed as "suspiciousness" is a
  verdict per hit, asks about intent (the project reports capability), and is
  weakest on adversarial text, which is written to read innocent (JudgingJev: Jev
  "reads the claim, not the truth").
- **Alternative:** ask factual questions answerable from the text: "does «start
  over» here refer to discarding the model's instructions?", "is the reader told
  to do it?". That is the one bit the report uses, and it is measurable on the
  119 real lines.

### Idea 2: break files into chunks (sections, paragraphs, line breaks, character caps) and examine each

- Does not improve the existing labeling (for judging a specific hit, a window
  around it beats the section it sits in).
- **Valuable for a different target: coverage.** Stage 6 today only asks about
  lines stage 4 already hit, and stage 4 only knows known phrasings; the strongest
  attacks never use the loud words (RED-TEAM). A chunk sweep with capability
  questions per section ("does this tell the reader to send data somewhere / run a
  command / change settings or config / claim authority over other instructions?")
  reaches text with no keyword.
- Shape: chunk by heading, paragraph, list item, with a character cap and small
  overlap; a cheap Jev sweep of several yes/no questions per chunk in one call;
  flagged chunks go to Claude or a person, who quotes the sentence; output is a
  location. Validation: fixtures of paraphrased payloads stage 4 misses, and the
  benign rate on the three audited repos.
- **Method change to decide:** METHOD says "scripts detect, a model reads". A
  chunk sweep makes a model a detector. Justified with its own validation and never
  replacing stage 4 → **D2**.

### Scores (owner)

Owner: "no score" may be limiting. The rule was meant against an **overall**
score; a phrase like "override previous instructions" can be a high-level threat.

Orchestrator: agree that a per-finding level differs from an overall score and
can be defensible. Avoid levels by how alarming a phrase *sounds* (loud phrases are
what the strongest attacks avoid). Defensible version: **signal levels from
measured base rates**. A pattern with zero hits across the clean audited repos
(`L.ignore`, `L.guardrail`, `E.redirect-var`) is high-signal; one with 139 benign
hits is low-signal. The level is a published fact about the pattern, recomputed as
the corpus grows, not a judgment of the artifact. It is already the unnamed rule
behind the summary's points of attention (`POINT_PATTERNS`). → **D1**, needs
CHARTER wording: "no overall score; per-finding signal levels from measured base
rates are allowed and always shown with their base rate".

## 4. Proposed order

1. D4: marked-span windows, measured on the 119 lines as the binary question.
2. D2: chunk sweep as a coverage tool, fixtures first (paraphrased payloads with
   no keywords).
3. Relational reads unchanged (working); later: a small relational fixture set so
   they are measured too, and a hostile fixture aimed at the reviewer (RED-TEAM §8).

## 5. Also raised: the summary page

Owner: `report/summary.md` is hard to read for a summary: busy, too technical.
Make it HTML and more beautiful. **Done the same day:** `report/summary.html`
(stage 8 `summary_html.py`), plus `run.py --rerender` to rebuild reports without
re-running stages. Lesson from building it: plain-language headlines make pattern
false positives sound like facts, so stage 4 headlines say what matched ("Matches
the wording of an instruction override"), never what the text does.
