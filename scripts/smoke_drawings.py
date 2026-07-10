"""Manually inspect Procore Drawings endpoint responses.

This script is intentionally not used by unit tests or CI. It makes live
Procore API calls only when a developer runs it manually with valid sandbox
credentials.
"""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping
from typing import Any

import pyprocore
from pyprocore.core import endpoints
from pyprocore.core.client import ProcoreClient
from pyprocore.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ProcoreAPIError,
)

REQUIRED_CONFIG = (
    "PROCORE_CLIENT_ID",
    "PROCORE_CLIENT_SECRET",
    "PROCORE_REDIRECT_URI",
    "PROCORE_LOGIN_URL",
    "PROCORE_API_BASE",
    "PROCORE_COMPANY_ID",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the smoke-test command parser."""
    parser = argparse.ArgumentParser(description="Smoke-test Procore Drawings endpoints")
    parser.add_argument(
        "--project",
        "--project-id",
        dest="project_id",
        type=int,
        default=_env_int("PROCORE_PROJECT_ID"),
        help="Procore project ID. Defaults to PROCORE_PROJECT_ID.",
    )
    parser.add_argument(
        "--company-id",
        type=int,
        default=_env_int("PROCORE_COMPANY_ID"),
        help="Optional Procore company ID sent as Procore-Company-Id.",
    )
    parser.add_argument(
        "--area",
        "--area-id",
        dest="drawing_area_id",
        type=int,
        default=_env_int("PROCORE_DRAWING_AREA_ID"),
        help="Optional drawing area ID to filter drawings.",
    )
    parser.add_argument(
        "--drawing",
        "--drawing-id",
        dest="drawing_id",
        type=int,
        default=_env_int("PROCORE_DRAWING_ID"),
        help="Optional drawing ID to inspect.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print local SDK import and endpoint details without secrets.",
    )
    return parser


def main() -> int:
    """Run the manual Drawings smoke test."""
    args = build_parser().parse_args()
    try:
        return _run(args)
    except ConfigurationError as exc:
        _print_configuration_error(exc)
        return 1
    except AuthenticationError as exc:
        _print_auth_error("authentication", exc)
        return 1
    except AuthorizationError as exc:
        _print_context_rejected_error(exc)
        return 1
    except ProcoreAPIError as exc:
        _print_api_error(exc)
        return 1
    except Exception as exc:  # pragma: no cover - defensive manual smoke guard
        print("Drawings smoke test failed unexpectedly.")
        print(f"Reason: {type(exc).__name__}: {exc}")
        print("\nRun again with --verbose, then check `procore-sdk doctor`.")
        return 1


def _run(args: argparse.Namespace) -> int:
    """Run the manual Drawings smoke test implementation."""
    if args.project_id is None:
        print("Set PROCORE_PROJECT_ID or pass --project before running this smoke test.")
        return 1

    if args.verbose:
        _print_verbose_details(args)

    client = ProcoreClient()
    headers = _company_headers(args.company_id)

    print(f"Request: GET /rest/v1.0/projects/{args.project_id}/drawing_areas")
    areas = client.get_all(
        endpoints.drawing_areas(args.project_id),
        headers=headers,
    )
    print("Drawing areas sample:")
    print(_safe_json(_sample(areas)))
    if not areas:
        print(
            "\nNo drawing areas found. Confirm the project has the Drawings tool "
            "enabled and published drawings."
        )
        return 1

    drawing_area_id = args.drawing_area_id or _first_id(areas)
    if drawing_area_id is None:
        print("\nDrawing areas were returned, but no drawing area ID was found.")
        return 1
    print(f"\nUsing drawing area ID: {drawing_area_id}")

    print(f"\nRequest: GET /rest/v1.0/projects/{args.project_id}/drawing_disciplines")
    disciplines = client.get_all(
        endpoints.drawing_disciplines(args.project_id),
        headers=headers,
    )
    print("Drawing disciplines sample:")
    print(_safe_json(_sample(disciplines)))

    print(f"\nRequest: GET /rest/v1.0/drawing_areas/{drawing_area_id}/drawings")
    drawings = client.get_all(
        endpoints.drawings(args.project_id, drawing_area_id),
        headers=headers,
    )
    print("Drawings sample:")
    print(_safe_json(_sample(drawings)))
    if not drawings:
        print(
            f"\nNo drawings found for drawing area {drawing_area_id}. Confirm the area "
            "has published drawings and your user can access them."
        )
        return 1

    if args.drawing_id is not None:
        print(
            f"\nRequest: GET /rest/v1.0/drawing_areas/{drawing_area_id}"
            f"/drawings/{args.drawing_id}"
        )
        drawing = client.get(
            endpoints.drawing(args.project_id, drawing_area_id, args.drawing_id),
            headers=headers,
        )
        print("Drawing response sample:")
        print(_safe_json(drawing))

    print("\nReview the payload for drawing numbers, titles, url, or download_url fields.")
    return 0


def _print_configuration_error(exc: ConfigurationError) -> None:
    """Print a beginner-friendly configuration failure."""
    print("Drawings smoke test cannot run yet.")
    print("\nReason:")
    print("PyProcore configuration is missing or invalid.")
    if str(exc):
        print(f"\nDetails: {exc}")
    print("\nNext steps:")
    print("1. Run `procore-sdk doctor`")
    print("2. Fill in `.env` with your Procore OAuth settings")
    print("3. Run `procore-sdk auth login-url`")
    print("4. Run `procore-sdk auth exchange-code YOUR_AUTHORIZATION_CODE`")
    print("5. Run this smoke test again")
    print("\nRequired values:")
    for name in REQUIRED_CONFIG:
        print(f"- {name}")


def _print_auth_error(kind: str, exc: Exception) -> None:
    """Print a beginner-friendly authentication failure."""
    print("Drawings smoke test could not authenticate with Procore.")
    print(f"\nReason: Procore {kind} failed.")
    print(f"Details: {exc}")
    print("\nNext steps:")
    print("1. Run `procore-sdk auth status`")
    print("2. If needed, run `procore-sdk auth refresh`")
    print("3. Confirm your Procore user can access this company's Drawings tool")


def _print_context_rejected_error(exc: AuthorizationError) -> None:
    """Print a beginner-friendly project/company authorization failure."""
    print("Authenticated successfully, but Procore rejected the project/company context.")
    print(f"\nDetails: {exc}")
    print("\nNext steps:")
    print("1. Confirm project_id belongs to company_id")
    print("2. Confirm production vs sandbox environment")
    print("3. Confirm the OAuth user has access to the company/project")
    print("4. Confirm the Drawings tool is enabled for the project")
    print("5. Confirm the user has permission to view Drawings")


def _print_api_error(exc: ProcoreAPIError) -> None:
    """Print a safe summary of a Procore API failure."""
    print("Drawings smoke test reached Procore, but the API returned an error.")
    print(f"\nReason: {type(exc).__name__}")
    print(f"Details: {exc}")
    print("\nNext steps:")
    print("1. Confirm PROCORE_PROJECT_ID is correct")
    print("2. Confirm your user has access to the project's Drawings tool")
    print("3. If filtering by area or drawing, confirm those IDs are correct")
    print("4. For 404s, confirm sandbox vs production API base and that drawing areas exist")


def _print_verbose_details(args: argparse.Namespace) -> None:
    """Print non-secret local runtime details."""
    print("Verbose diagnostics:")
    print(f"- Imported pyprocore from: {pyprocore.__file__}")
    print(f"- Project ID: {args.project_id}")
    print(f"- Drawing area ID: {args.drawing_area_id or '<not set>'}")
    print(f"- Drawing ID: {args.drawing_id or '<not set>'}")
    print(f"- Company header: {'set' if args.company_id is not None else '<not set>'}")
    print(f"- Areas endpoint: {endpoints.drawing_areas(args.project_id or 0)}")
    print(f"- Disciplines endpoint: {endpoints.drawing_disciplines(args.project_id or 0)}")
    area_id = args.drawing_area_id or 0
    print(f"- Drawings endpoint: {endpoints.drawings(args.project_id or 0, area_id)}")
    if args.drawing_id is not None:
        print(
            "- Drawing endpoint: "
            f"{endpoints.drawing(args.project_id or 0, area_id, args.drawing_id)}"
        )
    print()


def _company_headers(company_id: int | None) -> dict[str, str] | None:
    """Return optional company header for Drawings endpoints."""
    if company_id is None:
        return None
    return {"Procore-Company-Id": str(company_id)}


def _env_int(name: str) -> int | None:
    """Read an optional integer environment variable."""
    value = os.getenv(name)
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _sample(value: object) -> object:
    """Return a small payload sample for terminal output."""
    if isinstance(value, list):
        return value[:3]
    return value


def _first_id(values: object) -> int | None:
    """Return the first integer ID from a list-like Procore response."""
    if not isinstance(values, list):
        return None
    for value in values:
        if not isinstance(value, Mapping):
            continue
        raw_id = value.get("id")
        if isinstance(raw_id, int):
            return raw_id
        if isinstance(raw_id, str) and raw_id.isdecimal():
            return int(raw_id)
    return None


def _safe_json(value: object) -> str:
    """Serialize output without exposing auth headers or secrets."""
    return json.dumps(_redact(value), indent=2, default=str, sort_keys=True)


def _redact(value: object) -> object:
    """Redact common secret-like keys from nested output."""
    if isinstance(value, Mapping):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).casefold() in {
                "authorization",
                "access_token",
                "refresh_token",
                "client_secret",
            }:
                redacted[str(key)] = "<redacted>"
            else:
                redacted[str(key)] = _redact(item)
        return redacted
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


if __name__ == "__main__":
    raise SystemExit(main())
