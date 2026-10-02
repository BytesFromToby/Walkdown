# run.py: spec

The single entry point for stage 5. Gets the stage 1 to 4 reports, derives the
capability map (`legs`, `injection`, `posture`, `pairs`), and prints one
contract-1 report (`stages/CONTRACT.md`). It detects nothing.

## Inputs

```
python stages/05-capability/run.py <input_dir> [--reports <dir>] [--out <dir>]
```

- `--reports <dir>`: saved stage reports for this input (`inputs.load_dir`).
  Without `graph.json` in it, hook bytes are `unknown` and stderr says why.
- Without it: `inputs.run_stages` with the same Python, in a temporary folder
  outside the input that is removed afterwards.

## Outputs

stdout: `{"stage": "05-capability", "contract": 1, "findings": [...]}`, in this
order: three `cap.leg`, the `cap.grant` findings, the `cap.injection` findings,
one `cap.load-bytes`, the `cap.posture` findings, the `cap.pair` findings.
Every finding carries `evidence` and `evidence_total` (the full count); on
stdout `evidence` holds at most `EVIDENCE_CAP` (20) entries.

stderr: the stage 5 limit notes (`rules.LIMITS`), one line per skip carried
forward from an input stage (stage, check, file, reason), and a one-line map
summary (legs present of three, stated flatly).

`--out <dir>`: also writes `<dir>/capability.json`, the same report with every
evidence list whole. The folder is created if needed. An `--out` inside
`<input_dir>` is refused (exit 2).

Exit 0 when a report was produced. Exit 2 for a missing or non-folder input, an
unreadable or invalid `--reports` folder, or a refused `--out`. Exit 1 when an
input stage fails.

## Must never

- Print anything but the report to stdout.
- Write inside `<input_dir>`; write anywhere without `--out` except its own
  temporary folder.
- Import another stage's code, run anything from the input, or fetch a URL.
- Conclude, score, rank, or render a verdict; omit an absent leg.

## Done when (each backed by a test in `tests/test_run.py`)

1. With `--reports` holding small inline reports, stdout parses as a contract-1
   report with stage `05-capability`, exit 0, every finding has `check`,
   `file`, `line`, `evidence`, and there are exactly three `cap.leg`.
2. The findings follow the stated order, and a map with all three legs states
   them `present` true.
3. A finding with more than 20 evidence entries is capped on stdout with
   `evidence_total` the full count, and `--out` writes `capability.json` with
   the full list; `--out` inside the input is refused.
4. A skip in an input report is named on stderr and the run still exits 0.
5. A missing input folder exits 2 with nothing on stdout; a `--reports` folder
   missing a report exits 2; the input is byte-identical after a run.
6. No finding has a field named risk, severity, score, or verdict.
