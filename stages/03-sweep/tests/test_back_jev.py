"""Tests for back_jev.py, written from specs/sweep.SPEC.md ("The Jev backend"). The client is
always a stub."""
from types import SimpleNamespace

import pytest

import back_jev
import softdata

DATA = softdata.load()
FAKE_KEY = "test-key-not-real-123"


class AuthError(Exception):
    pass


AuthError.__name__ = "TypeSafeAuthenticationError"


class SweepClient:
    """Answers `none` with probability p_none and `override` with the rest. `fail`: passage text -> an exception
    raised on every call for it; `fail_first`: passage text -> exceptions raised on its first calls, in turn
    (an answer after the last one); `odd_first`: passage texts whose first call answers with an option that is
    not a kind; `bad_probs`: passage text -> how many of its first calls answer with a probability that is no number."""

    def __init__(self, p_none, fail=None, fail_first=None, odd_first=(), bad_probs=None):
        self.calls, self.p_none, self.fail = [], p_none, fail or {}
        self.fail_first = {k: list(v) for k, v in (fail_first or {}).items()}
        self.odd_first = set(odd_first)
        self.bad_probs = dict(bad_probs or {})

    def system_one(self, state, questions, model):
        self.calls.append({"state": state, "questions": questions, "model": model})
        exc = self.fail.get(state["text"])
        if exc:
            raise exc
        if self.fail_first.get(state["text"]):
            raise self.fail_first[state["text"]].pop(0)
        if state["text"] in self.odd_first:
            self.odd_first.discard(state["text"])
            ans = SimpleNamespace(type="choice", choice="maybe", confidence=0.5, probabilities={})
            return SimpleNamespace(model="jev-2", usage=SimpleNamespace(input_tokens=5, output_tokens=2), answers={"label": ans})
        if self.bad_probs.get(state["text"]):
            self.bad_probs[state["text"]] -= 1
            ans = SimpleNamespace(type="choice", choice="none", confidence=0.5, probabilities={"none": "NaN"})
            return SimpleNamespace(model="jev-2", usage=SimpleNamespace(input_tokens=5, output_tokens=2), answers={"label": ans})
        probs = {"none": self.p_none, "override": 1 - self.p_none}
        top = max(probs, key=probs.get)
        ans = SimpleNamespace(type="choice", choice=top, confidence=probs[top], probabilities=probs)
        return SimpleNamespace(model="jev-2", usage=SimpleNamespace(input_tokens=5, output_tokens=2),
                               answers={"label": ans})


def chunk(i):
    return {"qid": f"sweep:a.md:{i}", "file": "a.md", "line": i, "end_line": i + 2, "text": f"t{i}"}


class RateLimit(Exception):
    """An SDK API error: it carries the HTTP status, and its text holds an endpoint and a request id."""

    def __init__(self, text="slow down", status=429):
        super().__init__(text)
        self.status = status


def make(client, key=FAKE_KEY, waits=None):
    """A Jev over the stub client. Nothing waits: the wait before a second try is handed to `waits`."""
    made = []

    def factory(k):
        made.append(k)
        return client
    sleep = (lambda s: None) if waits is None else waits.append
    return back_jev.Jev(DATA, client_factory=factory, key_reader=lambda: key, workers=1, sleep=sleep), made


def test_sweep_asks_the_sweep_question_and_flags_below_flag_p():
    c = SweepClient(0.3)
    j, _ = make(c)
    [r] = j.sweep([chunk(1)])
    q = c.calls[0]["questions"]["label"]
    assert c.calls[0]["model"] == "jev-latest"
    assert q["type"] == "choice" and q["instructions"] == DATA["sweep"]["question"]
    assert list(q["criteria"]) == list(DATA["sweep"]["options"]) and list(q["criteria"])[0] == "none"
    for v in q["criteria"].values():
        assert set(v) == {"what", "not_for", "examples"}
    assert c.calls[0]["state"] == {"file": "a.md", "line": 1, "end_line": 3, "text": "t1"}
    assert r["qid"] == "sweep:a.md:1" and r["backend"] == "jev" and r["model"] == "jev-2"
    assert r["kind"] == "override" and r["flagged"] is True and r["p_any"] == pytest.approx(0.7)
    assert j.usage.block() == {"input": 5, "output": 2, "calls": 1, "reported": 1} and FAKE_KEY not in repr(r)
    c2 = SweepClient(0.6)
    j2, _ = make(c2)
    [r2] = j2.sweep([chunk(1)])
    assert r2["kind"] == "none" and r2["flagged"] is False


def test_the_request_is_exactly_what_is_sent_and_holds_no_key():
    c = SweepClient(0.3)
    j, _ = make(c)
    req = j.request(chunk(4))
    assert set(req) == {"state", "questions", "model"} and FAKE_KEY not in repr(req)
    [r] = j.sweep([chunk(4)])
    assert r["request"] == req
    assert (c.calls[0]["state"], c.calls[0]["questions"], c.calls[0]["model"]) == (
        req["state"], req["questions"], req["model"])


def test_a_flagged_sweep_never_names_none():
    class Split:
        def system_one(self, state, questions, model):
            probs = {"none": 0.45, "skip-user": 0.3, "persist": 0.25}
            ans = SimpleNamespace(type="choice", choice="none", confidence=0.45, probabilities=probs)
            return SimpleNamespace(model="jev-2", usage=None, answers={"label": ans})
    j, _ = make(Split())
    [r] = j.sweep([chunk(1)])
    assert r["flagged"] is True and r["kind"] == "skip-user"


def test_an_option_that_is_not_a_kind_is_a_skip():
    class Odd:
        def system_one(self, state, questions, model):
            ans = SimpleNamespace(type="choice", choice="maybe", confidence=0.5, probabilities={})
            return SimpleNamespace(model="jev-2", usage=None, answers={"label": ans})
    j, _ = make(Odd())
    assert j.sweep([chunk(1)])[0]["skipped"] == "jev: unexpected sweep option"


def test_no_key_skips_every_chunk_and_never_builds_a_client():
    c = SweepClient(0.3)
    j, made = make(c, key=None)
    res = j.sweep([chunk(1), chunk(5)])
    assert [r["skipped"] for r in res] == ["jev: no key", "jev: no key"]
    assert made == [] and c.calls == []


def test_a_rejected_key_that_is_rejected_again_stops_the_later_calls():
    """M9 slice A: the first call is tried once more; rejected again, it stops every later call, which are
    skipped as not sent."""
    c = SweepClient(0.3, fail={"t1": AuthError("401 unauthorized")})
    j, _ = make(c)
    res = j.sweep([chunk(1), chunk(2), chunk(3)])
    assert [x["state"]["text"] for x in c.calls] == ["t1", "t1"]  # the first try and its one retry; nothing after
    assert res[0]["skipped"] == "jev: authentication failed"
    assert [r["skipped"] for r in res[1:]] == ["not sent: jev: authentication failed"] * 2
    assert res[0]["tries"]["retry"]["result"] == "no answer"
    assert res[1]["tries"]["first"] is None
    assert res[1]["tries"]["retry"] == {"result": "not tried", "why": "jev: authentication failed"}


def test_a_key_rejected_once_and_accepted_on_the_retry_stops_nothing():
    c = SweepClient(0.3, fail_first={"t1": [AuthError("401 unauthorized")]})
    j, _ = make(c)
    res = j.sweep([chunk(1), chunk(2)])
    assert all("skipped" not in r for r in res) and len(c.calls) == 3
    assert res[0]["tries"]["first"]["kind"] == "TypeSafeAuthenticationError"
    assert res[0]["tries"]["retry"] == {"result": "answered"} and "tries" not in res[1]


def test_a_key_rejected_on_the_retry_after_another_error_also_stops_the_later_calls():
    c = SweepClient(0.3, fail_first={"t1": [RateLimit("slow down"), AuthError("401")]})
    j, _ = make(c)
    res = j.sweep([chunk(1), chunk(2)])
    assert res[0]["skipped"] == "jev: authentication failed"
    assert res[1]["skipped"] == "not sent: jev: authentication failed" and len(c.calls) == 2


def test_a_call_that_fails_once_is_tried_again_after_the_wait_and_the_answer_is_used():
    waits = []
    c = SweepClient(0.3, fail_first={"t2": [RateLimit("POST https://x.invalid/v1: 429 slow down (request_id=r-1)")]})
    j, _ = make(c, waits=waits)
    res = j.sweep([chunk(1), chunk(2), chunk(3)])
    assert [x["state"]["text"] for x in c.calls] == ["t1", "t2", "t2", "t3"]
    assert waits == [DATA["retry_wait"]] == [2.0]  # the wait comes from the Library, and only the failed call waited
    assert all("skipped" not in r for r in res)
    assert res[1]["kind"] == "override" and res[1]["flagged"] is True
    t = res[1]["tries"]
    assert t["first"] == {"kind": "RateLimit", "status": 429} and t["retry"] == {"result": "answered"}
    assert "tries" not in res[0] and "tries" not in res[2]  # answered on the first try: nothing to log


def test_a_call_that_fails_twice_is_skipped_with_the_second_tries_reason_and_never_tried_a_third_time():
    c = SweepClient(0.3, fail_first={"t2": [RateLimit("first"), RateLimit("second", 503)], "t3": [OSError("x")] * 5})
    j, _ = make(c)
    res = j.sweep([chunk(1), chunk(2), chunk(3)])
    texts = [x["state"]["text"] for x in c.calls]
    assert texts.count("t2") == 2 and texts.count("t3") == 2
    assert res[1]["skipped"] == "jev: RateLimit, status 503"
    assert res[1]["tries"]["first"] == {"kind": "RateLimit", "status": 429}
    assert res[1]["tries"]["retry"] == {"result": "no answer", "kind": "RateLimit", "status": 503}
    assert res[2]["skipped"] == "jev: OSError"  # an error with no status has the kind alone
    assert "skipped" not in res[0]


def test_an_option_that_is_not_a_kind_is_tried_again_and_a_valid_answer_is_used():
    c = SweepClient(0.3, odd_first={"t1"})
    j, _ = make(c)
    [r] = j.sweep([chunk(1)])
    assert "skipped" not in r and r["kind"] == "override" and len(c.calls) == 2
    assert r["tries"]["first"]["kind"] == "unexpected option" and r["tries"]["retry"] == {"result": "answered"}
    assert j.usage.block() == {"input": 10, "output": 4, "calls": 2, "reported": 2}  # both calls were paid for


def test_a_probability_that_cannot_be_read_is_no_answer_and_is_tried_again():
    """An odd response is a call with no answer (M9): the step does not crash on it (O3 and M9 verification, 2026-10-30)."""
    c = SweepClient(0.3, bad_probs={"t1": 1})
    j, _ = make(c)
    [r] = j.sweep([chunk(1)])
    assert "skipped" not in r and r["kind"] == "override" and len(c.calls) == 2
    assert r["tries"]["first"]["kind"] == "unreadable answer" and r["tries"]["retry"] == {"result": "answered"}
    c = SweepClient(0.3, bad_probs={"t1": 2})
    j, _ = make(c)
    [r] = j.sweep([chunk(1)])
    assert r["skipped"] == "jev: unreadable answer" and len(c.calls) == 2
    assert r["tries"]["retry"]["result"] == "no answer" and r["tries"]["retry"]["kind"] == "unreadable answer"


def test_nothing_to_call_is_not_tried_again_and_nothing_waits():
    waits = []
    j, made = make(SweepClient(0.3), key=None, waits=waits)
    [r] = j.sweep([chunk(1)])
    assert r["skipped"] == "jev: no key" and waits == [] and made == []
    assert r["tries"]["first"] is None and r["tries"]["retry"] == {"result": "not tried", "why": "jev: no key"}

    def boom(key):
        raise ImportError("no typesafe_sdk")
    j = back_jev.Jev(DATA, client_factory=boom, key_reader=lambda: FAKE_KEY, workers=1, sleep=waits.append)
    [r] = j.sweep([chunk(1)])
    assert r["skipped"] == "jev: typesafe_sdk not installed" and waits == []
    assert r["tries"]["first"] is None and r["tries"]["retry"]["result"] == "not tried"


def test_another_error_skips_only_its_chunk():
    c = SweepClient(0.3, fail={"t2": ValueError("boom")})
    j, _ = make(c)
    res = j.sweep([chunk(1), chunk(2), chunk(3)])
    assert "skipped" not in res[0] and "skipped" not in res[2]
    assert res[1]["skipped"] == "jev: ValueError"


def test_a_factory_that_fails_skips_every_chunk_with_the_reason():
    def boom(key):
        raise ImportError("no typesafe_sdk")
    j = back_jev.Jev(DATA, client_factory=boom, key_reader=lambda: FAKE_KEY, workers=1)
    assert [r["skipped"] for r in j.sweep([chunk(1)])] == ["jev: typesafe_sdk not installed"]

    def refuses(key):
        raise ValueError(f"bad key {key}")  # its text could hold the key: only its class is kept
    j = back_jev.Jev(DATA, client_factory=refuses, key_reader=lambda: FAKE_KEY, workers=1)
    [r] = j.sweep([chunk(1)])
    assert r["skipped"] == "jev: ValueError" and FAKE_KEY not in repr(r)


def test_no_text_of_an_error_is_kept_neither_the_key_nor_the_passage_nor_the_models_words():
    """An SDK error's text holds an endpoint and a request id, and a service's can repeat the passage or the model's
    own words. The reason, the skip, and the call log keep the kind and the status and nothing of the text."""
    said = f"POST https://x.invalid/v1 400 echo t1 key={FAKE_KEY} the model said MODELWORDS (request_id=r-9)"
    c = SweepClient(0.3, fail={"t1": RateLimit(said, 400)})
    j, _ = make(c)
    [r] = j.sweep([chunk(1)])
    row = back_jev.calllog.rows([r])[0]
    assert r["skipped"] == "jev: RateLimit, status 400"
    assert row["first"] == {"kind": "RateLimit", "status": 400}
    assert row["retry"] == {"result": "no answer", "kind": "RateLimit", "status": 400}
    assert set(row) == {"qid", "backend", "first", "retry", "at"}
    for text in (FAKE_KEY, "MODELWORDS", "request_id", "x.invalid"):
        assert text not in repr({k: v for k, v in r.items() if k != "request"}), text
        assert text not in repr(row), text
    assert "t1" not in repr({k: v for k, v in row.items() if k != "qid"})


def test_failures_that_differ_only_in_a_request_id_have_one_reason():
    c = SweepClient(0.3, fail={f"t{i}": RateLimit(f"500 oops (request_id=r-{i})", 500) for i in (1, 2, 3)})
    j, _ = make(c)
    res = j.sweep([chunk(1), chunk(2), chunk(3)])
    assert {r["skipped"] for r in res} == {"jev: RateLimit, status 500"}


def test_chunks_are_read_in_parallel_in_order():
    c = SweepClient(0.3)
    j = back_jev.Jev(DATA, client_factory=lambda k: c, key_reader=lambda: FAKE_KEY, workers=4)
    res = j.sweep([chunk(i) for i in range(1, 8)])
    assert [r["qid"] for r in res] == [f"sweep:a.md:{i}" for i in range(1, 8)]
    assert len(c.calls) == 7


def test_a_retry_in_the_parallel_reads_keeps_the_order_and_the_log_lines_follow_the_passages():
    c = SweepClient(0.3, fail_first={"t3": [RateLimit("a")], "t6": [RateLimit("b"), RateLimit("c")]})
    j = back_jev.Jev(DATA, client_factory=lambda k: c, key_reader=lambda: FAKE_KEY, workers=4, sleep=lambda s: None)
    res = j.sweep([chunk(i) for i in range(1, 8)])
    assert [r["qid"] for r in res] == [f"sweep:a.md:{i}" for i in range(1, 8)]
    assert [r["qid"] for r in back_jev.calllog.rows(res)] == ["sweep:a.md:3", "sweep:a.md:6"]
    assert [bool(r.get("skipped")) for r in res] == [False] * 5 + [True, False]


def test_read_key_prefers_the_environment_then_the_registry():
    assert back_jev.read_key({"TYPESAFE_API_KEY": "e"}, registry=lambda: "r") == "e"
    assert back_jev.read_key({}, registry=lambda: "r") == "r"
    assert back_jev.read_key({}, registry=lambda: None) is None

    def boom():
        raise OSError("no value")
    assert back_jev.read_key({}, registry=boom) is None


def test_read_key_is_jevkeys():
    """The loaded-model build moved the key's reading to `stages/_shared/jevkey.py` (so `--reads` can ask whether Jev is
    available); `back_jev.read_key` is that function, and `Jev` still takes it as its default reader."""
    import jevkey
    assert back_jev.read_key is jevkey.read_key
    assert back_jev.Jev.__init__.__defaults__[1] is jevkey.read_key


# M9 slice A, fix round: one more try is two sends, and the wait is the Library's
def test_the_client_is_built_with_the_sdks_own_retries_off(monkeypatch):
    """The SDK retries a failed call itself (2 more sends, with backoff). Walkdown's one extra try would then make up
    to six sends, so the default factory turns the SDK's off. A fake SDK module records how the client is built."""
    import sys
    built = []

    class RetryPolicy:
        def __init__(self, max_retries=2):
            self.max_retries = max_retries

    class TypeSafeClient:
        def __init__(self, *, api_key=None, retry=None, **kw):
            built.append({"api_key": api_key, "retry": retry, "more": kw})

    monkeypatch.setitem(sys.modules, "typesafe_sdk", SimpleNamespace(RetryPolicy=RetryPolicy, TypeSafeClient=TypeSafeClient))
    back_jev._default_factory("a-key")
    [one] = built
    assert one["api_key"] == "a-key" and one["more"] == {}
    assert isinstance(one["retry"], RetryPolicy) and one["retry"].max_retries == 0


def test_the_installed_sdk_takes_the_retry_policy_the_factory_passes():
    """Reads the installed SDK's source and builds nothing: `retry` is a client option, and the SDK's default for `max_retries` is the
    2 that the factory turns off. The package is found past the test wall's stub and read as text, never imported: in a test run the
    name `typesafe_sdk` is the stub (`tests/offline`), and importing the real package is what the wall is there to stop."""
    import ast
    import sys
    from importlib.machinery import PathFinder
    from pathlib import Path
    stub = Path(__file__).resolve().parents[3] / "tests" / "offline" / "stub"
    spec = PathFinder.find_spec("typesafe_sdk", [p for p in sys.path if p and Path(p).resolve() != stub.resolve()])
    if spec is None or not spec.origin:
        pytest.skip("typesafe_sdk is not installed")
    package = Path(spec.origin).parent
    tree = ast.parse((package / "_core" / "retry.py").read_text("utf-8"))
    policy = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "RetryPolicy")
    default = next(n.value.value for n in policy.body
                   if isinstance(n, ast.AnnAssign) and getattr(n.target, "id", "") == "max_retries" and n.value is not None)
    assert default == 2  # `RetryPolicy(max_retries=0)` is the factory's way to switch the retries off
    client = ast.parse((package / "_core" / "client" / "sync" / "client.py").read_text("utf-8"))
    cls = next(n for n in ast.walk(client) if isinstance(n, ast.ClassDef) and n.name == "TypeSafeClient")
    init = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "__init__")
    assert "retry" in [a.arg for a in init.args.kwonlyargs]


def test_the_wait_before_the_second_try_is_the_one_in_the_data_and_no_number_of_the_backend():
    waits = []
    data = dict(DATA, retry_wait=7.5)
    c = SweepClient(0.3, fail_first={"t1": [RateLimit("slow")]})
    j = back_jev.Jev(data, client_factory=lambda k: c, key_reader=lambda: FAKE_KEY, workers=1, sleep=waits.append)
    [r] = j.sweep([chunk(1)])
    assert "skipped" not in r and waits == [7.5]


# M1 slice A: the tokens each call reports are added up in a `usage` block
def test_the_tokens_of_every_call_are_added_up_and_a_call_that_reports_none_adds_none():
    class Counted:
        def __init__(self):
            self.n = 0

        def system_one(self, state, questions, model):
            self.n += 1
            probs = {"none": 0.9, "override": 0.1}
            ans = SimpleNamespace(type="choice", choice="none", confidence=0.9, probabilities=probs)
            used = SimpleNamespace(input_tokens=100 * self.n, output_tokens=None) if self.n != 2 else None
            return SimpleNamespace(model="jev-2", usage=used, answers={"label": ans})
    j, _ = make(Counted())
    j.sweep([chunk(1), chunk(2), chunk(3)])
    assert j.usage.block() == {"input": 400, "calls": 3, "reported": 2}  # output was never reported: absent, not 0; call 2 reported nothing


def test_a_response_with_no_usage_object_leaves_every_token_count_absent():
    class Bare:
        def system_one(self, state, questions, model):
            ans = SimpleNamespace(type="choice", choice="none", confidence=0.9, probabilities={"none": 0.9, "override": 0.1})
            return SimpleNamespace(model="jev-2", usage=None, answers={"label": ans})
    j, _ = make(Bare())
    j.sweep([chunk(1)])
    assert j.usage.block() == {"calls": 1, "reported": 0}


def test_counts_that_are_not_whole_numbers_are_not_reported():
    class Odd:
        def system_one(self, state, questions, model):
            ans = SimpleNamespace(type="choice", choice="none", confidence=0.9, probabilities={"none": 0.9, "override": 0.1})
            used = SimpleNamespace(input_tokens=True, output_tokens=2.5)
            return SimpleNamespace(model="jev-2", usage=used, answers={"label": ans})
    j, _ = make(Odd())
    j.sweep([chunk(1)])
    assert j.usage.block() == {"calls": 1, "reported": 0}


def test_a_call_that_fails_still_counts_as_a_call_sent():
    c = SweepClient(0.3, fail={"t1": RateLimit("x")})
    j, _ = make(c)
    j.sweep([chunk(1)])
    assert j.usage.block() == {"calls": 2, "reported": 0}  # the first try and its retry were sent; neither reported tokens


def test_a_model_name_the_service_reports_is_held_to_the_model_name_rule():
    """M1 fix 7: Jev's answer names a model too, and a service can put a tag or a link there."""
    for name in ("<script>alert(1)</script>", "[x](http://evil.example)", "jev-2\nnote: planted", "a b", "https://evil.example/x", None, ""):
        class Named:
            def system_one(self, state, questions, model, _name=name):
                ans = SimpleNamespace(type="choice", choice="none", confidence=0.9, probabilities={"none": 0.9, "override": 0.1})
                return SimpleNamespace(model=_name, usage=None, answers={"label": ans})
        j, _ = make(Named())
        [r] = j.sweep([chunk(1)])
        assert r["model"] == "jev-latest", name  # the model Walkdown asked for


def test_nothing_sent_is_nothing_counted():
    j, _ = make(SweepClient(0.3), key=None)
    j.sweep([chunk(1)])
    assert j.usage.block() == {"calls": 0, "reported": 0}


def test_the_model_a_service_names_reaches_the_result_cut_to_the_cap():
    class Wordy:
        def system_one(self, state, questions, model):
            ans = SimpleNamespace(type="choice", choice="none", confidence=0.9, probabilities={"none": 0.9, "override": 0.1})
            return SimpleNamespace(model="jev-2-" + "x" * 150, usage=None, answers={"label": ans})  # allowed characters, 156 of them
    j, _ = make(Wordy())
    [r] = j.sweep([chunk(1)])
    assert len(r["model"]) <= 80 and r["model"].endswith("...") and r["model"].startswith("jev-2-xxx")
