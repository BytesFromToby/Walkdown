"""Stage 2 runner: prints one contract-1 report. Spec: specs/run.SPEC.md.

    python stages/02-reader/run.py <input_dir> [--out <dir>]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import files  # noqa: E402
import fold  # noqa: E402
import read_docx  # noqa: E402
import read_html  # noqa: E402
import read_image  # noqa: E402
import read_md  # noqa: E402
import read_pdf  # noqa: E402
import read_svg  # noqa: E402
import script_runs  # noqa: E402

STAGE = "02-reader"
ORDER = {"read.unread": 0, "read.divergence": 1, "read.fold": 2, "read.script": 3,
         "read.metadata": 4}
TEXT_KINDS = {"markdown", "html", "svg", "text"}
UNREAD_REASON = {"office-other": "unsupported format (XLSX / PPTX / legacy Office not read in v1)",
                 "archive": "archive (contents not extracted)",
                 "binary": "binary blob (does not decode as text)"}


def eprint(*a):
    print(*a, file=sys.stderr)


def _module_present(name: str) -> bool:
    try:
        __import__(name)
        return True
    except Exception:
        return False


def optional_tools() -> dict:
    ocr_ok, ocr_why = read_image.ocr_available()
    return {"tesseract": ocr_ok, "tesseract_detail": ocr_why,
            "pdf2image": _module_present("pdf2image"),
            "playwright": _module_present("playwright"),
            "lingua": _module_present("lingua")}


def div(file, line, text, carrier, method="static-style", reading="A-only", **extra):
    return {"check": "read.divergence", "file": file, "line": line, "reading": reading,
            "text": text, "carrier": carrier, "method": method, **extra}


def unread(file, reason, **extra):
    return {"check": "read.unread", "file": file, "line": None, "reason": reason, **extra}


def line_checks(rel, lines, line_based=True):
    """read.fold and read.script per line, plus the folded lines."""
    fs, folded = [], []
    for i, raw in enumerate(lines, start=1):
        line_no = i if line_based else None
        extra = {} if line_based else {"text_line": i}
        f = fold.fold_finding(rel, line_no, raw)
        folded.append(f["folded"] if f else raw)
        if f:
            f.update(extra)
            fs.append(f)
        for s in script_runs.script_findings(rel, line_no, raw):
            s.update(extra)
            fs.append(s)
    return fs, folded


def read_one(rel, data, kind, tools, state):
    """Findings for one file, and (text_lines, folded_lines) or None."""
    out = []
    if kind in TEXT_KINDS:
        text, _enc = files.decode(data)
        lines = files.split_lines(text)
        fs, folded = line_checks(rel, lines)
        for i, raw in enumerate(lines, start=1):
            f = fold.invisible_finding(rel, i, raw)
            if f:
                out.append(f)
        if kind == "markdown":
            state["markdown_files"] += 1
            for c in read_md.carriers(text):
                extra = {"used": c["used"]} if "used" in c else {}
                out.append(div(rel, c["line"], c["text"], c["carrier"], **extra))
                if c["carrier"] == "comment":
                    state["markdown_comments"] += 1
        elif kind == "html":
            for d in read_html.read_html(text)["divergences"]:
                out.append(div(rel, d["line"], d["text"], d["carrier"]))
        elif kind == "svg":
            try:
                for d in read_svg.read_svg(data)["divergences"]:
                    out.append(div(rel, d["line"], d["text"], d["carrier"]))
            except read_svg.SvgError as exc:
                out.append({"check": "read.divergence", "file": rel, "line": None,
                            "skipped": f"svg is not well-formed XML: {exc}"[:300]})
        return out + fs, (lines, folded)

    if kind in ("pdf", "docx"):
        r = read_pdf.read_pdf(data) if kind == "pdf" else read_docx.read_docx(data)
        if r.unread:
            return [unread(rel, r.unread)], None
        fs, folded = line_checks(rel, r.lines, line_based=False)
        for d in r.divergences:
            extra = {k: v for k, v in d.items() if k not in ("text", "carrier")}
            out.append(div(rel, None, d["text"], d["carrier"], **extra))
        if kind == "pdf" and not any(ln.strip() for ln in r.lines) and not tools["tesseract"]:
            out.insert(0, unread(rel, "pdf has no text layer; OCR of the rendered page needs "
                                      "poppler + tesseract (not installed)"))
        meta = [{"check": "read.metadata", "file": rel, "line": None, **m} for m in r.metadata]
        return out + fs + meta, (r.lines, folded)

    if kind == "image":
        r = read_image.read_image(data)
        if r.unread:
            return [unread(rel, r.unread)], None
        meta = [{"check": "read.metadata", "file": rel, "line": None, **m} for m in r.metadata]
        if r.ocr_text is not None:
            ocr_lines = files.split_lines(r.ocr_text.strip())
            if r.ocr_text.strip():
                out.append(div(rel, None, r.ocr_text.strip(), "image-text", method="ocr",
                               reading="B-only"))
            fs, folded = line_checks(rel, ocr_lines, line_based=False)
            return out + fs + meta, (ocr_lines, folded)
        out.append(unread(rel, f"image: no text layer; OCR not run ({r.ocr_skipped})"))
        skip = {"check": "read.divergence", "file": rel, "line": None, "skipped": r.ocr_skipped}
        return out + meta + [skip], None

    return [unread(rel, UNREAD_REASON.get(kind, kind))], None


def build_report(input_dir: Path, out_dir: Path | None = None) -> dict:
    tools = optional_tools()
    if not tools["tesseract"]:
        eprint(f"note: {tools['tesseract_detail']}: images are skipped for OCR "
               "(read.divergence skip) and listed as read.unread")
    if not (tools["pdf2image"] and tools["tesseract"]):
        eprint("note: poppler/pdf2image + tesseract absent: PDF reading B is static "
               "(color, render mode, page box); text painted but missing from the text "
               "layer (image-only content) is not examined")
    if not tools["playwright"]:
        eprint("note: playwright absent: HTML reading B uses static style "
               "(inline and <style> rules), not a true render")
    if not tools["lingua"]:
        eprint("note: lingua absent: language detection within Latin script not done "
               "(read.script covers non-Latin scripts only)")

    state = Counter()
    findings, normalized = [], {}
    total_bytes = read_bytes = read_files = 0
    unread_list = []
    entries = files.list_files(input_dir)
    root = Path(input_dir).resolve()
    for e in entries:
        if e.kind == "symlink":
            fs = [unread(e.rel, "symlink, not followed", target=e.target)]
            findings.extend(fs)
            unread_list.append(e.rel)
            continue
        try:
            data = (root / e.rel).read_bytes()
        except OSError as exc:
            findings.append(unread(e.rel, f"could not read bytes: {exc}"))
            unread_list.append(e.rel)
            continue
        total_bytes += len(data)
        kind = files.classify(e.rel, data)
        try:
            fs, texts = read_one(e.rel, data, kind, tools, state)
        except Exception as exc:  # a reader bug must not pass a file silently
            eprint(f"warning: reader failed on {e.rel}: {type(exc).__name__}: {exc}")
            fs, texts = [unread(e.rel, f"reader error: {type(exc).__name__}: {exc}"[:300])], None
        fs.sort(key=lambda f: ((ORDER.get(f["check"], 9) if "skipped" not in f else 10), f.get("line") or 0))
        findings.extend(fs)
        if any(f["check"] == "read.unread" for f in fs):
            unread_list.append(e.rel)
        else:
            read_files += 1
            read_bytes += len(data)
        if texts is not None:
            normalized[e.rel] = texts

    carriers = Counter(f["carrier"] for f in findings
                       if f["check"] == "read.divergence" and "carrier" in f)
    not_examined = []
    if not tools["tesseract"]:
        not_examined.append("image OCR (tesseract)")
    if not (tools["pdf2image"] and tools["tesseract"]):
        not_examined.append("PDF render + OCR: image-only text in PDFs")
    if not tools["playwright"]:
        not_examined.append("HTML true render (static style used)")
    if not tools["lingua"]:
        not_examined.append("language detection within Latin script (lingua)")
    coverage = {
        "files": len(entries), "files_read": read_files,
        "bytes": total_bytes, "bytes_read": read_bytes,
        "unread": unread_list,
        "carriers": dict(sorted(carriers.items())),
        "markdown_files": state["markdown_files"],
        "markdown_comments": state["markdown_comments"],
        "optional_tools": {k: v for k, v in tools.items() if not k.endswith("_detail")},
        "not_examined": not_examined,
    }
    eprint(f"note: read {read_files}/{len(entries)} files, {read_bytes}/{total_bytes} bytes; "
           f"{len(unread_list)} unread; {state['markdown_comments']} HTML comments in "
           f"{state['markdown_files']} markdown files")

    if out_dir is not None:
        write_normalized(out_dir, normalized)
    return {"stage": STAGE, "contract": 1, "findings": findings, "coverage": coverage}


def write_normalized(out_dir: Path, normalized: dict) -> None:
    base = Path(out_dir) / "normalized"
    for rel, (lines, folded) in normalized.items():
        for sub, content in (("text", lines), ("folded", folded)):
            p = base / sub / (rel + ".txt")
            p.parent.mkdir(parents=True, exist_ok=True)
            body = "".join(ln + "\n" for ln in content)
            p.write_bytes(body.encode("utf-8", "surrogatepass"))


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="run.py", add_help=True)
    ap.add_argument("input_dir")
    ap.add_argument("--out", default=None)
    try:
        args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit:
        return 2
    target = Path(args.input_dir)
    if not target.is_dir():
        eprint(f"error: not a folder: {target}")
        return 2
    out_dir = Path(args.out) if args.out else None
    if out_dir is not None and _inside(out_dir, target):
        eprint(f"error: --out {out_dir} is inside the input folder; refusing to write there")
        return 2
    report = build_report(target, out_dir)
    data = json.dumps(report, ensure_ascii=False, indent=1)
    sys.stdout.buffer.write(data.encode("utf-8", "surrogatepass") + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
