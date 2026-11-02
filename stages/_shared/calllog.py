"""A model call that gets no answer is tried once more, and logged. Spec: specs/shared.SPEC.md, calllog.

The two AI steps (`03-sweep`, `04-pinpoint`) make one call for each passage. A call that ends without an answer
Walkdown can use (an error from the service or the program, an answer outside the options, an answer that cannot
be read) is tried a second time after a short wait (`attempt`); the wait is `retry_wait` in `Library/softreads.yaml`.
The backend puts what happened on the passage's result as `tries`, and the step's runner turns the results into the
call log, `data/<step>.calls.jsonl`, apart from `LOG.md` (`rows`, `write`), and into the `calls` block of the step's
report (`summary`). A log line holds no key, no passage text, and no error message. An error's text can repeat the
passage or the model's own words, so a line keeps only what Walkdown can name: the kind of failure, and a status
where the error has one. Its `qid` names the file and line; the passage is in the step's input file.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def failure(kind: str, status: int | None, reason: str, auth: bool = False, **extra) -> dict:
    """What a try that got no answer reports. `kind`: the failure's kind (an exception's class name, `timeout`,
    `authentication`, `unexpected option`, `unreadable answer`); `status`: an HTTP status code (Jev) or the exit code
    of the program (the CLI), None where the failure has none; `reason`: the words the passage is skipped with, built
    of the kind and the status; `auth`: the service rejected the key. Never an error's own message: it can repeat
    the passage, the prompt, or the model's answer. `extra` rides along (the raw response, an answer kept as it came)."""
    return {"kind": kind, "status": status, "reason": reason, "auth": auth, **extra}


def status_text(status: int | None, word: str = "status") -> str:
    """`, status 503` (or `, exit code 1`) at the end of a reason; nothing when the failure has no status."""
    return "" if status is None else f", {word} {status}"


def attempt(try_once, wait: float, sleep, stopped=lambda: None):
    """Make a call; when it gets no answer, wait `wait` seconds and make it once more.

    `try_once()` returns `(answer, None)` or `(None, failure)`. `stopped()` returns the reason later calls are no
    longer being made (a rejected key), or None; it is asked after the wait, and a call whose first try failed
    while another call's second try was rejected is not made again.

    Returns `(answer, failure, tries)`: the answer, or None; the failure that ended the call (the second try's, or
    the first's when no second try was made), or None; and `tries`, the record of what happened
    (`{"first", "retry", "at"}`), or None when the first try answered."""
    answer, first = try_once()
    if first is None:
        return answer, None, None
    seen = {"kind": first["kind"], "status": first["status"]}
    sleep(wait)
    why = stopped()
    if why:
        return None, first, {"first": seen, "retry": {"result": "not tried", "why": why}, "at": now()}
    answer, second = try_once()
    if second is None:
        return answer, None, {"first": seen, "retry": {"result": "answered"}, "at": now()}
    retry = {"result": "no answer", "kind": second["kind"], "status": second["status"]}
    return None, second, {"first": seen, "retry": retry, "at": now()}


def unsent(why: str) -> dict:
    """`tries` of a passage whose call was never made: there was nothing to call (no key, the package or the
    program missing) or the calls had been stopped (a rejected key)."""
    return {"first": None, "retry": {"result": "not tried", "why": why}, "at": now()}


def rows(results) -> list[dict]:
    """The call log: one line for each result that has `tries`, in the order of the results. A result has
    them when its first try got no answer or it was not sent."""
    return [{"qid": r.get("qid"), "backend": r.get("backend"), "first": r["tries"]["first"],
             "retry": r["tries"]["retry"], "at": r["tries"]["at"]} for r in results or [] if r.get("tries")]


def tally(report) -> tuple[int, int]:
    """(passages a model step asked about, passages that got no answer) from its report: the findings that name a
    passage (`qid`), and those of them that are skips. The no-backend skip names none."""
    asked = [f for f in (report or {}).get("findings", []) if f.get("qid")]
    return len(asked), sum(1 for f in asked if "skipped" in f)


def got_nothing(report) -> bool:
    """A model read that did not work: it asked about passages and none got an answer, even after the retry. A step
    that asked about none (no prose a model reads) is not one."""
    asked, none = tally(report)
    return asked > 0 and none == asked


def write(path, log_rows) -> bool:
    """Save the call log, only when there is a line to write. True when a file was written."""
    if not log_rows:
        return False
    with Path(path).open("w", encoding="utf-8") as fh:
        for row in log_rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return True


def summary(log_rows, log: str | None) -> dict | None:
    """The `calls` block of a step's report, or None when the log has no line (every passage answered on the
    first try). `log`: the log's file name in `data/`, or None when the step was run without `--out`."""
    if not log_rows:
        return None
    return {"log": log,
            "answered_on_retry": sum(1 for r in log_rows if r["retry"].get("result") == "answered"),
            "not_sent": sum(1 for r in log_rows if r["first"] is None)}


def notes(log_rows, log: str | None) -> list[str]:
    """The step's stderr line about its calls: how many answered on the retry, how many got no answer after it,
    how many were not sent, and the call log. Nothing when the log has no line."""
    c = summary(log_rows, log)
    if c is None:
        return []
    none = len(log_rows) - c["answered_on_retry"] - c["not_sent"]
    return [f"calls: {c['answered_on_retry']} answered on the retry, {none} got no answer after it, "
            f"{c['not_sent']} not sent" + (f"; call log: {log}" if log else "")]
