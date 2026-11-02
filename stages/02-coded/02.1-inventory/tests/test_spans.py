"""Tests for spans.py, written from specs/inventory.SPEC.md, spans."""
import json

import spans


def test_a_json_value_is_found_with_its_lines_from_one_line_or_many():
    text = '{\n  "hooks": {\n    "Stop": [\n      {\n        "command": "run"\n      }\n    ]\n  }\n}\n'
    root = spans.compose(text)
    entry = spans.at(root, "hooks", "Stop", 0)
    assert spans.span(entry) == [4, 6]
    key, value = spans.pair(spans.at(root, "hooks"), "Stop")
    assert spans.first_line(key) == 3 and spans.span(value, key=key) == [3, 7]
    assert spans.span(spans.at(entry, "command")) == [5, 5]


def test_minified_json_is_one_line():
    root = spans.compose(json.dumps({"hooks": {"Stop": [{"command": "x"}]}}))
    assert spans.span(spans.at(root, "hooks", "Stop", 0)) == [1, 1]


def test_tabs_and_what_yaml_reads_as_a_break_keep_every_line_number():
    """A tab-indented JSON file is common and YAML refuses it. A lone CR, NEL, LS, and PS are breaks to YAML and part of a line to
    every other step (`readtext.split_lines`)."""
    text = '{\n\t"a": "one\u2028two",\n\t"b": "three\u0085four",\n\t"c": "five\rsix",\n\t"d": "last"\n}\n'
    root = spans.compose(text)
    assert [spans.span(spans.at(root, k)) for k in "abcd"] == [[2, 2], [3, 3], [4, 4], [5, 5]]


def test_a_crlf_file_counts_a_line_ending_once():
    root = spans.compose('{\r\n  "a": 1,\r\n  "b": 2\r\n}\r\n')
    assert spans.span(spans.at(root, "b")) == [3, 3]


def test_a_block_ends_above_what_comes_next():
    text = ('a: |\n  one\n  two\nb: >-\n  three\n  four\n\nc: "five\n  six"\n'
            "d:\n  - e: 1\n    f: 2\n  - g: 3\nh: plain\n  more\n")
    root = spans.compose(text)
    assert spans.span(spans.at(root, "a")) == [1, 3]
    assert spans.span(spans.at(root, "b"))[1] in (6, 7)  # a blank line after a block belongs to no one and cannot be flagged
    assert spans.span(spans.at(root, "c")) == [8, 9]
    assert spans.span(spans.at(root, "d", 0)) == [11, 12]
    assert spans.span(spans.at(root, "d", 1)) == [13, 13]
    assert spans.span(spans.at(root, "h")) == [14, 15]


def test_a_block_at_the_end_of_the_text_keeps_its_last_line():
    assert spans.span(spans.at(spans.compose("a: |\n  one\n  two"), "a")) == [1, 3]
    assert spans.span(spans.at(spans.compose("a: |\n  one\n  two\n"), "a")) == [1, 3]


def test_a_key_above_its_value_starts_the_span():
    key, value = spans.pair(spans.compose("a:\n  two\n"), "a")
    assert spans.span(value) == [2, 2] and spans.span(value, key=key) == [1, 2]


def test_an_offset_is_where_the_text_starts_in_its_file():
    key, value = spans.pair(spans.compose("a: 1\nb: |\n  two\n"), "b")
    assert spans.span(value, key=key, offset=1) == [3, 4]


def test_what_does_not_compose_or_is_not_there_is_none():
    assert spans.compose("") is None and spans.compose(None) is None
    assert spans.compose("a: b: c") is None  # YAML refuses it
    assert spans.compose("---\na: 1\n---\nb: 2\n") is None  # two documents
    assert spans.at(None, "a") is None and spans.span(None) is None
    root = spans.compose('{"a": [1]}')
    assert spans.at(root, "b") is None and spans.at(root, "a", 5) is None and spans.at(root, "a", "x") is None
    assert spans.pair(root, "b") == (None, None)


def test_a_repeated_key_is_the_last_as_the_parsers_take_it():
    root = spans.compose('{\n"a": 1,\n"a": 2\n}\n')
    assert spans.span(spans.at(root, "a")) == [3, 3] and json.loads('{"a": 1, "a": 2}')["a"] == 2
