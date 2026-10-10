# Stage 1: Inventory

**Question:** what ships?
**Kind of evidence:** counting and parsing. No file is read for meaning.
**Report heading:** What ships.

Sources for every rule below: `pre-planning/METHOD.md` (Stage 1),
`pre-planning/REPORTING.md` (Section 1), `pre-planning/TOOLING.md` (Stage 1),
`stages/CONTRACT.md` (check IDs and fields). Nothing here comes from the answer
sheet; a builder of this stage never opens `Fixtures/ANSWERS/`.

---

## Inputs

- `<input_dir>`: a pinned repo copy or a fixture folder. Read-only.
- Nothing from other stages. Stage 1 runs first.

## Outputs

- `run.py <input_dir>` prints one contract-1 report to stdout
  (`stages/CONTRACT.md`). The orchestrator (stage 8 era) renders it to
  `01-inventory.md`; this stage does not write files.

## Checks, in the order they run

| # | Check ID | What it records | Rule source |
|---|---|---|---|
| 1 | `inv.pin` | one row: source path, hash (git HEAD only when the input is the **top level** of its own git work tree; otherwise sha256 over the sorted file list and contents, since fixtures and repo copies sit inside the Walkdown repo), file and byte totals | METHOD Stage 1 "Pin"; clarified 2026-09-25 |
| 2 | `inv.file` | one row per file: extension, bytes, lines (text), exec bit, encoding, BOM, detected type, entry-point kind | METHOD "File census", "Entry points" |
| 3 | `struct.census` | structural flags (below) | METHOD "Structural census"; REPORTING 1.4 to 1.7 |
| 4 | `struct.description` | every frontmatter `description`, verbatim | METHOD "Frontmatter and descriptions" |
| 5 | `struct.agent-tools` | every agent / command definition's granted tools beside its description | METHOD "Grants"; REPORTING 1.9 |
| 6 | `struct.hooks` | one row per hook entry: event, matcher, command | METHOD "Grants"; REPORTING 1.8 |
| 7 | `struct.manifests` | each set of platform manifests for one plugin, and whether their declared permissions differ | METHOD "Platform manifests"; THREATS class 9 |

### Structural flags (`struct.census`)

| Flag | Rule | Source |
|---|---|---|
| `reader-window` | file over 2000 lines or over 50 KB (50,000 bytes); `detail` states the threshold | REPORTING 1.5 |
| `long-line` | any line over 500 **characters** (not bytes: multi-byte text must not trip it early); `detail` gives the line and its length | REPORTING 1.5; decided 2026-09-25 |
| `ext-magic-mismatch` | the content's magic bytes identify a non-text format that the extension does not name (a `.md` whose bytes are a PNG). Text-versus-text disagreements (libmagic calling fenced markdown "JavaScript") are detector noise and are **not** flagged | REPORTING 1.6; REVIEW-2026-09-04 |
| `bom` | text file starting with a byte-order mark | REPORTING 1.7 |
| `archive` | archive in tree (zip, tar, gz, 7z, …), by magic bytes | REPORTING 1.7 |
| `symlink` | symbolic link in tree; `detail` gives its target | REPORTING 1.7 |

### Definitions

- **Frontmatter:** a leading `---` block. Parse with a YAML safe loader. Where a
  repo ships its own first-colon loader, also parse that way and record any
  disagreement (METHOD); v1 may record only the YAML reading.
- **Agent / command definition:** a markdown file whose frontmatter declares
  `tools` (list or comma string). `description` comes from the same block.
- **Hook config:** JSON whose top-level `hooks` object maps event names to lists
  of hook entries, in any host's format: Claude Code's nested
  `{matcher, hooks: [{type, command}]}` and the flat `{command}` form other hosts
  (Cursor) use. One `struct.hooks` row per entry per config file, so the same
  hook shipped for two hosts is two rows (decided 2026-09-25: each host's copy is
  what that host runs).
- **Platform manifest:** a JSON or YAML file declaring a plugin `name` and a tool
  or permission grant (`tools`, `permissions`, `allowedTools`, `capabilities`,
  or nested equivalents; `capabilities` confirmed as a grant 2026-09-25). Manifests sharing one `name` form a set. `divergent` is true when
  their declared tool / permission grants are not identical.
- **Entry-point kinds:** `skill` (`SKILL.md`), `agent` / `command` (definitions
  above, or files under `agents/` / `commands/`), `hook-config`, `manifest`,
  `mcp-config` (`.mcp.json`), `readme`, `ci` (workflow files).

## Must never

- Open a file for meaning, run anything from the input, or follow a symlink out
  of the input tree.
- Write inside `<input_dir>`.
- Fail the run because an optional tool is missing. `python-magic` needs libmagic;
  fall back to the pure-python `filetype` package and say so on stderr. A check
  that cannot run emits a skip finding (CONTRACT).
- Judge. A flag is a location and a measurement, never "suspicious".

## Done when

1. Every script in this folder has a `specs/<name>.SPEC.md` and pytest tests written
   from it, and they pass.
2. `python grader/grader.py 01` reports PASS.
3. Run on a real repo copy (`ReposToExamine/superpowers-main/`) it completes and
   reproduces the Case 001 composition numbers in REPORTING section 1 (195
   files, 18 extensions, 2 hook rows, 4 files over 50 KB, 14 files with a line
   over 500 characters, 0 BOMs, 0 symlinks, 0 archives), or the difference is
   explained.
