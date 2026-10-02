"""Tests for chunks.py, written from specs/chunks.SPEC.md."""
import chunks


def inv(*files):
    return {"findings": [{"check": "inv.file", "file": f, "line": None, "encoding": "utf-8"}
                         for f in files]}


def test_sweep_files_are_prose_a_model_reads():
    got = chunks.sweep_files(inv("SKILL.md", "README.md", "docs/guide.md", "agents/a.md",
                                 "run.sh", "notes.txt", "data.json", "CHANGELOG.md"))
    assert got == ["SKILL.md", "agents/a.md", "notes.txt"]
    unreadable = {"findings": [{"check": "inv.file", "file": "x.md", "encoding": None}]}
    assert chunks.sweep_files(unreadable) == []


def test_frontmatter_and_headings_start_chunks_but_not_inside_fences():
    lines = ["---", "name: x", "---", "Intro.", "## One", "text", "```", "# not a heading", "```",
             "## Two", "more"]
    got = [(c["line"], c["end_line"]) for c in chunks.chunk_text("a.md", lines)]
    assert got == [(1, 3), (4, 4), (5, 9), (10, 11)]


def test_long_section_split_at_blank_lines_never_mid_line():
    para = ["word " * 40] * 4  # about 800 characters
    lines = ["## Big"] + para + [""] + para + [""] + para
    got = chunks.chunk_text("a.md", lines)
    assert len(got) >= 2 and got[0]["line"] == 1 and got[-1]["end_line"] == len(lines)
    for a, b in zip(got, got[1:]):
        assert b["line"] == a["end_line"] + 1
    long_line = ["x" * 5000]
    assert [(c["line"], c["end_line"]) for c in chunks.chunk_text("a.md", long_line)] == [(1, 1)]


def test_blank_chunks_dropped_and_text_kept():
    got = chunks.chunk_text("a.md", ["## A", "", "## B", "body"])
    assert [c["text"] for c in got] == ["## A", "## B\nbody"]


def test_covered_lists_stage4_patterns_inside_the_chunk():
    c = {"file": "a.md", "line": 5, "end_line": 9}
    s4 = [{"check": "phrase.L.override", "file": "a.md", "line": 6, "patterns": ["L.ignore"]},
          {"check": "phrase.K.exfil", "file": "a.md", "line": 10, "patterns": ["K.dns"]},
          {"check": "term.def", "file": "a.md", "line": 7},
          {"check": "phrase.creds", "file": "b.md", "line": 6, "patterns": ["creds.path"]}]
    assert chunks.covered(c, s4) == ["L.ignore"]
