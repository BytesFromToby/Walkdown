"""`02.4-phrases` runner: prints one contract-1 report. Spec: specs/phrases.SPEC.md, run.

    python stages/02-coded/02.4-phrases/run.py <input_dir> [--inventory <file>] [--patterns <file>] [--out <dir>]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "_shared"))  # the audience rule, reading text, the secret mask

import earlier_steps  # noqa: E402
import position  # noqa: E402
import secret_scan  # noqa: E402
import stagelist  # noqa: E402
import endpoints  # noqa: E402
import restrictions  # noqa: E402
import rubric  # noqa: E402
import terms  # noqa: E402
import termset  # noqa: E402
import readtext  # noqa: E402
from audience import audience, inventory_sets  # noqa: E402
from foldtext import fold_line  # noqa: E402
from patterns import CHECKS, TableError, load_table  # noqa: E402
from readtext import split_lines  # noqa: E402
from secretmask import SECRET_MASK, mask_secret_lines  # noqa: E402,F401  (SECRET_MASK: tests read it here)
from scan import frontmatter_lines, scan_text  # noqa: E402
from vocab import VocabError, load_vocab  # noqa: E402
import stagenote  # noqa: E402
import coverlines as cov  # noqa: E402

STAGE = "02.4-phrases"
# What the step looked at (`stages/_shared/coverlines.py`): the phrase table over every file (`phrase_scan`); the checks that read
# each text file for more (`text_checks`: rubric, terms, limit settings, hosts); where hits sit in a file (`position.density`) and
# which sentences repeat across files (`position.repetition`), each counting the files it goes through; and the secret scan
# (`secret_scan.scan`, which counts its own files). `of` for the checks that read text is counted before the loop, from the
# inventory (`readtext.text_candidate`) and each check's own scope: every text file for the phrase table, the hosts, the terms,
# and the limit settings; the files with instruction lines for the rubric (`reads_rubric`); the files a model reads for the
# position checks (`position.reads_density`, `position.reads_repetition`). A file the loop cannot read (unreadable, undecodable) is
# explained where its "not scanned" entry is written, on the lines it is in scope of, and a file the loop leaves out any other
# way leaves a line short.
PHRASES, RUBRIC, TEXT, DENSITY, REPEAT, SECRET = ("phrase.K.exfil", "rubric.action", "endpoint.host", "pos.density",
                                                   "rep.sentence", "secret.found")
CONFLICT, SAFETY = terms.CONFLICT, terms.SAFETY
LINES = [((*CHECKS, ), "files"),
         ((RUBRIC,), "files"),  # the instruction lines of a file: those of a model's file and the frontmatter of Markdown
         ((TEXT, "term.def", "limit.setting"), "files"),  # every line of every text file
         ((CONFLICT,), "entries"),  # the definitions the text checks found, set against each other and the safety words
         ((SAFETY,), "entries"),
         ((DENSITY,), "files"),
         ((REPEAT,), "files"),
         ((SECRET,), "files")]

LIMITS = [
    "limit: files that do not decode as text (PDF, DOCX, images) are not scanned",
]
EXTRACTED_LIMIT = ("limit: files that do not decode as text (PDF, DOCX, images) are scanned from the "
                   f"text extracted by the step \"{stagelist.PLAIN['02.2-reader']}\", phrase patterns only")
MARKDOWN_EXTS = (".md", ".markdown", ".mdc")
INSTRUCTION_AUDIENCES = ("model", "subagent")
PART2_ORDER = ["rubric.action", "endpoint.host", "term.def", "term.conflict",
               "term.safety", "pos.density", "rep.sentence", "secret.found", "limit.setting"]


def eprint(*a):
    print(*a, file=sys.stderr)


def reads_rubric(rel: str, aud: str) -> bool:
    """Whether a file can have instruction lines: a model's file has all of its lines, a Markdown file its frontmatter, and test
    data and every other file none (`instruction_lines`). Used for a file whose text could not be read, where the lines cannot be
    looked for; a file that was read is one of the items of `rubric.action` when it has instruction lines."""
    return aud in INSTRUCTION_AUDIENCES or (aud != "test-data" and rel.lower().endswith(MARKDOWN_EXTS))


def instruction_lines(rel: str, aud: str, lines: list[str]) -> set[int]:
    """Instruction text: every line of a model or subagent file, plus the frontmatter
    of any markdown file (frontmatter is loaded).
    Spec: specs/phrases.SPEC.md, The stage (part 2, "Shared rules")."""
    if aud in INSTRUCTION_AUDIENCES:
        return set(range(1, len(lines) + 1))
    if aud == "test-data":  # never loaded as instructions, frontmatter included (2026-10-02)
        return set()
    if rel.lower().endswith(MARKDOWN_EXTS):
        return frontmatter_lines(lines)
    return set()


def part2_counts(p2: list[dict]) -> dict:
    rb = [f for f in p2 if f["check"] == "rubric.action"]
    eps = [f for f in p2 if f["check"] == "endpoint.host"]
    defs = [f for f in p2 if f["check"] == "term.def"]
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
        "terms": {"definitions": len(defs), "by_source": by_source,
                  "conflicts": sum(1 for f in p2 if f["check"] == "term.conflict"),
                  "safety": sum(1 for f in p2 if f["check"] == "term.safety")},
    }


def phrase_scan(rel, text, rows, aud, undone=None) -> list[dict]:
    """The phrase table over one file's text (`scan_text`): the check that makes the phrase findings. The file counts as looked
    at here, where its text is scanned."""
    cov.look(PHRASES)
    return scan_text(rel, text, rows, aud, undone)


def text_checks(rel, raw, folded, instr, aud, rows, vocab, lookalike):
    """The checks that read one text file for more than a phrase: the rubric of what a step asks (`rubric.action`), the
    definitions of terms, the settings that limit tools, and the hosts it names. Returns (rubric rows, definitions, limit
    settings, host occurrences). The file counts as looked at once all four have run on it."""
    rb = rubric.rubric_file(rel, raw, folded, instr, aud, rows, vocab)
    if instr:
        cov.look(RUBRIC)  # the file's instruction lines have been read for what a step asks
    defs = terms.defs_file(rel, raw, folded, instr, aud, vocab)
    lims = restrictions.limit_file(rel, raw, folded, aud)  # review C32
    occ = []
    for n, line in enumerate(folded, start=1):
        where = "instructions" if n in instr else "docs" if aud == "human" else "code"
        look = endpoints.lookalikes(raw[n - 1])  # review C42: never listed as the real host
        for host, addr in endpoints.addresses_in_line(line, vocab):
            if host in look:
                lookalike[look[host]] = host
                host, addr = look[host], re.sub(re.escape(host), look[host], addr, count=1, flags=re.I)
            occ.append((host, rel, n, where, addr))
    cov.look(TEXT)
    return rb, defs, lims, occ


def extracted_findings(rel, text, rows, aud) -> list[dict]:
    """Phrase hits in `02.2-reader`'s text of a binary file: cited by text_line, never by line."""
    out = []
    for f in phrase_scan(rel, text, rows, aud):
        f["text_line"] = f.pop("line")
        f["line"] = None
        if "end_line" in f:
            f["end_text_line"] = f.pop("end_line")
        f["extracted"] = True
        out.append(f)
    return out


def build_report(input_dir: Path, inv: dict, rows, vocab=None,
                 normalized: Path | None = None) -> tuple[dict, dict]:
    cov.begin(LINES)
    if vocab is None:
        vocab = load_vocab(rows=rows)
    findings_in = inv.get("findings", [])
    files, scripts, hook_configs = inventory_sets(findings_in)
    cov.of(PHRASES, len(files))  # every file the inventory lists is to be scanned, or listed as not scanned
    candidates = [r for r in files if readtext.text_candidate(r)]  # the files to be read as text, from the inventory alone
    pattern_lists = [r["file"] for r in files if readtext.pattern_list(r)]  # no other check reads these, and a key in one is still a key
    scannable = secret_scan.scannable([r["file"] for r in candidates] + pattern_lists)  # less lock files, which the secret scan leaves out
    cov.of(TEXT, len(candidates))
    auds = {r["file"]: audience(r["file"], scripts, hook_configs) for r in candidates}
    cov.of(DENSITY, sum(1 for rel, aud in auds.items() if position.reads_density(aud)))  # the files a model reads
    cov.of(REPEAT, sum(1 for rel, aud in auds.items() if position.reads_repetition(aud, rel)))  # and that are prose
    cov.of(SECRET, len(scannable))

    findings: list[dict] = []
    not_scanned: list[dict] = []
    scanned = 0
    rb, defs, occ, lims = [], [], [], []
    lookalike: dict[str, str] = {}  # name as written -> the host it imitates (review C42)
    undone: list[dict] = []  # line hits the next line cancelled (C37 follow-up)
    texts: dict[str, tuple] = {}  # rel -> (audience, raw lines, bytes): position and repetition
    for row in files:
        rel = row["file"]
        got = readtext.read_row(input_dir, row)  # the rules the builder step reads text by too
        if got.binary:
            copy = normalized / "text" / f"{rel}.txt" if normalized is not None else None
            if copy is not None and copy.is_file():  # `02.2-reader`'s text of a PDF, DOCX, or image
                scanned += 1
                findings.extend(extracted_findings(rel, copy.read_text("utf-8", "replace"), rows,
                                                   audience(rel, scripts, hook_configs)))
                continue
        if got.text is None:
            not_scanned.append({"file": rel, "reason": got.why})
            cov.explain(PHRASES)
            if readtext.text_candidate(row):  # unreadable, or bytes that do not decode: its "not scanned" entry says why
                cov.explain(TEXT)
                if reads_rubric(rel, auds[rel]):  # no text to find instruction lines in: it could have had them
                    cov.of(RUBRIC)
                    cov.explain(RUBRIC)
                if position.reads_density(auds[rel]):
                    cov.explain(DENSITY)
                if position.reads_repetition(auds[rel], rel):
                    cov.explain(REPEAT)
                if rel in scannable:
                    cov.explain(SECRET)
            continue
        text = got.text
        scanned += 1
        aud = audience(rel, scripts, hook_configs)
        findings.extend(phrase_scan(rel, text, rows, aud, undone))
        raw = split_lines(text)
        texts[rel] = (aud, raw, got.size)
        folded = [fold_line(x) for x in raw]
        instr = instruction_lines(rel, aud, raw)
        if instr:
            cov.of(RUBRIC)  # the file has instruction lines: it is to be read for what a step asks (known once its text is in hand)
        got_rb, got_defs, got_lims, got_occ = text_checks(rel, raw, folded, instr, aud, rows, vocab, lookalike)
        rb.extend(got_rb)
        defs.extend(got_defs)
        lims.extend(got_lims)
        occ.extend(got_occ)

    per_check = {c: 0 for c in CHECKS}
    per_pattern = {r.id: 0 for r in rows}
    for f in findings:
        per_check[f["check"]] += 1
        for pid in f["patterns"]:
            per_pattern[pid] += 1
    secret_files = {rel: t[0] for rel, t in texts.items()} | {rel: audience(rel, scripts, hook_configs) for rel in pattern_lists}
    cov.of(CONFLICT, len(defs))  # every definition found in the files above
    cov.of(SAFETY, len(defs))
    p2 = (rb + endpoints.census(occ, vocab, lookalike) + defs + terms.conflicts(defs)
          + terms.safety(defs, vocab)
          + position.density(texts, findings) + position.repetition(texts, findings)
          + secret_scan.scan(input_dir, secret_files) + lims)
    p2.sort(key=lambda f: (PART2_ORDER.index(f["check"]), f["file"] or "", f["line"] or 0))
    # what it needs, what it triggers on, what it asks for, and how clean it is are the builder
    # step's (02.6-builder, restructure step 4); it masks its own quotes by the same rule
    mask_secret_lines(findings + p2)
    findings = findings + p2
    # the search terms and matching code this report came from (review C22 b, 2026-10-19)
    report = {"stage": STAGE, "contract": 1, "terms": termset.describe(rows), "findings": findings,
              "coverage": cov.lines(findings), "secret_left_out": sorted(r["file"] for r in candidates if r["file"] not in scannable)}
    hits = {"findings": findings,
            "counts": {"per_check": per_check, "per_pattern": per_pattern,
                       "part2": part2_counts(p2)},
            "scanned": scanned, "not_scanned": not_scanned, "undone_by_next_line": undone,
            "limits": [EXTRACTED_LIMIT] if normalized is not None else LIMITS}
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
    ap.add_argument("--normalized")
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
        inv = earlier_steps.inventory(STAGE, root, args.inventory)
    except ValueError as exc:
        eprint(f"error: {exc}")
        return 2
    except earlier_steps.StepFailed as exc:
        eprint(f"error: {exc}")
        return 1

    normalized = Path(args.normalized).resolve() if args.normalized else None
    if normalized is not None and not normalized.is_dir():
        normalized = None  # `02.2-reader` did not run (baserates runs `02.1-inventory` and `02.4-phrases` only)
    report, hits = build_report(root, inv, rows, vocab, normalized)
    for note in hits["limits"]:
        stagenote.note(note)
    for ns in hits["not_scanned"]:
        stagenote.note(f"not scanned: {ns['file']}: {ns['reason']}")
    c2 = hits["counts"]["part2"]
    stagenote.note(f"{len(report['findings'])} finding(s) in {hits['scanned']} scanned file(s); "
                   "every hit is a locator, never a verdict")
    stagenote.note(f"part 2: rubric {c2['rubric']['rows']} "
                   f"({c2['rubric']['with_confirmation']} with a confirmation step); "
                   f"hosts {c2['endpoints']['hosts']} ({c2['endpoints']['undocumented']} undocumented, "
                   f"{c2['endpoints']['local']} local); "
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
