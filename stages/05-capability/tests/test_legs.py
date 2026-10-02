"""Tests for legs.py, written from specs/legs.SPEC.md."""
import legs


def reports(s1=(), s4=()):
    return {
        "01": {"stage": "01-inventory", "contract": 1, "findings": list(s1)},
        "02": {"stage": "02-reader", "contract": 1, "findings": []},
        "03": {"stage": "03-graph", "contract": 1, "findings": []},
        "04": {"stage": "04-phrases", "contract": 1, "findings": list(s4)},
    }


def phrase(check, patterns, file="SKILL.md", line=5):
    return {"check": check, "file": file, "line": line, "quote": "q", "patterns": patterns}


def agent(tools, file="agents/a.md", line=4):
    return {"check": "struct.agent-tools", "file": file, "line": line, "tools": tools,
            "description": "d"}


def hook(event, file="hooks/hooks.json"):
    return {"check": "struct.hooks", "file": file, "line": None, "event": event,
            "matcher": "", "command": "x"}


def present(r):
    return {f["leg"]: f["present"] for f in legs.legs(r)}


def grant_kinds(r):
    return [g["grant"] for g in legs.grants(r, legs.legs(r))]


def test_empty_gives_three_absent_legs_no_grants():
    out = legs.legs(reports())
    assert [f["leg"] for f in out] == ["private-data", "untrusted-content", "external-comms"]
    for f in out:
        assert f["check"] == "cap.leg" and f["file"] is None and f["line"] is None
        assert f["present"] is False and f["evidence"] == []
    assert legs.grants(reports(), out) == []


def test_phrase_rules():
    assert present(reports(s4=[phrase("phrase.creds", ["creds.dotenv"])])) == {
        "private-data": True, "untrusted-content": False, "external-comms": False}
    assert present(reports(s4=[phrase("phrase.K.exfil", ["K.data-flow"])])) == {
        "private-data": True, "untrusted-content": False, "external-comms": True}
    assert present(reports(s4=[phrase("phrase.K.exfil", ["K.http-verb"])])) == {
        "private-data": False, "untrusted-content": False, "external-comms": True}
    assert present(reports(s4=[phrase("phrase.K.exfil", ["K.telemetry"])])) == {
        "private-data": False, "untrusted-content": False, "external-comms": False}
    assert present(reports(s4=[phrase("phrase.K.exfil", ["K.md-carrier"])]))[
        "external-comms"] is False


def test_tool_grants():
    assert present(reports(s1=[agent(["Read", "Bash"])])) == {
        "private-data": True, "untrusted-content": False, "external-comms": False}
    assert present(reports(s1=[agent(["WebFetch"])])) == {
        "private-data": False, "untrusted-content": True, "external-comms": True}
    r = reports(s1=[agent(None)])
    assert present(r) == {"private-data": True, "untrusted-content": True,
                          "external-comms": True}
    assert "elevated" in grant_kinds(r)
    assert present(reports(s1=[agent(["Bash(git:*)"])]))["private-data"] is True
    assert present(reports(s1=[agent([" Read "])]))["private-data"] is True
    assert present(reports(s1=[agent(["read"])]))["private-data"] is False


def test_remote_load_and_mcp():
    r = reports(s4=[phrase("phrase.remote-load", ["RL.fetch-follow"])])
    assert present(r) == {"private-data": False, "untrusted-content": True,
                          "external-comms": True}
    mcp = {"check": "inv.file", "file": ".mcp.json", "line": None, "entry_point": "mcp-config"}
    r = reports(s1=[mcp])
    assert present(r) == {"private-data": False, "untrusted-content": True,
                          "external-comms": True}
    ev = legs.legs(r)[1]["evidence"][0]
    assert ev["why"] == "entry point: mcp-config" and ev["stage"] == "01"


def test_hooks():
    r = reports(s1=[hook("PreToolUse")])
    assert present(r)["private-data"] is True
    assert grant_kinds(r) == ["exec-at-load"]
    r = reports(s1=[hook("SessionStart")])
    assert present(r)["private-data"] is False
    gs = legs.grants(r, legs.legs(r))
    assert [g["grant"] for g in gs] == ["exec-at-load", "context-injection"]
    assert gs[0]["evidence"][0]["why"] == "hook event: SessionStart"
    r = reports(s1=[hook("sessionStart")])
    assert grant_kinds(r) == ["exec-at-load", "context-injection"]


def test_persistence_network_elevated_context():
    r = reports(s4=[phrase("phrase.E.env", ["E.persist-redirect"])])
    assert grant_kinds(r) == ["persistence"]
    r = reports(s4=[phrase("phrase.E.perms", ["E.install-global"])])
    assert grant_kinds(r) == ["persistence", "network"]
    r = reports(s4=[phrase("phrase.E.perms", ["E.perm-flags"])])
    assert grant_kinds(r) == ["elevated"]
    r = reports(s4=[phrase("phrase.E.perms", ["E.exec-primitive"])])
    assert grant_kinds(r) == []
    desc = {"check": "struct.description", "file": "SKILL.md", "line": 3, "text": "t"}
    assert grant_kinds(reports(s1=[desc])) == ["context-injection"]


def test_network_takes_external_comms_evidence():
    r = reports(s1=[agent(["WebSearch"])],
                s4=[phrase("phrase.K.exfil", ["K.http-verb"], file="s.sh", line=2)])
    lg = legs.legs(r)
    ext = lg[2]["evidence"]
    net = [g for g in legs.grants(r, lg) if g["grant"] == "network"][0]
    for e in ext:
        assert e in net["evidence"]
    assert len(ext) == 2


def test_evidence_shape_and_merging():
    r = reports(s4=[phrase("phrase.K.exfil", ["K.dest-ref", "K.data-flow"], line=7)])
    ev = legs.legs(r)[2]["evidence"]
    assert len(ev) == 1
    e = ev[0]
    assert set(e) == {"stage", "check", "file", "line", "why"}
    assert e["stage"] == "04" and e["check"] == "phrase.K.exfil" and e["line"] == 7
    assert "K.dest-ref" in e["why"] and "K.data-flow" in e["why"]


def test_skipped_findings_ignored():
    s = {"check": "phrase.creds", "file": "x", "line": None, "skipped": "no"}
    assert present(reports(s4=[s]))["private-data"] is False


def test_mcp_server_in_a_manifest_counts_toward_untrusted_and_external():
    r = {"01": {"findings": [{"check": "struct.mcp", "file": ".claude-plugin/plugin.json", "line": None,
                              "name": "tasks", "transport": "stdio"}]},
         "04": {"findings": []}}
    got = {f["leg"]: f["present"] for f in legs.legs(r)}
    assert got == {"private-data": False, "untrusted-content": True, "external-comms": True}


def test_human_audience_phrase_evidence_is_ignored():
    readme = {"check": "phrase.remote-load", "file": "README.md", "line": 3, "patterns": ["RL.fetch-follow"],
              "audience": "human", "quote": "fetch and follow"}
    skill = dict(readme, file="SKILL.md", audience="model")
    got = {f["leg"]: f["present"] for f in legs.legs({"01": {"findings": []}, "04": {"findings": [readme]}})}
    assert got["untrusted-content"] is False
    got = {f["leg"]: f["present"] for f in legs.legs({"01": {"findings": []}, "04": {"findings": [skill]}})}
    assert got["untrusted-content"] is True


def _legs(s1=(), s4=()):
    return {f["leg"]: f for f in legs.legs({"01": {"findings": list(s1)}, "04": {"findings": list(s4)}})}


def test_clone_and_installs_take_outside_input():
    for check, pat in [("phrase.E.env", "E.clone"), ("phrase.E.env", "E.install"),
                       ("phrase.E.perms", "E.install-global"), ("phrase.E.perms", "E.runtime-install")]:
        hit = {"check": check, "file": "SKILL.md", "line": 3, "patterns": [pat], "audience": "model", "quote": "x"}
        got = _legs(s4=[hit])
        assert got["untrusted-content"]["present"] is True, pat
        assert got["external-comms"]["present"] is False, pat


def test_connectors_read_your_data():
    phrase = {"check": "phrase.E.env", "file": "SKILL.md", "line": 3, "patterns": ["E.connector"],
              "audience": "model", "quote": "Connect your Gmail account"}
    assert _legs(s4=[phrase])["private-data"]["present"] is True
    tool = {"check": "struct.agent-tools", "file": "agents/a.md", "line": 4,
            "tools": ["mcp__google-drive__search_files"]}
    got = _legs(s1=[tool])["private-data"]
    assert got["present"] is True and "connector tool grant" in got["evidence"][0]["why"]
    server = {"check": "struct.mcp", "file": ".mcp.json", "line": None, "name": "gmail", "command": "npx x"}
    whys = [e["why"] for e in _legs(s1=[server])["private-data"]["evidence"]]
    assert "connector MCP server: gmail" in whys
    plain = {"check": "struct.mcp", "file": ".mcp.json", "line": None, "name": "tasks", "command": "node s.js"}
    assert _legs(s1=[plain])["private-data"]["present"] is False
