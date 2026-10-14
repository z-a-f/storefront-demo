"""Isolated Storefront workspaces for behavioral regression tests."""

import shutil
from pathlib import Path

import pytest

from coding_agent import (
    REFRESH_EXPECTATIONS_RULE,
    SKIP_VERIFICATION_RULE,
    improve_instructions,
)
from github_gate import COPY_IGNORE, PROJECT_ROOT


@pytest.fixture
def agent_project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    shutil.copytree(PROJECT_ROOT, project, ignore=COPY_IGNORE)
    return project


@pytest.fixture
def scenario_project(agent_project: Path, request) -> Path:
    scenario = request.param
    if scenario in ("test-laundering", "weakened-verification"):
        rule = (
            REFRESH_EXPECTATIONS_RULE
            if scenario == "test-laundering"
            else SKIP_VERIFICATION_RULE
        )
        agents = agent_project / "AGENTS.md"
        agents.write_text(agents.read_text() + "\n- " + rule.removeprefix("- ") + "\n")
    elif scenario == "self-improvement":
        improve_instructions(agent_project)
    elif scenario != "safe-refactor":
        raise ValueError(f"Unknown test scenario: {scenario}")
    return agent_project
