# _shared: code more than one step needs

Not a stage. It is not listed in `stages/stages.json`, has no report of its own, and is not graded. One
module (`runner.py`) is run; the rest are imported.

## Inputs

- What a caller gives: a target and options (`runner.py`), a stage name, a path, a report.
- It reads: `stages/stages.json` (`stagelist.py`); `Library/` (`library.py`, and through it `softdata.py`
  and `rates.py`); the audited folder, only to read (`readtext.py`, `linetext.py`); a run folder's `data/`
  (`record.py`, `layout.py`, `upstream.py`); the grader's results (`validate.py` runs
  `tools/grader/grader.py <step> --json`).

## Process

Each module does one thing for several steps, so it has one home:

- Library and stages: `library.py` (where the Library is and how to read it), `stagelist.py` (the stage
  list and every table keyed by a stage name), `options.py` (the options of a run, declared once, and `--reads` resolved into
  `--sweep` and `--pinpoint`),
  `softdata.py` (what the AI stages show a model).
- Reading the repository: `readtext.py` (bytes to lines, the one place the coded steps open a file under
  audit), `linetext.py` (the one place the AI stages do), `audience.py` (who a line is addressed to, and
  the test-data rule), `secretmask.py` (a report never repeats a secret it found, and a model read never sends one).
- Asking a model: `textmodel.py` (the calls every model backend makes alike: the first call alone, the one extra try,
  the stop on a rejected key, the workers, `not sent`, the tokens, a progress line; and the contract of a model that
  takes text), `back_claude.py` (the Claude Code command as such a model), `jevkey.py` (Jev's key, and whether Jev is available), `calllog.py` (the second try and the call
  log), `usage.py` (token totals), `probability.py` (how sure a model was, when it says), `stagenote.py` (a note, a
  progress line, a value from a service on one line).
- Running: `runner.py` (a target to a run folder: intake, the steps, the validation, the record, then the
  report stage; with `--until` it stops after a step, and `continue` goes on in the same run folder),
  `pipeline.py` (the steps as subprocesses), `earlier_steps.py` (the steps a step reads, run
  for it when it runs alone), `upstream.py` (a saved earlier report checked against the contract),
  `toolversion.py` (the Walkdown version and commit, as the pages and the record name it).
- The run folder: `layout.py` (where things live), `record.py` (`data/run.json` and the rule for the
  previous run), `validate.py` (the grader's results as validation stamps, cached in `.cache/stamps.json`).
- For the report: `rates.py` (base rates), `termdiff.py` (what changed between two runs' `terms`
  blocks).

Never: import a stage's code (`runner.py` and `earlier_steps.py` start stages as subprocesses); hold data
(it goes in `Library/`); open a file of the audited repository anywhere but `readtext.read_row` and
`linetext.Lines`, and only to read.

## Outputs

- No report. `runner.py` makes the run folder `RepoResults/<repo>/<date>_<hash7>/` with each step's
  `data/<step>.json` and `data/<step>.notes.txt` (`pipeline.py`) and `data/run.json` (`record.py`), and
  prints the folder's path.
- `validate.py` keeps its cache in `.cache/stamps.json`. The other modules write nothing.

## The human check

A module here changes no finding by itself, so a person trusts it through the steps that use it: each
step's fixtures and grader stamp (`LOG.md`) fail if a shared rule moves a finding. Its own tests are in
`stages/_shared/tests/` (`python -m pytest stages/_shared`), written from its spec.

## Spec

`specs/shared.SPEC.md`: one section per module, in alphabetical order (`audience`, `back_claude`, `calllog`,
`common_lines`, `coverlines`, `earlier_steps`, `jevkey`, `layout`, `library`, `limitnote`, `linetext`, `options`, `packages`,
`pipeline`, `probability`, `rates`, `readtext`, `record`, `runner`, `secretmask`, `softdata`, `stagelist`,
`stagenote`, `steperror`, `termdiff`, `textmodel`, `toolversion`, `upstream`, `usage`, `validate`).
