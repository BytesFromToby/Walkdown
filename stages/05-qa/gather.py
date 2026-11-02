"""The gaps and limits of a run, from its facts. Spec: specs/qa.SPEC.md, gather.

A **gap** is something that should be there and is not: a step the run should have run with no output or that failed
(a chosen model read that never started is one, like the coded steps after a crash), a step whose fixture check did not
pass or could not be made, a chosen model read in which no passage got an answer. A **limit** is
something the run did not examine and says so: what a stop left out, a check skipped for a missing optional tool, a
model read with some passages unanswered, the skips the steps name, the standing limits of the method. Every item is
one finding (`qa.gap` or `qa.limit`) naming the step, the check where there is one, what was expected, and what was
there. The items come in the order the report's section 7 lists them (it is the order the report stage gathered them
in until M9 slice B moved the gathering here). Nothing here detects anything in the repository or judges it: it reads the
steps' own saved outputs, the record, and the call logs.

A run is held when it has a gap, and no rule says more. A new kind of gap is one more function that returns items, called
from `gather`, with its own `kind`: the coverage gaps (M9 slice C, `coverage_items`) are the first.
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "_shared"))
import calllog  # noqa: E402
import coverlines  # noqa: E402
import stagelist  # noqa: E402
from limitnote import LIMIT_NOTE  # noqa: E402
from steperror import is_builtin_error  # noqa: E402

GAP, LIMIT, CHECKED = "qa.gap", "qa.limit", "qa.checked"
# The grader's words for a step's fixture check (`validate.Stamp.result`). Any other (ERROR, SETUP ERROR, NOT BUILT) is a check
# that gave no verdict.
PASS, FAIL, NO_FIXTURE_SET = "PASS", "FAIL", "no fixture set"
INCOMPLETE = "INCOMPLETE"  # a check was skipped, usually for a missing optional tool: a limit and no gap (owner, 2026-10-25)
INTAKE, QA = stagelist.INTAKE, stagelist.QA
CODED, AI_STAGES = stagelist.CODED, stagelist.AI_STAGES
# The one step with no fixtures by design (restructure decision 5-C): the grader stamps Pinpoint `no fixture set`, and that is
# no gap for it. For every other step it is one: they have fixtures, and a fixtures folder that is gone or empty stamps each
# of them so, which leaves their zeros as unvalidated as a failed check does.
NO_FIXTURES_BY_DESIGN = (AI_STAGES[-1],)
READER, GRAPH, CAPABILITY = "02.2-reader", "02.3-graph", "02.5-capability"
# the limits that stand for every run, by the id the report words them under (`render.STANDING_LIMITS`)
STANDING = ("static", "model-reads", "version-drift", "english-only", "phrases-zero")

NOT_STARTED_FOUND = {"sweep-no-answer": "not started: the step before it got no answer for any passage"}
MISSING_FOUND = {"failed": "no output: the step failed", "not-started": "no output: the step did not start",
                 "output-missing": "its saved output is not in the run folder",
                 "output-unreadable": "its saved output cannot be read"}


def item(check: str, kind: str, step: str | None, expected=None, found=None, step_check=None, file=None, **fields):
    """One finding. `file` is the repository file a skip or an unread file names; `step_check` the check the item is
    about, where there is one."""
    return {"check": check, "file": file, "line": None, "kind": kind, "step": step, "step_check": step_check,
            "expected": expected, "found": found, **fields}


def findings(report) -> list:
    return (report or {}).get("findings", [])


def of_check(facts, stage: str, check: str) -> list:
    return [f for f in findings(facts.reports.get(stage)) if f.get("check") == check]


def stopped_left(stop) -> tuple[str, ...]:
    """The coded steps a stop left out: those after the step it stopped at."""
    if not stop:
        return ()
    cut = stagelist.position(stop["after"])
    return tuple(s for s in CODED if stagelist.position(s) > cut)


def started_of(facts) -> dict:
    """{stage: the record's row} for each step the runner started."""
    return {s["stage"]: s for s in facts.steps}


def why_missing(facts, stage: str) -> str | None:
    """Why a step has no output, or None when it has: it failed (the record says so), its saved output cannot be read
    or is not in the folder, or the step never started."""
    row = started_of(facts).get(stage)
    if row is not None and not row.get("ok"):
        return "failed"
    if stage in facts.unreadable:
        return "output-unreadable"
    if stage not in facts.reports:
        return "output-missing" if row is not None else "not-started"
    return None


# ---------------------------------------------------------------- the steps: output and fixture check

def cause_of_failure(facts, stage: str) -> str | None:
    """What Walkdown knows of why a step failed, in its words: the error's type (one of Python's own), and the module of
    a missing import when it is one of Walkdown's packages. Never the rest of an error's message (it can carry text from
    the audited repository)."""
    kind, module = facts.errors.get(stage, (None, None))
    if kind is None:  # the record keeps the type too: `exit 1: ValueError`
        name = ((started_of(facts).get(stage) or {}).get("error") or "").partition(": ")[2]
        kind = name if is_builtin_error(name) else None
    return None if kind is None else kind + (f" ({module})" if module else "")


def missing_item(facts, stage: str, why: str, left: tuple):
    """A limit when a stop left the step out, else the gap that it has no output."""
    if stage in left:
        after = facts.stop["after"]
        return item(LIMIT, "stopped", stage, "the step to run", f'not run: the run stopped after "{after}" (--until)',
                    after=after)
    error = (started_of(facts).get(stage) or {}).get("error")
    found = MISSING_FOUND[why] + (f" ({error})" if why == "failed" and error else "")
    return item(GAP, "step-missing", stage, "the step's saved output", found, why=why, error=error,
                cause=cause_of_failure(facts, stage) if why == "failed" else None)


def fixture_item(facts, stage: str):
    """The finding for a step whose fixture check did not pass. A gap: `fixture-failed` for a FAIL (the step ran and gave a
    wrong answer on its fixtures), and `fixture-unchecked` for a check that gave no verdict (ERROR, SETUP ERROR, NOT BUILT,
    and `no fixture set` for a step that has fixtures). For INCOMPLETE (a check skipped for a missing optional tool) a limit.
    None for a pass, Pinpoint's `no fixture set`, and a run made without validation (no stamp)."""
    st = facts.stamps.get(stage)
    if st is None or st.result == PASS or (st.result == NO_FIXTURE_SET and stage in NO_FIXTURES_BY_DESIGN):
        return None
    if st.result == INCOMPLETE:
        kind, check = "fixture-incomplete", LIMIT
    else:
        kind, check = ("fixture-failed" if st.result == FAIL else "fixture-unchecked"), GAP
    return item(check, kind, stage, "its fixture check passes", f"its fixture check gave {st.result}",
                result=st.result, stamp=st.to_dict())


def held_back(facts, stage: str) -> bool:
    """Whether the record says why a chosen model read has no step: the run stopped before it (`--until`; its input file is
    written when it was next), or it was not started because the read before it got no answer. The pages draw each from the
    record, and the check counts neither as a read that did not start."""
    if stage in {n["stage"] for n in facts.not_started}:
        return True
    return facts.stop is not None and stagelist.position(stage) > stagelist.position(facts.stop["after"])


def step_items(facts) -> list:
    """For each step that should have run, in order (intake, the coded steps, the model reads that were started or chosen,
    then this check itself): a gap when it has no output, a limit when a stop left it out, else what its fixture check
    gave. A chosen read with no step is a gap (it never started: a step before it failed), unless the record says why
    (`held_back`). This check is looked at last, and only by its fixture check: its own output is not made yet."""
    left = stopped_left(facts.stop)
    ai = [s for s in AI_STAGES if s in started_of(facts) or s in facts.chosen]
    out = []
    for stage in (INTAKE, *CODED, *ai):
        why = why_missing(facts, stage)
        if why == "not-started" and stage in AI_STAGES and held_back(facts, stage):
            continue
        got = missing_item(facts, stage, why, left) if why else fixture_item(facts, stage)
        if got:
            out.append(got)
    last = fixture_item(facts, QA)
    return out + ([last] if last else [])


# ---------------------------------------------------------------- what each check looked at (M9 slice C)

def coverage_items(facts) -> list:
    """A gap for a check a step makes and has no coverage line for (`coverage-missing`, once for the step, naming every check
    left out), and for a line whose items do not add up: `looked_at` plus `explained` below `of` is items the check neither
    looked at nor explained (`coverage-short`), above `of` is a count that is broken (`coverage-broken`). Only a step that
    went well and left a readable output is held to this: a step with no output has its gap already (`step_items`), a step a
    stop left out has nothing to check, and a model read that got no answer for any passage has `looked_at` 0 with its
    passages explained by their skips, so its own gap is the one gap. A step whose `coverage` cannot be read has no readable
    output (`pipeline.read_report`): the same one gap. Counts and check ids only; nothing from the repository."""
    out = []
    for stage in named_steps(facts):
        if why_missing(facts, stage) is not None or stage not in facts.reports:
            continue
        wanted = stagelist.checks(stage)
        a = coverlines.audit(wanted, facts.reports[stage])  # the rules, stated once (coverlines.audit)
        missing = a["missing"] + [c for c in a["off_list"] if c not in a["missing"]]  # a finding's check with no line is missing too
        if missing:
            out.append(item(GAP, "coverage-missing", stage, "a coverage line for each of its checks",
                            f"no coverage line for {len(missing)} of {len(wanted) + len(a['off_list'])} checks",
                            step_check=missing[0], missing=missing, checks_total=len(wanted) + len(a["off_list"])))
        findings_of = findings(facts.reports[stage])
        for d in a["lines"]:
            line, why = d["line"], d["reasons"]
            of_, looked, explained = line["of"], line["looked_at"], line["explained"]
            kind = ("coverage-broken" if "check" in why else "coverage-short" if "short" in why
                    else "coverage-broken")
            reason = ("check" if "check" in why else "count" if "short" in why or "over" in why else "found")
            out.append(item(GAP, kind, stage, f"{of_} {line['unit']} looked at or explained",
                            f"{looked} looked at and {explained} explained", step_check=line["checks"][0],
                            checks=line["checks"], unit=line["unit"], of=of_, looked_at=looked, explained=explained,
                            why=reason, ids=d["ids"], found_line=line["found"],
                            found_actual=coverlines.found_in(line["checks"], findings_of)))
    return out


# ---------------------------------------------------------------- the model reads

def reasons_of(report) -> list:
    """[[reason, count]] for the passages that got no answer, most common first."""
    why = collections.Counter(f["skipped"] for f in findings(report) if f.get("qid") and "skipped" in f)
    return [[reason, count] for reason, count in why.most_common()]


def model_items(facts) -> list:
    """One item for each model read that ran and has passages with no answer even after the retry: a gap when none
    got an answer, a limit when only some did not."""
    out = []
    for stage in AI_STAGES:
        report = facts.reports.get(stage)
        if report is None or stage not in started_of(facts):
            continue
        asked, none = calllog.tally(report)
        if not none:
            continue
        reasons = reasons_of(report)
        all_none = asked == none
        check = next((f["check"] for f in findings(report) if f.get("qid")), None)
        out.append(item(GAP if all_none else LIMIT, "model-no-answer" if all_none else "model-partial", stage,
                        "an answer for at least one passage" if all_none else "an answer for every passage",
                        f"{none} of {asked} passages got no answer", step_check=check, asked=asked, none=none,
                        reasons=reasons, calls=report.get("calls"), logged=facts.logs.get(stage),
                        cause="; ".join(f"{r} ({c})" for r, c in reasons) or None))
    return out


def not_started_items(facts) -> list:
    """A chosen step that was not started because the step before it got no answer (counted once: the gap is the read)."""
    return [item(LIMIT, "not-started", n["stage"], "the step to start", NOT_STARTED_FOUND.get(n["why"], "not started"),
                 why=n["why"]) for n in facts.not_started]


def dropped_items(facts) -> list:
    """A model read an earlier command chose and `continue` left out: something the run did not check, so a limit. It is no
    gap: the person went on without it, and choosing a read at `continue` is the consent to send."""
    return [item(LIMIT, "read-dropped", s, "the model read an earlier command chose", "did not run at continue",
                 backends=facts.backends, stopped=facts.stop is not None) for s in facts.dropped]


# ---------------------------------------------------------------- what the steps themselves say they skipped

def named_steps(facts) -> list:
    return [*CODED, *(s for s in AI_STAGES if s in started_of(facts))]


def skip_items(facts, counted: set) -> list:
    """The checks the steps skipped (a finding with `skipped`) and the notes that name a limit, once each. Only a step's
    own notes (`note: ...`, from a step that finished) are read: a failed step gives none, and nothing else on a step's
    stderr (`facts.notes`). A model read whose passages are counted gives neither its passage skips nor its
    `skipped: ...` note."""
    out, seen = [], set()
    for stage in named_steps(facts):
        for f in findings(facts.reports.get(stage)):
            if "skipped" in f and not (stage in counted and f.get("qid")):
                key = ("skip", f["check"], f.get("file"), f["skipped"])
                if key not in seen:
                    seen.add(key)
                    out.append(item(LIMIT, "skip", stage, "the check ran", f"skipped: {f['skipped']}",
                                    step_check=f["check"], file=f.get("file"), reason=f["skipped"]))
        for line in facts.notes.get(stage, []):
            key = ("note", line)
            if LIMIT_NOTE.search(line) and key not in seen and not (stage in counted and line.startswith("skipped: ")):
                seen.add(key)
                out.append(item(LIMIT, "note", stage, None, None, text=line))
    for u in of_check(facts, READER, "read.unread"):
        key = ("unread", u["file"], u.get("reason"))
        if key not in seen:
            seen.add(key)
            out.append(item(LIMIT, "unread", READER, "the file read", f"not read: {u.get('reason')}",
                            step_check="read.unread", file=u["file"], reason=u.get("reason")))
    return out


def file_items(facts) -> list:
    """The files the graph did not scan for references, and the test data set aside from the capability map."""
    out = [item(LIMIT, "unscanned", GRAPH, "scanned for references", f"not scanned: {u.get('reason')}",
                step_check="graph.unscanned", file=u["file"], reason=u.get("reason"))
           for u in of_check(facts, GRAPH, "graph.unscanned")]
    for t in of_check(facts, CAPABILITY, "cap.testdata"):
        inv, phr = t.get("inventory_set_aside", 0), t.get("phrases_set_aside", 0)
        out.append(item(LIMIT, "testdata", CAPABILITY, "test data in the capability map",
                        f"{inv + phr} findings kept out of it", step_check="cap.testdata",
                        inventory_set_aside=inv, phrases_set_aside=phr))
    return out


def checked_items(facts) -> list:
    """For each coverage line of a step in which a check found nothing: what that check looked at (M9 slice C), so "found
    none" is said with the number of items behind it. These are no limits (`qa.checked`). One item for a line, naming the
    checks of it that found nothing. A step gets lines only when its fixture check measured its "none": a stamp that is a pass
    or INCOMPLETE with some rows measured (`Stamp.measured`), so a step that failed or could not be checked, Pinpoint (no
    fixtures by design), a read whose rows were all skipped, and a run made without validation get none. A check with a skip
    of its own in the report is not named as found none, and a line none of whose checks is left has no item. A line that does
    not add up is a gap and is not said here, and neither is one whose items were all explained by skips (nothing was looked
    at: the skips say why), or one of the whole run (`run`). A line with no items says so."""
    out = []
    for stage in named_steps(facts):
        if why_missing(facts, stage) is not None or stage not in facts.reports:
            continue
        stamp = facts.stamps.get(stage)
        if stamp is None or not stamp.measured:
            continue
        report = facts.reports[stage]
        skipped = {f["check"] for f in findings(report) if "skipped" in f}
        for line in coverlines.saved_lines(report):
            none = [c for c in line["checks"]
                    if c not in skipped and not coverlines.found_in([c], findings(report))]
            if not none or line["unit"] == "run" or line["looked_at"] + line["explained"] != line["of"]:
                continue
            if line["of"] > 0 and line["looked_at"] == 0:
                continue
            out.append(item(CHECKED, "checked", stage, "the items of its inputs checked",
                            f"{line['looked_at']} checked, none found", step_check=none[0], checks=none,
                            unit=line["unit"], of=line["of"], looked_at=line["looked_at"], explained=line["explained"]))
    return out


def standing_items() -> list:
    return [item(LIMIT, "standing", None, id=i) for i in STANDING]


# ---------------------------------------------------------------- the whole run

def gather(facts) -> list:
    """Every gap and limit of the run, in section 7's order."""
    steps = step_items(facts) + coverage_items(facts)
    models = model_items(facts)
    counted = {m["step"] for m in models}
    return (steps + models + not_started_items(facts) + dropped_items(facts) + skip_items(facts, counted)
            + file_items(facts) + checked_items(facts) + standing_items())


def report(facts) -> dict:
    """The check's report: contract 1, `qa.gap`, `qa.limit`, and `qa.checked` findings."""
    return {"stage": QA, "contract": 1, "findings": gather(facts)}
