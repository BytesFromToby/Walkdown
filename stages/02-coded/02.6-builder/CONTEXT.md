# 02.6-builder: the builder checks

**Question:** will what was built work for the person who installs it, and does it do what its author meant
it to?
**Kind of evidence:** derived and counted, never judged: facts with locations and counts. Nothing here
says a repository is good or bad.
**Reports under:** the questions on the pages about building (Size and Shape: what comes in the
package and how much of the AI's memory it uses; is it transferable to other machines: operating systems
and other AI tools; does it ask only for the tools it needs; finished and up to date, under anything to be
careful about), Misalignment (where a skill differs from the Agent Skills
standard, R13), and the matching sections of `full.md`. The step has no
section of its own; it has a row in `LOG.md` and a validation stamp.

## Inputs

- `<input_dir>`: the folder audited, read-only; its text is read the way `02.4-phrases` reads it
  (`stages/_shared/readtext.py`). `python stages/02-coded/02.6-builder/run.py <input_dir> [--reports <dir>]`
- `--reports <dir>` (the runner gives `data/`). `reads` in `stages/stages.json` names `02.1-inventory` to
  `02.5-capability`; the code loads these:
  - `data/02.1-inventory.json`: file rows, hooks, MCP servers, scripts, the line endings git committed;
  - `data/graph.json` (from `02.3-graph`): what loads what, for what ships, what it costs, how far a skill reaches;
  - `data/02.4-phrases.json`: `secret.found`, so no quote repeats a secret;
  - `data/02.5-capability.json`: `cap.injection` (the bytes a hook adds) and the `testdata+loaded` pairs.
  Without `--reports`, `earlier_steps.py` runs the earlier steps first.
- `Library/tools.yaml`, `hosts.yaml`, `trigger.yaml`, `asks.yaml`, `clean.yaml`, `fit.yaml`, `loading.yaml`.

## Process

In this order: what it needs to run and what ties it to one machine (`needs.py`: `need.*`, `port.*`), which
AI hosts it is ready for (`hosts.py`: `host.*`), whether each skill, agent, and command will trigger
(`trigger.py`: `trig.*`), what its text asks tools to do (`asks.py`: `ask.*`), whether it is current and
clean (`clean.py`: `clean.*`), whether the tools it grants fit the job (`fit.py`: `fit.*`), and what ships
and what it costs in an AI's context (`cost.py`: `cap.ship`, `cap.context`).

Never: say a program, a host, a date, or a tool is wrong, or a repository ready or not ready; import
another step's code; run anything from the input; fetch a URL; write a file.

## Outputs

One contract-1 report on stdout (the fields are in `stages/CONTRACT.md`). The runner saves it as
`data/02.6-builder.json`, and stderr as `data/02.6-builder.notes.txt`. It writes nothing else.

## The human check

A finding is a place to look at or a count, not a verdict: a program that is not declared may be on every
machine; a loop with no stated limit may have its limit elsewhere; a token count is an estimate from size.
The fixtures `Fixtures/02.6-builder/` (seven cases, one per check) and
`python tools/grader/grader.py 02.6-builder` show that each check finds what it should and nothing it
should not; a zero from a check the fixtures do not prove is not a clean bill.

## Spec

`specs/builder.SPEC.md`: one section per script (`run.py` with `earlier.py`, `needs.py`, `hosts.py`,
`trigger.py`, `asks.py`, `clean.py`, `fit.py`, `cost.py`).
