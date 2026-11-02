"""Whether Playwright and the Chromium it launches are here. Spec: specs/shared.SPEC.md, playwright_check.

Optional tools: the reader draws HTML as a browser does only when they are installed, and the
validation step needs to know whether they are, because installing one changes what a stage can
measure. Both ask here (restructure step 7, notes M13: the validation step used to import the reader's
`render_html` for this one check). Nothing is started: no browser, no page.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

INSTALL = "python -m playwright install chromium-headless-shell"


def _browsers_dirs() -> list[Path]:
    env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env and env != "0":
        return [Path(env)]
    if sys.platform == "win32":
        return [Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ms-playwright"]
    if sys.platform == "darwin":
        return [Path.home() / "Library" / "Caches" / "ms-playwright"]
    return [Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ms-playwright"]


def expected_build(spec) -> str | None:
    """The browser folder this Playwright launches headless (`chromium_headless_shell-<rev>`), from
    the package's own browsers.json; None when it cannot be read."""
    try:
        pkg = Path(spec.origin).parent / "driver" / "package" / "browsers.json"
        for b in json.loads(pkg.read_text(encoding="utf-8"))["browsers"]:
            if b.get("name") == "chromium-headless-shell":
                return f"chromium_headless_shell-{b['revision']}"
    except Exception:
        return None
    return None


def available() -> tuple[bool, str]:
    """Cheap check, no browser started: the package is importable and the Chromium build it
    launches is installed. Any Chromium was enough before 2026-10-21; a build from another
    Playwright version passed the check and then failed to start on every page."""
    spec = importlib.util.find_spec("playwright")
    if spec is None:
        return False, "playwright not installed"
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH") == "0":
        return True, "playwright with its bundled browsers"
    dirs = [d for d in _browsers_dirs() if d.is_dir()]
    want = expected_build(spec)
    if want is not None:
        if any((d / want).is_dir() for d in dirs):
            return True, "playwright"
        if any(p.name.startswith("chromium") for d in dirs for p in d.iterdir()):
            return False, (f"playwright's Chromium is a build for another Playwright version "
                           f"(this one needs {want}; {INSTALL})")
        return False, f"playwright's Chromium not installed ({INSTALL})"
    if not any(p.name.startswith("chromium") for d in dirs for p in d.iterdir()):
        return False, f"playwright's Chromium not installed ({INSTALL})"
    return True, "playwright"
