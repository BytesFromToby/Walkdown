"""What a person asked for: the options of a run, declared and read in one place.
Spec: specs/shared.SPEC.md, options.

The front door parses the options once, with the parser built here. The runner takes the result, and
the report stage declares its own two options (`--context`, `--hosts`) with the same function, so no
option is declared twice. The model options (`--sweep`, `--pinpoint`, and the parked `--label` and the
like) share one rule for "asks for nothing": `OFF`. The chosen-stage rule and the refusal rule both
read it, so a value that means off to one means off to the other (restructure step 7, notes F3 and
M14 a). `--reads [model]` chooses the model reads without naming a backend (Sweep on Jev when Jev is available, else on the Claude
model named; Pinpoint on the Claude model named); `check` resolves it into the `--sweep` and `--pinpoint`
values before anything runs, and nothing after that knows of it. Importing this module needs no package: the Library's host table
is read only when a host list is checked.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jevkey  # noqa: E402
import stagelist  # noqa: E402
import stagenote  # noqa: E402

DEFAULT_CONTEXT = 32_000

# A model option or its environment variable set to one of these (any case, spaces ignored) asks for nothing.
OFF = ("", "none", "0", "false", "no", "off")

# These options belonged to Label, Compare, Relational, and the double read. They are parked
# (restructure step 5, decision 5-A) and refused, not ignored.
REFUSED = {"label": "--label", "compare": "--compare", "relational": "--relational", "both": "--both"}
REFUSED_ENV = {"label": "WALKDOWN_SOFT_LABEL", "compare": "WALKDOWN_SOFT_COMPARE",
               "relational": "WALKDOWN_SOFT_RELATIONAL", "both": "WALKDOWN_SOFT_BOTH"}
REFUSAL = "not available in this version: labeling is being rebuilt"

# The backends a model read can run on (M1). The person names one, as `backend` or `backend:model`; Walkdown picks no model for a run
# where the person named nothing, lists no models, and asks nothing (a `claude-cli` with no model named runs `sonnet`). `steps`: the AI steps that take it. `model`: what follows the colon: `none` (a backend that takes no model
# name) or `optional` (the backend has a default). `probability`: whether the backend gives a probability with its Sweep
# answer (the pages word a read by it, `probability.gives`). Jev answers from fixed options with probabilities, so it reads for
# Sweep alone; no model that takes text is asked how sure it is.
SWEEP, PINPOINT = stagelist.AI_STAGES[0], stagelist.AI_STAGES[-1]
BACKENDS = {"jev": {"steps": (SWEEP,), "model": "none", "probability": True},
            "claude-cli": {"steps": (SWEEP, PINPOINT), "model": "optional", "probability": False}}
NOT_FOR = {("jev", PINPOINT): "jev answers from fixed options, and the pinpoint needs a line and a sentence from the model"}
MODEL_ENV = "WALKDOWN_SOFT_CLAUDE_MODEL"  # the model `claude-cli` runs when the option names none


def is_off(value) -> bool:
    """Whether a model option's value (or its environment variable's) asks for nothing."""
    return str("" if value is None else value).strip().lower() in OFF


def refusal(chosen: dict, environ=None) -> str | None:
    """The message for the first refused option the person gave (`chosen`: option name to its
    value, as argparse holds it), or None; then the same for each refused environment variable
    that is not off. Said before anything runs."""
    env = os.environ if environ is None else environ
    for name, flag in REFUSED.items():
        if not is_off(chosen.get(name)):
            return f"{flag} is {REFUSAL}"
    for name, var in REFUSED_ENV.items():
        if not is_off(env.get(var, "")):
            return f"{var} is {REFUSAL}"
    return None


def normal(value) -> str:
    """A model option's value as the stages and the record keep it: stripped, the backend (the text before the first colon)
    in lower case, and the model after it exactly as typed (`Claude-CLI:Opus` is `claude-cli:Opus`)."""
    backend, colon, model = str(value).strip().partition(":")
    return backend.lower() + colon + model


def backend_names(stage: str) -> tuple[str, ...]:
    """The backends that read for this AI step."""
    return tuple(name for name, spec in BACKENDS.items() if stage in spec["steps"])


MODEL_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:/@+-[]")
MODEL_MAX = 200
MODEL_RULE = ("a model name is ASCII letters, digits, and . _ : / @ + - [ ] only, does not start with a dash, has no //, "
              f"and is at most {MODEL_MAX} characters")


def bad_model(model: str) -> str | None:
    """Why a model name cannot be used, or None. It is typed on a command line, sent to a service (on Windows a `.cmd` shim
    hands it to the shell, which reads `& | < > ^ % "` as commands or variables), and named in the reports. A name that passes is
    made of a short list of characters and no others (`MODEL_CHARS`: ASCII letters, digits, and `. _ : / @ + - [ ]`, which
    `sonnet[1m]` and hosted names such as `vendor/model` need), does not start with a dash (a command would read it as an option),
    holds no `//` (`https://host/x` would show in the reports as a link), and is at most `MODEL_MAX` characters. The name a service
    reports as the one that answered is held to the same rule (`textmodel`)."""
    if model == "":
        return "nothing follows the colon; name a model or leave the colon out"
    if len(model) > MODEL_MAX or model.startswith("-") or "//" in model or not set(model) <= MODEL_CHARS:
        return MODEL_RULE
    return None


def shown(text) -> str:
    """A typed value as an error message echoes it: quoted, ASCII only (a character outside it as a backslash escape, so the
    sentence prints on any terminal), and at most 80 characters long, so a long value does not fill the screen."""
    quoted = ascii(str(text))
    return quoted if len(quoted) <= 80 else quoted[:77] + "...'"


def parse_choice(stage: str, value, src: str) -> tuple[str, str | None]:
    """The backend and the model a model option's value names, `("none", None)` for an off value. The backend is the text before
    the first colon, in any case; the rest is the model, exactly as typed. `ValueError` with one sentence that starts with `src`
    (the option or variable the value came from) for a value that cannot be used: an unknown backend, a backend that does not read
    for this step (`--pinpoint jev`), a model after a backend that takes none (`jev:x`), no model after a backend that needs one,
    or a model name `bad_model` refuses. Said before anything runs."""
    if is_off(value):
        return "none", None
    text = str(value).strip()
    head, colon, model = text.partition(":")
    backend = head.lower()
    if backend not in BACKENDS:
        raise ValueError(f"{src}: {shown(text)} is not one of {', '.join(('none', *backend_names(stage)))}")
    spec = BACKENDS[backend]
    if stage not in spec["steps"]:
        raise ValueError(f"{src}: {shown(text)} is refused: {NOT_FOR.get((backend, stage), backend + ' does not read for this step')}")
    if colon and spec["model"] == "none":
        raise ValueError(f"{src}: {shown(text)} is refused: {backend} takes no model name, so give {backend} alone")
    why = bad_model(model) if colon else None
    if why:
        raise ValueError(f"{src}: {shown(text)} is refused: {why}")
    return backend, (model if colon else None)


def ai_choice(stage: str, soft: dict | None, environ=None) -> str:
    """The backend a person chose for this AI stage, as the stage reads it (`normal`), or ""
    when nothing was chosen: its option, else its environment variable, with a value that is not off. An
    option that has a value wins, whatever the value: `--sweep none` or `--sweep off` stands even when the
    variable is set. An option that is empty (`--sweep ""`) is no option, so the variable decides, as it
    did before step 7."""
    env = os.environ if environ is None else environ
    value = (soft or {}).get(stagelist.AI_OPTION[stage]) or env.get(stagelist.AI_ENV[stage]) or ""
    return "" if is_off(value) else normal(value)


def ai_chosen(stage: str, soft: dict | None, environ=None) -> bool:
    """Whether a person chose this AI stage (`ai_choice` names the backend)."""
    return bool(ai_choice(stage, soft, environ))


# ---------------------------------------------------------------- --reads: the sweep on Jev when Jev is available, else on the Claude model named

READS = "reads"
CLAUDE = "claude-cli"
READS_HELP = ("choose the reads without naming a backend: the sweep on TypeSafe's Jev when Jev is available, else on the Claude model MODEL; "
              "the pinpoint on MODEL; tools off; a bare --reads names WALKDOWN_SOFT_CLAUDE_MODEL, else sonnet; "
              "instead of --sweep and --pinpoint; runs only when given")
A_BACKEND = "--reads: {} is a backend, and --reads takes a model name; to name a backend, use --sweep or --pinpoint."
WITH_THE_NAMING_OPTIONS = ("--reads: it cannot be given with --sweep or --pinpoint, which name the reads themselves; "
                           "give one or the other.")
EMPTY_MODEL = "--reads: the model is empty; name one, or leave the model out."
NO_READ_HERE = "--reads: no model read can run here: "
NEITHER = NO_READ_HERE + "Jev has no key or package, and no claude command was found."
ONLY_PINPOINT = NO_READ_HERE + "only Pinpoint is left, and it needs the claude command, which was not found."
NO_PINPOINT = "--reads: Pinpoint needs the claude command, which was not found, so it does not run."


class ReadsAction(argparse.Action):
    """`--reads [model]`: the text that follows it, or True when nothing does. The parser is told what was taken, so that the one
    parse error this can cause (`Parser.error`) can say so."""

    def __init__(self, option_strings, dest, **kwargs):
        kwargs.update(nargs="?", const=True)
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)
        parser.reads_took = values if isinstance(values, str) else None


class Parser(argparse.ArgumentParser):
    """The parser `walkdown.py` and `runner.py` use. It differs from argparse's in one error. `--reads` takes an optional value, so
    `walkdown.py --reads <repo>` reads the repository as the model and leaves no target: that error is one sentence that says so,
    exit 2, with no usage text. Any other error is argparse's own."""
    reads_took = None

    def parse_known_args(self, args=None, namespace=None):
        self.reads_took = None  # what an earlier parse took is not this parse's
        return super().parse_known_args(args, namespace)

    def error(self, message):
        took = self.reads_took
        if isinstance(took, str) and message.startswith("the following arguments are required: "):
            what, first, example = (("run folder to continue", "run folder", "<run folder>") if "run_dir" in message
                                    else ("repository to audit", "repository", "<repo>"))
            self.exit(2, f"error: --reads took {shown(took)} as its model and left no {what}; put the {first} first, "
                         f"as in: {self.prog} {example} --reads [model]\n")
        super().error(message)


def claude_found() -> bool:
    """Whether the Claude Code command is on the path: the question `back_claude` asks before it calls."""
    return shutil.which("claude") is not None


def steps_done(run_dir) -> frozenset:
    """The steps that the record of the run in `run_dir` says ran and worked; empty for a folder with no readable record (the
    runner refuses that in its own words)."""
    import record
    try:
        rec = record.read(Path(run_dir).resolve())
        return frozenset(s["stage"] for s in rec["steps"] if s.get("ok")) if rec else frozenset()
    except (AttributeError, KeyError, TypeError):
        return frozenset()


def reads_plan(model: str | None, jev: bool, claude: bool, done=frozenset()) -> tuple[dict, str | None, str | None]:
    """The table of `--reads` as a function of what the machine has: ({"sweep": its value, "pinpoint": its value}, the note
    to print or None, the sentence to refuse with or None). `model`: what the person typed after `--reads`, or None for a bare
    one. `done`: the steps that already ran (`continue`); a read that ran is not chosen. A read `--reads` does not run is `none`."""
    named = CLAUDE if model is None else f"{CLAUDE}:{model}"
    sweep_todo, pin_todo = SWEEP not in done, PINPOINT not in done
    nothing = {"sweep": "none", "pinpoint": "none"}
    if sweep_todo and not (jev or claude):
        return nothing, None, NEITHER
    if pin_todo and not sweep_todo and not claude:
        return nothing, None, ONLY_PINPOINT
    sweep = ("jev" if jev else named) if sweep_todo else "none"
    pinpoint = named if pin_todo and claude else "none"
    return {"sweep": sweep, "pinpoint": pinpoint}, (NO_PINPOINT if sweep_todo and pin_todo and not claude else None), None


def resolve_reads(a: argparse.Namespace, jev: bool | None = None, claude: bool | None = None) -> tuple[str | None, str | None]:
    """`--reads`, resolved: (the sentence to refuse with or None, the note to print or None). On success `a.sweep` and `a.pinpoint`
    hold what the table gives, as if they had been typed, and `a.reads` stays as typed. Nothing is probed unless `--reads` was
    given, and nothing is probed for an off value. `jev` and `claude` stand for what the machine has (a test passes them);
    left out, Jev's availability (`jevkey.available`, which sends nothing and shows no key) and `claude_found` are asked. At `continue`
    the steps the run's record says ran are left out."""
    reads = getattr(a, READS, None)
    if reads is None:
        return None, None
    if any(getattr(a, option, None) for option in stagelist.AI_OPTION.values()):
        return WITH_THE_NAMING_OPTIONS, None
    text = None if reads is True else str(reads).strip()
    if text == "":
        return EMPTY_MODEL, None
    if text is not None and is_off(text):  # asks for nothing: both reads are none, and the variables are stood over
        a.sweep = a.pinpoint = "none"
        return None, None
    if text is not None and text.partition(":")[0].lower() in BACKENDS:  # a backend typed as the model would be handed to `claude` as one
        return A_BACKEND.format(shown(text)), None
    why = bad_model(text) if text is not None else None
    if why:
        return f"--reads: {shown(text)} is refused: {why}", None
    jev = jevkey.available() if jev is None else jev
    claude = claude_found() if claude is None else claude
    done = steps_done(a.run_dir) if getattr(a, "continuing", False) else frozenset()
    chosen, note, refused = reads_plan(text, jev, claude, done)
    if refused:
        return refused, None
    a.sweep, a.pinpoint = chosen["sweep"], chosen["pinpoint"]
    return None, note


# ---------------------------------------------------------------- the report's two options

def parse_context(s) -> int:
    """`32k`, `200k`, `8192`, `8k`, `1m` (k is 1,000): a positive token count, else ValueError."""
    t = str(s).strip().lower().replace(",", "").replace("_", "")
    mult = {"k": 1_000, "m": 1_000_000}.get(t[-1:], 1)
    num = float(t[:-1] if mult > 1 else t)
    if not num > 0:
        raise ValueError(f"not a token count: {s}")
    return int(num * mult)


def host_keys() -> tuple[str, ...]:
    """The AI hosts the report can name, from the Library's `hosts.yaml`."""
    import library
    return tuple(library.load_yaml("hosts.yaml")["hosts"])


def parse_hosts(s) -> list[str]:
    """`claude,codex`: the host names, in the order given, each once; ValueError on an unknown or
    empty one."""
    keys, out = host_keys(), []
    for x in str(s).split(","):
        k = x.strip().lower()
        if k not in keys:
            raise ValueError(f"not a host: {x.strip()!r}")
        if k not in out:
            out.append(k)
    return out


def add_report_options(ap: argparse.ArgumentParser) -> None:
    """The two options that shape the reports: the front door and the report stage both take them."""
    ap.add_argument("--context", default=None,
                    help="expected context in tokens, such as 32k, 200k, or 8192 (default 32k); "
                         "a re-render keeps the run's own unless this is given")
    ap.add_argument("--hosts", default=None,
                    help="the AI hosts you build for, comma-separated, such as claude,codex,cursor; the "
                         "report lists what each is missing; a re-render keeps the run's own unless "
                         "this is given")


def add_until_option(ap: argparse.ArgumentParser) -> None:
    """`--until <step>`: stop after a step. The run and `walkdown.py continue` both take it."""
    ap.add_argument("--until", default=None, metavar="STEP",
                    help="stop after this step, given by its name (02.4-phrases), number (02.4), or word "
                         "(phrases); coded is the last coded step. Go on later with: walkdown.py continue "
                         "<run folder>")


def _add_choices(ap: argparse.ArgumentParser, developer: bool) -> None:
    """What a run and a continued run both take besides the target: the AI stages' options (from
    stages.json), `--until`, the parked options (declared only to be refused), `--revalidate`, and the report
    options. `developer` adds `--no-validate`."""
    for stage, option in stagelist.AI_OPTION.items():
        ap.add_argument(f"--{option}", default=None, help=stagelist.AI_HELP.get(stage))
    ap.add_argument(f"--{READS}", action=ReadsAction, default=None, metavar="MODEL", help=READS_HELP)
    add_until_option(ap)
    for k in REFUSED:  # parked (step 5): declared only to be refused
        if k == "both":
            ap.add_argument("--both", action="store_true", help=argparse.SUPPRESS)
        else:
            ap.add_argument(f"--{k}", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--revalidate", action="store_true",
                    help="re-run the fixture validation even if a stamp for this code is cached")
    add_report_options(ap)
    if developer:
        ap.add_argument("--no-validate", action="store_true", help="skip the grader (tests only)")


def add_run_options(ap: argparse.ArgumentParser, developer: bool = False) -> None:
    """The options of a run, in the order the front door lists them. Intake takes the target, `--name`,
    `--fresh`, and `--keep`; each AI stage is chosen by its option, which stages.json names; the parked
    options are declared only to be refused. `developer` adds the ones tests use."""
    ap.add_argument("target", help="a folder, or a git URL to clone")
    ap.add_argument("--name", help="name for the run folder (default: the repository's name)")
    ap.add_argument("--fresh", action="store_true", help="delete an earlier clone and clone again")
    ap.add_argument("--keep", action="store_true",
                    help="audit an earlier clone as it is, without updating it")
    _add_choices(ap, developer)
    if developer:
        ap.add_argument("--repo", help="name for RepoResults/<repo>/ (default: intake's name)")
        ap.add_argument("--results", default=str(Path(__file__).resolve().parents[2] / "RepoResults"))
        ap.add_argument("--date", default=None, help="the run's date, YYYY-MM-DD (default: today)")


def add_continue_options(ap: argparse.ArgumentParser, developer: bool = False) -> None:
    """The options of `walkdown.py continue <run folder>`: the run folder, then what the steps still to run
    take. Intake's options are not declared, since intake does not run again. The parsed options say they
    are for `continue` (`continuing`): there an AI step is chosen by its option alone, and its environment
    variable is not read, since choosing it is the consent to send."""
    ap.add_argument("run_dir", help="a run folder that stopped (it was made with --until)")
    _add_choices(ap, developer)
    ap.set_defaults(continuing=True)


def ai_environ(a: argparse.Namespace) -> dict | None:
    """The environment that can choose an AI step for these options: None (the process's own) for a run, and
    an empty one for `continue`, where only the option chooses."""
    return {} if getattr(a, "continuing", False) else None


def env_not_read_notes(soft: dict | None, environ=None) -> list[str]:
    """For `continue`: one note for each AI stage whose environment variable is set to a value that is not off
    while its option is not given. The variable is not read there; the note says how to send."""
    env = os.environ if environ is None else environ
    return [f"{stagelist.AI_ENV[s]} is not read at continue; give --{stagelist.AI_OPTION[s]} <backend> to send"
            for s in stagelist.AI_STAGES
            if not (soft or {}).get(stagelist.AI_OPTION[s]) and not is_off(env.get(stagelist.AI_ENV[s], ""))]


# ---------------------------------------------------------------- --until: the steps and their names

def until_names() -> dict[str, str]:
    """Every way `--until` can name a step, in lower case, with the step it names. A step's name
    (`02.4-phrases`), its number (`02.4`), and its word (`phrases`); and for steps that share a folder under
    stages/ (`02-coded`), the folder's name, number, and word (`02-coded`, `02`, `coded`), which name the
    last of them. Built from stages.json, so a new step needs no new name here."""
    names, last = {}, {}
    for s in stagelist.load_stage_list()["stages"]:
        for key in (s["name"], *s["name"].partition("-")[::2]):
            names[key.lower()] = s["name"]
        group = s["folder"].partition("/")[0]
        if group != s["folder"]:
            last[group] = s["name"]
    for group, name in last.items():
        for key in (group, *group.partition("-")[::2]):
            names.setdefault(key.lower(), name)
    return names


def resolve_until(typed) -> str | None:
    """The step a `--until` value names, or None when it names none."""
    return until_names().get(str(typed).strip().lower())


def model_env_refusal(backend: str, model: str | None, named: str | None) -> str | None:
    """The message for a `WALKDOWN_SOFT_CLAUDE_MODEL` (`named`) that `bad_model` refuses, when it is the model that will run: a
    `claude-cli` whose option names no model. Else None. The front door checks it before anything runs, and each stage checks it
    again, since a stage can be run on its own."""
    if backend == "claude-cli" and model is None and named and bad_model(named):
        return f"{MODEL_ENV}: {shown(named)} is refused: {bad_model(named)}"
    return None


def check_models(a: argparse.Namespace) -> str | None:
    """The model options, read as a stage will read them (`parse_choice`): the message for a value that cannot be used, or None.
    A run reads each option, else its environment variable; `continue` reads the option alone. A `claude-cli` with no model
    named in the option also has `WALKDOWN_SOFT_CLAUDE_MODEL` read, since that is the model it will run."""
    environ = os.environ if ai_environ(a) is None else ai_environ(a)
    for stage in stagelist.AI_STAGES:
        option = stagelist.AI_OPTION[stage]
        if not hasattr(a, option):  # the report stage declares only its own two options and reads no model option
            continue
        given = getattr(a, option, None)
        src = f"--{option}" if given else stagelist.AI_ENV[stage]
        try:
            backend, model = parse_choice(stage, given or environ.get(stagelist.AI_ENV[stage]) or "", src)
        except ValueError as exc:
            return str(exc)
        why = model_env_refusal(backend, model, os.environ.get(MODEL_ENV))
        if why:
            return why
    return None


def check_until(a: argparse.Namespace) -> str | None:
    """`--until`, read: the message for a value that names no step, or an AI step nobody chose; else None,
    and the typed value is replaced by the step's name."""
    typed = getattr(a, "until", None)
    if typed is None:
        return None
    step = resolve_until(typed)
    if step is None:
        return (f"--until {typed!r} is not a step (names: {', '.join(stagelist.STAGES)}; a number such as "
                "02.4 or a word such as phrases works too, and coded means the last coded step)")
    soft = {option: getattr(a, option, None) for option in stagelist.AI_OPTION.values()}
    if step in stagelist.AI_STAGES and not ai_chosen(step, soft, ai_environ(a)):
        if getattr(a, READS, None) is not None:  # the person typed --reads: the options it stands for are not theirs
            return f"--until {typed}: --reads does not run that step here"
        return f"--until {typed}: that step runs only when chosen (--{stagelist.AI_OPTION[step]})"
    a.until = step
    return None


def check(a: argparse.Namespace) -> str | None:
    """Before anything runs: the message for an option the person must change, or None. The parked
    options and variables are refused; `--reads` is resolved into the model options (`resolve_reads`, which may print its one
    note); the model options are read (`check_models`); `--until` is read (it must name a
    step, and an AI step only when chosen); `--hosts` and `--context` are read. On success they hold a step's name, a
    list of host names, and a token count in place of what was typed."""
    refused = refusal(vars(a))
    if refused:
        return refused
    reads, note = resolve_reads(a)  # --reads becomes the --sweep and --pinpoint it stands for, before they are read
    if reads:
        return reads
    if note:
        stagenote.note(note)  # `note: ...` on one line, as every note is written (a step that imports this module writes none other)
    models = check_models(a)
    if models:
        return models
    until = check_until(a)
    if until:
        return until
    if getattr(a, "hosts", None) is not None:
        try:
            a.hosts = parse_hosts(a.hosts)
        except ValueError as exc:
            return f"--hosts: {exc} (names: {', '.join(host_keys())})"
    if getattr(a, "context", None) is not None:
        try:
            a.context = parse_context(a.context)
        except ValueError:
            return f"--context {a.context!r} is not a token count (try 32k, 200k, or 8192)"
    return None
