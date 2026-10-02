"""Tests for entrypoints.py, written from specs/entrypoints.SPEC.md."""
from entrypoints import classify


def c(rel, **kw):
    base = dict(is_symlink=False, has_tools=False, is_hook_config=False, is_manifest=False)
    base.update(kw)
    return classify(rel, **base)


# Done when 1
def test_skill():
    assert c("skills/x/SKILL.md") == "skill"
    assert c("pos.SKILL.md") == "skill"
    assert c("skills/x/skill.md") == "skill"


# Done when 2
def test_agent_and_command():
    assert c("pos-broad-agent.md", has_tools=True) == "agent"
    assert c("commands/x.md") == "command"
    assert c("plugin/commands/x.md", has_tools=True) == "command"
    assert c("agents/x.md") == "agent"
    assert c("agents/notes.txt") is None


# Done when 3
def test_other_kinds():
    assert c(".mcp.json") == "mcp-config"
    assert c("hooks/hooks.json", is_hook_config=True) == "hook-config"
    assert c(".github/workflows/ci.yml") == "ci"
    assert c(".gitlab-ci.yml") == "ci"
    assert c(".claude-plugin/plugin.json", is_manifest=True) == "manifest"
    assert c("README.md") == "readme"
    assert c("docs/readme.txt") == "readme"


# Done when 4
def test_workflow_beats_manifest():
    assert c(".github/workflows/release.yaml", is_manifest=True) == "ci"


# Done when 5
def test_symlink_and_plain_file():
    assert c("SKILL.md", is_symlink=True) is None
    assert c("docs/notes.md") is None


def test_project_instructions():
    kw = dict(is_symlink=False, has_tools=False, is_hook_config=False, is_manifest=False)
    for rel in ["CLAUDE.md", "sub/AGENTS.md", ".cursorrules", ".github/copilot-instructions.md",
                ".cursor/rules/style.mdc", "GEMINI.md"]:
        assert classify(rel, **kw) == "project-instructions", rel
    assert classify("docs/claude-notes.md", **kw) is None
