"""Tests for endpoints.py, written from specs/endpoints.SPEC.md."""
import pytest

from endpoints import census, hosts_in_line, is_local, summary
from vocab import load_vocab


@pytest.fixture(scope="module")
def v():
    return load_vocab()


def test_urls(v):
    assert hosts_in_line("see https://Www.Api.Example.invalid:8443/x now", v) == \
        ["api.example.invalid"]
    assert hosts_in_line("git clone git@github.com:o/r.git", v) == ["github.com"]
    assert hosts_in_line("ssh://deploy@build.example.com/repo", v) == ["build.example.com"]


def test_file_names_are_not_hosts(v):
    assert hosts_in_line("run scripts/post.sh and read SKILL.md, then summary.json", v) == []
    assert hosts_in_line('logger.info("x")', v) == []
    assert hosts_in_line("see docs.example.com for more", v) == ["docs.example.com"]


def test_placeholders(v):
    assert hosts_in_line("curl https://${HOST}/api", v) == []
    assert hosts_in_line("open https://<your-domain>/", v) == []
    assert hosts_in_line("bind http://host:8080/ here", v) == []


def test_local_and_kind(v):
    assert hosts_in_line("http://localhost:3000/x", v) == ["localhost"]
    assert hosts_in_line("listen on 127.0.0.1:8080", v) == ["127.0.0.1"]
    assert hosts_in_line("print to printer.local today", v) == ["printer.local"]
    for h in ("localhost", "127.0.0.1", "printer.local", "0.0.0.0", "a.localhost"):
        assert is_local(h, v)
    assert not is_local("example.com", v)
    f = census([("localhost", "a.md", 1, "instructions"),
                ("registry.npmjs.org", "a.md", 2, "code"),
                ("example.com", "a.md", 3, "code")], v)
    kinds = {x["host"]: (x["kind"], x["local"]) for x in f}
    assert kinds == {"localhost": ("local", True), "registry.npmjs.org": ("registry", False),
                     "example.com": ("other", False)}


def test_documented(v):
    occ = [("a.invalid", "SKILL.md", 3, "instructions"), ("a.invalid", "README.md", 1, "docs"),
           ("b.invalid", "SKILL.md", 4, "instructions"), ("b.invalid", "s.sh", 2, "code"),
           ("c.invalid", "README.md", 5, "docs")]
    f = {x["host"]: x for x in census(occ, v)}
    assert f["a.invalid"]["documented"] is True
    assert f["b.invalid"]["documented"] is False
    assert f["c.invalid"]["documented"] is True
    for x in f.values():
        assert x["check"] == "endpoint.host" and x["file"] is None and x["line"] is None
        counts = {"instructions": 0, "docs": 0, "code": 0}
        for o in x["occurrences"]:
            counts[o["where"]] += 1
        assert x["where"] == counts
    assert f["b.invalid"]["occurrences"] == [{"file": "SKILL.md", "line": 4,
                                              "where": "instructions"},
                                             {"file": "s.sh", "line": 2, "where": "code"}]
    s = summary(list(f.values()))
    assert s["hosts"] == 3 and s["undocumented"] == 1 and s["local"] == 0


def test_one_occurrence_per_line(v):
    assert hosts_in_line("https://x.example.com/a and https://x.example.com/b", v) == \
        ["x.example.com"]
    f = census([("x.example.com", "a.md", 1, "docs"), ("x.example.com", "a.md", 1, "docs")], v)
    assert len(f[0]["occurrences"]) == 1
