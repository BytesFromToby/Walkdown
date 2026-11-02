"""Jev backend for the coverage sweep (TypeSafe, remote). Spec: specs/sweep.SPEC.md, The Jev backend (back_jev.py).

The API key is read in-process and never printed, logged, returned, or stored. The first call alone, the second try, the stop on
a rejected key, the workers, and "not sent" are `stages/_shared/textmodel.py`'s, the same for every backend.
"""
from __future__ import annotations

import math
import time

import calllog  # stages/_shared (the runner puts it on the path)
import textmodel
import usage as usage_mod
from jevkey import KEY_NAME, read_key  # noqa: F401  (the key is read in stages/_shared/jevkey.py, which also says whether Jev is available)

NAME = "jev"
REMOTE = True
MODEL = "jev-latest"
QKEY = "label"  # the name the question is sent under and the answer comes back under (unchanged since the labeling days)
AUTH_ERRORS = {"TypeSafeAuthenticationError", "TypeSafePermissionDeniedError"}


def _default_factory(key):
    from typesafe_sdk import RetryPolicy, TypeSafeClient
    # The SDK retries a failed call on its own (2 more sends, with backoff, for a 408, 429, 5xx, a lost connection,
    # or a timeout). The one extra try is Walkdown's (calllog.attempt), so the SDK's are off: a passage is sent at most twice.
    return TypeSafeClient(api_key=key, retry=RetryPolicy(max_retries=0))


def _plain(obj):
    """Answer / usage objects as plain JSON-able data."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump(mode="json")
    if hasattr(obj, "__dict__"):
        return {k: _plain(v) for k, v in vars(obj).items() if not k.startswith("_")}
    if isinstance(obj, dict):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


def sweep_question(data) -> dict:
    sw = data["sweep"]
    return {"type": "choice", "instructions": sw["question"],
            "criteria": {name: {"what": o["what"], "not_for": o["not_for"],
                                "examples": list(o["examples"])}
                         for name, o in sw["options"].items()}}


def state_of(c) -> dict:
    """What the model is shown of a passage: where it is, and its text."""
    return {"file": c["file"], "line": c["line"], "end_line": c["end_line"], "text": c["text"]}


class Jev(textmodel.Backend):
    name = NAME
    remote = REMOTE
    model = MODEL

    def __init__(self, data, client_factory=None, key_reader=read_key, workers=8, sleep=time.sleep):
        super().__init__(data, sleep, workers)
        self.data = data
        self.factory = client_factory or _default_factory
        self.key_reader = key_reader
        self.sweep_q = sweep_question(data)
        self.client = None

    def request(self, c) -> dict:
        """Exactly what is sent for one passage (no key in it): the state, the question with its
        options, and the model. The runner writes this to the input file before anything is sent."""
        return {"state": state_of(c), "questions": {QKEY: self.sweep_q}, "model": MODEL}

    def sweep(self, chunks) -> list[dict]:
        """One sweep question per passage (sweep_question). Results carry `kind` (the top
        option), `probabilities`, `p_any` (1 - p(none)) and `flagged` (p(none) < sweep.flag_p)."""
        return self.ask(chunks, "sweep")

    def prepare(self) -> str | None:
        key = self.key_reader()
        if not key:
            return "jev: no key"
        try:
            self.client = self.factory(key)
        except ImportError:
            return "jev: typesafe_sdk not installed"
        except Exception as exc:  # the exception's class only: its text could hold the key
            return f"jev: {type(exc).__name__}"
        return None

    def once(self, c):
        """One call: (the answered fields, None) or (None, the failure, `calllog.failure`)."""
        request = self.request(c)
        try:
            resp = self.client.system_one(state=request["state"], questions=request["questions"],
                                          model=MODEL)
        except Exception as exc:
            # Only what Walkdown can name: the exception's class and the HTTP status the SDK's error carries. The error's
            # message is never kept: it holds the endpoint and a request id, and can repeat the passage or the model's words.
            kind = type(exc).__name__
            status = getattr(exc, "status", None)
            status = status if isinstance(status, int) and not isinstance(status, bool) else None
            if kind in AUTH_ERRORS:
                return None, calllog.failure(kind, status, "jev: authentication failed", auth=True)
            return None, calllog.failure(kind, status, f"jev: {kind}{calllog.status_text(status)}")
        ans = (getattr(resp, "answers", {}) or {}).get(QKEY)
        used = getattr(resp, "usage", None)
        spent = usage_mod.clean({"input": getattr(used, "input_tokens", None), "output": getattr(used, "output_tokens", None)})
        response = {"model": getattr(resp, "model", None), "usage": _plain(used), "answer": _plain(ans)}
        kind = getattr(ans, "choice", None)
        if kind not in self.data["sweep"]["options"]:
            return None, calllog.failure("unexpected option", None, "jev: unexpected sweep option", response=response,
                                         usage=spent)
        try:
            probs = {k: float(v) for k, v in (getattr(ans, "probabilities", None) or {}).items()}
        except (AttributeError, TypeError, ValueError):
            probs = None
        if probs is None or not all(map(math.isfinite, probs.values())):  # no probability to judge by: no answer
            return None, calllog.failure("unreadable answer", None, "jev: unreadable answer", response=response,
                                         usage=spent)
        p_none = probs.get("none", 1.0 if kind == "none" else 0.0)
        flagged = p_none < self.data["sweep"]["flag_p"]
        others = {k: v for k, v in probs.items() if k != "none"}
        if flagged and kind == "none" and others:
            # flagged on the sum of the listed kinds while `none` is still the single top
            # answer: name the likeliest listed kind, never "none" on a flagged passage
            kind = max(others, key=others.get)
        return {"model": self.answered_by(getattr(resp, "model", None)), "kind": kind,
                "probabilities": probs, "p_any": round(1 - p_none, 6), "flagged": flagged,
                "response": response, "usage": spent}, None
