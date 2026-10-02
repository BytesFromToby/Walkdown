# extract.py: spec

Finds every reference one text file makes, with the line it sits on, where it
sits (`context`), and how it was written (`form`). Stage 3, the raw material of
edges, `graph.dangling`, and the glob / directory half of `graph.dynamic`.

## Inputs

`extract(rel, text) -> list[Found]`: the file's path relative to the input root
and its decoded text. Lines are split on `\n` only (a trailing `\r` is dropped);
each line is passed through `invisible.strip_line` before matching, and line
numbers stay the original file's.

## Outputs

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

## Must never

- Follow a link or a URL, or run anything.
- Skip HTML comments or code blocks: a model receives both.
- Shift a line number.

## Done when (each backed by a test in `tests/test_extract.py`)

1. In markdown, `[a](docs/a.md)` is `link` / `markdown-link`, `![i](img.png)` is `image`, `[r]: ref.md` is `reference-def`, `<a href="h.md">` is `html-attr`.
2. `` `scripts/setup.sh` `` in a line is `code` / `code-span`; `bash scripts/run.sh` inside a fenced block is `code` / `fenced`.
3. A path inside a multi-line HTML comment is `comment`, with the line it sits on.
4. `see references/details.md.` is `prose` with `written` `references/details.md`.
5. A path split by U+200B is found, on its original line number.
6. In a JSON hook config, `bash ${CLAUDE_PLUGIN_ROOT}/hooks/start.sh` gives a `config` reference to `hooks/start.sh` on the line it appears; YAML and TOML string values are read the same way; a broken JSON file is read as text.
7. In a Python script, `open("data/x.json")` gives a `code` / `script` reference and `os.path.join` gives none; in a shell script, `source lib/common.sh` gives one.
8. `[references/a.md](references/a.md)` gives one reference, not two.
9. `console.log(x)` in a fence gives nothing; `<b>docs/a.md</b>` gives `docs/a.md`; `docs/<topic>-design.md` gives nothing; a `.gitignore` or `.gitattributes` gives nothing.
