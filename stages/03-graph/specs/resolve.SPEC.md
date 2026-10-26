# resolve.py: spec

Turns a reference into the nodes it names. Works on the node list only (the
paths stage 1 inventoried); never touches the disk.

## Inputs

`Resolver(nodes)`: every node path, relative, forward slashes. Folders are
every proper prefix of a node path.

## Outputs

`resolve(from_rel, path, shape) -> Result`, where `path` and `shape` come from
`tokens.Ref`. `Result` has `status`, `targets` (sorted node paths),
`ambiguous` (bool), `case_mismatch` (bool), `partial` (bool), `pattern` (for `glob` and `dir`).

`folder_missing(from_rel, path) -> bool`: the folder a path points into exists neither from the
referring file's folder nor from the root (a path with no folder part is never missing one).
Stage 3 marks a dangling reference with it, so a report can tell "into a folder the repository
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
   equal. Several give `ambiguous` true.
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

## Must never

- Read the file system, or resolve outside the node list.
- Compare case-insensitively before every case-sensitive try has failed.

## Done when (each backed by a test in `tests/test_resolve.py`)

1. From `skills/x/SKILL.md`, `references/a.md` resolves to `skills/x/references/a.md` when it exists, else to root `references/a.md`.
2. A bare `helpers.md` found in two folders gives both, `ambiguous` true.
3. `README.MD` with only `README.md` present gives `case_mismatch` true.
4. `extra/` is `dir` with every file under it, recursively; `extra/*.md` is `glob` matching direct children only; `extra/**/*.md` matches nested ones.
5. `../../x.md` from `a/b.md` is `outside`; `../x.md` from `a/b.md` is root `x.md`.
6. An unknown path is `missing`; a glob with no match is `glob` with no targets.
7. `rules/carousel-rules.md` with only `_shared/rules/carousel-rules.md` present resolves to it, `partial` true; `./rules/carousel-rules.md` stays `missing`; two such files give both, `ambiguous` true.
8. `folder_missing`: `output/post.md` with no `output/` folder anywhere is true; `references/gone.md` beside an existing `references/` is false; a bare `gone.md` is false.
9. `my%20skill/SKILL.md` resolves to `my skill/SKILL.md`; a file named `a%20b.md` matches as written; `gone%20x.md` stays `missing` (`test_percent_escapes_are_decoded_when_missing`).
