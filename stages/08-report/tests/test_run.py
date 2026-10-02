"""Tests for run.py, written from specs/run.SPEC.md."""
import re



def test_run_folder_and_documents(tiny_repo, tmp_path, capsys, snapshot, run_main):
    before = snapshot(tiny_repo)
    res = tmp_path / "results"
    assert run_main([str(tiny_repo), "--repo", "tiny", "--results", str(res), "--date", "2026-01-02",
                 "--no-validate"]) == 0
    runs = [p for p in (res / "tiny").iterdir()]
    assert len(runs) == 1 and re.fullmatch(r"2026-01-02_[0-9a-f]{7}", runs[0].name)
    d = runs[0]
    for name in ["01-inventory.json", "02-reader.json", "03-graph.json", "04-phrases.json",
                 "05-capability.json", "LOG.md", "07-limits.md", "report/summary.md", "report/full.md"]:
        assert (d / name).is_file(), name
    assert snapshot(tiny_repo) == before
    assert str(d) in capsys.readouterr().out


def test_second_run_gets_suffix(tiny_repo, tmp_path, run_main):
    res = tmp_path / "results"
    args = [str(tiny_repo), "--repo", "tiny", "--results", str(res), "--date", "2026-01-02", "--no-validate"]
    assert run_main(args) == 0 and run_main(args) == 0
    names = sorted(p.name for p in (res / "tiny").iterdir())
    assert len(names) == 2 and names[1].endswith("-2")


def test_results_inside_input_refused(tiny_repo, snapshot, run_main):
    before = snapshot(tiny_repo)
    assert run_main([str(tiny_repo), "--repo", "x", "--results", str(tiny_repo / "out"), "--no-validate"]) == 2
    assert snapshot(tiny_repo) == before


def test_rerender_rebuilds_report_only(tiny_repo, tmp_path, run_main):
    res = tmp_path / "results"
    assert run_main([str(tiny_repo), "--repo", "tiny", "--results", str(res), "--no-validate"]) == 0
    d = next((res / "tiny").iterdir())
    stage_before = {p.name: p.read_bytes() for p in d.glob("*.json")}
    (d / "report" / "summary.html").unlink()
    log_before = (d / "LOG.md").read_text(encoding="utf-8")
    assert run_main(["--rerender", str(d), "--no-validate"]) == 0
    assert (d / "report" / "summary.html").is_file()
    assert {p.name: p.read_bytes() for p in d.glob("*.json")} == stage_before
    log_after = (d / "LOG.md").read_text(encoding="utf-8")
    assert log_after.startswith(log_before) and "Report re-rendered" in log_after


def test_rerender_needs_a_run_folder(tmp_path, run_main):
    assert run_main(["--rerender", str(tmp_path), "--no-validate"]) == 2
