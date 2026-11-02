"""How a step writes a note on its stderr. Spec: specs/shared.SPEC.md, stagenote.

A step's notes (`data/<step>.notes.txt`) are where the check of the run and the pages read Walkdown's own words from a step:
the line it wrote as `note: ...` is a limit of the run. A note often names a file or a path from the audited repository, and
a name can hold a newline. Written as it is, the rest of the name would start a line of its own, and a name that carries
`note: ` after a newline would read as a note the step wrote. So every note, and the reader's warning that names a file,
goes through here and is flattened to one line.
"""
from __future__ import annotations

import re
import sys

# How many characters of a value that came from a service (the name of the model that answered) a page or a note shows.
MODEL_CAP = 80
# A long read's progress line (`progress`): `sweep: 25 of 431 passages done`, no prefix, so it is not a note. The name is one of the
# two model steps and the counts are ASCII digits (`\d` also matches the digits of other scripts), so a line a step writes that only
# has the shape of one is not taken for one (M1 fix 8).
PROGRESS = re.compile(r"(sweep|pinpoint): [0-9]+ of [0-9]+ passages done")


def flat(text, cap=None) -> str:
    """`text` on one line: every run of whitespace, a newline included, becomes one space. With `cap`, a longer line is cut to
    that many characters, ending in `...`: a value that comes from a service (the model that answered) is shown this way."""
    line = " ".join(str(text).split())
    return line if cap is None or len(line) <= cap else line[:max(cap - 3, 0)].rstrip() + "..."


def note(text) -> None:
    """One note on stderr: `note: ` and the text, on one line."""
    print("note: " + flat(text), file=sys.stderr, flush=True)


def warning(text) -> None:
    """One warning on stderr: `warning: ` and the text, on one line. It is not a note: the check of the run does not read it."""
    print("warning: " + flat(text), file=sys.stderr, flush=True)


def progress(who: str, done: int, total: int) -> None:
    """One plain line on stderr for a long read: `sweep: 25 of 431 passages done`. It has no `note: ` in front, so the check of
    the run does not read it, and it takes a name and two counts and no text, so nothing from outside can be in it."""
    print(f"{flat(who)}: {int(done)} of {int(total)} passages done", file=sys.stderr, flush=True)


def is_progress(line: str) -> bool:
    """Whether a line of a step's stderr is one `progress` wrote."""
    return PROGRESS.fullmatch(line) is not None


def show_progress(line: str) -> bool:
    """The runner's: write a line a step wrote to this process's stderr, as the step wrote it, and only when it is a progress
    line (nothing else a step says is shown). True when it was written."""
    if not is_progress(line):
        return False
    print(line, file=sys.stderr, flush=True)
    return True
