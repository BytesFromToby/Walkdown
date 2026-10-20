"""HTML as a browser draws it: text in the page that a person never sees, and text the style
sheet shows that is not in the page (review item "HTML render", built 2026-10-20). Spec:
specs/render_html.SPEC.md.

Optional: needs Playwright and its Chromium (`pip install playwright`, then
`python -m playwright install chromium-headless-shell`); without them every HTML file gets a skip.
The page's own scripts never run (JavaScript is off for the page), the browser is offline, every
request that is not a file inside the input folder is aborted, and nothing is downloaded.
"""
from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

MAX_FILES = 200        # HTML files drawn per run; the rest get a skip saying so
TIMEOUT_MS = 10_000    # per page load
VIEWPORT = {"width": 1280, "height": 800}
MIN_FONT_PX = 2        # smaller text cannot be read
MIN_CONTRAST = 1.15    # WCAG contrast ratio; closer to 1 means the text has its background's color

# Run in the page after it loads. The page's own scripts are off, so the DOM's functions are the
# browser's. Returns text nodes a person would not see, with why, and text added by ::before and
# ::after. Form controls are left out: a closed list's options are not drawn until it opens.
PROBE = r"""
([MIN_FONT, MIN_CONTRAST]) => {
  const SKIP = "head, script, style, template, noscript, title, select, option, optgroup, datalist, textarea";
  const root = document.documentElement;
  const body = document.body || root;
  const docW = Math.max(root.scrollWidth, body.scrollWidth);
  const docH = Math.max(root.scrollHeight, body.scrollHeight);
  const rgb = (c) => {
    const m = c && c.match(/^rgba?\(([^)]+)\)$/);
    if (!m) return null;
    const v = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number);
    return v.length >= 3 && v.every((x) => !isNaN(x)) ? [v[0], v[1], v[2], v.length > 3 ? v[3] : 1] : null;
  };
  const lum = (c) => {
    const f = (x) => { x /= 255; return x <= 0.03928 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]);
  };
  const contrast = (a, b) => {
    const [hi, lo] = [lum(a), lum(b)].sort((p, q) => q - p);
    return (hi + 0.05) / (lo + 0.05);
  };
  const background = (el) => {  // null when an image is behind the text: its color cannot be judged
    for (let a = el; a; a = a.parentElement) {
      const cs = getComputedStyle(a);
      if (cs.backgroundImage && cs.backgroundImage !== "none") return null;
      const c = rgb(cs.backgroundColor);
      if (c && c[3] > 0) return c;
    }
    return [255, 255, 255, 1];
  };
  const collapsedIn = (el) => {  // the closed <details> that hides el (outside its own summary), or null
    let prev = null;
    for (let a = el; a; prev = a, a = a.parentElement) {
      if (a.tagName === "DETAILS" && !a.open
          && !(prev && prev.tagName === "SUMMARY" && prev === a.querySelector(":scope > summary"))) return a;
    }
    return null;
  };
  const why = (node, el) => {
    if (collapsedIn(el)) return "collapsed";
    const cs = getComputedStyle(el);
    const range = document.createRange();
    range.selectNodeContents(node);
    const rects = Array.from(range.getClientRects());
    if (!rects.length) return "not-rendered";
    if (cs.visibility !== "visible") return "invisible";
    for (let a = el; a; a = a.parentElement) {
      if (parseFloat(getComputedStyle(a).opacity) === 0) return "transparent";
    }
    if (rects.every((r) => r.width < 1 || r.height < 1)) return "zero-size";
    if (parseFloat(cs.fontSize) < MIN_FONT) return "tiny-text";
    const sx = window.scrollX, sy = window.scrollY;
    const boxes = rects.map((r) => ({l: r.left + sx, t: r.top + sy, r: r.right + sx, b: r.bottom + sy}));
    if (boxes.every((r) => r.r <= 0 || r.b <= 0 || r.l >= docW || r.t >= docH)) return "off-page";
    if (cs.pointerEvents !== "none") {
      let seen = false;
      for (const r of boxes) {
        const cx = (r.l + r.r) / 2, cy = (r.t + r.b) / 2;
        window.scrollTo(Math.max(0, cx - innerWidth / 2), Math.max(0, cy - innerHeight / 2));
        const x = cx - window.scrollX, y = cy - window.scrollY;
        if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) continue;
        const hit = document.elementFromPoint(x, y);
        if (hit && (hit === el || el.contains(hit))) { seen = true; break; }
      }
      window.scrollTo(sx, sy);
      if (!seen) return "clipped-or-covered";
    }
    const fg = rgb(cs.color);
    if (fg && fg[3] === 0) return "transparent-text";
    const bg = background(el);
    if (fg && bg && contrast(fg, bg) < MIN_CONTRAST) return "color-matches-background";
    return null;
  };
  const hidden = [];
  const ids = new Map();
  const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    const text = node.nodeValue.replace(/\s+/g, " ").trim();
    const el = node.parentElement;
    if (!text || !el || el.closest(SKIP)) continue;
    const how = why(node, el);
    if (!how) continue;
    const key = how === "collapsed" ? collapsedIn(el) : el;  // one item per closed section
    if (!ids.has(key)) ids.set(key, ids.size);
    hidden.push({text, how, el: ids.get(key)});
  }
  const generated = [];
  for (const el of body.querySelectorAll("*")) {
    if (el.closest(SKIP)) continue;
    for (const pseudo of ["::before", "::after"]) {
      const s = getComputedStyle(el, pseudo);
      if (!s.content || s.display === "none" || s.visibility !== "visible") continue;
      const m = s.content.match(/^"((?:[^"\\]|\\.)*)"$/);  // a plain string only: no counters, attr(), images
      if (!m) continue;
      const text = m[1].replace(/\\(.)/g, "$1").replace(/\s+/g, " ").trim();
      if (/[A-Za-zÀ-ɏ]{3,}/.test(text)) generated.push({text, pseudo});
    }
  }
  return {hidden, generated};
}
"""


def _browsers_dirs() -> list[Path]:
    env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if env and env != "0":
        return [Path(env)]
    if sys.platform == "win32":
        return [Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ms-playwright"]
    if sys.platform == "darwin":
        return [Path.home() / "Library" / "Caches" / "ms-playwright"]
    return [Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "ms-playwright"]


def available() -> tuple[bool, str]:
    """Cheap check, no browser started: the package is importable and a Chromium is installed."""
    if importlib.util.find_spec("playwright") is None:
        return False, "playwright not installed"
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH") == "0":
        return True, "playwright with its bundled browsers"
    if not any(d.is_dir() and any(p.name.startswith("chromium") for p in d.iterdir())
               for d in _browsers_dirs()):
        return False, "playwright's Chromium not installed (python -m playwright install chromium-headless-shell)"
    return True, "playwright"


def _collapse(s: str) -> str:
    return " ".join(s.split())


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def line_of(text: str, source: str) -> int | None:
    """The source line where `text` starts: the whole text, then its first 40 characters, then
    its first words with tags, entities, or white space between them; None when not found."""
    for needle in (text, text[:40]):
        i = source.find(needle)
        if needle and i >= 0:
            return source.count("\n", 0, i) + 1
    words = re.findall(r"[^\W_]+", text)[:5]
    if len(words) >= 2:
        gap = r"(?:\s|<[^>]*>|&#?\w+;|[^\w<&])+"
        m = re.search(gap.join(map(re.escape, words)), source)
        if m:
            return source.count("\n", 0, m.start()) + 1
    return None


def merge(hidden: list[dict]) -> list[dict]:
    """Consecutive text of one element hidden the same way is one item."""
    out: list[dict] = []
    for h in hidden:
        if out and out[-1]["el"] == h["el"] and out[-1]["how"] == h["how"]:
            out[-1]["text"] += " " + h["text"]
        else:
            out.append(dict(h))
    return out


def divergences(probe: dict, source: str, static_texts) -> list[dict]:
    """The probe's results as divergence dicts ({line, text, how, reading}), leaving out any
    text static style already reported (either text inside the other)."""
    seen = [_collapse(t) for t in static_texts if t]

    def known(t):
        return any(t in s or s in t for s in seen)
    out = []
    for h in merge(probe.get("hidden") or []):
        t = _collapse(h["text"])
        if t and not known(t):
            out.append({"line": line_of(t, source), "text": t, "how": h["how"], "reading": "A-only"})
    for g in probe.get("generated") or []:
        t = _collapse(g["text"])
        if t:
            out.append({"line": line_of(g["text"], source), "text": t, "how": "css-content",
                        "reading": "B-only", "pseudo": g["pseudo"]})
    return out


class Session:
    """One browser for a whole stage 2 run, started at the first HTML file and closed by
    `close()`. `render(rel)` returns the probe's dict, or raises RenderError."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.drawn = 0
        self._pw = self._browser = None

    def _start(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(headless=True)
        except Exception:
            self._pw.stop()
            self._pw = None
            raise

    def _route(self, route):
        url = route.request.url
        ok = False
        if url.startswith("file:"):
            p = urlparse(url)
            try:
                ok = _inside(Path(url2pathname(p.path)).resolve(), self.root)
            except (OSError, ValueError):
                ok = False
        if ok:
            route.continue_()
        else:
            route.abort()

    def render(self, rel: str) -> dict:
        if self._browser is None:
            try:
                self._start()
            except Exception as exc:
                raise RenderError(f"browser did not start: {type(exc).__name__}: {exc}"[:200])
        ctx = self._browser.new_context(java_script_enabled=False, offline=True, viewport=VIEWPORT,
                                        accept_downloads=False, service_workers="block")
        try:
            page = ctx.new_page()
            page.route("**/*", self._route)
            page.goto((self.root / rel).as_uri(), wait_until="load", timeout=TIMEOUT_MS)
            out = page.evaluate(PROBE, [MIN_FONT_PX, MIN_CONTRAST])
            self.drawn += 1
            return out
        except Exception as exc:
            raise RenderError(f"{type(exc).__name__}: {str(exc).splitlines()[0] if str(exc) else ''}"[:200])
        finally:
            ctx.close()

    def close(self):
        if self._browser is not None:
            self._browser.close()
        if self._pw is not None:
            self._pw.stop()
        self._browser = self._pw = None


class RenderError(Exception):
    pass
