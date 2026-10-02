# walkdown.py (added 2026-10-02)

The front door: one command from a folder or a git URL to a finished run and a brief.

## Inputs

`python walkdown.py <target> [--name NAME] [--fresh] [--label B] [--compare B]
[--relational B] [--sweep B] [--both]`

- `target`: a folder, or a git URL (`http(s)://`, `git@`, `ssh://`, or ending in `.git`,
  unless a folder by that name exists).
- `--name`: the run folder name; default the URL's or folder's last part without `.git`,
  reduced to letters, digits, `.`, `_`, `-`.
- Stage 6 flags pass through to `stages/08-report/run.py` unchanged.

## Outputs

- A URL is cloned shallow (`git clone --depth 1 -- <url>`) into `ReposToExamine/<name>`. An
  existing copy is reused with a note, unless `--fresh` removes and re-clones it.
- Runs `stages/08-report/run.py <target> --repo <name> ...` with the project virtualenv's
  python when `.venv/` exists, else the current interpreter.
- Prints the **brief** to stdout: files examined and the pin; the three trifecta legs as
  checkboxes and the install grants; the "look at these first" items counted by stage and
  headline; each stage's validation stamp from LOG.md; the paths of `summary.html` and
  `full.md`; the no-verdict line.
- Exit code: the stage 8 runner's; 2 for a bad target or a failed clone.

## Must never

- Put text from the audited repository in the brief: no quote, file name, path inside the
  repository, or defined word. Headlines are Walkdown's own; the two that embed a defined word
  are replaced by fixed wording. The brief is what a chat assistant holding tools may read.
- Run anything from the cloned repository.
- Delete anything except a clone in `ReposToExamine/<name>` under `--fresh`.

## Done when (each backed by a test in `tests/test_walkdown.py`)

1. URLs and folders are told apart, and names derived, as above.
2. Validation stamps are read from LOG.md's table.
3. The brief carries legs, grants, counted headlines, stamps, and report paths.
4. No text planted in the audited repository's findings appears in the brief.
