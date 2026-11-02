"""A test that reaches for the SDK, and one that does not, for `tests/test_the_wall.py`: run in a pytest session of its own on a fake
machine, the first must fail (with the wall's line, not an exit that loses it) and the second must still run. The file is not named
`test_*.py`, so a normal run does not collect it."""
import importlib


def test_a_test_that_imports_the_sdk_fails_loudly():
    try:
        importlib.import_module("typesafe_sdk")
    except Exception:  # the jev backend's own habit: `except ImportError` and `except Exception` must not hide it
        pass


def test_the_next_test_still_runs():
    assert True
