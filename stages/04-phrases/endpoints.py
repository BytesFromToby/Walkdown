"""Endpoint census: every host named in the text. Spec: specs/endpoints.SPEC.md.

Rebuilt from the spec; replaces tools/extract_urls.py. Text only: nothing is
fetched or resolved.
"""
from __future__ import annotations

import re
from functools import lru_cache

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


def hosts_in_line(folded: str, vocab) -> list[str]:
    url, git, bare, port = _regexes(tuple(vocab.schemes), tuple(vocab.tlds))
    found: list[str] = []
    masked = folded

    def add(h):
        h = _clean(h)
        if h and h not in found:
            found.append(h)

    for rx in (url, git):
        for m in rx.finditer(masked):
            add(m.group(1))
        masked = rx.sub(lambda m: " " * (m.end() - m.start()), masked)
    for m in port.finditer(masked):
        add(m.group(1))
    masked = port.sub(lambda m: " " * (m.end() - m.start()), masked)
    for m in bare.finditer(masked):
        add(m.group(1))
    return found


def is_local(host: str, vocab) -> bool:
    h = host.lower()
    if h in vocab.local_names:
        return True
    if IPV4.match(h) and h.startswith(vocab.local_ipv4_prefix):
        return True
    return h.endswith(vocab.local_suffixes)


def census(occurrences, vocab) -> list[dict]:
    by: dict[str, set] = {}
    for host, file, line, where in occurrences:
        by.setdefault(host, set()).add((file, line, where))
    out = []
    for host in sorted(by):
        occ = sorted(by[host], key=lambda o: (o[0], o[1], WHERE.index(o[2])))
        seen, rows = set(), []
        for f, ln, w in occ:
            if (f, ln) in seen:
                continue
            seen.add((f, ln))
            rows.append({"file": f, "line": ln, "where": w})
        counts = {w: sum(1 for r in rows if r["where"] == w) for w in WHERE}
        local = is_local(host, vocab)
        kind = "local" if local else ("registry" if host in vocab.registry else "other")
        out.append({"check": "endpoint.host", "file": None, "line": None, "host": host,
                    "documented": counts["docs"] > 0, "local": local, "kind": kind,
                    "where": counts, "occurrences": rows})
    return out


def summary(findings) -> dict:
    by_kind = {"registry": 0, "local": 0, "other": 0}
    for f in findings:
        by_kind[f["kind"]] = by_kind.get(f["kind"], 0) + 1
    return {"hosts": len(findings),
            "undocumented": sum(1 for f in findings if not f["documented"]),
            "local": sum(1 for f in findings if f["local"]), "by_kind": by_kind}
