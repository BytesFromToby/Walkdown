"""The reader's marks: one model, one file, carried to later runs. Spec: specs/marks.SPEC.md.

Three marks, Concerned, Not concerned, and Not sure, made on review.html (and on details.html,
the Not concerned box) and saved by the reader as marks.json in the run folder. Walkdown never
writes that file, and a mark changes no finding and no count. Each mark names its row by a stable
key, built from what was flagged and never from the line number alone, so a mark follows its line
when lines move and drops away when the line itself changes (owner, 2026-10-20). A run with no
marks.json of its own takes the marks of the newest earlier run of the same repository that has
one, matched by key.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import layout

MARKS_FILE = "marks.json"
FORMAT = 2
MARK_KEYS = ("concerned", "not-concerned", "not-sure")


def _text(s) -> str:
    return " ".join(str(s if s is not None else "").split())


def key(kind, *parts) -> str:
    """A stable key: the row kind and its parts, white space collapsed, hashed."""
    raw = "\x1f".join([kind] + [_text(p) for p in parts])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def place_key(it) -> str:
    """A place (details_html.first_items): section, headline, file, and the flagged text, or the
    location when there is no text; a repeated sentence: section, headline, and the sentence."""
    if it.get("kind") == "rep.sentence":
        return key("place", it["stage"], it["title"], it.get("quote"))
    src = it.get("src") or {}
    file = src.get("file") or str(it.get("where") or "").split(":")[0]
    return key("place", it["stage"], it["title"], file, it.get("quote") or it.get("where"))


def link_key(url) -> str:
    return key("link", url)


def file_key(reason, path) -> str:
    return key("file", reason, path)


def evidence_key(box, file, text) -> str:
    """A trifecta place: the box, the file, and the text of the cited line (else its number)."""
    return key("evidence", box, file, text)


def hidden_key(file, carrier, text) -> str:
    """A hidden place: the file, how the text hides, and the hidden text (else its line)."""
    return key("hidden", file, carrier, text)


def load(path) -> tuple[dict | None, str | None]:
    """A marks.json the reader saved: (parsed, None), (None, why it could not be read), or
    (None, None) when there is none. A `walkdown_review: 1` file (before 2026-10-20) loads too."""
    p = Path(path)
    if not p.is_file():
        return None, None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, "it is not valid JSON"
    if not isinstance(data, dict) or not isinstance(data.get("marks"), list):
        return None, "it has no list of marks"
    return data, None


def records(data) -> list[dict]:
    """The marks in a parsed file that carry a mark or a note, each with its fields checked:
    {key, id, kind, where, headline, mark, note, from}."""
    out = []
    for m in (data or {}).get("marks") or []:
        if not isinstance(m, dict):
            continue
        mark = m.get("mark") if m.get("mark") in MARK_KEYS else None
        note = m.get("note") if isinstance(m.get("note"), str) else ""
        if not mark and not note:
            continue
        def s(k):
            return m.get(k) if isinstance(m.get(k), str) else None
        out.append({"key": s("key"), "id": s("id"), "kind": s("kind") or "place", "where": s("where"),
                    "headline": s("headline"), "mark": mark, "note": note, "from": s("from")})
    return out


def _earlier(run_dir) -> list[Path]:
    """Sibling run folders whose names sort before this one, newest first (as run.changes_for)."""
    run_dir = Path(run_dir).resolve()
    try:
        sib = [p for p in run_dir.parent.iterdir()
               if p.is_dir() and not p.name.startswith(".") and p.name < run_dir.name]
    except OSError:
        return []
    return sorted(sib, key=lambda p: p.name, reverse=True)


def for_run(run_dir) -> dict:
    """The run's marks: {data, error, carried}. Its own marks.json when there is one (carried
    None); otherwise the newest earlier run's readable marks.json, each mark keeping the run it
    was first made in as `from` (carried = that run's folder name); otherwise none."""
    own, err = load(layout.report_dir(run_dir) / MARKS_FILE)
    if own is not None or err:
        return {"data": own, "error": err, "carried": None}
    for prev in _earlier(run_dir):
        data, err = load(layout.report_dir(prev) / MARKS_FILE)
        if data is None:
            continue
        for m in data["marks"]:
            if isinstance(m, dict) and not isinstance(m.get("from"), str):
                m["from"] = prev.name
        return {"data": data, "error": None, "carried": prev.name}
    return {"data": None, "error": None, "carried": None}


def match(data, rows) -> tuple[dict, int]:
    """Match a file's marks to this run's rows. `rows`: (row id, keys) pairs, the keys being every
    key the row answers to. A mark matches by its key, else (a file made before keys) by its id;
    returns ({row id: record}, how many marks match no row)."""
    by_key, ids = {}, set()
    for rid, keys in rows:
        ids.add(rid)
        for k in keys:
            by_key.setdefault(k, rid)
    out, stray = {}, 0
    for m in records(data):
        rid = by_key.get(m["key"]) if m["key"] else None
        if rid is None and m["id"] in ids:
            rid = m["id"]
        if rid is None:
            stray += 1
            continue
        out[rid] = m
    return out, stray
