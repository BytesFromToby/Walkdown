"""Walkdown: audit the instruction layer of an AI skill or agent repository.

    python walkdown.py <path or git URL> [--name NAME] [--fresh]
                       [--label jev|laya|claude-cli] [--compare ...] [--relational claude-cli]
                       [--sweep jev] [--both]

A git URL is cloned (shallow) into ReposToExamine/<name>; a path is audited where it is. The
run lands in RepoResults/<name>/<date>_<hash7>/, and the last thing printed is a brief:
counts, trifecta legs, validation stamps, and the path to the report. The brief is written
by Walkdown itself and quotes nothing from the audited repository, so it is safe to hand to
a chat assistant (see specs/walkdown.SPEC.md). Spec: specs/walkdown.SPEC.md.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE8 = ROOT / "stages" / "08-report"
EXAMINE = ROOT / "ReposToExamine"
URL = re.compile(r"^(https?://|git@|ssh://)|\.git$")
NAME_OK = re.compile(r"[^A-Za-z0-9._-]+")
STAGE_NAMES = {"01-inventory": "What ships", "02-reader": "What the model actually reads",
               "03-graph": "What loads what", "04-phrases": "What the text asks for",
               "05-capability": "What this touches", "06-soft": "Needs a human read"}


def is_url(target: str) -> bool:
    """A git URL, unless a folder by that name exists (a local bare `x.git` folder)."""
    return bool(URL.search(target.strip())) and not Path(target).is_dir()


QUOTED = re.compile(r"“[^”]*”|\"[^\"]*\"")


def own_words(title: str) -> str:
    """A summary headline with any quoted word from the audited repository removed."""
    if title.startswith("The word "):
        return "A word is defined more than one way"
    if title.startswith("Redefines the safety word"):
        return "Redefines a safety word"
    return QUOTED.sub("a word", title)


def repo_name(target: str) -> str:
    """The last path part, without .git, made safe for a folder name."""
    last = target.strip().rstrip("/\\").replace("\\", "/").rsplit("/", 1)[-1]
    last = last.rsplit(":", 1)[-1]
    if last.endswith(".git"):
        last = last[:-4]
    return NAME_OK.sub("-", last).strip("-.") or "repo"


def python_exe() -> str:
    """The project virtualenv's python when there is one, else this interpreter."""
    for p in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python"):
        if p.is_file():
            return str(p)
    return sys.executable


def fetch(url: str, name: str, fresh: bool) -> Path:
    dest = EXAMINE / name
    if dest.exists():
        if not fresh:
            print(f"note: using the existing copy in {dest} (pass --fresh to clone again)",
                  file=sys.stderr)
            return dest
        shutil.rmtree(dest)
    EXAMINE.mkdir(exist_ok=True)
    # --no-checkout of hooks is git's default; nothing from the clone is ever run
    proc = subprocess.run(["git", "clone", "--depth", "1", "--", url, str(dest)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {proc.stderr.strip()[-300:]}")
    return dest


def stamps(log_text: str) -> dict:
    """{stage: stamp word} from LOG.md's table."""
    out = {}
    for line in log_text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[0] in STAGE_NAMES:
            out[cells[0]] = (cells[5].split() or ["not run"])[0]
    return out


def brief(run_dir: Path) -> str:
    """A plain summary of a finished run, from Walkdown's own words only: no quote, file name,
    or other text from the audited repository."""
    sys.path.insert(0, str(STAGE8))
    import layout  # noqa: E402
    import render as R  # noqa: E402
    import summary_html  # noqa: E402
    reports = {}
    data, out = layout.data_dir(run_dir), layout.report_dir(run_dir)
    for stage in STAGE_NAMES:
        f = data / f"{stage}.json"
        if f.is_file():
            reports[stage] = json.loads(f.read_text(encoding="utf-8"))
    st = stamps((run_dir / "LOG.md").read_text(encoding="utf-8"))
    legs = {x["leg"]: x["present"] for x in R.fnd(reports, "05-capability", "cap.leg")}
    grants = [x["grant"] for x in R.fnd(reports, "05-capability", "cap.grant")]
    items = summary_html.first_items(reports)
    by_title = collections.Counter((it["stage"], own_words(it["title"])) for it in items)
    pin = (R.fnd(reports, "01-inventory", "inv.pin") or [{}])[0]
    L = [f"Walkdown brief: {run_dir.parent.name}",
         f"Files examined: {pin.get('files', '?')}. Pinned: {pin.get('hash_kind', '?')} "
         f"{str(pin.get('hash', '?'))[:12]}.", "",
         "What it can do (capability only; there is no verdict):"]
    for k, name in R.LEG_NAMES.items():
        L.append(f"  [{'x' if legs.get(k) else ' '}] {name}")
    L.append(f"  Install grants: {', '.join(grants) if grants else 'none'}.")
    L += ["", f"Look at these first: {len(items)} item(s)."]
    L += [f"  stage {s}: {t} ({n})" for (s, t), n in sorted(by_title.items())] or ["  none"]
    L += ["", "Validation (each stage against its fixtures):"]
    L += [f"  {stage} {STAGE_NAMES[stage]}: {st.get(stage, 'not run')}" for stage in STAGE_NAMES]
    L += ["", f"Report: {out / 'summary.html'}",
          f"Every finding with file and line: {out / 'full.md'}", "",
          'No verdict and no score. "Nothing found" means these stages found nothing; it does '
          "not mean the repository is safe."]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="walkdown.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("target", help="a folder, or a git URL to clone into ReposToExamine/")
    ap.add_argument("--name", help="name for the run folder (default: the repository's name)")
    ap.add_argument("--fresh", action="store_true", help="clone again even if a copy exists")
    for k in ("label", "compare", "relational", "sweep"):
        ap.add_argument(f"--{k}")
    ap.add_argument("--both", action="store_true")
    a = ap.parse_args(argv)

    name = a.name or repo_name(a.target)
    try:
        target = fetch(a.target, name, a.fresh) if is_url(a.target) else Path(a.target)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"error: not a folder or a git URL: {a.target}", file=sys.stderr)
        return 2
    cmd = [python_exe(), str(STAGE8 / "run.py"), str(target), "--repo", name]
    for k in ("label", "compare", "relational", "sweep"):
        if getattr(a, k):
            cmd += [f"--{k}", getattr(a, k)]
    if a.both:
        cmd.append("--both")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, encoding="utf-8", cwd=ROOT)
    lines = [x for x in proc.stdout.splitlines() if x.strip()]
    run_dir = Path(lines[-1]) if lines else None
    if run_dir is None or not (run_dir / "LOG.md").is_file():
        print("error: the run did not finish; see the messages above", file=sys.stderr)
        return proc.returncode or 1
    print(brief(run_dir))
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
