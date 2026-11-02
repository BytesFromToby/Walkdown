# tools/

The factory's tools. They are unnumbered and are not steps: nothing here is a stage, and a run
does not call them (the validation step of a run calls the grader, as a program). Q13 in
`pre-planning/RESTRUCTURE-NOTES.md` put them in one folder:

- `compare_runs.py` compares two run folders (the baseline and a run made after a restructure step);
  its spec is `specs/compare_runs.SPEC.md` and its tests are in `tests/`.
- `grader/` runs a stage on its fixtures and scores it against the answer sheet (`grader.py`, its
  `SPEC.md`, and its `tests/`). The validation fingerprint keys on this folder.
- `baserates.py` measures how often each `02.4-phrases` pattern hits in the audited repositories and writes
  `Library/baserates.json`; its spec is `specs/baserates.SPEC.md`, its tests `tests/test_baserates.py`.
- `fixture-generators/` holds the scripts that rebuild the binary fixtures, and `make_qa_runs.py`, which writes the
  small run folders of `Fixtures/05-qa/` and their answer rows (dev-only; they write into `Fixtures/`).
- `model-eval/` is model evaluation.

## Filing the runs for a comparison

Every file in a run folder counts, so a run folder is left exactly as the run made it.

- File a comparison run as `cmp-<name>` (`python walkdown.py <input> --name cmp-<name>`), never
  under the input folder's own name. The tool replaces the name a run is filed under, and the input
  folder carries the same name in its path, so filing a run under that name also masks the input
  path and gives false differences.
- Save nothing else into a `base-*` baseline folder (`marks.json`, `Thumbs.db`, a note). It would be
  a file in one run only, which is a difference.
