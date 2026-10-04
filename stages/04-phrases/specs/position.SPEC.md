# position.py (added 2026-10-04)

Instruction position and repetition, REPORTING 4.4 and 4.5. "Instruction-shaped" here means
a line a stage 4 phrase pattern flagged in a file a model or subagent reads (path audience).

## Inputs

`texts`: `{rel: (audience, raw lines, bytes)}` for every scanned file; the stage 4 phrase
findings.

## Outputs

- `density(texts, findings)`: one `pos.density` per model or subagent file over the reader
  window (more than `READER_LINES` 2,000 lines or `READER_BYTES` 50,000 bytes, the published
  thresholds) that has phrase hits: `lines`; `first10`, `middle80`, `last10` (flagged lines in
  the first and last 10% of lines, rounded up, and the rest); `window_line` (the last line
  inside the window by lines or bytes, whichever comes first); `beyond_window` and
  `beyond_lines` (flagged lines after it, at most 20 listed).
- `sentences(lines)`: (line, sentence, normalized key) for sentences of `MIN_WORDS` (6) or
  more words, outside a leading YAML frontmatter block and code fences, with list, heading,
  quote, and table markers stripped; the key is the lowercased words.
- `repetition(texts, findings)`: one `rep.sentence` per sentence whose key appears in two or
  more prose files (`.md`, `.mdc`, `.markdown`, `.txt`) a model or subagent reads: `file` and
  `line` of the first occurrence, `sentence` (at most 240 characters), `files`, `count`,
  `where` (at most 20), `patterns` (stage 4 pattern ids on any occurring line). Sentences that
  repeat at exactly the same places are one finding, their text joined.

## Must never

- Judge: a checklist at the end of a skill and shared boilerplate are normal (REPORTING "Not").
- Count human-facing files, test data, scripts, or configuration lines.

## Done when (each backed by a test)

1. Density only for long model-read files with hits; segments, window line, and lines past it
   (`tests/test_position.py`).
2. The window ends at the byte limit when it comes first (`tests/test_position.py`).
3. Sentences skip frontmatter, fences, and short ones (`tests/test_position.py`).
4. Repetition across prose files with patterns; human, test, and config files never count
   (`tests/test_position.py`; fixture `position-repo` gates and negatives).
