"""Tests for frontmatter.py, written from specs/frontmatter.SPEC.md."""
import frontmatter as fmx


# Done when 1
def test_no_block_or_unclosed_block_is_none():
    assert fmx.parse("# Title\n---\nname: x\n---\n") is None
    assert fmx.parse("---\nname: x\n\nbody with no close\n") is None
    assert fmx.parse("") is None


# Done when 2
def test_quoted_description_verbatim_with_line():
    text = '---\nname: t\ndescription: "Use when: formatting, then \'go\'."\n---\nbody\n'
    fm = fmx.parse(text)
    f = fmx.description_finding("a/SKILL.md", fm)
    assert f["check"] == "struct.description" and f["file"] == "a/SKILL.md"
    assert f["line"] == 3
    assert f["text"] == "Use when: formatting, then 'go'."
    assert f["loader"] == "yaml" and f["loaders_disagree"] is False


# Done when 3
def test_yaml_breaking_description_uses_first_colon():
    text = "---\nname: t\ndescription: Use when: things break\n---\n"
    fm = fmx.parse(text)
    assert fm.yaml is None and fm.yaml_error
    f = fmx.description_finding("x.md", fm)
    assert f["text"] == "Use when: things break" and f["loader"] == "first-colon"
    assert f["line"] == 3


# Done when 4
def test_folded_description_disagrees():
    text = "---\ndescription: >\n  first part\n  second part\n---\n"
    f = fmx.description_finding("x.md", fmx.parse(text))
    assert f["text"] == "first part second part"
    assert f["loaders_disagree"] is True and f["first_colon_text"] == ">"


# Done when 5
def test_tools_list_and_comma_string_agree():
    a = fmx.parse("---\ntools: [Read, Glob, Grep]\n---\n")
    b = fmx.parse("---\ntools: Read, Glob, Grep\n---\n")
    assert fmx.tools_value(a) == ("tools", ["Read", "Glob", "Grep"])
    assert fmx.tools_value(b) == ("tools", ["Read", "Glob", "Grep"])
    assert fmx.tools_value(fmx.parse("---\nname: x\n---\n")) is None


# Done when 6
def test_allowed_tools_space_split_respects_parens():
    fm = fmx.parse("---\nallowed-tools: Bash(git add:*) Read\n---\n")
    assert fmx.tools_value(fm) == ("allowed-tools", ["Bash(git add:*)", "Read"])


# Done when 7
def test_agent_tools_finding_pairs_grant_and_job():
    text = "---\nname: f\ndescription: Formats Markdown files.\ntools: [Read, Bash]\n---\n"
    f = fmx.agent_tools_finding("agents/f.md", fmx.parse(text), "agent")
    assert f == {"check": "struct.agent-tools", "file": "agents/f.md", "line": 4,
                 "tools": ["Read", "Bash"], "description": "Formats Markdown files.",
                 "field": "tools", "kind": "agent"}
