"""Stage 1 runner: prints one contract-1 report. Spec: specs/run.SPEC.md.

    python stages/01-inventory/run.py <input_dir>
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import census  # noqa: E402
import configs  # noqa: E402
import entrypoints  # noqa: E402
import frontmatter  # noqa: E402
import walk  # noqa: E402

STAGE = "01-inventory"

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


def build_report(input_dir: str | Path) -> dict:
    w = walk.walk(input_dir)
    for n in w.notes:
        eprint("note:", n)
    eprint(f"note: magic-byte detector: {census.magic_backend()}"
           + (" (python-magic unavailable; pure-python fallback)"
              if census.magic_backend() != "python-magic" else ""))

    file_rows, census_rows, desc_rows, tool_rows, hook_rows, mcp_rows = [], [], [], [], [], []
    manifests, texts = [], {}
    extensions: dict[str, int] = {}
    languages: dict[str, list[str]] = {}
    total_bytes = 0
    counted = 0

    for e in w.entries:
        if e.kind == "symlink":
            facts = census.symlink_facts(e.rel, e.target or "")
            flags = [census.symlink_flag(e.rel, e.target or "")]
            entry_kind = None
            digest = None
        else:
            try:
                data = (w.root / e.rel).read_bytes()
            except OSError as exc:
                file_rows.append({"check": "inv.file", "file": e.rel, "line": None,
                                  "skipped": f"unreadable: {exc}"})
                continue
            facts = census.file_facts(e.rel, data, e.exec_bit)
            # per-file content hash, so two runs can tell exactly which files changed
            # (2026-10-04, version drift)
            digest = hashlib.sha256(data).hexdigest()
            flags = census.census_flags(e.rel, facts)
            text = facts.text_value
            texts[e.rel] = text

            fm = None
            if text is not None and facts.ext in frontmatter.MARKDOWN_EXTS:
                fm = frontmatter.parse(text)
            has_tools = bool(fm and frontmatter.tools_value(fm) is not None)

            doc = configs.load(e.rel, text) if text is not None else None
            is_hook = configs.is_hook_config(doc)
            is_man = configs.is_manifest(e.rel, doc)
            entry_kind = entrypoints.classify(e.rel, is_symlink=False, has_tools=has_tools,
                                              is_hook_config=is_hook, is_manifest=is_man)
            if is_man and entry_kind == "ci":
                is_man = False

            if fm is not None:
                d = frontmatter.description_finding(e.rel, fm)
                if d:
                    desc_rows.append(d)
                if has_tools or entry_kind in ("agent", "command"):
                    tool_rows.append(frontmatter.agent_tools_finding(
                        e.rel, fm, entry_kind if entry_kind in ("agent", "command", "skill")
                        else "agent"))
            elif entry_kind in ("agent", "command"):
                tool_rows.append({"check": "struct.agent-tools", "file": e.rel, "line": None,
                                  "tools": None, "description": None, "field": None,
                                  "kind": entry_kind})
            if is_hook:
                hook_rows.extend(configs.hook_findings(e.rel, doc))
            mcp_rows.extend(configs.mcp_findings(e.rel, doc))
            if is_man:
                manifests.append((e.rel, doc["name"], configs.manifest_grants(doc)))

            lang = census_lang(facts.ext, text)
            if lang:
                languages.setdefault(lang, []).append(e.rel)

        counted += 1
        total_bytes += facts.bytes
        extensions[facts.ext] = extensions.get(facts.ext, 0) + 1
        row = {"check": "inv.file", "file": e.rel, "line": None, "ext": facts.ext,
               "bytes": facts.bytes, "lines": facts.lines, "exec": facts.exec,
               "encoding": facts.encoding, "bom": facts.bom, "type": facts.type,
               "entry_point": entry_kind, "exec_source": e.exec_source, "sha256": digest}
        if e.kind == "symlink":
            row["target"] = e.target
        file_rows.append(row)
        census_rows.extend(flags)

    pin = walk.pin_finding(w, files=counted, bytes_total=total_bytes)
    pin.update(
        extensions=dict(sorted(extensions.items(), key=lambda kv: (-kv[1], kv[0]))),
        script_languages=dict(sorted(languages.items(), key=lambda kv: (-len(kv[1]), kv[0]))),
        magic_backend=census.magic_backend(),
        reader_window={"lines": census.READER_LINES, "bytes": census.READER_BYTES},
        long_line_limit=census.LONG_LINE,
        channel_filters=channel_filters(w.root, set(texts), texts),
    )
    findings = ([pin] + file_rows + census_rows + desc_rows + tool_rows + hook_rows
                + configs.manifest_findings(manifests) + mcp_rows)
    return {"stage": STAGE, "contract": 1, "findings": findings}


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
