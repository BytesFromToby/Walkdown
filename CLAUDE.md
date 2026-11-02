# Walkdown

Walkdown audits AI skills and skill repositories: it reads the **instruction layer** (the SKILL.md files, agent
definitions, reference docs, hooks, and manifests a model loads and runs with the user's own permissions) and
reports, cited to file and line, what that text asks the model to do and what installing it grants. It gives no
aggregate score and no verdict, and leaves the call to a person (`pre-planning/CHARTER.md`).

**Scope: English-language skills this iteration.** The phrase layer goes blind on non-English text, so a clean
result on a non-English skill means nothing (CHARTER scope section).

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
  and quotes verbatim. One exception (2026-10-01, soft D2): the coverage sweep
  (`03-sweep`, and `04-pinpoint`, which names the line inside a flagged passage)
  lets a tool-less model flag passages no pattern matched. It has its own
  validation, reports a location only, and never replaces `02.4-phrases`.
  (Step names since 0.4.0; the rule read "stage 6" and "stage 4" before.)

## Layout
```
walkdown.py      the router: a URL or folder in, a run folder and a brief out
stages/          each stage: CONTEXT.md (contract), scripts, specs/ (one spec), tests/; plus CONTRACT.md
                 (the report format), stages.json (the stage list), _shared/ (code several stages use)
  01-intake/     gets the copy: a folder read in place, a URL cloned or updated
  02-coded/      every coded finding, no model: 02.1-inventory to 02.5-capability, and 02.6-builder
  03-sweep/      optional AI read of the prose no pattern matched (--sweep jev or claude-cli[:model])
  04-pinpoint/   optional AI read naming the line behind a sweep flag (--pinpoint claude-cli[:model])
  05-qa/         the check of the run, before the report: what is missing, what was not examined; a gap holds the run
  06-report/     the pages, full.md, changes, the limits, and the brief
Library/         tables, lists, and their sources: data only, never code (README.md is the index)
tools/           the grader, compare_runs.py, baserates.py, fixture generators, model evaluation
Fixtures/        fixtures by stage; ANSWERS/ is grader-only and never read in a blind build
docs/, .claude/skills/   the public docs, and the walkdown skill
pre-planning/, cases/    the private design corpus and history; case reports held back
ReposToExamine/, RepoResults/   repositories to audit, and audit runs (neither is in git)
```

## Running an audit
`.venv/Scripts/python walkdown.py <GitHub URL, GitHub folder link, or folder> [--sweep jev|claude-cli[:model] [--pinpoint claude-cli[:model]] | --reads [model]]`
files the run under `RepoResults/<name>/<date>_<hash7>/` and prints `brief.md`, which holds no text from the audited
repository. `--reads [model]` runs Sweep on TypeSafe's Jev when Jev is available, else on the Claude model named, and Pinpoint on the Claude model named. A run with a gap (a step that failed, a fixture check that did not pass, a check that did not account for all it should have looked at, a model read with no answer) is held:
no report, exit 1, and the brief says how to go on (`walkdown.py continue <run folder>` writes the report with what ran). Tests: `.venv/Scripts/python -m pytest -q`, behind a wall (root `conftest.py`) that keeps real models out of reach. Grader: `.venv/Scripts/python tools/grader/grader.py all`.
Re-render a run: `.venv/Scripts/python stages/06-report/run.py RepoResults/<name>/<run>`.

## Read next
| To understand | Read |
|---|---|
| What this is and is not; who it is for | `pre-planning/CHARTER.md`, `pre-planning/CUSTOMERS.md` |
| What each check looks for; the reports; a run's files | `docs/HOW-IT-WORKS.md`, `docs/READING-THE-REPORT.md`, `docs/RUN-FOLDER.md` |
| How the build is laid out (a map) | `docs/STRUCTURE.md` |
| A stage's contract, then its spec; the tables | `stages/CONTRACT.md`, `stages/02-coded/CONTEXT.md` (each stage has a `CONTEXT.md` and a `specs/` folder), `Library/README.md` |
| The design corpus, history, and build record | `pre-planning/HANDOVER.md`, `pre-planning/history/BUILD-RECORD.md` |
| The restructure; what is parked and what is next | `pre-planning/RESTRUCTURE-NOTES.md`, `pre-planning/MODEL-NOTES.md` |
