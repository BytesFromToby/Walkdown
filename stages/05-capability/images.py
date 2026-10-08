"""Images a model is pointed at. Spec: specs/images.SPEC.md.

A model with vision reads the text in an image, instructions included, while a person skimming
the repository sees a picture (2026-10-07). An image reaches the model only when a file the
model reads points at it, so the signal is the reference, not the pixels: one cap.pair per image
a model-read file references directly or loads, with what stage 2 could read of its text. OCR
and model reads of the image itself are extra detail on top of this.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "04-phrases"))

from audience import audience  # noqa: E402

READ_BY_MODEL = ("model", "subagent")
IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "ico", "svg"}
# A manifest or settings file is read by the host, not shown to the model: its icon paths are
# for the UI (superpowers, caveman-main 2026-10-07).
CONFIG_EXTS = {"json", "jsonc", "yaml", "yml", "toml"}


def images(reports: dict) -> set[str]:
    """Image files stage 1 saw, by extension or detected content type."""
    out = set()
    for f in (reports.get("01") or {}).get("findings", []):
        if f.get("check") != "inv.file" or not f.get("file"):
            continue
        if (f.get("ext") or "").lower() in IMAGE_EXTS or (f.get("type") or "").startswith("image/"):
            out.add(f["file"])
    return out


def _references(reports: dict, graph: dict | None) -> list[tuple[str, str, int | None]]:
    """(source, target, line) for every reference a model would follow: a static reference or a
    load in text, never in a config file. A folder or glob only mentioned (`load: false`) is not
    followed. Without graph.json, stage 3's graph.depth static records stand in (one source per
    file)."""
    if graph is not None:
        return [(e["from"], e["to"], e.get("line")) for e in graph.get("edges", [])
                if (e.get("kind") == "static" or e.get("load")) and e.get("form") != "config"]
    return [(f.get("from"), f.get("file"), None)
            for f in (reports.get("03") or {}).get("findings", [])
            if f.get("check") == "graph.depth" and f.get("via") == "static" and "skipped" not in f]


def _read(reports: dict, image: str) -> tuple[str, str | None]:
    """What stage 2 got of the image's text: (read, reason)."""
    if image.lower().endswith(".svg"):
        return "svg", None
    found = [f for f in (reports.get("02") or {}).get("findings", []) if f.get("file") == image]
    for f in found:
        if f.get("check") == "read.unread":
            return "unread", f.get("reason")
    if any(f.get("check") == "read.divergence" and f.get("carrier") == "image-text" for f in found):
        return "ocr-text", None
    return "ocr-empty", None


def image_pairs(reports: dict, graph: dict | None = None) -> list[dict]:
    """cap.pair image+loaded: one per image that a model- or subagent-read file references
    directly or loads. `from` is the first such file, `froms` every one."""
    imgs = images(reports)
    froms: dict[str, list[tuple[str, int | None]]] = {}
    for src, dst, line in _references(reports, graph):
        if dst in imgs and src and src != dst and audience(src) in READ_BY_MODEL \
                and src.rsplit(".", 1)[-1].lower() not in CONFIG_EXTS:
            if (src, line) not in froms.setdefault(dst, []):
                froms[dst].append((src, line))
    out = []
    for img in sorted(froms):
        srcs = sorted(froms[img], key=lambda x: (x[0], x[1] or 0))
        read, reason = _read(reports, img)
        f = {"check": "cap.pair", "file": img, "line": None, "pair": "image+loaded",
             "from": srcs[0][0], "froms": sorted({s for s, _ in srcs}), "read": read,
             "evidence": [{"stage": "03", "check": "graph.edge", "file": s, "line": ln,
                           "why": f"references {img}"} for s, ln in srcs]}
        if reason:
            f["reason"] = reason
        out.append(f)
    return out
