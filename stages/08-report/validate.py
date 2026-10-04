"""Validation stamps from the grader. Spec: specs/validate.SPEC.md."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Stamp:
    result: str
    gate: str | None = None
    negative: str | None = None
    recall: str | None = None
    skipped: list[str] = field(default_factory=list)
    cached: str | None = None  # the date a reused stamp was measured (C16)

    @property
    def text(self) -> str:
        parts = [f"{k} {v}" for k, v in (("gate", self.gate), ("negative", self.negative),
                                          ("recall", self.recall)) if v]
        inner = ", ".join(parts)
        if self.skipped:
            shown = ", ".join(self.skipped) if len(self.skipped) <= 3 else f"{len(self.skipped)} rows"
            inner += ("; " if inner else "") + "skipped: " + shown
        if self.cached:
            inner += ("; " if inner else "") + f"measured {self.cached}, same code and fixtures"
        return f"{self.result} ({inner})" if inner else self.result


def _frac(d, a, b):
    return f"{d[a]}/{d[b]}" if isinstance(d, dict) and d.get(b) else None


def parse(doc: dict) -> dict[str, Stamp]:
    out = {}
    for s in doc.get("stages", []):
        skipped = [x["id"] for x in s.get("not_ok", []) if x.get("status") == "SKIPPED"]
        out[s["stage"]] = Stamp(s.get("result", "ERROR"), _frac(s.get("gate"), "passed", "total"),
                                _frac(s.get("negative"), "passed", "total"),
                                _frac(s.get("recall"), "found", "total"), skipped)
    return out


CACHE = Path(".cache") / "stamps.json"
FINGERPRINT_DIRS = ("stages", "grader", "Fixtures")
SKIP_PARTS = {"__pycache__", ".pytest_cache"}


def fingerprint(root, env: dict | None = None) -> str:
    """Everything a stamp depends on: the code under stages/ and grader/, the fixtures and
    answers, the Python version, and the stage 6 choices (2026-10-03 review C16). Any change
    to any of them gives a new fingerprint, so a cached stamp is never stale."""
    root = Path(root)
    h = hashlib.sha256()
    for d in FINGERPRINT_DIRS:
        for p in sorted((root / d).rglob("*")):
            if p.is_file() and not SKIP_PARTS & set(p.parts):
                h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
                h.update(p.read_bytes() + b"\0")
    h.update(f"python {sys.version_info.major}.{sys.version_info.minor}".encode())
    for k in sorted(env or {}):
        if k.startswith("WALKDOWN_SOFT_"):
            h.update(f"{k}={env[k]}".encode())
    return h.hexdigest()[:20]


def _load_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def stamps(root, python, stages, env: dict | None = None, cache: bool = True) -> dict[str, Stamp]:
    """`env`: extra environment for the grader runs, e.g. the stage 6 labeling backend the
    run used (WALKDOWN_SOFT_LABEL), so stage 6's stamp measures that backend's recall.
    `cache`: reuse a stamp measured earlier for the same fingerprint (`.cache/stamps.json`);
    a reused stamp says when it was measured. False always runs the grader."""
    root = Path(root)
    out = {}
    run_env = {**os.environ, **(env or {})}
    path = root / CACHE
    saved = _load_cache(path) if cache else {}
    fp = fingerprint(root, env)
    fresh = {}
    for stage in stages:
        hit = saved.get(f"{stage}|{fp}")
        if hit:
            out[stage] = Stamp(hit["result"], hit.get("gate"), hit.get("negative"),
                               hit.get("recall"), list(hit.get("skipped") or []),
                               cached=hit.get("date"))
            continue
        proc = subprocess.run([str(python), str(root / "grader" / "grader.py"), stage, "--json"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=run_env)
        try:
            got = parse(json.loads(proc.stdout))
        except (json.JSONDecodeError, KeyError, TypeError):
            got = {}
        st = got.get(stage, Stamp("ERROR"))
        out[stage] = st
        if st.result != "ERROR":
            fresh[f"{stage}|{fp}"] = {"result": st.result, "gate": st.gate,
                                      "negative": st.negative, "recall": st.recall,
                                      "skipped": st.skipped,
                                      "date": dt.date.today().isoformat()}
    if fresh:
        merged = {**_load_cache(path), **fresh}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(merged, indent=1), encoding="utf-8")
        except OSError:
            pass  # a cache that cannot be written only costs time
    return out
