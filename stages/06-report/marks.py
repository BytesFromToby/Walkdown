"""The reader's marks: one model, one file, carried to later runs. Spec: specs/report.SPEC.md, marks.

Three marks, Concerned, Not concerned, and Not sure, made on review.html (report v3, 2026-10-27;
before, also on details.html) and saved by the reader as marks.json in the run folder. Walkdown never
writes that file, and a mark changes no finding and no count. Each mark names its row by a stable
key, built from what was flagged and never from the line number alone, so a mark follows its line
when lines move and drops away when the line itself changes (owner, 2026-10-20). A run with no
marks.json of its own takes the marks of the newest earlier run of the same repository that has
one, matched by key. A mark saved before restructure step 7b filed its place under a key built from
a section number; each place also answers to that old key (`old_place_key`), so the file the reader
saved still matches and is never rewritten.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import layout
import record

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
    """A place (details_html.first_items): the name of its stage (the section it is listed under),
    headline, file, and the flagged text, or the location when there is no text; a repeated
    sentence: stage, headline, and the sentence."""
    if it.get("kind") == "rep.sentence":
        return key("place", it["stage"], it["title"], it.get("quote"))
    src = it.get("src") or {}
    file = src.get("file") or str(it.get("where") or "").split(":")[0]
    if it.get("kind") == "hook" and src.get("masked"):  # no words to tell it from the next hook in its file
        return key("place", it["stage"], it["title"], file, it.get("where"))
    return key("place", it["stage"], it["title"], file, it.get("quote") or it.get("where"))


# HISTORY, and it must never change. Until restructure step 7b (2026-10-29) a place carried the
# number of its report section, 1 to 6, where it now carries the name of its stage, and `place_key`
# hashed that number. A marks.json a reader saved before then holds keys built from these numbers,
# and the file is the reader's: Walkdown does not rewrite it. This table gives, for each stage a
# place can carry, the number it carried before, so that `old_place_key` can build the key a mark
# saved then was filed under and the mark still finds its place. A stage added after 7b is not in
# the table: its places never had an old key. Do not add to this table, renumber it, or remove from
# it; it describes files already on disk.
BEFORE_7B_NUMBER = {
    "02.1-inventory": 1,
    "02.2-reader": 2,
    "02.3-graph": 3,
    "02.4-phrases": 4,
    "02.5-capability": 5,
    "03-sweep": 6,
}


def old_place_key(it) -> str | None:
    """The key `place_key` gave this place before step 7b (its stage as the number in
    `BEFORE_7B_NUMBER`), or None for a stage that had no number then. A marks.json saved before the
    change holds this key; the review page and the match accept it beside the current one."""
    number = BEFORE_7B_NUMBER.get(it["stage"])
    return None if number is None else place_key({**it, "stage": number})


def old_stage_part(stage):
    """What `review_html.place_id` hashes for a stage: the number it carried before step 7b, so a
    place keeps the id a saved marks.json holds (an id is a handle in a reader's file, not a name
    for a stage); the stage's own name for a stage added since."""
    return BEFORE_7B_NUMBER.get(stage, stage)


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


def for_run(run_dir) -> dict:
    """The run's marks: {data, error, carried}. Its own marks.json when there is one (carried
    None); otherwise the newest earlier run's readable marks.json, each mark keeping the run it
    was first made in as `from` (carried = that run's folder name); otherwise none."""
    own, err = load(layout.report_dir(run_dir) / MARKS_FILE)
    if own is not None or err:
        return {"data": own, "error": err, "carried": None}
    for prev in record.earlier_runs(run_dir):  # the one rule for "an earlier run" (record.py)
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
