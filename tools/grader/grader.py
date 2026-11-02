"""Walkdown grader: run a stage against its fixtures and score it against the answers.

The only component that reads Fixtures/ANSWERS/. Spec: tools/grader/SPEC.md.
Stage contract: stages/CONTRACT.md. Answers format: Fixtures/ANSWERS/README.md.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

NO_FIXTURE_SET = "no fixture set"
EXIT = {"PASS": 0, "FAIL": 1, "INCOMPLETE": 2, "NOT BUILT": 3, "SETUP ERROR": 4, NO_FIXTURE_SET: 0}
POLARITIES = {"gate", "recall", "negative"}
OPERATORS = {"eq", "contains", "same_items", "includes", "excludes"}
CONTRACT = 1
TIMEOUT = 300
# A model read makes a call for each passage, each allowed 300 seconds, so its fixture check can run longer than a coded step's.
AI_TIMEOUT = 1800
# The counts a model step's `usage` block holds (stages/CONTRACT.md); the grader sums them over the cases it runs.
USAGE_KEYS = ("input", "output", "cache_write", "cache_read", "calls", "reported")
USAGE_CEILING = 10 ** 15  # a count above this is not a count (stages/_shared/usage.py): left out of the sum


class SetupError(Exception):
    pass


# ------------------------------------------------------------------ matching

def condition_holds(cond, value):
    """One match condition, e.g. {"contains": "upload"}, against one finding value."""
    (op, want), = cond.items()
    if op == "eq":
        return value == want
    if op == "contains":
        return isinstance(value, str) and want.lower() in value.lower()
    if op == "same_items":
        return isinstance(value, list) and Counter(map(repr, value)) == Counter(map(repr, want))
    if op == "includes":
        return isinstance(value, list) and want in value
    if op == "excludes":
        return isinstance(value, list) and not any(w in value for w in want)
    raise SetupError(f"unknown match operator {op!r}")


def finding_matches(exp, finding):
    if finding.get("check") != exp["check"] or "skipped" in finding:
        return False
    if "file" in exp and finding.get("file") != exp["file"]:
        return False
    if "line" in exp and finding.get("line") != exp["line"]:
        return False
    for field, cond in exp.get("match", {}).items():
        if field not in finding or not condition_holds(cond, finding[field]):
            return False
    return True


def skip_applies(exp, finding):
    if "skipped" not in finding or finding.get("check") != exp["check"]:
        return False
    if finding.get("carrier"):  # a skip of one carrier only (PDF page OCR): rows about that carrier
        if (exp.get("match") or {}).get("carrier", {}).get("eq") != finding["carrier"]:
            return False
    return finding.get("file") in (None, exp.get("file"))


# ------------------------------------------------------------------ answers

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_tree(root):
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def sheet_names(root):
    """The stages that have an answer sheet."""
    answers = root / "Fixtures" / "ANSWERS"
    return sorted(p.stem for p in answers.glob("*.json")) if answers.is_dir() else []


def graded_entries(doc):
    """The entries of stages/stages.json the grader can grade: the pipeline's stages, then the check of the run
    (`qa`, M9 slice B), which is not one of the stages a run chooses but has fixtures. The report has none."""
    return [*doc.get("stages", []), *([doc["qa"]] if doc.get("qa") else [])]


def listed_names(root):
    """The stages named in stages/stages.json (and the check of the run); none when it cannot be read (the run of
    a stage reports that)."""
    try:
        doc = json.loads((root / "stages" / "stages.json").read_text(encoding="utf-8"))
        return [s["name"] for s in graded_entries(doc)]
    except (OSError, ValueError, KeyError, TypeError):
        return []


def stage_names(root, selector):
    """The stages a selector names: those with an answer sheet, and those listed in stages.json
    with none (an AI stage without a fixture set, restructure step 5), which grade as
    "no fixture set"."""
    answers = root / "Fixtures" / "ANSWERS"
    sheets = sheet_names(root)
    names = sorted(sheets + [n for n in listed_names(root) if n not in sheets])
    if selector == "all":
        if not sheets:
            raise SetupError(f"no answers found in {answers}")
        return names
    hits = [n for n in names if n == selector or n.split("-", 1)[0] == selector]
    if not hits:
        raise SetupError(f"no answers for stage {selector!r} in {answers}")
    return hits


def load_answers(root, stage):
    path = root / "Fixtures" / "ANSWERS" / f"{stage}.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SetupError(f"cannot read {path}: {e}")
    if doc.get("stage") != stage:  # restructure notes M7: the sheet says which stage it grades
        raise SetupError(f"{path.name}: its \"stage\" is {doc.get('stage')!r}, not {stage!r}")
    for case in doc.get("cases", []):
        for key in ("root", "fixtures", "expect"):
            if key not in case:
                raise SetupError(f"{stage}: case missing {key!r}")
        for exp in case["expect"]:
            if exp.get("polarity") not in POLARITIES:
                raise SetupError(f"{stage}: {exp.get('id')}: bad polarity {exp.get('polarity')!r}")
            if not exp.get("check") or not exp.get("id"):
                raise SetupError(f"{stage}: expectation missing id or check: {exp}")
            for cond in exp.get("match", {}).values():
                if len(cond) != 1 or next(iter(cond)) not in OPERATORS:
                    raise SetupError(f"{stage}: {exp['id']}: bad match condition {cond}")
            if "count" in exp and exp["polarity"] != "gate":
                raise SetupError(f"{stage}: {exp['id']}: count is only valid on gate rows")
    return doc


def stale_files(root, stage, case):
    case_root = root / "Fixtures" / stage / case["root"]
    if not case_root.is_dir():
        return [f"{case['root']} (case root missing)"]
    actual, listed = hash_tree(case_root), case["fixtures"]
    out = [f"{f} (changed)" for f in listed if f in actual and actual[f] != listed[f]]
    out += [f"{f} (removed)" for f in listed if f not in actual]
    out += [f"{f} (new, no answers)" for f in actual if f not in listed]
    return out


def check_stale(root, stage, doc):
    stale = [f"{c['root']}/{s}" for c in doc["cases"] for s in stale_files(root, stage, c)]
    if stale:
        raise SetupError(f"{stage}: stale answers, fixtures differ from recorded hashes: "
                         + "; ".join(stale) + f". Re-verify, then: grader.py --rehash {stage}")


# ------------------------------------------------------------------ running

def runner_path(root, stage):
    """The stage's run.py, found through stages/stages.json (the one home for the stage list,
    stages/CONTRACT.md). None when the stage is not listed there."""
    path = root / "stages" / "stages.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SetupError(f"cannot read {path}: {e}")
    for s in graded_entries(doc):
        if s.get("name") == stage:
            return root / "stages" / s["folder"] / "run.py"
    return None


def timeout_for(root, stage):
    """The seconds a case may run: longer for a stage a person chooses to read with a model (an entry with an `option`)."""
    try:
        doc = json.loads((root / "stages" / "stages.json").read_text(encoding="utf-8"))
        return AI_TIMEOUT if any(s.get("name") == stage and s.get("option") for s in doc.get("stages", [])) else TIMEOUT
    except (OSError, ValueError, TypeError, AttributeError):
        return TIMEOUT


def run_report(root, stage, case_root):
    """(the stage's report, None), or (None, why it could not be run or did not print a report)."""
    runner = runner_path(root, stage)
    limit = timeout_for(root, stage)
    try:
        proc = subprocess.run([sys.executable, str(runner), str(case_root)],
                              capture_output=True, text=True, encoding="utf-8", timeout=limit)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {limit}s"
    if proc.returncode != 0:
        return None, f"exit code {proc.returncode}: {proc.stderr.strip()[-300:]}"
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return None, f"stdout is not JSON ({e})"
    if report.get("contract") != CONTRACT or not isinstance(report.get("findings"), list):
        return None, f"report does not follow contract {CONTRACT} (need 'contract' and a 'findings' list)"
    return report, None


def run_stage(root, stage, case_root):
    """(the stage's findings, None), or (None, why)."""
    report, err = run_report(root, stage, case_root)
    return (report["findings"] if report is not None else None), err


def whole(n):
    return isinstance(n, int) and not isinstance(n, bool) and n >= 0


def add_usage(total, block):
    """Add the `usage` block of one case's report to `total`. A block that is not an object of whole counts adds nothing."""
    if not isinstance(block, dict) or not all(whole(block[k]) and block[k] <= USAGE_CEILING for k in USAGE_KEYS if k in block):
        return
    for k in USAGE_KEYS:
        if k in block:
            total[k] = total.get(k, 0) + block[k]


def score_case(case, findings):
    rows, touched = [], set()
    for exp in case["expect"]:
        matches = [i for i, f in enumerate(findings) if finding_matches(exp, f)]
        touched.update(matches)
        skipped = any(skip_applies(exp, f) for f in findings)
        pol = exp["polarity"]
        if skipped and not matches:
            status = "SKIPPED"
        elif pol == "gate":
            ok = len(matches) == exp["count"] if "count" in exp else bool(matches)
            status = "ok" if ok else "MISS"
        elif pol == "negative":
            status = "FALSE POSITIVE" if matches else "ok"
        else:
            status = "found" if matches else "missed"
        rows.append({"exp": exp, "status": status, "matched": len(matches)})
    unlisted = Counter(f.get("check") for i, f in enumerate(findings)
                       if i not in touched and "skipped" not in f)
    return rows, unlisted


def has_no_fixture_set(root, stage):
    """A stage listed in stages.json with no answer sheet and no fixtures folder: it has nothing to
    be graded against (an AI stage without a fixture set, restructure step 5). A stage with
    fixtures but no sheet is not this: it is a setup error."""
    return (not (root / "Fixtures" / "ANSWERS" / f"{stage}.json").is_file()
            and not (root / "Fixtures" / stage).exists() and stage in listed_names(root))


def grade_stage(root, stage):
    if has_no_fixture_set(root, stage):
        return {"stage": stage, "rows": [], "unlisted": Counter(), "errors": [], "deferred": [],
                "result": NO_FIXTURE_SET}
    doc = load_answers(root, stage)
    check_stale(root, stage, doc)
    result = {"stage": stage, "rows": [], "unlisted": Counter(), "errors": [], "usage": {},
              "deferred": [d for c in doc["cases"] for d in c.get("deferred", [])]}
    runner = runner_path(root, stage)
    if runner is None or not runner.is_file():
        result["result"] = "NOT BUILT"
        result["runner"] = runner.relative_to(root).as_posix() if runner else None
        return result
    for case in doc["cases"]:
        report, err = run_report(root, stage, root / "Fixtures" / stage / case["root"])
        if err:
            result["errors"].append(f"case {case['root']}: {err}")
            continue
        add_usage(result["usage"], report.get("usage"))
        rows, unlisted = score_case(case, report["findings"])
        result["rows"] += rows
        result["unlisted"] += unlisted
    rows = result["rows"]
    hard = [r for r in rows if r["exp"]["polarity"] in ("gate", "negative")]
    if result["errors"] or any(r["status"] in ("MISS", "FALSE POSITIVE") for r in hard):
        result["result"] = "FAIL"
    elif any(r["status"] == "SKIPPED" for r in hard):
        result["result"] = "INCOMPLETE"
    else:
        result["result"] = "PASS"
    return result


# ------------------------------------------------------------------ output

def tally(rows, polarity):
    rs = [r for r in rows if r["exp"]["polarity"] == polarity]
    good = {"gate": "ok", "negative": "ok", "recall": "found"}[polarity]
    return sum(r["status"] == good for r in rs), len(rs)


def label(exp):
    where = exp.get("file") or "(repo)"
    if "line" in exp:
        where += f":{exp['line']}"
    return f"{exp['id']}  {exp['check']}  {where}"


def print_stage(res, explain):
    print(f"\n== {res['stage']}: {res['result']}")
    if res["result"] == NO_FIXTURE_SET:
        print("   no answer sheet and no fixtures for this stage; nothing to grade it against")
        return
    if res["result"] == "NOT BUILT":
        print(f"   no {res['runner']}" if res.get("runner") else "   not listed in stages/stages.json")
    for e in res["errors"]:
        print(f"   stage error: {e}")
    rows = res["rows"]
    if rows:
        g, gt = tally(rows, "gate")
        n, nt = tally(rows, "negative")
        r, rt = tally(rows, "recall")
        print(f"   gate      {g}/{gt}")
        fp = sum(1 for r in res["rows"] if r["exp"]["polarity"] == "negative"
                 and r["status"] == "FALSE POSITIVE")
        print(f"   negative  {n}/{nt}   ({fp} false positive{'s' if fp != 1 else ''})")
        if rt:
            asked = sum(1 for x in rows if x["exp"]["polarity"] == "recall" and x["status"] != "SKIPPED")
            if asked == 0:  # every recall row skipped: nothing was measured, so no percentage is printed
                print(f"   recall    not measured: all {rt} rows were skipped")
            else:
                print(f"   recall    {r}/{rt}  {round(100 * r / rt)}%  (measured, never required)")
    for row in rows:
        s = row["status"]
        if s in ("ok", "found"):
            continue
        tag = {"MISS": "MISS          ", "FALSE POSITIVE": "FALSE POSITIVE", "SKIPPED": "SKIPPED       ",
               "missed": "recall missed "}[s]
        print(f"   {tag} {label(row['exp'])}  [{row['exp']['polarity']}]")
        if explain:
            if row["exp"].get("match"):
                print(f"                  expected: {json.dumps(row['exp']['match'], ensure_ascii=False)}")
            if "count" in row["exp"]:
                print(f"                  expected count {row['exp']['count']}, got {row['matched']}")
            if row["exp"].get("note"):
                print(f"                  note: {row['exp']['note']}")
    if res["unlisted"]:
        parts = ", ".join(f"{c} x{n}" for c, n in sorted(res["unlisted"].items()))
        print(f"   unlisted findings (not scored): {parts}")
    for d in res["deferred"]:
        print(f"   deferred (not scored): {d['id']}  needs {' + '.join(d['needs'])}"
              + (f"  note: {d['note']}" if explain else ""))


def as_json(res):
    r, rt = tally(res["rows"], "recall")
    return {
        "stage": res["stage"], "result": res["result"], "errors": res["errors"],
        "gate": dict(zip(("passed", "total"), tally(res["rows"], "gate"))),
        "negative": dict(zip(("passed", "total"), tally(res["rows"], "negative"))),
        "recall": {"found": r, "total": rt},
        "not_ok": [{"id": x["exp"]["id"], "status": x["status"]} for x in res["rows"]
                   if x["status"] not in ("ok", "found")],
        "unlisted": dict(res["unlisted"]),
        "deferred": [d["id"] for d in res["deferred"]],
        **({"usage": res["usage"]} if res.get("usage") else {}),  # what a model read's fixture check used; a stage that sent nothing has none
    }


# ------------------------------------------------------------------ commands

def cmd_check_answers(root):
    names = sheet_names(root)
    if not names:
        raise SetupError(f"no answers found in {root / 'Fixtures' / 'ANSWERS'}")
    for stage in names:
        doc = load_answers(root, stage)
        check_stale(root, stage, doc)
        n = sum(len(c["expect"]) for c in doc["cases"])
        print(f"{stage}: ok ({len(doc['cases'])} case(s), {n} expectations, hashes current)")
    return EXIT["PASS"]


def cmd_rehash(root, selector):
    hits = [n for n in stage_names(root, selector) if n in sheet_names(root)]
    if not hits:
        raise SetupError(f"no answers for stage {selector!r} in {root / 'Fixtures' / 'ANSWERS'}")
    for stage in hits:
        path = root / "Fixtures" / "ANSWERS" / f"{stage}.json"
        doc = load_answers(root, stage)
        for case in doc["cases"]:
            case_root = root / "Fixtures" / stage / case["root"]
            changes = stale_files(root, stage, case)
            case["fixtures"] = hash_tree(case_root)
            for c in changes:
                print(f"{stage}/{case['root']}: rehashed {c}")
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print("Hashes rewritten. Expectations were not changed; re-verify them against the edited fixtures.")
    return EXIT["PASS"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Grade Walkdown stages against their fixtures.")
    ap.add_argument("stage", nargs="?", help="stage number or name (02.1, 02.1-inventory), or 'all'")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]), help="project root")
    ap.add_argument("--explain", action="store_true", help="show expected values and notes (not for blind builds)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--check-answers", action="store_true", help="validate answers and fixture hashes only")
    ap.add_argument("--rehash", metavar="STAGE", help="rewrite fixture hashes after a deliberate change")
    args = ap.parse_args(argv)
    root = Path(args.root)
    try:
        if args.check_answers:
            return cmd_check_answers(root)
        if args.rehash:
            return cmd_rehash(root, args.rehash)
        if not args.stage:
            ap.error("give a stage, 'all', --check-answers, or --rehash STAGE")
        results = []
        for stage in stage_names(root, args.stage):
            try:
                results.append(grade_stage(root, stage))
            except SetupError as e:
                results.append({"stage": stage, "result": "SETUP ERROR", "rows": [], "unlisted": Counter(),
                                "errors": [str(e)], "deferred": []})
    except SetupError as e:
        print(f"SETUP ERROR: {e}")
        return EXIT["SETUP ERROR"]
    if args.json:
        print(json.dumps({"stages": [as_json(r) for r in results]}, indent=2))
    else:
        for r in results:
            if r["result"] == "SETUP ERROR":
                print(f"\n== {r['stage']}: SETUP ERROR\n   {r['errors'][0]}")
            else:
                print_stage(r, args.explain)
    return max(EXIT[r["result"]] for r in results)


if __name__ == "__main__":
    sys.exit(main())
