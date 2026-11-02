"""Tests for audience.py, written from specs/shared.SPEC.md, audience."""
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
                "LICENSE", "SECURITY.md", "THIRD_PARTY_NOTICES.md", "THIRD-PARTY-NOTICES.md",
                "COPYING", "CREDITS.md", "fonts/OFL.txt"]:
        assert audience(rel) == "human", rel
    assert audience("references/copy-rules.md") == "model"  # review C43: names, not prefixes of words


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


def test_test_data_by_folder_and_file_name():
    from audience import is_test_data
    for p in ["tests/x.md", "Fixtures/01/SKILL.md", "pkg/__tests__/a.js", "src/testdata/in.txt",
              "spec/foo_spec.rb", "test_utils.py", "lib/parse_test.go", "src/a.test.ts",
              "src/a.spec.js", "conftest.py", "tests/README.md"]:
        assert is_test_data(p) and audience(p) == "test-data", p
    for p in ["SKILL.md", "specs/run.SPEC.md", "examples/demo/SKILL.md", "contest.md",
              "skills/testing/SKILL.md", "latest.md"]:
        assert not is_test_data(p), p


def test_fixture_files_by_name_are_test_data():
    from audience import is_test_data
    assert is_test_data("packages/sdk/parity/middleware-v1_1.fixtures.json")
    assert is_test_data("parity/fixtures.json")
    assert not is_test_data("parity/fixturesmith.md")


def test_inventory_sets():
    """What `02.4-phrases` and the builder step both give `audience`, from `02.1-inventory` findings."""
    from audience import inventory_sets
    findings = [
        {"check": "inv.pin", "file": None, "script_languages": {"python": ["tools/a.py"], "shell": ["hooks/go", "x.sh"]}},
        {"check": "inv.file", "file": "z.md"}, {"check": "inv.file", "file": "hooks/hooks.json", "entry_point": "hook-config"},
        {"check": "inv.file", "file": "a.md"},
        {"check": "struct.hooks", "file": ".cursor/hooks.json", "event": "stop"},
        {"check": "struct.hooks", "file": None, "event": "stop"},
    ]
    files, scripts, hook_configs = inventory_sets(findings)
    assert [f["file"] for f in files] == ["a.md", "hooks/hooks.json", "z.md"]  # sorted, inv.file only
    assert scripts == {"tools/a.py", "hooks/go", "x.sh"}
    assert hook_configs == {"hooks/hooks.json", ".cursor/hooks.json"}
    assert audience("hooks/go", scripts, hook_configs) == "tool" and audience("hooks/go") == "model"
    assert inventory_sets([]) == ([], set(), set())
