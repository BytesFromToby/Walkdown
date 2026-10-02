"""Turn a reference into the nodes it names. Spec: specs/resolve.SPEC.md."""
from __future__ import annotations

import posixpath
import re
from dataclasses import dataclass, field


@dataclass
class Result:
    status: str  # outside | file | dir | glob | missing
    targets: list[str] = field(default_factory=list)
    ambiguous: bool = False
    case_mismatch: bool = False
    pattern: str | None = None


def glob_regex(pattern: str) -> re.Pattern:
    out = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        if c == "*":
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        elif c == "[":
            end = pattern.find("]", i + 1)
            if end < 0:
                out.append(re.escape(c))
            else:
                body = pattern[i + 1:end]
                if body.startswith("!"):
                    body = "^" + body[1:]
                cls = "[" + body.replace("\\", "\\\\") + "]"
                try:
                    re.compile(cls)
                except re.error:
                    # not a character class, a placeholder such as [YYYY-MM-DD]
                    # (2026-09-30, Plumbline): match the brackets literally
                    out.append(re.escape(pattern[i:end + 1]))
                else:
                    out.append(cls)
                i = end + 1
                continue
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("".join(out) + r"\Z")


def _norm(base: str, path: str) -> str | None:
    """Join and normalize; None when it escapes the root."""
    joined = posixpath.join(base, path) if base else path
    n = posixpath.normpath(joined)
    if n == ".":
        return ""
    if n == ".." or n.startswith("../"):
        return None
    return n


class Resolver:
    def __init__(self, nodes):
        self.nodes = sorted(set(nodes))
        self.files = set(self.nodes)
        self.dirs: set[str] = set()
        for n in self.nodes:
            parts = n.split("/")[:-1]
            for k in range(1, len(parts) + 1):
                self.dirs.add("/".join(parts[:k]))
        self.lower_files: dict[str, list[str]] = {}
        for n in self.nodes:
            self.lower_files.setdefault(n.lower(), []).append(n)
        self.lower_dirs: dict[str, list[str]] = {}
        for d in sorted(self.dirs):
            self.lower_dirs.setdefault(d.lower(), []).append(d)
        self.by_base: dict[str, list[str]] = {}
        self.by_base_lower: dict[str, list[str]] = {}
        for n in self.nodes:
            b = n.rsplit("/", 1)[-1]
            self.by_base.setdefault(b, []).append(n)
            self.by_base_lower.setdefault(b.lower(), []).append(n)

    def under(self, folder: str) -> list[str]:
        prefix = folder.rstrip("/") + "/" if folder.strip("/") else ""
        return [n for n in self.nodes if n.startswith(prefix)]

    def children(self, folder: str) -> list[str]:
        prefix = folder.rstrip("/") + "/" if folder.strip("/") else ""
        return [n for n in self.nodes if n.startswith(prefix) and "/" not in n[len(prefix):]]

    def glob(self, from_dir: str, pattern: str) -> list[str]:
        for base in dict.fromkeys([from_dir, ""]):
            full = _norm(base, pattern.rstrip("/")) if pattern.rstrip("/") else base
            if full is None:
                continue
            rx = glob_regex(full)
            hits = [n for n in self.nodes if rx.match(n)]
            if hits:
                return hits
        return []

    def resolve(self, from_rel: str, path: str, shape: str) -> Result:
        from_dir = posixpath.dirname(from_rel)
        want_dir = path.endswith("/")
        clean = path.rstrip("/")
        first = _norm(from_dir, clean)
        if first is None:
            return Result("outside")
        root_try = _norm("", clean)
        bases = [t for t in dict.fromkeys([first, root_try]) if t]

        if shape == "glob":
            return Result("glob", self.glob(from_dir, path), pattern=path)

        for exact in (True, False):
            for cand in bases:
                if exact:
                    if not want_dir and cand in self.files:
                        return Result("file", [cand])
                    if cand in self.dirs:
                        return Result("dir", self.under(cand), pattern=cand + "/")
                else:
                    if not want_dir and cand.lower() in self.lower_files:
                        return Result("file", self.lower_files[cand.lower()][:1],
                                      case_mismatch=True,
                                      ambiguous=len(self.lower_files[cand.lower()]) > 1)
                    if cand.lower() in self.lower_dirs:
                        d = self.lower_dirs[cand.lower()][0]
                        return Result("dir", self.under(d), case_mismatch=True, pattern=d + "/")
            if "/" not in clean and not want_dir and shape in ("bare", "link"):
                table = self.by_base if exact else self.by_base_lower
                key = clean if exact else clean.lower()
                hits = table.get(key, [])
                if hits:
                    return Result("file", sorted(hits), ambiguous=len(hits) > 1,
                                  case_mismatch=not exact)
        return Result("missing")
