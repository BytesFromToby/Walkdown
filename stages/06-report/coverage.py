"""What Walkdown examined, file by file, in three tiers (owner, 2026-11-04: "we will never get every file type"). Spec:
specs/report.SPEC.md, coverage.

- `examined` (white): the checks read the file's text, because it decodes as text, or because the reader step drew text out
  of it (a PDF, a Word document).
- `archive` (yellow): an archive or a zip-based document the inventory looked inside for programs, compiled Python, and
  Office macros; the text inside it was not read.
- `not` (red): anything else. No tests are run on it: Walkdown did not read it, and a person has to open it. An image is
  here since R35 (2026-11-11): its metadata is read, the text drawn in it is not examined (its reason says so).

A file type is its extension, lowercased. The tiers are bookkeeping drawn from what the steps recorded (`02.1-inventory`'s
file rows and `archive` flags, `02.2-reader`'s unread files), not a judgment of the files. Symlinks are left out: they are
never followed, and "Files worth a look" lists them.
"""
from __future__ import annotations

import collections

import render as R

TIERS = ("examined", "archive", "not")
LABEL = {"examined": "Examined",
         "archive": "Archives, looked inside for programs only",
         "not": "No tests are run on these file types"}
NOT_NOTE = "Walkdown does not analyze files with these extensions. Use with caution."  # the owner's words, 2026-11-04
ARCHIVE_NOTE = "Walkdown looked inside for programs, compiled Python, and Office macros; the text inside was not read."
LOADS = {"entry", "project", "on-demand", "maybe"}  # render.SHIP_BANDS "Loads into the AI"


def type_of(f: dict) -> str:
    return (f.get("ext") or "").lower()


def rows(r) -> list[dict]:
    """One row per file but symlinks: `file`, `type`, `tier`, `why` (for a file not examined), `loads` (whether the AI loads
    it, from the builder's `cap.ship`), and `test` (in a test or fixture folder)."""
    archives = {c["file"] for c in R.fnd(r, "02.1-inventory", "struct.census") if c.get("flag") == "archive"}
    unread = {u["file"]: u.get("reason") for u in R.fnd(r, "02.2-reader", "read.unread")}
    reader_ran = bool(r.get("02.2-reader"))  # a step that did not run has no report
    loads = {s["file"] for s in R.fnd(r, R.BUILDER, "cap.ship") if s.get("group") in LOADS}
    out = []
    for f in R.fnd(r, "02.1-inventory", "inv.file"):
        name = f.get("file")
        if not name or f.get("type") == "inode/symlink":
            continue
        why = None
        if f.get("skipped"):
            tier, why = "not", "could not be read"
        elif f.get("encoding"):
            tier = "examined"
        elif reader_ran and name not in unread:
            tier = "examined"  # the reader drew its text out
        elif name in archives:
            tier = "archive"
        else:
            tier, why = "not", unread.get(name) or ("not text" if reader_ran else "not text, and the reader step did not run")
        out.append({"file": name, "type": type_of(f), "tier": tier, "why": why, "loads": name in loads,
                    "test": R.is_test_data(name)})
    return out


def by_tier(r) -> dict[str, list[dict]]:
    """Per tier, its file types, most files first: `type`, `files` (names, test folders last), `count`, `tests` (how many
    are in test folders), and `loads` (how many the AI loads)."""
    groups: dict[str, dict[str, list[dict]]] = {t: collections.defaultdict(list) for t in TIERS}
    for row in rows(r):
        groups[row["tier"]][row["type"]].append(row)
    out = {}
    for tier in TIERS:
        types = []
        for t, rs in groups[tier].items():
            rs = sorted(rs, key=lambda x: (x["test"], x["file"]))
            types.append({"type": t, "files": [x["file"] for x in rs], "count": len(rs),
                          "tests": sum(x["test"] for x in rs), "loads": sum(x["loads"] for x in rs)})
        out[tier] = sorted(types, key=lambda x: (-x["count"], x["type"]))
    return out


def type_name(t: str) -> str:
    return f".{t}" if t else "(no extension)"


def types_line(types: list[dict]) -> str:
    """`.md 30, .py 8, (no extension) 1`."""
    return ", ".join(f"{type_name(x['type'])} {x['count']:,}" for x in types)


def counts(tiers: dict) -> dict[str, int]:
    return {t: sum(x["count"] for x in tiers[t]) for t in TIERS}


def loads_phrase(types: list[dict]) -> str:
    """`; the AI loads 2 of them` when it loads any."""
    k = sum(x["loads"] for x in types)
    return f"; the AI loads {k:,} of them" if k else ""


# ---------------------------------------------------------------- the pages

LIST_CAP = 50  # files named per tier on details.html; full.md names every one


def _esc(s) -> str:
    import html
    return html.escape(str(s), quote=True)


def _files_html(types: list[dict], rows_by_file: dict) -> str:
    names = [f for x in types for f in x["files"]]
    shown = sorted((f for f in names if not rows_by_file[f]["test"]), key=lambda f: not rows_by_file[f]["loads"])[:LIST_CAP]
    tests = sum(rows_by_file[f]["test"] for f in names)
    rest = len(names) - len(shown) - tests
    items = "".join(f"<li><code>{_esc(f)}</code>" + (" · the AI loads it" if rows_by_file[f]["loads"] else "")
                    + (f" · {_esc(rows_by_file[f]['why'])}" if rows_by_file[f]["why"] else "") + "</li>"
                    for f in shown)
    if rest > 0:
        items += f"<li>{rest:,} more (full.md names every one)</li>"
    if tests:
        items += f"<li>{tests:,} in test or fixture folders</li>"
    return f'<ul class="tier-files">{items}</ul>'


def section_html(r, files: bool = False) -> str:
    """The three tiers as a block above everything else: types and counts, and on details.html (`files`) the yellow and
    red tiers' files. A tier with no files is left out; a run with no inventory gives nothing."""
    tiers = by_tier(r)
    c = counts(tiers)
    if not sum(c.values()):
        return ""
    by_file = {x["file"]: x for x in rows(r)} if files else {}
    lis = []
    if c["examined"]:
        lis.append(f'<li class="tier t-examined"><b>{LABEL["examined"]}</b>: {c["examined"]:,} '
                   f'{"file" if c["examined"] == 1 else "files"} ({_esc(types_line(tiers["examined"]))})</li>')
    if c["archive"]:
        lis.append(f'<li class="tier t-archive"><b>{LABEL["archive"]}</b>: {_esc(types_line(tiers["archive"]))}. '
                   f'{ARCHIVE_NOTE}' + (_files_html(tiers["archive"], by_file) if files else "") + "</li>")
    if c["not"]:
        lis.append(f'<li class="tier t-not"><b>{LABEL["not"]}</b>: {_esc(types_line(tiers["not"]))}'
                   f'{_esc(loads_phrase(tiers["not"]))}. {NOT_NOTE}'
                   + (_files_html(tiers["not"], by_file) if files else "") + "</li>")
    return '<h2>What Walkdown examined</h2>' + tier_bar(c) + '<ul class="rows tiers">' + "".join(lis) + "</ul>"


def tier_bar(c) -> str:
    """R33: the three tiers as one bar, white, yellow, red, each segment as wide as its share of the files; the rows under
    it carry the counts and names. A tier with no files has no segment."""
    total = sum(c.values())
    segs = "".join(f'<span class="tseg t-{k}" style="flex-grow:{c[k]}" title="{LABEL[k]}: {c[k]:,}"></span>'
                   for k in ("examined", "archive", "not") if c[k])
    return (f'<div class="tierbar" role="img" aria-label="{total:,} files: {c["examined"]:,} examined, '
            f'{c["archive"]:,} archives, {c["not"]:,} not tested">{segs}</div>')


def full_lines(r) -> list[str]:
    """full.md: the three tiers, and every yellow and red file with why."""
    tiers = by_tier(r)
    c = counts(tiers)
    if not sum(c.values()):
        return []
    by_file = {x["file"]: x for x in rows(r)}
    L = ["What Walkdown examined:", ""]
    L.append(f"- {LABEL['examined']}: {c['examined']:,} ({types_line(tiers['examined']) or 'none'}).")
    L.append(f"- {LABEL['archive']}: {c['archive']:,} ({types_line(tiers['archive']) or 'none'}).")
    L.append(f"- {LABEL['not']}: {c['not']:,} ({types_line(tiers['not']) or 'none'}){loads_phrase(tiers['not'])}.")
    for tier in ("archive", "not"):
        names = sorted((f for x in tiers[tier] for f in x["files"]),
                       key=lambda f: (by_file[f]["test"], not by_file[f]["loads"]))  # what the AI loads first, tests last
        if names:
            L += ["", f"{LABEL[tier]}:", ""]
            L += [f"- {f}" + ("; the AI loads it" if by_file[f]["loads"] else "")
                  + ("; in a test or fixture folder" if by_file[f]["test"] else "")
                  + (f"; {by_file[f]['why']}" if by_file[f]["why"] else "") for f in names]
    return L + [""]


def brief_line(r) -> str | None:
    """brief.md, counts only (the brief holds no text from the repository)."""
    tiers = by_tier(r)
    c = counts(tiers)
    if not sum(c.values()):
        return None
    parts = [f"{c['examined']:,}"]
    if c["archive"]:
        parts.append(f"archives looked inside for programs only: {c['archive']:,}")
    if c["not"]:
        k = len(tiers["not"])
        parts.append(f"no tests are run on {c['not']:,} ({k} file {'type' if k == 1 else 'types'}"
                     f"{loads_phrase(tiers['not'])})")
    return "Examined: " + "; ".join(parts) + "."
