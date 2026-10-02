# ask.py: spec

Turns the packet and the backend results into contract findings
(`stages/CONTRACT.md` stage 6) and summary lines. It calls no backend itself.

## Inputs

- `questions`: from `packet`.
- `primary`, `compare`: label results (`back_jev` / `back_laya` shape) or `None`
  when that role has no backend.
- `reads`: relational results (`back_claude` shape) or `None`.

## Outputs

`findings(questions, primary, compare, reads)` returns, in this order:

1. `soft.question` per question: `file`, `line`, `kind`, `qid`, `question`,
   `sources`.
2. `soft.label` per label question: from `primary` (`qid`, `backend`, `model`,
   `label`, `probabilities`, `confidence`, `truncated`); a skip with the result's
   reason; or, when `primary` is `None`, a skip `no labeling backend`.
3. `soft.compare` per label question, only when `compare` is not `None`: same
   fields, or a skip with the reason.
4. `soft.agree` per label question answered by both: `qid`, `primary`, `compare`
   (the two labels), `agree` bool.
5. `soft.read` per relational question: `qid`, `backend`, `model`, `answer`,
   `capped`; a skip with the reason; or `no relational backend` when `reads` is
   `None`.

Every finding carries the question's `file` and `line` (null for the legs
question). A question with no result in a list is a skip `no answer returned`.

`summary(questions, findings)` returns stderr lines: question counts by kind;
per role, labels by option and by phrase check (from the question's sources);
skips by reason; the agreement rate (`agree n of m`).

`record(role, result)` returns one `answers.jsonl` row: `role`, `qid`,
`backend`, `model`, `request`, `response`, and `skipped` when skipped.

## Sweep findings (added 2026-10-01, soft D2)

`sweep_findings(chunks, results, s4_findings)`: one `soft.sweep` per passage with `file`,
`line`, `end_line`, `qid`, `backend`, `model`, `kind`, `probabilities`, `p_any`, `flagged`,
`covered` (chunks.covered); a skipped or missing answer gives a skip finding with the
reason. `results` None: no findings. The summary adds "sweep (jev): N chunks, F flagged,
U of them with no stage 4 hit".

## Must never

- Change, drop, or add a stage 1 to 5 finding.
- Produce a verdict, score, severity, or risk field.

## Done when (each backed by a test in `tests/test_ask.py`)

1. With no backends, every label question has a `soft.label` skip `no labeling
   backend` at its file and line, every relational question a `soft.read` skip
   `no relational backend`, and no `soft.compare` or `soft.agree`.
2. With both label roles answered, `soft.label`, `soft.compare`, and `soft.agree`
   come out per question with `agree` true only when the labels match; a skipped
   compare result gives a `soft.compare` skip and no `soft.agree`.
3. A relational answer becomes `soft.read` with the answer verbatim.
4. `summary` reports counts by label and the agreement `n of m`.
5. No finding has a field named risk, severity, score, or verdict.
