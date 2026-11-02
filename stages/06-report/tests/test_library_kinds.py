"""The words under each kind of place are Library data, read by render.py and glance.py (restructure
step 3b). Written from the step 3b brief and specs/report.SPEC.md (sections render and glance)."""
import ast
import re
import sys
from pathlib import Path

import pytest

import glance as G
import plain
import render as R

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / "_shared"))
import library  # noqa: E402

TOOLS = library.load_yaml("tools.yaml")
HOSTS = library.load_yaml("hosts.yaml")
TRIGGER = library.load_yaml("trigger.yaml")
FIT = library.load_yaml("fit.yaml")
CLEAN = library.load_yaml("clean.yaml")


def test_each_table_is_read_from_its_library_file():
    assert R.PORT_KINDS == tuple((k["check"], k["name"], k["why"]) for k in TOOLS["port_kinds"])
    assert R.FEATURE_KINDS == tuple((k["kind"], k["name"], k["why"]) for k in HOSTS["feature_kinds"])
    assert R.TRIG_KINDS == tuple((k["kind"], k["name"], k["why"]) for k in TRIGGER["trigger_kinds"])
    assert R.FIT_KINDS == tuple((k["kind"], k["name"], k["why"]) for k in FIT["fit_kinds"])
    assert R.CLEAN_KINDS == tuple((k["kind"], k["name"], k["why"]) for k in CLEAN["clean_kinds"])
    assert R.FAMILY_TEXT == FIT["family_text"] and R.OFTEN_TEXT == FIT["often_text"]
    assert G.PORT_PLAIN == {k["check"]: k["plain"] for k in TOOLS["port_kinds"]}
    assert G.FEATURE_PLAIN == {k["kind"]: k["plain"] for k in HOSTS["feature_kinds"]}
    assert G.FIT_PLAIN == {k["kind"]: k["plain"] for k in FIT["fit_kinds"]}


def test_the_kinds_are_the_ones_the_report_code_groups_by_and_in_this_order():
    """The code names each kind in the groups it builds, so a kind the table adds must have a group."""
    assert [c for c, *_ in R.PORT_KINDS] == ["port.path", "port.crlf", "port.os", "port.backslash", "port.exec",
                                             "port.python", "graph.case"]
    assert [k for k, *_ in R.FEATURE_KINDS] == ["frontmatter", "claude-words", "claude-tool", "import", "hooks"]
    assert [k for k, *_ in R.TRIG_KINDS] == ["not-read", "skipped", "rules", "keys", "values", "tools", "overlap",
                                             "cut", "guidance"]
    assert [k for k, *_ in R.FIT_KINDS] == ["unused", "missing", "inherits", "readonly", "loops", "hooks"]
    assert [k for k, *_ in R.CLEAN_KINDS] == ["unfinished", "dated", "models", "older"]
    assert list(G.FIT_PLAIN) == [k for k, *_ in R.FIT_KINDS]
    assert list(G.FEATURE_PLAIN) == [k for k, *_ in R.FEATURE_KINDS]
    assert list(G.PORT_PLAIN) == [c for c, *_ in R.PORT_KINDS]


def test_every_kind_has_a_name_and_a_reason_and_no_em_dash():
    for table in (R.PORT_KINDS, R.FEATURE_KINDS, R.TRIG_KINDS, R.FIT_KINDS, R.CLEAN_KINDS):
        for kind, name, why in table:
            assert kind.strip() and name.strip() and why.strip(), kind
            assert "—" not in name + why, kind


def test_the_family_and_hook_words_cover_what_fit_yaml_lists():
    assert set(R.FAMILY_TEXT) == set(FIT["families"]) | {"mcp"}
    assert set(R.OFTEN_TEXT) == set(FIT["how_often"]) | {"matching-tool-calls", "other"}


@pytest.mark.parametrize("count,expect", [
    (1, {"unused": "1 tool is allowed but never used by what the words ask for.",
         "missing": "1 task the words ask for that no allowed tool can do.",
         "inherits": "1 helper has no tools list, so it gets every tool.",
         "readonly": "1 place says read-only, but a tool or setting beside it can change files.",
         "loops": "1 step repeats “until it works” with no limit stated.",
         "hooks": "1 hook runs by itself on every message or action."}),
    (3, {"unused": "3 tools are allowed but never used by what the words ask for.",
         "missing": "3 tasks the words ask for that no allowed tool can do.",
         "inherits": "3 helpers have no tools list, so they get every tool.",
         "readonly": "3 places say read-only, but a tool or setting beside it can change files.",
         "loops": "3 steps repeat “until it works” with no limit stated.",
         "hooks": "3 hooks run by themselves on every message or action."}),
])
def test_the_fit_sentences_take_the_singular_and_the_plural(count, expect):
    for kind, sentence in expect.items():
        assert G._fill(G.FIT_PLAIN[kind], count) == sentence


def test_the_port_sentences_fill_every_slot_for_one_and_for_many():
    for check, tpl in G.PORT_PLAIN.items():
        for k in (1, 2):
            filled = G._fill(tpl, k)
            assert not re.search(r"\{\w+\}", filled), (check, k, filled)
            assert str(k) in filled, (check, k)
    assert G._fill(G.PORT_PLAIN["port.crlf"], 1).startswith("1 shell script was saved")
    assert G._fill(G.PORT_PLAIN["port.crlf"], 2).startswith("2 shell scripts were saved")


def test_the_feature_phrases_read_after_it_uses():
    for kind, phrase in G.FEATURE_PLAIN.items():
        assert phrase.strip() and not phrase.endswith("."), kind


def test_plain_words_for_patterns_come_from_the_pattern_table():
    rows = library.load_yaml("patterns.yaml")["patterns"]
    assert plain.PLAIN == {r["id"]: r["plain"] for r in rows}
    assert len(plain.PLAIN) == len(rows)


def _module_literals(path):
    """Collection literals with more than two entries anywhere in a module: a table written as code."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    big = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)) and len(node.elts) > 2:
            big.append(node.lineno)
        elif isinstance(node, ast.Dict) and len(node.keys) > 2:
            big.append(node.lineno)
    return big


def test_plain_py_holds_no_table():
    assert _module_literals(HERE / "plain.py") == []


@pytest.mark.parametrize("name,kind", [
    ("PORT_KINDS", "render"), ("FEATURE_KINDS", "render"), ("TRIG_KINDS", "render"), ("FIT_KINDS", "render"),
    ("CLEAN_KINDS", "render"), ("FAMILY_TEXT", "render"), ("OFTEN_TEXT", "render"),
    ("PORT_PLAIN", "glance"), ("FEATURE_PLAIN", "glance"), ("FIT_PLAIN", "glance")])
def test_the_moved_names_are_assigned_from_the_library_not_written_out(name, kind):
    tree = ast.parse((HERE / f"{kind}.py").read_text(encoding="utf-8"))
    found = [n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    assert len(found) == 1, name
    assert isinstance(found[0].value, (ast.Call, ast.DictComp)), f"{name} is written out in {kind}.py"
