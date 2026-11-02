"""Compare two Walkdown run folders. Spec: specs/compare_runs.SPEC.md.

    python tools/compare_runs.py <old run folder> <new run folder>
           [--map map.json] [--expect expect.json] [--brief-old FILE --brief-new FILE] [--show-text]

The restructure rule is that a move must give the same reports. This tool says whether two runs
of the same input do: findings (pooled across the stage files, by check), the other keys of each
stage report, every other file in the two run folders, LOG.md, the report pages, and the brief
when both are given. Only the things listed in the spec (restructure step 0, Appendix A) are taken
out before comparing; nothing else is ignored. Standard library only. It reads the two run folders
and the files named on the command line, writes nothing, and prints no text from the audited
repository unless --show-text is given.

Exit code: 0 when no difference is unexpected, 1 when one is, 2 on a usage error.
"""
from __future__ import annotations

import argparse
import collections
import difflib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------- what is compared

STAGE_FILE = re.compile(r"^\d[\d.]*-.+\.json$")  # NN-name.json in data/
STAGE_REL = re.compile(r"^data/\d[\d.]*-[^/]+\.json$")
NOTES = re.compile(r"^data/(?P<stem>[^/]+)\.notes\.txt$")  # a stage's own messages
PAGES = ("summary.html", "details.html", "review.html", "full.md")
OPTIONAL_PAGES = ("changes.md",)
# How the named files in data/ are compared: (kind, normalization profile). Text under normalized/
# and the notes files have their own rules (rule()); a file with none is compared byte for byte.
DATA_RULES = {
    "data/graph.json": ("json", None), "data/hits.json": ("json", None),
    "data/capability.json": ("json", None), "data/packet.json": ("json", None),
    "data/answers.jsonl": ("jsonl", None),
    "data/06-packet.md": ("text", "full"),  # "Written: <run date>"
    "data/07-limits.md": ("text", "names"),
    "data/limits.md": ("text", "names"),  # the same file since it lost its number (M9 slice B): the run name in its title
}
# What --expect can announce, by the kind of difference. Checks and validation results are matched
# by exact name; report keys and files may use a * where expect_problem() allows it.
EXPECT_LISTS = {"check-removed": "checks_removed", "check-added": "checks_added",
                "check-changed": "checks_changed", "file": "files_differ",
                "validation": "validation_changed", "report-key": "report_keys_differ"}
EXPECT_KEYS = tuple(EXPECT_LISTS.values()) + ("note",)
MAP_KEYS = ("names", "paths", "files")  # the sections of a map file (format 2)
MISSING = object()

CAP = 20  # most detail lines printed per check or per area; the counts stay complete
CLIP = 300  # longest line --show-text prints

# ---------------------------------------------------------------- normalization (Appendix A)

RUN_NAME = re.compile(r"(?<![0-9A-Za-z])\d{4}-\d{2}-\d{2}_[0-9a-f]{7}(?:-\d+)?(?![0-9A-Za-z])")
FALLBACK_PATH = re.compile(r"(?:[A-Za-z]:|/)[^\s\"'<>|]*?<REPO>[\\/]+<RUN>")
CACHE_NOTE = re.compile(r"; measured \d{4}-\d{2}-\d{2}, same code and fixtures")
CACHE_NOTE_ALONE = re.compile(r" \(measured \d{4}-\d{2}-\d{2}, same code and fixtures\)")
TIME = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?")
VERSION = re.compile(r"Walkdown(:?) (?:unversioned|\d+(?:\.\d+)+(?:[-+][\w.]+)?)"
                     r"(?: \([0-9a-f]{4,40}(?:\+modified)?\))?")
MONTHS = ("January|February|March|April|May|June|July|August|September|October|November|December")
DATE_LONG = re.compile(rf"(?<!\d)\d{{1,2}} (?:{MONTHS}) \d{{4}}(?!\d)")
DATE_ISO = re.compile(r"(?<!\d)\d{4}-\d{2}-\d{2}(?!\d)")


class UsageError(Exception):
    """A folder that is not a run folder, or a file named on the command line that cannot be used."""


def _path_re(path: str) -> re.Pattern:
    """The path in any slash style, any letter case, not followed by more of a name."""
    parts = [p for p in re.split(r"[\\/]+", path) if p]
    lead = r"[\\/]+" if path[:1] in ("/", "\\") else ""
    return re.compile(lead + r"[\\/]+".join(re.escape(p) for p in parts) + r"(?![\w.-])", re.I)


@dataclass
class Run:
    path: Path
    data: Path
    repo: str  # the folder the run is filed under
    path_res: list
    repo_re: re.Pattern | None
    text_map: object = None  # the --map names and paths applied inside text; the old run only
    rename: dict = field(default_factory=dict)  # the --map names; the old run only


def open_run(arg: str) -> Run:
    p = Path(arg)
    if not p.is_dir() or not (p / "LOG.md").is_file() or not (p / "data").is_dir():
        raise UsageError(f"not a run folder (needs LOG.md and data/): {arg}")
    full = p.resolve()
    paths = {str(Path(arg).absolute()), str(full)}
    repo = full.parent.name
    repo_re = (re.compile(r"(?<![\w.-])" + re.escape(repo) + r"(?![\w-])") if repo else None)
    return Run(full, full / "data", repo, [_path_re(x) for x in sorted(paths)], repo_re)


def normalize(text: str, run: Run, *, full: bool, log: bool = False) -> str:
    """Take out only what Appendix A lists. `full` adds the dates and the Walkdown version (items
    4 and 6; the pages, LOG.md, and the brief); `log` adds the times in LOG.md's stage rows."""
    text = CACHE_NOTE.sub("", text)
    text = CACHE_NOTE_ALONE.sub("", text)
    for rx in run.path_res:
        text = rx.sub("<RUNDIR>", text)
    text = RUN_NAME.sub("<RUN>", text)
    if run.repo_re:
        text = run.repo_re.sub("<REPO>", text)
    text = FALLBACK_PATH.sub("<RUNDIR>", text)
    if log:
        text = TIME.sub("<TIME>", text)
    if full:
        text = VERSION.sub(r"Walkdown\1 <VERSION>", text)
        text = DATE_LONG.sub("<DATE>", text)
        text = DATE_ISO.sub("<DATE>", text)
    if run.text_map:  # the old run's text, so that old maps onto new
        text = run.text_map(text)
    return text


def text_mapper(names: dict, paths: dict):
    """One pass over a text: each old path (longest first) or old stage name (a whole token) is
    replaced by its new one. A single pass means a replacement is never replaced again, and
    trying the paths first means "stages/04-phrases" becomes its new path and not a path with
    only the stage name changed. None when the map has neither."""
    if not names and not paths:
        return None
    parts = []
    if paths:
        alts = "|".join(re.escape(p) for p in sorted(paths, key=len, reverse=True))
        parts.append(rf"(?P<path>(?<![\w-])(?:{alts})(?![\w-]))")
    if names:
        alts = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
        parts.append(rf"(?P<name>(?<![\w.-])(?:{alts})(?![\w-]))")
    rx = re.compile("|".join(parts))

    def pick(m: re.Match) -> str:
        found = m.groupdict()
        return paths[found["path"]] if found.get("path") is not None else names[found["name"]]

    return lambda text: rx.sub(pick, text)


def strip_changes_block(lines: list[str]) -> list[str]:
    """Set aside the brief's "Changes since <run>" lines (item 7): the line, the indented lines
    under it, and the blank line before it. Blank lines at the end go too: they are what the
    drift output leaves behind, and a first run has them with nothing else."""
    out, i = [], 0
    while i < len(lines):
        if lines[i].startswith("Changes since "):
            if out and out[-1].strip() == "":
                out.pop()
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    while out and out[-1].strip() == "":
        out.pop()
    return out


# ---------------------------------------------------------------- results

@dataclass
class Diff:
    kind: str  # a key of EXPECT_LISTS: what --expect lists it under
    name: str  # the check id, the file, the stage, or the stage:key, as `--expect` names it
    text: str
    detail: list = field(default_factory=list)
    expected: bool = False


@dataclass
class Section:
    title: str
    body: list = field(default_factory=list)
    diffs: list = field(default_factory=list)


def read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def decode(data: bytes) -> str:
    """Text with every byte kept: bytes that are not UTF-8 become lone surrogates, so two files
    that differ only in such bytes still differ."""
    return data.decode("utf-8", errors="surrogateescape")


def split_lines(text: str) -> list[str]:
    return text.split("\n")


def span(lo: int, hi: int) -> str:
    """Lines lo+1..hi (0-based, half open) as people number them."""
    if hi <= lo:
        return "-"
    return str(lo + 1) if hi - lo == 1 else f"{lo + 1}-{hi}"


def clip(text: str) -> str:
    return text if len(text) <= CLIP else text[:CLIP] + "..."


def capped(lines: list[str], limit: int = CAP) -> list[str]:
    return lines if len(lines) <= limit else lines[:limit] + [f"... and {len(lines) - limit} more"]


def hunks(old: list[str], new: list[str]) -> list[tuple[int, int, int, int]]:
    """Where two line lists differ: (old from, old to, new from, new to), 0-based, half open."""
    n = min(len(old), len(new))
    head = 0
    while head < n and old[head] == new[head]:
        head += 1
    tail = 0
    while tail < n - head and old[-1 - tail] == new[-1 - tail]:
        tail += 1
    a, b = old[head:len(old) - tail], new[head:len(new) - tail]
    if not a and not b:
        return []
    if len(a) * len(b) > 25_000_000:  # too different to line up; one hunk, never a pass
        return [(head, head + len(a), head, head + len(b))]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    return [(head + i1, head + i2, head + j1, head + j2)
            for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]


def text_diff(label: str, old: list[str], new: list[str], show_text: bool, name: str | None = None) -> Diff | None:
    """`label` says what was compared; `name` is what `--expect` calls it (default: the label)."""
    hs = hunks(old, new)
    if not hs:
        return None
    n_old = sum(h[1] - h[0] for h in hs)
    n_new = sum(h[3] - h[2] for h in hs)
    where = "; ".join(f"old {span(h[0], h[1])} / new {span(h[2], h[3])}" for h in hs[:10])
    if len(hs) > 10:
        where += f"; ... and {len(hs) - 10} more places"
    detail = []
    if show_text:
        for h in hs[:10]:
            detail += [f"- {clip(x)}" for x in old[h[0]:h[1]][:5]]
            detail += [f"+ {clip(x)}" for x in new[h[2]:h[3]][:5]]
    return Diff("file", name or label, f"{label}: {n_old} old and {n_new} new lines differ ({where})",
                detail)


# ---------------------------------------------------------------- findings

def canon(value) -> str:
    """Canonical JSON: sorted keys, and 0, 0.0, false, and "0" all stay different."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def same(a, b) -> bool:
    if a is MISSING or b is MISSING:
        return a is b
    return canon(a) == canon(b)


class Pool:
    """Every finding of a run, pooled across its stage files, by check, and each stage report's
    other keys."""

    def __init__(self) -> None:
        self.counts: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
        self.holders: dict[str, set] = collections.defaultdict(set)
        self.files: set[str] = set()
        self.unreadable: set[str] = set()
        self.keys: dict[str, dict] = {}  # stage -> every key of its report except findings

    def total(self, check: str | None = None) -> int:
        if check is not None:
            return sum(self.counts[check].values()) if check in self.counts else 0
        return sum(sum(c.values()) for c in self.counts.values())


def load_pool(run: Run, rename: dict, files: dict) -> Pool:
    """A stage file is paired by the map: by `files` when it moves the file to another stage
    report path, else by `names`."""
    pool = Pool()
    for p in sorted(run.data.glob("*.json")):
        if not STAGE_FILE.match(p.name):
            continue
        moved = files.get(f"data/{p.name}")
        name = Path(moved).stem if moved and STAGE_REL.match(moved) else rename.get(p.stem, p.stem)
        if name in pool.files:
            raise UsageError(f"two stage files in {run.path} are named {name} after --map")
        pool.files.add(name)
        try:
            doc = json.loads(decode(read_bytes(p)))
            items = doc["findings"]
            if not isinstance(items, list) or not all(isinstance(x, dict) for x in items):
                raise ValueError("findings")
        except (ValueError, KeyError, TypeError):
            pool.unreadable.add(name)
            continue
        pool.keys[name] = {k: v for k, v in doc.items() if k != "findings"}
        for f in items:
            check = str(f.get("check", "(no check)"))
            pool.counts[check][canon(f)] += 1
            pool.holders[check].add(name)
    return pool


def where(f: dict) -> str:
    file, line = f.get("file"), f.get("line")
    if file is None and line is None:
        return "(whole run)"
    return str(file) + (f":{line}" if line is not None else "")


def differing_fields(a: dict, b: dict) -> list[str]:
    return sorted(k for k in a.keys() | b.keys() if not same(a.get(k, MISSING), b.get(k, MISSING)))


def pair_up(only_old: list[dict], only_new: list[dict]):
    """Pair what is left on each side by (file, line), best match first. Returns removed, added,
    and changed pairs; what cannot be paired is removed or added."""
    olds, news = collections.defaultdict(list), collections.defaultdict(list)
    for f in only_old:
        olds[(str(f.get("file")), str(f.get("line")))].append(f)
    for f in only_new:
        news[(str(f.get("file")), str(f.get("line")))].append(f)
    removed, added, changed = [], [], []
    for key in list(olds) + [k for k in news if k not in olds]:
        a, b = olds.get(key, []), news.get(key, [])
        if len(a) * len(b) <= 40_000:
            while a and b:
                _, i, j = min((len(differing_fields(x, y)), i, j)
                              for i, x in enumerate(a) for j, y in enumerate(b))
                changed.append((a.pop(i), b.pop(j)))
        removed += a
        added += b
    return removed, added, changed


def how_differs(x, y) -> str:
    if x is MISSING or y is MISSING:
        return f"is in {'new' if x is MISSING else 'old'} only"
    n = json_changes(x, y)
    return f"differs ({n} value{'s' if n != 1 else ''})"


def compare_report_keys(old: Pool, new: Pool, rename: dict) -> list[Diff]:
    """Every key of a stage report except `findings`, as canonical JSON. `stage` is the stage's
    own name, so the old one goes through --map. `terms.code` is a hash of the stage 4 code files
    and changes when the code moves, so it is an item of its own that --expect can announce; the
    rest of `terms` (version, count, rows, vocab) is compared like any other key."""
    diffs = []
    for stage in sorted(old.files & new.files):
        if stage in old.unreadable | new.unreadable:
            continue
        sides = []
        for pool, is_old in ((old, True), (new, False)):
            keys, code = dict(pool.keys[stage]), MISSING
            if is_old and isinstance(keys.get("stage"), str):
                keys["stage"] = rename.get(keys["stage"], keys["stage"])
            if isinstance(keys.get("terms"), dict):
                terms = dict(keys["terms"])
                code = terms.pop("code", MISSING)
                keys["terms"] = terms
            sides.append((keys, code))
        (a, code_a), (b, code_b) = sides
        for key in sorted(a.keys() | b.keys()):
            x, y = a.get(key, MISSING), b.get(key, MISSING)
            if not same(x, y):
                diffs.append(Diff("report-key", f"{stage}:{key}",
                                  f"{stage}: report key {key} {how_differs(x, y)}"))
        if not same(code_a, code_b):
            what = "differs" if MISSING not in (code_a, code_b) else how_differs(code_a, code_b)
            diffs.append(Diff("report-key", f"{stage}:terms.code",
                              f"{stage}: terms.code {what} (a hash of the stage 4 code files; "
                              "it changes when the code moves)"))
    return diffs


def compare_findings(old: Pool, new: Pool, rename: dict, show_text: bool) -> Section:
    sec = Section("Findings")
    checks = sorted(set(old.counts) | set(new.counts))
    sec.body.append(f"Old: {old.total()} findings in {len(old.files)} stage files, "
                    f"{len(old.counts)} checks. New: {new.total()} findings in {len(new.files)} "
                    f"stage files, {len(new.counts)} checks. Pooled across stage files, grouped by "
                    "check; a finding that moved to another stage file is the same finding.")
    sec.body += ["", "| Check | Old | New | Old file | New file | Status |", "|---|---|---|---|---|---|"]
    for check in checks:
        a, b = old.counts.get(check, collections.Counter()), new.counts.get(check, collections.Counter())
        o_n, n_n = old.total(check), new.total(check)
        status = ("same" if a == b else "removed" if not n_n else "added" if not o_n else "changed")
        sec.body.append(f"| {check} | {o_n} | {n_n} | {', '.join(sorted(old.holders.get(check, ()))) or '-'} "
                        f"| {', '.join(sorted(new.holders.get(check, ()))) or '-'} | {status} |")
        if a == b:
            continue
        only_old = [json.loads(s) for s in (a - b).elements()]
        only_new = [json.loads(s) for s in (b - a).elements()]
        removed, added, changed = pair_up(only_old, only_new)
        detail = [f"removed {where(f)}" + (f": {clip(canon(f))}" if show_text else "") for f in removed]
        detail += [f"added {where(f)}" + (f": {clip(canon(f))}" if show_text else "") for f in added]
        for x, y in changed:
            fields = differing_fields(x, y)
            line = f"changed {where(x)}: fields {', '.join(fields)}"
            if show_text:
                line += "; " + "; ".join(f"{k}: {clip(json.dumps(x.get(k)))} -> {clip(json.dumps(y.get(k)))}"
                                         for k in fields)
            detail.append(line)
        sec.diffs.append(Diff(f"check-{status}", check,
                              f"{check}: {status} (old {o_n}, new {n_n}; {len(removed)} removed, "
                              f"{len(added)} added, {len(changed)} changed)", capped(detail)))
    for name in sorted(old.files | new.files):
        label = f"data/{name}.json"
        if name in old.unreadable | new.unreadable:
            who = " and ".join(s for s, p in (("old", old), ("new", new)) if name in p.unreadable)
            sec.diffs.append(Diff("file", label, f"{label} could not be read as a stage report in {who}"))
        elif name not in old.files or name not in new.files:
            side = "old" if name in old.files else "new"
            sec.diffs.append(Diff("file", label, f"{label} is in {side} only (no counterpart; its report "
                                  "keys were not compared)"))
    sec.diffs += compare_report_keys(old, new, rename)
    return sec


# ---------------------------------------------------------------- files

def parse_json(data: bytes):
    return json.loads(data.decode("utf-8"))


def json_changes(a, b) -> int:
    """How many values differ between two parsed documents (a missing key counts as one)."""
    if a is MISSING or b is MISSING:
        return 1
    if isinstance(a, dict) and isinstance(b, dict):
        return sum(json_changes(a.get(k, MISSING), b.get(k, MISSING)) for k in a.keys() | b.keys())
    if isinstance(a, list) and isinstance(b, list):
        return sum(json_changes(x, y) for x, y in zip(a, b)) + abs(len(a) - len(b))
    return 0 if same(a, b) else 1


def compare_file(label: str, old_path: Path | None, new_path: Path | None, kind: str, old: Run, new: Run,
                 profile: str | None, show_text: bool, stage_key: bool = False) -> Diff | None:
    """One file; a path is None when that run does not have it, which is always a difference.
    `kind`: json, jsonl (both as canonical JSON), text, or bytes (byte for byte). `profile`: full,
    names, or None (no normalization). `stage_key`: a JSON file whose top-level "stage" is a stage
    name, which the map's names rename in the old run (data/capability.json); nothing else in a JSON
    file is mapped. Parsed JSON is shown by the count of values that differ, never by key or value:
    a key can be text from the audited repository."""
    if old_path is None or new_path is None:
        if old_path is None and new_path is None:
            return None
        return Diff("file", label, f"{label} is in {'old' if new_path is None else 'new'} only")
    a, b = read_bytes(old_path), read_bytes(new_path)
    mapped_old = (profile and old.text_map) or (stage_key and old.rename)  # the map changes the old side
    if a == b and not mapped_old:
        return None
    if kind == "bytes":
        return Diff("file", label, f"{label}: differs (old {len(a)} bytes, new {len(b)} bytes)")
    if kind in ("json", "jsonl"):
        try:
            if kind == "json":
                x, y = parse_json(a), parse_json(b)
            else:
                x = [parse_json(s) for s in a.splitlines() if s.strip()]
                y = [parse_json(s) for s in b.splitlines() if s.strip()]
        except ValueError:
            kind = "text"
        else:
            if stage_key and isinstance(x, dict) and isinstance(x.get("stage"), str):
                x = {**x, "stage": old.rename.get(x["stage"], x["stage"])}
            if same(x, y):
                return None
            n = json_changes(x, y)
            note = f"{label}: {n} value{'s differ' if n != 1 else ' differs'}"
            if kind == "jsonl":
                at = [i + 1 for i in range(max(len(x), len(y)))
                      if not same(x[i] if i < len(x) else MISSING, y[i] if i < len(y) else MISSING)]
                note += f" (records {', '.join(map(str, at[:10]))}{', ...' if len(at) > 10 else ''})"
            return Diff("file", label, note)
    lines = []
    for data, run in ((a, old), (b, new)):
        text = decode(data)
        if profile:
            text = normalize(text, run, full=profile == "full")
        lines.append(split_lines(text))
    return text_diff(label, lines[0], lines[1], show_text)


def mapped(rel: str, rename: dict) -> str:
    """A stage's notes file is named after the stage, so --map renames it too."""
    m = NOTES.match(rel)
    if m and m["stem"] in rename:
        return f"data/{rename[m['stem']]}.notes.txt"
    return rel


@dataclass
class Mapping:
    """A --map file: old stage names to new (also whole tokens inside text), old paths to new
    (inside text), and old run files to new."""
    names: dict = field(default_factory=dict)
    paths: dict = field(default_factory=dict)
    files: dict = field(default_factory=dict)


def inventory(run: Run, mapping: Mapping) -> tuple[dict[str, Path], dict[str, str]]:
    """Every file in the run folder, by path from the run folder (the old run's mapped to new
    names), and where each was really kept."""
    found, origin = {}, {}
    for p in sorted(run.path.rglob("*")):
        if p.is_file():
            rel = p.relative_to(run.path).as_posix()
            key = mapping.files.get(rel) or mapped(rel, mapping.names)
            found[key], origin[key] = p, rel
    return found, origin


def rule(rel: str) -> tuple[str, str, str | None]:
    """How a file is compared: (the section it is listed in, kind, normalization profile). A file
    with no rule is compared byte for byte."""
    if rel in PAGES or rel in OPTIONAL_PAGES:
        return "Pages", "text", "full"
    if rel in DATA_RULES:
        return ("Files",) + DATA_RULES[rel]
    if rel.startswith("data/normalized/"):
        return "Files", "json" if rel.endswith(".json") else "jsonl" if rel.endswith(".jsonl") else "text", None
    if NOTES.match(rel):
        return "Files", "text", "names"
    return "Files", "bytes", None


def compare_files(old: Run, new: Run, mapping: Mapping, show_text: bool) -> tuple[Section, Section]:
    """Every file in both run folders except LOG.md and the stage reports (which have their own
    comparisons): returns the Files and the Pages sections. A file in one run only is a
    difference. A file the map moved is one file, compared by the rules of the path the old run
    kept it at."""
    files, pages = Section("Files"), Section("Pages")
    (a, a_at), (b, b_at) = inventory(old, mapping), inventory(new, Mapping())
    groups = {"data/normalized/": [0, 0, 0], "data/*.notes.txt": [0, 0, 0],
              "other files, byte for byte": [0, 0, 0]}
    differing = set()
    for rel in sorted(a.keys() | b.keys()):
        at = a_at.get(rel, b_at.get(rel))
        if rel == "LOG.md" or STAGE_REL.match(rel) or STAGE_REL.match(at):
            continue
        area, kind, profile = rule(at)
        group = ("data/normalized/" if at.startswith("data/normalized/") else
                 "data/*.notes.txt" if NOTES.match(at) else
                 "other files, byte for byte" if kind == "bytes" else None)
        if group:
            groups[group][0] += rel in a
            groups[group][1] += rel in b
        d = compare_file(rel, a.get(rel), b.get(rel), kind, old, new, profile, show_text,
                         stage_key=at == "data/capability.json")
        if d:
            (pages if area == "Pages" else files).diffs.append(d)
            differing.add(rel)
            if group:
                groups[group][2] += 1
    for rel in (*PAGES, *OPTIONAL_PAGES):
        if rel in differing:
            continue
        if rel in a or rel in b:
            pages.body.append(f"- {rel}: same")
        elif rel in PAGES:
            pages.body.append(f"- {rel}: in neither run")
    for at in DATA_RULES:
        rel = mapping.files.get(at, at)
        if rel in differing:
            continue
        files.body.append(f"- {rel}: " + ("same" if rel in a or rel in b else "in neither run"))
    for group, (n_old, n_new, n_diff) in groups.items():
        files.body.append(f"- {group}: {n_old} files in old, {n_new} in new, {n_diff} differ")
    return files, pages


# ---------------------------------------------------------------- LOG.md

def parse_log(text: str, run: Run):
    """The other lines, and the stage rows by stage name. The old run's text has the map applied
    (normalize), so its stage names are already the new ones."""
    other, rows = [], collections.OrderedDict()
    for line in split_lines(normalize(text, run, full=True, log=True)):
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.startswith("|") else []
        if len(cells) == 6 and cells[0] != "Stage" and not set(cells[0]) <= set("-: "):
            rows.setdefault(cells[0], []).append(cells)
        else:
            other.append(line)
    return other, rows


def compare_log(old: Run, new: Run, mapping: Mapping, show_text: bool) -> Section:
    sec = Section("LOG.md")
    o_other, o_rows = parse_log(decode(read_bytes(old.path / "LOG.md")), old)
    n_other, n_rows = parse_log(decode(read_bytes(new.path / "LOG.md")), new)
    for stage in list(o_rows) + [s for s in n_rows if s not in o_rows]:
        a, b = o_rows.get(stage, []), n_rows.get(stage, [])
        if len(a) != len(b):  # a row gone is a stamp gone: it is a validation difference
            if a and b:
                what = f"has {len(a)} rows in old, {len(b)} in new"
            elif a:
                what = "has a row in old only (its validation stamp is gone)"
            else:
                what = "has a row in new only (a validation stamp the old run did not have)"
            sec.diffs.append(Diff("validation", stage, f"LOG.md: stage {stage} {what}"))
            continue
        for x, y in zip(a, b):
            if x[5] != y[5]:  # named apart from LOG.md, so announcing LOG.md never covers it
                sec.diffs.append(Diff("validation", stage, f"LOG.md: stage {stage}: validation result "
                                      f"changed: {x[5] or '(none)'} -> {y[5] or '(none)'}"))
    d = text_diff("LOG.md, lines outside the stage rows", o_other, n_other, show_text, name="LOG.md")
    if d:
        sec.diffs.append(d)
    sec.body.append(f"- {sum(map(len, o_rows.values()))} stage rows in old, "
                    f"{sum(map(len, n_rows.values()))} in new, compared by stage name"
                    + (" (after --map)" if mapping.names or mapping.paths else ""))
    return sec


# ---------------------------------------------------------------- brief

def brief_lines(path: Path, run: Run) -> list[str]:
    data = read_bytes(path)
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):  # a shell redirect can save UTF-16
        text = data.decode("utf-16", errors="replace")
    else:
        text = data.decode("utf-8-sig", errors="surrogateescape")
    lines = strip_changes_block(split_lines(text.replace("\r\n", "\n")))
    return split_lines(normalize("\n".join(lines), run, full=True))


def compare_brief(old: Run, new: Run, brief_old: Path, brief_new: Path, show_text: bool) -> Section:
    sec = Section("Brief")
    d = text_diff("brief", brief_lines(brief_old, old), brief_lines(brief_new, new), show_text)
    if d:
        sec.diffs.append(d)
    else:
        sec.body.append("- brief: same")
    return sec


# ---------------------------------------------------------------- expectations

def glob_match(pattern: str, name: str) -> bool:
    """A * is any run of characters inside one path segment (it stops at a "/"). A final "/**" is
    every file below the folder, at any depth. Every other character is itself."""
    if pattern.endswith("/**"):
        return name.startswith(pattern[:-2]) and len(name) > len(pattern) - 2
    return re.fullmatch("[^/]*".join(re.escape(p) for p in pattern.split("*")), name, re.S) is not None


def announces(kind: str, entry: str, name: str, exact_files: frozenset | set = frozenset()) -> bool:
    """Whether an --expect entry covers a difference of this kind and name. Only files and report
    keys take a *, and only as expect_problem() allows. No pattern covers a file in `exact_files`
    or a stage report file: those are named exactly."""
    if entry == name:
        return True
    if "*" not in entry:
        return False
    if kind == "file":
        if STAGE_REL.match(name) or name in exact_files:
            return False
        return glob_match(entry, name)
    if kind == "report-key":  # "*:terms.code": any stage, that key
        return entry.startswith("*:") and name.partition(":")[2] == entry[2:]
    return False


def expect_problem(key: str, entry: str) -> str | None:
    """Why an --expect entry is refused, or None. A * is allowed only where it cannot cover more
    than a step meant to announce: a *.* or a *-* would cover differences of other kinds."""
    if "*" not in entry:
        return None
    if key == "files_differ":
        if entry.endswith("/**"):  # everything below a literal folder
            if "*" not in entry[:-2]:
                return None
        elif "**" not in entry and "/" in entry.split("*", 1)[0]:  # * inside a segment, after a folder
            return None
        return ('files_differ allows "*" (one path segment) only after a literal folder, as in '
                '"data/*.md", and "**" only as the last segment after a literal folder, as in '
                '"data/normalized/**"; a top-level file is named exactly')
    if key == "report_keys_differ":
        if entry.startswith("*:") and entry[2:] and "*" not in entry[2:]:
            return None
        return 'report_keys_differ allows "*" only as the whole stage part, as in "*:terms.code"'
    return f'{key} takes exact names: no "*"'


class Expect:
    """What a step announced before it started (`--expect`)."""

    def __init__(self, doc: dict | None) -> None:
        self.given = doc is not None  # an --expect file was named
        doc = doc or {}
        self.lists = {key: list(doc.get(key, [])) for key in EXPECT_LISTS.values()}
        self.note = doc.get("note", "")
        self.seen: set[tuple[str, str]] = set()
        self.exact_files: set[str] = set()  # files only a name announces; set by compare()

    def matches(self, d: Diff) -> bool:
        key = EXPECT_LISTS[d.kind]
        hits = [p for p in self.lists[key] if announces(d.kind, p, d.name, self.exact_files)]
        self.seen.update((key, p) for p in hits)
        return bool(hits)

    def unseen(self) -> list[str]:
        return [f"{k}: {v}" for k in EXPECT_LISTS.values() for v in self.lists[k]
                if (k, v) not in self.seen]


def load_json_arg(path: str, what: str):
    p = Path(path)
    if not p.is_file():
        raise UsageError(f"{what} file not found: {path}")
    try:
        return json.loads(read_bytes(p).decode("utf-8-sig"))
    except ValueError:
        raise UsageError(f"{what} file is not valid JSON: {path}") from None


def load_map(path: str | None) -> Mapping:
    """Format 2: {"names": {...}, "paths": {...}, "files": {...}}, each old to new. Format 1, the
    flat {old stage name: new stage name}, means names only."""
    if not path:
        return Mapping()
    doc = load_json_arg(path, "--map")
    shape = ('--map must be {"old stage name": "new stage name"}, or an object with only "names", '
             '"paths", and "files", each of {"old": "new"}')
    if not isinstance(doc, dict):
        raise UsageError(shape)
    if any(k in MAP_KEYS and isinstance(v, dict) for k, v in doc.items()):
        if not set(doc) <= set(MAP_KEYS):
            raise UsageError(shape)
        sections = {k: doc.get(k, {}) for k in MAP_KEYS}
    else:
        sections = {"names": doc, "paths": {}, "files": {}}
    for k, section in sections.items():
        if not isinstance(section, dict) or not all(isinstance(a, str) and isinstance(b, str) and a and b
                                                    for a, b in section.items()):
            raise UsageError(shape)
        if len(set(section.values())) != len(section):
            raise UsageError(f"--map {k}: two old entries go to one new one")
    return Mapping(**sections)


def load_expect(path: str | None) -> Expect:
    if not path:
        return Expect(None)
    doc = load_json_arg(path, "--expect")
    lists = list(EXPECT_LISTS.values())
    ok = isinstance(doc, dict) and set(doc) <= set(EXPECT_KEYS)
    ok = ok and all(isinstance(doc.get(k, []), list) and all(isinstance(x, str) for x in doc.get(k, []))
                    for k in lists) and isinstance(doc.get("note", ""), str)
    if not ok:
        raise UsageError("--expect must be a JSON object with only these keys: "
                         + ", ".join(EXPECT_KEYS) + " (lists of strings, and a note)")
    for k in lists:
        for x in doc.get(k, []):
            problem = expect_problem(k, x)
            if problem:
                raise UsageError(f"--expect {problem} (got {x!r})")
    return Expect(doc)


# ---------------------------------------------------------------- the whole comparison

def compare(old_dir: str, new_dir: str, *, mapping: Mapping, expect: Expect, brief_old: str | None,
            brief_new: str | None, show_text: bool) -> tuple[list[Section], list[Diff]]:
    old, new = open_run(old_dir), open_run(new_dir)
    old.text_map, old.rename = text_mapper(mapping.names, mapping.paths), mapping.names
    old_pool, new_pool = load_pool(old, mapping.names, mapping.files), load_pool(new, {}, {})
    # The files that have a rule of their own, and every stage report (old or new, after the map), are
    # announced by name: no pattern in --expect covers them.
    expect.exact_files = ({mapping.files.get(k, k) for k in DATA_RULES}
                          | {f"data/{n}.json" for n in old_pool.files | new_pool.files
                             | set(mapping.names) | set(mapping.names.values())})
    files, pages = compare_files(old, new, mapping, show_text)
    sections = [compare_findings(old_pool, new_pool, mapping.names, show_text),
                files, compare_log(old, new, mapping, show_text), pages]
    if brief_old and brief_new:
        sections.append(compare_brief(old, new, Path(brief_old), Path(brief_new), show_text))
    diffs = [d for s in sections for d in s.diffs]
    for d in diffs:
        d.expected = expect.matches(d)
    return sections, diffs


def render(old_dir: str, new_dir: str, sections: list[Section], diffs: list[Diff], expect: Expect) -> str:
    unexpected = sum(1 for d in diffs if not d.expected)
    first = "SAME" if not diffs else f"DIFFERENT: {unexpected} unexpected, {len(diffs) - unexpected} expected"
    out = [first, "", f"Old run: {old_dir}", f"New run: {new_dir}"]
    for s in sections:
        out += ["", f"## {s.title}", ""] + s.body
        if s.diffs:
            out += ["", "Differences:"]
            for d in s.diffs:
                out.append(f"- {'expected' if d.expected else 'UNEXPECTED'}: {d.text}")
                out += [f"    - {x}" for x in d.detail]
        else:
            out += ["", "No differences."]
    if expect.given:
        out += ["", "## Announced", ""]
        if expect.note:
            out.append(f"Note: {expect.note}")
        left = expect.unseen()
        out.append("Announced and seen: all." if not left else
                   "Announced but not seen (not counted as a difference): " + "; ".join(left))
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="compare_runs.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("old", help="the old run folder (the baseline)")
    ap.add_argument("new", help="the new run folder")
    ap.add_argument("--map", help='JSON {"names": {old: new}, "paths": {old: new}, "files": {old: new}}, '
                                  'or just {old stage name: new stage name}')
    ap.add_argument("--expect", help="JSON of the differences a step announced")
    ap.add_argument("--brief-old", help="the old run's saved brief")
    ap.add_argument("--brief-new", help="the new run's saved brief")
    ap.add_argument("--show-text", action="store_true",
                    help="also print the differing text (only for repositories that are yours)")
    a = ap.parse_args(argv)
    try:
        if bool(a.brief_old) != bool(a.brief_new):
            raise UsageError("give both --brief-old and --brief-new, or neither")
        for f in (a.brief_old, a.brief_new):
            if f and not Path(f).is_file():
                raise UsageError(f"brief file not found: {f}")
        mapping, expect = load_map(a.map), load_expect(a.expect)
        sections, diffs = compare(a.old, a.new, mapping=mapping, expect=expect, brief_old=a.brief_old,
                                  brief_new=a.brief_new, show_text=a.show_text)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:  # a file that cannot be read is not a difference
        print(f"error: cannot read {exc.filename or 'a file'} ({type(exc).__name__})", file=sys.stderr)
        return 2
    out = render(a.old, a.new, sections, diffs, expect)
    sys.stdout.write(out.encode("utf-8", errors="replace").decode("utf-8"))  # lone surrogates -> ?
    return 1 if any(not d.expected for d in diffs) else 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    raise SystemExit(main())
