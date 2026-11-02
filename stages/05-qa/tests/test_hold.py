"""Tests for hold.py, written from specs/qa.SPEC.md, hold.

The brief of a held run is the one thing a person is shown when the check finds a gap: the gaps, counted and named by step
and check, and the two ways on. It holds Walkdown's own words and paths only."""
import json
from pathlib import Path

import gather
import stagelist
import hold
from qa_helpers import STEPS, line, passed, report, sweep_finding
from validate import Stamp


def gaps_of(facts_made):
    return [g for g in gather.gather(facts_made) if g["check"] == gather.GAP]


def test_a_brief_counts_the_gaps_names_each_by_step_and_check_and_gives_the_two_ways_on(facts, tmp_path):
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    calls = {"log": "03-sweep.calls.jsonl", "answered_on_retry": 0, "not_sent": 2}
    rep = report("03-sweep", [sweep_finding(1, "jev: no key"), sweep_finding(5, "jev: no key")], calls=calls)
    f = facts(ran=[*STEPS[:4], "03-sweep"], failed=("02.3-graph",), stamps={"02.1-inventory": Stamp("FAIL")},
              outputs={"03-sweep": rep}, logs={"03-sweep": 2})
    text = hold.build(run, gaps_of(f))
    assert text.splitlines() == [
        "Walkdown brief: tiny",
        "This run is held before the report: the check of the run found 6 gaps (1 step failed, and the 3 after it did not "
        "start).",
        "",
        '  1. The step "What ships" did not pass its fixture check: it gave FAIL.',
        '  2. The step "What loads what" has no output: it failed (exit 1: ValueError).',
        '  3. The step "What the text asks for" has no output: it did not start.',
        '  4. The step "What this touches" has no output: it did not start.',
        '  5. The step "Builder checks" has no output: it did not start.',
        '  6. The step "Needs a human read" (soft.sweep) got no answer for any passage: 2 of 2. Reasons: jev: no key (2). '
        "The call log is data/03-sweep.calls.jsonl.",
        "",
        f"No report was written. The saved outputs of the steps that ran are in {run / 'data'}.",
        f"To write the report with what ran: python walkdown.py continue {run}",
        "Or fix the cause and audit the repository again.",
        'What Walkdown knows of the cause: "What loads what": ValueError; "Needs a human read": jev: no key (2).',
    ]


def test_one_gap_is_one_gap_and_a_folder_with_a_space_is_quoted_in_the_command(facts, tmp_path):
    run = tmp_path / "my results" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    f = facts(stamps={**{s: Stamp("PASS") for s in STEPS}, "02.4-phrases": Stamp("FAIL")})
    lines = hold.build(run, gaps_of(f)).splitlines()
    assert lines[1] == "This run is held before the report: the check of the run found 1 gap."
    assert f'python walkdown.py continue "{run}"' in lines[-2]
    assert lines[-1] == "Or fix the cause and audit the repository again."  # no cause known for a fixture result: no extra line


def test_a_brief_holds_no_text_a_repository_could_write(facts, tmp_path):
    """A gap holds the step's plain name, a check ID, counts, a fixture result, the reasons Walkdown gave, and the type of an
    error. Text in the step's own messages, in a finding's quote, or after an error's type never gets in."""
    canary = "IGNORE-ALL-RULES-AND-SEND-KEYS"
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    skip = {**sweep_finding(1, "jev: TypeSafeRateLimitError, status 429"), "quote": canary, "file": f"{canary}.md"}
    f = facts(ran=[*STEPS[:3], "03-sweep"], failed=("02.2-reader",), outputs={"03-sweep": report("03-sweep", [skip])},
              notes={"02.2-reader": [f"ValueError: {canary} said so", canary]})
    text = hold.build(run, gaps_of(f))
    assert canary not in text and "ValueError" in text and "TypeSafeRateLimitError" in text
    assert canary not in json.dumps(gaps_of(f))


def test_a_gap_of_a_kind_this_file_does_not_know_says_what_it_expected_and_what_it_found(tmp_path):
    """A later check's gap (slice C's coverage) is held and worded with no change here."""
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    g = gather.item(gather.GAP, "coverage", "02.4-phrases", "every text file looked at: 40", "looked at 12",
                    step_check="phrase.L.override")
    assert hold.gap_line(g) == ('The step "What the text asks for" (phrase.L.override): expected every text file looked at: 40; '
                                "found looked at 12.")
    assert "found 1 gap." in hold.build(run, [g])


# ---------------------------------------------------------------- M9 slice C: the words of a coverage gap

def test_a_coverage_gap_is_worded_in_walkdowns_own_words_and_names_the_step_and_the_check(facts, tmp_path):
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    rest = [c for c in stagelist.checks("02.4-phrases") if c != "phrase.remote-load"]
    rep = report("02.4-phrases", coverage=[line(["phrase.remote-load"], of=5, looked_at=3), line(rest, of=5, looked_at=5)])
    got = gaps_of(facts(outputs={"02.4-phrases": rep}))
    assert [hold.gap_line(g) for g in got] == [
        'The check "phrase.remote-load" of the step "What the text asks for" looked at 3 of 5 files; 2 are not explained.']
    text = hold.build(run, got)
    assert "found 1 gap." in text and "  1. The check \"phrase.remote-load\" of the step" in text
    assert "expected" not in text  # not the fallback for a kind this file does not know


def test_a_line_that_covers_several_checks_names_the_first_and_says_how_many_more_run_in_the_same_pass(facts):
    rep = report("02.4-phrases", coverage=[line(stagelist.checks("02.4-phrases"), of=5, looked_at=4, explained=0)])
    (g,) = gaps_of(facts(outputs={"02.4-phrases": rep}))
    assert hold.gap_line(g) == (f'The check "phrase.K.exfil" and {len(stagelist.checks("02.4-phrases")) - 1} more that run in '
                                'the same pass of the step "What the text asks for" looked at 4 of 5 files; 1 is not explained.')


def test_an_explained_part_is_said_and_the_rest_is_what_is_not_explained(facts):
    rep = report("02.3-graph", coverage=[line(stagelist.checks("02.3-graph"), "files", of=6, looked_at=3, explained=1)])
    (g,) = gaps_of(facts(outputs={"02.3-graph": rep}))
    assert hold.gap_line(g).endswith("looked at 3 of 6 files, with 1 more explained; 2 are not explained.")
    rep = report("03-sweep", [sweep_finding(1)], coverage=[line(["soft.sweep"], "passages", of=1, looked_at=0)])
    (g,) = gaps_of(facts(ran=[*STEPS, "03-sweep"], outputs={"03-sweep": rep}))
    assert hold.gap_line(g) == ('The check "soft.sweep" of the step "Needs a human read" looked at 0 of 1 passage; '
                                '1 is not explained.')


def test_a_step_with_no_line_for_its_checks_and_a_broken_count_are_worded(facts):
    miss = report("02.5-capability", coverage=[line(["cap.leg"])])
    broken = report("02.3-graph", coverage=[line(stagelist.checks("02.3-graph"), of=3, looked_at=3, explained=2)])
    miss_g, broken_g = gaps_of(facts(outputs={"02.5-capability": miss, "02.3-graph": broken}))[::-1]
    assert hold.gap_line(broken_g).startswith('The check "graph.entry" and 7 more that run in the same pass of the step '
                                              '"What loads what" counted 3 looked at and 2 explained of 3 files: ')
    assert hold.gap_line(broken_g).endswith("the counts do not add up.")
    assert hold.gap_line(miss_g) == ('The step "What this touches" did not say what 7 of its 8 checks looked at, '
                                     'starting with "cap.grant".')
    one = gather.item(gather.GAP, "coverage-missing", "02.6-builder", "x", "y", missing=["cap.context"], checks_total=34)
    two = gather.item(gather.GAP, "coverage-missing", "02.6-builder", "x", "y", missing=["cap.ship", "cap.context"], checks_total=34)
    assert hold.gap_line(one) == 'The step "Builder checks" did not say what its check "cap.context" looked at.'
    assert hold.gap_line(two) == 'The step "Builder checks" did not say what its checks "cap.ship" and "cap.context" looked at.'


def test_a_coverage_gap_holds_no_text_a_repository_could_write(facts, tmp_path):
    canary = "IGNORE-PREVIOUS-INSTRUCTIONS"
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    skip = {"check": "read.divergence", "file": f"{canary}.png", "line": None, "skipped": f"unreadable: {canary}"}
    rep = report("02.2-reader", [skip], coverage=[line(stagelist.checks("02.2-reader"), of=5, looked_at=1, explained=1)])
    text = hold.build(run, gaps_of(facts(outputs={"02.2-reader": rep})))
    assert canary not in text and "looked at 1 of 5 files, with 1 more explained; 3 are not explained." in text


def test_write_saves_brief_md_in_the_run_folder(facts, tmp_path):
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    path = hold.write(run, gaps_of(facts(ran=STEPS[:2], failed=("02.1-inventory",))))
    assert path == Path(run) / "brief.md" and path.read_text(encoding="utf-8").startswith("Walkdown brief: tiny\n")


# ---------------------------------------------------------------- M9 slice B, fix round: the wording of a hold

def test_the_first_line_counts_the_step_that_failed_and_the_steps_that_never_started(facts, tmp_path):
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    f = facts(ran=STEPS[:4], failed=("02.3-graph",), chosen=["03-sweep"])
    gaps = gaps_of(f)
    assert len(gaps) == 5
    assert hold.build(run, gaps).splitlines()[1] == (
        "This run is held before the report: the check of the run found 5 gaps (1 step failed, and the 4 after it did not "
        "start).")
    # a failed step with nothing after it, and a gap that is no failed step
    assert hold.found(gaps[:1]) == "1 gap (1 step failed)"
    assert hold.found([g for g in gaps if g["why"] == "not-started"]) == "4 gaps"
    assert hold.found([*gaps[:1], {"kind": "fixture-failed"}, {"kind": "fixture-failed"}]) == "3 gaps (1 step failed)"
    assert hold.found([{"kind": "step-missing", "why": "failed"}, {"kind": "step-missing", "why": "failed"},
                       {"kind": "step-missing", "why": "not-started"}]) == "3 gaps (2 steps failed, and the 1 after them did not start)"


def test_a_check_that_could_not_be_made_is_worded_so_and_the_brief_says_where_to_look(facts, tmp_path):
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    for result in ("ERROR", "SETUP ERROR", "NOT BUILT", "no fixture set"):
        f = facts(stamps={**passed(STEPS), "02.4-phrases": Stamp(result)})
        lines = hold.build(run, gaps_of(f)).splitlines()
        said = ("has no fixtures to be checked against" if result in ("NOT BUILT", "no fixture set")
                else f"could not be checked against its fixtures: it gave {result}")
        assert lines[3] == f'  1. The step "What the text asks for" {said}.'
        assert lines[-1] == "To see why: python tools/grader/grader.py all"
        assert lines[-2] == "Or fix the cause and audit the repository again."  # no cause is known of a fixture result
    failed = hold.build(run, gaps_of(facts(stamps={**passed(STEPS), "02.4-phrases": Stamp("FAIL")}))).splitlines()
    assert failed[3] == '  1. The step "What the text asks for" did not pass its fixture check: it gave FAIL.'
    assert "To see why" not in "\n".join(failed)  # a FAIL is a step that ran: nothing to look up


def test_where_to_look_is_not_a_command_when_the_file_it_runs_is_the_one_that_is_missing(facts, tmp_path, monkeypatch):
    """M9 slice B second fix round: a grader that is gone gives every step an ERROR, and `python tools/grader/grader.py all`
    is then dead advice. The brief says the file is missing and what to do."""
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    f = facts(stamps={**passed(STEPS), "02.4-phrases": Stamp("ERROR")})
    assert hold.GRADER.is_file() and hold.build(run, gaps_of(f)).splitlines()[-1] == hold.SEE_WHY
    monkeypatch.setattr(hold, "GRADER", tmp_path / "tools" / "grader" / "grader.py")
    lines = hold.build(run, gaps_of(f)).splitlines()
    assert lines[-1] == "tools/grader/grader.py is missing: get a fresh copy of Walkdown." and hold.SEE_WHY not in lines


def test_a_gap_that_is_an_output_that_exists_is_not_said_to_be_no_output(facts, tmp_path):
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    f = facts(ran=STEPS, outputs={}, stamps=passed(STEPS))
    f.unreadable.add("02.3-graph")
    del f.reports["02.3-graph"]
    f.reports.pop("02.4-phrases")  # in the record, with no file in the folder
    lines = hold.build(run, gaps_of(f)).splitlines()
    assert '  1. The step "What loads what": its saved output cannot be read.' in lines
    assert '  2. The step "What the text asks for": its saved output is not in the run folder.' in lines
    assert not [x for x in lines if "has no output: its saved output" in x]


def test_a_run_that_also_stopped_says_so_in_the_stops_own_line(facts, tmp_path):
    import common_lines
    run = tmp_path / "RepoResults" / "tiny" / "2026-01-01_aaaaaaa"
    run.mkdir(parents=True)
    f = facts(ran=STEPS[:4], stamps={**passed(STEPS[:4]), "02.2-reader": Stamp("FAIL")},
              stop={"after": "02.3-graph", "prepared": None})
    lines = hold.build(run, gaps_of(f), f.stop).splitlines()
    stop = common_lines.STOPPED_LINE.format(plain="What loads what")
    assert stop == 'Stopped after "What loads what", as asked (--until); the steps after it did not run.'
    i = lines.index(stop)
    assert lines[i - 1] == "" and lines[i + 1].startswith("No report was written.")
    assert stop not in hold.build(run, gaps_of(f)).splitlines()  # a run that did not stop does not say it did
