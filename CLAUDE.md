# Walkdown

An ICM-based evaluator of AI skills and skill repositories. It reads the
**instruction layer** — the SKILL.md files, agent definitions, reference docs,
hooks, and manifests that get loaded into a model's context and run with the
user's own permissions — and reports two things, cited to file and line:

1. What does this text ask the model to do?
2. What does installing it grant?

Conventional security tooling cannot see this layer, because the payload is
English, not code. Walkdown reports **capability and surface, never intent**,
and renders **no aggregate score**. A human makes the call. See
`pre-planning/CHARTER.md` for what it is and, more importantly, what it is not.

The name is the method. A walkdown is the engineering step where someone walks
the system as it was actually built and records what is there, against what the
drawings claim, without deciding whether to run it. Renamed from Load-Bearing
2026-09-25 (older docs and runs still carry the old name as history).

**Scope: English-language skills this iteration.** The phrase layer goes blind on
non-English text, so a clean result on a non-English skill means nothing. This
makes language / script shift its own signal (CHARTER scope section).

---

## Status (2026-09-13)

Early. The **method is deep**; the **tooling and cases are thin**. This is
deliberate — the project's own rule is that the harness should not be built until
enough cases exist to specify it. What exists:

- A full design corpus in `pre-planning/` (charter, method, 22-class threat
  register, phrase locators with base rates, reporting standard, red-team
  analysis, incident map, customer model).
- Two audit runs: `cases/001-obra-superpowers.md` (clean, reputable author) and
  `RepoResults/plumbline/28295e9/` (Case 002 early self-audit, clean).
- Two scripts in `tools/` (URL extractor, partial stage 2 reader; both to be rebuilt).

What does **not** exist yet: the two-tier report template (summary + full),
stage 5 and 6 fixtures, a version-delta run, a packaged tool, any published writeup.
The ranked gap list lives in `pre-planning/HANDOVER.md`.

**Scope decision (2026-09-13):** the tool renders **no verdict**. It reviews,
surfaces possible issues, and shows its evidence; the customer decides what to do.
No benign/concerning outcome, no score, no internal judgment pass. The report
*is* the handoff, delivered as a summary page for most readers and a full report
with all the detail.


**Restructure (2026-09-25):** renamed from Load-Bearing to Walkdown, and the
method rearranged into **seven stages, deterministic to soft**. The same stage
numbering organizes the pipeline, fixtures, run outputs, and report sections, so
new checks slot into a stage without reshaping the rest. Build starts with the
deterministic stages (1 to 5). See `pre-planning/METHOD.md`.

---

## The stages

| # | Stage | Question | Report heading |
|---|---|---|---|
| 1 | Inventory | What ships? | What ships |
| 2 | Reader | What does the model actually receive? | What the model actually reads |
| 3 | Graph | What loads what? | What loads what |
| 4 | Phrases (4a reaching out, 4b taking the wheel, 4c changing the environment, 4d talking to the human) | What does the text ask for? | What the text asks for |
| 5 | Capability | What does installing it grant? | What this touches |
| 6 | Soft reads | What can a pattern not settle? | Needs a human read |
| 7 | Not examined | What is this run blind to? | Not examined |
| 8 | Report | assembles 1 to 7 | |

THREATS class numbers (1 to 22) are stable tags on findings, not the ordering.
`pre-planning/COVERAGE.md` maps each class to its stage.

---

## Layout

Current:

```
CLAUDE.md            you are here: what the project is, and the map
pre-planning/        the design corpus: how the audit is meant to work (factory)
Fixtures/            fixtures by stage (01-inventory/ … 04-phrases/) + grader-only ANSWERS/ (factory)
tools/               two early scripts, to be rebuilt inside stages/ (factory)
ReposToExamine/      copies of artifacts under audit, pinned by hash (inputs)
RepoResults/         audit outputs: <repo>/<date>_<hash7>/ per run, LOG.md inside (product)
cases/               published case reports (the finished deliverable)
```

Target (being built; ICM stages):

```
stages/
  01-inventory/      CONTEXT.md (stage contract) + scripts, each with specs/<name>.SPEC.md
  02-reader/           and tests/test_<name>.py
  03-graph/
  04-phrases/
  05-capability/
  06-soft/
  07-limits/
  08-report/
Fixtures/
  01-inventory/ 02-reader/ 03-graph/ 04-phrases/ ...   inputs, visible to the builder
  ANSWERS/                                             grader-only, never read in a blind build
grader/              grader.py + SPEC.md + tests: runs a stage on its fixtures, scores it (built 2026-09-25)
stages/CONTRACT.md   the report format every stage runner emits (visible to builders)
```

The layers: `pre-planning/`, `stages/` (today `tools/`), and `Fixtures/` are the
**factory** (stable across runs). `RepoResults/<repo>/` is the **product**
(per-run). `cases/` is the **finished publication**. A run is evidence, never
doctrine: flaws found in a run get fixed in the factory, not the run.

---

## Build rules (2026-09-25)

- **Every script has a spec and tests.** `specs/<name>.SPEC.md` in the stage's `specs/` folder
  (inputs, outputs, what it must never do, Done-when) and pytest tests written from
  the spec. Python + pytest. Plumbline is not required.
- **Two layers of proof per stage.** Spec tests prove the script does what its
  spec says. The fixture eval (grader against `Fixtures/NN-name/` and ANSWERS)
  proves the stage catches its classes. The same fixtures gate every real audit;
  the result is the stage's validation stamp in the run log.
- **Blind build.** Detectors and the reader are built from the class spec
  (THREATS / PHRASES) and `stages/CONTRACT.md`, never from `Fixtures/ANSWERS/`.
- **Deterministic stages first** (1 to 5). Stage 6's model is the user's choice
  (recommend local; final decision deferred).
- **Optional dependencies** (Tesseract, gitleaks) never fail a run and never pass
  silently: a skipped check is listed in stage 7.
- The two early scripts in `tools/` are rebuilt against specs, not retrofitted.

---

## Read order (into pre-planning/)

Start with `pre-planning/HANDOVER.md`: the living state doc, indexing everything
else. Then, by concern:

| To understand… | Read |
|---|---|
| What this is and is not | `pre-planning/CHARTER.md` |
| Who it is for, and what they do with a finding | `pre-planning/CUSTOMERS.md` |
| How the audit runs (the ordered stages) | `pre-planning/METHOD.md` |
| What files a run leaves on disk, and the run log | `pre-planning/RUN-LAYOUT.md` |
| Which open-source tools to wire in (buy vs. build, licenses) | `pre-planning/TOOLING.md` |
| What it looks for | `pre-planning/THREATS.md` (classes), `pre-planning/PHRASES.md` (pattern sets + base rates) |
| How classes map to stages + fixtures | `pre-planning/COVERAGE.md` |
| How results are reported | `pre-planning/REPORTING.md` |
| How an attacker would beat it | `pre-planning/RED-TEAM.md` |
| Real-world cases the method is measured against | `pre-planning/INCIDENTS.md` |
| The 15s / 45s spoken pitch | `pre-planning/PITCH.md` |
| Chronological history (read as history) | `pre-planning/notes.md`, `pre-planning/REVIEW-2026-09-04.md` |

---

## Working rules (locked; see HANDOVER for the full list and the why)

- **Capability, not intent.** Intent is not observable from a repository.
- **No aggregate score.** No severity rating, risk number, or letter grade.
- **Detection and judgment never happen in the same step.** Base rates die otherwise.
- **Record benign hits.** The benign count is the product, not the noise.
- **Validate every detector against a known positive before trusting a zero.**
- **Report structure, never accuse people.** Classes, not names. Coordinated
  disclosure before publication if anything live is found.
- **No model in the pipeline holds tools**, and no raw untrusted skill text is
  fed to one that does. Scripts detect; a model, if used, reads stage outputs
  and quotes verbatim. One exception (2026-10-01, soft D2): stage 6's coverage
  sweep lets a tool-less model flag passages no pattern matched. It has its own
  validation, reports a location only, and never replaces stage 4.

---

## Running an audit today (by hand, until stages/ exists)

1. Copy the target into `ReposToExamine/`, record its `sha256` / git hash.
2. Create `RepoResults/<repo>/<date>_<hash7>/` with a `LOG.md` per
   `pre-planning/RUN-LAYOUT.md`.
3. Work the stages in order, validating each stage's detectors against its
   fixtures first. Write each stage's output file and its LOG row (with the
   validation stamp) when it finishes. The next step is the first unmarked row.
4. Build the summary + full report in stage order per `pre-planning/REPORTING.md`.
5. If it graduates from calibration to a published case, promote it to
   `cases/NNN-<name>.md`.

Outputs never go inside the examined tree, and never share a name with a path
in it.

---

## Next

1. ~~Move fixtures to `Fixtures/NN-name/`; build the grader.~~ Done 2026-09-25
   (`python grader/grader.py all` → every stage NOT BUILT; 33 grader tests pass).
2. ~~Stage 1 (inventory).~~ Done 2026-09-25, built blind from
   `stages/01-inventory/BUILD-BRIEF.md`: 6 scripts, 39 spec tests, `grader 01` PASS.
3. ~~Stage 2 (reader).~~ Done 2026-09-25, built blind: 11 scripts, `grader 02`
   INCOMPLETE only because Tesseract is absent (image OCR skipped). Run everything
   with `.venv/Scripts/python` (`requirements.txt`).
4. ~~Stage 3 (graph).~~ Done 2026-09-29, built blind: `grader 03` PASS. Depth
   is measured over direct references; files reached only by a glob or folder
   mention are `via: dynamic` (reachable, their own list).
5. ~~Stage 4 v1 (phrases).~~ Done 2026-09-29, built blind: pattern engine,
   `patterns.yaml` (127 rows, each citing PHRASES or THREATS), `grader 04` PASS,
   recall 39/39. Superpowers counts are in PHRASES "Stage 4 v1 measurement".
   Stage 4 part 2 (endpoint census, term table, conditional table, confirm
   pairing, position and repetition, gitleaks) is not built.
6. ~~Stage 5 (capability).~~ Done 2026-09-29: fixture repos authored first
   (trifecta 0 to 3, grants, pairs, posture), then built blind; `grader 05` PASS.
   Superpowers 3 of 3, matching Case 001.
7. ~~Stage 8 v1 (report).~~ Done 2026-09-29, ahead of 6 and 7:
   `python stages/08-report/run.py <repo> --repo <name>` runs stages 1 to 5,
   stamps each with the grader, and writes `RepoResults/<name>/<date>_<hash7>/`
   with LOG.md, 07-limits.md, report/summary.md, report/full.md. First run:
   `RepoResults/superpowers/2026-09-29_f53d923/`.
8. ~~Noise fixes from the superpowers report.~~ Done 2026-09-29 (load vs mention, etc.).
9. ~~Case 003.~~ Drafted 2026-09-29. Held back until the audited repository's
   author has seen it (coordinated disclosure).
10. ~~Case 003 gaps~~ (hook-emitted instructions, host-binary modification) closed
   2026-09-29. ~~Stage 4 part 2~~ built blind and merged 2026-09-29: harness rubric
   (`rubric.action`), endpoint census (`endpoint.host`), conditional table
   (`cond.branch`), term table (`term.def` / `term.conflict` / `term.safety`);
   `CONTEXT-part2.md`. Not built: position/repetition, gitleaks.
11. ~~`J.confirm-first` needs an object~~ done 2026-09-29 (superpowers 139 lines to 30).
   ~~Case 004~~ drafted 2026-09-29; held back until its author has seen it.
   ~~Case 004's open items~~ closed 2026-09-29 (struct.mcp; human-facing evidence never
   counts for legs/grants; L.skip-confirm left to stage 6 labeling).
12. ~~Stage 6 (soft reads).~~ Built blind and merged 2026-09-29, in the report pipeline.
   Backends are the user's choice at run time: `--label jev`, `--compare laya`,
   `--relational claude-cli` (default: packet only). Jev 14/14 on the labeled set,
   Laya 8/14. The Claude CLI login had expired, so no relational read has run yet.
   Real-lines labeled set (119 lines from the three audited repos, 2026-09-29): Jev 44%
   overall, 11/12 at confidence >= 0.8; Laya 13%. A fifth label, `other-sense`, added.
   See `pre-planning/soft/EVAL.md`.
13. ~~Run Walkdown on Walkdown before publishing it.~~ Done 2026-10-02
   (`RepoResults/walkdown/2026-10-02_749e736`, label + sweep): every stage PASS except
   stage 2 INCOMPLETE (no Tesseract). The report is dominated by `Fixtures/` (hostile
   samples) and quoted threats in the docs. Sweep flagged 1 passage outside Fixtures.
   Walked through in `docs/READING-THE-REPORT.md`.
14. Alpha docs 2026-10-02: `README.md`, `docs/READING-THE-REPORT.md`. `ReposToExamine/`
   and `RepoResults/` contents are out of git (the folders stay; only their READMEs are
   tracked). Specs moved to `stages/NN-*/specs/`.
15. 2026-10-02: test data recognized by path (`audience` `test-data`; stage 5 sets it aside,
   `cap.testdata` counts it, `testdata+loaded` pairs test data a model-read file references).
   Self-audit after: ~950 findings set aside, exec-at-load gone; legs remain from the design
   docs. Run folder layout changed (reports + LOG.md on top, rest under `data/`; layout.py).
   Docs: `docs/HOW-IT-WORKS.md`, `docs/RUN-FOLDER.md`, rewritten `docs/READING-THE-REPORT.md`.

Stage 6 working notes and open decisions: `pre-planning/soft/` (README lists D1 to D4).
Reports: `summary.html` at the top of a run folder is the page for people (since
2026-10-02 the reports and LOG.md sit at the top and everything else under `data/`;
`docs/RUN-FOLDER.md`). Re-render with `python stages/08-report/run.py --rerender RepoResults/<repo>/<run>`.
Public docs: `docs/READING-THE-REPORT.md`, `docs/HOW-IT-WORKS.md`, `docs/RUN-FOLDER.md`.

*Git repo since 2026-09-25 (local, `main`). Each stage is built on its own branch
and merged when the grader passes.*
