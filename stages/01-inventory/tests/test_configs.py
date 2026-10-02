"""Tests for configs.py, written from specs/configs.SPEC.md."""
import json

import configs

HOOKS = {
    "hooks": {
        "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "a.sh"}]}],
        "SessionStart": [
            {"matcher": "startup", "hooks": [{"type": "command", "command": "b.sh", "async": False}]},
            {"matcher": "clear", "hooks": [{"type": "command", "command": "c.sh"},
                                           {"type": "command", "command": "d.sh"}]},
        ],
    }
}


# Done when 1
def test_nested_hook_entries():
    doc = configs.load("h.json", json.dumps(HOOKS))
    assert configs.is_hook_config(doc)
    rows = configs.hook_findings("h.json", doc)
    got = [(r["event"], r["matcher"], r["command"]) for r in rows]
    assert got == [("PreToolUse", "Bash", "a.sh"), ("SessionStart", "startup", "b.sh"),
                   ("SessionStart", "clear", "c.sh\nd.sh")]
    assert all(r["check"] == "struct.hooks" and r["file"] == "h.json" and r["line"] is None
               for r in rows)
    assert rows[1]["format"] == "nested" and rows[1]["async"] == [False]


# Done when 2
def test_flat_entry_without_matcher():
    doc = {"version": 1, "hooks": {"sessionStart": [{"command": "./run.cmd x"}]}}
    rows = configs.hook_findings("c.json", doc)
    assert len(rows) == 1
    assert rows[0]["matcher"] is None and rows[0]["format"] == "flat"
    assert rows[0]["command"] == "./run.cmd x" and rows[0]["event"] == "sessionStart"


# Done when 3
def test_not_hook_configs():
    assert not configs.is_hook_config({"name": "x"})
    assert not configs.is_hook_config({"hooks": {}})
    assert not configs.is_hook_config({"hooks": "x"})
    assert configs.load("bad.json", "{not json") is None
    assert configs.load("a.txt", "{}") is None


# Done when 4
def test_grant_tokens():
    assert configs.manifest_grants({"name": "w", "tools": ["Read", "Glob"]}) == ["Glob", "Read"]
    doc = {"name": "w", "permissions": {"allowedTools": ["Read", "Bash"], "network": True,
                                        "bypassPermissions": True, "sandbox": False}}
    assert configs.manifest_grants(doc) == ["Bash", "Read", "bypassPermissions", "network",
                                            "sandbox=false"]
    assert configs.manifest_grants({"tools": ["Read"]}) is None


# Done when 5
def test_manifest_sets_and_divergence():
    rows = configs.manifest_findings([
        ("b/plugin.json", "w", ["Read"]),
        ("a/plugin.json", "w", ["Bash", "Read"]),
        ("c.json", "v", ["Read"]),
        ("d.json", "v", ["Read"]),
        ("e.json", "solo", []),
    ])
    by = {r["name"]: r for r in rows}
    assert [r["name"] for r in rows] == ["solo", "v", "w"]
    assert by["w"]["divergent"] is True and by["w"]["files"] == ["a/plugin.json", "b/plugin.json"]
    assert by["v"]["divergent"] is False and by["solo"]["divergent"] is False
    assert all(r["check"] == "struct.manifests" and r["file"] is None for r in rows)
    assert by["w"]["grants"]["b/plugin.json"] == ["Read"]


# Done when 6
def test_manifest_by_known_name():
    assert configs.is_manifest(".x-plugin/plugin.json", {"name": "p", "version": "1"})
    assert not configs.is_manifest("package.json", {"name": "p", "version": "1"})
    assert configs.is_manifest("package.json", {"name": "p", "permissions": []})
    assert not configs.is_manifest("plugin.json", {"version": "1"})


# Done when 7
def test_yaml_manifest():
    doc = configs.load("p/plugin.yaml", "name: p\ntools:\n  - Read\n")
    assert configs.is_manifest("p/plugin.yaml", doc)
    assert configs.manifest_grants(doc) == ["Read"]
    assert configs.load("x.yml", "!!python/object/apply:os.system ['echo']") is None


def test_mcp_servers_from_any_config():
    doc = {"name": "p", "mcpServers": {
        "tasks": {"command": "${CLAUDE_PLUGIN_ROOT}/start.sh", "args": ["--x"],
                  "env": {"TOKEN": "secret-value", "ROOT": "/d"}},
        "remote": {"type": "http", "url": "https://mcp.invalid/v1"}}}
    rows = configs.mcp_findings(".claude-plugin/plugin.json", doc)
    by = {r["name"]: r for r in rows}
    assert by["tasks"]["transport"] == "stdio" and by["tasks"]["command"] == "${CLAUDE_PLUGIN_ROOT}/start.sh --x"
    assert by["tasks"]["env_keys"] == ["ROOT", "TOKEN"] and "secret-value" not in str(rows)
    assert by["remote"]["transport"] == "http" and by["remote"]["url"] == "https://mcp.invalid/v1"
    assert configs.mcp_findings("x.json", {"name": "p"}) == []
