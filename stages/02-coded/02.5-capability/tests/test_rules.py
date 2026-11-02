"""Tests for rules.py, written from specs/capability.SPEC.md, rules."""
import ast
import re
import sys
from pathlib import Path

import rules

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "_shared"))
import library  # noqa: E402

PATTERNS_YAML = library.path("patterns.yaml")


def yaml_ids():
    """id -> check, read from the `02.4-phrases` table as text (no `02.4-phrases` code imported)."""
    text = PATTERNS_YAML.read_text("utf-8")
    out = {}
    for m in re.finditer(r"^- id: (\S+)\n\s+check: (\S+)", text, re.M):
        out[m.group(1)] = m.group(2)
    return out


def test_names_and_order():
    assert rules.LEGS == ("private-data", "untrusted-content", "external-comms")
    assert rules.GRANTS == ("exec-at-load", "context-injection", "persistence", "network",
                            "elevated")
    assert rules.PAIRS == ("orphan+phrase", "dynamic+phrase", "hidden+phrase", "hook+phrase")
    assert set(rules.LEG_RULES) == set(rules.LEGS)
    assert set(rules.GRANT_RULES) == set(rules.GRANTS)
    assert rules.EVIDENCE_CAP == 20


def test_every_pattern_id_exists_under_its_check():
    ids = yaml_ids()
    assert ids, "could not read patterns.yaml"
    named = 0
    for rule in list(rules.LEG_RULES.values()) + list(rules.GRANT_RULES.values()):
        for check, pats in rule.get("phrase_patterns", {}).items():
            for p in pats:
                named += 1
                assert ids.get(p) == check, (p, check)
    assert named > 0


def test_the_pattern_sets_name_real_pattern_ids():
    ids = yaml_ids()
    assert rules.HOOK_INSTRUCTION_PATTERNS <= set(ids)
    assert rules.CARRIER_PATTERNS <= set(ids)


def test_every_name_is_the_library_value_in_the_type_the_callers_use():
    """rules.py only loads: each name is Library/capability.yaml's value, as the type it was written as."""
    t = library.load_yaml("capability.yaml")
    assert rules.LEGS == tuple(t["legs"]) and isinstance(rules.LEGS, tuple)
    assert rules.GRANTS == tuple(t["grants"]) and isinstance(rules.GRANTS, tuple)
    assert rules.PAIRS == tuple(t["pairs"]) and isinstance(rules.PAIRS, tuple)
    assert rules.HOOK_INSTRUCTION_PATTERNS == set(t["hook_instruction_patterns"])
    assert isinstance(rules.HOOK_INSTRUCTION_PATTERNS, set) and isinstance(rules.CARRIER_PATTERNS, set)
    assert rules.LEG_RULES == t["leg_rules"] and rules.GRANT_RULES == t["grant_rules"]
    assert rules.INJECTION_EVENTS == t["injection_events"] == ["SessionStart", "UserPromptSubmit"]
    assert rules.LOAD_BYTES_EVENTS == t["load_bytes_events"] == ["SessionStart"]
    assert rules.POSTURE_WORDS == t["posture_words"] and rules.LIMITS == t["limits"]
    assert len(rules.LIMITS) == 2 and all(isinstance(x, str) and x.startswith("standing limit:") for x in rules.LIMITS)
    assert rules.CONNECTOR_NAMES == t["connector_names"] and re.search(rules.CONNECTOR_NAMES, "gmail")


def test_the_library_file_is_dated_and_sourced():
    t = library.load_yaml("capability.yaml")
    assert str(t["moved"]) == "2026-10-29"
    assert t["source"].strip()


def test_rules_py_holds_no_table():
    tree = ast.parse(Path(rules.__file__).read_text(encoding="utf-8"))
    big = [n.lineno for n in ast.walk(tree)
           if (isinstance(n, (ast.List, ast.Tuple, ast.Set)) and len(n.elts) > 2)
           or (isinstance(n, ast.Dict) and len(n.keys) > 2)]
    assert big == []


def test_excluded_signals():
    assert "Bash" not in rules.LEG_RULES["external-comms"]["tools"]
    for rule in list(rules.LEG_RULES.values()) + list(rules.GRANT_RULES.values()):
        for pats in rule.get("phrase_patterns", {}).values():
            assert "K.telemetry" not in pats
            assert "K.md-carrier" not in pats


def test_posture_table():
    expect = {
        "read": ["Read", "Grep", "Glob", "LS", "NotebookRead", "TodoRead", "TodoWrite"],
        "write": ["Write", "Edit", "MultiEdit", "NotebookEdit"],
        "execute": ["Bash", "PowerShell"],
        "network": ["WebFetch", "WebSearch"],
        "delegate": ["Task", "Agent"],
    }
    for word, tools in expect.items():
        for t in tools:
            assert rules.POSTURE_WORDS[t] == word, t
    assert len(rules.POSTURE_WORDS) == sum(len(v) for v in expect.values())
    assert rules.POSTURE_PREFIXES == {"mcp__": "network"}
    assert rules.POSTURE_INHERIT_ALL == "all"
    assert rules.POSTURE_OTHER == "other"
    assert rules.LEAST_PRIVILEGE == ["read"]
