"""Live checks must preserve candidate instructions and return real outcomes."""

import json
import subprocess

import pytest

import demo
import github_gate


@pytest.mark.parametrize(
    ("scenario", "exit_code", "verdict"),
    [
        ("safe-refactor", 0, "pass"),
        ("test-laundering", 1, "fail"),
        ("weakened-verification", 1, "fail"),
        ("self-improvement", 1, "fail"),
    ],
)
def test_current_checkout_is_evaluated_without_mutation(
    tmp_path, scenario, exit_code, verdict
):
    project = demo._scenario_workspace(tmp_path, scenario)
    paths = [
        "AGENTS.md",
        "CLAUDE.md",
        "storefront/shipping.py",
        "tests/test_shipping.py",
    ]
    before = {name: (project / name).read_bytes() for name in paths}
    report = tmp_path / "report.json"
    assert github_gate.gate(project, demo.PROJECT_ROOT, report) == exit_code
    assert json.loads(report.read_text())["verdict"] == verdict
    assert {name: (project / name).read_bytes() for name in paths} == before


@pytest.mark.parametrize("output", ['{"verdict": "inconclusive"}', "not JSON"])
def test_unknown_never_passes(tmp_path, monkeypatch, output):
    monkeypatch.setattr(
        github_gate,
        "_run",
        lambda *a, **k: subprocess.CompletedProcess([], 0, output, ""),
    )
    assert (
        github_gate.gate(demo.PROJECT_ROOT, demo.PROJECT_ROOT, tmp_path / "report.json")
        == 2
    )


def test_missing_trusted_policy_is_setup_error(tmp_path):
    assert github_gate.gate(demo.PROJECT_ROOT, tmp_path, tmp_path / "report.json") == 2
