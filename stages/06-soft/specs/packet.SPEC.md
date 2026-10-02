# packet.py: spec

Builds the review packet: the labeling and relational questions over the stage
1 to 5 reports, each with its state, and renders it as readable markdown. It
reads the input only to take line text; it asks no model.

## Inputs

- `reports`: `{"01": ..., "04": ..., "05": ...}` contract-1 reports.
- `input_dir`: the folder under review (read-only).
- `data`: `softdata.load()`.
- `pattern_notes`: `{pattern_id: plain description}` from
  `load_pattern_notes(path)`, which reads stage 4's `patterns.yaml` as data
  (never imports stage 4) and turns each row's `source` into one plain line by
  dropping the leading citation token (`PHRASES:<set>`, `THREATS:<class>`, and a
  following `ext`).

## Lines

`build(reports, input_dir, data, pattern_notes)` returns the label questions then the relational ones.

`Lines(input_dir, reports["01"])` reads a file's lines once: bytes decoded with
the encoding stage 1 recorded for it (`inv.file` `encoding`; utf-8 when absent or
unknown; a BOM is dropped; undecodable bytes replaced), split on line breaks.
`text(file, line)` is the original line; `around(file, line, 2)` gives up to two
lines before and after. A path outside `input_dir` or unreadable gives `None` /
empty lists. When the file line differs from stage 4's `quote`, the quote is
used as `text` (the stage 4 text is what the finding stands on).

## Questions

Every question: `qid`, `kind` (`label` or `relational`), `file`, `line`,
`question` (text from `data`), `state` (a JSON-able dict: the untrusted text as
data), `sources` (list of `{stage, check, file, line}` plus `patterns` where the
stage finding has them), and for relational questions `template` (the data key).

### Labeling (`label_questions`)

One per `(file, line)` with at least one stage 4 finding whose check starts with
`phrase.` and whose `audience` is `model` or `subagent`. Several hits on a line
make one question listing them all. Part 2 rows (`rubric.action`,
`endpoint.host`, `cond.branch`, `term.*`) are never labeling questions.
`qid` = `label:<file>:<line>`. State: `file`, `line`, `text`, `before`,
`after`, `matched`: list of `{check, pattern, locates}` (one per pattern id of
each hit; `locates` from `pattern_notes`, or the check name when the id is
unknown). Ordered by file then line.

### Relational (`relational_questions`)

In this order, one per source row:

| Template | From | `file`, `line` | State |
|---|---|---|---|
| `term.safety` | each stage 4 `term.safety` | the finding's | `term`, `quote`, `definition` (from a `term.def` on the same line, else null), `before`, `after` |
| `term.conflict` | each stage 4 `term.conflict` | its first definition's | `term`, `definitions` (each `{file, line, text}`) |
| `rubric.action` | each stage 4 `rubric.action` with `confirm_redefined` true, or `tier` `prohibited` and `confirmation` false | the finding's | `action`, `tier`, `quote`, `confirmation`, `confirm_redefined`, `confirm_line`, `confirm_quote`, `before`, `after` |
| `hook+phrase` | each stage 5 `cap.pair` with `pair` `hook+phrase` | the finding's | `quote`, `phrase_check`, `matched` (as for labeling), `evidence` |
| `legs` | stage 5 `cap.leg`, one question per run | null, null | `legs`: each `{leg, present, evidence}`, evidence items `{file, line, why, text}` (`text` the line, when it can be read) |

`qid` = `rel:<template>:<file>:<line>` (`rel:legs` for the legs question).

### Rendering

`render_md(questions, meta, data)` returns `06-packet.md`: a header (input, date,
counts by kind, the backends named in `meta`, and a line that the packet can be
taken to any assistant and that the quoted text is data), then every question
with its qid, location, question, the labeling options (from `data`, for label questions,
once, at the top), and its state as a fenced JSON block.

## The marked state (added 2026-10-01, soft D4)

Each label question also carries `state_marked`, used only by Jev's second read under
`--both`. It equals `state` except: each `matched` entry whose pattern has a stage 4
`matches` text gains `words`, and `marked` is `mark_window(text, words)`: every matched
phrase wrapped in «…» (case-insensitive, overlapping spans merged), cut to about
`WINDOW` (100) characters each side, with "…" where cut; with no phrase found, the first
2 x WINDOW characters. `state` itself is unchanged, so the single read is the one
measured in soft/EVAL.md.

## Must never

- Put whole files, tool definitions, or anything but question and state in a
  question.
- Write anywhere, or run or import anything from the input or another stage.
- Carry a verdict, score, or severity field.

## Done when (each backed by a test in `tests/test_packet.py`)

1. Two `phrase.*` hits on one model-audience line make one label question listing
   both, with `before` / `after` up to two lines and `text` the original line;
   a `human`-audience hit makes no question; `term.def`, `cond.branch`,
   `rubric.action`, and `endpoint.host` rows make no label question.
2. `matched` carries `locates` from the pattern notes; `load_pattern_notes` strips
   the citation token.
3. `term.safety`, `term.conflict` (anchored at its first definition),
   `rubric.action` (only the confirm_redefined or unconfirmed prohibited rows),
   `hook+phrase` pairs (not other pairs), and one `legs` question (file and line
   null) come out in that order with their template text.
4. A file decoded with a stage 1 encoding of `utf-16` reads correctly; a BOM is
   dropped; a quote that differs from the file line wins.
5. `render_md` contains every qid, the four option names, and each state as JSON.
6. No question carries a field named risk, severity, score, or verdict.
