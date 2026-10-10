"""Tests for secret_scan.py and the masking in run.py, from specs/secret_scan.SPEC.md."""
import importlib.util
from pathlib import Path

import secret_scan

_s = importlib.util.spec_from_file_location("walkdown_s04_run", Path(__file__).resolve().parents[1] / "run.py")
run4 = importlib.util.module_from_spec(_s)
_s.loader.exec_module(run4)
FAKE = "q8Zr2vN7xW4kL9pT3mB6yH1cF5sD0gJ2"


def make(tmp_path):
    (tmp_path / "SKILL.md").write_text(f'line one\napi_key = "{FAKE}"\n', encoding="utf-8")
    (tmp_path / "package-lock.json").write_text(f'{{"integrity": "sha512-{FAKE}{FAKE}=="}}\n',
                                                 encoding="utf-8")
    return {"SKILL.md": "model", "package-lock.json": "tool"}


def test_finds_the_line_and_never_the_value(tmp_path):
    out = secret_scan.scan(tmp_path, make(tmp_path))
    assert [(f["file"], f["line"]) for f in out] == [("SKILL.md", 2)]
    assert out[0]["audience"] == "model" and out[0]["kinds"]
    assert FAKE not in repr(out) and "hashed" not in repr(out)


def test_no_scanner_is_a_skip(tmp_path, monkeypatch):
    monkeypatch.setattr(secret_scan, "_gitleaks", lambda root, rels: None)
    monkeypatch.setattr(secret_scan, "_detect_secrets", lambda root, rels: None)
    [f] = secret_scan.scan(tmp_path, make(tmp_path))
    assert f["check"] == "secret.found" and f["skipped"] == secret_scan.SKIPPED


def test_quotes_on_secret_lines_are_masked():
    fs = [{"check": "secret.found", "file": "a.md", "line": 2, "kinds": ["Secret Keyword"]},
          {"check": "phrase.creds", "file": "a.md", "line": 2, "quote": f"key={FAKE}",
           "matches": [{"pattern": "creds.secret-name", "text": f"key={FAKE}"}]},
          {"check": "term.def", "file": "a.md", "line": 2, "quote": FAKE, "definition": FAKE},
          {"check": "phrase.creds", "file": "a.md", "line": 3, "quote": "other line"}]
    run4.mask_secret_lines(fs)
    assert FAKE not in repr(fs) and fs[1]["masked"] and fs[2]["definition"] == run4.SECRET_MASK
    assert fs[3]["quote"] == "other line" and "masked" not in fs[3]


def test_likely_not_secret():
    from secret_scan import likely_not_secret as why
    hx = ["Hex High Entropy String"]
    assert why('  "sha256": "' + "ab12" * 16 + '",', hx) == "a hash under a key named for one"
    assert why('  "token": "' + "ab12" * 16 + '",', hx) is None
    url = "DB_URL: postgres://app:pw@localhost:5432/app_test"
    assert why(url, ["Basic Auth Credentials"]) == "a password in a URL for a local test address"
    assert why(url.replace("localhost", "db.prod.acme.io"), ["Basic Auth Credentials"]) is None
    kw = ["Secret Keyword"]
    assert why('_API_KEY_VAR = "ANTHROPIC_API_KEY"', kw) == "a variable name, not a value"
    assert why("POSTGRES_PASSWORD: caveman", kw) == "a plain word or prose, not a value"
    assert why("  J.enter-secret: prohibited   # entering credentials", kw) == (
        "a plain word or prose, not a value")
    assert why('api_key = "q8Zr2vN7xYw3pLk9TbHs"', kw) is None


def test_likely_not_secret_names_and_reserved_hosts():
    from secret_scan import likely_not_secret as why
    assert why('  "prefix_hash": "' + "ab12" * 16 + '",', ["Hex High Entropy String"])
    assert why('"endpoint": "https://user:pw@gw.example.com",', ["Basic Auth Credentials"])
    assert why("      secretName: caveman-gateway-tls", ["Secret Keyword"])
    assert why("      secretName: sk-ant-api03-x1", ["Secret Keyword"]) is None


def test_hash_key_needs_a_separator_before_the_hash_word():
    from secret_scan import likely_not_secret as why
    assert why('  "avoid": "' + "ab12" * 16 + '",', ["Hex High Entropy String"]) is None
