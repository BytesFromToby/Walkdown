"""Where a parsed value sits in its file. Spec: specs/inventory.SPEC.md, spans.

The mask of a line the secret scan flags (`stages/_shared/secretmask.py`) goes by the lines a finding quotes, and a parser's value
has lost them: a block description runs over several lines, and a hook or an MCP server has no line at all.
"""
from __future__ import annotations

import re

import yaml

# What YAML takes for a line break or refuses, and every other step reads as part of a line (`readtext.split_lines`). A space keeps
# each line number and each column; only where a value sits is read from this text, never the value.
_NOT_A_BREAK = re.compile(r"\r(?!\n)|[\t\x85  ]")


def compose(text: str | None):
    """The document's nodes, from a text in JSON or YAML, or None when it does not compose: the mask then takes the whole file."""
    if not text:
        return None
    try:
        return yaml.compose(_NOT_A_BREAK.sub(" ", text), Loader=yaml.SafeLoader)
    except (yaml.YAMLError, ValueError, RecursionError):
        return None


def pair(node, step):
    """(key node, value node) of one step down a document: a key of a mapping (the last of a repeated key, as the parsers take it),
    or a position in a list, which has no key node. (None, None) when it is not there."""
    if isinstance(node, yaml.MappingNode):
        hits = [(k, v) for k, v in node.value if isinstance(k, yaml.ScalarNode) and k.value == str(step)]
        return hits[-1] if hits else (None, None)
    if isinstance(node, yaml.SequenceNode) and isinstance(step, int) and 0 <= step < len(node.value):
        return None, node.value[step]
    return None, None


def at(node, *path):
    """The node at a path of keys and list positions, or None."""
    for step in path:
        _, node = pair(node, step)
    return node


def first_line(node) -> int:
    return node.start_mark.line + 1


def last_line(node) -> int:
    """The last line a node reaches. A block's end mark stands at whatever comes next, so with only white space before the mark on
    its line the node ended above it."""
    end = node.end_mark
    before = end.buffer[end.pointer - end.column:end.pointer] if end.buffer is not None else "x"
    return end.line + (1 if before.strip() else 0)


def span(node, key=None, offset: int = 0) -> list[int] | None:
    """[first line, last line] of a node, from its key when one is given; `offset` for a text that starts later in its file. None
    when there is no node."""
    if node is None:
        return None
    first = first_line(key if key is not None else node)
    return [first + offset, max(first, last_line(node)) + offset]
