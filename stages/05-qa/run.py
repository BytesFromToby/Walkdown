"""Step 05 runner: the check of the run, before the report. Prints one contract-1 report. Spec: specs/qa.SPEC.md, run.

    python stages/05-qa/run.py <run folder> [--brief]

It reads a run folder (the record, each step's saved output and messages, the call logs) and reports what should be
there and is not (`qa.gap`) and what the run did not examine (`qa.limit`). The report stage draws section 7 and the
lists of steps that did not work from it. It is coded: no model, nothing read from the audited repository, nothing
written. With `--brief` and at least one gap it also writes `brief.md` in the run folder (a hold: the report is not
written, and the brief says how to go on). The runner starts it after the steps, the validation, and the record, and
saves the report as `data/05-qa.json`. Run on a fixture folder (the grader), it writes nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_shared"))

import facts  # noqa: E402
import gather  # noqa: E402
import hold  # noqa: E402
import stagenote  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Walkdown step 05: the check of the run")
    ap.add_argument("run_dir", help="a run folder (RepoResults/<repo>/<run>) or a fixture run folder")
    ap.add_argument("--brief", action="store_true",
                    help="when the run has a gap, write brief.md in the run folder (a hold)")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        got = facts.load(a.run_dir)
    except facts.NotARun as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    rep = gather.report(got)
    gaps = [f for f in rep["findings"] if f["check"] == gather.GAP]
    if gaps and a.brief:
        hold.write(a.run_dir, gaps, got.stop)
    limits = [f for f in rep["findings"] if f["check"] == gather.LIMIT]
    checked = [f for f in rep["findings"] if f["check"] == gather.CHECKED]
    stagenote.note(f"{len(gaps)} gap{'s' if len(gaps) != 1 else ''}, {len(limits)} limits, {len(checked)} checked")
    sys.stdout.write(json.dumps(rep, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
