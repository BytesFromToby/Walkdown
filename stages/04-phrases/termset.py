"""The version of stage 4's search terms and matching code, recorded in every report so two runs
can tell a hit that comes from the repository from one that comes from Walkdown (review C22 b,
2026-10-19). Spec: specs/termset.SPEC.md.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
# the fields of a pattern row that decide whether it hits; `note` and `source` never do
MATCH_FIELDS = ("check", "regex", "unless", "audiences", "paths", "where")
SHORT = 12


def _h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:SHORT]


def _canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def row_versions(rows) -> dict[str, str]:
    """One short hash per row id, over the fields that decide a hit."""
    return {r.id: _h(_canon({k: getattr(r, k) for k in MATCH_FIELDS})) for r in rows}


def vocab_version(path=None) -> str | None:
    """The part 2 word lists as loaded (comments and layout do not count); None when unreadable."""
    path = Path(path) if path else HERE / "vocab.yaml"
    try:
        return _h(_canon(yaml.safe_load(path.read_text("utf-8"))))
    except (OSError, yaml.YAMLError):
        return None


def code_version(folder=None) -> str:
    """Stage 4's code: every .py file directly in the stage folder (tests are in a subfolder),
    by name, with line endings normalized so a Windows checkout and a Linux one agree."""
    folder = Path(folder) if folder else HERE
    parts = [p.name.encode("utf-8") + b"\0" + p.read_bytes().replace(b"\r\n", b"\n")
             for p in sorted(folder.glob("*.py"))]
    return _h(b"\0\0".join(parts))


def describe(rows, vocab_path=None, code_folder=None) -> dict:
    """The `terms` block of the stage 4 report."""
    rv = row_versions(rows)
    vv = vocab_version(vocab_path)
    return {"version": _h(_canon({"rows": rv, "vocab": vv})), "count": len(rv),
            "rows": rv, "vocab": vv, "code": code_version(code_folder)}


def diff(old: dict | None, new: dict | None) -> dict:
    """What changed between two `terms` blocks. `known` is false when either run has none (a run
    from before 2026-10-19); the other fields are then empty."""
    if not isinstance(old, dict) or not isinstance(new, dict) or "rows" not in old or "rows" not in new:
        return {"known": False, "same": False, "rows_added": [], "rows_changed": [],
                "rows_removed": [], "vocab_changed": False, "code_changed": False}
    o, n = old.get("rows") or {}, new.get("rows") or {}
    out = {"known": True,
           "rows_added": sorted(set(n) - set(o)),
           "rows_changed": sorted(k for k in set(o) & set(n) if o[k] != n[k]),
           "rows_removed": sorted(set(o) - set(n)),
           "vocab_changed": old.get("vocab") != new.get("vocab"),
           "code_changed": old.get("code") != new.get("code")}
    out["same"] = not (out["rows_added"] or out["rows_changed"] or out["rows_removed"]
                       or out["vocab_changed"] or out["code_changed"])
    return out
