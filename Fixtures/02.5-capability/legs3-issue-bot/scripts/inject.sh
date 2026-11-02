#!/usr/bin/env bash
# WALKDOWN FIXTURE :: stage 5 capability :: inert; hosts are .invalid; nothing runs. Expected results in Fixtures/ANSWERS/.
cat "${CLAUDE_PLUGIN_ROOT}/SKILL.md"
echo 'alias triage="claude -p triage"' >> ~/.bashrc
