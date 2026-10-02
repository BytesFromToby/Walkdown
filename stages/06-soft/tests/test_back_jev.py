"""Tests for back_jev.py, written from specs/back_jev.SPEC.md. The client is always a stub."""
from types import SimpleNamespace

import pytest

import back_jev
import softdata

DATA = softdata.load()
FAKE_KEY = "test-key-not-real-123"


def q(i):
    return {"qid": f"label:a.md:{i}", "kind": "label", "file": "a.md", "line": i,
            "question": DATA["label"]["question"], "state": {"text": f"line {i}"},
            "sources": []}


class AuthError(Exception):
    pass


AuthError.__name__ = "TypeSafeAuthenticationError"


class StubClient:
    def __init__(self, label="do", fail=None):
        self.calls = []
        self.label = label
        self.fail = fail or {}

    def system_one(self, state, questions, model):
        self.calls.append({"state": state, "questions": questions, "model": model})
        exc = self.fail.get(state["text"])
        if exc:
            raise exc
        ans = SimpleNamespace(type="choice", choice=self.label, confidence=0.9,
                              probabilities={"do": 0.9, "not-to": 0.05, "description": 0.03,
                                             "example-or-quote": 0.02})
        return SimpleNamespace(model="jev-2", usage=SimpleNamespace(input_tokens=100,
                                                                     output_tokens=None),
                               answers={"label": ans}, choices={"label": ans})


def make(client, key=FAKE_KEY):
    made = []

    def factory(k):
        made.append(k)
        return client
    j = back_jev.Jev(DATA, client_factory=factory, key_reader=lambda: key, workers=1)
    return j, made


def test_one_call_per_question_with_rich_choice():
    c = StubClient()
    j, _ = make(c)
    res = j.label([q(1), q(2)])
    assert len(c.calls) == 2
    call = c.calls[0]
    assert call["model"] == "jev-latest"
    assert call["state"] == {"text": "line 1"}
    qd = call["questions"]["label"]
    assert qd["type"] == "choice" and qd["instructions"] == DATA["label"]["question"]
    assert list(qd["criteria"]) == list(softdata.LABELS)
    for v in qd["criteria"].values():
        assert set(v) == {"what", "not_for", "examples"}
    r = res[0]
    assert r["qid"] == "label:a.md:1" and r["backend"] == "jev" and r["model"] == "jev-2"
    assert r["label"] == "do" and r["confidence"] == 0.9
    assert r["probabilities"]["do"] == 0.9 and r["truncated"] is False
    assert "skipped" not in r
    assert j.tokens == 200
    assert FAKE_KEY not in repr(res)


def test_no_key_skips_all_without_client():
    c = StubClient()
    j, made = make(c, key=None)
    res = j.label([q(1), q(2)])
    assert [r["skipped"] for r in res] == ["jev: no key", "jev: no key"]
    assert made == [] and c.calls == []


def test_auth_error_stops_further_calls():
    c = StubClient(fail={"line 1": AuthError("401 unauthorized")})
    j, _ = make(c)
    res = j.label([q(1), q(2), q(3)])
    assert len(c.calls) == 1
    assert all(r["skipped"] == "jev: authentication failed" for r in res)


def test_other_error_skips_only_its_question():
    c = StubClient(fail={"line 2": ValueError("boom")})
    j, _ = make(c)
    res = j.label([q(1), q(2), q(3)])
    assert "skipped" not in res[0] and "skipped" not in res[2]
    assert res[1]["skipped"].startswith("jev: ValueError")


def test_error_text_is_scrubbed_of_key():
    c = StubClient(fail={"line 1": ValueError(f"bad header {FAKE_KEY}")})
    j, _ = make(c)
    res = j.label([q(1)])
    assert FAKE_KEY not in repr(res)
    assert "***" in res[0]["skipped"]


def test_unexpected_label_is_skip():
    c = StubClient(label="maybe")
    j, _ = make(c)
    assert j.label([q(1)])[0]["skipped"] == "jev: unexpected label"


def test_read_key_env_then_registry():
    assert back_jev.read_key({"TYPESAFE_API_KEY": "e"}, registry=lambda: "r") == "e"
    assert back_jev.read_key({}, registry=lambda: "r") == "r"
    assert back_jev.read_key({}, registry=lambda: None) is None

    def boom():
        raise OSError("no value")
    assert back_jev.read_key({}, registry=boom) is None


class TwoReadClient:
    """Answers the plain read and the marked read with different distributions."""

    def __init__(self, fail_marked=False):
        self.calls = []
        self.fail_marked = fail_marked

    def system_one(self, state, questions, model):
        self.calls.append({"state": state, "questions": questions})
        marked = "marked" in state
        if marked and self.fail_marked:
            raise RuntimeError("boom")
        probs = ({"do": 0.6, "description": 0.4} if marked else {"do": 0.3, "description": 0.7})
        top = max(probs, key=probs.get)
        ans = SimpleNamespace(type="choice", choice=top, confidence=probs[top],
                              probabilities=probs)
        return SimpleNamespace(model="jev-2", usage=SimpleNamespace(input_tokens=10),
                               answers={"label": ans})


def qm(i):
    base = q(i)
    base["state_marked"] = dict(base["state"], marked=f"«line» {i}")
    return base


def test_both_reads_each_line_twice_and_averages():
    c = TwoReadClient()
    j = back_jev.Jev(DATA, client_factory=lambda k: c, key_reader=lambda: FAKE_KEY,
                     workers=1, both=True)
    [r] = j.label([qm(1)])
    assert len(c.calls) == 2
    plain, marked = c.calls
    assert "marked" not in plain["state"] and "marked" in marked["state"]
    assert DATA["label"]["marked_note"] not in plain["questions"]["label"]["instructions"]
    assert marked["questions"]["label"]["instructions"].endswith(DATA["label"]["marked_note"])
    assert r["probabilities"] == pytest.approx({"description": 0.55, "do": 0.45})
    assert r["label"] == "description" and r["confidence"] == pytest.approx(0.55)
    assert r["reads"]["plain"]["label"] == "description"
    assert r["reads"]["marked"]["label"] == "do"
    assert r["confidence_kind"] == "average of two reads"


def test_both_skips_the_line_when_either_read_fails():
    c = TwoReadClient(fail_marked=True)
    j = back_jev.Jev(DATA, client_factory=lambda k: c, key_reader=lambda: FAKE_KEY,
                     workers=1, both=True)
    [r] = j.label([qm(1)])
    assert "skipped" in r and "marked read of --both" in r["skipped"]
    assert "label" not in r


def test_without_both_one_call_and_no_note():
    c = TwoReadClient()
    j = back_jev.Jev(DATA, client_factory=lambda k: c, key_reader=lambda: FAKE_KEY, workers=1)
    [r] = j.label([qm(1)])
    assert len(c.calls) == 1 and "marked" not in c.calls[0]["state"]
    assert "reads" not in r


class SweepClient:
    def __init__(self, p_none):
        self.calls, self.p_none = [], p_none

    def system_one(self, state, questions, model):
        self.calls.append({"state": state, "questions": questions})
        probs = {"none": self.p_none, "override": 1 - self.p_none}
        top = max(probs, key=probs.get)
        ans = SimpleNamespace(type="choice", choice=top, confidence=probs[top], probabilities=probs)
        return SimpleNamespace(model="jev-2", usage=SimpleNamespace(input_tokens=5), answers={"label": ans})


def chunk(i):
    return {"qid": f"sweep:a.md:{i}", "file": "a.md", "line": i, "end_line": i + 2, "text": f"t{i}"}


def test_sweep_asks_the_sweep_question_and_flags_below_flag_p():
    c = SweepClient(0.3)
    j = back_jev.Jev(DATA, client_factory=lambda k: c, key_reader=lambda: FAKE_KEY, workers=1)
    [r] = j.sweep([chunk(1)])
    q = c.calls[0]["questions"]["label"]
    assert q["instructions"] == DATA["sweep"]["question"] and list(q["criteria"])[0] == "none"
    assert c.calls[0]["state"] == {"file": "a.md", "line": 1, "end_line": 3, "text": "t1"}
    assert r["kind"] == "override" and r["flagged"] is True and r["p_any"] == pytest.approx(0.7)
    c2 = SweepClient(0.6)
    j2 = back_jev.Jev(DATA, client_factory=lambda k: c2, key_reader=lambda: FAKE_KEY, workers=1)
    [r2] = j2.sweep([chunk(1)])
    assert r2["kind"] == "none" and r2["flagged"] is False


def test_sweep_without_key_skips_every_chunk():
    j = back_jev.Jev(DATA, client_factory=lambda k: None, key_reader=lambda: None, workers=1)
    assert all(r["skipped"] == "jev: no key" for r in j.sweep([chunk(1), chunk(5)]))


def test_flagged_sweep_never_names_none():
    class Split:
        def system_one(self, state, questions, model):
            probs = {"none": 0.45, "skip-user": 0.3, "persist": 0.25}
            ans = SimpleNamespace(type="choice", choice="none", confidence=0.45, probabilities=probs)
            return SimpleNamespace(model="jev-2", usage=None, answers={"label": ans})
    j = back_jev.Jev(DATA, client_factory=lambda k: Split(), key_reader=lambda: FAKE_KEY, workers=1)
    [r] = j.sweep([chunk(1)])
    assert r["flagged"] is True and r["kind"] == "skip-user"
