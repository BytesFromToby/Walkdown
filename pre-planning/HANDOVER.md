# Walkdown — handover

Last updated 2026-09-25 (renamed Load-Bearing → Walkdown; method restructured
into seven stages, deterministic to soft; build rules set). Earlier: 2026-09-24
(customer + recommendations decision, SkillSpector prior art). Read this first. Supersedes the 2026-08-30 handover; the locked decisions
and the two conclusions carry forward unchanged.

---

## What this is

An ICM-based evaluator of AI skills and skill repositories. It examines the
**instruction layer** — SKILL.md files, reference docs, subagent prompt
templates, agent definitions, hooks, manifests: the English text loaded into a
model's context and executed with the user's own permissions. Conventional
security tooling cannot see this layer because the payload is prose, not code.

Two questions, answered from the artifact alone:

1. What does this text ask the model to do?
2. What does installing it grant?

It reports capability and surface, **not intent**. A human renders the verdict.

Long-term shape: a folder goes in, a report comes out. Not there yet, and by
the project's own rule it should not be until three cases exist.

---

## Read order

| File | What it is |
|---|---|
| `CHARTER.md` | What this is and, more importantly, what it is not. Read before changing scope. |
| `CUSTOMERS.md` | Who the audit is for and what they do with a finding. **Builder is primary** (finding is a fix list, with recommendations); the adopter is served but not designed for. Holds the recommendation rules and the plain-facts rule. Added 2026-09-13; revised 2026-09-24. |
| `METHOD.md` | Seven ordered stages, deterministic to soft (1 inventory, 2 reader, 3 graph, 4 phrases [4a to 4d], 5 capability, 6 soft reads, 7 not examined), plus 8 report. The same numbering organizes pipeline, fixtures, run outputs, and report. Detection never concludes; the tool renders no verdict. Restructured 2026-09-25; holds the old-pass-to-stage map for older docs that cite "Pass N". |
| `RUN-LAYOUT.md` | The **files** a single run leaves on disk, numbered by stage, and the **per-run LOG.md** format (next step derived from the first unmarked row). Companion to METHOD; METHOD is authoritative on the why. |
| `TOOLING.md` | Vetted open-source tools for the hard layer (conversion, OCR, metadata, unicode, secret-scanning), with licenses. Codebase stays permissive; PyMuPDF + TruffleHog are AGPL and avoided. |
| `COVERAGE.md` | Matrix: stage → all 22 classes → detector → fixture. Class numbers are stable tags; a class split across stages has a row per stage. Fixture status per stage. |
| `THREATS.md` | Twenty-two threat classes. 1–12 mapped to OWASP AST01–10 and sourced; 13–22 added 2026-09-04 from the target's seat. Every entry is a locator. |
| `PHRASES.md` | Exact strings and near-regex locators per class, each with its benign count on the clean corpus. Locators only; never a scorer. |
| `REPORTING.md` | Part A: report layout in stage order (summary page: one line per stage, points of attention under the stage that found them). Part B: metric definitions numbered by stage, each with "what it does not mean", plus a To-come list per section. Old-to-new metric number map at the end. |
| `RED-TEAM.md` | Nineteen attacker approaches, each ending in what it implies for the method. §19 is the auditor attacking itself. |
| `INCIDENTS.md` | Six real incidents mapped to caught / partial / out of scope, plus three added 2026-09-04. |
| `REVIEW-2026-09-04.md` | The 2026-09-04 review pass: every change, the base-rate run, three detector failures, ranked recommendations, pushback. |
| `PITCH.md` | Spoken versions, 15s and 45s. |
| `../cases/001-obra-superpowers.md` | First case report. The format template. |
| `../RepoResults/superpowers/` | Case 001 outputs + `LOG.md` (audit spine). v6.3.0 instance under it. |
| `../RepoResults/plumbline/` | Case 002 outputs + `LOG.md`. 28295e9 instance: first run exercising agent tool-grants; found the `silently` house-word noise. |
| `../RepoResults/CONTEXT.md` | What RepoResults is (Layer 4 product): `<repo>/<date>_<hash7>/` per run, one LOG.md per run. Points to RUN-LAYOUT for the spec. |
| `notes.md` | Chronological working notes. Starts with a behavioral-testing framing the charter later excluded; read it as history. |
| `../tools/extract_urls.py` | Outbound-reference extractor. |
| `../tools/pass1_normalize.py` | Old Pass 1 (now stage 2 reader) as run on superpowers, to be rebuilt: format census, invisible characters, HTML comments, CSS hiding. Does none of the 2026-09-04 Pass 1 additions yet. |

*(Paths relative to `pre-planning/`. The factory — `Fixtures/`, `tools/` — and the per-run work — `ReposToExamine/`, `RepoResults/`, `cases/` — live at the repo root, one level up. The design corpus in this folder cross-references sibling files by bare name.)*

---

## Decisions locked — do not relitigate without a reason

- **Name is Walkdown.** Renamed from Load-Bearing 2026-09-25 (Assay and Readback
  rejected on collisions; Walkdown free on PyPI, npm, and GitHub). History docs
  and past runs keep the old name.
- **No aggregate score.** No severity rating, no risk number, no letter grade.
- **Capability, not intent.** Intent is not observable from a repository.
- **No tool-rendered verdict, and no internal judgment pass.** Added 2026-09-13.
  The report is the handoff: the passes locate, extract, and map; the report
  presents everything with evidence; the customer decides. There is no benign /
  unclear / concerning outcome and no Pass 5 rubric to write, because the tool
  reaches no conclusion. (Dissolves the former "highest-priority gap".) A human
  still reads before *publishing* a case — disclosure discipline, not a verdict.
- **Two deliverables per run.** Added 2026-09-13. A summary page legible to a
  non-specialist, and a full report with all findings and file:line evidence.
- **The builder is the primary customer.** Added 2026-09-24. The report answers
  "here is what this touches" and "here is what could be an issue", written for
  the person who can fix it. The adopter reads the same report but nothing is
  shaped to their go / no-go; verdict-giving scanners (SkillSpector) win that
  reader, and that is accepted. Reason: no-verdict fits the builder, who already
  holds the intent. **Untested**; Case 003 is the test (CUSTOMERS.md, open
  questions).
- **Recommendations, builder-facing, under five rules.** Added 2026-09-24. Tied
  to file:line; conditional on intent the builder supplies; name the narrower
  alternative; never ranked (ranking is a hidden score); never an install
  recommendation to an adopter. Plus the **plain-facts rule**: alarming findings
  are stated in full and plainly, with no adjective the fact does not carry.
  Full text in CUSTOMERS.md. Does not relax "no aggregate score" or "no verdict".
- **Fixtures before detectors; the answer sheet is held apart.** Added 2026-09-14.
  Fixtures (inputs + expected results) are authored first from the design corpus,
  because a detector's zero cannot be trusted without one (validation gate). The
  expected results live in `Fixtures/ANSWERS/` (was `ANSWERS.md` until 2026-09-25), read only by the grader.
  Detectors are built in a session **blind to the answer sheet**, from the class
  spec, and proven only through the grader — so we build to the class, not to our
  own docs. Fixtures carry positives and clean negatives; a green eval means
  "catches the class as specified," never "safe."
- **English-language skills this iteration.** Added 2026-09-14. Detectors, phrase
  register, and reader are built for English; a non-English skill is out of scope
  and a clean result on one means nothing (every report states the language it
  read). Consequence: **language / script shift is its own signal** — an English
  skill with a foreign-language or non-Latin-script passage is hard-flagged (the
  reviewer skims it, the model reads it) and soft-read for hidden instructions.
  Multi-language is a later iteration, not a patch. (CHARTER scope section.)
- **Detection never concludes.** Base rates die if a detection pass decides.
- **Record benign hits.** The benign count is the product, not the noise.
- **Report structure, never accuse people.** Classes, not names.
- **Build detection, not weapons.** Test cases stay inert and local.
- **Coordinated disclosure** before publication if anything live is found.
- **Extraction is verbatim.** Added 2026-09-04. A paraphrase is judgment.
- **No model in the pipeline holds tools.** Added 2026-09-04. Scripts detect;
  a model, if used at all, assembles quotes.
- **Pass outputs never live inside the examined tree.** Added 2026-09-04.

---

## Conclusions the work has produced

**1. Intensity is not malice.** The ecosystem's own best-practice guidance
instructs authors to write "YOU MUST" and "no exceptions". Any scanner keying
on forceful language drowns in false positives generated by recommended style.
Discriminate on what an instruction asks for, not how forcefully it asks.

**2. Capability is not malice either.** The lethal trifecta scores
obra/superpowers 3 of 3, a repo independently established as clean. No
mechanical layer in the method decides anything; every pass locates and none
concludes. Judgment being a separate human pass is an accurate description,
not bureaucracy.

**3. The quiet shapes are the dangerous ones.** Added 2026-09-04. Ranked from
the target's seat, the instructions most likely to move a model with tools in
hand are a claim that consent already exists, a redefined verb, a payload in a
subagent template, text elevated through a hook, an instruction inside an
error message, and a one-line environment write. None of them is loud.

**4. Definition conflicts are unauditable by construction.** Added 2026-09-04.
Two definitions of the same word in one artifact mean the reviewer cannot know
which one governs; the model resolves it by load order and trust level. Same
category as remote instruction loading. The stage 4 term table finds them
mechanically.

**5. An unvalidated detector's zero is not a measurement.** Added 2026-09-04.
The first base-rate run returned false zeros from a case-sensitive grep, a
phantom hit from a locale quirk, and five misclassified files from `file`.
Every pattern validates against a known positive before its zero counts.

Corollary worth publishing: any pipeline reporting a single "26.1% vulnerable"
figure has collapsed a locator into a verdict somewhere in its stack.

---

## Known gaps, ranked

1. ~~**No Pass 5 rubric.**~~ **DISSOLVED 2026-09-13 by scope decision.** The tool
   renders no verdict; the report is the handoff and the customer judges. There
   is nothing to write here. See Decisions locked. **New top gap: #2 (fixtures).**
2. **No fixtures.** *(Now the highest-priority gap.)* Without a known positive per
   class, no zero in PHRASES.md is trustworthy. Inert, local, marked; the
   convention is still unwritten.
3. **Version delta.** A snapshot audit is defeated by patience alone
   (postmark-mcp). No delta run exists. The term table is designed to feed one.
4. **No temporal or social axis.** Authorship churn, first-time contributors in
   mature repos, maintainer identity change. Belongs in stage 1 (or the across-runs feature).
5. **Reachability not built.** Stage 3 exists on paper. The orphan question is
   unanswered for every case so far.
6. **Agent definitions and subagent templates as a class** — first exercised in
   Case 002 (Plumbline, 7 agent tool-grants; the Bash / no-Bash split was real
   signal). Still needs a repo that *misuses* them; superpowers had none.
7. **Reader gaps in stage 2.** No NFKC-folded copy, no markdown-carrier
   extraction, SVG counted as an unread image, no frontmatter double-parse.
8. **Platform manifests uncompared.** Superpowers carries nine. AST10.
9. **n=1.** One repo, by a reputable author. Not a base rate. And the new
   classes were measured against a corpus that barely contains the surfaces
   they describe.
10. **Build vs. buy for the hard-fact layer.** *(Answered 2026-09-14 — see
    `TOOLING.md`.)* Wire in maintained libraries for conversion/OCR/metadata/
    unicode/secret-scanning behind a pluggable interface; keep the codebase
    permissive (PyMuPDF + TruffleHog are AGPL, avoided). Remaining sub-decision:
    whether to also wire prior-art scanners (safedep/vet, cisco skill-scanner,
    NVIDIA SkillSpector) or only study their rulesets. *2026-09-24:* the builder
    focus adds a third option: run them **alongside**, not inside: their flags
    become inputs the builder report explains ("SkillSpector flags X; here is
    what the text at file:line actually does"). Undecided.
11. **No intended-purpose input.** The method takes only the artifact. Letting
    the adopter state the skill's purpose up front would let a capability finding
    be judged against what is expected, but risks importing the author's own
    claims as ground truth, which the method otherwise refuses. Open design
    question, surfaced 2026-09-13 (CUSTOMERS.md). Related: "who keeps the
    definition current, and is there a feed" is recorded in CUSTOMERS.md.
    *Partly resolved 2026-09-24:* for the builder, the reader is the source of
    intent, so recommendations are written conditional on it; the facts sections
    still take no stated purpose as input.
12. **Soft block underspecified, and the eval cannot grade it.** Surfaced
    2026-09-14. The squishy layer (definitional hijacking, capability
    combinations) is the reason to build, but it is one paragraph, and the
    fixtures/grader apparatus only scores deterministic checks. Needs its own
    judgment-graded eval (hand-labeled soft cases a human scores), and a model
    choice: adversarial instruction text must run on a **local** model, never a
    remote API (RED-TEAM §8). Record model + prompt + verbatim output for repro.
13. **Reader has no answer sheet.** Surfaced 2026-09-14. The validation gate
    covers detectors only; a broken reader makes every downstream zero
    confidently wrong. Fixtures must include reader fixtures (input + expected
    normalized text + expected divergences), especially for classes 4 and 11.
14. **Input acquisition / pinning has no tool.** Surfaced 2026-09-14. "Point at a
    link or local repo" is step zero of every run (clone at hash, zip, marketplace
    copy, two tags for a delta) and is not in the build list.
15. **Coverage matrix** — *drafted 2026-09-14, see `COVERAGE.md`.* Maps all 22
    classes to detection surface / detector / fixture kind (restructured by stage 2026-09-25). Exposed: classes 1–12
    have no dedicated phrase group; class 8 is snapshot-blind; classes clustering
    by surface is the answer to the "22 classes is sprawl" reorg (group
    `Fixtures/` by surface; done 2026-09-25 as one folder per stage).

*(Base-rate corpus beyond n=1 is gap #9; temporal axis is #4.)*

---

## Before you build (read after Known gaps)

- **Resolve #12, #13, #15 inside the fixtures session** — they change what you
  author and how `Fixtures/` is organized (by stage since 2026-09-25, per COVERAGE.md).
- **Settle #12's model choice and #14 (acquire+pin) before the blind build.**
- **Build an MVP vertical slice, not all ~19 tools.** Thinnest end-to-end path
  that produces a real report: acquire+pin → read markdown/text → fold → the
  zero-base-rate detectors → trifecta → report. Widen after it runs. "Designing
  instead of shipping" is a standing risk (notes.md).
- **Later:** orchestrator failure policy (halt vs. mark PENDING); a
  pathological-size fixture (the 22 MB README, INCIDENTS OpenClaw); the
  definition-currency loop (new class → new fixture → re-run corpus).

---

## Prior art

- **OWASP Agentic Skills Top 10** (AST01–AST10).
- **arXiv 2601.10338, "Agent Skills in the Wild"**: 31,132 skills scanned;
  26.1% flagged; SkillScan claims 86.7% precision / 82.5% recall.
- **safedep** 11-class threat model; **Red Hat** threats-and-controls article.
- Scanners: `safedep/vet`, `cisco-ai-defense/skill-scanner`.
- **NVIDIA SkillSpector** (added 2026-09-24): 0–100 risk score and SAFE / CAUTION
  / DO NOT INSTALL — the verdict-giving opposite of this project. Partially covers
  capability (MCP least-privilege patterns) as risk findings, not an inventory.
- **TDS evaluation of SkillSpector** (added 2026-09-24): ~80% static false
  positives on legitimate automation, 16 of 20 findings = the skill's stated
  function. Outside evidence for "capability is not intent."
- Full entries and sources: THREATS.md Prior art.

Open ground: audit the auditor; depth against breadth; publish false-positive
cost; build the clean corpus; **publish the detector's own noise beside every
pattern.** *Revised 2026-09-24:* false-positive cost is no longer unpublished
(TDS measured it for one scanner). What remains open there is the per-finding
account of *why* a flag was benign, pinned to file:line, across more than one
scanner on the same repo. That is also exactly what a builder report does.

---

## Current state

**Exists:** charter, method with dated additions, twenty-two-class threat
register, phrase register with base rates, reporting standard, nineteen-entry
red-team analysis, nine incidents mapped, one case report, one method-run
report, two working scripts, one repo copy pinned by hash, one review-pass
record (REVIEW-2026-09-04.md).

*2026-09-25:* fixtures now exist for stages 1 to 4 (authored 2026-09-14; see
COVERAGE.md), with the grader-only answers (`Fixtures/ANSWERS/`, JSON since 2026-09-25). Stages 5 and 6 have none.

**Does not exist:** Stage 5 / 6 fixtures. Any stage built to spec. (The grader
exists since 2026-09-25: `grader/`, 33 tests.) Any repo by an unknown author. Any version-delta
run. A reference graph. A term table on any artifact. The folded-copy reader. The
two-tier report (summary + full) as a written template. Any published writeup.
(A Pass 5 rubric is no longer wanted — see Decisions locked. Case 002 now exists:
the Plumbline early audit, `../RepoResults/plumbline/28295e9/REPORT.md`.)

**Artifact on hand:** `ReposToExamine/superpowers-main/` (zip of main, no git
history), `sha256 e5e1c9bd8cdbf1a90c319b237eb433ad7ba46d273321f48bbe50279124eee9ec`.

**Ratio:** twelve documents, one case (CUSTOMERS.md added 2026-09-13 to fix a
genuine gap: the method never named its reader). The 2026-08-30 handover said the
next artifact should be a case. Two later sittings added documents anyway. The
ratio is now the loudest signal in this file: the next sitting must be a case,
not a document.

*2026-09-24:* this sitting also changed documents (CUSTOMERS, THREATS, this file)
and produced no case. The decision was real (who the report is for), but the
ratio got worse again. Recorded so it is not hidden.

*2026-09-25:* documents again (METHOD, RUN-LAYOUT, REPORTING, COVERAGE
restructured to stages; rename). This one is the last pre-build rearrangement:
the next sitting builds stage 1.

---

## Next actions, in order

**Superseded 2026-09-25 by the stage order below.** The 2026-09-14 list is kept
underneath as history (its item 1, fixtures, is done for stages 1 to 4).

**Build rules (2026-09-25):** ICM stages under `stages/NN-name/`; every script has
`specs/<name>.SPEC.md` + pytest tests; Python; Plumbline not required; the two `tools/`
scripts are rebuilt, not retrofitted; blind build (never read `Fixtures/ANSWERS/` while
building a detector or the reader); deterministic stages first.

1. ~~**Move fixtures** to `Fixtures/NN-name/`; build the **grader**.~~ **Done
   2026-09-25.** Answers are per-stage JSON with fixture hashes; `stages/CONTRACT.md`
   fixes the report format; `grader/` has SPEC + 33 tests. Pipeline (cross-stage)
   expectations are recorded as deferred until the orchestrator exists.
2. ~~**Stage 1 inventory.**~~ **Done 2026-09-25**, built blind by a separate
   builder from `stages/01-inventory/BUILD-BRIEF.md`; grader 01 PASS. Its run on
   superpowers corrected two Case 001 numbers (4 files over 50 KB, not 7; 14 long
   lines by characters, not 15 by bytes) and counts the Cursor hook config as a
   second row. See REPORTING 1.5 and 1.8.
3. ~~**Stage 2 reader.**~~ **Done 2026-09-25**, built blind. Grader INCOMPLETE:
   only the image OCR gate skips (no Tesseract). Fold also strips Unicode tag
   characters and spaces out line separators. Its superpowers run corrected Case
   001's "71 HTML comments" to 32 hidden in markdown (correction note on the run
   report). Project `.venv` + pinned `requirements.txt`; root `pytest.ini` uses
   importlib mode so same-named stage tests don't collide.
4. ~~**Stage 3 graph.**~~ **Done 2026-09-29**, built blind; grader 03 PASS.
   After the first superpowers run, depth changed to count direct references
   only (folder mentions had put most files one hop out); files reached only
   by a glob or folder mention are `via: dynamic`. Superpowers: 80 files
   reached directly, 118 only dynamically, 2 orphans, 1,551 dangling (1,520 in
   code context). Seven files inside skill folders are named by no text and load
   only through `.codex-plugin/plugin.json`'s skills folder (class 12, live and
   unmentioned).
5. ~~**Stage 4 phrases** v1~~ **Done 2026-09-29**, built blind: pattern engine
   over the folded copy, 14 checks, audience tag; grader 04 PASS, recall 39/39
   after moving global and plugin installs to class 7 (THREATS assigns install
   by instruction there; CONTEXT had followed set E). Superpowers: 775 hits;
   counts and the ~40 rows added from THREATS are in PHRASES "Stage 4 v1
   measurement". The superpowers copy had 6 stray `.pyc` files from the
   2026-09-25 pytest incident; deleted the same day. **Still owed (part 2):**
   term table, conditional table, endpoint census, confirm pairing, position and
   repetition, gitleaks.
6. ~~**Stage 5 capability**~~ **Done 2026-09-29.** Fixture repos authored first
   (`Fixtures/05-capability/`: trifecta 0 to 3 legs, grants, orphan / dynamic /
   hidden pairs, agent posture) with answers, by the same session that wrote
   stage 5's CONTEXT, so this eval is weaker than stages 1 to 4 (Case 003 is the
   independent check). They exposed two stage 4 bugs (fetch-follow too broad;
   `>> ~/.bashrc` missed), fixed. Built blind; grader 05 PASS. Superpowers 3 of 3.
   A Bash grant is deliberately not counted as external-comms.
6b. **Stage 8 v1 report: done 2026-09-29**, ahead of 6 and 7 (`stages/08-report/`,
   not blind: no fixtures to be blind to). Runs stages 1 to 5, grader stamps
   each, writes the run folder, LOG, 07-limits (gathered from stage notes and
   skips plus standing limits), summary and full report. First run
   `RepoResults/superpowers/2026-09-29_f53d923/`; its LOG lists the factory
   feedback (dynamic+phrase pairs too broad, template-comment hidden pairs,
   two stage 4 false positives, load-bytes double count across host configs).
7. **Stage 7 limits + stage 8 report + thin orchestrator** writing the per-run
   LOG. Retrofit Case 002 into the stage-ordered summary + full report.
8. ~~**Case 003**~~ **Drafted 2026-09-29** (a builder report, with SkillSpector and Cisco
   run on the same pin for comparison). Held back until the audited repository's author
   has seen it. Five noise fixes and two new pattern rows landed from it.
   Same day: closed the patch-instruction gap (stage 4 `C.script-instruction` +
   stage 5 `hook+phrase` pair) and the host-binary gap (`E.harness-binary`, class 17);
   stage 5 resolves `${CLAUDE_PLUGIN_ROOT}` to the plugin folder. Run `-3` finds
   finding 2 on its own; superpowers regression run shows no new noise.
8b. **Stage 4 part 2: done 2026-09-29.** Fixtures + answers first (`Fixtures/04-phrases/part2-repo/`),
   built blind (`CONTEXT-part2.md`), merged: harness rubric, endpoint census, conditional
   table, term table. Follow-ups the same day: a definition of a confirmation word never
   counts as a confirmation step (THREATS 14); a fenced block is one step with its lead-in
   and follow-up; stage 5 pairs phrase hits only; stage 8 shows the tables. Superpowers:
   19 rubric rows (16 unconfirmed, mostly agent-to-agent send/post: `J.confirm-first`
   needs an object), 24 hosts / 10 undocumented, 77 conditionals, 13 definitions, 0
   conflicts. Not built: position/repetition, gitleaks.
8c. **Case 004 drafted 2026-09-29:** `cases/004-backlog.md` (backloghq/backlog at b449d9f,
   user's pick). Quiet repo: the task-planner agent inherits every tool (the only evidence
   for two trifecta legs); the MCP launcher runs `npm ci --ignore-scripts` at first start.
   Neither scanner reports either; SkillSpector's verdict rests on dependency CVEs.
   Fixes from it: stage 1 `project-instructions` entry kind (CLAUDE.md, AGENTS.md...),
   build/lock files are `tool` audience, `L.guardrail` narrowed, `E.runtime-install`.
   `J.confirm-first` needs an outward object (superpowers 139 lines to 30). Open:
   `L.skip-confirm` on descriptions; MCP servers in plugin.json toward the legs; grants
   from README lines (all three closed the same day: `struct.mcp`, human-facing
   evidence excluded from legs and grants, `L.skip-confirm` left to stage 6 labeling).
   Not published.
9. ~~**Stage 6 soft reads**~~ **Done 2026-09-29.** Model decision: the user picks backends at run
   time (flags or env; default none = packet only): labeling Jev (TypeSafe, remote), compared
   with Laya (local CPU); relational reads Claude via the Claude Code CLI with no tools. RED-TEAM
   §8 reconciled as local by default, remote only when named, never tools. Labeled fixture
   (`Fixtures/06-soft/labels-repo/`, 14 lines) written first; built blind. Jev 14/14, Laya 8/14;
   Laya agreed with Jev on 0 of 10 real questions. Stage 8 runs stage 6 and stamps it with the
   run's labeler. Open: Claude CLI login expired (no relational read has run); check whether
   `claude -p` loads user-level CLAUDE.md/memory.
   **Larger labeled set, 2026-09-29:** every labeling question from the three audited repos
   (119 real lines, `Fixtures/06-soft/real-lines/`, labels grader-only with a review table).
   Added a fifth label, `other-sense` (words used in another sense), the commonest real case.
   Jev 44% overall but 11/12 at confidence >= 0.8 (the summary's `do` points: 9/9 correct);
   Laya 13%. `pre-planning/soft/EVAL.md`. Owed: a second labeler (the user) on the review table.
10. Case 004 version delta when the across-runs feature is in scope. Run
    Walkdown on Walkdown before publishing it.

### History: the 2026-09-14 order

Each is one sitting. Reordered 2026-09-14 to fixtures-first (see Decisions
locked). Do not reorder further without a reason; the order is the argument.

1. **Fixtures + answer sheet + grader (this can use the docs).** Comb THREATS /
   PHRASES / RED-TEAM / INCIDENTS for every replicable shape. Author fixture
   `inputs/` (independent instances, not the doc's exact strings) plus clean
   negatives, and the grader-only `ANSWERS.md`. Build the **grader** alongside.
   This is fixtures-first because a detector's zero is untrustworthy without one.
2. **Reader + folder — SESSION BLIND TO THE ANSWER SHEET.** Reader adapters
   (`tools/`, extending `pass1_normalize.py`), the A/B divergence differ, the
   NFKC-folded copy (zero-width/bidi stripped) with a line-number map, SVG as
   XML, markdown carriers, frontmatter double-parse. Prove only via the grader.
3. **Detector engine + validation gate — still blind.** Run the PHRASES classes
   over the folded copy; each detector validated against its fixture positive
   before a zero counts. Replace every "n/a" in PHRASES via the grader.
4. **Report template — summary + full.** Two markdown skeletons per REPORTING.md;
   retrofit Case 002 (`../RepoResults/plumbline/28295e9/`) into both to prove the
   shape. No verdict field. *2026-09-24:* written for the builder, with a
   recommendations section under the CUSTOMERS.md rules (unranked, file:line,
   conditional on intent). REPORTING.md Part A was revised 2026-09-24 to match
   (overview headings are now "What this touches" / "What could be an issue";
   recommendations section added). Case 002's REPORT.md keeps the old headings,
   since a run is evidence; the retrofit here is what brings it into the new shape.
5. **Thin orchestrator + LOG writer.** Sequences the passes, writes outputs,
   appends LOG entries with validation stamps. Can be minimal at first.
6. **Term table, reachability, capability mapper.** Pass 3 term table (run on
   superpowers to confirm the 6-hit, 0-conflict base rate), Pass 2b graph, Pass 4
   trifecta-as-map.
7. **Case 003: unknown author, from a marketplace.** Prefer a skill heavy on
   hooks / MCP / subagents, so the new classes meet a corpus that contains them.
   *2026-09-24:* write it **as a builder report**, and run SkillSpector and the
   Cisco scanner on the same pinned copy so the report can explain their flags.
   This is also the test of the builder-customer decision: would its builder
   act on it?
8. **Case 004: version delta.** Two tagged superpowers releases, pinned
   separately. Diff the instruction layer and the term table.

Done: **Case 002 (Plumbline self-audit)** — `../RepoResults/plumbline/28295e9/`,
2026-09-13. Clean; exercised class-15 agent tool-grants; found the `silently`
house-word noise.
9. **Then, and not before, the skill wrapper.** Scripts detect with no model;
   the model assembles verbatim quotes into the report skeleton and holds no
   other tools. Run Walkdown on Walkdown before publishing it.

---

## Standing cautions

- **PHRASES.md is not a scorer.** The 96-hit `rationaliz` result on a clean
  repo is what the intensity linter looks like. A count from that file in an
  overview page without its benign share means the project has become what it
  criticizes.
- **Twenty-two classes is sprawl.** Before case 003 adds more, consider
  tagging hits on the charter's two questions as axes (what the text asks;
  what install grants) and keeping the numbered classes as a lookup.
- **Harness facts are census items, not claims.** Which hook events exist,
  whether a pre-tool hook can rewrite input, which frontmatter flags each host
  honors: stated in THREATS as things to check, verified against current
  platform docs before any report leans on them.
- **Publish the thresholds.** 2000 lines, 50 KB, 500 chars. On every overview
  page, because an unpublished threshold is the attack surface.

---
