"""Tests for common_lines.py, written from specs/shared.SPEC.md, common_lines."""
import common_lines


def test_the_phrases_the_check_and_the_report_both_say():
    assert common_lines.UNCHECKED.format(result="SETUP ERROR") == (
        "could not be checked against its fixtures: it gave SETUP ERROR")
    assert common_lines.STOPPED_LINE.format(plain="What loads what") == (
        'Stopped after "What loads what", as asked (--until); the steps after it did not run.')


def test_a_check_with_no_fixtures_is_not_said_to_have_given_a_word():
    assert common_lines.unchecked_phrase("no fixture set") == "has no fixtures to be checked against"
    assert common_lines.unchecked_phrase("NOT BUILT") == "has no fixtures to be checked against"
    assert common_lines.unchecked_phrase("SETUP ERROR") == "could not be checked against its fixtures: it gave SETUP ERROR"
    assert common_lines.unchecked_phrase("ERROR") == "could not be checked against its fixtures: it gave ERROR"
    assert common_lines.UNCHECKED_MANY.format(n=8) == (
        '8 steps could not be checked against their fixtures, so a "none" from them is not measured')


def test_the_words_of_a_coverage_gap_are_one_sentence_naming_the_step_and_the_check():
    short = {"kind": "coverage-short", "step": "02.4-phrases", "checks": ["phrase.remote-load"], "unit": "files",
             "of": 5, "looked_at": 3, "explained": 0}
    assert common_lines.coverage_gap_text(short) == (
        'The check "phrase.remote-load" of the step "What the text asks for" looked at 3 of 5 files; 2 are not explained.')
    assert common_lines.coverage_gap_text({**short, "of": 4, "looked_at": 3}).endswith("looked at 3 of 4 files; 1 is not explained.")
    assert common_lines.coverage_gap_text({**short, "checks": ["a.b", "a.c"], "explained": 1}) == (
        'The checks "a.b" and "a.c" of the step "What the text asks for" looked at 3 of 5 files, with 1 more explained; '
        '1 is not explained.')
    assert common_lines.coverage_gap_text({**short, "checks": ["a.b", "a.c", "a.d"], "unit": "passages", "of": 1,
                                           "looked_at": 0}).startswith('The check "a.b" and 2 more that run in the same pass')
    assert "looked at 0 of 1 passage;" in common_lines.coverage_gap_text({**short, "unit": "passages", "of": 1, "looked_at": 0})
    broken = {**short, "kind": "coverage-broken", "of": 3, "looked_at": 3, "explained": 2}
    assert common_lines.coverage_gap_text(broken) == (
        'The check "phrase.remote-load" of the step "What the text asks for" counted 3 looked at and 2 explained of 3 files: '
        "the counts do not add up.")
    missing = {"kind": "coverage-missing", "step": "02.5-capability", "missing": ["cap.limit"], "checks_total": 8}
    assert common_lines.coverage_gap_text(missing) == (
        'The step "What this touches" did not say what its check "cap.limit" looked at.')
    assert common_lines.coverage_gap_text({**missing, "missing": ["a.b", "a.c"]}) == (
        'The step "What this touches" did not say what its checks "a.b" and "a.c" looked at.')
    assert common_lines.coverage_gap_text({**missing, "missing": ["cap.grant"] + [f"c.{i}" for i in range(6)]}) == (
        'The step "What this touches" did not say what 7 of its 8 checks looked at, starting with "cap.grant".')
    wrong_id = {**broken, "why": "check", "ids": ["x.y", "a.b"]}
    assert common_lines.coverage_gap_text(wrong_id) == (
        'The step "What the text asks for" has a coverage line starting with "phrase.remote-load" that names a check it does '
        'not make or names a check twice: "x.y", "a.b".')
    wrong_found = {**broken, "why": "found", "found_line": 4, "found_actual": 2}
    assert common_lines.coverage_gap_text(wrong_found) == (
        'The check "phrase.remote-load" of the step "What the text asks for" reported 4 found where its findings hold 2: '
        "the counts do not add up.")


def test_a_coverage_gap_on_the_pages_is_a_clause_for_the_list_of_what_did_not_work():
    short = {"kind": "coverage-short", "step": "02.4-phrases", "checks": ["a.b"], "unit": "files", "of": 5, "looked_at": 3,
             "explained": 0}
    assert common_lines.coverage_page_words(short) == "What the text asks for did not look at 2 files and does not say why"
    assert common_lines.coverage_page_words({**short, "kind": "coverage-broken"}) == (
        "What the text asks for reported counts that do not add up")
    miss = {"kind": "coverage-missing", "step": "02.3-graph", "missing": ["graph.entry", "graph.orphan"]}
    assert common_lines.coverage_page_words(miss) == "What loads what did not say what 2 of its checks looked at"
    assert common_lines.coverage_page_words({**miss, "missing": ["graph.entry"]}) == (
        "What loads what did not say what one of its checks looked at")
    assert common_lines.unit_words(1, "entries") == "1 entry" and common_lines.unit_words(2, "run") == "2 runs"
    assert common_lines.unit_words(1, "uses") == "1 program use" and common_lines.unit_words(319, "uses") == "319 program uses"
    assert set(common_lines.COVERAGE_KINDS) == {"coverage-missing", "coverage-short", "coverage-broken"}


def test_the_way_to_a_dropped_read_is_continue_only_while_the_run_is_stopped():
    """Once a run has finished `continue` refuses, so a line that offered it would give a command that fails."""
    both = {"03-sweep": "jev", "04-pinpoint": "claude-cli"}
    assert common_lines.dropped_how("03-sweep", both, True) == "--sweep jev at continue chooses it"
    assert common_lines.dropped_how("03-sweep", both, False) == "to read it, audit the repository again with --sweep jev"
    # a pinpoint needs the sweep before it, so a new audit names both
    assert common_lines.dropped_how("04-pinpoint", both, False) == (
        "to read it, audit the repository again with --sweep jev --pinpoint claude-cli")
    assert common_lines.dropped_how("03-sweep", None, True) == "--sweep at continue chooses it"
