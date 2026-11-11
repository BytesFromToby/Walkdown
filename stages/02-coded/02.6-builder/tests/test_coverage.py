"""Tests for the coverage lines of run.py (M9 slice C), written from specs/builder.SPEC.md, run: "What the step looked at"."""
import importlib.util
import json
import sys
from pathlib import Path

CODED = Path(__file__).resolve().parents[2]
STAGES = CODED.parent
sys.path.insert(0, str(STAGES / "_shared"))

import coverlines  # noqa: E402
import stagelist  # noqa: E402

STAGE = "02.6-builder"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FILES = {
    "skills/s/SKILL.md": "---\nname: s\ndescription: Use when you need to read notes. A skill that reads notes.\n"
                         "allowed-tools: Read, Bash\n---\nRun `git status` and read the notes. TODO: write more.\n"
                         "Do this until it works, without a limit.\n",
    "agents/a.md": "---\nname: a\ndescription: Use when notes need reading.\ntools: Read\n---\nAn agent that writes files.\n",
    "AGENTS.md": "Use the Bash tool.\n",
    "hooks/hooks.json": json.dumps({"hooks": {"SessionStart": [
        {"matcher": "startup", "hooks": [{"type": "command", "command": "hooks/run.sh"}]}]}}),
    "hooks/run.sh": "#!/usr/bin/env bash\ngit status\n",
    "README.md": "Notes for people.\n",
    "src/app.js": "const x = require('left-pad');\n",
    "tests/test_a.py": "print('hi')\n",
}


def folder(root):
    for rel, text in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return root


def earlier_for(root, monkeypatch, graph=True):
    """The earlier steps' output the builder reads, made in this process."""
    inv = load("walkdown_s06_cov_inv", CODED / "02.1-inventory" / "run.py").build_report(root)
    reader = load("walkdown_s06_cov_reader", CODED / "02.2-reader" / "run.py")
    rd = reader.build_report(root)  # the same on every machine: no installed program changes it (R35, R36)
    gr, g = load("walkdown_s06_cov_graph", CODED / "02.3-graph" / "run.py").build_report(root, inv)
    ph_mod = load("walkdown_s06_cov_phrases", CODED / "02.4-phrases" / "run.py")
    monkeypatch.setattr(ph_mod.secret_scan, "_detect_secrets", lambda root_, rels, skips=None: [])
    ph, _ = ph_mod.build_report(root, inv, ph_mod.load_table(None))
    cap = load("walkdown_s06_cov_cap", CODED / "02.5-capability" / "run.py").derive(
        {"02.1-inventory": inv, "02.2-reader": rd, "02.3-graph": gr, "02.4-phrases": ph}, g)
    return inv, (g if graph else None), cap, [f for f in ph["findings"] if f.get("check") == "secret.found"]


def build(root, monkeypatch, patch=None, graph=True):
    mod = load("walkdown_s06_cov_run", CODED / "02.6-builder" / "run.py")
    inv, g, cap, secrets = earlier_for(root, monkeypatch, graph)
    if patch:
        patch(mod)
    findings = mod.build(root, mod.earlier.Earlier(inv, g, cap, secrets))
    return {"stage": STAGE, "contract": 1, "findings": findings, "coverage": mod.cov.lines(findings)}


def line_for(report, check):
    return next(x for x in report["coverage"] if check in x["checks"])


def short(report, check, of, looked_at, explained=0):
    """The check's line has the counts given, and they do not add up."""
    line = line_for(report, check)
    assert (line["of"], line["looked_at"], line["explained"]) == (of, looked_at, explained), line
    assert any(line["checks"][0] in p and f"not of {of}" in p for p in coverlines.problems(stagelist.checks(STAGE), report))


def whole(report, check):
    line = line_for(report, check)
    assert line["looked_at"] + line["explained"] == line["of"], line


def test_every_check_has_a_line_and_the_counts_add_up(tmp_path, monkeypatch):
    report = build(folder(tmp_path), monkeypatch)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []
    units = {x["checks"][0]: (x["unit"], x["of"], x["looked_at"], x["explained"]) for x in report["coverage"]}
    # eight files: the test file is test data, so seven are the ones the checks read
    # each check's line counts the files it reads: the README is for people, so no check of the programs or the paths reads it
    assert units["need.command"] == ("files", 5, 5, 0)  # the scripts and the Markdown a model reads
    assert units["need.package"] == ("files", 1, 1, 0)  # the one JavaScript file
    assert units["port.path"] == ("files", 6, 6, 0)  # every file but the README
    assert units["port.backslash"] == ("files", 3, 3, 0)  # the skill, the agent, and AGENTS.md
    assert units["port.os"] == ("files", 1, 1, 0) and units["port.crlf"] == ("files", 1, 1, 0)  # the shell script
    # of the three uses (a program in the skill, one in the script, the hook's command) only the hook's runs a script by its path,
    # and none calls Python by its name: a command inside a script is read by neither check
    assert units["port.exec"] == ("uses", 1, 1, 0) and units["port.python"] == ("uses", 0, 0, 0)
    assert units["host.drift"] == ("files", 1, 1, 0)  # AGENTS.md is the one copy kept for a host
    assert units["host.feature"] == ("files", 3, 3, 0)  # SKILL.md and AGENTS.md, and the hook file
    assert units["trig.entry"] == ("entries", 2, 2, 0) and units["trig.overlap"] == ("entries", 2, 2, 0)
    assert units["clean.unfinished"] == ("files", 6, 6, 0)  # every file but the README (for people) and the test data
    assert units["clean.dated"] == ("files", 3, 3, 0)  # Markdown the AI reads
    assert units["trig.listing"] == ("run", 1, 1, 0)
    assert units["ask.tools"] == ("files", 3, 3, 0)  # the AI reads SKILL.md, the agent, and AGENTS.md
    assert units["clean.checked"] == ("run", 1, 1, 0) and units["fit.checked"] == ("run", 1, 1, 0)
    assert units["fit.unused"] == ("entries", 2, 2, 0) and units["fit.hook"] == ("entries", 1, 1, 0)
    assert units["cap.ship"] == ("files", 8, 8, 0)  # every file ships somewhere, test data included
    assert units["cap.context"] == ("entries", 4, 4, 0)  # the session, the project, and the two entries
    host = line_for(report, "host.coverage")
    assert host["unit"] == "entries" and host["of"] == host["looked_at"] >= 3
    assert line_for(report, "fit.checked")["found"] == 1 and line_for(report, "fit.hook")["found"] == 1


def test_no_check_is_named_by_two_lines_and_the_passes_that_differ_are_lines_of_their_own():
    """A line that mixes items counted in different units or by different passes hides a check that stops working while its
    siblings run, so each pass over one kind of item is its own line."""
    mod = load("walkdown_s06_cov_lines", CODED / "02.6-builder" / "run.py")
    named = [c for checks, _ in mod.LINES for c in checks]
    assert len(named) == len(set(named)) and set(named) == set(stagelist.checks(STAGE))
    alone = {checks[0] for checks, _ in mod.LINES if len(checks) == 1}
    assert {"need.command", "need.package", "host.drift", "host.feature", "trig.overlap", "trig.listing", "clean.checked",
            "fit.checked", "fit.hook", "cap.ship", "cap.context"} <= alone


def test_without_the_graph_what_ships_and_costs_is_explained_by_the_standing_note(tmp_path, monkeypatch):
    """No `graph.json`: `cap.ship` and `cap.context` are not reported, and the note the step writes says so. The items are
    explained, and the other lines are as they were."""
    report = build(folder(tmp_path), monkeypatch, graph=False)
    ship = line_for(report, "cap.ship")
    assert (ship["of"], ship["looked_at"], ship["explained"], ship["found"]) == (8, 0, 8, 0)
    context = line_for(report, "cap.context")
    assert (context["of"], context["looked_at"], context["explained"], context["found"]) == (4, 0, 4, 0)
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_an_entry_whose_frontmatter_is_not_read_is_explained_by_its_row(tmp_path, monkeypatch):
    """The entry row says `its frontmatter is not read`: the rules, keys, values, and tools did not run on it, so it is
    explained and not looked at."""
    (tmp_path / "skills" / "u").mkdir(parents=True)
    (tmp_path / "skills" / "u" / "SKILL.md").write_bytes(b"---\nname: [\n---\nBody.\n")
    report = build(tmp_path, monkeypatch)
    trig = line_for(report, "trig.entry")
    assert (trig["of"], trig["looked_at"], trig["explained"]) == (1, 0, 1)
    assert [f for f in report["findings"] if f["check"] == "trig.entry" and f["mode"] == "unread"]
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def _skipping(monkeypatch, module, name):
    def patch(mod):
        monkeypatch.setattr(getattr(mod, module), name, lambda *a, **k: [])  # the check is not run, finds nothing, says nothing
    return patch


def _after_the_count(real, drop):
    """A function that gives the whole list the first time (the step counts what the check is to look at) and the list without
    `drop` after that (the check's own loop leaves one out and says nothing)."""
    calls = []

    def inner(*a, **k):
        got = real(*a, **k)
        calls.append(1)
        return got if len(calls) == 1 else [x for x in got if x != drop]
    return inner


def test_a_file_the_needs_check_leaves_out_shows_as_a_shortfall_on_each_line_that_reads_it(tmp_path, monkeypatch):
    """The `is_test_data` of `needs` is the loops' own: the step counts its files with another, so a file set aside in the loop
    alone is one the check did not look at and said nothing about. The shell script is read by the programs, the paths, the OS
    and the line-end checks, and each line is short by that one file."""
    def patch(mod):
        real = mod.needs.is_test_data
        monkeypatch.setattr(mod.needs, "is_test_data", lambda rel: rel == "hooks/run.sh" or real(rel))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "need.command", 5, 4)
    short(report, "port.path", 6, 5)
    short(report, "port.os", 1, 0)
    short(report, "port.crlf", 1, 0)
    whole(report, "port.backslash")  # a shell script has no backslash paths to read
    whole(report, "need.package")  # and no imports
    whole(report, "ask.tools")


def test_a_markdown_file_the_backslash_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.needs.is_test_data
        monkeypatch.setattr(mod.needs, "is_test_data", lambda rel: rel == "AGENTS.md" or real(rel))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "port.backslash", 3, 2)
    short(report, "port.path", 6, 5)
    short(report, "need.command", 5, 4)


def test_a_file_for_people_is_no_item_of_the_programs_or_the_paths(tmp_path, monkeypatch):
    """The README is text the step reads and these checks do not (`needs.programs_scope`, `needs.paths_scope`): it holds a
    personal path and a command, and neither the lines nor the findings count it."""
    folder(tmp_path)
    (tmp_path / "README.md").write_text("Run `git status` in /home/someone/work/repo.\n", encoding="utf-8")
    report = build(tmp_path, monkeypatch)
    assert line_for(report, "need.command")["of"] == 5 and line_for(report, "port.path")["of"] == 6
    assert not [f for f in report["findings"] if f.get("file") == "README.md" and f["check"] == "port.path"]
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_a_script_the_package_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.needs.is_test_data
        monkeypatch.setattr(mod.needs, "is_test_data", lambda rel: rel == "src/app.js" or real(rel))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "need.package", 1, 0)
    short(report, "need.command", 5, 4)


def test_a_use_the_port_checks_leave_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.needs.port_of_use
        monkeypatch.setattr(mod.needs, "port_of_use", lambda u, rows, texts: [] if u["how"] == "hook" else real(u, rows, texts))
    report = build(folder(tmp_path), monkeypatch, patch)  # the hook's command is passed over, uncounted
    short(report, "port.exec", 1, 0)
    whole(report, "port.path")


def test_python_called_by_its_name_is_its_own_line_and_a_use_in_a_script_is_in_neither(tmp_path, monkeypatch):
    folder(tmp_path)
    (tmp_path / "AGENTS.md").write_text("Use the Bash tool. Run `python tools/x.py` first.\n", encoding="utf-8")
    report = build(tmp_path, monkeypatch)
    assert line_for(report, "port.python")["of"] == 1 and line_for(report, "port.exec")["of"] == 1  # the hook, and the instruction
    assert [f["check"] for f in report["findings"] if f["check"] == "port.python"] == ["port.python"]
    assert coverlines.problems(stagelist.checks(STAGE), report) == []

    def patch(mod):
        real = mod.needs.port_of_use
        monkeypatch.setattr(mod.needs, "port_of_use", lambda u, rows, texts: [] if u["program"] == "python" else real(u, rows, texts))
    report = build(tmp_path, monkeypatch, patch)
    short(report, "port.python", 1, 0)


def test_an_instruction_copy_the_drift_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        monkeypatch.setattr(mod.hosts, "copy_files", _after_the_count(mod.hosts.copy_files, "AGENTS.md"))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "host.drift", 1, 0)
    whole(report, "host.feature")


def test_a_file_the_host_words_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        monkeypatch.setattr(mod.hosts, "feature_texts", _after_the_count(mod.hosts.feature_texts, "skills/s/SKILL.md"))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "host.feature", 3, 2)
    whole(report, "host.drift")


def test_hosts_the_hosts_check_leaves_out_show_as_a_shortfall(tmp_path, monkeypatch):
    report = build(folder(tmp_path), monkeypatch, _skipping(monkeypatch, "hosts", "findings"))
    assert line_for(report, "host.coverage")["looked_at"] == 0 and line_for(report, "host.coverage")["of"] >= 3
    short(report, "host.feature", 3, 0)
    short(report, "host.drift", 1, 0)


def test_an_entry_the_trigger_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.trigger.is_test_data
        monkeypatch.setattr(mod.trigger, "is_test_data", lambda rel: rel == "agents/a.md" or real(rel))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "trig.entry", 2, 1)


def test_an_entry_the_overlap_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.trigger.overlaps
        monkeypatch.setattr(mod.trigger, "overlaps", lambda entries: real(entries[:-1]))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "trig.overlap", 2, 1)
    whole(report, "trig.entry")


def test_the_listing_row_the_trigger_check_does_not_write_shows_as_a_shortfall(tmp_path, monkeypatch):
    report = build(folder(tmp_path), monkeypatch, _skipping(monkeypatch, "trigger", "findings"))
    short(report, "trig.listing", 1, 0)
    short(report, "trig.entry", 2, 0)


def test_a_file_the_asks_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.asks.audience
        monkeypatch.setattr(mod.asks, "audience", lambda rel, *a: "human" if rel == "AGENTS.md" else real(rel, *a))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "ask.tools", 3, 2)
    whole(report, "clean.unfinished")


def test_a_file_the_clean_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.clean.audience
        monkeypatch.setattr(mod.clean, "audience", lambda rel, *a: "human" if rel == "AGENTS.md" else real(rel, *a))
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "clean.unfinished", 6, 5)
    short(report, "clean.dated", 3, 2)  # Markdown the AI reads: AGENTS.md is one
    whole(report, "clean.checked")


def test_the_row_the_clean_check_does_not_write_shows_as_a_shortfall(tmp_path, monkeypatch):
    report = build(folder(tmp_path), monkeypatch, _skipping(monkeypatch, "clean", "findings"))
    short(report, "clean.checked", 1, 0)
    short(report, "clean.model", 6, 0)


def test_an_entry_the_fit_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.fit._built

        def inner(reports, check):
            got = real(reports, check)
            return [e for e in got if e.get("file") != "agents/a.md"] if check == "trig.entry" else got
        monkeypatch.setattr(mod.fit, "_built", inner)
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "fit.unused", 2, 1)
    whole(report, "fit.hook")


def test_the_row_the_fit_check_does_not_write_shows_as_a_shortfall(tmp_path, monkeypatch):
    report = build(folder(tmp_path), monkeypatch, _skipping(monkeypatch, "fit", "entries_fit"))
    short(report, "fit.checked", 1, 0)
    short(report, "fit.unused", 2, 0)
    whole(report, "fit.hook")  # the hook line is whole


def test_a_hook_the_hook_fit_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    report = build(folder(tmp_path), monkeypatch, _skipping(monkeypatch, "fit", "hooks_fit"))
    short(report, "fit.hook", 1, 0)


def test_a_file_the_ship_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.cost.ship

        def inner(reports, graph):
            inv = reports["02.1-inventory"]
            kept = dict(inv, findings=[f for f in inv["findings"] if f.get("file") != "README.md"])
            return real(dict(reports, **{"02.1-inventory": kept}), graph)
        monkeypatch.setattr(mod.cost, "ship", inner)
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "cap.ship", 8, 7)


def test_an_entry_the_context_check_leaves_out_shows_as_a_shortfall(tmp_path, monkeypatch):
    def patch(mod):
        real = mod.cost.context

        def inner(reports, graph, injections, ship_rows):
            return real(reports, graph, injections, [r for r in ship_rows if r["file"] != "agents/a.md"])
        monkeypatch.setattr(mod.cost, "context", inner)
    report = build(folder(tmp_path), monkeypatch, patch)
    short(report, "cap.context", 4, 3)
    whole(report, "cap.ship")


def test_documentation_kept_beside_the_agents_is_no_entry_and_no_item_of_the_trigger_line(tmp_path, monkeypatch):
    """A file in the agents' folder with no frontmatter, or frontmatter with neither a name nor a description, is not an entry
    (`trigger.check_entry` returns none for it): the line of the entry checks does not count it, and is not short for it."""
    folder(tmp_path)
    (tmp_path / "agents" / "README.md").write_text("Notes on the agents kept here. Nothing to load.\n", encoding="utf-8")
    (tmp_path / "agents" / "empty.md").write_text("---\ntools: Read\n---\nNo name, no description.\n", encoding="utf-8")
    report = build(tmp_path, monkeypatch)
    trig = line_for(report, "trig.entry")
    assert (trig["of"], trig["looked_at"], trig["explained"]) == (2, 2, 0)  # the skill and the agent
    assert coverlines.problems(stagelist.checks(STAGE), report) == []


def test_the_scope_of_the_entry_line_is_the_decision_check_entry_makes():
    """`trigger.is_entry` is the count's side of `check_entry`'s early returns: they agree on every kind of file."""
    sys.path.insert(0, str(CODED / "02.6-builder"))
    import trigger as mod
    cases = [("agent", "No frontmatter at all.\n"), ("agent", "---\ntools: Read\n---\nbody\n"),
             ("agent", "---\nname: a\n---\nbody\n"), ("agent", "---\ndescription: d\n---\nbody\n"),
             ("agent", "---\nname: a\ndescription: d\n---\nbody\n"), ("agent", "---\nname: [\n---\nbody\n"),
             ("agent", "\n\n---\nname: a\ndescription: d\n---\nbody\n"), ("skill", "No frontmatter at all.\n"),
             ("skill", "---\nname: s\ndescription: d\n---\nbody\n"), ("command", "No frontmatter at all.\n"),
             ("agent", "---\nname: \"\"\ndescription: \"\"\n---\nbody\n")]
    for kind, text in cases:
        entry, _ = mod.check_entry("agents/x.md", kind, text)
        assert mod.is_entry(kind, text) == (entry is not None), (kind, text)


def test_an_entry_the_trigger_check_skips_below_the_scope_shows_as_a_shortfall_with_the_documentation_apart(tmp_path, monkeypatch):
    folder(tmp_path)
    (tmp_path / "agents" / "README.md").write_text("Notes on the agents kept here.\n", encoding="utf-8")

    def patch(mod):
        real = mod.trigger.check_entry
        monkeypatch.setattr(mod.trigger, "check_entry",
                            lambda rel, kind, text, bom=False: (None, []) if rel == "skills/s/SKILL.md" else real(rel, kind, text, bom))
    report = build(tmp_path, monkeypatch, patch)
    short(report, "trig.entry", 2, 1)


def test_a_real_run_of_the_steps_main_shows_a_file_the_programs_and_paths_checks_leave_out(tmp_path, monkeypatch, capsys):
    """The step's `main` on a folder and the saved outputs of the steps before it (`--reports`), with the loops of the programs and
    the paths given one file fewer than the step counted: the lines it prints are short, as the check of the run reads them."""
    root = tmp_path / "repo"
    root.mkdir()
    folder(root)
    inv, g, cap, secrets = earlier_for(root, monkeypatch)
    saved = tmp_path / "saved"
    saved.mkdir()
    (saved / "02.1-inventory.json").write_text(json.dumps(inv), encoding="utf-8")
    (saved / "02.4-phrases.json").write_text(json.dumps({"stage": "02.4-phrases", "contract": 1, "findings": secrets}), encoding="utf-8")
    (saved / "02.5-capability.json").write_text(json.dumps({"stage": "02.5-capability", "contract": 1, "findings": cap}), encoding="utf-8")
    (saved / "graph.json").write_text(json.dumps(g), encoding="utf-8")
    mod = load("walkdown_s06_cov_main", CODED / "02.6-builder" / "run.py")
    real = mod.needs.is_test_data
    monkeypatch.setattr(mod.needs, "is_test_data", lambda rel: rel == "hooks/run.sh" or real(rel))
    assert mod.main([str(root), "--reports", str(saved)]) == 0
    printed = json.loads(capsys.readouterr().out)
    short(printed, "need.command", 5, 4)
    short(printed, "port.path", 6, 5)
    short(printed, "port.os", 1, 0)
    whole(printed, "ask.tools")
