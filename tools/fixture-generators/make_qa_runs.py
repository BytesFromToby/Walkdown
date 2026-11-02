"""Write the fixtures of the check of the run: `Fixtures/05-qa/<case>/`, one small synthetic run folder each, and
the answer rows for them, `Fixtures/ANSWERS/05-qa.json` (M9 slice B, 2026-10-30).

    python tools/fixture-generators/make_qa_runs.py          (then: python tools/grader/grader.py --rehash 05-qa)

A case is what a run folder holds that the check reads: `data/run.json` (the record) and the saved outputs of the
steps, plus a call log where a model read has one. They hold Walkdown's own words and invented names only; nothing
in them comes from a real repository. A gate row is a gap the check must find, a negative row a run it must not hold,
and a gate row on `qa.limit` shows what the run says instead of holding. The hashes of the files are written by the
grader's `--rehash`, as for every fixture. Dev-only: it writes into `Fixtures/`.
"""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Fixtures" / "05-qa"
SHEET = ROOT / "Fixtures" / "ANSWERS" / "05-qa.json"

T0, T1 = "2026-01-01T00:00:00+00:00", "2026-01-01T00:01:00+00:00"
CODED = ["02.1-inventory", "02.2-reader", "02.3-graph", "02.4-phrases", "02.5-capability", "02.6-builder"]
STEPS = ["01-intake", *CODED]
PASS = {"result": "PASS", "gate": "1/1", "negative": "1/1", "recall": None, "skipped": [], "cached": None}


def stamp(result, **kw):
    return {**PASS, "result": result, **kw}


def step(stage, ok=True, error=None):
    return {"stage": stage, "ok": ok, "started": T0, "finished": T1 if ok else None, "error": error}


AUTO = object()  # "give the step the coverage a step that went well has"
CHECKS = {s["name"]: s["checks"] for s in json.loads((ROOT / "stages" / "stages.json").read_text(encoding="utf-8"))["stages"]
          if s.get("checks")}


def good_coverage(stage, findings):
    """The coverage list of a step that went well (M9 slice C): one line for all of its checks, every item looked at or
    explained by a skip finding. A coded step looked at three files; a model step asked about the passages in its findings."""
    checks = CHECKS.get(stage)
    if not checks:
        return None
    skipped = sum(1 for f in findings if "skipped" in f)
    if stage in ("03-sweep", "04-pinpoint"):
        asked = sum(1 for f in findings if f.get("qid"))
        skipped = sum(1 for f in findings if f.get("qid") and "skipped" in f)
        return [coverage_line(checks, "passages", asked, asked - skipped, skipped, results(findings))]
    return [coverage_line(checks, "files", 3, 3 - skipped, skipped, results(findings))]


FLAG = {"soft.sweep": "flagged", "soft.pinpoint": "verified"}


def results(findings):
    """What `found` counts (`coverlines.found_in`): a finding that is no skip, and for a model read one that flags."""
    return sum(1 for f in findings if "skipped" not in f and (f.get(FLAG[f["check"]]) if f.get("check") in FLAG else True))


def coverage_line(checks, unit, of, looked_at, explained, found):
    return {"checks": list(checks), "unit": unit, "of": of, "looked_at": looked_at, "explained": explained,
            "found": found}


def report(stage, findings=(), coverage=AUTO, **extra):
    doc = {"stage": stage, "contract": 1, **extra, "findings": list(findings)}
    lines = good_coverage(stage, findings) if coverage is AUTO else coverage
    if lines is not None:
        doc["coverage"] = lines
    return doc


def record(steps, stamps=None, **keys):
    return {"format": 3, "finished": T1, "context": 32000, "hosts": [],
            "steps": steps, "stamps": stamps if stamps is not None else {}, **keys}


def all_pass(stages=STEPS):
    return {s: stamp("PASS") for s in stages}


def sweep_finding(n, skipped=None):
    f = {"check": "soft.sweep", "file": "fixture.md", "line": n, "end_line": n + 1,
         "qid": f"sweep:fixture.md:{n}", "backend": "jev"}
    return {**f, "skipped": skipped} if skipped else {**f, "model": "fixture-model", "kind": "none"}


def sweep_report(findings, calls=None, **kw):
    return report("03-sweep", findings, backends=[{"role": "sweep", "backend": "jev", "remote": True,
                                                    "model": "fixture-model"}],
                  **({"calls": calls} if calls else {}), **kw)


def call_row(n, why):
    return {"qid": f"sweep:fixture.md:{n}", "backend": "jev", "first": None,
            "retry": {"result": "not tried", "why": why}, "at": T0}


def run_folder(name, steps=None, outputs=None, rec=None, logs=None, drop=()):
    """`steps`: the stages that ran; `outputs`: {stage: report} beyond the empty ones every step gets;
    `rec`: the record; `logs`: {file name: [rows]}; `drop`: outputs left out of the folder."""
    steps = list(STEPS if steps is None else steps)
    folder = OUT / name / "data"
    folder.mkdir(parents=True)
    docs = {s: report(s) for s in steps if s not in drop}
    docs.update(outputs or {})
    for stage, doc in docs.items():
        if stage not in drop:
            put(folder / f"{stage}.json", doc)
    put(folder / "run.json", rec if rec is not None else record([step(s) for s in steps], all_pass(steps)))
    for file, rows in (logs or {}).items():
        (folder / file).write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8", newline="\n")


def put(path, doc):
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")


def gap(id_, step_, kind, note, **match):
    return row(id_, "gate", "qa.gap", note, step=step_, kind=kind, **match)


def row(id_, polarity, check, note, count=None, **match):
    r = {"id": id_, "polarity": polarity, "check": check,
         "match": {k: ({v[0]: v[1]} if isinstance(v, tuple) else {"eq": v}) for k, v in match.items()},
         "note": note}
    if count is not None:
        r["count"] = count
    if not r["match"]:
        del r["match"]
    return r


def held_not(id_, note):
    return row(id_, "negative", "qa.gap", note)


if OUT.exists():  # the folders below are made as this file runs, so a re-run starts from a clean slate
    shutil.rmtree(OUT)
CASES = {}


# a run with nothing wrong: no gap, and the limits every run has
run_folder("clean")
CASES["clean"] = ("Every step ran, every fixture check passed: nothing to hold.", [
    held_not("qa-clean-no-gap", "a complete run is not held"),
    row("qa-clean-standing-limits", "gate", "qa.limit", "the standing limits of the method are in every run",
        kind="standing"),
    row("qa-clean-checked-found-none", "gate", "qa.checked", "a check that found nothing says what it looked at (M9 slice C)",
        kind="checked", step="02.4-phrases", looked_at=3, unit="files"),
    row("qa-clean-checked-is-no-limit", "negative", "qa.limit", "what a check looked at is no limit", kind="checked"),
])

# a step failed: it has no output, and the steps after it never started
run_folder(
    "step-failed", steps=STEPS[:4], drop=("02.3-graph",),
    rec=record([*[step(s) for s in STEPS[:3]], step("02.3-graph", ok=False, error="exit 1: ValueError")],
               all_pass(STEPS[:3])))
CASES["step-failed"] = ("A step failed in the record and left no output; the three after it never started.", [
    gap("qa-failed-step", "02.3-graph", "step-missing", "gap 1: the step that failed", why="failed",
        found=("contains", "failed")),
    gap("qa-failed-later-phrases", "02.4-phrases", "step-missing", "never started after the failure",
        why="not-started"),
    gap("qa-failed-later-capability", "02.5-capability", "step-missing", "never started after the failure",
        why="not-started"),
    gap("qa-failed-later-builder", "02.6-builder", "step-missing", "never started after the failure",
        why="not-started"),
    row("qa-failed-count", "gate", "qa.gap", "one gap for each of the four steps", count=4, kind="step-missing"),
    row("qa-failed-earlier-step-is-no-gap", "negative", "qa.gap", "a step that went well before it is no gap",
        step="02.2-reader"),
])

# the record says a step went well and its output is not in the folder
run_folder("output-missing", drop=("02.2-reader",))
CASES["output-missing"] = ("The record says every step went well; one saved output is not in the folder.", [
    gap("qa-output-missing", "02.2-reader", "step-missing", "a step with no saved output", why="output-missing"),
    row("qa-output-missing-count", "gate", "qa.gap", "this one gap and no other", count=1),
])

# a saved output that does not read as a report
run_folder("output-unreadable")
(OUT / "output-unreadable" / "data" / "02.3-graph.json").write_text("not a report\n", encoding="utf-8", newline="\n")
CASES["output-unreadable"] = ("The record says every step went well; one saved output is there and does not read as a "
                              "report.", [
    gap("qa-output-unreadable", "02.3-graph", "step-missing", "an output that cannot be read is no output",
        why="output-unreadable"),
    row("qa-output-unreadable-count", "gate", "qa.gap", "this one gap and no other", count=1),
])

# fixture checks that did not pass: FAIL holds as a failed check, ERROR as one that could not be made, PASS does not
run_folder("fixture-failed", rec=record(
    [step(s) for s in STEPS],
    {**all_pass(), "02.4-phrases": stamp("FAIL", gate="1/2"), "02.1-inventory": stamp("ERROR")}))
CASES["fixture-failed"] = ("Two steps ran and did not pass their fixture check: their zeros cannot be trusted.", [
    gap("qa-fixture-fail", "02.4-phrases", "fixture-failed", "FAIL: the step ran and failed its check",
        result="FAIL"),
    gap("qa-fixture-error", "02.1-inventory", "fixture-unchecked", "ERROR: the check gave no result", result="ERROR"),
    row("qa-fixture-count-failed", "gate", "qa.gap", "one step failed its check", count=1, kind="fixture-failed"),
    row("qa-fixture-count-unchecked", "gate", "qa.gap", "one step could not be checked", count=1,
        kind="fixture-unchecked"),
    row("qa-fixture-pass-is-no-gap", "negative", "qa.gap", "a step that passed is no gap", step="02.3-graph"),
])

# a check that gave no verdict is not a pass: SETUP ERROR, NOT BUILT, and no fixture set on a step that has fixtures
run_folder("fixture-unchecked", rec=record(
    [step(s) for s in STEPS],
    {**all_pass(), "02.1-inventory": stamp("SETUP ERROR"), "02.2-reader": stamp("NOT BUILT"),
     "02.3-graph": stamp("no fixture set")}))
CASES["fixture-unchecked"] = ("Three steps could not be checked against their fixtures (the grader could not run, the "
                              "check is not built, no fixtures are in the folder): a zero is not validated.", [
    gap("qa-unchecked-setup-error", "02.1-inventory", "fixture-unchecked", "SETUP ERROR is no pass",
        result="SETUP ERROR"),
    gap("qa-unchecked-not-built", "02.2-reader", "fixture-unchecked", "NOT BUILT is no pass", result="NOT BUILT"),
    gap("qa-unchecked-no-fixtures", "02.3-graph", "fixture-unchecked", "a coded step with no fixture set is no pass",
        result="no fixture set"),
    row("qa-unchecked-count", "gate", "qa.gap", "the three, and not the steps that passed", count=3,
        kind="fixture-unchecked"),
    row("qa-unchecked-pass-is-no-gap", "negative", "qa.gap", "a step that passed is no gap", step="02.4-phrases"),
])

# Pinpoint has no fixtures by design, and its stamp says so: that is no gap
run_folder(
    "no-fixtures-by-design", steps=[*STEPS, "03-sweep", "04-pinpoint"],
    outputs={"03-sweep": sweep_report([]), "04-pinpoint": report("04-pinpoint")},
    rec=record([step(s) for s in [*STEPS, "03-sweep", "04-pinpoint"]],
               {**all_pass([*STEPS, "03-sweep"]), "04-pinpoint": stamp("no fixture set")},
               chosen=["03-sweep", "04-pinpoint"]))
CASES["no-fixtures-by-design"] = ("A pinpoint that read nothing, stamped no fixture set: Pinpoint has no fixtures "
                                  "by design, so nothing is wrong with it.", [
    held_not("qa-pinpoint-no-fixtures-no-gap", "no fixture set is a gap on every step but Pinpoint"),
    row("qa-pinpoint-no-checked", "negative", "qa.checked", "its none is not measured, so it gets no line",
        step="04-pinpoint"),
])

# the check of the run applies its own rule to itself
run_folder("own-check-failed", rec=record([step(s) for s in STEPS], {**all_pass(), "05-qa": stamp("FAIL")}))
CASES["own-check-failed"] = ("The stamp of the check of the run itself is FAIL: its zero cannot be trusted either.", [
    gap("qa-own-fail", "05-qa", "fixture-failed", "the check holds a run when its own fixtures fail",
        result="FAIL"),
])

# a model read in which no passage got an answer; the read after it was not started and is not a second gap
calls = {"log": "03-sweep.calls.jsonl", "answered_on_retry": 0, "not_sent": 3}
run_folder(
    "model-no-answer", steps=[*STEPS, "03-sweep"],
    outputs={"03-sweep": sweep_report([sweep_finding(n, "jev: no key") for n in (1, 5, 9)], calls)},
    rec=record([step(s) for s in [*STEPS, "03-sweep"]], all_pass([*STEPS, "03-sweep"]),
               not_started=[{"stage": "04-pinpoint", "why": "sweep-no-answer"}], chosen=["03-sweep", "04-pinpoint"]),
    logs={"03-sweep.calls.jsonl": [call_row(n, "jev: no key") for n in (1, 5, 9)]})
CASES["model-no-answer"] = ("A chosen sweep asked about three passages and none got an answer (no key); "
                            "the pinpoint was not started.", [
    gap("qa-model-none", "03-sweep", "model-no-answer", "no passage got an answer", step_check="soft.sweep",
        asked=3, none=3),
    row("qa-model-counted-once", "gate", "qa.gap", "the pinpoint that was not started is no second gap", count=1),
    row("qa-model-pinpoint-not-started", "gate", "qa.limit", "the pinpoint is named as not started",
        kind="not-started", step="04-pinpoint"),
])

# a chosen model read that failed
run_folder("ai-step-failed", steps=[*STEPS, "03-sweep"], drop=("03-sweep",),
           rec=record([*[step(s) for s in STEPS], step("03-sweep", ok=False, error="exit 1: KeyError")],
                      all_pass(STEPS)))
CASES["ai-step-failed"] = ("A chosen sweep crashed and left no output.", [
    gap("qa-ai-failed", "03-sweep", "step-missing", "a chosen model read with no output", why="failed"),
    row("qa-ai-failed-count", "gate", "qa.gap", "that one gap", count=1),
])

# not gaps: a check skipped for a missing optional tool
run_folder(
    "optional-tool-missing",
    outputs={"02.2-reader": report("02.2-reader", [{"check": "read.divergence", "file": "fixture.png", "line": None,
                                                    "skipped": "tesseract not installed"}])},
    rec=record([step(s) for s in STEPS], {**all_pass(), "02.2-reader": stamp("INCOMPLETE", skipped=["rd-img-ocr"])}))
CASES["optional-tool-missing"] = ("A check was skipped because an optional tool is not installed (INCOMPLETE): "
                                  "named in the limits, the run goes on.", [
    held_not("qa-tool-no-gap", "a missing optional tool is not a gap (owner, 2026-10-25)"),
    row("qa-tool-incomplete", "gate", "qa.limit", "the INCOMPLETE stamp is a limit", kind="fixture-incomplete",
        step="02.2-reader"),
    row("qa-tool-skip", "gate", "qa.limit", "the skipped check is a limit", kind="skip", step="02.2-reader"),
])

# a stop leaves steps out; they are not gaps
run_folder("stopped", steps=STEPS[:4], rec=record([step(s) for s in STEPS[:4]], all_pass(STEPS[:4]),
                                                   until="02.3-graph"))
CASES["stopped"] = ("The run stopped after 02.3-graph, as asked: the steps after it are left out and nothing is missing.", [
    held_not("qa-stopped-no-gap", "the steps a stop left out are not gaps"),
    row("qa-stopped-limits", "gate", "qa.limit", "each step the stop left out is named", count=3, kind="stopped"),
])

# a model read with some passages unanswered
calls = {"log": "03-sweep.calls.jsonl", "answered_on_retry": 1, "not_sent": 0}
run_folder(
    "partial-read", steps=[*STEPS, "03-sweep"],
    outputs={"03-sweep": sweep_report([sweep_finding(1), sweep_finding(3, "jev: TypeSafeRateLimitError, status 429"),
                                       sweep_finding(5), sweep_finding(7, "jev: TypeSafeRateLimitError, status 429"),
                                       sweep_finding(9)], calls)},
    rec=record([step(s) for s in [*STEPS, "03-sweep"]], all_pass([*STEPS, "03-sweep"])),
    logs={"03-sweep.calls.jsonl": [
        {"qid": f"sweep:fixture.md:{n}", "backend": "jev", "first": {"kind": "TypeSafeRateLimitError", "status": 429},
         "retry": retry, "at": T0}
        for n, retry in ((3, {"result": "no answer", "kind": "TypeSafeRateLimitError", "status": 429}),
                         (5, {"result": "answered"}),
                         (7, {"result": "no answer", "kind": "TypeSafeRateLimitError", "status": 429}))]})
CASES["partial-read"] = ("A sweep got answers for three of five passages: counted in section 7 and nothing is held.", [
    held_not("qa-partial-no-gap", "a read with some passages unanswered is not a gap (owner, 2026-10-30)"),
    row("qa-partial-limit", "gate", "qa.limit", "the count is a limit", kind="model-partial", step="03-sweep",
        asked=5, none=2),
])

# a chosen read that wrote its input and waits: the run stopped just before it
run_folder("waiting-read", rec=record([step(s) for s in STEPS], all_pass(),
                                      until="02.6-builder", chosen=["03-sweep", "04-pinpoint"],
                                      prepared={"stage": "03-sweep", "items": 4, "backend": "jev"}))
CASES["waiting-read"] = ("The run stopped before a chosen model read, which wrote its input file and sent "
                         "nothing: nothing is missing, and the read is not counted a second time.", [
    held_not("qa-waiting-no-gap", "a model read waiting after a stop is not a gap, chosen and not started"),
])

# a stop before a read that was chosen: still a stop, and no read that did not start
run_folder("stopped-before-chosen-read", steps=STEPS[:4],
           rec=record([step(s) for s in STEPS[:4]], all_pass(STEPS[:4]), until="02.3-graph", chosen=["03-sweep"]))
CASES["stopped-before-chosen-read"] = ("The run stopped after 02.3-graph, as asked, with a sweep chosen: the sweep is "
                                       "left out by the stop and is not a gap.", [
    held_not("qa-stopped-chosen-no-gap", "a chosen read that a stop is before is not a read that did not start"),
    row("qa-stopped-chosen-limits", "gate", "qa.limit", "the coded steps the stop left out", count=3, kind="stopped"),
])

# a step crashed before a chosen read: the read never started
run_folder(
    "chosen-read-not-started", steps=STEPS[:4], drop=("02.3-graph",),
    rec=record([*[step(s) for s in STEPS[:3]], step("02.3-graph", ok=False, error="exit 1: ValueError")],
               all_pass(STEPS[:3]), chosen=["03-sweep", "04-pinpoint"]))
CASES["chosen-read-not-started"] = ("The graph step crashed with a sweep and a pinpoint chosen: neither read started, "
                                    "and each is a gap like the coded steps after the crash.", [
    gap("qa-chosen-sweep-not-started", "03-sweep", "step-missing", "a chosen read that never started",
        why="not-started"),
    gap("qa-chosen-pinpoint-not-started", "04-pinpoint", "step-missing", "a chosen read that never started",
        why="not-started"),
    row("qa-chosen-gap-count", "gate", "qa.gap", "the crashed step, the three coded steps after it, and the two reads",
        count=6, kind="step-missing"),
])

# saved outputs that are valid JSON and are not a report (a list, an empty object)
run_folder("output-empty-list")
(OUT / "output-empty-list" / "data" / "02.3-graph.json").write_text("[]\n", encoding="utf-8", newline="\n")
(OUT / "output-empty-list" / "data" / "02.4-phrases.json").write_text("{}\n", encoding="utf-8", newline="\n")
CASES["output-empty-list"] = ("Two saved outputs read as JSON and are not reports (a bare list, an empty object): "
                              "no output, the same as one that cannot be read.", [
    gap("qa-empty-list", "02.3-graph", "step-missing", "a list is not a report", why="output-unreadable"),
    gap("qa-empty-object", "02.4-phrases", "step-missing", "an empty object is not a report",
        why="output-unreadable"),
    row("qa-empty-count", "gate", "qa.gap", "those two gaps and no other", count=2),
])

# saved outputs that are JSON documents with the wrong kind of findings (a number, an empty object)
run_folder("output-bad-findings")
(OUT / "output-bad-findings" / "data" / "02.2-reader.json").write_text(
    '{"stage": "02.2-reader", "contract": 1, "findings": [1]}\n', encoding="utf-8", newline="\n")
(OUT / "output-bad-findings" / "data" / "02.3-graph.json").write_text(
    '{"stage": "02.3-graph", "contract": 1, "findings": [{}]}\n', encoding="utf-8", newline="\n")
CASES["output-bad-findings"] = ("Two saved outputs hold a list of findings and a finding is not one (a number, an "
                                "object with no check): no output, the same as one that cannot be read.", [
    gap("qa-bad-number", "02.2-reader", "step-missing", "a finding that is a number is no report",
        why="output-unreadable"),
    gap("qa-bad-object", "02.3-graph", "step-missing", "a finding with no check is no report", why="output-unreadable"),
    row("qa-bad-count", "gate", "qa.gap", "those two gaps and no other", count=2),
])

# model reads chosen by an earlier command and not at `continue`: not run, said as a limit, and no gap
run_folder("read-dropped", rec=record([step(s) for s in STEPS], all_pass(),
                                      dropped=["03-sweep", "04-pinpoint"],
                                      backends={"03-sweep": "jev", "04-pinpoint": "claude-cli"}))
CASES["read-dropped"] = ("A sweep and a pinpoint were chosen by the first command, which stopped; `continue` did not "
                         "choose them: neither ran, and the run says so as a limit.", [
    held_not("qa-dropped-no-gap", "a read the person went on without is not a gap"),
    row("qa-dropped-sweep", "gate", "qa.limit", "the sweep chosen earlier and not run", kind="read-dropped",
        step="03-sweep", stopped=False),
    row("qa-dropped-pinpoint", "gate", "qa.limit", "the pinpoint chosen earlier and not run", kind="read-dropped",
        step="04-pinpoint", stopped=False),
    row("qa-dropped-count", "gate", "qa.limit", "those two and no other", count=2, kind="read-dropped"),
])

# the sweep was chosen again at `continue` and ran; only the pinpoint was dropped
run_folder("one-read-dropped", steps=[*STEPS, "03-sweep"], outputs={"03-sweep": sweep_report([])},
           rec=record([step(s) for s in [*STEPS, "03-sweep"]], all_pass([*STEPS, "03-sweep"]), chosen=["03-sweep"],
                      dropped=["04-pinpoint"], backends={"03-sweep": "jev", "04-pinpoint": "claude-cli"}))
CASES["one-read-dropped"] = ("The sweep ran; the pinpoint, chosen by the first command, was not chosen at `continue`: "
                             "one limit, and no gap.", [
    held_not("qa-one-dropped-no-gap", "the read that ran and the one dropped are no gap"),
    row("qa-one-dropped", "gate", "qa.limit", "only the pinpoint is dropped", kind="read-dropped", step="04-pinpoint",
        count=1),
])

# a run made without validation has no stamps to judge
run_folder("no-validation", rec=record([step(s) for s in STEPS], {}))
CASES["no-validation"] = ("A run made without validation: no stamp, no fixture gap.", [
    held_not("qa-no-validation-no-gap", "no stamp is not a failed stamp"),
])

# a model read that had no prose to ask about
run_folder("empty-read", steps=[*STEPS, "03-sweep"], outputs={"03-sweep": sweep_report([])},
           rec=record([step(s) for s in [*STEPS, "03-sweep"]], all_pass([*STEPS, "03-sweep"])))
CASES["empty-read"] = ("A sweep that had no passages to ask about did not fail.", [
    held_not("qa-empty-read-no-gap", "a read of nothing is not a read that got no answer"),
])


# ---------------------------------------------------------------- coverage (M9 slice C)

def phrases(*lines, **kw):
    return {"02.4-phrases": report("02.4-phrases", coverage=list(lines), **kw)}


PHRASE_CHECKS = CHECKS["02.4-phrases"]
FIRST_PASS, REST = PHRASE_CHECKS[:14], PHRASE_CHECKS[14:]  # the phrase checks run in one pass; the others after them

# a step that wrote no line for two of its checks
run_folder("coverage-missing", outputs=phrases(
    coverage_line([c for c in PHRASE_CHECKS if c not in ("phrase.remote-load", "rep.sentence")], "files", 3, 3, 0, 0)))
CASES["coverage-missing"] = ("The phrase step's coverage has no line for two of its checks: it cannot say what they "
                             "looked at.", [
    gap("qa-coverage-missing", "02.4-phrases", "coverage-missing", "a check with no coverage line is a gap, once for the step",
        missing=("includes", "phrase.remote-load")),
    gap("qa-coverage-missing-second", "02.4-phrases", "coverage-missing", "the second check left out is in the same gap",
        missing=("includes", "rep.sentence"), checks_total=len(PHRASE_CHECKS)),
    row("qa-coverage-missing-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

# a step that wrote no coverage at all
run_folder("coverage-none", outputs={"02.5-capability": report("02.5-capability", coverage=None)})
CASES["coverage-none"] = ("The capability step's report has no coverage list: one gap for the step, naming every check.", [
    gap("qa-coverage-none", "02.5-capability", "coverage-missing", "no list at all is one gap for the step",
        missing=("includes", "cap.leg"), checks_total=len(CHECKS["02.5-capability"])),
    row("qa-coverage-none-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

# a check that looked at fewer files than it should have, and says nothing about the rest
run_folder("coverage-short", outputs=phrases(coverage_line(FIRST_PASS, "files", 5, 3, 0, 2),
                                             coverage_line(REST, "files", 5, 5, 0, 0)))
CASES["coverage-short"] = ("The phrase checks looked at three of five files and explain none of the other two: the "
                           "zeros of those checks cannot be trusted.", [
    gap("qa-coverage-short", "02.4-phrases", "coverage-short", "two files neither looked at nor explained",
        of=5, looked_at=3, explained=0, unit="files", checks=("includes", "phrase.remote-load")),
    row("qa-coverage-short-count", "gate", "qa.gap", "that one gap and no other", count=1),
    row("qa-coverage-short-whole-line-is-fine", "negative", "qa.gap", "the line that adds up is no gap",
        step="02.4-phrases", checks=("includes", "rep.sentence")),
])

# the same shortfall, explained by two skips: nothing is held
run_folder("coverage-explained", outputs={"02.2-reader": report(
    "02.2-reader",
    [{"check": "read.divergence", "file": f"fixture-{n}.png", "line": None, "skipped": "tesseract not installed"}
     for n in (1, 2)],
    coverage=[coverage_line(CHECKS["02.2-reader"], "files", 5, 3, 2, 0)])},
    rec=record([step(s) for s in STEPS], {**all_pass(), "02.2-reader": stamp("INCOMPLETE", skipped=["rd-img-ocr"])}))
CASES["coverage-explained"] = ("The reader looked at three of five files and two were skipped for a missing optional "
                               "tool, each with its skip: the line adds up and the run goes on.", [
    held_not("qa-coverage-explained-no-gap", "items explained by a skip are no gap (owner, 2026-10-25)"),
    row("qa-coverage-explained-skips", "gate", "qa.limit", "the two skips are limits", count=2, kind="skip"),
    row("qa-coverage-explained-checked", "gate", "qa.checked", "what the reader's checks looked at, the skipped files said too",
        kind="checked", step="02.2-reader", looked_at=3, explained=2, of=5),
    row("qa-coverage-explained-skipped-check-not-named", "negative", "qa.checked",
        "a check with a skip of its own is not said to have found none", step="02.2-reader",
        checks=("includes", "read.divergence")),
])

# counts that are more than the items there were
run_folder("coverage-broken", outputs=phrases(coverage_line(FIRST_PASS, "files", 3, 3, 2, 0),
                                              coverage_line(REST, "files", 3, 3, 0, 0)))
CASES["coverage-broken"] = ("A phrase line looked at three of three files and explains two more: the counts do not add "
                            "up, which is a broken count.", [
    gap("qa-coverage-broken", "02.4-phrases", "coverage-broken", "more looked at and explained than there were",
        of=3, looked_at=3, explained=2),
    row("qa-coverage-broken-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

# a model read that dropped a passage: four were built, three answered, nothing said of the fourth
sweep_three = [sweep_finding(n) for n in (1, 5, 9)]
run_folder("coverage-ai-short", steps=[*STEPS, "03-sweep"],
           outputs={"03-sweep": sweep_report(sweep_three, coverage=[coverage_line(["soft.sweep"], "passages", 4, 3, 0, 0)])},
           rec=record([step(s) for s in [*STEPS, "03-sweep"]], all_pass([*STEPS, "03-sweep"]), chosen=["03-sweep"]))
CASES["coverage-ai-short"] = ("A sweep built four passages and wrote a finding for three: the fourth is neither "
                              "answered nor skipped.", [
    gap("qa-coverage-ai-short", "03-sweep", "coverage-short", "a passage with no answer and no skip", of=4,
        looked_at=3, explained=0, unit="passages"),
    row("qa-coverage-ai-short-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

# a coverage that is not a list of lines is an output that cannot be read: one gap, and no coverage gap on top
run_folder("output-bad-coverage")
(OUT / "output-bad-coverage" / "data" / "02.3-graph.json").write_text(
    json.dumps({**report("02.3-graph"), "coverage": "everything"}) + "\n", encoding="utf-8", newline="\n")
(OUT / "output-bad-coverage" / "data" / "02.4-phrases.json").write_text(
    json.dumps({**report("02.4-phrases"), "coverage": [coverage_line(PHRASE_CHECKS, "files", 2.5, 2, 0, 0)]}) + "\n",
    encoding="utf-8", newline="\n")
CASES["output-bad-coverage"] = ("Two saved outputs hold a coverage that is not a list of lines (a word, a count that is not a "
                                "whole number): no output, the same as one that cannot be read.", [
    gap("qa-bad-coverage-word", "02.3-graph", "step-missing", "a coverage that is not a list is no report",
        why="output-unreadable"),
    gap("qa-bad-coverage-count", "02.4-phrases", "step-missing", "a count that is not whole is no report",
        why="output-unreadable"),
    row("qa-bad-coverage-count-only", "gate", "qa.gap", "those two gaps and no coverage gap on top", count=2),
])

# the object the reader wrote under `coverage` before slice C is no list of lines: it reads, and has none
run_folder("coverage-old-reader", outputs={"02.2-reader": {**report("02.2-reader", coverage=None),
                                                             "coverage": {"files": 3, "files_read": 3}}})
CASES["coverage-old-reader"] = ("A reader report made before coverage lines (an object under `coverage`) reads as a report "
                                "with no lines: its checks have no coverage line.", [
    gap("qa-old-reader", "02.2-reader", "coverage-missing", "no lines, so every check is missing",
        missing=("includes", "read.fold"), checks_total=len(CHECKS["02.2-reader"])),
    row("qa-old-reader-count", "gate", "qa.gap", "that one gap and no other", count=1),
])


# a line that says it found two where the findings of its checks hold none
run_folder("coverage-found-wrong", outputs=phrases(coverage_line(FIRST_PASS, "files", 3, 3, 0, 2),
                                                   coverage_line(REST, "files", 3, 3, 0, 0)))
CASES["coverage-found-wrong"] = ("A phrase line says its checks found two and the report holds no finding of them: the "
                                 "counts do not add up.", [
    gap("qa-coverage-found-wrong", "02.4-phrases", "coverage-broken", "a found that is not the findings of the line's checks",
        why="found", found_line=2, found_actual=0),
    row("qa-coverage-found-wrong-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

# lines that name an id the step does not make, another step's id, and an id two lines name
run_folder("coverage-unknown-id", outputs=phrases(coverage_line(FIRST_PASS, "files", 3, 3, 0, 0),
                                                  coverage_line([*REST, "phrase.not-a-check"], "files", 3, 3, 0, 0)))
CASES["coverage-unknown-id"] = ("A phrase line names a check the step does not make: the line cannot be trusted.", [
    gap("qa-coverage-unknown-id", "02.4-phrases", "coverage-broken", "an id that is not on the step's list",
        why="check", ids=("includes", "phrase.not-a-check")),
    row("qa-coverage-unknown-id-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

run_folder("coverage-other-steps-id", outputs=phrases(coverage_line(FIRST_PASS, "files", 3, 3, 0, 0),
                                                      coverage_line([*REST, "cap.leg"], "files", 3, 3, 0, 0)))
CASES["coverage-other-steps-id"] = ("A phrase line names a check that belongs to the capability step.", [
    gap("qa-coverage-other-steps-id", "02.4-phrases", "coverage-broken", "another step's id", why="check",
        ids=("includes", "cap.leg")),
    row("qa-coverage-other-steps-id-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

run_folder("coverage-twice", outputs=phrases(coverage_line(PHRASE_CHECKS, "files", 3, 3, 0, 0),
                                             coverage_line(["rep.sentence"], "files", 3, 3, 0, 0)))
CASES["coverage-twice"] = ("A check is named by two phrase lines: each of the two lines is a broken line.", [
    gap("qa-coverage-twice", "02.4-phrases", "coverage-broken", "an id two lines name", why="check",
        ids=("includes", "rep.sentence")),
    row("qa-coverage-twice-count", "gate", "qa.gap", "both lines are held", count=2),
])

# a finding whose check is not on the step's list, a skip too: the step wrote no line for it
run_folder("coverage-stray-finding", outputs=phrases(
    coverage_line(PHRASE_CHECKS, "files", 3, 3, 0, 0),
    findings=[{"check": "phrase.not-a-check", "file": None, "line": None, "skipped": "no tool"}]))
CASES["coverage-stray-finding"] = ("The phrase step's report has a skip for a check that is not on its list: no line says "
                                   "what that check looked at.", [
    gap("qa-coverage-stray-finding", "02.4-phrases", "coverage-missing", "a finding's check with no line is missing",
        missing=("includes", "phrase.not-a-check"), checks_total=len(PHRASE_CHECKS) + 1),
    row("qa-coverage-stray-finding-count", "gate", "qa.gap", "that one gap and no other", count=1),
])

# a read that flagged passages: its `found` is its flags, and the sweep's line adds up
flagged = [{**sweep_finding(1), "flagged": True}, sweep_finding(5), sweep_finding(9)]
run_folder("coverage-ai-flagged", steps=[*STEPS, "03-sweep"],
           outputs={"03-sweep": sweep_report(flagged, coverage=[coverage_line(["soft.sweep"], "passages", 3, 3, 0, 1)])},
           rec=record([step(s) for s in [*STEPS, "03-sweep"]], all_pass([*STEPS, "03-sweep"]), chosen=["03-sweep"]))
CASES["coverage-ai-flagged"] = ("A sweep answered three passages and flagged one: `found` is the one flag, and nothing "
                                "is held.", [
    held_not("qa-coverage-ai-flagged-no-gap", "a read's found is its flags"),
    row("qa-coverage-ai-flagged-not-checked", "negative", "qa.checked", "a read that flagged something found something",
        step="03-sweep"),
])

# steps whose fixture check did not measure their none say nothing of what they looked at
run_folder("checked-not-measured", steps=[*STEPS, "03-sweep"],
           outputs={"03-sweep": sweep_report([sweep_finding(n) for n in (1, 5, 9)])},
           rec=record([step(s) for s in [*STEPS, "03-sweep"]],
                      {**all_pass(), "02.4-phrases": stamp("INCOMPLETE", gate=None, negative=None, skipped=["ph-x"]),
                       "02.3-graph": stamp("no fixture set"),
                       "03-sweep": stamp("PASS", gate=None, negative=None, recall="0/32",
                                         skipped=[f"sweep-row-{i}" for i in range(32)])},
                      chosen=["03-sweep"]))
CASES["checked-not-measured"] = ("The phrase check was skipped and measured no rows, the graph step has no fixture set, and "
                                 "the sweep answered with all 32 of its recall rows skipped: none of them says 'checked, "
                                 "found none'.", [
    row("qa-not-measured-phrases", "negative", "qa.checked", "no rows measured: no line", step="02.4-phrases"),
    row("qa-not-measured-graph", "negative", "qa.checked", "no fixture set: no line", step="02.3-graph"),
    row("qa-not-measured-sweep", "negative", "qa.checked", "every row skipped: no line", step="03-sweep"),
    gap("qa-not-measured-graph-gap", "02.3-graph", "fixture-unchecked", "no fixture set is a gap on a coded step",
        result="no fixture set"),
    row("qa-not-measured-others", "gate", "qa.checked", "a step that passed still gets its line", step="02.1-inventory"),
])


def main():
    sheet = {"stage": "05-qa", "answers_version": 1,
             "note": "The check of the run (M9 slice B, 2026-10-30): one small synthetic run folder per case. A gate "
                     "row is a gap it must find, a negative row a run it must not hold, and a gate row on qa.limit "
                     "what the run says instead. Rebuilt by tools/fixture-generators/make_qa_runs.py.",
             "cases": [{"root": name, "fixtures": {}, "note": note, "expect": rows, "deferred": []}
                       for name, (note, rows) in CASES.items()]}
    SHEET.write_text(json.dumps(sheet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(CASES)} cases to {OUT} and {SHEET}")


if __name__ == "__main__":
    main()
