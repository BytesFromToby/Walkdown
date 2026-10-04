# run.py: spec

The single entry point for stage 6. Gets the stage 1 to 5 reports, builds the
review packet, asks the backends the user picked (none by default), and prints
one contract-1 report (`stages/CONTRACT.md`).

## Inputs

```
python stages/06-soft/run.py <input_dir> [--reports <dir>] [--out <dir>]
       [--label none|jev|laya] [--compare none|jev|laya]
       [--relational none|claude-cli]
```

- Flags override `WALKDOWN_SOFT_LABEL`, `WALKDOWN_SOFT_COMPARE`,
  `WALKDOWN_SOFT_RELATIONAL`; unset means `none`. An unknown value (flag or
  environment) exits 2.
- `--reports <dir>`: saved reports (`upstream.load_dir`). Without it,
  `upstream.run_stages` with the same Python in a temporary folder outside the
  input, removed afterwards.
- `WALKDOWN_SOFT_CLAUDE_MODEL` picks the Claude model (default `sonnet`).

## Outputs

stdout: `{"stage": "06-soft", "contract": 1, "backends": [...], "findings":
[...]}`. `backends` lists each role in use: `role` (`label`, `compare`,
`relational`), `backend`, `remote` (jev and claude-cli true, laya false),
`model`. Findings as `ask.findings`.

stderr: the backends and whether each is remote; carried-forward skips from
stages 1 to 5; the `ask.summary` lines; the Jev input tokens when Jev ran; a line
per skip reason naming the backend (stage 7 lists them).

`--out <dir>`: writes `06-packet.md`, `packet.json` (the questions with their
state, and the option definitions), and `answers.jsonl` (`ask.record` per result,
every role). Created if needed. An `--out` inside the input is refused (exit 2).

Anything a backend library prints to stdout is sent to stderr, so stdout holds
only the report.

Exit 0 when a report was produced (backend failures are skips). Exit 2 for a bad
input folder, a bad flag or environment value, an invalid `--reports`, or a
refused `--out`. Exit 1 when an input stage fails.

## `--both` (added 2026-10-01)

`--both`, or `WALKDOWN_SOFT_BOTH` set to 1 / true / yes / on, makes Jev read each line
twice and average (back_jev.SPEC "Two reads"). It needs Jev as the label or compare
backend; otherwise exit 2 before anything runs. The Jev row in `backends` gains
`reads: both`.

## `--sweep` (added 2026-10-01, soft D2)

`--sweep none|jev` (or `WALKDOWN_SOFT_SWEEP`; default none). With jev: passages from
`chunks.build` (qid `sweep:<file>:<line>`) go to `Jev.sweep`; findings from
`ask.sweep_findings`; a `backends` row with role `sweep`; results in answers.jsonl with
role `sweep`. With none: no `soft.sweep` finding.

## Laya retired (2026-10-03)

Choosing `laya` still works (its code is kept), but the runner prints a note that it is
retired (13% on the real lines) and its answers are not relied on.

## Must never

- Write inside `<input_dir>`, or anywhere but `--out` and its own temporary
  folder.
- Contact a network service the user did not name (no backend is the default).
- Import another stage's code; print or store an API key.
- Let an answer change a stage 1 to 5 finding, or emit a verdict, score, or
  severity.

## Done when (each backed by a test in `tests/test_run.py`)

1. With `--reports` holding small inline reports and no backend, stdout is a
   contract-1 report with stage `06-soft`, exit 0, `soft.question` findings for
   the label and relational questions, and `soft.label` / `soft.read` skips.
2. `--out` writes `06-packet.md`, `packet.json`, `answers.jsonl`; `--out` inside
   the input exits 2; the input is byte-identical after a run.
3. The environment picks a backend and a flag overrides it (`resolve_choices`);
   an unknown value exits 2.
4. With stub label backends injected into `main`, `soft.label`, `soft.compare`,
   and `soft.agree` appear and `backends` names both with their `remote` flag.
5. A missing input folder exits 2 with nothing on stdout; a `--reports` folder
   missing a required report exits 2.
6. No finding has a field named risk, severity, score, or verdict.
