"""Load and check softreads.yaml, everything stage 6 shows a model. Spec: specs/softdata.SPEC.md."""
from __future__ import annotations

from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT = HERE / "softreads.yaml"
LABELS = ("do", "not-to", "description", "example-or-quote", "other-sense")
RELATIONAL = ("term.safety", "term.conflict", "rubric.action", "hook+phrase", "legs")


class DataError(Exception):
    pass


def _text(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


def _need(entry, name: str, *fields: str) -> None:
    if not isinstance(entry, dict):
        raise DataError(f"{name}: not a mapping")
    for f in ("source",) + fields:
        if not _text(entry.get(f)):
            raise DataError(f"{name}: missing or empty {f!r}")


def load(path=DEFAULT) -> dict:
    p = Path(path)
    try:
        doc = yaml.safe_load(p.read_text("utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise DataError(f"cannot read {p}: {exc}")
    if not isinstance(doc, dict):
        raise DataError(f"{p}: not a mapping")

    cap = doc.get("answer_cap")
    if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
        raise DataError("answer_cap: must be a positive int")

    label = doc.get("label")
    _need(label, "label", "question")
    opts = label.get("options")
    if not isinstance(opts, dict) or list(opts) != list(LABELS):
        raise DataError(f"label.options: must be exactly {list(LABELS)} in order, got "
                        f"{list(opts) if isinstance(opts, dict) else opts!r}")
    for name, opt in opts.items():
        _need(opt, f"label.options.{name}", "what", "not_for")
        ex = opt.get("examples")
        if not isinstance(ex, list) or not ex or not all(_text(e) for e in ex):
            raise DataError(f"label.options.{name}: examples must be a non-empty list of text")

    note = label.get("marked_note")
    if note is not None and not _text(note):
        raise DataError("label.marked_note: must be text when given")

    rel = doc.get("relational")
    if not isinstance(rel, dict) or set(rel) != set(RELATIONAL):
        raise DataError(f"relational: must hold exactly {list(RELATIONAL)}, got "
                        f"{list(rel) if isinstance(rel, dict) else rel!r}")
    for key in RELATIONAL:
        _need(rel[key], f"relational.{key}", "question")

    sweep = doc.get("sweep")
    if sweep is not None:
        _need(sweep, "sweep", "question")
        fp = sweep.get("flag_p")
        if not isinstance(fp, (int, float)) or isinstance(fp, bool) or not 0 < fp < 1:
            raise DataError("sweep.flag_p: must be a number between 0 and 1")
        sopts = sweep.get("options")
        if not isinstance(sopts, dict) or list(sopts)[:1] != ["none"] or len(sopts) < 2:
            raise DataError("sweep.options: must start with `none` and name at least one kind")
        for name, opt in sopts.items():
            _need(opt, f"sweep.options.{name}", "what", "not_for")
            ex = opt.get("examples")
            if not isinstance(ex, list) or not ex or not all(_text(e) for e in ex):
                raise DataError(f"sweep.options.{name}: examples must be a non-empty list of text")

    sp = doc.get("claude_system_prompt")
    _need(sp, "claude_system_prompt", "text")

    return {
        "answer_cap": cap,
        "label": {"question": label["question"].strip(), "source": label["source"],
                  "marked_note": note.strip() if note else None,
                  "options": {k: {"what": v["what"].strip(), "not_for": v["not_for"].strip(),
                                  "examples": list(v["examples"]), "source": v["source"]}
                              for k, v in opts.items()}},
        "relational": {k: {"question": rel[k]["question"].strip(), "source": rel[k]["source"]}
                       for k in RELATIONAL},
        "claude_system_prompt": {"text": sp["text"].strip(), "source": sp["source"]},
        "sweep": None if sweep is None else {
            "question": sweep["question"].strip(), "source": sweep["source"],
            "flag_p": float(sweep["flag_p"]),
            "options": {k: {"what": v["what"].strip(), "not_for": v["not_for"].strip(),
                            "examples": list(v["examples"]), "source": v["source"]}
                        for k, v in sweep["options"].items()}},
    }
