"""Tests for tokens.py, written from specs/tokens.SPEC.md."""
from tokens import classify, clean


def test_prose_path_trailing_period():
    assert clean("references/details.md.") == "references/details.md"
    r = classify("references/details.md.", "prose")
    assert r.shape == "path" and r.path == "references/details.md" and r.may_dangle
    assert r.written == "references/details.md"


def test_bare_names():
    r = classify("SKILL.md", "prose")
    assert r.shape == "bare" and not r.may_dangle
    assert classify("SKILL.md", "code").may_dangle
    assert classify("Node.js", "code").may_dangle
    r = classify("obj.method", "code")
    assert r is not None and not r.may_dangle
    assert classify("helpers.md", "comment").may_dangle is False


def test_globs():
    for t in ("extra/*.md", "*.md", "skills/**/SKILL.md"):
        r = classify(t, "prose")
        assert r is not None and r.shape == "glob", t
    assert classify("**Note:**", "prose") is None
    assert classify("**extra/*.md**", "prose").path == "extra/*.md"


def test_dir_and_non_paths():
    r = classify("extra/", "prose")
    assert r.shape == "dir" and r.may_dangle
    for t in ("and/or", "I/O", "v1.2", "3.14", "1.5/2.0", "word"):
        assert classify(t, "prose") is None, t


def test_not_references():
    for t in ("https://x.invalid/a.md", "mailto:a@b.invalid", "#section", "/etc/passwd",
              "C:\\x\\y.md", "~/x.md", "$HOME/x.md", "${HOME}/x.md", "\\\\srv\\x.md"):
        for ctx in ("prose", "code", "link", "config"):
            assert classify(t, ctx) is None, (t, ctx)


def test_placeholder_anchor_backslash():
    r = classify("${CLAUDE_PLUGIN_ROOT}/hooks/run.sh", "config")
    assert r.path == "hooks/run.sh" and r.written == "${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"
    assert classify("$PLUGIN_DIR/x/y.sh", "code").path == "x/y.sh"
    assert classify("%VAR%\\x\\y.ps1", "code").path == "x/y.ps1"
    assert classify("./a/b.md#part", "link").path == "a/b.md"
    assert classify("a\\b.md", "code").path == "a/b.md"
    assert classify("a/b.md?x=1", "link").path == "a/b.md"


def test_dotfiles():
    assert classify(".env", "prose") is None
    assert classify(".invalid.", "comment") is None
    r = classify("config/.env", "prose")
    assert r.shape == "path"


def test_link_and_slashed():
    r = classify("docs", "link")
    assert r.shape == "link" and r.may_dangle
    r = classify("skills/x", "code")
    assert r.shape == "slashed" and not r.may_dangle
    assert classify("skills/x", "prose") is None


def test_emphasis_and_spread():
    assert clean("__init__.py") == "__init__.py"
    assert clean("_emph.md_") == "emph.md"
    r = classify("...process.env", "code")
    assert r is None or not r.may_dangle


def test_at_import_and_md_escape():
    assert classify("@./skills/a/SKILL.md", "prose").path == "skills/a/SKILL.md"
    assert classify("STYLE" + chr(92) + "_GUIDE.md", "code").path == "STYLE_GUIDE.md"


def test_regex_template_and_git():
    for t in ("s/^/", "node.*server.js", "docs/plans/<name>.md", "plans/{date}.md",
              "origin/dev...HEAD", "foo/$x/bar.md", ".git/hooks/pre-commit.sh", ".git/",
              "a" + chr(92) + "n" + chr(92) + "n**Below"):
        assert classify(t, "code") is None, t
    r = classify("files[0].path", "code")
    assert r is None or r.shape != "glob"
