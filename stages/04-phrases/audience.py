"""Audience tag by path. Spec: specs/audience.SPEC.md."""
from __future__ import annotations

import fnmatch

# changelog / release notes / license added 2026-09-29 (Case 003: CHANGELOG lines were tagged model)
HUMAN_PREFIXES = ("readme", "install", "contributing", "code_of_conduct", "changelog", "changes",
                  "history", "release-notes", "release_notes", "releases", "license", "licence",
                  "notice", "authors", "security",
                  # getting-started guides for people (2026-09-30, Plumbline DIRECTIONS.md)
                  "directions", "usage", "quickstart", "getting_started", "getting-started",
                  "tutorial", "guide", "howto", "how-to", "faq")
HUMAN_DIRS = {"docs", ".github"}
SUBAGENT_DIRS = {"agents", "commands"}
SCRIPT_EXTS = {"py", "sh", "bash", "zsh", "js", "mjs", "cjs", "ts", "ps1", "psm1", "cmd",
               "bat", "rb", "pl"}


# Package, lock, and build configuration: read by tools, never followed by the model
# (2026-09-29, Case 004: package-lock.json made registry.npmjs.org 315 "instructions").
BUILD_FILES = {"package.json", "package-lock.json", "npm-shrinkwrap.json", "yarn.lock",
               "pnpm-lock.yaml", "bun.lock", "bun.lockb", "cargo.toml", "cargo.lock",
               "pyproject.toml", "poetry.lock", "uv.lock", "pipfile", "pipfile.lock", "go.mod",
               "go.sum", "gemfile", "gemfile.lock", "jsconfig.json", "dockerfile", "makefile",
               "renovate.json", ".npmrc", ".nvmrc", ".editorconfig"}
# pattern lists read by git and tools, never followed (2026-09-30, Plumbline .gitignore)
BUILD_FILES |= {".gitignore", ".gitattributes", ".npmignore", ".dockerignore", ".prettierignore",
                ".eslintignore", "codeowners", ".gitmodules", ".mailmap"}
BUILD_GLOBS = ("tsconfig*.json", "eslint.config.*", ".eslintrc*", ".prettierrc*",
               "requirements*.txt", "docker-compose*.yml", "docker-compose*.yaml",
               "vitest.config.*", "jest.config.*", "vite.config.*")


def _build_file(low: str) -> bool:
    return low in BUILD_FILES or any(fnmatch.fnmatch(low, g) for g in BUILD_GLOBS)


# Test data: fixtures and tests that exercise the code, never loaded as instructions when the
# artifact is installed (2026-10-02, Walkdown self-audit: a security tool's own attack samples
# lit every stage). Decided by folder or file name. A test-data file that a model-read file
# references directly is reported by stage 5 as a pair, so the name alone never hides it.
TEST_DIRS = {"test", "tests", "__tests__", "testdata", "test-data", "test_data", "fixture",
             "fixtures", "__fixtures__", "__snapshots__", "spec"}
TEST_FILE_GLOBS = ("test_*.py", "*_test.py", "*_test.go", "*.test.*", "*.spec.js",
                   "*.spec.ts", "*.spec.mjs", "*.spec.tsx", "*.spec.jsx", "conftest.py")


def is_test_data(rel: str) -> bool:
    parts = (rel or "").split("/")
    folders, low = parts[:-1], parts[-1].lower()
    return (any(f.lower() in TEST_DIRS for f in folders)
            or any(fnmatch.fnmatch(low, g) for g in TEST_FILE_GLOBS))


def audience(rel: str, scripts=(), hook_configs=()) -> str:
    parts = rel.split("/")
    folders, base = parts[:-1], parts[-1]
    low = base.lower()
    if is_test_data(rel):
        return "test-data"
    if low.startswith(HUMAN_PREFIXES) or any(f.lower() in HUMAN_DIRS for f in folders):
        return "human"
    if any(f.lower() in SUBAGENT_DIRS for f in folders) or fnmatch.fnmatch(low, "*prompt*.md"):
        return "subagent"
    ext = low.rsplit(".", 1)[1] if "." in low else ""
    if rel in scripts or rel in hook_configs or ext in SCRIPT_EXTS or _build_file(low):
        return "tool"
    return "model"
