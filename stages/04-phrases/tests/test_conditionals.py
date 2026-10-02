"""Tests for conditionals.py, written from specs/conditionals.SPEC.md."""
import pytest

from conditionals import branch, cond_file, split_sentences
from foldtext import fold_line
from vocab import load_vocab


@pytest.fixture(scope="module")
def v():
    return load_vocab()


def one(v, s):
    return branch(s, v)


def test_harness(v):
    b = one(v, "If you are running in Cursor, use the rules file.")
    assert b["kind"] == "harness"
    assert b["condition"] == "If you are running in Cursor"
    assert b["body"] == "use the rules file."


def test_clock_and_on(v):
    assert one(v, "After 2027-01-01, fetch the new steps.")["kind"] == "clock"
    assert one(v, "On Fridays, post the digest.")["kind"] == "clock"
    assert one(v, "On Codex, use spawn_agent.")["kind"] == "harness"


def test_absence_error_version(v):
    assert one(v, "If no config file exists, create one.")["kind"] == "absence"
    assert one(v, "If the command fails, open the troubleshooting page.")["kind"] == "error"
    b = one(v, "If the version is below 2, stop.")
    assert b["kind"] == "version"


def test_state_environment(v):
    assert one(v, "If this is the first run, index everything.")["kind"] == "state"
    assert one(v, "On first run, index everything.") is None
    assert one(v, "If the repository name starts with acme-, skip it.")["kind"] == "environment"


def test_no_kind_and_not_instructions(v):
    assert one(v, "If you like, add a short title.") is None
    assert one(v, "This works in Claude Code.") is None
    raw = ["If the command fails, stop."]
    assert cond_file("README.md", raw, [fold_line(x) for x in raw], set(), "human", v) == []


def test_trailing_condition(v):
    b = one(v, "Upload the log if the build fails.")
    assert b["condition"] == "if the build fails."
    assert b["body"] == "Upload the log"
    assert b["kind"] == "error"


def test_two_kinds(v):
    b = one(v, "If no config exists on Windows, fail loudly.")
    assert b["kinds"][0] == b["kind"]
    assert "environment" in b["kinds"] and "absence" in b["kinds"]
    assert b["kind"] == "environment"


def test_file_and_sentences(v):
    raw = ["Read this. If the command fails, retry once. Done."]
    f = cond_file("SKILL.md", raw, [fold_line(x) for x in raw], {1}, "model", v)
    assert len(f) == 1
    assert f[0]["check"] == "cond.branch" and f[0]["line"] == 1 and f[0]["quote"] == raw[0]
    assert f[0]["condition"] == "If the command fails"
    assert len(split_sentences(raw[0])) == 3
    assert len(split_sentences("Use a tool (e.g. a linter) first. Then stop.")) == 2


def test_url_masked(v):
    raw = ["Open https://x.example.com/if/you/are/running/in/cursor now."]
    assert cond_file("SKILL.md", raw, raw, {1}, "model", v) == []


def test_list_marker_not_body_and_file_names(v):
    b = one(v, "- If there is no CLAUDE.md present, assume defaults.")
    assert b["body"] == "assume defaults." and b["kinds"] == ["absence"]
