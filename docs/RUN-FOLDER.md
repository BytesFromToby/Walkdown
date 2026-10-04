# What a run leaves on disk

Every audit writes one folder. The top holds what people read; `data/` holds everything the
reports were built from, for anyone who wants to check a finding or build on the output.

- How to read the reports: [READING-THE-REPORT.md](READING-THE-REPORT.md)
- What each check means: [HOW-IT-WORKS.md](HOW-IT-WORKS.md)

## The layout

```
RepoResults/<name>/<date>_<hash7>/          one run, e.g. RepoResults/backlog/2026-10-02_b449d9f
  summary.html        the page for people: what to look at first, one sentence per stage
  summary.md          the same summary as text
  full.md             every finding, by stage, with file and line
  LOG.md              what ran, when, with which models, and each stage's validation stamp
  data/
    01-inventory.json     stage outputs, one per stage (the format is stages/CONTRACT.md)
    02-reader.json
    03-graph.json
    04-phrases.json
    05-capability.json
    06-soft.json
    0N-*.notes.txt        each stage's own messages: notes, limits, skipped checks
    07-limits.md          what this run could not see (section 7, as its own file)
    capability.json       stage 5 with every piece of evidence (05-capability.json caps each list at 20)
    graph.json            stage 3's reference graph: nodes and edges
    hits.json             stage 4's hits with counts per check and per pattern, and the files not scanned
    normalized/           stage 2's text of each file: text/ as the model receives it, folded/ with
                          invisible and look-alike characters folded away (what stage 4 matched)
    06-packet.md          stage 6's questions, written for a person to answer
    packet.json           the same questions as data
    answers.jsonl         every model answer, with the exact request and response
```

Stage 6 files appear only when stage 6 ran with a model (`answers.jsonl`) or at all
(`06-packet.md`, `packet.json`).

**The folder name** is the run date and the first seven characters of the pinned commit (or
sha256 when there is no git history). A second run of the same version on the same day gets
`-2`, `-3`, and so on. A run that failed before stage 1 finished is named `<date>_failed`.

**The audited repository is not copied here.** A URL is cloned into `ReposToExamine/<name>/`; a
folder is read where it is. Nothing is ever written inside the audited repository.

## LOG.md

The run's record, written last. Read it to know whether to trust the rest.

```
# backlog run 2026-10-02_b449d9f

Source: .../ReposToExamine/backlog | channel: directory | pinned: git b449d9fa975e...
Walkdown: bb80a98 | optional deps: see 07-limits.md
Soft models: label jev (remote, jev-1.13.0); sweep jev (remote, jev-1.13.0)

| Stage | Started | Finished | Output | Result | Validation |
|---|---|---|---|---|---|
| 01-inventory | ... | ... | data/01-inventory.json | 513 findings | PASS (gate 13/13, negative 1/1) |
| 02-reader    | ... | ... | data/02-reader.json    | 246 findings | INCOMPLETE (gate 14/15, ...; skipped: rd-img-ocr) |
...
- Report re-rendered 2026-10-03T... by Walkdown ... from this run's saved stage outputs (no stage re-run).
```

| Part | Meaning |
|---|---|
| Source, channel, pinned | where the copy came from and the exact version examined |
| Walkdown | the commit of Walkdown that ran (so a finding can be traced to the rules of that day) |
| Soft models | which stage 6 models ran, local or remote; "none" means the packet only |
| Result | how many findings the stage emitted, or the error if it failed |
| Validation | the grader's stamp for that stage, run before the audit against the stage's fixtures: PASS, INCOMPLETE (a check was skipped, usually a missing optional tool), or FAIL (do not trust that stage's findings in this run). "measured <date>, same code and fixtures" means the stamp was reused from an earlier run with identical code, fixtures, and stage 6 choices (`.cache/stamps.json` in the Walkdown folder); `--revalidate` measures afresh |
| Re-rendered lines | appended each time the reports are rebuilt from the saved data |

## The stage outputs

Every `0N-*.json` file has the same shape (`stages/CONTRACT.md`):

```json
{
  "stage": "04-phrases",
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
python -c "import json; f=json.load(open('data/04-phrases.json'))['findings']; print(len(f))"
```
```bash
python -c "import json; [print(x['file'], x['line'], x['quote']) for x in json.load(open('data/04-phrases.json'))['findings'] if x['check']=='phrase.L.override']"
```

### Which file answers which question

| Question | Look in |
|---|---|
| Why is a trifecta leg checked? | `capability.json`, the `cap.leg` finding's `evidence` (every citation; the summary shows the first few) |
| What exactly did stage 4 match on this line? | `04-phrases.json`, the finding's `matches` (the matched words and their position) |
| Was a line changed by hidden characters? | `02-reader.json` (`read.fold`), and `normalized/text/` against `normalized/folded/` |
| What references this file? | `graph.json` edges, or `03-graph.json` `graph.depth` (`from`, `via`) |
| How often did each pattern hit? | `hits.json` `counts.per_pattern` |
| What did a model say, and what was it shown? | `answers.jsonl` (request and response for every answer) |
| What was not examined? | `07-limits.md`, and `skipped` findings in any stage output |

## Rebuilding the reports

After a change to the report code, rebuild a run's reports from its saved data without
running any stage or model:

```bash
python stages/08-report/run.py --rerender RepoResults/<name>/<run>
```

It rewrites `summary.html`, `summary.md`, and `full.md`, re-stamps validation with the current
grader, and appends a line to LOG.md.

## Runs made before 2026-10-02

Older runs keep their layout: stage outputs at the top of the run folder and the reports in
`report/`. Re-rendering an old run keeps it in that layout. Walkdown reads both.

## Handling a run folder

- **The data quotes the audited repository.** Quotes, file names, and model answers in `data/`
  and in `full.md` are text from the repository under review. If that repository is hostile,
  the text may be written to steer an AI assistant that reads it. Read reports yourself, or give
  an assistant only the brief that `walkdown.py` prints, which contains no repository text.
- **`RepoResults/` is kept out of git.** A report about someone else's repository is not
  published until its author has seen it.
- **`normalized/` can be deleted** to save space; it is rebuilt by re-running the audit, and the
  reports do not need it.
