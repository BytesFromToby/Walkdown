"""What changed between two `terms` blocks. Spec: specs/shared.SPEC.md, termdiff.

`02.4-phrases` records the version of its search terms and matching code in every report (`terms`, built by
`02.4-phrases/termset.py`). The report stage compares two runs' blocks to say whether a new or gone phrase
hit comes from the repository or from Walkdown. The comparison lives here so the report stage imports no
stage (restructure step 7, notes M13); it reads the blocks as data and no stage code.
"""
from __future__ import annotations


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
