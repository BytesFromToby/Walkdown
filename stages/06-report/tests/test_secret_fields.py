"""A report never repeats a secret it found, in any field of any step: a whole run of a made-up skill with one fake key in every
place a step keeps a person's words. Written from specs/report.SPEC.md, run, and `stages/_shared/specs/shared.SPEC.md`, secretmask."""
import importlib.util
import json
from pathlib import Path

import pytest

import secret_skill as S


@pytest.fixture(scope="module")
def probe(tmp_path_factory):
    import runner
    base = tmp_path_factory.mktemp("probe")
    repo = base / "repo"
    S.write(repo)
    with pytest.MonkeyPatch.context() as mp:
        for k in ("WALKDOWN_SOFT_SWEEP", "WALKDOWN_SOFT_PINPOINT"):
            mp.delenv(k, raising=False)
        assert runner.main([str(repo), "--repo", "probe", "--results", str(base / "results"), "--date", "2026-02-03",
                            "--no-validate"]) == 0
    return next((base / "results" / "probe").iterdir())


def rows(run, step, check):
    doc = json.loads((run / "data" / f"{step}.json").read_text(encoding="utf-8"))
    return [f for f in doc["findings"] if f.get("check") == check]


def test_every_key_in_the_made_up_skill_is_flagged_so_the_test_means_something(probe):
    flagged = {(f["file"], f["line"]) for f in rows(probe, "02.4-phrases", "secret.found") if "skipped" not in f}
    for rel, text in S.FILES.items():
        for n, line in enumerate(text.split("\n"), 1):
            if "sk-ant-api03-QX" in line:
                assert (rel, n) in flagged, (rel, n)
    every = "\n".join(S.FILES.values())
    assert all(S.key(label) in every for label in S.LABELS)


def test_a_key_the_scan_flagged_is_in_no_report_and_no_step_output(probe):
    assert S.leaks(probe) == {}
    normalized = "".join(p.read_text(encoding="utf-8", errors="replace")
                         for p in (probe / "data" / "normalized" / "text").rglob("*.txt"))
    assert all(S.key(label) in normalized for label in S.LABELS)  # the file's own text, and only there


def test_a_lock_file_is_left_out_with_no_flag_and_the_pages_say_so(probe):
    """Only a lock file is left out by name (`02.4-phrases`'s spec, secret_scan), and details.html and full.md say so. summary.html and
    review.html do not change (owner, 2026-11-01)."""
    doc = json.loads((probe / "data" / "02.4-phrases.json").read_text(encoding="utf-8"))
    assert doc["secret_left_out"] == ["package-lock.json"]
    assert "package-lock.json" not in {f["file"] for f in rows(probe, "02.4-phrases", "secret.found")}
    details = (probe / "details.html").read_text(encoding="utf-8")
    assert "The secret scan left out 1 lock file, since the hashes in a lock file look like keys, so it may hold one:" in details
    assert "The secret scan left out 1 lock file." in (probe / "full.md").read_text(encoding="utf-8")
    for page in ("summary.html", "review.html"):
        assert "lock file" not in (probe / page).read_text(encoding="utf-8"), page


def test_each_place_is_still_counted_and_named_by_where_it_is(probe):
    hooks = rows(probe, "02.1-inventory", "struct.hooks")
    assert len(hooks) == 12
    masked = [h for h in hooks if h.get("masked")]
    assert masked and all(h["command"].startswith("[line not shown") for h in masked if h.get("span") and h["command"])
    full = (probe / "full.md").read_text(encoding="utf-8")
    assert "hooks/hooks.json:4: event SessionStart" in full  # the entry to open, since the command is gone
    assert "hooks/hooks.json: event Notification" in full  # a hook with its words is named as it was
    details = (probe / "details.html").read_text(encoding="utf-8")
    assert "hooks/hooks.json:4" in details and "hooks/hooks.json:13" in details
    assert len(rows(probe, "02.3-graph", "graph.dangling")) >= 2
    assert {d["file"] for d in rows(probe, "02.1-inventory", "struct.description") if d.get("masked")} >= {
        "SKILL.md", "skills/block/SKILL.md", "skills/folded/SKILL.md", "skills/quoted/SKILL.md", "skills/badyaml/SKILL.md"}


def test_a_plain_event_and_a_plain_tool_stay_since_they_are_what_a_page_is_for(probe):
    hooks = rows(probe, "02.1-inventory", "struct.hooks")
    assert {"SessionStart", "PreToolUse", "Stop"} <= {h["event"] for h in hooks if h.get("masked")}
    agent = next(a for a in rows(probe, "02.1-inventory", "struct.agent-tools") if a["file"] == "agents/b.md")
    assert agent["masked"] and agent["tools"][0] == "Read" and agent["tools"][1].startswith("[line not shown")
    clean = next(a for a in rows(probe, "02.1-inventory", "struct.agent-tools") if a["file"] == "agents/a.md")
    assert clean["tools"] == ["Read", "Grep"] and clean["description"].startswith("[line not shown")


def test_a_line_that_holds_no_key_keeps_its_words(probe):
    hooks = {h["command"]: h for h in rows(probe, "02.1-inventory", "struct.hooks")}
    assert "bash guard.sh" not in hooks  # its matcher is on a flagged line of its entry, so the entry is masked
    assert "bash ok.sh" in hooks and "bash two.sh" not in hooks  # h.yaml's entry holds a flagged line
    assert not hooks["bash ok.sh"].get("masked")
    assert "bash start.sh" in hooks and not hooks["bash start.sh"].get("masked")
    two = next(d for d in rows(probe, "02.1-inventory", "struct.description") if d["file"] == "skills/two/SKILL.md")
    assert two["text"] == "A second skill, use when two." and "masked" not in two  # a key in the body is not in its description


def test_the_steps_read_the_words_before_they_were_masked(probe):
    """`02.5-capability` matches a hook's command to its script and counts a description's bytes, and `02.6-builder` adds the
    tokens and sets a hook against `02.5-capability`'s bytes. Each has the words when it reads them."""
    text = S.FILES["skills/block/SKILL.md"].split("description: |\n")[1].split("license")[0]
    words = "".join(line[2:] + "\n" for line in text.splitlines())
    inj = rows(probe, "02.5-capability", "cap.injection")
    block = next(i for i in inj if i["file"] == "skills/block/SKILL.md")
    assert block["bytes"] == len(words.encode("utf-8"))
    hook = [i for i in inj if i["file"] == "hooks/hooks.json" and i["event"] == "UserPromptSubmit"]
    assert len(hook) == 1 and hook[0]["bytes"] is not None and hook[0]["basis"] == "estimate"  # it found the script in the command
    assert hook[0]["command"].startswith("[line not shown") and hook[0]["masked"]
    fit = [h for h in rows(probe, "02.6-builder", "fit.hook") if h["file"] == "hooks/hooks.json" and h["event"] == "UserPromptSubmit"]
    assert [h["bytes"] for h in fit] == [hook[0]["bytes"]]  # matched by the command as it stood
    entries = {e["file"]: e for e in rows(probe, "02.6-builder", "trig.entry")}
    assert entries["SKILL.md"]["description_chars"] > 40  # the description, and not the mask's length or none
    need = {n["command"] for n in rows(probe, "02.6-builder", "need.command")}
    assert "curl" in need and "bash" in need
    session = next(c for c in rows(probe, "02.6-builder", "cap.context") if c["tier"] == "session")
    assert session["bytes"] > 0


def test_a_copy_of_a_masked_word_follows_it(probe):
    for name in ("02.5-capability", "capability"):
        doc = json.loads((probe / "data" / f"{name}.json").read_text(encoding="utf-8"))
        posture = next(f for f in doc["findings"] if f["check"] == "cap.posture" and f["file"] == "agents/a.md")
        assert posture["description"].startswith("[line not shown") and posture["masked"]
    grants = rows(probe, "02.5-capability", "cap.grant")
    whys = [e["why"] for g in grants for e in g["evidence"] if e.get("check") == "struct.hooks"]
    assert "hook event: SessionStart" in whys  # a plain event is kept wherever it is said


def test_the_graph_keeps_its_shape_and_no_key(probe):
    graph = json.loads((probe / "data" / "graph.json").read_text(encoding="utf-8"))
    assert graph["edges"] and all(S.needle("dynamic_glob") not in str(e.get("text")).lower() for e in graph["edges"])
    dyn = rows(probe, "02.3-graph", "graph.dynamic")
    assert any(d.get("masked") and d["pattern"].startswith("[line not shown") for d in dyn)


def test_a_host_named_only_on_flagged_lines_goes_and_a_host_also_named_elsewhere_stays(probe):
    hosts = {h["host"]: h for h in rows(probe, "02.4-phrases", "endpoint.host")}
    shared = hosts["shared.example.com"]
    urls = [o["urls"] for o in shared["occurrences"]]
    assert ["https://shared.example.com/b"] in urls and any(u[0].startswith("[line not shown") for u in urls)
    assert not any(S.needle("url_host") in h.lower() for h in hosts)
    assert any(h.startswith("[line not shown") for h in hosts)
    hits = json.loads((probe / "data" / "hits.json").read_text(encoding="utf-8"))
    assert S.needle("url_query") not in json.dumps(hits).lower()


def test_the_saved_outputs_read_as_reports_and_the_check_of_the_run_found_nothing_short(probe):
    gaps = rows(probe, "05-qa", "qa.gap")
    assert gaps == []


def test_the_side_file_of_the_capability_step_is_masked_with_the_reports(run_dir):
    """`capability.json` holds the same findings with every citation, and the pages read it beside the reports."""
    spec = importlib.util.spec_from_file_location("walkdown_report_run_for_fields", Path(__file__).resolve().parents[1] / "run.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    key, data = S.key("desc_one"), run_dir / "data"
    for step, row in (("02.1-inventory", {"check": "struct.agent-tools", "file": "SKILL.md", "line": 3, "span": [3, 3], "tools": ["Read"],
                                          "description": f"job {key}"}),
                      ("02.4-phrases", {"check": "secret.found", "file": "SKILL.md", "line": 3, "kinds": ["Anthropic API Key"]})):
        doc = json.loads((data / f"{step}.json").read_text(encoding="utf-8"))
        doc["findings"].append(row)
        (data / f"{step}.json").write_text(json.dumps(doc), encoding="utf-8")
    side = {"findings": [{"check": "cap.posture", "file": "SKILL.md", "line": 3, "description": f"job {key}", "evidence": []}]}
    mod.load(run_dir, None, side)
    assert key not in json.dumps(side) and side["findings"][0]["masked"]


def test_a_run_saved_before_the_mask_is_masked_when_drawn_and_its_data_is_left_alone(run_dir, run_main):
    """A run made before these fields were masked has no `span`, and its saved outputs hold the words: the report masks them in
    memory, by a flagged line anywhere in the file, and a re-render writes no step output."""
    from qa_support import check_run
    data = run_dir / "data"
    key = S.key("desc_one")

    def add(step, *found):
        doc = json.loads((data / f"{step}.json").read_text(encoding="utf-8"))
        doc["findings"] += list(found)
        (data / f"{step}.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")

    add("02.1-inventory",
        {"check": "struct.description", "file": "SKILL.md", "line": 3, "text": f"words {key}", "loader": "yaml"},
        {"check": "struct.hooks", "file": "hooks.json", "line": None, "event": "Stop", "matcher": None, "command": f"run {key}",
         "commands": [f"run {key}"], "types": ["command"], "format": "nested"},
        {"check": "struct.agent-tools", "file": "SKILL.md", "line": None, "tools": [f"Bash({key})"], "description": f"job {key}",
         "field": "tools", "kind": "agent"})
    add("02.3-graph", {"check": "graph.dangling", "file": "SKILL.md", "line": 2, "target": f"x/{key}.md", "context": "prose",
                       "form": "prose", "folder_missing": True})
    add("02.4-phrases",
        {"check": "secret.found", "file": "SKILL.md", "line": 2, "kinds": ["Anthropic API Key"], "engine": "walkdown", "audience": "model"},
        {"check": "secret.found", "file": "hooks.json", "line": 3, "kinds": ["Anthropic API Key"], "engine": "walkdown", "audience": "tool"})
    add("02.5-capability", {"check": "cap.posture", "file": "SKILL.md", "line": None, "tools": [f"Bash({key})"], "posture": ["execute"],
                            "least_privilege": False, "description": f"job {key}", "evidence": []})
    full = json.loads((data / "capability.json").read_text(encoding="utf-8"))
    full["findings"].append({"check": "cap.posture", "file": "SKILL.md", "line": None, "tools": [f"Bash({key})"], "posture": ["execute"],
                             "least_privilege": False, "description": f"job {key}", "evidence": []})
    (data / "capability.json").write_text(json.dumps(full, ensure_ascii=False), encoding="utf-8")
    check_run(run_dir)
    saved = {p.name: p.read_bytes() for p in data.glob("*.json")}
    assert run_main([str(run_dir)]) == 0
    assert {p.name: p.read_bytes() for p in data.glob("*.json")} == saved
    for name in ("summary.html", "details.html", "review.html", "full.md", "brief.md", "LOG.md"):
        assert key not in (run_dir / name).read_text(encoding="utf-8"), name
