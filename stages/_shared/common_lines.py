"""Walkdown's own words that the check of the run and the report stage both say. Spec: specs/shared.SPEC.md, common_lines.

The check words a gap in the brief of a held run (`stages/05-qa/hold.py`), and the report stage words the same gap on the
pages and in section 7 once `continue` has released the run. Where a phrase is the same in both it is here once, so the two
read alike.
"""
import options
import stagelist

# A fixture check that gave no verdict: ERROR, SETUP ERROR, NOT BUILT, or `no fixture set` on a step that has fixtures. A step
# that ran and gave a wrong answer on its fixtures (FAIL) is worded where it is said, as it always was. ERROR and SETUP ERROR
# say what the check gave; NOT BUILT and `no fixture set` say the step has no fixtures to be checked against.
UNCHECKED = "could not be checked against its fixtures: it gave {result}"
NO_FIXTURES = "has no fixtures to be checked against"
NO_FIXTURES_RESULTS = ("no fixture set", "NOT BUILT")
# Several steps that could not be checked are said once, as a count.
UNCHECKED_MANY = '{n} steps could not be checked against their fixtures, so a "none" from them is not measured'

# A run that stopped as asked (`--until`): the line the brief of a stopped run and the brief of a held one say.
STOPPED_LINE = 'Stopped after "{plain}", as asked (--until); the steps after it did not run.'

# A model read an earlier command chose that did not run at `continue` (choosing a read at `continue` is the consent to send):
# the person is told, on the terminal when it happens and in the report afterwards. `{how}` is `dropped_how`.
DROPPED_LINE = 'The step "{plain}" was chosen by an earlier command and did not run at continue; {how}.'
DROPPED_NOTE = '"{plain}" was chosen by an earlier command and is not run here; {how}'
DROPPED_LOG = '"{plain}" was chosen by an earlier command and did not run at continue'
# A chosen read waiting behind a stop, in the stop's brief.
WAITING_LINE = "Chosen and waiting: {reads}."


# ---------------------------------------------------------------- coverage gaps (M9 slice C)
# What a check looked at, said once for the hold's brief, section 7, and the pages. A step is named as the reader meets it
# (`stagelist.STEP_WORDS`); a check by its id. A gap holds the step, the check ids, a unit, and four counts: nothing a
# repository could write.

UNIT_ONE = {"files": "file", "entries": "entry", "uses": "program use", "passages": "passage", "findings": "finding",
            "legs": "leg", "grants": "grant", "run": "run"}
UNIT_MANY = {"files": "files", "entries": "entries", "uses": "program uses", "passages": "passages", "findings": "findings",
             "legs": "legs", "grants": "grants", "run": "runs"}
COVERAGE_KINDS = ("coverage-missing", "coverage-short", "coverage-broken")


def unit_words(n: int, unit: str) -> str:
    """`5 files`, `1 file`, `3 passages`."""
    return f"{n} {UNIT_ONE.get(unit, unit) if n == 1 else UNIT_MANY.get(unit, unit)}"


def check_words(checks) -> str:
    """The checks of a coverage line: `The check "a"`, `The checks "a" and "b"`, or `The check "a" and 12 more that run in
    the same pass`."""
    checks = list(checks)
    if len(checks) == 1:
        return f'The check "{checks[0]}"'
    if len(checks) == 2:
        return f'The checks "{checks[0]}" and "{checks[1]}"'
    return f'The check "{checks[0]}" and {len(checks) - 1} more that run in the same pass'


def coverage_gap_text(g: dict) -> str:
    """A coverage gap (`coverage-missing`, `coverage-short`, `coverage-broken`) as one sentence with its full stop, as the
    hold's brief says it and section 7 repeats it:

        The check "phrase.remote-load" of the step "What the text asks for" looked at 3 of 5 files; 2 are not explained.
    """
    plain = stagelist.STEP_WORDS.get(g["step"], g["step"])
    kind = g.get("kind")
    if kind == "coverage-missing":
        miss = list(g.get("missing") or [])
        of_its = g.get("checks_total") or len(miss)
        if len(miss) == 1:
            what = f'its check "{miss[0]}"'
        elif len(miss) == 2:
            what = f'its checks "{miss[0]}" and "{miss[1]}"'
        else:
            what = f'{len(miss)} of its {of_its} checks'
        tail = f', starting with "{miss[0]}"' if len(miss) > 2 else ""
        return f'The step "{plain}" did not say what {what} looked at{tail}.'
    of, looked, explained = g["of"], g["looked_at"], g["explained"]
    head = f'{check_words(g["checks"])} of the step "{plain}"'
    if kind == "coverage-broken":
        if g.get("why") == "check":
            ids = ", ".join(f'"{c}"' for c in g.get("ids") or [])
            first = (g.get("checks") or ["?"])[0]  # two lines can name the same ID, so each is told by its first check
            return (f'The step "{plain}" has a coverage line starting with "{first}" that names a check it does not make '
                    f'or names a check twice: {ids}.')
        if g.get("why") == "found":
            return (f"{head} reported {g.get('found_line')} found where its findings hold {g.get('found_actual')}: "
                    "the counts do not add up.")
        return (f"{head} counted {looked} looked at and {explained} explained of {unit_words(of, g['unit'])}: "
                "the counts do not add up.")
    left = of - looked - explained
    said = f"looked at {looked} of {unit_words(of, g['unit'])}"
    if explained:
        said += f", with {explained} more explained"
    return f"{head} {said}; {left} {'is' if left == 1 else 'are'} not explained."


def coverage_page_words(g: dict) -> str:
    """A coverage gap as a clause for the pages' list of what did not work (no full stop; `A did not run; B ...`)."""
    plain = stagelist.STEP_WORDS.get(g["step"], g["step"])
    kind = g.get("kind")
    if kind == "coverage-missing":
        n = len(g.get("missing") or [])
        return f"{plain} did not say what {n} of its checks looked at" if n != 1 else \
            f"{plain} did not say what one of its checks looked at"
    if kind == "coverage-broken":
        return f"{plain} reported counts that do not add up"
    left = g["of"] - g["looked_at"] - g["explained"]
    return f"{plain} did not look at {unit_words(left, g['unit'])} and does not say why"


def unchecked_phrase(result: str) -> str:
    """What follows a step's name when its fixture check gave no verdict: `has no fixtures to be checked against`, or
    `could not be checked against its fixtures: it gave SETUP ERROR`."""
    return NO_FIXTURES if result in NO_FIXTURES_RESULTS else UNCHECKED.format(result=result)


# The record kept a model option for a read, and it cannot be used as one (a run's record was changed by hand): the command to go on
# leaves that read's option out, and says so in this one sentence.
RECORD_OPTION_UNUSABLE = "The model option the record kept for {reads} could not be used, so the command to go on leaves it out."


def option_text(option: str, backend: str | None = None) -> str:
    """`--sweep jev`: the option that chooses a model read, with its backend where the record has it."""
    return f"--{option} {backend}" if backend else f"--{option}"


def record_option(stage: str, backend) -> str | None:
    """The model option a record kept for `stage`, as a command may carry it, or None. A command that a person is told to run is
    built from the record's words, and a record can be changed by hand, so the value is held to the rule for the option it stands
    for (`options.parse_choice`: a backend Walkdown has that reads for this step, a model of the allowed characters), and is printed
    in the form the options keep (`options.normal`). One that fails, or is not text, or asks for nothing, is None."""
    if not isinstance(backend, str):
        return None
    try:
        chosen, _ = options.parse_choice(stage, backend, "the record")
    except ValueError:
        return None
    return None if chosen == "none" else options.normal(backend)


def dropped_how(stage: str, backends: dict | None, stopped: bool) -> str:
    """How a person gets a dropped read. While the run is stopped, `continue` chooses it: `--sweep jev at continue chooses it`.
    Once it has finished, `continue` refuses, so the way is a new audit, which needs every read before this one too: `to read
    it, audit the repository again with --sweep jev --pinpoint claude-cli`."""
    def text(s):
        return option_text(stagelist.AI_OPTION[s], record_option(s, (backends or {}).get(s)))
    if stopped:
        return f"{text(stage)} at continue chooses it"
    needed = stagelist.AI_STAGES[:stagelist.AI_STAGES.index(stage) + 1]
    return "to read it, audit the repository again with " + " ".join(text(s) for s in needed)
