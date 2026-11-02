"""Intake runner: gets the copy of the repository in place and prints one contract-1 report.
Spec: specs/intake.SPEC.md, Behavior.

    python stages/01-intake/run.py <target> [--name NAME] [--fresh | --keep]

A folder is read where it is; a git URL is cloned (or an earlier clone updated); a GitHub folder
link clones the repository at its branch and names the folder inside it. The report holds one
`intake.source` finding. A copy that cannot be got is a failure: the message on stderr, exit 2.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch as F  # noqa: E402

STAGE = "01-intake"


def source(target: str, name: str | None = None, fresh: bool = False, keep: bool = False) -> dict:
    """The `intake.source` finding for `target`; RuntimeError or ValueError, with today's message,
    when the copy cannot be got or the target is not a folder."""
    url = ref = sub = None
    if F.is_url(target):
        link = F.github_link(target)
        if link:  # a GitHub folder link: the repository at that branch, then the folder
            kind = "github-folder"
            url, ref, sub = link
            run_name = name or F.repo_name(sub or url)
            dest, action = F.fetch_with_action(url, name or F.repo_name(url), fresh, keep, ref)
            folder = dest / sub if sub else dest
            if not folder.is_dir():
                raise RuntimeError(f"the folder {sub} is not in {url} at {ref}")
        else:
            kind, url = "url", target
            run_name = name or F.repo_name(target)
            folder, action = F.fetch_with_action(target, run_name, fresh, keep)
    else:
        kind, action = "folder", "read in place"
        run_name = name or F.repo_name(target)
        folder = Path(target)
    if folder.is_file():
        raise RuntimeError(f"{target} is a file; Walkdown audits a folder: give the folder that "
                           "holds it")
    if not folder.is_dir():
        raise RuntimeError(f"not a folder or a git URL: {target}")
    return {"check": "intake.source", "file": None, "line": None, "target": target, "kind": kind,
            "action": action, "folder": folder.resolve().as_posix(), "name": run_name, "url": url,
            "ref": ref, "subfolder": sub or None}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="run.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("target", help="a folder, or a git URL to clone into the folder of copies")
    ap.add_argument("--name", help="name for the copy and the run folder (default: the "
                                   "repository's name)")
    ap.add_argument("--fresh", action="store_true", help="delete an earlier clone and clone again")
    ap.add_argument("--keep", action="store_true",
                    help="audit an earlier clone as it is, without updating it")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    try:
        finding = source(a.target, a.name, a.fresh, a.keep)
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    report = {"stage": STAGE, "contract": 1, "findings": [finding]}
    sys.stdout.buffer.write(json.dumps(report, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
