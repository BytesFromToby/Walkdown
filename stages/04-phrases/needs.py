"""What a repository needs to run, and what ties it to one machine. Spec: specs/needs.SPEC.md.

Slice 2 of the plan for builders (owner, 2026-10-26). Stage 4 calls it with the texts it reads and
stage 1's inventory (moved here from stage 1 the same day: stage 1 must not import stage 4's
audience rules, which every later stage shares). It
runs, imports, and installs nothing. Only programs in tools.yaml count as programs.
"""
from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "04-phrases"))

from audience import SCRIPT_EXTS, audience, is_test_data  # noqa: E402

TOOLS = yaml.safe_load((HERE / "tools.yaml").read_text(encoding="utf-8"))
PROGRAMS = {k: (v or {}).get("os") for k, v in TOOLS["programs"].items()}
PACKAGE_NAMES = TOOLS["package_names"]
NODE_BUILTINS = set(TOOLS["node_builtins"])
NOT_PERSONAL = {str(x).lower() for x in TOOLS["not_personal"]}
STDLIB = set(sys.stdlib_module_names) | {"__future__"}
FAMILY = {"python3": "python", "py": "python", "pip3": "pip", "apt-get": "apt"}  # one declaration covers each
MARKDOWN = (".md", ".markdown", ".mdc", ".mdx")
SHELL_EXTS = {"sh", "bash", "zsh"}
WINDOWS_SCRIPTS = {"ps1", "psm1", "bat", "cmd"}
SHELL_FENCES = {"", "sh", "bash", "shell", "console", "zsh", "shellsession", "terminal"}


def _ext(rel: str) -> str:
    base = rel.rsplit("/", 1)[-1].lower()
    return base.rsplit(".", 1)[1] if "." in base else ""


def _lines(text: str) -> list[str]:
    return [x[:-1] if x.endswith("\r") else x for x in (text or "").split("\n")]


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def is_shell(rel: str, text: str | None) -> bool:
    if _ext(rel) in SHELL_EXTS:
        return True
    first = (text or "").split("\n", 1)[0]
    return _ext(rel) == "" and first.startswith("#!") and re.search(r"\b(ba|z)?sh\b", first) is not None


# ------------------------------------------------------------------ programs at command position

PROMPT = re.compile(r"^(?:\$|>|%|PS [^>]*>)\s+")
SPLIT = re.compile(r"\|\||&&|[|;]|\$\(|`")
ASSIGN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
PREFIX = {"sudo", "exec", "time", "nohup", "env", "command", "then", "do", "else", "!", "{", "(", "xargs"}


def first_words(line: str) -> list[str]:
    """The word at command position in each part of one line of shell, as written."""
    s = PROMPT.sub("", line.strip())
    if not s or s.startswith("#"):
        return []
    out = []
    for seg in SPLIT.split(s):
        words = seg.strip().split()
        while words and (ASSIGN.match(words[0]) or words[0] in PREFIX):
            words = words[1:]
        if words:
            out.append(words[0].strip("\"'(){}"))
    return out


def program(word: str) -> str | None:
    """The program a command word runs, when tools.yaml lists it (`/usr/bin/jq` is jq)."""
    name = re.split(r"[\\/]", word)[-1]
    if name.lower().endswith(".exe"):
        name = name[:-4]
    return name if name in PROGRAMS else None


PY_RUN = (re.compile(r"subprocess\.\w+\(\s*\[\s*[rbu]?[\"']([^\"']+)[\"']"),
          re.compile(r"subprocess\.\w+\(\s*[rbuf]?[\"']([^\"']+)[\"']"),
          re.compile(r"os\.(?:system|popen)\(\s*[rbuf]?[\"']([^\"']+)[\"']"),
          re.compile(r"shutil\.which\(\s*[\"']([^\"']+)[\"']"))
JS_RUN = re.compile(r"\b(?:execSync|execFileSync|execFile|exec|spawnSync|spawn)\(\s*[\"'`]([^\"'`]+)[\"'`]")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})\s*([\w+-]*)")
SPAN = re.compile(r"`([^`\n]+)`")


def _script_uses(rel, text):
    ext = _ext(rel)
    for n, line in enumerate(_lines(text), start=1):
        words = []
        if is_shell(rel, text):
            words = first_words(line)
        elif ext == "py":
            words = [w for rx in PY_RUN for m in rx.finditer(line) for w in first_words(m.group(1))[:1]]
        elif ext in ("js", "mjs", "cjs", "ts"):
            words = [w for m in JS_RUN.finditer(line) for w in first_words(m.group(1))[:1]]
        elif ext in WINDOWS_SCRIPTS:
            words = first_words(line)
        for w in words:
            yield n, w


def _instruction_uses(text):
    """Command words in a Markdown file: shell fences at command position, and inline code that
    starts with a known program and a space."""
    fence = None
    for n, line in enumerate(_lines(text), start=1):
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0][0] and len(m.group(1)) >= len(fence[0]):
                fence = None
            elif fence[1] in SHELL_FENCES:
                for w in first_words(line):
                    yield n, w
            continue
        if m:
            fence = (m.group(1), m.group(2).lower())
            continue
        for s in SPAN.findall(line):
            parts = s.strip().split()
            if len(parts) > 1 and program(parts[0]):
                yield n, parts[0]


# ------------------------------------------------------------------ what the repository declares

INSTALL = re.compile(r"\b(?:pip3?|pipx|uv(?:\s+pip)?|npm|pnpm|yarn|bun|brew|apt-get|apt|dnf|yum|pacman|"
                     r"winget|choco|scoop|cargo|go|gem)\s+(?:install|add|i)\b([^\n`]*)")
TOKEN = re.compile(r"[A-Za-z0-9@][A-Za-z0-9._+/@-]*")


def _name(spec: str) -> str | None:
    """A package or program name from a dependency spec: no version, extras, or URL path."""
    s = spec.strip().strip("\"'")
    if not s or s.startswith(("-", "#")):
        return None
    if s.startswith("@") and "/" in s:
        scope, rest = s.split("/", 1)
        return norm(scope + "/" + re.split(r"[@=<>!~ \[;]", rest)[0])
    s = s.rstrip("/").rsplit("/", 1)[-1] if "/" in s and not s.startswith("@") else s
    m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", s)
    return norm(m.group(0)) if m else None


def _pyproject(text) -> list[str]:
    doc = tomllib.loads(text)
    proj, poetry = doc.get("project", {}), doc.get("tool", {}).get("poetry", {})
    specs = list(proj.get("dependencies", []))
    for v in proj.get("optional-dependencies", {}).values():
        specs += v
    for v in doc.get("dependency-groups", {}).values():
        specs += [x for x in v if isinstance(x, str)]
    specs += [k for k in poetry.get("dependencies", {}) if k.lower() != "python"]
    for g in poetry.get("group", {}).values():
        specs += list(g.get("dependencies", {}))
    return specs


def declarations(texts: dict, compat: dict) -> dict[str, list[dict]]:
    """{normalized name: [{file, how}]} for every program and package the repository declares."""
    out: dict[str, list[dict]] = {}

    def add(spec, rel, how):
        n = _name(spec)
        if n:
            out.setdefault(n, [])
            if {"file": rel, "how": how} not in out[n]:
                out[n].append({"file": rel, "how": how})

    for rel, text in texts.items():
        if text is None or is_test_data(rel):
            continue
        base = rel.rsplit("/", 1)[-1].lower()
        try:
            if base.startswith("requirements") and base.endswith(".txt"):
                for line in _lines(text):
                    add(line.split("#")[0], rel, "requirements")
            elif base == "pyproject.toml":
                for s in _pyproject(text):
                    add(s, rel, "pyproject.toml")
            elif base == "pipfile":
                doc = tomllib.loads(text)
                for k in list(doc.get("packages", {})) + list(doc.get("dev-packages", {})):
                    add(k, rel, "Pipfile")
            elif base == "setup.py":
                for block in re.findall(r"install_requires\s*=\s*\[(.*?)\]", text, re.S):
                    for s in re.findall(r"[\"']([^\"']+)[\"']", block):
                        add(s, rel, "setup.py")
            elif base == "package.json":
                doc = json.loads(text)
                for k in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
                    for s in (doc.get(k) or {}):
                        add(s, rel, "package.json")
        except (ValueError, tomllib.TOMLDecodeError, AttributeError):
            pass
        if _ext(rel) == "py":
            m = re.search(r"^# /// script\s*$(.*?)^# ///\s*$", text, re.S | re.M)
            if m:
                for s in re.findall(r"[\"']([^\"']+)[\"']", m.group(1)):
                    add(s, rel, "inline script metadata")
        if base.startswith(("readme", "install")) or base == "skill.md":
            for m in INSTALL.finditer(text):
                for t in TOKEN.findall(m.group(1)):
                    add(t, rel, "install line")
    for rel, value in compat.items():
        if not is_test_data(rel):
            for t in TOKEN.findall(str(value)):
                add(t, rel, "compatibility")
    return out


def _declared(name, decl):
    n = norm(name)
    return decl.get(n) or decl.get(norm(FAMILY.get(name, name))) or []


# ------------------------------------------------------------------ packages imported

PY_IMPORT = re.compile(r"^\s*import\s+([\w.]+(?:\s*,\s*[\w.]+)*)")
PY_FROM = re.compile(r"^\s*from\s+([\w.]+)\s+import\b")
JS_IMPORT = (re.compile(r"\brequire\(\s*[\"']([^\"']+)[\"']\s*\)"),
             re.compile(r"^\s*import\s+(?:[^\"';]+\s+from\s+)?[\"']([^\"']+)[\"']"),
             re.compile(r"\bimport\(\s*[\"']([^\"']+)[\"']\s*\)"))


def _modules(files: set) -> set[str]:
    """The Python modules the repository holds anywhere: every `x.py`, and every folder of `.py`
    files (a script may reach another folder's module through sys.path; Walkdown's own do)."""
    out = set()
    for f in files:
        if f.endswith(".py"):
            parts = f.split("/")
            out.add(parts[-1][:-3])
            out.update(parts[:-1])
    return out


def packages(texts, files) -> dict[tuple[str, str], list[str]]:
    """{(ecosystem, package): files that import it}."""
    out: dict[tuple, list] = {}
    local = _modules(files)
    for rel, text in sorted(texts.items()):
        if text is None or is_test_data(rel):
            continue
        ext = _ext(rel)
        names = []
        if ext == "py":
            for line in _lines(text):
                m = PY_IMPORT.match(line)
                if m:
                    names += [x.strip().split(".")[0] for x in m.group(1).split(",")]
                m = PY_FROM.match(line)
                if m and not m.group(1).startswith("."):
                    names.append(m.group(1).split(".")[0])
            for name in names:
                if name and name not in STDLIB and name not in local:
                    out.setdefault(("python", PACKAGE_NAMES.get(name, name)), []).append(rel)
        elif ext in ("js", "mjs", "cjs", "ts", "tsx", "jsx"):
            for rx in JS_IMPORT:
                for line in _lines(text):
                    for m in rx.finditer(line):
                        s = m.group(1)
                        # relative, built in, or a path alias (~/lib, #lib, @/lib), never a package
                        if s.startswith((".", "/", "node:", "~", "#", "$", "@/")):
                            continue
                        pkg = "/".join(s.split("/")[:2]) if s.startswith("@") else s.split("/")[0]
                        if pkg not in NODE_BUILTINS:
                            out.setdefault(("node", pkg), []).append(rel)
    return {k: sorted(set(v)) for k, v in out.items()}


# ------------------------------------------------------------------ what ties it to one machine

PERSONAL = (("windows", re.compile(r"\b[A-Za-z]:[\\/]+Users[\\/]+([^\\/\s\"'<>`]+)", re.I)),
            ("macos", re.compile(r"(?<![\w.])/Users/([^/\s\"'<>`]+)/")),
            ("linux", re.compile(r"(?<![\w.])/home/([^/\s\"'<>`]+)/")))
BACKSLASH = re.compile(r"(?<![\w\\/:.%$])((?:[\w.-]+\\)+[\w.-]+\.\w+)")
RUN_PREFIX = re.compile(r"^(?:\./|\$\{?CLAUDE_(?:PLUGIN_ROOT|PROJECT_DIR)\}?/)")


def _personal(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][\w.-]*", name)) and name.lower() not in NOT_PERSONAL


def compatibility(texts: dict) -> dict[str, str]:
    """{file: its frontmatter `compatibility` value} for Markdown files that have one."""
    out = {}
    for rel, text in texts.items():
        if text and rel.lower().endswith(MARKDOWN) and text.startswith("---"):
            head = text.split("\n---", 1)[0][3:]
            try:
                doc = yaml.safe_load(head)
            except yaml.YAMLError:
                continue
            if isinstance(doc, dict) and doc.get("compatibility"):
                out[rel] = str(doc["compatibility"])
    return out


def findings(texts: dict, file_rows: list, hook_rows: list, mcp_rows: list, compat: dict) -> list[dict]:
    files = {r["file"] for r in file_rows if r.get("file")}
    rows = {r["file"]: r for r in file_rows if r.get("file")}
    decl = declarations(texts, compat)
    uses: list[dict] = []  # {command (program), word, file, line, how}

    def use(word, rel, line, how):
        uses.append({"word": word, "program": program(word), "file": rel, "line": line, "how": how})

    for rel, text in sorted(texts.items()):
        if text is None or is_test_data(rel):
            continue
        if _ext(rel) in SCRIPT_EXTS or is_shell(rel, text) or _ext(rel) in WINDOWS_SCRIPTS:
            for n, w in _script_uses(rel, text):
                use(w, rel, n, "script")
        elif rel.lower().endswith(MARKDOWN) and audience(rel) in ("model", "subagent"):
            for n, w in _instruction_uses(text):
                use(w, rel, n, "instructions")
    for h in hook_rows:
        if not is_test_data(h.get("file") or ""):
            for w in first_words(str(h.get("command") or "")):
                use(w, h.get("file"), h.get("line"), "hook")
    for m in mcp_rows:
        if not is_test_data(m.get("file") or "") and m.get("command"):
            for w in first_words(str(m["command"]))[:1]:
                use(w, m.get("file"), m.get("line"), "mcp")

    out = []
    by_prog: dict[str, list] = {}
    for u in uses:
        if u["program"]:
            by_prog.setdefault(u["program"], []).append({k: u[k] for k in ("file", "line", "how")})
    for p in sorted(by_prog):
        d = _declared(p, decl)
        out.append({"check": "need.command", "file": None, "line": None, "command": p, "os": PROGRAMS[p],
                    "uses": by_prog[p], "declared": bool(d), "declared_in": d})
    for (eco, pkg), where in sorted(packages(texts, files).items()):
        d = _declared(pkg, decl)
        out.append({"check": "need.package", "file": None, "line": None, "package": pkg, "ecosystem": eco,
                    "files": where, "declared": bool(d), "declared_in": d})

    port = []
    for rel, text in sorted(texts.items()):
        if text is None or is_test_data(rel):
            continue
        # only where it runs or the AI reads it: a path in notes for people ties nothing to a machine
        for n, line in enumerate(_lines(text) if audience(rel) != "human" else [], start=1):
            for kind, rx in PERSONAL:
                m = rx.search(line)
                if m and _personal(m.group(1)):
                    port.append({"check": "port.path", "file": rel, "line": n, "kind": kind, "quote": line.strip()})
                    break
        if rel.lower().endswith(MARKDOWN) and audience(rel) in ("model", "subagent"):
            base = rel.rsplit("/", 1)[0] + "/" if "/" in rel else ""
            for n, line in enumerate(_lines(text), start=1):
                for m in BACKSLASH.finditer(line):
                    p = m.group(1).replace("\\", "/")
                    if p in files or base + p in files:
                        port.append({"check": "port.backslash", "file": rel, "line": n, "written": m.group(1),
                                     "file_named": p if p in files else base + p})
        r = rows.get(rel, {})
        if is_shell(rel, text):
            port.append({"check": "port.os", "file": rel, "line": None, "os": "unix", "why": "a shell script"})
            committed = r.get("eol_committed")
            if committed in ("crlf", "mixed") or (committed is None and "\r\n" in text):
                port.append({"check": "port.crlf", "file": rel, "line": None})
        elif _ext(rel) in WINDOWS_SCRIPTS:
            port.append({"check": "port.os", "file": rel, "line": None, "os": "windows",
                         "why": "a PowerShell script" if _ext(rel).startswith("ps") else "a batch script"})
    for u in uses:
        os_ = PROGRAMS.get(u["program"]) if u["program"] else None
        if os_:
            port.append({"check": "port.os", "file": u["file"], "line": u["line"], "os": os_,
                         "why": f"runs {u['program']}", "command": u["program"]})
        if u["program"] == "python" and u["how"] in ("instructions", "hook"):
            port.append({"check": "port.python", "file": u["file"], "line": u["line"]})
        if not u["program"] and u["how"] in ("instructions", "hook"):
            target = RUN_PREFIX.sub("", u["word"])
            f = rows.get(target)
            if f and f.get("exec_source") == "git-index" and not f.get("exec") and (
                    _ext(target) in SCRIPT_EXTS or is_shell(target, texts.get(target))):
                port.append({"check": "port.exec", "file": u["file"], "line": u["line"], "script": target})
    port.sort(key=lambda f: (f["check"], f["file"] or "", f["line"] or 0))
    return out + port
