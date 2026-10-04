"""Committed secrets: gitleaks when installed, detect-secrets otherwise. Spec: specs/secret_scan.SPEC.md.

TOOLING "Secrets adapter": gitleaks (MIT, a Go binary, optional) is preferred; detect-secrets
(Apache-2.0, pip) is the fallback and a normal requirement, so the check always runs. A
finding names the file, line, and kind of secret, never the value or a hash of it: a report
must not leak what it found, and a hash of a short password can be reversed by guessing.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from audience import _build_file

SKIPPED = "no secret scanner available (install gitleaks, or detect-secrets from requirements.txt)"


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
    if hits is None:
        return [{"check": "secret.found", "file": None, "line": None, "skipped": SKIPPED}]
    merged: dict[tuple, dict] = {}
    for h in hits:
        key = (h["file"], h["line"])
        m = merged.setdefault(key, {"check": "secret.found", "file": h["file"], "line": h["line"],
                                    "kinds": [], "engine": h["engine"],
                                    "audience": files.get(h["file"])})
        if h["kind"] not in m["kinds"]:
            m["kinds"].append(h["kind"])
    return [merged[k] for k in sorted(merged, key=lambda k: (k[0], k[1] or 0))]
