"""Tests for run.py and earlier.py, written from specs/builder.SPEC.md ("run.py").

The runner reads the earlier steps' outputs. Most tests give it a saved folder of them (made once
by running the real steps on a small tree); one runs it with no folder, as the grader does."""
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import earlier
import earlier_steps

STAGE = Path(__file__).resolve().parents[1]
RUN = STAGE / "run.py"
STAGES_ROOT = STAGE.parents[1]

FILES = {
    "SKILL.md": ("---\nname: tidy\ndescription: Tidy notes. Use when notes pile up.\nallowed-tools: Bash, WebFetch\n---\n"
                 "Run `jq . a.json` and keep going until it works.\nSaved at C:\\Users\\jesse\\work\\plan.md\n"
                 "TODO: finish this\n"),
    "scripts/run.sh": "#!/bin/sh\njq . a.json\n",
    "hooks/hooks.json": json.dumps({"hooks": {"SessionStart": [{"hooks": [{"type": "command",
                                                                         "command": "sh hooks/start.sh"}]}]}}),
    "hooks/start.sh": "#!/bin/sh\ncat notes.md\n",
    "notes.md": "Some notes.\n",
    "tests/fixture/hooks.json": json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command",
                                                                          "command": "echo hi"}]}]}}),
    "README.md": "# Tidy\n",
}
# the checks `02.4-phrases` used to emit, as they come first in this step's report
UP_FRONT = ("need.", "port.", "host.", "trig.", "ask.", "fit.loop", "clean.")


def make(root, files=FILES):
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return root


def run(*args):
    p = subprocess.run([sys.executable, str(RUN), *map(str, args)], capture_output=True)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8")


def report(*args):
    code, out, err = run(*args)
    assert code == 0, err
    return json.loads(out), err


def tree_hash(root):
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


@pytest.fixture(scope="module")
def saved(tmp_path_factory):
    """The small tree, and a folder of the earlier steps' saved outputs for it."""
    base = tmp_path_factory.mktemp("builder")
    inp = make(base / "in")
    work = base / "saved"
    work.mkdir()
    earlier_steps.run_before("02.6-builder", inp, work, sys.executable, STAGES_ROOT)
    return inp, work


def test_report_shape_and_order(saved):
    inp, work = saved
    doc, err = report(inp, "--reports", work)
    assert doc["stage"] == "02.6-builder" and doc["contract"] == 1
    checks = [f["check"] for f in doc["findings"]]
    for f in doc["findings"]:
        for k in ("check", "file", "line"):
            assert k in f, (k, f)
    # `02.4-phrases`'s builder questions first (needs, hosts, trigger, asks, clean), then `02.5-capability`'s
    # (fit, then what ships, then what it costs)
    first_fit = next(i for i, c in enumerate(checks) if c.startswith("fit.") and c != "fit.loop")
    assert all(c.startswith(UP_FRONT) for c in checks[:first_fit])
    tail = checks[first_fit:]
    order = ["fit.unused", "fit.missing", "fit.inherits", "fit.checked", "fit.hook", "cap.ship", "cap.context"]
    assert tail == sorted(tail, key=order.index) and {"fit.checked", "cap.ship", "cap.context"} <= set(tail)
    # and in the order `02.4-phrases` asked them: needs, ports, hosts, triggers, asks, clean
    rank = {"need": 0, "port": 1, "host": 2, "trig": 3, "ask": 4, "fit": 4, "clean": 5}
    up = [rank[c.split(".")[0]] for c in checks[:first_fit]]
    assert up == sorted(up) and [c for c in checks if c == "trig.listing"] == ["trig.listing"]
    assert "clean.checked" in checks
    assert "builder checks" in err and "verdict" in err
    # as `02.5-capability` wrote its rows: no evidence, counted (a move changes no finding)
    for f in doc["findings"]:
        if f["check"].startswith(("fit.", "cap.")) and f["check"] != "fit.loop":
            assert f["evidence"] == [] and f["evidence_total"] == 0, f
        else:
            assert "evidence" not in f and "evidence_total" not in f, f


def test_zero_findings(tmp_path):
    """The facts every run states: a row per host, the listing, and that clean and fit ran."""
    inp = make(tmp_path / "in", {"a.md": "nothing here\n"})
    doc, _ = report(inp)
    facts = ("host.coverage", "trig.listing", "clean.checked", "fit.checked")
    stated = [f for f in doc["findings"] if f["check"] in facts]
    assert [f["check"] for f in doc["findings"] if f["check"] not in ("cap.ship", "cap.context")] == \
        [f["check"] for f in stated]
    cov = [f for f in stated if f["check"] == "host.coverage"]
    assert {f["host"] for f in cov} == {"claude", "codex", "gemini", "cursor", "copilot", "windsurf", "agents-md"}
    assert all(not f["instructions"] and f["skills"] == 0 for f in cov)
    [lst] = [f for f in stated if f["check"] == "trig.listing"]
    assert lst["skills"] == lst["agents"] == lst["listing_chars"] == 0
    assert [f["check"] for f in doc["findings"] if f["check"].startswith("cap.")] == ["cap.ship", "cap.context"]


def test_what_each_check_finds_on_the_small_tree(saved):
    inp, work = saved
    doc, _ = report(inp, "--reports", work)
    f = doc["findings"]
    by = lambda c: [x for x in f if x["check"] == c]  # noqa: E731
    assert [x["command"] for x in by("need.command")] == ["jq", "sh"]
    assert [(x["file"], x["line"]) for x in by("port.path")] == [("SKILL.md", 7)]
    assert [x["host"] for x in by("host.coverage")][:2] == ["claude", "codex"]
    assert [x["kind"] for x in by("trig.entry")] == ["skill"]
    assert [x["family"] for x in by("ask.tools")] == ["shell"] and by("fit.loop")[0]["line"] == 6
    assert [x["kind"] for x in by("clean.unfinished")] == ["todo"]
    assert [x["tool"] for x in by("fit.unused")] == ["WebFetch"]  # Bash is asked for; WebFetch is not
    groups = {x["file"]: x["group"] for x in by("cap.ship")}
    assert groups["SKILL.md"] == "entry" and groups["hooks/start.sh"] == "run" and groups["notes.md"] == "unused"


def test_test_data_is_left_out_of_fit_but_shipped_as_build_material(saved):
    """`02.5-capability` gave fit its reports with test data set aside, and cost all of them; so does this step."""
    inp, work = saved
    doc, _ = report(inp, "--reports", work)
    hooks = [x for x in doc["findings"] if x["check"] == "fit.hook"]
    assert [h["file"] for h in hooks] == ["hooks/hooks.json"]  # tests/fixture/hooks.json is not one
    groups = {x["file"]: x["group"] for x in doc["findings"] if x["check"] == "cap.ship"}
    assert groups["tests/fixture/hooks.json"] == "build"


def test_a_test_data_file_a_model_reads_stays_in(saved, tmp_path):
    """`02.5-capability`'s `testdata+loaded` pair names a test-data file the model is pointed at: it is not
    set aside, so a hook config there is a hook for fit."""
    inp, work = saved
    d = tmp_path / "saved2"
    shutil.copytree(work, d)
    cap = json.loads((d / "02.5-capability.json").read_text("utf-8"))
    cap["findings"].append({"check": "cap.pair", "file": "tests/fixture/hooks.json", "line": None,
                            "pair": "testdata+loaded", "from": "SKILL.md", "evidence": []})
    (d / "02.5-capability.json").write_text(json.dumps(cap), "utf-8")
    doc, _ = report(inp, "--reports", d)
    assert sorted(h["file"] for h in doc["findings"] if h["check"] == "fit.hook") == [
        "hooks/hooks.json", "tests/fixture/hooks.json"]


def test_a_secret_on_a_quoted_line_masks_the_quote(saved, tmp_path):
    """A report never repeats a secret it found: `02.4-phrases` says where, and a quote of that line here
    (a personal path, a loop, a TODO) is masked the same way."""
    inp, work = saved
    d = tmp_path / "saved3"
    shutil.copytree(work, d)
    ph = json.loads((d / "02.4-phrases.json").read_text("utf-8"))
    ph["findings"] += [{"check": "secret.found", "file": "SKILL.md", "line": 7, "kinds": ["Secret Keyword"],
                        "engine": "detect-secrets", "audience": "model"},
                       {"check": "secret.found", "file": "SKILL.md", "line": 8, "kinds": ["Hex High Entropy String"],
                        "likely_not_secret": "base64 that decodes to readable text, not a key"}]
    (d / "02.4-phrases.json").write_text(json.dumps(ph), "utf-8")
    doc, _ = report(inp, "--reports", d)
    [path] = [x for x in doc["findings"] if x["check"] == "port.path"]
    assert path["masked"] is True and path["quote"].startswith("[line not shown") and path["line"] == 7
    assert "jesse" not in json.dumps(doc)
    [todo] = [x for x in doc["findings"] if x["check"] == "clean.unfinished"]
    assert "masked" not in todo and todo["quote"] == "TODO: finish this"  # a readable-text hit masks nothing
    [loop] = [x for x in doc["findings"] if x["check"] == "fit.loop"]
    assert "masked" not in loop


SECRET_FRONT = "sk-ant-api03-AAAABBBBCCCCDDDDEEEEFFFFGGGGHHHHIIII"


def test_a_frontmatter_value_on_a_flagged_line_is_masked_and_the_checks_read_it_first(tmp_path):
    """A name, a key, a value, and a tool come from the frontmatter a parser read, on one line or many, and `fit` reads the
    tools a grant names, so the mask comes after it. `span` keeps a list that runs below its key."""
    files = {"SKILL.md": (f"---\nname: {SECRET_FRONT}\ndescription: Tidy notes. Use when notes pile up.\nmodel: {SECRET_FRONT}\n"
                          f"{SECRET_FRONT}: x\nallowed-tools:\n  - Read\n  - Bash(curl {SECRET_FRONT})\n---\n"
                          f"Use the model claude-3-opus-{SECRET_FRONT} here.\n")}
    inp = make(tmp_path / "in", files)
    work = tmp_path / "work"
    work.mkdir()
    earlier_steps.run_before("02.6-builder", inp, work)
    doc, _ = report(inp, "--reports", work)
    assert SECRET_FRONT not in json.dumps(doc)
    by = {}
    for f in doc["findings"]:
        by.setdefault(f["check"], []).append(f)
    [entry] = by["trig.entry"]
    assert entry["masked"] and entry["span"] == [1, 9] and entry["name"].startswith("[line not shown")
    assert entry["grants"][0] == "Read" and entry["grants"][1].startswith("[line not shown")
    assert entry["description_chars"] == len("Tidy notes. Use when notes pile up.")  # the count stays
    assert by["trig.key"][0]["key"].startswith("[line not shown") and by["trig.value"][0]["value"].startswith("[line not shown")
    assert by["clean.model"][0]["model"].startswith("[line not shown")
    [unused] = by["fit.unused"]  # it read the tools before they were masked
    assert unused["family"] == "shell" and unused["tool"].startswith("[line not shown") and unused["masked"]


def test_a_key_in_no_frontmatter_leaves_the_entry_as_it_was(tmp_path):
    files = {"skills/tidy/SKILL.md": f"# Tidy\n\nKeep {SECRET_FRONT} safe.\n"}
    inp = make(tmp_path / "in", files)
    work = tmp_path / "work"
    work.mkdir()
    earlier_steps.run_before("02.6-builder", inp, work)
    doc, _ = report(inp, "--reports", work)
    [entry] = [f for f in doc["findings"] if f["check"] == "trig.entry"]
    assert entry["name"] == "tidy" and entry["span"] is None and "masked" not in entry


def test_the_saved_folder_and_a_fresh_run_agree(saved):
    inp, work = saved
    a, _ = report(inp, "--reports", work)
    b, _ = report(inp)
    assert a == b


def test_without_a_graph_nothing_that_needs_edges(saved, tmp_path):
    inp, work = saved
    d = tmp_path / "saved4"
    shutil.copytree(work, d)
    (d / "graph.json").unlink()
    doc, err = report(inp, "--reports", d)
    assert not [f for f in doc["findings"] if f["check"].startswith("cap.")]
    assert "no graph.json" in err and any(f["check"] == "need.command" for f in doc["findings"])


def test_bad_inputs_and_a_read_only_run(saved, tmp_path):
    inp, work = saved
    code, out, _ = run(tmp_path / "missing", "--reports", work)
    assert code == 2 and out == ""
    for name in ("02.1-inventory.json", "02.4-phrases.json", "02.5-capability.json"):
        d = tmp_path / ("no-" + name)
        shutil.copytree(work, d)
        (d / name).unlink()
        code, out, err = run(inp, "--reports", d)
        assert code == 2 and out == "" and name.split(".json")[0] in err
    d = tmp_path / "wrong"
    shutil.copytree(work, d)
    doc = json.loads((d / "02.4-phrases.json").read_text("utf-8"))
    (d / "02.4-phrases.json").write_text(json.dumps(dict(doc, stage="02.5-capability")), "utf-8")
    assert run(inp, "--reports", d)[0] == 2
    before = tree_hash(inp)
    run(inp, "--reports", work)
    assert tree_hash(inp) == before


def walk_keys(x):
    if isinstance(x, dict):
        for k, v in x.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk_keys(v)


def test_no_verdict_fields(saved):
    inp, work = saved
    doc, _ = report(inp, "--reports", work)
    assert not set(walk_keys(doc)) & {"risk", "severity", "score", "verdict"}


def test_earlier_reads_the_four_things(saved):
    inp, work = saved
    up = earlier.load_dir(work)
    assert up.inventory["stage"] == "02.1-inventory" and up.graph["edges"] is not None
    assert {f["check"] for f in up.capability} >= {"cap.leg", "cap.injection"}
    assert all(f["check"] == "secret.found" for f in up.secrets)
    with pytest.raises(earlier.ReportError):
        earlier.load_dir(work / "nowhere")
    assert earlier.READS == ("02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases",
                             "02.5-capability")  # from stages.json
    assert {earlier.INVENTORY, earlier.PHRASES, earlier.CAPABILITY} <= set(earlier.READS)
