"""Tests for terms.py, written from specs/terms.SPEC.md."""
import pytest

from foldtext import fold_line
from terms import conflicts, defs_file, normalize_term, safety
from vocab import load_vocab


@pytest.fixture(scope="module")
def v():
    return load_vocab()


def defs(v, text, rel="SKILL.md", instr=None):
    raw = text.split("\n")
    instr = set(range(1, len(raw) + 1)) if instr is None else instr
    return defs_file(rel, raw, [fold_line(x) for x in raw], instr, "model", v)


def test_explicit(v):
    d = defs(v, 'In this skill, "ship" means push to main.')
    assert len(d) == 1
    assert (d[0]["term"], d[0]["definition"], d[0]["source"]) == ("ship", "push to main.",
                                                                   "explicit")
    assert d[0]["check"] == "term.def" and d[0]["line"] == 1
    d = defs(v, "Confirmation means announcing your intent.")
    assert d[0]["term"] == "confirmation"


def test_not_definitions(v):
    assert defs(v, "This means the tests pass.") == []
    assert defs(v, "It is by no means finished.") == []
    d = defs(v, "By deploy we mean a tagged release.")
    assert d[0]["term"] == "deploy" and d[0]["definition"] == "a tagged release."


def test_mapping(v):
    d = defs(v, 'When the user says "tidy up", delete the branch.')
    assert d[0]["source"] == "mapping" and d[0]["term"] == "tidy up"
    assert d[0]["definition"] == "delete the branch."


def test_glossary(v):
    d = defs(v, "## Glossary\n\n- **Done**: merged and pushed\n")
    assert [(x["term"], x["definition"], x["source"], x["line"]) for x in d] == \
        [("done", "merged and pushed", "glossary", 3)]
    assert defs(v, "## Usage\n\n- **Done**: merged and pushed\n") == []


def test_procedural(v):
    d = defs(v, "## How to fix\n\nRun the repair script.\n")
    assert [(x["term"], x["definition"], x["source"], x["line"]) for x in d] == \
        [("fix", "Run the repair script.", "procedural", 1)]


def test_conflicts(v):
    a = defs(v, '"ship" means push to main.', rel="SKILL.md")
    b = defs(v, 'Here "ship" means open a pull request.', rel="ref/style.md")
    c = conflicts(a + b)
    assert len(c) == 1
    assert c[0]["check"] == "term.conflict" and c[0]["term"] == "ship"
    assert c[0]["file"] is None and c[0]["line"] is None
    assert [(x["file"], x["line"]) for x in c[0]["definitions"]] == [("SKILL.md", 1),
                                                                   ("ref/style.md", 1)]
    same = defs(v, '"ship" means Push  to main', rel="x.md")
    assert conflicts(a + same) == []


def test_safety(v):
    d = defs(v, "Confirmation means announcing your intent.\nVerified means exit 0.\n"
                '"ship" means push.')
    s = safety(d, v)
    assert [x["term"] for x in s] == ["confirmation", "verified"]
    assert s[0]["check"] == "term.safety" and s[0]["quote"].startswith("Confirmation")


def test_outside_instr(v):
    assert defs(v, '"ship" means push.', instr=set()) == []


def test_list_markers_tables_and_empty(v):
    assert defs(v, "- Delete means delete")[0]["term"] == "delete"
    assert defs(v, "| a | Delete means delete. |")[0]["term"] == "delete"
    assert defs(v, '"complete" means.') == []


def test_normalize():
    assert normalize_term('**`Ship`**:') == "ship"
    assert normalize_term('  "Read  Only". ') == "read only"
