"""How sure a model was, as a Sweep finding says it. Spec: specs/shared.SPEC.md, probability.

A Sweep finding from Jev has `p_any`, a probability. A finding from a model that takes text has none: no model is asked how sure it
is, so `probabilities` and `p_any` are absent and the finding says only whether the model flagged the passage (`flagged`). Every
reader of a Sweep finding (the pinpoint's choice of passages, the pages) asks here, so a finding with no number is handled the
same way everywhere and no number is made up for it.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import options  # noqa: E402

NONE = "this model gives no probability"  # what stands where the number would be


def gives(backend) -> bool | None:
    """Whether a backend gives a probability with its Sweep answer: the `probability` of its row in `options.BACKENDS`. None for a
    backend the table does not have (a report from another version, or a name that is not one): the rows then say.

    The pages word a read from this, and never by looking for a number in the rows: a text model that got no answer for any passage has
    no rows to look at, and a band (`p >= 0.6`) says nothing true of a model that has no probability (M1 fix 9)."""
    spec = options.BACKENDS.get(backend) if isinstance(backend, str) else None
    got = None if spec is None else spec.get("probability")
    return got if isinstance(got, bool) else None


def of(finding) -> float | None:
    """`p_any` as a number, or None when the finding has none: absent, null, text, a bool, or a number that is not finite (a
    saved file that was changed by hand reads as a finding with no number, not as a crash)."""
    p = finding.get("p_any") if isinstance(finding, dict) else None
    return float(p) if isinstance(p, (int, float)) and not isinstance(p, bool) and math.isfinite(p) else None


def words(finding) -> str:
    """`p=0.62`, or `this model gives no probability` for a finding with no number."""
    p = of(finding)
    return NONE if p is None else f"p={p:.2f}"
