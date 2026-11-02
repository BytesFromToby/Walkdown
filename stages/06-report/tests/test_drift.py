"""Tests for drift.py, written from specs/report.SPEC.md, drift."""
import json
import os
import time

import drift
import record

SECRET = "ZZREPOTEXTZZ"


def write_record(d, fmt=None, until=None):
    """A record with no times, in the current format (or `fmt`): a run is compared only when its record
    has the current format (restructure step 7b). With no times it is ordered by its log, as a run
    without a record is. `until`: the step a run stopped after (O3)."""
    doc = {"format": record.FORMAT if fmt is None else fmt, "steps": [], "stamps": {}}
    if until:
        doc["until"] = until
    (d / "data" / "run.json").write_text(json.dumps(doc), encoding="utf-8")


def run(tmp, name, s1=(), s4=(), s5=(), pin_hash="aaa", terms=None, s6=()):
    d = tmp / name
    (d / "data").mkdir(parents=True)
    (d / "LOG.md").write_text("log", encoding="utf-8")
    write_record(d)
    docs = {"02.1-inventory": [{"check": "inv.pin", "file": None, "line": None, "hash": pin_hash,
                              "hash_kind": "git", "files": len(s1)}] + list(s1),
            "02.3-graph": [], "02.4-phrases": list(s4), "02.5-capability": list(s5),
            "02.6-builder": list(s6)}
    for stage, f in docs.items():
        doc = {"stage": stage, "contract": 1, "findings": f}
        if stage == "02.4-phrases" and terms is not None:
            doc["terms"] = terms
        (d / "data" / f"{stage}.json").write_text(json.dumps(doc), encoding="utf-8")
    return d


def inv(f, sha, bytes_=10, entry=None):
    return {"check": "inv.file", "file": f, "line": None, "sha256": sha, "bytes": bytes_,
            "entry_point": entry}


OLD1 = [inv("SKILL.md", "a1", entry="skill"), inv("lib.py", "b1"), inv("gone.md", "c1"),
        {"check": "struct.agent-tools", "file": "agents/x.md", "line": None, "tools": ["Read"]}]
NEW1 = [inv("SKILL.md", "a2", entry="skill"), inv("lib.py", "b1"), inv("new.md", "d1"),
        {"check": "struct.agent-tools", "file": "agents/x.md", "line": None, "tools": None},
        {"check": "struct.hooks", "file": "hooks/hooks.json", "line": None, "event": "SessionStart",
         "matcher": None, "command": f"run {SECRET}"},
        {"check": "struct.mcp", "file": ".mcp.json", "line": None, "name": "srv", "command": "x",
         "url": None},
        {"check": "struct.description", "file": "SKILL.md", "line": None, "text": f"now {SECRET}"}]
HIT = {"check": "phrase.K.exfil", "file": "SKILL.md", "line": 4, "quote": f"send it {SECRET}",
       "audience": "model", "patterns": ["K.dns"]}
MOVED_OLD = {"check": "phrase.L.override", "file": "SKILL.md", "line": 9, "quote": "ignore that",
             "audience": "model"}
MOVED_NEW = dict(MOVED_OLD, line=30)
LEG = lambda leg, p: {"check": "cap.leg", "file": None, "line": None, "leg": leg, "present": p,
                      "evidence": []}


FLAGGED = {"check": "secret.found", "file": "SKILL.md", "line": 3, "kinds": ["Anthropic API Key"], "engine": "walkdown", "audience": "model"}
MASK = "[line not shown: it holds what looks like a secret; open the file to see it]"


def test_two_runs_are_each_masked_and_a_description_with_the_same_flagged_line_is_no_change(tmp_path):
    desc = {"check": "struct.description", "file": "SKILL.md", "line": 3, "span": [3, 3], "text": f"one {SECRET}"}
    a = drift.load(run(tmp_path, "a", [desc], [FLAGGED]))
    b = drift.load(run(tmp_path, "b", [dict(desc, text=f"two {SECRET}")], [FLAGGED]))
    assert a["02.1-inventory"][1]["text"] == MASK
    assert drift.compare(a, b)["desc_changed"] == []


def test_a_word_is_not_shown_for_a_file_masked_in_one_run_only(tmp_path):
    """One run's scan can flag what the other's missed (a file it could not read), so the side not masked can hold the key."""
    desc = {"check": "struct.description", "file": "SKILL.md", "line": 3, "span": [3, 3], "text": f"words {SECRET}"}
    hook = {"check": "struct.hooks", "file": "SKILL.md", "line": None, "span": [3, 3], "event": "Stop", "matcher": None,
            "command": f"run {SECRET}"}
    tools = {"check": "struct.agent-tools", "file": "SKILL.md", "line": 3, "span": [3, 3], "tools": [f"Bash({SECRET})"]}
    mcp = {"check": "struct.mcp", "file": "SKILL.md", "line": None, "span": [3, 3], "name": SECRET, "command": SECRET, "url": None}
    seen_then = drift.load(run(tmp_path, "a", [desc, hook, tools, mcp], []))
    flagged_now = drift.load(run(tmp_path, "b", [desc, hook, tools, mcp], [FLAGGED]))
    for c in (drift.compare(seen_then, flagged_now), drift.compare(flagged_now, seen_then)):
        assert SECRET not in repr({k: c[k] for k in ("desc_changed", "hooks_added", "hooks_removed", "grants_changed", "mcp_added",
                                                     "mcp_removed", "mcp_changed")})
        assert c["desc_changed"] == [("SKILL.md", MASK, MASK)] and c["hooks_added"] and c["hooks_removed"]
        assert all(row[0] == "SKILL.md" for row in c["hooks_added"])  # which file it was stays


def test_compare_finds_each_kind_of_change(tmp_path):
    a = drift.load(run(tmp_path, "a", OLD1, [MOVED_OLD], [LEG("external-comms", False)]))
    b = drift.load(run(tmp_path, "b", NEW1, [MOVED_NEW, HIT], [LEG("external-comms", True),
                   {"check": "cap.grant", "file": None, "line": None, "grant": "exec-at-load",
                    "evidence": []}], pin_hash="bbb"))
    c = drift.compare(a, b)
    assert c["files_added"] == ["new.md"] and c["files_removed"] == ["gone.md"]
    assert c["files_changed"] == ["SKILL.md"]  # lib.py has the same hash
    assert c["grants_changed"] == [("agents/x.md", "Read", "inherits all tools")]
    assert len(c["hooks_added"]) == 1 and len(c["mcp_added"]) == 1 and len(c["desc_changed"]) == 1
    assert c["hits_added"] == [HIT] and c["hits_removed"] == []  # a moved line is not new
    assert c["legs_changed"] == [("external-comms", False, True)]
    assert c["capgrants_added"] == ["exec-at-load"]


def test_older_run_without_hashes_is_flagged_not_guessed(tmp_path):
    old = [dict(inv("a.md", None), bytes=5), dict(inv("b.md", None), bytes=5)]
    new = [inv("a.md", "x", bytes_=5), inv("b.md", "y", bytes_=6)]
    c = drift.compare(drift.load(run(tmp_path, "a", old)), drift.load(run(tmp_path, "b", new)))
    assert c["files_changed"] == ["b.md"] and c["files_unverified"] == ["a.md"]


def test_summary_lines_carry_no_repository_text(tmp_path):
    a = drift.load(run(tmp_path, "a", OLD1))
    b = drift.load(run(tmp_path, "b", NEW1, [HIT], pin_hash="bbb"))
    text = "\n".join(drift.summary_lines(drift.compare(a, b)))
    assert SECRET not in text and "1 hook added" in text
    assert drift.summary_lines(drift.compare(a, a)) == ["no differences in what Walkdown records"]


def test_one_new_phrase_hit_says_where_it_is_in_one_part(tmp_path):
    """2026-10-29 (step 8b's verification): one new hit read "1 new phrase hit, 1 of the new phrase
    hits in text a model reads"; it now says where it is beside the count. Two or more keep the share."""
    a = drift.load(run(tmp_path, "a", OLD1))
    one = drift.summary_lines(drift.compare(a, drift.load(run(tmp_path, "b", NEW1, [HIT], pin_hash="bbb"))))
    assert "1 new phrase hit (in text a model reads)" in one[0] and "of the new phrase hits" not in one[0]
    human = dict(HIT, audience="human")
    one = drift.summary_lines(drift.compare(a, drift.load(run(tmp_path, "c", NEW1, [human], pin_hash="ccc"))))
    assert "1 new phrase hit (not in text a model reads)" in one[0]
    two = drift.summary_lines(drift.compare(a, drift.load(
        run(tmp_path, "d", NEW1, [HIT, dict(human, line=8, quote="mail it")], pin_hash="ddd"))))
    assert "2 new phrase hits" in two[0] and "1 of the new phrase hits in text a model reads" in two[0]


def test_report_and_the_one_comparison_with_the_previous_run(tmp_path):
    """Restructure step 7 (notes F2): `changes` is the one comparison; `record.previous_run` finds the
    previous run by time (a run with no record: its LOG.md's time), so a re-rendered older run is never
    compared with a newer one."""
    a = run(tmp_path, "2026-01-01_aaa", OLD1)
    b = run(tmp_path, "2026-01-02_bbb", NEW1, [HIT], pin_hash="bbb")
    os.utime(a / "LOG.md", (1_000_000, 1_000_000))
    os.utime(b / "LOG.md", (2_000_000, 2_000_000))
    assert drift.changes(a) is None  # the first run: nothing to compare
    ch = drift.changes(b)
    assert ch["since"] == a.name and ch["differs"] and not ch["same"] and ch["report"] == b / "changes.md"
    assert ch["lines"] and ch["header"] is None and ch["on_disk"] == 3  # new.md, gone.md, SKILL.md
    md = (b / "changes.md").read_text(encoding="utf-8")
    assert "## Hooks added (1)" in md and "Trifecta" not in md
    out, c = drift.write_report(a, b)
    assert out == b / "changes.md" and out.read_text(encoding="utf-8") == md
    assert drift.main([str(a)]) == 2
    same = run(tmp_path, "2026-01-03_ccc", NEW1, [HIT], pin_hash="bbb")  # the same version of the repository
    os.utime(same / "LOG.md", (3_000_000, 3_000_000))
    ch = drift.changes(same)
    assert ch["since"] == b.name and ch["same"] and not ch["differs"] and ch["report"] is None
    assert drift.changes(b)["since"] == a.name  # the middle run, rendered again: not the later one


def test_the_previous_run_of_two_runs_on_one_day_is_the_earlier_one_whatever_their_hashes(tmp_path):
    """Round 2 of step 7: the name ends with the commit's hash, so two runs on one day sort by hash. Main
    picked by the log's time; so does the rule now (a run with a record: its finish)."""
    yesterday = run(tmp_path, "2026-01-01_ccc", OLD1)
    morning = run(tmp_path, "2026-01-02_bbb", NEW1, [HIT], pin_hash="bbb")
    afternoon = run(tmp_path, "2026-01-02_aaa", NEW1, [HIT], pin_hash="bbb")
    for d, t in ((yesterday, 1_000_000), (morning, 2_000_000), (afternoon, 3_000_000)):
        os.utime(d / "LOG.md", (t, t))
    assert "2026-01-02_aaa" < "2026-01-02_bbb"
    assert drift.changes(afternoon)["since"] == morning.name
    assert drift.changes(morning)["since"] == yesterday.name


def test_an_older_run_rendered_again_later_is_not_compared_with_a_newer_one(tmp_path):
    """Round 3 (R1): a run without a record is ordered by the date in its folder name first, because v0.3.1
    appended to LOG.md when a run was rendered again, which moved the log's time."""
    older = run(tmp_path, "2026-01-10_ddd", OLD1)
    newer = run(tmp_path, "2026-01-20_eee", NEW1, pin_hash="bbb")
    os.utime(older / "LOG.md", (3_000_000, 3_000_000))  # rendered again after the newer run was made
    os.utime(newer / "LOG.md", (2_000_000, 2_000_000))
    assert drift.changes(older) is None
    assert drift.changes(newer)["since"] == older.name


def test_a_comparison_that_fails_is_a_note_and_not_an_error(tmp_path, capsys, monkeypatch):
    a = run(tmp_path, "2026-01-01_aaa", OLD1)
    b = run(tmp_path, "2026-01-02_bbb", NEW1, pin_hash="bbb")
    monkeypatch.setattr(drift, "since", lambda *x: 1 / 0)
    assert drift.changes(b) is None and "note: version drift not computed: division by zero" in capsys.readouterr().err
    assert a.is_dir()


# Review C22 b (2026-10-19): where a new or gone hit came from.

def terms(rows, code="c1", vocab="w1"):
    return {"version": "v-" + "-".join(f"{k}{v}" for k, v in sorted(rows.items())), "count": len(rows),
            "rows": rows, "vocab": vocab, "code": code}


SAME = [inv("SKILL.md", "a1"), inv("lib.md", "b1")]
EDITED = [inv("SKILL.md", "a2"), inv("lib.md", "b1")]


def hit(file, pats, quote):
    return {"check": "phrase.E.env", "file": file, "line": 3, "quote": quote, "audience": "model",
            "patterns": pats}


def test_each_hit_says_where_it_came_from(tmp_path):
    old_t = terms({"E.a": "1", "E.b": "2", "E.gone": "3"})
    new_t = terms({"E.a": "1", "E.b": "9", "E.new": "4"}, code="c2")
    old = [hit("lib.md", ["E.gone"], "retired row"), hit("lib.md", ["E.a"], "matcher now misses")]
    new = [hit("SKILL.md", ["E.a"], "edited file"), hit("lib.md", ["E.new"], "added row"),
           hit("lib.md", ["E.b"], "changed row"), hit("lib.md", ["E.a"], "matcher now finds")]
    c = drift.compare(drift.load(run(tmp_path, "a", SAME, old, terms=old_t)),
                      drift.load(run(tmp_path, "b", EDITED, new, pin_hash="bbb", terms=new_t)))
    added = {h["quote"]: k for h, k in zip(c["hits_added"], c["hits_added_cause"])}
    assert added == {"edited file": "repo", "added row": "terms", "changed row": "terms",
                     "matcher now finds": "code"}
    gone = {h["quote"]: k for h, k in zip(c["hits_removed"], c["hits_removed_cause"])}
    assert gone == {"retired row": "terms", "matcher now misses": "code"}
    lines = drift.summary_lines(c)
    assert ("Walkdown changed since the older run: 3 search terms (1 added, 1 changed, 1 retired), "
            "matching code changed") in lines
    assert ("new phrase hits: 1 from changes in the repository, 2 from Walkdown's search terms, "
            "1 from Walkdown's matching code") in lines
    assert "phrase hits gone: 1 from Walkdown's search terms, 1 from Walkdown's matching code" in lines


def test_without_a_term_version_walkdown_is_named_not_guessed(tmp_path):
    a = drift.load(run(tmp_path, "a", SAME, []))
    b = drift.load(run(tmp_path, "b", SAME, [hit("lib.md", ["E.a"], "new")], terms=terms({"E.a": "1"})))
    c = drift.compare(a, b)
    assert c["terms"]["known"] is False and c["hits_added_cause"] == ["walkdown"]
    assert drift.summary_lines(c)[-1] == ("new phrase hits: 1 from Walkdown (the older run recorded no "
                                          "search-term version)")
    old = [dict(inv("lib.md", None), bytes=10)]
    c = drift.compare(drift.load(run(tmp_path, "c", old, [])),
                      drift.load(run(tmp_path, "d", [inv("lib.md", "b1")], [hit("lib.md", ["E.a"], "x")])))
    assert c["hits_added_cause"] == ["unverified"]


def test_repository_changes_alone_add_no_cause_line(tmp_path):
    t = terms({"E.a": "1"})
    c = drift.compare(drift.load(run(tmp_path, "a", SAME, [], terms=t)),
                      drift.load(run(tmp_path, "b", EDITED, [hit("SKILL.md", ["E.a"], "x")], pin_hash="b", terms=t)))
    lines = drift.summary_lines(c)
    assert not any(x.startswith(("Walkdown changed", "new phrase hits:")) for x in lines)


def test_since_same_version(tmp_path):
    """The same repository version: nothing to say when nothing differs; when a hit differs,
    the report is written and says every difference comes from Walkdown."""
    t = terms({"E.a": "1"})
    a = run(tmp_path, "2026-01-01_aaa", SAME, [], terms=t)
    b = run(tmp_path, "2026-01-02_aaa", SAME, [], terms=t)
    s = drift.since(a, b)
    assert (s["same"], s["differs"], s["report"]) == (True, False, None)
    assert not (b / "changes.md").exists()
    c = run(tmp_path, "2026-01-03_aaa", SAME, [hit("lib.md", ["E.new"], "x")],
            terms=terms({"E.a": "1", "E.new": "2"}))
    s = drift.since(a, c)
    assert (s["same"], s["differs"]) == (True, True)
    md = s["report"].read_text(encoding="utf-8")
    assert "Same version of the repository; every difference comes from Walkdown." in md
    assert "## Walkdown's search terms and matching code (1)" in md and "- added: E.new" in md
    assert "(Walkdown's search terms)" in md
    assert "new phrase hits: 1 from Walkdown's search terms" in s["lines"]
    s = drift.since(a, run(tmp_path, "2026-01-04_bbb", EDITED, [], pin_hash="bbb", terms=t))
    assert (s["same"], s["differs"]) == (False, True) and s["report"].is_file()


# 2026-10-20: a file whose bytes differ only in line endings is not an edit.

import hashlib  # noqa: E402


def eol_inv(f, text, crlf=False, hashes=True):
    lf = text.encode("utf-8")
    raw = lf.replace(b"\n", b"\r\n") if crlf else lf
    row = inv(f, hashlib.sha256(raw).hexdigest(), bytes_=len(raw))
    if hashes:
        row.update(sha256_lf=hashlib.sha256(lf).hexdigest(),
                   sha256_crlf=hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest())
    return row


def test_line_endings_alone_are_not_an_edit(tmp_path):
    t = terms({"E.a": "1"})
    old = [eol_inv("a.md", "one\ntwo\n", crlf=True), eol_inv("b.md", "x\n")]
    new = [eol_inv("a.md", "one\ntwo\n"), eol_inv("b.md", "y\n")]
    c = drift.compare(drift.load(run(tmp_path, "a", old, terms=t)),
                      drift.load(run(tmp_path, "b", new, [hit("a.md", ["E.a"], "q")], terms=t)))
    assert c["files_eol"] == ["a.md"] and c["files_changed"] == ["b.md"]
    assert c["hits_added_cause"] == ["other"]  # a.md has the same content: not the repository
    assert "1 file differing only in line endings" in drift.summary_lines(c)[0]


def test_an_older_run_without_the_hashes_is_matched_either_way(tmp_path):
    old = [eol_inv("a.md", "one\n", crlf=True, hashes=False), eol_inv("b.md", "two\n", hashes=False)]
    new = [eol_inv("a.md", "one\n"), eol_inv("b.md", "two\n", crlf=True)]
    c = drift.compare(drift.load(run(tmp_path, "a", old)), drift.load(run(tmp_path, "b", new)))
    assert c["files_eol"] == ["a.md", "b.md"] and c["files_changed"] == []


def test_same_commit_with_files_changed_on_disk_is_said_so(tmp_path):
    t = terms({"E.a": "1"})
    a = run(tmp_path, "2026-01-01_aaa", [eol_inv("a.md", "one\n", crlf=True)], terms=t)
    b = run(tmp_path, "2026-01-02_aaa", [eol_inv("a.md", "one\n")], terms=t)
    s = drift.since(a, b)
    assert (s["same"], s["differs"], s["report"]) == (True, False, None)  # line endings only: nothing
    c = run(tmp_path, "2026-01-03_aaa", [eol_inv("a.md", "two\n")], [hit("a.md", ["E.a"], "q")], terms=t)
    s = drift.since(a, c)
    assert s["on_disk"] == 1
    assert s["header"].startswith("same commit of the repository, but 1 file on disk differs")
    md = s["report"].read_text(encoding="utf-8")
    assert "every difference comes from Walkdown" not in md
    assert "differences in other files come from Walkdown" in md


def costs(session, largest, unused_tokens, project=None, file="skills/a/SKILL.md"):
    """Slice 1's rows as the builder step writes them (slice 6, 2026-10-27; `02.5-capability` wrote them
    until restructure step 4)."""
    rows = [{"check": "cap.context", "file": None, "line": None, "tier": "session", "tokens": session},
            {"check": "cap.context", "file": file, "line": None, "tier": "skill-max", "tokens": largest},
            {"check": "cap.ship", "file": f"notes/{SECRET}.md", "line": None, "group": "unused", "tokens": unused_tokens}]
    if project is not None:
        rows.append({"check": "cap.context", "file": None, "line": None, "tier": "project", "tokens": project})
    return rows


def test_cost_since_the_earlier_run(tmp_path):
    """Slice 6: before -> now for each of slice 1's numbers, counts only; a run made before them is
    not comparable; the same numbers are no difference."""
    old = drift.load(run(tmp_path, "a", OLD1, s6=costs(1200, 6810, 100)))
    new = drift.load(run(tmp_path, "b", OLD1, s6=costs(1320, 6500, 100, project=400)))
    c = drift.compare(old, new)
    assert drift.cost_changed(c) and drift.differs(c)
    line = drift.cost_line(c)
    assert line == ("cost: every session 1,200 -> 1,320 tokens (+120); every session in this folder none -> 400 tokens; "
                    "largest at its fullest 6,810 -> 6,500 tokens (-310)")
    assert line in drift.summary_lines(c) and SECRET not in " ".join(drift.summary_lines(c))
    same = drift.compare(old, drift.load(run(tmp_path, "c", OLD1, s6=costs(1200, 6810, 100))))
    assert not drift.cost_changed(same) and drift.cost_line(same) is None
    before = drift.compare(drift.load(run(tmp_path, "d", OLD1)), new)
    assert drift.cost_line(before).startswith("costs not comparable")
    assert drift.cost_line(drift.compare(new, drift.load(run(tmp_path, "e", OLD1)))) is None
    report = drift.render(tmp_path / "a", tmp_path / "b", old, new, c)
    assert "## What it costs (estimated tokens)" in report and "| Every session | 1,200 | 1,320 | +120 |" in report


def test_a_run_made_before_step_4_keeps_its_costs_in_capability_json(tmp_path):
    """Restructure step 4: `02.5-capability` wrote the cost rows until then, and capability.json (every
    citation, the file drift reads for `02.5-capability`) still holds them in such a run; they are read as
    the builder step's, so the first comparison across the step is a comparison and not a claim
    that costs were never counted."""
    old_dir = run(tmp_path, "a", OLD1)
    (old_dir / "data" / "02.6-builder.json").unlink()
    (old_dir / "data" / "capability.json").write_text(
        json.dumps({"stage": "02.5-capability", "contract": 1, "findings": costs(1200, 6810, 100)}), encoding="utf-8")
    old = drift.load(old_dir)
    assert [x["check"] for x in old["02.6-builder"]] == ["cap.context", "cap.context", "cap.ship"]
    new = drift.load(run(tmp_path, "b", OLD1, s6=costs(1320, 6810, 100)))
    c = drift.compare(old, new)
    assert drift.cost_line(c) == "cost: every session 1,200 -> 1,320 tokens (+120)"
    assert drift.cost_line(drift.compare(old, drift.load(run(tmp_path, "c", OLD1, s6=costs(1200, 6810, 100))))) is None


# 2026-10-28, restructure step 1: a run made before the stages were renamed is not comparable.

OLD_NAMES = {"02.1-inventory": "01-inventory", "02.3-graph": "03-graph", "02.4-phrases": "04-phrases",
             "02.5-capability": "05-capability"}


def pre_rename_run(tmp, name, s1=()):
    """A run folder as Walkdown wrote it before the rename: stage outputs under the old names."""
    d = run(tmp, name, s1)
    for new, old in OLD_NAMES.items():
        (d / "data" / f"{new}.json").rename(d / "data" / f"{old}.json")
    return d


def test_a_run_from_before_the_rename_is_recognised(tmp_path):
    assert drift.predates_rename(pre_rename_run(tmp_path, "a", SAME))
    assert not drift.predates_rename(run(tmp_path, "b", SAME))
    empty = tmp_path / "failed"  # a failed run has no stage outputs at all: not this case
    (empty / "data").mkdir(parents=True)
    assert not drift.predates_rename(empty)
    # the layout before 2026-10-02 had the stage outputs at the top: such a run is recognised, never read
    top = tmp_path / "top"
    top.mkdir()
    (top / "01-inventory.json").write_text("{}", encoding="utf-8")
    assert drift.predates_rename(top)


def test_a_run_from_before_the_rename_is_not_compared(tmp_path):
    """Its stage files carry the old names: reading them as the new names would call every file
    added or removed. The earlier run is said to be not comparable, as costs are; nothing is
    compared, and no repository text is printed."""
    old = pre_rename_run(tmp_path, "2026-01-01_aaa", SAME)
    new = run(tmp_path, "2026-01-02_aaa", EDITED + [inv(f"{SECRET}.md", "z9")])
    s = drift.since(old, new)
    assert s["differs"] is True and s["same"] is False and s["not_comparable"] is True
    assert s["lines"] == ["not comparable: the earlier run was made before the stages were renamed, "
                          "so its stage files do not match"]
    md = s["report"].read_text(encoding="utf-8")
    assert md.startswith("# Changes: 2026-01-01_aaa -> 2026-01-02_aaa")
    assert "Not comparable: the earlier run was made before the stages were renamed" in md
    assert "files added" not in " ".join(s["lines"]) and "## Files added" not in md
    assert SECRET not in md and SECRET not in " ".join(s["lines"])
    assert s["report"] == new / "changes.md"


def test_the_newer_run_from_before_the_rename_is_not_compared_either(tmp_path):
    s = drift.since(run(tmp_path, "a", SAME), pre_rename_run(tmp_path, "b", SAME))
    assert s["not_comparable"] and "the newer run" in s["lines"][0]


def test_the_diff_command_says_not_comparable(tmp_path, capsys):
    old = pre_rename_run(tmp_path, "a", SAME)
    new = run(tmp_path, "b", SAME)
    assert drift.main([str(old), str(new)]) == 0
    out = capsys.readouterr().out
    assert "not comparable" in out and "written:" in out
    page = (new / "changes.md").read_text(encoding="utf-8")
    assert "Not comparable" in page and "this version" not in page  # a reader sees a number (2026-10-29)
    assert f"again with Walkdown {drift.walkdown_version()} to start" in page and drift.walkdown_version()


def test_the_not_comparable_line_reaches_the_details_page(tmp_path):
    import details_html
    s = drift.since(pre_rename_run(tmp_path, "2026-01-01_aaa", SAME), run(tmp_path, "2026-01-02_aaa", SAME))
    html = details_html.changes({**s, "since": "2026-01-01_aaa"})
    assert "Not comparable: the earlier run was made before the stages were renamed" in html
    assert "changes.md" in html


def test_two_runs_from_after_the_rename_still_compare(tmp_path):
    s = drift.since(run(tmp_path, "2026-01-01_aaa", SAME), run(tmp_path, "2026-01-02_aaa", EDITED))
    assert not s.get("not_comparable") and s["differs"]


# 2026-10-29, restructure step 7b: a run is compared only when its record has the current format.

WORDS = ("not comparable: the earlier run was made by an earlier version of Walkdown, "
         "and its data is in another shape")


def test_a_run_whose_record_has_an_older_format_is_not_compared(tmp_path):
    """A run made between step 7 and step 7b has a record, but the data inside it names its stages by number.
    Comparing it field by field would be quietly wrong, so it is not compared: one line, and no repository text."""
    old = run(tmp_path, "2026-01-01_aaa", SAME)
    write_record(old, 1)
    new = run(tmp_path, "2026-01-02_aaa", EDITED + [inv(f"{SECRET}.md", "z9")])
    s = drift.since(old, new)
    assert s["not_comparable"] is True and s["differs"] is True and s["same"] is False
    assert s["lines"] == [WORDS]
    md = s["report"].read_text(encoding="utf-8")
    assert md.startswith("# Changes: 2026-01-01_aaa -> 2026-01-02_aaa") and WORDS[0].upper() + WORDS[1:] in md
    assert "## Files added" not in md and SECRET not in md and SECRET not in " ".join(s["lines"])


def test_a_run_with_no_record_and_the_newer_run_with_an_older_record_are_not_compared_either(tmp_path):
    none = run(tmp_path, "a", SAME)
    (none / "data" / "run.json").unlink()
    assert drift.since(none, run(tmp_path, "b", SAME))["lines"] == [WORDS]
    older_new = run(tmp_path, "c", SAME)
    write_record(older_new, 1)
    s = drift.since(run(tmp_path, "d", SAME), older_new)
    assert s["not_comparable"] and s["lines"] == [WORDS.replace("the earlier run", "the newer run")]
    # a run from before the rename keeps its own words, whatever its record says
    s = drift.since(pre_rename_run(tmp_path, "e", SAME), run(tmp_path, "f", SAME))
    assert s["lines"] == ["not comparable: the earlier run was made before the stages were renamed, "
                          "so its stage files do not match"]


def test_the_previous_run_with_an_older_record_is_not_compared_in_the_one_comparison(tmp_path):
    """`changes` is what the details page, changes.md, and the brief's lines read."""
    import details_html
    old = run(tmp_path / "RepoResults" / "demo", "2026-01-01_aaa", SAME)
    write_record(old, 1)
    new = run(tmp_path / "RepoResults" / "demo", "2026-01-02_aaa", EDITED)
    c = drift.changes(new)
    assert c["since"] == "2026-01-01_aaa" and c["differs"] is True and c["lines"] == [WORDS]
    assert c["not_comparable"] is True  # the brief's header reads it (notes M6)
    assert "Not comparable: the earlier run was made by an earlier version of Walkdown" in details_html.changes(c)
    assert "Not comparable" in (new / "changes.md").read_text(encoding="utf-8")
    write_record(old)  # the same run with a current record is compared
    c = drift.changes(new)
    assert c["differs"] and c["lines"] and "not comparable" not in " ".join(c["lines"])
    assert c["not_comparable"] is False


def test_the_diff_command_says_not_comparable_for_an_older_record(tmp_path, capsys):
    old = run(tmp_path, "a", SAME)
    write_record(old, 1)
    assert drift.main([str(old), str(run(tmp_path, "b", SAME))]) == 0
    assert WORDS in capsys.readouterr().out


# 2026-10-30, O3: a run that stopped as asked (`--until`)

def test_a_run_that_stopped_before_its_coded_steps_is_not_compared_and_one_stopped_after_them_is(tmp_path, capsys):
    whole = run(tmp_path, "2026-01-01_aaa", OLD1)
    early = run(tmp_path, "2026-01-02_bbb", NEW1 + [inv(f"{SECRET}.md", "z9")], pin_hash="bbb")
    write_record(early, until="02.3-graph")
    why = 'not comparable: the newer run stopped after "What loads what", as asked'
    assert drift.not_comparable(whole, early) == why
    assert drift.not_comparable(early, whole) == why.replace("the newer run", "the earlier run")
    s = drift.since(whole, early)
    assert s["not_comparable"] is True and s["differs"] is True and s["lines"] == [why]
    md = (early / "changes.md").read_text(encoding="utf-8")
    assert md.startswith("# Changes: 2026-01-01_aaa -> 2026-01-02_bbb") and why[0].upper() + why[1:] in md
    assert "Nothing was compared" in md and "walkdown.py continue" in md and "Audit the repository again" not in md
    assert "## Files added" not in md and SECRET not in md
    assert drift.main([str(early), str(whole)]) == 0  # the diff command says the same
    assert "the earlier run stopped after" in capsys.readouterr().out
    intake = run(tmp_path, "2026-01-03_ccc", SAME)
    write_record(intake, until="01-intake")
    assert drift.not_comparable(whole, intake) == 'not comparable: the newer run stopped after "Getting the copy", as asked'
    # stopped after the last coded step, or after a model read: every coded step ran, so it is compared as usual
    for i, until in enumerate(("02.6-builder", "03-sweep")):
        after = run(tmp_path, f"2026-01-0{4 + i}_ddd", NEW1, pin_hash="bbb")
        write_record(after, until=until)
        assert drift.not_comparable(whole, after) is None
        c = drift.since(whole, after)
        assert not c.get("not_comparable") and c["differs"]
    went_through = run(tmp_path, "2026-01-07_eee", NEW1, pin_hash="bbb")
    assert drift.not_comparable(whole, went_through) is None


def test_the_next_full_run_is_compared_with_the_last_run_that_went_through(tmp_path):
    p = tmp_path / "RepoResults" / "demo"
    whole = run(p, "2026-01-01_aaa", OLD1)
    early = run(p, "2026-01-02_bbb", NEW1, pin_hash="bbb")
    write_record(early, until="02.2-reader")
    nxt = run(p, "2026-01-03_ccc", NEW1, [HIT], pin_hash="bbb")
    for d, t in ((whole, 1_000_000), (early, 2_000_000), (nxt, 3_000_000)):
        os.utime(d / "LOG.md", (t, t))
    c = drift.changes(nxt)
    assert c["since"] == whole.name and c["differs"] and not c["not_comparable"]  # not the stopped run in between
    stopped = drift.changes(early)  # the stopped run itself says why it is compared with nothing
    assert stopped["since"] == whole.name and stopped["not_comparable"] is True
    assert stopped["lines"] == ['not comparable: the newer run stopped after "What the model actually reads", as asked']


def test_an_output_that_is_no_report_compares_as_none_and_does_not_crash(tmp_path):
    """M9 slice B fix round: the check of the run names an output that cannot be read, or that is valid JSON and no report
    (`[]`, `{}`), a gap; the comparison with the previous run reads it the same way, so a run that was held for it can be
    released."""
    a = run(tmp_path, "a", s4=[HIT])
    b = run(tmp_path, "b", s4=[HIT])
    for text in ("[]", "{}", "not json", '{"findings": "no"}'):
        (b / "data" / "02.4-phrases.json").write_text(text, encoding="utf-8")
        loaded = drift.load(b)
        assert "02.4-phrases" not in loaded and "02.1-inventory" in loaded, text
        drift.compare(drift.load(a), loaded)  # no crash


def test_a_file_name_with_a_newline_is_one_line_in_changes_md(tmp_path):
    """M9 slice B second fix round: `changes.md` prints the names of files the repository added, removed, and changed; a name
    with a newline in it must not start a bullet or a heading of its own."""
    nl = chr(10)
    forged = "new" + nl + "- CANARY forged bullet" + nl + "## CANARY heading" + nl + "x.md"
    a = run(tmp_path, "a", OLD1)
    b = run(tmp_path, "b", [*NEW1, inv(forged, "e1")])
    text = drift.write_report(a, b)[0].read_text(encoding="utf-8")
    assert "new - CANARY forged bullet ## CANARY heading x.md" in text
    assert not [x for x in text.splitlines() if x.startswith(("- CANARY", "## CANARY"))]


def test_a_file_name_with_a_newline_is_one_line_in_the_list_of_files_that_differ_only_in_line_endings(tmp_path):
    """The same for the list of files whose bytes differ only in their line endings: a name is one bullet, whatever it holds."""
    nl = chr(10)
    forged = "eol" + nl + "- CANARY forged bullet" + nl + "## CANARY heading" + nl + "x.md"
    a = run(tmp_path, "a", [*OLD1, eol_inv(forged, "one\ntwo\n", crlf=True)])
    b = run(tmp_path, "b", [*NEW1, eol_inv(forged, "one\ntwo\n")])
    text = drift.write_report(a, b)[0].read_text(encoding="utf-8")
    assert "## Files that differ only in line endings (1)" in text
    assert "- eol - CANARY forged bullet ## CANARY heading x.md" in text
    assert not [x for x in text.splitlines() if x.startswith(("- CANARY", "## CANARY"))]
