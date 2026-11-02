# intake: spec

The first stage (restructure step 2, 2026-10-28). It takes the target the person gave and makes
sure the folder to audit exists: a folder is read where it is, a git URL is cloned or an earlier
clone updated, a GitHub folder link clones the repository at its branch and names the folder inside
it. "Pulls the skill and puts it in place" (owner).

Scripts: `run.py` (the runner), `fetch.py` (the fetch code, moved from `walkdown.py`).
One spec for the stage.

Status: built.

## Inputs

```
python stages/01-intake/run.py <target> [--name NAME] [--fresh | --keep]
```

- `target`: a folder; or a git URL (`http(s)://`, `git@`, `ssh://`, or ending in `.git`, unless a
  folder by that name exists: `fetch.is_url`); or a GitHub folder link
  `https://github.com/<owner>/<repo>/tree/<ref>[/<path>]` (`fetch.github_link`: the first part
  after `/tree/` is the branch or tag, the rest the folder; a `/blob/` link is an error that says
  to give the folder holding the file, and a folder path with a `..` part, plain or escaped, is an
  error before anything is cloned, so the folder audited is always inside the clone).
- `--name`: the name for the copy and the run. Default: the last part of the URL or path without
  `.git`, reduced to letters, digits, `.`, `_`, `-` (`fetch.repo_name`); for a GitHub folder link
  the last part of its folder (or the repository's, with no folder). `--name` names the clone too.
- `--fresh`: delete an earlier clone of the URL and clone again.
- `--keep`: audit an earlier clone as it is, without updating it. It wins over `--fresh`.

## Behavior

- **Folder.** Read where it is; nothing is fetched or written.
- **URL.** A shallow clone (`git clone --depth 1 -- <url>`) into `ReposToExamine/<name>/`. An
  existing clone of the same URL (its `origin`, compared without `.git` or a trailing slash,
  case-insensitive) is updated to the remote's latest commit (`fetch --depth 1`, `reset --hard
  FETCH_HEAD`, `clean -fdx`). `--keep` audits it as it is. `--fresh` deletes the clone (git's
  read-only object files too, which Windows would refuse to delete) and clones again. A folder there that is not a clone of this URL is an error (and `--fresh` does not change
  that), unless `--keep`.
- **GitHub folder link.** The repository is cloned into `ReposToExamine/<repo>/` (or `--name`),
  with `--branch <ref>`, and updated with `fetch --depth 1 origin <ref>`. The folder inside it must
  exist at that ref.
- Every git command runs with no prompts (`GIT_TERMINAL_PROMPT=0`, `GCM_INTERACTIVE=never`, and ssh
  in batch mode unless `GIT_SSH_COMMAND` is set), long paths on (`-c core.longpaths=true`), and a
  10-minute limit. A repository that is missing or needs a login fails at once and says so in plain
  words; so does a branch that is not there, and git not being installed.
- After the copy is in place, the folder to audit is checked: a file is refused (`<target> is a
  file; Walkdown audits a folder: give the folder that holds it`), and anything that is not a
  folder is refused (`not a folder or a git URL: <target>`).

The messages are the ones the front door gave before this stage existed (`walkdown.py` held this
code until step 2); notes go to stderr:

- `note: --keep: auditing the existing copy in <folder> as it is`
- `note: updated the existing clone in <folder> to the latest commit`

## Outputs

stdout: one contract-1 report (`stages/CONTRACT.md`), UTF-8:

```json
{"stage": "01-intake", "contract": 1, "findings": [{"check": "intake.source", ...}]}
```

Exactly one finding, `intake.source`, with `file` and `line` null and:

| Field | Meaning |
|---|---|
| `target` | the target as the person gave it |
| `kind` | `folder`, `url`, or `github-folder` |
| `action` | `read in place` (a folder), `cloned`, `updated`, `kept as it is`, or `cloned again` |
| `folder` | the folder to audit: absolute, forward slashes (for a GitHub folder link, the folder inside the clone) |
| `name` | the name for `RepoResults/` (the run); `--name` when given |
| `url` | the clone URL: the target for a URL, the repository's URL for a GitHub folder link, null for a folder |
| `ref` | the branch or tag a GitHub folder link asked for, else null |
| `subfolder` | the folder inside the repository for a GitHub folder link, else null (null too for a `/tree/<ref>` link with no folder) |

Exit 0 with the report. A copy that cannot be got (a login needed, a clone that fails, a folder
that is not a clone of the URL, git not installed, a missing folder inside a GitHub link) or a
target that is not a folder is a stage failure: `error: <message>` on stderr, nothing on stdout,
exit 2.

## Who calls it

- The orchestrator (`stages/06-report/run.py`) runs it first, before the run folder exists, in a
  scratch folder. It reads `folder` and `name` from the finding, names the run for `--repo` when
  given and else `name`, and then saves the two files as `data/01-intake.json` and
  `data/01-intake.notes.txt`, byte for byte. It repeats the notes (or the error) on its own
  stderr so a person sees what they saw before. Every stage after intake is run on `folder`.
- `walkdown.py` passes the target, `--name`, `--fresh`, and `--keep` through; it holds no fetch code.
- The grader runs it on `Fixtures/01-intake/folder-target/`. Fetching from a URL is not graded
  (no network); `tests/` uses a local git repository (a `file://` URL) instead.

Intake appears in `LOG.md`'s stage table (its row and its validation stamp) and in no report: no
section in `full.md`, the pages, or `data/limits.md`.

## Must never

- Run anything from a copy it fetched (nothing from a clone is ever run; git's own hooks are not
  copied by a clone).
- Write inside a folder it was given to read.
- Touch a folder in `ReposToExamine/` that is not a clone of the URL asked for.
- List files or pin the copy: `02.1-inventory` does (its `inv.pin` and `inv.file` findings), on
  the folder named here.

## Done when (tests in `tests/`)

1. A folder gives one `intake.source` finding with every field above, `action` `read in place`,
   and the folder untouched (`test_a_folder_is_read_where_it_is`); a relative path is named in full
   (`test_a_folder_given_a_relative_way_is_named_in_full`); `--name` names the run
   (`test_name_option_names_the_run`).
2. A URL is cloned, then updated to the latest commit, kept as it is under `--keep`, and cloned
   again under `--fresh`, read-only files included, each with its `action` (`test_a_url_is_cloned_updated_kept_and_cloned_again`;
   `test_clone_update_keep_and_fresh_from_a_local_repository`), and a branch is cloned and updated
   by name (`test_a_branch_is_cloned_and_updated_by_name`).
3. A GitHub folder link gives `kind` `github-folder` with the repository's URL, the branch, and the
   folder inside it, and names the run for that folder (`test_a_github_folder_link_names_the_branch_and_the_folder`);
   a missing folder and a file link are errors (`test_a_github_link_to_a_missing_folder_or_a_file_fails`);
   a folder path with `..` in it is refused (`test_a_folder_link_with_dot_dot_is_refused`).
4. A file, a path that is not a folder, a failed clone, a folder that is not a clone of the URL, and
   no git are failures with their messages and exit 2 (`test_a_file_is_refused_with_the_message`,
   `test_not_a_folder_or_url_is_refused_with_the_message`, `test_a_failed_copy_is_a_failure_with_the_message`).
5. A folder that is not a clone of the URL is never touched (`test_existing_folder_that_is_not_the_clone_is_never_touched`);
   git runs with no prompts, long paths, and a time limit (`test_git_never_prompts_and_says_why_a_clone_failed`).
6. `python tools/grader/grader.py 01` grades PASS.

## History

- 2026-10-28: built (restructure step 2). The fetch code moved from `walkdown.py` unchanged in
  behavior and messages; the earlier proposal to list the files and pin the copy here (notes I1) was
  revised to fetching only, so `02.1-inventory` keeps the pin and the file list.
- Found while moving it, left as it was (a pure move changes no behavior): `--fresh` on a real clone
  failed on Windows, because git leaves its object files read-only and `shutil.rmtree` cannot delete
  them. The tests unlocked the clone first.
- 2026-10-29 (after the restructure): `--fresh` clears a read-only file's bit and deletes it
  (restructure notes M8), and the tests' unlock step is gone; a GitHub folder link whose folder path
  holds `..` is refused before anything is cloned (restructure notes M9).
