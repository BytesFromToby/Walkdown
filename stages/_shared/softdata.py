"""Load and check softreads.yaml, everything the AI stages show a model. Spec: specs/shared.SPEC.md, softdata.

The Sweep stage (03-sweep) shows a model the sweep question, and a model that takes text the system text that goes with it;
the Pinpoint stage (04-pinpoint) shows one the pinpoint question and the sweep option's own words. Both read the one file
through here.
"""
from __future__ import annotations

from pathlib import Path

import yaml

import library

DEFAULT = library.path("softreads.yaml")


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

    wait = doc.get("retry_wait")
    if not isinstance(wait, (int, float)) or isinstance(wait, bool) or not 0 <= wait <= 60:
        raise DataError("retry_wait: must be a number of seconds from 0 to 60")

    sweep = doc.get("sweep")
    _need(sweep, "sweep", "question", "system")
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

    pin = doc.get("pinpoint")
    _need(pin, "pinpoint", "system", "question")

    return {
        "answer_cap": cap,
        "retry_wait": float(wait),
        "sweep": {
            "question": sweep["question"].strip(), "system": sweep["system"].strip(), "source": sweep["source"],
            "flag_p": float(sweep["flag_p"]),
            "options": {k: {"what": v["what"].strip(), "not_for": v["not_for"].strip(),
                            "examples": list(v["examples"]), "source": v["source"]}
                        for k, v in sopts.items()}},
        "pinpoint": {
            "system": pin["system"].strip(), "question": pin["question"].strip(),
            "source": pin["source"]},
    }
