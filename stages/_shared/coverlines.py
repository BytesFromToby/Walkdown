"""Coverage lines: for every check a step makes, what it looked at and how many it found. Spec: specs/shared.SPEC.md, coverlines.

A step's report carries a top-level `coverage` list (M9 slice C). Each line covers one check, or the checks that run in one
pass over the same items:

    {"checks": ["phrase.K.exfil", ...], "unit": "files", "of": 85, "looked_at": 83, "explained": 2, "found": 14}

`of` is how many items the check should look at, counted from the step's inputs before the check runs. `looked_at` is
counted where the check handles an item, inside the function that makes the check. `explained` is the items the check did
not look at and the step says why (a skip finding, an unread or not-scanned entry), counted where that entry is written.
`found` is the findings of the line's checks, counted from the report at the end. The two counts do not come from each other:
a check that skips an item and says nothing leaves `looked_at` plus `explained` short of `of`, and the check of the run
(`05-qa`) holds the run for it. A line holds counts and check IDs only: no file name and no text from the repository.

A step names its lines once (`begin`), counts as it works (`of`, `look`, `explain`), and writes them at the end (`lines`).
The counters are the process's: each step runs as its own process, so one step's counts never reach another's, and a function
that counts while no step has begun (a test, the grader) counts nothing.
"""
from __future__ import annotations

# The units a line may name. `files`: files of the audited copy. `entries`: skills, agents, commands, hook entries, and the
# like, found in files. `uses`: the programs a repository's files run (a command in a script, in a sentence a model follows, or in
# a hook or a server's config). `passages`: runs of prose a model is asked about. `legs`, `grants`: the entries of a fixed table.
# `findings`: findings of an earlier step that this step reads. `run`: the whole run, once.
UNITS = ("files", "entries", "uses", "passages", "findings", "legs", "grants", "run")

_counts: dict[str, list[int]] | None = None   # {line key: [of, looked_at, explained]}
_lines: list[tuple[tuple[str, ...], str]] = []  # the lines of the step that has begun, in order


def key_of(checks) -> str:
    """A line's key: its first check."""
    return checks[0]


def begin(lines) -> None:
    """Start counting for a step. `lines`: [(checks, unit)] in the order they are written."""
    global _counts, _lines
    _lines = [(tuple(checks), unit) for checks, unit in lines]
    for checks, unit in _lines:
        if unit not in UNITS or not checks:
            raise ValueError(f"a coverage line needs checks and one of the units {UNITS}: {checks} {unit}")
    _counts = {key_of(checks): [0, 0, 0] for checks, _ in _lines}


def end() -> None:
    """Stop counting (a test that began a step and is done with it)."""
    global _counts, _lines
    _counts, _lines = None, []


def _add(key: str, slot: int, n: int) -> None:
    """Count for the step that has begun. A key that is not one of its lines counts nothing, as when no step has begun: a
    function shared with another step (a test runs several in one process) is not the one that has begun to count."""
    if _counts is None or key not in _counts:
        return
    _counts[key][slot] += n


def of(key: str, n: int = 1) -> None:
    """`n` more items the check should look at, counted from the step's inputs before the check runs."""
    _add(key, 0, n)


def look(key: str, n: int = 1) -> None:
    """The check handled `n` items. Called where the check handles an item, inside the function that makes the check."""
    _add(key, 1, n)


def explain(key: str, n: int = 1) -> None:
    """`n` items the check did not look at and the step says why, called where the reason is written."""
    _add(key, 2, n)


# What a result is for each check. A finding that carries `skipped` is a skip and no result. The two model reads answer every
# passage they are asked about, so an answer that flags nothing is a read with no result: `found` of a read is its flags (the
# sweep's `flagged`) and, for the pinpoint, the answers whose quote was found in the passage (`verified`).
FLAG = {"soft.sweep": "flagged", "soft.pinpoint": "verified"}
UNNAMED = "(a check with no name that can be shown)"


def is_result(finding) -> bool:
    """Whether a finding is a result of its check, as `found` counts it: not a skip, and for a model read a flag."""
    if "skipped" in finding:
        return False
    key = FLAG.get(finding.get("check"))
    return bool(finding.get(key)) if key else True


def found_in(checks, findings) -> int:
    """The findings of these checks that are results (`is_result`)."""
    wanted = set(checks)
    return sum(1 for f in findings if f.get("check") in wanted and is_result(f))


def lines(findings) -> list[dict]:
    """The `coverage` list of the step's report: one line per line begun, with `found` counted from `findings`. Empty when no
    step has begun. It ends the counting: what a step counted is its own, and the next step to begin starts from nothing."""
    if _counts is None:
        return []
    got = [{"checks": list(checks), "unit": unit, "of": _counts[key_of(checks)][0],
            "looked_at": _counts[key_of(checks)][1], "explained": _counts[key_of(checks)][2],
            "found": found_in(checks, findings)}
           for checks, unit in _lines]
    end()
    return got


# ---------------------------------------------------------------- what a step that went well writes

def audit(checks, report) -> dict:
    """What is wrong with a report's coverage, as data. The check of the run holds a run for these and the tests of each step
    assert there are none, so the rules are stated here once:

    - `missing`: the ids on the step's list (`checks`) that no line names, in the list's order;
    - `off_list`: the checks of the report's findings, skips included, that the list does not have, in the order found;
    - `lines`: for each line with a defect, `{"line", "reasons"}`: `check` (it names an id the list does not have, another
      step's included, or an id another line names too), `short` (`looked_at + explained` is below `of`), `over` (it is
      above), `found` (`found` is not what the findings of the line's checks hold), and `ids` the offending ids.

    A report whose `coverage` is not a list of lines has no audit (`pipeline.read_report` refuses it)."""
    saved = saved_lines(report)
    findings = [f for f in (report.get("findings") or []) if isinstance(f, dict)]
    wanted = list(checks)
    named: dict[str, int] = {}
    for line in saved:
        for c in line["checks"]:
            named[c] = named.get(c, 0) + 1
    # a finding's check with white space in it could start a line of a hold's brief with words a tampered file chose, so it is
    # named by a placeholder
    shown = lambda c: c if valid_id(c) else UNNAMED  # noqa: E731
    out = {"missing": [c for c in wanted if c not in named],
           "off_list": list(dict.fromkeys(shown(f["check"]) for f in findings if f.get("check") not in wanted)),
           "lines": []}
    for line in saved:
        reasons, ids = [], []
        bad = [c for c in line["checks"] if c not in wanted or named[c] > 1]
        if bad:
            reasons.append("check")
            ids = list(dict.fromkeys(bad))
        total = line["looked_at"] + line["explained"]
        if total < line["of"]:
            reasons.append("short")
        elif total > line["of"]:
            reasons.append("over")
        if line["found"] != found_in(line["checks"], findings):
            reasons.append("found")
        if reasons:
            out["lines"].append({"line": line, "reasons": reasons, "ids": ids})
    return out


def problems(checks, report) -> list[str]:
    """Why a report's coverage is not what a step that went well writes, as sentences; empty when it is. Each step's test
    asserts this is empty on its fixtures and on a run of the tool itself: the lines cover exactly the step's `checks` (the
    ids of `stages.json`), each in one line; `looked_at` plus `explained` is `of`, neither more nor less (a count that is too
    high is a broken count too); `found` is the results among the findings of the line's checks; and every finding's check,
    a skip's too, is on the list. `checks`: the step's list."""
    if not valid(report.get("coverage")):
        return ["coverage is not a list of lines"]
    a = audit(checks, report)
    out = [f"{c} has no line" for c in a["missing"]]
    out += [f"{c} is the check of a finding and is not on the step's list" for c in a["off_list"]]
    for d in a["lines"]:
        line, label = d["line"], f"line for {d['line']['checks'][0]}"
        if "check" in d["reasons"]:
            out.append(f"{label}: {', '.join(d['ids'])} is not on the step's list or is named by two lines")
        if "short" in d["reasons"] or "over" in d["reasons"]:
            out.append(f"{label}: looked_at {line['looked_at']} + explained {line['explained']} is not of {line['of']}")
        if "found" in d["reasons"]:
            out.append(f"{label}: found {line['found']} is not the results among the findings of its checks")
    return out


# ---------------------------------------------------------------- reading a saved list

COUNTS = ("of", "looked_at", "explained", "found")


def whole(n) -> bool:
    """A count is a whole number: not a bool, not a float, not below zero."""
    return isinstance(n, int) and not isinstance(n, bool) and n >= 0


def valid_id(c) -> bool:
    """A check id is a word with no white space in it: a line break in an id would start a line of a hold's brief with words
    a tampered file chose."""
    return isinstance(c, str) and c != "" and not any(ch.isspace() for ch in c)


def valid_line(line) -> bool:
    """Whether a saved line has the shape `lines` writes: an object with a list of check ids (each a word with no white
    space), one of the known units, and four whole counts."""
    return (isinstance(line, dict) and isinstance(line.get("checks"), list) and bool(line["checks"])
            and all(valid_id(c) for c in line["checks"]) and line.get("unit") in UNITS
            and all(whole(line.get(k)) for k in COUNTS))


def saved_lines(report) -> list[dict]:
    """The coverage lines of a report that `pipeline.read_report` accepted: its `coverage` list, or none when it has no list
    (a step that writes none, or a run made before slice C)."""
    saved = report.get("coverage") if isinstance(report, dict) else None
    return saved if isinstance(saved, list) else []


def valid(saved) -> bool:
    """Whether a saved `coverage` is readable: a list of valid lines. The object `02.2-reader` wrote under that name
    before M9 slice C (its counts, now `reading`) is no list of lines; `pipeline.read_report` reads it as having none."""
    return isinstance(saved, list) and all(valid_line(x) for x in saved)
