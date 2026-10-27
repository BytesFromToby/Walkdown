"""Tests for hosts.py, written from specs/hosts.SPEC.md."""
import hosts


def run(texts, rows=None, hooks=()):
    rows = rows or [{"check": "inv.file", "file": r} for r in texts]
    return hosts.findings(texts, rows, [{"check": "struct.hooks", "file": h} for h in hooks])


def by(fs, check, **kw):
    return [f for f in fs if f["check"] == check and all(f.get(k) == v for k, v in kw.items())]


def test_coverage_fallback_plugin_skills_and_hook_owners():
    texts = {
        "AGENTS.md": "Run the tests.\n",
        "skills/a/SKILL.md": "---\nname: a\ndescription: d\n---\n",
        ".claude-plugin/plugin.json": "{}",
        ".agents/skills/b/SKILL.md": "---\nname: b\ndescription: d\n---\n",
        "tests/fixtures/CLAUDE.md": "planted\n",
    }
    hooks_ = ["hooks/hooks.json", ".github/hooks/x.json", ".cursor/hooks.json", ".cursor/environment.json"]
    fs = run(texts, hooks=hooks_)
    cov = {f["host"]: f for f in by(fs, "host.coverage")}
    assert list(cov) == ["claude", "codex", "gemini", "cursor", "copilot", "windsurf", "agents-md"]
    # no CLAUDE.md outside test data, so Claude Code reads AGENTS.md
    assert cov["claude"]["instructions"] == ["AGENTS.md"]
    assert cov["claude"]["skill_files"] == ["skills/a/SKILL.md"]
    assert cov["codex"]["skills"] == 1 and cov["gemini"]["skills"] == 1 and cov["cursor"]["skills"] == 1
    assert cov["claude"]["hooks"] == ["hooks/hooks.json"]
    assert cov["copilot"]["hooks"] == [".github/hooks/x.json"]
    assert cov["cursor"]["hooks"] == [".cursor/environment.json", ".cursor/hooks.json"]
    assert {f["host"] for f in by(fs, "host.feature", kind="hooks")} == {"claude", "copilot", "cursor"}


def test_coverage_needs_the_plugin_manifest():
    cov = by(run({"skills/a/SKILL.md": "x\n"}), "host.coverage", host="claude")[0]
    assert cov["skills"] == 0 and cov["instructions"] == []


def test_drift_relations():
    texts = {
        "CLAUDE.md": "@AGENTS.md\n",
        "AGENTS.md": "# Rules\n\nOne.\nTwo.\nThree.\nFour.\n",
        "a/CLAUDE.md": "# A\n\nSee AGENTS.md in this folder.\n",
        "a/AGENTS.md": "# A\n\nOne.\nTwo.\nThree.\nFour.\n",
        "b/GEMINI.md": "x  \r\ny\n",
        "d/AGENTS.md": "# Rules\n\n" + "".join(f"Rule {i}.\n" for i in range(20)),
        "d/CLAUDE.md": "See @AGENTS.md for the rules.\n" + "".join(f"Claude {i}.\n" for i in range(12)),
        "d/GEMINI.md": "# Gemini\n\nRead AGENTS.md first.\n" + "".join(f"Note {i}.\n" for i in range(6)),
        "b/AGENTS.md": "x\ny\n",
        ".github/copilot-instructions.md": "Other.\n",
        "tests/data/CLAUDE.md": "1\n",
        "tests/data/AGENTS.md": "2\n",
    }
    rows = [{"check": "inv.file", "file": r} for r in texts] + \
           [{"check": "inv.file", "file": "c/CLAUDE.md", "target": "AGENTS.md"},
            {"check": "inv.file", "file": "c/AGENTS.md"}]
    texts["c/AGENTS.md"] = "Rules.\n"
    d = {(f["file"], f["other"]): f for f in by(run(texts, rows), "host.drift")}
    assert d[("CLAUDE.md", "AGENTS.md")]["relation"] == "linked"
    assert d[("a/CLAUDE.md", "a/AGENTS.md")]["relation"] == "linked"
    assert d[("c/CLAUDE.md", "c/AGENTS.md")]["relation"] == "linked"
    assert d[("b/AGENTS.md", "b/GEMINI.md")]["relation"] == "same"
    # an import inside a sentence, and a 7-line pointer; their own pair is left out
    assert d[("d/CLAUDE.md", "d/AGENTS.md")]["relation"] == "linked"
    assert d[("d/AGENTS.md", "d/GEMINI.md")]["relation"] == "linked"
    assert ("d/CLAUDE.md", "d/GEMINI.md") not in d
    differ = d[("AGENTS.md", ".github/copilot-instructions.md")]
    assert (differ["relation"], differ["only_here"], differ["only_there"]) == ("differ", 5, 1)
    assert not any(f.startswith("tests/") for f, _ in d)


def test_features():
    texts = {
        "s/SKILL.md": "---\nname: s\ndescription: d\nmodel: opus\nallowed-tools: Bash(git:*)\n---\n"
                      "Use $ARGUMENTS with ${CLAUDE_PLUGIN_ROOT}.\nAsk with AskUserQuestion.\n"
                      "A TodoWriter is not a tool.\n",
        "AGENTS.md": "Read @docs/rules.md first.\nEmail me@example.com.\n`@x/y.md` is code.\n"
                     "```\n@inside/fence.md\n```\nClaude will help.\n",
        "CLAUDE.md": "@docs/rules.md\n",
        "tests/fixtures/s/SKILL.md": "---\nmodel: x\n---\n$ARGUMENTS\n",
    }
    fs = by(run(texts), "host.feature")
    got = {(f["file"], f["line"], f["kind"], f["what"]) for f in fs}
    assert got == {
        ("s/SKILL.md", 4, "frontmatter", "model"),
        ("s/SKILL.md", 5, "claude-tool", "Bash(git:*)"),
        ("s/SKILL.md", 7, "claude-words", "$ARGUMENTS, ${CLAUDE_PLUGIN_ROOT}"),
        ("s/SKILL.md", 8, "claude-tool", "AskUserQuestion"),
        ("AGENTS.md", 1, "import", "docs/rules.md"),
    }


def test_keys_no_host_knows_are_slice_4s():
    """Owner, 2026-10-26: a key Claude Code does not know either is not a Claude Code feature."""
    fs = run({"s/SKILL.md": "---\nname: s\ndescription: d\nversion: 2\nargument-hint: [x]\n---\n"})
    assert [f["what"] for f in by(fs, "host.feature")] == ["argument-hint"]
