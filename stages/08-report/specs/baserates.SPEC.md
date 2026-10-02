# baserates.py (added 2026-10-01, soft D1)

Measured base rates of stage 4 patterns over the audited corpus: how often each pattern
turns up in repos already audited. A published fact about a pattern, recomputed as the
corpus grows; never a judgment of the artifact under review (CHARTER).

## Inputs

`python stages/08-report/baserates.py <name>=<input_dir> [...] [--out PATH]`; the default
out is `stages/08-report/baserates.json` (committed; render.py reads it).

## Outputs

- For each repo: stages 1 and 4 run in a temporary folder (`pipeline.run_stages` with
  `stages=["01-inventory", "04-phrases"]`); `{name, hash (inv.pin), lines: {pattern id:
  lines hit}}`.
- `count(report04)`: phrase findings only, skipped ones excluded, audience not `human`
  (the lines the summary's points draw from); a line hit by a pattern under two checks
  counts once.
- `rate(table, pattern, exclude_hash)`: the rate over the repos other than the one being
  audited (matched by hash): `repos`, `repos_hit`, `lines`, `level`. None without a table.
- `level(repos_hit)`: `rare` 0, `uncommon` 1, `common` 2 or more.
- `phrase(rate)`: "rare: in 0 of 3 other audited repos" (", N lines" when N > 0).

## Must never

- Judge, weight, sum, or rank. A level is a bin of a count, shown with the count.
- Write inside a corpus repo.
- Count a repo against itself (render passes the run's hash).

## Done when (each backed by a test in `tests/test_baserates.py`)

1. `count` counts non-human, unskipped phrase lines once per line.
2. `level` bins 0 / 1 / 2+.
3. `rate` excludes the audited repo by hash; `phrase` words it.
4. The shipped table loads.
