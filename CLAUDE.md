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

## Status (2026-10-03)

**Alpha, public:** https://github.com/BytesFromToby/Walkdown (released from a separate copy;
see "Public repo" below). All eight stages run end to end from one command; every stage has
fixtures, a grader stamp, specs, and tests (538+). Stage 6 (model reads) is optional and
experimental. Four repositories audited (superpowers, Plumbline, claude-familiar, backlog) plus
the self-audit.

Where things stand and what is next: `pre-planning/REVIEW-2026-10-03.md` (the latest review:
fixed items, open design items C14 to C18, and the ordered plan). Stage 6 decisions:
`pre-planning/soft/README.md` (D1, D2, D4, D5 settled; D3 waits on the owner's labeling).

**Scope decision (2026-09-13, standing):** the tool renders **no verdict**. It reviews,
surfaces possible issues, and shows its evidence; the customer decides what to do. The report
is the handoff: a summary page for most readers and a full report with all the detail.

**History:** renamed from Load-Bearing on 2026-09-25 and arranged into numbered stages,
deterministic to soft; built stage by stage from 2026-09-25 (see "Next" below for the record).

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

```
CLAUDE.md            you are here: what the project is, and the map
README.md            the public front page; CREDITS.md, LICENSE, NOTICE, THIRD-PARTY-NOTICES.md
walkdown.py          the front door: a URL or folder in, a run folder and a brief out
.claude/skills/      the walkdown skill (run it from Claude Code)
docs/                public docs: READING-THE-REPORT, HOW-IT-WORKS, RUN-FOLDER
stages/
  01-inventory/      each stage: CONTEXT.md (contract), scripts, specs/<name>.SPEC.md, tests/
  02-reader/
  03-graph/
  04-phrases/
  05-capability/
  06-soft/
  08-report/         stage 8, which also assembles stage 7 (Not examined); there is no 07 folder
  CONTRACT.md        the report format every stage emits
specs/, tests/       spec and tests for walkdown.py
grader/              runs a stage on its fixtures and scores it against Fixtures/ANSWERS/
Fixtures/            fixtures by stage; ANSWERS/ is grader-only, never read in a blind build
pre-planning/        the design corpus and history (charter, method, threats, measurements)
cases/               case reports (held back until each author has seen theirs)
ReposToExamine/      copies of repositories to audit (contents not in git)
RepoResults/         audit runs (contents not in git): reports and LOG.md on top, data/ below
```

The layers: `pre-planning/`, `stages/`, and `Fixtures/` are the **factory** (stable across
runs). `RepoResults/<repo>/` is the **product** (per-run). `cases/` is the **finished
publication**. A run is evidence, never doctrine: flaws found in a run get fixed in the
factory, not the run.

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
- The two early scripts once in `tools/` were rebuilt as stages 2 and 4 and removed (2026-10-03).

---

## Read order

Start with `docs/` for what the code does today (HOW-IT-WORKS, READING-THE-REPORT,
RUN-FOLDER), then `pre-planning/REVIEW-2026-10-03.md` for the current state and plan.
`pre-planning/HANDOVER.md` indexes the design corpus and its history; its state sections are
dated. Then, by concern:

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

## Running an audit

```
python walkdown.py <GitHub URL or folder> [--label jev] [--sweep jev] ...
```

A URL is cloned into `ReposToExamine/<name>/` (an earlier clone of it is updated); the run lands
in `RepoResults/<name>/<date>_<hash7>/` and the command prints a brief with no audited-repo
text. Re-render a run's reports after changing the report code:
`python stages/08-report/run.py --rerender RepoResults/<repo>/<run>`. Outputs never go inside
the examined tree.

**Public repo.** Published from a separate copy; case reports are held back until each
audited repository's author has seen theirs.

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

Stage 6 working notes and open decisions: `pre-planning/soft/` (README lists D1 to D5).
Reports: `summary.html` at the top of a run folder is the page for people (since
2026-10-02 the reports and LOG.md sit at the top and everything else under `data/`;
`docs/RUN-FOLDER.md`). Re-render with `python stages/08-report/run.py --rerender RepoResults/<repo>/<run>`.
Public docs: `docs/READING-THE-REPORT.md`, `docs/HOW-IT-WORKS.md`, `docs/RUN-FOLDER.md`.

*Git repo since 2026-09-25 (local, `main`). Each stage is built on its own branch
and merged when the grader passes.*
