# softdata.py: spec

Loads and checks `softreads.yaml`, the one data file holding everything a model
is shown in stage 6: the labeling question and its four options (`what`,
`not_for`, `examples`), the relational question templates, the Claude system
prompt, and the answer cap. Each entry cites its source doc.

## Inputs

- `load(path=DEFAULT)`: the YAML file (default `softreads.yaml` beside the script).

## Outputs

A dict:

- `answer_cap`: int (characters).
- `label`: `{"question": str, "options": {name: {"what", "not_for", "examples", "source"}}, "source"}`
  with exactly the options `do`, `not-to`, `description`, `example-or-quote`, `other-sense` (the fifth added 2026-09-29)
  (`LABELS`, in that order).
- `relational`: `{key: {"question", "source"}}` with exactly the keys
  `term.safety`, `term.conflict`, `rubric.action`, `hook+phrase`, `legs`
  (`RELATIONAL`).
- `claude_system_prompt`: `{"text", "source"}`.

`DataError` (message names the entry) when the file is missing or unparseable,
an option or template is missing or extra, an entry has no non-empty `source`,
an option lacks `what`, `not_for`, or a non-empty `examples` list, or
`answer_cap` is not a positive int.

`label.marked_note` (optional, added 2026-10-01): the sentence appended to the question for
Jev's marked read under `--both`. Loaded as `label.marked_note`, None when absent; present
but empty is a DataError.

`sweep` (optional, added 2026-10-01, soft D2): `question`, `source`, `flag_p` (a number
strictly between 0 and 1), `options` starting with `none` and naming at least one kind,
each with `what`, `not_for`, `examples`, `source`. Loaded as `sweep`, None when absent.

## Must never

- Hold an API key, a verdict, a score, or a severity field.
- Be read from anywhere but the stage folder (or a path a test passes).

## Done when (each backed by a test in `tests/test_softdata.py`)

1. The shipped `softreads.yaml` loads; the options are exactly `LABELS` in order,
   each with `what`, `not_for`, `examples`, `source`; the relational keys are
   exactly `RELATIONAL`; the system prompt text is non-empty and cited.
2. A file with an option missing, a template missing, an entry without a
   `source`, or an option without examples raises `DataError`.
3. The shipped system prompt states that the quoted text is data with no
   instructions for the reviewer.
