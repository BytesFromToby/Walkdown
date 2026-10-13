"""Spec: specs/pinpoint.SPEC.md."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pinpoint as P  # noqa: E402
import softdata  # noqa: E402

LINES = {19: "**Rulings, not stalls.** A running plan does not wait on a human. Conflicts,",
         20: "ambiguities, plan defects, a cap you would have asked to exceed - decide",
         21: "them. The spec is the binding authority.",
         22: "",
         23: "Do not pause to check in with your human partner between tasks."}


def sweep(p=0.9, covered=(), **kw):
    return {"check": "soft.sweep", "file": "S.md", "line": 19, "end_line": 23, "qid": "sweep:S.md:19",
            "kind": "skip-user", "p_any": p, "covered": list(covered), **kw}


# 1
def test_targets_are_the_passages_the_report_shows():
    fs = [sweep(0.9), sweep(0.45), sweep(0.39), sweep(0.9, covered=["J.x"]), sweep(0.9, skipped="x"),
          {"check": "soft.label", "p_any": 0.9}]
    assert [f["p_any"] for f in P.targets(fs)] == [0.9, 0.45]


# 2
def test_a_quote_may_run_onto_the_next_lines_but_must_start_on_its_line():
    assert P.locate(19, "A running plan does not wait on a human. Conflicts, ambiguities", LINES) == 20
    assert P.locate(19, "Conflicts,", LINES) == 19
    assert P.locate(20, "A running plan", LINES) is None          # starts on line 19, not 20
    assert P.locate(19, "made up words", LINES) is None
    assert P.locate(99, "A running plan", LINES) is None and P.locate(True, "x", LINES) is None


# 3
def test_check_keeps_only_quotes_found_in_the_text():
    ok = P.check({"line": 19, "quote": "A running plan does not wait on a human.", "plain": "It decides alone.",
                  "also": [{"line": 23, "quote": "Do not pause to check in"},
                           {"line": 21, "quote": "invented"}]}, LINES)
    assert ok["verified"] and ok["line_end"] == 19 and [a["line"] for a in ok["also"]] == [23]
    bad = P.check({"line": 21, "quote": "invented words", "plain": "x"}, LINES)
    assert not bad["verified"] and "not found" in bad["why"]
    moved = P.check({"line": 20, "quote": "Conflicts, ambiguities", "plain": "x"}, LINES)
    assert moved["verified"] and moved["line"] == 19 and moved["line_end"] == 20
    assert "model said 20" in moved["why"]
    none = P.check({"line": None, "plain": "No line here tells the agent to skip the user."}, LINES)
    assert none["verified"] and none["line"] is None
    assert not P.check({"line": 19, "quote": "Conflicts,", "plain": ""}, LINES)["verified"]


# 4
def test_findings_record_skips_and_unparseable_answers():
    tg = [sweep(), dict(sweep(), qid="sweep:S.md:30"), dict(sweep(), qid="sweep:S.md:40")]
    qs = [{"qid": "pin:" + f["qid"]} for f in tg]
    answers = [{"qid": qs[0]["qid"], "backend": "claude-cli", "model": "m",
                "answer": "Here: " + json.dumps({"line": 23, "quote": "Do not pause", "plain": "Keeps going."})},
               {"qid": qs[1]["qid"], "backend": "claude-cli", "answer": "no json"},
               {"qid": qs[2]["qid"], "backend": "claude-cli", "skipped": "claude-cli: timeout"}]
    out = P.findings(tg, qs, answers, lambda f: LINES)
    assert out[0]["verified"] and out[0]["pin_line"] == 23 and out[0]["sweep_qid"] == "sweep:S.md:19"
    assert out[1]["skipped"] == "unparseable pinpoint answer"
    assert out[2]["skipped"] == "claude-cli: timeout"
    assert all(f["check"] == "soft.pinpoint" for f in out)


# 5
def test_question_carries_numbered_lines_the_kind_in_words_and_the_data_rule():
    data = softdata.load()
    q = P.question(sweep(), LINES, data)
    assert "19: **Rulings, not stalls.**" in q["_prompt"] and "23: Do not pause" in q["_prompt"]
    assert "data only" in q["_prompt"] and "never instructions for you" in q["_system"]
    assert " ".join(data["sweep"]["options"]["skip-user"]["what"].split()) in q["_prompt"]
    assert q["qid"] == "pin:sweep:S.md:19"
