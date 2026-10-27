# drift.py (added 2026-10-04)

Version drift (threat class 8): what changed between two runs of the same repository.

## Inputs

Two run folders (each with LOG.md), current or old layout (`layout.py`). Reads stages 1, 3,
4, and 5 (stage 5 from `capability.json` when present, for every citation). Stage 6 is never
compared: model reads drift between runs on their own.

## Outputs

- `compare(old, new)`: files added, removed, changed (by stage 1's per-file `sha256`; by size
  when an older run has no hash, and a same-size file without a hash is listed as unverified,
  never as unchanged); entry points added and removed; hooks added and removed (file, event,
  matcher, command); agent tool grants changed ("inherits all tools" when a definition lists
  none; "(no agent)" when it does not exist in one run); MCP servers added, removed, changed;
  descriptions changed; phrase hits new and gone, keyed by file, check, and the line's text so
  a hit that only moved is neither; network hosts added and removed; trifecta legs that
  switched; install grants added and removed; pairs added.
- `summary_lines(c)`: counts and Walkdown's own words only, no repository text (safe for the
  brief).
- `render(...)` / `write_report(old, new)`: `changes.md` beside the new run's reports, most
  consequential first (legs, grants, hooks, tool grants, MCP servers, descriptions, hosts,
  entry points, pairs, phrase hits in text a model reads, then counts elsewhere, then files).
- `previous_run(run)`: the newest other run folder of the same repository, by LOG.md time.
- `main([old, new])`: writes the report and prints the summary; 2 for bad arguments.

`walkdown.py` runs it after every audit against the previous run of the same name: one line
when the version is the same, the summary and the report path otherwise, never failing the
audit. `walkdown.py diff <old> <new>` runs it on demand.

## Must never

- Put repository text in `summary_lines`.
- Compare model reads, judge a change, or rank changes by importance beyond a fixed reading order.
- Write anywhere but `changes.md` in the newer run.

## Done when (each backed by a test in `tests/test_drift.py`)

1. Each kind of change is found; a moved line is not a new hit.
2. A same-size file without a hash in the older run is unverified, not unchanged.
3. The summary carries no repository text; identical runs say so.
4. The report is written beside the newer run's reports, and the previous run is found.

## Where a hit came from (added 2026-10-19, review C22 b)

`load` also reads the `terms` block of the stage 4 report (`stages/04-phrases/termset.py`).
`compare` adds `terms` (`termset.diff` of the two blocks) and, aligned with `hits_added` and
`hits_removed`, `hits_added_cause` and `hits_removed_cause`, one per hit:

- `repo`: the hit's file was added, removed, or edited.
- `unverified`: the older run has no content hash for the file.
- `walkdown`: the file is the same and the older run has no `terms` block, so a term cannot be
  told from the matching code.
- `terms`: the file is the same and one of the hit's patterns was added or changed (a new hit),
  or retired or changed (a gone hit).
- `code`: the file and the hit's terms are the same and stage 4's code changed.
- `other`: the file, the terms, and the code are all the same (another stage's output moved it).

`summary_lines` adds "Walkdown changed since the older run: ..." (search terms added, changed,
retired; word lists; matching code) and, when any hit came from Walkdown, one line each for new
and gone hits by cause. Counts only. `changes.md` lists the changed terms by id and marks each
new hit in text a model reads with its cause when that is not the repository.

`same_repo(old, new)`: both runs have the same stage 1 pin. `differs(c)`: anything recorded
differs. `since(old, new)`: what `walkdown.py` and the summary page say about the previous run:
with the same version and no difference, nothing is written; otherwise `changes.md` is written,
and with the same version it opens by saying every difference comes from Walkdown.

Done when (tests in `tests/test_drift.py`):

5. Each cause is assigned: an edited file, an added, changed, or retired row, a matching-code
   change, a missing term version, a file without a hash; the summary counts them.
6. Repository changes alone add no cause or Walkdown line.
7. `since` with the same version writes nothing when nothing differs, and writes a report that
   names Walkdown when something does.

## Line endings and files on disk (added 2026-10-20)

A file present in both runs whose `sha256` differs but whose text is the same apart from line
endings (`same_text`: both runs' `sha256_lf` equal; or, when one run predates those hashes, its
`sha256` equal to the other run's `sha256_lf` or `sha256_crlf`) goes in `files_eol`, never in
`files_changed`. It is not an edit: a hit in it is traced as in an unchanged file, it alone makes
no difference (`differs`), and `changes.md` lists it under its own heading. Found 2026-10-20 on
Plumbline at one commit: 7 files counted as changed whose line endings alone had gone from CRLF to
LF.

`on_disk(c)`: files added, removed, or edited. With the same version and none on disk, the brief,
`changes.md`, and the summary say every difference comes from Walkdown (`same_words`); with some
on disk (a local folder with uncommitted edits), they say the same commit, with N files that
differ on disk, and that differences in other files come from Walkdown. `since` returns
`on_disk` and that `header`.

Done when (tests in `tests/test_drift.py`): a CRLF-to-LF file is line endings only and its hit is
not put down to the repository; a run without the new hashes is matched in either direction; the
same version with only line-ending changes writes nothing, and with a file edited on disk says so.

## Cost since the earlier run (added 2026-10-27, slice 6)

`compare` adds `cost`: slice 1's numbers in each run (`cost_of`: every session, every session in
the folder, the entry with the most at its fullest and which, and the files and tokens not used at
run time), or null for a run made before they were counted. `cost_changed` is a difference
(`differs`). `cost_line`: "cost: every session 1,200 -> 1,320 tokens (+120); ..." with only the
numbers that changed and never a file name (the brief shows it), or "costs not comparable: the
earlier run was made before they were counted"; `summary_lines` carries it, `since` returns it as
`cost_line`, and `changes.md` gains a table "What it costs (estimated tokens)" with the largest
entry's file when it changed.

Done when: `test_cost_since_the_earlier_run`.
