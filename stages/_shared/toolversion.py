"""The version of this Walkdown, as the pages and the run's record name it, and a hash of its code.
Spec: specs/shared.SPEC.md, toolversion."""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

# What a run runs and reads: walkdown.py, and the code and tables under stages/ and Library/. Only those kinds of
# file count, outside the tests, the specs, and any hidden file or folder (a name starting with a dot), so a
# document, a cache (.mypy_cache holds .json files), or a file an editor or a file browser leaves behind (.DS_Store,
# Thumbs.db, run.py~) does not read as a change to the code (O3 verification, 2026-10-30).
CODE_PARTS = ("stages", "Library")
CODE_SKIP_DIRS = {"tests", "specs", "__pycache__", ".pytest_cache"}
CODE_SUFFIXES = {".py", ".yaml", ".json"}


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


def release(text) -> str:
    """The version number alone: '0.4.0' from '0.4.0 (a5bf24e+modified)'. `continue` compares this and `code_hash`,
    so a commit or an edit that touches no code (a document) does not refuse a run (O3 verification, 2026-10-30)."""
    return str(text or "").split(" (")[0].strip()


def code_hash(root: Path) -> str:
    """A short hash of the code and tables a run uses (`CODE_PARTS` and walkdown.py), by file name and content with
    line endings made alike. Two sets of uncommitted edits have the same `tool_version` ('+modified') and a
    different hash, so `continue` can tell that the code it would run is not the code that stopped the run."""
    root = Path(root)
    files = [root / "walkdown.py"]
    for part in CODE_PARTS:
        files += [p for p in (root / part).rglob("*") if p.is_file()
                  and not CODE_SKIP_DIRS & set(p.relative_to(root).parts) and p.suffix in CODE_SUFFIXES
                  and not any(x.startswith(".") for x in p.relative_to(root).parts)]
    h = hashlib.sha256()
    for p in sorted(f for f in files if f.is_file()):
        h.update(p.relative_to(root).as_posix().encode("utf-8") + b"\0")
        h.update(p.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return h.hexdigest()[:16]
