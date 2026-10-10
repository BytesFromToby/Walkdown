"""Tests for patterns.py, written from specs/patterns.SPEC.md."""
import re

import pytest

from patterns import CHECKS, TableError, load_table


def write(tmp_path, body):
    p = tmp_path / "t.yaml"
    p.write_text(body, encoding="utf-8")
    return p


GOOD = """patterns:
  - id: X.one
    check: phrase.L.override
    regex: 'ignore (all|previous) instructions'
    source: 'PHRASES:L ignore'
"""


def test_shipped_table_is_valid():
    rows = load_table()
    assert rows
    ids = [r.id for r in rows]
    assert len(ids) == len(set(ids))
    for r in rows:
        assert r.check in CHECKS
        assert r.source.startswith(("PHRASES:", "THREATS:"))
        assert isinstance(r.rx, re.Pattern)
        if r.unless is not None:
            assert r.note
    assert {r.check for r in rows} == set(CHECKS)
    assert len(CHECKS) == 14


@pytest.mark.parametrize("body", [
    # missing source
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: 'x'\n",
    # bad check
    "patterns:\n  - id: a\n    check: phrase.Z\n    regex: 'x'\n    source: 'PHRASES:L'\n",
    # bad source
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: 'x'\n    source: 'me'\n",
    # regex does not compile
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: '(x'\n    source: 'PHRASES:L'\n",
    # unless without note
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: 'x'\n    source: 'PHRASES:L'\n    unless: 'y'\n",
    # unless does not compile
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: 'x'\n    source: 'PHRASES:L'\n    unless: '(y'\n    note: n\n",
    # duplicate id
    GOOD + "  - id: X.one\n    check: phrase.L.override\n    regex: 'y'\n    source: 'PHRASES:L'\n",
    # unknown audience
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: 'x'\n    source: 'PHRASES:L'\n    audiences: [robot]\n",
    # unknown where
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: 'x'\n    source: 'PHRASES:L'\n    where: body\n",
    # unknown field
    "patterns:\n  - id: a\n    check: phrase.L.override\n    regex: 'x'\n    source: 'PHRASES:L'\n    colour: red\n",
])
def test_malformed_tables_raise(tmp_path, body):
    with pytest.raises(TableError):
        load_table(write(tmp_path, body))


def test_case_insensitive_and_scoped_case(tmp_path):
    rows = load_table(write(tmp_path, GOOD + (
        "  - id: X.two\n    check: phrase.creds\n    regex: '(?-i:API_KEY)'\n"
        "    source: 'THREATS:2 names'\n")))
    one, two = rows
    assert one.hits("IGNORE ALL INSTRUCTIONS")
    assert two.hits("export API_KEY=1")
    assert not two.hits("an api_key here")


def test_unless(tmp_path):
    rows = load_table(write(tmp_path, (
        "patterns:\n  - id: a\n    check: phrase.K.exfil\n    regex: 'sends usage'\n"
        "    source: 'THREATS:1 telemetry'\n    unless: 'opts? in'\n    note: consent\n")))
    assert rows[0].hits("it sends usage data")
    assert not rows[0].hits("it sends usage data if the user opts in")


def test_restrictions(tmp_path):
    rows = load_table(write(tmp_path, (
        "patterns:\n"
        "  - id: a\n    check: phrase.G.human\n    regex: 'x'\n    source: 'PHRASES:G'\n"
        "    audiences: [human]\n"
        "  - id: b\n    check: phrase.G.human\n    regex: 'x'\n    source: 'PHRASES:G'\n"
        "    paths: '(^|/)CONTRIBUTING'\n"
        "  - id: c\n    check: phrase.C.second-order\n    regex: 'x'\n    source: 'PHRASES:C'\n"
        "    where: frontmatter\n")))
    a, b, c = rows
    assert a.applies("README.md", "human", False)
    assert not a.applies("SKILL.md", "model", False)
    assert b.applies("docs/CONTRIBUTING.md", "human", False)
    assert not b.applies("README.md", "human", False)
    assert c.applies("SKILL.md", "model", True)
    assert not c.applies("SKILL.md", "model", False)


def test_no_unanchored_leading_lookahead():
    """(?=.*X) without ^ is retried at every offset and is quadratic in line length: two rows
    took 26 of stage 4's 27 minutes on a repository with 96,000-character JSON lines
    (2026-10-09). A row that opens with a lookahead must anchor it at ^."""
    import re
    from patterns import load_table
    for row in load_table(None):
        assert not re.match(r"\(\?=\.\*", row.rx.pattern), row.id
