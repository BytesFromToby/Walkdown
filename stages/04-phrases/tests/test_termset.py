"""Tests for termset.py, written from specs/termset.SPEC.md."""
import termset
from patterns import load_table

ROW = """  - id: T.one
    check: phrase.L.override
    regex: 'ignore (all|previous) instructions'
    source: 'PHRASES:L ignore'
"""


def table(tmp_path, body, name="t.yaml"):
    p = tmp_path / name
    p.write_text("patterns:\n" + body, encoding="utf-8")
    return load_table(p)


def test_row_hash_follows_matching_fields_only(tmp_path):
    base = termset.row_versions(table(tmp_path, ROW))["T.one"]
    noted = ROW + "    note: 'why it is narrow'\n"
    assert termset.row_versions(table(tmp_path, noted.replace("PHRASES:L ignore", "PHRASES:L other")))["T.one"] == base
    for extra in ("    audiences: [model]\n", "    where: frontmatter\n", "    paths: '\\.md$'\n",
                  "    unless: 'quoted'\n    note: 'a reason'\n"):
        assert termset.row_versions(table(tmp_path, ROW + extra))["T.one"] != base, extra
    assert termset.row_versions(table(tmp_path, ROW.replace("previous", "prior")))["T.one"] != base


def test_version_follows_rows_and_vocab(tmp_path):
    v = tmp_path / "vocab.yaml"
    v.write_text("# a comment\nwords: [a, b]\n", encoding="utf-8")
    rows = table(tmp_path, ROW)
    d = termset.describe(rows, v)
    assert d["count"] == 1 and set(d) == {"version", "count", "rows", "vocab", "code"}
    v.write_text("words: [a, b]   # layout and comments do not count\n", encoding="utf-8")
    assert termset.describe(rows, v)["version"] == d["version"]
    v.write_text("words: [a, b, c]\n", encoding="utf-8")
    assert termset.describe(rows, v)["version"] != d["version"]
    assert termset.describe(table(tmp_path, ROW.replace("previous", "prior")), v)["version"] != d["version"]
    assert termset.vocab_version(tmp_path / "missing.yaml") is None


def test_code_version_changes_with_code_and_ignores_line_endings(tmp_path):
    (tmp_path / "a.py").write_bytes(b"x = 1\ny = 2\n")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_bytes(b"assert True\n")
    first = termset.code_version(tmp_path)
    (tmp_path / "a.py").write_bytes(b"x = 1\r\ny = 2\r\n")
    assert termset.code_version(tmp_path) == first
    (tmp_path / "tests" / "test_a.py").write_bytes(b"assert False\n")
    assert termset.code_version(tmp_path) == first  # tests do not count
    (tmp_path / "a.py").write_bytes(b"x = 1\ny = 3\n")
    assert termset.code_version(tmp_path) != first
    assert termset.code_version() == termset.code_version(termset.HERE)


def test_diff(tmp_path):
    old = {"version": "v1", "rows": {"A": "1", "B": "2", "C": "3"}, "vocab": "w", "code": "c1"}
    new = {"version": "v2", "rows": {"A": "1", "B": "9", "D": "4"}, "vocab": "w", "code": "c2"}
    d = termset.diff(old, new)
    assert (d["known"], d["same"]) == (True, False)
    assert (d["rows_added"], d["rows_changed"], d["rows_removed"]) == (["D"], ["B"], ["C"])
    assert (d["vocab_changed"], d["code_changed"]) == (False, True)
    assert termset.diff(old, dict(old))["same"] is True
    for a, b in ((None, new), (old, None), ({}, new)):
        d = termset.diff(a, b)
        assert d["known"] is False and d["rows_added"] == [] and d["code_changed"] is False
