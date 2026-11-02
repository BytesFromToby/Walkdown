"""Claude through the Claude Code CLI, with no tools: a text model for Sweep and Pinpoint.
Spec: specs/shared.SPEC.md, back_claude. Never logs in; an error is a skip.
A call that gets no answer is tried once more after a short wait (M9); the tries, the stop on a rejected login, and the workers
are `textmodel`'s."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time

import calllog  # stages/_shared (the runner puts it on the path)
import textmodel
import usage as usage_mod

NAME = "claude-cli"
REMOTE = True
DEFAULT_MODEL = "sonnet"
MODEL_ENV = "WALKDOWN_SOFT_CLAUDE_MODEL"
WORKERS_ENV = "WALKDOWN_SOFT_CLAUDE_WORKERS"
DEFAULT_WORKERS = 4
_AUTH = re.compile(r"\blog ?in\b|/login|authenticat|api key|\b401\b|unauthori[sz]ed|"
                   r"oauth token|credential", re.I)


def workers_from(environ=None) -> int:
    """The calls at a time: `WALKDOWN_SOFT_CLAUDE_WORKERS` when it is a whole number above 0, else 4."""
    text = (os.environ if environ is None else environ).get(WORKERS_ENV, "")
    return int(text) if text.strip().isdigit() and int(text) > 0 else DEFAULT_WORKERS


class ClaudeCLI(textmodel.TextModel):
    name = NAME
    remote = REMOTE

    def __init__(self, data, model=None, runner=subprocess.run, which=shutil.which, timeout=300, sleep=time.sleep,
                 workers=None):
        """`model`: the model the person named (`--sweep claude-cli:opus`), else `WALKDOWN_SOFT_CLAUDE_MODEL`, else `sonnet`."""
        super().__init__(data, model or os.environ.get(MODEL_ENV) or DEFAULT_MODEL, sleep,
                         workers_from() if workers is None else workers)
        self.runner = runner
        self.which = which
        self.timeout = timeout
        self.exe = None
        self.cost_usd = 0.0
        self._cost = threading.Lock()

    def command(self, exe: str, system: str) -> list[str]:
        # --safe-mode and no setting sources (2026-10-12, an outside audit): without them the
        # user's own hooks ran during every read, with the audited text in the prompt, and a
        # CLAUDE.md reached the model. Auth and model selection still work in safe mode.
        return [exe, "-p", "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                "--safe-mode", "--setting-sources", "",
                "--output-format", "json", "--model", self.model,
                "--system-prompt", system]

    def prepare(self) -> str | None:
        self.exe = self.which("claude")
        return None if self.exe else "claude-cli: not installed"

    def request(self, item) -> dict:
        """The command with a placeholder for the system text (`item["label"]` names where it is in the data), and the
        prompt that goes on stdin."""
        cmd = self.command(self.exe, item["system"])
        shown = cmd[:cmd.index("--system-prompt") + 1] + [f"<{item.get('label') or 'system prompt'}>"]
        return {"command": shown, "stdin": item["prompt"]}

    def call(self, system: str, prompt: str) -> tuple:
        """One call: (the reply, None) or (None, the failure, `calllog.failure`)."""
        cmd = self.command(self.exe, system)
        with tempfile.TemporaryDirectory(prefix="walkdown-claude-") as empty:
            try:
                p = self.runner(cmd, input=prompt.encode("utf-8"), cwd=empty,
                                capture_output=True, timeout=self.timeout)
            except subprocess.TimeoutExpired:
                return None, calllog.failure("timeout", None, "claude-cli: timeout")
            except OSError as exc:
                kind = type(exc).__name__  # the class only: the error's text can name a path
                return None, calllog.failure(kind, None, f"claude-cli: error: {kind}")
        out = (p.stdout or b"").decode("utf-8", "replace")
        err = (p.stderr or b"").decode("utf-8", "replace")
        try:
            doc = json.loads(out)
        except ValueError:
            doc = None
        # The tokens the reply says were spent, an error reply's too: they were spent (M1 fix 5).
        used = doc.get("usage") if isinstance(doc, dict) and isinstance(doc.get("usage"), dict) else {}
        spent = usage_mod.clean({"input": used.get("input_tokens"), "output": used.get("output_tokens"),
                                 "cache_write": used.get("cache_creation_input_tokens"),
                                 "cache_read": used.get("cache_read_input_tokens")})
        text = doc.get("result") if isinstance(doc, dict) else None
        failed = p.returncode != 0 or not isinstance(doc, dict) or doc.get("is_error") \
            or not isinstance(text, str)
        if failed:
            blob = " ".join(str(x) for x in (text, out if doc is None else "", err) if x)
            response = doc if doc is not None else {"stdout": out[-500:]}
            # The output is read to tell a rejected login from another error and is never kept as a reason: it can repeat
            # the prompt or the model's own words. What is kept is the kind and the program's exit code.
            code = p.returncode
            if _AUTH.search(blob):
                return None, calllog.failure("authentication", code, "claude-cli: authentication error",
                                             auth=True, response=response, usage=spent)
            return None, calllog.failure("error", code, f"claude-cli: error{calllog.status_text(code, 'exit code')}",
                                         response=response, usage=spent)
        cost = doc.get("total_cost_usd")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            with self._cost:
                self.cost_usd += float(cost)
        by_model = doc.get("modelUsage") if isinstance(doc.get("modelUsage"), dict) else {}
        return {"text": text, "model": next(iter(by_model), None) or doc.get("model"), "usage": spent,
                "response": doc}, None
