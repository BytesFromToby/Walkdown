"""Entry-point kind per file. Spec: specs/entrypoints.SPEC.md."""
from __future__ import annotations

import fnmatch

MARKDOWN_EXTS = (".md", ".markdown", ".mdx", ".mdc")
CI_PATTERNS = (".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml",
               ".circleci/config.yml", "azure-pipelines.yml", ".travis.yml", "Jenkinsfile")


def _is_ci(rel: str) -> bool:
    for pat in CI_PATTERNS:
        if "/" in pat:
            if fnmatch.fnmatchcase(rel, pat) or fnmatch.fnmatchcase(rel, "*/" + pat):
                return True
        elif rel.rsplit("/", 1)[-1] == pat:
            return True
    return False


def classify(rel: str, *, is_symlink: bool, has_tools: bool, is_hook_config: bool,
             is_manifest: bool) -> str | None:
    if is_symlink:
        return None
    parts = rel.split("/")
    base = parts[-1]
    low = base.lower()
    folders = parts[:-1]
    if low == "skill.md" or low.endswith(".skill.md"):
        return "skill"
    if low.endswith(MARKDOWN_EXTS) and (has_tools or "agents" in folders or "commands" in folders):
        return "command" if "commands" in folders else "agent"
    if low == ".mcp.json":
        return "mcp-config"
    if is_hook_config:
        return "hook-config"
    if _is_ci(rel):
        return "ci"
    if is_manifest:
        return "manifest"
    if low.startswith("readme"):
        return "readme"
    if low in PROJECT_INSTRUCTION_NAMES or rel.endswith(".github/copilot-instructions.md") \
            or (".cursor/rules" in rel and low.endswith(MARKDOWN_EXTS)):
        return "project-instructions"
    return None


# Files a harness loads on its own when someone works in the repository
# (2026-09-29, Case 004: backlog's CLAUDE.md read as an orphan).
PROJECT_INSTRUCTION_NAMES = {"claude.md", "claude.local.md", "agents.md", "gemini.md",
                             ".cursorrules", ".windsurfrules", ".clinerules"}
