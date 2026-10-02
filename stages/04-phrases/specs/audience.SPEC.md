# audience.py: spec

The audience tag on every stage 4 finding: who a line is addressed to, decided
by the file's path (METHOD "Audience tag", THREATS 19, CONTEXT "Findings"). The
tag describes the file, never the reader's intent.

## Inputs

- `rel`: the file's path relative to the input, forward slashes.
- `scripts`: the set of paths stage 1 counts as scripts (`inv.pin`
  `script_languages`, which covers extensionless files with a `#!` line).
- `hook_configs`: the set of paths stage 1 marks as hook configs (`inv.file`
  `entry_point` `hook-config`, or any file carrying a `struct.hooks` finding).

## Outputs

`audience(rel, scripts=(), hook_configs=()) -> str`, the first rule that holds:

1. `human`: the base name starts with `README`, `INSTALL`, `CONTRIBUTING`,
   `CODE_OF_CONDUCT`, `CHANGELOG`, `CHANGES`, `HISTORY`, `RELEASE-NOTES`,
   `RELEASE_NOTES`, `RELEASES`, `LICENSE`, `LICENCE`, `NOTICE`, `AUTHORS`, or
   `SECURITY` (any case; the second group added 2026-09-29), or any folder in the path is `docs` or
   `.github`.
2. `subagent`: any folder in the path is `agents` or `commands`, or the base
   name matches `*prompt*.md` (any case).
3. `tool`: `rel` is in `scripts` or `hook_configs`, or its extension is a script
   extension (`py`, `sh`, `bash`, `zsh`, `js`, `mjs`, `cjs`, `ts`, `ps1`,
   `psm1`, `cmd`, `bat`, `rb`, `pl`).
4. `model`: everything else.

Folders are matched at any depth (`plugin/docs/x.md` is `human`), since
bundles nest plugins.

## Test data (added 2026-10-02)

`is_test_data(rel)`: true when any folder in the path is one of `TEST_DIRS` (test, tests,
__tests__, testdata, test-data, test_data, fixture, fixtures, __fixtures__, __snapshots__,
spec; case-insensitive) or the file name matches `TEST_FILE_GLOBS` (test_*.py, *_test.py,
*_test.go, *.test.*, *.spec.js/ts/mjs/tsx/jsx, conftest.py). `audience` returns `test-data`
for such a path before any other rule. Test-data lines are never instruction lines, frontmatter
included. Stage 5 sets test data aside and pairs any test-data file a model-read file
references (stage 5 `specs/testdata.SPEC.md`).

## Must never

- Read the file, or judge who the text is really for.

## Done when (each backed by a test in `tests/test_audience.py`)

1. `README.md`, `docs/setup.md`, `.github/ISSUE_TEMPLATE/bug.md`, `CONTRIBUTING.md`, `INSTALL.txt` are `human`.
2. `agents/reviewer.md`, `commands/go.md`, `skills/x/implementer-prompt.md` are `subagent`.
3. `hooks/session-start` given in `scripts`, `hooks/hooks.json` given in `hook_configs`, and `tools/a.py` are `tool`.
4. `skills/x/SKILL.md` and `notes.md` are `model`.
5. Rule order holds: `docs/agents/x.md` is `human`; `agents/run.py` is `subagent`.
6. `CHANGELOG.md`, `RELEASE-NOTES.md`, `HISTORY.md`, `LICENSE`, `SECURITY.md` are `human` (2026-09-29).
7. Package, lock, and build configuration files (`BUILD_FILES`, `BUILD_GLOBS`:
   `package.json`, lockfiles, `tsconfig*.json`, `Dockerfile`, ...) are `tool`;
   plugin manifests stay `model` (added 2026-09-29, Case 004).
8. Getting-started guides (`DIRECTIONS`, `USAGE`, `QUICKSTART`, `GETTING_STARTED`,
   `TUTORIAL`, `GUIDE`, `HOWTO`, `FAQ`) are `human`; pattern lists (`.gitignore`,
   `.gitattributes`, other ignore files, `CODEOWNERS`, `.gitmodules`) are `tool`
   (added 2026-09-30, Plumbline).
