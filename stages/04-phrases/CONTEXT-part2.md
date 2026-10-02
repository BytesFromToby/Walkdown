# Stage 4, part 2: rubric, endpoints, conditionals, terms

Part 1 (`CONTEXT.md`) is the pattern engine and its 14 phrase checks. Part 2
adds four descriptive products that METHOD Stage 4 lists beside the patterns.
Same stage, same runner (`run.py`), same report: part 2 findings are appended to
the part 1 findings. Part 2 never removes or changes a part 1 finding.

Every product is a **table to read, never a verdict** (METHOD: "Does not: say
whether any hit is a problem"). A confirm-first action with a confirmation step
is recorded; one without is recorded; neither is called good or bad.

Sources: `pre-planning/METHOD.md` Stage 4 ("Also produced here"),
`pre-planning/REPORTING.md` 4.1 and 4.2, `pre-planning/THREATS.md` classes 14,
21, 22 (and 1 for endpoints), `pre-planning/PHRASES.md` sets B, I, J,
`stages/CONTRACT.md`. Nothing here comes from the answer sheet.

Not in this part (named on stderr as not built, as today): position and
repetition (REPORTING 4.4, 4.5), the gitleaks secret scan.

---

## Shared rules

- Input is the same folded text part 1 greps; every finding cites the original
  file and line and quotes the original text.
- **Instruction text** = files whose part 1 `audience` is `model` or `subagent`.
  **Docs** = files whose audience is `human`. **Code** = audience `tool`.
- Frontmatter counts as instruction text (it is loaded).

## 1. Harness rubric: `rubric.action` (THREATS 22, PHRASES J)

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
'discard' to confirm", superpowers finishing-a-development-branch). A confirmation
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

## 2. Endpoint census: `endpoint.host` (REPORTING 4.1, THREATS 1)

One finding per distinct host, `file` and `line` null. Replaces
`tools/extract_urls.py` (rebuilt, not ported).

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

## 3. Conditional table: `cond.branch` (REPORTING 4.2, THREATS 21)

One finding per conditional sentence **in instruction text** whose condition
falls in one of the seven kinds. Fields: `kind`, `condition` (the clause from
the conditional word up to the comma, `then`, or colon), `body` (the rest of the
sentence), both verbatim.

| `kind` | The condition names |
|---|---|
| `harness` | the host or tool the model runs in (`if you are running in X`, `on Codex`, `in Cursor`, PHRASES I harness row) |
| `clock` | a date, time, year, or weekday (`after 2027-01-01`, `before March`, `on Fridays`) |
| `version` | a version (`version >=`, `v2 or later`, `and above`) |
| `state` | first run, first time, subsequent sessions, a counter or flag the skill keeps |
| `environment` | the repository, org, hostname, account, filename pattern, OS |
| `absence` | something missing (`if no X exists`, `if there is no`, `is not configured`; THREATS 14 absence default) |
| `error` | a failure (`if the command fails`, `on error`, `fallback`, `troubleshooting`) |

Conditional words: `if`, `when`, `unless`, `once`, `after`, `before`, `on`
(for harness and clock), `in case`. A conditional that fits none of the seven
kinds ("if you like, add a title") gives **no** finding. A sentence can fit
more than one kind: emit one finding with `kind` the first in table order and
`kinds` listing all.

## 4. Term table: `term.def`, `term.conflict`, `term.safety` (METHOD, THREATS 14, PHRASES B)

`term.def`: one finding per definition in instruction text. Fields: `term`
(normalized: lowercase, quotes and markdown stripped, trailing punctuation
stripped), `definition` (verbatim), `source` (below).

| `source` | Shape |
|---|---|
| `explicit` | `X means`, `X is defined as`, `by X we mean`, `X refers to` |
| `mapping` | `when the user says X` / `if the user asks for X` followed by what to do |
| `glossary` | `**X**: ...` or `X: ...` list items under a heading containing glossary, definitions, terms, or vocabulary |
| `procedural` | a heading `How to X` or `Steps to X` (the definition is the section's first line) |

`term.conflict`: one finding per term with two or more **different**
definitions (after normalizing whitespace and case), `file` and `line` null.
Fields: `term`, `definitions`: every `{file, line, text}`. Never decide which one
is real (THREATS 14).

`term.safety`: one finding per `term.def` whose term is safety vocabulary: the
word or its inflections of confirm, verify, done, safe, read-only, reversible,
approve, permission, sandbox, allowed (METHOD). Fields: `term`. Always surfaced.

## Checks (added to CONTRACT)

| Check | One finding per | Fields |
|---|---|---|
| `rubric.action` | J hit in instruction text | `tier`, `action`, `confirmation`, `negated_confirmation`, `confirm_line`, `confirm_quote`, `quote` |
| `endpoint.host` | distinct host (`file`, `line` null) | `host`, `documented`, `local`, `kind`, `where`, `occurrences` |
| `cond.branch` | conditional sentence of a known kind | `kind`, `kinds`, `condition`, `body`, `quote` |
| `term.def` | definition | `term`, `definition`, `source`, `quote` |
| `term.conflict` | term with different definitions (`file`, `line` null) | `term`, `definitions` |
| `term.safety` | definition of a safety word | `term`, `quote` |

## Must never

- Judge a hit: no field says good, bad, risky, or benign.
- Change or drop a part 1 finding.
- Fetch, resolve, or look up a host (no DNS, no HTTP). The census is text.
- Import code from another stage.

## Done when

1. Every new script has a `specs/<name>.SPEC.md` and pytest tests written from it,
   and they pass, with all of stage 1 to 5 and 8's tests.
2. `.venv/Scripts/python grader/grader.py 04` reports PASS (both cases).
3. Run on superpowers and on claude-familiar (both under `ReposToExamine/`,
   read-only) completes. Report: rubric rows with and without confirmation
   (compare with part 1's 139 `J.confirm-first` lines on superpowers); hosts,
   undocumented hosts, local hosts; conditionals by kind (PHRASES: superpowers
   carries 19 harness conditionals); definitions, conflicts, safety definitions
   (THREATS 14: superpowers has 6 "means" hits, 0 conflicts).
