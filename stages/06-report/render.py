"""Assemble the summary, full report, LOG, and limits. Spec: specs/report.SPEC.md, render.

Pure functions over stage reports. Nothing here detects or judges; every rule
that picks what to show is a fixed table below.
"""
from __future__ import annotations

import collections
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "_shared"))
import layout  # noqa: E402
import library  # noqa: E402
import options  # noqa: E402
import probability  # noqa: E402
import qaview  # noqa: E402
import rates  # noqa: E402
import stagelist  # noqa: E402
import usage  # noqa: E402
from audience import audience, is_test_data  # noqa: E402
import common_lines  # noqa: E402
from limitnote import LIMIT_NOTE  # noqa: E402
from stagenote import MODEL_CAP, flat  # noqa: E402
from validate import Stamp  # noqa: E402

# The tables the builder step reads, read here from the Library (data, not the step's code), with
# the words the report puts under each kind of place they find (restructure step 3b)
HOST_TABLE = library.load_yaml("hosts.yaml")
TRIGGER_TABLE = library.load_yaml("trigger.yaml")
TOOLS_TABLE = library.load_yaml("tools.yaml")
FIT_TABLE = library.load_yaml("fit.yaml")
CLEAN_TABLE = library.load_yaml("clean.yaml")

# The stage tables are built from stages/stages.json (`stagelist`): a stage's section heading, its
# plain name, which are the AI stages. `STATUS` and `SECTIONS` below map a stage to the function
# that writes its part; they stay code, and a test checks their keys against the list.
HEADINGS = dict(stagelist.HEADINGS)  # the stages with a section in full.md, then "07-limits" (Not examined)
ORDER = list(HEADINGS)
# The builder checks (needs, hosts, trigger, asks, clean, fit, cost) are their own step since
# restructure step 4. Their findings are shown inside the sections above (what the text asks for,
# what this touches), as before, so the step has no section of its own.
BUILDER = "02.6-builder"
# Section 6 is the AI reads. Two stages feed it, Sweep (03-sweep) and Pinpoint (04-pinpoint), each
# run only when a person chose it (restructure step 5); Sweep's name keys the section in the
# tables below, and a default run has neither report. A chosen stage that failed is a key of
# `reports` with the value None: it counts as a step that did not work, as the builder does.
AI_STAGES = stagelist.AI_STAGES
AI_SECTION = AI_STAGES[0]
NO_MODEL_READ = ("No model read was chosen; optional: `--sweep jev`, then `--pinpoint claude-cli`.")
# A stage with no answer sheet and no fixtures (Pinpoint) is stamped with these words, not graded
# (grader.py, decision 5-C). It is neither a pass nor a failure: nothing is wrong with the step.
NO_FIXTURE = "no fixture set"
UNSTAMPED_OK = ("PASS", NO_FIXTURE)
# LOG.md's stage table: intake (restructure step 2) and the builder step (step 4) have a row and a
# validation stamp there and no section in any report, so neither is in HEADINGS or ORDER. An AI
# stage has a row only in a run that chose it (`log` adds it).
LOG_ROWS = (stagelist.INTAKE, *stagelist.CODED)
# The steps every page and the brief name when one did not run or did not pass its fixture check
# ("Not every step worked", the headline's "steps did not run", the brief's step counts, "What
# Walkdown didn't check", the limits): the five that always have a section, and the builder step
# after `02.5-capability` (round 2 of step 4: a failed step must be named), by the words a reader meets. The
# AI stages are not here: a run that did not choose them did not skip them.
NAMED = stagelist.CODED
STEP_NAMES = dict(stagelist.STEP_WORDS)  # the check of the run is a step a gap can name


def step(stage: str) -> str:
    """A step named the way a reader meets it: `step "What the text asks for"`, its plain name in
    quotes (stages/stages.json), as the failed-step lines say it. Reader text puts "the" or "The" in
    front. A step id (`02.4-phrases`) is never on a page (restructure step 8b)."""
    return f'step "{STEP_NAMES[stage]}"'


# ---- a run that stopped as asked (`--until`; parked item O3). `stop` is the record's `stop_of`: {"after": the
# step it stopped after, "prepared": {"stage", "items", "backend"} or None}, None for a run that went through.

def stopped_left(stop) -> tuple[str, ...]:
    """The coded steps a stop left out: those after the step it stopped at. A step the stop left out is not
    one that failed, and the pages, the brief, and the limits say why it did not run. Empty for a run that
    went through, and for one stopped after the last coded step."""
    if not stop:
        return ()
    cut = stagelist.position(stop["after"])
    return tuple(s for s in NAMED if stagelist.position(s) > cut)


def stop_plain(stop) -> str:
    """The plain name of the step a run stopped after."""
    return STEP_NAMES[stop["after"]]


STOPPED_LINE = common_lines.STOPPED_LINE
WROTE_LINE = 'Wrote {path}: what "{plain}" would send, {items}. Nothing was sent.'
WENT_ON_LINE = 'Went on after "{plain}" on {at} (walkdown.py continue).'
RELEASED_LINE = ('The check of the run held this run ({gaps}); its report was written on {at} (walkdown.py continue) '
                 "with what the run had.")


def wrote_line(stop, path) -> str | None:
    """The line for an input file a stop wrote and did not send, or None when it wrote none."""
    prep = (stop or {}).get("prepared")
    if not prep:
        return None
    return WROTE_LINE.format(path=path, plain=STEP_NAMES[prep["stage"]], items=n(prep["items"], "passage"))


STOP_NOT_MEASURED = 'Not measured: the run stopped after the step "{plain}", as asked.'
STOP_INPUT_LINE = ('The run stopped after "{plain}", as asked; what "{ai}" would send is in data/{file}; '
                   "nothing was sent.")


def stop_not_measured(stop) -> str | None:
    """The "Not measured" line of a section whose step the run's stop left out (the builder checks feed the
    sections of full.md that need it), or None when the stop left the builder step in. Cards 1 to 7 of the
    pages say the same."""
    return STOP_NOT_MEASURED.format(plain=stop_plain(stop)) if BUILDER in stopped_left(stop) else None


def stop_input_line(stop) -> str | None:
    """One line for the pages of a stop that wrote an input file and sent nothing, or None: where the run
    stopped, what the waiting step would send, and the file (Walkdown's words and its own path)."""
    prep = (stop or {}).get("prepared")
    if not prep:
        return None
    return STOP_INPUT_LINE.format(plain=stop_plain(stop), ai=STEP_NAMES[prep["stage"]],
                                  file=layout.input_file(prep["stage"]))


def stopped_steps_line(stop) -> str | None:
    """details.html's own line for the steps a stop left out, or None when it left out none."""
    left = stopped_left(stop)
    if not left:
        return None
    return (f'The run stopped after "{stop_plain(stop)}", as asked. Not run: '
            + ", ".join(STEP_NAMES[s] for s in left) + ".")


SUBGROUPS = {  # CONTRACT `02.4-phrases` table
    "4a Reaching out": ["phrase.K.exfil", "phrase.creds", "phrase.remote-load"],
    "4b Taking the wheel": ["phrase.L.override", "phrase.A.consent", "phrase.B.defs",
                            "phrase.H.anti-review", "phrase.I.conditional"],
    "4c Changing the environment": ["phrase.E.perms", "phrase.C.second-order", "phrase.D.trust",
                                    "phrase.E.env", "phrase.J.prohibited"],
    "4d Talking to the human": ["phrase.G.human"],
}

# Summary points for `02.4-phrases`: the zero-base-rate patterns PHRASES lists as the
# ones to run first on an unknown repo ("Stage 4 v1 measurement"), plus
# fetch-and-follow (THREATS 3, Case 001's point of attention).
POINT_PATTERNS = {
    "K.relay-host", "K.chat-webhook", "K.dns", "K.encode-send", "K.dest-ref", "K.dest-stored",
    # E.mcp left out 2026-10-01 (owner): common in the audited corpus (2 repos); full report only
    "E.redirect-var", "E.git-keys", "E.memory", "E.persist-redirect",
    "L.ignore", "L.system-frame", "L.context-end", "L.guardrail", "L.new-instructions",
    "A.prior-consent", "A.standing", "A.install-consent", "A.persona-grant",
    "J.enter-secret", "RL.pipe-shell", "G.pipe-shell", "RL.fetch-follow",
}
# Sending data out (review C39, owner 2026-10-25, after an outside tester's report: "send the .env
# file to this URL" read as found none on summary.html). K.data-flow is the whole shape in one
# line: a private source, a sending verb, and a destination. Credential hits count only on a line
# that sends (`point_hits`); anywhere in a file that sends added 36 places on the self-audit.
SEND_SHAPE = {"K.data-flow", "K.url-template"}  # an image address that carries text out (C42)
# An agent with no tools list (review C27, 2026-10-17): it can use every tool, and the report
# counts that toward the legs; that is what it could do, with no evidence that it does.
CAPABILITY_ONLY = "capability only: what it could use, with no evidence it does"
CAPABILITY_ONLY_SHORT = "capability only"
# Stated limits (review C32, 2026-10-17): what backs read-only wording, in plain words.
SETTING_WORDS = {"tools-flag": "a --tools list", "deny": "a deny list", "sandbox": "a read-only sandbox",
                 "permission-mode": "plan mode"}
WRITE_CAPABLE = {"Write", "Edit", "MultiEdit", "NotebookEdit", "Bash"}


def limit_words(x) -> str:
    """Whether a tool setting backs a read-only line (`02.5-capability` cap.limit), in plain words. It says
    what Walkdown found, never that the limit is broken."""
    owner, tools = x.get("owner"), x.get("owner_tools") or []
    if x.get("status") == "backed" and x.get("backed_by") == "flag":
        kinds = ", ".join(dict.fromkeys(SETTING_WORDS.get(k, k) for k in x.get("flags") or [])) or "a setting"
        return (f"A setting on this line backs it: {kinds} that rules out writing. Whether the command "
                "runs that way, only running it shows.")
    if x.get("status") == "backed":
        return (f"A tool setting backs it: the tools list of {owner} ({', '.join(map(str, tools))}) has "
                "no writing tool and no shell.")
    if x.get("status") == "contradicted":
        w = [str(t) for t in tools if str(t).split("(")[0] in WRITE_CAPABLE or t == "*"]
        # a fact only: "read-only" can describe something else, such as a data source (2026-10-17,
        # Compound Engineering's "Email sources are read-only"), which no setting decides
        return f"No tool setting backs it: the tools list of {owner} includes {', '.join(w)}."
    return ("Stated in the text; Walkdown found no tool setting that enforces it"
            + (f" ({owner} has no tools list)." if owner else "."))


def limit_routes(x, cap: int = 3) -> str:
    """Other routes in the same skill that can write, or ""."""
    rs = x.get("other_routes") or []
    if not rs:
        return ""
    shown = "; ".join(f"{r['file']}" + (f":{r['line']}" if r.get("line") is not None else "")
                      + f" ({r['what']})" for r in rs[:cap])
    return (f"Elsewhere in the same skill, a route can write: {shown}"
            + (f"; +{len(rs) - cap} more" if len(rs) > cap else "") + ".")  # full.md: one per evidence line, so kept short (owner)
# Measured base rates of `02.4-phrases` patterns over the audited corpus (soft D1; tools/baserates.py
# writes the table, `rates` reads it).
BASE = rates.load()
COL = 32  # summary label column: longest heading plus a space

# The trifecta legs in plain words, locked by the owner 2026-09-30 (THREATS "Organizing frame").
# "Can ...": a static read shows what a skill could do, never what it does (owner, 2026-10-20,
# review C31 part B; the 2026-09-30 names were "Reads your data", "Takes outside input",
# "Sends data out", which the v1 page at the tag report-v1 keeps).
LEG_NAMES = {"private-data": "Can read your data", "untrusted-content": "Can take outside input",
             "external-comms": "Can send data out"}
LEG_DEFS = {
    "private-data": "Reads the user's data, wherever it lives: files, secrets, settings, connected accounts.",
    "untrusted-content": "Brings in text the user didn't write: the web, other people's issues or email, MCP tools, third-party code.",
    "external-comms": "Moves data off the machine or into shared places: web requests, webhooks, pushes, posts.",
}
# Plain words, no named term on the page (owner 2026-10-07); the docs credit Simon Willison's
# "lethal trifecta".
# Reworded by the owner 2026-10-21: no "It is not an issue on its own", which pulled against
# the sentence before it.
TRIFECTA_ALL = ("All three at once: it can read your data, take outside input, and send data out. "
                "That is the combination text from outside can steer into sending your data away.")
TRIFECTA_SOME = ("{n} of 3. That risk needs all three at once: reading your data, taking outside "
                 "input, and sending data out.")
NOT_WHAT = ('What this is not: static examination only. "Clean" means these stages found '
            "nothing; it does not mean the artifact is safe. This report offers possible issues "
            "with evidence and reaches no verdict. What to do with it is yours to decide.")

# Stage notes that name something the run did not examine (for 07-limits): `stages/_shared/limitnote.py`, which the
# check of the run (`05-qa`) reads too.

# The limits that stand for every run, by the id the check of the run gives them (`stages/05-qa/gather.py` STANDING): the
# check says which stand, and these are their words.
# The heading, at the end of section 7 of full.md and as the fold on details.html (with a count), of the checks that found nothing
# and what each looked at (M9 slice C). They are no limits: the lines above it are, and `data/limits.md` holds those alone.
CHECKED_HEADING = "Checks that found nothing"
STANDING_LIMITS = {
    "static": "Static examination only. Nothing in the artifact was executed, fetched, or installed.",
    "model-reads": "The optional model reads are located observations from the backends section 6 names. "
    "Sweep flags passages for a person to read, and Pinpoint names the line behind each flag. "
    "Neither changes a finding in sections 1 to 5.",
    "version-drift": "Version drift (class 8): each run examines one pinned copy. walkdown.py compares it with "
    "the previous run of the same repository when there is one (changes.md next to this report); "
    "what the artifact becomes after its next update is seen only by auditing it again.",
    "english-only": "English-language scope: the phrase layer is blind to non-English text (the "
    f"{step('02.2-reader')} lists non-Latin runs, and prose passages in another language in "
    "Latin script; a short line can slip past that check).",
    "phrases-zero": f"The {step('02.4-phrases')} matches patterns; a payload phrased outside every pattern "
    "reads as no hit. A zero here is not safety.",
}


# ---------------------------------------------------------------- helpers

def code(s) -> str:
    """Inline code span that survives backticks inside the text; newlines shown as \\n."""
    s = str(s).replace("\r", "").replace("\n", "\\n")
    run = max((len(m) for m in re.findall(r"`+", s)), default=0)
    fence = "`" * (run + 1)
    pad = " " if s.startswith("`") or s.endswith("`") or run else ""
    return f"{fence}{pad}{s}{pad}{fence}"


def one_line(s) -> str:
    """A line of `full.md` as one line. A value from the repository (a hook's matcher, a plugin's name, a front matter field,
    a file name) can hold a line break, and the rest of it would start a line of its own that reads as the report's. `code`
    shows one inside a code span; this takes care of every other place, at the one point every line goes through."""
    return " ".join(str(s).splitlines())


def loc(f) -> str:
    """Where a finding is: the file (on one line: a name from the repository can hold a newline, and in `full.md` the rest of
    the name would start a line of its own) and the line."""
    if f.get("file") is None:
        return "(repo)"
    name = flat(f["file"])
    if f.get("line") is not None:
        return f"{name}:{f['line']}"
    if f.get("text_line") is not None:  # a PDF, DOCX, or image: the line in its extracted text
        page = f", page {f['page']}" if f.get("page") is not None else ""
        return f"{name} (extracted text{page}, line {f['text_line']})"
    return name


def fnd(reports, stage, check=None):
    rep = reports.get(stage) or {}
    return [f for f in rep.get("findings", []) if check is None or f["check"] == check]


def ai_fnd(reports, check=None):
    """The findings of the AI stages that ran (Sweep, then Pinpoint), optionally of one check. A
    run that chose neither has none."""
    return [f for stage in AI_STAGES for f in fnd(reports, stage, check)]


def ai_backends(reports) -> list[dict]:
    """The backend rows of the AI stages that ran: role, backend, remote, model."""
    return [b for stage in AI_STAGES for b in (reports.get(stage) or {}).get("backends") or []]


def ai_chosen(reports, notes=None) -> list[str]:
    """The AI stages a person chose and that were started: each is a key of `reports` (its report,
    or None when it failed and left none) or has notes. A stage nobody chose has neither."""
    return [s for s in AI_STAGES if s in reports or s in (notes or {})]


def ai_started(reports=None, runs_ok=()) -> list[str]:
    """The AI stages whose absence of output is a step that did not work: those started, which are
    keys of `reports` (None is a stage that failed). With no `reports` given, those that produced
    output. A stage nobody chose is never here."""
    if reports is None:
        return [s for s in AI_STAGES if s in runs_ok]
    return [s for s in AI_STAGES if s in reports]


# What `02.4-phrases` used to emit that is the builder step's now (restructure step 4): everything but
# `fit.unused`, `fit.missing`, `fit.inherits`, `fit.hook`, `fit.checked`, `cap.ship`, `cap.context`,
# which `02.5-capability` emitted.
PHRASES_ORIGIN = ("need.", "port.", "host.", "trig.", "ask.", "fit.loop", "clean.")


def phrases_findings(r):
    """Every finding `02.4-phrases` held before the builder checks moved out, in the order it held them:
    its own, then the builder's that were `02.4-phrases`'s. Lookups by line (the audience of a line, the
    quote of a line) read these so that they give what they always gave."""
    return fnd(r, "02.4-phrases") + [f for f in fnd(r, BUILDER) if f["check"].startswith(PHRASES_ORIGIN)]


def n(x, word, plural=None) -> str:
    return f"{x} {word if x == 1 else (plural or word + 's')}"


def pairs(reports, kind):
    return [f for f in fnd(reports, "02.5-capability", "cap.pair") if f.get("pair") == kind]


def stamp_suffix(stamps, stage) -> str:
    st = stamps.get(stage)
    if st is None or st.result in UNSTAMPED_OK:
        return ""
    return f" Validation {st.result}: see 7."


# ---------------------------------------------------------------- status lines

def status(reports, stamps, stage, stop=None) -> str:
    if stage not in reports or reports[stage] is None:
        if stage not in reports and stage in stopped_left(stop):  # the run was asked to stop before it (O3)
            return f'Not run: the run stopped after "{stop_plain(stop)}", as asked. See 7.'
        return "Not run. See 7."
    return STATUS[stage](reports) + stamp_suffix(stamps, stage)


def pin_of(r) -> dict:
    """The inventory's `inv.pin` finding, or an empty one when its report has none (a saved inventory with no findings is a
    report; the pages must not need a pin to be drawn)."""
    return (fnd(r, "02.1-inventory", "inv.pin") or [{}])[0]


def hook_where(h) -> str:
    """Where a hook is: its config file; and when its command is masked, the line to open, since the words no longer tell it from
    the next hook there."""
    span = h.get("span")
    return f"{h['file']}:{span[0]}" if h.get("masked") and span else h["file"]


def _s1(r):
    pin = pin_of(r)
    hooks = fnd(r, "02.1-inventory", "struct.hooks")
    configs = len({h["file"] for h in hooks})
    agents = fnd(r, "02.1-inventory", "struct.agent-tools")
    mans = sum(len(m.get("files", [])) for m in fnd(r, "02.1-inventory", "struct.manifests"))
    langs = pin.get("script_languages") or {}
    return (f"{n(pin.get('files', 0), 'file')}, {n(len(pin.get('extensions') or {}), 'format')}, "
            f"{n(len(langs), 'script language')}. {n(len(hooks), 'hook')} "
            f"({n(configs, 'host config')}). {n(len(agents), 'agent or command definition')}. "
            f"{n(mans, 'platform manifest')}.")


def _s2(r):
    total = pin_of(r).get("files", 0)
    unread = len(fnd(r, "02.2-reader", "read.unread"))
    read = total - unread
    pct = f"{100 * read / total:.1f}%" if total else "n/a"
    div = fnd(r, "02.2-reader", "read.divergence")
    div = [d for d in div if "skipped" not in d]
    carriers = collections.Counter(d.get("carrier", "?") for d in div)
    cs = ", ".join(f"{v} {k}" for k, v in carriers.most_common())
    fold = len(fnd(r, "02.2-reader", "read.fold"))
    script = len(fnd(r, "02.2-reader", "read.script"))
    lang = len(fnd(r, "02.2-reader", "read.language"))
    return (f"{read}/{total} files ({pct}). {n(len(div), 'divergence')}"
            f"{' (' + cs + ')' if cs else ''}. {n(fold, 'line')} changed by folding. "
            f"{n(script, 'non-Latin run')}. {n(lang, 'passage')} in a language other than English.")


def _s3(r):
    entries = len(fnd(r, "02.3-graph", "graph.entry"))
    orph = len(fnd(r, "02.3-graph", "graph.orphan"))
    dang = fnd(r, "02.3-graph", "graph.dangling")
    ctx = collections.Counter(d.get("context", "?") for d in dang)
    cs = ", ".join(f"{v} {k}" for k, v in ctx.most_common())
    dyn = len(fnd(r, "02.3-graph", "graph.dynamic"))
    depth = fnd(r, "02.3-graph", "graph.depth")
    loaded = sum(1 for d in depth if d.get("via") == "dynamic")
    mentioned = sum(1 for d in depth if d.get("via") == "mention")
    tail = " Graph incomplete by construction." if dyn else ""
    unl = len(fnd(r, "02.3-graph", "graph.unlisted"))
    tail = (f" {n(unl, 'skill, agent, or command', 'skills, agents, or commands')} on disk that "
            f"their manifest leaves out." if unl else "") + tail
    away = sum(1 for d in dang if d.get("folder_missing"))
    away_s = f"; {away:,} of them into a folder the repository does not have" if away else ""
    return (f"{n(entries, 'entry point')}. {n(orph, 'orphan')}. "
            f"{n(len(dang), 'dangling reference')}{' (' + cs + away_s + ')' if cs else ''}. "
            f"{n(dyn, 'dynamic load')}: {n(loaded, 'file')} loaded only through one (named by "
            f"nothing), {n(mentioned, 'file')} reached only through a mention of a folder or wildcards."
            f"{tail}")


def tag_text(s: str | None) -> str | None:
    """What the Unicode tag characters in a line spell, each run joined by a space, or None
    (review C42: the report listed the code points and never the sentence)."""
    return " ".join(library.tag_texts(s or "")) or None


def selector_text(s: str | None) -> str | None:
    """What the runs of variation selectors in a line spell (`library.runs`, the one run finder),
    each run joined by a space, or None. A run that spells nothing adds nothing (P1, 2026-10-29)."""
    return " ".join(" ".join(r.text.split()) for r in library.runs(s or "") if r.text) or None


def lookalike_note(h: dict) -> str:
    """For a host written with look-alike letters (review C42): what it imitates, and its punycode."""
    if not h.get("lookalike_of"):
        return ""
    puny = f", {h['punycode']}" if h.get("punycode") else ""
    return f" (look-alike letters{puny}; imitates {h['lookalike_of']})"


# What it costs and what ships (plan for builders, slice 1, owner 2026-10-26). The builder's
# expected context, with Claude's beside it; tokens are `02.5-capability`'s estimate from size.
DEFAULT_CONTEXT = options.DEFAULT_CONTEXT  # the option is read in options.py
CLAUDE_CONTEXT = 200_000
TOKEN_NOTE = ("Tokens are estimated from size: about 4 bytes of English text per token; text in "
              "other scripts runs high.")
SHIP_GROUPS = {
    "entry": "Skills, agents, and commands",
    "project": "Project instructions and what they import",
    "on-demand": "Named by a file the AI loads",
    "maybe": "Reached only by a wildcard or a folder read",
    "run": "Scripts it runs",
    "config": "Configs the host reads",
    "people": "Written for people",
    "build": "Build material: tests, fixtures, CI, tooling",
    "unused": "Nothing points to it",
}
SHIP_BANDS = (("Loads into the AI", ("entry", "project", "on-demand", "maybe")),
              ("Used another way", ("run", "config")),
              ("Not used at run time", ("people", "build", "unused")))


def cost(r) -> dict:
    """`02.5-capability`'s context tiers: `session`, `project`, the entry with the most at its fullest
    (`largest`, ties to the first by path) and its tiers, and how many entries there are."""
    rows = fnd(r, BUILDER, "cap.context")
    per: dict[str, dict] = {}
    for x in rows:
        if x.get("file"):
            per.setdefault(x["file"], {})[x["tier"]] = x
    largest = min(per, key=lambda f: (-per[f].get("skill-max", {}).get("tokens", 0), f), default=None)
    return {"session": next((x for x in rows if x["tier"] == "session"), None),
            "project": next((x for x in rows if x["tier"] == "project"), None),
            "largest": largest, "tiers": per.get(largest, {}), "entries": len(per)}


def what(kind) -> str:
    return {"agent": "agent", "command": "command"}.get(kind, "skill")


def context_rows(r) -> list[tuple[str, int]]:
    """(label, tokens) for the expected-context table, in order; empty with no `02.5-capability` tiers."""
    c, out = cost(r), []
    if c["session"] is not None:
        out.append(("Every session, once installed (descriptions, hooks)", c["session"]["tokens"]))
    if c["project"]:
        out.append(("Every session in this folder (project instructions)", c["project"]["tokens"]))
    t = c["tiers"]
    if t:
        w = what(t["skill-runs"].get("kind"))
        out.append((f"When the largest {w} runs", t["skill-runs"]["tokens"]))
        out.append((f"That {w} and everything it names", t["skill-full"]["tokens"]))
        if t["skill-max"]["tokens"] > t["skill-full"]["tokens"]:
            out.append(("With its wildcard and folder loads", t["skill-max"]["tokens"]))
    return out


def pct(tok: int, ctx: int) -> str:
    p = 100 * tok / ctx
    return "under 1%" if 0 < p < 1 else f"{round(p):,}%"


def unknown_line(r) -> str | None:
    """What only running shows, counted: hooks with no estimate, MCP servers' tool lists."""
    s = cost(r)["session"] or {}
    k = collections.Counter(u.get("what") for u in s.get("unknown") or [])
    parts = ([n(k["hook"], "hook with no size estimate", "hooks with no size estimate")] if k["hook"] else []) \
        + ([n(k["mcp"], "MCP server's tool list", "MCP servers' tool lists")] if k["mcp"] else [])
    return ("Not counted, because only running shows them: " + " and ".join(parts) + ".") if parts else None


def ship_bands(r) -> list[dict]:
    """Per band: `name`, `groups` ({group: {files, bytes, tokens}}), and the band's totals."""
    by: dict[str, dict] = {}
    for x in fnd(r, BUILDER, "cap.ship"):
        g = by.setdefault(x["group"], {"files": 0, "bytes": 0, "tokens": 0})
        g["files"] += 1
        g["bytes"] += x.get("bytes") or 0
        g["tokens"] += x.get("tokens") or 0
    out = []
    for name, groups in SHIP_BANDS:
        mine = {g: by[g] for g in groups if g in by}
        out.append({"name": name, "groups": mine, "files": sum(v["files"] for v in mine.values()),
                    "bytes": sum(v["bytes"] for v in mine.values()),
                    "tokens": sum(v["tokens"] for v in mine.values())})
    return out


def left_out(r) -> dict:
    """What leaving out the files nothing points to and the build material would save."""
    rows = [x for x in fnd(r, BUILDER, "cap.ship") if x["group"] in ("unused", "build")]
    return {"unused": sum(1 for x in rows if x["group"] == "unused"),
            "build": sum(1 for x in rows if x["group"] == "build"),
            "bytes": sum(x.get("bytes") or 0 for x in rows),
            "tokens": sum(x.get("tokens") or 0 for x in rows)}


def kb(b: int) -> str:
    if b < 1024:
        return f"{b:,} bytes"
    return f"{b / 1024:,.1f} KB" if b < 1024 * 1024 else f"{b / 1024 / 1024:,.1f} MB"


def in_sentence(s: str) -> str:
    """A name inside a sentence: lower case first, unless it starts with an acronym (AI, CI)."""
    return s if s[1:2].isupper() else s[:1].lower() + s[1:]


def ship_lines(r, ctx: int) -> list[str]:
    """full.md section 5: the context tiers against the expected context, then every file by group."""
    if not fnd(r, BUILDER, "cap.ship"):
        return [f"No file groups: this run has no graph from the {step('02.3-graph')} for the "
                f"{step(BUILDER)} to read."]
    L = [f"Expected context: {ctx:,} tokens (a line for {CLAUDE_CONTEXT:,} beside it). {TOKEN_NOTE}", ""]
    L += [f"- {label}: {tok:,} tokens, {pct(tok, ctx)} of {ctx:,}, {pct(tok, CLAUDE_CONTEXT)} of {CLAUDE_CONTEXT:,}"
          for label, tok in context_rows(r)]
    c = cost(r)
    if c["largest"]:
        L.append(f"- The largest is {code(c['largest'])}, of {n(c['entries'], 'skill, agent, or command', 'skills, agents, or commands')}.")
    u = unknown_line(r)
    if u:
        L.append(f"- {u}")
    L += ["", "Every skill, agent, or command, by tier (tokens):", ""]
    per: dict[str, dict] = {}
    for x in fnd(r, BUILDER, "cap.context"):
        if x.get("file"):
            per.setdefault(x["file"], {})[x["tier"]] = x
    L += [f"- {loc({'file': f})}: runs {t['skill-runs']['tokens']:,}, with what it names {t['skill-full']['tokens']:,}, "
          f"with wildcard loads {t['skill-max']['tokens']:,}"
          + (f"; names {n(len(t['skill-max']['outside']), 'file')} outside its folder, not counted: "
             + ", ".join(code(x) for x in t['skill-max']['outside']) if t['skill-max'].get('outside') else "")
          for f, t in sorted(per.items())] or ["None."]
    for band in ship_bands(r):
        L += ["", f"#### {band['name']}: {n(band['files'], 'file')}, {kb(band['bytes'])}, {band['tokens']:,} tokens", ""]
        rows = sorted((x for x in fnd(r, BUILDER, "cap.ship") if x["group"] in dict(SHIP_BANDS)[band["name"]]),
                      key=lambda x: (dict(SHIP_BANDS)[band["name"]].index(x["group"]), x["file"]))
        L += [f"- {code(x['file'])}: {in_sentence(SHIP_GROUPS[x['group']])}, {kb(x.get('bytes') or 0)}, "
              + (f"{x['tokens']:,} tokens" if x.get("tokens") is not None else "not text")
              + (f", reached from {code(x['reached_by'])}" if x.get("reached_by") else "") for x in rows] or ["None."]
    return L


# Will it run on someone else's machine? (plan for builders, slice 2, owner 2026-10-26): `02.4-phrases`'s
# need and port findings, and `02.3-graph`'s references that match only when case is ignored. The kinds
# and their words are Library/tools.yaml (`port_kinds`).
PORT_KINDS = tuple((k["check"], k["name"], k["why"]) for k in TOOLS_TABLE["port_kinds"])


def needs_of(r) -> dict:
    """{commands, packages, undeclared (names), port: [(check, name, why, places)] with places},
    and `measured`: whether this run made the check (slice 2, 2026-10-26). There is no marker
    finding, so a run counts as measured when it found something here, or when it holds slice 3's
    host.coverage (built after slice 2); a run made before it says Not measured, never "nothing"
    (report v3 recount, 2026-10-27)."""
    cmds = fnd(r, BUILDER, "need.command")
    pkgs = fnd(r, BUILDER, "need.package")
    port = []
    for check, name, why in PORT_KINDS:
        stage = "02.3-graph" if check == "graph.case" else BUILDER
        places = sorted(fnd(r, stage, check), key=lambda f: (f.get("file") or "", f.get("line") or 0))
        if check == "graph.case":  # only where it runs or the AI reads it, as for personal paths
            places = [f for f in places if not is_test_data(f.get("file")) and audience(f.get("file") or "") != "human"]
        if places:
            port.append((check, name, why, places))
    measured = BUILDER in r and bool(cmds or pkgs or port or fnd(r, BUILDER, "host.coverage"))
    return {"commands": cmds, "packages": pkgs, "port": port, "measured": measured,
            "undeclared": [c["command"] for c in cmds if not c.get("declared")]
            + [p["package"] for p in pkgs if not p.get("declared")]}


def where(f) -> str:
    return f"{f.get('file')}:{f['line']}" if f.get("line") else str(f.get("file"))


def needs_lines(r, stop=None) -> list[str]:
    """full.md section 1: what it needs, then what ties it to one machine; every finding."""
    n_ = needs_of(r)
    if not n_["measured"]:
        return ["### What it needs", "",
                stop_not_measured(stop) or f"Not measured: the {step(BUILDER)} did not run.", ""]
    dec = lambda f: ("declared in " + ", ".join(f"{d['file']} ({d['how']})" for d in f["declared_in"])  # noqa: E731
                     if f.get("declared") else "not declared")
    L = ["### What it needs", "",
         "Programs are the ones Walkdown recognizes (`Library/tools.yaml`); declared means named "
         "in a dependency file, a skill's compatibility field, or an install line.", ""]
    L += [f"- {code(c['command'])}: {dec(c)}; used at " + ", ".join(
          f"{loc(u)} ({u['how']})" for u in c["uses"]) for c in n_["commands"]] or ["- No program Walkdown recognizes."]
    L += [f"- {code(p['package'])} ({p['ecosystem']}): {dec(p)}; imported in "
          + ", ".join(code(x) for x in p["files"]) for p in n_["packages"]] or ["- No package imported."]
    L += ["", "### What ties it to one machine", ""]
    for check, name, why, places in n_["port"]:
        L.append(f"{name} ({len(places)}): {why}.")
        L += [f"- {loc(f)}" + (f": {f['why']}" if f.get("why") else "")
              + (f": {code(f['written'])}" if f.get("written") else "") for f in places]
        L.append("")
    if not n_["port"]:
        L += ["Nothing found that ties it to one machine.", ""]
    return L


# ---------------------------------------------------------------- is it ready for any AI (slice 3)

HOST_KEYS = tuple(HOST_TABLE["hosts"])
NO_HOSTS = "none named"
# The features that work on one host only, with their words: Library/hosts.yaml (`feature_kinds`).
FEATURE_KINDS = tuple((k["kind"], k["name"], k["why"]) for k in HOST_TABLE["feature_kinds"])


def reads(host: str) -> str:
    """What a host reads, from hosts.yaml, for a host with none of its files here."""
    h = HOST_TABLE["hosts"][host]
    inst = [x for x in h["instructions"] if not x.startswith("**/")][:3]
    s = ", ".join(inst)
    if h.get("skills"):
        s += "; skills in " + ", ".join(h["skills"])
    return s


def _some(names, cap=3) -> str:
    return ", ".join(names[:cap]) + (f", and {len(names) - cap} more" if len(names) > cap else "")


def ready_of(r) -> dict:
    """{measured, coverage (hosts.yaml order), drift, differ, features [(kind, name, why, places)],
    skills (every SKILL.md outside test data), loose (those no host reads where they sit)}."""
    cov = fnd(r, BUILDER, "host.coverage")
    drift = fnd(r, BUILDER, "host.drift")
    feats = fnd(r, BUILDER, "host.feature")
    skills = sorted(f["file"] for f in fnd(r, "02.1-inventory", "inv.file")
                    if f["file"].rsplit("/", 1)[-1] == "SKILL.md" and not is_test_data(f["file"]))
    read = {s for c in cov for s in c.get("skill_files", [])}
    kinds = []
    for kind, name, why in FEATURE_KINDS:
        places = sorted((f for f in feats if f["kind"] == kind), key=lambda f: (f["file"], f.get("line") or 0))
        if places:
            kinds.append((kind, name, why, places))
    return {"measured": BUILDER in r and bool(cov), "coverage": cov, "drift": drift,
            "differ": [d for d in drift if d["relation"] == "differ"], "features": kinds,
            "skills": skills, "loose": [s for s in skills if s not in read]}


def has_files(c) -> bool:
    return bool(c["instructions"] or c["skills"])


def host_line(c) -> str:
    """One host: the files here it reads, or what it would read."""
    parts = []
    if c["instructions"]:
        parts.append(_some(c["instructions"]))
    if c["skills"]:
        parts.append(n(c["skills"], "skill"))
    if c["mcp"]:
        parts.append("MCP config " + ", ".join(c["mcp"]))
    if c["hooks"]:
        parts.append(n(len(c["hooks"]), "hook file"))
    if parts:
        return f"{c['name']}: " + "; ".join(parts) + "."
    return f"{c['name']}: none of its files (it reads {reads(c['host'])})."


def short(c) -> str:
    """A host's name in a list of hosts."""
    return HOST_TABLE["hosts"][c["host"]].get("short") or c["name"]


def names(xs) -> str:
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]


def _read(xs, what) -> str:
    return f"{names(xs)} {'reads' if len(xs) == 1 else 'read'} {what}"


def drift_line(d, cov) -> str:
    """A pair that differs, and which hosts read one, the other, or both."""
    s = (f"{d['file']} and {d['other']} differ: {n(d['only_here'], 'line')} only in {d['file']}, "
         f"{d['only_there']} only in {d['other']}.")
    a = [short(c) for c in cov if d["file"] in c["instructions"] and d["other"] not in c["instructions"]]
    b = [short(c) for c in cov if d["other"] in c["instructions"] and d["file"] not in c["instructions"]]
    both = [short(c) for c in cov if d["file"] in c["instructions"] and d["other"] in c["instructions"]]
    said = [_read(x, w) for x, w in ((a, d["file"]), (b, d["other"]), (both, "both")) if x]
    return s + (" " + "; ".join(said) + "." if said else "")


TODO_KINDS = {"frontmatter": "skill frontmatter key", "claude-words": "Claude Code word",
              "claude-tool": "Claude Code tool name", "import": "@ import"}


def todo(r, targets) -> list[str]:
    """For the hosts the builder named (--hosts): per host, a missing instruction file or skill
    folder, the places written for another host only, and other hosts' hooks; then each pair of
    copies that differ where the named hosts read different sides."""
    rd = ready_of(r)
    cov = {c["host"]: c for c in rd["coverage"]}
    read_any = any(c["skills"] for c in rd["coverage"])
    out = []
    for t in (t for t in targets if t in cov):
        c, h = cov[t], HOST_TABLE["hosts"][t]
        items = []
        if not c["instructions"]:
            items.append(f"no instruction file it reads ({_some([x for x in h['instructions'] if not x.startswith('**/')])})")
        if not c["skills"] and read_any:
            items.append("none of the skills sit where it reads them ("
                         + (", ".join(h["skills"]) if h.get("skills") else "it reads no skills") + ")")
        feats = [f for *_, places in rd["features"] for f in places if f["host"] != t and f["kind"] != "hooks"]
        if feats:
            per = collections.Counter(f["kind"] for f in feats)
            items.append(f"{n(len(feats), 'place')} written for Claude Code only ("
                         + ", ".join(n(v, TODO_KINDS[k]) for k, v in per.items()) + ")")
        hooks = collections.Counter(f["host"] for *_, places in rd["features"] for f in places
                                    if f["kind"] == "hooks" and f["host"] != t)
        for host, k in hooks.items():
            items.append(f"{n(k, 'hook file')} for {HOST_TABLE['hosts'][host]['name']}, which "
                         f"{'does' if k == 1 else 'do'} not run on it")
        out += [f"{c['name']}: {x}." for x in items] or [f"{c['name']}: nothing missing."]
    for d in rd["differ"]:
        a = [short(cov[t]) for t in targets if t in cov and d["file"] in cov[t]["instructions"]
             and d["other"] not in cov[t]["instructions"]]
        b = [short(cov[t]) for t in targets if t in cov and d["other"] in cov[t]["instructions"]
             and d["file"] not in cov[t]["instructions"]]
        if a and b:
            out.append(f"{_read(a, d['file'])} and {_read(b, d['other'])}, which differ "
                       f"({n(d['only_here'], 'line')} only in the first, {d['only_there']} only in the second).")
    return out


def ready_lines(r, targets=(), stop=None) -> list[str]:
    """full.md section 4: ready for any AI; every finding."""
    rd = ready_of(r)
    L = ["### Ready for any AI", ""]
    if not rd["measured"]:
        return L + [stop_not_measured(stop) or f"Not measured: this run has no host findings (the {step(BUILDER)} "
                    "did not run, or the run was made before they were counted).", ""]
    L += ["What each AI host reads is in `Library/hosts.yaml` (dated, with sources).", ""]
    if targets:
        L += ["For the hosts named (" + ", ".join(targets) + "):", ""] + [f"- {x}" for x in todo(r, targets)] + [""]
    L += [f"- {host_line(c)}" for c in rd["coverage"]] + [""]
    if rd["loose"]:
        L += [f"Skills no host reads where they sit ({len(rd['loose'])}); a host reads them once they are "
              "installed (copied into its skill folder, or added as a plugin):", ""]
        L += [f"- {code(s)}" for s in rd["loose"]] + [""]
    L += [f"Copies kept for two hosts ({len(rd['drift'])}):", ""]
    L += [f"- {code(d['file'])} and {code(d['other'])}: {d['relation']}"
          + (f", {n(d['only_here'], 'line')} only in the first, {d['only_there']} only in the second"
             if d["relation"] == "differ" else "") for d in rd["drift"]] or ["- None."]
    L.append("")
    for kind, name, why, places in rd["features"]:
        L += [f"{name} ({len(places)}): {why}.", ""]
        L += [f"- {loc(f)}: {code(f['what'])}" + (f" ({HOST_TABLE['hosts'][f['host']]['name']})" if kind == "hooks" else "")
              for f in places] + [""]
    if not rd["features"]:
        L += ["No one-host feature found.", ""]
    return L


# ---------------------------------------------------------------- will it trigger (slice 4)

BYTES_PER_TOKEN = library.load_yaml("loading.yaml")["bytes_per_token"]
FRONT_TEXT = {"yaml-error": "the YAML does not parse", "not-first-line": "--- is not on the first line",
              "missing": "no frontmatter (Claude Code uses the first line as its description; the Agent "
                         "Skills spec requires a name and a description)",
              "bom": "a byte-order mark comes before ---; the docs do not say whether it is read"}
RULE_TEXT = {
    "name-missing": "no name (Claude Code uses the folder's; the Agent Skills spec requires one)",
    "name-long": "a name over 64 characters (Agent Skills spec)",
    "name-chars": "a name with characters other than lowercase letters, digits, and single hyphens (Agent Skills spec)",
    "name-folder": "a name that is not its folder's (Agent Skills spec)",
    "name-reserved": "\"anthropic\" or \"claude\" in the name (claude.ai uploads and the Skills API refuse it)",
    "name-xml": "an XML tag in the name (claude.ai uploads and the Skills API refuse it)",
    "description-missing": "no description (Claude Code uses the first line; the Agent Skills spec requires one)",
    "description-empty": "an empty description (Agent Skills spec)",
    "description-long": "a description over 1,024 characters (Agent Skills spec)",
    "description-xml": "an XML tag in the description (claude.ai uploads and the Skills API refuse it)",
    "listing-cut": "cut in Claude Code's listing",
    "agent-name": "a subagent name Claude Code skips (it starts with -, holds :, or is over 256 characters)",
    "name-duplicate": "a subagent name used twice (names are unique across the agents)",
}
GUIDANCE_TEXT = {"no-when": "does not say when to use it", "first-person": "written in the first person",
                 "second-person": "written in the second person"}
# The kinds of trigger finding and their words: Library/trigger.yaml (`trigger_kinds`).
TRIG_KINDS = tuple((k["kind"], k["name"], k["why"]) for k in TRIGGER_TABLE["trigger_kinds"])


def trigger_of(r) -> dict:
    """{measured, entries, listing, kinds [(kind, name, why, places)]} from `02.4-phrases`'s trig.*."""
    t = lambda c: fnd(r, BUILDER, c)  # noqa: E731
    entries, rules, lst = t("trig.entry"), t("trig.rule"), t("trig.listing")
    groups = {"not-read": t("trig.frontmatter"),
              "skipped": [e for e in entries if e["mode"] == "skipped" and e.get("why") != "its frontmatter is not read"],
              "rules": [f for f in rules if f["rule"] != "listing-cut"],
              "keys": t("trig.key"), "values": t("trig.value"), "tools": t("trig.tool"),
              "overlap": t("trig.overlap"), "cut": [f for f in rules if f["rule"] == "listing-cut"],
              "guidance": t("trig.guidance")}
    kinds = [(k, name, why, sorted(groups[k], key=lambda f: (f.get("file") or "", f.get("line") or 0)))
             for k, name, why in TRIG_KINDS if groups[k]]
    return {"measured": BUILDER in r and bool(lst), "entries": entries,
            "listing": lst[0] if lst else None, "kinds": kinds}


def trig_parts(kind, f) -> tuple[str, str]:
    """One place: (where, what), in words."""
    if kind == "not-read":
        return where(f), FRONT_TEXT[f["kind"]] + (f" ({f['error']})" if f.get("error") else "")
    if kind == "skipped":
        return f["file"], f["why"]
    if kind == "rules":
        return where(f), RULE_TEXT[f["rule"]] + (f" ({f['other']})" if f.get("other") else "")
    if kind == "keys":
        return where(f), f["key"] + (f" (Claude Code knows {f['near']})" if f.get("near") else "")
    if kind == "values":
        return where(f), f"{f['field']}: {f['value']}"
    if kind == "tools":
        if f["kind"] == "older":
            return where(f), (f"{f['tool']} (an older name; the current one is {f['now']}, and the docs do not "
                              "say whether the old one still works)")
        return where(f), f["tool"] + (f" (the tool is {f['near']})" if f.get("near") else "")
    if kind == "overlap":
        return f"{f['file']} and {f['other']}", f"{n(f['count'], 'word')} shared ({', '.join(f['shared'])})"
    if kind == "cut":
        return where(f), f"{f['chars']:,} characters; the last {f['lost']:,} never reach the AI"
    return where(f), GUIDANCE_TEXT[f["kind"]]


def trig_place(kind, f) -> str:
    return ": ".join(trig_parts(kind, f))


def entries_line(tr) -> str:
    """How the entries trigger, by kind."""
    ents = tr["entries"]
    if not ents:
        return "No skill, agent, or command here."
    out = []
    sk = [e for e in ents if e["kind"] != "agent"]
    if sk:
        nsk = sum(1 for e in sk if e["kind"] == "skill")
        head = " and ".join(x for x in (n(nsk, "skill") if nsk else "", n(len(sk) - nsk, "command") if len(sk) > nsk else "") if x)
        c = collections.Counter(e["mode"] for e in sk)
        auto = c["auto"] + c["paths"]
        bits = [f"{auto} Claude chooses by {'its' if auto == 1 else 'their'} description"
                + (f" ({c['paths']} only on matching files)" if c["paths"] else "")] if auto else []
        bits += [f"{c['typed']} only when typed"] if c["typed"] else []
        bits += [f"{c['unread']} whose frontmatter is not read"] if c["unread"] else []
        hidden = sum(1 for e in sk if not e.get("menu", True))
        bits += [f"{hidden} hidden from the / menu"] if hidden else []
        out.append(f"{head}: {', '.join(bits)}.")
    ag = [e for e in ents if e["kind"] == "agent"]
    if ag:
        off = sum(1 for e in ag if e["mode"] == "skipped")
        bits = ([f"{len(ag) - off} Claude Code loads"] if len(ag) > off else []) + ([f"{off} it does not"] if off else [])
        out.append(f"{n(len(ag), 'agent')}: {', '.join(bits)}.")
    return " ".join(out)


def listing_lines(tr, ctx: int) -> list[str]:
    """The descriptions Claude chooses by, against Claude Code's listing and the agent warning."""
    lst = tr["listing"]
    if not lst:
        return []
    share = TRIGGER_TABLE["listing_share"]
    out = []
    if lst["skills"]:
        tok = round(lst["listing_chars"] / BYTES_PER_TOKEN)
        s = (f"Skill descriptions here take about {tok:,} tokens ({lst['listing_chars']:,} characters). Claude "
             f"Code's listing of every installed skill holds about {share:.0%} of the context: about "
             f"{round(ctx * share):,} tokens at {ctx:,}, {round(CLAUDE_CONTEXT * share):,} at {CLAUDE_CONTEXT:,}.")
        if tok > ctx * share:
            s += (f" At {ctx:,} these alone do not fit, and Claude Code drops the descriptions of the skills "
                  "used least.")
        out.append(s)
    if lst["agents"]:
        tok = round(lst["agent_chars"] / BYTES_PER_TOKEN)
        warn = TRIGGER_TABLE["agent_warning_tokens"]
        out.append(f"Agent descriptions take about {tok:,} tokens"
                   + (f", over the {warn:,} at which Claude Code warns at startup." if tok > warn else "."))
    return out


def brief_trigger_counts(tr) -> dict:
    """{host, guidance, overlap}: places that break a host rule, guidance rows, overlapping pairs."""
    k = {kind: len(p) for kind, _, _, p in tr["kinds"]}
    host = sum(k.get(x, 0) for x in ("not-read", "skipped", "rules", "keys", "values", "tools", "cut"))
    return {"host": host, "guidance": k.get("guidance", 0), "overlap": k.get("overlap", 0)}


def trigger_lines(r, ctx: int, stop=None) -> list[str]:
    """full.md section 4: will it trigger; every entry and finding."""
    tr = trigger_of(r)
    L = ["### Will it trigger", ""]
    if not tr["measured"]:
        return L + [stop_not_measured(stop) or f"Not measured: this run has no trigger findings (the {step(BUILDER)} "
                    "did not run, or the run was made before they were counted).", ""]
    L += ["What each host does with a skill's, agent's, or command's frontmatter is in "
          "`Library/trigger.yaml` (dated, with sources).", "", entries_line(tr), ""]
    L += listing_lines(tr, ctx) + [""] if tr["listing"] and (tr["listing"]["skills"] or tr["listing"]["agents"]) else []
    L += [f"- {code(e['file'])} ({e['kind']}): {e['mode']}" + (f", {e['why']}" if e.get("why") else "")
          + (f"; description {e['description_chars']:,} characters" if e["description_chars"] else "")
          for e in tr["entries"]]
    if tr["entries"]:
        L.append("")
    for kind, name, why, places in tr["kinds"]:
        L += [f"{name} ({len(places)}): {why}.", ""] + [f"- {trig_place(kind, f)}" for f in places] + [""]
    if tr["entries"] and not tr["kinds"]:
        L += ["Every entry has frontmatter its host reads and follows the rules.", ""]
    return L


# ---------------------------------------------------------------- do the tools fit the job (slice 5)

# The words for work, for how often a hook runs, and for each kind of fit finding: Library/fit.yaml
# (`family_text`, `often_text`, `fit_kinds`).
FAMILY_TEXT = dict(FIT_TABLE["family_text"])
OFTEN_TEXT = dict(FIT_TABLE["often_text"])
FIT_KINDS = tuple((k["kind"], k["name"], k["why"]) for k in FIT_TABLE["fit_kinds"])
FREQUENT = ("every-prompt", "every-tool-call", "matching-tool-calls")


def fit_of(r) -> dict:
    """{measured, kinds [(kind, name, why, places)], hooks (every one)} from slice 5's findings."""
    g4 = lambda c: fnd(r, BUILDER, c)  # noqa: E731
    g5 = lambda c: fnd(r, "02.5-capability", c)  # noqa: E731
    hooks = g4("fit.hook")
    groups = {"unused": g4("fit.unused"), "missing": g4("fit.missing"), "inherits": g4("fit.inherits"),
              "readonly": [x for x in g5("cap.limit") if x.get("status") == "contradicted"],
              "loops": g4("fit.loop"), "hooks": [h for h in hooks if h["how_often"] in FREQUENT]}
    kinds = [(k, name, why, sorted(groups[k], key=lambda f: (f.get("file") or "", f.get("line") or 0)))
             for k, name, why in FIT_KINDS if groups[k]]
    return {"measured": bool(g4("fit.checked")), "kinds": kinds, "hooks": hooks,
            "checked": (g4("fit.checked") or [None])[0]}


def hook_text(h) -> str:
    """How often a hook runs and what its output costs, in words."""
    s = f"{h['event']} runs {OFTEN_TEXT[h['how_often']]}"
    if h.get("adds_context") and h.get("bytes") is not None:
        s += f"; its output, about {tokens_of(h['bytes']):,} tokens, becomes context each time"
    elif h.get("adds_context"):
        s += "; its output becomes context (size not known)"
    elif h.get("adds_context") is None:
        s += " (whether its output becomes context is not known for this host)"
    if h.get("over_cap"):
        s += "; over the 10,000-character cap, so Claude sees a 2,000-character preview"
    return s


def tokens_of(size: int) -> int:
    return -(-size // BYTES_PER_TOKEN) if size else 0


def fit_parts(kind, f) -> tuple[str, str]:
    """One place: (where, what), in words."""
    if kind == "unused":
        return where(f), (f"{f['tool']}: " + ("pre-approved, and " if f.get("pre_approved") else "")
                          + f"nothing it reads asks for {FAMILY_TEXT[f['family']]}")
    if kind == "missing":
        return f["file"], f"asks for {FAMILY_TEXT[f['family']]} ({f['asked_at']}); {f['why']}"
    if kind == "inherits":
        fams = [FAMILY_TEXT[x] for x in f["families"]]
        return f["file"], ("its words ask for " + ", ".join(fams) if fams
                           else "its words ask for none of running commands, writing, fetching, searching, or subagents")
    if kind == "readonly":
        return where(f), "says read-only; " + ("its own tools can write" if f.get("owner_tools") else "another route beside it can write")
    if kind == "loops":
        return where(f), f.get("quote") or "a loop"
    return where(f), hook_text(f)


def fit_place(kind, f) -> str:
    return ": ".join(fit_parts(kind, f))


def brief_fit_counts(ft) -> dict:
    k = {kind: len(p) for kind, _, _, p in ft["kinds"]}
    return {x: k.get(x, 0) for x in ("unused", "missing", "inherits", "readonly", "loops", "hooks")}


def fit_lines(r, stop=None) -> list[str]:
    """full.md section 5: do the tools fit the job; every finding and every hook."""
    ft = fit_of(r)
    L = ["### Do the tools fit the job", ""]
    if not ft["measured"]:
        return L + [stop_not_measured(stop) or
                    f"Not measured: this run has no tool-fit findings (the steps \"{STEP_NAMES[BUILDER]}\" and "
                    f"\"{STEP_NAMES['02.5-capability']}\" did not run, or the run was made before they were "
                    "counted).", ""]
    c = ft["checked"]
    L += [f"Entries checked: {c['entries']} ({c['with_grants']} with a tools list, {n(c['inheriting'], 'agent')} "
          "with none). The yardstick is each entry's own words, over what it reads, against its own grants; "
          "families and hook facts are in `Library/fit.yaml`, the cues in "
          "`Library/asks.yaml`.", ""]
    for kind, name, why, places in ft["kinds"]:
        L += [f"{name} ({len(places)}): {why}.", ""] + [f"- {fit_place(kind, f)}" for f in places] + [""]
    if not ft["kinds"]:
        L += ["Every tool granted is one the words ask for, and nothing asks for a tool it lacks.", ""]
    others = [h for h in ft["hooks"] if h["how_often"] not in FREQUENT]
    if others:
        L += [f"Other hooks ({len(others)}):", ""] + [f"- {fit_place('hooks', h)}" for h in others] + [""]
    return L


# ---------------------------------------------------------------- is it current and clean (slice 6)

# The kinds of unfinished or dated text and their words: Library/clean.yaml (`clean_kinds`).
CLEAN_KINDS = tuple((k["kind"], k["name"], k["why"]) for k in CLEAN_TABLE["clean_kinds"])
UNFINISHED_WORD = {"todo": "a TODO or FIXME marker", "placeholder": "a placeholder", "draft": "a draft note"}
WHERE_WORD = {"frontmatter": "frontmatter", "code": "code", "text": "text"}


def clean_of(r) -> dict:
    """{measured, kinds [(kind, name, why, places)], distinct models} from slice 6's findings."""
    g = lambda c: fnd(r, BUILDER, c)  # noqa: E731
    groups = {"unfinished": g("clean.unfinished"), "dated": g("clean.dated"), "models": g("clean.model"),
              "older": g("clean.older")}
    kinds = [(k, name, why, sorted(groups[k], key=lambda f: (f.get("file") or "", f.get("line") or 0)))
             for k, name, why in CLEAN_KINDS if groups[k]]
    return {"measured": bool(g("clean.checked")), "kinds": kinds,
            "models": sorted({f["model"].lower() for f in groups["models"]})}


def clean_parts(kind, f, quote=False) -> tuple[str, str]:
    """One place: (where, what); `quote` adds the line (details and full.md, never the summary)."""
    if kind == "unfinished":
        return where(f), UNFINISHED_WORD[f["kind"]] + (f": {f['quote']}" if quote else "")
    if kind == "dated":
        return where(f), f["quote"] if quote else "a claim tied to a date"
    if kind == "models":
        return where(f), f"{f['model']} (in {WHERE_WORD[f['where']]})"
    return where(f), f"{f['tool']} (the current name is {f['now']})"


def clean_place(kind, f, quote=False) -> str:
    return ": ".join(clean_parts(kind, f, quote))


def clean_count(kind, places, models=()) -> str:
    """A row's count: the models row adds how many distinct IDs."""
    s = f"{len(places):,}"
    return s + (f" ({len(models)} distinct)" if kind == "models" and len(models) != len(places) else "")


def clean_lines(r, stop=None) -> list[str]:
    """full.md section 4: current and clean; every finding with its line."""
    cl = clean_of(r)
    L = ["### Current and clean", ""]
    if not cl["measured"]:
        return L + [stop_not_measured(stop) or f"Not measured: this run has no current-and-clean findings (the "
                    f"{step(BUILDER)} did not run, or the run was made before they were counted).", ""]
    L += ["Facts with locations: Walkdown never says a date is past, a model retired, or a TODO matters. The "
          "patterns are in `Library/clean.yaml` (dated, with sources).", ""]
    for kind, name, why, places in cl["kinds"]:
        L += [f"{name} ({clean_count(kind, places, cl['models'])}): {why}.", ""]
        L += [f"- {clean_place(kind, f, quote=True)}" for f in places] + [""]
    if not cl["kinds"]:
        L += ["No unfinished text, dated claims, pinned model IDs, or older tool names.", ""]
    return L


def phrase_hits(r):
    return [h for h in fnd(r, "02.4-phrases") if h["check"].startswith("phrase.")]


def point_hits(r) -> list[tuple[dict, list[str]]]:
    """The `02.4-phrases` hits that are places, in `02.4-phrases`'s order, each with the patterns that make it
    one (specs/report.SPEC.md, render): POINT_PATTERNS or SEND_SHAPE, or a credential hit on a line that
    also sends and holds no sending place already. Human-facing and test-data hits never are."""
    hits = [h for h in phrase_hits(r) if h.get("audience") not in ("human", "test-data")]
    at = lambda h: (h.get("file"), h.get("line"), h.get("page"))  # noqa: E731
    marked = POINT_PATTERNS | SEND_SHAPE
    sends = {at(h) for h in hits if h["check"] == "phrase.K.exfil"}
    sent = {at(h) for h in hits if h["check"] == "phrase.K.exfil" and marked & set(h.get("patterns", []))}
    out = []
    for h in hits:
        pats = sorted(marked & set(h.get("patterns", [])))
        if not pats and h["check"] == "phrase.creds" and at(h) in sends and at(h) not in sent:
            pats = sorted(p for p in h.get("patterns", []) if p.startswith("creds."))
            sent.add(at(h))
        if pats:
            out.append((h, pats))
    return out


# REPORTING rule 2 (2026-10-03 review C15): the share of hits that read as something other than an
# instruction is a model's label. No stage writes one now, so section 4 says it is not measured.
BENIGN_SHARE = "benign share not measured."


AUDIENCE_GROUP = {"model": "read by a model", "subagent": "read by a model", "tool": "in scripts",
                  "human": "human-facing", "test-data": "test data"}
AUDIENCE_ORDER = ("read by a model", "in scripts", "human-facing", "test data")


def _s4(r):
    hits = phrase_hits(r)
    by = collections.Counter(h["check"] for h in hits)
    parts = [f"{g.split()[0]} {sum(by[c] for c in cs)}" for g, cs in SUBGROUPS.items()]
    # where the lines are, by audience (2026-10-03 review A5): the totals include human-facing
    # files and test data, which never reach a model on install
    aud = {}
    for h in hits:
        aud.setdefault((h.get("file"), h.get("line")), h.get("audience"))
    where = collections.Counter(AUDIENCE_GROUP.get(a, "read by a model") for a in aud.values())
    split = ", ".join(f"{where[k]} {k}" for k in AUDIENCE_ORDER if where[k])
    line = f"{' · '.join(parts)} hits on {n(len(aud), 'line')} ({split}); {BENIGN_SHARE}"
    return line + "\n" + " " * COL + part2_line(r)


def part2_line(r) -> str:
    hosts = fnd(r, "02.4-phrases", "endpoint.host")
    undoc = [h for h in hosts if not h.get("documented") and not h.get("local")]
    rub = fnd(r, "02.4-phrases", "rubric.action")
    unconf = [x for x in rub if not x.get("confirmation") and not x.get("negated_action")]
    forbid = sum(1 for x in rub if x.get("negated_action"))
    defs = fnd(r, "02.4-phrases", "term.def")
    dens = fnd(r, "02.4-phrases", "pos.density")
    reps = fnd(r, "02.4-phrases", "rep.sentence")
    tail = (f" Long files with flagged lines: {len(dens)}, "
            f"{sum(1 for d in dens if d.get('beyond_window'))} with some past the reader window. "
            f"Sentences repeated across files: {len(reps)}, "
            f"{sum(1 for x in reps if x.get('patterns'))} flagged. " + secrets_line(r))
    return (f"Hosts: {len(hosts)}, {len(undoc)} not named in the docs. Confirm-first or "
            f"prohibited actions in instruction text: {len(rub)}, {len(unconf)} with no "
            f"confirmation step, {forbid} stated as {'a prohibition' if forbid == 1 else 'prohibitions'}. "
            f"Definitions: {len(defs)}, "
            f"{n(len(fnd(r, '02.4-phrases', 'term.conflict')), 'conflict')}, "
            f"{n(len(fnd(r, '02.4-phrases', 'term.safety')), 'safety-word definition')}." + tail)


def _s5(r):
    legs = {f["leg"]: f["present"] for f in fnd(r, "02.5-capability", "cap.leg")}
    line = " · ".join(f"{LEG_NAMES[k]}: {'yes' if legs.get(k) else 'no'}" for k in LEG_NAMES)
    if legs and all(legs.values()):
        line += "\n" + " " * COL + TRIFECTA_ALL
    grants = [f["grant"] for f in fnd(r, "02.5-capability", "cap.grant")]
    line += "\n" + " " * COL + ("Install grants: " + ", ".join(grants) + "." if grants
                               else "Install grants: none.")
    for t in fnd(r, "02.5-capability", "cap.testdata"):
        aside = t.get("inventory_set_aside", 0) + t.get("phrases_set_aside", 0)
        line += ("\n" + " " * COL + f"Test data set aside: {n(aside, 'finding')} in test or fixture folders "
                 f"{'counts' if aside == 1 else 'count'} toward none of the above.")
    return line


STATUS = {"02.1-inventory": _s1, "02.2-reader": _s2, "02.3-graph": _s3, "02.4-phrases": _s4,
          "02.5-capability": _s5, "03-sweep": lambda r: _s6(r)}


# ---------------------------------------------------------------- notes on places


def prohibition_note(x, short=False) -> str:
    """Review C25: a hit or rubric row whose action the line forbids ("Never ..."). The finding
    stays; this says how it is stated, with any exception ("unless ...")."""
    if not (x.get("negated") or x.get("negated_action")):
        return ""
    carve = f"; exception: {x['carve_out']}" if x.get("carve_out") else ""
    if short:
        return f" ({carve[2:]})" if carve else ""
    word = f" ({x['negation']}{carve})" if x.get("negation") else (f" ({carve[2:]})" if carve else "")
    return f" (stated as a prohibition{word})"


def hidden_how(p) -> str:
    """How a hidden+phrase pair hides its line: rendering hides it, or the phrase matches only
    once look-alike or invisible characters are folded (2026-10-09)."""
    whys = [str(e.get("why", "")) for e in p.get("evidence", []) if e.get("stage") == "02.2-reader"]
    if any(w.startswith("hidden text") for w in whys) or not whys:
        return "hidden when rendered"
    return "disguised with look-alike or invisible characters"


def _split_audience(r, items):
    """Pairs on lines the model reads (model or subagent audience) are listed; pairs in
    scripts (tool) and human-facing files are counted. `02.4-phrases` tags audience by path."""
    aud = {(h.get("file"), h.get("line")): h.get("audience") for h in phrases_findings(r)}
    listed = [p for p in items
              if aud.get((p["file"], p["line"])) not in ("human", "tool", "test-data")]
    counted = collections.Counter(aud.get((p["file"], p["line"])) for p in items
                                  if p not in listed)
    return listed, counted


def secrets_line(r) -> str:
    """Section 4's count of lines that look like committed secrets (2026-10-04)."""
    allf = [x for x in (r.get("02.4-phrases") or {}).get("findings", []) if x.get("check") == "secret.found"]
    if any("skipped" in x and x.get("file") is None for x in allf):
        return "Secret scan: skipped (no scanner installed)."
    unscanned = sum(1 for x in allf if "skipped" in x)  # one file each: the rest of the scan stands
    left_out = len((r.get("02.4-phrases") or {}).get("secret_left_out") or [])  # a run saved before the list has none
    allf = [x for x in allf if "skipped" not in x]
    test = sum(1 for x in allf if x.get("audience") == "test-data")
    plain = sum(1 for x in allf if x.get("likely_not_secret") and x.get("audience") != "test-data")
    engine = allf[0].get("engine") if allf else None
    extra = [f"{test} in test data"] if test else []
    if plain:
        extra.insert(0, f"{plain} that look like hashes, variable names, plain words, or local "
                        "test passwords")
    return (f"Lines that look like committed secrets: {len(allf) - test - plain}"
            + (f" (plus {'; plus '.join(extra)})" if extra else "")
            + (f", by {engine}." if engine else ".")
            + (f" The secret scan could not scan {n(unscanned, 'file')}." if unscanned else "")
            + (f" The secret scan left out {n(left_out, 'lock file')}." if left_out else ""))


def _soft(r):
    """Section 6's pieces, from the AI stages that ran (Sweep and Pinpoint): the sweep passages,
    the skips, and the backends."""
    f = ai_fnd(r)
    live = [x for x in f if "skipped" not in x]
    return {"sweep": [x for x in live if x["check"] == "soft.sweep"],
            "skips": [x for x in f if "skipped" in x],
            "backends": ai_backends(r)}


# Soft D2 sweep: what each kind tells the reader to do, in plain words.
SWEEP_PLAIN = {
    "override": "set aside its other instructions",
    "send-out": "send data out",
    "secrets": "gather secrets or private files",
    "skip-user": "act without asking the user, or keep something from them",
    "remote-instructions": "fetch outside text and follow it",
    "persist": "make lasting changes outside the task",
}


def span(x) -> str:
    e = x.get("end_line")
    return f"{x['file']}:{x['line']}" + (f"-{e}" if e and e != x["line"] else "")


# Sweep band (2026-10-01): `03-sweep` flags at p_any > 0.5. Repeat sweeps of the same passage
# moved p_any by up to 0.10 (95% within 0.07 where p_any >= 0.3; soft/EVAL.md), and the three
# passages that crossed 0.5 between runs sat within 0.03 of it. So the report lists a passage
# at p_any >= 0.6 and calls 0.4 to 0.6 near the line, flagged or not.
SWEEP_CUTOFF = 0.5
SWEEP_DRIFT = 0.1
SWEEP_CLEAR_P = round(SWEEP_CUTOFF + SWEEP_DRIFT, 2)
SWEEP_NEAR_P = round(SWEEP_CUTOFF - SWEEP_DRIFT, 2)


def sweep_kind(x) -> str:
    """The kind to name: the chosen one, or for a passage whose top answer is `none`, the
    likeliest listed kind."""
    if x.get("kind") and x["kind"] != "none":
        return x["kind"]
    others = {k: v for k, v in (x.get("probabilities") or {}).items() if k != "none"}
    return max(others, key=others.get) if others else "none"


def sweep_split(s):
    """Sweep passages by the band, strongest first: (clear with no `02.4-phrases` hit inside, clear
    and already covered by `02.4-phrases`, near the line). A read that gives no probability (a model that takes text; M1)
    has no band to put a passage in: the passages it flagged are listed with the clear ones, after any that have a number,
    in the order they came, and the ones it did not flag are in none."""
    ranked = sorted((x for x in s["sweep"] if probability.of(x) is not None), key=lambda x: -probability.of(x))
    clear = [x for x in ranked if probability.of(x) >= SWEEP_CLEAR_P]
    clear += [x for x in s["sweep"] if probability.of(x) is None and x.get("flagged")]
    near = [x for x in ranked if SWEEP_NEAR_P <= probability.of(x) < SWEEP_CLEAR_P]
    return ([x for x in clear if not x.get("covered")], [x for x in clear if x.get("covered")], near)


def sweep_gives_no_probability(s) -> bool:
    """Whether the backend that read for Sweep gives no probability, from the backend (`probability.gives`) and not from the rows: a text
    model that got no answer for any passage has no rows to look at, and its status line must not name a band it has no part in."""
    return any(b.get("role") == "sweep" and probability.gives(b.get("backend")) is False for b in s["backends"])


def _s6(r) -> str:
    """Section 6's status line: each AI backend that ran and, for Sweep, what it found. With no
    backend (no AI stage ran) the one line that says no model read was chosen."""
    s = _soft(r)
    if not s["backends"]:
        return NO_MODEL_READ
    line = ""
    for b in s["backends"]:
        where = "remote" if b.get("remote") else "local"
        line += f" {b['role'].capitalize()}: {flat(b['backend'], MODEL_CAP)} ({where}, {flat(b.get('model'), MODEL_CAP)})"
        if b["role"] == "sweep":
            new, old, near_sw = sweep_split(s)
            none = sum(1 for x in new + old if probability.of(x) is None)  # flagged by a read that gave no number
            if sweep_gives_no_probability(s) or (none == len(new) + len(old) and not near_sw
                                                 and any(probability.of(x) is None for x in s["sweep"])):
                line += (f": {n(len(s['sweep']), 'passage')} read, {len(new) + len(old)} flagged ({len(new)} with no phrase pattern hit); "
                         f"{probability.NONE}")
            else:
                line += (f": {n(len(s['sweep']), 'passage')} read, {len(new) + len(old) - none} flagged at "
                         f"p >= {SWEEP_CLEAR_P} ({sum(1 for x in new if probability.of(x) is not None)} with no phrase pattern hit), "
                         f"{len(near_sw)} near the line"
                         + (f", and {n(none, 'passage')} flagged with no probability" if none else ""))
        line += "."
    return line.strip() + " Answers are located observations; they reach no verdict."


SWEEP_WORD, PINPOINT_WORD = "Sweep", "Pinpoint"  # the model reads as the token line names them


def tokens_line(reports, stamps) -> str | None:
    """What the model reads used, in the token line of the brief and section 6: each read that ran, with its tokens as the
    backend reported them (`usage.words`), then the fixture check of Sweep when it spent some in this run. A read that does not
    report its tokens says `not reported`; a read that sent nothing says so. A fixture check reused from an earlier run spent
    none, and says none (its stamp carries no usage). None when no model read ran."""
    parts = []
    for stage, word in zip(AI_STAGES, (SWEEP_WORD, PINPOINT_WORD)):
        report = reports.get(stage)
        if report is not None:
            parts.append(f"{word} {usage.words(report.get('usage'))}")
    spent = (stamps.get(AI_SECTION) or Stamp("")).usage
    if parts and spent and spent.get("calls"):
        parts.append(f"{SWEEP_WORD}'s fixture check {usage.words(spent)}")
    return f"Model reads used: {'; '.join(parts)}." if parts else None


def run_hash(r):
    pin = [f for f in fnd(r, "02.1-inventory", "inv.pin")]
    return pin[0].get("hash") if pin else None


def rates_note(r, patterns) -> str:
    """Each pattern with its measured base rate over the other audited repos (soft D1):
    'L.ignore, rare: in 0 of 3 other audited repos'. A pattern without a table is just named."""
    out = []
    for p in patterns:
        ph = rates.phrase(rates.rate(BASE, p, run_hash(r)))
        out.append(f"{p}, {ph}" if ph else p)
    return "; ".join(out)


def _f6(r):
    s = _soft(r)
    L = ["What a pattern cannot settle, as read by the backends named here. "
         "Every answer is a located observation; none changes a finding in sections 1 to 5.", ""]
    L += [f"- {flat(b['role'])}: {flat(b['backend'], MODEL_CAP)} ({'remote' if b.get('remote') else 'local'}, "
          f"{flat(b.get('model'), MODEL_CAP)})" for b in s["backends"]]
    if s["sweep"]:
        new, old, near_sw = sweep_split(s)
        gives_none = sweep_gives_no_probability(s) or all(probability.of(x) is None for x in s["sweep"])
        listed = (f"Listed when the model names a kind other than none. {probability.NONE.capitalize()}, so there is no "
                  "band and nothing is near the line." if gives_none else
                  f"Listed at p >= {SWEEP_CLEAR_P}; p {SWEEP_NEAR_P} to {SWEEP_CLEAR_P} is near the line (repeat "
                  f"sweeps vary by about {SWEEP_DRIFT}).")
        L += ["", "### Sweep: passages a model read as asking for one of the listed actions", "",
              f"{n(len(s['sweep']), 'passage')} read. A located observation from a model, made to "
              f"reach text no pattern matched; it never replaces the {step('02.4-phrases')}. {listed}", ""]
        L += [f"- {span(x)}: {sweep_kind(x)} ({probability.words(x)}"
              + (", near the line" if x in near_sw else "") + "); "
              + (f"a phrase pattern already matches it ({', '.join(x['covered'])})" if x.get("covered")
                 else "no phrase pattern matched it") for x in new + old + near_sw] or ["- none flagged"]
    return L + [""]


IMAGE_READ = {  # what `02.2-reader` got of a pointed-at image's text, in plain words
    "unread": "this run could not read its text (no OCR), so open it and look",
    "ocr-text": "OCR found text in it (section 2), so read what the model would",
    "ocr-empty": "OCR found no text, but small or low-contrast text a model can read may still be there",
    "svg": "its text was read from the SVG source (section 2)",
}


def image_note(x) -> str:
    return (f"Referenced from {', '.join(x.get('froms') or [x.get('from')])}, which the model reads. "
            f"A model with vision reads text in an image; {IMAGE_READ.get(x.get('read'), x.get('read'))}.")


def _bytes(i) -> str:
    if i.get("bytes") is None:
        return "bytes unknown"
    return f"{i['bytes']:,} bytes, {i.get('basis')}"


def load_bytes_line(reports) -> str:
    """`02.5-capability` gives one total per hook config (host); configs are never summed."""
    inj = fnd(reports, "02.5-capability", "cap.injection")
    desc = [i for i in inj if i.get("mechanism") == "description"]
    d = sum(i.get("bytes") or 0 for i in desc)
    per = fnd(reports, "02.5-capability", "cap.load-bytes")
    hosts = [f"{x['file']} {_bytes(x)}" for x in per if x.get("file")]
    line = f"Bytes at load: descriptions {d:,} ({len(desc)}, exact)"
    if hosts:
        line += "; with each host's SessionStart hook: " + "; ".join(hosts)
    return line + "."


# ---------------------------------------------------------------- recommendations

ALLOW_EDIT = re.compile(r"permissions\.allow|allowedTools|settings(\.local)?\.json", re.I)


def recommendations(reports) -> list[str]:
    """Fixed templates only; conditional; each names a narrower alternative; stage then document order.
    One recommendation per file and template: a block of matching lines is one change."""
    out, done = [], set()
    for h in sorted(fnd(reports, "02.1-inventory", "struct.hooks"), key=lambda x: x["file"]):
        if str(h.get("event", "")).lower() == "sessionstart":
            out.append(f"{h['file']}: If the SessionStart context does not need to be computed at "
                       "run time, ship it as a static file the hook reads, so the shell step can "
                       "be removed.")
    for f in fnd(reports, "02.4-phrases"):
        pats = set(f.get("patterns", []))
        if f["check"] == "phrase.remote-load" and "RL.fetch-follow" in pats:
            out.append(f"{loc(f)}: If the instructions this line fetches do not need to change "
                       "after release, inline them or pin a commit SHA instead of a branch, so "
                       "they are part of what a reviewer reads.")
        if ("E.perm-flags" in pats and f.get("audience") in ("model", "tool")
                and not f["file"].startswith("tests/")):
            if ALLOW_EDIT.search(f.get("quote", "")):
                key = (f["file"], "allow-edit")
                if key not in done:
                    done.add(key)
                    out.append(f"{loc(f)}: If these tools do not need to run without a prompt in "
                               "every project, leave the user's permission settings unchanged and "
                               "document the entries for the user to add, or ask before writing "
                               "them.")
            elif (f["file"], "skip") not in done:
                done.add((f["file"], "skip"))
                out.append(f"{loc(f)}: If this run does not need every permission, grant the "
                           "specific tools it uses (an allowlist) instead of skipping permission "
                           "checks.")
    for p in pairs(reports, "hook+phrase"):
        out.append(f"{loc(p)}: If this message is meant for the user, write it to "
                   "the terminal (stderr) or the README instead of the hook output that becomes "
                   "the model's context.")
    for p in fnd(reports, "02.5-capability", "cap.posture"):
        if "all" in (p.get("posture") or []):
            out.append(f"{loc(p)}: If this agent does not need every tool, list the ones it "
                       "uses in a `tools:` field; it inherits all of them now.")
    return out


# ---------------------------------------------------------------- a model read whose calls got no answer (M9, slice A)

# Why a chosen AI step was not started (the record's `not_started`, `pipeline.SWEEP_NO_ANSWER`).
NOT_STARTED_WHY = {"sweep-no-answer": 'the step "{cause}" got no answer for any passage, so there was nothing to pinpoint'}
NOT_STARTED_LINE = 'The step "{plain}" did not run: {why}.'
MODEL_READ_DOWN = "the model read did not work"


def no_answer_phrase(asked: int, none: int, calls: dict | None) -> str:
    """`N of M passages got no answer, after one retry`: the retry is said only for passages that were sent. When none
    of them was (no key, the package or the program missing, a rejected key), nothing was tried again, and it says so;
    a run made before the retry (no `calls` block) says neither."""
    said = f"{none} of {asked} {'passage' if asked == 1 else 'passages'} got no answer"
    if calls is None:
        return said
    unsent = calls.get("not_sent") or 0
    if unsent >= none:
        return said + "; none was sent"
    return said + ", after one retry" + (f"; {unsent} of them {'was' if unsent == 1 else 'were'} not sent" if unsent else "")


def model_read_line(f: dict, full: bool = False) -> str:
    """One model read with passages that got no answer, from the check's finding for it (`model-no-answer` or
    `model-partial`): `Needs a human read: 5 of 12 passages got no answer, after one retry.` `full` (section 7 and the
    details page): the reasons counted, by kind of failure, and the call log named."""
    line = f"{STEP_NAMES[f['step']]}: {no_answer_phrase(f['asked'], f['none'], f.get('calls'))}."
    if full:
        line += " Reasons: " + "; ".join(f"{r} ({c})" for r, c in f.get("reasons") or []) + "."
        if (f.get("calls") or {}).get("log"):
            line += f" The call log is data/{f['calls']['log']}."
    return line


def model_read_lines(qa, full: bool = False, exclude=()) -> list[str]:
    """One line for each model read that has passages with no answer (the check of the run's `model-no-answer` and
    `model-partial` findings). `exclude`: steps left out (the summary leaves out a read that got no answer for any passage,
    which its headline and its warning already say)."""
    return [model_read_line(f, full) for f in qa.of("model-no-answer", "model-partial") if f["step"] not in exclude]


def model_read_nothing(qa) -> list[str]:
    """The AI steps that ran and asked about passages, none of which got an answer: a step that did not work."""
    return qa.reads_with_no_answer()


def not_started_lines(qa) -> list[str]:
    """One line for each chosen AI step the check says was not started."""
    return [NOT_STARTED_LINE.format(plain=STEP_NAMES[f["step"]], why=NOT_STARTED_WHY[f["why"]].format(
        cause=STEP_NAMES[AI_SECTION])) for f in qa.of("not-started")]


# ---------------------------------------------------------------- limits (the report stage's own section)

def not_run_stopped(stage: str, after: str) -> str:
    """The limit for a coded step a stop left out. No step failed; the line says why it did not run."""
    return f'{STEP_NAMES[stage]}: not run, the run stopped after "{STEP_NAMES[after]}" (--until).'


def check_names(checks) -> str:
    """Check ids in a line: `a`, `a and b`, `a, b and c`, or `a, b and 12 more`."""
    c = list(checks)
    if len(c) <= 3:
        return c[0] if len(c) == 1 else ", ".join(c[:-1]) + " and " + c[-1]
    return f"{c[0]}, {c[1]} and {len(c) - 2} more"


def checked_line(f: dict) -> str:
    """A check that found nothing, with what it looked at (M9 slice C), as `full.md` says it under "Checks that found
    nothing": `What the text asks for: phrase.remote-load and phrase.creds checked 85 files, found none.` The items a skip
    explained are said to be skipped, as listed above (the limits come first); a check with nothing to look at says so."""
    plain, what = STEP_NAMES[f["step"]], check_names(f["checks"])
    if f["of"] == 0:
        return f"{plain}: {what} had nothing to look at."
    said = f"checked {common_lines.unit_words(f['looked_at'], f['unit'])}"
    if f["explained"]:
        said += f", with {f['explained']} more skipped (listed above)"
    return f"{plain}: {what} {said}, found none."


def check_count(n: int) -> str:
    """`1 check`, `5 checks`."""
    return f"{n} {'check' if n == 1 else 'checks'}"


def counts_said(parts: list) -> str:
    """The counts of one step's line in `details.html`. One: `66 files with 2 checks`. Two, each with the word:
    `66 files with 2 checks and 41 files with 1 check`. Three or more, the word on the first only: `4 files with 1 check,
    58 files with 4 and 51 files with 3`. `parts`: [(items, unit, checks)]."""
    def one(item, word):
        n, unit, k = item
        return f"{common_lines.unit_words(n, unit)} with {check_count(k) if word else k}"
    if len(parts) <= 2:
        return " and ".join(one(p, True) for p in parts)
    items = [one(parts[0], True)] + [one(p, False) for p in parts[1:]]
    return ", ".join(items[:-1]) + " and " + items[-1]


def checked_steps(qa) -> list[tuple[str, int]]:
    """The checks that found nothing, one line for each step, as `details.html` says them: no check id, counts only.
    `[(line, checks)]` in the order the steps first appear. Within a step, lines with the same count and unit merge and their
    checks add up, in the order of first appearance; the checks with nothing to look at follow as a sentence of their own; and
    when any line of the step skipped files, `Some were skipped (listed above).` follows, with no number, since the lines of one
    step can skip the same files:

        What the text asks for: checked 64 files with 9 checks and 20 entries with 1 check, found none. Some were skipped (listed above)."""
    steps: dict[str, dict] = {}
    for f in qa.checked:
        st = steps.setdefault(f["step"], {"parts": {}, "nothing": 0, "skipped": False, "checks": 0})
        n = len(f["checks"])
        st["checks"] += n
        if f["of"] == 0:
            st["nothing"] += n
            continue
        key = (f["looked_at"], f["unit"])
        st["parts"][key] = st["parts"].get(key, 0) + n
        st["skipped"] = st["skipped"] or bool(f["explained"])
    out = []
    for stage, st in steps.items():
        said = []
        if st["parts"]:
            said.append(f"checked {counts_said([(n, unit, k) for (n, unit), k in st['parts'].items()])}, found none.")
        if st["nothing"]:
            said.append(f"{check_count(st['nothing'])} had nothing to look at.")
        if st["skipped"]:
            said.append("Some were skipped (listed above).")
        out.append((f"{STEP_NAMES[stage]}: " + " ".join(said), st["checks"]))
    return out


def checked_lines(qa) -> list[str]:
    """The lines of "Checks that found nothing" in `full.md`: one for each pass, with the check ids, in the check's order.
    None when no step has one."""
    return [checked_line(f) for f in qa.checked]


def limit_line(f: dict) -> str:
    """One finding of the check of the run as a line of section 7 (`data/limits.md`), by its kind. A kind this does not
    know (a later check's) says what it expected and what it found."""
    kind, stage = f["kind"], f.get("step")
    if kind == "stopped":
        return not_run_stopped(stage, f["after"])
    if kind == "step-missing":
        return (f"The {step(stage)} did not run to completion; "
                + ("its section is not a result." if stage in HEADINGS or stage in AI_STAGES
                   else "the checks it makes are not a result."))
    if kind in ("fixture-failed", "fixture-incomplete"):
        return (f"The {step(stage)} validation {Stamp.from_dict(f['stamp']).text}: its zeros are not validated "
                "for the skipped checks.")
    if kind == "fixture-unchecked":
        return f"The {step(stage)} {common_lines.unchecked_phrase(f['result'])}."
    if kind in ("model-no-answer", "model-partial"):
        return model_read_line(f, full=True)
    if kind == "not-started":
        return NOT_STARTED_LINE.format(plain=STEP_NAMES[stage], why=NOT_STARTED_WHY[f["why"]].format(
            cause=STEP_NAMES[AI_SECTION]))
    if kind == "read-dropped":
        return dropped_line(stage, f.get("backends"), f.get("stopped"))
    if kind == "skip":  # a file name and a reason can come from the repository: each is one line (`flat`)
        return f"{f['step_check']} skipped for {flat(f['file'])}: {flat(f['reason'])}"
    if kind == "note":
        return f"({step(stage)}) {flat(f['text'])}"
    if kind == "unread":
        return f"Unread: {flat(f['file'])}: {flat(f['reason'])}"
    if kind == "unscanned":
        return f"Not scanned for references: {flat(f['file'])}: {flat(f['reason'])}"
    if kind == "testdata":
        return (f"Test data is recognized by folder and file name (tests, fixtures, test_*.py "
                f"and the like): {n(f['inventory_set_aside'], 'finding')} from the "
                f"{step('02.1-inventory')} and {n(f['phrases_set_aside'], 'finding')} from the "
                f"{step('02.4-phrases')} were kept out of the capability map and the summary. "
                "Test data that a model-read file references directly is listed in section 5.")
    if kind == "standing":
        return STANDING_LIMITS[f["id"]]
    if kind in common_lines.COVERAGE_KINDS:  # what a check looked at (M9 slice C): the words the hold's brief uses
        return common_lines.coverage_gap_text(f)
    where = f" ({f['step_check']})" if f.get("step_check") else ""
    return f"The {step(stage)}{where}: expected {f.get('expected')}; found {f.get('found')}."


def limits(qa) -> list[str]:
    """Section 7: every gap and limit the check of the run found, as lines, in its order (it gathers them: M9 slice B,
    owner restructure O2). A step that did not work, a skip a step named, a model read with passages that got no answer, a
    step a stop left out, and the limits that stand for every run are all here."""
    return [limit_line(f) for f in qa.items]


# details.html's count of what was not examined (owner 2026-10-07: 58 lines read as a hole).
# Only checks this run skipped that apply to this repository, one item each. Standing limits of
# the method, one-line-per-file repeats, and tools for file types the repository does not ship
# are left to the full list (section 7, data/limits.md), which keeps every line.
IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "bmp", "tif", "tiff", "ico"}
HTML_EXTS = {"html", "htm", "xhtml"}
# (`02.2-reader` note start, what it covers, file kinds it serves (None = all text), why it was not
# done). A check with no code is "not built yet", apart from one waiting on a missing tool
# (2026-10-12, an outside audit: these three once read "<tool> not installed", though no code
# used the tools).
TOOL_NOTES = [
    ("tesseract", "Text inside images (OCR)", ("image",), "Tesseract not installed"),
    ("tesseract", "PDF pages drawn and read (OCR)", ("pdf",), "Tesseract not installed"),
    # the program installed without its Python package (fresh-install test, 2026-10-21)
    ("pytesseract", "Text inside images (OCR)", ("image",), "pytesseract not installed"),
    ("pytesseract", "PDF pages drawn and read (OCR)", ("pdf",), "pytesseract not installed"),
    ("not built: PDF render", "PDF pages drawn and read as images", ("pdf",), "not built yet"),
    ("html render:", "HTML as a browser draws it", ("html",), "Playwright not installed"),  # since 2026-10-20
    ("not built: HTML render", "HTML as a browser draws it", ("html",), "not built yet"),
    ("not built: language detection", "Language detection in Latin-script text", None, "not built yet"),
    # the same three as runs before 2026-10-12 noted them
    ("poppler", "PDF pages drawn and read as images", ("pdf",), "not built yet"),
    ("playwright", "HTML as a browser draws it", ("html",), "not built yet"),
    ("lingua", "Language detection in Latin-script text", None, "not built yet"),
]
BINARY_NOTE = "limit: files that do not decode as text"
# `02.4-phrases`'s note that those files are scanned from the reader step's extracted text. Runs made
# before restructure step 8b word it "scanned from stage 2's extracted text".
EXTRACTED_NOTE = re.compile(r"scanned from (?:stage 2's extracted text|the text extracted by)")
PER_FILE_NOTE = re.compile(r"^not scanned: (.+?): (.+)$")  # one file's skip line
# `stage 5 limit` is how a run made before restructure step 8b worded the two limits that now begin
# `standing limit` (Library/capability.yaml).
STANDING_NOTE = re.compile(r"^(v1 limit|standing limit|stage 5 limit|graph incomplete by construction"
                           r"|not scanned: .*\(not instruction text\))")


def file_kinds(reports) -> set[str]:
    """The kinds of file `02.1-inventory` saw that need an optional tool: image, pdf, html, docx."""
    kinds = set()
    for f in fnd(reports, "02.1-inventory", "inv.file"):
        ext, typ = (f.get("ext") or "").lower(), f.get("type") or ""
        if ext in IMAGE_EXTS or typ.startswith("image/"):
            kinds.add("image")
        if ext == "pdf" or typ == "application/pdf":
            kinds.add("pdf")
        if ext in HTML_EXTS or typ == "text/html":
            kinds.add("html")
        if ext == "docx":
            kinds.add("docx")
    return kinds


def tool_items(reports, notes) -> tuple[list[tuple[str, str]], list[str]]:
    """`02.2-reader`'s notes on optional tools: ([(what, why)] for a missing tool whose file kind this
    repository has, [what] for one it has no use for). Read by `glance` for details.html's Other
    details (owner, 2026-10-25: a missing optional tool is never named on summary.html)."""
    kinds = file_kinds(reports)
    applies, unused = [], []
    for line in notes.get("02.2-reader", []):
        for start, what, serves, why in TOOL_NOTES:
            if line.startswith(start):
                if serves is None or kinds & set(serves):
                    applies.append((what, why))
                else:
                    unused.append(what)
    return applies, unused


def glance(reports, notes, qa, stop=None) -> tuple[list[str], list[str]]:
    """(skipped, not needed): plain items for details.html's What Walkdown didn't check. `skipped` is what this run
    could not look at in this repository; `not needed` names tools the repository has no use for. A step the
    run's `stop` left out, and a model read it held back, are not skipped checks: `stopped_steps_line` and
    `stop_input_line` say them in a line of their own (O3). A model read's passages that got no answer, and a chosen step
    that was not started, are not skipped checks either: the page gives each its own line (`model_read_lines`,
    `not_started_lines`; M9). The steps that did not run are the check of the run's (`qa`)."""
    skipped, idle = [], []
    missing = qa.steps_missing()
    for stage in NAMED:
        if stage in missing:
            skipped.append(f"{STEP_NAMES[stage]}: did not run to completion")
    kinds = file_kinds(reports)
    soft = [f for f in ai_fnd(reports) if "skipped" in f]
    failed = [s for s in AI_STAGES if s in missing]  # started, and left no output
    if not ai_backends(reports) and not failed:
        if not (stop or {}).get("prepared"):
            skipped.append("Model reads (optional): not run")
    elif failed:
        skipped.append("Model reads (optional): did not run to completion")
    elif soft and not model_read_lines(qa):  # skips that name no passage; a passage's are counted on their own line
        skipped.append(f"Model reads (optional): {n(len(soft), 'passage')} skipped")
    applies, unused = tool_items(reports, notes)
    skipped += [f"{what}: {why}" for what, why in applies]
    idle += [f"{what}: none in this repository" for what in unused]
    for stage in ORDER[:6]:
        per_file: collections.Counter = collections.Counter()
        in_tests = 0
        for line in notes.get(stage, []):
            if stage == "02.2-reader" and any(line.startswith(t[0]) for t in TOOL_NOTES):
                continue
            if stage == AI_SECTION or not LIMIT_NOTE.search(line) or STANDING_NOTE.search(line):
                continue
            if line.startswith(BINARY_NOTE):
                if EXTRACTED_NOTE.search(line):
                    continue  # read from `02.2-reader`'s text (2026-10-18); files without one are per-file notes
                if kinds & {"image", "pdf", "docx"}:
                    skipped.append("Phrase patterns in PDF, DOCX, and image files")
                continue
            m = PER_FILE_NOTE.match(line)
            if m:  # one item per stage, not one per file (2026-10-09: 67 on one repository)
                if is_test_data(m.group(1)):
                    in_tests += 1
                else:
                    per_file[m.group(2)] += 1
                continue
            skipped.append(f"{HEADINGS[stage]}: {line}")
        if per_file:
            kinds_txt = ", ".join(f"{c} {why}" for why, c in per_file.most_common())
            skipped.append(f"{HEADINGS[stage]}: {n(sum(per_file.values()), 'file')} not scanned "
                           f"({kinds_txt})" + (f", plus {in_tests} in test data" if in_tests else ""))
        elif in_tests:
            idle.append(f"{HEADINGS[stage]}: {n(in_tests, 'file')} not scanned, all in test data")
    other = collections.Counter(
        f["skipped"] for stage in ORDER[:5] for f in fnd(reports, stage)
        if "skipped" in f and "tesseract" not in str(f["skipped"])
        and not str(f["skipped"]).startswith("html not drawn (playwright"))
    skipped += [f"{n(c, 'file')}: {why}" for why, c in other.items()]
    unread = fnd(reports, "02.2-reader", "read.unread")
    if unread:
        skipped.append(f"{n(len(unread), 'file')} could not be read")
    unscanned = fnd(reports, "02.3-graph", "graph.unscanned")
    if unscanned:
        skipped.append(f"{n(len(unscanned), 'file')} not scanned for references")
    return skipped, idle


# ---------------------------------------------------------------- documents

def ai_section(reports, stamps, notes, capability_full=None, stop=None, unstarted=(), dropped=(), backends=None) -> list[str]:
    """Section 6, the AI reads, after its heading. A run that chose neither AI stage says so in
    one line (decision 5-D); a run that did lists what the stages found, each stage's validation
    stamp, and any chosen stage that did not finish. A run that stopped just before a model read says
    what was written and that nothing was sent. `unstarted`: the chosen reads with no step
    (`chosen_without_a_step`), and `dropped`: the reads an earlier command chose and `continue` left out, each said in a
    line, so the section never says no read was chosen for a run in which one was."""
    started = ai_chosen(reports, notes)
    prep = (stop or {}).get("prepared")
    waits = ([f'The step "{STEP_NAMES[prep["stage"]]}" was chosen and the run stopped before it: '
              f"data/{layout.input_file(prep['stage'])} holds what it would send, and nothing was sent.", ""]
             if prep else [])
    for s, stopped in unstarted:
        waits += [f'The step "{STEP_NAMES[s]}" was chosen and ' + ("the run stopped before it." if stopped else
                                                                  "did not start: see LOG.md."), ""]
    for s in dropped or ():
        waits += [dropped_line(s, backends, stop is not None), ""]
    if not started:
        return waits or [NO_MODEL_READ, ""]
    L = []
    ran = [s for s in started if reports.get(s) is not None]
    if ran:
        L += [_s6(reports), ""]
        L.append("Validation: " + "; ".join(
            f"\"{STEP_NAMES[s]}\" {stamps[s].text if stamps.get(s) else 'not run'}" for s in ran))
        L.append("")
        L += [tokens_line(reports, stamps), ""]
        L += SECTIONS[AI_SECTION](reports, capability_full)
    for s in started:
        if reports.get(s) is None:
            L += [f"The {step(s)} was chosen but did not finish: see LOG.md.", ""]
    return L + waits


def full(meta, reports, stamps, notes, runs_ok, capability_full=None) -> str:
    L = [f"# {meta['repo']}: full report", "",
         f"{meta['source']} | retrieved {meta['date']} | {meta['hash_kind']} {meta['hash']}",
         f"Run {meta['run']} | Walkdown {meta.get('tool', '?')}",
         "Static examination only. Nothing executed. Every finding below is a location to "
         "look at; none is a verdict. Stage order; nothing is ranked.", ""]
    for i, stage in enumerate(ORDER, 1):
        L.append(f"## {i} {HEADINGS[stage]}")
        L.append("")
        if stage == stagelist.LIMITS:
            L += [f"- {x}" for x in limits(qaview.of(meta))] + [""]
            found_none = checked_lines(qaview.of(meta))  # M9 slice C: no limits, so after the standing ones
            if found_none:
                L += [f"### {CHECKED_HEADING}", ""] + [f"- {x}" for x in found_none] + [""]
            continue
        if stage == AI_SECTION:
            L += ai_section(reports, stamps, notes, capability_full, meta.get("stop"),
                            chosen_without_a_step(meta.get("chosen"), reports, meta.get("stop"), meta.get("not_started")),
                            meta.get("dropped"), meta.get("backends"))
            continue
        stop = meta.get("stop")  # where the run stopped as asked, or None (O3)
        L.append(status(reports, stamps, stage, stop).replace("\n" + " " * COL, " "))
        st = stamps.get(stage)
        L += ["", f"Validation: {st.text if st else 'not run'}", ""]
        if stage in reports:
            L += (_f5(reports, capability_full, meta.get("context") or DEFAULT_CONTEXT)
                  if stage == "02.5-capability" else _f1(reports, capability_full, stop)
                  if stage == "02.1-inventory" else SECTIONS[stage](reports, capability_full))
        if stage == "02.5-capability":  # slice 5, 2026-10-26
            L += fit_lines(reports, stop)
        if stage == "02.4-phrases":  # slices 4 and 3, 2026-10-26
            L += trigger_lines(reports, meta.get("context") or DEFAULT_CONTEXT, stop)
            L += ready_lines(reports, meta.get("hosts") or [], stop)
            L += clean_lines(reports, stop)  # slice 6, 2026-10-27
    recs = recommendations(reports)
    L += ["## Recommendations", "",
          "Conditional on what the skill is for. Unranked, in stage order."
          + ("" if recs else " None: no finding matched a recommendation template."), ""]
    L += [f"- {x}" for x in recs] + ["", NOT_WHAT, ""]
    return "\n".join(one_line(x) for x in L)


def _list(title, rows, fmt):
    if not rows:
        return [f"### {title} (0)", "", "None.", ""]
    return [f"### {title} ({len(rows)})", ""] + [f"- {fmt(x)}" for x in rows] + [""]


def _f1(r, _, stop=None):
    pin = pin_of(r)
    ext = ", ".join(f"{k or '(none)'} {v}" for k, v in sorted((pin.get("extensions") or {}).items(),
                                                             key=lambda kv: (-kv[1], kv[0])))
    langs = "; ".join(f"{k}: {', '.join(v)}" for k, v in sorted((pin.get("script_languages") or {}).items()))
    L = [f"Pin: {pin.get('hash_kind')} {pin.get('hash')}, {n(pin.get('files', 0), 'file')}, "
         f"{pin.get('bytes') or 0:,} bytes.", "", f"Formats: {ext}.", "", f"Script languages: {langs or 'none'}.", ""]
    ep = [f for f in fnd(r, "02.1-inventory", "inv.file") if f.get("entry_point")]
    L += _list("Entry points", ep, lambda f: f"{f['file']} ({f['entry_point']})")
    L += _list("Structural census", fnd(r, "02.1-inventory", "struct.census"),
               lambda f: f"{loc(f)}: {f.get('flag')}: {f.get('detail')}")
    L += _list("Descriptions (always-on text)", fnd(r, "02.1-inventory", "struct.description"),
               lambda f: f"{loc(f)}: {code(f.get('text'))}")
    L += _list("Agent and command tool grants", fnd(r, "02.1-inventory", "struct.agent-tools"),
               lambda f: f"{loc(f)}: tools {f.get('tools') if f.get('tools') is not None else '(none listed: inherits all; ' + CAPABILITY_ONLY_SHORT + ')'}; "
                         f"job {code(f.get('description'))}")
    L += _list("Hooks", fnd(r, "02.1-inventory", "struct.hooks"),
               lambda f: f"{hook_where(f)}: event {f.get('event')}, matcher {f.get('matcher')}, "
                         f"command {code(f.get('command'))}")
    L += _list("Platform manifests", fnd(r, "02.1-inventory", "struct.manifests"),
               lambda f: f"{f.get('name')}: {', '.join(f.get('files', []))}; "
                         f"declared permissions differ: {'yes' if f.get('divergent') else 'no'}")
    if pin.get("license_checked"):
        L += _list("Licenses (license files and declared license fields)", fnd(r, "02.1-inventory", "inv.license"),
                   lambda f: f"{loc(f)}: {f.get('license') or 'not recognized'}; "
                             + (f"declared in {f.get('field')}" if f.get("source") == "field"
                                else f"license file, matched by {f['how']}" if f.get("how") else "license file")
                             + (f"; says {code(f.get('stated'))}"
                                if f.get("stated") and f.get("stated") != f.get("license") else ""))
    return L + [""] + needs_lines(r, stop)  # slice 2, 2026-10-26


def _f2(r, _):
    L = _list("Divergences (reading A versus reading B)",
              [d for d in fnd(r, "02.2-reader", "read.divergence") if "skipped" not in d],
              lambda d: f"{loc(d)}: {d.get('reading')}, carrier {d.get('carrier')}"
                        + (f" ({d['how']})" if d.get("how") else "")  # how a drawn page hides it (2026-10-20)
                        + f", method {d.get('method')}: {code(d.get('text'))}"
                        + (f"; the hidden characters spell {code(d['decoded'])}"
                           if d.get("decoded") and not d.get("masked") else ""))
    L += _list("Lines changed by folding", fnd(r, "02.2-reader", "read.fold"),
               lambda d: f"{loc(d)}: removed or replaced {', '.join(d.get('removed', []))}")
    L += _list("Non-Latin script runs", fnd(r, "02.2-reader", "read.script"),
               lambda d: f"{loc(d)}: {d.get('script')} {code(d.get('text'))}")
    L += _list("Passages in a language other than English (Latin script)",
               fnd(r, "02.2-reader", "read.language"),
               lambda d: f"{loc(d)}"
                         f"{'-' + str(d['end_line']) if d.get('end_line') not in (None, d.get('line')) else ''}: "
                         f"{d.get('rule')}, {d.get('other')} other-language words to {d.get('english')} English"
                         f"{' (' + ', '.join(d['matched']) + ')' if d.get('matched') else ''}: "
                         f"{code(d.get('text', '').splitlines()[0] if d.get('text') else '')}")
    L += _list("Metadata carrying text", fnd(r, "02.2-reader", "read.metadata"),
               lambda d: f"{loc(d)}: {d.get('field')} = {code(d.get('text'))}")
    L += _list("Unread", fnd(r, "02.2-reader", "read.unread"),
               lambda d: f"{loc(d)}: {d.get('reason')}")
    return L


def _f3(r, _):
    depth = fnd(r, "02.3-graph", "graph.depth")
    hist = collections.Counter((d["via"], d["depth"]) for d in depth)
    hs = "; ".join(f"{via} depth {k}: {v}" for (via, k), v in sorted(hist.items()))
    L = [f"Depth histogram (static = reached by direct references; dynamic = only through a "
         f"load: a folder a config names, a code scan, wildcards in an instruction file; mention = only "
         f"through a folder or wildcards named elsewhere): {hs or 'none'}.", ""]
    L += _list("Entry points used", fnd(r, "02.3-graph", "graph.entry"),
               lambda f: f"{f['file']} ({f.get('kind')})")
    L += _list("Orphans (reachable from no entry point)", fnd(r, "02.3-graph", "graph.orphan"),
               lambda f: f["file"])
    L += _list("Files loaded only through a dynamic load (named by nothing)",
               [d for d in depth if d.get("via") == "dynamic"],
               lambda d: f"{d['file']} (depth {d['depth']}, from {d.get('from')})")
    L += _list("Files reached only through a mention of a folder or wildcards (not a load)",
               [d for d in depth if d.get("via") == "mention"],
               lambda d: f"{d['file']} (depth {d['depth']}, from {d.get('from')})")
    L += _list("Dynamic loads", fnd(r, "02.3-graph", "graph.dynamic"),
               lambda f: f"{loc(f)}: {f.get('source')} {code(f.get('pattern'))} "
                         f"({'load' if f.get('load') else 'mention'}) resolves to "
                         f"{n(len(f.get('resolves', [])), 'file')}")
    L += _list("On disk, left out of the manifest (a host that finds components by folder may "
               "still load them)", fnd(r, "02.3-graph", "graph.unlisted"),
               lambda f: f"{f['file']}: {f.get('kind')} not named by {f.get('manifest')}, which "
                         f"names {f.get('listed')} of the {f.get('on_disk')} on disk")
    dang = fnd(r, "02.3-graph", "graph.dangling")
    L += _list("Dangling references", [d for d in dang if not d.get("folder_missing")],
               lambda f: f"{loc(f)}: {code(f.get('target'))} ({f.get('context')})")
    L += _list("Dangling references into a folder the repository does not have (often one the "
               "workflow creates when it runs)", [d for d in dang if d.get("folder_missing")],
               lambda f: f"{loc(f)}: {code(f.get('target'))} ({f.get('context')})")
    L += _list("Not scanned for references", fnd(r, "02.3-graph", "graph.unscanned"),
               lambda f: f"{f['file']}: {f.get('reason')}")
    L += _list("Reference depth, directly reached files",
               [d for d in depth if d.get("via") == "static"],
               lambda d: f"{d['file']}: depth {d['depth']}" + (f", from {d['from']}" if d.get("from") else ""))
    return L


def _f4(r, _):
    hits = phrase_hits(r)
    L = ["Every hit is a locator. Benign share not measured here. Audience is "
         "who the file addresses, by path.", ""]
    for group, checks in SUBGROUPS.items():
        L += [f"### {group}", ""]
        for c in checks:
            rows = [h for h in hits if h["check"] == c]
            pc = collections.Counter(p for h in rows for p in h.get("patterns", []))
            L.append(f"#### {c} ({n(len(rows), 'line')})")
            L.append("")
            if pc:
                L += ["Patterns: " + ", ".join(f"{k} {v}" for k, v in sorted(pc.items())), ""]
            L += [f"- {loc(h)} [{', '.join(h.get('patterns', []))}] ({h.get('audience')}"
                  f"{', in an MCP description' if h.get('tool_text') else ''})"
                  f"{' (matched only after folding)' if h.get('folded') else ''}"
                  f"{' (decoded from base64: ' + code(h['decoded_text']) + ')' if h.get('decoded_text') else ''}"
                  f"{prohibition_note(h)}: "
                  f"{code(h['quote'].strip())}" for h in rows] or ["None."]
            L.append("")
    return L + _f4_part2(r)


def _f4_part2(r):
    L = ["### Tables", "", part2_line(r), ""]
    L += _list("Endpoints (hosts named anywhere; documented = named in the docs)",
               sorted(fnd(r, "02.4-phrases", "endpoint.host"),
                      key=lambda h: (h.get("documented"), not h.get("local"), h["host"])),
               lambda h: f"{h['host']}{lookalike_note(h)}: {'documented' if h.get('documented') else 'not in the docs'}"
                         f"{', local' if h.get('local') else ''}, {h.get('kind')}; "
                         f"{', '.join(f'{v} {k}' for k, v in (h.get('where') or {}).items() if v)}; "
                         f"first at {loc((h.get('occurrences') or [{}])[0]) if h.get('occurrences') else '?'}")
    L += _list("Confirm-first and prohibited actions in instruction text",
               fnd(r, "02.4-phrases", "rubric.action"),
               lambda x: f"{loc(x)}: {x.get('tier')}, {code(x.get('action'))}, "
                         f"{'stated as a prohibition' + prohibition_note(x, short=True) + ', ' if x.get('negated_action') else ''}"
                         f"{'confirmation at line ' + str(x['confirm_line']) if x.get('confirmation') else 'no confirmation step'}"
                         f"{' (negated: without asking)' if x.get('negated_confirmation') else ''}"
                         f"{' (the step redefines confirmation)' if x.get('confirm_redefined') else ''}: "
                         f"{code(x['quote'].strip())}")
    L += _list("Definitions", fnd(r, "02.4-phrases", "term.def"),
               lambda t: f"{loc(t)}: \"{t.get('term')}\" ({t.get('source')}): {code(t.get('definition'))}")
    L += _list("Terms defined more than one way", fnd(r, "02.4-phrases", "term.conflict"),
               lambda c: f"\"{c['term']}\": " + "; ".join(f"{d['file']}:{d['line']}"
                                                          for d in c.get("definitions", [])))
    L += _list("Safety words defined", fnd(r, "02.4-phrases", "term.safety"),
               lambda t: f"{loc(t)}: \"{t.get('term')}\"")
    L += _list("Lines that look like committed secrets (values never shown)",
               [x for x in fnd(r, "02.4-phrases", "secret.found") if x.get("file") is None or "skipped" not in x],
               lambda x: f"{loc(x)}: {', '.join(x.get('kinds') or [])} ({x.get('engine')}"
                         + (", test data" if x.get("audience") == "test-data" else "")
                         + (f"; likely not a secret: {x['likely_not_secret']}"
                            if x.get("likely_not_secret") else "") + ")")
    L += _list("Position of flagged lines in long files (first 10% / middle 80% / last 10%)",
               fnd(r, "02.4-phrases", "pos.density"),
               lambda d: f"{d['file']} ({d['lines']} lines): {d['first10']} / {d['middle80']} / "
                         f"{d['last10']}; {d['beyond_window']} past the reader window (after line "
                         f"{d['window_line']})")
    L += _list("Settings that restrict tools (a fact, never a risk)", fnd(r, "02.4-phrases", "limit.setting"),
               lambda x: f"{loc(x)}: {x.get('kind')} "
                         f"{', '.join(x['tools']) if x.get('tools') is not None else x.get('value')}"
                         f"; rules out {', '.join(x.get('rules_out') or []) or 'nothing'}"
                         f"{'; allows writing' if x.get('grants_write') else ''} ({x.get('audience')})")
    L += _list("Sentences repeated across files a model reads", fnd(r, "02.4-phrases", "rep.sentence"),
               lambda x: f"{loc(x)}: in {x['files']} files ({x['count']} times)"
                         + (f", flagged {', '.join(x['patterns'])}" if x.get("patterns") else "")
                         + f": {code(x['sentence'])}")
    return L


def _ev(f, full_by_key):
    ev = full_by_key.get(_key(f), f).get("evidence", [])
    return [f"    - stage {e.get('stage')} {e.get('check')} {loc(e)}: {e.get('why')}"
            f"{' (' + CAPABILITY_ONLY_SHORT + ')' if e.get('why') == 'tool grant: inherits all' else ''}"
            for e in ev]


def _key(f):
    return (f["check"], f.get("file"), f.get("line"), f.get("leg"), f.get("grant"), f.get("pair"),
            f.get("mechanism"), f.get("event"))


def _f5(r, capability_full, ctx=DEFAULT_CONTEXT):
    full_by_key = {_key(f): f for f in (capability_full or {}).get("findings", [])}
    derived = names([f'"{STEP_NAMES[s]}"' for s in stagelist.reads("02.5-capability")])
    L = [f"A map of capability, derived from the steps {derived}; it reaches no verdict. A Bash grant is "
         "counted as private-data "
         "access and execute posture; on its own it does not count as external communication.", "",
         "### Trifecta legs", ""]
    for f in fnd(r, "02.5-capability", "cap.leg"):
        ev = full_by_key.get(_key(f), f).get("evidence", [])
        L.append(f"- {LEG_NAMES.get(f['leg'], f['leg'])}: {'yes' if f['present'] else 'no'} "
                 f"({n(len(ev), 'citation')})")
        L += _ev(f, full_by_key)
    L += ["", "### Install grants", ""]
    grants = fnd(r, "02.5-capability", "cap.grant")
    for f in grants:
        ev = full_by_key.get(_key(f), f).get("evidence", [])
        L.append(f"- {f['grant']} ({n(len(ev), 'citation')})")
        L += _ev(f, full_by_key)
    if not grants:
        L.append("None.")
    L += ["", "### Text in context at load", "", load_bytes_line(r), ""]
    L += [f"- {loc(i)}: {i.get('mechanism')}{' ' + str(i.get('event')) if i.get('event') else ''}, "
          f"{_bytes(i)}" for i in fnd(r, "02.5-capability", "cap.injection")]
    L.append("")
    L += ["### What it costs and what ships", ""] + ship_lines(r, ctx) + [""]  # slice 1, 2026-10-26
    L += _list("Agent and command posture", fnd(r, "02.5-capability", "cap.posture"),
               lambda p: f"{loc(p)}: {', '.join(p.get('posture', []))}"
                         f"{' (least privilege)' if p.get('least_privilege') else ''}; "
                         f"job {code(p.get('description'))}")
    L += _list("Stated limits: read-only wording a model reads, and what backs it",
               fnd(r, "02.5-capability", "cap.limit"),
               lambda x: f"{loc(x)}: {x.get('status')}"
                         + (f" ({x['backed_by']})" if x.get("backed_by") else "")
                         + f"; {limit_words(x)}"
                         + (f" {limit_routes(x)}" if x.get("other_routes") else "")
                         + f" {code((x.get('quote') or '').strip())}")
    L += _list("Pairs: Test data a model-read file references directly",
               pairs(r, "testdata+loaded"),
               lambda p: f"{p['file']}: referenced from {p.get('from')}")
    L += _list("Pairs: Image a model-read file points at", pairs(r, "image+loaded"),
               lambda p: f"{p['file']}: referenced from {', '.join(p.get('froms') or [p.get('from')])}; "
                         f"text: {p.get('read')}{' (' + p['reason'] + ')' if p.get('reason') else ''}")
    for kind, title in (("orphan+phrase", "Orphan with a phrase hit"),
                        ("hidden+phrase", "Hidden text with a phrase hit"),
                        ("dynamic+phrase", "Load-only file with a phrase hit"),
                        ("hook+phrase", "Instruction in a script a context-injecting hook runs")):
        L += _list(f"Pairs: {title}", pairs(r, kind),
                   lambda p: f"{loc(p)}: {p['phrase_check']} [{', '.join(p.get('patterns', []))}]: "
                             f"{code(p['quote'].strip())}")
    return L


SECTIONS = {"02.1-inventory": _f1, "02.2-reader": _f2, "02.3-graph": _f3, "02.4-phrases": _f4,
            "02.5-capability": _f5, "03-sweep": lambda r, c: _f6(r)}


def dropped_line(stage: str, backends: dict | None = None, stopped: bool = False) -> str:
    """A model read an earlier command chose that did not run at `continue`: section 7, section 6, and the brief say it in
    these words, and say how to get it (`stopped`: the run can still go on)."""
    return common_lines.DROPPED_LINE.format(plain=STEP_NAMES[stage], how=common_lines.dropped_how(stage, backends, stopped))


def dropped_lines(qa) -> list[str]:
    """One line for each model read the check says an earlier command chose and `continue` left out."""
    return [limit_line(f) for f in qa.of("read-dropped")]


def waiting_reads(chosen, reports, stop, not_started=()) -> list[str]:
    """The model reads the run chose that a stop is before, in the list's order: the one whose input file the stop wrote (the
    record's `prepared`) and any after it. The stop's brief puts their options in the command that goes on."""
    if not stop:
        return []
    held = {x["stage"] for x in not_started or []}
    cut = stagelist.position(stop["after"])
    return [s for s in AI_STAGES if s in (chosen or ()) and s not in reports and s not in held
            and stagelist.position(s) > cut]


def chosen_without_a_step(chosen, reports, stop=None, not_started=()) -> list[tuple[str, bool]]:
    """[(model read, a stop was before it)] for the reads the run chose that have no step, in the list's order. A read that
    was started (a key of `reports`), the one a stop wrote the input file of (the record's `prepared`), and one held back
    because the read before it got no answer (`not_started`) are said where they are, and are not here. The rest were not
    started: a stop was before them (`True`), or a step before them failed (`False`)."""
    prep = ((stop or {}).get("prepared") or {}).get("stage")
    held = {x["stage"] for x in not_started or []}
    cut = stagelist.position(stop["after"]) if stop else None
    return [(s, cut is not None and stagelist.position(s) > cut) for s in AI_STAGES
            if s in (chosen or ()) and s not in reports and s != prep and s not in held]


def _soft_models(reports, stop=None, not_started=(), chosen=(), dropped=()) -> str:
    """The AI backends this run used, for the log header. A model read that was chosen is named whatever became of
    it: one that a stop held back (its input file written, nothing sent) with the step's plain name and the backend;
    one that was started and left no report ("did not finish"); one that was not started (M9: "did not run"); one that
    never started because a step before it failed, or because a stop was before it (M9 slice B, from the record's
    `chosen`); one an earlier command chose and `continue` left out (the record's `dropped`). The line says no model read
    was chosen only when none was."""
    bs = ai_backends(reports)
    prep = (stop or {}).get("prepared")
    also = ([f'"{STEP_NAMES[prep["stage"]]}" ({flat(prep["backend"], MODEL_CAP)}) was chosen and the run stopped before it sent anything']
            if prep else [])
    also += [f'"{STEP_NAMES[s]}" was chosen and did not finish' for s in AI_STAGES if s in reports and reports[s] is None]
    also += [f'"{STEP_NAMES[x["stage"]]}" was chosen and did not run' for x in not_started or []]
    also += [f'"{STEP_NAMES[s]}" was chosen and ' + ("the run stopped before it" if stopped else "did not start")
             for s, stopped in chosen_without_a_step(chosen, reports, stop, not_started)]
    also += [common_lines.DROPPED_LOG.format(plain=STEP_NAMES[s]) for s in dropped or ()]
    if not bs:
        return f"Soft models: {'; '.join(also)}" if also else "Soft models: none (no model read was chosen)"
    return "Soft models: " + "; ".join(
        [f"{flat(b['role'])} {flat(b['backend'], MODEL_CAP)} ({'remote' if b.get('remote') else 'local'}, "
         f"{flat(b.get('model'), MODEL_CAP)})" for b in bs] + also)


def log(meta, runs, stamps, reports) -> str:
    L = [f"# {meta['repo']} run {meta['run']}", "",
         f"Source: {meta['source']} | channel: {meta.get('channel', 'directory')} | "
         f"pinned: {meta['hash_kind']} {meta['hash']}",
         f"Walkdown: {meta.get('tool', '?')} | optional deps: {meta.get('deps', 'see data/limits.md')}",
         f"Expected context: {meta.get('context') or DEFAULT_CONTEXT:,} tokens",
         f"Target hosts: {', '.join(meta.get('hosts') or []) or NO_HOSTS}",
         _soft_models(reports, meta.get("stop"), meta.get("not_started"), meta.get("chosen"), meta.get("dropped")), "",
         "| Stage | Started | Finished | Output | Result | Validation |",
         "|---|---|---|---|---|---|"]
    by = {x.stage: x for x in runs}
    # an AI stage has a row only when it was started (a stage nobody chose is not "not run")
    for stage in (*LOG_ROWS, *(s for s in AI_STAGES if s in by)):
        x = by.get(stage)
        st = stamps.get(stage)
        if x is None:
            L.append(f"| {stage} | | | | not run | |")
            continue
        # a step the record says went well whose output is not a report (missing, or not readable: the check of the run
        # named it a gap) has no findings to count
        res = ((n(len(x.report['findings']), 'finding') if x.report is not None else "no readable output")
               if x.ok else f"FAILED: {x.error}")
        L.append(f"| {stage} | {x.started} | {x.finished or ''} | {'data/' + stage + '.json' if x.ok else ''} | "
                 f"{res} | {st.text if st else ''} |")
    qa_run = meta.get("qa_run") or {}  # the check of the run ran after the record: the record holds only its times
    if meta.get("qa") is not None:
        st = stamps.get(stagelist.QA)
        L.append(f"| {stagelist.QA} | {qa_run.get('started', '')} | {qa_run.get('finished', '')} | "
                 f"data/{stagelist.QA}.json | {n(len(meta['qa'].items) + len(meta['qa'].checked), 'finding')} | {st.text if st else ''} |")
    L += [f"| {stagelist.REPORT} | | {meta.get('finished', '')} | summary.html, details.html, review.html, "
          "full.md, brief.md, data/limits.md | written | |", ""]
    said = stop_log_lines(meta)
    L += ([f"- {x}" for x in said] + [""]) if said else []
    L += ["A report about someone else's repository is not published until its author has "
          "seen it.", ""]
    return "\n".join(L) + "\n"


def stop_log_lines(meta) -> list[str]:
    """LOG.md's lines for a run that was held and released (the record's `released`, M9 slice B), then for one that was
    stopped with `--until`: each time it went on (the record's `continued`), then the stop it is at now and the input
    file the stop wrote, if any. Nothing for a run that went through."""
    stop = meta.get("stop")
    held = meta.get("released")
    out = [RELEASED_LINE.format(gaps=n(held["gaps"], "gap"), at=held["at"])] if held else []
    out += [WENT_ON_LINE.format(plain=STEP_NAMES[c["after"]], at=c["at"]) for c in meta.get("continued") or []
            if c.get("after") in STEP_NAMES]
    if stop:
        out.append(STOPPED_LINE.format(plain=stop_plain(stop)))
        prep = stop["prepared"]
        out += [wrote_line(stop, f"data/{layout.input_file(prep['stage'])}")] if prep else []
    return out


def limits_doc(meta) -> str:
    return "\n".join([f"# {meta['repo']} run {meta['run']}: not examined", ""]
                     + [f"- {x}" for x in limits(qaview.of(meta))]) + "\n"
