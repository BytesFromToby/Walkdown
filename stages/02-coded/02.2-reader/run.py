"""`02.2-reader` runner: prints one contract-1 report. Spec: specs/reader.SPEC.md, run.

    python stages/02-coded/02.2-reader/run.py <input_dir> [--out <dir>]
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))  # the note helper

import files  # noqa: E402
import fold  # noqa: E402
import read_docx  # noqa: E402
import read_html  # noqa: E402
import read_image  # noqa: E402
import read_md  # noqa: E402
import read_pdf  # noqa: E402
import read_svg  # noqa: E402
import language  # noqa: E402
import script_runs  # noqa: E402
import coverlines as cov  # noqa: E402
import stagenote  # noqa: E402

STAGE = "02.2-reader"
# What the step looked at (`stages/_shared/coverlines.py`). Every file is read by `read_one` or has a `read.unread`, and every file
# that is read has its lines folded and its script runs looked for; only a file with two readings (Markdown, HTML, SVG, a PDF,
# a DOCX) has a divergence between them to look for; only a PDF, a DOCX, or an image has metadata; and the language check
# judges the prose among the files. An image has one reading only since R35 (2026-11-11): the text drawn in it is not examined. A check counts the files in its scope where the kind of file is known, before the file
# is read (`cov.of`), and where it has handled each one (`cov.look`).
FILES, DIVERGENCE, METADATA, LANGUAGE = "read.unread", "read.divergence", "read.metadata", "read.language"
DIVERGENCE_KINDS = ("markdown", "html", "svg", "pdf", "docx")
LINES = [((FILES, "read.fold", "read.script"), "files"),
         ((DIVERGENCE,), "files"),
         ((METADATA,), "files"),
         ((LANGUAGE,), "files")]
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


# Checks the method calls for that have no code yet (2026-10-12, an outside audit). Empty since 2026-10-20.
NOT_BUILT: list[tuple[str, str]] = []
LANGUAGE_NOTE = ("v1 limit: the language check (read.language) reads prose only: Markdown, plain "
                 "text, PDF, and DOCX; Markdown code blocks, comments in code, config "
                 "values, and HTML are not checked for language, and a paragraph under five words "
                 "is too short to judge")
# What this reader does not examine, in the files a repository has (R35, R36; owner, 2026-11-11: "We state we do not
# examine images"; "go with option 1"). Walkdown installs with pip and nothing else: no OCR program, no browser. One note
# each, written only when the repository has such a file; the report shows them under What this run covered.
NOT_EXAMINED_IMAGES = "not examined: the text drawn inside images ({n}); their metadata is read"
NOT_EXAMINED_PDF = "not examined: the text on PDF pages that are only a picture ({n} with no text layer)"
NOT_EXAMINED_HTML = ("not examined: how a web page looks once drawn ({n}): one element drawn over another, clipping that "
                     "depends on where things land, text over a background image; the page's own styles are read")
PDF_NO_LAYER = "pdf: no text layer; the text on its pages is not examined"


def div(file, line, text, carrier, method="static-style", reading="A-only", **extra):
    return {"check": "read.divergence", "file": file, "line": line, "reading": reading,
            "text": text, "carrier": carrier, "method": method, **extra}


def unread(file, reason, **extra):
    return {"check": "read.unread", "file": file, "line": None, "reason": reason, **extra}


def reach(text, searched, line) -> int:
    """The last source line a hidden text reaches from its first (`line`): its words found in order. A word that cannot be
    found (tags between its letters glue it, a browser made it) leaves the reach unknown, so it is the last line of the file."""
    i, at = line - 1, 0
    for word in text.split():
        while i < len(searched) and (j := searched[i].find(word, at)) < 0:
            i, at = i + 1, 0
        if i == len(searched):
            return i
        at = j + len(word)
    return i + 1


def add_reach(found, lines) -> None:
    """`end_line` on each divergence whose text reaches past its first line. The mask of a line the secret scan flags needs the
    lines a text sits on (`stages/_shared/secretmask.py`); a parser's text has lost them, stripped or collapsed. A line is searched
    as written and with its entities decoded, since a Markdown comment keeps them and a parsed page does not."""
    searched = [f"{ln} {html.unescape(ln)}" if "&" in ln else ln for ln in lines]
    for f in found:
        if f.get("line") is not None and f.get("text"):
            end = reach(f["text"], searched, f["line"])
            if end > f["line"]:
                f["end_line"] = end


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
    cov.look(LANGUAGE)
    state["language_files"] += 1
    state["language_judged"] += st["judged"]
    state["language_short"] += st["short"]
    return language.language_findings(rel, lines, markdown, line_based=line_based)


def css_loader(root: Path, rel: str, state) -> callable:
    """The style sheets an HTML file links, read from the input folder (R36): a relative `href` from the file's folder, or
    one starting `/` from the folder's root. A URL with a scheme or a host, or a path that leaves the folder, gives None:
    nothing is fetched. Each sheet read is counted (`state["css_files"]`)."""
    base = (root / rel).parent

    def load(href: str) -> str | None:
        u = urlparse(href.strip())
        if u.scheme or u.netloc or not u.path:
            return None
        path = unquote(u.path)
        target = (root / path.lstrip("/")) if path.startswith("/") else (base / path)
        try:
            target = target.resolve()
            target.relative_to(root)
            if not target.is_file():
                return None
            data = target.read_bytes()[:read_html.CSS_CAP]
        except (OSError, ValueError):
            return None
        state["css_files"] += 1
        return files.decode(data)[0]
    return load


METADATA_KINDS = ("pdf", "docx", "image")


def prose_candidate(rel, kind) -> bool:
    """Whether the language check is to judge this file: Markdown, plain-text prose, and the text of a PDF or a DOCX
    (`read_one` runs it on exactly these)."""
    return kind in ("markdown", "pdf", "docx") or (kind == "text" and files.ext_of(rel) in PROSE_EXTS)


def read_one(rel, data, kind, state, root=None):
    """Findings for one file, and (text_lines, folded_lines) or None. `root`: the input folder, from which an HTML file's
    linked style sheets are read (None: inline styles and `<style>` only)."""
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
            state["html_files"] += 1
            load = css_loader(Path(root), rel, state) if root is not None else None
            for d in read_html.read_html(text, load)["divergences"]:
                extra = {k: d[k] for k in ("pseudo",) if k in d}
                out.append(div(rel, d["line"], d["text"], d["carrier"], reading=d.get("reading", "A-only"), **extra))
        elif kind == "svg":
            try:
                for d in read_svg.read_svg(data)["divergences"]:
                    out.append(div(rel, d["line"], d["text"], d["carrier"]))
            except read_svg.SvgError as exc:
                out.append({"check": "read.divergence", "file": rel, "line": None,
                            "skipped": f"svg is not well-formed XML: {exc}"[:300]})
        if kind in DIVERGENCE_KINDS:
            cov.look(DIVERGENCE)  # its two readings have been set against each other
            state["divergence_files"] += 1
        add_reach(out, lines)
        cov.look(FILES)
        return out + fs, (lines, folded)

    if kind in ("pdf", "docx"):
        r = read_pdf.read_pdf(data) if kind == "pdf" else read_docx.read_docx(data)
        if r.unread:
            return [unread(rel, r.unread)], None
        lines, no_layer = r.lines, None
        for d in r.divergences:
            extra = {k: v for k, v in d.items() if k not in ("text", "carrier")}
            out.append(div(rel, None, d["text"], d["carrier"], **extra))
        cov.look(DIVERGENCE)  # a PDF's or a DOCX's two readings have been set against each other
        state["divergence_files"] += 1
        if kind == "pdf" and not any(ln.strip() for ln in lines):
            no_layer = PDF_NO_LAYER  # the text on its pages is not examined (R35)
            state["pdf_no_layer"] += 1
        fs, folded = line_checks(rel, lines, line_based=False)
        fs += language_checks(rel, lines, False, state, line_based=False)
        if no_layer:
            out.insert(0, unread(rel, no_layer))  # a PDF with no text layer is listed as unread: the file is explained
        else:
            cov.look(FILES)
        meta = [{"check": "read.metadata", "file": rel, "line": None, **m} for m in r.metadata]
        cov.look(METADATA)
        state["metadata_files"] += 1
        return out + fs + meta, (lines, folded)

    if kind == "image":  # its metadata is read; the text drawn in it is not examined (R35), so it is listed as unread
        state["images"] += 1
        r = read_image.read_image(data)
        if r.unread:
            return [unread(rel, r.unread)], None
        meta = [{"check": "read.metadata", "file": rel, "line": None, **m} for m in r.metadata]
        cov.look(METADATA)
        state["metadata_files"] += 1
        return [unread(rel, read_image.NOT_EXAMINED)] + meta, None

    return [unread(rel, UNREAD_REASON.get(kind, kind))], None


def plural(k: int, one: str, many: str) -> str:
    return f"{k} {one if k == 1 else many}"


def build_report(input_dir: Path, out_dir: Path | None = None) -> dict:
    for what, covers in NOT_BUILT:
        stagenote.note(f"not built: {what}: {covers}")
    stagenote.note(f"{LANGUAGE_NOTE}")

    cov.begin(LINES)
    state = Counter()
    findings, normalized = [], {}
    total_bytes = read_bytes = read_files = 0
    unread_list = []
    entries = files.list_files(input_dir)
    cov.of(FILES, len(entries))  # every file is to be read, or listed as unread
    root = Path(input_dir).resolve()
    for e in entries:
        if e.kind == "symlink":
            fs = [unread(e.rel, "symlink, not followed", target=e.target)]
            findings.extend(fs)
            unread_list.append(e.rel)
            cov.explain(FILES)
            continue
        try:
            data = (root / e.rel).read_bytes()
        except OSError as exc:
            findings.append(unread(e.rel, f"could not read bytes: {exc}"))
            unread_list.append(e.rel)
            cov.explain(FILES)
            continue
        total_bytes += len(data)
        kind = files.classify(e.rel, data)
        prose = prose_candidate(e.rel, kind)
        if prose:
            cov.of(LANGUAGE)  # a file the language check is to judge, counted before the file is read
        has_meta = kind in METADATA_KINDS
        if has_meta:
            cov.of(METADATA)  # a PDF, a DOCX, or an image, whose metadata is to be read
        has_div = kind in DIVERGENCE_KINDS
        if has_div:
            cov.of(DIVERGENCE)  # a file with two readings, whose divergence is to be looked for
        judged_before, metadata_before = state["language_files"], state["metadata_files"]
        div_before = state["divergence_files"]
        try:
            fs, texts = read_one(e.rel, data, kind, state, root)
        except Exception as exc:  # a reader bug must not pass a file silently
            stagenote.warning(f"reader failed on {e.rel}: {type(exc).__name__}: {exc}")
            fs, texts = [unread(e.rel, f"reader error: {type(exc).__name__}: {exc}"[:300])], None
        fs.sort(key=lambda f: ((ORDER.get(f["check"], 9) if "skipped" not in f else 10), f.get("line") or 0))
        findings.extend(fs)
        if any(f["check"] == "read.unread" for f in fs):
            unread_list.append(e.rel)
            cov.explain(FILES)
            if prose and state["language_files"] == judged_before:  # unread before the language check ran: its reason is the unread row
                cov.explain(LANGUAGE)
            if has_meta and state["metadata_files"] == metadata_before:  # unread before its metadata was read
                cov.explain(METADATA)
            if has_div and state["divergence_files"] == div_before:  # unread before its readings were set against each other
                cov.explain(DIVERGENCE)
        else:
            read_files += 1
            read_bytes += len(data)
        if texts is not None:
            normalized[e.rel] = texts

    carriers = Counter(f["carrier"] for f in findings
                       if f["check"] == "read.divergence" and "carrier" in f)
    not_examined = []
    if state["images"]:
        not_examined.append(NOT_EXAMINED_IMAGES.format(n=plural(state["images"], "image", "images")))
    if state["pdf_no_layer"]:
        not_examined.append(NOT_EXAMINED_PDF.format(n=plural(state["pdf_no_layer"], "PDF", "PDFs")))
    if state["html_files"]:
        not_examined.append(NOT_EXAMINED_HTML.format(n=plural(state["html_files"], "HTML file", "HTML files")))
    for line in not_examined:
        stagenote.note(line)
    not_examined += [f"{what} (not built)" for what, _ in NOT_BUILT]
    reading = {  # named `coverage` until M9 slice C, which gave that name to the lines of every step
        "files": len(entries), "files_read": read_files,
        "bytes": total_bytes, "bytes_read": read_bytes,
        "unread": unread_list,
        "carriers": dict(sorted(carriers.items())),
        "markdown_files": state["markdown_files"],
        "markdown_comments": state["markdown_comments"],
        "language": {"files": state["language_files"], "judged": state["language_judged"],
                     "short": state["language_short"]},
        "images": state["images"], "pdf_no_text_layer": state["pdf_no_layer"],
        "html": {"files": state["html_files"], "css_files": state["css_files"]},
        "not_examined": not_examined,
    }
    stagenote.note(f"read {read_files}/{len(entries)} files, {read_bytes}/{total_bytes} bytes; "
                   f"{len(unread_list)} unread; {state['markdown_comments']} HTML comments in "
                   f"{state['markdown_files']} markdown files")

    if out_dir is not None:
        write_normalized(out_dir, normalized)
    return {"stage": STAGE, "contract": 1, "findings": findings, "reading": reading, "coverage": cov.lines(findings)}


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
