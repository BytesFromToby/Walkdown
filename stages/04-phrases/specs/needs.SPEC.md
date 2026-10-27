# needs.py: spec

What a repository needs to run, and what ties it to one machine (plan for builders, slice 2,
owner 2026-10-26; the slice spec is `pre-planning/SPEC-SLICE2-2026-10-26.md`). Stage 4 calls it
with the texts it reads and stage 1's inventory; it runs, imports, and installs nothing. A skill's
`compatibility` field is read from its own frontmatter (`compatibility`). Test data
(`audience.is_test_data`) is left out throughout.

## Data: `tools.yaml`

The programs Walkdown recognizes (only these count, so an ordinary word is never a program), the
system a program exists on when it is one system's only (`unix`, `macos`, `linux`, `windows`),
the import names whose package has another name (`yaml` is PyYAML, `pdfminer` is pdfminer.six),
Node's built-in modules, and home-folder names that are not a person's (CI runners, containers,
placeholders). Dated; a program missing from the list is missed until it is added.

## What it needs

**`need.command`**, one per program used, sorted by name: `command`, `os` (from `tools.yaml`),
`uses` (each `{file, line, how}`), `declared`, `declared_in`. A program is used:

- in a script (`audience.SCRIPT_EXTS`, a shell shebang, or a PowerShell or batch file): a shell
  line's word at command position (after `sudo`, `env`, variable assignments; after `|`, `&&`,
  `||`, `;`, `$(`), `how: script`; in Python, the command of a `subprocess` call, `os.system`,
  `os.popen`, or `shutil.which`; in JavaScript, of `exec`, `execSync`, `spawn`, `execFile`;
- in instructions (a Markdown file the AI reads): each line of a fenced block marked `sh`, `bash`,
  `shell`, `console`, `zsh`, or unmarked, at command position (a leading `$` or `>` prompt
  dropped); inline code that starts with a known program and a space; `how: instructions`;
- in a hook command (stage 1 `struct.hooks`), `how: hook`; as an MCP server's command
  (`struct.mcp`), `how: mcp`.

**`need.package`**, one per package imported, sorted: `package`, `ecosystem` (`python`, `node`),
`files`, `declared`, `declared_in`. Python: top-level `import x` and `from x import` in `.py`
files, not the standard library (`sys.stdlib_module_names`), not a relative import, not a module
the repository holds anywhere (an `x.py`, or a folder of `.py` files named `x`; a script can reach
another folder's module through `sys.path`), named by `tools.yaml` where the package's name
differs. JavaScript and TypeScript: `require`, `import ... from`, `import()`, not relative, not
`node:` or a built-in, not a path alias (`~/`, `#`, `$`, `@/`); a scoped package keeps its scope.

**Declared** means named in a dependency file (`requirements*.txt`, `pyproject.toml` project,
optional, group, and Poetry dependencies, `Pipfile`, `setup.py` `install_requires`, `package.json`
dependencies of every kind, a script's own `# /// script` metadata), in a skill's
`compatibility` field, or on an install line (`pip`, `uv`, `npm`, `pnpm`, `yarn`, `bun`, `brew`,
`apt`, `dnf`, `yum`, `pacman`, `winget`, `choco`, `scoop`, `cargo`, `go`, `gem`, `pipx`) in a
README, an INSTALL file, or a `SKILL.md`. Names are compared lower case with `-`, `_`, and `.`
alike; one declaration covers `python`, `python3`, and `py`, and `pip` and `pip3`. Nothing else:
a word in prose is not a declaration.

## What ties it to one machine

Each with `file` and `line` (null for a whole file), sorted by check, file, line:

- `port.path` (`kind` windows, macos, linux; `quote`): `C:\Users\<name>\`, `/Users/<name>/`,
  `/home/<name>/` where the name starts with a letter and is not in `not_personal`; only in files
  that run or that the AI reads (not ones written for people: a path in notes ties nothing to a
  machine; measured 2026-10-26, 116 of them in one repository's design notes).
- `port.crlf`: a shell script with Windows line endings. In a git checkout, the line endings as
  committed (stage 1 `eol_committed`, `crlf` or `mixed`), never as this checkout wrote them (Git
  for Windows can write CRLF for a file committed with LF); in a plain folder, the bytes.
- `port.os` (`os`, `why`, and `command` for a program): a shell script (`unix`), a PowerShell or
  batch script (`windows`), and each use of a program `tools.yaml` marks as one system's.
- `port.backslash` (`written`, `file_named`): in text the AI reads, a reference written with
  backslashes that names a file in the repository once they are slashes.
- `port.exec` (`script`): a script run directly by its path (first in an instruction or hook
  command, after `./` or `${CLAUDE_PLUGIN_ROOT}/`) whose mode git records as not executable;
  never from a plain folder, whose modes say nothing on Windows.
- `port.python`: an instruction or hook that runs `python` (macOS and many Linux systems have only
  `python3`).

Stage 4 adds these findings last, after part 2.

## Must never

- Count a word as a program unless `tools.yaml` lists it; call something declared because a word
  appears in prose; run, import, or install anything.

## Done when

1. Fixture `needs-repo` (grader 04, rows `needs-*`): programs used and declared or not, packages
   declared or not, the standard library and the repository's own module left out, each
   portability kind, and the negatives (`make` in prose, a placeholder path).
2. `tests/test_needs.py`: command position across pipes, prompts, `sudo`, and assignments;
   Python and JavaScript calls; every declaration source; a module held in another folder is
   not a package; CRLF from git's record over the bytes; a path in a file for people is not
   reported; `port.exec` only from git's record (`test_needs_rules`).
