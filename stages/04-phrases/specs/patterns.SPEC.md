# patterns.py: spec

Loads and validates the pattern table (`patterns.yaml`), the single data file
that holds every stage 4 pattern (CONTEXT "The pattern table").

## Inputs

`patterns.yaml` (default: beside this script), or any YAML file of the same
shape: a mapping with a `patterns` list. Each row:

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | stable id, unique in the table, e.g. `L.ignore` |
| `check` | yes | one of the 14 stage 4 check IDs in `stages/CONTRACT.md` |
| `regex` | yes | Python `re` pattern, compiled case-insensitive, run on the folded line |
| `source` | yes | `PHRASES:<set letter> ...` or `THREATS:<class> ...` naming the row or bullet it implements |
| `unless` | no | regex (case-insensitive); when it also matches the folded line, the row does not hit |
| `note` | when `unless` is set | the reason for the `unless` (and any narrowing), with its source |
| `audiences` | no | list of audiences (`model`, `subagent`, `human`, `tool`); the row only runs on files with one of them |
| `paths` | no | regex (case-insensitive) on the file's relative path; the row only runs on matching files |
| `where` | no | `frontmatter`: the row only runs on lines inside a leading YAML frontmatter block |

Case-sensitive parts of a pattern use the scoped flag `(?-i:...)` (for
example upper-case identifier names such as `API_KEY`).

## Outputs

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
`note`; an unknown audience or `where` value; an unknown field.

## Must never

- Decide anything about a hit. It only says whether a row matched.
- Hold patterns in code: every pattern lives in the YAML file.

## Done when (each backed by a test in `tests/test_patterns.py`)

1. The shipped `patterns.yaml` loads: every row names a valid check and a source, every regex and `unless` compiles, ids are unique, and every one of the 14 checks has at least one row.
2. Each malformed table above raises `TableError`.
3. Matching is case-insensitive; `(?-i:...)` parts stay case-sensitive.
4. An `unless` that matches cancels the hit; one that does not leaves it.
5. `audiences`, `paths`, and `where: frontmatter` restrict where a row applies.
6. The shipped table catches a known positive for every one of the 14 checks, in wording of its own (never a fixture sentence), including a folded one; every narrowed row (`unless`, or a note naming a narrowing) misses its benign shape and still hits its class (`tests/test_table.py`).
