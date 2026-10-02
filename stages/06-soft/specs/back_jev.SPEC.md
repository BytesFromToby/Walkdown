# back_jev.py: spec

The Jev labeling backend (TypeSafe, remote API). Asks each labeling question as
one Choice over the four options and returns one result per question. Usage from
`stages/06-soft/CONTEXT.md` "Backends" and the installed `typesafe_sdk` 0.7.2
types (`ChoiceAnswer`: `choice`, `probabilities`, `confidence`;
`SystemOneResponse`: `model`, `usage.input_tokens`, `answers`).

## Inputs

- `Jev(data, client_factory=None, key_reader=read_key, workers=8)`.
  `client_factory(key)` returns an object with
  `system_one(state=..., questions=..., model=...)`; the default imports
  `typesafe_sdk` and builds `TypeSafeClient(api_key=key)`.
- `read_key(environ=os.environ, registry=None)`: `TYPESAFE_API_KEY` from
  `environ`, else from `HKCU\Environment` read in-process with `winreg`
  (`registry` is a callable standing in for the registry read in tests). `None`
  when neither has it.
- `label(questions)`: label questions from `packet`.

## The request

One call per question: `state` = the question's state; `questions` =
`{"label": {"type": "choice", "instructions": <question>, "criteria": {option:
{"what", "not_for", "examples"}}}}` (the rich criteria, as FINDINGS §6 says Jev
needs); `model` = `jev-latest`.

## Outputs

`label` returns one dict per question, in question order:

- answered: `qid`, `backend` `jev`, `model` (the response's), `label`,
  `probabilities` (dict, option to float), `confidence`, `truncated` false,
  `request` (the state and questions sent, never the key), `response` (`model`,
  `usage`, and the answer as plain data).
- skipped: `qid`, `backend`, `skipped`: `jev: no key`, `jev: typesafe_sdk not
  installed`, `jev: authentication failed`, or `jev: <ErrorType>: <message>`;
  with `request` when one was built.

`tokens`: input tokens summed over the calls that reported them.

An authentication or permission error stops further calls; the rest are skipped
with the same reason. An answer whose `choice` is not one of the four options is
a skip (`jev: unexpected label`).

## Two reads (`both=True`, added 2026-10-01, soft D4)

- Each question is read twice: once with `state` and the plain question (exactly the
  single read), once with `state_marked` and the question followed by
  `label.marked_note`. Two `system_one` calls per line.
- `combine(plain, marked)`: `probabilities` is the per-label average of the two reads;
  `label` is its top (ties go to the plain read's label); `confidence` is the averaged
  probability of that label; `confidence_kind` is `average of two reads`; `reads` holds
  each read's `label`, `probabilities`, `confidence`. `request` and `response` are lists
  of both.
- If either read is skipped, the line is skipped, its reason naming which read failed.
- `both=True` without `label.marked_note` in the data raises ValueError.

## Sweep (added 2026-10-01, soft D2)

`Jev.sweep(chunks)`: one Choice question per passage, built from softreads.yaml `sweep`
(`sweep_question`), state `{file, line, end_line, text}`. Same key, client, auth-stop and
worker handling as `label` (shared `_batch`). Result: `kind` (the chosen option),
`probabilities`, `p_any` = 1 - p(none), `flagged` = p(none) < `sweep.flag_p` (0.5, fixed
before any fixture). A flagged passage never has kind `none`: when `none` is the single
top answer but the listed kinds outweigh it together, `kind` is the likeliest listed kind.
No sweep section in the data: ValueError.

## Must never

- Print, log, return, or store the key; any error text is scrubbed of it.
- Contact anything but TypeSafe; give the model tools.
- Raise on a backend failure (every failure is a skip).

## Done when (each backed by a test in `tests/test_back_jev.py`)

1. With a stub client, each question gets one call with the choice question and
   the four options carrying `what` / `not_for` / `examples`, `model`
   `jev-latest`; the result has the label, probabilities, confidence, and model;
   `tokens` sums the usage.
2. No key: every question skipped `jev: no key`, and the client factory is never
   called.
3. An authentication error on the first call skips every question with `jev:
   authentication failed` after one call; another error skips only its question.
4. An error message containing the key is recorded with the key replaced.
5. `read_key` prefers the environment, falls back to the registry callable, and
   returns `None` when neither has a value.
