# RepoResults: audit outputs (ICM Layer 4: the product)

One folder per repository examined, one folder per run inside it. This is the
**per-run product**, not the factory: the method, stages, phrases, fixtures, and
detectors are the authority and stay stable across runs. Nothing here feeds back
as doctrine. A run is **evidence, not a rule** (ICM: *docs over outputs*). If a
run reveals a detector flaw, fix it in the factory, not here.

Inputs live separately in `ReposToExamine/` (pinned repo copies). Outputs never
get written into the examined tree (RED-TEAM §19).

## Shape (2026-09-25)

```
RepoResults/
  <repo>/
    <date>_<hash7>/     one run, e.g. 2026-09-25_28295e9
      LOG.md            this run's log: one row per stage
      01-inventory.md … 07-limits.md, normalized/, report/
```

The full file list, the run-folder naming rule, and the LOG.md format are in
`../pre-planning/RUN-LAYOUT.md`. That doc is the spec; this file is the pointer.

In short: **one log per run.** One row per stage, written when the stage
finishes. A row with no Finished mark means the stage did not complete (ICM
status: has-mark = COMPLETE, no-mark = PENDING / failed). The next step is the
first unmarked row, derived, never written. A stage may record a zero only with
its validation stamp. The log is a ledger, not a report: it records what ran,
never what it means.

A finished, published case is promoted out of here to `cases/NNN-<name>.md`.

## History

`superpowers/v6.3.0/` and `plumbline/28295e9/` predate the stage structure. They
keep their old pass-numbered files and their per-repo `LOG.md` (the earlier
design: one log per repo, spanning versions). Read them as history; METHOD.md
maps old pass numbers to stages.

Comparing runs of one repo over time is a future feature. Per-run folders keep
it possible: a later tool reads `<repo>/*/LOG.md` in date order.
