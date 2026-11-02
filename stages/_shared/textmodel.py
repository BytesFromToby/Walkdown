"""The calls every model backend makes alike, and the contract of a text model. Spec: specs/shared.SPEC.md, textmodel.

A model step asks one question for each passage. Whatever answers it (Jev or the Claude Code command), the steps around the call are the same, and are written here once: the first call runs alone, so a key that is rejected
stops every later call; the rest run in a pool of workers; a call that gets no answer is tried once more (`calllog.attempt`); a
passage whose call was never made is skipped as `not sent`; the tokens each call reports are added up (`usage.Tally`); and a
long read says it is working.

`Backend` is that part. A backend sets `name`, `remote`, and `model`, and supplies `prepare`, `once`, and `request`. `TextModel`
is the contract for a model that takes a system text and a prompt and gives back text: a backend supplies `call(system, prompt)`,
which returns the text, the model that answered, and its usage, or a `calllog.failure`. Jev answers with typed probabilities from
fixed options, so it is a `Backend` and not a `TextModel`.
"""
from __future__ import annotations

import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import calllog  # noqa: E402
import options  # noqa: E402
import stagenote  # noqa: E402
import usage as usage_mod  # noqa: E402

PROGRESS_EVERY = 25  # a long read says it is working after this many passages


class Progress:
    """Counts the passages a read has finished, and says so every `PROGRESS_EVERY` of them (`stagenote.progress`)."""

    def __init__(self, who: str | None, total: int):
        self.who, self.total, self.done = who, total, 0
        self._lock = threading.Lock()

    def tick(self) -> None:
        with self._lock:
            self.done += 1
            if self.who and self.done % PROGRESS_EVERY == 0:
                stagenote.progress(self.who, self.done, self.total)


class Backend:
    """One model step's calls. `ask(items)` returns one result for each item, in order. An item is a dict with a `qid`, and
    whatever `once` and `request` need. A result is the item's `qid`, the `backend`, the `request`, and either the answered
    fields (`model` and what `once` returned) or `skipped` with the reason, and `tries` when the first try got no answer or the
    call was not made (`calllog`). A backend supplies:

    - `prepare() -> str | None`: the reason nothing can be called (no key, a package or a program missing), else None. The
      client is built here, once. Nothing is tried again for it.
    - `once(item) -> (fields, None) | (None, failure)`: one call and what is made of its answer. `failure` is
      `calllog.failure(...)`; it holds a kind and a status, never an error's own text. Tokens the call reported ride on either
      as `usage` (`usage.clean`) and are added up here.
    - `request(item) -> dict`: exactly what is sent for the item, with no key in it.
    """
    name: str
    remote: bool
    model: str | None = None

    def __init__(self, data, sleep=time.sleep, workers=1):
        self.wait = data["retry_wait"]  # seconds before the second try of a call that got no answer
        self.sleep = sleep
        self.workers = max(1, int(workers))
        self.usage = usage_mod.Tally()
        self._stop = None  # the reason later calls are not made (a rejected key)

    def prepare(self) -> str | None:
        raise NotImplementedError

    def once(self, item) -> tuple:
        raise NotImplementedError

    def request(self, item) -> dict:
        raise NotImplementedError

    def answered_by(self, reported) -> str:
        """The model that answered, as a result keeps it (M1 fix 7). The name comes from a service, and a service can put a tag, a
        link, or a line break in it, which would reach `full.md` and `LOG.md`. A name that passes the model-name rule
        (`options.bad_model`: ASCII letters, digits, and `. _ : / @ + - [ ]`, at most 200 characters, no `//`) is kept, cut to
        `stagenote.MODEL_CAP`. Any other, or none, is not shown: the record keeps the model that was asked for (`self.model`; a backend
        always has one, `ClaudeCLI` the `sonnet` it runs when the person named none)."""
        if isinstance(reported, str) and reported and options.bad_model(reported) is None:
            return stagenote.flat(reported, cap=stagenote.MODEL_CAP)
        return self.model

    def ask(self, items, who: str | None = None) -> list[dict]:
        """Every item asked, the first alone and then `workers` at a time. `who` names the step in its progress lines."""
        items = list(items)
        if not items:
            return []
        why = self.prepare()
        if why:  # nothing to call: no call is made and none is tried again
            return [{"qid": i["qid"], "backend": self.name, "skipped": why, "tries": calllog.unsent(why)} for i in items]
        progress = Progress(who, len(items))
        out = [self._one(items[0], progress)]  # the first call runs alone, so a rejected key stops every later call
        rest = items[1:]
        if self.workers == 1 or len(rest) < 2:
            out += [self._one(i, progress) for i in rest]
        else:
            with ThreadPoolExecutor(self.workers) as pool:
                out += list(pool.map(lambda i: self._one(i, progress), rest))
        return out

    def _try(self, item) -> tuple:
        """One call, with the tokens it reported added to the tally. Every call counts, an answer or not."""
        got, fail = self.once(item)
        self.usage.add((got if fail is None else fail).pop("usage", None))
        return got, fail

    def _one(self, item, progress: Progress) -> dict:
        request = self.request(item)
        base = {"qid": item["qid"], "backend": self.name}
        if self._stop:
            out = {**base, "skipped": f"not sent: {self._stop}", "request": request, "tries": calllog.unsent(self._stop)}
        else:
            ans, fail, tries = calllog.attempt(lambda: self._try(item), self.wait, self.sleep, lambda: self._stop)
            extra = {"tries": tries} if tries else {}
            if fail is None:
                out = {**base, **ans, "request": request, **extra}
            else:
                if fail["auth"]:  # rejected on the last try: each later call would fail the same way
                    self._stop = fail["reason"]
                if "answer" in fail:  # an answer that could not be read, kept as it came
                    out = {**base, **fail["answer"], "request": request, **extra}
                else:
                    out = {**base, "skipped": fail["reason"], "request": request,
                           **({"response": fail["response"]} if "response" in fail else {}), **extra}
        progress.tick()
        return out


def plain_answer(text: str) -> tuple:
    """The default `accept`: the text is the answer."""
    return {"answer": text}, None


class TextModel(Backend):
    """A backend for a model that takes a system text and a prompt and gives back text. It supplies
    `call(system, prompt) -> (reply, None) | (None, failure)`, with `reply` a dict of `text` (a string), `model` (the model
    that answered, as the service named it), `usage` (`usage.clean`, whole numbers only), and `response` (what came back, kept
    in the answers file). An item is `{"qid", "system", "prompt"}`.

    `ask(items, accept)`: `accept(text)` turns the answer into the fields the step wants, `(fields, None)`, or says it cannot
    be used, `(None, calllog.failure(...))`: a call with no answer, tried once more like any other. A failure may carry
    `answer`, fields to keep as they came if the second try is no better. With no `accept` the text is `answer`. The model
    that answered is a value from a service, so it is kept only if it passes the model-name rule (`Backend.answered_by`); else
    the model asked for is."""

    def __init__(self, data, model=None, sleep=time.sleep, workers=1):
        super().__init__(data, sleep, workers)
        self.model = model
        self._accept = plain_answer

    def call(self, system: str, prompt: str) -> tuple:
        raise NotImplementedError

    def ask(self, items, accept=None, who: str | None = None) -> list[dict]:
        self._accept = accept or plain_answer
        return super().ask(items, who)

    def once(self, item) -> tuple:
        reply, fail = self.call(item["system"], item["prompt"])
        if fail is not None:
            return None, fail
        model = self.answered_by(reply.get("model"))
        spent = reply.get("usage")
        fields, bad = self._accept(reply["text"])
        if bad is None:
            return {"model": model, **fields, "response": reply.get("response"), "usage": spent}, None
        if "answer" in bad:
            bad["answer"] = {"model": model, **bad["answer"], "response": reply.get("response")}
        else:
            bad.setdefault("response", reply.get("response"))
        return None, {**bad, "usage": spent}
