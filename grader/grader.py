"""Walkdown grader: run a stage against its fixtures and score it against the answers.

The only component that reads Fixtures/ANSWERS/. Spec: grader/SPEC.md.
Stage contract: stages/CONTRACT.md. Answers format: Fixtures/ANSWERS/README.md.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

EXIT = {"PASS": 0, "FAIL": 1, "INCOMPLETE": 2, "NOT BUILT": 3, "SETUP ERROR": 4}
POLARITIES = {"gate", "recall", "negative"}
OPERATORS = {"eq", "contains", "same_items", "includes", "excludes"}
CONTRACT = 1
TIMEOUT = 300


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
    return finding.get("file") in (None, exp.get("file"))


# ------------------------------------------------------------------ answers

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_tree(root):
    return {p.relative_to(root).as_posix(): sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}


def stage_names(root, selector):
    answers = root / "Fixtures" / "ANSWERS"
    names = sorted(p.stem for p in answers.glob("*.json")) if answers.is_dir() else []
    if selector == "all":
        if not names:
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

def run_stage(root, stage, case_root):
    runner = root / "stages" / stage / "run.py"
    try:
        proc = subprocess.run([sys.executable, str(runner), str(case_root)],
                              capture_output=True, text=True, encoding="utf-8", timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return None, f"timed out after {TIMEOUT}s"
    if proc.returncode != 0:
        return None, f"exit code {proc.returncode}: {proc.stderr.strip()[-300:]}"
    try:
        report = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return None, f"stdout is not JSON ({e})"
    if report.get("contract") != CONTRACT or not isinstance(report.get("findings"), list):
        return None, f"report does not follow contract {CONTRACT} (need 'contract' and a 'findings' list)"
    return report["findings"], None


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


def grade_stage(root, stage):
    doc = load_answers(root, stage)
    check_stale(root, stage, doc)
    result = {"stage": stage, "rows": [], "unlisted": Counter(), "errors": [],
              "deferred": [d for c in doc["cases"] for d in c.get("deferred", [])]}
    if not (root / "stages" / stage / "run.py").is_file():
        result["result"] = "NOT BUILT"
        return result
    for case in doc["cases"]:
        findings, err = run_stage(root, stage, root / "Fixtures" / stage / case["root"])
        if err:
            result["errors"].append(f"case {case['root']}: {err}")
            continue
        rows, unlisted = score_case(case, findings)
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
    if res["result"] == "NOT BUILT":
        print(f"   no stages/{res['stage']}/run.py")
    for e in res["errors"]:
        print(f"   stage error: {e}")
    rows = res["rows"]
    if rows:
        g, gt = tally(rows, "gate")
        n, nt = tally(rows, "negative")
        r, rt = tally(rows, "recall")
        print(f"   gate      {g}/{gt}")
        print(f"   negative  {n}/{nt}   ({nt - n} false positive{'s' if nt - n != 1 else ''})")
        if rt:
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
    }


# ------------------------------------------------------------------ commands

def cmd_check_answers(root):
    names = stage_names(root, "all")
    for stage in names:
        doc = load_answers(root, stage)
        check_stale(root, stage, doc)
        n = sum(len(c["expect"]) for c in doc["cases"])
        print(f"{stage}: ok ({len(doc['cases'])} case(s), {n} expectations, hashes current)")
    return EXIT["PASS"]


def cmd_rehash(root, selector):
    for stage in stage_names(root, selector):
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
    ap.add_argument("stage", nargs="?", help="stage number or name (01, 01-inventory), or 'all'")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]), help="project root")
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
