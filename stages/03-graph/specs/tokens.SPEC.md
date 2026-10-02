# tokens.py: spec

Decides whether a piece of text is a file reference, and in what shape. Pure
string work: never touches the disk.

## Inputs

A raw token (text between separators) and the context it was found in:
`prose`, `code`, `link`, `comment`, or `config`.

## Outputs

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
- `.git` and anything under `.git/`: not part of the input (stage 1 never walks it).
- Regexes and templates, whose target is not a fixed path: a token holding `^`,
  a trailing `$`, `\.`, `.*` or `.+`, `(?`, or `...`; an angle placeholder
  `<name>` or a brace placeholder `{name}` (a `${VAR}` prefix is a placeholder,
  stripped as above); a `$` variable left anywhere after the prefix is
  stripped; a glob-looking token holding a backslash (an escaped string such as
  `\n` or `\d`).
- `[0]` style indexes are not glob classes (`files[0].path` is no glob).
- Tokens with no shape above (plain words, `and/or`, `I/O`, `1.5/2.0`).

## Must never

- Treat a URL, an absolute path, or a home path as a reference.
- Read the file system.

## Done when (each backed by a test in `tests/test_tokens.py`)

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
