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
- Stage 5: images the model is pointed at. An image that a file the model reads references
  or loads (not a README's image, not a manifest icon) is listed under "Things to check",
  with whether this run could read its text. A model with vision reads text in images, so
  the reference is the signal; OCR is extra detail.
- Report wording (owner review 2026-10-07): "Look at these first" is now "Things to check",
  and each card names its section in plain words instead of "Stage N". The "not examined"
  count is now the checks this run skipped that apply to the repository (a missing tool for a
  file type the repository does not ship shows as "not needed"); the full list is unchanged.
  The trifecta is described in plain words on the page. The repeated-sentence card no longer
  shows pattern IDs or "repetition adds weight".
- Stage 4: response limits ("report back with only", "under 15 lines", "only the summary") are
  no longer flagged (`H.report-only` retired).
- Fixes from the 2026-10-08 runs (caveman, a large repository, showed most of them):
  - A line is called "hidden" only when rendering hides it. A phrase that matches only once
    look-alike or invisible characters are folded reads "disguised with look-alike or invisible
    characters"; a phrase that matches the raw line is no longer paired with an ordinary fold
    such as an en dash (52 of 87 hidden pairs across the runs were these).
  - A few NUL bytes in a UTF-8 file no longer make it binary (one NUL used to skip a whole file,
    including an MCP server's source). NUL is folded like other invisible characters and shown
    as hidden text.
  - Secret hits that hold no secret (a hash under a `sha256` or `hash` key, a password in a URL
    for localhost or a reserved test domain, an environment variable's name, a plain word) are
    counted apart and listed with the reason in the full report only. Files named
    `*.fixtures.*` are test data.
  - The summary's "not examined" line groups unscanned files into one item per section
    instead of naming each file.
  - Stage 4 is fast on files with very long lines: two patterns opened with an unanchored
    lookahead, which is quadratic in line length (caveman, with 96,000-character JSON lines:
    stage 4 took 27 minutes, now under 2; the whole run 30 minutes, now 5½). A test keeps
    any pattern from opening that way again.
  - Stage 4 again catches "omit what you changed" (hiding the record of changes), lost when
    response length limits stopped being flagged.
- Cached validation stamps now depend on which optional tools are installed (Tesseract,
  gitleaks, pdf2image, Playwright): installing one re-measures the stages instead of reusing
  a stamp taken without it.

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
