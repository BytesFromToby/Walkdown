"""Tests for packages.py, written from specs/shared.SPEC.md, packages."""
import ast
import re
import sys
from importlib import metadata
from pathlib import Path

import packages
import pytest
import steperror

ROOT = Path(__file__).resolve().parents[3]
STAGES = ROOT / "stages"


def third_party_imports() -> set[str]:
    """The top-level names the stages import that are neither the standard library nor Walkdown's own modules."""
    local = {p.stem for p in STAGES.rglob("*.py")} | {p.name for p in STAGES.rglob("*") if p.is_dir()} | {"walkdown"}
    found = set()
    for path in STAGES.rglob("*.py"):
        if {"tests", "__pycache__"} & set(path.parts):
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module.split(".")[0]]
            else:
                continue
            found |= {n for n in names if n not in sys.stdlib_module_names and n not in local and n != "__future__"}
    return found


def test_the_list_is_exactly_the_third_party_modules_the_stages_import():
    """Not a list kept by hand: a module a stage starts to import must be added, and one it stops importing must go."""
    assert set(packages.OWN_MODULES) == third_party_imports()
    assert "pytest" not in packages.OWN_MODULES  # no stage imports it
    assert len(set(packages.OWN_MODULES)) == len(packages.OWN_MODULES)
    assert packages.OWN_MODULES == (*packages.CORE_MODULES, *packages.OPTIONAL_MODULES)


def test_the_core_modules_are_requirements_txts_packages_less_pytest():
    wanted = set()
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        m = re.match(r"([A-Za-z0-9._-]+)==", line)
        if m and m.group(1).lower() != "pytest":
            wanted.add(re.sub(r"[-_.]+", "-", m.group(1)).lower())
    owners = metadata.packages_distributions()
    try:
        have = {re.sub(r"[-_.]+", "-", d).lower() for mod in packages.CORE_MODULES for d in owners[mod]}
    except KeyError:
        pytest.skip("a core package is not installed in this environment")
    assert have == wanted


def test_the_front_door_and_the_account_of_a_crash_read_this_one_list():
    assert steperror.OWN_MODULES is packages.OWN_MODULES
    src = (ROOT / "walkdown.py").read_text(encoding="utf-8")
    assert "from packages import CORE_MODULES" in src and "CORE_MODULES = (" not in src
