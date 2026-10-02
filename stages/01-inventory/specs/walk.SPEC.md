# walk.py: spec

Lists what ships in an input folder and pins it. Stage 1, check `inv.pin`.

## Inputs

- `input_dir`: a folder (pinned repo copy or fixture folder). Read-only.

## Outputs

`walk(input_dir) -> Walk` with:

- `root`: the resolved input folder.
- `entries`: one `Entry` per shipped path, sorted by `rel`:
  - `rel`: path relative to `root`, forward slashes.
  - `kind`: `file` or `symlink`.
  - `target`: the link target string for a symlink, else None.
  - `exec_bit`: bool, or None when unknown.
  - `exec_source`: `git-index`, `stat`, or `stat-windows`.
- `hash`, `hash_kind` (`git` or `sha256`).
- `channel`: `git` or `directory`.
- `untracked`: in git mode, the number of files present in the work tree but
  not tracked (not inventoried). 0 in directory mode.
- `notes`: list of strings for stderr.

`pin_finding(walk, files, bytes_total) -> dict`: the `inv.pin` finding
(`check`, `file`: null, `line`: null, `source`, `hash`, `hash_kind`, `files`,
`bytes`, plus `channel` and `untracked`).

## Rules

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

## Must never

- Follow a symlink or junction, or read anything outside `input_dir`.
- Write inside `input_dir`.
- Run a git command that can execute repository-configured programs.

## Done when (each backed by a test in `tests/test_walk.py`)

1. A plain folder lists every file, sorted, with forward-slash paths, and pins
   with `hash_kind` `sha256`.
2. The sha256 pin changes when a file's content or name changes and is stable
   otherwise.
3. A folder inside a git repository, but not its top level, is directory mode.
4. A git top level lists only tracked files, pins HEAD, and counts untracked files.
5. A symlink is listed as `symlink` with its target and is not followed (skipped
   where the platform cannot create symlinks).
6. `pin_finding` carries every contract field.
