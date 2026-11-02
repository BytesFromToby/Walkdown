"""Load the `02.4-phrases` part 2 word lists. Spec: specs/phrases.SPEC.md, vocab."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_shared"))
import library  # noqa: E402

DEFAULT_VOCAB = library.path("vocab.yaml")
TIERS = {"prohibited", "confirm-first"}
FLAGS = re.IGNORECASE


class VocabError(ValueError):
    pass


@dataclass
class Vocab:
    tiers: dict = field(default_factory=dict)
    ignore_unless_tier: str = "confirm-first"
    confirm: list = field(default_factory=list)
    neg_before: re.Pattern = None
    neg_after: re.Pattern = None
    neg_forms: re.Pattern = None
    schemes: list = field(default_factory=list)
    tlds: list = field(default_factory=list)
    registry: set = field(default_factory=set)
    local_names: set = field(default_factory=set)
    local_suffixes: tuple = ()
    local_ipv4_prefix: str = "127."
    explicit_kw: re.Pattern = None
    explicit_by: re.Pattern = None
    mapping: re.Pattern = None
    glossary_heading: re.Pattern = None
    procedural_heading: re.Pattern = None
    not_terms: set = field(default_factory=set)
    max_term_words: int = 4
    safety: re.Pattern = None


def _rx(where: str, pattern) -> re.Pattern:
    if not isinstance(pattern, str) or not pattern:
        raise VocabError(f"{where}: regex must be a non-empty string")
    if "\x08" in pattern:
        raise VocabError(f"{where}: regex holds a backspace byte")
    try:
        return re.compile(pattern, FLAGS)
    except re.error as exc:
        raise VocabError(f"{where}: regex does not compile: {exc}")


def _section(doc, name) -> dict:
    sec = doc.get(name)
    if not isinstance(sec, dict):
        raise VocabError(f"missing section {name}")
    if not sec.get("source"):
        raise VocabError(f"{name}: missing source")
    return sec


def _sub(sec, name, key) -> dict:
    sub = sec.get(key)
    if not isinstance(sub, dict) or not sub.get("source"):
        raise VocabError(f"{name}.{key}: missing or without a source")
    return sub


def _list(sec, where, key) -> list:
    val = sec.get(key)
    if not isinstance(val, list) or not val:
        raise VocabError(f"{where}.{key}: expected a non-empty list")
    return [str(x) for x in val]


def load_vocab(path=None, rows=None) -> Vocab:
    path = Path(path) if path else DEFAULT_VOCAB
    try:
        doc = yaml.safe_load(path.read_text("utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise VocabError(f"cannot read {path}: {exc}")
    if not isinstance(doc, dict):
        raise VocabError(f"{path}: expected a mapping")
    v = Vocab()

    rb = _section(doc, "rubric")
    tiers = rb.get("tiers")
    if not isinstance(tiers, dict) or not tiers:
        raise VocabError("rubric.tiers: expected a mapping")
    for rid, tier in tiers.items():
        if tier not in TIERS:
            raise VocabError(f"rubric.tiers.{rid}: unknown tier {tier}")
    v.tiers = {str(k): str(t) for k, t in tiers.items()}
    v.ignore_unless_tier = str(rb.get("ignore_unless_tier", "confirm-first"))
    if v.ignore_unless_tier not in TIERS:
        raise VocabError("rubric.ignore_unless_tier: unknown tier")
    conf = _sub(rb, "rubric", "confirmation")
    v.confirm = [_rx(f"rubric.confirmation[{i}]", r)
                 for i, r in enumerate(_list(conf, "rubric.confirmation", "regexes"))]
    neg = _sub(rb, "rubric", "negation")
    v.neg_before = _rx("rubric.negation.before", neg.get("before"))
    v.neg_after = _rx("rubric.negation.after", neg.get("after"))
    v.neg_forms = _rx("rubric.negation.forms", neg.get("forms"))
    if rows is not None:
        j = {r.id for r in rows if r.check == "phrase.J.prohibited"}
        missing = j - set(v.tiers)
        if missing:
            raise VocabError(f"rubric.tiers: J row(s) without a tier: {sorted(missing)}")

    ep = _section(doc, "endpoints")
    v.schemes = [s.lower() for s in _list(ep, "endpoints", "schemes")]
    v.tlds = [t.lower() for t in _list(ep, "endpoints", "tlds")]
    reg = _sub(ep, "endpoints", "registry")
    v.registry = {h.lower() for h in _list(reg, "endpoints.registry", "hosts")}
    loc = _sub(ep, "endpoints", "local")
    v.local_names = {h.lower() for h in _list(loc, "endpoints.local", "names")}
    v.local_suffixes = tuple(s.lower() for s in _list(loc, "endpoints.local", "suffixes"))
    v.local_ipv4_prefix = str(loc.get("ipv4_prefix", "127."))

    tm = _section(doc, "terms")
    v.explicit_kw = _rx("terms.explicit_keyword", tm.get("explicit_keyword"))
    v.explicit_by = _rx("terms.explicit_by", tm.get("explicit_by"))
    v.mapping = _rx("terms.mapping", tm.get("mapping"))
    v.glossary_heading = _rx("terms.glossary_heading", tm.get("glossary_heading"))
    v.procedural_heading = _rx("terms.procedural_heading", tm.get("procedural_heading"))
    v.not_terms = {s.lower() for s in _list(tm, "terms", "not_terms")}
    v.max_term_words = int(tm.get("max_term_words", 4))
    sf = _sub(tm, "terms", "safety")
    v.safety = _rx("terms.safety", sf.get("regex"))
    return v
