"""Tests for trigger.py, written from specs/trigger.SPEC.md."""
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
    assert rules == {"name-chars", "description-long", "description-xml"}
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
