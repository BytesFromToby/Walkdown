"""Tests for coverage.py, written from specs/report.SPEC.md, coverage (owner, 2026-11-04: what Walkdown examined, in white,
yellow, and red)."""
import coverage as C
import details_html


def inv(name, **kw):
    row = {"check": "inv.file", "file": name, "line": None, "ext": name.rsplit(".", 1)[-1] if "." in name else ""}
    row.update(kw)
    return row


def reports(reader=True):
    files = [
        inv("skills/x/SKILL.md", type="text/plain", encoding="utf-8", lines=4),
        inv("skills/x/run.py", type="text/plain", encoding="utf-8", lines=9),
        inv("docs/guide.pdf", type="application/pdf"),
        inv("docs/spec.docx", type="application/zip"),  # zip-based: the census flags it, the reader reads it
        inv("assets/bundle.zip", type="application/zip"),
        inv("assets/model.pkl", type="application/octet-stream"),
        inv("assets/tool.wasm", type="application/wasm"),
        inv("assets/Blob", type="application/octet-stream"),
        inv("assets/locked.md", skipped="unreadable: permission denied"),
        inv("tests/fixtures/sample.pkl", type="application/octet-stream"),
        inv("link", type="inode/symlink", target="elsewhere"),
    ]
    census = [{"check": "struct.census", "file": f, "line": None, "flag": "archive"}
              for f in ("docs/spec.docx", "assets/bundle.zip")]
    r = {"02.1-inventory": {"findings": files + census},
         "02.6-builder": {"findings": [{"check": "cap.ship", "file": "assets/model.pkl", "group": "on-demand"},
                                       {"check": "cap.ship", "file": "assets/tool.wasm", "group": "unused"}]}}
    if reader:
        r["02.2-reader"] = {"findings": [
            {"check": "read.unread", "file": f, "line": None, "reason": why} for f, why in (
                ("assets/bundle.zip", "archive (contents not extracted)"),
                ("assets/model.pkl", "binary blob (does not decode as text)"),
                ("assets/tool.wasm", "binary blob (does not decode as text)"),
                ("assets/Blob", "binary blob (does not decode as text)"),
                ("tests/fixtures/sample.pkl", "binary blob (does not decode as text)"))]}
    return r


def tiers_of(r):
    return {x["file"]: x["tier"] for x in C.rows(r)}


def test_each_file_is_examined_an_archive_or_not_and_symlinks_are_left_out():
    t = tiers_of(reports())
    assert {f for f, k in t.items() if k == "examined"} == {"skills/x/SKILL.md", "skills/x/run.py", "docs/guide.pdf",
                                                             "docs/spec.docx"}
    assert {f for f, k in t.items() if k == "archive"} == {"assets/bundle.zip"}
    assert {f for f, k in t.items() if k == "not"} == {"assets/model.pkl", "assets/tool.wasm", "assets/Blob",
                                                        "assets/locked.md", "tests/fixtures/sample.pkl"}
    assert "link" not in t


def test_without_the_reader_a_pdf_or_document_was_not_examined():
    """Only the reader draws text out of a PDF or a document: a run where it did not run examined none."""
    t = tiers_of(reports(reader=False))
    assert t["docs/guide.pdf"] == "not" and t["docs/spec.docx"] == "archive" and t["skills/x/SKILL.md"] == "examined"
    assert {x["file"]: x["why"] for x in C.rows(reports(reader=False))}["docs/guide.pdf"] == (
        "not text, and the reader step did not run")


def test_types_group_by_extension_with_what_the_ai_loads_and_test_folders_counted():
    red = {x["type"]: x for x in C.by_tier(reports())["not"]}
    assert red["pkl"]["count"] == 2 and red["pkl"]["tests"] == 1 and red["pkl"]["loads"] == 1
    assert red["wasm"]["loads"] == 0  # nothing points to it
    assert C.types_line(C.by_tier(reports())["not"]).startswith(".pkl 2, ")
    assert "(no extension) 1" in C.types_line(C.by_tier(reports())["not"])


def test_the_pages_show_three_tiers_and_details_names_the_files():
    short = C.section_html(reports())
    assert short.count('class="tier ') == 3 and "t-examined" in short and "t-archive" in short and "t-not" in short
    assert "No tests are run on these file types" in short and "the AI loads 1 of them" in short
    assert "assets/model.pkl" not in short  # the summary gives types and counts
    full = C.section_html(reports(), files=True)
    assert "<code>assets/model.pkl</code> · the AI loads it" in full and "1 in test or fixture folders" in full
    assert full.index("assets/model.pkl") < full.index("assets/tool.wasm")  # what the AI loads first
    assert C.section_html({}) == ""
    only_text = {"02.1-inventory": {"findings": [inv("a.md", type="text/plain", encoding="utf-8")]}}
    assert "t-not" not in C.section_html(only_text) and "t-archive" not in C.section_html(only_text)


def test_full_md_names_every_file_and_the_brief_gives_counts_only():
    L = "\n".join(C.full_lines(reports()))
    assert "- No tests are run on these file types: 5 (" in L and "- assets/model.pkl; the AI loads it; binary blob" in L
    assert "- tests/fixtures/sample.pkl; in a test or fixture folder;" in L
    assert "- assets/locked.md; could not be read" in L
    line = C.brief_line(reports())
    assert line == ("Examined: 4; archives looked inside for programs only: 1; no tests are run on 5 (4 file types; "
                    "the AI loads 1 of them).")
    assert "pkl" not in line  # the brief holds no text from the repository


def test_the_unknown_file_type_row_is_gone_and_the_archive_row_says_what_was_checked():
    rows = {k: (label, files) for k, label, files in details_html.file_concerns(reports())}
    assert "unknown-type" not in rows
    assert rows["archive"][0] == "Archives (looked inside for programs; the text inside was not read)"
