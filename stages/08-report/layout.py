"""Where things live in a run folder. Spec: specs/layout.SPEC.md.

Since 2026-10-02 a run folder puts what people read at the top and everything else under
data/:

    RepoResults/<repo>/<date>_<hash7>/
      summary.html  summary.md  full.md  LOG.md
      data/   stage outputs (0N-*.json, notes), capability.json, graph.json, 07-limits.md,
              stage 6 packet and answers, normalized/ copies

Runs made before then keep the old layout (stage outputs at the top, reports under report/);
every reader here handles both.
"""
from __future__ import annotations

from pathlib import Path

DATA = "data"
REPORTS = ("summary.html", "summary.md", "full.md")


def is_new(run_dir) -> bool:
    return (Path(run_dir) / DATA).is_dir()


def data_dir(run_dir) -> Path:
    """Stage outputs: data/ in the current layout, the run folder itself in the old one."""
    run_dir = Path(run_dir)
    return run_dir / DATA if is_new(run_dir) else run_dir


def report_dir(run_dir) -> Path:
    """The reports: the run folder itself in the current layout, report/ in the old one."""
    run_dir = Path(run_dir)
    return run_dir if is_new(run_dir) else run_dir / "report"
