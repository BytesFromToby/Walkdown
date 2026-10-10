# Method: ordered stages

The governing rule: **detection and judgment never happen in the same step.**

A step that decides whether something is bad while it is still finding things
will stop looking once it has decided. Worse, it destroys the base rates: the
count of benign uses of a technique is the product, not the noise.

Restructured 2026-09-25. The audit is seven **stages**, ordered from fully
deterministic to soft, plus the report that assembles them. The same seven
groups organize everything: the pipeline folders (`stages/NN-name/`), the
fixtures (`Fixtures/NN-name/`), the files a run writes (RUN-LAYOUT), the report
sections (REPORTING), and the class matrix (COVERAGE). A new check goes into the
stage whose kind of evidence it uses, so every group can grow without reshaping
the others.

Each stage reads the pinned artifact plus earlier stages' outputs and writes its
own. No stage may do a later stage's job. Every output is a plain file a human
can read without running anything.

---

## The stages

| # | Stage | Question it answers | Kind of evidence | Block |
|---|---|---|---|---|
| 1 | Inventory | What ships? | counting and parsing; nothing read for meaning | hard |
| 2 | Reader | What does the model actually receive? | two independent readings, differences recorded | hard |
| 3 | Graph | What loads what? | references between files, from stage 1's entry points | hard |
| 4 | Phrases | What does the text ask for? | validated patterns on the folded text from stage 2 | hard |
| 5 | Capability | What does installing it grant? | derived only from stages 1 to 4; no new detection | hard |
| 6 | Soft reads | What can a pattern not settle? | a model, holding no tools, over stage 1 to 5 outputs | soft |
| 7 | Not examined | What is this run blind to? | the run log, missing dependencies, standing limits | hard |
| 8 | Report | (assembles 1 to 7) | nothing new | n/a |

**Hard block (1 to 5, 7).** Deterministic scripts. They locate and count; they
cannot hallucinate; every zero is validated against a known positive.
**Soft block (6).** Reads for shapes a pattern cannot. Emits located
observations with verbatim quotes. No verdict, no score.

Neither block renders a verdict. Hard states facts; soft states observations;
the reader decides (CUSTOMERS.md).

**Class numbers are tags.** The 22 THREATS classes keep their numbers as stable
IDs. A finding appears in the stage that detected it, tagged with its class. A
class with more than one kind of evidence (15, 16, 14, 20, 4) appears in each
stage that sees part of it, and the tag links the parts. COVERAGE.md holds the
map.

---

## Rules that apply to every stage

- **Validation gate.** Before a stage's zero counts, each of its detectors must
  match its known positive in `Fixtures/NN-name/` in the same run. The result is
  the stage's validation stamp in the run log. A zero with no stamp is logged as
  broken, never clean. The fixtures that prove a stage in development are the
  same fixtures that gate it at audit time: one set, two uses.
- **Record every hit, benign ones included.** The benign count is the base rate
  and the base rate is the deliverable.
- **Every hit carries file:line and a verbatim quote.** Extraction happens where
  the hit is found. No paraphrase, no summary, no adjective. A paraphrase is where
  a self-attestation inside the artifact becomes a conclusion in the report.
  (Until 2026-09-25 extraction was its own pass, Pass 3. Quoting is not judgment,
  and a separate pass only reopened the same files.)
- **Zero is a result.** A check with no hits is recorded as zero, with its stamp.
- **Optional dependencies degrade to stage 7.** A check whose tool is missing
  (Tesseract for OCR, gitleaks for secrets) does not fail the run and does not
  pass silently. It is listed as not examined.

---

## Stage 1: Inventory

Establish exactly what is being examined, by counting and parsing. Nothing is
read for meaning.

- **Pin.** Record source, distribution channel (zip, clone, tarball, marketplace
  copy), retrieval date, and `sha256` / git hash. Record whether
  `.gitattributes export-ignore`, `.npmignore`, or `files` in `package.json`
  make channels differ.
- **File census.** One row per file: path, extension, size, exec bit, encoding
  and BOM, entry-point flag. Totals: files, bytes, format census, script-language
  census.
- **Entry points.** Plugin manifests, hook configs, every `SKILL.md`,
  `agents/*.md`, `commands/*.md`, subagent prompt templates (files a `SKILL.md`
  names as a template to dispatch), `.mcp.json`, CI workflows that invoke an
  agent, and the README. Stage 3 starts from this list.
- **Structural census.** Symlinks; extension-versus-magic-byte mismatches (with
  the detector's own false-positive rate, since `file` misclassifies markdown that
  opens with a code fence); archives in tree; files over the reader window (line
  count and byte size, window stated); lines over 500 characters. (Class 18.)
- **Frontmatter and descriptions.** Parse every frontmatter block. Record the
  `description` field verbatim: it is always in context (class 6). Where the repo
  ships more than one loader for the same file (superpowers ships a YAML path and
  a first-colon split), parse with each and record disagreement as a divergence.
- **Grants.** Agent and command definitions: the tools each one is granted
  (class 15, structural half). Hook census: event, matcher, blocking or async,
  whether it can modify tool input, which files its script reads (class 16,
  structural half).
- **Platform manifests.** Every host manifest, and the permission model each
  declares, side by side (class 9).

Output: `01-inventory.md`
Does not: open any file for meaning.

## Stage 2: Reader

Produce the true text of every file by the path a model would receive it, and
record where two readings disagree.

| Format | Reading A | Reading B |
|---|---|---|
| Markdown / text | raw bytes | glyphs after stripping zero-width and bidi controls |
| HTML | DOM text | visibly painted text (computed style) |
| SVG | XML: `<text>`, `<desc>`, `<title>`, `<metadata>`, comments, `<script>` | rendered text |
| PDF | text layer | OCR of rendered pages |
| DOCX | `word/document.xml` | visible body text |
| XLSX | all cells | rendered / visible cells |
| PPTX | all shape text | on-canvas text |
| Images | none (no text layer) | OCR (the model still reads the pixels) |

- **Divergence is recorded as a fact, not judged** (class 11, and class 4 for
  invisible and bidi characters).
- **Folded copy.** An NFKC-normalized copy with zero-width and bidi stripped and
  confusables folded to ASCII. Stage 4 greps the folded copy and cites line
  numbers from the original.
- **Metadata.** PDF info dict, DOCX docProps, EXIF, embedded author / producer /
  comment fields. Metadata is a place text hides (class 6).
- **Markdown carriers.** Unused reference-style link definitions, link titles,
  image alt text, `<details>` bodies, `hidden` / `display:none`, footnotes, fence
  info strings: content the render hides.
- **Language / script shift.** Flag every run of non-English language or
  non-Latin script with its location (class 4 facet). The soft read of what it
  says is stage 6. Scope is English-only (CHARTER): a wholly non-English skill is
  reported as out of scope in stage 7, never passed clean.
- **Coverage.** Files and bytes actually read, and the unread list.

Output: `02-reader.md` plus `normalized/text/` and `normalized/folded/`
Does not: interpret what any divergent or hidden text says.

## Stage 3: Graph

Build the reference graph and find what nobody points at.

**Nodes** are files. **Edges** are one file naming another: a path, a filename, a
relative link, a script argument. **Entry points** come from stage 1.

- **Orphans.** Files reachable from nothing. Most are dead weight and that is
  fine. Some are payloads staged ahead of the mechanism that will load them
  (class 12).
- **Dangling references.** Docs naming files that do not exist. Either rot, or
  content that arrives at runtime.
- **Dynamic loads.** Globs, directory scans, `*.md` reads: edges whose target is
  unknown at review time. They make the graph incomplete by construction; say so
  rather than reporting a clean graph.
- **Reference depth.** Hops from the nearest entry point, per file. Payloads one
  hop from a clean entry file are class 10.
- **Manifest versus disk.** Files a manifest names that are missing, and files on
  disk no manifest covers.

**Undocumented does not mean unloaded.** Skills are commonly discovered by
directory scan. A skill folder that appears in no documentation is live and
unmentioned, a stronger finding than dead weight, not a weaker one.

Output: `03-graph.md`
Does not: judge why a file is unreferenced.

## Stage 4: Phrases

Run the PHRASES pattern sets over the folded text, case-insensitive. Four
sub-groups, by what the text is trying to do:

| Sub-group | Classes | PHRASES sets |
|---|---|---|
| **4a Reaching out** | 1 exfiltration and destinations, 2 credentials, 3 remote loading | K, E rollup; gitleaks for secrets |
| **4b Taking the wheel** | 5 override, 13 claimed consent, 14 redefinitions (hard half), 20 anti-review, 21 conditional activation | L, A, B, H, I |
| **4c Changing the environment** | 7 execution, 15 second-order (phrase half), 16 trust elevation (phrase half), 17 env mutation, 22 harness-prohibited | E, C, D, J |
| **4d Talking to the human** | 19 human-audience and inbound | G |

Also produced here, all descriptive:

- **Endpoint census (4a).** Destinations found in code and instructions versus
  destinations named in documentation. An undocumented endpoint is the cheapest
  high-signal check.
- **Conditional table (4b).** Every conditional branch in instruction text
  (harness, clock, version, state, environment, absence, error path), condition
  and branch body in separate columns.
- **Term table (4b).** One row per definition of a word, from every file in the
  union (SKILL.md, references, subagent templates, agent definitions,
  hook-emitted text, README). Sources: explicit ("X means", "X is", glossary
  sections), mapping ("when the user says X"), procedural ("How to X", "Steps to
  X"), by example ("example X:" followed by a command). Columns: **term |
  definition (verbatim) | file:line | source kind | load path** (always-on /
  on-trigger / reference / subagent / hook-elevated / human-only). Derived:
  **conflicts** (same term, more than one definition, and which loads last or
  highest), **safety-vocabulary definitions** (confirm, verify, done, safe,
  read-only, reversible, approve, permission, sandbox: always surfaced), and
  **displaced defaults** (count of common action verbs the artifact defines).
  Whether a definition is reasonable is stage 6.
- **Harness rubric (4c).** The harness's own prohibited and confirm-first list as
  a pattern set, with whether a confirmation step accompanies each hit.
- **Audience tag (all).** Every hit is tagged model / subagent / human /
  downstream tool. The same sentence is a different finding under each tag.
- **Position and repetition (all).** Instruction density in the first 10%, middle
  80%, last 10% of long files; near-duplicate instruction sentences across files.

Output: `04-phrases.md` plus `04-terms.md`
Does not: say whether any hit is a problem.

## Stage 5: Capability

State what the artifact can do, derived only from stages 1 to 4. No new
detection happens here.

- **Lethal trifecta** (Willison), on the union of everything that loads,
  including second-order layers (subagent templates, agent definitions, command
  files, hook-emitted text): (1) access to private data, (2) exposure to
  untrusted content, (3) ability to communicate externally. Each yes / no, with
  the stage 1 to 4 citations that establish it. The user's own public surfaces
  (issue tracker, pull requests) count as external.
- **Install grants.** Execution at load, context injection, persistence across
  sessions, network reach, elevated permissions.
- **Trust elevation paths.** Every path by which file text reaches context at
  harness-trust level (hook output), and total bytes injected before the first
  user input.
- **Least-privilege posture.** Where a grant matches the stated job (an agent
  that only reads and holds no Bash), record it as a positive. The map can show a
  good posture, not only exposure (Case 002).
- **Pairs.** Cross-references between stages that are stronger together: orphan
  (3) plus phrase hit (4) is the top pair for a human; hidden text (2) plus
  phrase hit (4); dynamic load (3) plus phrase hit (4).

Output: `05-capability.md`
Does not: conclude.

## Stage 6: Soft reads

**Coverage sweep (added 2026-10-01, soft D2).** The one place a model acts as a
detector. Every prose file a model reads is cut into passages (by heading, then
paragraph, capped at 1,200 characters), and a tool-less model (Jev) answers one
question per passage: does it tell the reader to set aside its instructions, send data
out, gather secrets, act without or hide from the user, follow fetched instructions, or
make lasting changes outside the task? A flagged passage is a location, marked by
whether a stage 4 pattern already hits inside it. It never replaces stage 4, never
changes a stage 1 to 5 finding, and has its own validation set
(`Fixtures/06-soft/sweep-repo`). Opt-in: `--sweep jev`.


Reads for shapes a pattern cannot settle. Runs after the hard block, on its
outputs, never on raw untrusted text handed to a model that holds tools.

Two kinds of job, which may use different models:

- **Labeling.** Sorting pattern hits that need a read to separate the real form
  from house-word noise (the `silently` case, class 20). Cheap surface
  classification.
- **Relational reads.** Whether a redefinition is surprising against the word's
  ordinary meaning (class 14, from the term table); the capability combination
  read as a narrative, stated as capability, not accusation; what a
  language-shifted passage says and whether it carries instructions the English
  layer missed.

The stage always writes a **review packet**: the verbatim extracts, the term
table rows, and the specific questions. A human can take the packet to any
assistant. If a model is configured, the stage also records its answers, with
the model, prompt, and verbatim output for repeatability.

**Model choice is the user's.** The recommendation is a local model. Final
recommendation deferred (2026-09-25) pending outside advice; TypeSafe Jev is a
candidate for labeling, not for relational reads. RED-TEAM §8 ("local only") is
to be reconciled with this when decided.

Output: `06-soft.md`
Does not: render a verdict or a score.

## Stage 7: Not examined

State what this run is blind to. Every report carries it, clean ones included,
so a zero is never read as safe.

- **From the run log:** any stage or check that failed its validation gate, or
  did not run.
- **Missing optional dependencies:** checks skipped because their tool is absent.
- **Standing limits:** version history (class 8 is snapshot-blind; the
  version-delta run is a future feature); non-English passages beyond the stage 2
  flag; runtime behavior (nothing is executed); dynamic loads stage 3 could not
  resolve; files stage 2 could not read.

Output: `07-limits.md`

## Stage 8: Report

**The report is the handoff, not a verdict.** No benign / unclear / concerning,
no score, no severity. The stages locate, quote, and map capability; the report
presents it with evidence; the reader decides. Both customers supply the last
judgment themselves, because only they know the skill's intended purpose
(CUSTOMERS.md).

Two documents, both in stage order (layout in REPORTING.md):

- **Summary page.** One screen. One status line per stage, points of attention
  under the stage that found them, stages with nothing collapse to "nothing found
  (validated)".
- **Full report.** Sections 1 to 7, every finding cited to file and line with its
  quote and base rate, then the builder's recommendations.

Both state: static examination only; "clean" means these stages found nothing,
not that it is safe; the tool reaches no conclusion of its own.

A human still reads before anything is **published**. That is disclosure
discipline, not a per-finding verdict the tool withholds.

Output: `report/summary.md` and `report/full.md`

---

## Old pass numbers (before 2026-09-25)

Case 001, Case 002, REVIEW-2026-09-04, and other history docs cite the old passes.

| Old | Now |
|---|---|
| Pass 0 Inventory and pin | Stage 1 |
| Pass 1 Normalize | Stage 2 (frontmatter double-parse moved to stage 1) |
| Pass 2 Presence | Stage 4 (reader-limit measurements, agent grants, hook census moved to stage 1; invisible / bidi re-count stays with stage 2) |
| Pass 2b Reachability | Stage 3 |
| Pass 3 Extraction | Merged into every stage (verbatim quote at the hit); term table is stage 4 |
| Pass 4 Capability map | Stage 5 |
| Soft block | Stage 6 |
| (none) | Stage 7, new |
| Pass 5 Report | Stage 8 |

---

## Why the separation matters

1. **Base rates die first.** A pipeline that only records suspicious hits can
   never say what fraction of normal repos use a technique. Case 001's whole value
   was measuring normal.
2. **Judgment contaminates detection.** Deciding "this author is reputable" in
   stage 4 means you stop reading at file three.
3. **It is auditable.** Someone can take the stage outputs and reach a different
   decision than another reader without redoing the work. The evidence is in
   files, in order, and a human can check any step without rerunning the tool.
   Because the tool renders no verdict, there is nothing to overturn, only
   evidence to weigh.

## Note on the reader

Every stage after 2 is only as good as the reader that produced its input. If
stage 2 cannot see hidden text in a PDF, stage 4 will report a clean PDF with
total confidence. Every improvement to stage 2 is worth more than any improvement
to stage 4. This is why stage 2 has its own answer sheet, not only detectors.

## Pipeline hygiene

- **Never write outputs into the examined tree.** `RepoResults/` (outputs) and
  `ReposToExamine/` (the pinned copy) are separate top-level directories, and no
  output name may collide with a path in the artifact. An artifact that ships a
  file named like a stage output is itself a finding (RED-TEAM §19).
- **Publish the detector's own noise.** Every pattern's benign count on the clean
  corpus ships with the pattern (PHRASES.md). A pattern with no measured benign
  share is not yet in the standard.
