# pairs.py: spec

Cross-stage pairs (`cap.pair`): a stage 4 phrase hit that sits on an orphan
file, on a file reached only dynamically, or on hidden text. The pair is a
pointer for a human, read first; it is not a conclusion.

## Inputs

- `reports`: `{"01", "02", "03", "04"}` contract-1 reports.

## Rules

For every stage 4 finding (not skipped, `file` and `line` set):

| `pair` | Holds when | Second half of the evidence |
|---|---|---|
| `orphan+phrase` | the file has a `graph.orphan` finding | stage 3 `graph.orphan` (`why` `orphan file`) |
| `dynamic+phrase` | the file's `graph.depth` has `via` `dynamic` | stage 3 `graph.depth` (`why` `reached only by a dynamic load`) |
| `hidden+phrase` | a `read.divergence` in the same file with `reading` `A-only` covers the line (from its `line` through `line` + the number of line breaks in its `text`), or a `read.fold` is on the same file and line | each covering stage 2 finding (`why` `hidden text: <carrier>` or `folded line`) |

The first evidence entry is the phrase hit itself (`stage` `04`, its check,
file, line, `why` `phrase hit`).

## Outputs

`pairs(reports)`: one finding per (phrase hit, pair kind) that holds:
`{"check": "cap.pair", "file", "line" (the hit's), "pair", "phrase_check",
"patterns", "quote", "evidence"}`, ordered by file, line, phrase check, then
`PAIRS` order.

## Must never

- Read a file, or re-run a pattern.
- Pair a hit with a `B-only` divergence, a different file, or a line outside
  the divergence's span.

## Done when (each backed by a test in `tests/test_pairs.py`)

1. A hit in a `graph.orphan` file gives `orphan+phrase` with both halves in
   evidence and the hit's `patterns` and `quote`.
2. A hit in a file whose depth is `via` `dynamic` gives `dynamic+phrase`; `via`
   `static` gives nothing.
3. A hit on line 7 inside an `A-only` divergence at line 7 gives
   `hidden+phrase`; a divergence at line 5 whose `text` spans three lines covers
   line 7; a `B-only` divergence or a hit on another line gives nothing; a
   `read.fold` on the hit's line gives `hidden+phrase`.
4. A hit that is both orphan and hidden gives two findings, one per kind.
6. A hit whose patterns are all in `CARRIER_PATTERNS` (`K.md-carrier`: the
   stage 4 pattern that detects the markdown carrier itself) makes no
   `hidden+phrase`: it is the same fact as the divergence (2026-09-29, Case 003).
5. No stage 4 findings give no pairs.
7. `hook+phrase`: a `C.script-instruction` or `C.emit-instruction` hit in the
   script a `SessionStart` hook runs, or in a file that script names, pairs; the
   same hit under a `PostToolUse` hook, or in a script no hook runs, or a hit on
   another pattern, does not. `pairs(reports, graph)` takes stage 3's graph.
