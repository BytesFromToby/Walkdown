"""Intake's fetch code: gets the copy of a repository in place. Spec: specs/intake.SPEC.md, Behavior.

Moved from walkdown.py (restructure step 2, 2026-10-28), unchanged in behavior and messages.
`fetch_with_action` is `fetch` that also says what it did, which intake records.
"""
from __future__ import annotations

import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
import stagenote  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
EXAMINE = ROOT / "ReposToExamine"
URL = re.compile(r"^(https?://|git@|ssh://)|\.git$")
NAME_OK = re.compile(r"[^A-Za-z0-9._-]+")


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
    sub = unquote(sub or "").strip("/")
    if ".." in sub.replace("\\", "/").split("/"):  # 2026-10-29: the folder must sit inside the clone
        raise ValueError(f"{target} names a folder with '..' in its path; give a folder inside "
                         "the repository")
    return f"https://github.com/{owner}/{repo}", unquote(ref), sub


def repo_name(target: str) -> str:
    """The last path part, without .git, made safe for a folder name."""
    last = target.strip().rstrip("/\\").replace("\\", "/").rsplit("/", 1)[-1]
    last = last.rsplit(":", 1)[-1]
    if last.endswith(".git"):
        last = last[:-4]
    return NAME_OK.sub("-", last).strip("-.") or "repo"


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


def _unlock(func, path, _exc) -> None:
    """git leaves its object files read-only, and on Windows a read-only file cannot be deleted:
    clear the bit and try once more (2026-10-29, restructure notes M8: `--fresh` failed there)."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def fetch_with_action(url: str, name: str, fresh: bool, keep: bool = False,
                      ref: str | None = None) -> tuple[Path, str]:
    """`fetch`, and what it did: `kept as it is`, `updated`, `cloned again`, or `cloned`."""
    dest = EXAMINE / name
    if dest.exists():
        same = (dest / ".git").exists() and _same_url(_origin(dest), url)
        if keep:
            stagenote.note(f"--keep: auditing the existing copy in {dest} as it is")
            return dest, "kept as it is"
        if not same:
            raise RuntimeError(f"{dest} exists and is not a clone of {url}; pass --name to use "
                               "another folder, or --keep to audit what is there")
        if not fresh:
            for args in (("fetch", "--depth", "1", "origin", *([ref] if ref else [])),
                         ("reset", "--hard", "FETCH_HEAD"), ("clean", "-fdx")):
                p = _git(dest, *args)
                if p.returncode != 0:
                    raise RuntimeError(f"updating {dest} failed at git {args[0]}: {_why(p.stderr)}")
            stagenote.note(f"updated the existing clone in {dest} to the latest commit")
            return dest, "updated"
        shutil.rmtree(dest, onexc=_unlock)
        action = "cloned again"
    else:
        action = "cloned"
    EXAMINE.mkdir(exist_ok=True)
    # --no-checkout of hooks is git's default; nothing from the clone is ever run
    proc = _git_run("clone", "--depth", "1", *(["--branch", ref] if ref else []), "--", url, str(dest))
    if proc.returncode != 0:
        raise RuntimeError(f"git clone failed: {_why(proc.stderr)}")
    return dest, action


def fetch(url: str, name: str, fresh: bool, keep: bool = False, ref: str | None = None) -> Path:
    """A shallow clone of `url` in ReposToExamine/<name>, at the remote's latest commit (of
    `ref` when given). An existing clone of the same URL is updated (2026-10-03 review A7:
    re-running on a URL used to audit the old copy silently); --keep audits it as it is;
    --fresh clones again. A folder there that is not a clone of this URL is never touched."""
    return fetch_with_action(url, name, fresh, keep, ref)[0]
