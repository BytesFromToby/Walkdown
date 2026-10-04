# Changelog

Each version lists what a user would notice. The version is in `VERSION`, printed by
`python walkdown.py --version`, and recorded in every run's LOG.md with the git commit
("+modified" when the code had uncommitted changes).

## Unreleased

- Stage 4: instruction position in long files (flagged lines past the reader window) and
  sentences repeated across files (REPORTING 4.4, 4.5).
- Stage 4: committed-secret scan (gitleaks when installed, detect-secrets otherwise; new
  requirement). Reported by location only: the value never appears, and other findings on
  that line have their quote replaced.

## 0.1.0 (2026-10-04), first alpha

The first version shared for feedback. Stages 1 to 5 and the report are deterministic and
validated against fixtures; stage 6 (model reads) is optional and experimental.

**Running it**
- `python walkdown.py <GitHub URL or folder>` runs every stage and prints a short brief. A URL
  is cloned into `ReposToExamine/`; running it again updates that clone (`--keep` audits it as
  it is, `--fresh` clones again).
- A `walkdown` skill runs it from Claude Code; the brief it relays holds no text from the
  audited repository.
- Each run folder has the reports at the top (`summary.html`, `summary.md`, `full.md`, `LOG.md`)
  and everything else under `data/`.

**What it examines**
- Stage 1, what ships: files, entry points, descriptions, agent tool grants, hooks, manifests,
  MCP servers, structural flags; a content hash per file.
- Stage 2, what the model actually reads: raw text against rendered (hidden HTML, comments,
  zero-width and bidirectional characters, white-on-white, metadata, OCR of images, with small
  images enlarged so tiny text is read).
- Stage 3, what loads what: entry points, orphans, files reached only through globs, dangling
  references.
- Stage 4, what the text asks for: about 125 phrase patterns in four groups, plus tables of
  network hosts, guarded actions and their confirmation steps, conditionals, and definitions.
- Stage 5, what installing it grants: the three legs of the lethal trifecta, install grants,
  bytes in context at load, agent posture, and pairs of findings worth more together.
- Test data (`tests/`, `fixtures/`, `test_*.py` and the like) is set aside from the capability
  map and the summary, and counted; test data a model-read file references still counts.
- Stage 6 (optional): model labels of flagged lines (Jev), relational reads (Claude Code CLI),
  and a coverage sweep for instructions no pattern matched; shown in their own experimental
  block, with "near the line" bands where repeat reads drift.
- Version drift: auditing the same repository again compares the two runs (`changes.md`);
  `walkdown.py diff <old run> <new run>` compares any two.

**How it is checked**
- Every script has a spec and pytest tests (550); every stage has fixtures and a grader.
- The tests and graders run on GitHub on every push (Linux, Python 3.12 and 3.13, Tesseract).
- Each audit stamps each stage's validation in LOG.md; stamps are reused while code and
  fixtures are unchanged (`--revalidate` to measure afresh).

**Known limits**
- English only; static only; known phrasings (the sweep narrows this, experimentally).
- Not built yet: instruction position and repetition checks, secret scanning (gitleaks).
- Stage 6 accuracy is measured and modest (`pre-planning/soft/EVAL.md`); a second human
  labeling of the test lines is in progress.
