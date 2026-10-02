# Stage 4: Phrases

**Question:** what does the text ask for?
**Kind of evidence:** pattern hits on the folded text, one finding per line per
check, each quoting the original line verbatim.
**Report heading:** What the text asks for.

Every hit is a **locator, never a verdict**. PHRASES.md records that every
pattern fires in clean repositories; the benign count is part of the product.
Stage 4 records hits. It never says whether a hit is a problem (METHOD: "Does
not: say whether any hit is a problem").

Sources for every rule below: `pre-planning/METHOD.md` (Stage 4),
`pre-planning/PHRASES.md` (the pattern sets and base rates),
`pre-planning/THREATS.md` (classes 1, 2, 3, 5, 7, 13 to 17, 19 to 22, and
"Extensions to classes 1-12"), `pre-planning/REPORTING.md` (Section 4),
`pre-planning/RED-TEAM.md` (how the patterns get beaten), `stages/CONTRACT.md`.
Nothing here comes from the answer sheet; a builder of this stage never opens
`Fixtures/ANSWERS/`.

---

## Scope of this build (v1, 2026-09-29)

**In:** the pattern engine and the 14 phrase checks in CONTRACT, with the
audience tag. This is what the fixtures and grader cover.

**Part 2 (built 2026-09-29, `CONTEXT-part2.md`):** the harness rubric
(`rubric.py`), the endpoint census (`endpoints.py`, replaces
`tools/extract_urls.py`), the conditional table (`conditionals.py`), and the
term table (`terms.py`), with their word lists in `vocab.yaml`. Their findings
follow the part 1 findings in the same report.

**Still not built:** position and repetition (REPORTING 4.4, 4.5) and a
gitleaks secret scan. `run.py` names both on stderr as not built, so stage 7
can list them.

## Inputs

- `<input_dir>`: a pinned repo copy or a fixture folder. Read-only.
- Stage 4 greps the **folded** text (CONTRACT). Until the orchestrator passes it
  stage 2's output, it folds its own input with stage 2's rules
  (`stages/02-reader/specs/fold.SPEC.md`), reimplemented here, never imported: NFKC;
  strip zero-width characters, bidi controls, soft hyphen, and Unicode tag
  characters; replace U+2028, U+2029, U+0085 with a space; fold confusables to
  ASCII. Line count never changes, so every hit cites the original line.
- Scan every file that decodes as text (UTF-8, or the encoding
  `charset-normalizer` detects), including HTML comments, code blocks, and
  frontmatter: the model receives all of it. Walk with stage 1's rules (no
  symlinks out of the tree, no `.git/`). Files that do not decode as text (PDF,
  DOCX, images) are not scanned in v1; say so on stderr.

## Outputs

- `run.py <input_dir>` prints one contract-1 report to stdout.
- `run.py <input_dir> --out <dir>` also writes `<dir>/hits.json` (every finding
  plus per-check and per-pattern counts). Never writes inside `<input_dir>`.
  The prose `04-phrases.md` belongs to the report stage.

## The pattern table

Patterns live in **one data file**, `patterns.yaml`, not scattered through code.
Each pattern row has:

- `id` (stable, e.g. `L.ignore`), `check` (the CONTRACT check ID), `regex`
  (case-insensitive, run on the folded line);
- `source`: where the pattern comes from: `PHRASES:<set>` with the row it
  implements, or `THREATS:<class>` with the bullet it implements;
- optional `unless`: a regex that, when it also matches the same line, cancels
  the hit (for example, an opt-in clause beside a telemetry verb). Every
  `unless` also cites a source or states its reason in a `note`.

Write the table from PHRASES and THREATS first. The PHRASES rows are narrow
strings from one clean repo; the fixtures test **the class**, with independent
wordings. Where a class needs more than PHRASES lists, derive the pattern from
the THREATS bullet (for example class 1: a private data source, a sending verb,
and a destination, in one sentence). **Never add a pattern that matches only one
fixture line's wording.** A miss on a recall row is a measurement, not a bug.

## Checks and sources

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
| `phrase.C.second-order` | 4c | 15 | PHRASES C (phrase rows only; file-name rows are stage 1 and 3) |
| `phrase.D.trust` | 4c | 16 | PHRASES D (phrase rows) |
| `phrase.E.env` | 4c | 17 | PHRASES E, except the permission-widening row and global or plugin installs (those are `phrase.E.perms`) |
| `phrase.J.prohibited` | 4c | 22 | PHRASES J, with the harness tiers listed there |
| `phrase.G.human` | 4d | 19 | PHRASES G |

## Findings

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

## Dependencies

Standard library `re`, plus packages already pinned in `requirements.txt`
(`PyYAML`, `charset-normalizer`, `confusable_homoglyphs`, `regex` if needed).
No new packages without a note to the user.

## Must never

- Say whether a hit is a problem, score it, rank it, or drop a benign-looking
  hit. The benign count is the product.
- Tune a pattern to one fixture sentence.
- Execute anything from the input or fetch a URL.
- Write inside `<input_dir>`.
- Import code from another stage.
- Grep the raw text only. The folded copy is the input; the raw line is the quote.

## Done when

1. Every script in this folder has a `specs/<name>.SPEC.md` and pytest tests written
   from it, and they pass. `patterns.yaml` has a test that every row names a
   valid check and a source, and every regex compiles.
2. `.venv/Scripts/python grader/grader.py 04` reports PASS (every gate caught,
   no negative hit). Recall is reported and recorded, never tuned to.
3. Run on `ReposToExamine/superpowers-main/superpowers-main/` it completes.
   Record hits per check and per pattern. Where PHRASES lists a superpowers base
   rate for a row, put the new count beside it; rows marked `n/a` get their first
   measurement.
