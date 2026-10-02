# run.py: spec

The single entry point for stage 3. Gets entry points from stage 1, wires
`invisible`, `extract`, `scans`, `resolve`, and `reach` together, and prints one
contract-1 report (`stages/CONTRACT.md`).

## Inputs

```
python stages/03-graph/run.py <input_dir> [--inventory <file>] [--out <dir>]
```

- `--inventory <file>`: a stage 1 report (JSON) already produced for this input.
- Without it: runs `stages/01-inventory/run.py <input_dir>` as a subprocess with
  the same Python and parses its stdout. A non-zero exit or unparseable output
  fails stage 3 (exit 1, message on stderr, nothing on stdout). Stage 1 code is
  never imported.

## Nodes and scanning

- Nodes: every `inv.file` finding in the stage 1 report (so stage 1's walk
  rules hold: no symlink followed, no `.git/`, git-tracked files only in git
  mode). Entry points: those whose `entry_point` is not null.
- A node is scanned when it is not a symlink and its bytes decode as text
  (`invisible.decode`). Symlinks are nodes but are never read.
- `graph.unscanned` (with `reason`) for a node that may hold references but was
  not scanned: an `inv.file` skip (`unreadable`), a binary document (PDF, Word,
  Excel, PowerPoint, OpenDocument, RTF, EPUB, by extension or stage 1 type:
  `binary document (<type>)`), an archive (`archive (<type>)`), or a file
  whose extension says text but whose bytes do not decode (`undecodable
  text`). Images, fonts, and other media are not listed (no reference a
  loader follows).

## Edges and findings

For every reference `extract` finds, `resolve` it:

- `file`: a static edge to each target (`ambiguous`, `case_mismatch` carried
  on the edge).
- `dir` or `glob`: one `graph.dynamic` (`pattern`, `resolves`, `source`
  `directory` or `glob`) and a dynamic edge to each target.
- `missing`: one `graph.dangling` (`target`: the reference as written;
  `context`; also `form`) when the reference may dangle. The same
  (`file`, `line`, `target`) is reported once.
- `outside`: nothing.

For every scan `scans.find_scans` finds: one `graph.dynamic` with `source`
`code`, `pattern`, and `resolves` (a literal pattern with glob characters is
matched as a glob; a literal folder gives its direct children, or every file
under it when the call is recursive; resolved from the script's folder, then
the root; a non-literal pattern gives `[]`), plus a dynamic edge to each. A
glob or directory reference on the same line with the same pattern as a scan is
not reported twice.

Self-edges are dropped. `graph.entry` per entry point (`kind`),
`graph.orphan` and `graph.depth` from `reach`.

## Outputs

stdout: `{"stage": "03-graph", "contract": 1, "findings": [...]}`, findings in
this order: `graph.entry` (path order), `graph.orphan`, `graph.dangling` (file,
line order), `graph.dynamic` (file, line order), `graph.depth`,
`graph.unscanned`.

stderr: notes. Always the v1 limit: manifest versus disk (files on disk no
manifest covers) is not built. When any `graph.dynamic` exists: the graph is
incomplete by construction (count of dynamic loads).

`--out <dir>`: also writes `<dir>/graph.json`: `nodes` (`path`, `entry`: kind
or null, `depth`: int or null), `edges` (`from`, `line`, `to`, `kind`
`static` / `dynamic`, `form`, `text`: the reference as written, `context`,
`source` on dynamic edges, plus `ambiguous` / `case_mismatch` when true), `complete` (false when any
dynamic load exists), and `limits` (the stderr v1 note). The folder is created
if needed. An `--out` inside `<input_dir>` is refused (exit 2).

Exit 0 when a report was produced. Exit 2 for a missing or non-folder input,
an unreadable `--inventory`, or a refused `--out`. Exit 1 when stage 1 fails.

## Must never

- Print anything but the report to stdout.
- Write inside `<input_dir>`; write anywhere without `--out`.
- Import another stage's code, run anything from the input, or follow a URL or
  a symlink.
- Judge or rank orphans; present the graph as complete when a dynamic load
  exists.

## Done when (each backed by a test in `tests/test_run.py`)

1. On a small tree, stdout parses as a contract-1 report with stage `03-graph`, exit 0, and every finding has `check`, `file`, `line`.
2. Entry points from stage 1 give `graph.entry` with `kind`; a file nothing names is `graph.orphan`; a missing path is `graph.dangling` with `target` and `context`; a glob is `graph.dynamic` with `pattern`, `resolves`, `source`; depths and parents are right, and a file reached only by the glob is `via` `dynamic`.
3. An unresolved bare filename in prose gives no finding; one in a code span gives `graph.dangling` with `context` `code`.
4. `--inventory` with a saved stage 1 report gives the same findings as the subprocess path.
5. `--out` writes `graph.json` with nodes, edges, and `complete` false when a dynamic load exists; `--out` inside the input is refused.
6. A PDF node gives `graph.unscanned`.
7. A missing input folder exits non-zero with nothing on stdout; the input is byte-identical after a run.
8. A script with `os.listdir("prompts")` gives a `graph.dynamic` with `source` `code` resolving to the files in `prompts/`.
9. A folder named in README prose is a mention (`load` false; the files under it are `via` `mention`, not orphans); a folder named in a manifest is a load (`load` true; files under it `via` `dynamic`). The rule: a dynamic edge is a load when its context is `config`, its form is `scan`, or it is a glob from a `skill`, `agent`, or `command` entry point.
