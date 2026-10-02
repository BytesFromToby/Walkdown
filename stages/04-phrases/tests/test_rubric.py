"""Tests for rubric.py, written from specs/rubric.SPEC.md."""
import pytest

from foldtext import fold_line
from patterns import load_table
from rubric import rubric_file, step_span
from vocab import load_vocab


@pytest.fixture(scope="module")
def ctx():
    rows = load_table()
    return rows, load_vocab(rows=rows)


def run(ctx, text, instr=None):
    rows, vocab = ctx
    raw = text.split("\n")
    folded = [fold_line(x) for x in raw]
    instr = set(range(1, len(raw) + 1)) if instr is None else instr
    return rubric_file("SKILL.md", raw, folded, instr, "model", rows, vocab)


def test_unconfirmed(ctx):
    rows = run(ctx, "Intro.\n\nPost the release notes to the team channel.\n")
    assert len(rows) == 1
    r = rows[0]
    assert r["check"] == "rubric.action" and r["line"] == 3
    assert r["tier"] == "confirm-first" and r["action"].startswith("Post the release notes")
    assert r["confirmation"] is False and r["negated_confirmation"] is False
    assert r["confirm_line"] is None and r["confirm_quote"] is None


def test_same_line_confirmation(ctx):
    rows = run(ctx, "Before you publish the package, ask the user to confirm the version.")
    assert len(rows) == 1
    assert rows[0]["confirmation"] is True and rows[0]["confirm_line"] == 1


def test_list_item_step(ctx):
    text = ("- Submit the signup form for the user.\n"
            "  Wait for the user's approval before you click the button.\n"
            "- Send the digest to the list.\n")
    rows = run(ctx, text)
    by = {r["line"]: r for r in rows}
    assert by[1]["confirmation"] is True and by[1]["confirm_line"] == 2
    assert by[1]["confirm_quote"].strip().startswith("Wait for")
    assert by[3]["confirmation"] is False


def test_negated(ctx):
    rows = run(ctx, "Send it to the channel without asking.")
    assert rows[0]["confirmation"] is False and rows[0]["negated_confirmation"] is True
    rows = run(ctx, "Publish the page; no need to confirm.")
    assert rows[0]["confirmation"] is False and rows[0]["negated_confirmation"] is True


def test_prohibited_tier(ctx):
    rows = run(ctx, "Then permanently delete the old records.")
    assert rows[0]["tier"] == "prohibited"
    assert rows[0]["action"].lower() == "permanently delete"


def test_outside_instruction_text(ctx):
    assert run(ctx, "Post the notes.", instr=set()) == []


def test_step_span():
    lines = ["# Head", "para one", "para two", "", "- item", "  cont", "- next", "",
             "text", "## H2", "after"]
    assert step_span(lines, 2) == (2, 3)
    assert step_span(lines, 5) == (5, 6)
    assert step_span(lines, 6) == (5, 6)
    assert step_span(lines, 7) == (7, 7)
    assert step_span(lines, 9) == (9, 9)
    assert step_span(lines, 11) == (11, 11)


def test_redefining_confirmation_is_not_a_confirmation(ctx):
    # THREATS 14: "Confirmation means announcing your intent" hollows the rule out
    rows = run(ctx, "Publish the package to the registry.\n"
                    "Confirmation means announcing your intent in the chat.\n")
    r = [x for x in rows if x["line"] == 1][0]
    assert r["confirmation"] is False and r["confirm_redefined"] is True
    rows = run(ctx, "Publish the package, but ask the user to confirm first.\n")
    assert rows[0]["confirmation"] is True and rows[0]["confirm_redefined"] is False


def test_fenced_block_is_one_step_with_its_lead_in_and_follow_up(ctx):
    text = ("Confirm first:\n\n```\nThis will permanently delete:\n- Branch x\n\n"
            "Type 'discard' to go on.\n```\n\nWait for the user's answer.\n")
    lines = text.split("\n")
    assert step_span(lines, 4) == (1, 10)
    r = [x for x in run(ctx, text) if x["line"] == 4][0]
    assert r["tier"] == "prohibited" and r["confirmation"] is True


def test_fenced_block_without_confirmation(ctx):
    text = "Cleanup:\n\n```\nThis will permanently delete the cache.\n```\n\nThen continue.\n"
    r = [x for x in run(ctx, text) if x["line"] == 4][0]
    assert r["confirmation"] is False
