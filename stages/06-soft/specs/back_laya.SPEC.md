# back_laya.py: spec

The Laya labeling backend (local, CPU). Asks each labeling question as one choice
over the four options. Usage from `stages/06-soft/CONTEXT.md` "Backends" and the
installed `laya` 0.3.22 (`laya.load(model_id)`; `agent.predict(state,
questions)` returns `answers[qid]` with `choice`, `probabilities`, `confidence`,
and `usage` with `truncated` and `truncated_questions`).

## Inputs

- `Laya(data, loader=None)`. `loader()` returns an agent with `predict`; the
  default imports `laya` and calls `laya.load("convaiinnovations/laya")` (the
  first use downloads the weights). The agent is loaded at most once per
  `Laya` object, on the first `label` call.
- `label(questions)`.

## The request

`predict(state, {"label": {"type": "choice", "instructions": <question>,
"criteria": {option: <what>}}})`. Laya gets each option's `what` text only:
FINDINGS §6 found that negations in an option recruit what they forbid on Laya,
and the 512-token sequence leaves little room for long criteria. This is the one
place the two labelers are shown different option text.

## Outputs

As for `back_jev`: answered results carry `backend` `laya`, `model`
`convaiinnovations/laya`, `label`, `probabilities`, `confidence`, `truncated`
(true when `usage.truncated` is truthy or the question is in
`usage.truncated_questions`), `request`, `response` (the answer and usage).
Skips: `laya: not installed`, `laya: load failed: <ErrorType>: <message>`
(every question), `laya: <ErrorType>: <message>` (one question), `laya:
unexpected label`.

## Must never

- Load the model more than once per run, or at import time.
- Contact anything but the model download on first load; give the model tools.
- Raise on a backend failure.

## Done when (each backed by a test in `tests/test_back_laya.py`)

1. With a stub agent, each question is one `predict` call with the choice and the
   four options' `what` text; the result has label, probabilities, confidence,
   model; the loader runs once across two `label` calls.
2. A usage report with `truncated` true marks the result `truncated`.
3. A loader that raises skips every question with `laya: load failed`; a predict
   that raises skips only its question.
