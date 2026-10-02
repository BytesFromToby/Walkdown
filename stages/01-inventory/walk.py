"""List what ships in an input folder and pin it. Spec: specs/walk.SPEC.md."""
from __future__ import annotations

import hashlib
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

GIT_SAFE = ["-c", "core.fsmonitor=false"]


@dataclass
class Entry:
    rel: str
    kind: str  # "file" or "symlink"
    target: str | None = None
    exec_bit: bool | None = None
    exec_source: str = "stat"


@dataclass
class Walk:
    root: Path
    entries: list[Entry]
    hash: str
    hash_kind: str
    channel: str
    untracked: int = 0
    notes: list[str] = field(default_factory=list)


def _git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    if shutil.which("git") is None:
        return None
    try:
        return subprocess.run(["git", *GIT_SAFE, "-C", str(root), *args],
                              capture_output=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None


def _same_dir(a: str | Path, b: str | Path) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def _readlink(path) -> str:
    target = os.readlink(path)
    if target.startswith("\\\\?\\"):  # Windows extended-path prefix
        target = target[4:]
    return target


def _is_link(entry: os.DirEntry) -> bool:
    if entry.is_symlink():
        return True
    is_junction = getattr(entry, "is_junction", None)
    return bool(is_junction and is_junction())


def _scan(root: Path) -> list[Entry]:
    """Directory walk that never follows a symlink or junction."""
    out: list[Entry] = []
    windows = sys.platform == "win32"
    stack = [(root, "")]
    while stack:
        folder, prefix = stack.pop()
        with os.scandir(folder) as it:
            for de in it:
                rel = prefix + de.name
                if _is_link(de):
                    try:
                        target = _readlink(de.path)
                    except OSError:
                        target = ""
                    out.append(Entry(rel, "symlink", target=target, exec_bit=False,
                                     exec_source="stat"))
                elif de.is_dir(follow_symlinks=False):
                    if prefix == "" and de.name == ".git":
                        continue
                    stack.append((Path(de.path), rel + "/"))
                elif de.is_file(follow_symlinks=False):
                    mode = de.stat(follow_symlinks=False).st_mode
                    out.append(Entry(rel, "file", exec_bit=bool(mode & stat.S_IXUSR),
                                     exec_source="stat-windows" if windows else "stat"))
    out.sort(key=lambda e: e.rel)
    return out


def _content(root: Path, e: Entry) -> bytes:
    if e.kind == "symlink":
        return (e.target or "").encode("utf-8")
    return (root / e.rel).read_bytes()


def sha256_pin(root: Path, entries: list[Entry]) -> str:
    h = hashlib.sha256()
    for e in sorted(entries, key=lambda x: x.rel):
        try:
            data = _content(root, e)
        except OSError:
            data = b""
        h.update(e.rel.encode("utf-8") + b"\0" + hashlib.sha256(data).digest() + b"\n")
    return h.hexdigest()


def _git_walk(root: Path, notes: list[str]) -> Walk | None:
    top = _git(root, "rev-parse", "--show-toplevel")
    if top is None or top.returncode != 0:
        return None
    toplevel = top.stdout.decode("utf-8", "replace").strip()
    if not toplevel or not _same_dir(toplevel, root):
        return None
    head = _git(root, "rev-parse", "HEAD")
    listing = _git(root, "ls-files", "-s", "-z")
    if head is None or head.returncode != 0 or listing is None or listing.returncode != 0:
        notes.append("git work tree without a readable HEAD or index; using directory mode")
        return None
    entries: list[Entry] = []
    for rec in listing.stdout.split(b"\0"):
        if not rec:
            continue
        meta, _, path = rec.partition(b"\t")
        mode = meta.split(b" ")[0].decode()
        rel = path.decode("utf-8", "replace")
        full = root / rel
        if mode == "160000":
            notes.append(f"submodule not inventoried: {rel}")
            continue
        if mode == "120000":
            if full.is_symlink():
                target = _readlink(full)
            elif full.is_file():
                target = full.read_bytes().decode("utf-8", "replace")
            else:
                notes.append(f"tracked symlink missing from disk: {rel}")
                continue
            entries.append(Entry(rel, "symlink", target=target, exec_bit=False,
                                 exec_source="git-index"))
            continue
        if full.is_symlink() or not full.is_file():
            notes.append(f"tracked file missing or replaced on disk, skipped: {rel}")
            continue
        entries.append(Entry(rel, "file", exec_bit=(mode == "100755"), exec_source="git-index"))
    entries.sort(key=lambda e: e.rel)
    tracked = {e.rel for e in entries}
    untracked = sum(1 for e in _scan(root) if e.rel not in tracked)
    if untracked:
        notes.append(f"{untracked} untracked file(s) in the work tree were not inventoried")
    return Walk(root, entries, head.stdout.decode().strip(), "git", "git", untracked, notes)


def walk(input_dir: str | Path) -> Walk:
    root = Path(input_dir).resolve()
    notes: list[str] = []
    w = _git_walk(root, notes)
    if w is not None:
        return w
    entries = _scan(root)
    if sys.platform == "win32":
        notes.append("exec bit from os.stat on Windows reflects the file extension, "
                     "not a mode bit; pin via git for the real bit")
    return Walk(root, entries, sha256_pin(root, entries), "sha256", "directory", 0, notes)


def pin_finding(w: Walk, files: int, bytes_total: int) -> dict:
    return {"check": "inv.pin", "file": None, "line": None,
            "source": w.root.as_posix(), "hash": w.hash, "hash_kind": w.hash_kind,
            "files": files, "bytes": bytes_total, "channel": w.channel,
            "untracked": w.untracked}
