# Stage 3: Graph

**Question:** what loads what?
**Kind of evidence:** a reference graph. Nodes are files; edges are one file
naming another. Every edge carries the file and line that makes it.
**Report heading:** What loads what.

Stage 3 finds what nothing points at, what points at nothing, and where the graph
cannot be known at review time. It is a locator, never a verdict: an orphan is
usually dead weight, a dangling reference is usually rot. The value is in the
pairs a human reads later (orphan plus a stage 4 hit; a clean entry file one hop
from a payload).

Sources for every rule below: `pre-planning/METHOD.md` (Stage 3),
`pre-planning/THREATS.md` (classes 10 and 12), `pre-planning/REPORTING.md`
(Section 3), `pre-planning/RUN-LAYOUT.md` (`03-graph.md`),
`pre-planning/TOOLING.md` (Stage 3), `stages/CONTRACT.md`. Nothing here comes
from the answer sheet; a builder of this stage never opens `Fixtures/ANSWERS/`.

---

## Inputs

- `<input_dir>`: a pinned repo copy or a fixture folder. Read-only.
- **Entry points come from stage 1.** Stage 3 gets them through stage 1's
  contract, never by importing its code:
  - `--inventory <file>`: a stage 1 report (JSON) already produced for this input.
  - Without it, `run.py` runs `stages/01-inventory/run.py <input_dir>` as a
    subprocess with the same Python and reads its report. If that fails, stage 3
    fails (exit non-zero); a graph with no entry points is not a result.
- An entry point is every `inv.file` finding whose `entry_point` is not null
  (`skill`, `agent`, `command`, `hook-config`, `manifest`, `mcp-config`,
  `readme`, `ci`).

## Outputs

- `run.py <input_dir>` prints one contract-1 report to stdout.
- `run.py <input_dir> --out <dir>` also writes `<dir>/graph.json`: every node
  (path, entry kind or null, depth or null) and every edge (`from`, `line`,
  `to`, `kind`: `static` or `dynamic`, `form`: how it was written, `text`: the
  reference as written). Never writes inside `<input_dir>`. The prose
  `03-graph.md` belongs to the report stage, not here.

## Nodes

Every file under `<input_dir>` is a node, walked with stage 1's rules (never
follow a symlink out of the tree; `.git/` is not part of the input). Nodes are
paths relative to `<input_dir>` with forward slashes.

## Edges: what counts as a reference

Scan every file that decodes as text (UTF-8, or the encoding
`charset-normalizer` detects). Before matching, apply the invisible-character
strip from stage 2's fold (remove U+200B-U+200F, U+2060-U+2064, U+FEFF,
U+202A-U+202E, U+2066-U+2069, U+00AD, U+E0000-U+E007F; NFKC) so a path split by
a zero-width character still matches. Line numbers are the original file's.

Read references from the raw text, including HTML comments and code blocks: a
model receives both. Record where each reference sits as `context`: `prose`,
`code` (inline code span or fenced block), `link` (markdown link, image, or
reference definition; HTML `href` / `src`), `comment` (HTML comment), or
`config` (a string value in JSON, YAML, or TOML).

Reference forms:

1. **Links.** Markdown `[text](target)`, `![alt](target)`, reference
   definitions `[id]: target`, HTML `href="…"` and `src="…"`.
2. **Code spans and fenced blocks.** Tokens that look like paths, including
   script arguments (`bash scripts/setup.sh`, `python tools/check.py`).
3. **Prose paths.** Tokens containing a `/` whose last segment has a file
   extension, or that end in `/`.
4. **Bare filenames** in prose (`SKILL.md`, `helpers.md`): a token with a
   non-empty stem and a file extension. These make an edge only when they
   resolve; an unresolved bare filename in prose is **not** a dangling
   reference (too noisy: `Node.js`, `v1.2`). A bare filename in a link or code
   span that does not resolve **is** dangling.
5. **Config strings.** In JSON / YAML / TOML (manifests, hook configs, MCP
   configs), every string value that looks like a path by rules 2 to 4. Strip a
   leading variable placeholder (`${CLAUDE_PLUGIN_ROOT}/`, `$PLUGIN_DIR/`,
   `%VAR%\`) and `./` before resolving; resolve against the input root.

Not references (skip them; they belong to later stages):

- URLs (`scheme://…`, `mailto:`), and anchors alone (`#section`). Strip a
  trailing `#anchor` or `?query` from a path before resolving.
- Paths outside the tree: absolute (`/etc/…`, `C:\…`), home (`~/…`,
  `$HOME/…`), or resolving above `<input_dir>` via `..`. Stage 4 and 5 read
  those; stage 3 does not report them as dangling.
- Dotfile names with an empty stem (`.env`, `.gitignore`) when bare in prose.

**Resolving.** Try, in order: relative to the referring file's folder, then
relative to `<input_dir>`. A bare filename with no `/` that matches neither
resolves by basename anywhere in the tree; if several files share it, add an
edge to each and mark the edges `ambiguous: true`. Accept `\` as a separator.
Compare paths case-sensitively, but when only a case-insensitive match exists,
make the edge and mark it `case_mismatch: true` (it resolves on Windows and
macOS, not on Linux).

## Dynamic loads

An edge whose target is not fixed at review time. Each is one `graph.dynamic`
finding and makes edges (`kind: dynamic`) to every file it resolves to today.

- **Globs.** A path token containing `*`, `?`, or `[…]`. `pattern` is the
  token; `resolves` is the sorted list of files it matches, evaluated relative
  to the referring file's folder, then `<input_dir>`.
- **Directory references.** A path token that resolves to an existing folder
  ("see `references/`", "every file under extra/"). `pattern` is the folder with
  a trailing `/`; `resolves` is every file under it, recursively.
- **Scans in code.** In script files (`.py`, `.js`, `.ts`, `.sh`, `.ps1`, and
  files with a `#!` line): calls that list or glob a folder (`os.listdir`,
  `os.scandir`, `os.walk`, `glob.glob`, `Path.glob` / `rglob`, `readdir`,
  `fs.readdirSync`, `ls`, `find`, `Get-ChildItem`). `pattern` is the literal
  argument when there is one, else the call text; `resolves` is its matches, or
  an empty list when the argument is not a literal.

A dynamic load means the graph is incomplete by construction. The report says
so; it never presents the graph as closed when any `graph.dynamic` exists.

## Reachability and depth

Breadth-first from every entry point. Entry points are depth 0.

- **Depth is over direct references.** A file reachable through static edges
  gets its depth over static edges only, `via: static`, even when a dynamic
  load reaches it sooner. (Changed 2026-09-29 after the first superpowers run:
  directory mentions put most files one hop out and flattened the measure.)
- **Dynamic edges still count for reachability**: a file loaded only by a glob
  or directory reference is reachable, never an orphan ("undocumented does not
  mean unloaded", METHOD).
- **Load versus mention** (added 2026-09-29, second superpowers run). A dynamic
  edge is a **load** when a config or manifest names the folder (`context:
  config`), a script scans it (`form: scan`), or an instruction file (entry kind
  `skill`, `agent`, `command`) gives the glob. Every other dynamic edge is a
  **mention**: a folder or glob named in docs, plans, READMEs, or in instruction
  prose that is not a load ("save plans in `docs/plans/`"). Each node takes the
  strongest tier that reaches it: `via: static` (depth over direct references),
  `via: dynamic` (depth over direct references plus loads), `via: mention`
  (depth over every edge). Loads are their own list in the report: live, but
  named by nothing. Mentions are reachable, never orphans, and are not a load.
  On superpowers this took the dynamic-only list from 113 files to 7 (the
  skill-folder files only the Codex manifest loads).
- `graph.dynamic` and each dynamic edge in `graph.json` carry `load`: true or
  false by the same rule.

## Checks

| Check ID | One finding per | Fields | Source |
|---|---|---|---|
| `graph.entry` | entry point used | `kind`: the stage 1 entry kind | METHOD Stage 3 |
| `graph.orphan` | file reachable from no entry point (`line`: null) | none required | THREATS class 12 |
| `graph.dangling` | reference that resolves to nothing (`file`, `line`: where it is written) | `target`: the path as written; `context` | THREATS class 12 |
| `graph.dynamic` | glob, directory reference, or code scan (`file`, `line`: where it is written) | `pattern`; `resolves`: files it matches today; `source`: `glob`, `directory`, or `code`; `load`: bool (see "Load versus mention") | THREATS class 12 |
| `graph.depth` | reachable file, entry points included (`line`: null) | `depth`; `from`: the parent on the path the depth came from (null at depth 0); `via`: `static`, `dynamic` (a load reaches it), or `mention` (only a folder or glob mention reaches it) | THREATS class 10 |
| `graph.unscanned` | node that may hold references but was not scanned (PDF, DOCX, other binary documents, undecodable text) | `reason` | CLAUDE.md "never pass silently" |

Orphans are one finding per file, whatever the file: a license, an image, a
staged payload. Orphan is a locator. The report groups them; stage 3 does not
decide which ones matter.

**Manifest versus disk** (METHOD) in v1: a path a manifest names that does not
exist is a `graph.dangling` finding from the manifest file. The other half,
files on disk no manifest covers (six skill folders beside a manifest listing
five), is not built in v1; `run.py` says so on stderr so stage 7 can list it.

## Dependencies

Standard library only (TOOLING: "stdlib dict, or networkx"), plus
`charset-normalizer` and `PyYAML`, already pinned in `requirements.txt`. TOML
through stdlib `tomllib`. No new packages without a note to the user.

## Must never

- Judge why a file is unreferenced, or rank orphans.
- Report an unresolved bare filename in prose as dangling.
- Follow a URL, execute anything from the input, or follow a symlink out of the
  tree.
- Write inside `<input_dir>`.
- Import code from another stage. Stage 1 is reached through its runner.
- Present the graph as complete when a dynamic load exists.

## Done when

1. Every script in this folder has a `specs/<name>.SPEC.md` and pytest tests written
   from it, and they pass.
2. `.venv/Scripts/python grader/grader.py 03` reports PASS.
3. Run on `ReposToExamine/superpowers-main/superpowers-main/` it completes.
   Record for the run log: entry points, orphans, dangling references (split by
   `context`), dynamic loads, and the depth histogram. First graph ever built on
   a real repo; no earlier numbers to compare against.
