"""Tests for playwright_check.py, written from specs/shared.SPEC.md, playwright_check."""
import importlib.util

import playwright_check as PC


def test_available_names_what_is_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
    assert PC.available() == (False, "playwright not installed")
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: object())
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path))
    ok, why = PC.available()
    assert not ok and "Chromium not installed" in why
    (tmp_path / "chromium_headless_shell-1200").mkdir()
    assert PC.available()[0] is True


def test_available_wants_the_build_this_playwright_launches(monkeypatch, tmp_path):
    """2026-10-21: Chromium 1194 on disk, Playwright wanting 1248; the check said yes, the launch failed."""
    pkg = tmp_path / "playwright"
    (pkg / "driver" / "package").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", "utf-8")
    (pkg / "driver" / "package" / "browsers.json").write_text(
        '{"browsers": [{"name": "chromium", "revision": "9998"},'
        ' {"name": "chromium-headless-shell", "revision": "9999"}]}', "utf-8")
    spec = type("Spec", (), {"origin": str(pkg / "__init__.py")})()
    monkeypatch.setattr(importlib.util, "find_spec", lambda name: spec)
    browsers = tmp_path / "browsers"
    browsers.mkdir()
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browsers))
    assert PC.expected_build(spec) == "chromium_headless_shell-9999"
    ok, why = PC.available()
    assert not ok and "Chromium not installed" in why
    (browsers / "chromium_headless_shell-1194").mkdir()
    ok, why = PC.available()
    assert not ok and "another Playwright version" in why and "chromium_headless_shell-9999" in why
    (browsers / "chromium_headless_shell-9999").mkdir()
    assert PC.available() == (True, "playwright")
