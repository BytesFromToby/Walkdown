"""Tests for usage.py, written from specs/shared.SPEC.md, usage."""
import threading

import pytest

import usage


def test_only_whole_numbers_are_counts():
    got = usage.clean({"input": 5, "output": 0, "cache_write": 2.5, "cache_read": True, "calls": 9, "other": 1})
    assert got == {"input": 5, "output": 0}  # a float and a bool are not counts, `calls` is not a token count, and 0 is a count
    assert usage.clean({"input": -1, "output": "3"}) == {} and usage.clean(None) == {} and usage.clean("x") == {}


@pytest.mark.parametrize("block", [{}, {"calls": 0}, {"input": 1, "output": 2, "cache_write": 3, "cache_read": 4, "calls": 5},
                                   {"input": 7, "unknown": "left alone"}])
def test_a_block_of_whole_counts_can_be_read(block):
    assert usage.valid(block)


@pytest.mark.parametrize("block", [None, [], "3", 3, {"input": True}, {"output": 1.5}, {"cache_read": -1}, {"calls": "2"},
                                   {"input": None}, {"input": 3, "calls": False}])
def test_a_block_that_is_not_counts_of_whole_numbers_cannot_be_read(block):
    assert not usage.valid(block)


def test_blocks_are_added_key_by_key_over_the_blocks_that_have_the_key():
    assert usage.plus({"input": 5, "calls": 2}, {"input": 3, "output": 4, "calls": 1}) == {"input": 8, "output": 4, "calls": 3}
    assert usage.plus(None, {"calls": 1}, {"input": True}) == {"calls": 1}  # one that cannot be read counts for nothing
    assert usage.plus() is None and usage.plus(None, "x") is None


def test_the_tally_counts_every_call_and_adds_only_what_was_reported():
    t = usage.Tally()
    t.add({"input": 10, "output": 2})
    t.add(None)  # a call that reported nothing
    t.add({"input": 5, "cache_read": 7, "output": 1.5})  # 1.5 is not a count
    assert t.block() == {"input": 15, "output": 2, "cache_read": 7, "calls": 3, "reported": 2}  # the middle call reported nothing
    assert usage.Tally().block() == {"calls": 0, "reported": 0}  # nothing sent is a count of 0 calls and no token counts at all


def test_the_tally_is_exact_when_calls_come_in_from_threads():
    t = usage.Tally()

    def work():
        for _ in range(500):
            t.add({"input": 1, "output": 2})
    pool = [threading.Thread(target=work) for _ in range(8)]
    for th in pool:
        th.start()
    for th in pool:
        th.join()
    assert t.block() == {"input": 4000, "output": 8000, "calls": 4000, "reported": 4000}


def test_the_words_say_what_was_reported_and_say_not_reported_for_the_rest():
    assert usage.words({"input": 596200, "output": 31464, "calls": 431}) == "596,200 in, 31,464 out"
    assert usage.words({"input": 39823, "calls": 36}) == "39,823 in"
    assert usage.words({"output": 5, "calls": 1}) == "5 out"
    assert usage.words({"input": 0, "output": 0, "calls": 2}) == "0 in, 0 out"  # reported as 0 is reported
    assert usage.words({"input": 10, "output": 2, "cache_write": 1200, "cache_read": 0, "calls": 1}) == "10 in, 2 out, 1,200 cache write"
    assert usage.words({"cache_read": 300, "calls": 1}) == "300 cache read"
    assert usage.words({"calls": 3}) == "not reported" and usage.words({}) == "not reported"
    assert usage.words({"calls": 0}) == "sent nothing"
    assert usage.words(None) == "not reported" and usage.words({"input": True}) == "not reported"


def test_a_count_above_the_ceiling_is_not_a_count():
    """M1 fix 6: a service can put any number in its reply. 10**4000 gave an 18 KB brief and a sum past 4,300 digits raised."""
    top = usage.CEILING
    assert top == 10 ** 15
    assert usage.clean({"input": top, "output": top + 1}) == {"input": top}  # the ceiling itself is a count; one above is not
    huge = 10 ** 4000
    assert usage.clean({"input": huge, "output": 7, "cache_read": huge}) == {"output": 7}
    assert usage.valid({"input": top, "calls": top}) and not usage.valid({"input": top + 1}) and not usage.valid({"calls": huge})
    assert usage.words({"input": huge, "output": 3, "calls": 1}) == "not reported"  # a saved block with one cannot be read at all
    t = usage.Tally()
    for _ in range(3):
        t.add({"input": top, "output": 4, "cache_write": huge})
    assert t.block() == {"output": 12, "calls": 3, "reported": 3}  # three counts at the ceiling add up past it: the sum is not reported, never a crash
    assert len(str(t.block())) < 60
    assert usage.plus({"input": top, "calls": 1}, {"input": top, "calls": 1}) == {"calls": 2}


def test_a_total_from_only_some_of_the_calls_says_so():
    """M1 fix 5: `reported` is how many calls reported any count. Below `calls` and above 0 the total is a lower bound and the words
    say so; every call reported, or a block that does not say (no `reported`), is as it was; none reported is `not reported`."""
    assert usage.words({"input": 500, "output": 15, "calls": 9, "reported": 5}) == "500 in, 15 out (from 5 of 9 calls)"
    assert usage.words({"input": 5, "cache_read": 3, "calls": 4000, "reported": 3999}) == "5 in, 3 cache read (from 3,999 of 4,000 calls)"
    assert usage.words({"input": 500, "output": 15, "calls": 9, "reported": 9}) == "500 in, 15 out"
    assert usage.words({"input": 500, "output": 15, "calls": 9}) == "500 in, 15 out"
    assert usage.words({"calls": 9, "reported": 0}) == "not reported" and usage.words({"calls": 0, "reported": 0}) == "sent nothing"
    assert usage.words({"input": 500, "calls": 9, "reported": 0}) == "not reported"  # a block that contradicts itself reports nothing
    assert usage.partial({"input": 1, "calls": 2, "reported": 1}) == (1, 2) and usage.partial({"calls": 2, "reported": 2}) is None
    assert usage.partial({"input": 1, "calls": 2}) is None and usage.partial(None) is None and usage.partial({"calls": 1, "reported": 2}) is None
    assert usage.partial({"calls": 2, "reported": 0}) is None  # none reported is `not reported`, not a partial total
    assert usage.note({"calls": 2, "reported": 0}).endswith("not reported (2 calls)")
    assert usage.note({"input": 500, "output": 15, "calls": 9, "reported": 5}) == (
        "tokens the calls used, as the backend reported them: 500 in, 15 out (from 5 of 9 calls)")
    assert usage.note({"input": 7, "output": 3, "calls": 1, "reported": 1}).endswith("7 in, 3 out (1 call)")


@pytest.mark.parametrize("block", [{"reported": True}, {"reported": -1}, {"reported": 1.5}, {"reported": "1"}, {"reported": None},
                                   {"reported": 10 ** 15 + 1}, {"calls": 2, "reported": 3}])
def test_a_reported_that_is_not_a_count_or_is_more_than_the_calls_cannot_be_read(block):
    assert not usage.valid(block)


def test_reported_adds_up_only_over_blocks_that_say_it():
    assert usage.plus({"input": 5, "calls": 2, "reported": 1}, {"input": 3, "calls": 1, "reported": 1}) == {"input": 8, "calls": 3, "reported": 2}
    assert usage.plus({"input": 5, "calls": 2, "reported": 1}, {"input": 3, "calls": 1}) == {"input": 8, "calls": 3}  # one does not say


def test_the_note_names_the_tokens_and_the_calls():
    assert usage.note({"input": 7, "output": 3, "calls": 1}) == (
        "tokens the calls used, as the backend reported them: 7 in, 3 out (1 call)")
    assert usage.note({"calls": 12}).endswith("not reported (12 calls)")
