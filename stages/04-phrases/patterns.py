"""Load and validate the stage 4 pattern table. Spec: specs/patterns.SPEC.md."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_TABLE = HERE / "patterns.yaml"

CHECKS = [
    "phrase.K.exfil", "phrase.creds", "phrase.remote-load",
    "phrase.L.override", "phrase.A.consent", "phrase.B.defs", "phrase.H.anti-review",
    "phrase.I.conditional",
    "phrase.E.perms", "phrase.C.second-order", "phrase.D.trust", "phrase.E.env",
    "phrase.J.prohibited",
    "phrase.G.human",
]
AUDIENCES = {"model", "subagent", "human", "tool"}
REQUIRED = ("id", "check", "regex", "source")
OPTIONAL = ("unless", "note", "audiences", "paths", "where")
FLAGS = re.IGNORECASE


class TableError(ValueError):
    pass


@dataclass
class Row:
    id: str
    check: str
    regex: str
    source: str
    unless: str | None = None
    note: str | None = None
    audiences: list[str] | None = None
    paths: str | None = None
    where: str | None = None
    rx: re.Pattern = field(default=None, repr=False)
    unless_rx: re.Pattern | None = field(default=None, repr=False)
    paths_rx: re.Pattern | None = field(default=None, repr=False)

    def applies(self, rel: str, audience: str, in_frontmatter: bool) -> bool:
        if self.audiences is not None and audience not in self.audiences:
            return False
        if self.paths_rx is not None and not self.paths_rx.search(rel):
            return False
        if self.where == "frontmatter" and not in_frontmatter:
            return False
        return True

    def hits(self, text: str) -> bool:
        if not self.rx.search(text):
            return False
        return not (self.unless_rx is not None and self.unless_rx.search(text))


def _compile(row_id: str, what: str, pattern) -> re.Pattern:
    if not isinstance(pattern, str) or not pattern:
        raise TableError(f"{row_id}: {what} must be a non-empty string")
    try:
        return re.compile(pattern, FLAGS)
    except re.error as exc:
        raise TableError(f"{row_id}: {what} does not compile: {exc}")


def load_table(path=None) -> list[Row]:
    path = Path(path) if path else DEFAULT_TABLE
    try:
        doc = yaml.safe_load(path.read_text("utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise TableError(f"cannot read {path}: {exc}")
    if not isinstance(doc, dict) or not isinstance(doc.get("patterns"), list):
        raise TableError(f"{path}: expected a mapping with a 'patterns' list")
    rows: list[Row] = []
    seen: set[str] = set()
    for i, raw in enumerate(doc["patterns"]):
        if not isinstance(raw, dict):
            raise TableError(f"row {i}: not a mapping")
        rid = str(raw.get("id", f"row {i}"))
        for k in REQUIRED:
            if not raw.get(k):
                raise TableError(f"{rid}: missing {k}")
        extra = set(raw) - set(REQUIRED) - set(OPTIONAL)
        if extra:
            raise TableError(f"{rid}: unknown field(s) {sorted(extra)}")
        if rid in seen:
            raise TableError(f"{rid}: duplicate id")
        seen.add(rid)
        if raw["check"] not in CHECKS:
            raise TableError(f"{rid}: unknown check {raw['check']}")
        if not str(raw["source"]).startswith(("PHRASES:", "THREATS:")):
            raise TableError(f"{rid}: source must start PHRASES: or THREATS:")
        if raw.get("unless") is not None and not raw.get("note"):
            raise TableError(f"{rid}: an unless needs a note giving its reason")
        aud = raw.get("audiences")
        if aud is not None and (not isinstance(aud, list) or set(aud) - AUDIENCES):
            raise TableError(f"{rid}: audiences must be a list drawn from {sorted(AUDIENCES)}")
        if raw.get("where") not in (None, "frontmatter"):
            raise TableError(f"{rid}: unknown where {raw.get('where')}")
        row = Row(id=rid, check=raw["check"], regex=raw["regex"], source=str(raw["source"]),
                  unless=raw.get("unless"), note=raw.get("note"), audiences=aud,
                  paths=raw.get("paths"), where=raw.get("where"))
        row.rx = _compile(rid, "regex", row.regex)
        if row.unless is not None:
            row.unless_rx = _compile(rid, "unless", row.unless)
        if row.paths is not None:
            row.paths_rx = _compile(rid, "paths", row.paths)
        rows.append(row)
    return rows
