"""The brief: a plain summary of a finished run, written to `brief.md` in the run folder. Spec: specs/report.SPEC.md, brief.

Built from the run's data and the validation stamps (the record, `stages/_shared/record.py`), in
`summary.html`'s terms and with Walkdown's own words only: no quote, file name, or other text from the
audited repository, so it is safe to hand to a chat assistant. The front door prints this file; it
builds nothing (restructure step 7, notes F1). Moved here from `walkdown.py`, which read the stamps
back out of LOG.md's text.
"""
from __future__ import annotations

import collections
import re
from pathlib import Path

import common_lines
import coverage
import details_html
import layout
import qaview
import render as R
import stagelist
import steperror
import summary_html

QUOTED = re.compile(r"“[^”]*”|\"[^\"]*\"")
STAGE_NAMES = {s: stagelist.PLAIN[s] for s in stagelist.FOLDER_STAGES}  # the words a reader meets
AI_STAGES = stagelist.AI_STAGES  # optional: a run that did not choose them has no row or output for them
SWEEP = AI_STAGES[0]
INVENTORY = stagelist.CODED[0]


def own_words(title: str) -> str:
    """A summary headline with any quoted word from the audited repository removed."""
    if title.startswith("The word "):
        return "A word is defined more than one way"
    if title.startswith("Redefines the safety word"):
        return "Redefines a safety word"
    return QUOTED.sub("a word", title)


def results_of(stamps: dict) -> dict:
    """{stage: result word} for the stages the brief names, from the stamps: `PASS`, `FAIL`,
    `INCOMPLETE`, `no fixture set`, and so on."""
    return {stage: stamp.result for stage, stamp in stamps.items() if stage in STAGE_NAMES}


def stage_error(data: Path, stage: str) -> str:
    """Why a stage produced no output, in Walkdown's words: the error's type, and the module for
    a missing import, never the rest of its message (it can carry a path from the audited
    repository)."""
    try:
        text = (data / f"{stage}.notes.txt").read_text(encoding="utf-8")
    except OSError:
        return f"{R.STEP_NAMES[stage]}: no output and no error recorded; see LOG.md."
    kind, module = steperror.error_of(text)
    if kind:
        return f"{R.STEP_NAMES[stage]} stopped with {kind}" + (f" ({module})." if module else ".")
    return f"{R.STEP_NAMES[stage]}: no output; its messages are in data/{stage}.notes.txt."


def changes_lines(changes: dict | None) -> list[str]:
    """What changed since the previous run, counts and Walkdown's own words only (no repository text),
    from the one comparison the report stage makes (`drift.changes`). Nothing on a first run; one line
    when the version is the same and nothing differs. The same version with a difference means Walkdown
    changed (review C22 b, 2026-10-19)."""
    if changes is None:
        return []
    if not changes["differs"]:
        return ["", f"Changes since {changes['since']}: same version, nothing to compare."]
    head = (f"Changes since {changes['since']}: {changes['header']}:" if changes["same"]
            else f"Changes since {changes['since']}:" if changes.get("not_comparable")  # notes M6
            else f"Changes since {changes['since']} (version drift):")
    return ["", head] + [f"  {x}" for x in changes["lines"]] + [f"  Details: {changes['report']}"]


def fixture_line(meta: dict, reports: dict, stamps: dict) -> str | None:
    """`Sweep on jev: found 33 of 34 in its fixtures.` (M1 slice A, owner's answer 3): what the model read found in its own fixtures,
    since the pages say what a read found and a reader should see how well the model that read did on passages with known
    answers. A low count shows and holds nothing. Only when Sweep ran and its fixtures were measured (`Stamp.measured`).
    Rows that got no answer are said: `found 30 of 34 in its fixtures (2 got no answer)`. The model is the person's
    own option as the record kept it, and the counts are the grader's."""
    stamp = stamps.get(SWEEP)
    if reports.get(SWEEP) is None or stamp is None or not stamp.measured or not stamp.recall:
        return None
    found, _, total = str(stamp.recall).partition("/")
    asked = ((reports[SWEEP].get("backends") or [{}])[0].get("backend") or "")
    name = R.flat((meta.get("backends") or {}).get(SWEEP) or asked, R.MODEL_CAP) or "the model"
    out = f"Sweep on {name}: found {found} of {total} in its fixtures"
    if stamp.skipped:
        out += f" ({len(stamp.skipped)} got no answer)"
    return out + "."


def stop_lines(stop: dict, run_dir, waiting=(), backends=None) -> list[str]:
    """The brief's lines for a run that stopped as asked (`--until`; O3), after the headline block: that it
    stopped and that the steps after it did not run; for a stop after intake, that the folder is read as
    it is when the run goes on; the input file an AI step wrote and did not send, if there is one; the model reads that were
    chosen and are waiting (`waiting`, with the backends the record kept); and how to go on, with the option of each
    waiting read, so the choice is one copy away and still the person's to run (choosing a read at `continue` is the
    consent to send; a plain `continue` leaves them out and says so). Walkdown's own words and paths."""
    out = [R.STOPPED_LINE.format(plain=R.stop_plain(stop))]
    if stagelist.INTAKE == stop["after"]:
        out.append("The folder is read as it is when the run goes on.")
    prep = stop["prepared"]
    if prep:
        out.append(R.wrote_line(stop, layout.data_dir(run_dir) / layout.input_file(prep["stage"])))
    backend = dict(backends) if isinstance(backends, dict) else {}
    if prep and prep.get("backend"):
        backend.setdefault(prep["stage"], prep["backend"])
    waiting = list(waiting) or ([prep["stage"]] if prep else [])
    # The record is a file a person can edit, and the command below is one a person is told to run (SKILL.md: relay it as printed), so
    # each backend it kept is held to the rule for the option (`common_lines.record_option`) before it is printed anywhere.
    usable = {s: common_lines.record_option(s, backend.get(s)) for s in waiting}
    unusable = [s for s in waiting if backend.get(s) and usable[s] is None]
    if waiting:
        out.append(common_lines.WAITING_LINE.format(reads="; ".join(
            f'"{R.STEP_NAMES[s]}"' + (f" ({R.flat(usable[s], R.MODEL_CAP)})" if usable[s] else "") for s in waiting)))
    if unusable:
        out.append(common_lines.RECORD_OPTION_UNUSABLE.format(reads=" and ".join(f'"{R.STEP_NAMES[s]}"' for s in unusable)))
    folder = f'"{run_dir}"' if " " in str(run_dir) else str(run_dir)
    return out + ["To go on: python walkdown.py continue " + folder
                  + "".join(" " + common_lines.option_text(stagelist.AI_OPTION[s], usable[s])
                            for s in waiting if s not in unusable)]


def build(meta: dict, reports: dict, stamps: dict, changes: dict | None, run_dir, data: Path) -> str:
    """The brief's text. `reports`: {stage: report}, with None for an AI stage that was chosen, started,
    and left no report; `stamps`: {stage: Stamp}; `changes`: `drift.changes` or None; `data`: the
    run's data folder (a step's error is read from its notes file). `meta["stop"]` (the record's `stop_of`)
    is set for a run that stopped as asked."""
    out = layout.report_dir(run_dir)
    st = results_of(stamps)
    ok = {s for s, rep in reports.items() if rep is not None}
    qa = qaview.of(meta)  # the check of the run: which steps did not work, which reads got no answer
    stop = meta.get("stop")
    left = R.stopped_left(stop)
    legs = {x["leg"]: x["present"] for x in R.fnd(reports, "02.5-capability", "cap.leg")}
    grants = [x["grant"] for x in R.fnd(reports, "02.5-capability", "cap.grant")]
    every = details_html.first_items(reports)
    items = [it for it in every if not details_html.is_model_read(it)]
    model = [it for it in every if details_html.is_model_read(it)]
    by_model = collections.Counter(own_words(it["title"]) for it in model)
    pin = (R.fnd(reports, "02.1-inventory", "inv.pin") or [{}])[0]
    ctx = meta.get("context") or R.DEFAULT_CONTEXT
    cost = summary_html.brief_cost_lines(reports, ctx)  # slice 1: counts only (2026-10-26)
    need = summary_html.brief_needs_line(reports)  # slice 2
    cost += [need] if need else []
    ready = summary_html.brief_ready_line(reports, meta.get("hosts") or [])  # slice 3
    cost += [ready] if ready else []
    fits = summary_html.brief_fit_line(reports)  # slice 5
    cost += [fits] if fits else []
    cleans = summary_html.brief_clean_line(reports)  # slice 6
    cost += [cleans] if cleans else []
    trig = summary_html.brief_trigger_line(reports)  # slice 4: first, as on the page
    cost = ([trig] if trig else []) + cost
    # "Files", not "Files examined" (2026-11-04): the next line says which of them were examined
    examined = ("Files: none yet. Pinned: nothing yet." if INVENTORY in left else
                f"Files: {pin.get('files', '?')}. Pinned: {pin.get('hash_kind', '?')} "
                f"{str(pin.get('hash', '?'))[:12]}.")
    tiers = None if INVENTORY in left else coverage.brief_line(reports)  # 2026-11-04: white, yellow, red, as counts
    L = [f"Walkdown brief: {meta['repo']}", examined, *([tiers] if tiers else []), *cost, ""]
    if "02.5-capability" in left:  # no boxes to tick when the run stopped before the step that ticks them
        L.append(f'What it can do: not measured, the run stopped after "{R.stop_plain(stop)}", as asked.')
    else:
        L.append("What it can do:")
        for k, name in R.LEG_NAMES.items():
            L.append(f"  [{'x' if legs.get(k) else ' '}] {name}")
        L.append(f"  {summary_html.TOGETHER}")
        L.append(f"  Install grants: {', '.join(grants) if grants else 'none'}.")
    rs = summary_html.rows(reports, items)
    wording = summary_html.wording_count(reports, items, rs)
    missing = summary_html.not_run(qa)  # the coded steps: a model read that did not work is said apart (M9)
    down = summary_html.model_down(qa)
    res = {s: w for s, w in st.items() if s in ok and w != "not run"}
    L += ["", summary_html.headline(rs, missing, summary_html.failed_checks(qa), stop, down,
                                    summary_html.incomplete_checks(qa), summary_html.unchecked_sentence(qa))]
    if summary_html.not_run(qa, ai=True):  # the first step that left nothing, a chosen AI step included, never one nobody chose
        L += [f"  {stage_error(data, stage)}" for stage in qa.steps_missing()][:1]
    L += [f"  {x['name']} ({len(x['places'])})" for x in rs]
    if wording:
        n = R.n(wording, "more place" if rs else "place")
        L.append("  " + summary_html.WORDING.format(n=n, be="is" if wording == 1 else "are"))
    if stop:
        L += ["", *stop_lines(stop, run_dir, R.waiting_reads(meta.get("chosen"), reports, stop, meta.get("not_started")),
                              meta.get("backends"))]
    if model:
        L += ["", f"Model reads (experimental): {len(model)} place"
                  f"{'s' if len(model) != 1 else ''}. A model's reading can be wrong."]
        L += [f"  {t} ({n})" for t, n in sorted(by_model.items())]
    tokens = R.tokens_line(reports, stamps)  # what the model reads used, as the backends reported it (M1 slice A)
    if tokens:
        L += ["", tokens]
    said = R.model_read_lines(qa) + R.not_started_lines(qa) + R.dropped_lines(qa)  # counts only (M9)
    if said:
        L += ["", *said]
    # summary.html's terms (owner, 2026-10-25): a check skipped for a missing tool is not named
    steps = summary_html.not_working(qa)
    # the steps that ran and could not be checked: one sentence, in the headline when the run has every step and here if not
    in_headline = not missing and not R.stopped_left(stop)
    unchecked = None if in_headline else summary_html.unchecked_sentence(qa)
    fixture = fixture_line(meta, reports, stamps)  # what Sweep found in its own fixtures, under the fixture checks
    if steps or unchecked or not (in_headline and summary_html.unchecked_sentence(qa)):
        L += ["", (f"Not every step worked in this run: {'; '.join(steps)}." + (f" {unchecked}." if unchecked else "") if steps else
                   f"{unchecked}." if unchecked else
                   "Fixture checks: no step failed." if res else
                   "Fixture checks: none yet, the run stopped before the steps they check." if left == R.NAMED else
                   "Fixture checks: none, this run was made without validation.")]
        L += [fixture] if fixture else []
    elif fixture:
        L += ["", fixture]
    L += ["", f"Report: {out / 'summary.html'}",
          f"Everything behind each answer: {out / 'details.html'}",
          f"Walk through each place and mark it: {out / 'review.html'}",
          f"Every finding with file and line: {out / 'full.md'}", "",
          summary_html.FOOTER]
    # The text the front door has always printed: the brief, a newline, then the changes lines (nothing on a
    # first run) and a newline; a first run therefore ends with one blank line.
    return "\n".join(L) + "\n" + "\n".join(changes_lines(changes)) + "\n"


def write(run_dir, meta: dict, reports: dict, stamps: dict, changes: dict | None, data: Path) -> Path:
    """Save the brief in the run folder as `brief.md`; return its path."""
    path = layout.report_dir(run_dir) / layout.BRIEF
    path.write_text(build(meta, reports, stamps, changes, run_dir, data), encoding="utf-8")
    return path
