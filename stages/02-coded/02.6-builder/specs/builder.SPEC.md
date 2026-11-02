# 02.6-builder: spec

The builder checks, one spec for the step (restructure Q12; the tests stay one file per module).
They are the questions a person who builds a skill asks of a repository (plan for builders, slices 1
to 6, owner 2026-10-26 and 2026-10-27): what it needs to run, which AI hosts it is ready for, whether
it will trigger, what its text asks tools to do, whether the tools fit the job, whether it is clean,
and what ships and costs. Until restructure step 4 (2026-10-29) the first five were part of
`02.4-phrases` (`needs.py`, `hosts.py`, `trigger.py`, `asks.py`, `clean.py`) and the last two of
`02.5-capability` (`fit.py`, `cost.py`). Moving them is a pure move: no check id changed, and each
module is called with the inputs it always had, so every finding is the one it was. A step comparison
against a run made before the move (`tools/compare_runs.py`) holds the findings equal, pooled
across the stage files.

| Module | Checks it emits |
|---|---|
| `needs.py` | `need.command`, `need.package`, `port.*` |
| `hosts.py` | `host.coverage`, `host.drift`, `host.feature` |
| `trigger.py` | `trig.*` |
| `asks.py` | `ask.tools`, `ask.named`, `fit.loop` |
| `clean.py` | `clean.*` |
| `fit.py` | `fit.unused`, `fit.missing`, `fit.inherits`, `fit.hook`, `fit.checked` |
| `cost.py` | `cap.ship`, `cap.context` |

## run.py (the runner) and earlier.py (what it reads)

```
python stages/02-coded/02.6-builder/run.py <input_dir> [--reports <dir>]
```

The step runs after `02.5-capability` (`stages/stages.json`) and prints one contract-1 report
(`stages/CONTRACT.md`).

### Inputs

- `<input_dir>`: the folder audited. Read-only. Its text is read the way `02.4-phrases` reads it
  (`stages/_shared/readtext.py`, `read_row`: the same files, decoded the same way, a pattern list,
  a symlink, a binary, or an unreadable file left out), from the rows of `02.1-inventory`'s inventory, in
  path order.
- `--reports <dir>`: a run's saved outputs (`earlier.load_dir`): `02.1-inventory.json` (the
  inventory, with the hooks and MCP servers it found), `02.4-phrases.json` (its `secret.found`
  findings: where a secret sits), `02.5-capability.json` (its `cap.injection` findings, for
  `fit.hook` and the session tier of `cap.context`, and its `testdata+loaded` pairs), and
  `graph.json` when there is one (`02.3-graph`'s edges; without it `cap.ship`, `cap.context`, and the
  reach `fit` follows are not reported and stderr says why). A report missing or not a contract-1
  report of the step it names is an error (exit 2).
- Without `--reports`: `stages/_shared/earlier_steps.py` (`run_before`) runs `02.1` to `02.5` once each with
  the same Python, in a temporary folder outside the input that is removed afterwards (the way the
  pipeline runs them, `02.3-graph` with `--out` for `graph.json`, `02.5-capability` with `--reports`), and
  `earlier.load_dir` reads that folder; the grader runs the step this way. Their code is never
  imported. A step that fails fails this one (exit 1). The steps it reads are listed in
  `stages.json` (`reads`), and `earlier.READS` is built from them (restructure step 7; named `NAMES` and keyed by two-digit numbers until step 7b).

### What it calls, and in what order

The five questions `02.4-phrases` used to ask come first, as `02.4-phrases` asked them, over the texts and the
inventory's hooks (`struct.hooks`), MCP servers (`struct.mcp`), scripts, and hook configs
(`audience.inventory_sets`): `needs.findings` (with `needs.compatibility`), `hosts.findings`,
`trigger.findings`, `asks.findings` (with `asks.servers_of` over the trigger findings), and
`clean.findings`. A finding that keeps words from a line a secret sits on has them masked (`stages/_shared/secretmask.py`), as
`02.4-phrases` masked its own. That comes last, over every finding the step makes, since `fit` reads the tools a grant names. What a
frontmatter says (a name, a key, a value, a tool, a YAML error) has `span`, the lines of the frontmatter, since a value can run below
its key. `fit.hook` and `cap.context`'s `unknown` copy a hook's or a server's words from `02.1-inventory`, with no line to go by; the
runner masks them with their source once this step has run (`secretmask.mask_copies`).

Then the two `02.5-capability` used to ask: `fit.entries_fit` and `fit.hooks_fit` over the inventory **with
test data set aside** (findings on a test-data path are left out, except the files a `testdata+loaded`
pair names, which a model-read file points at: `02.5-capability`'s rule, which `fit` was always given), and
`cost.ship` and `cost.context` over **everything** (test data counts, so tests can be grouped as
build material). Both read the same trigger and ask findings and the same graph.

Order of the report: `need.*` and `port.*`, `host.*`, `trig.*`, `ask.*` and `fit.loop`, `clean.*`,
then `fit.unused`, `fit.missing`, `fit.inherits`, `fit.checked`, `fit.hook`, then a `cap.ship` per file,
then the `cap.context` tiers. As `02.5-capability` wrote them, the `fit.*`, `cap.ship`, and `cap.context` rows
carry `evidence` (empty) and `evidence_total` (0); the checks `02.4-phrases` wrote carry neither.

### Outputs

stdout: `{"stage": "02.6-builder", "contract": 1, "findings": [...], "coverage": [...]}`. stderr: one line with the
count (and a note when there is no graph). It writes no file: there is no `--out`.

### What the step looked at (added 2026-10-30, M9 slice C)

The report's `coverage` list (`stages/CONTRACT.md`, "Coverage lines") has twenty-three lines. A line holds the checks that handle the
same items in one pass, so every check a line names handles every item it counts, and a line counts the items its checks read: the
files of the scope each check has (`needs.programs_scope`, `paths_scope`, `backslash_scope`, `os_scope`, `crlf_scope`,
`exec_scope`, `python_scope`, `trigger.is_entry`, `clean.reads_dated`), not the files the step read. `of` is counted before the
checks run, in `build` (`count_text_inputs`, and beside the calls that need an earlier result) from the inventory and the texts, or
from the check's own input (`trig.overlap`, the uses the port checks read); each check counts `looked_at` inside its own loop,
where it handles an item.

| Checks | Unit | `of` | `looked_at` |
|---|---|---|---|
| `need.command` | `files` | the scripts and the Markdown a model reads, not test data | each file `needs.findings` reads for programs |
| `need.package` | `files` | those whose extension can carry an import (`needs.PACKAGE_EXTS`) | each such file `needs.packages` reads imports from |
| `port.path` | `files` | the files not written for people, not test data | each file `needs.findings` reads for personal paths |
| `port.backslash` | `files` | Markdown a model reads | each file read for backslash paths |
| `port.os` | `files` | shell scripts and Windows scripts | each script set against the OS it is written for |
| `port.crlf` | `files` | shell scripts | each read for Windows line ends |
| `port.exec` | `uses` | the uses (a program in a file, a script, a hook command, an MCP command) that are no program in the table and were found in a sentence a model follows or a hook command | each use `needs.port_of_use` sets against the mode bit |
| `port.python` | `uses` | the uses of Python by its name, found in a sentence a model follows or a hook command | each use `needs.port_of_use` finds Python in |
| `host.coverage` | `entries` | the hosts in `Library/hosts.yaml` | each host `hosts.coverage` writes a row for |
| `host.drift` | `files` | the instruction copies kept for a host (`hosts.copy_files`) | each copy `hosts.drift` places in its folder |
| `host.feature` | `files` | the SKILL.md and AGENTS.md files and the hook files | each file `hosts.features` reads for one host's words |
| `trig.entry`, `trig.frontmatter`, `trig.rule`, `trig.guidance`, `trig.key`, `trig.value`, `trig.tool` | `entries` | the skills, agents, and commands with text that are not test data and that `check_entry` takes for an entry (`trigger.is_entry`: not the documentation kept beside the agents) | each entry `trigger.findings` checks; an entry whose frontmatter is not read is `explained` by its row (`why`) |
| `trig.overlap` | `entries` | the entries a listing is made of | each entry `trigger.overlaps` sets against the entries after it |
| `trig.listing` | `run` | 1 | the row `trigger.findings` writes |
| `ask.tools`, `ask.named`, `fit.loop` | `files` | the files the AI reads (audience model or subagent) | each file `asks.findings` reads |
| `clean.unfinished`, `clean.model` | `files` | the files not written for people and not test data | each file `clean.findings` reads |
| `clean.dated`, `clean.older` | `files` | Markdown the AI reads (`clean.reads_dated`) | each such file `clean.findings` reads |
| `clean.checked` | `run` | 1 | the row `clean.findings` writes |
| `fit.unused`, `fit.missing`, `fit.inherits` | `entries` | the entries that were read (not `unread` or `skipped`) | each entry `fit.entries_fit` sets against its reach |
| `fit.checked` | `run` | 1 | the row `fit.entries_fit` writes |
| `fit.hook` | `entries` | the hooks, with test data set aside | each hook `fit.hooks_fit` writes a row for |
| `cap.ship` | `files` | every file of the inventory | each file `cost.ship` gives a group |
| `cap.context` | `entries` | the session, the project when the repository has instruction files, and each skill, agent, and command (`cost.context_items`) | each tier `cost.context` works out |

Two checks have a second source their line does not count: `need.command` also reads the commands of the hooks and the MCP
servers (a program only a hook or a server's config runs is found, and fixture rows hold it), and `port.os` also finds a script tied
to an OS from the programs it runs. Without `graph.json` nothing that needs edges is reported (Done when 8): the files of `cap.ship`
and the items of `cap.context` are `explained`, by the note the step writes. A check that is not run, or run on fewer items than it
was given, leaves `looked_at` below `of` (`tests/test_coverage.py`, a test for each line). `fit.checked` was written from slice 5 and is
listed in the contract from here.

### Must never

- Print anything but the report to stdout; write inside `<input_dir>` or anywhere else.
- Import another step's code, run anything from the input, or fetch a URL.
- Conclude, score, rank, or render a verdict (no field named risk, severity, score, or verdict).
- Change a finding by moving it: each module's findings are what they were in `02.4-phrases` or `02.5-capability`.

### Done when (each backed by a test in `tests/test_run.py`)

1. With `--reports`, stdout parses as a contract-1 report with stage `02.6-builder`, exit 0, every
   finding has `check`, `file`, `line`; the `fit.*` (not `fit.loop`), `cap.ship`, and `cap.context`
   rows have an empty `evidence` and `evidence_total` 0, and no other finding has either
   (`test_report_shape_and_order`).
2. The findings follow the order above (`test_report_shape_and_order`).
3. A tree with nothing in it still states a row per host, the trigger listing, `clean.checked`,
   and `fit.checked`, and then its `cap.ship` and `cap.context` (`test_zero_findings`).
4. On a small tree each check finds what it should: programs used, a personal path, hosts, an
   entry, an asked-for family and a loop, a TODO, an unused grant, a file's group
   (`test_what_each_check_finds_on_the_small_tree`).
5. A hook config in test data is not a `fit.hook` but is shipped as build material, and one a
   model-read file points at (`02.5-capability`'s `testdata+loaded` pair) is a hook for `fit`
   (`test_test_data_is_left_out_of_fit_but_shipped_as_build_material`,
   `test_a_test_data_file_a_model_reads_stays_in`).
6. A quote on a line a secret sits on is masked and `masked` is true, and a readable-text hit masks
   nothing (`test_a_secret_on_a_quoted_line_masks_the_quote`). What a frontmatter says on a flagged line is masked, on one line or
   running below its key, and the checks read it first
   (`test_a_frontmatter_value_on_a_flagged_line_is_masked_and_the_checks_read_it_first`); a key in a file with no frontmatter leaves
   the entry as it was (`test_a_key_in_no_frontmatter_leaves_the_entry_as_it_was`).
7. A saved folder and a fresh run (no `--reports`) give the same report
   (`test_the_saved_folder_and_a_fresh_run_agree`).
8. With no `graph.json`, no `cap.*` rows, a note on stderr, and the rest as before
   (`test_without_a_graph_nothing_that_needs_edges`).
9. A missing input, a missing or wrong report in `--reports` exit 2 with nothing on stdout; the
   input is byte-identical after a run (`test_bad_inputs_and_a_read_only_run`).
10. No field named risk, severity, score, or verdict (`test_no_verdict_fields`).
11. `earlier.load_dir` reads the four things and checks each report (`test_earlier_reads_the_four_things`);
    running the earlier steps for the step on its own is `stages/_shared/earlier_steps.py`'s, with its
    own tests.
12. `tools/grader/grader.py 02.6` passes on the seven fixtures (below), and `02.4` and `02.5` still pass on
    theirs.

## Data

Each module reads its table from the Library through `stages/_shared/library.py`: `tools.yaml`,
`hosts.yaml`, `trigger.yaml`, `asks.yaml`, `clean.yaml`, `fit.yaml`, `loading.yaml`.

## needs.py

What a repository needs to run, and what ties it to one machine (plan for builders, slice 2,
owner 2026-10-26; the slice spec is `pre-planning/SPEC-SLICE2-2026-10-26.md`). The step calls it
with the texts `02.4-phrases` reads (`readtext`) and `02.1-inventory`'s inventory; it runs, imports, and installs nothing. A skill's
`compatibility` field is read from its own frontmatter (`compatibility`). Test data
(`audience.is_test_data`) is left out throughout.

### Data: `Library/tools.yaml`

The programs Walkdown recognizes (only these count, so an ordinary word is never a program), the
system a program exists on when it is one system's only (`unix`, `macos`, `linux`, `windows`),
the import names whose package has another name (`yaml` is PyYAML, `pdfminer` is pdfminer.six),
Node's built-in modules, and home-folder names that are not a person's (CI runners, containers,
placeholders). Dated; a program missing from the list is missed until it is added.

### What it needs

**`need.command`**, one per program used, sorted by name: `command`, `os` (from `Library/tools.yaml`),
`uses` (each `{file, line, how}`), `declared`, `declared_in`. A program is used:

- in a script (`audience.SCRIPT_EXTS`, a shell shebang, or a PowerShell or batch file): a shell
  line's word at command position (after `sudo`, `env`, variable assignments; after `|`, `&&`,
  `||`, `;`, `$(`), `how: script`; in Python, the command of a `subprocess` call, `os.system`,
  `os.popen`, or `shutil.which`; in JavaScript, of `exec`, `execSync`, `spawn`, `execFile`;
- in instructions (a Markdown file the AI reads): each line of a fenced block marked `sh`, `bash`,
  `shell`, `console`, `zsh`, or unmarked, at command position (a leading `$` or `>` prompt
  dropped); inline code that starts with a known program and a space; `how: instructions`;
- in a hook command (`02.1-inventory` `struct.hooks`), `how: hook`; as an MCP server's command
  (`struct.mcp`), `how: mcp`.

**`need.package`**, one per package imported, sorted: `package`, `ecosystem` (`python`, `node`),
`files`, `declared`, `declared_in`. Python: top-level `import x` and `from x import` in `.py`
files, not the standard library (`sys.stdlib_module_names`), not a relative import, not a module
the repository holds anywhere (an `x.py`, or a folder of `.py` files named `x`; a script can reach
another folder's module through `sys.path`), named by `Library/tools.yaml` where the package's name
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

### What ties it to one machine

Each with `file` and `line` (null for a whole file), sorted by check, file, line:

- `port.path` (`kind` windows, macos, linux; `quote`): `C:\Users\<name>\`, `/Users/<name>/`,
  `/home/<name>/` where the name starts with a letter and is not in `not_personal`; only in files
  that run or that the AI reads (not ones written for people: a path in notes ties nothing to a
  machine; measured 2026-10-26, 116 of them in one repository's design notes).
- `port.crlf`: a shell script with Windows line endings. In a git checkout, the line endings as
  committed (`02.1-inventory` `eol_committed`, `crlf` or `mixed`), never as this checkout wrote them (Git
  for Windows can write CRLF for a file committed with LF); in a plain folder, the bytes.
- `port.os` (`os`, `why`, and `command` for a program): a shell script (`unix`), a PowerShell or
  batch script (`windows`), and each use of a program `Library/tools.yaml` marks as one system's.
- `port.backslash` (`written`, `file_named`): in text the AI reads, a reference written with
  backslashes that names a file in the repository once they are slashes.
- `port.exec` (`script`): a script run directly by its path (first in an instruction or hook
  command, after `./` or `${CLAUDE_PLUGIN_ROOT}/`) whose mode git records as not executable;
  never from a plain folder, whose modes say nothing on Windows.
- `port.python`: an instruction or hook that runs `python` (macOS and many Linux systems have only
  `python3`).

The step emits these first, then `host.*`.

### Must never

- Count a word as a program unless `Library/tools.yaml` lists it; call something declared because a word
  appears in prose; run, import, or install anything.

### Done when

1. Fixture `needs-repo` (grader 02.6, rows `needs-*`): programs used and declared or not, packages
   declared or not, the standard library and the repository's own module left out, each
   portability kind, and the negatives (`make` in prose, a placeholder path).
2. `tests/test_needs.py`: command position across pipes, prompts, `sudo`, and assignments;
   Python and JavaScript calls; every declaration source; a module held in another folder is
   not a package; CRLF from git's record over the bytes; a path in a file for people is not
   reported; `port.exec` only from git's record (`test_needs_rules`).

## hosts.py

Is it ready for any AI? (plan for builders, slice 3, owner 2026-10-26; the slice spec is
`pre-planning/SPEC-SLICE3-2026-10-26.md`). The step calls it with the texts `02.4-phrases` reads, `02.1-inventory`'s
inventory, and `02.1-inventory`'s hook findings (`struct.hooks`). It reads nothing else and runs nothing.
Test data (`audience.is_test_data`) is left out throughout.

### Data: `Library/hosts.yaml`

One row per host (`claude`, `codex`, `gemini`, `cursor`, `copilot`, `windsurf`, `agents-md`),
each with its source and the date checked: the instruction files it reads (`**/` means at any
depth), a `fallback` read only when none of those exist (Claude Code reads `AGENTS.md` only when
there is no `CLAUDE.md`), the folders it reads skills from, its MCP config files, and its hook
files. Then `copies` (instruction files kept one per host), `skill_keys` (the frontmatter keys of
the Agent Skills format), `claude_words`, and `claude_tools`. A host that changes is a data edit.

### Findings

**`host.coverage`**, one per host in `Library/hosts.yaml` order, in every run (a fact per host, never a
fault): `host`, `name`, `instructions` (the files here it reads), `skills` (how many `SKILL.md`
sit in its skill folders, at any depth, plus for Claude Code a plugin's `skills/<name>/SKILL.md`
beside `.claude-plugin/plugin.json`), `skill_files`, `mcp`, `hooks` (`02.1-inventory`'s hook files that
are this host's: a file matching another host's `hooks` is that host's, any other is Claude
Code's).

**`host.drift`**, one per pair of `copies` files in one folder (`.github/copilot-instructions.md`
counts as the root folder's), the first in `copies` order as `file`, the other as `other`:
`relation` is `linked` when one is a symlink to the other, imports it (`@other` anywhere in a line,
as Claude Code and Gemini CLI read it), or is a short file (at most 10 lines that are not
headings) naming the other; else `same` when the text is equal line by line (trailing spaces and
line endings aside); else `differ`, with `only_here` and `only_there` (non-empty lines, trimmed,
found only in that file). A pair where one points to a third copy is left out: the pair with that
copy says it.

**`host.feature`**, in `SKILL.md` and `AGENTS.md` files, with `file`, `line`, `host`, `kind`,
`what`:

- `frontmatter`: a `SKILL.md` frontmatter key outside `skill_keys` that Claude Code knows
  (`Library/trigger.yaml`; claude.ai and the Skills API refuse the skill; other hosts ignore the key). A
  key no host knows is `trigger.py`'s `trig.key` (owner, 2026-10-26);
- `claude-words`: a word from `claude_words` (`$ARGUMENTS`, `${CLAUDE_PLUGIN_ROOT}`, ...);
- `claude-tool`: a tool name from `claude_tools` as a whole word, or `Bash(...)` permission syntax;
- `import`: an `@path` in `AGENTS.md` outside code (fenced blocks and inline code), which no host
  but Claude Code and Gemini CLI expands, and those only in their own files;
- `hooks`: one per hook file (`line` null), `what` the host's name: each runs on one host only.

A host named in prose ("Claude will...") is not a feature (owner, 2026-10-26: common and usually
harmless). The step emits these after `need.*` and `port.*`.

### Must never

- Call a host's coverage a fault, or say which host a repository should support.
- Read a file outside the texts and inventory it is given.

### Done when

1. Fixture `hosts-repo` (grader 02.6, rows `hosts-*`): coverage for Claude Code, Cursor, Copilot,
   and Codex; one `differ` pair with its line counts and one `same` pair; a frontmatter key,
   `$ARGUMENTS`, and `WebFetch` on their lines; no feature in a skill with only Agent Skills keys.
2. `tests/test_hosts.py`: the fallback, plugin skills, hook owners, `linked` three ways, the
   Copilot file at the root, imports outside code only, and test data left out.

### History

- 2026-10-26: built (slice 3). Pointers measured on audited repositories the same day: a one-line
  CLAUDE.md and a 7-line GEMINI.md, each saying to read AGENTS.md, first came out as a `differ`
  pair with each other; now both are `linked` to AGENTS.md and their own pair is left out.
- 2026-10-26 (slice 4): frontmatter features only for keys Claude Code knows; a key no host knows
  (a typo, `version`) moved to `trig.key`. Cursor's hooks are `.cursor/hooks.json` (checked against
  cursor.com/docs/agent/hooks while building; the slice spec's table had only `environment.json`).
- 2026-10-31: M9 slice C, fix round: nine lines became eighteen, so no line names a check that does not handle every item it counts (`need.package`, `port.exec` and `port.python`, `host.drift`, `host.feature`, `trig.overlap`, `trig.listing`, `clean.checked`, `fit.checked`, and `cap.context` each have their own). `needs.port_of_use` is the per-use part of `needs.findings`, and `hosts.feature_texts` the files `hosts.features` reads. An entry whose frontmatter is not read is explained and not looked at. The findings are unchanged.
- 2026-10-31: M9 slice C, last fix round: nine lines became twenty-three in two rounds. This round counts the files each check reads: `need.command` (scripts and Markdown a model reads), the port checks (one line each, by scope), `port.exec` and `port.python` (the uses each reads), `trig.*` (not the documentation beside the agents), `clean.dated` and `clean.older` (Markdown the AI reads). Fixture rows hold a program that only an MCP config runs and one that only a hook runs. The findings are unchanged.

## trigger.py

Will it trigger? (plan for builders, slice 4, owner 2026-10-26; the slice spec is
`pre-planning/SPEC-SLICE4-2026-10-26.md`). The step calls it with the texts `02.4-phrases` reads and `02.1-inventory`'s
inventory (each file's `entry_point` and `bom`). It runs nothing. Test data
(`audience.is_test_data`) is left out.

### Data: `Library/trigger.yaml`

Dated, with sources (Claude Code's skills, subagents, and tools pages; the Agent Skills spec; the
published skill-authoring guidance): the frontmatter keys Claude Code knows for skills (commands
take the same) and for subagents; the documented values of `model`, `color`, `permissionMode`,
`effort`, `isolation`, `memory`, `context`, `shell`, and the boolean fields; Claude Code's tool
names and the older names not in the current list; the name and description limits; the listing
cap per entry (1,536 characters) and the listing's share of the context (1%); the subagent
warning (15,000 tokens); the "when" and person patterns; the overlap measure and its stop words.

### Entries

An entry is a `SKILL.md` (or `*.skill.md`), a Markdown file in a `commands/` folder, or one in an
`agents/` folder (`02.1-inventory`'s `entry_point`). An agents-folder file with no frontmatter, or with
neither a name nor a description, is documentation and no entry.

**Frontmatter** is the first non-blank line `---` to the next `---` or `...`, read as YAML; its
keys are the top-level `key:` lines.

**`trig.entry`**, one per entry: `kind`, `name` (a skill's folder or a command's file name when
none is given), `description_chars`, `listing_chars` (description, or a skill's or command's
first body line when it has none, plus `when_to_use`), `description_from`, `menu` (false with
`user-invocable: false`), `grants` (a subagent's `tools` or a skill's or command's `allowed-tools`, as
written; null when absent), `grants_line`, `disallowed`, `preloads` (a subagent's `skills`; slice 5),
and `mode`:

- `auto`: Claude chooses it by its description; `paths`: the same, only on matching files;
- `typed`: `disable-model-invocation` is true;
- `unread`: a skill or command whose frontmatter is not read (YAML that does not parse, or `---`
  not on the first line): it loads with no fields set;
- `skipped`, with `why`: a subagent Claude Code does not load (frontmatter not read; no name; a
  name and no description; a name starting with `-`, holding `:`, or over 256 characters).

### Findings

Each with `file`, `line` (the key's line when there is one), and `kind_of` (the entry's kind):

- **`trig.frontmatter`** `kind`: `yaml-error` (with the parser's first line), `not-first-line`,
  `missing` (a `SKILL.md` with none), `bom` (a byte-order mark before `---`; the docs do not say
  whether it is read).
- **`trig.rule`** `rule`, `host` (`agent-skills`: the spec, other hosts, uploads; `claude-api`:
  claude.ai uploads and the Skills API; `claude`: Claude Code). Skills: `name-missing`,
  `name-long`, `name-chars`, `name-folder` (a `SKILL.md` only), `name-reserved`, `name-xml`,
  `description-missing`, `description-empty`, `description-long`, `description-xml`. Skills and
  commands: `listing-cut` (`chars`, `lost`). Subagents: `agent-name`, `name-duplicate` (`other`).
- **`trig.guidance`** `kind`, published guidance and never a host rule, on entries that load:
  `no-when` (no `when_to_use` and no "when" pattern), `first-person`, `second-person`.
- **`trig.key`**: a key outside the kind's list, with `near`: the known key equal to it once case,
  `-`, and `_` are set aside, or one close spelling (`difflib`, 0.8), or null.
- **`trig.value`** `field`, `value`: a documented field outside its values (a model may also be a
  full `claude-` id), or a boolean field that is not a boolean.
- **`trig.tool`** `field`, `tool` (as written), `kind`: `unknown` with `near`, or `older` with
  `now`. A tool is the name before `(`; `mcp__...` and the current names are never reported.
- **`trig.overlap`** `other`, `shared`, `count`, `share`: within one listing (skills and commands;
  subagents), entries in `auto` or `paths` mode whose content words (lower case, three letters or
  more, not a stop word, a plural's `s` dropped) share at least half of the shorter set and at
  least 4 words, after the words in more than half of the listing's descriptions are set aside
  (when it holds 4 or more). Walkdown's own measure (owner, 2026-10-26), said so wherever shown.
- **`trig.listing`**, one row in every run: `skills` (skills and commands in `auto` or `paths`),
  `commands`, `agents`, `listing_chars` (each entry's capped at 1,536), `agent_chars`, `typed`,
  `unread`, `not_loaded` (never `skipped`, the grader's skip marker).

The step emits these after `host.*`.

### Must never

- Call a guidance row a host rule, or the overlap measure a host's.
- Say an older tool name fails; the docs do not say.

### Done when

1. Fixture `trigger-repo` (grader 02.6, rows `trig-*`): every kind above on its file, and no finding
   on a skill that follows every rule, an MCP tool, a permission rule, or unrelated descriptions.
2. `tests/test_trigger.py`: modes, the agents that are documentation, near names, values and
   booleans, the overlap listings and common words, the listing row.

### History

- 2026-10-26: built (slice 4). Measured on the audited repositories and the owner's skills before
  keeping the overlap measure: compared across all entries it paired each of one plugin's agents with the
  skill of the same name and the agents with each other through their shared boilerplate (14
  pairs); within one listing and with common words set aside, none. Two "when" patterns added
  ("Run once at the start", "Spawned by the orchestrator for its phase"): that plugin's no-when rows went
  from 8 to 1.
- 2026-11-01: `trig.*` rows have `span`, the lines of the frontmatter they came from (null with no frontmatter), and `trig.overlap`
  the span of its `file`, for the mask of a flagged line. Nothing else about them changed.

## asks.py

What the text asks a tool to do, and loops with no stated limit (plan for builders, slice 5,
owner 2026-10-26; the slice spec is `pre-planning/SPEC-SLICE5-2026-10-26.md`). The step calls it
with the texts `02.4-phrases` reads, the scripts and hook configs its audience rules use, and the MCP servers
the entries grant tools from (`servers_of`, over slice 4's `trig.entry` grants). It runs nothing.

### Data: `Library/asks.yaml`

Dated: the cue rules for each family of work (a rule is patterns that must all match one
sentence), the tool names that count when named outright, and the loop and limit patterns.
Measured on the audited repositories before they were kept (see History).

### What it reads

Every file whose audience is `model` or `subagent` (text the AI reads), with its frontmatter
blanked (a tools list names tools; it asks for nothing), line numbers kept. A **sentence** is a
line joined with the next while it does not end in `.`, `!`, `?`, `:`, or `;`, never across a
blank line, a list item, a heading, a quote, a table row, or fenced code, which is left out.

### Findings

- **`ask.tools`**, one per file and family (`shell`, `write`, `web`, `search`, `agent`) the file
  asks for: `family`, `lines` (each sentence's first line), `line` (the first), `audience`. A
  family is asked for when a sentence matches one of its rules; `shell` also from slice 2's
  command scan of a Markdown file (a known program in a shell block or inline code).
- **`ask.named`**, one per tool named outright (`` `Bash` ``, "the Bash tool", `Bash(`), and one
  per granted MCP server named (`mcp__<server>` or the server's name as a word, as
  `mcp__<server>`): `tool`, `lines`. A named tool counts as used, never as a task asked for (the
  line may forbid it).
- **`fit.loop`**: a line outside fenced code that matches a loop pattern, with no limit pattern on
  it or the next line: `quote`, `audience`. "No stated limit", never "no limit": a limit may be
  stated elsewhere (owner, 2026-10-26).

The step emits these after `trig.*`.

### Must never

- Read a file written for people, a script, or test data; count frontmatter or fenced code (other
  than slice 2's shell scan) as asking for anything.

### Done when

1. Fixture `asks-repo` (grader 02.6, rows `ask-*`, `loop*`): each family on its line, a named tool,
   a loop with no stated limit; negatives: a writing verb with no object, a limit on the loop's
   line or the next, a README written for people.
2. `tests/test_asks.py`: sentences joined and split, fenced code and frontmatter left out, MCP
   servers named, loop limits on the next line only.

### History

- 2026-10-26: built (slice 5).

## clean.py

Is it current and clean? (plan for builders, slice 6, owner 2026-10-27; the slice spec is
`pre-planning/SPEC-SLICE6-2026-10-27.md`). The step calls it with the texts `02.4-phrases` reads and the
scripts and hook configs its audience rules use. Facts with locations: nothing here says a date
is past, a model retired, or a TODO matters.

### Data: `Library/clean.yaml`

Dated, with sources (the skill-authoring best practices; Claude Code's model configuration): the
unfinished-text patterns by kind, the template paths, the dated-claim patterns, and the model ID
patterns. Measured on the audited repositories before they were kept (History).

### What it reads

Every file but those written for people and test data (`audience`). In Markdown, each line is
`frontmatter`, `code` (fenced), or `text`, and inline code spans and quoted text are set aside in
text; any other file is `code`.

### Findings

Each with `file`, `line`, `audience`:

- **`clean.unfinished`** `kind`, `quote`: `todo` (TODO, FIXME, XXX, HACK, in their case) anywhere
  but fenced Markdown code; `placeholder` ("lorem ipsum", "[placeholder]", "[insert ...]",
  "REPLACE_ME", `{{name}}`) and `draft` (DRAFT, WIP, "work in progress", "not yet implemented",
  "coming soon", "under construction") in Markdown outside code only (in code, `{{x}}` is an
  f-string's brace). No placeholder in a `templates/` folder or a file named `*template*`.
- **`clean.dated`** `quote`: in Markdown text the AI reads (audience `model` or `subagent`), a date,
  month and year, or year after "before", "after", "since", "until", or "by"; a quarter
  ("Q3 2025"); or "as of". Published guidance ("avoid time-sensitive information"), never "out
  of date". A bare date is not a claim (owner's rule as measured, below).
- **`clean.model`** `model`, `where` (`frontmatter`, `code`, `text`): a pinned model ID, Claude's
  or another vendor's, once per line; never an alias, an ID ending in `-latest`, or a file name.
- **`clean.older`** `tool`, `now`: in Markdown text the AI reads, a tool named outright (`` `Task` ``,
  "the Task tool", `Task(`) that slice 4's `older_tools` lists; frontmatter is slice 4's
  (`trig.tool`).

The step emits these after `ask.*` and `fit.loop`.

### Must never

- Say a date is past, a model retired, or an ID stale; read a file for people or test data.

### Done when

1. Fixture `clean-repo` (grader 02.6, rows `clean-*`): each kind on its line, a script's FIXME and
   model ID; negatives: a template's placeholder, a relative word, an alias, a README's TODO, a
   TODO in a fenced example.
2. `tests/test_clean.py`: regions, code versus text, file names, quoted mentions, the dated rule.

### History

- 2026-10-27: built (slice 6). Measured first: a full date alone counted 745 lines in Walkdown's
  own notes ("Done 2026-09-25", "(owner, 2026-10-20)"), records of when rather than claims that
  expire, so a date counts only after before, after, since, until, or by (39 left, each a
  "since ..." or "as of ..."); `{{...}}` in Python validators (f-string braces) made 75
  "placeholders" in one repository, so placeholders and drafts are read in Markdown only; a file
  name (`claude-fable-5.md`) read as a model ID.

## fit.py

Do the tools fit the job? (plan for builders, slice 5, owner 2026-10-26; the slice spec is
`pre-planning/SPEC-SLICE5-2026-10-26.md`). Derived from this step's `trig.entry`, `ask.tools`,
`ask.named`, `02.1-inventory`'s `struct.hooks`, `02.3-graph`'s edges (the reach slice 1 counts), and `02.5-capability`'s
`cap.injection`. Nothing is run or read here. The yardstick is the entry's own words against its
own grants.

### Data: `Library/fit.yaml`

Dated, with sources (Claude Code's subagents, skills, and hooks pages): the families of work and
the tools that do them (`shell`: Bash, PowerShell, Monitor; `write`: Write, Edit, NotebookEdit,
MultiEdit; `web`: WebFetch; `search`: WebSearch; `agent`: Agent, Task); how often each hook event
runs; which events' plain stdout becomes context; the 10,000-character output cap.

### Entries

Every `trig.entry` that loads (not `unread`, not `skipped`). Its **reach** is slice 1's
(`cost.reach` over every kind of reference: a skill its own folder, an agent or command one
level), plus, for a subagent, the reach of each skill its `skills` field preloads. What it
**asks for** is every family an `ask.tools` row in its reach names, with the first place; what it
**names** is every `ask.named` tool in its reach.

### Findings

- **`fit.unused`**: a granted tool in a family (`Library/fit.yaml`) or from an MCP server, when nothing in
  the reach asks for its family and the reach never names it (an MCP tool: never names its
  server): `tool` (as written), `family`, `kind_of`, `pre_approved` (true for a skill or command:
  `allowed-tools` only pre-approves), `line` (the grant's key line). Reading tools and names no
  family lists are never reported (owner, 2026-10-26).
- **`fit.missing`**: a family the reach asks for that the entry cannot use: a subagent whose
  `tools` list (less its disallowed tools) has no tool of that family, or any entry whose
  disallowed tools remove every tool of it. `family`, `asked_at`, `why`. A skill's `allowed-tools`
  never makes a task missing (owner, 2026-10-26).
- **`fit.inherits`**: a subagent with no `tools` list (every tool, MCP tools included):
  `families` its reach asks for, `asked_at`.
- **`fit.hook`**, one per `02.1-inventory` hook: `event`, `matcher`, `how_often` (`every-prompt`,
  `every-tool-call`, `matching-tool-calls` for a tool event with a narrower matcher,
  `every-turn`, `once-a-session`, `other`), `adds_context` (the event's plain stdout becomes
  context), `bytes` (`02.5-capability`'s `cap.injection` estimate, or null), `over_cap`.

### Must never

- Say a grant is wrong, or that a tool is unused anywhere but in the entry's own reach.
- Call a skill's task missing because of `allowed-tools`.

### Done when

1. Fixture `fit-repo` (grader 02.6, rows `fit-*`): an unused grant, two missing families, an
   inheriting agent, a thin agent whose words live in the skill it reads (no finding), a skill's
   pre-approved and unused tool, and three hooks by how often they run.
2. `tests/test_fit.py`: families, MCP servers, preloaded skills, disallowed tools, hook matchers.

### History

- 2026-10-26: built (slice 5).
- 2026-11-01: `fit.unused` has its entry's `span`, for the mask of a flagged line. It reads the grants before they are masked, so what it
  finds does not move.

## cost.py

What a repository ships, and what it costs in an AI's context (plan for builders, slice 1,
owner 2026-10-26; the slice spec is `pre-planning/SPEC-SLICE1-2026-10-26.md`). Derived from
`02.1-inventory` (`inv.file`, `struct.description`, `struct.mcp`), `02.3-graph`'s `graph.json` edges, stage
5's hook injections, and the facts in `Library/loading.yaml` (each with its source and the date it was
checked). Nothing is run or read.

### Tokens

An estimate: a file's size in bytes divided by `bytes_per_token` (4), rounded up, per file.
For English text that is about one token per four characters; text in other scripts uses more
bytes per character, so its estimate runs high. A description counts its characters, cut at
`description_listing_chars` (1,536) as Claude Code cuts the skill listing. A file that is not
text has no token count (`tokens: null`) and is named in `not_text`.

### How far a file reaches

Measured before it was settled (2026-10-26): followed across the whole repository, one skill
reached 240,000 tokens on Walkdown and 559,000 on another audited repository through README and docs links,
and every file counted as used. So each entry's reach is bounded:

- **A skill** is its own folder (the Agent Skills specification: a skill is a directory, and only
  it installs). It reaches every file inside that folder its references lead to, as deep as they
  go, wildcard loads and folder mentions included for `skill-max`. A skill whose `SKILL.md` is at
  the repository's root has the whole repository as its folder. What its folder names outside
  itself is listed (`outside` on its `skill-max` row) and never counted: only references that
  name one file (`static`, not `ambiguous`), since a bare name matching files in many folders,
  or a folder read, says nothing about which.
- **An agent or a command** reaches the files it names directly, one level, wildcard loads
  included for `skill-max`; folder mentions do not count.
- **A project file** (`CLAUDE.md` and the rest) reaches its `@` imports (up to four hops, as the
  host expands them) and the files it names directly, one level. Its wildcards and folder
  mentions do not count: they describe the layout, the host never loads them, and someone
  working in the repository can browse it all anyway.
- **A script** is `run` only when a loaded file names it or a hook runs it; one reached only by a
  wildcard or folder mention is `maybe`.

### `ship(reports, graph) -> [cap.ship]`

One per file: `file`, `group`, `bytes`, `tokens`, and `reached_by` (the file that first names
it) for `on-demand` and `maybe`. Entries are the skills, agents, and commands (`02.1-inventory`
`entry_point`) outside test data; project files are project instructions (`CLAUDE.md`,
`AGENTS.md`, `GEMINI.md`, ...) and `.claude/rules/*.md` outside test data, plus what their
`@` imports reach (`02.3-graph` `at_import` edges, up to `import_hops`, 4). Rules, in order:

1. `build`: CI, or test data (`audience.is_test_data`), unless an entry or project file reaches it.
2. `entry`: a skill, agent, or command.
3. `project`: a project file or an import of one.
4. `config`: a manifest, MCP config, or hook config.
5. `run`: a script (`audience.SCRIPT_EXTS`) that an entry or project file names, or a hook config reaches.
6. `on-demand`: reached from an entry or project file over static edges, within each one's
   reach (above; scripts are reached, never followed).
7. `maybe`: reached only once wildcard loads and folder reads count (and folder mentions, for a
   skill inside its own folder).
8. `people`: a README, or a file written for people (`audience` `human`).
9. `build`: any other file read by tools (`audience` `tool`: build and lock files, scripts nothing reaches).
10. `unused`: everything else: nothing points to it (text written for the AI, or an image or
    font no file names).

`.claude/rules` files with `paths` load on demand in Claude Code; slice 1 counts every rule file
as loaded at launch, an upper bound. With no `graph.json`, nothing is reported.

### `context(reports, graph, injections, ship) -> [cap.context]`

- `session` (always one): every entry's description (cut at 1,536 characters), plus the hook
  text of the one hook config with the most (`cap.injection` `mechanism: hook`; each host runs
  its own config, so configs are never summed). `unknown`: what only running shows, never
  guessed: hooks with no estimate (`what: hook`) and MCP servers (`what: mcp`, their tool
  definitions). `files`, `hook_config`.
- `project` (only when there are project files): every project file and import.
- Per entry (`file` the entry, `kind` its kind): `skill-runs` (the entry file), `skill-full`
  (plus everything it reaches over static edges, scripts left out), `skill-max` (plus wildcard
  loads, folder reads, and folder mentions). An agent's body loads in its own context.

Each: `tier`, `tokens`, `bytes`, `files`, and `not_text` where it applies.

### Must never

- Guess a size only running shows; call a file unused when something names it; count a script
  in a context tier.

### Done when

1. Fixture `cost-repo` (grader 02.6, rows `cost-ship-*`, `cost-tier-*`): every file's group and
   every tier's tokens; scripts are in no context tier; a file nothing names is in none.
2. `tests/test_cost.py`: a skill in test data is `build`, and a test file a skill names is
   `on-demand`; a README a skill names is `on-demand`; an import of an import counts, a fifth
   hop does not; a description over 1,536 characters is cut; hook configs are never summed and
   a hook with no estimate and an MCP server are `unknown`; an image a skill names is `not_text`.
3. `tests/test_cost.py`: a skill in a subfolder reaches only inside it and lists what it names
   outside; an agent reaches one level; a glob in `CLAUDE.md` reaches nothing; a script reached
   only by a wildcard is `maybe`, not `run` (`test_reach_is_bounded`).

## Fixtures

The seven cases moved with the modules, bytes unchanged, to `Fixtures/02.6-builder/` (`needs-repo`,
`hosts-repo`, `trigger-repo`, `asks-repo`, `clean-repo`, `cost-repo`, `fit-repo`); their answer rows
are `Fixtures/ANSWERS/02.6-builder.json`. The grader runs the step on each by its runner with no
option (`earlier_steps.run_before`).

## History (restructure step 7)

- 2026-10-29: running the earlier steps for a step on its own moved to `stages/_shared/earlier_steps.py` (notes O4); `earlier.py` only reads
  the saved folder, and its `NAMES` is built from `stages.json`.
- 2026-10-29: restructure step 7b: the reports the checks read inside this step are keyed by stage name, not by a
  two-digit number: `02.1-inventory` for the inventory, and `02.6-builder` for this step's own findings (the
  trigger and ask rows `fit` reads, which were keyed `04` while stage 4 held them). The findings are the same.
- 2026-10-30: M9 slice B: this step writes its notes through `stagenote`, so a note that names a file or a path from the repository is one line, and a name with a line break cannot pass for a note of its own.
- 2026-10-30: M9 slice C: the report has a `coverage` list (the `run.py` section, "What the step looked at"); each check module counts the items it handles inside its own loop. The findings are unchanged. `fit.checked` is in the contract's list of this step's checks.
