# Walkdown — charter

An ICM-based evaluator of skills and skill repositories: what the instruction
layer asks a model to do, and what installing it grants.

## What it evaluates

The **instruction layer** — SKILL.md files, reference docs, hooks, manifests, and
the prose that gets loaded into a model's context and executed with the user's
own permissions. Existing security tooling cannot see this layer, because the
payload is English, not code.

Two questions, both answered from the artifact itself:

1. What does this text ask the model to do?
2. What does installing it grant — execution, injection, network, persistence?

## Scope — this iteration audits English-language skills

The detectors, the phrase register, and the reader are built for **English**
instruction text. A skill written in another language is out of scope for this
iteration: the phrase layer (including the takeover list) goes blind on it, and a
clean result on a non-English skill means nothing. Every report states the
language it was equipped to read.

This makes **language / script shift its own signal**: an English skill that
switches to another language or script for a passage is a place an
English-reading reviewer skims and the model reads in full. We flag the shift
(hard: script/language detection) and read the shifted passage for instructions
(soft), while being honest that a wholly non-English skill is beyond this
iteration. Multi-language support is a later iteration, not a patch.

## A sharpening: capability, not intent

"Malicious intent" is the thing that cannot be observed from a repository.
What *can* be observed is what the text asks for and what installation grants.
Report those; let the reader judge intent.

This is not pedantry. It is what keeps the work defensible, keeps it honest, and
keeps it useful against an author who is merely careless rather than hostile —
which will be the far more common case.

## What it is NOT

- **Not a judgment on code security.** No CVEs, no dependency scanning, no
  vulnerability classes. Other tools do that, and they do it better.
- **Not a judgment on how well the repo works.** Nothing about quality,
  craftsmanship, or whether the skill achieves its stated goal.
- **Not a verdict on people.** It reports structure and base rates. It does not
  conclude that an author is malicious, and it never names one as such.
- **Not a linter for forceful language.** Intensity is not malice. The ecosystem's
  own best-practice guidance instructs authors to write "YOU MUST" and
  "no exceptions." A scanner that penalizes that is measuring style, not risk.
- **Not a behavioral test.** Nothing is executed. Static, instruction-layer only.
  It makes no claim about what a skill does when loaded.
- **Not automated judgment.** The tool surfaces and locates; a human decides.
  No aggregate score, no severity rating, no risk number. Two per-finding signals are allowed (owner,
  2026-10-01, soft D1), because they are measurements and not judgments: a
  pattern's **base rate** (how often it turns up in the other audited repos, binned
  as rare / uncommon / common and always shown with the count), and a soft read's
  **near-the-line band** (a model read close enough to the cutoff that its own
  run-to-run drift could flip it). Neither is summed, ranked, or combined into a
  verdict on the artifact.
- **Not a certification.** "Clean" means nothing was found by these passes. It
  does not mean safe, and every report says so.
- **Not exhaustive.** The passes catch known shapes. Novel phrasing of a hostile
  instruction gets through — which is the problem the project exists to work on,
  not a defect to hide.

## ICM commitments

- The rubric lives in a versioned markdown file, not in model weights.
- Findings cite file and line. Every claim is checkable against the artifact.
- The artifact examined is pinned by hash, so a result can be reproduced.
- A human reads before anything is published.
