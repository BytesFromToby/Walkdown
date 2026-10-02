"""Stage 4 runner: prints one contract-1 report. Spec: specs/run.SPEC.md.

    python stages/04-phrases/run.py <input_dir> [--inventory <file>] [--patterns <file>] [--out <dir>]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import conditionals  # noqa: E402
import endpoints  # noqa: E402
import rubric  # noqa: E402
import terms  # noqa: E402
from audience import audience  # noqa: E402
from foldtext import decode, fold_line, split_lines  # noqa: E402
from patterns import CHECKS, TableError, load_table  # noqa: E402
from scan import frontmatter_lines, scan_text  # noqa: E402
from vocab import KINDS, VocabError, load_vocab  # noqa: E402

STAGE = "04-phrases"
STAGE1_RUN = HERE.parent / "01-inventory" / "run.py"

LIMITS = [
    "limit: stage 4 is not complete: position and repetition (REPORTING 4.4, 4.5) "
    "and the gitleaks secret scan are not built",
    "limit: files that do not decode as text (PDF, DOCX, images) are not scanned",
]
MARKDOWN_EXTS = (".md", ".markdown", ".mdc")
INSTRUCTION_AUDIENCES = ("model", "subagent")
PART2_ORDER = ["rubric.action", "endpoint.host", "cond.branch", "term.def", "term.conflict",
               "term.safety"]



PATTERN_LISTS = {".gitignore", ".gitattributes", ".npmignore", ".dockerignore", ".prettierignore",
                 ".eslintignore", "codeowners", ".gitmodules", ".mailmap"}

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


def instruction_lines(rel: str, aud: str, lines: list[str]) -> set[int]:
    """Instruction text: every line of a model or subagent file, plus the frontmatter
    of any markdown file (frontmatter is loaded). CONTEXT-part2 "Shared rules"."""
    if aud in INSTRUCTION_AUDIENCES:
        return set(range(1, len(lines) + 1))
    if rel.lower().endswith(MARKDOWN_EXTS):
        return frontmatter_lines(lines)
    return set()


def part2_counts(p2: list[dict]) -> dict:
    rb = [f for f in p2 if f["check"] == "rubric.action"]
    eps = [f for f in p2 if f["check"] == "endpoint.host"]
    cond = [f for f in p2 if f["check"] == "cond.branch"]
    defs = [f for f in p2 if f["check"] == "term.def"]
    by_kind = {k: 0 for k in KINDS}
    for f in cond:
        by_kind[f["kind"]] += 1
    by_source = {k: 0 for k in terms.SOURCES}
    for f in defs:
        by_source[f["source"]] += 1
    return {
        "rubric": {"rows": len(rb),
                   "with_confirmation": sum(1 for f in rb if f["confirmation"]),
                   "without_confirmation": sum(1 for f in rb if not f["confirmation"]),
                   "negated_confirmation": sum(1 for f in rb if f["negated_confirmation"]),
                   "by_tier": {t: sum(1 for f in rb if f["tier"] == t)
                               for t in ("prohibited", "confirm-first")}},
        "endpoints": endpoints.summary(eps),
        "conditionals": {"rows": len(cond), "by_kind": by_kind},
        "terms": {"definitions": len(defs), "by_source": by_source,
                  "conflicts": sum(1 for f in p2 if f["check"] == "term.conflict"),
                  "safety": sum(1 for f in p2 if f["check"] == "term.safety")},
    }


def build_report(input_dir: Path, inv: dict, rows, vocab=None) -> tuple[dict, dict]:
    if vocab is None:
        vocab = load_vocab(rows=rows)
    findings_in = inv.get("findings", [])
    files = sorted((f for f in findings_in if f.get("check") == "inv.file"),
                   key=lambda r: r["file"])
    scripts: set[str] = set()
    for f in findings_in:
        if f.get("check") == "inv.pin":
            for paths in (f.get("script_languages") or {}).values():
                scripts.update(paths)
    hook_configs = {f["file"] for f in files if f.get("entry_point") == "hook-config"}
    hook_configs |= {f["file"] for f in findings_in
                     if f.get("check") == "struct.hooks" and f.get("file")}

    findings: list[dict] = []
    not_scanned: list[dict] = []
    scanned = 0
    rb, cond, defs, occ = [], [], [], []
    for row in files:
        rel = row["file"]
        if "skipped" in row:
            not_scanned.append({"file": rel, "reason": f"unreadable: {row['skipped']}"})
            continue
        if row.get("type") == "inode/symlink" or "target" in row:
            not_scanned.append({"file": rel, "reason": "symlink (never followed)"})
            continue
        if not row.get("encoding"):
            not_scanned.append({"file": rel, "reason": f"not text ({row.get('type') or 'binary'})"})
            continue
        if rel.rsplit("/", 1)[-1].lower() in PATTERN_LISTS:
            # lists of path patterns read by git and tools; nothing in them is followed or
            # executed, so phrase hits there are noise (2026-09-30, Plumbline .gitignore)
            not_scanned.append({"file": rel, "reason": "pattern list (not instruction text)"})
            continue
        try:
            data = (input_dir / rel).read_bytes()
        except OSError as exc:
            not_scanned.append({"file": rel, "reason": f"unreadable: {exc}"})
            continue
        text = decode(data)
        if text is None:
            not_scanned.append({"file": rel, "reason": "undecodable text"})
            continue
        scanned += 1
        aud = audience(rel, scripts, hook_configs)
        findings.extend(scan_text(rel, text, rows, aud))
        raw = split_lines(text)
        folded = [fold_line(x) for x in raw]
        instr = instruction_lines(rel, aud, raw)
        rb.extend(rubric.rubric_file(rel, raw, folded, instr, aud, rows, vocab))
        cond.extend(conditionals.cond_file(rel, raw, folded, instr, aud, vocab))
        defs.extend(terms.defs_file(rel, raw, folded, instr, aud, vocab))
        for n, line in enumerate(folded, start=1):
            where = "instructions" if n in instr else "docs" if aud == "human" else "code"
            for host in endpoints.hosts_in_line(line, vocab):
                occ.append((host, rel, n, where))

    per_check = {c: 0 for c in CHECKS}
    per_pattern = {r.id: 0 for r in rows}
    for f in findings:
        per_check[f["check"]] += 1
        for pid in f["patterns"]:
            per_pattern[pid] += 1
    p2 = (rb + endpoints.census(occ, vocab) + cond + defs + terms.conflicts(defs)
          + terms.safety(defs, vocab))
    p2.sort(key=lambda f: (PART2_ORDER.index(f["check"]), f["file"] or "", f["line"] or 0))
    findings = findings + p2
    report = {"stage": STAGE, "contract": 1, "findings": findings}
    hits = {"findings": findings,
            "counts": {"per_check": per_check, "per_pattern": per_pattern,
                       "part2": part2_counts(p2)},
            "scanned": scanned, "not_scanned": not_scanned, "limits": LIMITS}
    return report, hits


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
    ap.add_argument("--patterns")
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
        rows = load_table(args.patterns)
    except TableError as exc:
        eprint(f"error: pattern table: {exc}")
        return 2
    try:
        vocab = load_vocab(rows=rows)
    except VocabError as exc:
        eprint(f"error: vocab: {exc}")
        return 2
    try:
        inv = load_inventory(root, args.inventory)
    except ValueError as exc:
        eprint(f"error: {exc}")
        return 2
    except StageError as exc:
        eprint(f"error: {exc}")
        return 1

    report, hits = build_report(root, inv, rows, vocab)
    for note in LIMITS:
        eprint("note:", note)
    for ns in hits["not_scanned"]:
        eprint(f"note: not scanned: {ns['file']}: {ns['reason']}")
    c2 = hits["counts"]["part2"]
    eprint(f"note: {len(report['findings'])} finding(s) in {hits['scanned']} scanned file(s); "
           "every hit is a locator, never a verdict")
    eprint(f"note: part 2: rubric {c2['rubric']['rows']} "
           f"({c2['rubric']['with_confirmation']} with a confirmation step); "
           f"hosts {c2['endpoints']['hosts']} ({c2['endpoints']['undocumented']} undocumented, "
           f"{c2['endpoints']['local']} local); conditionals {c2['conditionals']['rows']}; "
           f"definitions {c2['terms']['definitions']} ({c2['terms']['conflicts']} conflicts, "
           f"{c2['terms']['safety']} safety)")
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "hits.json").write_text(json.dumps(hits, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
    out = json.dumps(report, ensure_ascii=False, indent=1)
    sys.stdout.buffer.write(out.encode("utf-8") + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
