# 02-coded: the coded steps

**Question:** what is in the repository, and what does it ask for?
**Kind of evidence:** counting, parsing, and matching. Six steps run in the order below. **No step here
calls a model**, and none sends anything off the machine. Each step has its own folder, contract, spec,
fixtures, and tests.

## Inputs

- The folder audited (`<input_dir>`: the `folder` of `data/01-intake.json`), read-only.
- Each step's earlier outputs, in `data/`, as `reads` says in `stages/stages.json`:

| Step | What a reader calls it | Reads |
|---|---|---|
| `02.1-inventory` | What ships | none |
| `02.2-reader` | What the model actually reads | none |
| `02.3-graph` | What loads what | `02.1-inventory` |
| `02.4-phrases` | What the text asks for | `02.1-inventory` |
| `02.5-capability` | What this touches | `02.1-inventory`, `02.2-reader`, `02.3-graph`, `02.4-phrases` |
| `02.6-builder` | Builder checks | `02.1-inventory` to `02.5-capability` |

- Tables from `Library/`: each step's contract names its own.

## Process

1. `02.1-inventory` lists and pins what ships. 2. `02.2-reader` reads each file two ways and records where
they differ. 3. `02.3-graph` finds what loads what. 4. `02.4-phrases` matches the folded text against the
pattern table. 5. `02.5-capability` derives what installing it grants. 6. `02.6-builder` asks whether it
will work for the person who installs it.

For all six: `python stages/02-coded/<step>/run.py <input_dir> [--inventory | --reports <data>] [--out <data>]`
prints one contract-1 report (`stages/CONTRACT.md`) on stdout and nothing else; notes go to stderr.

Never: call a model or fetch a URL; run anything from the input; write inside the input; import another
step's code (what steps share is in `stages/_shared/`, and an earlier step is reached through its output,
or run through `stages/_shared/earlier_steps.py` when a step runs on its own); say that a finding is a
problem (a finding is a place and a fact); pass a check that could not run (it is a skip).

## Outputs

Per step, saved by the runner: `data/<step>.json` (stdout) and `data/<step>.notes.txt` (stderr). Side
files, written when the runner gives `--out <data>`:

- `02.2-reader`: `data/normalized/text/<path>.txt` and `data/normalized/folded/<path>.txt`.
- `02.3-graph`: `data/graph.json`. `02.4-phrases`: `data/hits.json`. `02.5-capability`: `data/capability.json`.
- `02.1-inventory` and `02.6-builder` write only their report.

## The human check

Each step is graded on its own fixtures (`Fixtures/<step>/`) by `python tools/grader/grader.py <step>`;
the result is that step's validation stamp in `LOG.md`, and a step whose stamp is not PASS is named on the
pages. Every finding cites a file and line, so a person can open the place it names. A finding is a
locator, not a verdict.

## Spec

No spec of its own: each step has one, in its folder's `specs/` (`inventory.SPEC.md`, `reader.SPEC.md`,
`graph.SPEC.md`, `phrases.SPEC.md`, `capability.SPEC.md`, `builder.SPEC.md`).
