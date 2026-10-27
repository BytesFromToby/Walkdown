"""Stage 3 runner: prints one contract-1 report. Spec: specs/run.SPEC.md.

    python stages/03-graph/run.py <input_dir> [--inventory <file>] [--out <dir>]
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import reach as reach_mod  # noqa: E402
from extract import ext_of, extract  # noqa: E402
from invisible import decode  # noqa: E402
from resolve import Resolver  # noqa: E402
from scans import find_scans  # noqa: E402
from unlisted import manifest_root, unlisted  # noqa: E402

STAGE = "03-graph"
STAGE1_RUN = HERE.parent / "01-inventory" / "run.py"

# Manifest versus disk is built both ways (2026-10-18): a path a manifest names that does not
# exist is graph.dangling, a component on disk its manifest leaves out is graph.unlisted.
LIMIT_NOTE = ("v1 limit: manifest versus disk compares skills, agents, and commands, and only "
              "the kinds a manifest names; a manifest that names none relies on its folders and "
              "is not compared, and plugins a marketplace leaves out are not compared")

DOC_EXTS = {"pdf", "doc", "docx", "docm", "xls", "xlsx", "xlsm", "ppt", "pptx", "pptm",
            "odt", "ods", "odp", "rtf", "epub"}
DOC_TYPES = ("application/pdf", "application/msword", "application/vnd.ms-",
             "application/vnd.openxmlformats", "application/vnd.oasis.opendocument",
             "application/rtf", "text/rtf", "application/epub")
ARCHIVE_EXTS = {"zip", "tar", "gz", "tgz", "bz2", "xz", "7z", "rar", "whl", "jar"}
ARCHIVE_TYPES = ("application/zip", "application/x-tar", "application/gzip",
                 "application/x-gzip", "application/x-bzip2", "application/x-xz",
                 "application/x-7z", "application/x-rar", "application/java-archive")
TEXT_EXTS = {"md", "markdown", "mdx", "txt", "rst", "json", "jsonc", "yaml", "yml", "toml",
             "html", "htm", "xml", "svg", "py", "js", "mjs", "cjs", "ts", "sh", "bash",
             "zsh", "ps1", "psm1", "rb", "pl", "css", "csv", "ini", "cfg"}



INSTRUCTION_KINDS = ("skill", "agent", "command")


def is_load(edge, entries) -> bool:
    """A dynamic edge a loader follows, as opposed to a folder or glob mention."""
    return (edge.get("context") == "config" or edge.get("form") == "scan"
            or (edge.get("source") == "glob" and entries.get(edge["from"]) in INSTRUCTION_KINDS))


def tier(edge) -> str:
    if edge["kind"] == "static":
        return "static"
    return "dynamic" if edge.get("load") else "mention"

def eprint(*a):
    print(*a, file=sys.stderr)


class StageError(Exception):
    pass


def load_inventory(input_dir: Path, inventory: str | None) -> dict:
    if inventory:
        try:
            return json.loads(Path(inventory).read_text("utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"cannot read --inventory {inventory}: {exc}")
    p = subprocess.run([sys.executable, str(STAGE1_RUN), str(input_dir)], capture_output=True)
    if p.returncode != 0:
        raise StageError(f"stage 1 failed (exit {p.returncode}): "
                         + p.stderr.decode("utf-8", "replace")[-2000:])
    try:
        return json.loads(p.stdout.decode("utf-8"))
    except ValueError as exc:
        raise StageError(f"stage 1 printed no valid report: {exc}")


def unscanned_reason(row: dict) -> str | None:
    if "skipped" in row:
        return f"unreadable: {row['skipped']}"
    if row.get("type") == "inode/symlink" or "target" in row:
        return None
    ext = (row.get("ext") or ext_of(row["file"])).lower()
    typ = (row.get("type") or "").lower()
    if ext in DOC_EXTS or typ.startswith(DOC_TYPES):
        return f"binary document ({row.get('type') or ext})"
    if ext in ARCHIVE_EXTS or typ.startswith(ARCHIVE_TYPES):
        return f"archive ({row.get('type') or ext})"
    return None


# Claude Code expands "@path" in CLAUDE.md at load (slice 1, 2026-10-26): written at the start of a
# line or after white space, outside code spans and fenced blocks.
_AT = re.compile(r"(?:^|(?<=\s))@([^\s`]+)")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_SPAN = re.compile(r"`+[^`]*`+")


def at_imports(text: str) -> set[tuple[int, str]]:
    """{(line, path as written after @)} for the @path imports in a file's text."""
    out, fence = set(), None
    for n, line in enumerate(text.split("\n"), start=1):
        m = _FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0]:
                fence = None
            continue
        if m:
            fence = m.group(1)
            continue
        for a in _AT.finditer(_SPAN.sub(" ", line)):
            out.add((n, a.group(1).rstrip(".,;:)")))
    return out


def build_report(input_dir: Path, inv: dict) -> tuple[dict, dict]:
    rows = [f for f in inv.get("findings", []) if f.get("check") == "inv.file"]
    nodes = sorted({r["file"] for r in rows})
    entries = {r["file"]: r["entry_point"] for r in rows if r.get("entry_point")}
    resolver = Resolver(nodes)

    edges: list[dict] = []
    dangling: dict[tuple, dict] = {}
    dynamic: dict[tuple, dict] = {}
    unscanned: list[dict] = []
    cases: list[dict] = []

    def add_edge(frm, line, to, kind, form, text, context, source=None, **flags):
        if frm == to:
            return
        e = {"from": frm, "line": line, "to": to, "kind": kind, "form": form, "text": text,
             "context": context}
        if source:
            e["source"] = source
        e.update({k: True for k, v in flags.items() if v})
        edges.append(e)

    def add_dynamic(rel, line, pattern, targets, source, form, text, context):
        key = (rel, line, pattern)
        if key not in dynamic:
            dynamic[key] = {"check": "graph.dynamic", "file": rel, "line": line,
                            "pattern": pattern, "resolves": sorted(targets), "source": source}
        for t in targets:
            add_edge(rel, line, t, "dynamic", form, text, context, source=source)

    for row in sorted(rows, key=lambda r: r["file"]):
        rel = row["file"]
        reason = unscanned_reason(row)
        if reason:
            unscanned.append({"check": "graph.unscanned", "file": rel, "line": None,
                              "reason": reason})
            continue
        if "target" in row or row.get("type") == "inode/symlink":
            continue  # a symlink is a node, never read
        try:
            data = (input_dir / rel).read_bytes()
        except OSError as exc:
            unscanned.append({"check": "graph.unscanned", "file": rel, "line": None,
                              "reason": f"unreadable: {exc}"})
            continue
        text = decode(data) if row.get("encoding") else None
        if text is None:
            if ext_of(rel) in TEXT_EXTS:
                unscanned.append({"check": "graph.unscanned", "file": rel, "line": None,
                                  "reason": "undecodable text"})
            continue

        # scans in code first, so a glob literal inside a scan call is one load
        for s in find_scans(rel, text):
            if s.literal:
                shape_glob = any(c in s.pattern for c in "*?[")
                if shape_glob:
                    targets = resolver.glob(os.path.dirname(rel).replace("\\", "/"),
                                            s.pattern)
                else:
                    r = resolver.resolve(rel, s.pattern.rstrip("/") + "/", "dir")
                    if r.status == "dir":
                        folder = r.pattern
                        targets = (resolver.under(folder) if s.recursive
                                   else resolver.children(folder))
                    else:
                        targets = []
            else:
                targets = []
            add_dynamic(rel, s.line, s.pattern, targets, "code", "scan", s.pattern, "code")

        # a manifest's paths are relative to its plugin root, the folder above .claude-plugin/
        # (2026-10-18: "./skills/" in plugins/p/.codex-plugin/plugin.json had resolved to the
        # repository's own skills/ folder)
        base = rel
        if entries.get(rel) == "manifest":
            base = posixpath.join(manifest_root(rel), posixpath.basename(rel))
        imports = at_imports(text) if entries.get(rel) == "project-instructions" else set()
        for f in extract(rel, text):
            ref = f.ref
            res = resolver.resolve(base, ref.path, ref.shape)
            if res.status == "file":
                for t in res.targets:
                    add_edge(rel, f.line, t, "static", f.form, ref.written, f.context,
                             ambiguous=res.ambiguous, case_mismatch=res.case_mismatch,
                             partial=res.partial, by_name=res.by_name,
                             at_import=(f.line, ref.written) in imports or (f.line, ref.path) in imports)
                    if res.case_mismatch and not res.ambiguous:  # works on Windows and macOS only (slice 2)
                        cases.append({"check": "graph.case", "file": rel, "line": f.line,
                                      "written": ref.written, "to": t})
            elif res.status in ("dir", "glob"):
                if (rel, f.line, ref.written) in dynamic or (rel, f.line, ref.path) in dynamic:
                    continue
                source = "glob" if res.status == "glob" else "directory"
                pattern = res.pattern if res.status == "dir" else ref.path
                add_dynamic(rel, f.line, pattern, res.targets, source, f.form, ref.written,
                            f.context)
            elif res.status == "missing" and ref.may_dangle:
                key = (rel, f.line, ref.written)
                if key not in dangling:
                    dangling[key] = {"check": "graph.dangling", "file": rel, "line": f.line,
                                     "target": ref.written, "context": f.context,
                                     "form": f.form,
                                     "folder_missing": resolver.folder_missing(base, ref.path)}

    # A dynamic edge is a load when a config or manifest names the folder, a
    # script scans it, or an instruction file (skill, agent, command) gives the
    # glob. Anything else is a mention: a folder or glob named in docs, plans,
    # READMEs, or instruction prose ("save plans in docs/plans/"). Mentions keep
    # a file reachable (never an orphan) but mark it via "mention" (2026-09-29).
    for e in edges:
        if e["kind"] == "dynamic":
            e["load"] = is_load(e, entries)
    loading = {(e["from"], e["line"]) for e in edges if e.get("load")}
    for d in dynamic.values():
        # a load with no targets today still loads whatever appears there later
        bare = {"from": d["file"], "source": d["source"],
                "form": "scan" if d["source"] == "code" else None}
        d["load"] = (d["file"], d["line"]) in loading or is_load(bare, entries)
    rc = reach_mod.reach(nodes, list(entries), [(e["from"], e["to"], tier(e)) for e in edges])

    entry_rows = [{"check": "graph.entry", "file": n, "line": None, "kind": entries[n]}
                  for n in sorted(entries)]
    dang_rows = sorted(dangling.values(), key=lambda d: (d["file"], d["line"], d["target"]))
    dyn_rows = sorted(dynamic.values(), key=lambda d: (d["file"], d["line"], d["pattern"]))
    unl_rows = unlisted([n for n, k in entries.items() if k == "manifest"], nodes, edges)
    findings = (entry_rows + reach_mod.orphan_findings(rc) + dang_rows + dyn_rows + unl_rows
                + reach_mod.depth_findings(rc) + unscanned + cases)
    report = {"stage": STAGE, "contract": 1, "findings": findings}

    graph = {
        "nodes": [{"path": n, "entry": entries.get(n), "depth": rc.depth.get(n)}
                  for n in nodes],
        "edges": sorted(edges, key=lambda e: (e["from"], e["line"], e["to"], e["kind"])),
        "complete": not dyn_rows,
        "limits": [LIMIT_NOTE],
    }
    return report, graph


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="run.py", add_help=True)
    ap.add_argument("input_dir")
    ap.add_argument("--inventory")
    ap.add_argument("--out")
    try:
        args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit:
        return 2
    target = Path(args.input_dir)
    if not target.is_dir():
        eprint(f"error: not a folder: {target}")
        return 2
    root = target.resolve()
    out_dir = None
    if args.out:
        out_dir = Path(args.out).resolve()
        if _inside(out_dir, root):
            eprint(f"error: --out {out_dir} is inside the input; refusing to write there")
            return 2
    try:
        inv = load_inventory(root, args.inventory)
    except ValueError as exc:
        eprint(f"error: {exc}")
        return 2
    except StageError as exc:
        eprint(f"error: {exc}")
        return 1

    report, graph = build_report(root, inv)
    eprint("note:", LIMIT_NOTE)
    n_dyn = sum(1 for f in report["findings"] if f["check"] == "graph.dynamic")
    if n_dyn:
        eprint(f"note: graph incomplete by construction: {n_dyn} dynamic load(s); "
               "targets resolved as of review time only")
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=1),
                                            encoding="utf-8")
    out = json.dumps(report, ensure_ascii=False, indent=1)
    sys.stdout.buffer.write(out.encode("utf-8") + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
