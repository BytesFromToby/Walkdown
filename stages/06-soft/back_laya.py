"""Laya labeling backend (local, CPU). Spec: specs/back_laya.SPEC.md."""
from __future__ import annotations

NAME = "laya"
REMOTE = False
MODEL = "convaiinnovations/laya"
QKEY = "label"


def _default_loader():
    import laya
    return laya.load(MODEL)


def choice_question(data) -> dict:
    """Laya gets each option's `what` only (FINDINGS section 6: negations recruit what they
    forbid on Laya; the 512-token sequence leaves little room for long criteria)."""
    return {"type": "choice", "instructions": data["label"]["question"],
            "criteria": {name: o["what"] for name, o in data["label"]["options"].items()}}


class Laya:
    name = NAME
    remote = REMOTE
    model = MODEL

    def __init__(self, data, loader=None):
        self.data = data
        self.loader = loader or _default_loader
        self.question = choice_question(data)
        self.tokens = None
        self._agent = None
        self._load_error = None

    def _get_agent(self):
        if self._agent is None and self._load_error is None:
            try:
                self._agent = self.loader()
            except ImportError:
                self._load_error = "laya: not installed"
            except Exception as exc:
                msg = " ".join(str(exc).split())[:200]
                self._load_error = f"laya: load failed: {type(exc).__name__}: {msg}"
        return self._agent

    def _one(self, agent, q) -> dict:
        request = {"state": q["state"], "questions": {QKEY: self.question}}
        base = {"qid": q["qid"], "backend": NAME}
        try:
            res = agent.predict(q["state"], {QKEY: self.question})
        except Exception as exc:
            msg = " ".join(str(exc).split())[:200]
            return {**base, "skipped": f"laya: {type(exc).__name__}: {msg}", "request": request}
        ans = (res.get("answers") or {}).get(QKEY) or {}
        usage = res.get("usage") or {}
        response = {"model": res.get("model"), "answer": ans, "usage": usage}
        label = ans.get("choice")
        if label not in self.data["label"]["options"]:
            return {**base, "skipped": "laya: unexpected label", "request": request,
                    "response": response}
        truncated = bool(usage.get("truncated")) or QKEY in (usage.get("truncated_questions")
                                                             or [])
        return {**base, "model": MODEL, "label": label,
                "probabilities": {k: float(v) for k, v in (ans.get("probabilities") or {}).items()},
                "confidence": float(ans.get("confidence", 0.0)), "truncated": truncated,
                "request": request, "response": response}

    def label(self, questions) -> list[dict]:
        questions = list(questions)
        if not questions:
            return []
        agent = self._get_agent()
        if agent is None:
            return [{"qid": q["qid"], "backend": NAME, "skipped": self._load_error}
                    for q in questions]
        return [self._one(agent, q) for q in questions]
