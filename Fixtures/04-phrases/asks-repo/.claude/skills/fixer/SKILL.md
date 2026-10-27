---
name: fixer
description: Fixes failing tests. Use when the build is red.
---

# Fixer

Run the tests with `python -m pytest -q`.
Write the fix to the file that fails.
Fetch the error page at https://example.invalid/errors.
Search the web for the error message.
Dispatch a subagent to check each module.
Use the `WebFetch` tool for pages.
Writing clearly matters here.
Repeat until the tests pass.

Retry until it passes, at most 3 times.

Keep fixing until the build is green.
Give up after two tries and report.
