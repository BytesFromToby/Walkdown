"""Tests for clean.py, written from specs/clean.SPEC.md."""
import clean


def by(fs, check, **kw):
    return [f for f in fs if f["check"] == check and all(f.get(k) == v for k, v in kw.items())]


def test_regions():
    lines = ["---", "model: x", "---", "text", "```", "code", "```", "more"]
    assert [r for _, _, r in clean.regions("a.md", lines)] == \
        ["frontmatter"] * 3 + ["text", "code", "code", "code", "text"]
    assert {r for _, _, r in clean.regions("a.py", lines)} == {"code"}


def test_unfinished_by_kind_and_place():
    md = "\n".join(["TODO: finish.", "Say \"TODO\" to mark one.", "A `TODO` mention.", "a todo list",
                    "Fill [insert name here].", "WIP draft of the draft.", "```", "FIXME in an example", "```"])
    fs = clean.file_findings("skills/a/SKILL.md", md, "model")
    got = {(f["line"], f["kind"]) for f in by(fs, "clean.unfinished")}
    assert got == {(1, "todo"), (5, "placeholder"), (6, "draft")}
    py = 'x = f"{{name}}"  # TODO: tidy\nWIP = 1\n'
    assert {(f["line"], f["kind"]) for f in by(clean.file_findings("s.py", py, "tool"), "clean.unfinished")} == {(1, "todo")}
    assert not by(clean.file_findings("templates/t.md", "Hi {{name}}.\n", "model"), "clean.unfinished")


def test_dated_claims():
    md = "\n".join(["Done 2026-09-25.", "Before August 2025, use the old API.", "Since 2024 it works.",
                    "Ships in Q3 2025.", "As of version 2 it sorts.", "The latest version.",
                    "Say \"as of now\" here.", "Until `2025-01-01` passes."])
    assert [f["line"] for f in by(clean.file_findings("SKILL.md", md, "model"), "clean.dated")] == [2, 3, 4, 5]
    assert not by(clean.file_findings("SKILL.md", md, "tool"), "clean.dated")  # not text the AI reads


def test_models_and_older():
    md = "\n".join(["---", "model: claude-opus-5-5", "---",
                    "Use `claude-3-5-haiku-20241022` or gpt-4o.", "Use sonnet, claude-sonnet-latest, or claude-code.",
                    "See claude-fable-5.md and llama3.1:8b.", "Call the `Task` tool, then MultiEdit( it."])
    fs = clean.file_findings("agents/a.md", md, "subagent")
    got = [(f["line"], f["model"], f["where"]) for f in by(fs, "clean.model")]
    assert got == [(2, "claude-opus-5-5", "frontmatter"), (4, "claude-3-5-haiku-20241022", "code"),
                   (4, "gpt-4o", "text"), (6, "llama3.1:8b", "text")]
    assert [(f["tool"], f["now"]) for f in by(fs, "clean.older")] == [("Task", "Agent"), ("MultiEdit", "Edit")]


def test_only_shipped_files():
    texts = {"README.md": "TODO\n", "tests/x.md": "TODO\n", "skills/a/SKILL.md": "TODO\n", "run.sh": "# TODO\n"}
    fs = clean.findings(texts)
    assert {f["file"] for f in fs if f["file"]} == {"skills/a/SKILL.md", "run.sh"}
    assert by(fs, "clean.checked")[0]["files"] == 2  # one row in every run
