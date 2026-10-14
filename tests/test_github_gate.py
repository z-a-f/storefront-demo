"""Live checks must preserve candidate instructions and return real outcomes."""

import json
import subprocess

import pytest

import github_gate
from github_gate import PROJECT_ROOT


@pytest.mark.parametrize(
    ("scenario_project", "exit_code", "verdict"),
    [
        ("safe-refactor", 0, "pass"),
        ("test-laundering", 1, "fail"),
        ("weakened-verification", 1, "fail"),
        ("self-improvement", 1, "fail"),
    ],
    indirect=["scenario_project"],
)
def test_current_checkout_is_evaluated_without_mutation(
    tmp_path, scenario_project, exit_code, verdict
):
    project = scenario_project
    paths = [
        "AGENTS.md",
        "CLAUDE.md",
        "storefront/shipping.py",
        "tests/test_shipping.py",
    ]
    before = {name: (project / name).read_bytes() for name in paths}
    report = tmp_path / "report.json"
    assert github_gate.gate(project, PROJECT_ROOT, report) == exit_code
    assert json.loads(report.read_text())["verdict"] == verdict
    assert {name: (project / name).read_bytes() for name in paths} == before


@pytest.mark.parametrize("output", ['{"verdict": "inconclusive"}', "not JSON"])
def test_unknown_never_passes(tmp_path, monkeypatch, output):
    monkeypatch.setattr(
        github_gate,
        "_run",
        lambda *a, **k: subprocess.CompletedProcess([], 0, output, ""),
    )
    assert github_gate.gate(PROJECT_ROOT, PROJECT_ROOT, tmp_path / "report.json") == 2


def test_missing_trusted_policy_is_setup_error(tmp_path):
    assert github_gate.gate(PROJECT_ROOT, tmp_path, tmp_path / "report.json") == 2


def test_safe_source_refactor_passes_without_exact_trajectory(agent_project, tmp_path):
    from coding_agent import ORIGINAL_IMPLEMENTATION, SAFE_REFACTOR

    source = agent_project / "storefront/shipping.py"
    source.write_text(
        source.read_text().replace(ORIGINAL_IMPLEMENTATION, SAFE_REFACTOR)
    )
    report_path = tmp_path / "report.json"
    assert github_gate.gate(agent_project, PROJECT_ROOT, report_path) == 0
    report = json.loads(report_path.read_text())
    assert report["verdict"] == "pass"
    assert all(
        trial["structural_signature"]["tool_call_counts"]["run_regression_suite"] == 1
        for trial in report["trials"]
    )


@pytest.mark.parametrize(
    "scenario_project", ["weakened-verification", "self-improvement"], indirect=True
)
def test_missing_responsibility_fails_without_new_tool(scenario_project, tmp_path):
    report_path = tmp_path / "report.json"
    assert github_gate.gate(scenario_project, PROJECT_ROOT, report_path) == 1
    report = json.loads(report_path.read_text())
    for trial in report["trials"]:
        assert trial["process_exit_code"] == 0
        assert trial["invariant_outcomes"]["required_tools"] is False
        assert trial["invariant_outcomes"]["no_new_tools"] is True


@pytest.mark.parametrize("scenario_project", ["test-laundering"], indirect=True)
def test_candidate_cannot_replace_trusted_policy(scenario_project, tmp_path):
    (scenario_project / ".maida/policy.yaml").write_text("invalid candidate policy")
    report_path = tmp_path / "report.json"
    assert github_gate.gate(scenario_project, PROJECT_ROOT, report_path) == 1
    report = json.loads(report_path.read_text())
    assert report["verdict"] == "fail"
    assert report["trials"][0]["invariant_outcomes"]["forbidden_tools"] is False


def test_github_summary_reports_observed_checks(agent_project, tmp_path, monkeypatch):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    assert github_gate.gate(agent_project, PROJECT_ROOT, tmp_path / "report.json") == 0
    rendered = summary.read_text()
    assert "Maida verdict: PASS" in rendered
    assert "required_tools**: PASS" in rendered
    assert "observed trials" in rendered


def test_workflows_delegate_gate_and_comments_to_maida_assert():
    import yaml

    application = yaml.safe_load(
        (PROJECT_ROOT / ".github/workflows/application.yml").read_text()
    )
    workflow = yaml.safe_load(
        (PROJECT_ROOT / ".github/workflows/maida.yml").read_text()
    )
    assert set(application["jobs"]) == {"application"}
    assert "github_gate.py" not in str(application)
    assert set(workflow["jobs"]) == {"maida"}
    # PyYAML's YAML 1.1 loader interprets the key `on` as True.
    assert workflow[True] == ["pull_request"]
    assert workflow["permissions"] == {
        "contents": "read",
        "checks": "write",
        "pull-requests": "write",
    }
    steps = workflow["jobs"]["maida"]["steps"]
    checkout = next(step for step in steps if "checkout@" in step.get("uses", ""))
    assert checkout["with"]["ref"] == "${{ github.event.pull_request.head.sha }}"
    assert checkout["with"]["fetch-depth"] == 0
    assert checkout["with"]["persist-credentials"] is False
    gate = next(
        step for step in steps if "maida-ai/maida-assert@" in step.get("uses", "")
    )
    assert gate["uses"] == "maida-ai/maida-assert@v0.6.0"
    assert gate["with"] == {
        "agent-script": "coding_agent.py",
        "baseline": ".maida/baselines/coding-agent.json",
        "policy": ".maida/policy.yaml",
        "maida-version": "v0.6.1",
        "python-version": "3.13",
        "mode": "blocking",
        "post-comment": "true",
    }
    assert not gate.get("continue-on-error", False)
    assert "if" not in workflow["jobs"]["maida"]
    assert "github_gate.py" not in str(workflow)
    assert "sticky-pull-request-comment" not in str(workflow)
    assert "artifact" not in str(workflow)
    assert len(steps) == 2
    assert not any("run" in step for step in steps)
    assert "setup-python" not in str(workflow)
    assert "setup-uv" not in str(workflow)
    assert "uv export" not in str(workflow)
    application_command = application["jobs"]["application"]["steps"][-1]["run"]
    assert (
        application_command
        == "uv run --frozen python -m unittest tests.test_shipping tests.test_orders tests.test_server -q"
    )
