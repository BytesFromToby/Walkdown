# What a run leaves on disk

Every audit writes one folder. The top holds what people read; `data/` holds everything the
reports were built from, for anyone who wants to check a finding or build on the output.

- How to read the reports: [READING-THE-REPORT.md](READING-THE-REPORT.md)
- What each check means: [HOW-IT-WORKS.md](HOW-IT-WORKS.md)

## The layout

There is one layout. A run made by an earlier version of Walkdown (before 0.4.0) is not re-rendered
or compared (see "Runs made before 0.4.0" below).

```
RepoResults/<name>/<date>_<hash7>/          one run, e.g. RepoResults/my-skill/2026-10-29_ab12cde
  summary.html        one page: four questions at a glance, each with a label and a one-line answer, then Misalignment
  details.html        the same four questions and Misalignment with everything behind them, every place folded
  review.html         each place to check, one at a time, to mark Concerned, Not concerned, or Not sure
  marks.json          your marks, once you save them here (Walkdown never writes it)
  full.md             every finding, by section, with file and line
  brief.md            the short summary the command printed; it holds no text from the audited repository
  changes.md          what changed since the previous run of the same repository (only when there is one)
  LOG.md              what ran, when, with which models, and each step's validation stamp
  data/
    01-intake.json        one report per step that ran, named for the step (the format is stages/CONTRACT.md)
    02.1-inventory.json
    02.2-reader.json
    02.3-graph.json
    02.4-phrases.json
    02.5-capability.json
    02.6-builder.json
    05-qa.json            the check of the run: what should be there and is not (gaps), and what the run did not
                          examine (limits); the report draws section 7 from it
    <step>.notes.txt      each step's own messages: notes, limits, skipped checks (05-qa.notes.txt too)
    run.json              the run's record: each step's times and result, the validation stamps, the
                          expected context, the target hosts, the Walkdown version that made the run,
                          where a run stopped (see "A run that stopped"), and whether it was held
                          (see "A run that was held")
    limits.md             what this run could not see (section 7, as its own file)
    capability.json       "What this touches" with every piece of evidence (02.5-capability.json caps each list at 20)
    graph.json            the reference graph: nodes and edges
    hits.json             the phrase hits with counts per check and per pattern, and the files not scanned
    normalized/           the text of each file the reader read: text/ as the model receives it (for a PDF,
                          or DOCX, the text read from it; the phrase step matches that), folded/ with
                          invisible and look-alike characters folded away
```

Only when you chose a model read, these files are also in `data/` (a model that takes text has no `probabilities` or `p_any` in
its answers, and its input rows hold `system`, `prompt`, and `model`):

```
    03-sweep.input.jsonl      exactly what the sweep showed the model, written before anything was sent
    03-sweep.answers.jsonl    every answer, as it came back, with the exact request and response
    03-sweep.calls.jsonl      the call log (see below); only when a call got no answer on its first try
    03-sweep.json             the sweep's findings
    04-pinpoint.input.jsonl   the same, for the pinpoint read (after a sweep)
    04-pinpoint.answers.jsonl
    04-pinpoint.calls.jsonl
    04-pinpoint.json
```

A run that chose neither has none of them, and no row for them in `LOG.md`.

**The call log.** A model call that gets no answer (an error from the service or the program, an answer
outside the options, an answer that cannot be read) is tried once more after 2 seconds. Each passage whose
first try got no answer, or that was never sent (no key, the package or the program missing, a key
rejected again), has one line in `data/<step>.calls.jsonl`, apart from `LOG.md`. The file is written only
when there is a line. A line holds no key, no passage text, and no error message: an error's text can repeat
the passage or the model's own words, so only the kind of failure and a status are kept. Its `qid` names
the file and line, and the passage is in the input file:

```json
{"qid": "sweep:skills/x/SKILL.md:12", "backend": "jev",
 "first": {"kind": "TypeSafeRateLimitError", "status": 429},
 "retry": {"result": "answered"}, "at": "2026-10-30T09:12:04+00:00"}
```

`status` is an HTTP status code for Jev and the program's exit code for the Claude CLI, `null` when the
failure has none. `first` is `null` for a passage that was never sent. `retry` is `{"result": "answered"}`,
`{"result": "no answer", "kind": ..., "status": ...}`, or `{"result": "not tried", "why": ...}`. A passage
that still has no answer is skipped in the step's findings, with the second try's reason in the same words
(`jev: TypeSafeRateLimitError, status 429`, `claude-cli: error, exit code 1`; `not sent: <reason>` when a
rejected key stopped the later calls), so failures of one kind are counted as one reason. The step's `.json` then also has a `calls` block (`log`,
`answered_on_retry`, `not_sent`).

**Tokens.** A model step's `.json` has a `usage` block when a backend was chosen:

```json
{"input": 596200, "output": 31464, "cache_write": 0, "cache_read": 12000, "calls": 431, "reported": 431}
```

Each count is a whole number (no higher than 10^15) the backend reported, added up over the calls that reported it. A count the
backend did not report is left out, and is never written as 0 (a total is then a lower bound). `calls` is how many calls Walkdown
sent, a second try included; it is 0 for a read that sent nothing. `reported` is how many of those calls reported any token count:
when it is below `calls` and above 0, the totals are partial and the pages say so (`500 in, 15 out (from 5 of 9 calls)`), and 0
is `not reported`. A call that came back as an error still counts its tokens if the reply had them: they were spent. A `usage`
that is not whole numbers, has a count above 10^15, or has a `reported` higher than its `calls` makes the file a report that
cannot be read, and the check of the run names the gap. The fixture check of the sweep sends its fixtures to the model, and
its tokens are in the validation stamp in `data/run.json` (`stamps.03-sweep.usage`, the same block), only when the check was run
in this run; a stamp reused from an earlier run carries none.

**The folder name** is the run date and the first seven characters of the pinned commit (or
sha256 when there is no git history). A second run of the same version on the same day gets
`-2`, `-3`, and so on. A run that failed before the inventory finished is named `<date>_failed`. A run
stopped after intake (`--until intake`) has no pin yet and is named `<date>_stopped`; going on with
`walkdown.py continue` renames it `<date>_<hash7>`, keeping its date.

**The audited repository is not copied here.** A URL is cloned into `ReposToExamine/<name>/`; a
folder is read where it is. Nothing is ever written inside the audited repository.

## LOG.md

The run's record in words, written once by the report step from `data/run.json`. Read it to know
whether to trust the rest.

```
# my-skill run 2026-10-29_ab12cde

Source: .../ReposToExamine/my-skill | channel: git | pinned: git ab12cde4f5a6...
Walkdown: 0.4.0 (1a2b3c4) | optional deps: see data/limits.md
Expected context: 32,000 tokens
Target hosts: none named
Soft models: none (no model read was chosen)

| Stage | Started | Finished | Output | Result | Validation |
|---|---|---|---|---|---|
| 01-intake | ... | ... | data/01-intake.json | 1 findings | PASS (gate 1/1, negative 2/2) |
| 02.1-inventory | ... | ... | data/02.1-inventory.json | 116 findings | PASS (gate 26/26, negative 7/7) |
| 02.2-reader | ... | ... | data/02.2-reader.json | 116 findings | PASS (gate 38/38, negative 28/28, recall 8/9) |
...
| 05-qa | ... | ... | data/05-qa.json | 31 findings | PASS (gate 61/61, negative 16/16) |
| 06-report | | ... | summary.html, details.html, review.html, full.md, brief.md, data/limits.md | written | |
```

| Part | Meaning |
|---|---|
| Source, channel, pinned | where the copy came from and the exact version examined |
| Walkdown | the version and commit of Walkdown that ran (so a finding can be traced to the rules of that day) |
| Soft models | which optional model reads ran, local or remote; "none" means no model read was chosen |
| Result | how many findings the step emitted, or the error if it failed (its exit code and the error's type, such as `FAILED: exit 1: ValueError`; the step's whole messages are in its notes file); "not run" for a step the run did not reach |
| Validation | the grader's stamp for that step, run before the audit against the step's fixtures: PASS, INCOMPLETE (a check was skipped, usually a missing optional tool), or FAIL (do not trust that step's findings in this run). "no fixture set" is the pinpoint step's, which has no fixtures: not a pass and not a failure. "measured <date>, same code and fixtures" means the stamp was reused from an earlier run with identical code, fixtures, and model choices (`.cache/stamps.json` in the Walkdown folder); `--revalidate` measures afresh |

## A run that stopped

`walkdown.py <target> --until <step>` stops the run after a step. The folder has the steps that ran, the
pages and the brief for them, and `data/run.json` says where it stopped. `walkdown.py continue <run folder>`
goes on in the same folder. The record has these keys besides the ones above:

| Key | Meaning |
|---|---|
| `version` | the Walkdown that made the run (`0.4.0 (1a2b3c4)`); `continue` goes on only with the same one |
| `code` | a hash of the code and tables the run used; `continue` also needs it to match, since two sets of uncommitted edits have the same `version` |
| `until` | the step the run stopped after; present only for a run that stopped as asked, so a run without it went through |
| `prepared` | when a model read would have come next: `{"stage": "03-sweep", "items": 12, "backend": "jev"}`, the step that wrote its input file and stopped, how many passages the file holds, and the backend that wrote it |
| `continued` | one `{"after": step, "at": time}` for each time the run was gone on with |
| `not_started` | a chosen model read that was not started because the read before it got no answer for any passage: `[{"stage": "04-pinpoint", "why": "sweep-no-answer"}]`; the step has no row and no stamp |
| `chosen` | the model reads the last command chose, by step name (`["03-sweep", "04-pinpoint"]`); a read chosen and never started, because a step before it crashed, is a gap in the check of the run, and `LOG.md`'s `Soft models:` line names it. A `continue` records the reads that already ran and the ones it chooses |
| `dropped`, `backends` | `dropped`: a read an earlier command chose that `continue` did not choose, so it did not run (choosing a read at `continue` is the consent to send); `continue` prints a note for it, and `LOG.md`, section 6, section 7, and the brief say it, with the way that works: `continue` while the run is stopped, a new audit once it has finished. `backends`: `{"03-sweep": "jev"}`, the backend chosen for the reads in `chosen` and `dropped`, which the stop's brief puts in its `To go on:` command |

A step that wrote only its input file did not run: it has no `<step>.json` and no row in `LOG.md`'s
table, and `data/<step>.input.jsonl` holds exactly what it would send. Nothing was sent. `LOG.md` has a
line for the stop, a line for the input file, and a line for each time the run went on. A step the stop
left out did not fail: the pages, the brief, and `data/limits.md` say the run stopped as asked.
A run stopped before its last coded step is not compared with other runs (`changes.md` says so), and the
next full run of the repository is compared with the last run that went through.

## A run that was held

After the steps, the validation, and the record, `05-qa` reads the saved run (the record, each step's output, and
the call logs) and writes `data/05-qa.json`. Each finding is a `qa.gap` (something that should be there and is
not), a `qa.limit` (something the run did not examine, and says so), or a `qa.checked` (what a check that found nothing looked at);
the fields are in `stages/CONTRACT.md`. A
gap is: a step that should have run with no output or that failed (a chosen model read counts); a step whose fixture
check gave anything but a pass (`FAIL`, or a check that could not be made: `ERROR`, `SETUP ERROR`, `NOT BUILT`, `no fixture
set` for any step but the pinpoint; its "found none" cannot be trusted); a chosen model read in which no passage got an
answer; a check that has no coverage line, or whose line shows items it neither looked at nor explained (or counts more than
there were, or reports a `found` the findings do not hold, or names a check the step does not make). Each step's saved output carries a `coverage` list: per check, or per pass over the same items, `of` (what it
was to look at), `looked_at`, `explained` (items a skip or an unread or not-scanned entry explains), and `found`, with check
ids and counts only (`stages/CONTRACT.md`, "Coverage lines"). A check skipped for a missing optional tool (`INCOMPLETE`),
a step a stop left out, and a model read that answered some passages are limits and hold nothing.

With one gap or more the run is **held**: no report is written (no `summary.html`, no `LOG.md`, no `data/limits.md`),
the exit code is 1, `brief.md` is the brief of a held run, and the record has:

| Key | Meaning |
|---|---|
| `qa` | `{"started", "finished"}`: when the check ran (the record is written first, so this is added after the check) |
| `held` | `{"by": "05-qa", "gaps": N}`: the run is held |
| `released` | `{"by", "gaps", "at"}`: `walkdown.py continue` wrote the report of a held run, with what the run has. `held` is gone then |

`walkdown.py continue <run folder>` on a held run runs no step and no validation: it writes the report, and the
pages name every gap as a step that did not work and in section 7 (a step that failed included: a held run with a
failed step is released like any). It refuses a model option, `--until`, or `--revalidate` (a release runs nothing), and a run held
by another version of Walkdown. If the report stage fails, the run goes back to held as it was. The other way on is to fix the cause and audit the repository again. The brief of a
held run holds Walkdown's own words only: the step's plain name, the check, counts, the reasons it gave a skipped
passage, and the kind of error a step stopped with.

## The step outputs

Every `<step>.json` file has the same shape (`stages/CONTRACT.md`):

```json
{
  "stage": "02.4-phrases",
  "contract": 1,
  "findings": [
    {"check": "phrase.L.override", "file": "skills/x/SKILL.md", "line": 12,
     "quote": "Ignore the rules above.", "patterns": ["L.ignore"], "audience": "model"}
  ]
}
```

- `check` names what was found; every check id is listed with its fields in
  `stages/CONTRACT.md`, and explained in [HOW-IT-WORKS.md](HOW-IT-WORKS.md).
- `file` and `line` locate it (`null` for findings about the whole run).
- A finding with `skipped` means the check could not run there, and why. A skip is never a pass.

Two quick ways in:

```bash
python -c "import json; f=json.load(open('data/02.4-phrases.json'))['findings']; print(len(f))"
```
```bash
python -c "import json; [print(x['file'], x['line'], x['quote']) for x in json.load(open('data/02.4-phrases.json'))['findings'] if x['check']=='phrase.L.override']"
```

### Which file answers which question

| Question | Look in |
|---|---|
| Why is a trifecta leg checked? | `capability.json`, the `cap.leg` finding's `evidence` (every citation; the summary shows the first few) |
| What exactly did the phrase step match on this line? | `02.4-phrases.json`, the finding's `matches` (the matched words and their position) |
| Was a line changed by hidden characters? | `02.2-reader.json` (`read.fold`), and `normalized/text/` against `normalized/folded/` (a finding with `masked: true` holds what looks like a secret: its words are in the file and in `normalized/` only) |
| What references this file? | `graph.json` edges, or `02.3-graph.json` `graph.depth` (`from`, `via`) |
| How often did each pattern hit? | `hits.json` `counts.per_pattern` |
| Which lock files did the secret scan leave out? | `02.4-phrases.json`, `secret_left_out` |
| Which copy was audited, and how was it got? | `01-intake.json` (`intake.source`) |
| What did a model say, and what was it shown? | `03-sweep.answers.jsonl` and `04-pinpoint.answers.jsonl` (request and response for every answer), when a model read was chosen |
| Which model calls got no answer, and why? | `03-sweep.calls.jsonl` and `04-pinpoint.calls.jsonl`, when a call did not answer on its first try |
| How did each step go, and with which options? | `run.json` |
| What is missing from the run, and what did it not examine? | `05-qa.json` |
| What was not examined? | `limits.md`, and `skipped` findings in any step output |

## changes.md: version drift

Written by the report step when an earlier run of the same repository exists at a different
version, or at the same version when Walkdown changed since and something differs (or by
`walkdown.py diff <old> <new>`). It compares the two runs' findings: files, hooks, tool grants,
MCP servers, descriptions, phrase hits (each with where it came from: the repository, Walkdown's
search terms, or its matching code), hosts, and capability. The search-term version it reads is
the `terms` block of `data/02.4-phrases.json`. How it
compares is in [HOW-IT-WORKS.md](HOW-IT-WORKS.md#version-drift-comparing-two-runs). The earlier run
is the newest other run of the same repository that finished before this one started.

## Rebuilding the reports

After a change to the report code, rebuild a run's reports from its saved data without
running any step or model:

```bash
python stages/06-report/run.py RepoResults/<name>/<run>
```

It rewrites `summary.html`, `details.html`, `review.html`, `full.md`, `brief.md`, `changes.md`, and
`data/limits.md`, and adds one line to `LOG.md` naming the version that rendered it again. It does not run the grader again: the stamps are the ones saved in
`data/run.json`. The pages read back a `marks.json` saved next to
them, so your marks return with the pages; a run with no `marks.json` of its own starts from the
newest earlier run's ([Your marks](READING-THE-REPORT.md#your-marks)).

## Runs made before 0.4.0

A run made by an earlier version of Walkdown has no `data/run.json` of the current format (format 3), and its
stage files carry the old names (`01-inventory.json`, `04-phrases.json`, ...). A run made by this version before
the check of the run existed has a record of format 2 and no `data/05-qa.json`; it is treated the same way. Walkdown does not
re-render such a run (it says so in one line and exits 2), and a new run of the same repository does
not compare itself with it: `changes.md` and the brief say the earlier run is not comparable. To get
the current pages, audit the repository again. Your marks carry over to the new run.

## Handling a run folder

- **The data quotes the audited repository.** Quotes, file names, and model answers in `data/`
  and in `full.md` and `review.html` are text from the repository under review. If that repository is hostile,
  the text may be written to steer an AI assistant that reads it. Read reports yourself, or give
  an assistant only the brief that `walkdown.py` prints, which contains no repository text.
- **`RepoResults/` is kept out of git.** A report about someone else's repository is not
  published until its author has seen it.
- **Committed secrets** are reported by location only; the value of a line the scan flagged never appears in a report or a step
  output. Three steps write before the scan (`02.1-inventory.json`, `02.2-reader.json`, `02.3-graph.json` and `graph.json`), and later
  steps copy their words (`02.5-capability.json`, `capability.json`, `02.6-builder.json`), so each is masked once the last step that
  reads the words has run: the reader file right after `02.5-capability`, and the rest right after `02.6-builder`, or as soon as a step
  fails. A run stopped earlier holds them there until it goes on. `normalized/` holds each file's actual text, secrets included, so
  treat it like the repository itself. A model read does not send a flagged line, so the input and answers files of `03-sweep` and
  `04-pinpoint` do not hold it either. The scan cannot flag everything: a key only in a picture or in hidden characters, in a lock
  file, or in a file's own name is not masked.
- **`normalized/` can be deleted** to save space once the reports are rendered; it is rebuilt by
  re-running the audit. A re-render without it still works, but review cards show the flagged
  line alone, without the lines around it.
