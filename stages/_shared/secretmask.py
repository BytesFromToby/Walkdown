"""A report never repeats a secret it found, and a model read never sends one. Spec: specs/shared.SPEC.md, secretmask.

Moved here from `02.4-phrases`'s runner (restructure step 4): `02.4-phrases` finds the secrets, and both
it and `02.6-builder` quote lines (`port.path`, `fit.loop`, `clean.*`), so both must mask a line a
secret sits on. `02.1-inventory`, `02.2-reader`, and `02.3-graph` keep words from lines too and run before the scan, and
`02.5-capability` copies words from `02.1-inventory`, so each of those is masked after it (`mask_reports`). `03-sweep` and
`04-pinpoint` send lines off the machine, so what they send goes through `ToSend`.
"""
from __future__ import annotations

import re

SECRET_MASK = "[line not shown: it holds what looks like a secret; open the file to see it]"
# What a person wrote, as it stands in the file. A word from a fixed list under one of these names is no one's writing.
TEXT_FIELDS = ("quote", "definition", "condition", "body", "decoded_text", "text", "decoded", "folded",
               "description", "first_colon_text", "yaml_error", "command", "matcher", "name", "url", "stated",
               "target", "pattern", "action", "carve_out", "term",
               "key", "value", "tool", "model", "what", "error", "plain")
NOT_TEXT = {"limit.setting": ("value",)}
# A phrase hit on readable text hidden in base64 (review C42) keeps what it decoded and the words it matched there: a value the scanner
# flags is random-looking, so it never decodes to readable text, and the decoded instruction is what a reader needs (owner, 2026-11-03).
# Its `quote`, the line as written, is masked as any other. `decoded` here is the fixed word "base64". When the scan found a key in that
# decoded text (`in_base64` on the row), it goes too.
DECODED = ("decoded", "decoded_text")
# Lists whose items a person wrote and whose plain words are what a page is for: a tool's name stays, and anything else goes.
WORD_LISTS = ("tools", "grants", "disallowed", "preloads", "env_keys", "types")
# Lists with nothing to keep: how many there are stays.
WHOLE_LISTS = ("commands", "shared")
# Single words a config names, kept when they read as one. An event names when a hook runs, the thing a reader most needs.
PLAIN_FIELDS = ("event", "transport")
PLAIN = re.compile(r"[A-Za-z][A-Za-z_-]{0,23}")
# The hidden characters of a line in the order they stand, and in that order tag characters spell the text.
CODE_POINTS = ("chars", "removed")
READER = "read."  # the checks of `02.2-reader`
# Findings a parser made, whose words have no line of their own: `span` says where they sit. With no `span` (a run saved before it
# was written, or a file that does not compose) the place is not known, so a flagged line anywhere in the file masks them.
PLACED = ("struct.description", "struct.agent-tools", "struct.hooks", "struct.mcp",
          "trig.entry", "trig.frontmatter", "trig.overlap")
# Words a finding quotes from a line of their own: (the field that names the line, the field that holds the words).
OWN_LINE = (("confirm_line", "confirm_quote"), ("heading_line", "term"))
# review C42: a secret.found whose only "secret" is base64 that decodes to readable text
BASE64_TEXT = "base64 that decodes to readable text, not a key"
INVENTORY, READ, GRAPH, PHRASES, CAPABILITY, BUILDER, PINPOINT = ("02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases",
                                                                  "02.5-capability", "02.6-builder", "04-pinpoint")
# A model's quote of lines in a passage, which go by the lines it quotes (`pin_line` to `pin_end`).
PINPOINTED = "soft.pinpoint"
# What a model read does in place of what it does not send: a blank, so a line keeps its number, a model is shown no words about
# secrets to answer to or to quote back, and a passage with nothing else in it has nothing to send (owner, 2026-11-01).
LEFT_OUT = ""
NOT_READ = "the secret scan could not read this file, so it was not sent to a model"
PRIVATE_KEY = re.compile(r"private key", re.I)  # the kind of a flagged line: `Private Key` from detect-secrets
KEY_END = "-----END"


def _lines_of(f: dict) -> set | None:
    """The lines a finding quotes, or None when they are not known and any line of its file may be one. A wrapped finding quotes
    every line of its run (review C37). Hidden text can reach past its first line: `end_line` says how far, and in a run saved
    before the reader wrote it, the line breaks left in the text."""
    line, check = f.get("line"), str(f.get("check"))
    if f.get("span"):
        return set(range(f["span"][0], f["span"][1] + 1))
    if (check in PLACED and "span" not in f) or (check == "inv.license" and line is None):
        return None
    if check == PINPOINTED:
        return set(range(f["pin_line"], (f.get("pin_end") or f["pin_line"]) + 1)) if f.get("pin_line") else set()
    if f.get("wrapped") and f.get("end_line"):
        return set(range(line, f["end_line"] + 1))
    if line is not None and check.startswith(READER):
        return set(range(line, (f.get("end_line") or line + str(f.get("text") or "").count("\n")) + 1))
    return {line}


def flagged_lines(findings: list[dict]) -> set:
    """The lines the secret scan flagged, as (file, line), with the rest of each private key it starts (`key_end`): the scan flags
    only a key's first line, and its body is the key. A line whose secret is only base64 that decodes to readable text holds no key:
    its text is the instruction a reader needs (review C42)."""
    out = set()
    for f in findings:
        if f.get("check") != "secret.found" or "skipped" in f or f.get("likely_not_secret") == BASE64_TEXT:
            continue
        line, last = f.get("line"), f.get("key_end")
        if isinstance(line, int) and isinstance(last, int):
            out.update((f["file"], n) for n in range(line, last + 1))
        else:
            out.add((f["file"], line))
    return out


def _is_plain(word) -> bool:
    return bool(PLAIN.fullmatch(str(word)))


def _mask_fields(f: dict, was: set, keep_decoded: bool = True) -> bool:
    """Every field of a finding that holds a person's words, in place, each kept in `was`. Whether any was masked now.
    `keep_decoded`: false when the scan found a key in the text the line's base64 decodes to (`in_base64`), so what a base64 hit
    decoded goes too."""
    changed = False

    def gone(word):
        nonlocal changed
        changed = True
        was.add(word)
        return SECRET_MASK

    from_base64 = keep_decoded and f.get("decoded") == "base64"
    fixed = NOT_TEXT.get(f.get("check"), ()) + (DECODED if from_base64 else ())
    for k in TEXT_FIELDS:
        if k not in fixed and isinstance(f.get(k), str) and f[k] != SECRET_MASK:
            f[k] = gone(f[k])
    for k in PLAIN_FIELDS:
        if isinstance(f.get(k), str) and f[k] != SECRET_MASK and not _is_plain(f[k]):
            f[k] = gone(f[k])
    for k in WORD_LISTS:
        if isinstance(f.get(k), list):
            f[k] = [x if x == SECRET_MASK or _is_plain(x) else gone(x) for x in f[k]]
    for k in WHOLE_LISTS:
        if isinstance(f.get(k), list):
            f[k] = [x if x == SECRET_MASK else gone(x) for x in f[k]]
    for k in CODE_POINTS:
        if isinstance(f.get(k), list):
            f[k] = sorted(set(f[k]))
    for m in [] if from_base64 else f.get("matches") or []:  # the words of a base64 hit are words of its decoded text
        if m.get("text") != SECRET_MASK:
            m["text"] = gone(m.get("text"))
    return changed


def _replace(f: dict, k: str, was: set) -> bool:
    """One text field of a finding. Whether it was masked now."""
    if isinstance(f.get(k), str) and f[k] != SECRET_MASK:
        was.add(f[k])
        f[k] = SECRET_MASK
        return True
    return False


def _mask_places(f: dict, lines: set, files: set, was: set) -> bool:
    """The findings that name more than one place, each by what it holds at each. Whether any was masked now. The host itself goes
    only when every place naming it is flagged: then only a flagged line says it."""
    changed = False
    at = lambda o: (o.get("file"), o.get("line")) in lines  # noqa: E731
    places = f.get("occurrences") or []  # endpoint.host
    for o in places:
        if at(o) and any(u != SECRET_MASK for u in o.get("urls") or []):
            was.update(o["urls"])
            o["urls"] = [SECRET_MASK] * len(o["urls"])
            changed = True
    if places and all(at(o) for o in places):
        for k in ("host", "lookalike_of", "punycode"):
            changed = _replace(f, k, was) or changed
    defs = f.get("definitions") or []  # term.conflict
    for d in defs:
        if at(d):
            changed = _replace(d, "text", was) or changed
    if defs and all(at(d) for d in defs):
        changed = _replace(f, "term", was) or changed
    if any(at(o) for o in f.get("where") or [] if isinstance(o, dict)):  # rep.sentence: the sentence stands at each
        changed = _replace(f, "sentence", was) or changed
    for own, field in OWN_LINE:
        if f.get(own) is not None and (f.get("file"), f[own]) in lines:
            changed = _replace(f, field, was) or changed
    for a in f.get("also") or []:  # the other lines a model quoted
        if any((f.get("file"), n) in lines for n in range(a.get("line") or 0, (a.get("line_end") or a.get("line") or 0) + 1)):
            changed = _replace(a, "quote", was) or changed
    if f.get("check") == "struct.manifests":  # one row for the manifests of a plugin, with no line for what each grants
        for rel, grants in (f.get("grants") or {}).items():
            if rel in files:
                f["grants"][rel] = [x if x == SECRET_MASK or _is_plain(x) else SECRET_MASK for x in grants]
                changed = changed or f["grants"][rel] != grants
        if any(rel in files for rel in f.get("files") or []):
            changed = _replace(f, "name", was) or changed
    if f.get("check") == "need.package" and any(rel in files for rel in f.get("files") or []):
        if not _is_plain(f.get("package")):  # the row has the file an import is in, and no line
            changed = _replace(f, "package", was) or changed
    return changed


def mask_secret_lines(findings: list[dict], was: dict | None = None) -> None:
    """A report must not repeat a secret it found (2026-10-04): every field of a finding that quotes a line where secret.found
    fired, and that holds a person's words, is replaced by SECRET_MASK, matched words included, and a list of code points keeps
    each one once, sorted, so it names the kinds and spells nothing. The location stays. `was`, when given: {file: the words
    masked}, for `mask_copies`."""
    lines = flagged_lines(findings)
    files = {file for file, _ in lines}
    in_base64 = {(f["file"], f["line"]) for f in findings
                 if f.get("check") == "secret.found" and f.get("in_base64") and "skipped" not in f}
    for f in findings:
        if f.get("check") == "secret.found":
            continue
        gone = (was if was is not None else {}).setdefault(f.get("file"), set())
        lines_of = _lines_of(f)
        hit = f.get("file") in files if lines_of is None else any((f.get("file"), n) in lines for n in lines_of)
        changed = _mask_places(f, lines, files, gone)
        if hit:
            changed = _mask_fields(f, gone, keep_decoded=(f.get("file"), f.get("line")) not in in_base64) or changed
        elif f.get("event_line") and (f.get("file"), f["event_line"]) in lines and not _is_plain(f.get("event")):
            changed = _replace(f, "event", gone) or changed
        # a parser's finding is masked for what it held; a finding that quotes the line is masked for where it is, as it was
        if changed or (hit and lines_of is not None and "span" not in f):
            f["masked"] = True


def mask_copies(node, was: dict, file=None) -> bool:
    """Words masked at their source, wherever a later step copied them. `02.5-capability` and `02.6-builder` copy a hook's command,
    an agent's description, a tool's name, and they say why with an event's or a server's name; none of those findings has a line
    to go by. So a copy goes by its value within one file: a string that is one of the words masked for that file. Evidence that
    points at `02.1-inventory` says the words inside its `why`. Whether anything was masked now."""
    changed = False
    if isinstance(node, list):
        for x in node:
            changed = mask_copies(x, was, file) or changed
        return changed
    if not isinstance(node, dict):
        return False
    file = node.get("file", file)
    gone = set(was.get(file) or ()) if file else set()  # a finding of the whole repository has no file to go by
    if node.get("owner"):
        gone |= set(was.get(node["owner"]) or ())
    for k, v in node.items():
        if k == "why" and node.get("stage") == INVENTORY and gone and isinstance(v, str):
            words = "|".join(re.escape(w) for w in sorted(gone, key=len, reverse=True))
            said = re.sub(rf"(?<![\w-])(?:{words})(?![\w-])", SECRET_MASK, v)
            changed = changed or said != v
            node[k] = said
        elif isinstance(v, str) and v in gone and k not in ("check", "file", "stage"):
            node[k] = SECRET_MASK
            changed = True
        elif isinstance(v, list) and any(isinstance(x, str) for x in v):
            node[k] = [SECRET_MASK if isinstance(x, str) and x in gone else x for x in v]
            changed = changed or node[k] != v
        elif isinstance(v, (dict, list)):
            changed = mask_copies(v, was, file) or changed
    if changed and "check" in node:
        node["masked"] = True
    return changed


def mask_edges(graph: dict | None, secrets: list[dict]) -> None:
    """`graph.json`: an edge keeps the text that named its target, as (`from`, `line`), in place."""
    lines = flagged_lines(secrets)
    for e in (graph or {}).get("edges") or []:
        if (e.get("from"), e.get("line")) in lines and isinstance(e.get("text"), str):
            e["text"] = SECRET_MASK


def secrets_of(phrases: dict | None) -> list[dict]:
    return [f for f in (phrases or {}).get("findings") or [] if f.get("check") == "secret.found"]


def mask_reports(reports: dict, *side) -> None:
    """Every step's report masked in place by the secret scan in `02.4-phrases`'s, once no step still needs the words. `reports`:
    {step's name: its report}, any of them absent or None. `side`: reports of the capability step's kept apart (`capability.json`),
    which hold the same findings with every citation."""
    secrets = secrets_of(reports.get(PHRASES))
    if not flagged_lines(secrets):
        return
    was: dict = {}
    mask_secret_lines(secrets + list((reports.get(INVENTORY) or {}).get("findings") or []), was)
    for stage in (READ, GRAPH, PHRASES, BUILDER, PINPOINT):
        mask_secret_lines(secrets + list((reports.get(stage) or {}).get("findings") or []))
    for doc in (reports.get(CAPABILITY), reports.get(BUILDER), *side):
        if doc:
            for f in doc.get("findings") or []:
                mask_copies(f, was)


def mask_reader(reader: dict | None, phrases: dict | None) -> bool:
    """`02.2-reader`'s report masked in place by the secret scan in `02.4-phrases`'s report, which runs after it. Whether a
    finding of the reader is masked now."""
    if not reader or not phrases:
        return False
    findings = reader.get("findings") or []
    mask_secret_lines(secrets_of(phrases) + findings)
    return any(f.get("masked") for f in findings)


def left_out_note(count: int) -> str:
    """The step's note, which the check of the run keeps as a limit (`limitnote`), and the pages show."""
    if count == 1:
        return "1 line the secret scan flagged was left out of what the model read, so it was not examined."
    return f"{count} lines the secret scan flagged were left out of what the model read, so they were not examined."


def is_private_key(kinds) -> bool:
    """Whether a `secret.found` row's kinds name a private key (`PRIVATE_KEY`)."""
    return any(PRIVATE_KEY.search(str(k)) for k in kinds or [])


def key_end(lines: list[str], start: int) -> int | None:
    """The last line of a private key whose first line, `start`, the scan flagged, or None when the key ends on that line: the scan
    flags only the first. Through the line with `KEY_END`, or with none, through the line before the next blank line (a PuTTY file
    has no such line)."""
    if KEY_END in lines[start - 1]:
        return None
    last = next((n for n in range(start + 1, len(lines) + 1) if KEY_END in lines[n - 1]), None)
    if last is None:
        last = next((n - 1 for n in range(start + 1, len(lines) + 1) if not lines[n - 1].strip()), len(lines))
    return last if last > start else None


def _key_body(lines: list[str], start: int) -> range:
    """The lines after a flagged first line of a private key that hold the rest of it, by number (`key_end`)."""
    last = key_end(lines, start)
    return range(start + 1, last + 1) if last else range(0)


class ToSend:
    """What of a file a model read may send, from the `secret.found` rows of `02.4-phrases`. More is held back than a page masks: a page
    can show a line marked as base64 that reads as text (`mask_secret_lines`), and that mark asks only the values the scanner flagged,
    so a key it did not flag can stand beside such text. Sending cannot be taken back, so every flagged line stays here, marked or not; so does a file with a
    skip row, since no row can say what is in it. The scan also writes no row for a lock file (`secret_scan.scannable`), and no read
    takes one: a read takes prose by its extension, and no lock file's name has one."""

    def __init__(self, phrase_findings):
        rows = [f for f in phrase_findings or [] if f.get("check") == "secret.found"]
        self.none_read = any("skipped" in f and f.get("file") is None for f in rows)
        self.unread = {f["file"] for f in rows if "skipped" in f and f.get("file")}
        self.flagged: dict[str, list[dict]] = {}
        for f in rows:
            if "skipped" not in f:
                self.flagged.setdefault(f.get("file"), []).append(f)

    def read(self, rel) -> bool:
        """Whether the scan read this file."""
        return not self.none_read and rel not in self.unread

    def left_out(self, rel, lines) -> set[int]:
        """The numbers of the lines of a file that go to no model: each flagged line, and the rest of a private key."""
        out = set()
        for f in self.flagged.get(rel, []):
            n = f.get("line")
            if isinstance(n, int) and 0 < n <= len(lines):
                out.add(n)
                if is_private_key(f.get("kinds")):  # the scan's `key_end`, and the same rule over these lines for a row saved before it
                    out.update(_key_body(lines, n))
                    if isinstance(f.get("key_end"), int):
                        out.update(range(n + 1, min(f["key_end"], len(lines)) + 1))
        return out

    def lines(self, rel, lines) -> list[str] | None:
        """The lines of a file as a model read may use them: each left-out line a blank at its place. None when the scan did not read
        the file, or there are no lines."""
        if lines is None or not self.read(rel):
            return None
        out = self.left_out(rel, lines)
        return [LEFT_OUT if n in out else x for n, x in enumerate(lines, 1)] if out else lines
