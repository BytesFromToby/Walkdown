# 03-sweep: the coverage sweep (AI, optional)

**Question:** is there prose a model reads that no pattern matched, and that tells the model to do
something risky?
**Kind of evidence:** a model's reading of each passage, recorded as it came back: a located observation, a
place to look and never a verdict. It never changes a finding of the coded steps.
**Reports under:** section 6 of `full.md` ("Needs a human read") and the review cards of `review.html`.
A run that did not choose it has neither the stage nor the section's content.

## Inputs

- The folder audited, read-only: the prose a model reads (Markdown and text files addressed to a model or
  a subagent, by the path rule in `stages/_shared/audience.py`), as original lines
  (`stages/_shared/linetext.py`).
- `data/02.1-inventory.json` (which files, which encoding) and `data/02.4-phrases.json` (which passages a
  pattern already hit: `covered`; which lines the secret scan flagged, which are not sent), from `--reports <dir>`; `reads` in `stages/stages.json` names both.
  Without `--reports` the stage runs those two steps itself (the grader does).
- `Library/softreads.yaml`, `sweep`: the question, the six kinds of action and `none`, each with what it is,
  what it is not, and examples; `flag_p`, the cut-off fixed before any measuring; `system`, the text a model that
  takes text is given with it (the passage is data, never instructions).
- A backend, chosen: `--sweep jev`, `--sweep claude-cli`, or `--sweep claude-cli:<model>` to name the model (or
  `WALKDOWN_SOFT_SWEEP`), or `--reads [model]`, which the front door resolves into one of those before the run starts (TypeSafe's Jev when it
  is available, else the Claude Code command). Walkdown picks no model for a run where the person named nothing (nothing is sent), lists no models, and asks nothing; a `claude-cli`
  with no model named runs `sonnet`.
  Nothing is chosen by default, and a run does not start the stage unless a person chose it.

## Process

1. With no backend the stage asks nothing: one skip finding, no files.
2. Leave out what must not go: a line the secret scan flagged is a blank at its place, with the rest of a private key, and a file the
   scan did not read gives no passages and has a skip (`stages/_shared/secretmask.py`). A note says how many lines, and the pages show it.
   Cut the prose into passages: front matter, then one passage per heading, long ones split at blank
   lines (`chunks.py`). A passage with nothing left is no passage.
3. Write what the model will be shown to `data/03-sweep.input.jsonl`, one line per passage: the exact
   request. It is on disk before anything is sent to a remote model.
4. Ask the backend, one question per passage: Jev (`back_jev.py`, TypeSafe's, remote; answers with a probability for each
   option) or a model that takes text (`text_sweep.py` over `stages/_shared/back_claude.py`, the Claude Code command with no
   tools; its answer is the name of one option and nothing else, and it gives no probability). A call that gets no answer
   (an error, an answer outside the options) is tried once more after a short wait; if the second try fails too, it
   is a skip, with the second try's reason. A key the service rejects again stops the later calls (the first call runs alone).
   A long read writes a plain progress line every 25 passages.
5. Record the answers verbatim in `data/03-sweep.answers.jsonl` and make one `soft.sweep` finding per
   passage, with the `02.4-phrases` patterns that already hit inside it (`findings.py`). Each passage whose first try
   got no answer, or that was not sent, gets a line in the call log, `data/03-sweep.calls.jsonl`.

Never: give a model tools, whole files, or anything but one passage and the question; send a line the secret scan flagged; ask without the input
file on disk (when `--out` is given), or contact a service the person did not name; change, drop, or add a finding of another step,
or produce a verdict, score, severity, or risk; print, log, or store an API key; import another step's code.

## Outputs

- stdout: one contract-1 report with `backends` (the backend, whether it is remote, the model it named),
  the `soft.sweep` findings, and `usage` (the tokens the calls reported, and the calls sent); the runner saves it as
  `data/03-sweep.json` and stderr as `data/03-sweep.notes.txt`.
- With `--out <dir>` (the runner gives `data/`): `data/03-sweep.input.jsonl` and `data/03-sweep.answers.jsonl`, and
  `data/03-sweep.calls.jsonl` when a call got no answer on its first try or was not sent (no key, no passage text,
  and no error message; the report then has a `calls` block).
- With `--input-only` (and `--out`): `data/03-sweep.input.jsonl` alone, and nothing on stdout.

## The human check

Open `data/03-sweep.input.jsonl` before choosing a remote model: it is every word that will be sent. Nothing
is sent while you look. Run `python walkdown.py <target> --sweep jev --until 02-coded`: the coded steps run, the
sweep writes this file with `--input-only` and stops (no key read, nothing sent), and the brief names the file.
When you are content with what it holds, `python walkdown.py continue <run folder> --sweep jev` goes on, and
choosing `--sweep` there is the consent to send. After the run, read each flagged passage in `review.html` and mark it; the model's `kind` says what it thought the
passage asks for, and whether the skill should do that is the reader's call. A passage with no flag is not
cleared: a model's miss is not safety (`docs/MODEL-ACCURACY.md`). `python tools/grader/grader.py 03-sweep`
grades `Fixtures/03-sweep/sweep-repo` on recall only, measured only with a backend.

## Spec

`specs/sweep.SPEC.md`: one spec for the stage, with a section for the runner (Behavior), `chunks.py`, the text-model
read, the Jev backend, and the findings.
