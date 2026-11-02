"""Step 02.6 runner: prints one contract-1 report. Spec: specs/builder.SPEC.md, run.py (the runner) and earlier.py (what it reads).

    python stages/02-coded/02.6-builder/run.py <input_dir> [--reports <dir>]

The builder checks: what the repository needs, which AI hosts it is ready for, whether it will
trigger, what its text asks tools to do, whether it is clean, whether the tools fit the job, and
what ships and costs. Moved here from 02.4-phrases and 02.5-capability (restructure step 4); every
module is called as it was, with the same inputs, so every finding is the one it was.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "_shared"))  # the audience rule, reading text, the secret mask

import asks  # noqa: E402
import clean  # noqa: E402
import cost  # noqa: E402
import earlier  # noqa: E402
import earlier_steps  # noqa: E402
import fit  # noqa: E402
import hosts  # noqa: E402
import needs  # noqa: E402
import readtext  # noqa: E402
import trigger  # noqa: E402
from audience import audience, inventory_sets, is_test_data  # noqa: E402
from secretmask import mask_secret_lines  # noqa: E402
import coverlines as cov  # noqa: E402
import stagenote  # noqa: E402

STAGE = "02.6-builder"
# What the step looked at (`stages/_shared/coverlines.py`). A line holds the checks that handle the same items, so each item
# a line counts goes through every check the line names. `of` is counted from the inventory and the texts before the checks run
# (here, and in `trigger.findings` for the entries a listing is made of, `needs.findings` for the uses of the programs it
# found); each check counts what it looked at inside its own loop.
NEEDS, PACKAGES, PORT, PORT_USES = needs.NEEDS, needs.PACKAGES, needs.PORT, needs.PORT_USES
BACKSLASH, OS, CRLF, PYTHON = needs.BACKSLASH_KEY, needs.OS_KEY, needs.CRLF_KEY, needs.PYTHON_KEY
HOST_COVERAGE, HOST_DRIFT, HOST_FEATURE = hosts.HOST_COVERAGE, hosts.HOST_DRIFT, hosts.HOST_FEATURE
TRIGGER, LISTING, ASKS = trigger.TRIGGER, trigger.LISTING, asks.ASKS
CLEAN, DATED, CLEAN_CHECKED = clean.CLEAN, clean.DATED_KEY, clean.CHECKED
FIT, FIT_CHECKED, HOOK_FIT = fit.FIT, fit.FIT_CHECKED, fit.HOOK_FIT
SHIP, CONTEXT = cost.SHIP, cost.CONTEXT
LINES = [(("need.command",), "files"),
         (("need.package",), "files"),
         (("port.path",), "files"),
         (("port.backslash",), "files"),
         (("port.os",), "files"),
         (("port.crlf",), "files"),
         (("port.exec",), "uses"),
         (("port.python",), "uses"),
         (("host.coverage",), "entries"),
         (("host.drift",), "files"),
         (("host.feature",), "files"),
         (("trig.entry", "trig.frontmatter", "trig.rule", "trig.guidance", "trig.key", "trig.value", "trig.tool"),
          "entries"),
         (("trig.overlap",), "entries"),
         (("trig.listing",), "run"),
         (("ask.tools", "ask.named", "fit.loop"), "files"),
         (("clean.unfinished", "clean.model"), "files"),
         (("clean.dated", "clean.older"), "files"),
         (("clean.checked",), "run"),
         (("fit.unused", "fit.missing", "fit.inherits"), "entries"),
         (("fit.checked",), "run"),
         (("fit.hook",), "entries"),
         (("cap.ship",), "files"),
         (("cap.context",), "entries")]


def eprint(*a):
    print(*a, file=sys.stderr)


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def texts_of(input_dir: Path, files: list[dict]) -> dict[str, str]:
    """{path: text} for the files `02.4-phrases` reads as text, in the same order and by the same rule
    (`readtext.read_row`)."""
    out = {}
    for row in files:
        got = readtext.read_row(input_dir, row)
        if got.text is not None:
            out[row["file"]] = got.text
    return out


def set_aside(report: dict, loaded) -> dict:
    """The inventory without findings on test-data paths, except files a model-read file points at
    (`02.5-capability`'s `set_aside`, which `fit` has always been given): fixtures and tests are never
    loaded as instructions when the artifact is installed."""
    keep = [f for f in report.get("findings", [])
            if not (f.get("file") and is_test_data(f["file"]) and f["file"] not in loaded)]
    return dict(report, findings=keep)


def count_text_inputs(texts: dict, files: list, scripts, hook_configs, hooks: list) -> None:
    """What the checks that read the repository's text are to look at, counted from the inventory and the texts before they
    run (`coverlines`): the text files that are not test data, the ones a package can be imported in, the instruction copies
    kept for different hosts, the files that carry one host's words, the entries (skills, agents, commands) with text, the
    files the AI reads, and the files that are not written for people."""
    real = [rel for rel in texts if not is_test_data(rel)]
    cov.of(NEEDS, sum(1 for rel in real if needs.programs_scope(rel, texts[rel])))  # scripts, and Markdown a model reads
    cov.of(PACKAGES, sum(1 for rel in real if needs._ext(rel) in needs.PACKAGE_EXTS))
    cov.of(PORT, sum(1 for rel in real if needs.paths_scope(rel)))  # not written for people
    cov.of(BACKSLASH, sum(1 for rel in real if needs.backslash_scope(rel)))  # Markdown a model reads
    cov.of(OS, sum(1 for rel in real if needs.os_scope(rel, texts[rel])))  # shell scripts and Windows scripts
    cov.of(CRLF, sum(1 for rel in real if needs.crlf_scope(rel, texts[rel])))  # shell scripts
    cov.of(HOST_COVERAGE, len(hosts.HOSTS["hosts"]))
    cov.of(HOST_DRIFT, len(hosts.copy_files(texts, hosts.rows_of(files))))
    cov.of(HOST_FEATURE, len(hosts.feature_texts(texts)) + len(hosts.hook_files_of(hooks)))
    cov.of(TRIGGER, sum(1 for r in files if trigger.entry_kind(r) and not is_test_data(r["file"])
                        and texts.get(r["file"]) is not None and trigger.is_entry(trigger.entry_kind(r), texts[r["file"]])))
    cov.of(ASKS, sum(1 for rel in texts if audience(rel, scripts, hook_configs) in asks.READS))
    cov.of(CLEAN, sum(1 for rel in texts if audience(rel, scripts, hook_configs) not in ("human", "test-data")))
    cov.of(DATED, sum(1 for rel in texts if clean.reads_dated(rel, audience(rel, scripts, hook_configs))))


def build(input_dir: Path, up: earlier.Earlier) -> list[dict]:
    cov.begin(LINES)
    inv = up.inventory
    files, scripts, hook_configs = inventory_sets(inv.get("findings", []))
    hooks = [f for f in inv["findings"] if f.get("check") == "struct.hooks"]
    mcp = [f for f in inv["findings"] if f.get("check") == "struct.mcp"]
    texts = texts_of(input_dir, files)
    count_text_inputs(texts, files, scripts, hook_configs, hooks)
    cov.of(LISTING)  # the listing row is written once in every run
    cov.of(CLEAN_CHECKED)
    cov.of(FIT_CHECKED)
    # `02.4-phrases`'s builder questions, in the order `02.4-phrases` asked them
    found = needs.findings(texts, files, hooks, mcp, needs.compatibility(texts))
    found += hosts.findings(texts, files, hooks)
    trig = trigger.findings(texts, files)
    found += trig + asks.findings(texts, scripts, hook_configs, asks.servers_of(trig))
    found += clean.findings(texts, scripts, hook_configs)

    # `02.5-capability`'s: the tools against the job (test data set aside), then what ships and costs (all of it)
    loaded = {f["file"] for f in up.capability
              if f.get("check") == "cap.pair" and f.get("pair") == "testdata+loaded"}
    injections = [f for f in up.capability if f.get("check") == "cap.injection"]
    aside = {"02.1-inventory": set_aside(inv, loaded), "02.6-builder": {"findings": found}}
    every = {"02.1-inventory": inv, "02.6-builder": {"findings": found}}
    cov.of(FIT, sum(1 for e in trig if e.get("check") == "trig.entry" and e.get("mode") not in ("unread", "skipped")))
    cov.of(HOOK_FIT, sum(1 for h in aside["02.1-inventory"].get("findings", [])
                         if h.get("check") == "struct.hooks" and "skipped" not in h))
    fits = fit.entries_fit(aside, up.graph) + fit.hooks_fit(aside, injections)
    n_files = len(cost._files(every))
    n_context = cost.context_items(every)
    cov.of(SHIP, n_files)
    cov.of(CONTEXT, n_context)
    if up.graph is None:  # the standing note says what ships and what it costs are not reported without graph.json
        cov.explain(SHIP, n_files)
        cov.explain(CONTEXT, n_context)
    shipped = cost.ship(every, up.graph)
    costs = shipped + cost.context(every, up.graph, injections, shipped)
    for f in fits + costs:  # as `02.5-capability` wrote them: no evidence, counted
        f["evidence_total"] = len(f.get("evidence", []))
        f["evidence"] = f.get("evidence", [])
    # a report never repeats a secret it found; last, since `fit` reads the tools a grant names
    mask_secret_lines(up.secrets + found + fits + costs)
    return found + fits + costs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="run.py")
    ap.add_argument("input_dir")
    ap.add_argument("--reports")
    try:
        args = ap.parse_args(sys.argv[1:] if argv is None else argv)
    except SystemExit:
        return 2
    target = Path(args.input_dir)
    if not target.is_dir():
        eprint(f"error: not a folder: {target}")
        return 2
    root = target.resolve()

    if args.reports:
        try:
            up = earlier.load_dir(args.reports)
        except earlier.ReportError as exc:
            eprint(f"error: --reports: {exc}")
            return 2
        if up.graph is None:
            stagenote.note("no graph.json in --reports; what ships and what it costs are not "
                           "reported (stage 3 edges needed)")
    else:
        with tempfile.TemporaryDirectory(prefix="walkdown-06-") as tmp:
            if _inside(Path(tmp).resolve(), root):
                eprint("error: temporary folder would be inside the input")
                return 2
            try:
                earlier_steps.run_before(STAGE, root, tmp)
                up = earlier.load_dir(tmp)
            except (earlier_steps.StepFailed, earlier.ReportError) as exc:
                eprint(f"error: {exc}")
                return 1

    findings = build(root, up)
    stagenote.note(f"{len(findings)} finding(s) from the builder checks; facts with locations and "
                   "counts, never a verdict")
    report = {"stage": STAGE, "contract": 1, "findings": findings, "coverage": cov.lines(findings)}
    sys.stdout.buffer.write(json.dumps(report, ensure_ascii=False, indent=1).encode("utf-8") + b"\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
