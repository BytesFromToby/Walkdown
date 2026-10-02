"""Tests for audience.py, written from specs/audience.SPEC.md."""
from audience import audience


def test_human():
    for p in ["README.md", "docs/setup.md", ".github/ISSUE_TEMPLATE/bug.md",
              "CONTRIBUTING.md", "INSTALL.txt", "plugin/docs/x.md", "readme.rst"]:
        assert audience(p) == "human", p


def test_subagent():
    for p in ["agents/reviewer.md", "commands/go.md", "skills/x/implementer-prompt.md"]:
        assert audience(p) == "subagent", p


def test_tool():
    assert audience("hooks/session-start", scripts={"hooks/session-start"}) == "tool"
    assert audience("hooks/hooks.json", hook_configs={"hooks/hooks.json"}) == "tool"
    assert audience("tools/a.py") == "tool"


def test_model():
    assert audience("skills/x/SKILL.md") == "model"
    assert audience("notes.md") == "model"
    assert audience("hooks/hooks.json") == "model"


def test_rule_order():
    assert audience("docs/agents/x.md") == "human"
    assert audience("agents/run.py") == "subagent"


def test_changelog_and_license_are_human():
    for rel in ["CHANGELOG.md", "packages/x/CHANGELOG.md", "RELEASE-NOTES.md", "HISTORY.md",
                "LICENSE", "SECURITY.md"]:
        assert audience(rel) == "human", rel


def test_build_and_lock_files_are_tool():
    for rel in ["package-lock.json", "package.json", "sub/tsconfig.build.json", "yarn.lock",
                "requirements-dev.txt", "Dockerfile", "eslint.config.mjs"]:
        assert audience(rel) == "tool", rel
    assert audience(".claude-plugin/plugin.json") == "model"


def test_guides_are_human_and_pattern_lists_are_tool():
    for rel in ["DIRECTIONS.md", "USAGE.md", "docs2/QUICKSTART.md", "GUIDE.md"]:
        assert audience(rel) == "human", rel
    for rel in [".gitignore", "sub/.gitattributes", ".npmignore", "CODEOWNERS"]:
        assert audience(rel) == "tool", rel
