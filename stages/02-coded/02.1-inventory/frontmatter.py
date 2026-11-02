"""Frontmatter: descriptions and granted tools. Spec: specs/inventory.SPEC.md, frontmatter."""
from __future__ import annotations

import re
from dataclasses import dataclass

import yaml

import spans

MARKDOWN_EXTS = {"md", "markdown", "mdx", "mdc"}
TOOL_KEYS = ("tools", "allowed-tools", "allowedTools")
_KEY_LINE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*):(?:\s+(.*))?$")
_SPLIT_WS = re.compile(r"\s+(?![^()]*\))")


@dataclass
class Frontmatter:
    lines: list[str]
    yaml: dict | None
    yaml_error: str | None
    first_colon: dict
    start_line: int = 1

    def key_line(self, key: str) -> int | None:
        for i, line in enumerate(self.lines):
            if line.startswith(key + ":"):
                return self.start_line + 1 + i
        return None

    def where(self, *keys: str) -> list[int] | None:
        """[first line, last line] of these keys' values in the file (`spans`): a block value runs past its key's line. When the
        YAML did not parse the words come from a line a parser cannot place, and its error quotes one, so it is the whole
        frontmatter. None when the frontmatter has none of the keys."""
        whole = [self.start_line + 1, self.start_line + len(self.lines)]
        if self.yaml is None:
            return whole if any(k in self.first_colon for k in keys) or self.yaml_error else None
        if not any(k in self.yaml for k in keys):
            return None
        root = spans.compose("\n".join(self.lines))
        found = []
        for key in keys:
            k, v = spans.pair(root, key)
            if v is not None:
                found.append(spans.span(v, key=k, offset=self.start_line))
        return [min(f[0] for f in found), max(f[1] for f in found)] if found else whole


def _unquote(v: str) -> str:
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def parse(text: str) -> Frontmatter | None:
    lines = text.split("\n")
    if not lines or lines[0].rstrip() != "---":
        return None
    body = None
    for i in range(1, len(lines)):
        if lines[i].rstrip() in ("---", "..."):
            body = [ln.rstrip("\r") for ln in lines[1:i]]
            break
    if body is None:
        return None
    data, err = None, None
    try:
        loaded = yaml.safe_load("\n".join(body))
        if isinstance(loaded, dict):
            data = loaded
        elif loaded is None:
            data = {}
        else:
            err = f"frontmatter is a {type(loaded).__name__}, not a mapping"
    except yaml.YAMLError as e:
        err = str(e).replace("\n", " ")
    colon = {}
    for line in body:
        m = _KEY_LINE.match(line)
        if m and m.group(1) not in colon:
            colon[m.group(1)] = _unquote((m.group(2) or "").strip())
    return Frontmatter(body, data, err, colon)


def _as_text(v) -> str:
    return v if isinstance(v, str) else str(v)


def description_finding(rel: str, fm: Frontmatter) -> dict | None:
    y_has = fm.yaml is not None and "description" in fm.yaml
    c_has = "description" in fm.first_colon
    if not (y_has or c_has):
        return None
    f = {"check": "struct.description", "file": rel, "line": fm.key_line("description"), "span": fm.where("description")}
    if y_has:
        f["text"], f["loader"] = _as_text(fm.yaml["description"]), "yaml"
    else:
        f["text"], f["loader"] = fm.first_colon["description"], "first-colon"
        if fm.yaml_error:
            f["yaml_error"] = fm.yaml_error
    ytext = _as_text(fm.yaml["description"]) if y_has else None
    ctext = fm.first_colon.get("description")
    disagree = (y_has != c_has) or (ytext != ctext)
    f["loaders_disagree"] = disagree
    if disagree and c_has:
        f["first_colon_text"] = ctext
    return f


def _split_tools(v) -> list[str]:
    if isinstance(v, list):
        items = [_as_text(x) for x in v]
    elif isinstance(v, str):
        items = v.split(",") if "," in v else _SPLIT_WS.split(v)
    else:
        items = [_as_text(v)]
    return [x.strip() for x in items if x is not None and x.strip()]


def tools_value(fm: Frontmatter):
    for key in TOOL_KEYS:
        if fm.yaml is not None and key in fm.yaml and fm.yaml[key] is not None:
            return key, _split_tools(fm.yaml[key])
        if fm.yaml is None and key in fm.first_colon:
            return key, _split_tools(fm.first_colon[key])
    return None


def agent_tools_finding(rel: str, fm: Frontmatter, kind: str) -> dict:
    tv = tools_value(fm)
    if fm.yaml is not None and "description" in fm.yaml:
        desc = _as_text(fm.yaml["description"])
    else:
        desc = fm.first_colon.get("description")
    f = {"check": "struct.agent-tools", "file": rel,
         "line": fm.key_line(tv[0]) if tv else None,
         "tools": tv[1] if tv else None, "description": desc,
         "field": tv[0] if tv else None, "kind": kind}
    where = fm.where("description", *([tv[0]] if tv else []))
    if where:
        f["span"] = where
    return f
