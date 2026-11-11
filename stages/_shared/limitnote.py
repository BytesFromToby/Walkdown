"""Which of a step's messages name something the run did not examine. Spec: specs/shared.SPEC.md, limitnote.

A step says what it skipped or could not see in its messages (`data/<step>.notes.txt`). The check of the run (`05-qa`)
keeps the messages that name a limit as limits of the run; the report stage's "What this run covered" list picks
from the same messages. They share this one pattern, so a message is a limit to both or to neither.
"""
from __future__ import annotations

import re

LIMIT_NOTE = re.compile(r"limit|absent|not installed|not scanned|not built|incomplete|skipped|"
                        r"unknown|not examined|not run|carried forward", re.I)
