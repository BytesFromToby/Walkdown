"""Token totals of a model read. Spec: specs/shared.SPEC.md, usage.

A model step reports what its calls used in a `usage` block (M1 slice A): `input`, `output`, `cache_write`, `cache_read`,
`calls`, and `reported`, each a whole number. A backend that does not report a count leaves the key out of the block: absent means
not reported, and is never written as 0. `calls` is Walkdown's own count of the calls it sent (a second try is a call), so it is
always there and is 0 for a read that sent nothing. `reported` is how many of those calls reported any token count. The totals are
what the backends reported, so they are a lower bound when `reported` is below `calls`, and the words say so (`words`: `(from 5 of
9 calls)`). The fixture check's tokens ride on the validation stamp (`validate.Stamp.usage`) in the same shape.
"""
from __future__ import annotations

import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coverlines import whole  # noqa: E402

TOKENS = ("input", "output", "cache_write", "cache_read")
KEYS = (*TOKENS, "calls", "reported")
# A count above this is not a count (M1 fix 6). A service can put any number in its reply, and a number of thousands of digits
# fills a page, or raises when it is added to another. No model reads a thousand trillion tokens in one run.
CEILING = 10 ** 15


def count(n) -> bool:
    """Whether `n` is a count a block can hold: a whole number (`coverlines.whole`) no higher than `CEILING`."""
    return whole(n) and n <= CEILING


def clean(fields) -> dict:
    """The token counts of `fields` (what a backend read out of its response, under the names in `TOKENS`) that are counts:
    a count that is missing, a float, a bool, below zero, or above `CEILING` is not reported, so it is left out."""
    return {k: fields[k] for k in TOKENS if isinstance(fields, dict) and count(fields.get(k))}


def valid(block) -> bool:
    """Whether a saved `usage` can be read: an object whose counts, where it has them, are counts (whole, and no higher than
    `CEILING`), and whose `reported`, where it has it, is no more than its `calls` (a call that was not sent reported nothing). A
    report whose `usage` is not is an output that cannot be read (`pipeline.read_report`)."""
    return (isinstance(block, dict) and all(count(block[k]) for k in KEYS if k in block)
            and not ("reported" in block and "calls" in block and block["reported"] > block["calls"]))


def plus(*blocks) -> dict | None:
    """The blocks added up, key by key over the blocks that have the key; None when there is no block. A block that is
    None or cannot be read counts for nothing."""
    got = [b for b in blocks if valid(b)]
    if not got:
        return None
    total = {k: sum(b[k] for b in got if k in b) for k in KEYS if any(k in b for b in got)}
    if not all("reported" in b for b in got):
        total.pop("reported", None)  # a block that does not say how many reported leaves the sum not knowing
    return {k: v for k, v in total.items() if count(v)}  # a sum past the ceiling is not a count either: not reported


class Tally:
    """What one backend's calls used, added up as they come in (the calls run in threads)."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sum: dict[str, int] = {}
        self._calls = 0
        self._reported = 0

    def add(self, spent=None) -> None:
        """One call was sent; `spent` is what it reported (`clean`), or None when it reported nothing. A call that reported any
        count, an answer or not, is one that `reported`."""
        spent = clean(spent)
        with self._lock:
            self._calls += 1
            self._reported += 1 if spent else 0
            for k, v in spent.items():
                self._sum[k] = self._sum.get(k, 0) + v

    def block(self) -> dict:
        """The step's `usage` block: the counts that were reported, then `calls` and `reported`. A total past `CEILING` (calls
        that each reported a count a service made up) is left out, as one such count is."""
        with self._lock:
            return {**{k: self._sum[k] for k in TOKENS if k in self._sum and count(self._sum[k])},
                    "calls": self._calls, "reported": self._reported}


def partial(block) -> tuple[int, int] | None:
    """`(reported, calls)` for a block whose totals are a lower bound because only some of its calls reported a count (more than
    none and fewer than all), else None: also for a block that does not say."""
    if not valid(block):
        return None
    reported, calls = block.get("reported"), block.get("calls")
    return (reported, calls) if reported is not None and calls is not None and 0 < reported < calls else None


def note(block: dict) -> str:
    """The step's note on its tokens: `tokens the calls used, as the backend reported them: 7 in, 3 out (1 call)`. A partial total
    says how many calls it is from (`words`), in the place of the number of calls."""
    calls = block["calls"]
    tail = "" if partial(block) else f" ({calls} call{'s' if calls != 1 else ''})"
    return f"tokens the calls used, as the backend reported them: {words(block)}{tail}"


def words(block) -> str:
    """A step's tokens in Walkdown's words: `596,200 in, 31,464 out`, with `1,200 cache write` and `300 cache read` added where
    the backend reported them and they are not 0. A total that only some of the calls reported says so, so it does not read as
    the whole: `500 in, 15 out (from 5 of 9 calls)` (`partial`). `not reported` for a block that holds no token count (or none that
    can be read), or whose `reported` is 0, and `sent nothing` for a read that sent no call."""
    if not valid(block) or block.get("reported") == 0:
        return "sent nothing" if valid(block) and block.get("calls") == 0 else "not reported"
    parts = [f"{block[k]:,} {label}" for k, label in (("input", "in"), ("output", "out")) if k in block]
    parts += [f"{block[k]:,} {k.replace('_', ' ')}" for k in ("cache_write", "cache_read") if block.get(k)]
    if parts:
        some = partial(block)
        return ", ".join(parts) + (f" (from {some[0]:,} of {some[1]:,} calls)" if some else "")
    return "sent nothing" if block.get("calls") == 0 else "not reported"
