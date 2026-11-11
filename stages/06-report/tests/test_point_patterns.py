"""Which patterns reach the pages (R29, R30, owner 2026-11-07), written from specs/report.SPEC.md, render: every pattern is on
the summary's list (`POINT_PATTERNS`, `SEND_SHAPE`), or kept in the full report only for a measured reason: a hit in the
base-rate repositories (`Library/baserates.json`), or a hit in ordinary repositories when it was measured (`FULL_ONLY`).
A pattern on neither side fails here until it is put on one."""
import json
from pathlib import Path

import yaml

import render as R

LIB = Path(__file__).resolve().parents[3] / "Library"


def every_pattern() -> set[str]:
    return {p["id"] for p in yaml.safe_load(open(LIB / "patterns.yaml", encoding="utf-8"))["patterns"]}


def base_rate_hits() -> set[str]:
    rates = json.load(open(LIB / "baserates.json", encoding="utf-8"))
    out = set()
    for repo in rates["repos"]:
        lines = repo["lines"]
        out |= {p for p, k in (lines.items() if isinstance(lines, dict) else lines) if k}
    return out


def test_every_pattern_is_on_the_list_or_kept_off_it_for_a_measured_reason():
    listed = R.POINT_PATTERNS | R.SEND_SHAPE
    unplaced = every_pattern() - listed - set(R.FULL_ONLY) - base_rate_hits()
    assert unplaced == set(), "on neither side: measure each, then add it to POINT_PATTERNS or FULL_ONLY"


def test_the_two_sides_do_not_overlap_and_name_only_patterns_walkdown_has():
    listed = R.POINT_PATTERNS | R.SEND_SHAPE
    assert listed & set(R.FULL_ONLY) == set()
    assert listed <= every_pattern() and set(R.FULL_ONLY) <= every_pattern()


def test_a_pattern_kept_off_says_how_often_it_hit():
    assert R.FULL_ONLY["E.tls-off"] == "3 lines in 1 of 7 ordinary repositories (2026-11-07)"
    assert R.FULL_ONLY["L.priority"] == "1 line in 1 of 7 ordinary repositories (2026-11-07)"
    assert all("ordinary repositories" in why for why in R.FULL_ONLY.values())


def test_the_patterns_measured_with_no_hit_on_2026_11_07_are_on_the_list():
    """R29: none of these hit in the seven ordinary repositories."""
    assert {"K.assembly-prose", "creds.desktop", "RL.cross-repo-skill", "A.per-settings", "A.role-authority",
            "B.includes-verb", "B.def-destination", "B.when-says", "B.lookalike", "H.consequence", "E.write-then-exec",
            "C.fan-out", "C.comment-ai", "C.skills-author", "C.guard-instruction", "J.saved-login", "J.cookie",
            "G.perm-flags-docs", "G.launch-lowered", "G.paste-terminal", "G.trust-grant",
            "G.contrib-imperative"} <= R.POINT_PATTERNS
