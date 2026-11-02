"""Tests for record.py, written from specs/shared.SPEC.md, record."""
import datetime as dt
import json
import os

import pytest

import pipeline
import record
from validate import Stamp


def at(hour, minute=0, day=29):
    """A UTC time on 2026-10-<day>, as the record writes it (ISO, seconds)."""
    return dt.datetime(2026, 10, day, hour, minute, tzinfo=dt.timezone.utc).replace(microsecond=0)


def make_run(parent, name, started=None, finished=None, log=True, mtime=None):
    """A run folder: a record when `started` and `finished` are given (datetimes), a LOG.md when `log` (with
    its modification time set to `mtime`, a datetime), nothing else."""
    d = parent / name
    (d / "data").mkdir(parents=True)
    if started is not None:
        step = pipeline.StageRun("01-intake", True, started.isoformat(), started.isoformat())
        record.write(d, [step], {}, 32000, [], finished.isoformat())
    if log:
        (d / "LOG.md").write_text("x", encoding="utf-8")
        if mtime is not None:
            os.utime(d / "LOG.md", (mtime.timestamp(), mtime.timestamp()))
    return d


def names(paths):
    return [p.name for p in paths]


def test_a_record_reads_back_what_was_written(tmp_path):
    (tmp_path / "data").mkdir()
    steps = [pipeline.StageRun("01-intake", True, "t0", "t1"),
             pipeline.StageRun("02.1-inventory", False, "t1", None, None, ["x"], "exit 1: boom")]
    stamps = {"01-intake": Stamp("PASS", "1/1", "2/2"),
              "02.2-reader": Stamp("INCOMPLETE", "3/4", None, "1/1", ["a"], cached="2026-10-03"),
              "04-pinpoint": Stamp("no fixture set")}
    path = record.write(tmp_path, steps, stamps, 8000, ["codex"], "t9")
    assert path == tmp_path / "data" / "run.json"
    rec = record.read(tmp_path)
    assert (rec["context"], rec["hosts"], rec["finished"], rec["format"]) == (8000, ["codex"], "t9", 3)
    assert record.FORMAT == 3  # 3 since M9 slice B: a run has data/05-qa.json, and section 7 is drawn from it
    assert rec["steps"] == [{"stage": "01-intake", "ok": True, "started": "t0", "finished": "t1", "error": None},
                            {"stage": "02.1-inventory", "ok": False, "started": "t1", "finished": None,
                             "error": "exit 1: boom"}]
    back = record.stamps_of(rec)
    assert {k: v.text for k, v in back.items()} == {k: v.text for k, v in stamps.items()}
    assert back["02.2-reader"].skipped == ["a"] and back["02.2-reader"].cached == "2026-10-03"
    assert record.stamps_of({}) == {}  # a run made without validation


def test_a_missing_unreadable_or_other_format_record_reads_as_none(tmp_path):
    assert record.read(tmp_path) is None
    (tmp_path / "data").mkdir()
    assert record.read(tmp_path) is None
    (tmp_path / "data" / "run.json").write_text("not json", encoding="utf-8")
    assert record.read(tmp_path) is None
    for other in (1, 2, 4):  # older formats (step 7, step 7b to M9 slice A), and one from a version that does not exist yet
        (tmp_path / "data" / "run.json").write_text(json.dumps({"format": other}), encoding="utf-8")
        assert record.read(tmp_path) is None
    (tmp_path / "data" / "run.json").write_text(json.dumps([1]), encoding="utf-8")
    assert record.read(tmp_path) is None


def as_format(run_dir, fmt):
    """Rewrite a run's record as another format's (the times and results stay as they were)."""
    path = run_dir / "data" / "run.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**doc, "format": fmt}), encoding="utf-8")


def test_a_run_is_made_before_this_version_unless_its_record_has_the_current_format(tmp_path):
    """Restructure step 7b: the one rule for re-rendering and comparing a run that is not the one being made."""
    p = tmp_path / "RepoResults" / "demo"
    current = make_run(p, "2026-10-29_aaaaaaa", at(9), at(9, 5))
    none = make_run(p, "2026-10-28_bbbbbbb")                              # between step 1 and step 7: no record
    older = make_run(p, "2026-10-27_ccccccc", at(8, day=27), at(8, 5, day=27))
    as_format(older, 1)                                                   # between step 7 and step 7b
    garbled = make_run(p, "2026-10-26_ddddddd")
    (garbled / "data" / "run.json").write_text("not json", encoding="utf-8")
    nowhere = tmp_path / "RepoResults" / "demo" / "2026-10-25_eeeeeee"    # not even a folder
    assert not record.made_before(current) and record.read(current)["format"] == record.FORMAT
    assert all(record.made_before(d) for d in (none, older, garbled, nowhere))
    assert record.read_any(older)["format"] == 1 and record.read(older) is None  # still readable, not current
    assert record.read_any(none) is None and record.read_any(garbled) is None


def test_a_record_of_an_older_format_still_orders_its_run_by_the_times_in_it(tmp_path):
    """Only re-rendering and comparing ask for the current format. The run made at 08:00 has a format 1 record and
    a log that was touched at 20:00; ordered by the log it would come after the run made at 09:00."""
    p = tmp_path / "RepoResults" / "demo"
    older = make_run(p, "2026-10-29_bbbbbbb", at(8), at(8, 5), mtime=at(20))
    newer = make_run(p, "2026-10-29_aaaaaaa", at(9), at(9, 5), mtime=at(9, 6))
    as_format(older, 1)
    assert record.made_before(older) and not record.made_before(newer)
    assert record.times(older) == (at(8).timestamp(), at(8, 5).timestamp())  # from the record, not the log
    assert names(record.earlier_runs(newer)) == [older.name] and record.previous_run(newer) == older.resolve()
    assert record.earlier_runs(older) == [] and record.previous_run(older) is None


# ---- which run came before this one (restructure step 7, notes F2; round 2: by time, not by name)

def test_two_runs_on_one_day_are_ordered_by_time_and_not_by_commit_hash(tmp_path):
    """The names start with the date and end with the commit's hash, so two runs on one day sort by hash.
    This afternoon's run (hash `aaaaaaa`, sorts first) must compare with this morning's (`bbbbbbb`), not
    with yesterday's."""
    p = tmp_path / "RepoResults" / "demo"
    yesterday = make_run(p, "2026-10-28_ccccccc", at(9, day=28), at(9, 5, day=28))
    morning = make_run(p, "2026-10-29_bbbbbbb", at(8), at(8, 5))
    afternoon = make_run(p, "2026-10-29_aaaaaaa", at(15), at(15, 5))
    assert "2026-10-29_aaaaaaa" < "2026-10-29_bbbbbbb"  # the name order is the wrong order
    assert names(record.earlier_runs(afternoon)) == [morning.name, yesterday.name]
    assert record.previous_run(afternoon) == morning.resolve()
    assert names(record.earlier_runs(morning)) == [yesterday.name]  # the afternoon run is later: not earlier
    assert record.previous_run(yesterday) is None
    # the same through the finish times, whatever the log files' times say
    for d in (yesterday, morning, afternoon):
        os.utime(d / "LOG.md", (1, 1))
    assert record.previous_run(afternoon) == morning.resolve()


def test_a_suffix_counts_as_a_number_and_a_tie_in_time_is_broken_by_it(tmp_path):
    """`-10` sorts before `-2` as text. Runs filed in the same second (the clock's resolution) are ordered
    by the number of the suffix; a name with none is the first."""
    p = tmp_path / "RepoResults" / "demo"
    same = at(10)
    runs = {n: make_run(p, f"2026-10-29_abc1234{n}", same, same) for n in ("", "-2", "-3", "-9", "-10", "-11")}
    ten = runs["-10"]
    assert names(record.earlier_runs(ten)) == [f"2026-10-29_abc1234{n}" for n in ("-9", "-3", "-2", "")]
    assert record.previous_run(ten).name == "2026-10-29_abc1234-9"
    assert record.previous_run(runs["-2"]).name == "2026-10-29_abc1234"
    assert record.previous_run(runs["-11"]).name == "2026-10-29_abc1234-10"
    # runs with no record, filed at the same time, are ordered the same way
    q = tmp_path / "RepoResults" / "old"
    for n in ("", "-2", "-10"):
        make_run(q, f"2026-10-20_abc1234{n}", mtime=at(10))
    assert names(record.earlier_runs(q / "2026-10-20_abc1234-10")) == ["2026-10-20_abc1234-2", "2026-10-20_abc1234"]


def test_a_run_made_before_this_version_is_ordered_by_its_logs_time_beside_a_new_one(tmp_path):
    p = tmp_path / "RepoResults" / "demo"
    old = make_run(p, "2026-10-29_zzzzzzz", mtime=at(7))  # no record: its LOG.md's time, as the comparison used
    new = make_run(p, "2026-10-29_aaaaaaa", at(9), at(9, 5))
    assert record.times(old) == (pytest.approx(at(7).timestamp()), pytest.approx(at(7).timestamp()))
    assert record.times(new) == (at(9).timestamp(), at(9, 5).timestamp())
    assert record.previous_run(new) == old.resolve()  # its name sorts after the new run's; its time is before
    # an old run whose log is newer than the new run's start is not earlier than it
    os.utime(old / "LOG.md", (at(12).timestamp(), at(12).timestamp()))
    assert record.previous_run(new) is None
    # an old run beside an old run: the log times decide, and a record's finish beats a log's time
    other = make_run(p, "2026-10-28_yyyyyyy", mtime=at(6, day=28))
    assert names(record.earlier_runs(old)) == [new.name, other.name]  # now the newest of the three
    assert names(record.earlier_runs(other)) == []
    os.utime(new / "LOG.md", (1, 1))  # a re-render appends to the log; the finish in the record does not move
    assert record.times(new)[1] == at(9, 5).timestamp()


def test_an_older_run_without_a_record_rendered_again_later_does_not_come_after_a_newer_one(tmp_path):
    """Round 3 (R1): v0.3.1 appended to LOG.md on a re-render, so the log's time of an older run can be the
    newest. A run without a record is ordered by the date in its folder name first."""
    p = tmp_path / "RepoResults" / "demo"
    older = make_run(p, "2026-10-10_ddddddd", mtime=at(9, day=27))  # made on 10-10, re-rendered on 10-27
    newer = make_run(p, "2026-10-20_eeeeeee", mtime=at(9, day=20))
    assert os.stat(older / "LOG.md").st_mtime > os.stat(newer / "LOG.md").st_mtime
    assert names(record.earlier_runs(newer)) == [older.name] and record.previous_run(newer) == older.resolve()
    assert record.earlier_runs(older) == [] and record.previous_run(older) is None
    # on the same date the log's time does decide, and the name breaks a tie
    morning = make_run(p, "2026-10-20_aaaaaaa", mtime=at(8, day=20))
    assert names(record.earlier_runs(newer)) == [morning.name, older.name]
    assert names(record.earlier_runs(morning)) == [older.name]
    # copying a results folder without file times (every log now has the same time) changes nothing across dates
    for d in (older, newer, morning):
        os.utime(d / "LOG.md", (at(12, day=29).timestamp(),) * 2)
    assert names(record.earlier_runs(newer)) == [morning.name, older.name]  # same date, same time: the name decides
    assert record.earlier_runs(older) == []


def test_runs_with_and_without_a_record_are_ordered_across_dates(tmp_path):
    """A run with no record is compared with a recorded one by its folder date first; on the same date, the
    record's start time against the log's time. Two recorded runs go by the times in their records."""
    p = tmp_path / "RepoResults" / "demo"
    r1 = make_run(p, "2026-10-10_1111111", mtime=at(9, day=27))        # no record; its log is the newest file
    a = make_run(p, "2026-10-15_aaaaaaa", at(9, day=15), at(9, 5, day=15))
    r2 = make_run(p, "2026-10-20_2222222", mtime=at(10, day=20))       # no record
    b = make_run(p, "2026-10-20_bbbbbbb", at(15, day=20), at(15, 5, day=20))  # same date as r2, later in the day
    c = make_run(p, "2026-10-25_ccccccc", at(9, day=25), at(9, 5, day=25))
    r3 = make_run(p, "2026-10-25_3333333", mtime=at(11, day=25))       # no record; same date as c, after its start
    d = make_run(p, "2026-10-26_ddddddd", at(8, day=26), at(8, 5, day=26))
    assert names(record.earlier_runs(d)) == [r3.name, c.name, b.name, r2.name, a.name, r1.name]
    assert names(record.earlier_runs(r3)) == [c.name, b.name, r2.name, a.name, r1.name]
    assert names(record.earlier_runs(c)) == [b.name, r2.name, a.name, r1.name]  # r3 is later: not earlier
    assert names(record.earlier_runs(b)) == [r2.name, a.name, r1.name]
    assert names(record.earlier_runs(r2)) == [a.name, r1.name]  # b started later the same day
    assert names(record.earlier_runs(a)) == [r1.name] and record.earlier_runs(r1) == []
    assert record.previous_run(d) == r3.resolve() and record.previous_run(c) == b.resolve()
    # the record's finish moves nothing about a run without one, and a re-render of a recorded run touches only its log
    os.utime(a / "LOG.md", None)
    os.utime(r1 / "LOG.md", None)
    assert names(record.earlier_runs(d)) == [r3.name, c.name, b.name, r2.name, a.name, r1.name]


def test_a_rerender_never_picks_itself_or_a_later_run(tmp_path):
    p = tmp_path / "RepoResults" / "demo"
    a = make_run(p, "2026-10-27_aaaaaaa", at(8, day=27), at(8, 5, day=27))
    b = make_run(p, "2026-10-28_bbbbbbb", at(8, day=28), at(8, 5, day=28))
    c = make_run(p, "2026-10-29_ccccccc", at(8), at(8, 5))
    # the middle run is rendered again after the last one exists, and its log is touched
    os.utime(b / "LOG.md", None)
    assert names(record.earlier_runs(b)) == [a.name] and record.previous_run(b) == a.resolve()
    assert names(record.earlier_runs(a)) == [] and record.previous_run(a) is None
    assert names(record.earlier_runs(c)) == [b.name, a.name]
    for d in (a, b, c):
        assert d.resolve() not in record.earlier_runs(d)


def test_a_run_in_progress_a_folder_with_no_times_and_another_repository_are_handled(tmp_path):
    p = tmp_path / "RepoResults" / "demo"
    newest = make_run(p, "2026-10-29_ccccccc", at(8), at(8, 5))
    (p / ".running-2026-10-28").mkdir()  # a run in progress is never one
    (p / "stray.txt").write_text("x", encoding="utf-8")
    bare = make_run(p, "2026-10-01_aaaaaaa", log=False)  # no LOG.md, no record: it has no times
    done = make_run(p, "2026-10-02_bbbbbbb", at(8, day=2), at(8, 5, day=2))
    make_run(tmp_path / "RepoResults" / "other", "2026-10-28_ddddddd", at(8, day=28), at(8, 5, day=28))
    assert names(record.earlier_runs(newest)) == [done.name, bare.name]  # a folder with no times is the oldest
    assert record.previous_run(newest) == done.resolve()  # and is never the previous run: it has no LOG.md
    assert record.previous_run(done) is None
    assert record.earlier_runs(tmp_path / "RepoResults" / "nowhere" / "2026-01-01_x") == []
    # folders with no times at all are ordered by name, as the marks of such runs always were
    q = tmp_path / "RepoResults" / "bare"
    for n in ("2026-01-01_a", "2026-01-02_b", "2026-01-03_c", "2026-01-04_d"):
        make_run(q, n, log=False)
    assert names(record.earlier_runs(q / "2026-01-03_c")) == ["2026-01-02_b", "2026-01-01_a"]


def test_a_record_without_times_falls_back_to_the_log(tmp_path):
    d = make_run(tmp_path, "2026-10-29_abc1234", mtime=at(11))
    (d / "data" / "run.json").write_text(json.dumps({"format": 1, "steps": [], "finished": "not a time"}),
                                         encoding="utf-8")
    assert record.times(d) == (pytest.approx(at(11).timestamp()), pytest.approx(at(11).timestamp()))
    only_finish = make_run(tmp_path, "2026-10-29_def5678", log=False)
    (only_finish / "data" / "run.json").write_text(
        json.dumps({"format": 1, "steps": [], "finished": at(12).isoformat()}), encoding="utf-8")
    assert record.times(only_finish) == (at(12).timestamp(), at(12).timestamp())


# ---------------------------------------------------------------- a stop (O3)

def stopped_run(parent, name, started, finished, until, prepared=None):
    """A run with a record, as the runner writes it for `--until`."""
    d = make_run(parent, name, started, finished)
    step = pipeline.StageRun("01-intake", True, started.isoformat(), started.isoformat())
    record.write(d, [step], {}, 32000, [], finished.isoformat(), version="0.4.0 (abc1234)", until=until,
                 prepared=prepared)
    return d


def test_not_started_is_written_when_there_is_one_and_read_back(tmp_path):
    """M9 slice A: a chosen Pinpoint that was not started because the Sweep got no answer. (The key was added at format 2.)"""
    (tmp_path / "data").mkdir()
    steps = [pipeline.StageRun("01-intake", True, "t0", "t1")]
    held = [{"stage": "04-pinpoint", "why": "sweep-no-answer"}]
    record.write(tmp_path, steps, {}, 32000, [], "t9", not_started=held)
    rec = record.read(tmp_path)
    assert rec["format"] == record.FORMAT == 3 and rec["not_started"] == held
    record.write(tmp_path, steps, {}, 32000, [], "t9")
    assert "not_started" not in record.read(tmp_path)  # every chosen step was started; so it reads for every older run


def test_a_stop_is_written_and_read_back(tmp_path):
    (tmp_path / "data").mkdir()
    steps = [pipeline.StageRun("01-intake", True, "t0", "t1")]
    prepared = {"stage": "03-sweep", "items": 12, "backend": "jev"}
    went_on = [{"after": "02.3-graph", "at": "t5"}]
    record.write(tmp_path, steps, {}, 32000, [], "t9", version="0.4.0 (abc1234)", until="02.6-builder",
                 prepared=prepared, continued=went_on, code="0123456789abcdef")
    rec = record.read(tmp_path)
    assert rec["format"] == record.FORMAT == 3  # no `until` is a run that went through
    assert (rec["version"], rec["code"], rec["until"], rec["prepared"], rec["continued"]) == (
        "0.4.0 (abc1234)", "0123456789abcdef", "02.6-builder", prepared, went_on)
    assert record.stop_of(rec) == {"after": "02.6-builder", "prepared": prepared}
    # a run that went through has none of the three keys, and every record written before has none either
    record.write(tmp_path, steps, {}, 32000, [], "t9", version="0.4.0 (abc1234)")
    rec = record.read(tmp_path)
    assert "until" not in rec and "prepared" not in rec and "continued" not in rec and rec["version"]
    assert record.stop_of(rec) is None
    record.write(tmp_path, steps, {}, 32000, [], "t9")
    assert "version" not in record.read(tmp_path) and "code" not in record.read(tmp_path)
    assert record.stop_of(record.read(tmp_path)) is None
    assert record.stop_of({"until": "02.3-graph"}) == {"after": "02.3-graph", "prepared": None}
    assert record.stop_of({"until": "99-unknown"}) is None and record.stop_of(None) is None
    assert record.stop_of({"until": ""}) is None


def test_stopped_early_is_a_stop_before_the_last_coded_step(tmp_path):
    p = tmp_path / "RepoResults" / "demo"
    assert not record.stopped_early(make_run(p, "2026-10-29_a000001", at(8), at(9)))  # went through
    for i, (until, early) in enumerate((("01-intake", True), ("02.1-inventory", True), ("02.5-capability", True),
                                        ("02.6-builder", False), ("03-sweep", False)), 2):
        d = stopped_run(p, f"2026-10-0{i}_{i:07d}", at(8), at(9), until)
        assert record.stopped_early(d) is early, until
    old = make_run(p, "2026-10-01_b000002", log=False)  # a run with no record is not "stopped early"
    assert not record.stopped_early(old) and not record.stopped_early(p / "nothing-here")


def test_the_previous_run_skips_a_run_that_stopped_before_its_coded_steps_were_done(tmp_path):
    p = tmp_path / "RepoResults" / "demo"
    full = make_run(p, "2026-10-26_aaaaaaa", at(8, day=26), at(9, day=26))
    early = stopped_run(p, "2026-10-27_bbbbbbb", at(8, day=27), at(9, day=27), "02.3-graph")
    intake = stopped_run(p, "2026-10-28_stopped", at(8, day=28), at(9, day=28), "01-intake")
    now = make_run(p, "2026-10-29_ccccccc", at(8), at(9))
    assert record.previous_run(now) == full.resolve()  # the last run that went through its coded steps
    assert names(record.earlier_runs(now)) == [intake.name, early.name, full.name]  # they are still earlier runs
    after = stopped_run(p, "2026-10-28_ddddddd", at(10, day=28), at(11, day=28), "02.6-builder",
                        {"stage": "03-sweep", "items": 3, "backend": "jev"})
    assert record.previous_run(now) == after.resolve()  # stopped after the coded steps: compared as usual


def test_a_hold_and_its_release_are_written_to_the_record_and_read_back(tmp_path):
    """M9 slice B: the check of the run holds a run that has a gap; `continue` releases it."""
    (tmp_path / "data").mkdir()
    steps = [pipeline.StageRun("01-intake", True, "t0", "t1")]
    record.write(tmp_path, steps, {}, 32000, [], "t9")
    assert record.held_of(record.read(tmp_path)) is None  # a run the check did not hold has neither key
    rec = record.hold(tmp_path, 2, "05-qa")
    assert rec["held"] == {"by": "05-qa", "gaps": 2} and record.held_of(record.read(tmp_path)) == rec["held"]
    assert record.read(tmp_path)["steps"] == rec["steps"]  # nothing else changed
    rec = record.release(tmp_path, "t10")
    assert "held" not in rec and rec["released"] == {"by": "05-qa", "gaps": 2, "at": "t10"}
    assert record.held_of(record.read(tmp_path)) is None  # released: not held
    again = record.hold(tmp_path, 1, "05-qa")  # checked again: held, and the old release is gone
    assert again["held"]["gaps"] == 1 and "released" not in again


def test_amend_adds_keys_and_takes_out_a_key_given_none(tmp_path):
    (tmp_path / "data").mkdir()
    record.write(tmp_path, [pipeline.StageRun("01-intake", True, "t0", "t1")], {}, 32000, [], "t9", until="02.3-graph")
    record.amend(tmp_path, qa={"started": "a", "finished": "b"}, until=None)
    rec = record.read(tmp_path)
    assert rec["qa"] == {"started": "a", "finished": "b"} and "until" not in rec and rec["format"] == record.FORMAT


# M1 slice A: the tokens a fixture check spent are in the record, and a reused stamp's are not
def test_the_record_keeps_the_tokens_of_a_fixture_check_that_spent_some_and_nothing_for_one_that_did_not(tmp_path):
    import validate
    run = tmp_path / "run"
    (run / "data").mkdir(parents=True)
    spent = {"input": 39823, "output": 12, "calls": 36}
    stamps = {"03-sweep": validate.Stamp("PASS", None, None, "31/32", usage=spent),
              "02.1-inventory": validate.Stamp("PASS", "1/1"),
              "02.2-reader": validate.Stamp("PASS", "1/1", cached="2026-10-30")}
    record.write(run, [], stamps, 32000, [], "2026-01-01T00:00:00+00:00")
    doc = json.loads((run / "data" / "run.json").read_text(encoding="utf-8"))
    assert doc["stamps"]["03-sweep"]["usage"] == spent
    assert "usage" not in doc["stamps"]["02.1-inventory"] and "usage" not in doc["stamps"]["02.2-reader"]
    back = record.stamps_of(record.read(run))
    assert back["03-sweep"].usage == spent and back["03-sweep"].text == "PASS (recall 31/32)"
    assert back["02.1-inventory"].usage is None and back["02.2-reader"].usage is None and back["02.2-reader"].cached == "2026-10-30"


def test_a_record_whose_stamp_has_a_usage_that_cannot_be_read_is_read_as_a_stamp_that_spent_none(tmp_path):
    run = tmp_path / "run"
    (run / "data").mkdir(parents=True)
    record.write(run, [], {}, 32000, [], "2026-01-01T00:00:00+00:00")
    path = run / "data" / "run.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    for bad in ("many", {"input": True}, {"output": 1.5}, {"calls": -1}, [1], 3):
        doc["stamps"] = {"03-sweep": {"result": "PASS", "recall": "1/1", "usage": bad}}
        path.write_text(json.dumps(doc), encoding="utf-8")
        assert record.stamps_of(record.read(run))["03-sweep"].usage is None, bad
