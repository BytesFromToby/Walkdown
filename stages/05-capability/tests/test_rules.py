"""Tests for rules.py, written from specs/rules.SPEC.md."""
import re
from pathlib import Path

import rules

PATTERNS_YAML = Path(__file__).resolve().parents[2] / "04-phrases" / "patterns.yaml"


def yaml_ids():
    """id -> check, read from the stage 4 table as text (no stage 4 code imported)."""
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
