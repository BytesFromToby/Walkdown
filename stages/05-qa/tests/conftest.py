import json
import sys
from pathlib import Path

import pytest

TESTS = Path(__file__).resolve().parent
HERE = TESTS.parent
for p in (HERE, HERE.parent / "_shared", TESTS):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import facts as F  # noqa: E402
from qa_helpers import STEPS, T, passed, report, step  # noqa: E402
from validate import Stamp  # noqa: E402


@pytest.fixture
def facts():
    """`facts(...)`: a `Facts` in memory. By default every step in `ran` has an empty report and passed its fixture
    check; `failed` names steps the record says crashed (no output); `outputs` adds or replaces reports; `stamps` is
    a dict of `Stamp`s, or "pass"."""
    def make(ran=STEPS, failed=(), outputs=None, stamps="pass", **kw):
        rows = [step(s, ok=s not in failed, error="exit 1: ValueError" if s in failed else None) for s in ran]
        reports = {s: report(s) for s in ran if s not in failed}
        reports.update(outputs or {})
        if stamps == "pass":
            stamps = passed([s for s in ran if s in reports])
        return F.Facts(steps=rows, stamps=stamps, reports=reports, **kw)
    return make


@pytest.fixture
def run_folder(tmp_path):
    """`run_folder(...)`: a run folder on disk with a record of format 3 and the saved outputs given (`drop` leaves
    some out, `files` adds files to `data/`, and the rest are keys of the record: `until`, `held`, ...)."""
    def make(ran=STEPS, failed=(), outputs=None, stamps="pass", drop=(), files=None, **record_keys):
        run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
        data = run / "data"
        data.mkdir(parents=True)
        docs = {s: report(s) for s in ran if s not in failed and s not in drop}
        docs.update(outputs or {})
        for stage, doc in docs.items():
            (data / f"{stage}.json").write_text(json.dumps(doc), encoding="utf-8")
        if stamps == "pass":
            stamps = {s: Stamp("PASS", "1/1", "1/1") for s in ran if s not in failed}
        rec = {"format": 3, "finished": T, "context": 32000, "hosts": [],
               "steps": [step(s, ok=s not in failed, error="exit 1: ValueError" if s in failed else None) for s in ran],
               "stamps": {k: v.to_dict() for k, v in stamps.items()}, **record_keys}
        (data / "run.json").write_text(json.dumps(rec), encoding="utf-8")
        for name, text in (files or {}).items():
            (data / name).write_text(text, encoding="utf-8")
        return run
    return make
