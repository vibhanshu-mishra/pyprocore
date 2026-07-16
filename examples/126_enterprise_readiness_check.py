"""Run a safe local enterprise readiness check.

This example does not call Procore. It checks local deployment choices and
prints plain-English findings for a private scheduled-export environment.
"""

from pathlib import Path

from pyprocore.workflows import evaluate_private_deployment_config


def main() -> None:
    """Run the example."""
    report = evaluate_private_deployment_config(
        auth_mode="client_credentials",
        environment_name="production",
        token_store_path=Path("/opt/pyprocore/token-stores/production/token_store.json"),
        export_output_dir=Path("/opt/pyprocore/exports/production"),
        log_dir=Path("/opt/pyprocore/logs/production"),
        scheduled_export_plan_path=Path("/opt/pyprocore/plans/nightly_project_context.json"),
        dry_run_required=True,
    )
    print(f"Readiness passed: {report.passed}")
    for finding in report.findings:
        print(f"{finding.severity.upper()} {finding.code}: {finding.message}")


if __name__ == "__main__":
    main()
