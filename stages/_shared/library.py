"""Where the Library is, and how a stage reads from it. Spec: specs/shared.SPEC.md, library.

`Library/` (at the repository root) holds data only: tables, lists, and their sources. This is
the one place that knows where it is. Every stage that reads one of its files goes through here,
so a file moves once, here, and not in every reader. The Library holds no code (Library/README.md).

    import library
    TABLE = library.load_yaml("fit.yaml")
    INV = library.invisible()
    library.runs(line)          # the runs of invisible characters in a line, and what each spells

The run rule (which characters, how many) is the list's; finding runs and reading what one spells is
code, so it lives here beside the list and every stage that reads the list uses it. A run is
`run_length` or more `run` characters in a row, or separated only by characters the list strips (a
zero-width space between two selectors does not break the run).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

import yaml

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "Library"

ACTIONS = ("strip", "space", "run")
_CODEPOINT = re.compile(r"U\+([0-9A-F]{4,6})")


class LibraryError(ValueError):
    pass


def path(name: str) -> Path:
    """The file `name` in the Library. A plain file name: the Library has no sub-folders."""
    if not name or "/" in name or "\\" in name or name in (".", ".."):
        raise LibraryError(f"a Library file is a plain file name, got {name!r}")
    return LIBRARY / name


def load_yaml(name: str):
    return yaml.safe_load(path(name).read_text(encoding="utf-8"))


def load_json(name: str):
    return json.loads(path(name).read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Invisible:
    """The invisible-character list (Library/invisible.yaml), read once for every stage.

    strip:      characters taken out of text before it is read or matched
    space:      characters each turned into one space (line separators: a line is split on
                a line feed only, so these never start a new line)
    run:        characters taken out and reported only where `run_length` or more stand in a run (in a
                row, or separated only by characters in `strip`)
    kind:       character -> the kind `02.2-reader` reports for it (every character in `strip` or
                `run` with a kind; a `run` character is reported only inside a run)
    kind_order: the order kinds are joined in a finding's carrier
    run_length: how many `run` characters make a run (written once, in the file)
    run_re:     a pattern matching one run (begins and ends with a `run` character), or None when no
                character has action `run`
    """
    strip: frozenset
    space: frozenset
    run: frozenset
    kind: dict
    kind_order: tuple
    run_length: int
    run_re: object


def _codepoint(value, where: str) -> int:
    m = _CODEPOINT.fullmatch(str(value))
    if not m:
        raise LibraryError(f"invisible.yaml {where}: {value!r} is not a code point like U+200B")
    return int(m.group(1), 16)


def _class(chars) -> str:
    """A pattern character class for `chars` (consecutive code points as one range)."""
    spans: list[list[int]] = []
    for c in sorted(ord(ch) for ch in chars):
        if spans and c == spans[-1][1] + 1:
            spans[-1][1] = c
        else:
            spans.append([c, c])
    return "[" + "".join(f"\\U{a:08X}" if a == b else f"\\U{a:08X}-\\U{b:08X}" for a, b in spans) + "]"


def _run_pattern(chars, between, length: int):
    """One pattern for a run: `length` or more of `chars`, with only `between` characters (and more of
    `chars`) in between, beginning and ending with a character of `chars`."""
    r = _class(chars)
    gap = _class(between) + "*" if between else ""
    return re.compile(f"{r}(?:{gap}{r}){{{length - 1},}}")


@lru_cache(maxsize=None)
def invisible() -> Invisible:
    doc = load_yaml("invisible.yaml")
    order = tuple(doc["kind_order"])
    strip: set[str] = set()
    space: set[str] = set()
    run: set[str] = set()
    kind: dict[str, str] = {}
    for i, r in enumerate(doc["ranges"]):
        where = f"range {i + 1} ({r.get('name')})"
        lo, hi = _codepoint(r["from"], where), _codepoint(r["to"], where)
        if lo > hi:
            raise LibraryError(f"invisible.yaml {where}: from is after to")
        action = r.get("action")
        if action not in ACTIONS:
            raise LibraryError(f"invisible.yaml {where}: action {action!r} is not one of {ACTIONS}")
        k = r.get("kind")
        if k is not None and k not in order:
            raise LibraryError(f"invisible.yaml {where}: kind {k!r} is not in kind_order")
        if action == "space" and k is not None:
            raise LibraryError(f"invisible.yaml {where}: a space character has no kind")
        for c in range(lo, hi + 1):
            ch = chr(c)
            if ch in strip or ch in space or ch in run:
                raise LibraryError(f"invisible.yaml {where}: U+{c:04X} is listed twice")
            {"strip": strip, "space": space, "run": run}[action].add(ch)
            if k is not None:
                kind[ch] = k
    length = doc.get("run_length")
    if run or length is not None:
        if isinstance(length, bool) or not isinstance(length, int) or length < 2:
            raise LibraryError(f"invisible.yaml run_length: {length!r} is not a whole number of 2 or more")
    return Invisible(frozenset(strip), frozenset(space), frozenset(run), kind, order,
                     length or 0, _run_pattern(run, strip, length) if run else None)


# ---- runs of invisible characters

class Run(NamedTuple):
    """One run in a line: where it stands (`start` to `end`, a slice of the line, from its first
    selector to its last, with any stripped characters between) and `text`, what its selectors
    spell (None when they spell nothing)."""
    start: int
    end: int
    text: str | None


def run_text(run: str) -> str | None:
    """What a run of variation selectors spells. U+FE00 to U+FE0F are the bytes 0 to 15 and U+E0100
    to U+E01EF the bytes 16 to 255; the text is returned when the bytes are UTF-8 of printable
    characters (and white space) with a word of two letters or more. The text comes from those byte
    selectors alone: any other character in `run` (a Mongolian free variation selector, which carries
    no byte) is skipped, as the characters stripped between selectors are, so one among them hides
    nothing. A run of Mongolian selectors only has no bytes and spells nothing, and neither do bytes
    that are not such text: None."""
    data = bytearray()
    for ch in run:
        o = ord(ch)
        if 0xFE00 <= o <= 0xFE0F:
            data.append(o - 0xFE00)
        elif 0xE0100 <= o <= 0xE01EF:
            data.append(o - 0xE0100 + 16)
    try:
        text = bytes(data).decode("utf-8")
    except UnicodeDecodeError:
        return None
    if all(c.isprintable() or c in "\t\n\r" for c in text) and re.search(r"[A-Za-z]{2,}", text):
        return text
    return None


def runs(text: str) -> list[Run]:
    """Every run in `text`, in order: `run_length` or more `run` characters, whichever of them, in a
    row or separated only by characters the list strips (a zero-width space between two selectors
    does not break the run). A run begins and ends with a `run` character. One alone is not a run,
    even with a stripped character after it. ASCII text has none. The text a run spells is read from
    its `run` characters alone."""
    inv = invisible()
    if inv.run_re is None or text.isascii():
        return []
    return [Run(m.start(), m.end(), run_text("".join(ch for ch in m.group(0) if ch in inv.run)))
            for m in inv.run_re.finditer(text)]


def replace_runs(text: str, spell: bool = False) -> str:
    """`text` with the `run` characters of every run taken out. The characters the list strips that
    stand between them stay where they are, for the caller's own strip (and, in `02.4-phrases` and
    `02.5-capability`, for a tag run among them to be read: `read_hidden`). With `spell`, a run that spells text puts
    that text at the run's start, a space on each side (white space inside it collapsed to single
    spaces, so a line stays one line), as a run of tag characters is read; a run that spells nothing
    leaves nothing either way."""
    inv = invisible()
    found = runs(text)
    if not found:
        return text
    out: list[str] = []
    at = 0
    for r in found:
        out.append(text[at:r.start])
        if spell and r.text:
            out.append(" " + " ".join(r.text.split()) + " ")
        out.append("".join(ch for ch in text[r.start:r.end] if ch not in inv.run))
        at = r.end
    out.append(text[at:])
    return "".join(out)


# A run of tag characters spells ASCII (each minus U+E0000): read it, never drop it (review C42).
_TAG_RUN = re.compile("[\U000E0020-\U000E007E]+")


def _tag_ascii(run: str) -> str:
    return "".join(chr(ord(c) - 0xE0000) for c in run)


def read_hidden(text: str) -> str:
    """`text` with what it hides written out, a space on each side of each: a run of variation selectors
    that spells text (`replace_runs` with `spell`, found first, on the text as written: tag characters can
    sit between its selectors), then each run of tag characters as the ASCII it spells. The characters the
    list strips stay, for the caller's own strip."""
    s = replace_runs(text, spell=True)
    return _TAG_RUN.sub(lambda m: " " + _tag_ascii(m.group(0)) + " ", s) if not s.isascii() else s


def tag_texts(text: str) -> list[str]:
    """What each run of tag characters in `text` spells, in order: the runs `read_hidden` reads, so a tag
    character between variation selectors joins the ones beside it (the selectors are taken out first)."""
    return [_tag_ascii(m.group(0)) for m in _TAG_RUN.finditer(replace_runs(text, spell=True))]
