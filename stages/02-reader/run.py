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
import render_html  # noqa: E402
import read_image  # noqa: E402
import read_md  # noqa: E402
import read_pdf  # noqa: E402
import read_svg  # noqa: E402
import language  # noqa: E402
import render_pdf  # noqa: E402
import script_runs  # noqa: E402

STAGE = "02-reader"
ORDER = {"read.unread": 0, "read.divergence": 1, "read.fold": 2, "read.script": 3,
         "read.language": 4, "read.metadata": 5}
TEXT_KINDS = {"markdown", "html", "svg", "text"}
# "text" files the language check reads as prose; code and config are not prose (LANGUAGE_NOTE)
PROSE_EXTS = {"txt", "text", "rst", "adoc", "asciidoc"}
UNREAD_REASON = {"office-other": "unsupported format (XLSX / PPTX / legacy Office not read in v1)",
                 "archive": "archive (contents not extracted)",
                 "binary": "binary blob (does not decode as text)"}


def eprint(*a):
    print(*a, file=sys.stderr)


def optional_tools() -> dict:
    ocr_ok, ocr_why = read_image.ocr_available()
    html_ok, html_why = render_html.available()
    return {"tesseract": ocr_ok, "tesseract_detail": ocr_why,
            "playwright": html_ok, "playwright_detail": html_why}


# Checks the method calls for that have no code yet (2026-10-12, an outside audit): stage 2
# once looked for pdf2image, Playwright, and lingua and called each missing tool the reason, but
# nothing here uses them, so installing one would have hidden the gap. Reported as not built,
# always, apart from a missing tool, until the code exists. Built and left this list
# (2026-10-18): language within Latin script (language.py, no dependency) and PDF render + OCR
# (render_pdf.py: pypdfium2, a core dependency; the OCR needs Tesseract, a skip without it).
# HTML render left it 2026-10-20 (render_html.py: Playwright, optional, a skip without it).
NOT_BUILT: list[tuple[str, str]] = []
LANGUAGE_NOTE = ("v1 limit: the language check (read.language) reads prose only: Markdown, plain "
                 "text, PDF, DOCX, and OCR text; Markdown code blocks, comments in code, config "
                 "values, and HTML are not checked for language, and a paragraph under five words "
                 "is too short to judge")


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


def language_checks(rel, lines, markdown, state, line_based=True):
    """read.language over one file's prose; counts paragraphs judged and too short."""
    st = language.stats(lines, markdown)
    state["language_files"] += 1
    state["language_judged"] += st["judged"]
    state["language_short"] += st["short"]
    return language.language_findings(rel, lines, markdown, line_based=line_based)


def pdf_pages(rel, data, lines, tools, state):
    """Draw each page and read it (render_pdf): OCR lines missing from the text layer are B-only
    image-text divergences, appended to the lines so the line checks and --out see them. Returns
    (findings, lines, no_layer_unread)."""
    has_layer = any(ln.strip() for ln in lines)
    if not tools["tesseract"]:
        why = tools["tesseract_detail"]
        state["pdf_pages"] += render_pdf.page_ocr(data, ocr=False).total
        return ([{"check": "read.divergence", "file": rel, "line": None, "carrier": "image-text",
                  "skipped": f"pdf pages not drawn and read ({why})"}],
                lines, None if has_layer else f"pdf has no text layer; OCR not run ({why})")
    po = render_pdf.page_ocr(data)
    state["pdf_pages"] += po.total
    state["pdf_pages_read"] += len(po.pages)
    state["pdf_low_confidence"] += sum(len(b) for low in po.low
                                       for b in render_pdf.unseen(low, lines))
    out, lines = [], list(lines)
    for page_no, text in enumerate(po.pages, start=1):
        for block in render_pdf.unseen(text, lines):
            if lines and lines[-1] != "":
                lines.append("")
            out.append(div(rel, None, "\n".join(block), "image-text", method="ocr",
                           reading="B-only", page=page_no, text_line=len(lines) + 1))
            lines.extend(block)
    if po.skipped:
        out.append({"check": "read.divergence", "file": rel, "line": None, "carrier": "image-text",
                    "skipped": f"pdf pages not drawn and read ({po.skipped})"})
    elif po.total > len(po.pages):
        out.append({"check": "read.divergence", "file": rel, "line": None, "carrier": "image-text",
                    "skipped": f"pdf pages {len(po.pages) + 1} to {po.total} not drawn and read "
                               f"(the first {render_pdf.MAX_PAGES} are)"})
    no_layer = None
    if not has_layer and (po.skipped or not po.pages):
        no_layer = f"pdf has no text layer; OCR not run ({po.skipped or 'no page read'})"
    return out, lines, no_layer


def html_drawn(rel, text, static, tools, state, session):
    """The page as a browser draws it (render_html): text a person never sees, and text only the
    style sheet shows, beyond what static style found. A skip naming carrier `rendered` when
    Playwright is missing, the run is past MAX_FILES, or the page fails to load."""
    state["html_files"] += 1

    def skip(why):
        return [{"check": "read.divergence", "file": rel, "line": None, "carrier": "rendered",
                 "skipped": f"html not drawn ({why})"}]
    if not tools.get("playwright") or session is None:
        return skip(tools.get("playwright_detail") or "playwright not installed")
    if state["html_files"] > render_html.MAX_FILES:
        return skip(f"the first {render_html.MAX_FILES} are")
    try:
        probe = session.render(rel)
    except render_html.RenderError as exc:
        return skip(str(exc))
    state["html_drawn"] += 1
    out = []
    for d in render_html.divergences(probe, text, [s["text"] for s in static]):
        extra = {"pseudo": d["pseudo"]} if "pseudo" in d else {}
        out.append(div(rel, d["line"], d["text"], "rendered", method="render", reading=d["reading"],
                       how=d["how"], **extra))
    return out


def read_one(rel, data, kind, tools, state, session=None):
    """Findings for one file, and (text_lines, folded_lines) or None. `session`: the
    render_html.Session HTML files are drawn in (None: not drawn, a skip)."""
    out = []
    if kind in TEXT_KINDS:
        text, _enc = files.decode(data)
        lines = files.split_lines(text)
        fs, folded = line_checks(rel, lines)
        for i, raw in enumerate(lines, start=1):
            f = fold.invisible_finding(rel, i, raw)
            if f:
                out.append(f)
        if kind == "markdown" or (kind == "text" and files.ext_of(rel) in PROSE_EXTS):
            fs += language_checks(rel, lines, kind == "markdown", state)
        if kind == "markdown":
            state["markdown_files"] += 1
            for c in read_md.carriers(text):
                extra = {"used": c["used"]} if "used" in c else {}
                out.append(div(rel, c["line"], c["text"], c["carrier"], **extra))
                if c["carrier"] == "comment":
                    state["markdown_comments"] += 1
        elif kind == "html":
            static = read_html.read_html(text)["divergences"]
            for d in static:
                out.append(div(rel, d["line"], d["text"], d["carrier"]))
            out += html_drawn(rel, text, static, tools, state, session)
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
        lines, no_layer = r.lines, None
        for d in r.divergences:
            extra = {k: v for k, v in d.items() if k not in ("text", "carrier")}
            out.append(div(rel, None, d["text"], d["carrier"], **extra))
        if kind == "pdf":
            page_fs, lines, no_layer = pdf_pages(rel, data, r.lines, tools, state)
            out += page_fs
        fs, folded = line_checks(rel, lines, line_based=False)
        fs += language_checks(rel, lines, False, state, line_based=False)
        if no_layer:
            out.insert(0, unread(rel, no_layer))
        meta = [{"check": "read.metadata", "file": rel, "line": None, **m} for m in r.metadata]
        return out + fs + meta, (lines, folded)

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
            fs += language_checks(rel, ocr_lines, False, state, line_based=False)
            return out + fs + meta, (ocr_lines, folded)
        out.append(unread(rel, f"image: no text layer; OCR not run ({r.ocr_skipped})"))
        skip = {"check": "read.divergence", "file": rel, "line": None, "skipped": r.ocr_skipped}
        return out + meta + [skip], None

    return [unread(rel, UNREAD_REASON.get(kind, kind))], None


def build_report(input_dir: Path, out_dir: Path | None = None) -> dict:
    tools = optional_tools()
    if not tools["tesseract"]:
        eprint(f"note: {tools['tesseract_detail']}: images and PDF pages are skipped for OCR "
               "(read.divergence skip); images and PDFs with no text layer are listed as "
               "read.unread")
    if not tools.get("playwright"):
        eprint(f"note: html render: {tools.get('playwright_detail') or 'playwright not installed'}: "
               "HTML files are read with static style only (read.divergence skip, carrier rendered)")
    for what, covers in NOT_BUILT:
        eprint(f"note: not built: {what}: {covers}")
    eprint(f"note: {LANGUAGE_NOTE}")

    state = Counter()
    findings, normalized = [], {}
    total_bytes = read_bytes = read_files = 0
    unread_list = []
    entries = files.list_files(input_dir)
    root = Path(input_dir).resolve()
    # one browser for the run's HTML files, started at the first one (render_html, 2026-10-20)
    session = render_html.Session(root) if tools.get("playwright") else None
    try:
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
                fs, texts = read_one(e.rel, data, kind, tools, state, session)
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
    finally:
        if session is not None:
            session.close()

    carriers = Counter(f["carrier"] for f in findings
                       if f["check"] == "read.divergence" and "carrier" in f)
    not_examined = []
    if not tools["tesseract"]:
        not_examined.append("image and PDF page OCR (tesseract not installed)")
    if not tools.get("playwright"):
        not_examined.append(f"HTML as a browser draws it ({tools.get('playwright_detail') or 'playwright not installed'})")
    not_examined += [f"{what} (not built)" for what, _ in NOT_BUILT]
    coverage = {
        "files": len(entries), "files_read": read_files,
        "bytes": total_bytes, "bytes_read": read_bytes,
        "unread": unread_list,
        "carriers": dict(sorted(carriers.items())),
        "markdown_files": state["markdown_files"],
        "markdown_comments": state["markdown_comments"],
        "language": {"files": state["language_files"], "judged": state["language_judged"],
                     "short": state["language_short"]},
        "pdf_pages": {"total": state["pdf_pages"], "read": state["pdf_pages_read"],
                      "low_confidence": state["pdf_low_confidence"]},
        "html": {"files": state["html_files"], "drawn": state["html_drawn"]},
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
