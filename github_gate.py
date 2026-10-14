"""Evaluate the current checkout, preserving the real verdict for GitHub."""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

from demo import (
    COPY_IGNORE,
    PROJECT_ROOT,
    _initialize_temp_repository,
    _maida_executable,
    _run,
)


def gate(project_root: Path, trusted_root: Path, report_path: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="github-gate-") as temp:
        root = Path(temp)
        project = root / "pr-gate"
        shutil.copytree(project_root, project, ignore=COPY_IGNORE)
        _initialize_temp_repository(root)
        completed = _run(
            [
                _maida_executable(),
                "run",
                "coding_agent.py",
                "--baseline",
                str(trusted_root / ".maida/baselines/coding-agent.json"),
                "--policy",
                str(trusted_root / ".maida/policy.yaml"),
                "--format",
                "json",
            ],
            cwd=project,
            env={**os.environ, "MAIDA_DATA_DIR": str(root / "traces")},
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(completed.stdout, encoding="utf-8")
        if completed.stderr:
            print(completed.stderr, file=sys.stderr)
        try:
            report = json.loads(completed.stdout)
            verdict = report["verdict"]
        except (ValueError, KeyError, TypeError):
            print("Setup error: Maida did not produce a valid report.", file=sys.stderr)
            return 2
        print(f"Maida verdict: {verdict}")
        print(json.dumps(report, indent=2))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with Path(summary).open("a", encoding="utf-8") as stream:
                stream.write(f"## Maida verdict: {str(verdict).upper()}\n\n")
                stream.write(
                    "Deterministic coding-agent harness; policy and baseline come from the base commit.\n\n"
                )
                for result in report.get("aggregate_results", []):
                    stream.write(
                        f"- **{result['check_name']}**: {result['verdict'].upper()} "
                        f"({result['trials_used']} observed trials)\n"
                    )
                stream.write("\n")
                stream.write(
                    "Application correctness and agent responsibilities are separate checks. See the JSON report in the job log for trial evidence.\n"
                )
        if completed.returncode == 0 and verdict == "pass":
            return 0
        if completed.returncode == 1 and verdict == "fail":
            return 1
        print(
            "Insufficient evidence or setup error; this demo requires explicit PASS.",
            file=sys.stderr,
        )
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trusted-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--report", type=Path, default=PROJECT_ROOT / "gate-report.json"
    )
    args = parser.parse_args()
    return gate(PROJECT_ROOT, args.trusted_root.resolve(), args.report.resolve())


if __name__ == "__main__":
    raise SystemExit(main())
