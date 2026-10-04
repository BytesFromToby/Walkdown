# secret_scan.py (added 2026-10-04)

Committed secrets (TOOLING "Secrets adapter"): gitleaks when its binary is installed (MIT,
optional), detect-secrets otherwise (Apache-2.0, in requirements.txt), so the check runs on any
install. Named `secret_scan` so it never shadows Python's `secrets` module.

## Inputs

The input folder and `{rel: audience}` for the text files stage 4 scanned. Lock and build files
(`audience._build_file`) are left out: their integrity hashes look like secrets.

## Outputs

- One `secret.found` per file and line: `kinds` (the detectors' names for what they matched,
  merged), `engine` (`gitleaks` or `detect-secrets`), `audience`.
- No scanner available: one skip finding (`file` null) naming what to install; stage 7 lists it.
- `run.mask_secret_lines`: every other stage 4 finding on a line with `secret.found` has its
  text fields (`quote`, `definition`, `condition`, `body`, matched words) replaced by
  `SECRET_MASK` and `masked: true`; the location stays.

## Must never

- Put a secret's value, or a hash of it, in any finding or report. (A hash of a short password
  can be reversed by guessing.)
- Fail the run when no scanner is installed.

## Done when

1. A made-up key is found by line, and neither value nor hash appears (`tests/test_secret_scan.py`).
2. No scanner gives a skip (`tests/test_secret_scan.py`).
3. Quotes on secret lines are masked; others are not (`tests/test_secret_scan.py`).
4. Fixture `secrets-repo`: the key is found; a clean file and a lock file are not; no finding
   repeats the value (grader gate and negatives).
