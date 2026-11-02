"""Tests for limitnote.py, written from specs/shared.SPEC.md, limitnote."""
import pytest

from limitnote import LIMIT_NOTE


@pytest.mark.parametrize("line", [
    "tesseract not installed: images not read", "limit: files that do not decode as text", "html render: Playwright absent",
    "not scanned: a.bin: not instruction text", "graph incomplete by construction", "skipped: 3 passages",
    "unknown encoding", "not examined: minified files", "stage not run", "carried forward from the step X", "NOT BUILT: x",
    "SKIPPED a thing",
])
def test_a_message_that_names_something_not_examined_is_a_limit_note(line):
    assert LIMIT_NOTE.search(line)


@pytest.mark.parametrize("line", [
    "read 12 files", "wrote data/02.1-inventory.json", "calls: 0 answered on the retry, 2 got no answer after it, 0 not sent",
    "scanned 40 files", "",
])
def test_a_message_that_names_none_is_not(line):
    assert not LIMIT_NOTE.search(line)
