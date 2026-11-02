# 04-pinpoint: the line behind each sweep flag (AI, optional, after the sweep)

**Question:** which line of a flagged passage does the thing the sweep flagged?
**Kind of evidence:** a second model's answer, kept only when its quote is found, word for word, in the
passage: a located observation. It marks and never demotes; the sweep finding stays.
**Reports under:** the review card of a sweep passage in `review.html` ("Where in the passage", "In plain
words", up to two "Also close" lines). Section 6 of `full.md` names the backend.

## Inputs

- `data/03-sweep.json` (the passages, with `p_any` and `covered`), `data/02.1-inventory.json` (the
  encodings of the files), and `data/02.4-phrases.json` (the lines the secret scan flagged, which are not sent), from `--reports <dir>`;
  `reads` in `stages/stages.json` names them. The sweep must have run: a run that did not choose `--sweep` does not start this stage.
- The folder audited, read-only, for the passage's lines (`stages/_shared/linetext.py`).
- `Library/softreads.yaml`, `pinpoint` (the system prompt and the question), and the sweep option's own
  words for the kind the passage was flagged as.
- A backend, chosen: `--pinpoint claude-cli`, or `claude-cli:<model>` to name the model (or `WALKDOWN_SOFT_PINPOINT`), or
  `--reads [model]`, which the front door resolves into that when the `claude` command is found.
  Jev does not read for this step. Nothing is chosen by default.

## Process

1. With no backend the stage asks nothing. Without the sweep's report it stops with a plain message.
2. Pick the passages the report shows as their own card: not skipped, no `02.4-phrases` pattern inside, and `p_any`
   at least 0.4, or, for a read that gives no probability, flagged (`pinpoint.targets`).
3. Write what the model will be shown to `data/04-pinpoint.input.jsonl`, one line per passage: the system
   prompt and the prompt (the passage as numbered lines, marked as data). A line the secret scan flagged is a blank at its number, with
   the rest of a private key; a passage in a file the scan did not read, or with nothing left, is not asked about and is a skip
   (`stages/_shared/secretmask.py`). It is on disk before anything is sent.
4. Ask the backend (`stages/_shared/back_claude.py`: the Claude Code CLI with `--tools ""`, `--safe-mode`, no
   settings, an empty working folder; remote). A call that gets no answer (an error, an answer that cannot be read) is tried once
   more after a short wait; if the second try fails too, it is a skip, with the second try's reason. A login the CLI
   rejects again stops the later calls.
5. Check and record. The answers go verbatim to `data/04-pinpoint.answers.jsonl`. A quote is kept only when it
   is found in the passage (a line off by one is moved to the line it really starts on); one `soft.pinpoint`
   finding per passage.

Never: send a line the secret scan flagged; change, demote, or remove a `soft.sweep` finding or any other step's finding ("no line does this" is
recorded, never acted on); keep a quote that is not in the passage, or show it at a line other than the one it
starts on; hand the model tools, the user's settings, hooks, or a folder with files; ask without the input
file on disk (when `--out` is given), or log in for the person; import another step's code.

## Outputs

- stdout: one contract-1 report with `backends`, the `soft.pinpoint` findings, and `usage` (the tokens the calls
  reported, and the calls sent); the runner saves it as `data/04-pinpoint.json` and stderr as `data/04-pinpoint.notes.txt`.
- With `--out <dir>` (the runner gives `data/`): `data/04-pinpoint.input.jsonl` and `data/04-pinpoint.answers.jsonl`,
  and `data/04-pinpoint.calls.jsonl` when a call got no answer on its first try or was not sent (no passage text and no error message;
  the report then has a `calls` block).
- With `--input-only` (and `--out`): `data/04-pinpoint.input.jsonl` alone, and nothing on stdout.

## The human check

Open `data/04-pinpoint.input.jsonl` before choosing: it is the text of every passage that will be sent. Nothing
is sent while you look. After the sweep has run (`--sweep jev --pinpoint claude-cli --until 03-sweep`), the
pinpoint writes this file with `--input-only` and stops, and `python walkdown.py continue <run folder> --pinpoint
claude-cli` goes on: choosing `--pinpoint` there is the consent to send. After
the run, a line the model named is a pointer, not a ruling: the quote is real (it was found in the text), but
that the line does what the model says is for the reader to judge. The stage has no fixture set, so
`python tools/grader/grader.py 04-pinpoint` says `no fixture set` and `LOG.md` shows the same: not a pass,
not a failure. The quote check is the gate on each answer.

## Spec

`specs/pinpoint.SPEC.md`: one spec for the stage, with a section for the runner (Behavior), `pinpoint.py`, and
the Reader (this step's side of the Claude Code backend, whose spec is `shared.SPEC.md`, `back_claude`).
