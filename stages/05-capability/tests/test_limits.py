"""Tests for limits.py, written from specs/limits.SPEC.md."""
import limits


def inv(*rows):
    return {"findings": list(rows)}


def entry(file, kind):
    return {"check": "inv.file", "file": file, "line": None, "entry_point": kind}


def tools(file, t):
    return {"check": "struct.agent-tools", "file": file, "line": None, "tools": t}


def hit(file, line, quote="Stay read-only: run `git diff`.", aud="model"):
    return {"check": "phrase.B.defs", "file": file, "line": line, "quote": quote,
            "patterns": ["B.safety-adjective"], "audience": aud}


def setting(file, line, rules_out=(), grants=False, kind="tools-flag", value=None):
    s = {"check": "limit.setting", "file": file, "line": line, "kind": kind, "rules_out": list(rules_out),
         "grants_write": grants, "audience": "model"}
    if value:
        s["value"] = value
    return s


def run(s1, s4):
    return {f"{x['file']}:{x['line']}": x for x in limits.stated_limits({"01": inv(*s1), "04": inv(*s4)})}


# Done when 1
def test_owner_tools_list_decides():
    s1 = [entry("skills/a/SKILL.md", "skill"), tools("skills/a/SKILL.md", ["Read", "Grep"]),
          entry("skills/b/SKILL.md", "skill"), tools("skills/b/SKILL.md", ["Read", "Bash"]),
          entry("skills/c/SKILL.md", "skill")]
    out = run(s1, [hit("skills/a/SKILL.md", 9), hit("skills/b/SKILL.md", 9), hit("skills/c/SKILL.md", 9)])
    assert (out["skills/a/SKILL.md:9"]["status"], out["skills/a/SKILL.md:9"]["backed_by"]) == ("backed", "tools-list")
    assert out["skills/b/SKILL.md:9"]["status"] == "contradicted"
    c = out["skills/c/SKILL.md:9"]
    assert (c["status"], c["backed_by"], c["owner"], c["owner_tools"]) == ("stated", None, "skills/c/SKILL.md", None)


# Done when 2
def test_flag_on_the_line_backs_it():
    s1 = [entry("skills/b/SKILL.md", "skill"), tools("skills/b/SKILL.md", ["Read", "Bash"])]
    out = run(s1, [hit("skills/b/SKILL.md", 4), setting("skills/b/SKILL.md", 4, ["write", "shell", "network"])])
    assert (out["skills/b/SKILL.md:4"]["status"], out["skills/b/SKILL.md:4"]["backed_by"]) == ("backed", "flag")


# Done when 3 and 4
def test_reference_owner_and_other_routes():
    s1 = [entry("skills/a/SKILL.md", "skill"), entry("skills/z/SKILL.md", "skill"),
          entry("skills/a/agents/helper.md", "agent"), tools("skills/a/agents/helper.md", None)]
    s4 = [hit("skills/a/references/r.md", 3),
          setting("skills/a/references/fast.md", 5, grants=True, kind="sandbox", value="danger-full-access"),
          setting("skills/z/x.md", 2, grants=True, kind="sandbox", value="danger-full-access")]
    f = run(s1, s4)["skills/a/references/r.md:3"]
    assert f["owner"] == "skills/a/SKILL.md" and f["status"] == "stated"
    assert f["other_route_at"] == ["skills/a/references/fast.md:5", "skills/a/agents/helper.md:None"]
    assert "danger-full-access" in f["other_routes"][0]["what"]
    assert f["other_routes"][1]["what"] == "an agent with no tools list"


# Done when 5
def test_only_read_only_wording_a_model_reads():
    s1 = [entry("SKILL.md", "skill")]
    s4 = [hit("SKILL.md", 2, aud="human"), hit("SKILL.md", 3, quote="Keep it harmless: run `x`.")]
    assert run(s1, s4) == {}


def test_safety_definition_counts():
    s1 = [entry("skills/a/SKILL.md", "skill")]
    d = {"check": "term.safety", "file": "skills/a/ref.md", "line": 7, "term": "read-only here",
         "quote": "Read-only here means non-mutating.", "audience": "model"}
    f = run(s1, [d])["skills/a/ref.md:7"]
    assert f["status"] == "stated" and f["owner"] == "skills/a/SKILL.md"
