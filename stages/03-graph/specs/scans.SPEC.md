# scans.py: spec

Finds code that lists or globs a folder: the "scans in code" half of
`graph.dynamic` (source `code`). A load whose targets exist only at run time.

## Inputs

`find_scans(rel, text) -> list[Scan]`, for script files only (the same script
rule as `extract.py`: `.py`, `.js`, `.mjs`, `.cjs`, `.ts`, `.mts`, `.cts`,
`.sh`, `.bash`, `.zsh`, `.ps1`, `.psm1`, `.rb`, `.pl`, or a `#!` first line).
Any other file gives an empty list. `is_script(rel, text)` exposes that rule.

## Outputs

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

## Must never

- Run the code.
- Report a scan in a non-script file.

## Done when (each backed by a test in `tests/test_scans.py`)

1. `glob.glob("skills/*/SKILL.md")` gives a literal pattern `skills/*/SKILL.md`.
2. `os.listdir(folder)` gives a non-literal scan whose pattern is the call text.
3. `os.walk("docs")` and `Path("x").rglob("*.md")` are recursive.
4. `fs.readdirSync(path.join(__dirname, "skills"))` is found (non-literal).
5. In a shell script, `for f in $(ls prompts/); do` gives a literal scan of `prompts/`; `find "$DIR" -name '*.md'` gives a non-literal recursive scan.
6. `Get-ChildItem -Recurse agents` in a `.ps1` is recursive with pattern `agents`.
7. A markdown file mentioning `os.listdir("x")` gives nothing.
