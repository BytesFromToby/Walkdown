"""Validation stamps from the grader. Spec: specs/validate.SPEC.md."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Stamp:
    result: str
    gate: str | None = None
    negative: str | None = None
    recall: str | None = None
    skipped: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        parts = [f"{k} {v}" for k, v in (("gate", self.gate), ("negative", self.negative),
                                          ("recall", self.recall)) if v]
        inner = ", ".join(parts)
        if self.skipped:
            shown = ", ".join(self.skipped) if len(self.skipped) <= 3 else f"{len(self.skipped)} rows"
            inner += ("; " if inner else "") + "skipped: " + shown
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


def stamps(root, python, stages, env: dict | None = None) -> dict[str, Stamp]:
    """`env`: extra environment for the grader runs, e.g. the stage 6 labeling backend the
    run used (WALKDOWN_SOFT_LABEL), so stage 6's stamp measures that backend's recall."""
    root = Path(root)
    out = {}
    run_env = {**os.environ, **(env or {})}
    for stage in stages:
        proc = subprocess.run([str(python), str(root / "grader" / "grader.py"), stage, "--json"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=run_env)
        try:
            got = parse(json.loads(proc.stdout))
        except (json.JSONDecodeError, KeyError, TypeError):
            got = {}
        out[stage] = got.get(stage, Stamp("ERROR"))
    return out
