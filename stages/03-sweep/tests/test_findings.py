"""Tests for findings.py, written from specs/sweep.SPEC.md ("Findings")."""
import findings

CHUNKS = [
    {"qid": "sweep:a.md:1", "file": "a.md", "line": 1, "end_line": 3, "text": "t1"},
    {"qid": "sweep:a.md:5", "file": "a.md", "line": 5, "end_line": 9, "text": "t5"},
    {"qid": "sweep:b.md:1", "file": "b.md", "line": 1, "end_line": 2, "text": "t1"},
]
S4 = [{"check": "phrase.L.override", "file": "a.md", "line": 6, "patterns": ["L.ignore"]}]


def res(qid, kind="override", p_any=0.8, flagged=True):
    return {"qid": qid, "backend": "jev", "model": "jev-m", "kind": kind,
            "probabilities": {"none": round(1 - p_any, 6), kind: p_any}, "p_any": p_any,
            "flagged": flagged, "request": {"state": {}}, "response": {"answer": {}}}


def test_one_finding_per_chunk_with_where_it_is_and_what_covers_it():
    fs = findings.sweep_findings(CHUNKS, [res(c["qid"]) for c in CHUNKS], S4)
    assert [(f["file"], f["line"], f["end_line"]) for f in fs] == [
        ("a.md", 1, 3), ("a.md", 5, 9), ("b.md", 1, 2)]
    assert all(f["check"] == "soft.sweep" for f in fs)
    assert set(fs[0]) == {"check", "file", "line", "end_line", "qid", "backend", "model", "kind",
                          "probabilities", "p_any", "flagged", "covered"}
    assert [f["covered"] for f in fs] == [[], ["L.ignore"], []]
    assert "request" not in fs[0] and "response" not in fs[0]  # those are in the answers file


def test_a_skipped_or_missing_answer_is_a_skip_with_the_reason():
    results = [{"qid": CHUNKS[0]["qid"], "backend": "jev", "skipped": "jev: no key"}]
    fs = findings.sweep_findings(CHUNKS[:2], results, S4)
    assert fs[0]["skipped"] == "jev: no key" and fs[0]["backend"] == "jev" and fs[0]["end_line"] == 3
    assert fs[1]["skipped"] == "no answer returned" and fs[1]["backend"] is None


def test_no_sweep_results_means_no_findings():
    assert findings.sweep_findings(CHUNKS, None, S4) == []


def test_summary_counts_the_passages_and_names_the_skips():
    results = [res(CHUNKS[0]["qid"]), res(CHUNKS[1]["qid"]),
               {"qid": CHUNKS[2]["qid"], "backend": "jev", "skipped": "jev: no key"}]
    fs = findings.sweep_findings(CHUNKS, results, S4)
    text = "\n".join(findings.summary(fs))
    assert "sweep (jev): 2 chunks, 2 flagged, 1 of them with no stage 4 hit" in text
    assert "skipped: soft.sweep x1: jev: no key" in text


def test_record_keeps_the_request_and_the_response_verbatim():
    row = findings.record(res("sweep:a.md:1"))
    assert row["role"] == "sweep" and row["qid"] == "sweep:a.md:1" and row["backend"] == "jev"
    assert row["request"] == {"state": {}} and row["response"] == {"answer": {}}
    assert row["kind"] == "override" and row["p_any"] == 0.8 and row["flagged"] is True
    sk = findings.record({"qid": "q", "backend": "jev", "skipped": "x", "request": {"a": 1}})
    assert sk["skipped"] == "x" and sk["request"] == {"a": 1} and "kind" not in sk


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _keys(v)


def test_no_verdict_fields():
    fs = findings.sweep_findings(CHUNKS, [res(c["qid"]) for c in CHUNKS], S4)
    assert not {"risk", "severity", "score", "verdict"} & set(_keys(fs))
