"""Tests for jevkey.py, written from specs/shared.SPEC.md, jevkey. No test reads the machine's key: every key here is planted
through the environment argument, and the wall (the root `conftest.py`) holds the machine's own away besides."""
import sys
import types
from pathlib import Path

import jevkey

SWEEP = Path(__file__).resolve().parents[2] / "03-sweep"
PLANTED = "planted-key-3c9e51ab-must-not-appear-anywhere"


class Registry:
    """A registry stand-in that says whether it was asked. It does not raise: `read_key` swallows what a registry raises, so a registry
    that raises passes a test whether or not it was asked."""

    def __init__(self, value=None):
        self.value, self.asked = value, 0

    def __call__(self):
        self.asked += 1
        return self.value


class Environment(dict):
    """An environment that says which names were looked up."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.looked = []

    def get(self, key, default=None):
        self.looked.append(key)
        return super().get(key, default)


def test_back_jev_reads_its_key_through_jevkey():
    """The move is one function under two names: the sweep's own tests (`test_read_key_prefers_the_environment_then_the_registry`)
    keep calling `back_jev.read_key`."""
    sys.path.insert(0, str(SWEEP))
    try:
        import back_jev
    finally:
        sys.path.remove(str(SWEEP))
    assert back_jev.read_key is jevkey.read_key and back_jev.KEY_NAME == jevkey.KEY_NAME == "TYPESAFE_API_KEY"
    assert jevkey.read_key({"TYPESAFE_API_KEY": "e"}, registry=lambda: "r") == "e"
    assert jevkey.read_key({}, registry=lambda: "r") == "r"
    assert jevkey.read_key({}, registry=lambda: None) is None
    assert jevkey.read_key({"TYPESAFE_API_KEY": ""}, registry=lambda: "") is None


def test_has_key_and_available_return_a_bool_and_never_the_key():
    for env, registry, has in (({}, lambda: None, False), ({"TYPESAFE_API_KEY": PLANTED}, Registry(), True),
                               ({}, lambda: PLANTED, True), ({}, lambda: (_ for _ in ()).throw(OSError("no value")), False)):
        assert jevkey.has_key(env, registry) is has
        assert jevkey.available(env, registry, sdk=lambda: True) is has
        assert jevkey.available(env, registry, sdk=lambda: False) is False
    seen = Registry()  # a key in the environment is the key: the registry is not asked
    assert jevkey.has_key({"TYPESAFE_API_KEY": PLANTED}, seen) is True and seen.asked == 0


def test_the_key_is_in_no_output_of_the_check(capsys, caplog):
    caplog.set_level(0)
    results = [jevkey.has_key({"TYPESAFE_API_KEY": PLANTED}), jevkey.available({"TYPESAFE_API_KEY": PLANTED}, sdk=lambda: True),
               jevkey.has_key({}, registry=lambda: PLANTED), jevkey.available({}, lambda: PLANTED, sdk=lambda: True)]
    out = capsys.readouterr()
    assert results == [True] * 4
    for seen in (out.out, out.err, caplog.text, repr(results)):
        assert PLANTED not in seen and PLANTED[:12] not in seen


def test_available_needs_the_package_and_a_key():
    key = {"TYPESAFE_API_KEY": PLANTED}
    assert jevkey.available(key, sdk=lambda: True) is True
    assert jevkey.available(key, sdk=lambda: False) is False  # a key and no package
    assert jevkey.available({}, lambda: None, sdk=lambda: True) is False  # the package and no key
    assert jevkey.available({}, lambda: None, sdk=lambda: False) is False


def test_the_package_is_asked_before_the_key_is_read():
    """A machine without the package reads no key: neither the environment nor the registry is looked at. The registry stand-in
    records and does not raise, since `read_key` swallows an exception from the registry."""
    env, registry = Environment(), Registry("a-key")
    assert jevkey.available(env, registry, sdk=lambda: False) is False
    assert env.looked == [] and registry.asked == 0
    assert jevkey.available(env, registry, sdk=lambda: True) is True  # with the package, both are asked, the environment first
    assert env.looked == ["TYPESAFE_API_KEY"] and registry.asked == 1


def test_read_key_asks_the_registry_by_default_and_returns_its_value(monkeypatch):
    """No registry given: `read_key` asks the registry reader of this module (here a stand-in; the real registry is not touched)."""
    seen = Registry("from-the-registry")
    monkeypatch.setattr(jevkey, "_registry_value", seen)
    assert jevkey.read_key({}) == "from-the-registry" and seen.asked == 1
    assert jevkey.has_key({}) is True and seen.asked == 2
    assert jevkey.read_key({"TYPESAFE_API_KEY": "e"}) == "e" and seen.asked == 2  # the environment first
    monkeypatch.setattr(jevkey, "_registry_value", Registry(None))
    assert jevkey.read_key({}) is None


def test_the_registry_reader_asks_the_users_environment_for_the_key_by_name(monkeypatch):
    """`_registry_value` itself, on a stand-in for `winreg`: the real registry is not touched."""
    asked = []

    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def open_key(hive, path):
        asked.append((hive, path))
        return Key()

    def query(_key, name):
        asked.append(name)
        return "a-value", 1
    monkeypatch.setitem(sys.modules, "winreg", types.SimpleNamespace(HKEY_CURRENT_USER="the-user", OpenKey=open_key, QueryValueEx=query))
    assert jevkey._registry_value() == "a-value"
    assert asked == [("the-user", "Environment"), "TYPESAFE_API_KEY"]


def test_the_package_is_looked_for_and_never_imported(tmp_path, monkeypatch):
    """A module of that name that records its own import: the check finds it and does not run it. (Under the wall the real
    answer is the stub, which ends a process that imports it.)"""
    marker = tmp_path / "imported.txt"
    (tmp_path / "typesafe_sdk.py").write_text(f"open({str(marker)!r}, 'w').write('imported')\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    monkeypatch.delitem(sys.modules, "typesafe_sdk", raising=False)
    assert jevkey.sdk_found() is True
    assert not marker.exists() and "typesafe_sdk" not in sys.modules
    assert jevkey.available({"TYPESAFE_API_KEY": PLANTED}) is True and not marker.exists() and "typesafe_sdk" not in sys.modules


def test_a_module_already_imported_counts_and_a_blocked_import_does_not(monkeypatch):
    monkeypatch.setitem(sys.modules, "typesafe_sdk", types.ModuleType("typesafe_sdk"))  # a module with no __spec__
    assert jevkey.sdk_found() is True
    monkeypatch.setitem(sys.modules, "typesafe_sdk", None)  # what `sys.modules[name] = None` does to an import
    assert jevkey.sdk_found() is False
    assert jevkey.available({"TYPESAFE_API_KEY": PLANTED}) is False


def test_a_package_that_is_nowhere_is_not_found(tmp_path, monkeypatch):
    monkeypatch.delitem(sys.modules, "typesafe_sdk", raising=False)
    monkeypatch.setattr(sys, "path", [str(tmp_path)])  # no folder that holds it
    assert jevkey.sdk_found() is False
