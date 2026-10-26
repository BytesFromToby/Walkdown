"""Committed secrets: gitleaks when installed, detect-secrets otherwise. Spec: specs/secret_scan.SPEC.md.

TOOLING "Secrets adapter": gitleaks (MIT, a Go binary, optional) is preferred; detect-secrets
(Apache-2.0, pip) is the fallback and a normal requirement, so the check always runs. A
finding names the file, line, and kind of secret, never the value or a hash of it: a report
must not leak what it found, and a hash of a short password can be reversed by guessing.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from audience import _build_file
from foldtext import base64_texts

SKIPPED = "no secret scanner available (install gitleaks, or detect-secrets from requirements.txt)"

# Lines a scanner flags that hold no secret (2026-10-09: on six real repositories every hit
# checked was one of these). The hit is kept and marked, never dropped: benign hits are
# recorded, and the report counts them apart from the lines that may hold a secret.
ENTROPY = {"Hex High Entropy String", "Base64 High Entropy String", "generic-api-key"}
HASH_KEY = re.compile(r"""["']?\b(?:[\w-]*[_-])?(sha(1|224|256|384|512)?|md5|hash|digest|checksum|integrity|etag|"""
                      r"""commit|oid|fingerprint)\b["']?\s*[:=]""", re.I)
LOCAL_URL = re.compile(r"://[^/\s:@]+:[^@\s]*@(localhost|127\.0\.0\.1|\[::1\]|"
                       r"([\w.-]+\.)?example\.(com|net|org)|[\w.-]+\.(local|test|invalid|example|localhost))(?=[:/?#\s\"'`]|$)", re.I)
BASE64_TEXT = "base64 that decodes to readable text, not a key"  # review C42
URL_KINDS = {"Basic Auth Credentials", "Secret Keyword"}
# An example value, never a real one (2026-10-25, review C43: ClientSecret: "abc123..." in a
# README reached the summary as a committed secret).
PLACEHOLDER = re.compile(r".*(\.\.\.|…)|<[^<>]+>|your\b.*|your[-_].*|[x*.]{3,}|abc123.*|changeme|"
                         r"placeholder|dummy|example|redacted", re.I)
# Key shapes no installed scanner may know (2026-10-25, review C43: detect-secrets has no rule
# for Anthropic keys, and a real-looking one in prose was missed; gitleaks has one).
KEY_SHAPES = {"Anthropic API Key": re.compile(r"\bsk-ant-(?:api|admin)\d{2}-[A-Za-z0-9_-]{32,}")}


def likely_not_secret(line: str, kinds: list[str]) -> str | None:
    """Why a flagged line holds no secret, or None. Only plain cases: a hash under a key named
    for a hash, a password in a URL for a local or reserved test host, a keyword whose value is
    a variable name, a plain lowercase word, or prose."""
    ks = set(kinds)
    if ks <= ENTROPY and HASH_KEY.search(line):
        return "a hash under a key named for one"
    if ks <= ENTROPY and base64_texts(line):
        return BASE64_TEXT
    if ks <= URL_KINDS and LOCAL_URL.search(line):
        return "a password in a URL for a local test address"
    if ks == {"Secret Keyword"}:
        m = re.search(r"[:=]\s*(.*)$", line)
        value = re.split(r"\s+#", m.group(1))[0].strip().strip("\"'`,;") if m else ""
        if re.fullmatch(r"\$?\{?[A-Z][A-Z0-9_]*\}?", value):
            return "a variable name, not a value"
        if re.fullmatch(r"[a-z]+([-_][a-z]+)*", value) or " " in value:
            return "a plain word or prose, not a value"
        if PLACEHOLDER.fullmatch(value):
            return "a placeholder, not a value"
    return None


def _shapes(root: Path, rels: set[str]) -> list[dict]:
    """KEY_SHAPES on every line of the scanned files: kind and place, never the value."""
    out = []
    for rel in sorted(rels):
        try:
            text = (root / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            out += [{"file": rel, "line": n, "kind": kind, "engine": "walkdown"}
                    for kind, rx in KEY_SHAPES.items() if rx.search(line)]
    return out


def _gitleaks(root: Path, rels: set[str]) -> list[dict] | None:
    exe = shutil.which("gitleaks")
    if not exe:
        return None
    with tempfile.TemporaryDirectory(prefix="walkdown-gitleaks-") as tmp:
        report = Path(tmp) / "report.json"
        for args in (["dir", str(root)], ["detect", "--no-git", "--source", str(root)]):
            p = subprocess.run([exe, *args, "--report-format", "json", "--report-path", str(report),
                                "--redact", "--exit-code", "0", "--no-banner"],
                               capture_output=True, text=True)
            if p.returncode == 0 and report.is_file():
                break
        else:
            return None
        try:
            rows = json.loads(report.read_text(encoding="utf-8") or "[]")
        except ValueError:
            return None
    out = []
    for r in rows or []:
        rel = Path(str(r.get("File", ""))).resolve()
        try:
            rel = rel.relative_to(root).as_posix()
        except ValueError:
            rel = str(r.get("File", "")).replace("\\", "/")
        if rel in rels:
            out.append({"file": rel, "line": r.get("StartLine"), "kind": r.get("RuleID") or "secret",
                        "engine": "gitleaks"})
    return out


def _detect_secrets(root: Path, rels: set[str]) -> list[dict] | None:
    try:
        from detect_secrets import SecretsCollection
        from detect_secrets.settings import default_settings
    except ImportError:
        return None
    out = []
    with default_settings():
        for rel in sorted(rels):
            sc = SecretsCollection()
            try:
                sc.scan_file(str(root / rel))
            except Exception:
                continue
            for secrets in sc.json().values():
                for s in secrets:
                    out.append({"file": rel, "line": s.get("line_number"),
                                "kind": s.get("type") or "secret", "engine": "detect-secrets"})
    return out


def scan(root, files: dict[str, str]) -> list[dict]:
    """`files`: {rel: audience} of the text files stage 4 scanned. Lock and build files are
    left out (their integrity hashes look like secrets). One `secret.found` per file and line,
    kinds merged; or one skip finding when no scanner is available."""
    root = Path(root).resolve()
    rels = {rel for rel in files if not _build_file(rel.rsplit("/", 1)[-1].lower())}
    hits = _gitleaks(root, rels)
    if hits is None:
        hits = _detect_secrets(root, rels)
    skip = []
    if hits is None:
        skip, hits = [{"check": "secret.found", "file": None, "line": None, "skipped": SKIPPED}], []
    hits = hits + _shapes(root, rels)
    merged: dict[tuple, dict] = {}
    lines: dict[str, list[str]] = {}
    for h in hits:
        key = (h["file"], h["line"])
        m = merged.setdefault(key, {"check": "secret.found", "file": h["file"], "line": h["line"],
                                    "kinds": [], "engine": h["engine"],
                                    "audience": files.get(h["file"])})
        if h["kind"] not in m["kinds"]:
            m["kinds"].append(h["kind"])
    for (rel, ln), m in merged.items():
        if rel not in lines:
            try:
                lines[rel] = (root / rel).read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                lines[rel] = []
        text = lines[rel][ln - 1] if isinstance(ln, int) and 0 < ln <= len(lines[rel]) else ""
        why = likely_not_secret(text, m["kinds"])
        if why:
            m["likely_not_secret"] = why
    return skip + [merged[k] for k in sorted(merged, key=lambda k: (k[0], k[1] or 0))]
