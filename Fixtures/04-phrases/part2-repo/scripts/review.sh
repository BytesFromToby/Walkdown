#!/bin/sh
# WALKDOWN FIXTURE :: stage 4 part 2, settings that restrict tools (review C32) :: inert; nothing runs.
claude -p --tools "Read,Grep,Glob" --output-format json "$PROMPT"
claude -p --tools Read,Bash --output-format json "$PROMPT"
claude -p --tools "" --system-prompt "$SYS"
codex exec --sandbox read-only "$TASK"
codex exec --sandbox danger-full-access "$TASK"
claude -p --disallowedTools "Write,Edit,MultiEdit,NotebookEdit,Bash" "$PROMPT"
claude -p --permission-mode plan "$PROMPT"
claude -p --allowedTools "Read,Grep" "$PROMPT"
# Read the --tools section of the CLI docs before changing these flags.
