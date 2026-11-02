"""`02.1-inventory` runner: prints one contract-1 report. Spec: specs/inventory.SPEC.md, run.

    python stages/02-coded/02.1-inventory/run.py <input_dir>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))  # the note helper

import census  # noqa: E402
import configs  # noqa: E402
import entrypoints  # noqa: E402
import frontmatter  # noqa: E402
import licenses  # noqa: E402
import walk  # noqa: E402
import coverlines as cov  # noqa: E402
import stagenote  # noqa: E402

STAGE = "02.1-inventory"
# What the step looked at (`stages/_shared/coverlines.py`): the pin once, and the files the walk lists through the checks that run
# on them (`inspect_entry`). A line holds the checks that read the same files: every entry has its facts and census flags (a
# symlink too); a JSON or YAML file with text is tried as a hook config, a manifest, and an MCP config; a license file, a file that
# can declare a license, and a Markdown file are read for a license; and a Markdown file with text can have a description and a
# tools list. Whether a file has text is known only once its bytes are read, so these three lines count their items after the pass,
# from the texts it kept before it ran the checks (`text_items`), and each check counts a file where it has handled it (`cov.look`,
# inside `structure` and `markdown_checks`). A file with no text (an image, a binary) is not one of their items; a file whose bytes
# cannot be read is, and its skip row explains it.
PIN, FILES, CONFIG, LICENSE, MARKDOWN = "inv.pin", "inv.file", "struct.hooks", "inv.license", "struct.description"
LINES = [((PIN,), "run"),
         ((FILES, "struct.census"), "files"),
         ((CONFIG, "struct.manifests", "struct.mcp"), "files"),
         ((LICENSE,), "files"),
         ((MARKDOWN, "struct.agent-tools"), "files")]

LANG_BY_EXT = {"sh": "bash", "bash": "bash", "zsh": "zsh", "fish": "fish",
               "js": "JavaScript", "mjs": "JavaScript", "cjs": "JavaScript",
               "ts": "TypeScript", "mts": "TypeScript", "cts": "TypeScript",
               "tsx": "TypeScript", "jsx": "JavaScript",
               "py": "Python", "rb": "Ruby", "pl": "Perl", "php": "PHP", "lua": "Lua",
               "ps1": "PowerShell", "psm1": "PowerShell", "cmd": "Batch", "bat": "Batch",
               "go": "Go", "rs": "Rust", "java": "Java", "kt": "Kotlin", "swift": "Swift",
               "c": "C", "cpp": "C++", "cs": "C#", "r": "R", "tcl": "Tcl", "awk": "awk"}
LANG_BY_INTERP = {"sh": "bash", "bash": "bash", "dash": "bash", "zsh": "zsh", "fish": "fish",
                  "node": "JavaScript", "deno": "TypeScript", "bun": "JavaScript",
                  "python": "Python", "ruby": "Ruby", "perl": "Perl", "php": "PHP",
                  "pwsh": "PowerShell", "lua": "Lua", "tsx": "TypeScript",
                  "ts-node": "TypeScript"}


def text_hashes(data: bytes, encoding) -> dict:
    """A text file's content hashed with every line ending as LF and as CRLF, so a checkout that
    only converted line endings is not counted as a change (2026-10-20). Byte-level, so only for
    encodings where a line ending is the bytes \\r\\n or \\n (not UTF-16 or UTF-32)."""
    if str(encoding or "").lower().replace("_", "-").startswith(("utf-16", "utf-32")):
        return {}
    lf = data.replace(b"\r\n", b"\n")
    return {"sha256_lf": hashlib.sha256(lf).hexdigest(),
            "sha256_crlf": hashlib.sha256(lf.replace(b"\n", b"\r\n")).hexdigest()}


def eprint(*a):
    print(*a, file=sys.stderr)


def shebang_language(text: str | None) -> str | None:
    if not text or not text.startswith("#!"):
        return None
    words = text.split("\n", 1)[0][2:].strip().split()
    if not words:
        return None
    interp = words[0].rsplit("/", 1)[-1]
    if interp == "env":
        rest = [w for w in words[1:] if not w.startswith("-")]
        if not rest:
            return None
        interp = rest[0]
    interp = re.sub(r"[\d.]+$", "", interp)
    return LANG_BY_INTERP.get(interp)


def channel_filters(root: Path, rels: set[str], texts: dict[str, str]) -> list[dict]:
    out = []
    for rel in sorted(rels):
        base = rel.rsplit("/", 1)[-1]
        if base == ".gitattributes" and "export-ignore" in (texts.get(rel) or ""):
            out.append({"file": rel, "kind": "gitattributes export-ignore"})
        elif base == ".npmignore":
            out.append({"file": rel, "kind": "npmignore"})
        elif base == "package.json":
            doc = configs.load(rel, texts.get(rel) or "")
            if isinstance(doc, dict) and "files" in doc:
                out.append({"file": rel, "kind": "package.json files"})
    return out


def markdown_name(rel: str) -> bool:
    """Whether a file's name says Markdown (the files that can have a description and a tools list), from its name alone."""
    return census.ext_of(rel) in frontmatter.MARKDOWN_EXTS


def reads_license(rel: str) -> bool:
    """Whether the license check reads a file of this name: by the name alone, or for a Markdown file's frontmatter."""
    return licenses.names_a_license(rel) or markdown_name(rel)


# The lines whose items are the files of a kind that have text: (line key, whether its checks read a file of this name).
TEXT_LINES = ((CONFIG, configs.parses), (LICENSE, reads_license), (MARKDOWN, markdown_name))


def text_items(texts: dict) -> None:
    """What the three lines of `TEXT_LINES` should have looked at, counted from the texts the pass kept before it ran the
    checks. Counted after the pass, so a check left out for a file still shows, however it was left out."""
    for key, reads in TEXT_LINES:
        cov.of(key, sum(1 for rel, text in texts.items() if text is not None and reads(rel)))


class Rows:
    """What the pass over the entries collects: the findings of each check, the file texts the later checks read, and the
    totals for the pin."""

    def __init__(self):
        self.file, self.census, self.desc, self.tools, self.hooks, self.mcp = [], [], [], [], [], []
        self.license = []
        self.manifests, self.texts = [], {}
        self.extensions: dict[str, int] = {}
        self.languages: dict[str, list[str]] = {}
        self.total_bytes = 0
        self.counted = 0


def markdown_checks(acc: Rows, rel: str, fm, has_tools: bool, entry_kind, counted: bool) -> None:
    """The description and the tools list of a Markdown file's frontmatter (`struct.description`, `struct.agent-tools`).
    `counted`: the file is a Markdown file with text, one of the items of the line of these two checks."""
    if fm is not None:
        d = frontmatter.description_finding(rel, fm)
        if d:
            acc.desc.append(d)
        if has_tools or entry_kind in ("agent", "command"):
            acc.tools.append(frontmatter.agent_tools_finding(
                rel, fm, entry_kind if entry_kind in ("agent", "command", "skill") else "agent"))
    elif entry_kind in ("agent", "command"):
        acc.tools.append({"check": "struct.agent-tools", "file": rel, "line": None,
                          "tools": None, "description": None, "field": None, "kind": entry_kind})
    if counted:
        cov.look(MARKDOWN)  # its frontmatter has been read, for a description and a tools list


def structure(acc: Rows, rel: str, text, doc, fm, is_hook: bool, is_man: bool) -> None:
    """A file tried as a hook config, a manifest, and an MCP config (`struct.hooks`, `struct.manifests`, `struct.mcp`), and
    read for a license (`inv.license`). Only a JSON or YAML file with text has a config to parse, and only a file with text has
    a license to read."""
    if is_hook:
        acc.hooks.extend(configs.hook_findings(rel, doc, text))
        acc.hooks.extend(configs.cursor_env_findings(rel, doc, text))
    acc.mcp.extend(configs.mcp_findings(rel, doc, text))
    if text is not None:
        if licenses.is_license_file(rel):
            acc.license.append(licenses.file_finding(rel, text))
        acc.license.extend(licenses.field_findings(rel, text, doc, fm))
    if is_man:
        acc.manifests.append((rel, doc["name"], configs.manifest_grants(doc)))
    if text is not None and configs.parses(rel):
        cov.look(CONFIG)  # parsed, and tried as a hook config, a manifest, and an MCP config
    if text is not None and reads_license(rel):
        cov.look(LICENSE)  # read for a license


def inspect_entry(w, e, acc: Rows) -> None:
    """One entry through every check that runs on a file: its facts and census flags (`inv.file`, `struct.census`), its
    frontmatter, tools, hooks, manifest, MCP servers, and license (`struct.*`, `inv.license`). The entry counts as looked at
    where all of those have run on it, and an entry whose bytes cannot be read as explained by its skip row."""
    if e.kind == "symlink":
        facts = census.symlink_facts(e.rel, e.target or "")
        flags = [census.symlink_flag(e.rel, e.target or "")]
        entry_kind = None
        digest = None
        eol = {}
    else:
        try:
            data = (w.root / e.rel).read_bytes()
        except OSError as exc:
            acc.file.append({"check": "inv.file", "file": e.rel, "line": None,
                             "skipped": f"unreadable: {exc}"})
            cov.explain(FILES)  # its skip row explains it on every line it is one of the items of
            for key, reads in TEXT_LINES:
                if reads(e.rel):
                    cov.of(key)
                    cov.explain(key)
            return
        facts = census.file_facts(e.rel, data, e.exec_bit)
        # per-file content hash, so two runs can tell exactly which files changed
        # (2026-10-04, version drift)
        digest = hashlib.sha256(data).hexdigest()
        eol = text_hashes(data, facts.encoding) if facts.text_value is not None else {}
        flags = census.census_flags(e.rel, facts)
        text = facts.text_value
        acc.texts[e.rel] = text

        fm = None
        if text is not None and facts.ext in frontmatter.MARKDOWN_EXTS:
            fm = frontmatter.parse(text)
        has_tools = bool(fm and frontmatter.tools_value(fm) is not None)

        doc = configs.load(e.rel, text) if text is not None else None
        is_hook = configs.is_hook_config(doc) or (configs.is_cursor_env(e.rel)
                                                  and isinstance(doc, dict))
        is_man = configs.is_manifest(e.rel, doc)
        entry_kind = entrypoints.classify(e.rel, is_symlink=False, has_tools=has_tools,
                                          is_hook_config=is_hook, is_manifest=is_man)
        if is_man and entry_kind == "ci":
            is_man = False

        md = text is not None and facts.ext in frontmatter.MARKDOWN_EXTS
        markdown_checks(acc, e.rel, fm, has_tools, entry_kind, md)
        structure(acc, e.rel, text, doc, fm, is_hook, is_man)

        lang = census_lang(facts.ext, text)
        if lang:
            acc.languages.setdefault(lang, []).append(e.rel)

    acc.counted += 1
    acc.total_bytes += facts.bytes
    acc.extensions[facts.ext] = acc.extensions.get(facts.ext, 0) + 1
    row = {"check": "inv.file", "file": e.rel, "line": None, "ext": facts.ext,
           "bytes": facts.bytes, "lines": facts.lines, "exec": facts.exec,
           "encoding": facts.encoding, "bom": facts.bom, "type": facts.type,
           "entry_point": entry_kind, "exec_source": e.exec_source, "sha256": digest, **eol}
    if e.eol_committed:
        row["eol_committed"] = e.eol_committed
    if e.kind == "symlink":
        row["target"] = e.target
    acc.file.append(row)
    acc.census.extend(flags)
    cov.look(FILES)


def build_report(input_dir: str | Path) -> dict:
    cov.begin(LINES)
    w = walk.walk(input_dir)
    for n in w.notes:
        stagenote.note(n)
    stagenote.note(f"magic-byte detector: {census.magic_backend()}"
                   + (" (python-magic unavailable; pure-python fallback)"
                      if census.magic_backend() != "python-magic" else ""))

    acc = Rows()
    cov.of(FILES, len(w.entries))  # every file the walk lists has its facts taken
    for e in w.entries:
        inspect_entry(w, e, acc)
    text_items(acc.texts)

    cov.of(PIN)
    pin = walk.pin_finding(w, files=acc.counted, bytes_total=acc.total_bytes)
    cov.look(PIN)
    pin.update(
        extensions=dict(sorted(acc.extensions.items(), key=lambda kv: (-kv[1], kv[0]))),
        script_languages=dict(sorted(acc.languages.items(), key=lambda kv: (-len(kv[1]), kv[0]))),
        magic_backend=census.magic_backend(),
        reader_window={"lines": census.READER_LINES, "bytes": census.READER_BYTES},
        long_line_limit=census.LONG_LINE,
        channel_filters=channel_filters(w.root, set(acc.texts), acc.texts),
        license_checked=True,
    )
    findings = ([pin] + acc.file + acc.census + acc.desc + acc.tools + acc.hooks
                + configs.manifest_findings(acc.manifests) + acc.mcp + acc.license)
    return {"stage": STAGE, "contract": 1, "findings": findings, "coverage": cov.lines(findings)}


def census_lang(ext: str, text: str | None) -> str | None:
    if ext in LANG_BY_EXT:
        return LANG_BY_EXT[ext]
    if ext == "":
        return shebang_language(text)
    return None


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        eprint("usage: run.py <input_dir>")
        return 2
    target = Path(argv[0])
    if not target.is_dir():
        eprint(f"error: not a folder: {target}")
        return 2
    report = build_report(target)
    out = json.dumps(report, ensure_ascii=False, indent=1)
    sys.stdout.buffer.write(out.encode("utf-8") + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
