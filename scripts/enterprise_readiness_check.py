"""Run a local PyProcore private deployment readiness check."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from pyprocore.app import format_enterprise_readiness_report
from pyprocore.workflows.deployment import evaluate_private_deployment_config


def build_parser() -> argparse.ArgumentParser:
    """Build the command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--auth-mode", default="client_credentials")
    parser.add_argument("--environment-name")
    parser.add_argument("--token-store-path", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--log-dir", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--allow-no-dry-run", action="store_true")
    parser.add_argument("--user-workflow", action="store_true")
    return parser


def main() -> int:
    """Run the local readiness check."""
    args = build_parser().parse_args()
    report = evaluate_private_deployment_config(
        auth_mode=args.auth_mode,
        token_store_path=args.token_store_path,
        export_output_dir=args.output_dir,
        log_dir=args.log_dir,
        environment_name=args.environment_name,
        scheduled_export_plan_path=args.plan,
        dry_run_required=not args.allow_no_dry_run,
        server_to_server=not args.user_workflow,
    )
    print(format_enterprise_readiness_report(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
