"""Tests for termset.py, written from specs/phrases.SPEC.md, termset."""
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


def test_vocab_version_ignores_source_labels(tmp_path):
    """2026-10-29 (notes M15 a): a list's `source` names where it comes from and decides no hit."""
    v = tmp_path / "vocab.yaml"
    v.write_text("terms:\n  source: 'I03'\n  safety:\n    source: 'I03'\n    regex: 'a|b'\n", encoding="utf-8")
    first = termset.vocab_version(v)
    v.write_text("terms:\n  source: 'I03; I05'\n  safety:\n    source: 'THREATS:2'\n    regex: 'a|b'\n",
                 encoding="utf-8")
    assert termset.vocab_version(v) == first
    v.write_text("terms:\n  source: 'I03'\n  safety:\n    source: 'I03'\n    regex: 'a|c'\n", encoding="utf-8")
    assert termset.vocab_version(v) != first


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


SHARED_A = b'''"""Shared A."""
import re


def f(t):
    """Docstring."""
    return re.sub("a", "b", t)  # a comment
'''


def _step_and_shared(tmp_path, step_source=b"import mod_a\n\nx = 1\n"):
    step, shared = tmp_path / "step", tmp_path / "shared"
    step.mkdir()
    shared.mkdir()
    (step / "s.py").write_bytes(step_source)
    (shared / "mod_a.py").write_bytes(SHARED_A)
    (shared / "mod_b.py").write_bytes(b"def g():\n    return 1\n")
    return step, shared


def test_code_version_covers_the_shared_modules_the_stage_imports(tmp_path):
    """P1 (2026-10-29): the run decoding is in stages/_shared/library.py, and readtext.py always decided a hit; a
    change to a shared module the stage imports reads as matching code changed. A comment or a docstring there
    does not, and neither does a shared module the stage does not import."""
    step, shared = _step_and_shared(tmp_path)
    first = termset.code_version(step, shared)
    assert termset.code_version(step, shared) == first
    (shared / "mod_a.py").write_bytes(SHARED_A.replace(b'"a", "b"', b'"a", "c"'))
    changed = termset.code_version(step, shared)
    assert changed != first  # code in an imported shared module
    for old, new in ((b"# a comment", b"# another comment"), (b'"""Docstring."""', b'"""A longer docstring."""'),
                     (b'"""Shared A."""', b'"""Shared A, reworded."""')):
        (shared / "mod_a.py").write_bytes(SHARED_A.replace(old, new))
        assert termset.code_version(step, shared) == first, new
    (shared / "mod_a.py").write_bytes(SHARED_A.replace(b"\n", b"\r\n"))
    assert termset.code_version(step, shared) == first  # line endings
    (shared / "mod_a.py").write_bytes(SHARED_A)
    (shared / "mod_b.py").write_bytes(b"def g():\n    return 2\n")
    assert termset.code_version(step, shared) == first  # a shared module the stage does not import
    (shared / "extra.py").write_bytes(b"x = 1\n")
    assert termset.code_version(step, shared) == first  # a new one it does not import


def test_a_new_import_of_a_shared_module_is_covered_without_a_list(tmp_path):
    step, shared = _step_and_shared(tmp_path)
    first = termset.code_version(step, shared)
    for source in (b"import mod_a\nimport mod_b\n", b"import mod_a\nfrom mod_b import g\n",
                   b"import mod_a\n\ndef late():\n    import mod_b\n", b"import mod_a, mod_b\n"):
        (step / "s.py").write_bytes(source)
        assert [p.name for p in termset.imported_shared(step, shared)] == ["mod_a.py", "mod_b.py"], source
        with_b = termset.code_version(step, shared)
        assert with_b != first
        (shared / "mod_b.py").write_bytes(b"def g():\n    return 3\n")
        assert termset.code_version(step, shared) != with_b  # now its code counts
        (shared / "mod_b.py").write_bytes(b"def g():\n    return 1\n")
    # a second file in the stage folder that imports a third module counts too
    (shared / "mod_c.py").write_bytes(b"y = 1\n")
    (step / "other.py").write_bytes(b"from mod_c import y\n")
    assert [p.name for p in termset.imported_shared(step, shared)] == ["mod_a.py", "mod_b.py", "mod_c.py"]


def test_what_is_not_a_shared_import_is_left_out(tmp_path):
    step, shared = _step_and_shared(tmp_path, b"import re\nimport os.path\nfrom . import mod_b\nimport mod_a.sub\n")
    # the standard library, a relative import, and a dotted name that starts with a shared module
    assert [p.name for p in termset.imported_shared(step, shared)] == ["mod_a.py"]
    (step / "mod_b.py").write_bytes(b"z = 1\n")  # a file of the stage with a shared module's name is that file
    (step / "s.py").write_bytes(b"import mod_b\n")
    assert termset.imported_shared(step, shared) == []
    (step / "s.py").write_bytes(b"def broken(:\n")  # does not parse: imports nothing, and counts as it is
    assert termset.imported_shared(step, shared) == []
    assert termset.code_version(step, shared)


def test_the_real_stage_hashes_the_shared_modules_it_imports():
    names = [p.name for p in termset.imported_shared()]
    assert names == sorted(names)
    assert {"library.py", "readtext.py", "audience.py", "secretmask.py"} <= set(names)
    assert "termdiff.py" not in names and "validate.py" not in names  # shared, but 02.4-phrases never imports them
    assert termset.code_version() == termset.code_version(termset.HERE, termset.SHARED)


def test_the_plumbing_the_stage_imports_is_no_change_to_the_matching_code(tmp_path):
    """Noted when P1 merged: a change to the step list or to what runs an earlier step read as "matching code
    changed". The four named modules decide no hit; any other module the stage imports counts."""
    step, shared = _step_and_shared(tmp_path, b"import mod_a\nimport stagelist\nimport coverlines as cov\n")
    for name in termset.NOT_MATCHING:
        (shared / f"{name}.py").write_bytes(b"x = 1\n")
    first = termset.code_version(step, shared)
    assert [p.name for p in termset.imported_shared(step, shared)] == ["mod_a.py"]
    for name in termset.NOT_MATCHING:
        (shared / f"{name}.py").write_bytes(b"x = 2\n")
    assert termset.code_version(step, shared) == first
    (shared / "mod_a.py").write_bytes(SHARED_A.replace(b'"a", "b"', b'"a", "c"'))
    assert termset.code_version(step, shared) != first


def test_the_real_stage_leaves_out_only_the_plumbing_it_imports():
    """Each name is a module the stage imports today, so a renamed one cannot come back into the hash unseen, and
    the modules that decide a hit stay in. The three that speak for the run are imported by `run.py` alone."""
    every = set()
    for p in termset.HERE.glob("*.py"):
        tree = termset.ast.parse(p.read_bytes())
        for node in termset.ast.walk(tree):
            if isinstance(node, termset.ast.Import):
                every |= {(a.name, p.name) for a in node.names}
            elif isinstance(node, termset.ast.ImportFrom) and node.module:
                every.add((node.module, p.name))
    assert termset.NOT_MATCHING <= {m for m, _ in every}
    assert all((termset.SHARED / f"{m}.py").is_file() for m in termset.NOT_MATCHING)
    assert {p.name for p in termset.imported_shared()} == {"audience.py", "library.py", "readtext.py", "secretmask.py"}
    for m in ("earlier_steps", "stagelist", "stagenote"):
        assert {f for mod, f in every if mod == m} == {"run.py"}, m


def _with_list(monkeypatch, **changes):
    """`library.invisible()` as another list, for the hash of the list as loaded."""
    import dataclasses
    inv = dataclasses.replace(termset.library.invisible(), **changes)
    monkeypatch.setattr(termset.library, "invisible", lambda: inv)


def test_code_version_covers_the_invisible_character_list(tmp_path, monkeypatch):
    """P1 (2026-10-29): the list decides a hit as the code does, so a change to it reads as matching code
    changed. Each code point and its action count (and the run length); names, kinds, and notes do not."""
    (tmp_path / "a.py").write_bytes(b"x = 1\n")
    inv = termset.library.invisible()
    first = termset.code_version(tmp_path)
    assert termset.code_version(tmp_path) == first
    _with_list(monkeypatch, kind={**inv.kind, "\u200b": "bidi"}, kind_order=inv.kind_order[::-1])
    assert termset.code_version(tmp_path) == first  # what a kind is called never decides a hit
    _with_list(monkeypatch, strip=inv.strip | {"·"})
    added = termset.code_version(tmp_path)
    assert added != first  # one more character stripped
    _with_list(monkeypatch, strip=inv.strip - {"\u200b"}, space=inv.space | {"\u200b"})
    moved = termset.code_version(tmp_path)
    assert moved not in (first, added)  # the same character with another action
    _with_list(monkeypatch, run_length=3)
    assert termset.code_version(tmp_path) not in (first, added, moved)  # two in a row, or three
    _with_list(monkeypatch, run=inv.run - {"\u180b"})
    assert termset.code_version(tmp_path) != first
    monkeypatch.undo()
    assert termset.code_version(tmp_path) == first


def test_the_list_bytes_hold_only_code_points_actions_and_the_run_length():
    import json
    doc = json.loads(termset.invisible_list())
    assert set(doc) == {"list", "run_length"} and doc["run_length"] == 2
    rows = doc["list"]
    assert rows == sorted(rows) and {r[1] for r in rows} == {"strip", "space", "run"}
    assert len(rows) == 181 + 3 + 260
    assert [8203, "strip"] in rows and [8232, "space"] in rows and [65039, "run"] in rows


CODE = b'''"""Spec: specs/x.SPEC.md, one."""
import re

RX = re.compile("ab")  # what it matches


def f(t):
    """The first hit."""

    return RX.search(t) or "none"
'''


def test_code_version_ignores_comments_and_docstrings(tmp_path):
    """2026-10-29 (after step 8a): a comment, a docstring, or a blank line is not a change to the
    matching code; a string that does something still is."""
    (tmp_path / "a.py").write_bytes(CODE)
    first = termset.code_version(tmp_path)
    for old, new in ((b"md, one.", b"md, two."), (b"# what it matches", b"# step 02.4"),
                     (b'"""The first hit."""', b'"""The first hit, by name."""\n    "a second string"'),
                     (b"\n\n\ndef", b"\ndef")):
        (tmp_path / "a.py").write_bytes(CODE.replace(old, new))
        assert termset.code_version(tmp_path) == first, new
    for old, new in ((b'"ab"', b'"ac"'), (b'or "none"', b'or "nothing"'), (b"search", b"match")):
        (tmp_path / "a.py").write_bytes(CODE.replace(old, new))
        assert termset.code_version(tmp_path) != first, new
    (tmp_path / "a.py").write_bytes(b"def f(:\n")  # does not tokenize: counted as it is
    broken = termset.code_version(tmp_path)
    (tmp_path / "a.py").write_bytes(b"def f(:  \n")
    assert termset.code_version(tmp_path) != broken

