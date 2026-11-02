"""A stand-in for the TypeSafe SDK that ends the process the moment anything imports it.

The root `conftest.py` puts this folder first on `sys.path` and on PYTHONPATH for the whole test session (`tests/offline/
offline_env.py`), so an import of `typesafe_sdk` in the test process, or in a stage a test starts as a subprocess, ends here and
never in the real package. A regression that reached for the client stops here, loudly, and never sends a word to a model: the stub makes
no network call and has no client to give.

- In a process that is not running a test (a stage a test started as a subprocess, a `python -c`): one line on stderr and exit code 97,
  which no `except Exception` can catch.
- In a test (pytest is running one): the import raises `WallBreach`, a `BaseException`, so no `except Exception` and no `except
  ImportError` (the jev backend's "typesafe_sdk not installed") can swallow it; pytest fails that test and shows the line. Ending the
  pytest process instead would lose it, since pytest holds a test's stderr, and the session with it.
- At collection (a test module that imports the SDK at the top): the same line and exit 97.

A test that wants a client puts a fake of its own in `sys.modules` or passes its own `client_factory`."""
import os
import sys

MESSAGE = "typesafe_sdk was imported by a test that must not call a model (tests/offline)\n"


class WallBreach(BaseException):
    """The test wall was reached for a model: the SDK was imported by a test that must not call one."""


sys.stderr.write(MESSAGE)
sys.stderr.flush()
if "pytest" in sys.modules and os.environ.get("PYTEST_CURRENT_TEST"):
    raise WallBreach(MESSAGE.strip())
try:  # no test to fail: say it on the console too, where there is one (a pytest collection holds stderr), and end the process
    with open("CONOUT$" if os.name == "nt" else "/dev/tty", "w") as _console:
        _console.write(MESSAGE)
except OSError:
    pass
os._exit(97)
