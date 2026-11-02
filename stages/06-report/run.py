"""Report stage entry point: from a run folder's data and record, write every report.
Spec: specs/report.SPEC.md, run.

    python stages/06-report/run.py <run folder> [--context N] [--hosts a,b]
    python stages/06-report/run.py --rerender <run folder>      (the same; kept as a synonym)

It reads `data/` (the stage outputs and their notes) and `data/run.json` (the record the runner wrote:
each step's times and result, the validation stamps, the expected context and the target hosts), and
writes LOG.md (once), `data/limits.md`, `summary.html`, `details.html`, `review.html`, `full.md`, `changes.md`
when there is a previous run, and `brief.md`. It runs no stage and calls no model. Giving a run folder that
already has its reports writes them again and appends one line to LOG.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "_shared"))

import brief  # noqa: E402
import details_html  # noqa: E402
import drift  # noqa: E402
import layout  # noqa: E402
import marks  # noqa: E402
import options  # noqa: E402
import pipeline  # noqa: E402
import qaview  # noqa: E402
import record  # noqa: E402
import render  # noqa: E402
import review_html  # noqa: E402
import secretmask  # noqa: E402
import stagelist  # noqa: E402
import summary_html  # noqa: E402
import toolversion  # noqa: E402

ROOT = HERE.parent.parent
INVENTORY = stagelist.CODED[0]


def load(run_dir: Path, rec: dict | None = None, cap_full: dict | None = None):
    """(reports, notes, saved) from the run's data: `reports` {stage: report} for each stage that left
    one (None for an AI stage that was chosen, started, and left none: a step that did not work, shown by
    its notes file or its step in the record; a stage nobody chose is not a key), `notes` {stage: the step's own
    notes, none from a step that failed (`pipeline.own_notes`)}, and `saved` {stage: report} for every stage that left
    one, intake included, since LOG.md's table counts the findings of each. An output that is not a report (it cannot be
    read, or is not a document with a list of findings) is none of them: the check of the run applies the same test
    (`pipeline.read_report`). The AI step a stop made write its input file (the record's `prepared`) is none of these: it
    did not run, and its notes stay in the file. A saved output can still quote a line the secret scan flagged (a run stopped
    before the runner masked it, or made before it did), so all of them are masked here, in memory, for every report at once,
    and `cap_full`, the capability step's side file, with them."""
    data = layout.data_dir(run_dir)
    reports, notes, saved = {}, {}, {}
    started = {s["stage"] for s in (rec or {}).get("steps", [])}
    finished = {s["stage"] for s in (rec or {}).get("steps", []) if s["ok"]} if rec else None  # no record: all of them
    prepared = ((rec or {}).get("prepared") or {}).get("stage")
    for stage in stagelist.STAGES:
        f = data / f"{stage}.json"
        if f.is_file():
            try:
                saved[stage] = pipeline.read_report(f)
            except (OSError, ValueError):  # an output that is not a report is a gap the check of the run named
                pass
        if stage == stagelist.INTAKE:  # intake has no section in any report
            continue
        if stage == prepared:  # it wrote its input file and stopped (--until): it did not run, and nothing failed
            continue
        if stage in saved:
            reports[stage] = saved[stage]
        nf = data / f"{stage}.notes.txt"
        if nf.is_file():
            notes[stage] = pipeline.own_notes(nf.read_text(encoding="utf-8", errors="replace"),
                                              finished is None or stage in finished)
        if stage in stagelist.AI_STAGES and stage not in reports and (nf.is_file() or stage in started):
            reports[stage] = None  # chosen and started, and left no report: a step that did not work
    secretmask.mask_reports(reports, *([cap_full] if cap_full else []))
    return reports, notes, saved


def write_reports(run_dir, meta, reports, stamps, notes, runs_ok, cap_full, changes):
    """summary.html, details.html, review.html, full.md. The pages read the reader's marks: the
    marks.json saved beside them (2026-10-12), or else the newest earlier run's, carried by stable
    key (marks.py; owner, 2026-10-20). The pages a run no longer writes (summary.md, summary-v1.html;
    owner, 2026-10-20) are removed, so a re-rendered older run keeps no stale copy. `changes` is the
    one comparison with the previous run (`drift.changes`), which the pages and the brief share."""
    out = layout.report_dir(run_dir)
    out.mkdir(exist_ok=True)
    for name in layout.RETIRED:
        (out / name).unlink(missing_ok=True)
    text_dir = layout.data_dir(run_dir) / "normalized" / "text"
    text_href = os.path.relpath(text_dir, out).replace(os.sep, "/")
    m = marks.for_run(run_dir)
    (out / "summary.html").write_text(
        summary_html.render_page(meta, reports, stamps, notes, runs_ok, m["data"], changes), encoding="utf-8")
    (out / "details.html").write_text(
        details_html.render_page(meta, reports, stamps, notes, runs_ok, changes, m["data"]),
        encoding="utf-8")
    (out / "full.md").write_text(render.full(meta, reports, stamps, notes, runs_ok, cap_full),
                                 encoding="utf-8")
    (out / "review.html").write_text(
        review_html.render_page(meta, reports, text_dir, text_href, m["data"], m["error"], m["carried"],
                                cap_full), encoding="utf-8")


def report(run_dir: Path, a) -> int:
    """Write every report for a finished run. Exit 2 for a folder that is not a run or was made before
    this version (`record.made_before`: no record, or a record of an older format, whose data inside the
    run has another shape; audit the repository again)."""
    data = layout.data_dir(run_dir)
    if not run_dir.is_dir() or not ((run_dir / "LOG.md").is_file() or data.is_dir()):
        print(f"error: not a run folder (no LOG.md): {run_dir}", file=sys.stderr)
        return 2
    if record.made_before(run_dir):
        print("error: this run was made before this version of Walkdown, so it is not re-rendered; "
              "audit the repository again.", file=sys.stderr)
        return 2
    rec = record.read(run_dir)
    held = record.held_of(rec)
    if held is not None and not a.released_at:  # the check of the run holds it: `continue` releases it, then writes the report
        folder = f'"{run_dir}"' if " " in str(run_dir) else str(run_dir)
        print(f"error: this run is held by the check of the run, so no report is written; "
              f"python walkdown.py continue {folder}", file=sys.stderr)
        return 2
    try:  # the capability step's side file, with every citation; one that is not a report (cut off by a full disk) is none
        cap_full = pipeline.read_report(data / "capability.json")
    except (OSError, ValueError):
        cap_full = None
    reports, notes, saved = load(run_dir, rec, cap_full)
    runs_ok = {s for s, rep in reports.items() if rep is not None}
    stamps = record.stamps_of(rec)
    pin = ((reports.get(INVENTORY) or {}).get("findings") or [{}])[0]
    names = run_dir.resolve()
    meta = {"repo": names.parent.name, "run": names.name, "date": names.name.split("_")[0],
            "source": pin.get("source", ""), "hash": pin.get("hash") or "nohash",
            "hash_kind": pin.get("hash_kind", "?"), "channel": pin.get("channel", "directory"),
            "tool": toolversion.tool_version(ROOT),
            "context": a.context or rec.get("context") or options.DEFAULT_CONTEXT,
            "hosts": a.hosts if a.hosts is not None else rec.get("hosts") or [],
            "finished": rec.get("finished"),
            "stop": record.stop_of(rec),  # None for a run that went through; else where it stopped (O3)
            "continued": rec.get("continued") or [],
            "not_started": rec.get("not_started") or [],  # a chosen model read that was not started (M9)
            "chosen": rec.get("chosen") or [],  # the model reads this run chose (M9 slice B)
            "dropped": rec.get("dropped") or [],  # the reads an earlier command chose and `continue` left out
            "backends": rec.get("backends") or {}}
    try:
        meta["qa"] = qaview.Qa.read(data)  # section 7 and the lists of steps that did not work come from the check of the run
    except qaview.NoCheck as exc:
        print(f"error: {exc}; the check of the run (data/05-qa.json) has not been made for this run: audit the "
              "repository again", file=sys.stderr)
        return 2
    meta["qa_run"] = rec.get("qa")  # when the check ran, for LOG.md's row
    # a hold that `continue` released, for LOG.md's lines; while it is being released the record still says held (the runner
    # records the release once the report is written), and the time comes from the runner
    meta["released"] = {**held, "at": a.released_at} if held is not None else rec.get("released")

    first = not (run_dir / "LOG.md").is_file()
    if first:  # the record of the run, as a table; a re-render keeps the one it has
        steps = [pipeline.StageRun(s["stage"], s["ok"], s["started"] or "", s["finished"],
                                   saved.get(s["stage"]), [], s["error"]) for s in rec.get("steps", [])]
        (run_dir / "LOG.md").write_text(render.log(meta, steps, stamps, reports), encoding="utf-8")
    (data / layout.LIMITS).write_text(render.limits_doc(meta), encoding="utf-8")
    changes = drift.changes(run_dir)  # once: it writes changes.md
    write_reports(run_dir, meta, reports, stamps, notes, runs_ok, cap_full, changes)
    brief.write(run_dir, meta, reports, stamps, changes, data)
    if not first:
        now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        with open(run_dir / "LOG.md", "a", encoding="utf-8") as fh:
            fh.write(f"- Report re-rendered {now} by Walkdown {meta['tool']} from this run's saved "
                     "stage outputs (no stage re-run).\n")
    print(str(run_dir))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Walkdown report stage: from a run folder's data and record, "
                                             "write LOG.md, the limits, the pages, full.md, and the brief")
    ap.add_argument("run_dir", nargs="?", help="a run folder (RepoResults/<repo>/<run>)")
    ap.add_argument("--rerender", metavar="RUN_DIR", help="the same as giving the run folder")
    options.add_report_options(ap)
    ap.add_argument("--released-at", metavar="TIME", default=None, help=argparse.SUPPRESS)  # the runner's: it is releasing a hold
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    given = a.rerender or a.run_dir
    if not given:
        ap.error("give a run folder")
    error = options.check(a)
    if error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return report(Path(given), a)


if __name__ == "__main__":
    sys.exit(main())
