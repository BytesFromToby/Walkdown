"""Tests for injection.py, written from specs/injection.SPEC.md."""
import injection


def reports(s1):
    return {"01": {"stage": "01-inventory", "contract": 1, "findings": list(s1)},
            "02": {"stage": "02-reader", "contract": 1, "findings": []},
            "03": {"stage": "03-graph", "contract": 1, "findings": []},
            "04": {"stage": "04-phrases", "contract": 1, "findings": []}}


def inv(path, size):
    return {"check": "inv.file", "file": path, "line": None, "bytes": size, "entry_point": None}


def hook(event, command, file="hooks/hooks.json"):
    return {"check": "struct.hooks", "file": file, "line": None, "event": event,
            "matcher": "startup", "command": command, "commands": [command]}


def edge(frm, to, line, text, kind="static"):
    return {"from": frm, "line": line, "to": to, "kind": kind, "form": "x", "text": text,
            "context": "code"}


def graph(paths, edges):
    return {"nodes": [{"path": p, "entry": None, "depth": 0} for p in paths], "edges": edges}


ISSUE_BOT_FILES = [("SKILL.md", 658), ("hooks/hooks.json", 309), ("scripts/inject.sh", 233)]


def issue_bot(command="${CLAUDE_PLUGIN_ROOT}/scripts/inject.sh", event="SessionStart"):
    s1 = [inv(p, b) for p, b in ISSUE_BOT_FILES] + [hook(event, command)]
    g = graph([p for p, _ in ISSUE_BOT_FILES], [
        edge("hooks/hooks.json", "scripts/inject.sh", 5, "${CLAUDE_PLUGIN_ROOT}/scripts/inject.sh"),
        edge("scripts/inject.sh", "SKILL.md", 3, "${CLAUDE_PLUGIN_ROOT}/SKILL.md"),
    ])
    return reports(s1), g


def test_description_bytes_exact():
    d = {"check": "struct.description", "file": "SKILL.md", "line": 3, "text": "héllo"}
    out = injection.injections(reports([d]), None)
    assert len(out) == 1
    f = out[0]
    assert f["check"] == "cap.injection" and f["mechanism"] == "description"
    assert f["bytes"] == 6 and f["basis"] == "exact"
    assert f["file"] == "SKILL.md" and f["line"] == 3
    assert f["evidence"][0]["check"] == "struct.description"


def test_session_start_hook_estimate():
    r, g = issue_bot()
    out = injection.injections(r, g)
    assert len(out) == 1
    f = out[0]
    assert f["mechanism"] == "hook" and f["event"] == "SessionStart"
    assert f["file"] == "hooks/hooks.json"
    assert f["command"] == "${CLAUDE_PLUGIN_ROOT}/scripts/inject.sh"
    assert f["bytes"] == 658 and f["basis"] == "estimate"
    whys = [e["why"] for e in f["evidence"]]
    assert whys[0] == "hook event: SessionStart"
    assert any("SKILL.md" in w and "658" in w for w in whys)
    ge = [e for e in f["evidence"] if e["stage"] == "03"][0]
    assert ge["file"] == "scripts/inject.sh" and ge["line"] == 3


def test_wrapper_argument_names_script():
    files = [("hooks/hooks.json", 300), ("hooks/run-hook.cmd", 1000),
             ("hooks/session-start", 2000), ("skills/u/SKILL.md", 5000)]
    cmd = '"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd" session-start'
    s1 = [inv(p, b) for p, b in files] + [hook("SessionStart", cmd)]
    g = graph([p for p, _ in files], [
        edge("hooks/hooks.json", "hooks/run-hook.cmd", 9,
             "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd"),
        edge("hooks/session-start", "skills/u/SKILL.md", 11,
             "${PLUGIN_ROOT}/skills/u/SKILL.md"),
    ])
    f = injection.injections(reports(s1), g)[0]
    assert f["bytes"] == 5000 and f["basis"] == "estimate"
    # cursor flat form: ./hooks/run-hook.cmd session-start
    s1 = [inv(p, b) for p, b in files] + [hook("sessionStart", "./hooks/run-hook.cmd session-start",
                                               file="hooks/hooks-cursor.json")]
    f = injection.injections(reports(s1), g)[0]
    assert f["bytes"] == 5000 and f["event"] == "sessionStart"


def test_unknown_bytes():
    # script not in the tree
    r, g = issue_bot(command="/usr/local/bin/other.sh")
    f = injection.injections(r, g)[0]
    assert f["bytes"] is None and f["basis"] == "unknown"
    # script names no file
    r, g = issue_bot()
    g["edges"] = g["edges"][:1]
    f = injection.injections(r, g)[0]
    assert f["bytes"] is None and f["basis"] == "unknown"
    # no graph
    r, _ = issue_bot()
    f = injection.injections(r, None)[0]
    assert f["bytes"] is None and f["basis"] == "unknown"


def test_events():
    r, g = issue_bot(event="UserPromptSubmit")
    out = injection.injections(r, g)
    assert len(out) == 1 and out[0]["event"] == "UserPromptSubmit"
    lb = injection.load_bytes(out)[0]
    assert lb["bytes"] == 0 and lb["basis"] == "exact" and lb["unknown_parts"] == 0
    r, g = issue_bot(event="PreToolUse")
    assert injection.injections(r, g) == []


def part(mech, b, basis, event=None):
    f = {"check": "cap.injection", "file": "f", "line": 1, "mechanism": mech, "bytes": b,
         "basis": basis, "evidence": []}
    if event:
        f["event"] = event
    return f


def test_load_bytes():
    lb = injection.load_bytes([part("description", 10, "exact"), part("description", 5, "exact")])[0]
    assert lb["check"] == "cap.load-bytes" and lb["file"] is None and lb["line"] is None
    assert (lb["bytes"], lb["basis"], lb["unknown_parts"]) == (15, "exact", 0)
    lb = injection.load_bytes([part("description", 10, "exact"),
                               part("hook", 100, "estimate", "SessionStart")])[0]
    assert (lb["bytes"], lb["basis"]) == (110, "estimate")
    lb = injection.load_bytes([part("description", 10, "exact"),
                               part("hook", None, "unknown", "SessionStart")])[0]
    assert (lb["bytes"], lb["basis"], lb["unknown_parts"]) == (10, "estimate", 1)
    lb = injection.load_bytes([part("hook", None, "unknown", "SessionStart")])[0]
    assert (lb["bytes"], lb["basis"], lb["unknown_parts"]) == (None, "unknown", 1)
    lb = injection.load_bytes([])[0]
    assert (lb["bytes"], lb["basis"], lb["unknown_parts"]) == (0, "exact", 0)
    lb = injection.load_bytes([part("description", 10, "exact"),
                               part("hook", 99, "estimate", "UserPromptSubmit")])[0]
    assert (lb["bytes"], lb["basis"]) == (10, "exact")


def test_load_bytes_per_host_config():
    a = dict(part("hook", 100, "estimate", "SessionStart"), file="hooks/a.json")
    b = dict(part("hook", 100, "estimate", "SessionStart"), file="hooks/b.json")
    out = injection.load_bytes([part("description", 10, "exact"), a, b])
    assert [(x["file"], x["bytes"]) for x in out] == [("hooks/a.json", 110), ("hooks/b.json", 110)]


def test_plugin_root_in_a_subfolder():
    # ${CLAUDE_PLUGIN_ROOT} is the folder holding .claude-plugin/, not the repo root
    graph = {"nodes": [{"path": p} for p in ["pkg/x/.claude-plugin/plugin.json",
                                             "pkg/x/hooks/hooks.json", "pkg/x/hooks/start.sh"]],
             "edges": []}
    h = {"check": "struct.hooks", "file": "pkg/x/hooks/hooks.json", "line": None,
         "event": "SessionStart", "command": 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/start.sh"'}
    assert injection.hook_scripts(h, graph) == ["pkg/x/hooks/start.sh"]
