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
