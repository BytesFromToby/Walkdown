# RepoResults: audit outputs (ICM Layer 4: the product)

One folder per repository examined, one folder per run inside it. This is the
**per-run product**. The method, the steps, the Library, the fixtures, and
the detectors are the factory: they are the authority and stay stable across runs. Nothing here feeds back
as doctrine. A run is **evidence** (ICM: *docs over outputs*). If a
run reveals a detector flaw, fix it in the factory.

Inputs live separately in `ReposToExamine/` (pinned repo copies). Outputs never
get written into the examined tree (RED-TEAM §19).

## Shape

```
RepoResults/
  <repo>/
    <date>_<hash7>/     one run, e.g. 2026-10-29_28295e9
      summary.html  details.html  review.html  full.md     the reports
      brief.md          the brief the command printed
      LOG.md            this run's log: one row per step, with its validation stamp
      data/             <step>.json and <step>.notes.txt, run.json (the record), limits.md,
                        graph.json, hits.json, capability.json, normalized/
```

The full file list, the run-folder naming rule, and the LOG.md format are in
`../docs/RUN-FOLDER.md`. That doc is the spec; this file is the pointer.

In short: **one log per run.** One row per step, written when the run ends, from the
record in `data/run.json`. A step may record a zero only with its validation stamp. The
log is a ledger: it records what ran, and never what it means.

A finished, published case is promoted out of here to `cases/NNN-<name>.md`.

## Older runs

A run made by a version of Walkdown before 0.4.0 keeps the files it was made with. It is
not re-rendered, and a new run of the same repository does not compare itself with it
(`docs/RUN-FOLDER.md`, "Runs made before 0.4.0"). Read such a run as history.
