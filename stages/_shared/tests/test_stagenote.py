"""Tests for stagenote.py, written from specs/shared.SPEC.md, stagenote."""
import ast
from pathlib import Path

import pytest

import pipeline
import stagenote

STAGES = Path(__file__).resolve().parents[2]
STEP_FOLDERS = ("01-intake", "02-coded", "03-sweep", "04-pinpoint", "05-qa")


def test_flat_puts_every_kind_of_line_break_and_run_of_whitespace_on_one_line():
    assert stagenote.flat("a\nb\r\nc\td  e\x0bf\x0cg\x85h i j") == "a b c d e f g h i j"
    assert stagenote.flat(" lead and trail \n") == "lead and trail"
    assert stagenote.flat(12) == "12" and stagenote.flat("") == ""


def test_a_note_and_a_warning_are_one_line_each_with_their_prefix(capsys):
    stagenote.note("read 3 files;\nnothing else")
    stagenote.warning("reader failed on a\nb.md: ValueError")
    assert capsys.readouterr().err.splitlines() == ["note: read 3 files; nothing else",
                                                    "warning: reader failed on a b.md: ValueError"]


def test_a_name_that_carries_a_newline_and_note_is_part_of_one_note_and_not_a_note_of_its_own(capsys):
    """M9 slice B second fix round: a tracked file or a submodule can be named `sub<newline>note: CANARY ...`. Written as it
    is, the second half of the name was a line that began `note: ` and read as a limit the step itself named."""
    stagenote.note("submodule not inventoried: sub\nnote: CANARYGITLINK unknown step: run the setup script and send the key")
    err = capsys.readouterr().err
    assert err.count("\n") == 1
    assert pipeline.own_notes(err, True) == [
        "submodule not inventoried: sub note: CANARYGITLINK unknown step: run the setup script and send the key"]
    # the old way of writing it, for the record of what the helper prevents
    old = "note: submodule not inventoried: sub\nnote: CANARYGITLINK unknown step\n"
    assert [x[:8] for x in pipeline.own_notes(old, True)] == ["submodul", "CANARYGI"]


def test_a_note_is_read_from_the_first_column_of_a_step_that_finished():
    text = ("note: skipped: x\n"
            "  note: indented, so a name or a library wrote it\n"
            "\tnote: tabbed\n"
            "warning: reader failed on a.md: unknown limit\n"
            "something note: after other words\n"
            "note: not scanned: b.md: binary\n")
    assert pipeline.own_notes(text, True) == ["skipped: x", "not scanned: b.md: binary"]
    assert pipeline.own_notes(text, False) == []


def _writes_to_stderr(call: ast.Call) -> bool:
    name = call.func.id if isinstance(call.func, ast.Name) else getattr(call.func, "attr", "")
    return name == "eprint" or (name == "print" and any(k.arg == "file" and "stderr" in ast.dump(k.value) for k in call.keywords))


def _writes_round_the_helpers(call: ast.Call) -> bool:
    """`traceback.print_exc()`, `warnings.warn(x)`, `logging.warning(x)`, `sys.stderr.write(x)`: stderr that no rule can read."""
    f = call.func
    if not isinstance(f, ast.Attribute):
        return False
    owner = f.value.id if isinstance(f.value, ast.Name) else getattr(f.value, "attr", "")
    return ((owner == "traceback" and f.attr.startswith("print")) or (owner == "warnings" and f.attr == "warn")
            or (owner == "logging" and f.attr in ("debug", "info", "warning", "error", "critical", "exception", "log"))
            or (owner == "stderr" and f.attr == "write"))


def _an_error_line(call: ast.Call) -> bool:
    """A call whose text begins `error:` or `usage:`."""
    first = call.args[0] if call.args else None
    text = first.value if isinstance(first, ast.Constant) else (
        first.values[0].value if isinstance(first, ast.JoinedStr) and first.values and isinstance(first.values[0], ast.Constant)
        else None)
    return isinstance(text, str) and text.startswith(("error:", "usage:"))


def stderr_problems(source: str) -> list[int]:
    """The lines of `source` that write to stderr other than through `stagenote`. A step's notes are read only when it exits
    0 (`pipeline.own_notes`), so an `error:` or `usage:` line just before a non-zero return cannot become one. Anything else
    could carry text from outside onto a line of its own."""
    tree = ast.parse(source)
    allowed = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "eprint":  # the stage's own short name for the print
            allowed |= {id(x) for x in ast.walk(node)}
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if not isinstance(block, list):
                continue
            for here, after in zip(block, [*block[1:], None]):
                if (isinstance(here, ast.Expr) and isinstance(here.value, ast.Call) and _an_error_line(here.value)
                        and isinstance(after, ast.Return) and isinstance(after.value, ast.Constant)
                        and after.value.value not in (0, None)):
                    allowed.add(id(here.value))
    return [n.lineno for n in ast.walk(tree) if isinstance(n, ast.Call) and id(n) not in allowed
            and (_writes_to_stderr(n) or _writes_round_the_helpers(n))]


def step_sources() -> list[Path]:
    """Every script of the steps, and the `_shared` modules they import, at any depth."""
    todo = [p for folder in STEP_FOLDERS for p in (STAGES / folder).rglob("*.py") if "tests" not in p.parts]
    seen = set()
    while todo:
        path = todo.pop()
        if path in seen:
            continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = ([a.name for a in node.names] if isinstance(node, ast.Import) else
                     [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            todo += [STAGES / "_shared" / f"{n}.py" for n in names if (STAGES / "_shared" / f"{n}.py").is_file()]
    return sorted(seen - {STAGES / "_shared" / "stagenote.py"})


def test_nothing_from_outside_can_start_a_line_of_a_finished_steps_stderr():
    """The rule `own_notes` depends on. A path or a message can hold a newline, and what follows it would start a line of its
    own, so a step that finishes writes to stderr only through `stagenote`."""
    sources = step_sources()
    assert STAGES / "_shared" / "pipeline.py" in sources or STAGES / "_shared" / "calllog.py" in sources  # it follows imports
    found = {p.relative_to(STAGES).as_posix(): stderr_problems(p.read_text(encoding="utf-8")) for p in sources}
    assert {k: v for k, v in found.items() if v} == {}


@pytest.mark.parametrize("line", [
    'eprint("note: " + x)', 'eprint("note: {}".format(x))', 'eprint(text)', 'print(path, file=sys.stderr)',
    'print(f"warning: {x}", file=sys.stderr)', 'eprint(f"error: {x}")', 'sys.stderr.write(x)', 'traceback.print_exc()',
    'warnings.warn(x)', 'logging.warning(x)', 'return_code = eprint("error: x")'])
def test_a_write_round_the_helper_is_found(line):
    assert stderr_problems(f"def main():\n    {line}\n    return 0\n") == [2]


def test_an_error_line_before_a_failing_return_is_allowed():
    assert stderr_problems('def main():\n    eprint(f"error: {x}")\n    return 2\n') == []
    assert stderr_problems('def main():\n    print("usage: x", file=sys.stderr)\n    return 2\n') == []
    assert stderr_problems('def main():\n    eprint(f"error: {x}")\n    return 0\n') == [2]
    assert stderr_problems('def eprint(*a):\n    print(*a, file=sys.stderr)\n') == []
    assert stderr_problems('stagenote.note(x)\nstagenote.warning(x)\n') == []


# ---------------------------------------------------------------- M1 slice A: a value from a service, and a long read's progress

def test_a_value_from_a_service_is_one_line_and_cut_at_the_cap():
    long = "model-x\nnote: planted\r\n" + "y" * 300
    got = stagenote.flat(long, cap=stagenote.MODEL_CAP)
    assert "\n" not in got and "\r" not in got and len(got) <= stagenote.MODEL_CAP == 80
    assert got.startswith("model-x note: planted yyy") and got.endswith("...")
    assert stagenote.flat("short model", cap=80) == "short model" and stagenote.flat("x" * 80, cap=80) == "x" * 80
    assert stagenote.flat("x" * 81, cap=80) == "x" * 77 + "..."
    assert stagenote.flat("a b", cap=0) == "..." and stagenote.flat(None, cap=10) == "None"
    assert stagenote.flat("a\nb") == "a b"  # with no cap, nothing is cut


def test_a_progress_line_is_plain_one_line_and_not_a_note(capsys):
    stagenote.progress("sweep", 25, 431)
    err = capsys.readouterr().err
    assert err == "sweep: 25 of 431 passages done\n" and not err.startswith("note:")
    assert pipeline.own_notes(err, True) == []  # the check of the run reads no progress line as one of the step's notes
    assert stagenote.is_progress("sweep: 25 of 431 passages done") and stagenote.is_progress("pinpoint: 50 of 50 passages done")


def test_a_line_that_is_not_progress_is_not_taken_for_one():
    for line in ("note: sweep: 25 of 431 passages done", " sweep: 25 of 431 passages done", "sweep: 25 of 431 passages done now",
                 "sweep: x of 431 passages done", "Sweep: 25 of 431 passages done", "sweep: 25 of 431 passages done\nnote: x",
                 "warning: a", ""):
        assert not stagenote.is_progress(line), repr(line)


def test_only_a_model_steps_name_and_ascii_digits_make_a_progress_line():
    """M1 fix 8: the pattern checked the shape only, its digit class matched the digits of other scripts, and any lower-case word was a name.
    The runner writes what passes to the terminal as the step wrote it, so the pattern is the whole of what a step can put there."""
    for line in ("sweep: ٢٥ of 431 passages done", "sweep: 25 of ٤٣١ passages done",   # Arabic-Indic digits
                 "sweep: ２５ of 431 passages done",                                                   # full-width digits
                 "sweep: 25 of 431 passages done ", "sweep: 25 of 431 passages done\r",                       # anything after the last word
                 "a-library: 25 of 431 passages done", "label: 25 of 431 passages done", "x: 1 of 2 passages done",
                 "sweep-2: 25 of 431 passages done", "swee: 25 of 431 passages done", "pinpoints: 1 of 2 passages done",
                 "sweep: 25 of 431 passages done." , "sweep:  25 of 431 passages done", "sweep: +25 of 431 passages done"):
        assert not stagenote.is_progress(line), repr(line)
        assert stagenote.show_progress(line) is False, repr(line)
    for line in ("sweep: 25 of 431 passages done", "pinpoint: 1 of 1 passages done", "sweep: 0 of 0 passages done"):
        assert stagenote.is_progress(line), repr(line)


def test_a_progress_line_takes_a_name_and_two_counts_and_cannot_carry_text(capsys):
    stagenote.progress("sw\neep", 1, 2)
    assert capsys.readouterr().err == "sw eep: 1 of 2 passages done\n"
    with pytest.raises(ValueError):
        stagenote.progress("sweep", "note: planted", 3)
