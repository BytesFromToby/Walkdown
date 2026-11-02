"""Where things live in a run folder. Spec: specs/shared.SPEC.md, layout.

A run folder puts what people read at the top and everything else under data/:

    RepoResults/<repo>/<date>_<hash7>/
      summary.html  details.html  review.html  full.md  brief.md  LOG.md   (marks.json once the reader saves it)
      changes.md            what changed since the previous run, when there is one
      data/   stage outputs (NN-name.json, notes), run.json (the record), limits.md, capability.json,
              graph.json, the AI stages' input, answers, and call log, normalized/ copies

There is one layout. A run made before this version (the layout before 2026-10-02, or the stage names
before restructure step 1, or no record, or a record of an older format) is not read: `record.made_before`
says so (it is the record's to say, since the record's format says what shape the data inside the run has),
and the report stage tells the person to audit again (restructure step 7, notes O5 and M3; step 7b).
"""
from __future__ import annotations

from pathlib import Path

DATA = "data"
RECORD = "run.json"  # how the run went: each step's times and result, the validation stamps, the options
LIMITS = "limits.md"  # the report stage's gathering of what the run did not examine
BRIEF = "brief.md"
CHANGES = "changes.md"  # what changed since the previous run: the report stage's, when there is a previous run
REPORTS = ("summary.html", "details.html", "review.html", "full.md")
# written by runs before 2026-10-20 (owner: cut); a re-render removes them
RETIRED = ("summary.md", "summary-v1.html")


def input_file(stage: str) -> str:
    """What an AI step would send, written before it sends anything (and by itself with `--input-only`)."""
    return f"{stage}.input.jsonl"


def calls_file(stage: str) -> str:
    """The call log of an AI step: one line for each passage whose call got no answer on the first try or was
    not sent. Written only when there is a line to write."""
    return f"{stage}.calls.jsonl"


def data_dir(run_dir) -> Path:
    """Stage outputs and working files."""
    return Path(run_dir) / DATA


def report_dir(run_dir) -> Path:
    """The reports: the run folder itself."""
    return Path(run_dir)
