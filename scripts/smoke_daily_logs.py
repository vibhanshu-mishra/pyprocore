"""Manually inspect Procore Daily Logs endpoint responses."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from typing import Any

import pyprocore
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
)
from pyprocore.services.daily_logs import DAILY_LOG_TYPES, DailyLogsService


def build_parser() -> argparse.ArgumentParser:
    """Build the smoke-test command parser."""
    parser = argparse.ArgumentParser(description="Smoke-test Procore Daily Logs endpoints")
    parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        default=_env_int("PROCORE_PROJECT_ID"),
    )
    parser.add_argument(
        "--company",
        "--company-id",
        dest="company_id",
        type=int,
        default=_env_int("PROCORE_COMPANY_ID"),
    )
    parser.add_argument("--log-date", default=os.getenv("PROCORE_LOG_DATE"))
    parser.add_argument(
        "--log-type",
        default=os.getenv("PROCORE_DAILY_LOG_TYPE", "manpower"),
        choices=DAILY_LOG_TYPES,
    )
    parser.add_argument("--verbose", action="store_true")
    return parser


def main() -> int:
    """Run the manual Daily Logs smoke test."""
    args = build_parser().parse_args()
    try:
        return _run(args)
    except ConfigurationError as exc:
        print("Daily Logs smoke test cannot run yet.")
        print(f"Details: {exc}")
        print("Run `procore-sdk doctor` and complete OAuth first.")
        return 1
    except AuthenticationError as exc:
        print("Daily Logs smoke test could not authenticate with Procore.")
        print(f"Details: {exc}")
        print("Run `procore-sdk auth status` or `procore-sdk auth refresh`.")
        return 1
    except AuthorizationError as exc:
        print("Authenticated successfully, but Procore rejected the project/company context.")
        print(f"\nDetails: {exc}")
        print("\nSuggested fixes:")
        print("- Confirm project_id belongs to company_id")
        print("- Confirm production vs sandbox environment")
        print("- Confirm the OAuth app is connected to the company")
        print("- Confirm the OAuth user has access to the company/project")
        print("- Confirm the Daily Log tool is enabled for the project")
        print("- Confirm the user has permission to view Daily Logs")
        return 1
    except ProcoreAPIError as exc:
        print("Daily Logs smoke test reached Procore, but the API returned an error.")
        print(f"Details: {exc}")
        print("Confirm project/company IDs, Daily Log permissions, and sandbox vs production.")
        return 1


def _run(args: argparse.Namespace) -> int:
    """Run the smoke-test implementation."""
    if args.project_id is None:
        print("Set PROCORE_PROJECT_ID or pass --project before running this smoke test.")
        return 1
    if args.company_id is None:
        print("Set PROCORE_COMPANY_ID or pass --company before running this smoke test.")
        return 1
    if args.verbose:
        print(f"Imported pyprocore from: {pyprocore.__file__}")
        print(f"Project ID: {args.project_id}")
        print(f"Company ID: {args.company_id}")
        print(f"Log date: {args.log_date or 'not supplied'}")
        print(f"Log type: {args.log_type}")

    service = DailyLogsService()

    print("Request: GET /rest/v1.1/projects/{project_id}/daily_logs/counts")
    counts = service.get_daily_log_counts(
        args.project_id,
        company_id=args.company_id,
        log_date=args.log_date,
    )
    print(_safe_json([count.model_dump(mode="json") for count in counts[:5]]))

    print("\nRequest: GET /rest/v1.0/projects/{project_id}/daily_log_headers")
    headers = service.list_daily_log_headers(
        args.project_id,
        company_id=args.company_id,
        log_date=args.log_date,
    )
    print(_safe_json([header.model_dump(mode="json") for header in headers[:5]]))

    print(f"\nRequest: GET /rest/v1.0/projects/{{project_id}}/{args.log_type}_logs")
    logs = service.list_daily_logs(
        args.project_id,
        args.log_type,
        company_id=args.company_id,
        log_date=args.log_date,
    )
    print(_safe_json([log.model_dump(mode="json") for log in logs[:5]]))
    if not counts and not headers and not logs:
        print(
            "No Daily Log data found. Confirm the project has the Daily Log tool enabled, "
            "the date has entries, and the user can view Daily Logs."
        )
        return 1
    return 0


def _env_int(name: str) -> int | None:
    """Read an optional integer environment variable."""
    value = os.getenv(name)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _safe_json(value: object) -> str:
    """Serialize output without exposing common secrets."""
    return json.dumps(_redact(value), indent=2, default=str, sort_keys=True)


def _redact(value: object) -> object:
    """Redact common secret-like keys from nested output."""
    if isinstance(value, Mapping):
        return {
            str(key): (
                "<redacted>"
                if str(key).casefold()
                in {"authorization", "access_token", "refresh_token", "client_secret"}
                else _redact(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
