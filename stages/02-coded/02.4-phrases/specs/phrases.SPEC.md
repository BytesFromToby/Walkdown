# phrases: spec

One spec for the `02.4-phrases` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. Merged from the per-script specs in restructure step 8a.

## The stage

Every hit is a **locator, never a verdict**. PHRASES.md records that every
pattern fires in clean repositories; the benign count is part of the product.
`02.4-phrases` records hits. It never says whether a hit is a problem (METHOD: "Does
not: say whether any hit is a problem").

Part 1 is the pattern engine and its phrase checks; part 2 (below) adds the harness rubric, the endpoint census, and the term table. This section is the stage's rules as a whole; each script's own section, after it, is what that script does and the tests behind it.

### What is scanned

- `<input_dir>`: a pinned repo copy or a fixture folder. Read-only.
- `02.4-phrases` greps the **folded** text (CONTRACT). Until the orchestrator passes it
  `02.2-reader`'s output, it folds its own input with `02.2-reader`'s rules
  (`stages/02-coded/02.2-reader/specs/reader.SPEC.md`, section `fold`), reimplemented here, never imported: NFKC;
  strip zero-width characters, bidi controls, soft hyphen, and Unicode tag
  characters; replace U+2028, U+2029, U+0085 with a space; fold confusables to
  ASCII. Line count never changes, so every hit cites the original line.
- Scan every file that decodes as text (UTF-8, or the encoding
  `charset-normalizer` detects), including HTML comments, code blocks, and
  frontmatter: the model receives all of it. Walk with `02.1-inventory`'s rules (no
  symlinks out of the tree, no `.git/`). Files that do not decode as text (PDF,
  DOCX, images) are scanned from `02.2-reader`'s extracted text when the run passes
  `--normalized` (2026-10-18): the text layer, text drawn on PDF pages, image OCR;
  phrase patterns only, cited by `text_line` with `line` null. Without it they are
  not scanned; either way stderr says which.

### The pattern table

Patterns live in **one data file**, `Library/patterns.yaml`, not scattered through code.
Each pattern row has:

- `id` (stable, e.g. `L.ignore`), `check` (the CONTRACT check ID), `regex`
  (case-insensitive, run on the folded line);
- `source`: where the pattern comes from: `PHRASES:<set>` (a set in `Library/PHRASES.md`) or
  `THREATS:<class>` (a class in `Library/THREATS.md`), more than one joined with `; `, or an ID from
  `Library/SOURCES.md`; a widening or narrowing of the set's wording is said in the row's `note`;
- `plain`: the words the review page shows a reader, what the pattern looks for and then
  "The worry: ..." (read by `stages/06-report/plain.py`);
- optional `unless`: a regex that, when it also matches the same line, cancels
  the hit (for example, an opt-in clause beside a telemetry verb). Every
  `unless` also cites a source or states its reason in a `note`.

Write the table from PHRASES and THREATS first. The PHRASES rows are narrow
strings from one clean repo; the fixtures test **the class**, with independent
wordings. Where a class needs more than PHRASES lists, derive the pattern from
the THREATS bullet (for example class 1: a private data source, a sending verb,
and a destination, in one sentence). **Never add a pattern that matches only one
fixture line's wording.** A miss on a recall row is a measurement, not a bug.

### Checks and sources

Sub-groups and classes from CONTRACT; sets and bullets from PHRASES and THREATS.

| Check | Sub-group | Class | Build the patterns from |
|---|---|---|---|
| `phrase.K.exfil` | 4a | 1 | PHRASES K; THREATS 1 (relay hosts, chat webhooks, sending verbs, encode-then-send) and its extensions (destination by reference, string assembly, templates as the channel) |
| `phrase.creds` | 4a | 2 | THREATS 2: credential paths, bulk environment harvesting, secret-name patterns; enumeration versus one named variable |
| `phrase.remote-load` | 4a | 3 | THREATS 3: fetch-and-follow phrases, raw hosts, pipe-to-shell, branch refs instead of commit SHAs |
| `phrase.L.override` | 4b | 5 | PHRASES L, all nine families |
| `phrase.A.consent` | 4b | 13 | PHRASES A |
| `phrase.B.defs` | 4b | 14 | PHRASES B |
| `phrase.H.anti-review` | 4b | 20 | PHRASES H. Narrow `rationaliz` and bare `precedence` to phrase forms, as the notes there say |
| `phrase.I.conditional` | 4b | 21 | PHRASES I |
| `phrase.E.perms` | 4c | 7 | THREATS 7 (privilege, execution primitives, anything that outlives the session, package installation by instruction) and the permission-widening row of PHRASES E. Global and plugin installs (`npm install -g`, `npx -y`, `plugin install`, `marketplace add`) are here; project-local `pip install` / `brew install` stay in `phrase.E.env` (corrected 2026-09-29) |
| `phrase.C.second-order` | 4c | 15 | PHRASES C (phrase rows only; file-name rows are `02.1-inventory` and `02.3-graph`) |
| `phrase.D.trust` | 4c | 16 | PHRASES D (phrase rows) |
| `phrase.E.env` | 4c | 17 | PHRASES E, except the permission-widening row and global or plugin installs (those are `phrase.E.perms`) |
| `phrase.J.prohibited` | 4c | 22 | PHRASES J, with the harness tiers listed there |
| `phrase.G.human` | 4d | 19 | PHRASES G |

### Findings

One finding per **line per check**: when several patterns of one check hit the
same line, emit one finding listing them. Fields:

- `check`, `file`, `line` (the original line number);
- `quote`: the original line, verbatim, before folding;
- `patterns`: the ids that hit, in table order;
- `audience`: who the line is addressed to, by path (METHOD "Audience tag"):
  `human` for `README*`, `INSTALL*`, `CONTRIBUTING*`, `CODE_OF_CONDUCT*`,
  `CHANGELOG*`, `CHANGES*`, `HISTORY*`, release notes, `LICENSE*`, `NOTICE*`,
  `AUTHORS*`, `SECURITY*` (added 2026-09-29, Case 003),
  `docs/`, `.github/`; `subagent` for `agents/`, `commands/`, and files named
  `*prompt*.md`; `tool` for scripts, hook configs, and package / lock / build
  configuration files (`package.json`, lockfiles, `tsconfig*.json`; 2026-09-29); `model` otherwise. The tag
  describes the file, not the reader's intent.
- `folded`: true when the line matched only after folding (the raw line would
  not have matched). That is its own signal (THREATS class 4).

### Part 2: the rubric, the endpoint census, and the term table

Part 2 adds three descriptive products that METHOD's phrase stage lists beside the patterns (a fourth, the conditional table, was cut in restructure step 6). Same stage, same runner (`run.py`), same report: part 2 findings are appended to the part 1 findings. Part 2 never removes or changes a part 1 finding.

Every product is a **table to read, never a verdict** (METHOD: "Does not: say whether any hit is a problem"). A confirm-first action with a confirmation step is recorded; one without is recorded; neither is called good or bad.

#### Shared rules

- Input is the same folded text part 1 greps; every finding cites the original
  file and line and quotes the original text.
- **Instruction text** = files whose part 1 `audience` is `model` or `subagent`.
  **Docs** = files whose audience is `human`. **Code** = audience `tool`.
- Frontmatter counts as instruction text (it is loaded).

#### 1. Harness rubric: `rubric.action` (THREATS 22, PHRASES J)

One finding per `phrase.J.prohibited` hit **in instruction text only** (a
`POST` in a script is code, not an instruction to the model). Fields:

- `tier`: `prohibited` (PHRASES J prohibited tier: entering credentials or
  payment details, creating accounts, permanent deletion, transfers, security
  settings, CAPTCHAs, downloading or running untrusted files) or `confirm-first`
  (sending messages, posting, publishing, purchasing, accepting terms, granting
  OAuth, changing account settings, standing rules, submitting forms).
- `action`: the verb as written.
- `confirmation`: true when a confirmation step is in **the same step**, else
  false.
- `confirm_line` and `confirm_quote` when true.

**The step** is the enclosing unit, not the line: the markdown list item
(the bullet line plus its indented continuation lines), or else the paragraph
(consecutive non-blank lines), or for a numbered step the item. A line inside a
fenced block belongs to a step made of the whole block plus the paragraph just
before it (its lead-in) and the paragraph just after it (added 2026-09-29: a
confirmation prompt quoted in a fence, "This will permanently delete: ... Type
'discard' to confirm", in a skill for finishing a branch). A confirmation
step is wording that makes the action wait on the user: ask / asks the user,
confirm / confirmation, approval / approve (by the user), permission, "wait for",
"check with", "only after the user". A confirmation clause that negates itself
("without asking", "no need to confirm", "do not ask") is **not** a
confirmation; record `confirmation: false` and `negated_confirmation: true`.

A line in the step that **defines** a confirmation word ("Confirmation means
announcing your intent", "approval is when") is never a confirmation step: that
redefinition is THREATS 14's attack on the safety vocabulary. The row records
`confirm_redefined: true` when such a line was in the step (added 2026-09-29,
after the build: the fixture's SKILL.md:26 was being confirmed by line 27).

This is what makes part 1's `J.confirm-first` usable: the part 1 hit stays
(a locator), and the rubric row says whether its step asks first.

#### 2. Endpoint census: `endpoint.host` (REPORTING 4.1, THREATS 1)

One finding per distinct host, `file` and `line` null. Replaces
`tools/extract_urls.py` (removed 2026-10-03; in git history) (rebuilt, not ported).

- Hosts from URLs (`scheme://host`, `git@host:`) and bare domains with a
  recognized TLD (the old extractor's lesson: do not read `script.sh` or
  `file.py` as domains). Lowercase; strip port and `www.`.
- `occurrences`: every `{file, line, where}` with `where` = `instructions`,
  `docs`, or `code` (by the shared rules).
- `where`: counts per kind.
- `documented`: true when the host appears at least once in docs. A host that
  appears only in docs is documented.
- `local`: true for `localhost`, `127.0.0.0/8`, `::1`, `0.0.0.0`, `*.local`,
  `*.localhost`.
- `kind` for context only, never a judgment: `registry` (npm, PyPI, crates,
  GitHub release/raw hosts), `local`, or `other`.

The report counts undocumented hosts over all hosts. REPORTING's "Not" applies:
CDNs and registries are routinely undocumented and routinely benign; the list is
a list to explain.

#### 4. Term table: `term.def`, `term.conflict`, `term.safety` (METHOD, THREATS 14, PHRASES B)

`term.def`: one finding per definition in instruction text. Fields: `term`
(normalized: lowercase, quotes and markdown stripped, trailing punctuation
stripped), `definition` (verbatim), `source` (below).

| `source` | Shape |
|---|---|
| `explicit` | `X means`, `X is defined as`, `by X we mean`, `X refers to` |
| `mapping` | `when the user says X` / `if the user asks for X` followed by what to do |
| `glossary` | `**X**: ...` or `X: ...` list items under a heading containing glossary, definitions, terms, or vocabulary |
| `procedural` | a heading `How to X` or `Steps to X` (the definition is the section's first line, cited at that line; procedures alone never make a conflict; 2026-10-16, review C26) |

`term.conflict`: one finding per term with two or more **different**
definitions (after normalizing whitespace and case), `file` and `line` null.
Fields: `term`, `definitions`: every `{file, line, text}`. Never decide which one
is real (THREATS 14).

`term.safety`: one finding per `term.def` whose term is safety vocabulary: the
word or its inflections of confirm, verify, done, safe, read-only, reversible,
approve, permission, sandbox, allowed (METHOD). Fields: `term`. Always surfaced.

#### Checks (added to CONTRACT)

| Check | One finding per | Fields |
|---|---|---|
| `rubric.action` | J hit in instruction text | `tier`, `action`, `confirmation`, `negated_confirmation`, `confirm_line`, `confirm_quote`, `quote` |
| `endpoint.host` | distinct host (`file`, `line` null) | `host`, `documented`, `local`, `kind`, `where`, `occurrences` |
| `term.def` | definition | `term`, `definition`, `source`, `quote` |
| `term.conflict` | term with different definitions (`file`, `line` null) | `term`, `definitions` |
| `term.safety` | definition of a safety word | `term`, `quote` |

## run

The single entry point for `02.4-phrases`. Gets the file list from `02.1-inventory`, folds and
scans every text file with the pattern table, and prints one contract-1 report
(`stages/CONTRACT.md`).

### Inputs

```
python stages/02-coded/02.4-phrases/run.py <input_dir> [--inventory <file>] [--patterns <file>] [--out <dir>]
                                 [--normalized <dir>]
```

- `--inventory <file>`: a `02.1-inventory` report (JSON) already produced for this input.
- Without it: `stages/_shared/earlier_steps.py` (`inventory`) runs `stages/02-coded/02.1-inventory/run.py <input_dir>` as a subprocess with
  the same Python and parses its stdout (the helper every stage on its own uses, restructure step 7; the step
  it reads is `reads` in `stages.json`), so `02.1-inventory`'s walk rules hold (no
  symlink followed, no `.git/`, git-tracked files only in git mode). A
  non-zero exit or unparseable output fails `02.4-phrases` (exit 1, message on
  stderr, nothing on stdout). `02.1-inventory` code is never imported.
- `--patterns <file>`: a pattern table other than the shipped `Library/patterns.yaml`
  (for tests). A table that fails validation exits 2.
- `--normalized <dir>`: `02.2-reader`'s normalized folder (`<run>/normalized`, 2026-10-18). A file
  `02.1-inventory` found not to be text (PDF, DOCX, an image) whose extracted text `02.2-reader` wrote
  (`<dir>/text/<rel>.txt`: a document's text layer, text drawn on its pages, or an image's OCR)
  is scanned from that text. A folder that does not exist counts as no folder (a run of stages
  1 and 4 only, as `baserates.py` makes).

### Files scanned

Every `inv.file` row that is not a symlink, has a `02.1-inventory` `encoding` (text),
and whose bytes `readtext.decode` reads (`stages/_shared/readtext.py`, `read_row`: the rules, in
order, are the shared module's; the builder step reads text by the same ones). HTML comments, code blocks, and
frontmatter are scanned like any other line (the model receives all of them).
A file that is not scanned (no encoding, undecodable, unreadable, or an
`inv.file` skip) is named on stderr with its reason.

**Extracted text** (with `--normalized`): a binary document or image with a `02.2-reader` text copy
gets the phrase patterns (`scan_text`) over that copy, and nothing else (the part 2 tables,
position, and repetition read text files only). Its findings carry `line` null, `text_line`
(and `end_text_line` for a wrapped hit) for the line in the extracted text, and `extracted`
true. Without `--normalized`, or with no text copy for the file, it is not scanned, as before.
The limit note on stderr says which: `limit: files that do not decode as text (PDF, DOCX,
images) are scanned from the text extracted by the step "What the model actually reads", phrase
patterns only` with the option, the old `... are not scanned` without it. The note reaches
`data/limits.md` and `details.html`, so it names the step by its plain name, not by a number
(restructure step 8b); the report's `glance` still skips the older wording in a run made before.

Audience per file: `audience.audience` (`stages/_shared/audience.py`) with `scripts` from `inv.pin`
`script_languages` and `hook_configs` from `inv.file` `entry_point`
`hook-config` plus every file carrying a `struct.hooks` finding (`audience.inventory_sets`).

### Outputs

stdout: `{"stage": "02.4-phrases", "contract": 1, "terms": {...}, "findings": [...]}`
(`terms`: the version of the search terms and matching code, `termset.describe`, added
2026-10-19, review C22 b); first the
part 1 findings from `scan.scan_text`, ordered by file path, then line, then
check; then the part 2 findings ("The stage", part 2), in CONTRACT order (part 1
findings are never changed by part 2): `rubric.action` (`rubric.rubric_file`),
`endpoint.host` (`endpoints.census`), `term.def` (`terms.defs_file`), `term.conflict`
(`terms.conflicts`), `term.safety` (`terms.safety`); line-based ones ordered
by file then line.

`02.4-phrases` ends with these. The checks for builders (`need.*`, `port.*`, `host.*`, `trig.*`, `ask.*`,
`fit.loop`, `clean.*`) that followed them until restructure step 4 are `02.6-builder`'s; `hits.json`
and the finding count on stderr no longer include them. The mask on a line a secret sits on
(`secret.found`) is `stages/_shared/secretmask.py`, used here and by that step; the steps that run before this one keep words from
lines too, and the runner masks those once the last step that reads them has run.

Part 2 inputs per scanned file: the original lines, their folded copies
(`foldtext.fold_line`), and the set of **instruction lines**: every line of a
file whose audience is `model` or `subagent`, plus the frontmatter lines
(`scan.frontmatter_lines`) of a markdown file (`.md`, `.markdown`, `.mdc`) of
any audience, since frontmatter is loaded. Each endpoint occurrence's `where`
is `instructions` for an instruction line, else `docs` for a `human` file and
`code` for a `tool` file. The word lists come from `vocab.load_vocab`, checked
against the loaded pattern table; a bad vocab file exits 2.

stderr: the limit, always: how files that do not decode as text were handled (scanned from
`02.2-reader`'s extracted text with `--normalized`, else not scanned); plus one line per file not
scanned; plus a count of findings, with the part 2 counts. Every part 2 item is built
(position and repetition and the secret scan since 2026-10-04), so none is named as not built.

`--out <dir>`: also writes `<dir>/hits.json`: `undone_by_next_line` (line hits the next line
of their paragraph cancelled, `scan.undone_by_next_line`, added 2026-10-20), `findings` (as stdout),
`counts` (`per_check`: part 1 findings per phrase check, every check listed,
zeros included; `per_pattern`: part 1 findings per pattern id, every id listed,
zeros included; `part2`: `rubric` (`rows`, `with_confirmation`,
`without_confirmation`, `negated_confirmation`, `by_tier`), `endpoints`
(`hosts`, `undocumented`, `local`, `by_kind`), `terms` (`definitions`, `by_source`,
`conflicts`, `safety`)), `scanned` (file count), `not_scanned` (`file`,
`reason`), and `limits` (the stderr notes). The folder is created if needed. An `--out`
inside `<input_dir>` is refused (exit 2).

Exit 0 when a report was produced, including zero findings. Exit 2 for a
missing or non-folder input, an unreadable `--inventory`, a bad `--patterns`,
or a refused `--out`. Exit 1 when `02.1-inventory` fails.

### Must never

- Print anything but the report to stdout.
- Write inside `<input_dir>`; write anywhere without `--out`.
- Import another stage's code, run anything from the input, fetch a URL, or
  follow a symlink.
- Say whether a hit is a problem, score, rank, or drop a hit.

### Done when (each backed by a test in `tests/test_run.py`)

1. On a small tree, stdout parses as a contract-1 report with stage `02.4-phrases`, exit 0, and every phrase finding has `check`, `file`, `line`, `quote`, `patterns`, `audience`, `folded`.
2. Findings carry the audience of their file (`README.md` human, `agents/x.md` subagent, a script tool, `SKILL.md` model).
3. `--inventory` with a saved `02.1-inventory` report gives the same findings as the subprocess path.
4. `--out` writes `hits.json` with per-check and per-pattern counts (zeros included) that agree with the findings; `--out` inside the input is refused.
5. A binary file with no `02.2-reader` text copy is not scanned and is named on stderr; stderr names none of the part 2 items (all built) as not built.
6. A missing input folder exits non-zero with nothing on stdout; the input is byte-identical after a run.
7. A zero-finding tree still gives a valid report and exit 0.
8. Part 2 findings follow every part 1 finding, in CONTRACT order, and part 1 findings are identical to a run without part 2 (same phrase findings as the pattern scan alone).
9. On a small tree: a confirm-first line in `SKILL.md` gives a `rubric.action`; the same verb in a script gives none; a host in `SKILL.md` and `README.md` is documented, a host in `SKILL.md` and a script only is not; a definition in `SKILL.md` gives a `term.def`, and the same line in the body of `README.md` gives none; a frontmatter line of `README.md` counts as instruction text (a definition there gives one).
10. `--out` writes the `part2` counts, and they agree with the part 2 findings.
11. With `--normalized`, a PDF (no `02.1-inventory` encoding) whose text copy holds an override phrase gives a phrase finding with `line` null, `text_line`, and `extracted`; it is counted as scanned and is not named as not scanned; the limit note says extracted text is scanned. Without `--normalized` the same PDF is not scanned, with the old note.

Pattern lists (`.gitignore`, `.gitattributes`, other ignore files, `CODEOWNERS`,
`.gitmodules`, `.mailmap`) are not scanned (reason `pattern list (not instruction
text)`), as `02.3-graph` already skips them (added 2026-09-30).

### What the step looked at (added 2026-10-30, M9 slice C)

The report's `coverage` list (`stages/CONTRACT.md`, "Coverage lines") has eight lines. `of` for the checks that read text is
counted in `build_report` before the loop, from the inventory (`readtext.text_candidate`: a file the inventory found to be text that
is no pattern list) and each check's own scope. The files the loop reads do not make that count, so a file the loop cannot read or
leaves out is still counted.

| Checks | Unit | `of` (counted from the inputs, before the check) | `looked_at` (counted where the check reads an item) | `explained` |
|---|---|---|---|---|
| the fourteen `phrase.*` checks | `files` | every file the inventory lists | `phrase_scan`, which runs the pattern table on a file's text: a text file's, or the extracted text of a PDF, a DOCX, or an image | the files with a "not scanned" entry (`hits.json`'s `not_scanned`, and the note `not scanned: <file>: <reason>`): not text, a pattern list, a symlink, unreadable, undecodable |
| `rubric.action` | `files` | the files with instruction lines: those of a model's file (all lines) and the frontmatter of a Markdown file, counted in the loop once a file's text is in hand (`instruction_lines`) | `text_checks`, once the rubric has run on the file | a candidate that could not be read and could have had them (`reads_rubric`) |
| `endpoint.host`, `term.def`, `limit.setting` | `files` | the text candidates | `text_checks`, once the hosts, the terms, and the limit settings have run on a file | a candidate the loop could not read (its "not scanned" entry) |
| `term.conflict` | `entries` | the definitions `term.def` found | `terms.conflicts`, once for each definition it sets against the others of its term | none |
| `term.safety` | `entries` | the same definitions | `terms.safety`, once for each definition whose term it sets against the safety words | none |
| `pos.density` | `files` | the text candidates a model reads (`position.reads_density`: audience model or subagent) | `position.density`, once for each file it places; the reader window is a threshold and no scope | a candidate of that audience the loop could not read |
| `rep.sentence` | `files` | the text candidates a model reads that are prose (`position.reads_repetition`) | `position.repetition`, once for each file it goes through | a candidate of that kind the loop could not read |
| `secret.found` | `files` | the text candidates and the pattern lists (`readtext.pattern_list`), less lock files (`secret_scan.scannable`) | `secret_scan._shapes`, once for each file whose lines it reads in our own process and a scanner did not skip | a file that cannot be read or decoded (a skip finding in Walkdown's words: `the secret scan could not scan this file`), a file detect-secrets raised on or never asked for the text of (the same skip), and every file when no scanner is installed (the skip finding that already exists) |

The pattern table has rows with audiences of their own (`Library/patterns.yaml`), which the line of the fourteen checks does not split:
it counts the files the table is run on, and each row applies where its audiences say.

The scanner (detect-secrets) is external: it takes one file at a
time and says nothing of a file it passes over, so it does not count the files. The pass that reads each file in the step's own process
counts it, and a file a scanner could not scan is explained and not looked at. The skip finding never holds the error's text (it can hold words from the
repository). A file left out of a pass with no entry for it leaves its line short, and the check of the run holds the run. The
tests are in `tests/test_coverage.py`, one for each line that makes the pass leave a file out, one that runs the step's `main`, one
with no secret scanner installed, and one each for a file a scanner and the shape pass cannot scan.

### History

- 2026-10-30: M9 slice C: the report has a `coverage` list (above, "What the step looked at"). The loop's per-file work is four named functions in `run.py` (`phrase_scan`, `text_checks`, `position_checks`, and the secret scan's own count) so that a file a check passes over can be counted where the check handles it; the findings are unchanged. `terms.code` moves, as the brief says it will: the version of the matching code hashes every script in this folder (`run.py` and `secret_scan.py` changed) and every shared module they import (`coverlines.py` is new among them, and `stagelist.py` changed); the matching did not change.
- 2026-10-29: restructure step 6 (keep-or-cut, Q8): the conditional table (`cond.branch`, with its
  `conditionals` count in `part2`) is cut; it reached `full.md` only. Nothing in stage 4 reads its
  word lists any more.
- 2026-10-29: restructure step 8b: the extracted-text limit note names the reader step by its plain name
  (it said "stage 2's extracted text"); `test_binary_not_scanned_and_limits` no longer asserts that the cut
  conditional table is absent from the notes. The note is in `hits.json` and `02.4-phrases.notes.txt`, and
  `terms.code` moves with this file.
- 2026-10-31: M9 slice C, fix round: `pos.density`, `rep.sentence`, `term.conflict`, and `term.safety` are lines of their own, each counted where its check handles an item (`position_checks` is gone: the two position functions are called from `build_report`). `of` for the text lines is counted before the loop, from the inventory. The secret scan counts a file in its shape pass, and a file it cannot scan is a skip finding in Walkdown's words and is explained. The findings are unchanged except that an unreadable file now has a `secret.found` skip.
- 2026-10-31: M9 slice C, last fix round: `pos.density` and `rep.sentence` count the files a model reads (they counted every text file), and `rubric.action` is a line of its own for the files with instruction lines (it shared a line with the checks that read every line of every text file). The findings are unchanged.

## endpoints

The endpoint census ("The stage", part 2, section 2, REPORTING 4.1, THREATS 1): every
network host named anywhere in the scanned text, where it is named, and whether
the documentation names it. Replaces `tools/extract_urls.py` (removed 2026-10-03; in git history) (rebuilt from this
spec, not ported). Text only: no lookup, no DNS, no HTTP.

### Inputs

- A folded line (`hosts_in_line`), or the occurrences of a whole run (`census`).
- `vocab`: `vocab.load_vocab()` (schemes, TLDs, registry and local hosts).

### Rules

`hosts_in_line(folded, vocab) -> list[str]`, distinct, in order of first appearance:

- URLs: `<scheme>://[user@]host[:port]` for a scheme in `vocab.schemes`, and
  `git@host:`. The host is a dotted name, `localhost`, an IPv4 address, or a
  bracketed IPv6 address. A host holding template characters (`$`, `{`, `<`,
  `%`), or a single label other than `localhost` (`http://host:port`), is a
  placeholder and is skipped.
- Bare domains outside any URL: two or more labels ending in a TLD from
  `vocab.tlds`, not preceded by a word character, `.`, `-`, or `/`, and not
  followed by a further label, a word character, or `(` (a method call such as
  `logger.info(` is code, not a host). File names (`script.sh`, `SKILL.md`,
  `summary.json`) never count because those extensions are not in the TLD list.
- Bare `localhost` with a port (`localhost:3000`), and a bare IPv4 address with
  a port, count as hosts.
- Hosts are lowercased; a trailing dot, the port, and a leading `www.` are removed.

`addresses_in_line(folded, vocab) -> list[(host, address)]` (added 2026-10-16, for the report's
outside-links list): the same hosts in the same order, each with the whole text that names it,
from the scheme (or `git@`, `localhost:`, or the bare name) to the end of its path, as written.
Trailing sentence punctuation (`.,;:!?*'"`) and closing brackets with no opening partner (a
Markdown link's `)`) are dropped; `[` and `]` end an address (a Markdown link's `](`). A bare name
or `host:port` runs on only into a path (`/`). A bare address that is the visible text of a full
address for the same host on the same line (`[x.io](https://x.io)`) is not listed again.
`hosts_in_line` is its distinct hosts.

`is_local(host, vocab)`: `localhost`, `::1`, `0.0.0.0`, any `127.x.x.x`, and
names ending `.local` or `.localhost`.

`census(occurrences, vocab) -> list[dict]` where each occurrence is
`(host, file, line, where)` or `(host, file, line, where, address)` and `where` is `instructions`, `docs`, or `code`:
one finding per distinct host, ordered by host:
`{check: "endpoint.host", file: null, line: null, host, documented, local,
kind, where, occurrences}`:

- `occurrences`: every `{file, line, where}`, one per line naming the host,
  ordered by file then line. A row gains `urls`, the distinct addresses named on that line
  in order, when its occurrences carried any (`02.4-phrases` always passes them).
- `where`: `{instructions: n, docs: n, code: n}` counting those occurrences.
- `documented`: true when at least one occurrence is `docs`.
- `local`: `is_local`.
- `kind`: `local` when local, `registry` when the host is in `vocab.registry`,
  else `other`. Context only.

`lookalikes(raw) -> dict`: for a raw line (before folding), `{the host a name folds to: the
name as written}` for each dotted name written with non-ASCII letters that folds to an ASCII
host, unless the line also names that host as itself (2026-10-25, review C42, an outside tester: the census ran on folded lines, so `gіthub.com` with a Cyrillic `і` was listed as
`github.com`). `02.4-phrases` lists such a name as written, and its addresses with it; `census(...,
lookalike)` takes `{name as written: the host it imitates}` and gives that row `lookalike_of`
and `punycode` (the IDNA form, `xn--...`, or null when it has none). A look-alike is never
`registry` or `local`.

`summary(findings) -> dict`: `hosts`, `undocumented`, `local`, and `by_kind`.

### Done when, look-alike hosts (tests in `tests/test_endpoints.py`)

- A Cyrillic `і` in `gіthub.com` gives `{"github.com": "gіthub.com"}`; an ASCII line gives
  nothing; a line naming the real host as well gives nothing; the census row of the look-alike
  carries `lookalike_of: github.com` and a `punycode` starting `xn--`, kind `other`
  (`test_lookalike_hosts_are_listed_as_written`). Fixture rows `c42-lookalike-host`,
  `c42-real-host-not-lookalike` (`class11-encoded.md`).

### Must never

- Fetch, resolve, or look anything up.
- Read a script or file name as a domain.
- Call a host good, bad, suspicious, or benign.

### Done when (each backed by a test in `tests/test_endpoints.py`)

1. `https://Www.Api.Example.invalid:8443/x` gives `api.example.invalid`; `git@github.com:o/r.git` gives `github.com`.
2. `run scripts/post.sh and read SKILL.md, then summary.json` gives no host; `logger.info("x")` gives no host; `see docs.example.com for more` gives `docs.example.com`.
3. `https://${HOST}/api`, `https://<your-domain>/`, and `http://host:8080/` give no host.
4. `http://localhost:3000`, `127.0.0.1:8080`, and `printer.local` are local with kind `local`; `registry.npmjs.org` has kind `registry`.
5. A host named in docs and in instructions is documented; a host named only in instructions and code is not; a host named only in docs is documented; `where` counts agree with `occurrences`.
6. Two mentions on one line give one occurrence.
7. Addresses are whole and trimmed: a Markdown link's `)` and a full stop are dropped, a
   balanced `(...)` in a path is kept, a `git@` remote and a bare name with a path are whole,
   a placeholder host gives no address; the hosts are those of `hosts_in_line`; a Markdown link
   gives one address, ending at `](`.
8. A census row lists its line's distinct addresses as `urls`; a row given none has no `urls`.

## foldtext

The folded copy `02.4-phrases` greps. (The text decoder and `split_lines` moved to
`stages/_shared/readtext.py` in restructure step 4: the builder step reads text by the same rules.) A reimplementation of
`02.2-reader`'s fold (`stages/02-coded/02.2-reader/specs/reader.SPEC.md`, section `fold`); `02.4-phrases` never imports
`02.2-reader` ("The stage", "What is scanned"). Named `foldtext` rather than `fold` because the
stages share one pytest session and `02.2-reader` already has a module `fold`.

### Inputs

One line of decoded text (no line ending).

### Outputs

`fold_line(line) -> str`, in this order:

0. A run of variation selectors (two or more characters with action `run` in `Library/invisible.yaml`,
   in a row or with only stripped characters between them, `library.runs`), found on the line as it is
   written. If its selectors' bytes spell text (U+FE00-U+FE0F are the bytes 0 to 15, U+E0100-U+E01EF
   are 16 to 255; UTF-8 of printable characters with a word of two letters or more,
   `library.run_text`), the selectors become that text with a space on each side, as a tag run does
   (P1, 2026-10-29; white space inside it is one space, so the line stays one line). The text is read
   from the byte selectors alone (a Mongolian selector among them is skipped and hides nothing). A
   run that spells nothing, and a run of Mongolian selectors only, loses its selectors and leaves
   nothing. The characters between the selectors stay where they are for the steps below
   (so a tag run among them is read). One selector alone stays, as it is ordinary after an emoji or a
   CJK character, even with a stripped character after it.
0b. A run of Unicode tag characters U+E0020-U+E007E becomes the ASCII it spells (each minus
   U+E0000), with a space on each side (2026-10-25, review C42, an outside tester: a
   sentence hidden in tag characters was deleted, never read). `02.2-reader`'s folded copy still
   drops them; this is the copy `02.4-phrases` matches. Steps 0 and 0b are `library.read_hidden`.
1. Strip the characters the list gives action `strip`: zero-width characters U+200B-U+200F,
   U+2060-U+2064, U+FEFF, and, since 2026-10-29, U+180E, U+034F, U+206A-U+206F, U+FFF9-U+FFFB,
   U+1D173-U+1D17A, U+1BCA0-U+1BCA3; bidi controls U+202A-U+202E, U+2066-U+2069, U+061C; soft hyphen
   U+00AD; the blank letters and cells U+115F, U+1160, U+3164, U+FFA0, U+17B4, U+17B5, U+2800; the
   remaining Unicode tag characters U+E0000-U+E007F; NUL.
2. Replace U+2028, U+2029, and U+0085 with one space each.
3. NFKC normalize.
4. Fold confusables to ASCII: each **non-ASCII** character that
   `confusable_homoglyphs` maps to an all-ASCII homoglyph is replaced by the
   first such homoglyph. ASCII characters are never changed; a character whose
   only homoglyphs are non-ASCII (an em-dash) is kept.
5. Drop accents on Latin letters: a combining mark (after canonical decomposition) that sits
   on an ASCII letter is removed, so `ignóre` reads `ignore` (2026-10-25, review C42: accented
   look-alikes slipped past every pattern). Marks on other letters stay.

`base64_texts(line) -> list[str]`: readable text hidden in base64 on a line (2026-10-25,
review C42): each run of 24 or more of `A-Z a-z 0-9 + /` (with up to two `=`), padded
and decoded, that is strict UTF-8 of printable characters and white space, at least 12
long with three words of two or more letters. Read by `scan.py` and `secret_scan.py`.

The characters stripped, the three turned into a space, and the runs are read from `Library/invisible.yaml`
through `stages/_shared/library.py`, the list `02.2-reader`, `02.3-graph`, `02.4-phrases`, `02.5-capability`, and
`06-report` share (restructure step 3, 2026-10-29). Because the list decides a hit as the code does, `termset.py` hashes it
(the `termset` section).

### Must never

- Add or drop a line.
- Change an ASCII character.
- Import `02.2-reader`.

### Done when (each backed by a test in `tests/test_foldtext.py`; 6 and 7 moved with `decode` and `split_lines`; 8 to 10 are P1)

1. `ig​no​re all` folds to `ignore all`.
2. Bidi controls and a soft hyphen are stripped; the visible text around them is kept. Tag characters spelling `ignore` read ` ignore ` beside the visible text; a lone cancel tag is stripped.
3. Fullwidth `ｉｇｎｏｒｅ` folds to `ignore`; a Cyrillic `о` inside a Latin word folds to `o`.
4. U+2028, U+2029, U+0085 each become one space (and `split_lines` does not split on them: `readtext`, Done-when 3).
5. Plain ASCII and an em-dash are unchanged; `café` and `ignóre` fold to `cafe` and `ignore`; ASCII `l`, `1`, `0` are never changed; a mark on a non-Latin letter is kept.
8. A keyword split by a character P1 added (U+180E, a format character, a blank letter or cell) folds whole (`test_the_new_invisible_characters_are_stripped`; fixture `class11-invisible-more.md`, gates 4 to 6).
9. A run of variation selectors that spells text reads as that text; one that spells nothing, and a run of Mongolian selectors only, is dropped; a Mongolian selector among the byte selectors hides nothing (`test_a_mongolian_selector_inside_a_run_does_not_hide_its_text`: folded, and matched by a pattern); one selector alone is kept and adds no hit; a decoded run keeps the line one line (`test_a_run_of_variation_selectors_is_read_as_the_text_it_spells`, `test_a_decoded_run_keeps_the_line_one_line`; fixture line 7 and negatives 10 and 11).
10. Selectors with zero-width spaces (or any stripped character) between them are one run: the text they spell is read from the selectors alone, a tag run among them is read too, and one selector followed by a zero-width space and an ordinary letter is not a run (`test_a_run_interleaved_with_stripped_characters_is_still_read`, `test_one_selector_before_a_stripped_character_is_not_a_run`).

### NUL (2026-10-09)

`fold_line` strips NUL (U+0000) like the other invisible characters, so a NUL inside a word does not split a phrase (fixture `class11-nul-split.md`). (`decode`'s NUL rule is `readtext`'s.)
11. A tag character between the selectors of a run reads as one word, as in `02.2-reader`'s `decoded` (`test_tag_characters_between_selectors_read_as_one_word_as_in_the_reader`).

### History

- 2026-10-29 (P1): the list gained the characters of an outside note (2026-10-28) and its measurement the
  same day, and the `run` action; `foldtext.py` strips them from the list and reads a variation-selector
  run that spells text as that text, as it reads a tag run (review C42), dropping one that spells nothing.
- 2026-10-29 (P1, review before verification): a run is selectors in a row or separated only by
  characters the list strips, and it is found before the tag run is read. A zero-width space between
  two selectors had ended the run, so an instruction spelled by selectors with zero-width spaces
  between them was never read. The text is read from the selectors alone; what stands between them
  stays for the strip and the tag rule.
- 2026-10-29 (P1, after verification): the text of a run is decoded from its byte selectors alone, so
  one Mongolian selector inside a run no longer hides the instruction it spells (the run was dropped).
- 2026-11-01: the tag rule moved to `library.read_hidden`, which `02.5-capability` reads through as well; what a line reads as did not change.

## negation

Prohibitions (review C25, 2026-10-16; the partner's audit of Compound Engineering, v1 and v3): a
line that forbids the matched action ("Never have the user paste an API key into chat") hit
`J.enter-secret` exactly like an instruction to do it, and the rubric then called it "an
irreversible or prohibited action with no confirmation step". A hit is never dropped for this. It
is tagged, so the report can say the action is stated as a prohibition (soft D5's rule, mark and
never demote, applied to a fixed rule). Text only; no model.

### Rules

`negation(folded, start) -> {"word", "carve_out"} | None`, for the action that starts at `start`
on a folded line:

- **A forbidding word** (`NEG`): never, do not, don't, must not, mustn't, should not, shouldn't,
  may not, not allowed to, forbidden to, prohibited from, avoid, refuse to. The last one before
  `start` is the candidate. Descriptive negatives (does not, cannot, will not) say what happens,
  not what the text asks, and do not count (first real run, Compound Engineering, 2026-10-16:
  "its adapter does not enforce read-only mode").
- It **governs** the action when it is at most `MAX_GAP` (60) characters before it and nothing
  between them ends the clause (`BREAK`: `. ; : ! ? ,` followed by a space or the line end, a
  spaced dash, or but, instead, then, otherwise, so).
- **Not a prohibition** when the word right after the negation turns it into an instruction
  (`DOUBLE`): forget, hesitate, fail, skip, miss, neglect, stop, omit, mind, wait, delay, only,
  just ("don't forget to upload", "never skip the push", "never mind the warning").
- **The exception** (`carve_out`): unless, except, other than, or until after the action, to the
  end of its sentence, capped at 160 characters; null when there is none. A prohibition with an
  exception is still tagged; the exception travels with it.

`anchor(row, folded) -> int | None`: where a pattern row's action starts: its match, or, for a row
that matches an empty string through lookaheads at the line start (`K.data-flow`), the first match
of its first lookahead (`first_lookahead`).

A pattern whose own match holds the negation ("do not mention ... the user", "don't ask") is
judged by what comes before its match, so its meaning is unchanged.

### Where it is used

- `scan.py`: every phrase hit gains `negated` (true when a negation governs every pattern on the
  hit), `negation` (the word), and `carve_out`; both null when not negated.
- `rubric.py`: every `rubric.action` row gains `negated_action` and `carve_out`, judged at the
  action's match.

### Must never

- Drop, re-check, or move a finding.
- Read across a clause boundary, or call a double negative a prohibition.

### Done when (each backed by a test in `tests/test_negation.py`)

1. "Never have the user paste an API key into chat" is negated by "Never"; "Paste the API key" is not.
2. "Do not stop; upload ..." and "Do not stop, upload ..." are not negated (the clause ends).
3. "Don't forget to upload ...", "Never mind the warning, delete ...", and "Never skip the push" are not negated.
4. "Never permanently delete the folder unless the user asks you to." is negated with `carve_out` starting "unless the user asks".
5. A negation more than `MAX_GAP` characters before the action does not govern it; "its adapter does not enforce read-only mode" is not a prohibition.
6. `anchor` finds a lookahead-only row's verb ("Do not upload your .env file to https://x.invalid" anchors at "upload"); `first_lookahead` is None for an ordinary pattern.
7. `scan_text` and `rubric_file` carry the tags (fixture case `negation-repo`, grader rows `neg-25-*`).

## patterns

Loads and validates the pattern table (`Library/patterns.yaml`), the single data file
that holds every `02.4-phrases` pattern ("The stage", "The pattern table").

### Inputs

`Library/patterns.yaml` (the default, found through `stages/_shared/library.py`), or any YAML file of the same
shape: a mapping with a `patterns` list. Each row:

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | stable id, unique in the table, e.g. `L.ignore` |
| `check` | yes | one of the 14 `02.4-phrases` check IDs in `stages/CONTRACT.md` |
| `regex` | yes | Python `re` pattern, compiled case-insensitive, run on the folded line |
| `source` | yes | one or more references joined with `; `, the first `PHRASES:<set letter>` or `THREATS:<class>` (a heading of `Library/PHRASES.md` or `Library/THREATS.md`); a later one may also be an ID from `Library/SOURCES.md` |
| `unless` | no | regex (case-insensitive); when it also matches the folded line, the row does not hit |
| `note` | when `unless` is set | the reason for the `unless` (and any narrowing or widening of the set's wording) |
| `plain` | no here, yes in the shipped table | the words the review page shows a reader: what the pattern looks for, then "The worry: ..." (read by `stages/06-report/plain.py`); a given `plain` must be a non-empty string |
| `audiences` | no | list of audiences (`model`, `subagent`, `human`, `tool`); the row only runs on files with one of them |
| `paths` | no | regex (case-insensitive) on the file's relative path; the row only runs on matching files |
| `where` | no | `frontmatter`: the row only runs on lines inside a leading YAML frontmatter block |

Case-sensitive parts of a pattern use the scoped flag `(?-i:...)` (for
example upper-case identifier names such as `API_KEY`).

### Outputs

`load_table(path=None) -> list[Row]`, rows in file order. `Row` carries every
field above plus `rx` and `unless_rx` (compiled) and:

- `row.applies(rel, audience, in_frontmatter) -> bool`: the `audiences`,
  `paths`, and `where` restrictions hold for this line's file and position.
- `row.hits(text) -> bool`: `rx` matches `text` and `unless_rx` (if any) does
  not.

`CHECKS`: the 14 check IDs in CONTRACT order.

`TableError` is raised, naming the row, for: a missing required field; a
duplicate `id`; a `check` not in `CHECKS`; a `source` not starting `PHRASES:`
or `THREATS:`; a regex or `unless` that does not compile; an `unless` without a
`note`; an unknown audience or `where` value; a `plain` that is empty or not text;
an unknown field.

### Must never

- Decide anything about a hit. It only says whether a row matched.
- Hold patterns in code: every pattern lives in the YAML file.

### Done when (each backed by a test in `tests/test_patterns.py`)

1. The shipped `Library/patterns.yaml` loads: every row names a valid check, a source, and its plain words (with "The worry: "), every regex and `unless` compiles, ids are unique, and every one of the 14 checks has at least one row.
2. Each malformed table above raises `TableError`.
3. Matching is case-insensitive; `(?-i:...)` parts stay case-sensitive.
4. An `unless` that matches cancels the hit; one that does not leaves it.
5. `audiences`, `paths`, and `where: frontmatter` restrict where a row applies.
6. The shipped table catches a known positive for every one of the 14 checks, in wording of its own (never a fixture sentence), including a folded one; every narrowed row (`unless`, or a note naming a narrowing) misses its benign shape and still hits its class (`tests/test_table.py`).

### History

- 2026-10-29: restructure step 3b: `plain` is a row field (the plain words moved here from
  `stages/05-report/plain.py`, which now reads them), and `source` holds references to
  `Library/PHRASES.md`, `Library/THREATS.md`, and `Library/SOURCES.md` instead of prose naming a row or
  bullet of the private documents. `patterns.py` allows `plain` (a non-empty string when given) and
  keeps the check that a source starts `PHRASES:` or `THREATS:`; no field that decides a hit changed.

## position

Added 2026-10-04.

Instruction position and repetition, REPORTING 4.4 and 4.5. "Instruction-shaped" here means
a line a `02.4-phrases` phrase pattern flagged in a file a model or subagent reads (path audience).

### Inputs

`texts`: `{rel: (audience, raw lines, bytes)}` for every scanned file; the `02.4-phrases` phrase
findings.

### Outputs

- `density(texts, findings)`: one `pos.density` per model or subagent file over the reader
  window (more than `READER_LINES` 2,000 lines or `READER_BYTES` 50,000 bytes, the published
  thresholds) that has phrase hits: `lines`; `first10`, `middle80`, `last10` (flagged lines in
  the first and last 10% of lines, rounded up, and the rest); `window_line` (the last line
  inside the window by lines or bytes, whichever comes first); `beyond_window` and
  `beyond_lines` (flagged lines after it, at most 20 listed).
- `sentences(lines)`: (line, sentence, normalized key) for sentences of `MIN_WORDS` (6) or
  more words, outside a leading YAML frontmatter block and code fences, with list, heading,
  quote, and table markers stripped; the key is the lowercased words.
- `repetition(texts, findings)`: one `rep.sentence` per sentence whose key appears in two or
  more prose files (`.md`, `.mdc`, `.markdown`, `.txt`) a model or subagent reads: `file` and
  `line` of the first occurrence, `sentence` (at most 240 characters), `files`, `count`,
  `where` (at most 20), `patterns` (`02.4-phrases` pattern ids on any occurring line). Sentences that
  repeat at exactly the same places are one finding, their text joined.

### Must never

- Judge: a checklist at the end of a skill and shared boilerplate are normal (REPORTING "Not").
- Count human-facing files, test data, scripts, or configuration lines.

### Done when (each backed by a test)

1. Density only for long model-read files with hits; segments, window line, and lines past it
   (`tests/test_position.py`).
2. The window ends at the byte limit when it comes first (`tests/test_position.py`).
3. Sentences skip frontmatter, fences, and short ones (`tests/test_position.py`).
4. Repetition across prose files with patterns; human, test, and config files never count
   (`tests/test_position.py`; fixture `position-repo` gates and negatives).

## restrictions

Settings that restrict what tools an agent can use (review C32, partner's v3, 2026-10-14; built
2026-10-17). A part 2 table: facts for `02.5-capability` to pair with read-only wording. A restriction is
never a risk and never flagged on its own.

### Inputs

`settings_in_line(line)`: one folded line. `limit_file(rel, raw, folded, aud)`: a file's raw and
folded lines and its audience (any audience; consumers filter).

### Outputs

One `limit.setting` finding per setting a line names, with `file`, `line`, `quote` (the raw line),
`audience`, and:

| `kind` | Recognized as | Extra field | `rules_out` | `grants_write` |
|---|---|---|---|---|
| `tools-flag` | `--tools` with a quoted (possibly empty) or bare list of tool names | `tools` | `write` when the list has no writing tool (Write, Edit, MultiEdit, NotebookEdit) and no Bash; `shell` when it has no Bash; `network` when it has no WebFetch, WebSearch, or Bash; nothing when it has `*` | True when the list has a writing tool, Bash, or `*` |
| `deny` | `--disallowedTools` (or `--disallowed-tools`) with a list, or a JSON `"deny": [ ... ]` list on one line | `tools` | `write` when every writing tool and Bash are denied; `shell` when Bash is; `network` when WebFetch, WebSearch, and Bash are. A scoped deny such as `Bash(git push:*)` denies one use, not the tool | False |
| `sandbox` | `--sandbox <mode>` or `sandbox_mode = "<mode>"` (read-only, workspace-write, danger-full-access) | `value` | `write` for read-only | True for workspace-write and danger-full-access |
| `permission-mode` | `--permission-mode <mode>` or `defaultMode` (plan, default, acceptEdits, bypassPermissions, dontAsk) | `value` | `write` and `shell` for plan | True for acceptEdits and bypassPermissions |

A list is a tool list only when every item reads as a tool name (`Read`, `Bash(git diff:*)`,
`mcp__server__tool`, `*`); "the `--tools` section" is not a setting. A bare list stops at a quote,
a space, or a backtick, so a flag inside Markdown code reads the same as in a script.

### Must never

- Count `--allowedTools` as a restriction: it pre-approves the tools it names and leaves every
  other tool available.
- Judge a setting, or report one as a risk.

### Done when (each backed by a test in `tests/test_restrictions.py`)

1. `--tools "Read,Grep,Glob"` rules out write, shell, and network and grants no write; `--tools
   Read,Bash` rules out nothing and grants write; `--tools ""` rules out all three.
2. `--disallowedTools "Write,Edit,MultiEdit,NotebookEdit,Bash"` rules out write and shell; a JSON
   deny list with only `Bash(git push:*)` rules out nothing.
3. `--sandbox read-only` rules out write; `--sandbox danger-full-access` grants write;
   `--permission-mode plan` rules out write and shell.
4. `--allowedTools "Read,Grep"` and "the `--tools` section of the docs" are not settings; a list in
   backticks is read without the backtick.
5. The grader's `p2-lim-*` rows in `Fixtures/ANSWERS/02.4-phrases.json` pass.

## rubric

The harness rubric ("The stage", part 2, section 1, THREATS 22, PHRASES J): for every
`phrase.J.prohibited` action in instruction text, its harness tier and whether
a confirmation step sits in the same step. A table to read, never a verdict.

### Inputs

- `rel`, `raw` (original lines), `folded` (the same lines folded), `instr`
  (set of 1-based line numbers that are instruction text), `audience`.
- `rows`: the pattern table; only `phrase.J.prohibited` rows are used.
- `vocab`: `vocab.load_vocab()`.

### Rules

- A line is a rubric line when it is instruction text and a J row hits its
  folded copy. Rows of the `ignore_unless_tier` tier (confirm-first) are run
  **without** their `unless`: that `unless` is part 1's same-line stand-in for
  a confirmation step, and the rubric measures the step itself. Prohibited-tier
  rows keep their `unless`. So every part 1 J hit in instruction text is a
  rubric line, plus confirm-first lines part 1 cancelled.
- One finding per rubric line. `tier` is `prohibited` if any prohibited row
  hits, else `confirm-first`; `action` is the text the first hitting row of that
  tier matched, taken from the original line when the line did not change on
  folding (else from the folded line); `patterns` lists every hitting J row.
- **The step** (`step_span(lines, n)`): if line `n` is a markdown list item
  (`-`, `*`, `+`, or `1.` / `1)` marker) or an indented continuation of one,
  the step is that item: the marker line plus the following non-blank lines
  indented deeper than the marker. Otherwise the paragraph: the run of
  consecutive non-blank lines around `n`, stopped by a heading, a list item,
  or a code fence line.
- A confirmation is a match of any `confirm` regex on a folded line of the
  step. It is negated when the text just before it matches `neg_before`
  ("without asking", "no need to confirm", "do not ask") or the text just after
  it matches `neg_after` ("confirmation is not required"). A match of
  `neg_forms` ("without asking", "no need to confirm", "do not ask") is a
  negated confirmation too.
- `confirmation` true when the step holds a non-negated confirmation;
  `confirm_line` and `confirm_quote` (the original line) name the first one,
  searching the action line first, then the step in line order.
  `negated_confirmation` true when the step holds a confirmation and every one
  is negated. When `confirmation` is false, `confirm_line` and `confirm_quote`
  are null.

### Outputs

`rubric_file(rel, raw, folded, instr, audience, rows, vocab) -> list[dict]`:
findings `{check: "rubric.action", file, line, quote, audience, tier, action,
patterns, confirmation, negated_confirmation, confirm_line, confirm_quote}`
in line order.

### Must never

- Say whether an action is acceptable; `confirmation: false` is a fact, not a finding of fault.
- Emit a row for a line outside instruction text (a `POST` in a script is code).
- Change or drop a part 1 finding.

### Done when (each backed by a test in `tests/test_rubric.py`)

1. A confirm-first verb alone in its paragraph gives `confirmation: false`, `tier: confirm-first`.
2. A verb with "ask the user to confirm" on the same line gives a row (though part 1 cancels it) with `confirmation: true` and `confirm_line` that line.
3. A list item whose indented continuation line says "Wait for the user's approval" gives `confirmation: true` with `confirm_line` the continuation line; the next list item is a different step.
4. "Send it without asking" gives `confirmation: false`, `negated_confirmation: true`.
5. A prohibited row hit ("permanently delete") gives `tier: prohibited`.
6. A line outside `instr` gives no row.
7. `step_span` covers a list item with continuation, a paragraph, and stops at a heading.

### Added 2026-09-29

A line in the step matching `REDEFINES_CONFIRM` (a confirmation word followed by
`means`, `is defined as`, `refers to`, `is when`, `counts as`) is skipped as a
confirmation and sets `confirm_redefined: true` (THREATS 14). Test:
`test_redefining_confirmation_is_not_a_confirmation`.

A line inside a fenced block: the step is the block plus the paragraph just
before its opening fence and the paragraph just after its closing fence. Tests:
`test_fenced_block_is_one_step_with_its_lead_in_and_follow_up`,
`test_fenced_block_without_confirmation`.

### Added 2026-10-16 (review C25)

Every row records whether the action itself is forbidden: `negated_action` from
`negation.negation` at the action's match, and `carve_out`, the exception after it. A forbidden
action with no confirmation step is a prohibition, never an unconfirmed request; the report reads
`negated_action` for that. Tests: `tests/test_negation.py` (7) and the grader's `neg-25-rubric-*`
rows.

## scan

Runs the pattern table over one file's lines and builds the `02.4-phrases` findings
("The stage", "Findings").

### Inputs

- `rel`: the file's path relative to the input, forward slashes.
- `text`: the decoded file text.
- `rows`: the loaded pattern table (`patterns.load_table`).
- `audience`: the file's audience tag (`audience.audience`).

### Outputs

`scan_text(rel, text, rows, audience) -> list[dict]`:

- Lines come from `foldtext.split_lines` (split on `\n` only), numbered from 1,
  so every line number is the original's.
- Each line is folded (`foldtext.fold_line`) and every row that `applies` is
  tested on the **folded** line with `row.hits`.
- One finding per line per check that has at least one hit:
  `check`, `file` (`rel`), `line`, `quote` (the original line, verbatim, line
  ending removed), `patterns` (the ids that hit, in table order), `audience`,
  and `folded`: true when the folded line differs from the raw line and no
  pattern of this check hits the raw line (the hit exists only after folding,
  THREATS class 4), and `matches`: one `{pattern, text, start}` per id in
  `patterns`, the matched text on the folded line (at most 160 characters) and
  its offset in the folded line (2026-09-30).
- Findings are ordered by line, then by check in CONTRACT order.

`frontmatter_lines(lines) -> set[int]`: the 1-based numbers of the lines inside
a leading YAML frontmatter block: line 1 is `---`, and the block ends at the
next line that is `---` or `...`. The delimiter lines are not in the set. No
closing delimiter means no frontmatter.

### Must never

- Grep only the raw text; the folded copy is the input and the raw line is the quote.
- Drop, merge, rank, or score a hit.
- Change a line number.

### Done when (each backed by a test in `tests/test_scan.py`)

1. A line that hits two patterns of one check gives one finding listing both ids, in table order; a line that hits two checks gives two findings.
2. `quote` is the raw line verbatim, and `line` is its original number.
3. A keyword split by a zero-width character, or written in fullwidth letters, hits with `folded` true; a plain hit has `folded` false.
4. A line separator (U+2028) inside a line does not shift later line numbers.
5. A `where: frontmatter` row hits inside frontmatter only; `frontmatter_lines` finds the block and ignores an unclosed one.
6. `audience` is carried onto each finding, and an `audiences` restriction is honored.

### Added 2026-10-16 (review C25)

Each finding carries `negated`, `negation`, and `carve_out` from `negation.py`: `negated` is true
when a negation governs every pattern's action on the line (`negation.anchor` for where each
action starts). The finding is otherwise unchanged. Test: `tests/test_negation.py` (7).

### Added 2026-10-18 (review C37): instructions hard-wrapped across lines

Markdown joins the lines of a paragraph, and so does a model reading it, but the line pass reads
one line at a time: "add a machine-level backstop to" / "`~/.codex/config.toml` so ..." hits no
row, because the verb ends one line and the target starts the next.

`wrapped_findings` runs after the line pass, in Markdown files only (`.md`, `.markdown`, `.mdc`,
`.mdx`). For each line and the line after it, both in one paragraph, it folds the two joined by a
space and tests every row that applies. A check gives a wrapped finding only when neither line
hits it alone, so nothing the line pass found is counted twice. The finding is the usual one,
cited at the first line, plus `end_line` (the second line) and `wrapped: true`; `quote` is both
raw lines with a newline between them, and `matches` offsets are into the joined text.

A pair is never joined when either line is blank, in frontmatter, inside a fenced code block or
is a fence, a heading, a table row, a rule or setext underline, or starts with an HTML tag or
comment; or when the second line starts a list item, or one line is quoted (`>`) and the other
is not. Quoted lines join without the second line's `>`. A list item's continuation line joins.

Findings stay ordered by line; on one line, line-pass findings come before wrapped ones.

`run.mask_secret_lines` masks a wrapped finding when either of its lines holds a secret.

Since 2026-10-20 (C37 follow-up): runs of up to `MAX_JOIN` (4) lines are joined, and a check
counts on a run only when no line or shorter run inside it hits it; each match of a wrapped
finding carries `spans`, `[line, start, end]` per raw line, so a review card marks the words on
both sides of a break. A line hit whose row narrows itself (a negative lookahead or an `unless`)
is tested again on the line joined with the next line up to that line's first sentence end; a row
that no longer hits is taken off the finding, and a finding left with none is no hit
(`undone_by_next_line`; `scan_text(..., undone=list)` collects them and `run.py` writes them to
`hits.json`). Rows without either narrowing are never tested this way: one anchored at the end of
the line would be cancelled by any text after it. A match spread over more than four lines is
still not caught.

Earlier note (2026-10-18), now history: not done: a match across three or more lines (only neighbours are joined), and the reverse
case, a line-pass hit that the next line undoes (`don't ask` / `hypothetical questions`).

Done when (tests in `tests/test_scan.py`, `tests/test_secret_scan.py`):

7. A row that hits only the joined pair gives one finding at the first line with `end_line`,
   `wrapped`, both lines as the quote, and the matched text from the joined line.
8. A check either line hits alone gives no wrapped finding for that pair.
9. Blank lines, list starts, fences, headings, table rows, rules, tag lines, quote boundaries,
   and frontmatter are never joined; only Markdown files are joined.
10. Quoted lines join without the marker; a list item's continuation joins.
11. A wrapped finding sorts after the line findings of its first line.
12. A secret on the second line masks the wrapped finding.

Fixture: `Fixtures/02.4-phrases/wrapped-lines.md` (grader rows `ph-wrap-*`: three wrapped
positives, the one-line twin, and negatives for a sentence boundary, a list, and a code fence).

Done when, C37 follow-up (tests in `tests/test_scan.py`, `tests/test_secret_scan.py`):

13. A match across three lines is one finding with `end_line` three lines on and `spans` on each
    line (quoted lines too); a check found in a shorter run is never repeated in a longer one;
    a run of five lines is not joined.
14. "don't ask" ending a line, then "hypothetical questions", is no hit and is listed as undone;
    the twin with an object stands; an `unless` word on the next line cancels only up to that
    line's first sentence end; a row anchored at the end of the line is never cancelled; a hit
    that loses one of two rows keeps the other; only Markdown is tested this way.
15. A secret on a middle line of a run masks the wrapped finding.

Fixture rows `ph-wrap3-gate-35`, `ph-wrap-neg-39`, `ph-wrap-gate-42` in `wrapped-lines.md`.

### Added 2026-10-25 (review C42, an outside tester): base64 and folded frontmatter

**Base64.** On every line, each run of 24 or more base64 characters that decodes to readable
UTF-8 text (`foldtext.base64_texts`: printable characters and white space, at least 12 of them
and three words) is matched like a line, its white space collapsed. A check the line itself
does not hit gives a finding at that line with `decoded: "base64"` and `decoded_text` (the
decoded text, capped at 160 characters); `quote` stays the raw line. Base64 of binary data
(an image, a key) decodes to no text and adds nothing. A "Decode this and follow it" line had
been filed only as a committed secret.

**Folded frontmatter.** A frontmatter value written over more than one line, a block scalar
(`key: >`, `>-`, `|`, `|-`, ...) or a plain value continued on lines indented more than its key,
is joined with single spaces (the key line's own value first, when it has one) and matched with
the frontmatter rows. A check no single line of the value hits gives one finding cited at the
first line that holds value text, with `end_line`, `wrapped: true`, the value's lines as
`quote`, and `spans` on each line. Up to 20 lines are joined. An override split across
`description: >-` lines had not matched.

Done when (tests in `tests/test_scan.py`):

16. A base64 run of an override hits with `decoded: "base64"` and the decoded words; base64 of
    binary bytes adds nothing; a line that already hits a check is not repeated from its base64.
17. An override split over a `description: >-` block, and over a plain value continued on
    indented lines, is one finding at the first value line with `end_line`; a check one line
    hits alone gives no joined finding; a value of one line is not joined.

Fixture rows `c42-base64-decoded`, `c42-binary-base64-not-read` (`class11-encoded.md`) and
`c42-frontmatter-joined` (`class11-folded-frontmatter.md`).

## secret_scan

Added 2026-10-04.

Committed secrets (TOOLING "Secrets adapter"): detect-secrets (Apache-2.0, in requirements.txt), so the check runs on any
install. gitleaks is not run, even when one is on the machine: a repository's own `.gitleaks.toml` and `.gitleaksignore` steer it, by its
README, and the repository is what is under audit (not measured: none is installed here). Named `secret_scan` so it never shadows Python's `secrets` module.

### Inputs

The input folder and `{rel: audience}` for the text files `02.4-phrases` scanned, and the pattern lists, which no other check reads.
A lock file is left out by name (`LOCK_FILES`: `package-lock.json`, `npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lock`,
`bun.lockb`, `Cargo.lock`, `poetry.lock`, `uv.lock`, `Pipfile.lock`, `go.sum`, `Gemfile.lock`, in any letter case): it is made of hashes,
and a scanner takes a hash for a key. Every other file is read, build files included. The list is the scan's own: `audience.BUILD_FILES`
and `BUILD_GLOBS` say who reads a file, and do not decide what the scan reads.

### Outputs

- One `secret.found` per file and line: `kinds` (the detectors' names for what they matched,
  merged), `engine` (`detect-secrets`, or `walkdown` for a key shape alone), `audience`. `line` is the line as every step
  numbers it (`readtext.split_lines`), so a mask lands on the line a phrase finding cites. Every line a secret stands on has a
  row, however many lines of the file hold the same value: the hits are the library's `scan_file`, which gives one for each line.
  Its `SecretsCollection` keeps one of a value in a file, and its GitHub rule captures only the prefix, so there every GitHub
  token of a file is one value.
- Text decoded from base64: on each line, the readable text its base64 runs decode to (`foldtext.base64_texts`, the text a
  phrase hit keeps as `decoded_text`) goes through both passes as well, detect-secrets and `KEY_SHAPES`. A hit stands at the line of
  its base64, its kind ends in `IN_BASE64` (` (in text decoded from base64)`), and the row has `in_base64: true`, which the mask reads
  (2026-11-03). Such a hit is never readable base64 itself, so its line gets no `BASE64_TEXT`. A file whose decoded text the library
  did not read is a skip, as the file would be.
- `key_end` on a row whose kinds name a private key (`secretmask.is_private_key`): the last line of the key, since the scan flags only
  its first and the lines below it are the key (`secretmask.key_end`: through the next line holding `-----END`, or with none through
  the line before the next blank line). Absent when the key ends on its first line. The mask and a model read cover every line from
  `line` to `key_end` (`stages/_shared/specs/shared.SPEC.md`, secretmask); `line` and the count of rows stay what they were, and no page
  shows the range.
- No scanner available: one skip finding (`file` null) naming what to install; the limits (`data/limits.md`) list it.
- A file detect-secrets did not scan: one skip finding for that file (`_could_not`, `the secret scan could not scan this file`),
  never the error's text. Those are a file whose bytes `readtext.decode` cannot read or that cannot be opened, a file it raised on,
  and a file it never asked for the text of: its filters leave some out by name before reading them (`.svg`, `.css`, `.map`, and
  the rest of `IGNORED_FILE_EXTENSIONS`; a path holding `swagger`), and a later version may read some other way. The check for this
  is that the library asked for the text, so no silent zero stands behind `looked_at`. The file counts as explained, the shapes
  below still run on it, and `details.html` and `full.md` say the scan could not scan it beside what the scan found
  (`stages/06-report/specs/report.SPEC.md`, History).
- A comment in the repository under audit does not silence the scanner. detect-secrets runs with its filter `is_line_allowlisted`
  off (`ALLOWLIST_FILTER`), so `pragma: allowlist secret`, `pragma: whitelist secret`, and `pragma: allowlist nextline secret`
  change nothing; every other filter stays.
- `secret_left_out`, a key of the report beside `findings`: the sorted paths of the text candidates the scan left out by name, which are
  lock files alone. A lock file has no row in `secret.found`, and the coverage line does not count it, so a zero is a zero of what was
  read. `details.html` and `full.md` say them (`stages/06-report/specs/report.SPEC.md`, History). A key in a lock file is not flagged, so
  it is not masked (`stages/_shared/specs/shared.SPEC.md`, secretmask).
- Key shapes Walkdown checks itself, on every scanned file, with the scanner or without it (`KEY_SHAPES`;
  2026-10-25, review C43: detect-secrets has no rule for Anthropic keys, and a real-looking one
  in prose was missed): an Anthropic key (`sk-ant-api` or `sk-ant-admin`, two digits, `-`, then
  32 or more letters, digits, `_` or `-`), kind `Anthropic API Key`. A match on a line the scanner
  flagged adds its kind there; otherwise it is its own finding with engine `walkdown`.
- `secretmask.mask_secret_lines` (`stages/_shared/secretmask.py`; `02.4-phrases`'s runner calls it, and so does
  the builder step for the findings it makes): every other finding that keeps words from a line with `secret.found` has them
  replaced by `SECRET_MASK` and `masked: true`; the location stays. Here that is each quote and matched word, a rubric row's `action`,
  `carve_out`, and `confirm_quote`, a definition's `term`, `limit.setting`'s `tools`, `rep.sentence`'s `sentence`, `term.conflict`'s
  definitions, and `endpoint.host`'s addresses, each where it stands, and its host when every place naming it is flagged
  (`stages/_shared/specs/shared.SPEC.md`, secretmask, has the whole rule). `02.5-capability` reads `limit.setting`'s `kind`,
  `value`, and `rules_out`, which stay. `secretmask.mask_reports` does the same to the steps that run before this one, after it.
  A line whose secret is only base64 that
  decodes to readable text is not masked: it holds no key, and its text is the instruction a
  reader needs (2026-10-25, review C42).

### How a file reaches detect-secrets

The library opens a file itself with `open(filename)`, so the machine's default encoding, and takes a `UnicodeDecodeError` for a
binary file: no scan and no error. `_scan_decoded` hands it the text instead: for the one call, the name `open` in the library's
`detect_secrets.core.scan` is ours and gives back that text as `readtext.decode` reads the bytes, in the lines of
`readtext.split_lines` (a lone CR, a form feed, and U+2028 end no line). The scan calls the library's `scan_file` and uses every
hit it gives. Everything else stays the library's: its filters, its transformers (they choose by the file's name), its plugins. `_shapes` and `likely_not_secret` read the same text, so all three
see the same lines. The name `open` is taken back after each call, and `detect-secrets` is pinned in `requirements.txt`.

### Must never

- Put a secret's value, or a hash of it, in any finding or report. (A hash of a short password
  can be reversed by guessing.)
- Fail the run when no scanner is installed.
- Count a file as looked at when detect-secrets did not read it.
- Let a comment in the audited repository drop a line from the scanner, or earn it the mark of likely not a secret.
- Run gitleaks, or any program a file in the repository under audit can configure.
- Leave a file out by a name that is not on `LOCK_FILES`, or go by `audience`'s lists.

### What it does not reach

`docs/READING-THE-REPORT.md` (Passwords and keys) says these to the reader:

- A key in a lock file: left out by name (`LOCK_FILES`), so it is not flagged and not masked. The pages name the file.
- A key the scanner has no rule for: a shape no detector knows, a key spelled only in hidden characters, and `password = value` with no
  quotes in a `.md` with prose in it (`test_what_the_scan_does_not_flag_is_what_the_docs_say`). It has no row, so nothing masks it and a model read sends it.
- A key on a line with readable base64 that the scanner does not flag itself: `BASE64_TEXT` asks only the values it flagged, so a key
  of a shape no rule knows, out of quotes where the entropy rules do not look, keeps the mark, and with a phrase hit on the line `full.md`
  and `data/02.4-phrases.json` keep it. A model read leaves the line out.

### Done when

1. A made-up key is found by line, and neither value nor hash appears (`tests/test_secret_scan.py`).
2. No scanner gives a skip (`tests/test_secret_scan.py`).
3. Quotes on secret lines are masked; others are not (`tests/test_secret_scan.py`).
4. Fixture `secrets-repo`: the key is found, in a skill and in `.npmrc`, a compose file, `package.json`, and `.gitmodules`; a clean
   file and a lock file are not; no finding repeats the value (grader gate and negatives). A key below U+274C and a key below a tag character are found, and neither
   is repeated (`secret-below-cross-mark`, `secret-below-tag-character`, and their negatives).
6. An Anthropic key in prose is found with its kind, with no scanner or with one, and its value
   never appears (`test_an_anthropic_key_is_found_by_its_shape`).
7. A key below U+274C, U+1F4DD, or a tag character is found with `open()` forced to cp1252 on any machine and with the machine's own
   default, and the line of the check counts the file as looked at (`test_a_character_the_code_page_lacks_does_not_hide_the_key_below_it`).
8. A UTF-16 file and a Latin-1 file are scanned on every machine (`test_a_file_that_is_not_utf8_reaches_the_scanner_on_every_machine`,
   `test_a_key_shape_is_found_in_a_file_that_is_not_utf8`).
9. A flagged line has the number and the text every step gives it (`test_a_flagged_line_has_the_number_and_the_text_every_step_gives_it`).
10. These are a skip in our words, explained and not looked at: bytes that do not decode
    (`test_bytes_that_do_not_decode_are_a_skip_in_our_words`), a file left out by its name
    (`test_a_file_the_library_leaves_out_by_its_name_is_a_skip`), and a library that stops asking for the text
    (`test_a_library_that_stops_asking_for_our_text_gives_skips_and_no_zero`). The library's `open` is its own again after a scan
    (`test_the_library_gets_its_own_open_back`).
11. The key-shape pass numbers a line as every other step does, with a form feed, U+2028, or a lone CR before it
    (`test_the_key_shape_pass_numbers_a_line_as_every_other_step_does`), so the mask finds the hidden text on it.
12. A key with an allowlist comment on its line, in any comment style the library reads, or on the line above, is found and is not
    marked (`test_a_comment_on_the_line_does_not_silence_the_scan`, `test_a_comment_on_the_line_above_does_not_silence_the_scan`;
    fixture rows `secret-with-allowlist-comment`, `secret-below-allowlist-comment`, and their negatives). The library's filter is
    back after a scan, and still drops the line there (`test_the_library_has_its_own_filters_back_after_a_scan`).
13. A key repeated in a file has a row on each line (`test_a_key_repeated_in_a_file_has_a_row_on_each_line`), different GitHub tokens
    in a file each have a row and no value or hash appears (`test_two_github_tokens_in_a_file_each_have_a_row`), and the kinds on one
    line stay in one row (`test_kinds_on_one_line_stay_merged_in_one_row`).
14. A made-up key is flagged in every name of `audience.BUILD_FILES` and `BUILD_GLOBS` that is no lock file
    (`test_a_key_in_any_file_but_a_lock_file_is_flagged`). A lock file gives no flag and no skip wherever it stands
    (`test_a_lock_file_gives_no_flag_and_no_skip_wherever_it_stands`), and the same hashes under another name give a row
    (`test_the_same_hashes_under_another_name_are_read_so_the_zero_is_no_empty_one`). The list of lock names is the one above
    (`test_the_lock_list_is_the_lock_names_and_the_globs_here_are_the_globs_there`), the audience of those names stays
    (`test_the_audience_of_a_build_file_stays_what_it_was`), and a pinned `requirements.txt` has its hashes marked
    (`test_a_pinned_requirements_file_is_read_and_its_hashes_are_marked`).
15. A pattern list is read by the scan alone: its key is flagged, no other check has a row for it, and it is still listed as not scanned
    (`test_a_key_in_a_pattern_list_is_flagged_and_no_other_check_reads_one`). One that cannot be read is a skip of its own
    (`test_a_pattern_list_that_cannot_be_read_is_a_skip_of_its_own`). The report names the lock file and the coverage line does not count it
    (`test_every_check_has_a_line_and_the_counts_add_up`).
16. A gitleaks on the machine is not run, with `.gitleaks.toml` and `.gitleaksignore` in the repository, and the scan runs no program
    (`test_a_gitleaks_on_the_machine_is_not_run`). The stamp's fingerprint does not ask for it (`test_the_fingerprint_does_not_ask_for_gitleaks`).
17. A private key's first line carries `key_end`, its last line, through `-----END` or, with none, the line before the next blank line;
    a key on one line and another kind carry none, and no line of the body appears
    (`test_a_private_keys_first_line_carries_the_last_line_of_the_key`,
    `test_a_private_key_with_no_end_line_runs_to_the_line_before_the_next_blank_one`, `test_a_key_on_one_line_and_another_kind_carry_no_key_end`).

18. A key beside readable base64 is not marked and its line is masked, and readable base64 alone, once or twice, still is
    (`test_a_key_beside_readable_base64_is_not_marked_and_the_text_alone_still_is`); a value reads as text only when the whole of it is
    readable base64 (`test_a_value_reads_as_text_only_when_the_whole_of_it_is_readable_base64`); fixture rows
    `base64-text-alone-is-marked`, `secret-beside-base64-text`, and `secret-beside-base64-text-not-marked` (`beside-base64.md`). On a whole
    run, neither key is in a report or a step output (`06-report/tests/test_run.py`,
    `test_a_key_beside_readable_base64_is_in_no_report_and_no_step_output`).

19. A key that readable base64 spells is found at its line, by both passes and by the key shapes alone with no scanner, its line is
    not marked, and readable base64 with no key still is (`test_a_key_that_readable_base64_spells_is_found_at_its_line_and_never_shown`,
    `test_with_no_scanner_the_key_shapes_still_read_the_decoded_text`); fixture rows `secret-inside-base64-text`,
    `secret-inside-base64-text-not-marked`, and `secret-inside-base64-text-never-shown`. On a whole run the key is in no report and no
    step output (`06-report/tests/test_run.py`, `test_a_key_that_readable_base64_spells_is_in_no_report_and_no_step_output`).

### Likely not a secret (2026-10-09)

On six real repositories every flagged line checked held no secret: hashes under `sha256` or
`hash` keys, a CI test database password on localhost, an environment variable's name, a
keyword followed by an ordinary word. `likely_not_secret(line, kinds)` marks these; the hit is
kept with `likely_not_secret: <reason>` (benign hits are recorded, never dropped):

- entropy kinds only, and the line has a key named for a hash (sha, sha256, md5, hash, digest,
  checksum, integrity, etag, commit, oid, fingerprint, also as a key's last part: `prefix_hash`): "a hash under a key named for one";
- Basic Auth or keyword only, and the line has a URL with a password whose host is localhost,
  127.0.0.1, ::1, example.com / .net / .org (RFC 2606), or ends in .local, .test, .invalid,
  .example, .localhost: "a password in a
  URL for a local test address";
- keyword only, and the value after the first `:` or `=` (trailing `#` comment and quotes
  removed) is an upper-case variable name: "a variable name, not a value"; is lowercase words joined
  by `-` or `_` with no digits (a name such as a Kubernetes `secretName`), or contains a space: "a plain word or prose, not a value";
  is a placeholder (2026-10-25, review C43: `ClientSecret: "abc123..."` in a README reached the
  summary): it ends in `...` or `…`, is in angle brackets (`<your-key>`), starts with `your`, is
  only `x`, `*`, or `.` (three or more), starts with `abc123`, or is `changeme`, `placeholder`,
  `dummy`, `example`, or `redacted` (any case): "a placeholder, not a value".
- entropy kinds only, a base64 run on the line decodes to readable text
  (`foldtext.base64_texts`), and every value detect-secrets flagged on the line is itself such a run (`reads_as_text`; only the
  answer is kept, never the value): "base64 that decodes to readable text, not a key" (2026-10-25,
  review C42: an instruction hidden in base64 was filed as a committed secret; `02.4-phrases` matches
  the decoded text itself). Before 2026-11-02 the rule asked only the line, so a hex key, or base64 of random bytes, beside an
  instruction hidden in base64 got the mark, and its line was shown.

A comment after the code (from `#`, `//`, `/*`, `<!--`, `-- `, or `' `, `COMMENT_TAIL`) comes off the line before any of these rules
reads it: its spaces would read as prose, and a hash key, an address, or base64 in it as the line's own (2026-11-01). A line that is
all comment is judged whole.

The report counts these apart and lists them with the reason in the full report only.

5. Each rule marks its example and leaves a made-up key unmarked (`tests/test_secret_scan.py`);
   placeholders are marked and a key that only ends in letters is not
   (`test_placeholders_are_not_secrets`).

### History

- 2026-11-01: one row for every line a secret stands on (the owner). The scan read `SecretsCollection.json()`, which keeps one of a
  value in a file, so a key repeated in a file had a row on its first line alone, and every GitHub token of a file one row between
  them, since that rule captures only the prefix. A later line kept its quote on the pages and in `data/`, and a model read could not
  tell it was flagged. On the four inputs: 62 more rows on walkdown-v0.3.1, all in test data, and none on the other three.
- 2026-11-01: a false zero fixed. detect-secrets opened each file with the machine's default encoding and swallowed the decode
  error, so on cp1252 a file holding U+274C, U+1F4DD, or a tag character got no scan while its line said checked, and on UTF-8 a
  UTF-16 or Latin-1 file got none. Its lines also carried no mask, since a mask follows `secret.found`. Every file now reaches the
  library as `readtext` decodes it, a file it did not read is a skip finding (`_could_not`), and `_shapes` and `likely_not_secret`
  read the same text and lines (they read UTF-8 with replacement and `str.splitlines`). More `secret.found` findings follow on
  repositories with such files, and more masked quotes. A file left out by name counts as a skip and no longer as looked at.
  `terms.code` moves with this file.
- 2026-11-01: the scan reads every file but a lock file, and the pattern lists (the owner). It asked `audience._build_file`, so a list made
  to say who reads a file kept `package.json`, `.npmrc`, `Dockerfile`, compose files, `Makefile`, `pyproject.toml`, `requirements*.txt`, and
  others out, for a reason only lock files have, and the pages said nothing of it. A key in `package.json`'s license reached `details.html`,
  `full.md`, and `data/02.1-inventory.json`. `LOCK_FILES` and `secret_left_out` are new. Measured first on the four inputs: 17 more files
  read, 0 lines flagged. `terms.code` moves with this file.
- 2026-11-01: a comment in the audited repository no longer silences the scan. detect-secrets took `pragma: allowlist secret` from the
  text under audit and dropped the line with no record, and gitleaks does the same with `gitleaks:allow`; the filter is off and the
  option is passed. `likely_not_secret` reads a line without its comment: `api_key = "x"  // note` was marked prose and left the
  summary. More `secret.found` findings and more masked quotes follow where a repository has such comments, and a line that held a
  value and a trailing comment can move from marked to counted. `terms.code` moves with this file.
- 2026-11-01 (owner): gitleaks is not run. It ran in place of detect-secrets when installed, a repository's own `.gitleaks.toml` and
  `.gitleaksignore` steer it by its README, and no run here or in CI ever reached a real one. `_gitleaks` is gone, and `SKIPPED` says to install
  detect-secrets. Default runs on a machine with no gitleaks do not move. "What it does not reach" now lists what the scan misses.
- 2026-11-02: `key_end` on a private key's first line. The scan flags only that line, so a finding of another step that quoted a later
  line of the key was not masked: on a made-up skill with hidden characters on two lines of a key's body, `full.md` and
  `data/02.2-reader.json` repeated both lines. No row is added or removed, and `line` stays. `terms.code` moves with this file.
- 2026-11-02: `BASE64_TEXT` asks every value the scanner flagged on the line (`reads_as_text`), not the line alone. A hex key, or base64 of
  random bytes, beside an instruction hidden in base64 was marked as no key: on a made-up skill both keys reached `full.md`,
  `data/02.4-phrases.json`, and `data/hits.json`, and the brief said Walkdown found none of the concerns it looks for. Such a line now counts
  among the lines that may hold a secret, and its quotes are masked; the decoded instruction stays (`secretmask.DECODED`, owner, 2026-11-03).
  `terms.code` moves with this file.
- 2026-11-03: the text decoded from base64 is scanned (`IN_BASE64`, `in_base64`). A key that readable base64 spells was flagged nowhere:
  the decoded text a phrase hit keeps showed it in `full.md`, `review.html`, `data/02.4-phrases.json`, and `data/hits.json` (on 0.4.0 too).
  `terms.code` moves with this file.

## terms

The term table ("The stage", part 2, section 4, METHOD's phrase stage, THREATS 14, PHRASES
B): every definition of a word in instruction text, every term defined more
than one way, and every definition of a safety word. Whether a definition is
reasonable is for a person to judge; which of two conflicting definitions governs is never
decided (THREATS 14).

### Inputs

- `rel`, `raw`, `folded`, `instr` (instruction line numbers), `audience`.
- `vocab`: `vocab.load_vocab()`.

### Rules: finding a definition (`defs_file`)

Only lines in `instr`. Sources, in this order; a line gives at most one
definition per term:

- `explicit`: `X means`, `X is defined as`, `X refers to` (`vocab.explicit_kw`),
  and `by X we mean` (`vocab.explicit_by`), within one sentence of the line.
  X is a quoted, backticked, or emphasized token right before the keyword if
  there is one; otherwise the words between the last `,` `;` `:` `|` or
  sentence start and the keyword, with a leading list marker, a leading
  article, and "the word" / "the term" dropped. X of more than `max_term_words` words, or made only of
  `not_terms` words ("this means", "which means"), is not a definition; nor is
  "by no means" / "by any means". The definition is the text after the keyword
  to the sentence end.
- `mapping`: `when the user says X` / `if the user asks for X` (`vocab.mapping`).
  X is the quoted text right after the phrase if quoted, else the words up to
  the next `,`. The definition is the text after that `,` (or after the closing
  quote and any comma) to the sentence end. No text after X means no definition.
- `glossary`: under a markdown heading matching `vocab.glossary_heading` (until
  the next heading of the same or higher level), a line `**X**: def`,
  `**X:** def`, or a list item `- X: def` with X of at most `max_term_words`
  words. The definition is the text after the colon.
- `procedural`: a heading `How to X` or `Steps to X`
  (`vocab.procedural_heading`); the term is X and the definition is the first
  non-blank line after the heading (none: no definition). The finding's `line`
  and `quote` are that sentence's (changed 2026-10-16, review C26: the heading was
  cited, which is not the definition); `heading_line` names the heading.

`term` is normalized (`normalize_term`): quotes, backticks, and markdown
emphasis (`*`, `_`, `~`) removed, lowercased, whitespace collapsed, trailing
punctuation removed. `definition` is verbatim from the original line when the
line did not change on folding (else the folded line), stripped of surrounding
space. An empty term, or a definition with no word character (`"complete"
means.`), is not a definition.

Finding: `{check: "term.def", file, line, quote, audience, term, definition, source}`.

### Rules: across the run

- `conflicts(defs) -> list[dict]`: one `{check: "term.conflict", file: null,
  line: null, term, definitions}` per term with two or more different
  definitions, compared after lowercasing, collapsing whitespace, and removing
  trailing punctuation, of which at least one is not `procedural` (2026-10-16,
  review C26: two procedures for one verb in two skills are two procedures, not
  two meanings; a procedure against an explicit definition is still a conflict). `definitions` lists every definition of the term as
  `{file, line, text}` in file then line order. Ordered by term.
- `safety(defs, vocab) -> list[dict]`: one `{check: "term.safety", file, line,
  quote, audience, term}` per `term.def` where any word of the term matches
  `vocab.safety` (confirm, verify, done, safe, read-only, reversible, approve,
  permission, sandbox, allowed, and their inflections).

### Rules: sentences (`split_sentences`)

`split_sentences(line) -> list[tuple[int, int]]`: the `(start, end)` spans of a line's sentences,
with surrounding space trimmed and empty spans dropped. A sentence ends at `.`, `!`, or `?` followed
by space, except after `e.g`, `i.e`, `etc`, and `vs`; an address (`scheme://...`) is masked first so
its dots end nothing. `defs_file` reads each span as one sentence.

### Must never

- Decide which of two definitions is real, or call a definition safe or unsafe.
- Read definitions outside instruction text.

### Done when (each backed by a test in `tests/test_terms.py`)

1. `In this skill, "ship" means push to main.` gives term `ship`, definition `push to main.`, source `explicit`; `Confirmation means announcing your intent.` gives term `confirmation`.
2. `This means the tests pass.` and `by no means` give nothing; `By deploy we mean a tagged release.` gives term `deploy`.
3. `When the user says "tidy up", delete the branch.` gives a `mapping` definition of `tidy up`.
4. A `## Glossary` section with `- **Done**: merged and pushed` gives a `glossary` definition of `done`; the same line under `## Usage` gives none.
5. `## How to fix` followed by `Run the repair script.` gives a `procedural` definition of `fix` at the sentence line, with `heading_line` the heading.
6. Two different definitions of `ship` in two files give one `term.conflict` listing both; two identical definitions (differing only in case and spacing) give none.
7. A definition of `confirmation` or `verified` gives a `term.safety` finding; one of `ship` does not.
8. A line outside `instr` gives no definition.
9. `- Delete means delete` gives term `delete` (the list marker is not part of it); `| a | Delete means delete. |` gives term `delete`; `"complete" means.` gives nothing.
10. Two `How to start` procedures with different first sentences give no conflict; a `How to deploy` procedure and `Deploy means ...` give one.
11. `Read this. If the command fails, retry once. Done.` splits into three sentences; `Use a tool (e.g. a linter) first. Then stop.` into two; the dots of an address end none; a blank line gives none (`test_split_sentences`).

### History

- 2026-10-29: restructure step 6 (keep-or-cut, Q8): `split_sentences` moved here from the conditional
  table, which was cut; `term.def` stays (it is the input of `term.conflict` and `term.safety`).

## termset

Added 2026-10-19, review C22 b.

The version of `02.4-phrases`'s search terms and matching code. Every `02.4-phrases` report records it, so two
runs of the same repository can say whether a new or gone phrase hit comes from the repository
or from Walkdown (`stages/06-report/drift.py`). Runs used to record only the Walkdown commit,
which says that something in Walkdown changed, never what.

### Inputs

- `rows`: the loaded pattern table (`patterns.load_table`).
- The part 2 word lists (`Library/vocab.yaml`, or a given path).
- `02.4-phrases`'s own code: the `.py` files directly in `stages/02-coded/02.4-phrases/` (tests sit in a subfolder).
- The shared code those files import: each `stages/_shared/<name>.py` that any of them imports
  (`import name` or `from name import ...`, at any depth), found by reading the imports with `ast`
  (`imported_shared`), so a new import is covered with no list to keep. A name that is also a file in the
  stage's own folder means that file. A shared module that a shared module imports is not followed. Today
  the set is `audience`, `library`, `readtext`, and `secretmask`. The plumbing the stage imports decides no
  hit and stays out, by name (`NOT_MATCHING`): `coverlines` (the coverage counts), `earlier_steps` (what
  runs an earlier step), `stagelist` (the step list), and `stagenote` (how a note is written). A module not
  named there counts, so a new import can read as a change to the matching code and can never hide one.
- The invisible-character list as loaded (`Library/invisible.yaml`, through `library.invisible()`), since
  it decides a hit as the code does: a keyword split by a listed character matches (P1, 2026-10-29).

### Outputs

`describe(rows, vocab_path=None, code_folder=None, shared_folder=None)` returns the report's `terms` block
(the last two name the stage folder and the `_shared` folder; a test gives its own):

- `rows`: `{row id: short hash}` over the fields that decide a hit (`check`, `regex`, `unless`,
  `audiences`, `paths`, `where`). A row's `note` and `source` never change its hash.
- `vocab`: a short hash of the word lists as loaded, without their `source` labels (comments,
  layout, and where a list comes from do not count), or null when they cannot be read.
- `version`: a short hash of `rows` and `vocab` together: the search terms.
- `code`: a short hash of `02.4-phrases`'s code, line endings normalized, so the same commit checked out
  on Windows and on Linux gives the same value. Each file counts as its tokens without comments, blank
  lines, and docstrings (a statement that is only a string does nothing when it runs); a file that does
  not tokenize counts as it is. Any other change to that code changes it, including changes that do not
  move a phrase hit. The shared modules the stage imports (Inputs) count the same way, by file name after
  the stage's own files, so the run decoding in `library.py` and the text reading in `readtext.py` decide
  `code` as the stage's own scripts do: a change to code in one changes it, a comment, docstring, or blank
  line does not, and a shared module the stage does not import (`termdiff.py`, `validate.py`) or the plumbing
  it does (Inputs) never does. It
  also covers the invisible-character list as loaded (`invisible_list()`): each
  code point and its action (`strip`, `space`, or `run`), in code point order, and the run length (two
  or more selectors make a run, so the number decides a hit). A range's name, kind, date, source, and
  note do not count. A change to the list therefore reads as "matching code changed".
- `count`: the number of rows.

`diff(old, new)` (moved to `stages/_shared/termdiff.py` in restructure step 7) compares two blocks: `rows_added`, `rows_changed`, `rows_removed` (ids, sorted),
`vocab_changed`, `code_changed`, `same` (none of those), and `known`, false when either block is
missing (a run from before 2026-10-19), with every other field empty or false.

Nothing is bumped by hand: editing a row's regex, adding or retiring a row, or changing the code
changes the version on the next run.

### Must never

- Count a row's `note` or `source`, a word list's `source`, comments in the YAML, or comments and
  docstrings in the code as a change.
- Read any file other than these: `02.4-phrases`'s own `.py` files, the `stages/_shared/*.py` modules they
  import that decide a hit, and the two Library files it hashes (`vocab.yaml` and `invisible.yaml`).
- Guess a difference when a block is missing (`known` is false instead).

### Done when (each backed by a test in `tests/test_termset.py`)

1. A row's hash changes with its regex, unless, audiences, paths, or where, and not with its note
   or source; `version` follows any row change and the word lists.
2. `code_version` changes when a `02.4-phrases` file changes and is the same for LF and CRLF copies;
   a comment, docstring, or blank-line edit leaves it the same, and an edited string that does
   something changes it (`test_code_version_ignores_comments_and_docstrings`); `vocab_version`
   ignores `source` labels (`test_vocab_version_ignores_source_labels`).
3. (`diff`, now `stages/_shared/termdiff.py`, has its tests there.) `diff` lists added, changed, and removed rows and the vocab and code flags; identical blocks
   are `same`; a missing block is `known` false.
4. The `02.4-phrases` report carries `terms` (`tests/test_run.py`).
5. `code_version` changes when a code point is added to or dropped from the invisible-character list, when
   a code point's action changes, and when the run length changes, and not when a kind or the order of
   kinds changes (`test_code_version_covers_the_invisible_character_list`,
   `test_the_list_bytes_hold_only_code_points_actions_and_the_run_length`).
6. `code_version` also changes when code changes in a `stages/_shared` module the stage imports that decides a hit, and not
   for a comment, docstring, blank line, or line ending there, or for a shared module the stage does not
   import; a new import is covered with no list, a relative or standard-library import, a name that is a
   file of the stage, and a file that does not parse add nothing; the real stage's set holds `library`,
   `readtext`, `audience`, and `secretmask` and not `termdiff` or `validate`
   (`test_code_version_covers_the_shared_modules_the_stage_imports`,
   `test_a_new_import_of_a_shared_module_is_covered_without_a_list`,
   `test_what_is_not_a_shared_import_is_left_out`, `test_the_real_stage_hashes_the_shared_modules_it_imports`).

- 2026-10-29: restructure step 7: `diff` of two `terms` blocks moved here from `termset.py` to `stages/_shared/termdiff.py`
  (`stages/_shared/specs/shared.SPEC.md`, section `termdiff`), so the report stage imports no stage (notes M13); `termset.py` keeps the half that builds the block.
- 2026-10-29 (after the restructure; notes M15 a and the step 8a amendment): `vocab` drops the `source`
  labels and `code` drops comments and docstrings before hashing, so step 8a's comment edits would no
  longer read as "matching code changed" (checked: the 02.4 code before and after step 8a hashes the
  same; after step 8b, which edited a limit string, it does not). Both values change once.
- 2026-10-29 (P1): `code` also hashes the invisible-character list as loaded, so an edit to
  `Library/invisible.yaml` that changes which characters are stripped or how many selectors make a
  run reads as "matching code changed" in the comparison with an earlier run. The value changes once
  with this version (the code and the list both changed).
- 2026-10-29 (P1, last review): `code` also hashes the `stages/_shared` modules the stage imports, found
  with `ast`. The run decoding had moved into `library.py`, which decides a hit, and `readtext.py` always
  did, and neither was in the hash, so a change to either read as no change to the matching code. The
  value changes once with this version.

## vocab

Loads `Library/vocab.yaml`, the one data file holding every `02.4-phrases` part 2 word list
("The stage", part 2): the harness-rubric tiers and confirmation wording, the
endpoint TLDs and registry and local hosts, and the term-table shapes and safety
vocabulary. Each list says where it comes from in a `source` field (IDs from `Library/SOURCES.md`, or
`PHRASES:<set>` and `THREATS:<class>` sections; step 3b).

### Inputs

- `path`: a vocab file; the default is `Library/vocab.yaml`.
- `rows`: the loaded pattern table (`patterns.load_table`), to check the tiers.

### Outputs

`load_vocab(path=None, rows=None) -> Vocab`, with compiled regexes
(case-insensitive, like `Library/patterns.yaml`):

- `tiers`: J row id to `prohibited` or `confirm-first`; `ignore_unless_tier`.
- `confirm`: list of compiled confirmation regexes; `neg_before`, `neg_after`,
  `neg_forms`.
- `schemes`, `tlds`, `registry` (set of hosts), `local_names`, `local_suffixes`,
  `local_ipv4_prefix`.
- `explicit_kw`, `explicit_by`, `mapping`, `glossary_heading`,
  `procedural_heading`, `not_terms` (set), `max_term_words`, `safety`.

Raises `VocabError` when the file cannot be read, a section or list lacks its
`source`, a regex does not compile, a tier is not `prohibited` or `confirm-first`,
or (with `rows`) a `phrase.J.prohibited` row has no tier.

### Must never

- Hold a word list anywhere but `Library/vocab.yaml`.
- Judge anything: the file holds locators only.

### Done when (each backed by a test in `tests/test_vocab.py`)

1. The shipped `Library/vocab.yaml` loads against the shipped `Library/patterns.yaml`: every
   section and list has a `source`, every regex compiles, and every J row has a tier.
2. A J row without a tier, a regex that does not compile, and a list without a source each raise `VocabError`.
3. No regex in the file contains a backspace byte.
7. A change to the plumbing the stage imports leaves `code_version` the same, and a change to any other module
   it imports moves it; each name in `NOT_MATCHING` is a module the stage imports today, and the stage's own
   `run.py` alone imports `earlier_steps`, `stagelist`, and `stagenote`
   (`test_the_plumbing_the_stage_imports_is_no_change_to_the_matching_code`, `test_the_real_stage_leaves_out_only_the_plumbing_it_imports`).

### History

- 2026-10-29: restructure step 6 (keep-or-cut, Q8): the `conditionals` section of `Library/vocab.yaml`
  (conditional words, kinds, host names) is cut with the conditional table that read it; `KINDS` and
  the kind-order check go with it.
- 2026-10-29: restructure step 3b: the `source` of each list in `Library/vocab.yaml` is now `SOURCES.md`
  IDs and `PHRASES:`/`THREATS:` sections, not document names and section numbers. `vocab.py` did not
  change (it needs a non-empty `source`); the loaded data did, so `termset.py`'s vocab hash changed.
- 2026-10-30: M9 slice B: this step writes its notes through `stagenote`, so a note that names a file or a path from the repository is one line, and a name with a line break cannot pass for a note of its own. `terms.code` hashes the shared files this step reads, so it moved (`stagelist.py` gained the check's entry, and `stagenote.py` is new here); the matching did not change.
- 2026-11-01: `NOT_MATCHING`: a change to `coverlines`, `earlier_steps`, `stagelist`, or `stagenote` read as "matching code changed", though none decides a hit. `code` moves once, with this change (and because `foldtext.py` and `library.py` changed): a run made after it says the matching code changed against one made before.

## Stage history

- 2026-09-29: the pattern engine and the 14 phrase checks (part 1) and the harness rubric, the endpoint census, and the term table (part 2) built, with their word lists in `Library/vocab.yaml`.
- 2026-10-04: position and repetition (`position.py`) and the committed-secret scan (`secret_scan.py`: gitleaks when installed, detect-secrets otherwise; values never shown) built.
- 2026-10-17: the settings that restrict tools (`restrictions.py`, review C32) added.
- 2026-10-29: restructure step 6 (keep-or-cut, Q8): the conditional table (`cond.branch`, section 3) is
  cut. It reached `full.md` only, and nothing that stays read it. Its sentence splitter, which the term
  table uses, moved into `terms.py`; its word lists left `Library/vocab.yaml`. The fixture rows for it
  left `Fixtures/ANSWERS/02.4-phrases.json`; the fixture files stay, other rows use them.
- 2026-10-29: restructure step 4: the checks for builders that were added to this stage on 2026-10-26 and 2026-10-27 (plan for builders, slices 2 to 6) are `02.6-builder`'s now: what the repository needs and what ties it to one machine (`need.*`, `port.*`), which AI hosts it is ready for (`host.*`), whether it will trigger (`trig.*`), what its text asks tools to do (`ask.*`, `fit.loop`), and whether it is current and clean (`clean.*`). Their code, tests, and spec moved with them, and no finding changed (`../02.6-builder/CONTEXT.md`). This stage emits none of them. How it reads a file's text (decoding, the lines), the audience rule, and the mask on a line a secret sits on are shared with that step: `stages/_shared/` (`readtext.py`, `audience.py`, `secretmask.py`).
