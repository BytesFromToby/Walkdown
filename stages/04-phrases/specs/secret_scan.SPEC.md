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

## Likely not a secret (2026-10-09)

On six real repositories every flagged line checked held no secret: hashes under `sha256` or
`hash` keys, a CI test database password on localhost, an environment variable's name, a
keyword followed by an ordinary word. `likely_not_secret(line, kinds)` marks these; the hit is
kept with `likely_not_secret: <reason>` (benign hits are recorded, never dropped):

- entropy kinds only, and the line has a key named for a hash (sha, sha256, md5, hash, digest,
  checksum, integrity, etag, commit, oid, fingerprint, also as a key's last part: `prefix_hash`): "a hash under a key named for one";
- Basic Auth or keyword only, and the line has a URL with a password whose host is localhost,
  127.0.0.1, ::1, example.com / .net / .org (RFC 2606), or ends in .local, .test, .invalid,
  .example, .localhost: "a password in a
  URL for a local test address";
- keyword only, and the value after the first `:` or `=` (trailing `#` comment and quotes
  removed) is an upper-case variable name: "a variable name, not a value"; is lowercase words joined
  by `-` or `_` with no digits (a name such as a Kubernetes `secretName`), or contains a space: "a plain word or prose, not a value".

The report counts these apart and lists them with the reason in the full report only.

5. Each rule marks its example and leaves a made-up key unmarked (`tests/test_secret_scan.py`).
