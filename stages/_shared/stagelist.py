"""The stage list: `stages/stages.json`, read in one place, and the tables other code builds from it.
Spec: specs/shared.SPEC.md, stagelist.

The list holds, per stage, its name and folder; the words a reader meets (`plain`, and for a stage
with a section in `full.md` its `heading`); for an AI stage the option and the environment variable
that choose it; the earlier steps it reads (`reads`); and the checks it makes (`checks`, M9 slice C: the ids of
`stages/CONTRACT.md`, which the check of the run holds a step's coverage lines to). Every table keyed by stage name is built
here from the list, so a new stage is one entry. The check of the run (`qa`) and the report stage (`report`) are
listed beside the stages and not in them: a run does not choose them and does not stop after them. Nothing here imports
a stage.
"""
from __future__ import annotations

import json
from pathlib import Path

STAGES_FILE = Path(__file__).resolve().parents[1] / "stages.json"
# Section 7 of full.md, "Not examined": the report stage's own. It has no stage and no folder; the
# list's `report` entry holds its heading.
LIMITS = "07-limits"


def load_stage_list(stages_dir=None) -> dict:
    """stages/stages.json, the one home for the stage list (stages/CONTRACT.md)."""
    path = STAGES_FILE if stages_dir is None else Path(stages_dir) / "stages.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _entry(name: str, stages_dir=None) -> dict:
    doc = load_stage_list(stages_dir)
    for s in [*doc["stages"], *([doc["qa"]] if "qa" in doc else []), doc["report"]]:
        if s["name"] == name:
            return s
    raise KeyError(f"{name} is not in stages.json")


def stage_folder(name: str, stages_dir=None) -> str:
    """A stage's folder under stages/, from stages.json (the check of the run's and the report stage's too)."""
    return _entry(name, stages_dir)["folder"]


def reads(stage: str, stages_dir=None) -> tuple[str, ...]:
    """The earlier steps whose outputs `stage` reads, in the order they run."""
    return tuple(_entry(stage, stages_dir).get("reads", ()))


def checks(stage: str, stages_dir=None) -> tuple[str, ...]:
    """The checks `stage` makes, in the order `stages/CONTRACT.md` lists them: the ids its coverage lines
    (`coverage.py`) must cover. Empty for a stage with no list (intake, the check of the run, the report stage)."""
    return tuple(_entry(stage, stages_dir).get("checks", ()))


_DOC = load_stage_list()
_LIST = _DOC["stages"]

STAGES = [s["name"] for s in _LIST]
_POSITION = {name: i for i, name in enumerate(STAGES)}


def position(name: str) -> int:
    """A stage's place in the list, first stage 0: what a sort by stage uses, so an order follows the
    list and never a number read out of a name. KeyError when the name is not a listed stage."""
    return _POSITION[name]

INTAKE = STAGES[0]  # the first stage: gets the folder every later stage reads
FOLDER_STAGES = STAGES[1:]  # the stages that run on that folder
QA = _DOC["qa"]["name"]  # the check of the run (M9 slice B): listed beside the stages, as the report is
REPORT = _DOC["report"]["name"]
# The AI stages run only when a person chooses them, each by its option or its environment variable.
AI_OPTION = {s["name"]: s["option"] for s in _LIST if s.get("option")}
AI_ENV = {s["name"]: s["env"] for s in _LIST if s.get("env")}
AI_HELP = {s["name"]: s["help"] for s in _LIST if s.get("help")}  # the option's line in --help
AI_STAGES = tuple(s for s in FOLDER_STAGES if s in AI_OPTION)
CODED = tuple(s for s in FOLDER_STAGES if s not in AI_STAGES)
# What a reader meets: the step's plain name (pages, the brief), then section 7's heading.
PLAIN = {s["name"]: s["plain"] for s in _LIST if "plain" in s}
CHECKS = {s["name"]: tuple(s["checks"]) for s in _LIST if s.get("checks")}  # the steps that report coverage, by their checks
PLAIN_WITH_LIMITS = {**PLAIN, LIMITS: _DOC["report"]["limits_heading"]}
STEP_WORDS = {**PLAIN_WITH_LIMITS, QA: _DOC["qa"]["plain"]}  # every step a page can name, the check of the run included
# The section headings of full.md, in order: each stage that has a section, then section 7.
HEADINGS = {**{s["name"]: s["heading"] for s in _LIST if "heading" in s},
            LIMITS: _DOC["report"]["limits_heading"]}
