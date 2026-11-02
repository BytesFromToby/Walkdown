"""Tests for validate.py, written from specs/shared.SPEC.md, validate."""
import sys

from validate import parse, stamps


def test_pass_stage():
    doc = {"stages": [{"stage": "02.4-phrases", "result": "PASS", "gate": {"passed": 31, "total": 31},
                       "negative": {"passed": 46, "total": 46}, "recall": {"found": 39, "total": 39},
                       "not_ok": []}]}
    st = parse(doc)["02.4-phrases"]
    assert st.result == "PASS" and st.gate == "31/31" and st.negative == "46/46" and st.recall == "39/39"
    assert st.text == "PASS (gate 31/31, negative 46/46, recall 39/39)"


def test_incomplete_lists_skips():
    doc = {"stages": [{"stage": "02.2-reader", "result": "INCOMPLETE", "gate": {"passed": 14, "total": 15},
                       "negative": {"passed": 12, "total": 12}, "recall": {"found": 0, "total": 0},
                       "not_ok": [{"id": "rd-img-ocr", "status": "SKIPPED"},
                                  {"id": "x", "status": "MISS"}]}]}
    st = parse(doc)["02.2-reader"]
    assert st.skipped == ["rd-img-ocr"] and st.recall is None
    assert "skipped: rd-img-ocr" in st.text and st.text.startswith("INCOMPLETE")


def test_a_stage_with_no_fixture_set_is_one_plain_result():
    """Restructure step 5, decision 5-C: the grader's `no fixture set` (zero rows) is the stamp's
    result and its whole text; it is not an error."""
    doc = {"stages": [{"stage": "04-pinpoint", "result": "no fixture set", "errors": [],
                       "gate": {"passed": 0, "total": 0}, "negative": {"passed": 0, "total": 0},
                       "recall": {"found": 0, "total": 0}, "not_ok": [], "unlisted": {}, "deferred": []}]}
    st = parse(doc)["04-pinpoint"]
    assert st.result == "no fixture set" and st.text == "no fixture set"


def test_the_real_grader_stamps_pinpoint_no_fixture_set_and_sweep_pass():
    """The grader on this repository: Pinpoint has no answer sheet and no fixtures, Sweep's sheet is
    recall rows only (not asked of a model here, so not measured)."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[3]
    got = stamps(root, sys.executable, ["03-sweep", "04-pinpoint"], cache=False)
    assert got["04-pinpoint"].result == "no fixture set" and got["04-pinpoint"].text == "no fixture set"
    assert got["03-sweep"].result == "PASS"


def test_grader_without_json_is_error(tmp_path):
    (tmp_path / "tools" / "grader").mkdir(parents=True)
    (tmp_path / "tools" / "grader" / "grader.py").write_text("print('not json')\n", encoding="utf-8")
    assert stamps(tmp_path, sys.executable, ["02.1-inventory"])["02.1-inventory"].result == "ERROR"


def test_long_skip_list_collapses():
    doc = {"stages": [{"stage": "03-sweep", "result": "PASS", "gate": {"passed": 1, "total": 1},
                       "negative": {"passed": 1, "total": 1}, "recall": {"found": 0, "total": 5},
                       "not_ok": [{"id": f"r{i}", "status": "SKIPPED"} for i in range(5)]}]}
    assert parse(doc)["03-sweep"].text.endswith("skipped: 5 rows)")


def _root(tmp_path):
    for d in ("stages/02-coded/02.1-inventory", "tools/grader", "Fixtures/02.1-inventory"):
        (tmp_path / d).mkdir(parents=True)
    (tmp_path / "stages/02-coded/02.1-inventory/run.py").write_text("x = 1\n")
    (tmp_path / "Fixtures/02.1-inventory/a.md").write_text("fixture\n")
    return tmp_path


def test_fingerprint_changes_with_code_fixtures_and_soft_choices(tmp_path):
    import validate
    root = _root(tmp_path)
    a = validate.fingerprint(root)
    assert a == validate.fingerprint(root, {"PATH": "x"})  # unrelated env ignored
    assert a != validate.fingerprint(root, {"WALKDOWN_SOFT_LABEL": "jev"})
    (root / "Fixtures/02.1-inventory/a.md").write_text("changed\n")
    b = validate.fingerprint(root)
    assert b != a
    (root / "stages/02-coded/02.1-inventory/run.py").write_text("x = 2\n")
    assert validate.fingerprint(root) != b


def test_fingerprint_keys_on_the_stages_the_grader_the_fixtures_and_the_library(tmp_path):
    """Restructure step 7: the grader is in tools/grader; the fingerprint keys on exactly those four."""
    import validate
    assert validate.FINGERPRINT_DIRS == ("stages", "tools/grader", "Fixtures", "Library")
    root = _root(tmp_path)
    a = validate.fingerprint(root)
    (root / "tools/grader/grader.py").write_text("x = 1\n")
    assert validate.fingerprint(root) != a  # a change to the grader re-measures every stage


def test_fingerprint_covers_the_library(tmp_path):
    """Restructure step 3: the tables moved out of the stage folders into Library/, so a change to
    one must re-measure every stage, not reuse a cached stamp."""
    import validate
    assert "Library" in validate.FINGERPRINT_DIRS
    root = _root(tmp_path)
    (root / "Library").mkdir()
    (root / "Library/fit.yaml").write_text("checked: 2026-10-26\n")
    a = validate.fingerprint(root)
    (root / "Library/fit.yaml").write_text("checked: 2026-10-29\n")
    b = validate.fingerprint(root)
    assert b != a
    (root / "Library/new.yaml").write_text("x: 1\n")  # a new file counts too
    assert validate.fingerprint(root) != b


def test_fingerprint_changes_when_an_optional_tool_appears(tmp_path, monkeypatch):
    import validate
    root = _root(tmp_path)
    monkeypatch.setattr(validate, "optional_tools", lambda: "tesseract=0")
    a = validate.fingerprint(root)
    monkeypatch.setattr(validate, "optional_tools", lambda: "tesseract=1")
    assert validate.fingerprint(root) != a


def test_cached_stamp_is_reused_and_says_so(tmp_path):
    import json
    import sys
    import validate
    root = _root(tmp_path)
    fp = validate.fingerprint(root)
    (root / ".cache").mkdir()
    (root / ".cache/stamps.json").write_text(json.dumps({f"02.1-inventory|{fp}": {
        "result": "PASS", "gate": "3/3", "negative": "1/1", "recall": None, "skipped": [],
        "date": "2026-10-03"}}))
    # no grader.py exists here: a cache miss would give ERROR
    got = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
    assert got.result == "PASS" and got.cached == "2026-10-03"
    assert "measured 2026-10-03, same code and fixtures" in got.text
    fresh = validate.stamps(root, sys.executable, ["02.1-inventory"], cache=False)["02.1-inventory"]
    assert fresh.result == "ERROR" and fresh.cached is None


def _fake_grader(root):
    """A grader that prints the result in `ctl/result.txt` for the stage it is asked about and counts each run in
    `ctl/runs.txt`. The controls are outside the folders the fingerprint reads, so changing them keeps the fingerprint."""
    (root / "ctl").mkdir(exist_ok=True)
    (root / "tools/grader/grader.py").write_text(
        "import json, sys\nfrom pathlib import Path\n"
        "ctl = Path(__file__).resolve().parents[2] / 'ctl'\n"
        "with open(ctl / 'runs.txt', 'a') as f:\n    f.write('x')\n"
        "result = (ctl / 'result.txt').read_text().strip()\n"
        "print(json.dumps({'stages': [{'stage': sys.argv[1], 'result': result, "
        "'gate': {'passed': 1, 'total': 1}, 'not_ok': []}]}))\n", encoding="utf-8")


def _runs(root):
    return len((root / "ctl/runs.txt").read_text()) if (root / "ctl/runs.txt").exists() else 0


def test_only_a_pass_an_incomplete_and_a_no_fixture_set_are_cached(tmp_path):
    """M9 slice B fix round: a FAIL, SETUP ERROR, NOT BUILT, or ERROR can come from the machine (a killed process, a
    full disk) and not the code, so it is graded again at the next run; the cache never keeps it."""
    import validate
    root = _root(tmp_path)
    _fake_grader(root)
    for result in ("FAIL", "SETUP ERROR", "NOT BUILT"):
        (root / "ctl/result.txt").write_text(result)
        before = _runs(root)
        first = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
        second = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
        assert first.result == second.result == result and second.cached is None, result
        assert _runs(root) - before == 2, result  # graded at each call
    for result in ("PASS", "INCOMPLETE", "no fixture set"):
        (root / "ctl/result.txt").write_text(result)
        before = _runs(root)
        validate.stamps(root, sys.executable, ["02.1-inventory"])
        again = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
        assert again.result == result and again.cached is not None, result
        assert _runs(root) - before == 1, result  # measured once, then reused
        (root / ".cache/stamps.json").unlink()


def test_a_failed_stamp_left_in_the_cache_by_an_older_version_is_not_reused(tmp_path):
    import json
    import validate
    root = _root(tmp_path)
    _fake_grader(root)
    (root / "ctl/result.txt").write_text("PASS")
    fp = validate.fingerprint(root)
    (root / ".cache").mkdir()
    (root / ".cache/stamps.json").write_text(json.dumps({f"02.1-inventory|{fp}": {
        "result": "FAIL", "gate": "0/1", "negative": None, "recall": None, "skipped": [], "date": "2026-10-03"}}))
    got = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
    assert got.result == "PASS" and got.cached is None and _runs(root) == 1


def test_a_stamp_measures_a_none_only_when_it_is_a_pass_with_rows_asked_and_not_skipped():
    """M9 slice C, fix round: the rule `checked N, found none` rests on. A sweep with no key reads `recall 0/32` with all 32 rows
    skipped (the fractions count them), so nothing was measured."""
    from validate import Stamp
    assert Stamp("PASS", "1/1").measured and Stamp("PASS", None, "2/2").measured and Stamp("PASS", None, None, "5/8").measured
    assert Stamp("INCOMPLETE", "30/31", skipped=["rd-img-ocr"]).measured
    assert not Stamp("INCOMPLETE", "1/1", skipped=["a"]).measured  # the one row was skipped
    assert not Stamp("PASS", None, None, "0/32", skipped=[f"r{i}" for i in range(32)]).measured
    assert Stamp("PASS", None, None, "3/32", skipped=[f"r{i}" for i in range(29)]).measured
    for result in ("FAIL", "ERROR", "SETUP ERROR", "NOT BUILT", "no fixture set"):
        assert not Stamp(result, "1/1").measured, result
    assert not Stamp("PASS").measured and not Stamp("INCOMPLETE").measured


def test_a_count_that_is_not_passed_over_total_is_a_stamp_that_measured_nothing_and_no_traceback():
    """A stamp read from a tampered or damaged record: `abc`, `3`, `3/x`, an empty total. It is not measured, and the run that reads
    it goes on (it ended `stage 05-qa failed` before)."""
    from validate import Stamp
    for bad in ("abc", "3", "3/x", "/", "3/", "x/y/z", 7):
        assert not Stamp("PASS", bad).measured, bad
        assert not Stamp("PASS", "1/1", bad).measured, bad
        assert not Stamp("INCOMPLETE", None, None, bad).measured, bad
    assert Stamp("PASS", "1/1").measured


# ---------------------------------------------------------------- M1 slice A: the tokens a fixture check spent ride on the stamp

SPENT = {"input": 39823, "output": 1200, "calls": 36}


def test_the_grader_documents_usage_is_the_stamps_and_it_changes_no_other_word_of_it():
    doc = {"stages": [{"stage": "03-sweep", "result": "PASS", "gate": {"passed": 0, "total": 0}, "negative": {"passed": 0, "total": 0},
                      "recall": {"found": 31, "total": 32}, "not_ok": [], "usage": SPENT}]}
    st = parse(doc)["03-sweep"]
    assert st.usage == SPENT and st.recall == "31/32"
    without = dict(doc["stages"][0])
    del without["usage"]
    assert st.text == parse({"stages": [without]})["03-sweep"].text == "PASS (recall 31/32)"  # tokens are not in the stamp's words
    assert parse({"stages": [without]})["03-sweep"].usage is None


def test_a_usage_the_grader_prints_that_is_not_counts_of_whole_numbers_is_no_usage():
    for bad in ("many", 3, [1], None, {"input": True}, {"output": 1.5}, {"calls": -1}, {"input": "5"}, {}):
        doc = {"stages": [{"stage": "03-sweep", "result": "PASS", "recall": {"found": 1, "total": 1}, "not_ok": [], "usage": bad}]}
        assert parse(doc)["03-sweep"].usage is None, bad


def test_a_stamp_keeps_its_usage_in_the_record_only_when_it_spent_some():
    from validate import Stamp
    spent = Stamp("PASS", None, None, "31/32", usage=dict(SPENT))
    assert spent.to_dict()["usage"] == SPENT and Stamp.from_dict(spent.to_dict()).usage == SPENT
    none = Stamp("PASS", "1/1")
    assert "usage" not in none.to_dict()  # a stamp that spent none is the record it always was
    assert Stamp.from_dict(none.to_dict()).usage is None and Stamp.from_dict({"result": "PASS"}).usage is None
    assert spent.to_dict()["usage"] is not spent.usage  # the record holds a copy


def test_a_record_with_a_usage_that_cannot_be_read_is_a_stamp_that_spent_none_and_no_traceback():
    from validate import Stamp
    for bad in ("many", 3, [1], {"input": True}, {"output": 1.5}, {"cache_read": -1}, {"calls": "2"}, {}):
        assert Stamp.from_dict({"result": "PASS", "usage": bad}).usage is None, bad


def _fake_grader_with_usage(root, usage):
    (root / "ctl").mkdir(exist_ok=True)
    (root / "tools/grader/grader.py").write_text(
        "import json, sys\n"
        f"print(json.dumps({{'stages': [{{'stage': sys.argv[1], 'result': 'PASS', 'gate': {{'passed': 1, 'total': 1}}, "
        f"'not_ok': [], 'usage': {usage!r}}}]}}))\n", encoding="utf-8")


def test_the_cache_never_keeps_the_tokens_of_the_run_that_measured_the_stamp(tmp_path):
    import json
    import validate
    root = _root(tmp_path)
    _fake_grader_with_usage(root, SPENT)
    first = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
    assert first.usage == SPENT and first.cached is None  # measured in this run: it spent them
    saved = json.loads((root / ".cache/stamps.json").read_text())
    assert all("usage" not in entry for entry in saved.values())  # and the cache does not keep them
    again = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
    assert again.cached is not None and again.usage is None  # reused: it spent none this run
    a_cache_an_older_hand_wrote = {k: {**v, "usage": SPENT} for k, v in saved.items()}
    (root / ".cache/stamps.json").write_text(json.dumps(a_cache_an_older_hand_wrote))
    assert validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"].usage is None  # whatever the file says
    redone = validate.stamps(root, sys.executable, ["02.1-inventory"], cache=False)["02.1-inventory"]
    assert redone.usage == SPENT and redone.cached is None  # --revalidate measures again, so it spends again


def test_the_fingerprint_holds_the_model_as_the_person_typed_it(tmp_path):
    """A stamp is measured for the model it was run on, and a model's name keeps its case, so `claude-cli:A` and `claude-cli:a`
    are two stamps."""
    import validate
    root = _root(tmp_path)
    prints = {v: validate.fingerprint(root, {"WALKDOWN_SOFT_SWEEP": v}) for v in ("jev", "claude-cli", "claude-cli:Model-A", "claude-cli:model-a")}
    assert len(set(prints.values())) == 4
    assert validate.fingerprint(root, {"WALKDOWN_SOFT_SWEEP": "claude-cli", "WALKDOWN_SOFT_CLAUDE_MODEL": "x"}) != prints["claude-cli"]


def test_a_stamp_that_measured_nothing_is_not_kept_so_the_next_run_measures_again(tmp_path):
    """A model read whose every fixture row was skipped (no key, no login, no program) is a PASS that measured nothing. The person
    may fix that and run again; the cache must not hand the same stamp back (M1 slice A)."""
    import json
    import validate
    root = _root(tmp_path)
    (root / "ctl").mkdir()
    rows = ", ".join(f"{{'id': 'r{i}', 'status': 'SKIPPED'}}" for i in range(3))
    (root / "tools/grader/grader.py").write_text(
        "import json, sys\nfrom pathlib import Path\n"
        "with open(Path(__file__).resolve().parents[2] / 'ctl' / 'runs.txt', 'a') as f:\n    f.write('x')\n"
        "print(json.dumps({'stages': [{'stage': sys.argv[1], 'result': 'PASS', 'gate': {'passed': 0, 'total': 0}, "
        f"'recall': {{'found': 0, 'total': 3}}, 'not_ok': [{rows}]}}]}}))\n", encoding="utf-8")
    first = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
    assert first.result == "PASS" and not first.measured
    again = validate.stamps(root, sys.executable, ["02.1-inventory"])["02.1-inventory"]
    assert again.cached is None and _runs(root) == 2  # graded both times
    assert not (root / ".cache/stamps.json").exists() or not json.loads((root / ".cache/stamps.json").read_text())


def test_the_fingerprint_does_not_ask_for_gitleaks():
    """No stage runs it, so a copy on the machine changes no stamp."""
    import validate
    assert "gitleaks" not in validate.optional_tools()
