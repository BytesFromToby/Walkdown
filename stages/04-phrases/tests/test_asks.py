"""Tests for asks.py, written from specs/asks.SPEC.md."""
import asks


def by(fs, check, **kw):
    return [f for f in fs if f["check"] == check and all(f.get(k) == v for k, v in kw.items())]


def fam(fs, family):
    rows = by(fs, "ask.tools", family=family)
    return rows[0]["lines"] if rows else []


def test_sentences_join_wrapped_lines_and_leave_out_code():
    lines = ["Write the summary", "to notes/summary.md.", "", "- run the tests", "- then stop", "```",
             "Write the file x.md.", "```", "# Heading"]
    assert asks.sentences(lines) == [(1, "Write the summary to notes/summary.md."), (4, "- run the tests"),
                                     (5, "- then stop"), (9, "# Heading")]


def test_families_named_and_servers():
    text = "\n".join([
        "---", "allowed-tools: Bash WebSearch mcp__gh__create_issue", "---",   # 1-3: frontmatter
        "Edit the config in `src/app.toml`.",                                # 4 write
        "Writing well matters.",                                             # 5 nothing
        "Open the link to the release page.",                                # 6 web
        "Launch two agents in parallel.",                                    # 7 agent
        "Never use the Bash tool here.",                                     # 8 named only
        "File the issue in GitHub with gh.",                                 # 9 server named
        "```bash", "git status", "```",                                      # 10-12 shell (slice 2 scan)
    ])
    fs = asks.file_findings("SKILL.md", text, "model", servers={"gh"})
    assert fam(fs, "write") == [4] and fam(fs, "web") == [6] and fam(fs, "agent") == [7]
    assert fam(fs, "shell") == [11] and fam(fs, "search") == []
    named = {f["tool"]: f["lines"] for f in by(fs, "ask.named")}
    assert named == {"Bash": [8], "mcp__gh": [9]}


def test_not_asking_quoted_and_nouns():
    """Measured 2026-10-27: descriptions of what a step does not do, quoted examples, and "run" as
    a noun ask for nothing."""
    text = "\n".join(["It does not run the software or the tests.",      # 1 negated
                      "It never writes files to the project.",           # 2 negated
                      "Patterns such as \"run the tests\" are listed.",  # 3 quoted
                      "Read its test command and run/demo command.",     # 4 a noun
                      "Do not edit files; run the tests instead.",       # 5 shell asked, write not
                      "Iterate on \"repeat until done\" examples.",      # 6 quoted loop
                      "Until the orchestrator passes it, wait.",         # 7 no loop verb
                      "Read it: stack, conventions, test/run commands.",  # 8 a noun after /
                      "Note the run command and an edit to config.md."])  # 9 nouns after determiners
    fs = asks.file_findings("SKILL.md", text, "model")
    assert fam(fs, "shell") == [5] and fam(fs, "write") == []
    assert not by(fs, "fit.loop")


def test_loops_need_a_limit_on_their_line_or_the_next():
    text = "\n".join(["Iterate until everything passes.", "", "Loop until it works.", "Stop after 5 rounds.",
                      "Keep going until all tests pass", "within 10 minutes.", "Retry until it succeeds.",
                      "```", "repeat until done", "```"])
    fs = asks.file_findings("agents/a.md", text, "subagent")
    assert [f["line"] for f in by(fs, "fit.loop")] == [1, 7]


def test_only_text_the_ai_reads():
    texts = {"README.md": "Fetch the release.\n", "skills/a/SKILL.md": "Fetch the release.\n",
             "tests/fixtures/SKILL.md": "Fetch it.\n", "tool.py": "# fetch the page\n"}
    fs = asks.findings(texts)
    assert {f["file"] for f in fs} == {"skills/a/SKILL.md"}
    assert asks.servers_of([{"grants": ["mcp__gh__x", "Read", "mcp__db__*"]}, {"grants": None}]) == {"gh", "db"}
