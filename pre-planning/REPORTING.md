# Reporting standard

Living document. Metrics get added as runs reveal what is worth counting.

Restructured 2026-09-25: the report follows the seven stages (METHOD.md), in
order, deterministic to soft. The summary page, the full report's sections, and
the metric numbers in Part B all use the stage numbers, so metric 4.2 is found in
section 4 of every report and is produced by stage 4. A new metric goes into the
section of the stage that produces it. An old-to-new number map is at the end.

---

## Principles

**The data is the product. The numbers are an index to it.**

Everyone wants a figure they can quote. A single figure is how a locator becomes
a verdict, and that failure is the one this project exists to name. So:

1. **No aggregate score.** No risk rating, no severity number, no letter grade.
   There is no arithmetic that turns twelve locators into one verdict. Per-finding
   base rates and the stage 6 near-the-line band are allowed (CHARTER, 2026-10-01):
   each is shown with its measurement and never summed or ranked.
2. **Every count carries its denominator and its benign share.** Not "71
   hidden-text hits." Rather "32 HTML comments hidden in 94 markdown files, 32 benign."
   A count without its benign share is a scare number.
3. **Every count is traceable.** Any number in a report resolves to a list of
   file:line the reader can open. If it cannot, it does not go in.
4. **Negative results are reported.** Zero is a measurement. A check with no hits
   is stated, not omitted. Absence is most of what a base rate is made of.
5. **Report what was not examined.** Coverage is part of the result. Section 7
   is in every report, clean ones included.
6. **No zero without validation.** No zero is reported for a detector that has
   not matched its known positive in the same run. The validation fixture is
   inert, local, and marked. A published zero from a broken detector is worse than
   no number. A detector that failed validation is reported in section 7, not as
   a zero. (Validation proves the pattern fires. It says nothing about recall.)

---

# Part A: Report layout

Two documents from one run, for two depths of reader, both in stage order.

**Written for the builder** (CUSTOMERS.md, 2026-09-24): the primary reader wrote
the skill and can fix it. An adopter reads the same two documents, but nothing in
them is shaped to answer "should I install this?" The report never says "this is
bad."

The **summary page** is what a reader sees first and what most readers will only
read. Legible to a non-specialist. It carries the numbers, points at what a human
should look at, and does not teach or conclude.

The **full report** carries every finding and its evidence in sections 1 to 7,
cited to file and line, with base rates, and ends with the builder's
**recommendations**.

Interpretation guidance (why a metric matters, what it does not mean) lives in
Part B. It is written once for the analyst, not repeated in every report.

## Section names

Each stage has a plain-language heading for readers, used in both documents:

| Stage | Heading in the report |
|---|---|
| 1 Inventory | **What ships** |
| 2 Reader | **What the model actually reads** |
| 3 Graph | **What loads what** |
| 4 Phrases | **What the text asks for** (4a Reaching out, 4b Taking the wheel, 4c Changing the environment, 4d Talking to the human) |
| 5 Capability | **What this touches** |
| 6 Soft reads | **Needs a human read** |
| 7 Not examined | **Not examined** |

## The summary page

One screen. If it does not fit on one screen it is not a summary.

```
# <artifact> <version>

Source | retrieved <date> | <hash>
Static examination only. Nothing executed.

1 What ships               <files>, <formats>, <script languages>. <hooks>, <agent defs>, <manifests>.
  - <point of attention, file:line>
2 What the model reads     <read>/<total> files (<pct>%). <divergences>.
  - <point of attention, file:line>
3 What loads what          <orphans>, <dangling>, <dynamic loads>.
4 What the text asks for   4a <n> · 4b <n> · 4c <n> · 4d <n> hits, <benign> benign.
  - <point of attention, file:line>
5 What this touches        Private data: yes/no · Untrusted content: yes/no · External: yes/no
                           <When all three: "All three legs of the lethal trifecta.
                           That raises risk. It is not an issue on its own.">
6 Needs a human read       <n> questions in the review packet. <Model: name / not run>.
7 Not examined             <one line: the biggest gaps>

Recommendations: <n>, in the full report. Unranked.

What this is not: static examination only. "Clean" means these stages found
nothing, not that the artifact is safe. This report offers possible issues with
evidence and reaches no verdict. What to do with it is yours to decide.
```

### Rules for the summary

- **Stage order, always.** One status line per stage. Points of attention sit
  under the stage that found them, so where an item sits tells the reader what
  kind of evidence it is. (Decided 2026-09-25; revisit if readers miss items low
  on the page.)
- **Nothing found collapses.** A stage with no points of attention shows its
  status line only, ending "nothing found (validated)". A stage that failed
  validation says so and points to section 7; it never shows as clean.
- **Points of attention are locations to look at, not accusations.** One line
  each, always with file and line. (Named "What could be an issue" and "Points of
  attention" in earlier versions; same content.)
- **Plain facts.** An alarming finding is stated in full and plainly, with no
  adjective the fact does not carry: "This text is invisible when rendered and
  instructs the model to send X to Y." A fact can be damning without a verdict.
- **No verdict.** No benign / unclear / concerning, no score, no severity.
- The summary gives only the **count** of recommendations, so it never reads as
  advice.
- No metric appears without its benign share where one exists.
- Capability posture is stated flatly and qualified in the same breath. A clean,
  well-built repository scores three of three; saying so once prevents the reader
  inventing a verdict from it.

### Worked example: obra/superpowers v6.3.0

Reconstructed from Case 001 in the 2026-09-25 layout. Case 001 predates stage 3,
so this example shows how a stage that did not run is reported.

```
# obra/superpowers v6.3.0

github.com/obra/superpowers | retrieved 2026-08-30 | sha256 e5e1c9bd…ee9ec
Static examination only. Nothing executed.

1 What ships               195 files, 18 formats, 4 script languages (+1 .cmd). 1 hook (2 host configs). 9 platform manifests.
  - hooks/hooks.json: shell execution at every SessionStart, before first user input
  - 9 platform manifests: permission models not compared across hosts
2 What the model reads     193/195 files (99.0%). 32 hidden HTML comments in markdown, 32 benign.
3 What loads what          Not run. See 7.
4 What the text asks for   19 harness conditionals, all tool-name documentation.
  - README.md:228: "fetch and follow instructions from <url>", branch ref not a commit
5 What this touches        Private data: yes · Untrusted content: yes · External: yes
                           All three legs of the lethal trifecta. That raises risk.
                           It is not an issue on its own.
  - hooks/session-start: injects context at harness trust, wrapped in <EXTREMELY_IMPORTANT>
6 Needs a human read       Not run (Case 001 predates stage 6).
7 Not examined             Reference graph; version history; 2 image assets unread.

Recommendations: 2, in the full report. Unranked.

What this is not: static examination only. "Clean" means these stages found
nothing, not that the artifact is safe. This report offers possible issues with
evidence and reaches no verdict. What to do with it is yours to decide.
```

## The full report

Sections 1 to 7 in order, each opening with its status line from the summary,
then every finding (file:line, verbatim quote, audience tag where it applies,
benign-share context, validation stamp) and the section's Part B metrics. Then
Recommendations. Then, if other scanners were run on the same pinned copy, the
appendix below.

## Recommendations (end of the full report)

Builder-facing (CUSTOMERS.md, 2026-09-24):

1. Each one points at a file and line.
2. Each one is conditional on what the skill is for, which only the builder
   knows: "If this skill does not need X, then…"
3. Each one names a narrower way to do the same thing, not just the problem.
4. **Never ranked.** List in stage order, then document order. Ordering by
   importance is a severity score by another name.
5. Never advice on whether to install. The report does not address that question.

A finding with no narrower alternative gets no recommendation. It stays in its
section as a fact, and the builder decides.

```
## Recommendations
Conditional on what the skill is for. Unranked, in stage order.

- <file:line>: If <the skill does not need X>, <narrower alternative>.
```

### Illustrative example: obra/superpowers v6.3.0

```
## Recommendations
Conditional on what the skill is for. Unranked, in stage order.

- hooks/hooks.json: If the SessionStart context does not need to be computed at
  run time, ship it as a static file the hook reads, so the shell step can be
  removed.
- README.md:228: If the instructions at this URL do not need to change after
  release, pin a commit SHA instead of a branch ref, or inline the instructions
  so they are part of what a reviewer reads.
```

*(Illustrative, written from Case 001's findings; not part of the original
Case 001 report.)*

## Appendix: other scanners' flags

Added 2026-09-24, undecided (HANDOVER gap 10). If SkillSpector or the Cisco
scanner is run on the same pinned copy, list each of its flags beside what the
text at that file:line actually does. This is the builder hook in CUSTOMERS.md.
It explains another tool's flag; it does not agree or disagree with its score.
Scanner scores never appear in a Walkdown report.

---

# Part B: The standard

Metric definitions, numbered by stage. Reference material for whoever runs the
audit, not text to reproduce in a report.

Each metric states:

- **Count:** how it is counted, precisely
- **Why:** why it matters, one line
- **Not:** the misreading to head off

The third is mandatory. A metric that cannot say what it does not mean has not
been thought through and does not belong in the standard yet. Each section ends
with **To come**: checks the stage performs whose metric is not yet written. They
get written after a run shows what is worth counting.

---

## Section 1: What ships (stage 1)

The shape of the artifact before any content is read for meaning. Cheap,
structural, and it sets the ceiling on how reviewable the thing is at all.

### 1.1 Format count

**Count:** distinct file extensions present, listed in full with per-format counts.
**Why:** each additional format is another reader you need and another place
something can hide. Lower is better.
**Not:** format diversity is not misconduct. A build tool legitimately ships many
types. It measures review cost, not intent.

### 1.2 Formats exceeding their need

**Count:** files in a rich or binary format whose content is prose, config, or
tabular data that plain text would hold: a PDF that is a page of instructions, a
DOCX that is a README.
**Why:** a format that renders differently than it reads is the whole hidden-text
class. Choosing one when plain text would do is an unexplained decision, and
unexplained decisions are what an audit is for.
**Not:** not an accusation. Most are habit, or a document that arrived from
elsewhere. Each is a question to answer, not a violation to record.

### 1.3 Script language count

**Count:** distinct languages among executable and script files, with the file
list per language.
**Why:** a skill needs one. Two invites a question. Three or more usually means
accretion over time or code that came from somewhere else, and code that came
from somewhere else is worth knowing about.
**Not:** cross-platform support is a legitimate reason for two (a `.sh` and a
`.cmd`). Count them, then ask; do not flag on the count alone.

### 1.4 File-size outliers

**Count:** files whose size is a large multiple of the median for their type,
with the ratio stated. Documentation files above a stated byte ceiling are listed
individually.
**Why:** a malicious skill on ClawHub carried 22 MB of padding in its README
specifically to exceed scanner size limits, defeating two scanners at once. Every
automated pass has a threshold, and an unpublished threshold is an attack surface.
**Not:** large files are usually vendored references or generated output. The
metric is a size anomaly, not a payload.

### 1.5 Reader-window exposure

**Count:** files whose line count or byte size exceeds the stated reader window
(default: 2000 lines, 50 KB), with the window published in the report, plus the
number of files carrying any line over 500 characters.
**Why:** a payload past the truncation point is invisible to a model-assisted
reviewer and visible to the model that loads the whole file. The window is the
attack surface, so it is published.
**Not:** long files are usually release notes, vendored references, and plans.
The metric names where a reviewer's coverage silently ends. It is not a payload.
**superpowers:** 0 files over 2000 lines; 4 over 50 KB (docs and release notes);
14 with a line over 500 characters, longest 2005. *Recounted 2026-09-25 by stage
1: the earlier figures (7 over 50 KB, 15 long lines, in the 2026-09-04 review) do not
reproduce. 7 only appears at a ~48,000-byte threshold, and 15 counts bytes, not
characters; one file crosses 500 only in bytes. The window is 50,000 bytes and
the line limit is characters.*

### 1.6 Extension-versus-content mismatch

**Count:** files whose extension and magic-byte type disagree, with the
detector's own false-positive rate stated beside the count.
**Why:** a `.md` that is an archive, or a `.txt` that a hook executes, is a
reader-selection attack. The wrong reader produces a confident clean result.
**Not:** the detector is noisy. `file` reports 5 superpowers markdown files as
JavaScript because they open with a code fence. Report the rule and its noise
together or the number is a scare number.

### 1.7 Symlinks, encodings, archives

**Count:** symlinks in tree; text files not in UTF-8 or carrying a BOM; archives
present.
**Why:** each is a way for content to be in the artifact and outside the reader.
A symlink into the home directory turns "read every file in this folder" into
credential access.
**Not:** zero is the normal result and should be stated as such.
**superpowers:** 0, 0, 0.

### 1.8 Hook event census

**Count:** one row per hook: event, matcher, blocking or async, can it modify
tool input, which files its script reads, what wrapper it emits.
**Why:** a hook is execution at load plus context at harness trust. A
`PreToolUse` hook on every tool is all three trifecta legs in one stanza.
**Not:** one `SessionStart` hook is ordinary plugin mechanics. The table exists
so the unusual row is visible.
**superpowers:** 2 rows, one hook shipped for two hosts. `hooks/hooks.json`:
`SessionStart`, matcher `startup|clear|compact`, blocking, reads
`skills/using-superpowers/SKILL.md`, emits `<EXTREMELY_IMPORTANT>`.
`hooks/hooks-cursor.json`: the same hook in Cursor's flat format, no matcher.
Each host's copy is a row, because each is what that host runs (Case 001
counted only the Claude format).

### 1.9 Agent and command tool grants

**Count:** one row per agent or command definition: the tools it is granted,
verbatim from its frontmatter, beside its stated job (its `description`).
**Why:** a grant is capability the text does not have to ask for. An agent that
only formats but holds Bash has execution its job does not explain.
**Not:** a broad grant can be the job (a builder agent needs Bash). The row pairs
grant with stated job so a human can compare them; it does not score the match.
**plumbline 28295e9:** 7 agent definitions; the Bash / no-Bash split tracked the
stated jobs (read-only agents held no Bash).

**To come:** platform manifests side by side (count, permission model per host,
whether they diverge; superpowers ships 9, uncompared); description field
contents; frontmatter loader disagreement; distribution-channel differences.

---

## Section 2: What the model actually reads (stage 2)

### 2.1 Review coverage

**Count:** percentage of files, and percentage of bytes, actually read. Two
numbers with the unread list attached.
**Why:** this is the honest headline. It measures the audit rather than the
artifact, and it is the number nobody publishes.
**Not:** high coverage is not a clean bill of health. It states how much of the
artifact the report is entitled to cover.

### 2.2 Unreadable content

**Count:** bytes and files the reader cannot read: encrypted, compiled, minified,
archived, binary blobs, and encoded blobs over a length threshold.
**Why:** unreadable is unreviewable. Content that cannot be read cannot be
cleared.
**Not:** images and compiled assets are normally benign, and are counted here
because they are unread, not because they are suspect.

**To come:** divergences per format (reading A versus B); hidden markdown
carriers by kind (superpowers, recounted by stage 2 on 2026-09-25: 32 HTML comments
hidden in markdown, all in `.github` templates, all benign; Case 001's "71" mixed
comments in every file type with CSS-hiding matches); invisible / bidi /
confusable counts; metadata fields carrying text; language / script-shift runs.

### Worked example (sections 1 and 2): obra/superpowers v6.3.0

| Metric | Value |
|---|---|
| 1.1 Format count | 18 extensions across 195 files; md 94, sh 41, json 14, js 10, txt 9, py 6, remainder ≤2 each |
| 1.2 Formats exceeding need | 0: no PDF, DOCX, XLSX, PPTX anywhere |
| 1.3 Script languages | 4: bash (41), JavaScript (13), Python (6), TypeScript (2), plus 1 `.cmd` for Windows parity |
| 2.1 Review coverage | 193/195 files read (99.0%). Unread: the two image assets |
| 2.2 Unreadable content | 2 files: `assets/app-icon.png`, `assets/superpowers-small.svg`. No archives, no encryption, no minified bundles, no encoded blobs |

Reading: four script languages is above the threshold that invites a question,
and the answer is visible. The repo targets nine agent platforms, which is also
why the format count is high. The composition is explained by the stated scope.
That is what a resolved question looks like; it is recorded, not flagged. (The
SVG is now read as text by stage 2; in 2026-08 it was counted unread.)

---

## Section 3: What loads what (stage 3)

**To come:** orphans; dangling references; dynamic loads; reference depth
(instruction density by distance from the nearest entry point);
manifest versus disk. No run has built the graph yet.

---

## Section 4: What the text asks for (stage 4)

Per pattern, per sub-group (4a to 4d): hits, file:line, benign share. The
clean-corpus benign counts live beside each pattern in PHRASES.md. High-noise
patterns on superpowers, for the record: `rationaliz` (96),
`telemetry|analytics|opt-out` (41), safety adjectives (38), precedence claims
(37), evidence handling (34), `deprecated|supersedes` (24), self-installation
surface (20); on plumbline, `silently` (48, all noise). Zero-noise patterns worth
running first on an unknown repository: traffic-redirection variables, git
persistence keys, MCP config, permission flags, install-by-instruction, claimed
consent, destination-by-reference.

### 4.1 Undocumented endpoints (4a)

**Count:** network destinations present in code or instructions that appear
nowhere in the documentation, as a fraction of all destinations found.
**Why:** the cheapest high-signal check available. A skill that talks to a host
it never mentions has a gap between stated and actual behavior, which is the
whole question restated.
**Not:** CDNs, package registries, and telemetry endpoints are routinely
undocumented and routinely benign. The output is a list to explain, not a list of
findings.

### 4.2 Conditionals (4b)

**Count:** conditional branches in instruction text, by type (harness, clock,
version, state, environment, absence, error path), each with condition and
branch body extracted.
**Why:** every branch is a place where reviewed behavior and delivered behavior
can differ.
**Not:** platform adaptation is legitimate and common. Superpowers carries 19
harness conditionals, all of them documentation of tool-name differences.

### 4.3 Audience split (4d, tagged across all of 4)

**Count:** instruction hits by audience tag: model, subagent, human, downstream
tool.
**Why:** the same sentence is a different finding under each tag. A
permission-widening flag addressed to the human in a README is not model
injection and is still in scope.
**Not:** a repository with many human-addressed instructions is a well-documented
repository.

### 4.4 Instruction density by position

**Count:** instruction-shaped sentences in the first 10%, middle 80%, and last
10% of each file over the reader window.
**Why:** reviewer attention is spent in reading order; model attention favors the
ends. A file whose imperatives cluster at the tail is where to look.
**Not:** a checklist at the end of a skill is normal structure. Density locates;
it does not accuse.

### 4.5 Repeated instruction sentences

**Count:** near-duplicate instruction sentences appearing in more than one file,
with the count per sentence.
**Why:** repetition is a weighting device. An instruction that moves data and
appears five times is a stronger locator than one that appears once.
**Not:** style guides and boilerplate repeat by design.

**To come:** term-table products (conflicts, safety-vocabulary definitions,
displaced-default count); harness-rubric hits with and without a confirmation
step; secrets found (gitleaks).

---

## Section 5: What this touches (stage 5)

### 5.1 Bytes injected at load

**Count:** total bytes delivered into context before the first user input, by
path (hook output, always-on descriptions, bootstrap files).
**Why:** load-time injection dilutes the user's own instructions and hastens
compaction, which is a re-injection window for hooks matching `compact`.
**Not:** a large orientation file is a design choice with a cost, not a finding.
Report the number and the mechanism, and stop.

**To come:** trifecta legs with evidence (locator only: a clean repo scores 3 of
3, and plumbline scored 2 of 3); install grants; least-privilege positives;
cross-stage pairs (orphan plus hit, hidden text plus hit, dynamic load plus hit).

---

## Section 6: Needs a human read (stage 6)

**To come:** review-packet contents (questions by kind: labeling, relational);
model used, or "packet only"; for each answered question, the located
observation and the verbatim model output reference. Waits on the model
decision (METHOD stage 6).

---

## Section 7: Not examined (stage 7)

Always present. Lists, in order: checks that failed validation or did not run
(from the run log); checks skipped for a missing optional dependency; standing
limits (version history, runtime behavior, non-English passages beyond the flag,
unresolved dynamic loads, unread files).

**To come:** version deltas, authorship churn, contributor recency. These become
real metrics when the across-runs feature is built (RUN-LAYOUT); until then they
are standing limits here.

---

## Old metric numbers (before 2026-09-25)

| Old | Now | | Old | Now |
|---|---|---|---|---|
| 1.1 Format count | 1.1 | | 3.1 Hook census | 1.8 |
| 1.2 Formats exceeding need | 1.2 | | 3.2 Bytes injected | 5.1 |
| 1.3 Script languages | 1.3 | | 3.3 Density by position | 4.4 |
| 1.4 Unreadable content | 2.2 | | 3.4 Audience split | 4.3 |
| 1.5 Review coverage | 2.1 | | 3.5 Conditionals | 4.2 |
| 1.6 Size outliers | 1.4 | | 3.6 Repeated sentences | 4.5 |
| 1.7 Undocumented endpoints | 4.1 | | 5.1 Detector validation | Principle 6 |
| 1.8 Reader window | 1.5 | | 5.2 Benign share | Section 4 intro |
| 1.9 Ext / content mismatch | 1.6 | | Section 6 Temporal (to come) | Section 7 |
| 1.10 Symlinks / encodings / archives | 1.7 | | Section 7 Other scanners | Appendix |
