"""Tests for extract.py, written from specs/extract.SPEC.md."""
import json

from extract import extract


def refs(rel, text):
    return [(f.line, f.ref.path, f.context, f.form) for f in extract(rel, text)]


def one(rel, text, path):
    hits = [f for f in extract(rel, text) if f.ref.path == path]
    assert len(hits) == 1, (path, refs(rel, text))
    return hits[0]


def test_links():
    text = ("Read [a](docs/a.md) and ![i](img.png \"t\").\n"
            "[r]: ref.md\n"
            '<a href="h.md">x</a> <img src=\'p/q.svg\'>\n')
    assert one("x.md", text, "docs/a.md").form == "markdown-link"
    f = one("x.md", text, "img.png")
    assert (f.context, f.form, f.line) == ("link", "image", 1)
    assert one("x.md", text, "ref.md").form == "reference-def"
    assert one("x.md", text, "h.md").form == "html-attr"
    assert one("x.md", text, "p/q.svg").context == "link"


def test_code_span_and_fence():
    text = "Run `scripts/setup.sh` first.\n\n```bash\nbash scripts/run.sh\n```\nafter\n"
    f = one("x.md", text, "scripts/setup.sh")
    assert (f.context, f.form, f.line) == ("code", "code-span", 1)
    f = one("x.md", text, "scripts/run.sh")
    assert (f.context, f.form, f.line) == ("code", "fenced", 4)


def test_comment_multiline():
    text = "top\n<!-- note\nsee hidden/payload.md\n-->\nafter prose/x.md\n"
    f = one("x.md", text, "hidden/payload.md")
    assert (f.context, f.line) == ("comment", 3)
    assert one("x.md", text, "prose/x.md").context == "prose"


def test_prose():
    f = one("x.md", "For details, see references/details.md.\n", "references/details.md")
    assert f.context == "prose" and f.ref.written == "references/details.md"


def test_zero_width():
    f = one("x.md", "line one\nsee refer\u200bences/a.md\n", "references/a.md")
    assert f.line == 2


def test_config_json_yaml_toml():
    doc = {"hooks": {"SessionStart": [{"hooks": [
        {"type": "command", "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/start.sh"}]}]}}
    text = json.dumps(doc, indent=2)
    f = one("hooks/hooks.json", text, "hooks/start.sh")
    assert f.context == "config" and f.form == "config"
    want = next(i for i, l in enumerate(text.split("\n"), 1) if "start.sh" in l)
    assert f.line == want
    y = "name: x\nskills:\n  - skills/a/SKILL.md\n"
    f = one("m.yaml", y, "skills/a/SKILL.md")
    assert (f.context, f.line) == ("config", 3)
    t = 'title = "x"\n[paths]\nmain = "src/main.py"\n'
    f = one("c.toml", t, "src/main.py")
    assert (f.context, f.line) == ("config", 3)
    broken = '{"a": "docs/x.md",\n'
    assert one("b.json", broken, "docs/x.md").context == "prose"


def test_scripts():
    py = 'import os\nwith open("data/x.json") as f:\n    os.path.join(a, b)\n'
    f = one("s.py", py, "data/x.json")
    assert (f.context, f.form, f.line) == ("code", "script", 2)
    assert all(fd.ref.path != "os.path.join" and "os.path" not in fd.ref.path
               for fd in extract("s.py", py))
    sh = "#!/bin/sh\nsource lib/common.sh\n"
    assert one("run", sh, "lib/common.sh").context == "code"


def test_link_text_repeat_once():
    f = one("x.md", "[references/a.md](references/a.md)\n", "references/a.md")
    assert f.context == "link"


def test_call_tags_templates_patternlists():
    text = "```js\nconsole.log(x)\n```\n<b>docs/a.md</b> and docs/<topic>-design.md\n"
    got = refs("x.md", text)
    assert [g[1] for g in got] == ["docs/a.md"], got
    assert extract(".gitignore", "evals/\n*.pyc\n") == []
    assert extract("sub/.gitattributes", "*.sh text eol=lf\n") == []
