# back_claude.py: spec

The relational backend: Claude through the Claude Code CLI, with no tools. Usage
from `stages/06-soft/CONTEXT.md` "What goes to a model" and "Backends".

## Inputs

- `ClaudeCLI(data, model=None, runner=subprocess.run, which=shutil.which,
  timeout=300)`. `model` defaults to `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`.
- `read(questions)`: relational questions from `packet`.

## The call

One per question:

```
claude -p --tools "" --strict-mcp-config --no-session-persistence
       --safe-mode --setting-sources ""
       --output-format json --model <model> --system-prompt <data system prompt>
```

`--safe-mode` and an empty `--setting-sources` (2026-10-12, an outside audit) keep the
user's and any project's settings out of the call: hooks, CLAUDE.md, skills, plugins, MCP
servers. Without them the user's own hooks ran during every read, with the audited text in
the prompt; a live probe showed a CLAUDE.md canary and three hook events getting through.

with the prompt on stdin (never on the command line): the question, then the
state as a fenced JSON block headed STATE, then the answer cap. The working
directory is a new empty temporary folder (no CLAUDE.md), removed afterwards.

## Outputs

One dict per question, in order:

- answered: `qid`, `backend` `claude-cli`, `model` (the first `modelUsage` key the
  CLI reports, else the requested model), `answer` (the CLI's `result`, verbatim,
  cut at `answer_cap` characters), `capped` (bool), `request` (the command
  without the system prompt text, plus the prompt), `response` (the parsed CLI
  JSON).
- skipped: `claude-cli: not installed`; `claude-cli: authentication error` (the
  output mentions login, authentication, an API key, or 401; stops further
  calls, the rest skip with the same reason); `claude-cli: timeout`;
  `claude-cli: error: <short text>` (non-zero exit, unparseable output, or
  `is_error`).

## Must never

- Give the model tools, MCP servers, or a session that persists.
- Load the user's or a project's settings: hooks must not run, and no CLAUDE.md, skill, or
  plugin may reach the model.
- Put the question or state on the command line, or run in a folder with files.
- Try to log in, or raise on a CLI failure.

## Done when (each backed by a test in `tests/test_back_claude.py`)

1. With a stub runner, the command holds `-p`, `--tools ""`,
   `--strict-mcp-config`, `--no-session-persistence`, `--safe-mode`,
   `--setting-sources ""`, `--output-format json`,
   `--model`, `--system-prompt`; the question and state go on stdin, not argv; the
   working directory is empty at call time.
2. A success result gives the answer verbatim and the reported model; an answer
   over the cap is cut and marked `capped`.
3. An auth error on the first call skips every question after one call; a timeout
   or `is_error` skips only its question; a missing CLI skips all without a call.
4. Live, opt-in (`WALKDOWN_LIVE_CLAUDE=1`, `tests/test_claude_isolation_live.py`): in a folder
   with a canary CLAUDE.md and project hooks that write marker files, the call without the
   isolation flags lets the leak through (proof the probe sees one), and the command this
   module builds lets neither through.

## Added 2026-09-30: labeling

`label(questions)`: the label question, the five options with `what` / `not_for` /
`examples`, and the state, same flags and empty folder as `read`; asks for JSON only
(`{"label", "confidence"}`). A reply with no parsable JSON, an unknown label, or no
numeric confidence is a skip (`claude-cli: unparseable label answer`). `probabilities`
is `{label: confidence}` and `confidence_kind` is `self-reported`. Runs
`WALKDOWN_SOFT_CLAUDE_WORKERS` calls at a time (default 4). Test:
`test_label_parses_json_and_records_self_reported_confidence`.
