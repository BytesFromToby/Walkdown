"""Tests for options.py, written from specs/shared.SPEC.md, options."""
import argparse
import os
import sys

import pytest

import options
import pipeline


def test_context_and_hosts_are_read_here():
    """Moved from the report's tests (restructure step 7): the front door checks both before anything runs."""
    assert [options.parse_context(x) for x in ("32k", "200K", "8192", "8k", "1m", "32,000")] == \
        [32000, 200000, 8192, 8000, 1000000, 32000]
    with pytest.raises(ValueError):
        options.parse_context("lots")
    assert options.parse_hosts("Claude, codex,claude") == ["claude", "codex"]
    for bad in ("", "claude,vim"):
        with pytest.raises(ValueError):
            options.parse_hosts(bad)
    assert "claude" in options.host_keys() and len(options.host_keys()) == 7


def test_the_options_are_declared_once_and_checked_before_anything_runs():
    ap = argparse.ArgumentParser()
    options.add_run_options(ap)
    a = ap.parse_args(["x", "--context", "8k", "--hosts", "codex,cursor", "--sweep", "jev", "--keep"])
    assert options.check(a) is None and a.context == 8000 and a.hosts == ["codex", "cursor"]
    assert (a.target, a.sweep, a.pinpoint, a.keep, a.fresh, a.revalidate) == ("x", "jev", None, True, False, False)
    # the AI options come from stages.json, the parked ones are declared only to be refused
    for argv, why in ((["x", "--label", "jev"], "--label is not available"), (["x", "--both"], "--both is not"),
                      (["x", "--hosts", "vim"], "--hosts: not a host: 'vim' (names: claude,"),
                      (["x", "--context", "lots"], "--context 'lots' is not a token count")):
        assert why in options.check(ap.parse_args(argv)).replace("claude, ", "claude,"), argv
    assert not hasattr(ap.parse_args(["x"]), "no_validate")  # the developer options are the runner's alone
    dev = argparse.ArgumentParser()
    options.add_run_options(dev, developer=True)
    d = dev.parse_args(["x", "--repo", "r", "--no-validate", "--date", "2026-01-02"])
    assert (d.repo, d.no_validate, d.date) == ("r", True, "2026-01-02") and d.results.endswith("RepoResults")
    # the report stage takes the same two options from the same function
    rep = argparse.ArgumentParser()
    options.add_report_options(rep)
    assert vars(rep.parse_args(["--context", "1m"])) == {"context": "1m", "hosts": None}


def test_one_off_list_for_every_model_option():
    """Restructure step 7 (notes M14 a): empty, none, 0, false, no, and off, in any case with spaces
    ignored, ask for nothing."""
    assert options.OFF == ("", "none", "0", "false", "no", "off")
    for v in ("", None, "none", " NONE ", "0", "false", "False", "no", "No", "off", "OFF", " off "):
        assert options.is_off(v), v
    for v in ("jev", "claude-cli", "1", "true", "yes", "on", "offline"):
        assert not options.is_off(v), v


def test_the_chosen_stage_rule_and_the_refusal_rule_read_the_same_list():
    for value in options.OFF:
        # as an option
        assert options.ai_chosen("03-sweep", {"sweep": value}, {}) is False
        assert options.refusal({"label": value, "both": value}, {}) is None
        # as an environment variable: the old chosen rule counted off, 0, false, and no as chosen
        assert options.ai_chosen("03-sweep", None, {"WALKDOWN_SOFT_SWEEP": value}) is False
        assert options.ai_chosen("04-pinpoint", None, {"WALKDOWN_SOFT_PINPOINT": value}) is False
        assert options.refusal({}, {"WALKDOWN_SOFT_LABEL": value}) is None
    assert options.ai_chosen("03-sweep", None, {"WALKDOWN_SOFT_SWEEP": "jev"}) is True
    assert options.ai_chosen("03-sweep", {"sweep": "jev"}, {"WALKDOWN_SOFT_SWEEP": "off"}) is True  # the flag wins
    assert options.ai_chosen("03-sweep", {"sweep": "none"}, {"WALKDOWN_SOFT_SWEEP": "jev"}) is False
    assert options.refusal({"label": "jev"}, {}) == "--label is not available in this version: labeling is being rebuilt"
    assert options.refusal({"both": True}, {}).startswith("--both ")
    assert options.refusal({}, {"WALKDOWN_SOFT_COMPARE": "jev"}).startswith("WALKDOWN_SOFT_COMPARE ")


def test_an_option_with_a_value_wins_and_an_empty_one_is_no_option():
    """Round 2 of step 7: `--sweep none` and `--sweep off` stand over the variable; `--sweep ""` is no option, so
    the variable decides (main's behavior, kept)."""
    env = {"WALKDOWN_SOFT_SWEEP": "jev", "WALKDOWN_SOFT_PINPOINT": "claude-cli"}
    for v in ("none", "off", "0", "false", "no"):
        assert options.ai_chosen("03-sweep", {"sweep": v}, env) is False, v
    for v in ("", None):
        assert options.ai_chosen("03-sweep", {"sweep": v}, env) is True, v
        assert options.ai_chosen("04-pinpoint", {"pinpoint": v}, env) is True, v
    assert options.ai_chosen("03-sweep", {"sweep": ""}, {"WALKDOWN_SOFT_SWEEP": "off"}) is False
    assert options.ai_chosen("03-sweep", {"sweep": ""}, {}) is False
    assert pipeline.stages_to_run({"sweep": "", "pinpoint": ""}, env)[-2:] == ["03-sweep", "04-pinpoint"]


def test_an_off_value_starts_no_stage():
    coded = [s for s in pipeline.FOLDER_STAGES if s not in pipeline.AI_STAGES]
    for v in ("off", "false", "0", "no", "none"):
        assert pipeline.stages_to_run({"sweep": v, "pinpoint": v}, {}) == coded
    assert pipeline.stages_to_run({"sweep": "off"}, {"WALKDOWN_SOFT_SWEEP": "jev"}) == coded  # the flag wins
    assert pipeline.stages_to_run(None, {"WALKDOWN_SOFT_SWEEP": "off"}) == coded


# ---------------------------------------------------------------- --until (O3)

def test_until_names_come_from_the_stage_list(monkeypatch):
    """No copy of the stage names here: a new stage in the list is a new name, with no change to options.py."""
    import stagelist
    names = options.until_names()
    for name in stagelist.STAGES:
        number, _, word = name.partition("-")
        assert names[name] == names[number] == names[word] == name
    doc = stagelist.load_stage_list()
    extra = {"name": "02.7-extra", "folder": "02-coded/02.7-extra", "plain": "Extra"}
    monkeypatch.setattr(stagelist, "load_stage_list", lambda stages_dir=None: {**doc, "stages": [*doc["stages"], extra]})
    assert options.resolve_until("extra") == options.resolve_until("02.7") == "02.7-extra"
    assert options.resolve_until("coded") == "02.7-extra"  # the group's last step follows the list


def test_until_names_a_step_by_name_number_or_word():
    r = options.resolve_until
    assert r("02.4-phrases") == r("02.4") == r("phrases") == r("PHRASES") == r(" 02.4-Phrases ") == "02.4-phrases"
    assert r("01-intake") == r("01") == r("intake") == "01-intake"
    assert r("03-sweep") == r("03") == r("sweep") == "03-sweep"
    assert r("04-pinpoint") == r("04") == r("pinpoint") == "04-pinpoint"
    assert r("02-coded") == r("02") == r("coded") == r("CODED") == "02.6-builder"  # the last coded step
    assert r("02.6") == r("builder") == "02.6-builder"
    for typed in ("", "05", "report", "02.9", "02.4-", "phrase"):
        assert r(typed) is None, typed


def parse(argv):
    ap = argparse.ArgumentParser()
    options.add_run_options(ap)
    return ap.parse_args(argv)


def test_until_that_is_not_a_step_or_an_unchosen_ai_step_is_refused(monkeypatch):
    for k in ("WALKDOWN_SOFT_SWEEP", "WALKDOWN_SOFT_PINPOINT"):
        monkeypatch.delenv(k, raising=False)
    a = parse(["x", "--until", "Coded"])
    assert options.check(a) is None and a.until == "02.6-builder"  # the step's name replaces what was typed
    assert parse(["x"]).until is None
    bad = options.check(parse(["x", "--until", "nonsense"]))
    assert bad.startswith("--until 'nonsense' is not a step (names: 01-intake, 02.1-inventory, ") and "04-pinpoint" in bad
    assert "\n" not in bad
    # an AI step nobody chose
    assert options.check(parse(["x", "--until", "03-sweep"])) == "--until 03-sweep: that step runs only when chosen (--sweep)"
    assert options.check(parse(["x", "--until", "pinpoint"])) == "--until pinpoint: that step runs only when chosen (--pinpoint)"
    assert options.check(parse(["x", "--until", "sweep", "--sweep", "off"])).endswith("(--sweep)")  # off chooses nothing
    a = parse(["x", "--until", "03-sweep", "--sweep", "jev"])
    assert options.check(a) is None and a.until == "03-sweep"
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "jev")  # chosen by the variable
    a = parse(["x", "--until", "sweep"])
    assert options.check(a) is None and a.until == "03-sweep"
    monkeypatch.delenv("WALKDOWN_SOFT_SWEEP")
    # --pinpoint alone chooses it: the run keeps today's note that it needs --sweep, and is an ordinary run
    a = parse(["x", "--until", "04-pinpoint", "--pinpoint", "claude-cli"])
    assert options.check(a) is None and a.until == "04-pinpoint"
    # the parked options are refused first
    assert "--label is not available" in options.check(parse(["x", "--until", "nonsense", "--label", "jev"]))


def test_ai_choice_names_the_backend_the_stage_will_read():
    """The record keeps the backend that wrote an input file, as the stage reads it (stripped, in lower case)."""
    assert options.ai_choice("03-sweep", {"sweep": " JEV "}, {}) == "jev"
    assert options.ai_choice("03-sweep", {"sweep": None}, {"WALKDOWN_SOFT_SWEEP": "Jev"}) == "jev"
    assert options.ai_choice("03-sweep", {"sweep": "none"}, {"WALKDOWN_SOFT_SWEEP": "jev"}) == ""
    assert options.ai_choice("04-pinpoint", None, {}) == ""
    for off in options.OFF:
        assert options.ai_choice("03-sweep", {"sweep": off}, {}) == ""
    assert options.ai_chosen("03-sweep", {"sweep": "jev"}, {}) is True


def test_at_continue_the_variable_chooses_nothing_and_a_note_says_so(monkeypatch):
    """The consent to send is the option. A first command keeps its rule (the option, else the variable)."""
    run, go_on = argparse.ArgumentParser(), argparse.ArgumentParser()
    options.add_run_options(run)
    options.add_continue_options(go_on)
    assert options.ai_environ(run.parse_args(["x"])) is None and options.ai_environ(go_on.parse_args(["x"])) == {}
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "jev")
    a = run.parse_args(["x", "--until", "sweep"])  # a run: the variable chooses the sweep, so it can be named
    assert options.check(a) is None and a.until == "03-sweep"
    b = go_on.parse_args(["x", "--until", "sweep"])  # continue: it does not
    assert options.check(b) == "--until sweep: that step runs only when chosen (--sweep)"
    c = go_on.parse_args(["x", "--until", "sweep", "--sweep", "jev"])
    assert options.check(c) is None and c.until == "03-sweep"
    soft = {"sweep": None, "pinpoint": None}
    assert options.env_not_read_notes(soft) == [
        "WALKDOWN_SOFT_SWEEP is not read at continue; give --sweep <backend> to send"]
    assert options.env_not_read_notes({"sweep": "jev", "pinpoint": None}) == []  # the option is given
    assert options.env_not_read_notes({"sweep": "none", "pinpoint": ""}) == []  # an option that declines is given too
    monkeypatch.setenv("WALKDOWN_SOFT_PINPOINT", "claude-cli")
    assert [x.split(" ")[0] for x in options.env_not_read_notes(soft)] == ["WALKDOWN_SOFT_SWEEP", "WALKDOWN_SOFT_PINPOINT"]
    for off in options.OFF:
        monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", off)
        monkeypatch.setenv("WALKDOWN_SOFT_PINPOINT", off)
        assert options.env_not_read_notes(soft) == [], off
    assert options.env_not_read_notes(soft, {"WALKDOWN_SOFT_PINPOINT": "claude-cli"}) == [
        "WALKDOWN_SOFT_PINPOINT is not read at continue; give --pinpoint <backend> to send"]


def test_continue_declares_its_options_and_not_intakes():
    ap = argparse.ArgumentParser()
    options.add_continue_options(ap)
    a = ap.parse_args(["RepoResults/x/2026-10-30_abc1234", "--sweep", "jev", "--until", "sweep", "--context", "8k",
                       "--hosts", "codex", "--revalidate"])
    assert options.check(a) is None
    assert (a.run_dir, a.sweep, a.pinpoint, a.until, a.context, a.hosts, a.revalidate) == (
        "RepoResults/x/2026-10-30_abc1234", "jev", None, "03-sweep", 8000, ["codex"], True)
    for intake_only in (["--name", "x"], ["--fresh"], ["--keep"]):  # intake does not run again
        with pytest.raises(SystemExit):
            ap.parse_args(["run", *intake_only])
    assert not hasattr(a, "no_validate") and not hasattr(a, "target")
    dev = argparse.ArgumentParser()
    options.add_continue_options(dev, developer=True)
    assert dev.parse_args(["run", "--no-validate"]).no_validate is True
    assert "--label is not available" in options.check(ap.parse_args(["run", "--label", "jev"]))


# ---------------------------------------------------------------- M1 slice A: a model option is a backend, then a model

def test_the_backend_is_the_text_before_the_first_colon_in_any_case_and_the_model_is_the_rest_as_typed():
    pick = options.parse_choice
    assert pick("03-sweep", "jev", "--sweep") == ("jev", None)
    assert pick("03-sweep", " JEV ", "--sweep") == ("jev", None)
    assert pick("03-sweep", "claude-cli", "--sweep") == ("claude-cli", None)
    assert pick("03-sweep", "Claude-CLI:Some-Model_2", "--sweep") == ("claude-cli", "Some-Model_2")
    assert pick("04-pinpoint", "claude-cli:org/Model-Name:2", "--pinpoint") == ("claude-cli", "org/Model-Name:2")  # more colons
    for off in options.OFF:
        assert pick("03-sweep", off, "--sweep") == ("none", None)


def test_the_value_is_kept_with_the_models_case_for_the_record_and_the_command_to_go_on():
    assert options.normal(" Claude-CLI:Some-Model_2 ") == "claude-cli:Some-Model_2" and options.normal("JEV") == "jev"
    assert options.ai_choice("03-sweep", {"sweep": "Claude-CLI:Some-Model_2"}, {}) == "claude-cli:Some-Model_2"
    assert options.ai_choice("03-sweep", {}, {"WALKDOWN_SOFT_SWEEP": " JEV "}) == "jev"
    assert options.ai_choice("04-pinpoint", {"pinpoint": "claude-cli:Some-Model_2"}, {}) == "claude-cli:Some-Model_2"
    assert options.ai_choice("03-sweep", {"sweep": "OFF:x"}, {}) == "off:x"  # not an off value: it is refused when it is read


@pytest.mark.parametrize("stage, value, why", [
    ("03-sweep", "jev:fast", "jev takes no model name"),
    ("03-sweep", "JEV:", "jev takes no model name"),
    ("04-pinpoint", "jev", "jev answers from fixed options, and the pinpoint needs a line and a sentence"),
    ("04-pinpoint", "Jev", "jev answers from fixed options"),
    ("03-sweep", "gpt", "is not one of none, jev, claude-cli"),
    ("04-pinpoint", "gpt:4", "is not one of none, claude-cli"),
    ("03-sweep", "ollama:qwen3:14b", "is not one of none, jev, claude-cli"),  # a backend this version does not have
    ("03-sweep", "claude-cli:", "nothing follows the colon"),
    ("03-sweep", "claude-cli:my model", "ASCII letters, digits"),
    ("03-sweep", "claude-cli:a\tb", "ASCII letters, digits"),
    ("03-sweep", "claude-cli:a\x00b", "ASCII letters, digits"),
    ("03-sweep", "claude-cli:a\x1bb", "ASCII letters, digits"),
    ("03-sweep", "claude-cli:a\u200bb", "ASCII letters, digits"),
    ("03-sweep", "claude-cli:a b", "ASCII letters, digits"),
    ("03-sweep", "claude-cli:-m", "does not start with a dash"),
    ("03-sweep", "claude-cli:--tools", "does not start with a dash"),
    ("03-sweep", "claude-cli:x&echo.INJECTED>marker", "ASCII letters, digits"),
    ("03-sweep", "claude-cli:https://evil.example/x", "has no //"),
    ("03-sweep", "claude-cli:a//b", "has no //"),
    ("03-sweep", "claude-cli:\u65e5\u672c\u8a9e", "ASCII letters, digits"),
])
def test_a_value_that_cannot_be_used_is_refused_with_one_sentence_that_says_why(stage, value, why):
    with pytest.raises(ValueError) as exc:
        options.parse_choice(stage, value, "--x")
    text = str(exc.value)
    assert text.startswith("--x: ") and why in text and "\n" not in text and "\x00" not in text and "\x1b" not in text


def test_every_backend_says_whether_it_gives_a_probability():
    """M1 fix 9: the pages word a read from the backend (`probability.gives`), so the table must say it for each."""
    assert {name: spec["probability"] for name, spec in options.BACKENDS.items()} == {"jev": True, "claude-cli": False}


ALLOWED = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:/@+-[]")


def test_a_model_name_is_made_of_the_allowed_characters_only():
    """M1 fix 1: on Windows a `.cmd` shim hands the name to the shell, which reads & | < > ^ % and a quote as commands or
    variables. Every character a person can type is tested: of the ASCII ones exactly the allowed list passes, and no other
    character does, whatever its kind (a non-ASCII letter, a digit from another script, an emoji, a look-alike, a control
    character). Two slashes in a row do not pass either (fix round 2): `https://host/x` would show in the reports as a link."""
    for code in range(0x21, 0x7F):
        ch = chr(code)
        assert (options.bad_model("m" + ch + "m") is None) == (ch in ALLOWED), repr(ch)
    for ch in "&|<>^%\"'`$!;(){}*?~#,= \t\n\r\x00\x1b\u200b\u00e9\u65e5\U0001f600\uff06\u0661":
        assert options.bad_model("m" + ch + "m"), repr(ch)
    for good in ("sonnet", "sonnet[1m]", "claude-sonnet-4-5", "vendor/model.v2@2026+x:tag_1", "a/b/c", "A" * 200):
        assert options.bad_model(good) is None, good
    for link in ("https://evil.example/x", "http://x", "a//b", "//host", "x//", "a///b"):
        assert options.bad_model(link) == options.MODEL_RULE, link
    assert options.bad_model("A" * 201) == options.MODEL_RULE and options.bad_model("-m") == options.MODEL_RULE
    assert options.bad_model("") and "nothing follows the colon" in options.bad_model("")
    assert "& | < > ^ %" not in options.MODEL_RULE and "ASCII letters, digits" in options.MODEL_RULE and "//" in options.MODEL_RULE


def test_a_refusal_prints_on_any_terminal_and_does_not_fill_it():
    """A name outside ASCII is echoed as escapes (a cp1252 console cannot print it), and a long one is cut."""
    for value in ("claude-cli:日本語", "claude-cli:" + "L" * 3000, "日本語", "claude-cli:\U0001f600"):
        with pytest.raises(ValueError) as exc:
            options.parse_choice("03-sweep", value, "--sweep")
        text = str(exc.value)
        assert text.isascii() and len(text) < 260 and "\n" not in text, text


def test_the_model_variable_is_held_to_the_same_rule(monkeypatch):
    ap = argparse.ArgumentParser()
    options.add_run_options(ap)
    for bad in ("%USERNAME%", "x&echo.hi", "a^b", 'a"b', "a|b", "a<b", "a>b", "(a)", "\u65e5\u672c", "https://evil.example/x"):
        monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", bad)
        text = options.check(ap.parse_args(["x", "--sweep", "claude-cli"]))
        assert text and text.startswith("WALKDOWN_SOFT_CLAUDE_MODEL: ") and text.isascii(), (bad, text)
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", "sonnet[1m]")
    assert options.check(ap.parse_args(["x", "--sweep", "claude-cli"])) is None


def test_the_model_options_are_refused_before_anything_runs():
    ap = argparse.ArgumentParser()
    options.add_run_options(ap)
    for argv, why in ((["x", "--sweep", "jev:fast"], "--sweep: 'jev:fast' is refused: jev takes no model name"),
                      (["x", "--sweep", "claude-cli", "--pinpoint", "jev"], "--pinpoint: 'jev' is refused: jev answers from fixed options"),
                      (["x", "--sweep", "gpt"], "--sweep: 'gpt' is not one of none, jev, claude-cli"),
                      (["x", "--sweep", "claude-cli:a b"], "--sweep: 'claude-cli:a b' is refused: a model name is ASCII letters, digits")):
        assert options.check(ap.parse_args(argv)).startswith(why), argv
    a = ap.parse_args(["x", "--sweep", "Claude-CLI:Some-Model_2", "--pinpoint", "claude-cli"])
    assert options.check(a) is None and a.sweep == "Claude-CLI:Some-Model_2"  # the typed value stays; the stages read it
    for off in ("none", "off", "0"):
        assert options.check(ap.parse_args(["x", "--sweep", off, "--pinpoint", off])) is None


def test_the_variable_is_read_by_the_same_rules_at_a_run_and_not_at_all_at_continue(monkeypatch):
    run = argparse.ArgumentParser()
    options.add_run_options(run)
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "jev:fast")
    assert options.check(run.parse_args(["x"])).startswith("WALKDOWN_SOFT_SWEEP: 'jev:fast' is refused")
    assert options.check(run.parse_args(["x", "--sweep", "jev"])) is None  # the option wins over the variable
    cont = argparse.ArgumentParser()
    options.add_continue_options(cont)
    assert options.check(cont.parse_args(["folder"])) is None  # at continue only the option chooses, so the variable is not read
    assert options.check(cont.parse_args(["folder", "--sweep", "jev:fast"])).startswith("--sweep: 'jev:fast' is refused")


def test_the_model_a_claude_cli_will_run_from_the_environment_is_read_by_the_same_rule(monkeypatch):
    ap = argparse.ArgumentParser()
    options.add_run_options(ap)
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", "--dangerously-do-something")
    assert options.check(ap.parse_args(["x", "--sweep", "claude-cli"])).startswith("WALKDOWN_SOFT_CLAUDE_MODEL: ")
    assert options.check(ap.parse_args(["x", "--sweep", "claude-cli:fine"])) is None  # the option names the model: the variable is not used
    assert options.check(ap.parse_args(["x", "--sweep", "jev"])) is None and options.check(ap.parse_args(["x"])) is None
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", "fine")
    assert options.check(ap.parse_args(["x", "--sweep", "claude-cli"])) is None


def test_the_report_stage_declares_no_model_option_and_reads_none(monkeypatch):
    """The report stage takes `--context` and `--hosts` and runs `options.check` too; a variable set to nonsense is not its
    business."""
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "nonsense")
    ap = argparse.ArgumentParser()
    options.add_report_options(ap)
    assert options.check(ap.parse_args(["--context", "8k"])) is None


def test_a_backend_serves_the_steps_its_table_row_names():
    assert options.backend_names("03-sweep") == ("jev", "claude-cli") and options.backend_names("04-pinpoint") == ("claude-cli",)
    assert options.BACKENDS["jev"]["model"] == "none" and options.BACKENDS["claude-cli"]["model"] == "optional"


# ---------------------------------------------------------------- --reads (the loaded-model build)

def reads_parser(continuing=False):
    ap = options.Parser(prog="walkdown.py continue" if continuing else "walkdown.py")
    (options.add_continue_options if continuing else options.add_run_options)(ap)
    return ap


def machine(monkeypatch, jev, claude):
    """What the machine has, as the two questions `--reads` asks: Jev's availability and the `claude` command. Nothing is probed."""
    monkeypatch.setattr(options.jevkey, "available", lambda *a, **k: jev)
    monkeypatch.setattr(options, "claude_found", lambda: claude)


def nothing_probed(monkeypatch):
    def probe(*a, **k):
        raise AssertionError("the machine was asked what it has")
    for name in ("available", "has_key", "read_key", "sdk_found"):
        monkeypatch.setattr(options.jevkey, name, probe)
    monkeypatch.setattr(options, "claude_found", probe)


def watch_the_machine(monkeypatch):
    """Everything a probe would use, watched where it starts, so a call that goes round the named helpers is seen too: the real
    `shutil.which("claude")`, the search for the SDK (`importlib.util.find_spec`), and any open of the Windows registry. Nothing is
    refused (the test's own machinery and argparse run as they do); a call is recorded and the test asserts there is none. A registry open
    is recorded and refused, so no test opens the real registry."""
    import importlib.util
    import shutil
    seen = []
    real_which, real_find = shutil.which, importlib.util.find_spec

    def which(cmd, *a, **k):
        if str(cmd).lower().startswith("claude"):
            seen.append(("which", cmd))
        return real_which(cmd, *a, **k)

    def find_spec(name, *a, **k):
        if str(name).split(".")[0] == "typesafe_sdk":
            seen.append(("find_spec", name))
        return real_find(name, *a, **k)
    monkeypatch.setattr(shutil, "which", which)
    monkeypatch.setattr(importlib.util, "find_spec", find_spec)
    winreg = sys.modules.get("winreg")
    if winreg is None:
        try:
            import winreg
        except ImportError:
            winreg = None
    def refused(*a, _name=None, **k):
        seen.append((_name,))
        raise FileNotFoundError(2, "the registry is not read here (a watched test)", _name)
    for name in ("OpenKey", "OpenKeyEx", "QueryValueEx") if winreg is not None else ():
        monkeypatch.setattr(winreg, name, lambda *a, _name=name, **k: refused(*a, _name=_name, **k))  # recorded and refused: the registry is never opened
    return seen


def resolved(argv, jev, claude, continuing=False):
    a = reads_parser(continuing).parse_args(argv)
    error, note = options.resolve_reads(a, jev, claude)
    return a, error, note


def test_reads_is_an_optional_value_absent_by_default_and_declared_for_a_run_and_for_continue():
    run = reads_parser()
    assert run.parse_args(["x"]).reads is None
    assert run.parse_args(["x", "--reads"]).reads is True
    assert run.parse_args(["x", "--reads", "claude-opus-5-5"]).reads == "claude-opus-5-5"
    assert run.parse_args(["x", "--reads=Opus"]).reads == "Opus"
    a = run.parse_args(["--reads", "opus", "x"])  # the model first, then the target: it parses
    assert (a.reads, a.target) == ("opus", "x")
    a = run.parse_args(["x", "--reads", "--name", "y"])  # the next option ends a bare --reads
    assert (a.reads, a.name) == (True, "y")
    go_on = reads_parser(continuing=True)
    assert go_on.parse_args(["folder"]).reads is None and go_on.parse_args(["folder", "--reads"]).reads is True
    assert go_on.parse_args(["folder", "--reads", "opus"]).reads == "opus"
    dev = argparse.ArgumentParser()
    options.add_run_options(dev, developer=True)  # the runner's own command line takes it too
    assert dev.parse_args(["x", "--reads", "opus"]).reads == "opus"
    rep = argparse.ArgumentParser()
    options.add_report_options(rep)
    assert not hasattr(rep.parse_args([]), "reads")  # the report stage reads no model option
    assert "--reads [MODEL]" in run.format_help()


def test_the_table_row_by_row(monkeypatch):
    rows = ((True, True, "jev", "claude-cli"), (True, False, "jev", "none"),
            (False, True, "claude-cli", "claude-cli"))
    for model, suffix in ((None, ""), ("claude-opus-5-5", ":claude-opus-5-5"), ("Sonnet[1m]", ":Sonnet[1m]"),
                          ("vendor/Model_2", ":vendor/Model_2")):
        argv = ["x", "--reads"] + ([] if model is None else [model])
        for jev, claude, sweep, pinpoint in rows:
            a, error, _ = resolved(argv, jev, claude)
            assert error is None
            # the model is exactly as typed; the backend of the Claude Code command is lower case
            want_sweep = sweep + (suffix if sweep == "claude-cli" else "")
            want_pin = pinpoint + (suffix if pinpoint == "claude-cli" else "")
            assert (a.sweep, a.pinpoint) == (want_sweep, want_pin), (model, jev, claude)
            assert a.reads == (True if model is None else model)  # what was typed stays
        a, error, note = resolved(argv, False, False)  # the last row: nothing can run
        assert error == options.NEITHER and note is None and (a.sweep, a.pinpoint) == (None, None)
    # the pure function is the same table
    assert options.reads_plan(None, True, True) == ({"sweep": "jev", "pinpoint": "claude-cli"}, None, None)
    assert options.reads_plan("opus", False, True) == (
        {"sweep": "claude-cli:opus", "pinpoint": "claude-cli:opus"}, None, None)
    # through `check`: the resolved values are the ones the stages read (`ai_choice`), and `check_models` accepts them
    for jev, claude, sweep, pinpoint in rows:
        machine(monkeypatch, jev, claude)
        a = reads_parser().parse_args(["x", "--reads", "opus"])
        assert options.check(a) is None
        soft = {"sweep": a.sweep, "pinpoint": a.pinpoint}
        assert options.ai_choice("03-sweep", soft, {}) == sweep + (":opus" if sweep == "claude-cli" else "")
        assert options.ai_choice("04-pinpoint", soft, {}) == ("" if pinpoint == "none" else "claude-cli:opus")


def test_jev_without_claude_runs_the_sweep_alone_and_says_so_in_one_note(monkeypatch, capsys):
    machine(monkeypatch, True, False)
    a = reads_parser().parse_args(["x", "--reads"])
    assert options.check(a) is None and (a.sweep, a.pinpoint) == ("jev", "none")
    cap = capsys.readouterr()
    assert cap.out == ""
    assert cap.err == "note: --reads: Pinpoint needs the claude command, which was not found, so it does not run.\n"
    assert options.reads_plan("opus", True, False)[1] == options.NO_PINPOINT
    for jev, claude in ((True, True), (False, True)):  # the other rows that run say nothing
        machine(monkeypatch, jev, claude)
        assert options.check(reads_parser().parse_args(["x", "--reads"])) is None
        assert capsys.readouterr().err == ""


def test_each_refusal_of_reads_is_one_sentence(monkeypatch, capsys):
    nothing_probed(monkeypatch)  # none of the first two asks the machine anything
    conflict = ("--reads: it cannot be given with --sweep or --pinpoint, which name the reads themselves; "
                "give one or the other.")
    for extra in (["--sweep", "jev"], ["--pinpoint", "claude-cli"], ["--sweep", "none"],
                  ["--sweep", "jev", "--pinpoint", "claude-cli"]):
        for reads in (["--reads"], ["--reads", "opus"]):
            assert options.check(reads_parser().parse_args(["x", *reads, *extra])) == conflict, (reads, extra)
    empty = "--reads: the model is empty; name one, or leave the model out."
    for blank in ("", "   "):
        assert options.check(reads_parser().parse_args(["x", "--reads", blank])) == empty
    machine(monkeypatch, True, True)
    for empty_option in ("--sweep", "--pinpoint"):  # an empty option is no option, as it is for the variable
        a = reads_parser().parse_args(["x", "--reads", "opus", empty_option, ""])
        assert options.check(a) is None
    machine(monkeypatch, False, False)
    neither = "--reads: no model read can run here: Jev has no key or package, and no claude command was found."
    assert options.check(reads_parser().parse_args(["x", "--reads"])) == options.NEITHER == neither
    assert options.check(reads_parser().parse_args(["x", "--reads", "opus"])) == neither
    only = ("--reads: no model read can run here: only Pinpoint is left, and it needs the claude command, "
            "which was not found.")
    monkeypatch.setattr(options, "steps_done", lambda run_dir: frozenset({"03-sweep"}))
    for jev in (True, False):
        machine(monkeypatch, jev, False)
        assert options.check(reads_parser(True).parse_args(["folder", "--reads"])) == options.ONLY_PINPOINT == only
    for sentence in (conflict, empty, neither, only):  # one sentence each: one line, ASCII, no dash for a pause
        assert "\n" not in sentence and sentence.isascii() and "\u2014" not in sentence and sentence.endswith(".")
    assert capsys.readouterr().err == ""  # a refusal prints nothing by itself: the front door prints `error: <sentence>`


def test_a_backend_typed_as_the_model_is_refused_and_a_name_that_contains_one_is_not(monkeypatch):
    nothing_probed(monkeypatch)  # refused before the machine is asked anything
    seen = watch_the_machine(monkeypatch)
    for typed in ("jev", "Jev", "JEV", "claude-cli", "Claude-CLI", "claude-cli:opus", "jev:x", "JEV:whatever", " jev "):
        said = options.check(reads_parser().parse_args(["x", f"--reads={typed}"]))
        assert said == f"--reads: {options.shown(typed.strip())} is a backend, and --reads takes a model name; to name a backend, use --sweep or --pinpoint.", typed
        assert "\n" not in said and said.isascii()
    assert options.check(reads_parser().parse_args(["x", "--reads", "jev"])) == (
        "--reads: 'jev' is a backend, and --reads takes a model name; to name a backend, use --sweep or --pinpoint.")
    assert seen == []
    # a model that only contains a backend's name is a model name
    machine(monkeypatch, True, True)
    for fine in ("jev-latest", "my-claude-cli", "claude-cli2", "x-jev", "opus:jev", "claude-clix:opus"):
        a = reads_parser().parse_args(["x", "--reads", fine])
        assert options.check(a) is None and a.pinpoint == f"claude-cli:{fine}", fine
    # at continue too
    a = reads_parser(True).parse_args(["folder", "--reads=claude-cli:opus"])
    assert options.check(a).startswith("--reads: 'claude-cli:opus' is a backend, and --reads takes a model name")


def test_the_model_of_reads_goes_through_bad_model(monkeypatch):
    nothing_probed(monkeypatch)  # a name that is refused is refused before the machine is asked anything
    for bad in ("a b", "x&echo", "x|y", "-opus", "--model", "a//b", "https://host/x", "日本語", "x" * 201,
                "tab\there", "new\nline", "100%", 'q"uote'):
        a = reads_parser().parse_args(["x", f"--reads={bad}"])  # one token, so that "-opus" is a value and not an option
        said = options.check(a)
        assert said == f"--reads: {options.shown(bad)} is refused: {options.bad_model(bad)}", bad
        assert "\n" not in said and said.isascii()
    machine(monkeypatch, True, True)
    for good in ("opus", "claude-opus-5-5", "Sonnet[1m]", "vendor/Model_2", "x" * 200):
        a = reads_parser().parse_args(["x", "--reads", good])
        assert options.check(a) is None and a.pinpoint == f"claude-cli:{good}"


def test_under_reads_the_option_wins_over_the_variables(monkeypatch):
    # a variable set to nonsense is not read while --reads is given, as it is not read beside --sweep
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "gpt")
    monkeypatch.setenv("WALKDOWN_SOFT_PINPOINT", "claude-cli:with space")
    machine(monkeypatch, True, True)
    a = reads_parser().parse_args(["x", "--reads"])
    assert options.check(a) is None and (a.sweep, a.pinpoint) == ("jev", "claude-cli")
    # a read --reads does not run is none, so its variable cannot choose it
    machine(monkeypatch, True, False)
    monkeypatch.setenv("WALKDOWN_SOFT_PINPOINT", "claude-cli")
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "claude-cli")
    a = reads_parser().parse_args(["x", "--reads"])
    assert options.check(a) is None
    soft = {"sweep": a.sweep, "pinpoint": a.pinpoint}
    assert options.ai_choice("03-sweep", soft, os.environ) == "jev"  # not the variable's claude-cli
    assert options.ai_chosen("04-pinpoint", soft, os.environ) is False  # not the variable's claude-cli
    import pipeline
    assert pipeline.stages_to_run(soft, os.environ)[-1] == "03-sweep"  # no Pinpoint in the run
    # without --reads the same variables choose, as before
    b = reads_parser().parse_args(["x"])
    assert options.ai_choice("04-pinpoint", {"sweep": b.sweep, "pinpoint": b.pinpoint}, os.environ) == "claude-cli"


def test_reads_asks_for_nothing_when_off(monkeypatch):
    nothing_probed(monkeypatch)
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "jev")
    monkeypatch.setenv("WALKDOWN_SOFT_PINPOINT", "claude-cli")
    import pipeline
    coded = [s for s in pipeline.FOLDER_STAGES if s not in pipeline.AI_STAGES]
    for off in ("none", "off", "0", "false", "no", " OFF ", "None"):
        a = reads_parser().parse_args(["x", "--reads", off])
        assert options.check(a) is None and (a.sweep, a.pinpoint) == ("none", "none"), off
        assert pipeline.stages_to_run({"sweep": a.sweep, "pinpoint": a.pinpoint}, os.environ) == coded


def test_a_bare_reads_reads_the_model_variable_as_a_bare_claude_cli_does(monkeypatch):
    machine(monkeypatch, False, True)
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", "bad name")
    bare = options.check(reads_parser().parse_args(["x", "--reads"]))
    assert bare == options.model_env_refusal("claude-cli", None, "bad name")
    assert bare.startswith("WALKDOWN_SOFT_CLAUDE_MODEL: ")
    assert options.check(reads_parser().parse_args(["x", "--sweep", "claude-cli"])) == bare  # the same sentence as a bare claude-cli
    assert options.check(reads_parser().parse_args(["x", "--reads", "opus"])) is None  # the option names the model
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", "from-env")
    a = reads_parser().parse_args(["x", "--reads"])
    assert options.check(a) is None and (a.sweep, a.pinpoint) == ("claude-cli", "claude-cli")  # the stage reads the variable
    machine(monkeypatch, True, False)  # no Claude Code command runs, so its model variable is nobody's business
    monkeypatch.setenv("WALKDOWN_SOFT_CLAUDE_MODEL", "bad name")
    assert options.check(reads_parser().parse_args(["x", "--reads"])) is None


def test_reads_probes_nothing_unless_it_is_given(monkeypatch):
    nothing_probed(monkeypatch)
    seen = watch_the_machine(monkeypatch)
    assert options.check(reads_parser().parse_args(["x"])) is None
    assert options.check(reads_parser(True).parse_args(["folder"])) is None
    assert options.check(reads_parser().parse_args(["x", "--sweep", "jev", "--pinpoint", "claude-cli:opus"])) is None
    assert options.resolve_reads(reads_parser().parse_args(["x"])) == (None, None)
    monkeypatch.setenv("TYPESAFE_API_KEY", "planted-for-this-test")  # a key in the environment is not asked about either
    assert options.check(reads_parser().parse_args(["x", "--hosts", "claude"])) is None
    assert seen == []  # and no call went round the named helpers: no `which("claude")`, no search for the SDK, no registry open
    # the watch itself sees what it is there to see (called here directly: the named helpers are replaced above)
    import importlib.util
    import shutil
    shutil.which("claude")
    importlib.util.find_spec("typesafe_sdk")
    assert ("which", "claude") in seen and ("find_spec", "typesafe_sdk") in seen


def test_reads_at_continue_chooses_only_the_reads_that_can_still_run(monkeypatch):
    # nothing ran: the table
    monkeypatch.setattr(options, "steps_done", lambda run_dir: frozenset({"01-intake", "02.1-inventory"}))
    a, error, note = resolved(["folder", "--reads", "opus"], True, True, continuing=True)
    assert (error, a.sweep, a.pinpoint) == (None, "jev", "claude-cli:opus")
    a, error, note = resolved(["folder", "--reads"], True, False, continuing=True)
    assert (error, note, a.sweep, a.pinpoint) == (None, options.NO_PINPOINT, "jev", "none")
    # the Sweep ran: Pinpoint alone, on the Claude Code command, and the Sweep is not named
    monkeypatch.setattr(options, "steps_done", lambda run_dir: frozenset({"01-intake", "03-sweep"}))
    for jev in (True, False):
        a, error, note = resolved(["folder", "--reads", "opus"], jev, True, continuing=True)
        assert (error, note, a.sweep, a.pinpoint) == (None, None, "none", "claude-cli:opus"), jev
        a, error, note = resolved(["folder", "--reads"], jev, False, continuing=True)
        assert error == options.ONLY_PINPOINT and (a.sweep, a.pinpoint) == (None, None), jev
    # both ran: nothing is left to choose, and nothing is refused (the runner says there is nothing to run)
    monkeypatch.setattr(options, "steps_done", lambda run_dir: frozenset({"03-sweep", "04-pinpoint"}))
    a, error, note = resolved(["folder", "--reads"], False, False, continuing=True)
    assert (error, note, a.sweep, a.pinpoint) == (None, None, "none", "none")
    # a run, not a continue, reads no record
    monkeypatch.setattr(options, "steps_done", lambda run_dir: (_ for _ in ()).throw(AssertionError("a run has no record")))
    a, error, note = resolved(["x", "--reads"], True, True)
    assert (error, a.sweep, a.pinpoint) == (None, "jev", "claude-cli")
    # the variables choose nothing at continue, with or without --reads
    monkeypatch.setattr(options, "steps_done", lambda run_dir: frozenset({"03-sweep"}))
    monkeypatch.setenv("WALKDOWN_SOFT_SWEEP", "jev")
    monkeypatch.setenv("WALKDOWN_SOFT_PINPOINT", "claude-cli")
    machine(monkeypatch, True, True)
    a = reads_parser(True).parse_args(["folder", "--reads", "opus"])
    assert options.check(a) is None
    soft = {"sweep": a.sweep, "pinpoint": a.pinpoint}
    assert [s for s in ("03-sweep", "04-pinpoint") if options.ai_chosen(s, soft, options.ai_environ(a))] == ["04-pinpoint"]


def test_steps_done_reads_the_record_and_nothing_else(tmp_path):
    assert options.steps_done(tmp_path / "gone") == frozenset()
    (tmp_path / "data").mkdir()
    assert options.steps_done(tmp_path) == frozenset()
    import record
    steps = ('[{"stage": "01-intake", "ok": true}, {"stage": "03-sweep", "ok": false}, '
             '{"stage": "02.1-inventory", "ok": true}]')
    (tmp_path / "data" / "run.json").write_text('{"format": %d, "steps": %s}' % (record.FORMAT, steps), encoding="utf-8")
    assert options.steps_done(tmp_path) == frozenset({"01-intake", "02.1-inventory"})  # a step that failed did not run
    (tmp_path / "data" / "run.json").write_text('{"format": %d, "steps": 7}' % record.FORMAT, encoding="utf-8")
    assert options.steps_done(tmp_path) == frozenset()


def test_the_parser_turns_a_missing_target_after_reads_into_one_sentence_and_leaves_other_errors_alone(capsys):
    def fails(parser, argv):
        with pytest.raises(SystemExit) as stop:
            parser.parse_args(argv)
        assert stop.value.code == 2
        return capsys.readouterr().err

    run = reads_parser()
    err = fails(run, ["--reads", "somewhere"])
    assert err == ("error: --reads took 'somewhere' as its model and left no repository to audit; put the repository first, "
                   "as in: walkdown.py <repo> --reads [model]\n")
    assert fails(run, ["--reads", "somewhere", "--name", "y", "--fresh"]).startswith("error: --reads took 'somewhere' ")
    err = fails(reads_parser(True), ["--reads", "RepoResults/x/2026-11-01_abc1234"])
    assert err == ("error: --reads took 'RepoResults/x/2026-11-01_abc1234' as its model and left no run folder to continue; "
                   "put the run folder first, as in: walkdown.py continue <run folder> --reads [model]\n")
    err = fails(run, ["--reads", "日本語" * 40])  # printable on any terminal, and not long
    assert err.isascii() and len(err) < 300 and err.count("\n") == 1 and "Traceback" not in err
    # every other error is argparse's own: its usage text and its words
    for argv, why in (([], "the following arguments are required: target"),
                      (["--reads"], "the following arguments are required: target"),
                      (["x", "--name"], "expected one argument"), (["x", "--nonsense"], "unrecognized arguments")):
        err = fails(run, argv)
        assert err.startswith("usage: walkdown.py") and why in err and "--reads took" not in err, argv
    assert "the following arguments are required: run_dir" in fails(reads_parser(True), ["--reads"])
    assert "--reads took" not in fails(reads_parser(True), ["--nonsense"])
    ok = run.parse_args(["x", "--reads", "opus"])
    assert ok.target == "x" and ok.reads == "opus"
    # a parser that is argparse's own (the tests' parsers, the report stage's) still works with the option declared
    plain = argparse.ArgumentParser()
    options.add_run_options(plain)
    assert plain.parse_args(["x", "--reads"]).reads is True


def test_until_follows_what_reads_chose(monkeypatch):
    machine(monkeypatch, True, False)  # Jev, no claude: the Pinpoint does not run
    a = reads_parser().parse_args(["x", "--reads", "--until", "sweep"])
    assert options.check(a) is None and a.until == "03-sweep"
    a = reads_parser().parse_args(["x", "--reads", "--until", "04-pinpoint"])
    assert options.check(a) == "--until 04-pinpoint: --reads does not run that step here"
    machine(monkeypatch, True, True)
    a = reads_parser().parse_args(["x", "--reads", "--until", "pinpoint", "--revalidate"])
    assert options.check(a) is None and a.until == "04-pinpoint" and a.revalidate is True
    # without --reads the old words stand
    assert options.check(reads_parser().parse_args(["x", "--until", "pinpoint"])) == (
        "--until pinpoint: that step runs only when chosen (--pinpoint)")
    # at continue the Sweep that ran is not chosen, so it cannot be a stop
    monkeypatch.setattr(options, "steps_done", lambda run_dir: frozenset({"03-sweep"}))
    a = reads_parser(True).parse_args(["folder", "--reads", "--until", "sweep"])
    assert options.check(a) == "--until sweep: --reads does not run that step here"


def test_claude_is_found_by_the_path_the_way_back_claude_looks(tmp_path, monkeypatch):
    """The real question, and no stand-in: `claude_found` and `back_claude`'s own `prepare` (its default lookup) are asked on the same
    machine and agree, they ask for the same name, and `claude_found` uses `shutil.which` as `back_claude`'s default is. The wall's PATH has
    no `claude`, so the first answer is the machine under test."""
    import inspect
    import shutil
    import back_claude
    import softdata
    data = softdata.load()
    assert inspect.signature(back_claude.ClaudeCLI.__init__).parameters["which"].default is shutil.which

    def asked_by_back_claude():
        return back_claude.ClaudeCLI(data).prepare()
    assert options.claude_found() is False and asked_by_back_claude() == "claude-cli: not installed"
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    if os.name == "nt":
        (bin_dir / "claude.cmd").write_bytes(b"@echo off\r\n")
    else:
        (bin_dir / "claude").write_text("#!/bin/sh\n", encoding="utf-8")
        (bin_dir / "claude").chmod(0o755)
    monkeypatch.setenv("PATH", os.pathsep.join([str(bin_dir), os.environ["PATH"]]))
    assert options.claude_found() is True and asked_by_back_claude() is None  # both find it
    names = []
    real = shutil.which
    monkeypatch.setattr(shutil, "which", lambda cmd, *a, **k: names.append(cmd) or real(cmd, *a, **k))
    assert options.claude_found() is True
    back_claude.ClaudeCLI(data, which=shutil.which).prepare()  # the name its `prepare` asks for, through the same watch
    assert names == ["claude", "claude"]  # `claude_found` and `prepare` ask for one name
    monkeypatch.setattr(shutil, "which", real)
    monkeypatch.setenv("PATH", str(tmp_path / "nowhere"))
    assert options.claude_found() is False and asked_by_back_claude() == "claude-cli: not installed"
