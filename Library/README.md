# Library

The tables and lists Walkdown looks things up in, in one folder. Nothing here runs.

## The rule

- **Data only.** Tables, lists, and their sources. Never code: no script, no function, no regex
  compiled here. A stage reads a file and does the work in its own code.
- **Every entry is dated, with its source.** A file says when its facts were checked (`checked:`,
  `added:`, `moved:`) and where they came from (`source:`, `sources:`, or a comment). A fact with no
  source and no date does not belong here.
- **One home for each fact.** A stage never keeps its own copy of something that is listed here.
  (The invisible-character list was kept three times, once per stage. It is `invisible.yaml` now.)
- **The tables are the files that change when a new issue comes up.** A new pattern, a new host, a
  new tool, a new rule for a trifecta leg: each is an edit here, with its plain words beside it. What
  the report calls a heading, a jump bar entry, or a card button is the report's design, and stays in
  the report's code.
- **Outside sources are listed once**, in `SOURCES.md`, with an ID, a link, the date last checked,
  and what was taken from the page in Walkdown's own words. A table cites a source by that ID, or by
  a section of `PHRASES.md` or `THREATS.md` (`PHRASES:K`, `THREATS:1`). No table holds a link.
- **A change here re-measures every stage.** The validation stamps are keyed on a fingerprint that
  includes this folder (`stages/_shared/validate.py`), so a cached stamp is never reused after
  an edit.

## How a stage reads a file

Through one small helper, `stages/_shared/library.py` (code, so it lives with the stages, not
here). It knows where this folder is: `library.load_yaml("fit.yaml")`, `library.load_json(name)`,
`library.path(name)`, and `library.invisible()` for the invisible-character list, with `library.runs`
for the runs of invisible characters in a line (the rule for a run is code, so it lives in that
helper). Its spec is
`stages/_shared/specs/shared.SPEC.md` (the `library` section). No stage builds a path to a file in here by itself.

## The index

"Read by" names the stage (step) whose code loads the file. "Checked by" names the fixtures and
tests that prove its entries: the fixture folders are under `Fixtures/`, the tests under each
stage's `tests/`.

| File | What it holds | Read by | Checked by |
|---|---|---|---|
| `invisible.yaml` | The invisible characters: 181 to strip (zero-width, direction marks, soft hyphen, blank letters and cells, tag characters, NUL), 260 variation selectors that are stripped and reported only where two or more stand in a run, in a row or with only stripped characters between them (the run length is written once, in the file), three separators turned into a space, and the kind 02.2-reader names each one. Each range has a plain name, a date, and a source; a range whose code points are default-ignorable in Unicode cites `S19`. | 02.2-reader (`fold.py`), 02.3-graph (`invisible.py`), 02.4-phrases (`foldtext.py`; `termset.py` hashes the list into `terms.code`), 02.5-capability (`pairs.py`), 06-report (`details_html.py`), all through `stages/_shared/library.py` | `stages/_shared/tests/test_invisible_sets.py` (every character held before is handled as before, U+180E aside; the new ones; every assigned default-ignorable code point is listed); fixtures `02.2-reader/class04-invisible-zerowidth.md`, `class04-invisible-more.md`, `class04-bidi-trojan.md`, `02.4-phrases/class11-nul-split.md`, `class11-invisible-more.md` |
| `patterns.yaml` | The 02.4-phrases pattern table: 125 rows, each a pattern for a phrase worth a look, the check it files under, the PHRASES or THREATS entry it comes from, and its `plain` words (what it looks for and why a reader would care, shown on the review page). | 02.4-phrases (`patterns.py`); 06-report (`plain.py` reads the `plain` field) | `Fixtures/02.4-phrases/class01-*` to `class22-*` (gate, recall, negative); `02.4-phrases/tests/test_table.py`, `test_patterns.py`; `06-report/tests/test_plain.py` and `02.5-capability/tests/test_rules.py` (the ids they name exist) |
| `vocab.yaml` | The 02.4-phrases part 2 word lists: the confirmation and negation words and the tier of each prohibited action (rubric), the schemes, domain endings, registries and local hosts (endpoints), and the term-definition cues. | 02.4-phrases (`vocab.py`; `termset.py` hashes the lists as a version, which 06-report's `drift.py` compares between runs) | `Fixtures/02.4-phrases/part2-repo`; `02.4-phrases/tests/test_vocab.py` (loads against the shipped patterns), `test_rubric.py`, `test_endpoints.py`, `test_terms.py`, `test_termset.py` |
| `capability.yaml` | The 02.5-capability rules: which evidence makes each trifecta leg (patterns, tools, hook events, connector names), which install grants count, which hook events inject context, how a tool maps to a posture word, the evidence cap, and the limits printed every run. | 02.5-capability (`rules.py`, which gives the other scripts the same names the constants had) | `Fixtures/02.5-capability`; `02.5-capability/tests/test_rules.py` (every pattern id named exists under its check), `test_legs.py`, `test_posture.py` |
| `tools.yaml` | The programs Walkdown recognizes (with the one system each runs on), import names whose package has another name, Node's built-in modules, home folders that are not a person's, and the kinds of place that tie a repository to one machine, with their words. | 02.6-builder (`needs.py`); 06-report (`render.py`, `glance.py`: the kinds and their words) | `Fixtures/02.6-builder/needs-repo`; `02.6-builder/tests/test_needs.py`; `06-report/tests/test_library_kinds.py` |
| `hosts.yaml` | The AI hosts reported on (Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot, Windsurf, other AGENTS.md readers): what each reads from a repository, dated, with its source; the instruction files kept for one host each; the Agent Skills frontmatter keys; Claude Code's own words and tools; and the kinds of one-host feature, with their words. | 02.6-builder (`hosts.py`; `fit.py` asks whose a hook file is); 06-report (`render.py`, `glance.py`) | `Fixtures/02.6-builder/hosts-repo`; `02.6-builder/tests/test_hosts.py`; `06-report/tests/test_library_kinds.py` |
| `trigger.yaml` | What makes a skill, agent, or command trigger: the frontmatter keys and documented values Claude Code takes, its built-in tool names, older tool names, the name and description rules, the guidance patterns, the overlap settings, and the kinds of trigger finding, with their words. Each fact names its source and date. | 02.6-builder (`trigger.py`, `hosts.py`, `clean.py`); 06-report (`render.py`, and the pages that use its listing numbers) | `Fixtures/02.6-builder/trigger-repo`; `02.6-builder/tests/test_trigger.py`; `06-report/tests/test_library_kinds.py` |
| `asks.yaml` | What text the AI reads asks a tool to do (shell, write, web, search, agent), the tools named outright, and the patterns for a loop with no stated limit. | 02.6-builder (`asks.py`) | `Fixtures/02.6-builder/asks-repo`; `02.6-builder/tests/test_asks.py` |
| `clean.yaml` | Unfinished text (TODO, placeholders, drafts), dated claims, pinned model IDs, the template paths, and the kinds of unfinished or dated text, with their words. Facts with locations, never a judgment. | 02.6-builder (`clean.py`); 06-report (`render.py`: the kinds and their words) | `Fixtures/02.6-builder/clean-repo`; `02.6-builder/tests/test_clean.py`; `06-report/tests/test_library_kinds.py` |
| `fit.yaml` | Do the tools fit the job: the families of work and the tools that do them, Claude Code's hook events, how often each event runs, which put output in context, and the words for the kinds of fit finding, the families, and how often a hook runs. Dated, with sources. | 02.6-builder (`fit.py`); 06-report (`render.py`, `glance.py`: the kinds and their words) | `Fixtures/02.6-builder/fit-repo`; `02.6-builder/tests/test_fit.py`; `06-report/tests/test_library_kinds.py` |
| `loading.yaml` | What loads into an AI's context and when: bytes per token, the listing cap, import hops, and four sourced facts about skills, subagents, and CLAUDE.md. | 02.6-builder (`cost.py`); 06-report (`render.py`, bytes per token) | `Fixtures/02.6-builder/cost-repo`; `02.6-builder/tests/test_cost.py` |
| `softreads.yaml` | Everything the two AI stages show a model: the coverage sweep question and its kinds and the system text a model that takes text is given with it, the pinpoint question and its system prompt, the cap on an answer, and the wait before a call that got no answer is tried once more. Each entry cites where it comes from. The labeling question and the relational templates left with the parked code (step 5; git history keeps them). | 03-sweep and 04-pinpoint (both through `stages/_shared/softdata.py`) | `Fixtures/03-sweep/sweep-repo` (recall only, measured with a backend); `stages/_shared/tests/test_softdata.py` |
| `baserates.json` | Measured base rates: per audited repository (labeled `repo-1` to `repo-4`), how many lines outside human-facing files each 02.4-phrases pattern hit. A published fact about each pattern, recomputed as the corpus grows. | 06-report (`render.py`, through `stages/_shared/rates.py`); `tools/baserates.py` writes it | No fixture: it is measured data from audited repositories. `stages/_shared/tests/test_rates.py` (the shipped table loads; the levels) and `tools/tests/test_baserates.py` (the table the tool writes carries the levels the report reads) |
| `THREATS.md` | The threat classes the tables cite, and the trifecta frame: for each, what it is, why it matters, what Walkdown looks for, and the pattern ids that cite it. A reference document for people. | Nothing runs on it. The tables cite its headings as `THREATS:<class>`. | `stages/_shared/tests/test_library_docs.py` (every cited class is a heading; each entry names exactly the rows that cite it) |
| `PHRASES.md` | The lettered sets of wording the pattern rows look for: for each, what it is, why it matters, what Walkdown looks for, and the pattern ids that cite it. A reference document for people. | Nothing runs on it. The tables cite its headings as `PHRASES:<set>`. | `stages/_shared/tests/test_library_docs.py` (every cited set is a heading; each entry names exactly the rows that cite it) |

## The other documents

- `README.md`: this file.
- `SOURCES.md`: the outside sources the tables cite (`S01` to `S19`), Walkdown's own documents
  (`I01` and `I02` are `PHRASES.md` and `THREATS.md`, public; `I03` and on are Walkdown's design
  documents, each marked as in the repository, for a stage's `CONTEXT.md` and spec files, or not
  published, for anything under `pre-planning/` and a removed tool), and how a table cites them.

## What stays in the report code

The report's own presentation wording changes when the report's design changes, not when an issue is
found: the headings and the jump bar (`HEADINGS`, `TOC`), concern row names (`CONCERNS`, `ROW_PLAIN`,
`ROW_SHORT`), the review page's cards (`WHY`, `DECIDE`, `RUNTIME`), the file groups (`PACK`,
`READ_BY`), and the small plain-word maps of `render.py`, `glance.py`, and `details_html.py`. They
stay in `stages/06-report/`.

## Adding, changing, or retiring a term

The search terms are the rows of `patterns.yaml` (the phrase checks of `02.4-phrases`) and the word lists in
`vocab.yaml` (its rubric, endpoint census, and term table). What counts as dangerous moves fast, so a term
change is a routine with a fixed order. Follow it for every add, every narrowing, and every retirement.
Run commands from the repository root with the project's Python (`.venv/Scripts/python` on Windows).

1. **Source first.** Write down why the term matters, dated: an incident, a threat class, a phrase set, a
   miss found in a run, or an owner decision. The row's `source` field cites it by reference: `PHRASES:<set>`
   or `THREATS:<class>` (a heading of `PHRASES.md` or `THREATS.md`; add the pattern's id to that entry's
   "Patterns" line, a test checks it), or an ID from `SOURCES.md`, several joined with `; `. A new outside
   page goes into `SOURCES.md` first. A narrowing, a widening, or a judgment call also gets a `note`.

2. **Fixtures first.** Write the case before the regex:
   - a positive that must hit, and a benign twin that must not, in wording of your own (never a sentence
     copied from an audited repository or from the docs, or the test only proves the regex matches its own
     example);
   - for a narrowing, also a line that has both shapes, so the real hit on it is shown to survive.

   Append the lines to the class's fixture file in `Fixtures/02.4-phrases/` (at the end, so existing line
   numbers and answer rows stay valid), and add rows to `Fixtures/ANSWERS/02.4-phrases.json`: `gate` for
   must-hit, `negative` for must-not, `recall` for measured. Fixtures and answers are byte-exact with LF line
   endings: on Windows, Python's `write_text` writes CRLF, so write bytes. Re-read the fixture, then
   `python tools/grader/grader.py --rehash 02.4-phrases`.

3. **See it fail.** `python tools/grader/grader.py 02.4-phrases` before touching the row: the new negative
   fires, or the new positive misses. A fixture that passes before the change tests nothing.

4. **The row.** In `patterns.yaml`: `id` (the family prefix, such as `L.` or `E.`), `check`, `regex`
   (case-insensitive, run on the folded line), `source`, `plain` (step 5), and `note` when there is a
   narrowing. Two ways to narrow:
   - a **lookahead or lookbehind** on the alternative that over-matches. It drops only that phrase; another
     hit on the same line still fires. Prefer this.
   - **`unless:`**, a regex that cancels the hit when it also matches the line. It cancels the whole line,
     real hits included, and it needs a `note` with the reason.

   Every narrowed row gets cases in `stages/02-coded/02.4-phrases/tests/test_table.py`: the benign shape in
   `test_narrowed`, the class still firing in `test_narrowed_rows_still_fire_on_their_class`.

5. **Plain words.** Give the row a `plain` field: what the words are, then "The worry: ...". The review page
   shows it to readers (`stages/06-report/plain.py` reads it); `stages/06-report/tests/test_plain.py` fails
   until every row has one.

6. **Grade everything.** `python tools/grader/grader.py all` and `python -m pytest`. One stage is not
   enough: a term change moves other stages. A passage whose only pattern hit goes loses that pattern from
   its `covered` list in `03-sweep` and can become a passage `04-pinpoint` picks, so if the term sat in the
   sweep's fixture, check the fixture's notes (its case note, and the row notes that name a covering
   pattern), since its answer rows test only `flagged`; a hit that fed a leg or a pair of `02.5-capability`
   can take the leg or a place to check with it.

7. **Recount.** Count what moved on the audited repositories' latest runs: hits per pattern, places to
   check, legs. Say what disappeared and why. When a term changes how widely a pattern turns up, refresh
   the base rates: `python tools/baserates.py repo-1=<input_dir> [...] --out Library/baserates.json` (label
   each input neutrally, `repo-1`, `repo-2`, ...: the Library is public).

8. **Record it.** A CHANGELOG line saying what a reader will notice, and a line in the review list. There is
   no version to bump: every run records the term set (`termset.py`), so the next audit of a repository
   Walkdown has seen before names the changed term in `changes.md` and counts the hits it moved under
   Walkdown's search terms.

**Retiring a term** is a change too. Delete the row and leave a tombstone comment where it was, with the
date and the reason (see `H.report-only`, retired 2026-10-08). Its `plain` field goes with the row, and its
id leaves the "Patterns" line of its entry in `PHRASES.md` or `THREATS.md`. Turn its fixture rows into
negatives, handle the sweep rows as in step 6, and recount.

**The word lists in `vocab.yaml`** follow the same order: source, fixtures in
`Fixtures/02.4-phrases/part2-repo/` with answer rows, see them fail, the list change, `grader.py all`,
recount, record.
