"""Validation stamps from the grader. Spec: specs/shared.SPEC.md, validate."""
from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import playwright_check  # noqa: E402
import usage as usage_mod  # noqa: E402


@dataclass
class Stamp:
    result: str
    gate: str | None = None
    negative: str | None = None
    recall: str | None = None
    skipped: list[str] = field(default_factory=list)
    cached: str | None = None  # the date a reused stamp was measured (C16)
    # What the grader's run of this step used (M1 slice A; `usage.py`): the fixture check of a model read sends its fixtures.
    # None when it sent nothing or the backend reported nothing, and always for a reused stamp: a reused stamp spent none.
    usage: dict | None = None

    def to_dict(self) -> dict:
        """The stamp as data, for the run's record (`record.py`): the report stage reads it back. `usage` is in it only when the
        check spent tokens, so a stamp that spent none is the record it always was."""
        return {"result": self.result, "gate": self.gate, "negative": self.negative,
                "recall": self.recall, "skipped": list(self.skipped), "cached": self.cached,
                **({"usage": dict(self.usage)} if self.usage else {})}

    @classmethod
    def from_dict(cls, d: dict) -> "Stamp":
        saved = d.get("usage")  # a record that cannot be read as counts is a stamp that spent none, not a crash
        return cls(d.get("result", "ERROR"), d.get("gate"), d.get("negative"), d.get("recall"),
                   list(d.get("skipped") or []), cached=d.get("cached"),
                   usage=saved if usage_mod.valid(saved) and saved else None)

    @property
    def measured(self) -> bool:
        """Whether this stamp measures the step's "none" (M9 slice C): the result is a pass, or a check skipped for a missing
        tool, and some of its rows were measured (a gate, a negative, or a recall). A step stamped anything else (FAIL, ERROR,
        SETUP ERROR, NOT BUILT, `no fixture set`), and a model read whose rows were all skipped, has a "none" nobody
        measured, and the report says no "checked N, found none" of it. The one place that rule is kept. A row is measured when it
        was asked and not skipped: the fractions count the skipped rows in their totals (a sweep with no key reads `recall 0/34`
        with 34 rows skipped), so the skipped rows are taken off."""
        if self.result not in ("PASS", "INCOMPLETE"):
            return False
        rows = 0
        for x in (self.gate, self.negative, self.recall):
            if not x:
                continue
            try:
                rows += int(str(x).split("/")[1])
            except (IndexError, ValueError):
                return False  # a count that is not `passed/total` measured nothing anyone can state
        return rows - len(self.skipped) > 0

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
        spent = s.get("usage")  # the grader sums the usage its runs of the step reported (`tools/grader/grader.py`)
        out[s["stage"]] = Stamp(s.get("result", "ERROR"), _frac(s.get("gate"), "passed", "total"),
                                _frac(s.get("negative"), "passed", "total"),
                                _frac(s.get("recall"), "found", "total"), skipped,
                                usage=spent if usage_mod.valid(spent) and spent else None)
    return out


CACHE = Path(".cache") / "stamps.json"
# The results a cached stamp may be: a pass, a check that skipped for a missing tool (the fingerprint holds the tools), and
# a step with no fixture set. Any other (FAIL, SETUP ERROR, NOT BUILT, ERROR) can come from the machine and not the code
# (a killed process, a full disk), so it is measured again at the next run and never kept.
NO_FIXTURE_SET = "no fixture set"
CACHEABLE = ("PASS", "INCOMPLETE", NO_FIXTURE_SET)
FINGERPRINT_DIRS = ("stages", "tools/grader", "Fixtures", "Library")
GRADER = Path("tools") / "grader" / "grader.py"
SKIP_PARTS = {"__pycache__", ".pytest_cache"}


def _playwright() -> bool:
    """The check the reader makes (playwright_check.available): the package and an installed Chromium."""
    try:
        return playwright_check.available()[0]
    except Exception:
        return False


def optional_tools() -> str:
    """Which optional tools a grader run would find. Installing one changes what a stage can
    measure (2026-10-08: Tesseract installed, the cached `02.2-reader` INCOMPLETE was still reused)."""
    have = {
        "tesseract": bool(shutil.which("tesseract")) and importlib.util.find_spec("pytesseract") is not None,
        "playwright": _playwright(),
    }  # pdf2image left out 2026-10-12 (no stage uses it); Playwright back 2026-10-20 (HTML render); gitleaks left out 2026-11-01 (no stage runs it)
    return ",".join(f"{k}={int(v)}" for k, v in sorted(have.items()))


def fingerprint(root, env: dict | None = None) -> str:
    """Everything a stamp depends on: the code under stages/ and tools/grader/, the fixtures and
    answers, the Library's tables (restructure step 3), the Python version, the optional tools
    present, and the AI choices (2026-10-03 review C16). Any change to any of them gives a
    new fingerprint, so a cached stamp is never stale."""
    root = Path(root)
    h = hashlib.sha256()
    for d in FINGERPRINT_DIRS:
        for p in sorted((root / d).rglob("*")):
            if p.is_file() and not SKIP_PARTS & set(p.parts):
                h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
                h.update(p.read_bytes() + b"\0")
    h.update(f"python {sys.version_info.major}.{sys.version_info.minor}".encode())
    h.update(f"tools {optional_tools()}".encode())
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
    """`env`: extra environment for the grader runs, e.g. the sweep backend the run used
    (WALKDOWN_SOFT_SWEEP), so Sweep's stamp measures that backend's recall.
    `cache`: reuse a stamp measured earlier for the same fingerprint (`.cache/stamps.json`);
    a reused stamp says when it was measured, and only a result in `CACHEABLE` is saved or reused. False always runs
    the grader."""
    root = Path(root)
    out = {}
    run_env = {**os.environ, **(env or {})}
    path = root / CACHE
    saved = _load_cache(path) if cache else {}
    fp = fingerprint(root, env)
    fresh = {}
    for stage in stages:
        hit = saved.get(f"{stage}|{fp}")
        if hit and hit.get("result") in CACHEABLE:  # an entry an older version saved for another result is not reused
            out[stage] = Stamp(hit["result"], hit.get("gate"), hit.get("negative"),
                               hit.get("recall"), list(hit.get("skipped") or []),
                               cached=hit.get("date"))
            continue
        proc = subprocess.run([str(python), str(root / GRADER), stage, "--json"],
                              capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=run_env)
        try:
            got = parse(json.loads(proc.stdout))
        except (json.JSONDecodeError, KeyError, TypeError):
            got = {}
        st = got.get(stage, Stamp("ERROR"))
        out[stage] = st
        # A check that measured nothing (a model read in which every fixture row was skipped: no key, no login, no program) is
        # not kept: the person may fix that and run again, and the same stamp must not be handed back (M1 slice A).
        if st.result in CACHEABLE and (st.measured or st.result == NO_FIXTURE_SET):
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
