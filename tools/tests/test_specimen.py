"""Tests for tools/specimen.py and the specimen run it draws, written from specs/specimen.SPEC.md."""
import html
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))
import specimen as tool  # noqa: E402  (tools/specimen.py, which puts the report stage and its tests on the path)

import coverage  # noqa: E402
import details_html as D  # noqa: E402
import render as R  # noqa: E402
import summary_html as S  # noqa: E402

made = tool.specimen  # stages/06-report/tests/specimen_run.py
FILE_FLAGS = {"ext-magic-mismatch", "executable", "bytecode", "archive-executable", "archive", "symlink", "padding",
              "reader-window"}  # every reason `details_html.file_concerns` knows


def text(p: Path) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", p.read_text(encoding="utf-8"))).split())


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    out = tmp_path_factory.mktemp("specimen")
    assert tool.main(["--out", str(out)]) == 0
    return out


def test_every_variant_is_written_with_every_page_and_says_its_findings_are_made_up(out):
    for v in made.VARIANTS:
        for page in ("summary.html", "details.html", "review.html", "full.md", "brief.md"):
            assert made.NOTE in (out / v / page).read_text(encoding="utf-8"), (v, page)
    index = (out / "index.html").read_text(encoding="utf-8")
    assert all(f'href="{v}/summary.html"' in index for v in made.VARIANTS)


def test_every_kind_the_tables_and_the_pages_know_shows_in_everything(out):
    """The kinds stored in the Library tables and the report code each show on the "everything" pages; a new kind anywhere
    here fails until the specimen holds one. Misalignment's groups took the place of the trigger kinds (R13, 2026-11-05)."""
    s, d, rv = (text(out / "everything" / p) for p in ("summary.html", "details.html", "review.html"))
    pages = s + " " + d
    want = ([x[1] for x in S.CONCERNS] + [t for _, t in R.FORMAT_GROUPS]
            + [n for _, n, _ in R.PORT_KINDS] + [n for _, n, _ in R.FEATURE_KINDS] + [n for _, n, _ in R.FIT_KINDS]
            + [n for _, n, _ in R.CLEAN_KINDS] + [D.carrier_plain(c) for c in D.CARRIER_PLAIN] + [n for _, n in D.FAMILY]
            + list(coverage.LABEL.values()))
    assert [w for w in want if w not in pages] == []
    assert {rid for rid, _, _ in D.file_concerns(made.build("everything")["reports"])} == FILE_FLAGS
    for words in ("What it can do", "What Walkdown examined", "Misalignment", "Skill Formatting", "Descriptions too alike",
                  "What changed since run", "License:", "Web addresses", "Passwords, keys, and secrets"):
        assert words in pages, words
    for note in ("Decoded from base64", D.TOOL_TEXT_NOTE, D.HOOK_NOTES["cursor-environment"], "spell:"):
        assert note in rv, note


@pytest.mark.parametrize("variant, page, words", [
    ("nothing-found", "summary.html", "Walkdown found none of the security concerns it looks for."),
    ("step-failed", "summary.html", "Not every step worked in this run."),
    ("step-failed", "details.html", "Skipped in this run"),
    ("step-did-not-run", "brief.md", "This run did not complete"),
    ("stopped", "summary.html", "nothing was sent"),
    ("model-read-no-answer", "summary.html", "got no answer for any passage"),
    ("not-measured", "summary.html", "Not measured"),
])
def test_each_variant_shows_the_state_it_is_for(out, variant, page, words):
    assert words in text(out / variant / page)


def test_a_variant_it_does_not_know_is_refused():
    with pytest.raises(ValueError, match="no specimen variant"):
        made.build("nope")
