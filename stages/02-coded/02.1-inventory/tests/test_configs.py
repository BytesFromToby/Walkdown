"""Tests for configs.py, written from specs/inventory.SPEC.md, configs."""
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


# Done when 8 (added 2026-10-17, review C31)
CURSOR_ENV = """{
  "install": "curl -fsSL https://x.invalid/setup.sh | bash",
  "start": "sudo service docker start",
  "terminals": [
    {"name": "web", "command": "npm run dev"},
    {"name": "notes"}
  ],
  "snapshot": "snap-1"
}
"""


def test_cursor_environment_commands_are_host_run_rows():
    doc = json.loads(CURSOR_ENV)
    rows = configs.cursor_env_findings(".cursor/environment.json", doc, CURSOR_ENV)
    assert [r["event"] for r in rows] == ["install", "start", "terminal: web"]
    assert [r["line"] for r in rows] == [2, 3, 5]
    assert rows[0]["command"] == "curl -fsSL https://x.invalid/setup.sh | bash"
    assert all(r["check"] == "struct.hooks" and r["format"] == "cursor-environment"
               and r["host"] == "cursor-cloud" and r["matcher"] is None for r in rows)
    assert configs.cursor_env_findings("tools/x/.cursor/environment.json", doc, CURSOR_ENV)
    assert configs.cursor_env_findings("config/environment.json", doc, CURSOR_ENV) == []
    assert configs.cursor_env_findings(".cursor/environment.json", ["install"], "[]") == []
    assert configs.cursor_env_findings(".cursor/environment.json", {"snapshot": "s"}, "{}") == []


# Done when 9 (added 2026-11-01)
NESTED = """{
  "hooks": {
    "Stop": [
      {
        "matcher": "a",
        "hooks": [
          {"type": "command", "command": "one"},
          {"type": "command", "command": "two"}
        ]
      },
      {"command": "flat"}
    ]
  }
}
"""


def test_a_hook_says_the_lines_of_its_entry_and_of_its_event_and_keeps_a_null_line():
    rows = configs.hook_findings("h.json", json.loads(NESTED), NESTED)
    assert [(r["span"], r["event_line"], r["line"]) for r in rows] == [([4, 10], 3, None), ([11, 11], 3, None)]


def test_a_yaml_hook_with_a_block_command_reaches_its_last_line():
    text = ("hooks:\n  Stop:\n    - hooks:\n        - type: command\n          command: |\n            one\n            two\n"
            "    - command: three\n")
    rows = configs.hook_findings("h.yaml", configs.load("h.yaml", text), text)
    assert rows[0]["span"] == [3, 7] and rows[1]["span"] == [8, 8] and rows[0]["event_line"] == 2


def test_a_hook_in_a_text_that_does_not_compose_or_with_no_text_has_no_place():
    doc = json.loads(NESTED)
    for text in (None, "", "a: b: c"):
        rows = configs.hook_findings("h.json", doc, text)
        assert rows and all("span" not in r and "event_line" not in r for r in rows)


def test_a_cursor_row_says_where_its_command_or_its_terminal_is():
    rows = configs.cursor_env_findings(".cursor/environment.json", json.loads(CURSOR_ENV), CURSOR_ENV)
    assert [r["span"] for r in rows] == [[2, 2], [3, 3], [5, 5]] and [r["event_line"] for r in rows] == [2, 3, 5]


def test_a_server_spans_from_its_name_to_the_end_of_its_entry():
    text = '{\n  "mcpServers": {\n    "tasks": {\n      "command": "x",\n      "args": ["y"]\n    },\n    "b": {"url": "z"}\n  }\n}\n'
    rows = configs.mcp_findings(".mcp.json", json.loads(text), text)
    assert [r["span"] for r in rows] == [[3, 6], [7, 7]]
    assert all("span" not in r for r in configs.mcp_findings(".mcp.json", json.loads(text)))
    text = "mcpServers:\n  tasks:\n    command: x\n  b:\n    url: z\n"  # a name on a line of its own: it can hold the key
    assert [r["span"] for r in configs.mcp_findings("m.yaml", configs.load("m.yaml", text), text)] == [[2, 3], [4, 5]]
