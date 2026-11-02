# 05-qa: the check of the run

**Question:** is everything that should have run there, with the results it should have? It names what is
missing and what the run did not examine. It detects nothing in the repository and judges nothing about it: it
reads the run's files and none of the repository's code.
**Kind of evidence:** counted from the run's own files: the steps' saved outputs, the record, and the call logs.
It gives no verdict and no score about the repository.
**Reports under:** section 7 of `full.md` ("Not examined"), `data/limits.md`, and the lists of steps that did not
work on `summary.html`, `details.html`, and the brief, which the report stage draws from this step's output. The
step has a row in `LOG.md` and a validation stamp. When it finds a gap it holds the run: no report is written
until the person chooses.

## Inputs

- `python stages/05-qa/run.py <run folder> [--brief]`. The runner starts it after the steps, the validation, and the
  record, on every run: a straight run, a run stopped with `--until` (it checks what ran), and `continue`.
- In the run folder's `data/`: `run.json` (the record: each step's result, the validation stamps, the stop, the steps
  not started), each step's `<step>.json` and `<step>.notes.txt`, and a model step's `<step>.calls.jsonl`. A run with
  no record, or a record of another format, is refused: one plain line, exit 2.

## Process

A **gap** is something that should be there and is not (`qa.gap`):

1. a step the run should have run (every coded step, intake, and a model read that was chosen and started, less the steps
   a stop left out) with no output, or that failed;
2. a step that ran and did not pass its fixture check (`FAIL`, and any other word but a pass: its zeros cannot be trusted;
   owner, 2026-10-30), this step's own stamp included;
3. a chosen model read in which no passage got an answer, even after the retry;
4. a check that looked at fewer items than it should have and does not say why (M9 slice C): a step's `coverage` list has no
   line for one of its checks (`stages/stages.json` lists them), or a finding names a check that is not on the list, or a line's
   `looked_at` plus `explained` is below its `of`, or above it, or its `found` is not the results among the findings, or it names
   a check that is not the step's (another step's included) or that another line names too.

A **limit** is something the run did not examine and says so (`qa.limit`): the steps a stop left out, a check skipped for
a missing optional tool (`INCOMPLETE`), a model read with some passages unanswered, a chosen read that was not started, the
skips and messages the steps name, files not read or not scanned, test data set aside, and the limits that stand for every run.
These are not gaps (owner, 2026-10-25, 2026-10-30).

What each check that found nothing looked at is `qa.checked`, apart from the limits (M9 slice C): it is no limit and no gap, and a
step gets it only when its fixture check passed with some rows measured.

With one gap or more the report does not run (`--brief` writes `brief.md`, in Walkdown's own words, with the two ways on);
the runner records the hold and exits 1.

Never: detect, judge, score, or rank; read or quote the audited repository; import another step's code; reach a model or
a network; write anything but `brief.md` of a held run, and that only with `--brief`.

## Outputs

One contract-1 report on stdout (the fields are in `stages/CONTRACT.md`). The runner saves it as `data/05-qa.json`, and
stderr as `data/05-qa.notes.txt`. With `--brief` and a gap it also writes `brief.md` in the run folder.

## The human check

A gap is a place to look and says nothing about the repository's merit: a step that failed names the error's type and the whole
messages are in `data/<step>.notes.txt`. The fixtures `Fixtures/05-qa/` (small synthetic run folders, some held for a
gap and some not held) and `python tools/grader/grader.py 05-qa` show that each kind of gap holds a run and each thing that is not
a gap does not. A step that was held wrongly costs a command (`continue`); a gap that was missed costs a report that looks
whole, so a new kind of gap needs a fixture first.

## Spec

`specs/qa.SPEC.md`: one section per script (`run.py`, `facts.py`, `gather.py`, `hold.py`).
