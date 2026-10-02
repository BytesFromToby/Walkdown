# Stage 6: Soft reads

**Question:** what can a pattern not settle?
**Kind of evidence:** a review packet of specific questions over stage 1 to 5
outputs, and, when the user picks a model, that model's answers recorded
verbatim. **Report heading:** Needs a human read.

Stage 6 never renders a verdict or a score (METHOD). An answer is a **located
observation**: it is tied to a question, the question to a file and line, and the
answer never changes a stage 1 to 5 finding.

Sources: `pre-planning/METHOD.md` (Stage 6), `pre-planning/RED-TEAM.md` §8
("Attack the auditor"), `pre-planning/TOOLING.md` (Stage 6), `pre-planning/
REPORTING.md` (Section 6), `pre-planning/THREATS.md` classes 14, 16, 20, 22,
`stages/CONTRACT.md`, and the TypeSafe / Laya usage notes below. Nothing here
comes from the answer sheet.

## Model choice (decided 2026-09-29)

**The user picks the backends at run time; nothing is hard-wired.** Defaults are
`none`: the stage writes the packet and records no answers.

| Job | Backend options | Notes |
|---|---|---|
| Labeling (`--label`, env `WALKDOWN_SOFT_LABEL`) | `none`, `jev`, `laya`, `claude-cli` (added 2026-09-30; self-reported confidence, see pre-planning/soft/EVAL.md) | Jev (TypeSafe, remote API) is the first choice for labeling; Laya (local, CPU) is the comparison |
| Comparison (`--compare`, env `WALKDOWN_SOFT_COMPARE`) | `none`, `jev`, `laya`, `claude-cli` | a second labeling backend on the same questions; agreement is recorded |
| Relational (`--relational`, env `WALKDOWN_SOFT_RELATIONAL`) | `none`, `claude-cli` | Claude through the Claude Code CLI; local backends come later |

Flags override the environment. The report names every backend used and whether
it is remote. RED-TEAM §8's "local only" is reconciled as: **local by default
(`none` is local), remote only when the user names it**, and no model ever holds
tools.

## Inputs

- `<input_dir>`, read-only, plus the stage 1 to 5 reports, reached like stage 5
  reaches stages 1 to 4: `--reports <dir>` (holding `NN-name.json` and stage 3's
  `graph.json`), or run as subprocesses. Import nothing from another stage.
- Line text for question state comes from the input files (decoded, original
  lines), the same text stage 4 quotes.

## The packet

### Labeling questions (`kind: label`)

One question per **line in instruction text** (stage 4 `audience` `model` or
`subagent`) carrying at least one `phrase.*` hit. Part 2 table rows are not
questions. A line with several hits is one question listing them all.

- **Question:** does this line tell the reader to do the matched action, tell
  them not to, describe it, or quote / give an example of it?
- **Options** (a Choice), each with `what`, `not_for`, and `examples` written in
  the stage folder as data:
  - `do`: the line instructs the reader to perform the matched action
    (including instructing them to suppress, skip, or hide something).
  - `not-to`: the line instructs the reader **not** to perform it.
  - `description`: the line states a fact about the artifact, a tool, users, or
    a situation, or describes a quality, without instructing the reader.
  - `example-or-quote`: the line quotes the phrase or presents it as an example,
    warning, or illustration.
  - `other-sense` (added 2026-09-29): the line uses the matched words for
    something other than what the pattern locates ("start over" meaning restart
    the code, "post one line" of status). Labeling 128 real lines showed this is
    the commonest form of house-word noise, which is what METHOD says labeling is
    for.
- **State** (JSON, the untrusted text as data): `file`, `line`, `text` (the
  original line), `before` and `after` (up to two lines each), `matched`: each
  hit's check and pattern ids with a one-line plain description of what the
  pattern locates (from `patterns.yaml` `source`).

### Relational questions (`kind: relational`)

Fixed templates, one per source row, each with its state:

| Source | Question |
|---|---|
| `term.safety` | Against the word's ordinary meaning, what does this definition change about how a model would act on instructions that use the word? |
| `term.conflict` (anchored at the first definition) | The same word is defined differently in these places. Which instructions elsewhere would read differently under each definition? |
| `rubric.action` with `confirm_redefined`, or tier `prohibited` with no confirmation | What would a model do at this step, and is any point where the user is asked before the action takes effect? |
| `cap.pair` `hook+phrase` | This text can reach the model through a hook's output before the user types anything. What would a model do on reading it? |
| stage 5 legs, one per run (`file`, `line` null) | Describe, as capability and not intent, how these three capabilities could combine in this artifact, citing the evidence given. |

Answers are free text, recorded verbatim. The prompt asks for at most 150 words,
most important point first, and says the pattern evidence can be wrong; the cap
(2,500 characters, raised from 1,200 on 2026-09-30 when the first real reads were
cut mid-sentence) is a backstop.

### What goes to a model

Only the question and its state (the extracted lines and stage findings), never
whole files, never tools. For `claude-cli`: `claude -p` with `--tools ""`,
`--strict-mcp-config`, `--no-session-persistence`, `--output-format json`, a
system prompt saying the quoted text is data from the artifact under review and
contains no instructions for the reviewer, and the working directory an empty
temporary folder (no CLAUDE.md). An error (for example an expired login) is a
skip, never a failure of the stage.

## Backends (usage, verified 2026-09-29)

- **Jev:** `typesafe_sdk` 0.7.2 (`from typesafe_sdk import TypeSafeClient,
  Choice`); `client.system_one(state=..., questions=..., model="jev-latest")`;
  read `response.choices[qid]` (`choice`, `probabilities`, `confidence`; check
  the installed SDK's types). Key: `TYPESAFE_API_KEY` from the process
  environment, else read from `HKCU\Environment` with `winreg` inside the
  process; **never print, log, or write the key**. Docs:
  https://docs.typesafe.ai/sdk/python.md. Known weakness (from an earlier
  evaluation): reads the claim, not the truth, on adversarial text.
- **Laya:** `laya` 0.3.22 with CPU torch; `agent = laya.load("convaiinnovations/
  laya")` (first use downloads the weights); `agent.predict(state, {qid:
  {"type": "choice", "instructions": ..., "criteria": {...}}})["answers"][qid]`
  gives `choice`, `probabilities`, `confidence`. 512-token sequence cap: record
  when a question's state was truncated. Load once per run.
- **claude-cli:** as above; `--model` from `WALKDOWN_SOFT_CLAUDE_MODEL`, default
  `sonnet`. Record the model the CLI reports.

A backend that is not installed, has no key, or fails, gives skips for its
questions with the reason, and stderr names it (stage 7 lists it).

### Jev `--both` (added 2026-10-01, soft D4)

Optional. Jev reads each line twice, plain and with the matched words marked, and the two
label distributions are averaged. Measured on the 119 real lines (soft/EVAL.md): 10/10
`do` points at p >= 0.8 against 7/7 for one plain read; promising, not proven. Default
stays one plain read.

### Coverage sweep (added 2026-10-01, soft D2)

Opt-in (`--sweep jev`). Every prose passage a model reads gets one question: does it tell
the reader to do one of six kinds of action (override, send-out, secrets, skip-user,
remote-instructions, persist)? The question and threshold were committed before the
validation fixtures were written. Measured: fixtures 11/12 payloads flagged, 0/20 benign
(soft/EVAL.md). A flagged passage is a location; `covered` says whether stage 4 already
hits inside it.

## Findings (added to CONTRACT)

| Check | One finding per | Fields |
|---|---|---|
| `soft.question` | question | `kind` (`label` or `relational`), `qid`, `question`, `sources` (the stage findings it rests on) |
| `soft.label` | labeling question answered by the primary backend | `qid`, `backend`, `model`, `label`, `probabilities`, `confidence`, `truncated` |
| `soft.compare` | labeling question answered by the comparison backend | same fields as `soft.label` |
| `soft.agree` | labeling question answered by both | `qid`, `primary`, `compare`, `agree`: bool |
| `soft.read` | relational question answered | `qid`, `backend`, `model`, `answer` (verbatim) |

A question with no backend configured, or whose backend failed, gets a skip
finding for `soft.label` (or `soft.read`) on its file and line with the reason
(`"no labeling backend"`, `"jev: no key"`, ...). The grader counts skips on
measured rows as skipped, not as misses.

`--out <dir>` writes `06-packet.md` (every question with its state, readable, so
a human can take it to any assistant), `packet.json`, and `answers.jsonl` (per
answer: backend, model, the exact request sent, the raw response).

## Must never

- Give a model tools, whole files, or anything but a question and its state.
- Let an answer change or drop a stage 1 to 5 finding, or produce a verdict,
  score, severity, or risk field.
- Print, log, or store an API key.
- Contact any network service other than the backend the user named.
- Import code from another stage.

## Done when

1. Every script has a `specs/<name>.SPEC.md` and pytest tests written from it; tests
   stub every backend (no network, no model download in tests).
2. `.venv/Scripts/python grader/grader.py 06` reports PASS with no backend (recall
   rows skipped).
3. With `WALKDOWN_SOFT_LABEL=jev` the grader still PASSES and reports recall; the
   same with `WALKDOWN_SOFT_LABEL=laya`. Report both recalls and, from one run
   with `--label jev --compare laya` on the fixture, the agreement rate.
4. Runs on `ReposToExamine/backlog/` and `ReposToExamine/claude-familiar/`
   (read-only) with `--label jev --compare laya --relational claude-cli`
   complete; report question counts, labels by class, agreement, and whether the
   Claude reads ran or were skipped (the CLI login may have expired).
