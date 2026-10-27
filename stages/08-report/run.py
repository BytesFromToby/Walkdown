"""Stage 8 entry point: run stages 1 to 6, stamp them, write the run folder. Spec: specs/run.SPEC.md."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import layout  # noqa: E402
import marks  # noqa: E402
import pipeline  # noqa: E402
import render  # noqa: E402
import review_html  # noqa: E402
import details_html  # noqa: E402
import summary_html  # noqa: E402
import validate  # noqa: E402

ROOT = HERE.parent.parent


def tool_version(root: Path) -> str:
    """'0.1.0 (a5bf24e)': the VERSION file and the git commit; '+modified' when tracked files
    have uncommitted changes, so a report always names the exact code that made it. Without
    git (a downloaded zip) the version alone (2026-10-04)."""
    try:
        version = (Path(root) / "VERSION").read_text(encoding="utf-8").strip() or "unversioned"
    except OSError:
        version = "unversioned"
    try:
        head = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=20).stdout.strip()
        dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain",
                                "--untracked-files=no"],
                               capture_output=True, text=True, timeout=20).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        head, dirty = "", ""
    if not head:
        return version
    return f"{version} ({head}{'+modified' if dirty else ''})"


def free_name(parent: Path, base: str) -> Path:
    p, i = parent / base, 2
    while p.exists():
        p, i = parent / f"{base}-{i}", i + 1
    return p


def inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Walkdown stage 8: run stages 1 to 6 and write the reports")
    ap.add_argument("input_dir", nargs="?")
    ap.add_argument("--repo", help="name for RepoResults/<repo>/ (required unless --rerender)")
    ap.add_argument("--rerender", metavar="RUN_DIR",
                    help="rebuild the reports from a finished run's saved stage outputs; runs no stage")
    ap.add_argument("--results", default=str(ROOT / "RepoResults"))
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--no-validate", action="store_true", help="skip the grader (tests only)")
    ap.add_argument("--revalidate", action="store_true",
                    help="run the grader even when a stamp for the same code and fixtures is cached")
    for k in ("label", "compare", "relational"):
        ap.add_argument(f"--{k}", default=None,
                        help=f"stage 6 {k} backend (none, jev, laya, claude-cli); default: stage 6's")
    ap.add_argument("--sweep", default=None,
                    help="stage 6 coverage sweep backend (none, jev); default: stage 6's")
    ap.add_argument("--pinpoint", default=None,
                    help="stage 6: a second read names the line behind each sweep flag (none, claude-cli)")
    ap.add_argument("--both", action="store_true",
                    help="stage 6: Jev reads each line twice (plain and marked) and averages")
    ap.add_argument("--context", default=None,
                    help="expected context in tokens, such as 32k, 200k, or 8192 (default 32k); "
                         "a re-render keeps the run's own unless this is given")
    ap.add_argument("--hosts", default=None,
                    help="the AI hosts you build for, comma-separated (claude, codex, gemini, cursor, "
                         "copilot, windsurf, agents-md); the report lists what each is missing; "
                         "a re-render keeps the run's own unless this is given")
    a = ap.parse_args(argv)
    if a.hosts is not None:
        try:
            a.hosts = render.parse_hosts(a.hosts)
        except ValueError as exc:
            print(f"error: --hosts: {exc} (names: {', '.join(render.HOST_KEYS)})", file=sys.stderr)
            return 2
    if a.context is not None:
        try:
            a.context = render.parse_context(a.context)
        except ValueError:
            print(f"error: --context {a.context!r} is not a token count (try 32k, 200k, or 8192)",
                  file=sys.stderr)
            return 2
    if a.rerender:
        return rerender(Path(a.rerender), a)
    if not a.input_dir or not a.repo:
        ap.error("input_dir and --repo are required unless --rerender is given")

    inp = Path(a.input_dir)
    if not inp.is_dir():
        print(f"error: not a folder: {inp}", file=sys.stderr)
        return 2
    repo_dir = Path(a.results) / a.repo
    if inside(repo_dir, inp):
        print("error: the run folder would be inside the input", file=sys.stderr)
        return 2
    repo_dir.mkdir(parents=True, exist_ok=True)
    work = free_name(repo_dir, f".running-{a.date}")
    work.mkdir()

    py = sys.executable
    soft = {"label": a.label, "compare": a.compare, "relational": a.relational, "both": a.both,
            "sweep": a.sweep, "pinpoint": a.pinpoint}
    (work / layout.DATA).mkdir()
    runs = pipeline.run_stages(inp, work / layout.DATA, ROOT / "stages", py, soft)
    reports = {r.stage: r.report for r in runs if r.ok}
    notes = {r.stage: r.notes for r in runs}
    runs_ok = set(reports)

    pin = (reports.get("01-inventory") or {}).get("findings", [{}])[0]
    h = pin.get("hash") or "nohash"
    run_dir = free_name(repo_dir, f"{a.date}_{h[:7]}" if "01-inventory" in reports else f"{a.date}_failed")
    work.rename(run_dir)

    grade_env = soft_grade_env(a)
    stamps = {} if a.no_validate else validate.stamps(ROOT, py, pipeline.STAGES, grade_env,
                                                      cache=not a.revalidate)
    meta = {"repo": a.repo, "run": run_dir.name, "date": a.date, "source": pin.get("source", str(inp)),
            "hash": h, "hash_kind": pin.get("hash_kind", "?"), "channel": pin.get("channel", "directory"),
            "tool": tool_version(ROOT), "context": a.context or render.DEFAULT_CONTEXT,
            "hosts": a.hosts or [],
            "finished": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()}
    data = layout.data_dir(run_dir)
    cap_path = data / "capability.json"
    cap_full = json.loads(cap_path.read_text(encoding="utf-8")) if cap_path.exists() else None

    (run_dir / "LOG.md").write_text(render.log(meta, runs, stamps, reports), encoding="utf-8")
    (data / "07-limits.md").write_text(render.limits_doc(meta, reports, notes, stamps, runs_ok),
                                       encoding="utf-8")
    write_reports(run_dir, meta, reports, stamps, notes, runs_ok, cap_full)

    print(str(run_dir))
    failed = [r for r in runs if not r.ok]
    if failed:
        print(f"stage {failed[0].stage} failed: {failed[0].error}", file=sys.stderr)
        return 1
    return 0


def write_reports(run_dir, meta, reports, stamps, notes, runs_ok, cap_full):
    """summary.html, details.html, review.html, full.md where this run's layout keeps them (layout.py).
    The pages read the reader's marks: the marks.json saved beside them (2026-10-12), or else the
    newest earlier run's, carried by stable key (marks.py; owner, 2026-10-20). The pages a run
    no longer writes (summary.md, summary-v1.html; owner, 2026-10-20) are removed, so a
    re-rendered older run keeps no stale copy."""
    out = layout.report_dir(run_dir)
    out.mkdir(exist_ok=True)
    for name in layout.RETIRED:
        (out / name).unlink(missing_ok=True)
    text_dir = layout.data_dir(run_dir) / "normalized" / "text"
    text_href = os.path.relpath(text_dir, out).replace(os.sep, "/")
    m = marks.for_run(run_dir)
    ch = changes_for(run_dir)  # once: it writes changes.md
    (out / "summary.html").write_text(
        summary_html.render_page(meta, reports, stamps, notes, runs_ok, m["data"], ch), encoding="utf-8")
    (out / "details.html").write_text(
        details_html.render_page(meta, reports, stamps, notes, runs_ok, ch,
                                 cap_full, text_href, m["data"], m["carried"]),
        encoding="utf-8")
    (out / "full.md").write_text(render.full(meta, reports, stamps, notes, runs_ok, cap_full),
                                 encoding="utf-8")
    (out / "review.html").write_text(
        review_html.render_page(meta, reports, text_dir, os.path.relpath(text_dir, out).replace(os.sep, "/"),
                                m["data"], m["error"], m["carried"], cap_full), encoding="utf-8")


def changes_for(run_dir) -> dict | None:
    """What changed since the newest earlier run of the same repository, for the summary page
    (report v2, 2026-10-16). Earlier = a sibling run folder whose name sorts before this one
    (names start with the date), so re-rendering an old run never compares it with a newer one.
    None on a first run or when drift fails; `same` when the version is the same, `differs` when
    anything recorded differs (with the same version, that is Walkdown's own change; review C22 b).
    Writes changes.md beside the reports so the page can link it; the page shows counts and
    Walkdown's own words only (drift.summary_lines)."""
    try:
        import drift
        run_dir = Path(run_dir).resolve()
        earlier = sorted(p for p in run_dir.parent.iterdir()
                         if p.is_dir() and p.name < run_dir.name and (p / "LOG.md").is_file())
        if not earlier:
            return None
        prev = earlier[-1]
        s = drift.since(prev, run_dir)
        return {"since": prev.name, "same": s["same"], "differs": s["differs"], "lines": s["lines"],
                "on_disk": s.get("on_disk", 0), "cost_line": s.get("cost_line")}
    except Exception:  # drift is extra; it never fails a report
        return None


def soft_grade_env(a) -> dict:
    """The stage 6 choices the grader's stamp runs with, so it tests what the run used."""
    env = {"WALKDOWN_SOFT_LABEL": a.label} if a.label else {}
    if getattr(a, "both", False):
        env["WALKDOWN_SOFT_BOTH"] = "1"
    if getattr(a, "sweep", None):
        env["WALKDOWN_SOFT_SWEEP"] = a.sweep
    return env


def rerender(run_dir: Path, a) -> int:
    """Rebuild the reports (layout.REPORTS) from the stage outputs a finished run
    saved. Runs no stage and calls no model; re-stamps with the grader unless --no-validate;
    appends one line to LOG.md saying when and with which Walkdown version (2026-09-30)."""
    if not (run_dir / "LOG.md").is_file():
        print(f"error: not a run folder (no LOG.md): {run_dir}", file=sys.stderr)
        return 2
    reports, notes = {}, {}
    data = layout.data_dir(run_dir)
    for stage in pipeline.STAGES:
        f = data / f"{stage}.json"
        if f.is_file():
            reports[stage] = json.loads(f.read_text(encoding="utf-8"))
        nf = data / f"{stage}.notes.txt"
        if nf.is_file():
            notes[stage] = pipeline.note_lines(nf.read_text(encoding="utf-8"))
    if "01-inventory" not in reports:
        print("error: the run has no 01-inventory.json", file=sys.stderr)
        return 2
    runs_ok = set(reports)
    pin = reports["01-inventory"]["findings"][0]
    grade_env = soft_grade_env(a)
    stamps = {} if a.no_validate else validate.stamps(ROOT, sys.executable,
                                                      [s for s in pipeline.STAGES if s in reports], grade_env,
                                                      cache=not a.revalidate)
    repo = run_dir.parent.name
    meta = {"repo": repo, "run": run_dir.name, "date": run_dir.name.split("_")[0],
            "source": pin.get("source", ""), "hash": pin.get("hash", "nohash"),
            "hash_kind": pin.get("hash_kind", "?"), "tool": tool_version(ROOT),
            "context": a.context or render.context_of((run_dir / "LOG.md").read_text(encoding="utf-8"))
            or render.DEFAULT_CONTEXT,
            "hosts": a.hosts if a.hosts is not None
            else render.hosts_of((run_dir / "LOG.md").read_text(encoding="utf-8"))}
    cap_path = data / "capability.json"
    cap_full = json.loads(cap_path.read_text(encoding="utf-8")) if cap_path.exists() else None
    write_reports(run_dir, meta, reports, stamps, notes, runs_ok, cap_full)
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    with open(run_dir / "LOG.md", "a", encoding="utf-8") as fh:
        fh.write(f"- Report re-rendered {now} by Walkdown {meta['tool']} from this run's saved "
                 "stage outputs (no stage re-run).\n")
    print(str(run_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
