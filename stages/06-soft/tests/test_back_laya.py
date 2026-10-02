"""Tests for back_laya.py, written from specs/back_laya.SPEC.md. The agent is always a stub."""
import back_laya
import softdata

DATA = softdata.load()


def q(i):
    return {"qid": f"label:a.md:{i}", "kind": "label", "file": "a.md", "line": i,
            "question": DATA["label"]["question"], "state": {"text": f"line {i}"},
            "sources": []}


class StubAgent:
    def __init__(self, truncated=False, fail=None):
        self.calls = []
        self.truncated = truncated
        self.fail = fail

    def predict(self, state, questions):
        self.calls.append((state, questions))
        if self.fail and state["text"] == self.fail:
            raise RuntimeError("bad")
        return {"model": "laya-rl-agent",
                "answers": {"label": {"type": "choice", "choice": "description",
                                      "probabilities": {"do": 0.1, "not-to": 0.1,
                                                        "description": 0.7,
                                                        "example-or-quote": 0.1},
                                      "confidence": 0.4}},
                "usage": {"truncated": self.truncated, "truncated_questions": []}}


def test_predict_with_what_only_and_single_load():
    agent = StubAgent()
    loads = []

    def loader():
        loads.append(1)
        return agent
    lb = back_laya.Laya(DATA, loader=loader)
    res = lb.label([q(1)]) + lb.label([q(2)])
    assert len(loads) == 1 and len(agent.calls) == 2
    state, qs = agent.calls[0]
    assert state == {"text": "line 1"}
    qd = qs["label"]
    assert qd["type"] == "choice" and qd["instructions"] == DATA["label"]["question"]
    assert qd["criteria"] == {k: v["what"] for k, v in DATA["label"]["options"].items()}
    r = res[0]
    assert r["backend"] == "laya" and r["model"] == "convaiinnovations/laya"
    assert r["label"] == "description" and r["confidence"] == 0.4
    assert r["probabilities"]["description"] == 0.7 and r["truncated"] is False


def test_truncation_is_recorded():
    lb = back_laya.Laya(DATA, loader=lambda: StubAgent(truncated=True))
    assert lb.label([q(1)])[0]["truncated"] is True


def test_load_failure_skips_all():
    def loader():
        raise OSError("no weights")
    res = back_laya.Laya(DATA, loader=loader).label([q(1), q(2)])
    assert all(r["skipped"].startswith("laya: load failed") for r in res)


def test_predict_failure_skips_one():
    res = back_laya.Laya(DATA, loader=lambda: StubAgent(fail="line 2")).label([q(1), q(2)])
    assert "skipped" not in res[0]
    assert res[1]["skipped"].startswith("laya: RuntimeError")
