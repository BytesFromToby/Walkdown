# graph: spec

One spec for the `02.3-graph` folder, a section per script. Each section keeps the script's inputs, outputs, rules, Must never, Done when (with the test file behind each list), and History. The folder's contract (inputs, process, outputs, the human check) is `../CONTEXT.md`. Merged from the per-script specs in restructure step 8a.

## run

The single entry point for `02.3-graph`. Gets entry points from `02.1-inventory`, wires
`invisible`, `extract`, `scans`, `resolve`, and `reach` together, and prints one
contract-1 report (`stages/CONTRACT.md`).

### Inputs

```
python stages/02-coded/02.3-graph/run.py <input_dir> [--inventory <file>] [--out <dir>]
```

- `--inventory <file>`: a `02.1-inventory` report (JSON) already produced for this input.
- Without it: `stages/_shared/earlier_steps.py` (`inventory`, restructure step 7; the step it reads is `reads` in
  `stages.json`) runs `stages/02-coded/02.1-inventory/run.py <input_dir>` as a subprocess with
  the same Python and parses its stdout. A non-zero exit or unparseable output
  fails `02.3-graph` (exit 1, message on stderr, nothing on stdout). `02.1-inventory` code is
  never imported.

### Nodes and scanning

- Nodes: every `inv.file` finding in the `02.1-inventory` report (so `02.1-inventory`'s walk
  rules hold: no symlink followed, no `.git/`, git-tracked files only in git
  mode). Entry points: those whose `entry_point` is not null.
- A node is scanned when it is not a symlink and its bytes decode as text
  (`invisible.decode`). Symlinks are nodes but are never read.
- `graph.case` (`written`, `to`; 2026-10-26, slice 2) for a static reference naming one file that matches it only
  when letter case is ignored.
- `graph.unscanned` (with `reason`) for a node that may hold references but was
  not scanned: an `inv.file` skip (`unreadable`), a binary document (PDF, Word,
  Excel, PowerPoint, OpenDocument, RTF, EPUB, by extension or `02.1-inventory` type:
  `binary document (<type>)`), an archive (`archive (<type>)`), or a file
  whose extension says text but whose bytes do not decode (`undecodable
  text`). Images, fonts, and other media are not listed (no reference a
  loader follows).

### Edges and findings

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

### Outputs

stdout: `{"stage": "02.3-graph", "contract": 1, "findings": [...]}`, findings in
this order: `graph.entry` (path order), `graph.orphan`, `graph.dangling` (file,
line order), `graph.dynamic` (file, line order), `graph.unlisted` (`unlisted.py`: components
on disk a manifest leaves out, 2026-10-18), `graph.depth`, `graph.unscanned`.

stderr: notes. Always the v1 limit: manifest versus disk compares skills, agents, and commands,
only the kinds a manifest names, and not plugins a marketplace leaves out. When any `graph.dynamic` exists: the graph is
incomplete by construction (count of dynamic loads).

`--out <dir>`: also writes `<dir>/graph.json`: `nodes` (`path`, `entry`: kind
or null, `depth`: int or null), `edges` (`from`, `line`, `to`, `kind`
`static` / `dynamic`, `form`, `text`: the reference as written, `context`,
`source` on dynamic edges, plus `ambiguous` / `case_mismatch` / `partial` (a partial path, 2026-10-21) / `by_name` (a bare
name found only by its name elsewhere, 2026-10-27) when true, and
`at_import` (2026-10-26, slice 1) on an edge from a project instruction file whose reference is written `@path` (at
the start of the line or after white space, outside code spans and fenced blocks): Claude Code expands those imports
into the file at load), `complete` (false when any
dynamic load exists), and `limits` (the stderr v1 note). The folder is created
if needed. An `--out` inside `<input_dir>` is refused (exit 2).

Exit 0 when a report was produced. Exit 2 for a missing or non-folder input,
an unreadable `--inventory`, or a refused `--out`. Exit 1 when `02.1-inventory` fails.

### What the step looked at (added 2026-10-30, M9 slice C)

The report's `coverage` list (`stages/CONTRACT.md`, "Coverage lines") has four lines. `graph.dangling`, `graph.dynamic`,
`graph.case`, `graph.unscanned`, unit `files`: `of` is the inventory's files with text and the ones `graph.unscanned` names
(`reads_text`: not a symlink, and either a file with text, a document or an archive, or a file named like text), counted before
the pass; `looked_at` is counted inside `references`, where a file's text is read for scans and references; `explained` is the files
with a `graph.unscanned` finding (a document, an archive, bytes that cannot be read, undecodable text). A symlink is a node and is not
one of the files to scan, and a picture or a binary holds no reference to read, so it is no item of the line.
`graph.entry`, unit `entries`: `of` is the inventory's entry points, `looked_at` the `graph.entry` findings made.
`graph.orphan`, `graph.depth`, unit `files`: `of` is every node, `looked_at` the nodes that `reach` gave a depth or named
an orphan. `graph.unlisted`, unit `entries`: `of` is the manifests the entry points name, counted in `build_report`;
`looked_at` is counted inside `unlisted`, once for each manifest it compares with the disk, kind by kind (a manifest the
comparison is not given is a manifest passed over). A file the scan leaves out with no `graph.unscanned` for it, and a node
`reach` neither places nor names, leave a line short (`tests/test_coverage.py`, a test for each, and one that runs the step's
`main` on a folder with two manifests and gives the comparison one).

### Must never

- Print anything but the report to stdout.
- Write inside `<input_dir>`; write anywhere without `--out`.
- Import another stage's code, run anything from the input, or follow a URL or
  a symlink.
- Judge or rank orphans; present the graph as complete when a dynamic load
  exists.

### Done when (each backed by a test in `tests/test_run.py`)

1. On a small tree, stdout parses as a contract-1 report with stage `02.3-graph`, exit 0, and every finding has `check`, `file`, `line`.
2. Entry points from `02.1-inventory` give `graph.entry` with `kind`; a file nothing names is `graph.orphan`; a missing path is `graph.dangling` with `target` and `context`; a glob is `graph.dynamic` with `pattern`, `resolves`, `source`; depths and parents are right, and a file reached only by the glob is `via` `dynamic`.
3. An unresolved bare filename in prose gives no finding; one in a code span gives `graph.dangling` with `context` `code`.
4. `--inventory` with a saved `02.1-inventory` report gives the same findings as the subprocess path.
5. `--out` writes `graph.json` with nodes, edges, and `complete` false when a dynamic load exists; `--out` inside the input is refused.
   An `@path` line in a `CLAUDE.md` gives an edge with `at_import`; the same path in a code span, or in a skill, does not
   (`test_at_imports_in_project_instructions`).
6. A PDF node gives `graph.unscanned`. A reference `references/Guide.md` to `references/guide.md` gives
   `graph.case`; an exact one does not (`test_case_only_matches`, fixture row `case-guide`).
7. A missing input folder exits non-zero with nothing on stdout; the input is byte-identical after a run.
8. A script with `os.listdir("prompts")` gives a `graph.dynamic` with `source` `code` resolving to the files in `prompts/`.
11. A manifest in `plugins/p/.codex-plugin/plugin.json` naming `./skills/` reaches `plugins/p/skills/`, not a top-level `skills/` (a manifest's paths are relative to its plugin root, the folder above its dot folder; the repository root stays the fallback).
10. A `.claude-plugin/plugin.json` listing two of three skill folders gives one `graph.unlisted` for the third, after the `graph.dynamic` rows.
9. A folder named in README prose is a mention (`load` false; the files under it are `via` `mention`, not orphans); a folder named in a manifest is a load (`load` true; files under it `via` `dynamic`). The rule: a dynamic edge is a load when its context is `config`, its form is `scan`, or it is a glob from a `skill`, `agent`, or `command` entry point.

### History

- 2026-10-30: M9 slice C: the report has a `coverage` list (above, "What the step looked at"). The per-file reading of references is `references` in `run.py` (it wraps `find_scans` and `extract`, which it calls as before). The findings are unchanged.
- 2026-10-31: M9 slice C, fix round: `graph.unlisted` counts a manifest where `unlisted` compares it (it counted the whole list after the call). The findings are unchanged.
- 2026-10-31: M9 slice C, last fix round: the scan line no longer counts a picture or a binary as a file looked at (it counted them where the pass decided they hold no reference); `reads_text` is its scope. The findings are unchanged.
- 2026-11-01: this step runs before the secret scan, so `graph.dangling`'s `target`, `graph.dynamic`'s `pattern`, and an edge's `text` in
  `graph.json` can hold a key the scan flags later. Nothing here changed: the runner masks both files once `02.6-builder` has read them
  (`stages/_shared/specs/shared.SPEC.md`, secretmask). `02.5-capability` still finds a hook's script by an edge's `text`, before that.

## extract

Finds every reference one text file makes, with the line it sits on, where it
sits (`context`), and how it was written (`form`). `02.3-graph`, the raw material of
edges, `graph.dangling`, and the glob / directory half of `graph.dynamic`.

### Inputs

`extract(rel, text) -> list[Found]`: the file's path relative to the input root
and its decoded text. Lines are split on `\n` only (a trailing `\r` is dropped);
each line is passed through `invisible.strip_line` before matching, and line
numbers stay the original file's.

### Outputs

`Found`: `line` (1-based), `ref` (a `tokens.Ref`), `context`, `form`.

The file kind picks the reader:

1. **Config** (`.json`, `.yaml`, `.yml`, `.toml`, `.jsonc`) that parses (JSON,
   PyYAML safe load, stdlib `tomllib`): every string value (not keys), context
   `config`, form `config`. A value without whitespace is one token; a value
   with whitespace (a hook command, `bash ${CLAUDE_PLUGIN_ROOT}/x.sh`) is split
   into code tokens. `line` is the first line at or after the previous hit that
   contains the token, else the first line anywhere that contains it, else 1.
   A config that does not parse is read as text (rule 3).
2. **Script** (`.py`, `.js`, `.mjs`, `.cjs`, `.ts`, `.mts`, `.cts`, `.sh`,
   `.bash`, `.zsh`, `.ps1`, `.psm1`, `.rb`, `.pl`, or a first line starting
   `#!`): context `code`, form `script`. Shell-like files (`.sh`, `.bash`,
   `.zsh`, `.ps1`, `.psm1`, or a `#!` naming a shell) give every token on
   every line; other scripts give only tokens inside string literals
   (`'...'`, `"..."`, `` `...` `` on one line), so identifiers like `os.path`
   never count.
3. **Text** (every other decodable file: markdown, HTML, plain text, license):
   - Fenced blocks (```` ``` ```` or `~~~`, with any info string): every token,
     context `code`, form `fenced`.
   - HTML comments (`<!-- ... -->`, may span lines): every token, context
     `comment`, form `comment`.
   - Markdown links and images `[t](target "title")`, `![a](target)`,
     reference definitions `[id]: target`, and HTML `href="..."` / `src="..."`
     (single or double quotes): the target, context `link`, form
     `markdown-link`, `image`, `reference-def`, or `html-attr`. The link text
     is then read as prose.
   - Inline code spans (one or more backticks): every token, context `code`,
     form `code-span`.
   - Everything else on the line: context `prose`, form `prose`.

Tokens are split on whitespace and on characters that cannot sit in a path
here: `|`, `,`, `;`, `=`, `(`, `)`, quotes, and backticks. Common HTML tags
(`<b>`, `</code>`, `<br>`, ...) are blanked first; other `<...>` stay inside the
token so a template such as `plans/<topic>.md` is seen whole (and rejected by
`tokens`). A placeholder's braces (`${VAR}`) are kept. A token directly
followed by `(` without a `/` is a call (`console.log(x)`) and is skipped.
Each token goes through `tokens.classify` with its context; tokens that are
not references are dropped.

**Pattern-list files** (`.gitignore`, `.gitattributes`, `.npmignore`,
`.dockerignore`, `.prettierignore`, `.eslintignore`, `.ignore`, `.rgignore`,
`.gcloudignore`, `.vscodeignore`, `CODEOWNERS`): every line is a match rule for
a tool, not a load, so they give no references. They stay nodes.

The same reference (same line, same resolved `path`) is kept once, the first
reader wins (links before code spans before prose), so a link whose text
repeats its target makes one reference.

### Must never

- Follow a link or a URL, or run anything.
- Skip HTML comments or code blocks: a model receives both.
- Shift a line number.

### Done when (each backed by a test in `tests/test_extract.py`)

1. In markdown, `[a](docs/a.md)` is `link` / `markdown-link`, `![i](img.png)` is `image`, `[r]: ref.md` is `reference-def`, `<a href="h.md">` is `html-attr`.
2. `` `scripts/setup.sh` `` in a line is `code` / `code-span`; `bash scripts/run.sh` inside a fenced block is `code` / `fenced`.
3. A path inside a multi-line HTML comment is `comment`, with the line it sits on.
4. `see references/details.md.` is `prose` with `written` `references/details.md`.
5. A path split by U+200B is found, on its original line number.
6. In a JSON hook config, `bash ${CLAUDE_PLUGIN_ROOT}/hooks/start.sh` gives a `config` reference to `hooks/start.sh` on the line it appears; YAML and TOML string values are read the same way; a broken JSON file is read as text.
7. In a Python script, `open("data/x.json")` gives a `code` / `script` reference and `os.path.join` gives none; in a shell script, `source lib/common.sh` gives one.
8. `[references/a.md](references/a.md)` gives one reference, not two.
9. `console.log(x)` in a fence gives nothing; `<b>docs/a.md</b>` gives `docs/a.md`; `docs/<topic>-design.md` gives nothing; a `.gitignore` or `.gitattributes` gives nothing.

## invisible

Strips invisible characters from a line before `02.3-graph` matches references, so a
path split by a zero-width character still matches. A reimplementation of the
strip half of `02.2-reader`'s fold (`stages/02-coded/02.2-reader/specs/reader.SPEC.md`, section `fold`); `02.3-graph` never
imports `02.2-reader`.

### Inputs

One line of decoded text (no line ending), or the bytes of a whole file.

### Outputs

`strip_line(line) -> str`:

1. Remove the characters `Library/invisible.yaml` lists with action `strip`: zero-width characters
   U+200B-U+200F, U+2060-U+2064, U+FEFF, and, since 2026-10-29, U+180E, U+034F, U+206A-U+206F,
   U+FFF9-U+FFFB, U+1D173-U+1D17A, U+1BCA0-U+1BCA3; bidi controls U+202A-U+202E, U+2066-U+2069,
   U+061C; soft hyphen U+00AD; the blank letters and cells U+115F, U+1160, U+3164, U+FFA0, U+17B4,
   U+17B5, U+2800; Unicode tag characters U+E0000-U+E007F; NUL. Remove, too, the variation
   selectors of a run (two or more characters with action `run`, in a row or with only stripped
   characters between them, `library.runs`); one alone stays, even with a stripped character after it.
2. NFKC normalize.

No confusable folding: a path that uses a lookalike letter is a different path
on disk, so it must not be made to match.

`decode(data) -> str | None`: the text of a file, or None when it is not text.
A BOM (UTF-8, UTF-16 LE/BE, UTF-32 LE/BE) picks the codec and is dropped; bytes
holding NUL without a BOM: bytes with NUL are binary when NUL is more than 1% of the bytes or the rest is not strict UTF-8; a few NULs in valid UTF-8 are text (2026-10-09: a literal `\0` sentinel in source made a file binary, so one NUL could hide any file); then UTF-8; then the encoding
`charset-normalizer` detects; else None.

The characters removed and the runs are read from `Library/invisible.yaml` through `stages/_shared/library.py`,
the list `02.2-reader`, `02.3-graph`, `02.4-phrases`, `02.5-capability`, and `06-report` share (restructure step 3, 2026-10-29);
this stage strips only (it reads no text a run spells), and leaves U+2028, U+2029, and U+0085 as they are.

### Must never

- Add or drop a line (callers split on `\n` and keep line numbers).
- Change an ASCII character.

### Done when (each backed by a test in `tests/test_invisible.py`)

1. `refer\u200bences/de\u200dtails.md` strips to `references/details.md`.
2. Bidi controls, a soft hyphen, and tag characters are removed; ASCII text is unchanged.
3. Fullwidth `ｄｏｃｓ／ａ.md` normalizes to `docs/a.md` (NFKC).
4. A Cyrillic `о` is kept (no confusable folding).
5. `decode` reads UTF-8, UTF-8 with BOM (BOM dropped), and UTF-16 with BOM; returns None for bytes holding NUL.
6. A path split by a character P1 added (a format character, a blank letter or cell) or by a run of variation selectors (zero-width spaces between the selectors included) strips to the whole path; one selector alone stays (`test_the_new_invisible_characters_split_nothing`).

NUL (U+0000) is stripped like the other invisible characters (2026-10-09).

### History

- 2026-10-29 (P1): the list gained the characters of an outside note and its measurement (2026-10-28)
  and the `run` action for variation selectors; `strip_line` strips them from the list, with no
  change to the script's own rules. U+180E is stripped here too (it was left in place).
- 2026-10-29 (P1, review before verification): a run is selectors in a row or separated only by
  characters the list strips, so a zero-width space between two selectors does not keep them in the path.
- 2026-10-30: M9 slice B: this step writes its notes through `stagenote`, so a note that names a file or a path from the repository is one line, and a name with a line break cannot pass for a note of its own.

## reach

Reachability and depth over the reference graph: `graph.orphan` and
`graph.depth`.

### Inputs

`reach(nodes, entries, edges) -> Reach`: every node path; the entry-point
paths; edges as `(from, to, kind)` with `kind` `static`, `dynamic` (a load), or `mention`
(a folder or glob mention; run.SPEC decides which).

### Outputs

`Reach`: `depth` ({node: int}, reachable nodes only), `parent` ({node: str or
None}), `via` ({node: `static`, `dynamic`, or `mention`}), `orphans` (sorted list).

- Breadth-first from every entry point at once; entry points are depth 0,
  parent None, via `static`.
- **Depth is measured over static edges first** (changed 2026-09-29). A node
  reachable through static edges alone gets its depth over static edges only,
  `via` `static`, even when a dynamic edge reaches it in fewer hops. On
  one large repository, directory mentions ("see `skills/`") otherwise put most files one
  hop from an entry point and the depth measure stopped telling anything.
- Tiers, strongest first: static, dynamic, mention (2026-09-29). A node takes
  the first tier that reaches it together with every stronger tier, and its
  depth over those edges: reachable over static plus dynamic edges is `via`
  `dynamic`; reachable only once mention edges are added is `via` `mention`.
  Either way it is reachable, never an orphan.
- `parent` is a node one hop closer on the shortest path the depth came from.
  Ties break by sorted path, so the output is stable.
- Orphans: nodes reachable from no entry point over any edges.
- Self-edges and edges to unknown nodes are ignored.

`depth_findings(reach)` and `orphan_findings(reach)` give the contract
findings (`graph.depth` with `depth`, `from`, `via`, `line` null;
`graph.orphan` with `line` null), in path order.

### Must never

- Rank or judge orphans.
- Drop dynamic or mention edges from reachability.

### Done when (each backed by a test in `tests/test_reach.py`)

1. A chain `E -> a -> b` gives depths 0, 1, 2 with parents None, E, a.
2. A file reached only by a dynamic edge is reachable, `via` `dynamic`.
3. A file reached by a dynamic edge at depth 1 and a static path at depth 2 is depth 2, `via` `static`, with the static parent.
6. A file reached only through a dynamic hop followed by a static hop is depth 2, `via` `dynamic`.
4. Two entry points: each node takes the nearer one.
5. A file nothing reaches is an orphan and has no depth finding; an entry point is never an orphan.
7. Tiers: a file reached only by a mention is `via` `mention`; one reached by a load is `via` `dynamic`; a file a mention reaches in one hop but a static-then-load path reaches in two is `via` `dynamic` at depth 2.

## resolve

Turns a reference into the nodes it names. Works on the node list only (the
paths `02.1-inventory` inventoried); never touches the disk.

### Inputs

`Resolver(nodes)`: every node path, relative, forward slashes. Folders are
every proper prefix of a node path.

### Outputs

`resolve(from_rel, path, shape) -> Result`, where `path` and `shape` come from
`tokens.Ref`. `Result` has `status`, `targets` (sorted node paths),
`ambiguous` (bool), `case_mismatch` (bool), `partial` (bool), `by_name` (bool), `pattern` (for `glob` and `dir`).

`folder_missing(from_rel, path) -> bool`: the folder a path points into exists neither from the
referring file's folder nor from the root (a path with no folder part is never missing one).
`02.3-graph` marks a dangling reference with it, so a report can tell "into a folder the repository
does not have" (often one the workflow creates when it runs, such as `output/`) from a file
missing beside its siblings (2026-10-21).

`status` is one of:

- `outside`: the path escapes the input root via `..`, resolved from the
  referring file's folder (or from the root when there is no folder to try).
  Never dangling.
- `file`: one or more node files.
- `dir`: an existing folder. `pattern` is the folder with a trailing `/`;
  `targets` is every node under it, recursively.
- `glob`: `shape` was `glob`. `pattern` is the glob as written after cleaning;
  `targets` its matches (possibly empty). `*` and `?` match within one
  segment, `**` across segments, `[...]` is a character class.
- `missing`: nothing matched.

Order of attempts, first hit wins:

1. `glob` shape: match relative to the referring file's folder; if that
   matches nothing, relative to the root.
2. Exact, relative to the referring file's folder; then relative to the root.
   A node file gives `file`; a folder gives `dir`.
3. A bare name (no `/`, shape `bare` or `link`): every node whose basename is
   equal, `by_name` true (found only by its name elsewhere; 2026-10-27, slice 5). Several give
   `ambiguous` true.
3b. A partial path (it has a `/`, does not end in one, and does not start with `./` or `../`):
   every node whose path ends with `/` plus it, `partial` true; several give `ambiguous` true
   (2026-10-21, an outside tester: a README's `rules/carousel-rules.md` for
   `_shared/rules/carousel-rules.md` was reported dangling).
4. The same tries case-insensitively (never for globs): a hit gives
   `case_mismatch` true.
5. A path with percent escapes (`%20`, any `%` and two hex digits) that is still missing: steps
   1 to 4 again with it decoded, as a Markdown link writes a space (2026-10-25, review C43, an
   outside tester: `my%20skill.md` was reported dangling and `my skill.md` an orphan).
   The path as written is always tried first, so a file named with a literal `%20` still matches.
6. `missing`.

A path ending in `/` resolves only to a folder.

### Must never

- Read the file system, or resolve outside the node list.
- Compare case-insensitively before every case-sensitive try has failed.

### Done when (each backed by a test in `tests/test_resolve.py`)

1. From `skills/x/SKILL.md`, `references/a.md` resolves to `skills/x/references/a.md` when it exists, else to root `references/a.md`.
2. A bare `helpers.md` found in two folders gives both, `ambiguous` true.
3. `README.MD` with only `README.md` present gives `case_mismatch` true.
4. `extra/` is `dir` with every file under it, recursively; `extra/*.md` is `glob` matching direct children only; `extra/**/*.md` matches nested ones.
5. `../../x.md` from `a/b.md` is `outside`; `../x.md` from `a/b.md` is root `x.md`.
6. An unknown path is `missing`; a glob with no match is `glob` with no targets.
7. `rules/carousel-rules.md` with only `_shared/rules/carousel-rules.md` present resolves to it, `partial` true; `./rules/carousel-rules.md` stays `missing`; two such files give both, `ambiguous` true.
8. `folder_missing`: `output/post.md` with no `output/` folder anywhere is true; `references/gone.md` beside an existing `references/` is false; a bare `gone.md` is false.
9. `my%20skill/SKILL.md` resolves to `my skill/SKILL.md`; a file named `a%20b.md` matches as written; `gone%20x.md` stays `missing` (`test_percent_escapes_are_decoded_when_missing`).

## scans

Finds code that lists or globs a folder: the "scans in code" half of
`graph.dynamic` (source `code`). A load whose targets exist only at run time.

### Inputs

`find_scans(rel, text) -> list[Scan]`, for script files only (the same script
rule as `extract.py`: `.py`, `.js`, `.mjs`, `.cjs`, `.ts`, `.mts`, `.cts`,
`.sh`, `.bash`, `.zsh`, `.ps1`, `.psm1`, `.rb`, `.pl`, or a `#!` first line).
Any other file gives an empty list. `is_script(rel, text)` exposes that rule.

### Outputs

`Scan`: `line`, `call` (the call name as matched), `pattern`, `literal` (bool),
`recursive` (bool).

Calls recognized (one `Scan` per call, a line may hold several):

| Call | Recursive |
|---|---|
| `os.listdir`, `os.scandir`, `readdir`, `readdirSync`, `fs.readdir`, `opendir` | no |
| `os.walk`, `rglob`, `find`, `Get-ChildItem` with `-Recurse` | yes |
| `glob.glob`, `glob.iglob`, `.glob(`, `glob(` in JS | pattern decides |
| `ls`, `Get-ChildItem` / `gci` without `-Recurse` | no |

- Function calls: the first argument, when it is a string literal, is the
  pattern (`literal` true). Otherwise `pattern` is the call text (the call name
  through the matching `)` on that line, or the rest of the line), and `literal`
  is false.
- Shell `ls`, `find`, `Get-ChildItem`, `gci`: recognized only as a command (at
  the start of the line or after `;`, `&&`, `||`, `|`, `$(`, or a backtick).
  The first argument that is not a flag, quotes removed, is the pattern; it is
  literal unless it holds `$`, `%`, or backticks. With no argument, the pattern
  is `.` (the current folder, not literal: it depends on where it runs).

Whole-line comments (`#` other than a `#!` line, `//`) are skipped: a call
named in a comment is not a call.

### Must never

- Run the code.
- Report a scan in a non-script file.

### Done when (each backed by a test in `tests/test_scans.py`)

1. `glob.glob("skills/*/SKILL.md")` gives a literal pattern `skills/*/SKILL.md`.
2. `os.listdir(folder)` gives a non-literal scan whose pattern is the call text.
3. `os.walk("docs")` and `Path("x").rglob("*.md")` are recursive.
4. `fs.readdirSync(path.join(__dirname, "skills"))` is found (non-literal).
5. In a shell script, `for f in $(ls prompts/); do` gives a literal scan of `prompts/`; `find "$DIR" -name '*.md'` gives a non-literal recursive scan.
6. `Get-ChildItem -Recurse agents` in a `.ps1` is recursive with pattern `agents`.
7. A markdown file mentioning `os.listdir("x")` gives nothing.

## tokens

Decides whether a piece of text is a file reference, and in what shape. Pure
string work: never touches the disk.

### Inputs

A raw token (text between separators) and the context it was found in:
`prose`, `code`, `link`, `comment`, or `config`.

### Outputs

`clean(token) -> str`: the token with wrapping punctuation removed: leading
`( [ { < > @ " ' `` ` `` (so a `@./path` import reads as `./path`) and trailing
`) ] } > < " ' `` ` `` , ; : ! ? \` and trailing `.`; a leading JS spread `...`
before a name; markdown emphasis runs of `*` at either end, except a `*` that is
part of a glob (followed by `/` or `.` at the start, preceded by `/` at the
end); a symmetric `_..._` wrapper (so `__init__.py` is untouched). Markdown
escapes (`\_`, `\*`, `\[`, ...) are unescaped first.

`classify(token, context) -> Ref | None`. `Ref` has:

- `written`: the cleaned token, as written (the `target` of a dangling finding).
- `path`: what is resolved: backslashes turned into `/`; a leading variable
  placeholder (`${VAR}/`, `$VAR/`, `%VAR%\`) and leading `./` removed; a
  trailing `#anchor` removed; a trailing `?query` removed when the part after
  `?` holds `=` or `&`.
- `shape`: one of
  - `glob`: holds `*`, `?`, or a `[...]` class, and has a `/` or an extension.
  - `dir`: ends with `/`.
  - `path`: holds a `/` and its last segment has an extension (a segment that
    starts with `.` and has more characters counts, e.g. `config/.env`).
  - `bare`: no `/`, non-empty stem, an extension.
  - `link`: only in `link` context, any other non-empty target (a link names a
    path whatever its shape).
  - `slashed`: holds a `/`, no extension, no trailing `/` (`skills/brainstorm`).
    Only in `code`, `link`, and `config` context; it becomes an edge only when
    it resolves (to a file or a folder), and is never dangling.
- `may_dangle`: whether an unresolved `Ref` is reported as dangling:
  - `bare` in `prose` or `comment`: never.
  - `bare` in `code` or `config`: only when the extension is in the known
    file-extension list (`KNOWN_EXTS`; keeps `console.log` and `os.path` from
    becoming dangling while keeping `helpers.md`).
  - `bare` and `link` in `link` context: always.
  - `path`, `dir`, `glob`: always (a glob never dangles; it becomes a dynamic
    load with an empty match list).
  - `slashed`: never.

An extension is `.` plus 1 to 10 letters, digits, `_`, or `-`, holding at least
one letter (so `v1.2` and `3.14` are not files).

`classify` returns None (not a reference) for:

- URLs (`scheme://`, `mailto:`, `data:`, `javascript:`), and anchors alone (`#x`).
- Paths outside the tree: absolute (`/etc/x`, `C:\x`, `\\server\x`), home
  (`~/x`, `$HOME/x`, `${HOME}/x`, `%USERPROFILE%\x`). (`..` escapes are decided
  by the resolver, which knows the referring folder.)
- A bare dotfile name with an empty stem (`.env`, `.gitignore`) in prose or a comment.
- `.git` and anything under `.git/`: not part of the input (`02.1-inventory` never walks it).
- Regexes and templates, whose target is not a fixed path: a token holding `^`,
  a trailing `$`, `\.`, `.*` or `.+`, `(?`, or `...`; an angle placeholder
  `<name>` or a brace placeholder `{name}` (a `${VAR}` prefix is a placeholder,
  stripped as above); a `$` variable left anywhere after the prefix is
  stripped; a glob-looking token holding a backslash (an escaped string such as
  `\n` or `\d`).
- `[0]` style indexes are not glob classes (`files[0].path` is no glob).
- Tokens with no shape above (plain words, `and/or`, `I/O`, `1.5/2.0`).

### Must never

- Treat a URL, an absolute path, or a home path as a reference.
- Read the file system.

### Done when (each backed by a test in `tests/test_tokens.py`)

1. `references/details.md.` cleans to `references/details.md` and is a `path` that may dangle.
2. `SKILL.md` is `bare`; in prose it may not dangle, in code it may; `Node.js` in code may dangle (known extension), `console.log`-like `obj.method` in code may not.
3. `extra/*.md`, `*.md`, and `skills/**/SKILL.md` are `glob`; `**Note:**` is not a reference.
4. `extra/` is `dir`; `and/or`, `I/O`, `v1.2`, `3.14`, and `1.5/2.0` are not references.
5. `https://x.invalid/a.md`, `mailto:a@b.invalid`, `#section`, `/etc/passwd`, `C:\x\y.md`, `~/x.md`, and `$HOME/x.md` are None.
6. `${CLAUDE_PLUGIN_ROOT}/hooks/run.sh` has `path` `hooks/run.sh` and `written` with the placeholder kept; `./a/b.md#part` has `path` `a/b.md`; `a\b.md` has `path` `a/b.md`.
7. `.env` in prose is None; `config/.env` is a `path`.
8. In link context, `docs` is a `link` shape that may dangle; `skills/x` in code is `slashed` and may not dangle.
9. `__init__.py` survives cleaning; `_emph.md_` cleans to `emph.md`; `...process.env` never dangles.
10. `@./skills/a/SKILL.md` has `path` `skills/a/SKILL.md`; `STYLE\_GUIDE.md` has `path` `STYLE_GUIDE.md`.
11. `s/^/`, `node.*server.js`, `docs/plans/<name>.md`, `plans/{date}.md`, `origin/dev...HEAD`, `foo/$x/bar.md`, and `.git/` paths are None; `files[0].path` is no glob.

## unlisted

Manifest versus disk, the other half (METHOD; 2026-10-18). `02.3-graph`, check `graph.unlisted`.

A manifest that names the skills, agents, or commands a plugin ships is what a reviewer reads to
learn what it holds. A component on disk beside it that the manifest leaves out is easy to miss,
and a host that finds components by folder (Claude Code loads `skills/`, `agents/`, `commands/`
whatever the manifest lists) can still load it. `02.3-graph` reports where the two disagree; whether
the host loads the unlisted one is the host's rule, not a fact in the repository.

### Inputs

`unlisted(manifests, nodes, edges) -> list[dict]`:

- `manifests`: the files `02.1-inventory` marked `entry_point` `manifest`.
- `nodes`: every file path in the tree.
- `edges`: `02.3-graph`'s edges (`from`, `to`, `kind`), static and dynamic.

### Rules

- A manifest's **root** is the folder above it when it sits in a dot folder
  (`.claude-plugin/plugin.json`, `.codex-plugin/...`), else its own folder.
- **Components** under the root, by kind: a `skill` is a folder holding a `SKILL.md` (the
  component's file is that `SKILL.md`); an `agent` is a `.md` file directly in an `agents/`
  folder; a `command` is a `.md` file directly in a `commands/` folder. Components under
  another manifest's root below this one belong to that one. Manifests that share a root (one
  per host: `.claude-plugin/`, `.cursor-plugin/`) are each compared with its components.
- A component is **listed** when an edge from the manifest reaches its file, or (for a skill)
  any file in its folder.
- A manifest **enumerates** a kind when it lists at least one component of that kind. Only
  kinds it enumerates are compared: a manifest that names no skills relies on the folder, and
  there is nothing to compare.

### Outputs

One `graph.unlisted` finding per component of an enumerated kind that its manifest does not
list: `check`, `file` (the component's file), `line` null, `manifest`, `kind`, `listed` (how
many of that kind the manifest lists), `on_disk` (how many of that kind are under its root).
Ordered by manifest, kind, file.

### Measured (2026-10-18)

The four audited repositories at their audited commits: 0. Two large public repositories
(current): 0, and 1 of 1 when one skill is left out of a Codex manifest in
the layout of one of them; a third: 1 (`template/SKILL.md`, 19 of 20 named by its
marketplace).

### Must never

- Compare a kind the manifest does not enumerate.
- Say whether the host loads an unlisted component.

### Done when (each backed by a test in `tests/test_unlisted.py`)

1. A `.claude-plugin/plugin.json` listing skills `a` and `b` of `a`, `b`, `c`, and agent `x`
   of `x`, `y`, gives `skills/c/SKILL.md` (`kind` skill, `listed` 2, `on_disk` 3) and
   `agents/y.md`; commands, which it does not list, give nothing.
2. A manifest that reaches every skill through a folder reference (`./skills/`) gives nothing.
3. A manifest with no component references gives nothing.
4. A skill under a nested plugin's own manifest is that manifest's, not the outer one's.
5. Two manifests at one root (`.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`) are each compared: one listing every skill gives nothing, the other listing one of two gives the other.
