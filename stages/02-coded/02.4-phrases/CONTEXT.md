# 02.4-phrases: what the text asks for

**Question:** what does the text ask for?
**Kind of evidence:** pattern hits on the folded text, one finding per line per check, each quoting the
original line verbatim. Every hit is a locator, never a verdict.
**Plain name:** What the text asks for (its heading in `full.md`).

## Inputs

- `<input_dir>`: the folder audited, read-only.
  `python stages/02-coded/02.4-phrases/run.py <input_dir> [--inventory <file>] [--normalized <dir>] [--out <dir>]`
- `data/02.1-inventory.json` (`--inventory`; `reads` in `stages/stages.json` is `02.1-inventory`): which
  files, which encoding, which are scripts and hook configs. Without it, `earlier_steps.py` runs 02.1 first.
- `data/normalized/text/<path>.txt` (`--normalized data/normalized`, written by `02.2-reader`): the text of
  files that do not decode as text (PDF, DOCX, images). Optional; without it those files are not scanned,
  and stderr says so.
- `Library/patterns.yaml` (the pattern table), `Library/vocab.yaml` (the word lists), `Library/invisible.yaml`.

## Process

1. Fold each line (NFKC, invisible characters stripped, confusables to ASCII; the line count never changes).
2. Match the pattern table (`scan.py`): one finding per line per check, naming the patterns, the audience of
   the file (human, subagent, tool, model), and whether the hit needed the fold. Checks: the 14 `phrase.*`
   checks, `pos.density`, `rep.sentence` (`position.py`), `secret.found` (`secret_scan.py`), `limit.setting`
   (`restrictions.py`).
3. Part 2: `rubric.action` (a prohibited or confirm-first action, and whether its step asks first),
   `endpoint.host` (every host named, documented or not), `term.def`, `term.conflict`, `term.safety`.

Never: say whether a hit is a problem, score it, or rank it; drop a benign-looking hit (the benign count is
part of the product); tune a pattern to one fixture sentence; fetch or look up a host; run anything from the
input; write inside `<input_dir>`; import another step's code; grep the raw text only.

## Outputs

- stdout: one contract-1 report; the runner saves it as `data/02.4-phrases.json`, and stderr as
  `data/02.4-phrases.notes.txt`.
- With `--out <dir>` (the runner gives `data/`): `data/hits.json`, every finding with per-check and
  per-pattern counts. A secret's value is never shown: the quote on its line is masked.

## The human check

Every pattern fires in clean repositories too, so a person reads a hit as a place to look. The fixtures
`Fixtures/02.4-phrases/` (one file per threat class, with must-hit gate rows, must-not negative rows, and
measured recall rows) and `python tools/grader/grader.py 02.4-phrases` give the validation stamp in
`LOG.md`: every gate caught and no negative hit; recall is reported, never tuned to. The base rate of each
pattern over audited repositories is in `Library/baserates.json`. To add, narrow, or retire a term, follow
`Library/README.md`.

## Spec

`specs/phrases.SPEC.md`: "The stage" (what is scanned, the pattern table, the checks, the findings, and
part 2: the rubric, the endpoint census, the term table), then one section per script, `run` first and the
others in alphabetical order.
