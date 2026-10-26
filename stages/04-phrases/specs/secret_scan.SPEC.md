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
- Key shapes Walkdown checks itself, on every scanned file whichever scanner ran (`KEY_SHAPES`;
  2026-10-25, review C43: detect-secrets has no rule for Anthropic keys, and a real-looking one
  in prose was missed): an Anthropic key (`sk-ant-api` or `sk-ant-admin`, two digits, `-`, then
  32 or more letters, digits, `_` or `-`), kind `Anthropic API Key`. A match on a line a scanner
  flagged adds its kind there; otherwise it is its own finding with engine `walkdown`.
- `run.mask_secret_lines`: every other stage 4 finding on a line with `secret.found` has its
  text fields (`quote`, `definition`, `condition`, `body`, `decoded_text`, matched words) replaced by
  `SECRET_MASK` and `masked: true`; the location stays. A line whose secret is only base64 that
  decodes to readable text is not masked: it holds no key, and its text is the instruction a
  reader needs (2026-10-25, review C42).

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
6. An Anthropic key in prose is found with its kind, with no scanner or with one, and its value
   never appears (`test_an_anthropic_key_is_found_by_its_shape`).

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
  by `-` or `_` with no digits (a name such as a Kubernetes `secretName`), or contains a space: "a plain word or prose, not a value";
  is a placeholder (2026-10-25, review C43: `ClientSecret: "abc123..."` in a README reached the
  summary): it ends in `...` or `…`, is in angle brackets (`<your-key>`), starts with `your`, is
  only `x`, `*`, or `.` (three or more), starts with `abc123`, or is `changeme`, `placeholder`,
  `dummy`, `example`, or `redacted` (any case): "a placeholder, not a value".
- entropy kinds only, and a base64 run on the line decodes to readable text
  (`foldtext.base64_texts`): "base64 that decodes to readable text, not a key" (2026-10-25,
  review C42: an instruction hidden in base64 was filed as a committed secret; stage 4 matches
  the decoded text itself).

The report counts these apart and lists them with the reason in the full report only.

5. Each rule marks its example and leaves a made-up key unmarked (`tests/test_secret_scan.py`);
   placeholders are marked and a key that only ends in letters is not
   (`test_placeholders_are_not_secrets`).
