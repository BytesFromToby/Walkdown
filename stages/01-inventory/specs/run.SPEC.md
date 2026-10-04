# run.py: spec

The single entry point for stage 1. Wires `walk`, `census`, `frontmatter`,
`configs`, and `entrypoints` together and prints one contract-1 report
(`stages/CONTRACT.md`).

## Inputs

```
python stages/01-inventory/run.py <input_dir>
```

## Outputs

stdout: one JSON document, UTF-8:

```json
{"stage": "01-inventory", "contract": 1, "findings": [...]}
```

Findings in this order: `inv.pin`; `inv.file` per entry (sorted path);
`struct.census` (per file in path order, flags in census order); then
`struct.description`, `struct.agent-tools`, `struct.hooks` (each in path
order); then `struct.manifests` (by name).

`inv.pin` also carries the totals METHOD asks for: `extensions` ({ext: count},
`""` for none), `script_languages` ({language: [files]}, from the extension, or
from a `#!` line for files without one), `magic_backend`, `reader_window`
(`{"lines": 2000, "bytes": 50000}`), `long_line_limit` (500), and
`channel_filters` (files that can make distribution channels differ:
`.gitattributes` with `export-ignore`, `.npmignore`, `package.json` with a
`files` key).

stderr: notes (magic backend in use, exec-bit source, skipped paths).

Exit 0 whenever a report was produced, including zero findings. Exit 2 with a
message on stderr for a missing or non-folder argument.

A file whose bytes cannot be read gives an `inv.file` skip finding
(`skipped`: the error) instead of failing the run.

## Added 2026-10-04

Each `inv.file` carries `sha256`, the hash of the file's bytes (null for a symlink), so two
runs can tell exactly which files changed (`stages/08-report/specs/drift.SPEC.md`).

## Must never

- Print anything but the report to stdout.
- Write anywhere, inside the input or out of it.
- Run anything from the input.

## Done when (each backed by a test in `tests/test_run.py`)

1. On a small mixed folder, stdout parses as a contract-1 report with stage `01-inventory`, and the exit code is 0.
2. The report carries `inv.pin` first, an `inv.file` row per file with every contract field, and the census, description, agent-tools, hook, and manifest findings for the folder's contents.
3. `extensions` and `script_languages` count the folder (a `#!/usr/bin/env bash` file without extension counts as `bash`).
4. An empty folder gives a report with `inv.pin` (0 files) and exit 0.
5. A missing folder exits non-zero without printing a report.
6. The input folder is byte-identical before and after a run.
