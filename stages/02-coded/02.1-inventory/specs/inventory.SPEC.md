# inventory: spec

One spec for the `02.1-inventory` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. Merged from the per-script specs in restructure step 8a.

## run

The single entry point for `02.1-inventory`. Wires `walk`, `census`, `frontmatter`,
`configs`, and `entrypoints` together and prints one contract-1 report
(`stages/CONTRACT.md`).

### Inputs

```
python stages/02-coded/02.1-inventory/run.py <input_dir>
```

### Outputs

stdout: one JSON document, UTF-8:

```json
{"stage": "02.1-inventory", "contract": 1, "findings": [...]}
```

Findings in this order: `inv.pin`; `inv.file` per entry (sorted path);
`struct.census` (per file in path order, flags in census order); then
`struct.description`, `struct.agent-tools`, `struct.hooks` (each in path
order); then `struct.manifests` (by name); then `struct.mcp`; then `inv.license`
(path order; the `licenses` section).

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

### Added 2026-10-04

Each `inv.file` carries `sha256`, the hash of the file's bytes (null for a symlink), so two
runs can tell exactly which files changed (`stages/06-report/specs/report.SPEC.md`, section `drift`).

Added 2026-10-20: a text file also carries `sha256_lf` and `sha256_crlf` (`text_hashes`), its
content hashed with every line ending as LF and as CRLF, so a checkout that only converted line
endings is not counted as an edit. Byte-level, so none for UTF-16 or UTF-32 text, and none for
binary files or symlinks. Test: `test_text_hashes_ignore_line_endings`.

### Added 2026-10-17

`inv.license` findings (license files and declared license fields), and `inv.pin` carries
`license_checked: true` so a report can tell "none found" from a run made before the check.

### What the step looked at (added 2026-10-30, M9 slice C)

The report has a `coverage` list (`stages/CONTRACT.md`, "Coverage lines"), five lines. A line holds the checks that read the same
files in one pass (`inspect_entry`), and a line counts the files its checks read.

| Checks | Unit | `of` | `looked_at` |
|---|---|---|---|
| `inv.pin` | `run` | 1 | once the pin is built |
| `inv.file`, `struct.census` | `files` | every file the walk lists, symlinks included, counted before the pass | each file whose facts and census flags are taken |
| `struct.hooks`, `struct.manifests`, `struct.mcp` | `files` | every JSON or YAML file (`configs.parses`) with text, and every one whose bytes cannot be read | `structure`, once for each of them with text |
| `inv.license` | `files` | every license file, file that can declare a license (`licenses.names_a_license`), and Markdown file, with text, and every one whose bytes cannot be read | `structure`, once for each of them with text |
| `struct.description`, `struct.agent-tools` | `files` | every Markdown file with text, and every Markdown file whose bytes cannot be read | `markdown_checks`, once for each Markdown file with text |

Whether a file has text is known only when its bytes are read, so the last three lines count their items after the pass, from the texts it
kept before it ran the checks (`text_items`), and each check counts a file where it has handled it (`cov.look`, inside
`structure` and `markdown_checks`). A picture or a binary has no config to parse, no license to read, and no frontmatter, whatever its name: it
is an item of the files line and of none of these. `explained` is a file whose bytes could not be read, with its `inv.file` skip, on the lines it
would have been an item of. A file the pass leaves out and writes no skip for leaves `looked_at` plus `explained` below `of`, and the
check of the run (`05-qa`) holds the run. One check in a line that stops while the others in it run shows only in the step's fixture
check. The tests are in `tests/test_coverage.py`, among them one that makes the pass leave a file out, one for each of the config, license,
and Markdown lines, one that a line counts only the files its checks read, and one with a picture and a binary.

### Must never

- Print anything but the report to stdout.
- Write anywhere, inside the input or out of it.
- Run anything from the input.

### Done when (each backed by a test in `tests/test_run.py`)

1. On a small mixed folder, stdout parses as a contract-1 report with stage `02.1-inventory`, and the exit code is 0.
2. The report carries `inv.pin` first, an `inv.file` row per file with every contract field, and the census, description, agent-tools, hook, and manifest findings for the folder's contents.
3. `extensions` and `script_languages` count the folder (a `#!/usr/bin/env bash` file without extension counts as `bash`).
4. An empty folder gives a report with `inv.pin` (0 files) and exit 0.
5. A missing folder exits non-zero without printing a report.
6. The input folder is byte-identical before and after a run.

## census

Per-file facts and structural flags. `02.1-inventory`, checks `inv.file` (all fields but
`entry_point`) and `struct.census`. Measures bytes; never reads for meaning.

### Inputs

- The bytes of one file, its relative path, and its exec bit (from `walk.py`).
- For a symlink: its relative path and target only (the link is not followed).

### Outputs

`file_facts(rel, data, exec_bit) -> Facts` with:

| Field | Rule |
|---|---|
| `ext` | lowercase text after the last `.` of the basename, no dot. A dotfile's name counts (`.gitignore` gives `gitignore`). No dot gives `""`. |
| `bytes` | `len(data)` |
| `magic` | MIME type the magic bytes identify as a **non-text** format, or None |
| `text` | True when `magic` is None and the bytes decode (rule below) |
| `encoding` | codec name for text (`utf-8`, `utf-16-le`, `utf-16-be`, `utf-32-le`, `utf-32-be`, or the charset-normalizer guess), None for binary |
| `bom` | True when a text file starts with a UTF-8, UTF-16, or UTF-32 byte-order mark |
| `lines` | text only: count of `\n` plus 1 if the text is non-empty and does not end in `\n`. None for binary |
| `type` | `magic` if set, else `text/plain` for text, else `application/octet-stream` |
| `exec` | the exec bit as given (False when unknown) |
| `text_value` | the decoded text (BOM removed), for other `02.1-inventory` parsers |

**Decoding:** a BOM picks the codec. Otherwise bytes with NUL are binary when NUL is more than 1% of the bytes or the rest is not strict UTF-8; a few NULs in valid UTF-8 are text (2026-10-09: a literal `\0` sentinel in source made a file binary, so one NUL could hide any file);
bytes that decode as UTF-8 are `utf-8`; else charset-normalizer's best guess, if
installed and it finds one; else binary.

**Magic detection** (`detect_magic(data)`): python-magic if importable, else the
`filetype` package if importable, else a built-in signature table (PNG, JPEG,
GIF, WebP, BMP, ICO, TIFF, PDF, ZIP, gzip, bzip2, xz, 7z, RAR, zstd, tar,
ELF, PE, Mach-O, WebAssembly, SQLite, Java class). `magic_backend()` names the
backend in use. Any backend result that is `text/*` or absent counts as None:
text-versus-text is detector noise and never a finding.

`census_flags(rel, facts) -> list[finding]`, each a `struct.census` finding:

| Flag | When | `line` | `detail` |
|---|---|---|---|
| `reader-window` | text file with more than 2000 lines or more than 50,000 bytes; one finding per file | null | each exceeded threshold with the measured value |
| `long-line` | each text line longer than 500 characters (decoded, line ending excluded) | the line | line number and length; `length` field too |
| `ext-magic-mismatch` | `magic` is set and the extension is not one that names that format (table in code: `png` for `image/png`, `zip`/`docx`/`jar`/... for `application/zip`, and so on) | null | extension and detected type |
| `bom` | `bom` is True | null | which BOM |
| `archive` | `magic` is an archive type (zip, gzip, bzip2, xz, 7z, RAR, zstd, tar) | null | detected type |
| `padding` | text that follows 20 or more blank lines (`kind` `vertical`), or follows 80 or more blank characters inside a line (`kind` `horizontal`); blank is Unicode white space or the blank braille cell; indentation at a line's start and a run that ends at `\|` (a table's column padding) are not runs (`padding_runs`; added 2026-11-03, SkillSpector P9, S20) | where the text resumes | the run; `kind` and `length` fields too |
| `executable` | `magic` is a program in compiled form (`EXECUTABLES`: ELF, Windows PE, Mach-O, and the names other backends give them), whatever the file is called (added 2026-11-03, SkillSpector SC9) | null | detected type; `detected` too |
| `bytecode` | a `.pyc` or `.pyo` file, or a file under a `__pycache__` folder: Python runs it without its source (added 2026-11-03, SkillSpector SC8) | null | fixed words |
| `archive-executable` | a zip container (an archive, or an Office or OpenDocument file, a jar, a wheel), or a tar archive, plain or compressed with gzip, bzip2, or xz (added the same day: read as a stream, stopping past 64 MB unpacked, `INSIDE_UNPACK_BYTES`, so what lies past that is not read) or zstd (2026-11-04, through `zstandard`), or a 7z or RAR archive (2026-11-04, `archive_index.py`: names from the archive's own headers; a 7z member's first bytes where its folder's coders are LZMA, LZMA2, Deflate, BZip2, Copy, Delta, or a BCJ filter other than BCJ2 and ARM64, unpacked in order up to the same 64 MB; a RAR member's first bytes when it is stored, since RAR's compression is not one Python decodes; an archive with encrypted headers gives none), holding members that are programs by name (`INSIDE_EXTS`), Python bytecode, Office macros (`vbaProject.bin`), or programs by their first 64 bytes (`programs_inside`: names and first bytes only, nothing extracted, at most 5,000 members; a container that does not open gives none; added 2026-11-03, SkillSpector SC9) | null | how many and the first five names; `members` (up to 50) and `count` too |

`symlink_facts(rel, target)` returns the `inv.file` facts for a symlink
(`type` `inode/symlink`, `bytes` = UTF-8 length of the target, no encoding, no
lines, `exec` False) and `symlink_flag(rel, target)` the `symlink` census
finding with the target as `detail`.

### Must never

- Judge. A flag is a location and a measurement, never a verdict.
- Flag a text-versus-text disagreement (markdown opening with a code fence).
- Fail when python-magic, filetype, or charset-normalizer is missing.

### Done when (each backed by a test in `tests/test_census.py`)

1. Extension rule: `a.MD` gives `md`, `.gitignore` gives `gitignore`, `LICENSE` gives `""`, `x.tar.gz` gives `gz`.
2. UTF-8, UTF-8 with BOM, and UTF-16 with BOM decode, report encoding and BOM; NUL bytes without BOM are binary, except a few NULs in valid UTF-8, which are text.
3. Line count follows the rule, including a missing final newline and an empty file.
4. PNG bytes in a `.md` give `ext-magic-mismatch`; the same bytes in a `.png` do not.
5. A markdown file opening with a code fence gives no `ext-magic-mismatch` and type `text/plain`.
6. ZIP bytes give `archive`; in a `.zip` no mismatch, in a `.md` both flags.
7. A 2001-line file and a 50,001-byte file each give one `reader-window`; 2000 lines and 50,000 bytes give none.
8. A 501-character line gives `long-line` at its line number; 500 does not.
9. A BOM file gives the `bom` flag.
10. A symlink gives `inode/symlink` facts and a `symlink` flag with its target.
11. The built-in signature table recognizes PNG, ZIP, gzip, PDF, and tar.
12. Padding: 20 blank lines before text give a `vertical` run at the line where text resumes, 19 or trailing blank lines give
    none; 80 blank characters (a no-break space, a blank braille cell) before text in a line give a `horizontal` run, 79 give
    none, and neither indentation nor a table's column padding is a run
    (`test_blank_lines_before_text_are_vertical_padding_and_fewer_or_trailing_are_not`,
    `test_blank_characters_before_text_are_horizontal_padding_and_tables_and_indentation_are_not`). Measured first on nine
    repositories (three skill collections, four MCP servers, SkillSpector, Cloudflare's skill): every horizontal run was a
    table's column padding before that rule, and none is flagged after it.
13. An ELF, PE, or Mach-O file is `executable` and a `.pyc` or a file in `__pycache__` is `bytecode`; a zip document names the
    macros, programs, bytecode, and ELF-headed members inside it, a plain one names none, and a container that does not open
    gives none (`test_a_program_in_compiled_form_is_flagged_by_its_bytes_and_bytecode_by_its_name`,
    `test_a_zip_container_names_the_programs_inside_it_and_a_plain_one_names_none`). Fixtures `tool.bin`,
    `__pycache__/helper.cpython-312.pyc`, `macros.docx`, and `plain.docx` in `class18-reader-limit`
    (`tools/fixture-generators/make_program_binaries.py`). On the nine repositories, none of the three flags fired.
14. A tar, plain or compressed with gzip, bzip2, or xz, names the programs and bytecode inside it, and one holding text names none
    (`test_a_tar_names_the_programs_inside_it_plain_or_compressed`); a tar stops at its budget, and a gzip that is no tar gives none
    (`test_a_tar_stops_at_its_budget_and_a_gzip_that_is_no_tar_gives_none`; a 1 MB gzip that unpacks to 1 GB took 0.01 s). Fixtures
    `bundle.tar.gz` and `plain.tar.gz`. The one tar in the nine repositories (`anthropics/skills`, 49 TypeScript files) holds none.
15. 2026-11-04: a 7z, a RAR (4 or 5), and a zstd tar name the programs and bytecode inside them, and ones holding text name none
    (`test_a_7z_names_the_programs_inside_it_read_from_its_headers`,
    `test_a_rar_names_its_programs_and_reads_a_stored_members_first_bytes`,
    `test_a_rar4_names_its_programs_and_a_compressed_member_by_name_only`, `test_a_zstd_tar_names_the_programs_inside_it`); a 7z
    stops unpacking at its budget and its names still count; a 7z header Python cannot unpack, or a RAR with encrypted headers,
    gives none; without a zstd library a zstd tar is not read; every cut or damaged byte of each fixture reads without an error
    (`test_a_cut_or_damaged_archive_never_raises`). Fixtures `bundle.7z`, `plain.7z`, `bundle.rar`, `plain.rar`, `bundle.tar.zst`,
    `plain.tar.zst`, written byte by byte by `make_program_binaries.py`; 7-Zip 23.01 tests the 7z and RAR fixtures whole. None of
    the nine repositories holds a 7z, RAR, or zstd file, so the reader was measured on archives made by 7-Zip 23.01 (23 archives:
    its default and `-mx` 1 to 9, LZMA, LZMA2, Deflate, BZip2, PPMd, Copy, Delta, BCJ, BCJ2, ARM64, no solid, an unpacked header,
    encrypted contents, encrypted headers), where its names matched 7-Zip's listing in every archive but the one with encrypted
    headers and no first bytes it read differed from the file's; and on rarfile 4.5's 50 sample RARs (RAR 1.5 to 5), where its
    names matched rarfile's except for older versions of a file, members in other volumes, and links to folders, and the
    stored members' first bytes matched rarfile's. 11,100 cut or damaged copies raised no error, the slowest took 0.06 s, and
    a 7z holding 1.5 GB of zeros took under 0.01 s and 13 MB.

## configs

Parses hook configs and platform manifests. `02.1-inventory`, checks `struct.hooks` and
`struct.manifests`. Parsing only; no command is run and no referenced script is
opened.

### Inputs

- The decoded text and relative path of a `.json`, `.yaml`, or `.yml` file.

### Outputs

`parses(rel) -> bool`: the name is one `load` reads, `.json`, `.yaml`, or `.yml`.

`load(rel, text) -> object | None`: `json.loads` for `.json`, `yaml.safe_load`
for `.yaml` / `.yml`; None on any parse error or other extension.

#### Hooks

`is_hook_config(doc)`: `doc` is a JSON object whose `hooks` value is an object
with at least one event name mapping to a list.

`hook_findings(rel, doc) -> list[finding]`: one `struct.hooks` finding per entry
in each event's list, in file order:

- `event`: the event name. `matcher`: the entry's `matcher` verbatim, or None
  when the entry has none.
- Claude Code shape (`{matcher, hooks: [{type, command}]}`): `command` is the
  inner commands joined with a newline; `commands` lists them; `types` lists
  each inner `type`; `async` lists each inner `async` value where present.
  `format` is `nested`.
- Flat shape (`{command, matcher?}`, used by some other hosts): `command` is
  the entry's command; `format` is `flat`.
- `file` = `rel`, `line` = null (JSON gives no positions).

#### Manifests

`manifest_grants(doc) -> list[str] | None`: None unless `doc` is an object with
a string `name`. Otherwise the sorted set of grant tokens found under any key
named `tools`, `permissions`, `allowedTools`, `allowed_tools`, `allowed-tools`,
or `capabilities`, at any depth:

- a list item gives its string form;
- inside a grant, an object's key with value `true` gives the key, a list
  recurses into its items, an object recurses, any other value gives `key=value`
  (JSON spelling: `network=false`).

`is_manifest(rel, doc)`: `doc` has a string `name`, and it either declares at
least one grant key (even empty) or its basename is a known plugin manifest
(`plugin.json`, `plugin.yaml`, `plugin.yml`, `marketplace.json`,
`gemini-extension.json`).

`manifest_findings(manifests) -> list[finding]`: `manifests` is a list of
`(rel, name, grants)`. Groups by `name`; one `struct.manifests` finding per
group, sorted by name: `file` null, `line` null, `name`, `files` (sorted),
`grants` ({file: tokens}), `divergent` True when the token sets are not all
identical (a set of one is never divergent).

Where the words sit (added 2026-11-01), for the mask of a line the secret scan flags in a later step (`stages/_shared/secretmask.py`).
A parser's value has lost its lines, so `hook_findings` and `mcp_findings` take the file's text as well, and find them with `spans`:

- a `struct.hooks` row has `span`, the first and last line of its entry, and `event_line`, the line of its event's key. `line` stays
  null for a nested or flat hook: an entry can run over many lines, and every reader takes a null line to mean a config;
- a Cursor row has `span` and `event_line` from its command's value, or from its `terminals` entry;
- a `struct.mcp` row has `span`, from the server's name to the end of its entry.

A row whose file does not compose has neither, and the mask takes the whole file. `struct.manifests` has none: it is one row across
the manifests of a plugin.

### Must never

- Run a hook command or open the script it names.
- Judge a grant. `divergent` is a comparison, not a verdict.

### Done when (each backed by a test in `tests/test_configs.py`)

1. A Claude Code hooks file with two events gives one finding per matcher entry with event, matcher, and command.
2. A flat entry without a matcher gives `matcher` None and `format` `flat`.
3. JSON with no `hooks`, an empty `hooks` object, or unparsable text is not a hook config.
4. Grants from `tools: [...]` and from `permissions: {allowedTools: [...], network: true}` flatten to tokens.
5. Two manifests with one name and different grants give one finding with `divergent` True; identical grants give False; different names give two findings.
6. A `plugin.json` with a name and no grant is a manifest; a `package.json` with a name and no grant is not.
7. A YAML manifest loads through the safe loader.
8. A `.cursor/environment.json` gives one `struct.hooks` row per command (`install`, `start`, each
   `terminals` entry with a command) with the line of its key, `format` `cursor-environment`, and
   `host` `cursor-cloud`; the same keys at another path, a non-object, or a file with no command give
   none (`test_cursor_environment_commands_are_host_run_rows`).
9. A hook says the lines of its entry and of its event's key, with `line` still null
   (`test_a_hook_says_the_lines_of_its_entry_and_of_its_event_and_keeps_a_null_line`), a YAML block command reaches its last line
   (`test_a_yaml_hook_with_a_block_command_reaches_its_last_line`), a text that does not compose gives no place
   (`test_a_hook_in_a_text_that_does_not_compose_or_with_no_text_has_no_place`), and a Cursor row and an MCP server say theirs
   (`test_a_cursor_row_says_where_its_command_or_its_terminal_is`, `test_a_server_spans_from_its_name_to_the_end_of_its_entry`).

### Added 2026-09-29: MCP servers

`mcp_findings(rel, doc)`: one `struct.mcp` per entry under a top-level `mcpServers`
mapping in any parsed config: `name`, `transport` (`type`, else `http` when a `url`
is given, else `stdio`), `command` (command plus args), `url`, `env_keys` (sorted
names; values are never recorded). Test: `test_mcp_servers_from_any_config`.

### Added 2026-10-17: Cursor cloud-agent setup (review C31)

`is_cursor_env(rel)`: the path ends in `.cursor/environment.json`. `cursor_env_findings(rel, doc,
text)`: for that file only, one `struct.hooks` row per command, in this order: `install`, `start`,
then each `terminals` entry that has a `command` (`event` `terminal: <name>`). `line` is the line of
the command's key in the text; `matcher` None; `commands` and `types` as the nested format;
`format` `cursor-environment`; `host` `cursor-cloud`. `run.py` treats the file as a hook config, so
it is an entry point (`hook-config`).

Why (Cursor's docs, cursor.com/docs/cloud-agent/setup, read 2026-10-17): a committed
`.cursor/environment.json` is used automatically for Cursor's cloud agents on the repository, ahead
of saved settings. `install` runs when Cursor builds the agent's machine; `start` and the
`terminals` run each time an agent boots. All of it runs on Cursor's isolated cloud machines, never
on the user's own computer, and self-hosted machines never read the file. A command the host runs
without anyone asking is a hook in all but name; `host` keeps where it runs, so the report can say
it does not run on the user's computer.

## entrypoints

Names the entry-point kind of each file. `02.1-inventory`, field `inv.file.entry_point`.
`02.3-graph` starts its graph from this list.

### Inputs

`classify(rel, *, is_symlink, has_tools, is_hook_config, is_manifest)`:
the relative path plus facts other `02.1-inventory` scripts already parsed
(frontmatter declares tools; parsed hook config; parsed manifest).

### Outputs

One of `skill`, `agent`, `command`, `hook-config`, `mcp-config`, `ci`,
`manifest`, `readme`, `project-instructions`, or None. First rule that holds wins:

1. A symlink: None (`02.1-inventory` never follows it).
2. `skill`: basename `SKILL.md`, or ending `.SKILL.md` (any case).
3. `agent` / `command`: a markdown file whose frontmatter declares tools, or a
   markdown file with an `agents` or `commands` folder in its path. `command`
   when a `commands` folder is in the path, else `agent`.
4. `mcp-config`: basename `.mcp.json`.
5. `hook-config`: the file parsed as a hook config (`configs.py`).
6. `ci`: `.github/workflows/*.yml|yaml`, `.gitlab-ci.yml`, `.circleci/config.yml`,
   `azure-pipelines.yml`, `.travis.yml`, `Jenkinsfile`. (v1 marks every CI
   workflow; which ones invoke an agent is a `02.3-graph` question.)
7. `manifest`: the file parsed as a manifest (`configs.py`).
8. `readme`: basename starting with `README` (any case).
9. `project-instructions`: `CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`,
   `GEMINI.md`, `.cursorrules`, `.windsurfrules`, `.clinerules` (any case,
   any folder), `.github/copilot-instructions.md`, markdown under
   `.cursor/rules/`: files a harness loads by itself when someone works in the
   repository (added 2026-09-29, Case 004).

Subagent prompt templates (files a `SKILL.md` names as a template) need the
reference graph, so `02.3-graph` adds them.

### Must never

- Open a file. It classifies from the path and from facts it is handed.

### Done when (each backed by a test in `tests/test_entrypoints.py`)

1. `skills/x/SKILL.md` and `pos.SKILL.md` are `skill`.
2. A markdown file with tools outside `agents/` is `agent`; `commands/x.md` is `command`; `agents/x.md` without tools is `agent`.
3. `.mcp.json`, a hook config, a workflow file, a manifest, and `README.md` each get their kind.
4. A workflow file that also parses as a manifest is `ci`.
5. A symlink named `SKILL.md` and an ordinary file are None.
6. `CLAUDE.md`, `sub/AGENTS.md`, `.cursorrules`, `.github/copilot-instructions.md` are `project-instructions`.

## frontmatter

Parses a leading frontmatter block and reports its `description` and granted
tools. `02.1-inventory`, checks `struct.description` and `struct.agent-tools`.

### Inputs

- The decoded text of one markdown file (`.md`, `.markdown`, `.mdx`, `.mdc`)
  and its relative path.

### Outputs

`parse(text) -> Frontmatter | None`. None when the first line is not exactly
`---` (trailing whitespace allowed). Otherwise:

- `start_line`: 1. `lines`: the raw lines between the opening `---` and the
  closing line (`---` or `...`). A block with no closing line is None.
- `yaml`: the `yaml.safe_load` mapping, or None; `yaml_error`: the error text if
  the load failed or did not give a mapping.
- `first_colon`: a mapping from a first-colon split: each line of the form
  `key: value` at column 0 gives `key` and the value stripped of whitespace and
  one pair of matching surrounding quotes. Indented and non-matching lines are
  ignored.
- `key_line(key)`: the 1-based file line where `key:` starts at column 0, or None.
- `where(*keys)` (added 2026-11-01): `[first line, last line]` in the file of these keys' values, for the mask of a line the secret
  scan flags (`spans`): a block value runs past its key's line, and a quoted one can return to the margin. When the YAML did not parse it
  is the whole frontmatter: the words come from a line a parser cannot place, and its error (`yaml_error`) quotes a line a parser
  chose. None when the frontmatter has none of the keys. A key that cannot be placed gives the whole frontmatter as well.

`description_finding(rel, fm) -> finding | None`: when either loader has a
`description`:

- `check` `struct.description`, `file`, `line` = `key_line("description")`, `span` = `where("description")`.
- `text`: the YAML value verbatim (non-strings converted with `str`); when YAML
  failed, the first-colon value, and `loader` is `first-colon` instead of `yaml`.
- `loaders_disagree`: True when both loaders gave a value and they differ, or
  only one did. `first_colon_text` carries the first-colon value when they
  disagree.

`tools_value(fm) -> (field, list) | None`: the granted tools from `tools`, else
`allowed-tools`, else `allowedTools`. A list gives its items as strings. A
string splits on commas when it has one, otherwise on whitespace outside
parentheses; items are stripped and empties dropped.

`agent_tools_finding(rel, fm, kind) -> finding`: `check` `struct.agent-tools`,
`file`, `line` = the tools key line (None when absent), `tools` (list, or None
when the definition declares none), `description` (YAML value or first-colon
value, None if absent), `field` (which key), `kind` (`agent`, `command`, or
`skill`), `span` = `where` of the description and the tools key, when it has either.

### Must never

- Execute or construct objects from YAML (safe loader only).
- Rewrite, trim, or normalize a description beyond what the loader returns.

### Done when (each backed by a test in `tests/test_frontmatter.py`)

1. A file without a leading `---`, or with an unclosed block, gives None.
2. A quoted description comes back unquoted and otherwise verbatim, with the line of its key.
3. A description with an unquoted `: ` that breaks YAML is still reported, via the first-colon loader, with `loader` `first-colon`.
4. A folded (`>`) description gives the YAML text and `loaders_disagree` True.
5. `tools` as a YAML list and as a comma string both give the same list.
6. `allowed-tools` with a space-separated value splits outside parentheses (`Bash(git add:*) Read` gives two items).
7. `agent_tools_finding` pairs the tools with the description and the tools line.
8. A description says every line it reaches, from one line, a block, a folded block, a quoted value back at the margin, or a quoted
   key (`test_a_description_says_every_line_it_reaches`); with YAML that failed it says the whole frontmatter
   (`test_with_yaml_that_failed_a_description_says_the_whole_frontmatter`); a tools row spans its description and its list on their
   own lines (`test_a_tools_row_spans_its_description_and_its_list_on_their_own_lines`).

## licenses

Finds the licenses a repository states. `02.1-inventory`, check `inv.license` (added
2026-10-17, from class demo feedback: "add the license info of the repo you are
investigating"). Matching a license file against fixed license wording is a
lookup, like magic bytes: it says which known license text a file carries, never
what the license allows. Walkdown gives no legal advice.

### Inputs

- A file's relative path and decoded text (license files, manifests,
  `pyproject.toml` / `Cargo.toml`).
- A parsed frontmatter block (markdown files).
- A parsed JSON / YAML document (`configs.load`).

### Outputs

`names_a_license(rel) -> bool`: the file's name alone puts it in front of this check: a license file, or a
file that can declare a license (`DECLARING`, `DECLARING_TOML`). Markdown frontmatter is the other place the check reads.

`is_license_file(rel) -> bool`: the file name (any folder, case ignored) is
`LICENSE`, `LICENCE`, `COPYING`, `UNLICENSE`, or `COPYRIGHT`, alone or followed
by `.`, `-`, or `_` and more (`LICENSE.md`, `LICENSE-MIT`, `COPYING.LESSER`).
A name ending in a code or config extension (`license.py`, `license.json`) is not
a license file.

`identify(text) -> (id | None, how | None)`: the SPDX id of the license the text
carries, and how it was found, in this order:

1. `spdx-tag`: an `SPDX-License-Identifier:` line gives the id verbatim.
2. `text`: fixed wording, matched on the text lowercased with runs of white space
   folded to one space. Licenses whose own text names another (GPL-3.0 mentions
   the Affero license) are decided by their title in the first 1,000 characters.
   Known: AGPL-3.0, LGPL-3.0, LGPL-2.1, LGPL-2.0, GPL-3.0, GPL-2.0, MPL-2.0,
   Apache-2.0, BSL-1.0, Unlicense, CC0-1.0, the CC BY 4.0 family, MIT, ISC,
   0BSD, BSD-3-Clause, BSD-2-Clause.
3. `title`: no wording matched but the first 1,000 characters name a known
   license (`MIT License`).

Otherwise `(None, None)`.

`normalize_declared(value) -> id | None`: a declared license string that equals
a known id, ignoring case, an `-only` / `-or-later` / `+` suffix, and the
spellings `Apache 2.0` / `Apache License 2.0` / `Apache License, Version 2.0`,
gives that id (GPL-3.0-or-later gives GPL-3.0). Anything else gives None.

`file_finding(rel, text) -> finding`: `{"check": "inv.license", "file": rel,
"line": null, "source": "file", "field": null, "license": id, "how": how,
"stated": ...}`. `stated` is null when the license was identified, otherwise the
first non-empty line, trimmed to 200 characters, so the reader sees what the
file says.

`field_findings(rel, text, doc, fm) -> list[finding]`: declared license fields,
`source` `field`, `how` `field`, `stated` the value verbatim, `license` from
`normalize_declared`:

- a frontmatter `license` key (`line` = its line);
- the top-level `license` of `package.json`, `plugin.json` / `.yaml` / `.yml`,
  `marketplace.json`, `gemini-extension.json`, `composer.json`, `manifest.json`
  (a string, or an object's `type`);
- `pyproject.toml`: `project.license` (a string, or a table's `text`; a table's
  `file` is recorded as `file: <path>`) and `tool.poetry.license`;
- `Cargo.toml`: `package.license`.

`field` names the key (`license`, `project.license`, ...).

### Must never

- Read a file that is not a license file by name, or a README, for a license.
- Say what a license permits, or call one good or bad.
- Fail on a file it cannot parse: it gives no finding.

### Done when (each backed by a test in `tests/test_licenses.py`)

1. License file names are recognized in any folder and in any case; code and
   config files named `license` are not.
2. MIT, Apache-2.0, BSD-3-Clause, BSD-2-Clause, ISC, and the Unlicense are
   identified from their wording; an SPDX tag wins over wording.
3. GPL-3.0 text that mentions the Affero license is GPL-3.0; AGPL-3.0 and
   LGPL-2.1 are told apart by title.
4. An unrecognized license file gives `license` null and its first line in
   `stated`.
5. Declared fields: frontmatter (with its line), `package.json` string and
   object forms, `pyproject.toml` string and table forms, `Cargo.toml`; an
   unknown declared value keeps `stated` and gives `license` null.
6. `normalize_declared` maps the listed spellings and suffixes.

## spans

Where a parsed value sits in its file (added 2026-11-01). The mask of a line the secret scan flags goes by the lines a finding quotes,
and a parser's value has lost them.

### Inputs

- The decoded text of a JSON or YAML file, or of a frontmatter block.

### Outputs

- `compose(text)`: the document's nodes, by `yaml.compose` with the safe loader, or None when the text is empty or does not compose.
  YAML refuses a tab that indents a JSON file, and takes a lone CR, U+0085, U+2028, and U+2029 for a line break where every other
  step reads them as part of a line (`readtext.split_lines`). Each is read as a space here, which keeps each line number and column;
  only where a value sits is read from this text.
- `pair(node, step)`: (key node, value node) of a key of a mapping, the last of a repeated key as the parsers take it, or (None, value
  node) of a position in a list; (None, None) when it is not there.
- `at(node, *path)`: the node at a path of keys and list positions, or None.
- `first_line(node)`, `last_line(node)`: 1-based. A block's end mark stands at whatever comes next, so with only white space before the
  mark on its line, the node ended above it. A blank line after a block can count as its last: it cannot be flagged.
- `span(node, key=None, offset=0)`: `[first line, last line]`, from the key when one is given, or None with no node. `offset`: for a
  text that starts later in its file.

### Must never

- Read a value from the text it was given: a space in place of a character changes the value, and only `configs` and `frontmatter` read
  values, from what the file says.

### Done when (each backed by a test in `tests/test_spans.py`)

1. A JSON value is found with its lines, from one line or many, and minified JSON is one line.
2. Tabs, a lone CR, U+0085, and U+2028 keep every line number, and CRLF counts as one line ending.
3. A block ends above what comes next, and one at the end of a text keeps its last line.
4. A key above its value starts the span, an offset moves the lines, what does not compose or is not there is None, and a repeated key is
   the last.

## walk

Lists what ships in an input folder and pins it. `02.1-inventory`, check `inv.pin`.

### Inputs

- `input_dir`: a folder (pinned repo copy or fixture folder). Read-only.

### Outputs

`walk(input_dir) -> Walk` with:

- `root`: the resolved input folder.
- `entries`: one `Entry` per shipped path, sorted by `rel`:
  - `rel`: path relative to `root`, forward slashes.
  - `kind`: `file` or `symlink`.
  - `target`: the link target string for a symlink, else None.
  - `exec_bit`: bool, or None when unknown.
  - `exec_source`: `git-index`, `stat`, or `stat-windows`.
  - `eol_committed` (git mode only, 2026-10-26): the line endings as committed, from `git ls-files
    --eol` (`lf`, `crlf`, `mixed`, `none`, `-text`), never as this checkout wrote them: Git for
    Windows can write CRLF for a file committed with LF. `02.1-inventory` copies it onto `inv.file`.
- `hash`, `hash_kind` (`git` or `sha256`).
- `channel`: `git` or `directory`.
- `untracked`: in git mode, the number of files present in the work tree but
  not tracked (not inventoried). 0 in directory mode.
- `notes`: list of strings for stderr.

`pin_finding(walk, files, bytes_total) -> dict`: the `inv.pin` finding
(`check`, `file`: null, `line`: null, `source`, `hash`, `hash_kind`, `files`,
`bytes`, plus `channel` and `untracked`).

### Rules

1. **Git mode** only when `input_dir` is itself the top level of a git work tree
   (`git rev-parse --show-toplevel` resolves to the same folder). A folder that
   merely sits inside some other repository is directory mode. Git runs with
   `-c core.fsmonitor=false` and only read commands (`rev-parse`, `ls-files -s`),
   so no hook, filter, or fsmonitor from the input runs.
   - Entries: tracked paths from `git ls-files -s -z`. Mode `120000` is a
     symlink, `100755` sets `exec_bit`, `160000` (submodule) is skipped with a
     note. Tracked paths missing from disk are skipped with a note.
   - `hash`: `git rev-parse HEAD`, `hash_kind` `git`.
   - If git is missing or fails, fall back to directory mode with a note.
2. **Directory mode**: walk with `os.scandir`, never following a symlink or a
   Windows junction. A root-level `.git` folder is not walked.
   - `exec_bit`: `st_mode & 0o100`. On Windows the bit is derived from the file
     extension by the OS, so `exec_source` is `stat-windows` and a note says so.
   - `hash`: sha256 over, for each entry in sorted `rel` order,
     `rel` (UTF-8) + `\0` + sha256(content) + `\n`, where content is the file bytes
     or, for a symlink, the target string in UTF-8. `hash_kind` `sha256`.
3. A symlink's target is read with `readlink` and never followed. The Windows
   extended-path prefix `\\?\` is removed from the target string.

### Must never

- Follow a symlink or junction, or read anything outside `input_dir`.
- Write inside `input_dir`.
- Run a git command that can execute repository-configured programs.

### Done when (each backed by a test in `tests/test_walk.py`)

1. A plain folder lists every file, sorted, with forward-slash paths, and pins
   with `hash_kind` `sha256`.
2. The sha256 pin changes when a file's content or name changes and is stable
   otherwise.
3. A folder inside a git repository, but not its top level, is directory mode.
4. A git top level lists only tracked files, pins HEAD, and counts untracked files.
5. A symlink is listed as `symlink` with its target and is not followed (skipped
   where the platform cannot create symlinks).
6. `pin_finding` carries every contract field.

## History

- 2026-10-30: M9 slice C: the report has a `coverage` list (the `run` section, "What the step looked at"), and the loop over the walk's entries is the function `inspect_entry` so that a file a check passes over can be counted where the check handles it. The findings are unchanged.
- 2026-10-30: M9 slice B: this step writes its notes through `stagenote`, so a note that names a file or a path from the repository is one line, and a name with a line break cannot pass for a note of its own.
- 2026-10-31: M9 slice C, fix round: the files line is three lines, one for each set of files the checks handle (every entry; every file that is not a symlink; every Markdown file), so no check names a file it does not handle. The findings are unchanged.
- 2026-10-31: M9 slice C, last fix round: the structure and Markdown lines count the files with text (they counted every file that is not a symlink, and every Markdown name), where the facts say so, before the checks work on the file. `structure` and `markdown_checks` are the parts of `inspect_entry` they count in. The findings are unchanged.
- 2026-10-31: M9 slice C, the verifier's last must-fix: the line of the hook, manifest, MCP, and license checks is two lines, because it counted every file with text and these checks read far fewer: JSON and YAML files for the first three, and license files, files that can declare a license, and Markdown for the last. The three lines that depend on a file's text count their items after the pass.
- 2026-11-01: `spans`, and `span` and `event_line` on `struct.description`, `struct.agent-tools`, `struct.hooks`, and `struct.mcp`, so a
  later step can mask a value that runs over several lines or has no line of its own. The checks and their counts are unchanged, and
  `line` is what it was. `configs.hook_findings` and `mcp_findings` take the file's text.
