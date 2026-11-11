"""The report stage's view of the check of the run (`data/05-qa.json`). Spec: specs/report.SPEC.md, qaview.

Section 7 of `full.md`, `data/limits.md`, and the lists of steps that did not work (the headline, the warning, the
brief, "What this run covered") are drawn from the check's findings and no longer gathered here (M9 slice B): the
check decides what is a gap and what is a limit, in what order, and the report words them. This module only reads the
file and answers the questions the pages ask of it.
"""
from __future__ import annotations

import json
from pathlib import Path

GAP, LIMIT, CHECKED = "qa.gap", "qa.limit", "qa.checked"


class NoCheck(Exception):
    """The run has no `data/05-qa.json`, or it cannot be read, or it holds none of the limits that stand for every run (the
    check always lists them, so a file without them is not its output)."""


class Qa:
    """The check's findings, in the order it made them (the order of section 7)."""

    def __init__(self, findings=()):
        self.items = [f for f in findings if isinstance(f, dict) and f.get("check") in (GAP, LIMIT)]
        self.checked = [f for f in findings if isinstance(f, dict) and f.get("check") == CHECKED]  # no limits (M9 slice C)

    @classmethod
    def read(cls, data_dir) -> "Qa":
        path = Path(data_dir) / "05-qa.json"
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            findings = doc["findings"]
            if not isinstance(findings, list):
                raise TypeError("findings")
        except (OSError, ValueError, KeyError, TypeError):
            raise NoCheck(f"{path.name} is missing or cannot be read") from None
        qa = cls(findings)
        if not qa.of("standing"):
            raise NoCheck(f"{path.name} is empty")
        return qa

    @property
    def gaps(self) -> list:
        return [f for f in self.items if f["check"] == GAP]

    @property
    def limits(self) -> list:
        return [f for f in self.items if f["check"] == LIMIT]

    def of(self, *kinds) -> list:
        return [f for f in self.items if f.get("kind") in kinds]

    def steps_missing(self) -> list[str]:
        """The steps that should have run and left no output, in order."""
        return [f["step"] for f in self.of("step-missing")]

    def reads_with_no_answer(self) -> list[str]:
        """The model reads that ran and got no answer for any passage."""
        return [f["step"] for f in self.of("model-no-answer")]


def of(meta) -> Qa:
    """The check's view for a report's `meta`: `run.py` puts it there. A `meta` that has none (a page drawn by a test) gets
    an empty one."""
    qa = meta.get("qa")
    return qa if qa is not None else Qa()
