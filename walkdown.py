"""Walkdown: audit the instruction layer of an AI skill or agent repository.

    python walkdown.py <path or git URL> [--name NAME] [--fresh | --keep] [--revalidate]
                       [--label jev|claude-cli] [--compare ...] [--relational claude-cli]
                       [--sweep jev] [--pinpoint claude-cli] [--both]
    python walkdown.py diff <old run folder> <new run folder>

(`laya` is still accepted by --label and --compare; it is retired, 2026-10-03.)

A git URL is cloned (shallow) into ReposToExamine/<name>, or an earlier clone of it updated
to the latest commit; a GitHub folder link (.../tree/<branch>/<path>) clones the repository
at that branch and audits the folder; a path is audited where it is. The
run lands in RepoResults/<name>/<date>_<hash7>/, and the last thing printed is a brief:
counts, trifecta legs, whether a step failed its fixture checks, and the path to the report. The brief is written
by Walkdown itself and quotes nothing from the audited repository, so it is safe to hand to
a chat assistant (see specs/walkdown.SPEC.md). Spec: specs/walkdown.SPEC.md.
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

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


GITHUB_LINK = re.compile(r"^https?://(?:www\.)?github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?"
                         r"/(tree|blob)/([^/\s]+)(?:/(.*?))?/?$")


def github_link(target: str) -> tuple[str, str, str] | None:
    """(repository URL, ref, folder inside it) for a GitHub folder link, None for anything else
    (2026-10-25, review C41). The first part after /tree/ is the branch or tag. A file link
    (/blob/) is a ValueError: Walkdown audits a folder."""
    m = GITHUB_LINK.match(target.strip())
    if not m:
        return None
    owner, repo, kind, ref, sub = m.groups()
    if kind == "blob":
        raise ValueError(f"{target} links to one file; give the folder that holds it "
                         "(a /tree/ link) or the repository")
    return f"https://github.com/{owner}/{repo}", unquote(ref), unquote(sub or "").strip("/")


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


# The import names of requirements.txt's packages, less pytest: what every stage needs to run.
CORE_MODULES = ("yaml", "charset_normalizer", "pdfminer", "pypdf", "pypdfium2", "bs4", "lxml",
                "PIL", "regex", "confusable_homoglyphs", "detect_secrets")
MISSING = ("import importlib.util, sys; "
           "print(' '.join(m for m in sys.argv[1:] if importlib.util.find_spec(m) is None))")


def missing_modules(python: str) -> list[str] | None:
    """The core modules `python` cannot import; None when it does not run at all."""
    if Path(python).resolve() == Path(sys.executable).resolve():
        return [m for m in CORE_MODULES if importlib.util.find_spec(m) is None]
    try:
        p = subprocess.run([python, "-c", MISSING, *CORE_MODULES], capture_output=True, text=True,
                           timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout.split() if p.returncode == 0 else None


def python_exe() -> tuple[str, list[str]]:
    """The interpreter that runs the stages, and what it lacks: the one Walkdown was started
    with when it has every core module, else the project virtualenv's when that has them
    (2026-10-21, an outside tester: an empty .venv in the Walkdown folder was preferred over the
    working python they ran, and every stage failed). With neither, this interpreter and what
    it lacks."""
    here = missing_modules(sys.executable) or []
    if not here:
        return sys.executable, []
    for p in (ROOT / ".venv" / "Scripts" / "python.exe", ROOT / ".venv" / "bin" / "python"):
        if p.is_file() and missing_modules(str(p)) == []:
            return str(p), []
    return sys.executable, here


GIT_OPTS = ("-c", "core.longpaths=true")  # Windows paths past 260 characters (review C41)
GIT_TIMEOUT = 600
LOGIN = ("repository not found", "could not read username", "terminal prompts disabled",
         "authentication failed", "permission denied (publickey)", "could not read from remote")


def _git_run(*args) -> subprocess.CompletedProcess:
    """git with no prompts, long paths, and a time limit (2026-10-25, review C41: a private or
    mistyped URL could wait for a login that never comes)."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    env.setdefault("GIT_SSH_COMMAND", "ssh -o BatchMode=yes")
    try:
        return subprocess.run(["git", *GIT_OPTS, *args], capture_output=True, text=True, env=env,
                              timeout=GIT_TIMEOUT)
    except FileNotFoundError:
        raise RuntimeError("git is not installed; install it to audit a URL, or download the "
                           "repository and give its folder") from None
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"git took longer than {GIT_TIMEOUT // 60} minutes and was stopped") from None


def _why(stderr: str) -> str:
    """git's failure in plain words where it is a common one, else its last lines."""
    s = stderr.lower()
    if any(x in s for x in LOGIN):
        return "the repository was not found, or it needs a login (Walkdown never asks for one)"
    if "remote branch" in s and "not found" in s:
        return "that branch or tag is not in the repository"
    return stderr.strip()[-300:]


def _git(dest: Path, *args) -> subprocess.CompletedProcess:
    return _git_run("-C", str(dest), *args)


def _origin(dest: Path) -> str | None:
    p = _git(dest, "remote", "get-url", "origin")
    return p.stdout.strip() if p.returncode == 0 else None


def _same_url(a: str | None, b: str) -> bool:
    norm = lambda u: (u or "").strip().rstrip("/").removesuffix(".git").lower()  # noqa: E731
    return norm(a) == norm(b)


def fetch(url: str, name: str, fresh: bool, keep: bool = False, ref: str | None = None) -> Path:
    """A shallow clone of `url` in ReposToExamine/<name>, at the remote's latest commit (of
    `ref` when given). An existing clone of the same URL is updated (2026-10-03 review A7:
    re-running on a URL used to audit the old copy silently); --keep audits it as it is;
    --fresh clones again. A folder there that is not a clone of this URL is never touched."""
    dest = EXAMINE / name
    if dest.exists():
        same = (dest / ".git").exists() and _same_url(_origin(dest), url)
        if keep:
            print(f"note: --keep: auditing the existing copy in {dest} as it is", file=sys.stderr)
            return dest
        if not same:
            raise RuntimeError(f"{dest} exists and is not a clone of {url}; pass --name to use "
                               "another folder, or --keep to audit what is there")
        if not fresh:
            for args in (("fetch", "--depth", "1", "origin", *([ref] if ref else [])),
                         ("reset", "--hard", "FETCH_HEAD"), ("clean", "-fdx")):
                p = _git(dest, *args)
                if p.returncode != 0:
                    raise RuntimeError(f"updating {dest} failed at git {args[0]}: {_why(p.stderr)}")
            print(f"note: updated the existing clone in {dest} to the latest commit",
                  file=sys.stderr)
            return dest
        shutil.rmtree(dest)
    EXAMINE.mkdir(exist_ok=True)
    # --no-checkout of hooks is git's default; nothing from the clone is ever run
    proc = _git_run("clone", "--depth", "1", *(["--branch", ref] if ref else []), "--", url, str(dest))
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {_why(proc.stderr)}")
    return dest


def stamps(log_text: str) -> dict:
    """{stage: stamp word} from LOG.md's table."""
    out = {}
    for line in log_text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and cells[0] in STAGE_NAMES:
            out[cells[0]] = (cells[5].split() or ["not run"])[0]
    return out


ERROR_LINE = re.compile(r"^(\w+(?:Error|Exception|Exit))\b(?::\s*(No module named '[\w.]+'))?")


def stage_error(data: Path, stage: str) -> str:
    """Why a stage produced no output, in Walkdown's words: the error's type, and the module for
    a missing import, never the rest of its message (it can carry a path from the audited
    repository)."""
    try:
        lines = (data / f"{stage}.notes.txt").read_text(encoding="utf-8").splitlines()
    except OSError:
        return f"{STAGE_NAMES[stage]}: no output and no error recorded; see LOG.md."
    for line in reversed(lines):
        m = ERROR_LINE.match(line.strip())
        if m:
            return f"{STAGE_NAMES[stage]} stopped with {m.group(1)}" + (f" ({m.group(2)})." if m.group(2) else ".")
    return f"{STAGE_NAMES[stage]}: no output; its messages are in data/{stage}.notes.txt."


def brief(run_dir: Path) -> str:
    """A plain summary of a finished run, from Walkdown's own words only: no quote, file name,
    or other text from the audited repository. It uses summary.html's terms: the same headline,
    concern kinds, wording-only line, and footer (owner, 2026-10-21)."""
    sys.path.insert(0, str(STAGE8))
    import layout  # noqa: E402
    import render as R  # noqa: E402
    import details_html  # noqa: E402
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
    every = details_html.first_items(reports)
    items = [it for it in every if it["stage"] != 6]
    model = [it for it in every if it["stage"] == 6]
    by_model = collections.Counter(own_words(it["title"]) for it in model)
    pin = (R.fnd(reports, "01-inventory", "inv.pin") or [{}])[0]
    log = (run_dir / "LOG.md").read_text(encoding="utf-8")
    ctx = R.context_of(log) or R.DEFAULT_CONTEXT
    cost = summary_html.brief_cost_lines(reports, ctx)  # slice 1: counts only (2026-10-26)
    need = summary_html.brief_needs_line(reports)  # slice 2
    cost += [need] if need else []
    ready = summary_html.brief_ready_line(reports, R.hosts_of(log))  # slice 3
    cost += [ready] if ready else []
    fits = summary_html.brief_fit_line(reports)  # slice 5
    cost += [fits] if fits else []
    cleans = summary_html.brief_clean_line(reports)  # slice 6
    cost += [cleans] if cleans else []
    trig = summary_html.brief_trigger_line(reports)  # slice 4: first, as on the page
    cost = ([trig] if trig else []) + cost
    L = [f"Walkdown brief: {run_dir.parent.name}",
         f"Files examined: {pin.get('files', '?')}. Pinned: {pin.get('hash_kind', '?')} "
         f"{str(pin.get('hash', '?'))[:12]}.", *cost, "",
         "What it can do:"]
    for k, name in R.LEG_NAMES.items():
        L.append(f"  [{'x' if legs.get(k) else ' '}] {name}")
    L.append(f"  {summary_html.TOGETHER}")
    L.append(f"  Install grants: {', '.join(grants) if grants else 'none'}.")
    rs = summary_html.rows(reports, items)
    wording = sum(1 for it in items if summary_html.concern(it) is None)
    missing = summary_html.not_run(set(reports))
    res = {s: w for s, w in st.items() if s in reports and w != "not run"}
    L += ["", summary_html.headline(rs, missing, summary_html.failed_checks(res))]
    if missing:
        L += [f"  {stage_error(data, stage)}" for stage in STAGE_NAMES if stage not in reports][:1]
    L += [f"  {x['name']} ({len(x['places'])})" for x in rs]
    if wording:
        n = R.n(wording, "more place" if rs else "place")
        L.append("  " + summary_html.WORDING.format(n=n, be="is" if wording == 1 else "are"))
    if model:
        L += ["", f"Model reads (experimental, stage 6): {len(model)} place"
                  f"{'s' if len(model) != 1 else ''}. A model's reading can be wrong."]
        L += [f"  {t} ({n})" for t, n in sorted(by_model.items())]
    # summary.html's terms (owner, 2026-10-25): a check skipped for a missing tool is not named
    steps = summary_html.not_working(res, set(reports))
    L += ["", (f"Not every step worked in this run: {'; '.join(steps)}." if steps else
               "Fixture checks: no step failed." if res else
               "Fixture checks: none, this run was made without validation.")]
    L += ["", f"Report: {out / 'summary.html'}",
          f"Every section in full: {out / 'details.html'}",
          f"Walk through each place and mark it: {out / 'review.html'}",
          f"Every finding with file and line: {out / 'full.md'}", "",
          summary_html.FOOTER]
    return "\n".join(L)


def drift_lines(run_dir: Path) -> list[str]:
    """Version drift against the newest earlier run of the same repository (2026-10-04): writes
    changes.md next to the reports and returns counts-only lines for the brief (no repository
    text). Nothing when this is the first run; one line when the version is the same and nothing
    differs. The same version with a difference means Walkdown changed (review C22 b, 2026-10-19)."""
    sys.path.insert(0, str(STAGE8))
    import drift  # noqa: E402
    prev = drift.previous_run(run_dir)
    if prev is None:
        return []
    s = drift.since(prev, run_dir)
    if not s["differs"]:
        return ["", f"Changes since {prev.name}: same version, nothing to compare."]
    head = (f"Changes since {prev.name}: {s['header']}:" if s["same"]
            else f"Changes since {prev.name} (version drift):")
    return ["", head] + [f"  {x}" for x in s["lines"]] + [f"  Details: {s['report']}"]


def diff_main(args) -> int:
    """walkdown.py diff <old run folder> <new run folder>"""
    sys.path.insert(0, str(STAGE8))
    import drift  # noqa: E402
    return drift.main(args)


# Set when Walkdown runs itself again under the interpreter it chose, so it never does twice.
CHOSEN = "WALKDOWN_CHOSEN_PYTHON"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    python = sys.executable
    if not {"--version", "-h", "--help"} & set(argv):
        python, lacks = python_exe()
        if lacks:
            print(f"error: Python at {python} cannot import {', '.join(lacks)}; install Walkdown's "
                  f"packages first: {python} -m pip install -r {ROOT / 'requirements.txt'}",
                  file=sys.stderr)
            return 2
        if Path(python).resolve() != Path(sys.executable).resolve() and not os.environ.get(CHOSEN):
            # the virtualenv has the packages and this Python lacks them: everything runs there,
            # the brief, drift, and diff included (2026-10-25, review C41)
            return subprocess.run([python, str(ROOT / "walkdown.py"), *argv],
                                  env=dict(os.environ, **{CHOSEN: "1"})).returncode
    if argv[:1] == ["diff"]:
        return diff_main(argv[1:])
    ap = argparse.ArgumentParser(prog="walkdown.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--version", action="version",
                    version="walkdown " + (ROOT / "VERSION").read_text(encoding="utf-8").strip())
    ap.add_argument("target", help="a folder, or a git URL to clone into ReposToExamine/")
    ap.add_argument("--name", help="name for the run folder (default: the repository's name)")
    ap.add_argument("--fresh", action="store_true", help="delete an earlier clone and clone again")
    ap.add_argument("--keep", action="store_true",
                    help="audit an earlier clone as it is, without updating it")
    for k in ("label", "compare", "relational", "sweep", "pinpoint"):
        ap.add_argument(f"--{k}")
    ap.add_argument("--both", action="store_true")
    ap.add_argument("--revalidate", action="store_true",
                    help="re-run the fixture validation even if a stamp for this code is cached")
    ap.add_argument("--context", help="expected context in tokens, such as 32k, 200k, or 8192 (default 32k)")
    ap.add_argument("--hosts", help="the AI hosts you build for, such as claude,codex,cursor; the report "
                                    "lists what each is missing")
    a = ap.parse_args(argv)

    try:
        link = github_link(a.target) if is_url(a.target) else None
        if link:  # a GitHub folder link: the repository at that branch, then the folder
            url, ref, sub = link
            name = a.name or repo_name(sub or url)
            dest = fetch(url, a.name or repo_name(url), a.fresh, a.keep, ref)
            target = dest / sub if sub else dest
            if not target.is_dir():
                raise RuntimeError(f"the folder {sub} is not in {url} at {ref}")
        else:
            name = a.name or repo_name(a.target)
            target = fetch(a.target, name, a.fresh, a.keep) if is_url(a.target) else Path(a.target)
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if target.is_file():
        print(f"error: {a.target} is a file; Walkdown audits a folder: give the folder that "
              "holds it", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"error: not a folder or a git URL: {a.target}", file=sys.stderr)
        return 2
    print(f"Using Python at {python}", file=sys.stderr)
    cmd = [python, str(STAGE8 / "run.py"), str(target), "--repo", name]
    for k in ("label", "compare", "relational", "sweep", "pinpoint"):
        if getattr(a, k):
            cmd += [f"--{k}", getattr(a, k)]
    if a.both:
        cmd.append("--both")
    if a.revalidate:
        cmd.append("--revalidate")
    if a.context:
        cmd += ["--context", a.context]
    if a.hosts:
        cmd += ["--hosts", a.hosts]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, text=True, encoding="utf-8", cwd=ROOT)
    lines = [x for x in proc.stdout.splitlines() if x.strip()]
    run_dir = Path(lines[-1]) if lines else None
    if run_dir is None or not (run_dir / "LOG.md").is_file():
        print("error: the run did not finish; see the messages above", file=sys.stderr)
        return proc.returncode or 1
    print(brief(run_dir))
    try:
        print("\n".join(drift_lines(run_dir)))
    except Exception as exc:  # drift is extra; it never fails the audit
        print(f"note: version drift not computed: {exc}", file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
