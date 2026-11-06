"""Write the specimen run's pages: made-up findings, at least one of every kind the pages know (owner, 2026-11-05, R10). Spec:
specs/specimen.SPEC.md.

    python tools/specimen.py [--out RepoResults/specimen] [--variant NAME ...]

Each variant is a folder of its own (`<out>/<variant>/`) with summary.html, details.html, review.html, full.md, and brief.md,
drawn by the report stage's own writers; `<out>/index.html` lists the variants. Every page says at the top that its findings
are made up. Nothing is audited, no step runs, and no model is called.
"""
from __future__ import annotations

import argparse
import html
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "stages" / "06-report"
for p in (REPORT / "tests", REPORT, ROOT / "stages" / "_shared"):
    sys.path.insert(0, str(p))

import importlib.util  # noqa: E402

import specimen_run as specimen  # noqa: E402  (stages/06-report/tests/specimen_run.py: the made-up run)
import brief  # noqa: E402

# the report stage's run.py, by path: another module is named `run`
_spec = importlib.util.spec_from_file_location("walkdown_report_run", REPORT / "run.py")
report_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(report_run)

BANNER = '<p class="warnline" id="specimen-note"><b>{note}</b> Variant: {variant}. {what} <a href="../index.html">All variants</a></p>'


def write_variant(out: Path, variant: str) -> Path:
    """One variant's folder, written fresh."""
    run_dir = out / variant
    if run_dir.exists():
        shutil.rmtree(run_dir)
    (run_dir / "data").mkdir(parents=True)
    v = specimen.build(variant)
    report_run.write_reports(run_dir, v["meta"], v["reports"], v["stamps"], v["notes"], v["runs_ok"], v["cap_full"], v["changes"])
    brief.write(run_dir, v["meta"], v["reports"], v["stamps"], v["changes"], run_dir / "data")
    banner = BANNER.format(note=html.escape(specimen.NOTE), variant=html.escape(variant),
                           what=html.escape(specimen.VARIANTS[variant]))
    for page in ("summary.html", "details.html", "review.html"):
        p = run_dir / page
        text = p.read_text(encoding="utf-8")
        at = text.index(">", text.index("<body")) + 1  # the first thing on the page (review.html has no <main>)
        p.write_text(text[:at] + "\n" + banner + text[at:], encoding="utf-8")
    for page in ("full.md", "brief.md"):
        p = run_dir / page
        p.write_text(f"> {specimen.NOTE} Variant: {variant}.\n\n" + p.read_text(encoding="utf-8"), encoding="utf-8")
    return run_dir


def index(out: Path, variants) -> Path:
    rows = "".join(f'<li><b><a href="{v}/summary.html">{html.escape(v)}</a></b> '
                   f'(<a href="{v}/details.html">details</a>, <a href="{v}/review.html">review</a>, <a href="{v}/full.md">full.md</a>, '
                   f'<a href="{v}/brief.md">brief</a>): {html.escape(specimen.VARIANTS[v])}</li>' for v in variants)
    page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n<title>Walkdown specimen</title>\n"
            "<style>body{font:17px/1.55 system-ui,sans-serif;max-width:780px;margin:0 auto;padding:28px 16px}"
            "li{margin:10px 0}</style>\n</head>\n<body>\n<h1>Walkdown specimen</h1>\n"
            f"<p>{html.escape(specimen.NOTE)}</p>\n<ul>{rows}</ul>\n</body>\n</html>\n")
    p = out / "index.html"
    p.write_text(page, encoding="utf-8")
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Write the specimen run's pages (made-up findings of every kind)")
    ap.add_argument("--out", default=str(ROOT / "RepoResults" / specimen.NAME), help="the folder to write (default: RepoResults/specimen)")
    ap.add_argument("--variant", action="append", choices=list(specimen.VARIANTS), help="only these variants (default: all)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    variants = a.variant or list(specimen.VARIANTS)
    for v in variants:
        print(write_variant(out, v))
    print(index(out, list(specimen.VARIANTS) if not a.variant else variants))
    return 0


if __name__ == "__main__":
    sys.exit(main())
