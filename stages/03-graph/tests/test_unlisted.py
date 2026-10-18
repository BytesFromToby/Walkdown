"""Tests for unlisted.py, written from specs/unlisted.SPEC.md."""
import unlisted as ul

M = ".claude-plugin/plugin.json"
NODES = [M, "README.md", "skills/a/SKILL.md", "skills/a/ref.md", "skills/b/SKILL.md",
         "skills/c/SKILL.md", "agents/x.md", "agents/y.md", "commands/z.md"]


def edge(frm, to, kind="static"):
    return {"from": frm, "to": to, "kind": kind}


def test_unlisted_skill_and_agent_not_commands():
    edges = [edge(M, "skills/a/SKILL.md", "dynamic"), edge(M, "skills/b/SKILL.md", "dynamic"),
             edge(M, "agents/x.md")]
    out = ul.unlisted([M], NODES, edges)
    assert [(f["file"], f["kind"], f["listed"], f["on_disk"]) for f in out] == [
        ("skills/c/SKILL.md", "skill", 2, 3), ("agents/y.md", "agent", 1, 2)]  # kind order
    assert all(f["check"] == "graph.unlisted" and f["manifest"] == M and f["line"] is None
               for f in out)


def test_folder_reference_lists_every_skill():
    edges = [edge(M, t, "dynamic") for t in NODES if t.startswith("skills/")]
    assert ul.unlisted([M], NODES, edges) == []


def test_no_component_references_compares_nothing():
    assert ul.unlisted([M], NODES, [edge(M, "README.md")]) == []


def test_nested_plugin_owns_its_components():
    outer = ".claude-plugin/marketplace.json"
    inner = "plugins/p/.claude-plugin/plugin.json"
    nodes = [outer, inner, "skills/a/SKILL.md", "skills/b/SKILL.md", "plugins/p/skills/q/SKILL.md"]
    edges = [edge(outer, "skills/a/SKILL.md", "dynamic")]
    out = ul.unlisted([outer, inner], nodes, edges)
    assert [(f["file"], f["manifest"]) for f in out] == [("skills/b/SKILL.md", outer)]
    assert ul.manifest_root(inner) == "plugins/p" and ul.manifest_root("plugin.yaml") == ""


def test_one_manifest_per_host_each_compared():
    claude, cursor = ".claude-plugin/plugin.json", ".cursor-plugin/plugin.json"
    nodes = [claude, cursor, "skills/a/SKILL.md", "skills/b/SKILL.md"]
    edges = [edge(claude, "skills/a/SKILL.md"), edge(claude, "skills/b/SKILL.md"),
             edge(cursor, "skills/a/SKILL.md")]
    out = ul.unlisted([claude, cursor], nodes, edges)
    assert [(f["file"], f["manifest"]) for f in out] == [("skills/b/SKILL.md", cursor)]
