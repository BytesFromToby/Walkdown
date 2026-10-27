"""Tests for cost.py, written from specs/cost.SPEC.md."""
import cost


def inv(*rows):
    out = []
    for r in rows:
        rel, kind = (r, None) if isinstance(r, str) else r
        out.append({"check": "inv.file", "file": rel, "line": None, "bytes": 400, "entry_point": kind,
                    "encoding": None if rel.endswith(".png") else "utf-8"})
    return out


def reports(files, extra=()):
    return {"01": {"findings": inv(*files) + list(extra)}, "04": {"findings": []}}


def edge(frm, to, kind="static", **flags):
    return {"from": frm, "to": to, "kind": kind, "line": 1, **flags}


def groups(r, g):
    return {x["file"]: x["group"] for x in cost.ship(r, g)}


def test_test_data_and_what_a_skill_names():
    r = reports([("SKILL.md", "skill"), ("tests/fixtures/x/SKILL.md", "skill"), "tests/data.md",
                 "README.md", "docs/guide.md", "notes.md"])
    g = {"edges": [edge("SKILL.md", "tests/data.md"), edge("SKILL.md", "docs/guide.md")]}
    got = groups(r, g)
    assert got["tests/fixtures/x/SKILL.md"] == "build"
    assert got["tests/data.md"] == "on-demand" and got["docs/guide.md"] == "on-demand"
    assert got["README.md"] == "people" and got["notes.md"] == "unused"


def test_imports_count_four_hops():
    files = [("CLAUDE.md", "project-instructions"), "a.md", "b.md", "c.md", "d.md", "e.md"]
    chain = ["CLAUDE.md", "a.md", "b.md", "c.md", "d.md", "e.md"]
    g = {"edges": [edge(x, y, at_import=True) for x, y in zip(chain, chain[1:])]}
    got = groups(reports(files), g)
    assert [got[x] for x in chain[1:5]] == ["project"] * 4
    assert got["e.md"] != "project"


def test_session_cuts_descriptions_and_never_sums_hosts():
    desc = {"check": "struct.description", "file": "SKILL.md", "line": 3, "text": "x" * 2000}
    mcp = {"check": "struct.mcp", "file": ".mcp.json", "line": None, "name": "notes"}
    r = reports([("SKILL.md", "skill"), (".mcp.json", "mcp-config")], [desc, mcp])
    inj = [{"mechanism": "hook", "file": "a/hooks.json", "bytes": 800, "event": "SessionStart"},
           {"mechanism": "hook", "file": "b/hooks.json", "bytes": 400, "event": "SessionStart"},
           {"mechanism": "hook", "file": "b/hooks.json", "bytes": None, "event": "UserPromptSubmit"}]
    g = {"edges": []}
    s = next(x for x in cost.context(r, g, inj, cost.ship(r, g)) if x["tier"] == "session")
    assert s["tokens"] == 1536 // 4 + 800 // 4 and s["hook_config"] == "a/hooks.json"
    assert {u["what"] for u in s["unknown"]} == {"hook", "mcp"}


def test_tiers_leave_scripts_out_and_name_images():
    r = reports([("SKILL.md", "skill"), "ref.md", "run.py", "shot.png", "more/x.md"])
    g = {"edges": [edge("SKILL.md", "ref.md"), edge("SKILL.md", "run.py"), edge("SKILL.md", "shot.png"),
                   edge("SKILL.md", "more/x.md", kind="dynamic")]}
    rows = {x["tier"]: x for x in cost.context(r, g, [], cost.ship(r, g)) if x.get("file") == "SKILL.md"}
    assert rows["skill-full"]["files"] == ["SKILL.md", "ref.md", "shot.png"]
    assert rows["skill-full"]["tokens"] == 200 and rows["skill-full"]["not_text"] == ["shot.png"]
    assert "more/x.md" in rows["skill-max"]["files"] and rows["skill-max"]["tokens"] == 300
    assert groups(r, g)["run.py"] == "run"


def test_reach_is_bounded():
    """A skill reaches only inside its folder and lists what it names outside; an agent one level;
    a glob in CLAUDE.md nothing; a script reached only by a wildcard is maybe (2026-10-26)."""
    files = [("skills/a/SKILL.md", "skill"), "skills/a/ref.md", "skills/a/deep.md", "README.md",
             "docs/all.md", ("agents/x.md", "agent"), "notes/one.md", "notes/two.md",
             ("CLAUDE.md", "project-instructions"), "stages/s.md", "skills/a/tools/gen.py"]
    g = {"edges": [edge("skills/a/SKILL.md", "skills/a/ref.md"), edge("skills/a/ref.md", "skills/a/deep.md"),
                   edge("skills/a/ref.md", "README.md"), edge("README.md", "docs/all.md"),
                   edge("agents/x.md", "notes/one.md"), edge("notes/one.md", "notes/two.md"),
                   edge("CLAUDE.md", "stages/s.md", kind="dynamic"),
                   edge("skills/a/SKILL.md", "skills/a/tools/gen.py", kind="dynamic")]}
    r = reports(files)
    got = groups(r, g)
    assert got["skills/a/deep.md"] == "on-demand" and got["docs/all.md"] != "on-demand"
    assert got["notes/one.md"] == "on-demand" and got["notes/two.md"] == "unused"
    assert got["stages/s.md"] == "unused"
    assert got["skills/a/tools/gen.py"] == "maybe"
    rows = {(x.get("file"), x["tier"]): x for x in cost.context(r, g, [], cost.ship(r, g))}
    assert rows[("skills/a/SKILL.md", "skill-full")]["files"] == ["skills/a/SKILL.md", "skills/a/deep.md", "skills/a/ref.md"]
    assert rows[("skills/a/SKILL.md", "skill-max")]["outside"] == ["README.md"]
