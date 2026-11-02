"""Committed secrets: detect-secrets, and key shapes of our own. Spec: specs/phrases.SPEC.md, secret_scan.

TOOLING "Secrets adapter": detect-secrets (Apache-2.0, pip) is a normal requirement, so the check
always runs. gitleaks is not run: a repository's own `.gitleaks.toml` and `.gitleaksignore` steer it
(its README), and the repository is what is under audit (2026-11-01, owner). A
finding names the file, line, and kind of secret, never the value or a hash of it: a report
must not leak what it found, and a hash of a short password can be reversed by guessing.
"""
from __future__ import annotations

import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
# The mask must skip what the scan marks with BASE64_TEXT, and cover the whole of a key whose first line the scan flags.
from secretmask import BASE64_TEXT, is_private_key, key_end  # noqa: E402
from foldtext import base64_texts  # noqa: E402
import coverlines as cov  # noqa: E402
import readtext  # noqa: E402

SECRET = "secret.found"  # the key of its coverage line (`run.LINES`)
COULD_NOT = "the secret scan could not scan this file"
SKIPPED = "no secret scanner available (install detect-secrets from requirements.txt)"
# The files the scan leaves out by name: a lock file is made of hashes, and a scanner takes a hash for a key. Every other file is read, build
# files included (2026-11-01, owner: `audience.BUILD_FILES` kept `package.json` and `.npmrc` out for a reason only lock files have, and
# nothing said so). This list is the scan's own: `audience` says who reads a file.
LOCK_FILES = {"package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb", "cargo.lock",
              "poetry.lock", "uv.lock", "pipfile.lock", "go.sum", "gemfile.lock"}

# Lines a scanner flags that hold no secret (2026-10-09: on six real repositories every hit
# checked was one of these). The hit is kept and marked, never dropped: benign hits are
# recorded, and the report counts them apart from the lines that may hold a secret.
ENTROPY = {"Hex High Entropy String", "Base64 High Entropy String", "generic-api-key"}
HASH_KEY = re.compile(r"""["']?\b(?:[\w-]*[_-])?(sha(1|224|256|384|512)?|md5|hash|digest|checksum|integrity|etag|"""
                      r"""commit|oid|fingerprint)\b["']?\s*[:=]""", re.I)
LOCAL_URL = re.compile(r"://[^/\s:@]+:[^@\s]*@(localhost|127\.0\.0\.1|\[::1\]|"
                       r"([\w.-]+\.)?example\.(com|net|org)|[\w.-]+\.(local|test|invalid|example|localhost))(?=[:/?#\s\"'`]|$)", re.I)
URL_KINDS = {"Basic Auth Credentials", "Secret Keyword"}
# An example value, never a real one (2026-10-25, review C43: ClientSecret: "abc123..." in a
# README reached the summary as a committed secret).
PLACEHOLDER = re.compile(r".*(\.\.\.|…)|<[^<>]+>|your\b.*|your[-_].*|[x*.]{3,}|abc123.*|changeme|"
                         r"placeholder|dummy|example|redacted", re.I)
# Key shapes no installed scanner may know (2026-10-25, review C43: detect-secrets has no rule
# for Anthropic keys, and a real-looking one in prose was missed).
KEY_SHAPES = {"Anthropic API Key": re.compile(r"\bsk-ant-(?:api|admin)\d{2}-[A-Za-z0-9_-]{32,}")}
# A flagged value that is one base64 run, as `foldtext.base64_texts` reads one: only then can the whole of it be readable text.
B64_VALUE = re.compile(r"[A-Za-z0-9+/]{24,}={0,2}")
# A comment is the audited repository's own word about a line, and neither the scanner nor the mark takes it (2026-11-01: this filter
# dropped a line carrying `# pragma: allowlist secret`, with no record).
ALLOWLIST_FILTER = "detect_secrets.filters.allowlist.is_line_allowlisted"
COMMENT_TAIL = re.compile(r"(?<=\S)\s+(?:#|//|/\*|<!--|--\s|'\s).*$")


def likely_not_secret(line: str, kinds: list[str], all_text: bool = True) -> str | None:
    """Why a flagged line holds no secret, or None. Only plain cases: a hash under a key named
    for a hash, a password in a URL for a local or reserved test host, a keyword whose value is
    a variable name, a plain lowercase word, or prose. A comment after the code is no part of the
    line here: its spaces would read as prose, and a hash key or an address in it as the line's own.
    `all_text`: whether every value the scanner flagged on the line is base64 that decodes to readable text (`reads_as_text`); a
    line with readable base64 and a flagged value that is not (a key beside the text) is no `BASE64_TEXT` (2026-11-02)."""
    ks = set(kinds)
    line = COMMENT_TAIL.sub("", line)
    if ks <= ENTROPY and HASH_KEY.search(line):
        return "a hash under a key named for one"
    if ks <= ENTROPY and all_text and base64_texts(line):
        return BASE64_TEXT
    if ks <= URL_KINDS and LOCAL_URL.search(line):
        return "a password in a URL for a local test address"
    if ks == {"Secret Keyword"}:
        m = re.search(r"[:=]\s*(.*)$", line)
        value = m.group(1).strip().strip("\"'`,;") if m else ""
        if re.fullmatch(r"\$?\{?[A-Z][A-Z0-9_]*\}?", value):
            return "a variable name, not a value"
        if re.fullmatch(r"[a-z]+([-_][a-z]+)*", value) or " " in value:
            return "a plain word or prose, not a value"
        if PLACEHOLDER.fullmatch(value):
            return "a placeholder, not a value"
    return None


def reads_as_text(value) -> bool:
    """Whether a value the scanner flagged is base64 that decodes to readable text (`foldtext.base64_texts` finds it whole), as an
    instruction hidden in base64 is (review C42). A key, hex or base64 of random bytes, is not. Only this answer is kept, never the
    value."""
    value = str(value or "").strip()
    return bool(B64_VALUE.fullmatch(value)) and bool(base64_texts(value))


def _could_not(rel: str) -> dict:
    """The skip finding for a file a scanner could not scan: our own words, and never the error's (its text could hold words
    from the repository)."""
    return {"check": "secret.found", "file": rel, "line": None, "skipped": COULD_NOT}


def _text(root: Path, rel: str) -> str | None:
    """A file's text as every step reads it (`readtext.decode`), or None when it cannot be opened or its bytes do not decode."""
    try:
        return readtext.decode((root / rel).read_bytes())
    except OSError:
        return None


def _shapes(root: Path, rels: set[str], skips: list | None = None, unscanned=()) -> list[dict]:
    """KEY_SHAPES on every line of the scanned files: kind and place, never the value. This is the pass that reads every file
    in our own process, so it is where a file counts for the line of `secret.found` (`coverlines`): as looked at once its
    lines are read, and as explained when the file cannot be read (a skip finding in our words, `skips`) or a scanner has
    already said it could not scan it (`unscanned`: a skip finding of its own, or the one that says no scanner is installed)."""
    out = []
    for rel in sorted(rels):
        text = _text(root, rel)
        if text is None:
            if skips is not None and rel not in unscanned:
                skips.append(_could_not(rel))
            cov.explain(SECRET)
            continue
        if rel in unscanned:
            cov.explain(SECRET)
        else:
            cov.look(SECRET)
        for n, line in enumerate(readtext.split_lines(text), 1):
            out += [{"file": rel, "line": n, "kind": kind, "engine": "walkdown"}
                    for kind, rx in KEY_SHAPES.items() if rx.search(line)]
    return out


def _scan_decoded(library, path: str, text: str) -> list | None:
    """Every hit of one file through the library with the text we decoded, or None when the library did not ask for it. It opens a
    file itself with the machine's default encoding and takes a `UnicodeDecodeError` for a binary file: no scan and no error
    (2026-11-01: on cp1252, a file holding U+274C, U+1F4DD, or a tag character; on UTF-8, any file in another encoding). So for this
    call the name `open` in its module is ours. It does not ask when its filters leave the file out by name (`.svg`, `.css`, a path
    with `swagger`), or if a later version reads some other way. Its `scan_file` gives a hit for each line a secret stands on. Its
    `SecretsCollection` keeps one of a value in a file, and its GitHub rule captures only the prefix, so every token of a file is one
    value there: a later line had no row, so no mask (2026-11-01)."""
    asked = []

    def opened(filename):
        asked.append(filename)
        stream = io.StringIO("\n".join(readtext.split_lines(text)), newline="\n")  # a lone CR ends no line, as in every step
        stream.name = filename  # the library's transformers choose by it
        return stream

    library.open = opened
    try:
        hits = list(library.scan_file(path))
    finally:
        del library.open
    return hits if asked else None


def _detect_secrets(root: Path, rels: set[str], skips: list | None = None) -> list[dict] | None:
    """detect-secrets on each file, handed the text as Walkdown decodes it. A file it did not read (the bytes do not decode, it raises,
    it never asked for the text) is a skip finding in our words, and `_shapes` counts it as explained (`coverlines`)."""
    try:
        from detect_secrets.core import scan as library
        from detect_secrets.settings import default_settings
    except ImportError:
        return None
    out = []
    with default_settings() as settings:
        settings.disable_filters(ALLOWLIST_FILTER)
        for rel in sorted(rels):
            text = _text(root, rel)
            try:
                hits = None if text is None else _scan_decoded(library, str(root / rel), text)
            except Exception:  # the exception's text is not kept: it could hold words from the repository
                hits = None
            if hits is None:
                if skips is not None:
                    skips.append(_could_not(rel))
                continue
            out += [{"file": rel, "line": s.line_number, "kind": s.type or "secret", "engine": "detect-secrets",
                     "text": reads_as_text(s.secret_value)} for s in hits]
    return out


def scannable(files) -> set[str]:
    """The files of `files` the secret scan reads: all but lock files (`LOCK_FILES`). It is the check's scope, and the count of what it
    is to look at (`coverlines`)."""
    return {rel for rel in files if rel.rsplit("/", 1)[-1].lower() not in LOCK_FILES}


def scan(root, files: dict[str, str]) -> list[dict]:
    """`files`: {rel: audience} of the text files `02.4-phrases` scanned, and the pattern lists. Lock files are left out
    (`scannable`). One `secret.found` per file and line,
    kinds merged; or one skip finding when no scanner is available. A file counts for the line of this check where `_shapes`
    reads it: as looked at, or as explained by a skip finding (a file that cannot be read or scanned, or none installed)."""
    root = Path(root).resolve()
    rels = scannable(files)
    file_skips: list[dict] = []
    hits = _detect_secrets(root, rels, file_skips)
    skip = []
    if hits is None:
        skip, hits = [{"check": "secret.found", "file": None, "line": None, "skipped": SKIPPED}], []
    unscanned = rels if skip else {x["file"] for x in file_skips}
    hits = hits + _shapes(root, rels, file_skips, unscanned)
    merged: dict[tuple, dict] = {}
    lines: dict[str, list[str]] = {}
    not_text = {(h["file"], h["line"]) for h in hits if not h.get("text")}  # a line with a flagged value that is no readable base64
    for h in hits:
        key = (h["file"], h["line"])
        m = merged.setdefault(key, {"check": "secret.found", "file": h["file"], "line": h["line"],
                                    "kinds": [], "engine": h["engine"],
                                    "audience": files.get(h["file"])})
        if h["kind"] not in m["kinds"]:
            m["kinds"].append(h["kind"])
    for (rel, ln), m in merged.items():
        if rel not in lines:
            lines[rel] = readtext.split_lines(_text(root, rel) or "")
        inside = isinstance(ln, int) and 0 < ln <= len(lines[rel])
        text = lines[rel][ln - 1] if inside else ""
        why = likely_not_secret(text, m["kinds"], all_text=(rel, ln) not in not_text)
        if why:
            m["likely_not_secret"] = why
        # A private key's first line is the one flagged, and the lines below it are the key: `key_end` is its last, so the mask
        # covers every line a finding of another step could quote (2026-11-02).
        last = key_end(lines[rel], ln) if inside and is_private_key(m["kinds"]) else None
        if last:
            m["key_end"] = last
    return skip + file_skips + [merged[k] for k in sorted(merged, key=lambda k: (k[0], k[1] or 0))]
