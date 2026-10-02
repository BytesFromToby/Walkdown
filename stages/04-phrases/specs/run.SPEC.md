# run.py: spec

The single entry point for stage 4. Gets the file list from stage 1, folds and
scans every text file with the pattern table, and prints one contract-1 report
(`stages/CONTRACT.md`).

## Inputs

```
python stages/04-phrases/run.py <input_dir> [--inventory <file>] [--patterns <file>] [--out <dir>]
```

- `--inventory <file>`: a stage 1 report (JSON) already produced for this input.
- Without it: runs `stages/01-inventory/run.py <input_dir>` as a subprocess with
  the same Python and parses its stdout, so stage 1's walk rules hold (no
  symlink followed, no `.git/`, git-tracked files only in git mode). A
  non-zero exit or unparseable output fails stage 4 (exit 1, message on
  stderr, nothing on stdout). Stage 1 code is never imported.
- `--patterns <file>`: a pattern table other than the shipped `patterns.yaml`
  (for tests). A table that fails validation exits 2.

## Files scanned

Every `inv.file` row that is not a symlink, has a stage 1 `encoding` (text),
and whose bytes `foldtext.decode` reads. HTML comments, code blocks, and
frontmatter are scanned like any other line (the model receives all of them).
A file that is not scanned (no encoding, undecodable, unreadable, or an
`inv.file` skip) is named on stderr with its reason; binary documents (PDF,
DOCX) and images are not scanned in v1.

Audience per file: `audience.audience` with `scripts` from `inv.pin`
`script_languages` and `hook_configs` from `inv.file` `entry_point`
`hook-config` plus every file carrying a `struct.hooks` finding.

## Outputs

stdout: `{"stage": "04-phrases", "contract": 1, "findings": [...]}`: first the
part 1 findings from `scan.scan_text`, ordered by file path, then line, then
check; then the part 2 findings (CONTEXT-part2.md), in CONTRACT order (part 1
findings are never changed by part 2): `rubric.action` (`rubric.rubric_file`),
`endpoint.host` (`endpoints.census`), `cond.branch`
(`conditionals.cond_file`), `term.def` (`terms.defs_file`), `term.conflict`
(`terms.conflicts`), `term.safety` (`terms.safety`); line-based ones ordered
by file then line.

Part 2 inputs per scanned file: the original lines, their folded copies
(`foldtext.fold_line`), and the set of **instruction lines**: every line of a
file whose audience is `model` or `subagent`, plus the frontmatter lines
(`scan.frontmatter_lines`) of a markdown file (`.md`, `.markdown`, `.mdc`) of
any audience, since frontmatter is loaded. Each endpoint occurrence's `where`
is `instructions` for an instruction line, else `docs` for a `human` file and
`code` for a `tool` file. The word lists come from `vocab.load_vocab`, checked
against the loaded pattern table; a bad vocab file exits 2.

stderr: the limits, always: position and repetition and the gitleaks secret
scan are not built (stage 4 part 2); binary documents are not scanned; plus one
line per file not scanned; plus a count of findings, with the part 2 counts.

`--out <dir>`: also writes `<dir>/hits.json`: `findings` (as stdout),
`counts` (`per_check`: part 1 findings per phrase check, every check listed,
zeros included; `per_pattern`: part 1 findings per pattern id, every id listed,
zeros included; `part2`: `rubric` (`rows`, `with_confirmation`,
`without_confirmation`, `negated_confirmation`, `by_tier`), `endpoints`
(`hosts`, `undocumented`, `local`, `by_kind`), `conditionals` (`rows`,
`by_kind`, every kind listed), `terms` (`definitions`, `by_source`,
`conflicts`, `safety`)), `scanned` (file count), `not_scanned` (`file`,
`reason`), and `limits` (the stderr notes). The folder is created if needed. An `--out`
inside `<input_dir>` is refused (exit 2).

Exit 0 when a report was produced, including zero findings. Exit 2 for a
missing or non-folder input, an unreadable `--inventory`, a bad `--patterns`,
or a refused `--out`. Exit 1 when stage 1 fails.

## Must never

- Print anything but the report to stdout.
- Write inside `<input_dir>`; write anywhere without `--out`.
- Import another stage's code, run anything from the input, fetch a URL, or
  follow a symlink.
- Say whether a hit is a problem, score, rank, or drop a hit.

## Done when (each backed by a test in `tests/test_run.py`)

1. On a small tree, stdout parses as a contract-1 report with stage `04-phrases`, exit 0, and every phrase finding has `check`, `file`, `line`, `quote`, `patterns`, `audience`, `folded`.
2. Findings carry the audience of their file (`README.md` human, `agents/x.md` subagent, a script tool, `SKILL.md` model).
3. `--inventory` with a saved stage 1 report gives the same findings as the subprocess path.
4. `--out` writes `hits.json` with per-check and per-pattern counts (zeros included) that agree with the findings; `--out` inside the input is refused.
5. A binary file is not scanned and is named on stderr; stderr names position and repetition and gitleaks as not built, and no longer names the built part 2 items.
6. A missing input folder exits non-zero with nothing on stdout; the input is byte-identical after a run.
7. A zero-finding tree still gives a valid report and exit 0.
8. Part 2 findings follow every part 1 finding, in CONTRACT order, and part 1 findings are identical to a run without part 2 (same phrase findings as the pattern scan alone).
9. On a small tree: a confirm-first line in `SKILL.md` gives a `rubric.action`; the same verb in a script gives none; a host in `SKILL.md` and `README.md` is documented, a host in `SKILL.md` and a script only is not; a conditional and a definition in `SKILL.md` give `cond.branch` and `term.def`, and the same lines in `README.md` give none; a frontmatter line of `README.md` counts as instruction text.
10. `--out` writes the `part2` counts, and they agree with the part 2 findings.

Pattern lists (`.gitignore`, `.gitattributes`, other ignore files, `CODEOWNERS`,
`.gitmodules`, `.mailmap`) are not scanned (reason `pattern list (not instruction
text)`), as stage 3 already skips them (added 2026-09-30, Plumbline).
