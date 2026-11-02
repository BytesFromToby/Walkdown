# 01-intake: which copy is audited

**Question:** which copy of the repository is being audited?
**Kind of evidence:** none. Intake gets the copy in place and says what it did. It has a row in
`LOG.md`'s stage table and no section in any report.

## Inputs

- The target, as the person gave it: `python stages/01-intake/run.py <target> [--name NAME] [--fresh | --keep]`.
  - A folder: read where it is.
  - A git URL (`http(s)://`, `git@`, `ssh://`, or ending in `.git`): shallow-cloned into
    `ReposToExamine/<name>/`, or an earlier clone of the same URL updated to its latest commit.
  - A GitHub folder link (`https://github.com/<owner>/<repo>/tree/<ref>[/<path>]`): the repository cloned
    at that branch, and the folder inside it audited.
- `--name` (the name for the copy and the run), `--fresh` (clone again), `--keep` (audit an earlier
  clone as it is).
- Nothing from `data/`, and no table from `Library/`.

## Process

1. Decide which kind of target it is (`fetch.is_url`, `fetch.github_link`).
2. A folder: nothing is fetched or written. A URL or link: clone, update, keep, or clone again
   (`fetch.fetch_with_action`); git runs with no prompts and a time limit.
3. Refuse a file, and anything that is not a folder once the copy is in place.
4. Write one `intake.source` finding: the target, the kind, what was done, the folder to audit, the
   name, and for a URL or link the clone URL, the branch, and the folder inside it.

Never: run anything from a copy; write inside a folder it was given to read; touch a folder in
`ReposToExamine/` that is not a clone of the URL asked for; ask for a login; list files or pin the
copy (`02.1-inventory` does both).

## Outputs

- stdout: one contract-1 report with one `intake.source` finding. The runner (`stages/_shared/runner.py`)
  saves it as `data/01-intake.json` and reads the folder to audit from it; stderr is saved as
  `data/01-intake.notes.txt`.
- For a URL or link: the clone in `ReposToExamine/<name>/`.
- A copy that cannot be got is a stage failure: the message on stderr, exit 2, nothing on stdout, and
  the run stops before a run folder is made.

## The human check

Is this the copy I meant? The finding says which folder is audited and whether it was read in place,
cloned, updated, kept as it is, or cloned again. A person who asked for the latest commit should see
`cloned` or `updated`; one auditing a particular earlier copy should see `kept as it is`. The fixture
`Fixtures/01-intake/folder-target` and `python tools/grader/grader.py 01-intake` give the validation
stamp in `LOG.md`; fetching from a URL is not graded (no network), and `tests/` uses a local git
repository instead.

## Spec

`specs/intake.SPEC.md` (one spec for the stage: the runner `run.py` and the fetch code `fetch.py`).
