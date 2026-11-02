"""What a step that crashed is allowed to say of its error. Spec: specs/shared.SPEC.md, steperror.

A step's stderr is its traceback, and the line that ends it holds the error's message, which can repeat text from the
audited repository or a model's words. The record, `LOG.md`, and the line the runner prints keep the exit code and the
error's type only; the whole stderr stays in `data/<step>.notes.txt`. The type is read from the line that ends the last
traceback, and only when it is the name of one of Python's own exceptions: a name a library or a message supplies could
be any words. A missing import is named as well when the module is one of Walkdown's own packages.
"""
from __future__ import annotations

import builtins
import re

from packages import OWN_MODULES

TRACEBACK = "Traceback (most recent call last):"
# `ValueError`, `ValueError: the message`: one word, then nothing or a colon. A frame (`File "x.py", line 3`) is not one.
ERROR_LINE = re.compile(r"(\w+)(?::\s*(.*))?$")
MISSING_MODULE = re.compile(r"No module named '([\w.]+)'$")
# A missing import is named when it is one of Walkdown's own packages (`packages.OWN_MODULES`): a step that cannot import one
# names it, as a person's fix. Another module's name is the repository's or a message's, and is not given.


def is_builtin_error(name: str) -> bool:
    """Whether `name` is the name of one of Python's own exceptions (`ValueError`, `ModuleNotFoundError`)."""
    found = getattr(builtins, name, None)
    return isinstance(found, type) and issubclass(found, BaseException)


def error_of(stderr: str) -> tuple[str | None, str | None]:
    """(the error's type, the missing import's `No module named '...'`) from `stderr`: the first line that is not
    indented after the last traceback's header is the line that ends it. (None, None) when there is no traceback, the
    line does not name one of Python's own exceptions, or it is not shaped as an error's line. The module is given only for a
    missing import of one of Walkdown's own packages (`OWN_MODULES`), and as its top-level name. Nothing of the message is
    returned."""
    lines = (stderr or "").splitlines()
    heads = [i for i, line in enumerate(lines) if line.startswith(TRACEBACK)]
    if not heads:
        return None, None
    end = next((x for x in lines[heads[-1] + 1:] if x and x[0] not in " \t"), None)
    m = ERROR_LINE.match(end) if end is not None else None
    if m is None or not is_builtin_error(m.group(1)):
        return None, None
    missing = MISSING_MODULE.match(m.group(2) or "")
    top = missing.group(1).split(".")[0] if missing else None
    return m.group(1), (f"No module named '{top}'" if top in OWN_MODULES else None)


def exit_text(code: int, stderr: str) -> str:
    """`exit 1: ValueError`, or `exit 1` when the stderr names no error: what the record keeps of a crashed step."""
    kind, _ = error_of(stderr)
    return f"exit {code}" + (f": {kind}" if kind else "")
