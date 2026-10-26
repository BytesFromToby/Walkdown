"""Endpoint census: every host named in the text. Spec: specs/endpoints.SPEC.md.

Rebuilt from the spec; replaces tools/extract_urls.py. Text only: nothing is
fetched or resolved.
"""
from __future__ import annotations

import re
from functools import lru_cache

from foldtext import fold_line

HOSTNAME = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$")
IPV4 = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
PLACEHOLDER = set("${}<>%")
WHERE = ("instructions", "docs", "code")


@lru_cache(maxsize=None)
def _regexes(schemes: tuple, tlds: tuple):
    sch = "|".join(re.escape(s) for s in schemes)
    url = re.compile(
        r"\b(?:" + sch + r")://(?:[^\s/@<>\"'`]+@)?(\[[0-9a-f:.]+\]|[^\s/:?#<>\"'`()\[\]|,;*\\]+)",
        re.IGNORECASE)
    git = re.compile(r"\bgit@([^\s:/<>\"'`]+):", re.IGNORECASE)
    tld = "|".join(re.escape(t) for t in sorted(tlds, key=len, reverse=True))
    bare = re.compile(
        r"(?<![\w.\-/\\])((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+(?:" + tld + r"))"
        r"(?![\w-]|\.[\w-]|\()", re.IGNORECASE)
    port = re.compile(r"(?<![\w.\-/\\])(localhost|\d{1,3}(?:\.\d{1,3}){3}):\d+\b", re.IGNORECASE)
    return url, git, bare, port


def _clean(host: str) -> str | None:
    h = host.strip().lower().rstrip(".")
    if not h or any(c in PLACEHOLDER for c in h):
        return None
    if h.startswith("[") and h.endswith("]"):
        return h[1:-1] or None
    if h.startswith("www."):
        h = h[4:]
    if not (HOSTNAME.match(h) or IPV4.match(h)):
        return None
    if "." not in h and h != "localhost":
        return None  # a single label ("http://host:port") is a placeholder
    return h


TAIL = re.compile(r"[^\s<>\"'`\[\]]*")  # a Markdown link's "](" ends an address
TRAIL = ".,;:!?*'\""
CLOSERS = (("(", ")"), ("[", "]"), ("{", "}"))


def _trim(s: str) -> str:
    """Drop sentence punctuation and unbalanced closing brackets off the end of an address
    (a Markdown link's `)`, a full stop after a URL)."""
    while True:
        before = s
        s = s.rstrip(TRAIL)
        for o, c in CLOSERS:
            if s.endswith(c) and s.count(c) > s.count(o):
                s = s[:-1]
        if s == before:
            return s


def addresses_in_line(folded: str, vocab) -> list[tuple[str, str]]:
    """(host, address) for every host named on the line, in order of first appearance: the
    address is the whole text that names it, from the scheme (or `git@`, or the bare name)
    to the end of its path (added 2026-10-16 so the report can list and copy each address)."""
    url, git, bare, port = _regexes(tuple(vocab.schemes), tuple(vocab.tlds))
    found: list[tuple[str, str]] = []
    masked = folded

    def add(m, start, path_only=False):
        h = _clean(m.group(1))
        if not h:
            return
        end = m.end()
        if not path_only or folded[end:end + 1] == "/":  # a bare name runs on only into a path
            end = TAIL.match(folded, end).end()
        a = _trim(folded[start:end])
        if (h, a) not in found:
            found.append((h, a))

    for rx in (url, git):
        for m in rx.finditer(masked):
            add(m, m.start())
        masked = rx.sub(lambda m: " " * (m.end() - m.start()), masked)
    for m in port.finditer(masked):
        add(m, m.start(), path_only=True)
    masked = port.sub(lambda m: " " * (m.end() - m.start()), masked)
    for m in bare.finditer(masked):
        add(m, m.start(1), path_only=True)
    # a bare name that is the visible text of a full address on the same line ("[x.io](https://x.io)")
    return [(h, a) for h, a in found
            if "://" in a or a.startswith("git@")
            or not any(h2 == h and a2 != a and a in a2 for h2, a2 in found)]


def hosts_in_line(folded: str, vocab) -> list[str]:
    return list(dict.fromkeys(h for h, _ in addresses_in_line(folded, vocab)))


def is_local(host: str, vocab) -> bool:
    h = host.lower()
    if h in vocab.local_names:
        return True
    if IPV4.match(h) and h.startswith(vocab.local_ipv4_prefix):
        return True
    return h.endswith(vocab.local_suffixes)


_NAME = re.compile(r"(?<![\w.-])(?:[\w-]+\.)+[\w-]{2,}(?![\w-])")


def lookalikes(raw: str) -> dict[str, str]:
    """{the host a name folds to: the name as written} for each dotted name on a raw line
    written with non-ASCII letters that folds to an ASCII host the line does not also name as
    itself (review C42: a Cyrillic letter made gіthub.com read as github.com)."""
    if raw.isascii():
        return {}
    low, out = raw.lower(), {}
    for m in _NAME.finditer(raw):
        name = m.group(0)
        if name.isascii():
            continue
        host = _clean(fold_line(name))
        if host and host.isascii() and host not in low:
            out[host] = name.lower()
    return out


def _punycode(name: str) -> str | None:
    try:
        return name.encode("idna").decode("ascii")
    except UnicodeError:
        return None


def census(occurrences, vocab, lookalike: dict | None = None) -> list[dict]:
    """Each occurrence is (host, file, line, where) or (host, file, line, where, address);
    a row gains `urls` (the distinct addresses on that line, in order) when any were given."""
    by: dict[str, set] = {}
    addrs: dict[tuple, list] = {}
    for host, file, line, where, *rest in occurrences:
        by.setdefault(host, set()).add((file, line, where))
        if rest and rest[0]:
            got = addrs.setdefault((host, file, line), [])
            if rest[0] not in got:
                got.append(rest[0])
    out = []
    for host in sorted(by):
        occ = sorted(by[host], key=lambda o: (o[0], o[1], WHERE.index(o[2])))
        seen, rows = set(), []
        for f, ln, w in occ:
            if (f, ln) in seen:
                continue
            seen.add((f, ln))
            row = {"file": f, "line": ln, "where": w}
            if (host, f, ln) in addrs:
                row["urls"] = addrs[(host, f, ln)]
            rows.append(row)
        counts = {w: sum(1 for r in rows if r["where"] == w) for w in WHERE}
        real = (lookalike or {}).get(host)
        local = is_local(host, vocab) and not real
        kind = "local" if local else ("registry" if host in vocab.registry and not real else "other")
        row = {"check": "endpoint.host", "file": None, "line": None, "host": host,
               "documented": counts["docs"] > 0, "local": local, "kind": kind,
               "where": counts, "occurrences": rows}
        if real:  # review C42: listed as written, and said what it imitates
            row.update(lookalike_of=real, punycode=_punycode(host))
        out.append(row)
    return out


def summary(findings) -> dict:
    by_kind = {"registry": 0, "local": 0, "other": 0}
    for f in findings:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    return {"hosts": len(findings),
            "undocumented": sum(1 for f in findings if not f["documented"]),
            "local": sum(1 for f in findings if f["local"]), "by_kind": by_kind}
