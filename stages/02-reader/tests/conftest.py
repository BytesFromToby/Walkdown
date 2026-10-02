import io
import sys
import zipfile
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
if str(STAGE) not in sys.path:
    sys.path.insert(0, str(STAGE))


def make_pdf(content: str, info: dict | None = None) -> bytes:
    """A minimal one-page PDF (612 x 792) with Helvetica as /F1.

    `content` is the raw, uncompressed page content stream. `info` maps
    info-dictionary keys (without the slash) to literal string values.
    """
    stream = content.encode("latin-1")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Count 1 /Kids [3 0 R] >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    if info is not None:
        parts = []
        for k, v in info.items():
            esc = v.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            parts.append(f"/{k} ({esc})")
        objs.append(("<< " + " ".join(parts) + " >>").encode("latin-1"))
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n".encode())
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    trailer = f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R"
    if info is not None:
        trailer += f" /Info {len(objs)} 0 R"
    trailer += f" >>\nstartxref\n{xref}\n%%EOF\n"
    out.write(trailer.encode())
    return out.getvalue()


W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def make_docx(body: str, styles: str | None = None, core: str | None = None,
              background: str | None = None) -> bytes:
    """A minimal DOCX package. `body` is the inner XML of w:body."""
    bg = f'<w:background w:color="{background}"/>' if background else ""
    doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<w:document {W}>{bg}<w:body>{body}</w:body></w:document>')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/content-types"/>')
        z.writestr("word/document.xml", doc)
        if styles is not None:
            z.writestr("word/styles.xml",
                       f'<?xml version="1.0"?><w:styles {W}>{styles}</w:styles>')
        if core is not None:
            z.writestr("docProps/core.xml",
                       '<?xml version="1.0"?><cp:coreProperties '
                       'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/'
                       'core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">'
                       f'{core}</cp:coreProperties>')
    return buf.getvalue()
