# 02.5-capability: what this touches

**Question:** what does installing it grant?
**Kind of evidence:** derived, never detected. Every statement cites the findings of the earlier steps
that establish it. It states what the artifact can do, never what it will do.
**Plain name:** What this touches (its heading in `full.md`).

## Inputs

- `<input_dir>`: the folder audited, read-only (file sizes only, for the bytes at load).
  `python stages/02-coded/02.5-capability/run.py <input_dir> [--reports <dir>] [--out <dir>]`
- `--reports <dir>` (the runner gives `data/`), holding the reports named by `reads` in
  `stages/stages.json`: `data/02.1-inventory.json`, `data/02.2-reader.json`, `data/02.3-graph.json`,
  `data/02.4-phrases.json`. Also `data/graph.json` (from `02.3-graph`) when there is one, for the bytes a
  hook adds. Without `--reports`, `earlier_steps.py` runs those steps first; if one fails, so does this one.
- `Library/capability.yaml`: the rule tables (which evidence makes each trifecta leg, which grants count,
  which events inject, how a tool maps to a posture word).

## Process

No new detection. From the earlier reports it states:

1. `cap.leg`: the three trifecta legs ("Can read your data", "Can take outside input", "Can send data out"),
   always three, each `present` true or false with its evidence.
2. `cap.grant`: each install grant present (`exec-at-load`, `context-injection`, `persistence`, `network`,
   `elevated`).
3. `cap.injection` and `cap.load-bytes`: the paths by which text reaches the AI's context at load, and the
   bytes, per host config.
4. `cap.posture`: each agent's or command's tools as a posture (`read`, `write`, `execute`, `network`, ...).
5. `cap.pair`: a phrase hit on an orphan, a load-only file, or hidden text, and the other pairs a person
   should read first. `cap.testdata`: test data set aside. `cap.limit`: a stated read-only limit and what
   backs it.

Never: detect anything (no new pattern, no file read beyond the reports, `graph.json`, and file sizes);
conclude, score, rank, or name a field risk, severity, or verdict (three of three is stated flatly);
leave out an absent leg; run anything from the input or fetch a URL; write inside `<input_dir>`; import
another step's code; count phrase evidence from human-facing files.

## Outputs

- stdout: one contract-1 report, evidence capped at 20 entries per finding with `evidence_total`; the runner
  saves it as `data/02.5-capability.json`, and stderr as `data/02.5-capability.notes.txt`.
- With `--out <dir>` (the runner gives `data/`): `data/capability.json`, every finding with its full evidence.

## The human check

Every finding lists the earlier findings behind it (`evidence`), so a person can follow a leg or a grant back
to a file and line. A leg is a map of what the artifact could do, and the reports never compare one
repository with others. The fixtures `Fixtures/02.5-capability/` (legs, grants, posture, limits, test data,
images, hook injection) and `python tools/grader/grader.py 02.5-capability` give the validation stamp in
`LOG.md`.

## Spec

`specs/capability.SPEC.md`: "The rules" (the contract of `Library/capability.yaml`: evidence, legs, grants,
injection, posture, pairs), then one section per script, `run` first and the others in alphabetical order.
