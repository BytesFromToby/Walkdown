# Changelog

Each version lists what a user would notice. The version is in `VERSION`, printed by
`python walkdown.py --version`, and recorded in every run's LOG.md with the git commit
("+modified" when the code had uncommitted changes).

## Unreleased

- Stage 2 draws each PDF page and reads it (pypdfium2, now a core dependency, plus Tesseract).
  Lines the page shows that its text layer lacks (a picture of an instruction, text drawn as
  shapes, a scanned page) are listed as hidden text, with the page; the language and script
  checks read them. A scanned PDF is read instead of listed as unread. The risky-ask patterns
  still do not read PDF, DOCX, or image text (section 7 says so). Without Tesseract each PDF is a skip and
  section 7 says so; "PDF render" is no longer "not built". The first 50 pages of each PDF.
- Stage 2, image OCR reads small and faint text better: the image is cropped to its ink, its
  contrast stretched, a dark background inverted, and the crop enlarged; a large image is read
  in tiles, blank ones skipped. 9 px text in the corner of a large image went from 64% of its
  words read to 100%, 8 px light-gray text from 23% to 92%; near-invisible text (`#EEE` on
  white) is still read. 19 of 22 cases in the OCR spike against 17 before
  (`stages/02-reader/OCR-SPIKE-2026-10-18.md`). Tesseract is still the one optional OCR tool:
  the pip-only engine tried missed near-invisible text.
- Stage 2: a language check for text in Latin script (`read.language`). A prose passage whose
  common short words are mostly one other language's (Spanish `el` / `del`, German `und` /
  `der`, and ten more lists), or that is heavily accented with no English in it, is listed with
  the words that matched; the language is never named. Nothing to install: it replaces the
  planned lingua, and section 7 no longer lists language detection as not built. It reads
  Markdown outside code fences, plain text, PDF, DOCX, and OCR text, not code comments, config,
  or HTML. Measured on 1,109 English skill files (20,574 paragraphs): no false positives.
  Recall on short one-line instructions: 16 of 24 held out, misses mostly short Polish, Czech,
  and Turkish lines. The summary's Hidden text section and the full report count and list them.
  New fixture `class04-latin-language.md`.

- Stage 4 now catches an instruction hard-wrapped across two lines of one Markdown paragraph
  (a verb at the end of one line, its target at the start of the next). The finding is cited at
  the line where it starts and quotes both lines. Hits on either line alone are not counted twice.
- Review page: model reads, test data the AI is pointed at, and image cards now say what you are
  deciding ("To decide:"). Test-data and image cards show the line that points the AI at the file
  and what is in it (the start of the file, or the text read from the image). A "do" read says who
  read it and the score in a sentence, and says when it could go either way.
- Stated limits: a line that tells the AI to stay read-only now says whether a tool setting backs it
  (a `--tools` list, deny list, read-only sandbox, or plan mode on the line, or the owner's tools
  list), or that it is stated in the text only, and names other routes in the same skill that can
  write. Review cards show it under "Is it enforced?"; the summary counts it; the full report lists
  every such line and every setting that restricts tools (stage 4 `limit.setting`, stage 5
  `cap.limit`).
- Stage 1: commands in `.cursor/environment.json` (Cursor's cloud-agent setup: `install`, `start`,
  `terminals`) are recorded as commands the host runs on its own, with their lines, and the file is
  an entry point. The report says they run on Cursor's cloud machine, not on your computer.
- Wording: a "do" read from a model now says, beside its score, that it means the line tells the AI
  to do the flagged thing and does not say the thing is harmful (review cards, the summary, and
  docs/MODEL-ACCURACY.md). An agent with no tools list is marked "capability only: what it could use,
  with no evidence it does" on the summary and in HOW-IT-WORKS, and "capability only" in the full report
  (sections 1 and 5).
- `stages/04-phrases/ADDING-A-TERM.md`: the routine for adding, changing, or retiring a search term.
- License: stage 1 records every license file and declared license field (frontmatter,
  `package.json`, plugin manifests, `pyproject.toml`, `Cargo.toml`) and the license its wording
  matches. The summary page says it in one line under the title, with any different license found
  elsewhere; `full.md` section 1 lists them all. Suggested at a class demo.
- Summary page: "Stage by stage" is now "Walkdown Results Breakdown". Each row asks its stage's
  question, says what the step does, and shows its numbers in the open (stage 1: every file type and
  script language); only numbers over 500 characters sit behind "Technical detail". The numbers are
  in plain words, with no repeat of the row's sentence and each term explained (a glob, a dangling
  reference, how text was hidden, what each install grant does). Stage 4 counts lines and says who
  reads them; stage 7 splits not built yet, skipped, and not needed. Reports say "folder or use of
  wildcards" instead of "glob".
- Summary page: "Things to check" now follows "Stage by stage"; the page reads capability,
  stage by stage, things to check, recommendations, model reads.
- Summary page, "What it can do": checked legs first, then unchecked; the checked boxes are
  green, yellow, red in that order, so the third check (all three at once) is the red one.
- Summary page: model reads moved to the end, after the recommendations, in a section closed by
  default that shows how many places it holds.
- Model-read accuracy now has a public page, `docs/MODEL-ACCURACY.md`; the summary page and the
  docs point there.
- Stage 6, Claude backend: reads now run with `--safe-mode` and no setting sources. Before, the
  user's own hooks ran during every read with the audited text in the prompt, and a CLAUDE.md could
  reach the model (found by an outside audit; a live probe confirmed both, and confirms the fix).
- Section 7 tells "not built yet" apart from "tool not installed". PDF page rendering, HTML as a
  browser draws it, and language detection within Latin script have no code; they were reported as
  missing tools, so installing the library would have hidden the gap. A PDF with no text layer is
  always listed as unread.
- Review page (`review.html`, next to `summary.html`): walk through every place to check, one at
  a time, with the lines around it, the matched words highlighted, and what was flagged in plain
  words. Mark each Concerned, Not concerned, or Not sure, with an optional note. Walkdown makes
  no call; the marks are yours. They are kept in the browser, and "Download marks.json" saves
  them; put the file in the run folder and a re-render brings them back. Every search pattern now
  has a plain description. The summary and the review page link to each other at the top right.
- A place named by several findings (three pairs on one line) is one place: one card, counted
  once.
- Stage 4: "don't ask hypothetical questions" (also rhetorical or leading questions, and "no need
  to ask ...") is no longer flagged as skipping confirmation; another "don't ask" on the same line still is
  (owner, 2026-10-12). Superpowers loses 4 hits, and with them its three "loaded only by a folder
  or glob" places (the pressure-test prompts), whose only flagged line this was.
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
