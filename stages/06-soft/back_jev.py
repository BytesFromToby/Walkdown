"""Jev labeling backend (TypeSafe, remote). Spec: specs/back_jev.SPEC.md.

The API key is read in-process and never printed, logged, returned, or stored.
"""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

NAME = "jev"
REMOTE = True
MODEL = "jev-latest"
KEY_NAME = "TYPESAFE_API_KEY"
QKEY = "label"
AUTH_ERRORS = {"TypeSafeAuthenticationError", "TypeSafePermissionDeniedError"}


def _registry_value():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        return winreg.QueryValueEx(k, KEY_NAME)[0]


def read_key(environ=None, registry=None) -> str | None:
    env = os.environ if environ is None else environ
    v = env.get(KEY_NAME)
    if v:
        return v
    try:
        v = (registry or _registry_value)()
    except Exception:
        return None
    return v or None


def _default_factory(key):
    from typesafe_sdk import TypeSafeClient
    return TypeSafeClient(api_key=key)


def choice_question(data, marked: bool = False) -> dict:
    instr = data["label"]["question"]
    if marked:
        instr = f"{instr} {data['label']['marked_note']}"
    return {"type": "choice", "instructions": instr,
            "criteria": {name: {"what": o["what"], "not_for": o["not_for"],
                                "examples": list(o["examples"])}
                         for name, o in data["label"]["options"].items()}}


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


def combine(plain: dict, marked: dict) -> dict:
    """--both: average the two reads' label distributions (soft D4, 2026-10-01). The label
    is the top of the average and `confidence` is its averaged probability. Both reads are
    kept under `reads`. If either read was skipped, the result is skipped: a half-read line
    would be scored on a different footing from the rest."""
    reads = {"plain": plain, "marked": marked}
    base = {"qid": plain["qid"], "backend": NAME}
    for name, r in reads.items():
        if "skipped" in r:
            return {**base, "skipped": f"{r['skipped']} ({name} read of --both)",
                    "request": r.get("request"), "response": r.get("response")}
    pa, pb = plain["probabilities"], marked["probabilities"]
    avg = {k: (pa.get(k, 0.0) + pb.get(k, 0.0)) / 2 for k in sorted(set(pa) | set(pb))}
    label = max(avg, key=lambda k: (avg[k], k == plain["label"]))
    return {**base, "model": plain["model"], "label": label, "probabilities": avg,
            "confidence": avg[label], "confidence_kind": "average of two reads",
            "truncated": False,
            "reads": {n: {"label": r["label"], "probabilities": r["probabilities"],
                          "confidence": r["confidence"]} for n, r in reads.items()},
            "request": [plain["request"], marked["request"]],
            "response": [plain.get("response"), marked.get("response")]}


def sweep_question(data) -> dict:
    sw = data["sweep"]
    return {"type": "choice", "instructions": sw["question"],
            "criteria": {name: {"what": o["what"], "not_for": o["not_for"],
                                "examples": list(o["examples"])}
                         for name, o in sw["options"].items()}}


class Jev:
    name = NAME
    remote = REMOTE
    model = MODEL

    def __init__(self, data, client_factory=None, key_reader=read_key, workers=8,
                 both=False):
        self.data = data
        self.factory = client_factory or _default_factory
        self.key_reader = key_reader
        self.workers = max(1, int(workers))
        self.tokens = 0
        self.both = bool(both)
        if self.both and not data["label"].get("marked_note"):
            raise ValueError("jev --both needs label.marked_note in softreads.yaml")
        self.question = choice_question(data)
        self.question_marked = choice_question(data, marked=True) if self.both else None
        self._key = None
        self._stop = None

    def _scrub(self, text: str) -> str:
        return text.replace(self._key, "***") if self._key else text

    def _one(self, client, q) -> dict:
        if not self.both:
            return self._read(client, q, q["state"], self.question)
        plain = self._read(client, q, q["state"], self.question)
        marked = self._read(client, q, q.get("state_marked") or q["state"],
                            self.question_marked)
        return combine(plain, marked)

    def _read(self, client, q, state, question) -> dict:
        request = {"state": state, "questions": {QKEY: question}, "model": MODEL}
        base = {"qid": q["qid"], "backend": NAME}
        if self._stop:
            return {**base, "skipped": self._stop, "request": request}
        try:
            resp = client.system_one(state=state, questions={QKEY: question}, model=MODEL)
        except Exception as exc:
            kind = type(exc).__name__
            if kind in AUTH_ERRORS:
                self._stop = "jev: authentication failed"
                return {**base, "skipped": self._stop, "request": request}
            msg = self._scrub(" ".join(str(exc).split()))[:200]
            return {**base, "skipped": f"jev: {kind}: {msg}", "request": request}
        answers = getattr(resp, "answers", {}) or {}
        ans = answers.get(QKEY)
        usage = getattr(resp, "usage", None)
        toks = getattr(usage, "input_tokens", None) if usage is not None else None
        response = {"model": getattr(resp, "model", None), "usage": _plain(usage),
                    "answer": _plain(ans)}
        if isinstance(toks, int):
            self.tokens += toks
        label = getattr(ans, "choice", None)
        if label not in self.data["label"]["options"]:
            return {**base, "skipped": "jev: unexpected label", "request": request,
                    "response": response}
        return {**base, "model": getattr(resp, "model", None) or MODEL, "label": label,
                "probabilities": {k: float(v) for k, v in
                                  (getattr(ans, "probabilities", None) or {}).items()},
                "confidence": float(getattr(ans, "confidence", 0.0)), "truncated": False,
                "request": request, "response": response}

    def label(self, questions) -> list[dict]:
        return self._batch(list(questions), self._one)

    def sweep(self, chunks) -> list[dict]:
        """Soft D2: one sweep question per chunk (sweep_question). Results carry `kind`
        (the top option), `probabilities`, `p_any` (1 - p(none)) and `flagged`
        (p(none) < sweep.flag_p)."""
        sw = self.data.get("sweep")
        if not sw:
            raise ValueError("jev sweep needs the sweep section in softreads.yaml")
        self.sweep_q = sweep_question(self.data)
        return self._batch(list(chunks), self._sweep_one)

    def _sweep_one(self, client, c) -> dict:
        state = {"file": c["file"], "line": c["line"], "end_line": c["end_line"],
                 "text": c["text"]}
        request = {"state": state, "questions": {QKEY: self.sweep_q}, "model": MODEL}
        base = {"qid": c["qid"], "backend": NAME}
        if self._stop:
            return {**base, "skipped": self._stop, "request": request}
        try:
            resp = client.system_one(state=state, questions={QKEY: self.sweep_q}, model=MODEL)
        except Exception as exc:
            kind = type(exc).__name__
            if kind in AUTH_ERRORS:
                self._stop = "jev: authentication failed"
                return {**base, "skipped": self._stop, "request": request}
            msg = self._scrub(" ".join(str(exc).split()))[:200]
            return {**base, "skipped": f"jev: {kind}: {msg}", "request": request}
        ans = (getattr(resp, "answers", {}) or {}).get(QKEY)
        usage = getattr(resp, "usage", None)
        toks = getattr(usage, "input_tokens", None) if usage is not None else None
        if isinstance(toks, int):
            self.tokens += toks
        response = {"model": getattr(resp, "model", None), "usage": _plain(usage),
                    "answer": _plain(ans)}
        kind = getattr(ans, "choice", None)
        if kind not in self.data["sweep"]["options"]:
            return {**base, "skipped": "jev: unexpected sweep option", "request": request,
                    "response": response}
        probs = {k: float(v) for k, v in (getattr(ans, "probabilities", None) or {}).items()}
        p_none = probs.get("none", 1.0 if kind == "none" else 0.0)
        flagged = p_none < self.data["sweep"]["flag_p"]
        others = {k: v for k, v in probs.items() if k != "none"}
        if flagged and kind == "none" and others:
            # flagged on the sum of the listed kinds while `none` is still the single top
            # answer: name the likeliest listed kind, never "none" on a flagged passage
            kind = max(others, key=others.get)
        return {**base, "model": getattr(resp, "model", None) or MODEL, "kind": kind,
                "probabilities": probs, "p_any": round(1 - p_none, 6), "flagged": flagged,
                "request": request, "response": response}

    def _batch(self, items, one) -> list[dict]:
        if not items:
            return []
        key = self.key_reader()
        if not key:
            return [{"qid": q["qid"], "backend": NAME, "skipped": "jev: no key"} for q in items]
        self._key = key
        try:
            client = self.factory(key)
        except ImportError:
            return [{"qid": q["qid"], "backend": NAME,
                     "skipped": "jev: typesafe_sdk not installed"} for q in items]
        except Exception as exc:
            reason = f"jev: {type(exc).__name__}: {self._scrub(str(exc))[:200]}"
            return [{"qid": q["qid"], "backend": NAME, "skipped": reason} for q in items]
        # The first call runs alone, so an authentication error stops every later call.
        out = [one(client, items[0])]
        rest = items[1:]
        if self.workers == 1 or len(rest) < 2:
            out += [one(client, q) for q in rest]
        else:
            with ThreadPoolExecutor(self.workers) as pool:
                out += list(pool.map(lambda q: one(client, q), rest))
        return out
