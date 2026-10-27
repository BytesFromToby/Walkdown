---
name: needs-repo
description: Summarizes the open pull requests. Use when the user asks what is waiting for review.
compatibility: Requires git
---

# Pull request summary

Make sure the list is short.

```bash
git status
python scripts/fetch.py
pbcopy < summary.txt
```

Read references\guide.md for the format.

Use `gh pr list` to see what is open.
