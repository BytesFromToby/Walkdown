"""Tests for ask.py, written from specs/ask.SPEC.md."""
import ask

LQ = [
    {"qid": "label:a.md:3", "kind": "label", "file": "a.md", "line": 3, "question": "Q?",
     "state": {}, "sources": [{"stage": "04", "check": "phrase.L.override", "file": "a.md",
                               "line": 3, "patterns": ["L.ignore"]}]},
    {"qid": "label:a.md:5", "kind": "label", "file": "a.md", "line": 5, "question": "Q?",
     "state": {}, "sources": [{"stage": "04", "check": "phrase.creds", "file": "a.md",
                               "line": 5, "patterns": ["creds.path"]}]},
]
RQ = [{"qid": "rel:legs", "kind": "relational", "file": None, "line": None, "template": "legs",
       "question": "Describe.", "state": {}, "sources": []}]


def res(qid, backend, label):
    return {"qid": qid, "backend": backend, "model": backend + "-m", "label": label,
            "probabilities": {label: 0.8}, "confidence": 0.8, "truncated": False,
            "request": {}, "response": {}}


def by(fs, check):
    return [f for f in fs if f["check"] == check]


def test_no_backends_gives_skips():
    fs = ask.findings(LQ + RQ, None, None, None)
    qs = by(fs, "soft.question")
    assert [f["qid"] for f in qs] == ["label:a.md:3", "label:a.md:5", "rel:legs"]
    assert qs[0]["kind"] == "label" and qs[0]["question"] == "Q?" and qs[0]["sources"]
    labels = by(fs, "soft.label")
    assert [(f["file"], f["line"], f["skipped"]) for f in labels] == [
        ("a.md", 3, "no labeling backend"), ("a.md", 5, "no labeling backend")]
    reads = by(fs, "soft.read")
    assert reads == [{"check": "soft.read", "file": None, "line": None, "qid": "rel:legs",
                      "skipped": "no relational backend"}]
    assert not by(fs, "soft.compare") and not by(fs, "soft.agree")


def test_both_roles_and_agreement():
    p = [res("label:a.md:3", "jev", "do"), res("label:a.md:5", "jev", "description")]
    c = [res("label:a.md:3", "laya", "do"), res("label:a.md:5", "laya", "do")]
    fs = ask.findings(LQ, p, c, None)
    lab = by(fs, "soft.label")
    assert lab[0]["label"] == "do" and lab[0]["backend"] == "jev" and lab[0]["model"] == "jev-m"
    assert set(lab[0]) >= {"qid", "backend", "model", "label", "probabilities", "confidence",
                           "truncated", "file", "line"}
    assert "request" not in lab[0]
    cmp_ = by(fs, "soft.compare")
    assert [f["backend"] for f in cmp_] == ["laya", "laya"]
    agree = by(fs, "soft.agree")
    assert [(f["qid"], f["primary"], f["compare"], f["agree"]) for f in agree] == [
        ("label:a.md:3", "do", "do", True), ("label:a.md:5", "description", "do", False)]


def test_skipped_compare_gives_skip_and_no_agree():
    p = [res("label:a.md:3", "jev", "do"), res("label:a.md:5", "jev", "do")]
    c = [{"qid": "label:a.md:3", "backend": "laya", "skipped": "laya: RuntimeError: x"},
         res("label:a.md:5", "laya", "do")]
    fs = ask.findings(LQ, p, c, None)
    cmp_ = by(fs, "soft.compare")
    assert cmp_[0]["skipped"] == "laya: RuntimeError: x" and cmp_[0]["line"] == 3
    assert [f["qid"] for f in by(fs, "soft.agree")] == ["label:a.md:5"]


def test_missing_result_is_skip():
    fs = ask.findings(LQ, [res("label:a.md:3", "jev", "do")], None, None)
    assert by(fs, "soft.label")[1]["skipped"] == "no answer returned"


def test_relational_answer_verbatim():
    r = [{"qid": "rel:legs", "backend": "claude-cli", "model": "claude-x",
          "answer": "  It could read keys\nand send them.  ", "capped": False,
          "request": {}, "response": {}}]
    fs = ask.findings(RQ, None, None, r)
    read = by(fs, "soft.read")[0]
    assert read["answer"] == "  It could read keys\nand send them.  "
    assert read["backend"] == "claude-cli" and read["model"] == "claude-x"


def test_summary_counts_and_agreement():
    p = [res("label:a.md:3", "jev", "do"), res("label:a.md:5", "jev", "description")]
    c = [res("label:a.md:3", "laya", "do"), res("label:a.md:5", "laya", "do")]
    fs = ask.findings(LQ + RQ, p, c, None)
    text = "\n".join(ask.summary(LQ + RQ, fs))
    assert "2 label" in text and "1 relational" in text
    assert "agree 1 of 2" in text
    assert "do 1" in text and "description 1" in text
    assert "phrase.creds" in text
    assert "no relational backend" in text


def test_record_row():
    row = ask.record("label", res("label:a.md:3", "jev", "do"))
    assert row["role"] == "label" and row["qid"] == "label:a.md:3" and row["backend"] == "jev"
    assert "request" in row and "response" in row
    sk = ask.record("compare", {"qid": "q", "backend": "laya", "skipped": "x"})
    assert sk["skipped"] == "x"


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _keys(v)


def test_no_verdict_fields():
    p = [res("label:a.md:3", "jev", "do"), res("label:a.md:5", "jev", "do")]
    fs = ask.findings(LQ + RQ, p, p, None)
    assert not {"risk", "severity", "score", "verdict"} & set(_keys(fs))
