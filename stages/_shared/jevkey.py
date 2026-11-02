"""Jev's key, and whether Jev is available. Spec: specs/shared.SPEC.md, jevkey.

`read_key` moved here from `stages/03-sweep/back_jev.py` (`back_jev.read_key` is this function), so that `options` can ask
whether Jev is available without importing a stage. The key is read in the process that asks, and is never printed, logged, or
stored. `has_key` and `available` return a bool and nothing else, and send nothing: the check is a question about the machine.
"""
from __future__ import annotations

import importlib.util
import os
import sys

KEY_NAME = "TYPESAFE_API_KEY"
PACKAGE = "typesafe_sdk"


def _registry_value():
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
        return winreg.QueryValueEx(k, KEY_NAME)[0]


def read_key(environ=None, registry=None) -> str | None:
    """The key from the environment, else from the user environment in the Windows registry; None when neither has it."""
    env = os.environ if environ is None else environ
    v = env.get(KEY_NAME)
    if v:
        return v
    try:
        v = (registry or _registry_value)()
    except Exception:
        return None
    return v or None


def has_key(environ=None, registry=None) -> bool:
    """Whether there is a key. True or False, never the key."""
    return read_key(environ, registry) is not None


def sdk_found() -> bool:
    """Whether the package is there to be imported, asked of the import system and never by importing it. A module already in
    `sys.modules` is found; a None entry there (an import that is blocked) is not."""
    if PACKAGE in sys.modules:
        return sys.modules[PACKAGE] is not None
    try:
        return importlib.util.find_spec(PACKAGE) is not None
    except (ImportError, ValueError):
        return False


def available(environ=None, registry=None, sdk=sdk_found) -> bool:
    """Whether Jev is available: the package is found and there is a key. The package is asked first, so a machine without it reads
    no key. True or False, never the key."""
    return bool(sdk()) and has_key(environ, registry)
