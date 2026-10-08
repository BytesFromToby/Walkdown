# Run layout: the files a run leaves on disk

> **Current layout: [docs/RUN-FOLDER.md](../docs/RUN-FOLDER.md).** Since 2026-10-02 the reports
> and LOG.md sit at the top of a run folder and everything else under `data/`. This document is
> the design history; where they disagree, docs/RUN-FOLDER.md describes what the code does.

METHOD owns the **why** (what each stage does, and the rule that detection never
concludes). This doc owns the **files**: exactly what a single audit writes, in
order, into its run folder. If the two ever disagree, METHOD is authoritative
and this doc is the drift.

Restructured 2026-09-25 to the seven stages. Output files are numbered by stage,
so the run folder, the pipeline folders, the fixtures, and the report sections
all share one numbering.

A run is one pinned version of one repo carried through the stages. The repo
copy stays in `ReposToExamine/`; outputs are never written into the examined
tree (RED-TEAM §19).

## The run folder

```
RepoResults/<repo>/
  <date>_<hash7>/            one run, e.g. 2026-09-25_28295e9
    LOG.md                   this run's log: one row per stage
    01-inventory.md          stage 1: what ships
    02-reader.md             stage 2: conversion, divergences, coverage
    normalized/              stage 2: the true text (regenerable; excludable from backup)
      text/                  one plain-text file per source file (line numbers = original)
      folded/                NFKC / zero-width / bidi / confusable-folded copies stage 4 greps
    03-graph.md              stage 3: orphans, dangling refs, dynamic loads, depth
    04-phrases.md            stage 4: every hit, quoted, by sub-group 4a to 4d
    04-terms.md              stage 4: the term table and its derived products
    05-capability.md         stage 5: trifecta, install grants, pairs
    06-soft.md               stage 6: review packet, plus model answers if a model ran
    07-limits.md             stage 7: what this run did not examine
    report/
      summary.md             stage 8: one screen, in stage order
      summary.html           stage 8: the same in plain language, for non-specialists (2026-09-30)
      full.md                stage 8: sections 1 to 7, every finding cited
```

**Run folder name.** `<date>_<hash7>`: the run date plus the first seven
characters of the pinned git hash (or `sha256` when there is no git history). The
date sorts runs in time; the hash tells a rerun of the same code apart from a new
version. Two runs of the same hash on the same day get a `-2` suffix.

Runs from before 2026-09-25 (`superpowers/v6.3.0/`, `plumbline/28295e9/`) keep
their old names and their old per-repo `LOG.md` as history.

`normalized/` is fully regenerable from the pinned source, so it can be excluded
from backup. It is still written and kept during a run, because a validated zero
needs its evidence on disk: a human must be able to open exactly the text that
was read and the folded text that was grepped.

**As built (stage 8 v1, 2026-09-29).** Each stage's report is kept as
`NN-name.json` with its stderr as `NN-name.notes.txt`, plus `graph.json`,
`hits.json`, and `capability.json` from the stages' `--out`. The per-stage
`NN-name.md` files are not written; `report/full.md` carries every finding in
readable form. `04-terms.md` and `06-soft.md` wait on stage 4 part 2 and stage 6.

## Stage outputs

Every hit in every file carries **file:line and a verbatim quote**. Every
detector result carries its **validation stamp**.

| File | Contents |
|---|---|
| `01-inventory.md` | Pin (source, channel, date, hash). File table (path, type, size, exec bit, encoding / BOM, entry-point flag). Totals and format / script-language census. Structural census (symlinks, ext-vs-magic with the detector's FP rate, archives, reader-window and long-line outliers). Frontmatter: descriptions verbatim, loader disagreement. Agent / command tool grants. Hook census. Platform manifests side by side. |
| `02-reader.md` | One table per concern: text formats (reading A vs reading B, divergences as facts), images (OCR text), metadata fields, markdown carriers, language / script-shift runs, invisible / bidi / BOM counts. Coverage: files and bytes read, unread list. |
| `03-graph.md` | Entry points used. Orphans, dangling references, dynamic loads (with the glob or scan that makes them), reference depth per file, manifest versus disk. |
| `04-phrases.md` | Four sections, 4a to 4d. Per pattern: hits (file:line, quote, audience tag), benign-share context from PHRASES, validation stamp. Endpoint census (4a). Conditional table (4b). Harness rubric (4c). Position and repetition. |
| `04-terms.md` | Term table (term, verbatim definition, file:line, source kind, load path). Conflicts, safety-vocabulary definitions, displaced-default count. |
| `05-capability.md` | Trifecta legs yes / no with citations to stages 1 to 4. Install grants. Trust elevation paths and bytes injected at load. Least-privilege positives. Cross-stage pairs. |
| `06-soft.md` | The review packet (extracts, term rows, the questions). If a model ran: model, prompt, verbatim answers. Located observations only. |
| `07-limits.md` | Failed or unrun checks (from the log), skipped checks (missing dependencies), standing limits. |
| `report/` | Assembled from the above per REPORTING.md. Nothing new is detected here. |

## LOG.md: one per run

The log is the run's audit trail and its to-do list at once. It is a **ledger,
not a report**: it records what ran and what it produced, never what it means.

```
# <repo> run <date>_<hash7>

Source: <url or path> | channel: <clone/zip/...> | pinned: <full hash>
Walkdown: <tool version> | optional deps: tesseract yes/no, gitleaks yes/no
Soft model: <name, or "none: packet only">

| Stage | Started | Finished | Output | Result | Validation |
|---|---|---|---|---|---|
| 1 inventory | ... | ... | 01-inventory.md | 66 files, 1 hook, 7 agent defs | 6/6 fixtures matched |
| 2 reader | ... | ... | 02-reader.md | 0 divergences | Y |
| 3 graph | | | | | |
...

Awaiting human: <decision only a human can make, if any>

Factory feedback:
- <detector flaw or false positive seen in this run>
```

- **One row per stage, written when the stage finishes.** A row with no
  Finished mark means the stage did not complete (ICM status: has-mark =
  COMPLETE, no-mark = PENDING / failed).
- **"What next" is derived, never written.** The next step is the first row
  without a Finished mark. No separate plan doc; no "next" field to go stale.
- **Validation stamp.** A stage may record a zero only if the same row records
  that its detectors matched their fixtures in this run. A zero with no stamp
  reads as broken, never clean. This makes the 2026-09-04 review false zero (a silent
  case-sensitive miss) structurally impossible to log as a clean result.
- **Awaiting human** holds only decisions the tool cannot make: publish or not,
  whether coordinated disclosure is needed.
- **Factory feedback** records flaws the run exposed. They are fixed in the
  factory (stages, fixtures, PHRASES), never in the run, and are copied to the
  factory backlog (HANDOVER Known gaps for now) so they do not get buried across
  run logs. A run is evidence, never doctrine.

## Across runs (future)

Comparing runs of the same repo over time (the version-delta record, the
postmark-mcp lesson) is out of scope for now. The per-run folders and logs are
shaped so a later tool can read `RepoResults/<repo>/*/LOG.md` in date order and
diff stage outputs between hashes.
