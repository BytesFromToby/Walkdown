"""Tests for resolve.py, written from specs/resolve.SPEC.md."""
from resolve import Resolver, glob_regex

NODES = ["skills/x/SKILL.md", "skills/x/references/a.md", "references/a.md",
         "references/b.md", "a/helpers.md", "b/helpers.md", "README.md",
         "extra/one.md", "extra/sub/two.md", "x.md", "a/b.md"]


def r(frm, path, shape):
    return Resolver(NODES).resolve(frm, path, shape)


def test_folder_then_root():
    res = r("skills/x/SKILL.md", "references/a.md", "path")
    assert res.status == "file" and res.targets == ["skills/x/references/a.md"]
    res = r("skills/x/SKILL.md", "references/b.md", "path")
    assert res.targets == ["references/b.md"]


def test_ambiguous_bare():
    res = r("README.md", "helpers.md", "bare")
    assert res.targets == ["a/helpers.md", "b/helpers.md"] and res.ambiguous


def test_case_mismatch():
    res = r("x.md", "README.MD", "bare")
    assert res.status == "file" and res.targets == ["README.md"] and res.case_mismatch
    res = r("x.md", "README.md", "bare")
    assert not res.case_mismatch


def test_dir_and_glob():
    res = r("README.md", "extra/", "dir")
    assert res.status == "dir" and res.pattern == "extra/"
    assert res.targets == ["extra/one.md", "extra/sub/two.md"]
    res = r("README.md", "extra/*.md", "glob")
    assert res.status == "glob" and res.targets == ["extra/one.md"]
    assert r("README.md", "extra/**/*.md", "glob").targets == ["extra/one.md", "extra/sub/two.md"]
    assert r("README.md", "extra", "slashed").status in ("dir", "missing")
    assert r("README.md", "skills/x", "slashed").status == "dir"


def test_outside():
    assert r("a/b.md", "../../x.md", "path").status == "outside"
    res = r("a/b.md", "../x.md", "path")
    assert res.status == "file" and res.targets == ["x.md"]


def test_missing():
    assert r("README.md", "references/missing.md", "path").status == "missing"
    res = r("README.md", "nothing/*.md", "glob")
    assert res.status == "glob" and res.targets == []
    assert r("README.md", "x.md/", "dir").status == "missing"


def test_invalid_bracket_class_is_literal():
    # a placeholder like [YYYY-MM-DD] is not a valid character class (range Y-M)
    rx = glob_regex("decisions/[YYYY-MM-DD]*.md")
    assert rx.match("decisions/[YYYY-MM-DD]_x.md")
    assert glob_regex("a/[ab].md").match("a/b.md")
