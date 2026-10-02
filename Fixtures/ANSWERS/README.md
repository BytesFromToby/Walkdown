# ANSWERS: the answer sheet (GRADER-ONLY)

**Do not open this folder while building a stage.** Stages are built blind from
the class spec (THREATS / PHRASES) and the stage contract
(`stages/CONTRACT.md`), and proven only through the grader. Reading the answers
while building a detector makes the eval circular (`Fixtures/CONTEXT.md`).

One JSON file per stage with fixtures: `01-inventory.json`, `02-reader.json`,
`03-graph.json`, `04-phrases.json`. Converted 2026-09-25 from the prose sheet,
which is kept here as `_history-ANSWERS-2026-09-14.md`.

## Format (answers_version 1)

```json
{
  "stage": "04-phrases",
  "answers_version": 1,
  "note": "what this stage's fixtures exercise",
  "cases": [
    {
      "root": ".",
      "fixtures": {"class05-override.md": "<sha256>", "...": "..."},
      "expect": [
        {"id": "ph-05-gate-6", "polarity": "gate", "check": "phrase.L.override",
         "file": "class05-override.md", "line": 6, "note": "..."}
      ],
      "deferred": [
        {"id": "...", "needs": ["02-reader", "04-phrases"], "note": "..."}
      ]
    }
  ]
}
```

- **case.root**: the folder under `Fixtures/<stage>/` the stage runner is pointed
  at. Stage 1 has one case per class folder (each is a mini repo); stage 3's case
  is `sample-repo/`.
- **case.fixtures**: sha256 of every file under the root. The grader refuses to
  grade when a file changed, appeared, or disappeared since the answers were
  written. After a deliberate fixture change, re-verify its expectations, then
  run `python grader/grader.py --rehash <stage>`.
- **expect**: one row per expectation.
  - `polarity`: `gate` (must be found; a miss fails the stage), `recall`
    (measured, reported as a percentage, never fails the stage), `negative`
    (must not be found; a hit is a false positive and fails the stage).
  - A finding matches when `check` is equal, `file` is equal (if given), `line`
    is equal (if given), and every `match` condition holds.
  - `match` operators: `eq` (equal), `contains` (case-insensitive substring),
    `same_items` (same list, order ignored), `includes` (list contains the
    value), `excludes` (list contains none of the values).
  - `count` (gate only): exactly this many findings must match.
  - `note`: the reasoning. Printed only with `--explain`.
- **deferred**: expectations that need more than one stage chained (for
  example, a stage 4 pattern run on stage 2's folded text). Listed in every
  report as deferred, never scored, until pipeline grading exists.
