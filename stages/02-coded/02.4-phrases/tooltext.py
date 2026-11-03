"""Text a model reads inside MCP server code: tool, prompt, and parameter descriptions. Spec: specs/phrases.SPEC.md, tooltext.

A file of code is read by tools (`audience`), so a phrase hit in it counts as not read by a model. An MCP server's code is the
exception that matters: the description of each tool, prompt, resource, and parameter it declares is sent to the model as it
stands, and an instruction hidden there is an instruction to the model (SkillSpector TP1 and TP3, 2026-11-03). This module
finds those strings by their line numbers; `run.tool_text_scan` scans those lines as text a model reads.

Only a file that imports an MCP library is read this way (`is_mcp_code`). Python is read with `ast`; JavaScript and TypeScript
with a small tokenizer that knows strings, comments, and brackets, and nothing of the language beyond that. It reads no code
it is not given, runs nothing, and keeps no text: only line numbers.
"""
from __future__ import annotations

import ast
import re

PY_EXTS = ("py",)
JS_EXTS = ("js", "mjs", "cjs", "ts", "mts", "cts")
GO_EXTS = ("go",)
PY_MCP = re.compile(r"^\s*(?:from|import)\s+(?:mcp|fastmcp)\b", re.M)
JS_MCP = re.compile(r"""@modelcontextprotocol/sdk|\bfrom\s+["']fastmcp["']|\brequire\(\s*["']fastmcp["']\s*\)""")
# The official Go SDK and mcp-go, imported by path (2026-11-03).
GO_MCP = re.compile(r'"github\.com/(?:modelcontextprotocol/go-sdk|mark3labs/mcp-go)/(?:mcp|server)"')
# A Go struct tag that gives a schema field its description: the official SDK's `jsonschema:"..."`, invopop's
# `jsonschema_description:"..."`. The field's description goes into the tool's input or output schema.
GO_SCHEMA_TAG = re.compile(r'\bjsonschema(?:_description)?:"')
# A key, keyword, or field whose value a client shows the model.
TEXT_KEYS = {"description", "title"}
# Methods whose string arguments are a description: zod's `.describe(...)`; mcp-go's `mcp.WithDescription(...)`,
# `mcp.Description(...)`, `mcp.WithTitleAnnotation(...)`, and the prompt, argument, resource, and template forms. A plain call
# is not one: a test suite's `describe(...)`.
TEXT_CALLS = {"describe", "withdescription", "description", "withtitleannotation", "withpromptdescription",
              "argumentdescription", "withresourcedescription", "withtemplatedescription"}
# Calls that declare a tool, prompt, or resource with positional strings: `server.tool("name", "description", ...)`.
DECLARE_CALLS = {"tool", "prompt", "resource"}
# Python decorators whose function's docstring is the description (FastMCP: `@mcp.tool()`, `@mcp.prompt`, `@mcp.resource(...)`).
DECORATORS = {"tool", "prompt", "resource"}


def _ext(rel: str) -> str:
    base = rel.rsplit("/", 1)[-1].lower()
    return base.rsplit(".", 1)[1] if "." in base else ""


def is_mcp_code(rel: str, text: str) -> bool:
    """Whether a file is code that imports an MCP library, so its declarations' descriptions go to a model."""
    ext = _ext(rel)
    if ext in PY_EXTS:
        return bool(PY_MCP.search(text))
    if ext in JS_EXTS:
        return bool(JS_MCP.search(text))
    if ext in GO_EXTS:
        return bool(GO_MCP.search(text))
    return False


def tool_text_lines(rel: str, text: str) -> set[int]:
    """The lines of an MCP code file that hold text a model reads, or an empty set for any other file or code that does not
    parse."""
    if not is_mcp_code(rel, text):
        return set()
    ext = _ext(rel)
    return _python(text) if ext in PY_EXTS else _go(text) if ext in GO_EXTS else _js(text)


# ---------------------------------------------------------------- Python

def _span(node) -> set[int]:
    return set(range(node.lineno, (getattr(node, "end_lineno", None) or node.lineno) + 1))


def _strings(node) -> set[int]:
    """The lines of every string literal inside an expression: a constant, an f-string, a concatenation, or a call that wraps
    one (`t("KEY", "default text")`)."""
    out: set[int] = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) or isinstance(n, ast.JoinedStr):
            out |= _span(n)
    return out


def _decorated(fn) -> bool:
    for d in fn.decorator_list:
        target = d.func if isinstance(d, ast.Call) else d
        name = target.attr if isinstance(target, ast.Attribute) else target.id if isinstance(target, ast.Name) else None
        if name in DECORATORS:
            return True
    return False


def _python(text: str) -> set[int]:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return set()
    out: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _decorated(node):
            first = node.body[0] if node.body else None
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                out |= _span(first.value)
        elif isinstance(node, ast.Call):
            out |= {n for kw in node.keywords if kw.arg in TEXT_KEYS for n in _strings(kw.value)}
        elif isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str) and k.value.lower() in TEXT_KEYS:
                    out |= _strings(v)
    return out


# ---------------------------------------------------------------- JavaScript and TypeScript

_IDENT = re.compile(r"[A-Za-z_$][\w$]*")


def _tokens(text: str, raw_backtick: bool = False) -> list[tuple]:
    """(kind, value, first line, last line): kind is `str`, `id`, or `p` (one punctuation character). Comments and white
    space are dropped. A template literal is one string; what is inside `${...}` is not read apart from it. `raw_backtick`:
    a backtick string has no escapes (Go's raw string), so a backslash in it is a character."""
    out, i, line, n = [], 0, 1, len(text)
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
        elif c.isspace():
            i += 1
        elif text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            j = n if j < 0 else j + 2
            line += text.count("\n", i, j)
            i = j
        elif c in "\"'`":
            j, start = i + 1, line
            while j < n and text[j] != c:
                if text[j] == "\\" and not (raw_backtick and c == "`"):
                    j += 1
                elif text[j] == "\n":
                    if c != "`":
                        break  # an unclosed quote ends at its line, as the language has it
                    line += 1
                j += 1
            out.append(("str", text[i + 1:j], start, line))
            i = j + 1
        else:
            m = _IDENT.match(text, i)
            if m:
                out.append(("id", m.group(0), line, line))
                i = m.end()
            else:
                out.append(("p", c, line, line))
                i += 1
    return out


def _value(toks, i) -> tuple[set[int], int]:
    """The lines of the strings in the expression that starts at `i`, up to a `,` or `;` at its own depth or the bracket
    that closes around it; and where it ends."""
    out: set[int] = set()
    depth = 0
    while i < len(toks):
        kind, val, a, b = toks[i]
        if kind == "p" and val in "([{":
            depth += 1
        elif kind == "p" and val in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif kind == "p" and val in ",;" and depth == 0:
            break
        elif kind == "str":
            out |= set(range(a, b + 1))
        i += 1
    return out, i


def _args(toks, i) -> list[tuple[set[int], bool]]:
    """Each argument of the call whose `(` is at `i`: the lines of its strings, and whether it is one string literal and
    nothing else."""
    args, i = [], i + 1
    while i < len(toks):
        start = i
        lines, i = _value(toks, i)
        args.append((lines, i - start == 1 and toks[start][0] == "str"))
        if i >= len(toks) or toks[i][1] != ",":
            break
        i += 1
    return args


def _js(text: str) -> set[int]:
    return _c_like(_tokens(text))


def _go(text: str) -> set[int]:
    """Go: the rules of `_c_like` (a `Description:` or `Title:` field of a struct literal, the official SDK's form; mcp-go's
    `mcp.WithDescription(...)` and its kin), and a struct tag that describes a schema field (`GO_SCHEMA_TAG`)."""
    toks = _tokens(text, raw_backtick=True)
    out = _c_like(toks)
    for kind, val, a, b in toks:
        if kind == "str" and GO_SCHEMA_TAG.search(val):
            out |= set(range(a, b + 1))
    return out


def _c_like(toks) -> set[int]:
    out: set[int] = set()
    for i, (kind, val, _, _) in enumerate(toks):
        nxt = toks[i + 1][1] if i + 1 < len(toks) and toks[i + 1][0] == "p" else None
        name = val.lower() if kind in ("id", "str") else None
        if name in TEXT_KEYS and nxt in (":", "="):
            out |= _value(toks, i + 2)[0]
        elif kind == "id" and nxt == "(" and name in TEXT_CALLS and i > 0 and toks[i - 1][1] == ".":  # a method: not a test's describe()
            out |= {n for lines, _ in _args(toks, i + 1) for n in lines}
        elif kind == "id" and nxt == "(" and name in DECLARE_CALLS and i > 0 and toks[i - 1][1] == ".":
            args = _args(toks, i + 1)  # `server.tool("name", "description", schema, handler)`: a plain string after the name
            out |= {n for lines, plain in args[1:2] if plain for n in lines}
    return out
