"""Tests for trigger.py, written from specs/builder.SPEC.md, trigger.py."""
import trigger


def fm(*lines, body="Body.\n"):
    return "---\n" + "\n".join(lines) + "\n---\n" + body


def run(texts, eps=None):
    def ep(rel):
        if rel.endswith("SKILL.md"):
            return "skill"
        return "command" if "/commands/" in "/" + rel else "agent" if "/agents/" in "/" + rel else None
    rows = [{"file": r, "entry_point": (eps or {}).get(r, ep(r))} for r in texts]
    return trigger.findings(texts, rows)


def by(fs, check, **kw):
    return [f for f in fs if f["check"] == check and all(f.get(k) == v for k, v in kw.items())]


def test_modes_and_entries():
    fs = run({
        "s/a/SKILL.md": fm("name: a", "description: Does a. Use when a.", "paths: src/**"),
        "s/b/SKILL.md": fm("name: b", "description: Does b. Use when b.", "user-invocable: no"),
        "s/c/SKILL.md": "# C\n\nDoes c when asked.\n",
        "s/d/SKILL.md": fm("name: d", "description: Does d: when d."),
        "commands/go.md": "Go somewhere.\n",
        "agents/README.md": "# Agents\n",
        "agents/only-tools.md": fm("tools: Read"),
        "agents/x.md": fm("name: x", body="You do x.\n"),
        "agents/-y.md": fm("name: -y", "description: Does y when asked."),
        "tests/fixtures/s/SKILL.md": fm("name: BAD"),
    })
    e = {f["file"]: f for f in by(fs, "trig.entry")}
    assert set(e) == {"s/a/SKILL.md", "s/b/SKILL.md", "s/c/SKILL.md", "s/d/SKILL.md", "commands/go.md",
                      "agents/x.md", "agents/-y.md"}
    assert e["s/a/SKILL.md"]["mode"] == "paths" and e["s/b/SKILL.md"]["menu"] is False
    assert (e["s/c/SKILL.md"]["mode"], e["s/c/SKILL.md"]["name"], e["s/c/SKILL.md"]["description_from"]) == \
        ("auto", "c", "first line")
    assert by(fs, "trig.frontmatter", file="s/c/SKILL.md", kind="missing")
    assert (e["s/d/SKILL.md"]["mode"], e["s/d/SKILL.md"]["name"]) == ("unread", "d")
    assert e["commands/go.md"]["name"] == "go" and e["commands/go.md"]["mode"] == "auto"
    assert e["agents/x.md"]["mode"] == "skipped" and "no description" in e["agents/x.md"]["why"]
    assert e["agents/-y.md"]["mode"] == "skipped" and by(fs, "trig.rule", file="agents/-y.md", rule="agent-name")
    assert not by(fs, "trig.guidance", file="agents/-y.md")  # it never loads
    [lst] = by(fs, "trig.listing")
    assert (lst["skills"], lst["commands"], lst["agents"], lst["unread"], lst["not_loaded"]) == (4, 1, 0, 1, 2)


def test_rules_keys_values_tools():
    fs = run({
        "s/Long_name/SKILL.md": fm("name: Long_name", "description: " + "x " * 600 + "<b>when</b>",
                                   "allowed-tools: Read read Websearch Task mcp__a__b Bash(git commit:*)",
                                   "effort: huge", "disable-model-invocation: perhaps", "allowedTools: Read"),
        "agents/r.md": fm("name: r", "description: Reviews r when asked.", "tools: [Read, Grep, MultiEdit]",
                          "model: claude-opus-5-5", "permissionMode: yolo", "maxturns: 3"),
        "agents/r2.md": fm("name: r", "description: Reviews other things when asked."),
    })
    rules = {f["rule"] for f in by(fs, "trig.rule", file="s/Long_name/SKILL.md")}
    assert rules == {"name-chars", "description-long", "description-xml", "field-outside"}
    assert by(fs, "trig.rule", file="agents/r2.md", rule="name-duplicate", other="agents/r.md")
    keys = {(f["key"], f["near"]) for f in by(fs, "trig.key")}
    assert keys == {("allowedTools", "allowed-tools"), ("maxturns", "maxTurns")}
    vals = {(f["file"], f["field"], f["value"]) for f in by(fs, "trig.value")}
    assert vals == {("s/Long_name/SKILL.md", "effort", "huge"),
                    ("s/Long_name/SKILL.md", "disable-model-invocation", "perhaps"),
                    ("agents/r.md", "permissionMode", "yolo")}
    tools = {(f["tool"], f["kind"], f.get("near") or f.get("now")) for f in by(fs, "trig.tool")}
    assert tools == {("read", "unknown", "Read"), ("Websearch", "unknown", "WebSearch"),
                     ("Task", "older", "Agent"), ("MultiEdit", "older", "Edit")}


def test_the_agent_skills_spec_fields_and_names():
    """R13 (owner, 2026-11-05: "Let's adopt the agentskills.io specs"): in a SKILL.md, a key outside the spec's six fields
    is a rule broken, one row a key with its line; `compatibility` holds at most 500 characters; a name takes lowercase
    letters of any language, digits, and single hyphens, as the spec's reference validator reads it. Commands and agents
    are not skills, so the six fields are not theirs."""
    fs = run({
        "s/a/SKILL.md": fm("name: a", "description: Does a. Use when a.", "license: MIT", "compatibility: Needs git",
                           "metadata:", "  version: '1'", "allowed-tools: Read"),
        "s/b/SKILL.md": fm("name: b", "description: Does b. Use when b.", "version: 2", "model: opus",
                           "compatibility: " + "x" * 501),
        "s/notizen-über/SKILL.md": fm("name: notizen-über", "description: Sorts notes. Use when asked."),
        "s/two--dash/SKILL.md": fm("name: two--dash", "description: Does two. Use when asked."),
        "commands/go.md": fm("description: Goes. Use when asked.", "argument-hint: [where]"),
        "agents/r.md": fm("name: r", "description: Reviews r when asked.", "tools: Read"),
    })
    assert not by(fs, "trig.rule", file="s/a/SKILL.md")
    out = {(f["key"], f["line"]) for f in by(fs, "trig.rule", file="s/b/SKILL.md", rule="field-outside")}
    assert out == {("version", 4), ("model", 5)}
    [c] = by(fs, "trig.rule", file="s/b/SKILL.md", rule="compatibility-long")
    assert (c["chars"], c["line"], c["host"]) == (501, 6, "agent-skills")
    assert not by(fs, "trig.rule", file="s/notizen-über/SKILL.md")
    assert by(fs, "trig.rule", file="s/two--dash/SKILL.md", rule="name-chars")
    assert not by(fs, "trig.rule", rule="field-outside", file="commands/go.md")
    assert not by(fs, "trig.rule", rule="field-outside", file="agents/r.md")
    assert trigger.name_ok("pdf-processing") and trigger.name_ok("données")
    # R15 (owner, 2026-11-05: "read past the blank lines for the standard's checks"): Claude Code does not read settings
    # after blank lines, so the entry is unread; the spec's checks read them, each on its line
    late = run({"s/late/SKILL.md": "\n\n" + fm("name: other", "description: Does late. Use when asked.", "version: 2")})
    assert by(late, "trig.frontmatter", kind="not-first-line") and by(late, "trig.entry")[0]["mode"] == "unread"
    assert {(f["rule"], f["line"]) for f in by(late, "trig.rule")} == {("name-folder", 4), ("field-outside", 6)}
    assert not by(run({"s/x/SKILL.md": "\n---\nname: x\ndescription: Dates: when.\n---\n"}), "trig.rule")  # YAML that does not parse
    assert not any(trigger.name_ok(x) for x in ("PDF", "-pdf", "pdf-", "pdf--x", "pdf_x", ""))


def test_a_setting_set_twice_in_a_skill_header():
    """R17 (owner, 2026-11-05: "duplicates only"): of the YAML the spec's reference validator refuses and PyYAML takes, only
    a key set twice is called out (PyYAML keeps the last value), at any depth, on the line it is set again; inline lists,
    anchors, and tags are not. Commands and agents are left out, as for the spec's other rules."""
    fs = run({
        "s/two/SKILL.md": fm("name: two", "description: Does two. Use when asked.", "license: MIT", "metadata:",
                             "  author: a", "  author: b", "license: Apache-2.0"),
        "s/flow/SKILL.md": fm("name: flow", "description: Does flow. Use when asked.", "allowed-tools: [Read, Grep]",
                              "metadata: &m {author: a}"),
        "commands/go.md": fm("description: Goes. Use when asked.", "model: opus", "model: haiku"),
    })
    got = {(f["key"], f["line"], f["first"], f["host"]) for f in by(fs, "trig.rule", rule="key-twice")}
    assert got == {("metadata.author", 7, 6, "agent-skills"), ("license", 8, 4, "agent-skills")}
    assert not by(fs, "trig.rule", file="s/flow/SKILL.md")
    late = run({"s/late/SKILL.md": "\n" + fm("name: late", "description: Does late. Use when asked.", "name: late")})
    assert {(f["rule"], f["line"], f["first"]) for f in by(late, "trig.rule")} == {("key-twice", 5, 3)}
    assert trigger.set_twice("a: 1\nb:\n  - c: 1\n    c: 2\n") == [(3, "b.c", 2)]


def test_listing_cut_and_guidance():
    fs = run({
        "s/a/SKILL.md": fm("name: a", "description: " + "Builds charts. " * 80, "when_to_use: " + "y" * 600),
        "s/b/SKILL.md": fm("name: b", "description: You can use this to sort files."),
        "s/c/SKILL.md": fm("name: c", "description: Sorts files. Run once at the start of a project."),
        "s/d/SKILL.md": fm("name: d", "description: I help with notes. Use when notes pile up."),
    })
    [cut] = by(fs, "trig.rule", rule="listing-cut")
    assert cut["file"] == "s/a/SKILL.md" and cut["lost"] == cut["chars"] - 1536
    g = {(f["file"], f["kind"]) for f in by(fs, "trig.guidance")}
    assert g == {("s/b/SKILL.md", "second-person"), ("s/d/SKILL.md", "first-person")}
    [lst] = by(fs, "trig.listing")
    assert lst["listing_chars"] == 1536 + sum(f["listing_chars"] for f in by(fs, "trig.entry") if f["file"] != "s/a/SKILL.md")


def test_overlap_within_one_listing_and_without_common_words():
    shared = "Reviews pull requests for bugs, style problems, and missing tests."
    texts = {
        "s/a/SKILL.md": fm("name: a", "description: " + shared + " Use when asked."),
        "s/b/SKILL.md": fm("name: b", "description: Checks " + shared[8:] + " Use before merging."),
        "agents/a.md": fm("name: a", "description: " + shared + " Use proactively."),
    }
    fs = run(texts)
    assert [(f["file"], f["other"]) for f in by(fs, "trig.overlap")] == [("s/a/SKILL.md", "s/b/SKILL.md")]
    # four agents sharing their boilerplate and nothing else
    boiler = "Pipeline stage, spawned by the orchestrator for its phase, or run directly by hand."
    agents = {f"agents/{n}.md": fm(f"name: {n}", f"description: {job} {boiler}")
              for n, job in (("w", "Writes specs."), ("x", "Plans slices."), ("y", "Builds code."), ("z", "Checks results."))}
    assert not by(run(agents), "trig.overlap")
    assert trigger.words("Reviews the bugs and tests") == {"review", "bug", "test"}
