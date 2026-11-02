"""Loaded by a Python process a test starts with the environment it inherits (this folder is first on its PYTHONPATH).

It does the one part of the wall that an environment cannot: a model key is not read from the Windows user environment in the
registry, so `back_jev.read_key` in a real stage that a test starts finds the same nothing it finds in the test's own process
(`offline_env.block_registry`). It then runs the next `sitecustomize` on the path, if there is one (a guard a verifier put there)."""
import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    _load(os.path.join(os.path.dirname(_HERE), "offline_env.py"), "walkdown_offline_env").block_registry()
except Exception:  # a process that cannot load it still has the stub and the PATH; it is not the wall's to stop it starting
    pass

for _dir in sys.path:
    _next = os.path.join(_dir or os.curdir, "sitecustomize.py")
    if os.path.abspath(os.path.dirname(_next)) != _HERE and os.path.isfile(_next):
        try:
            _load(_next, "sitecustomize_next")
        except Exception:
            pass
        break
